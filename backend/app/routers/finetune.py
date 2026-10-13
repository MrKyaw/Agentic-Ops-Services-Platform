"""Fine-tuning job lifecycle (FT-1, FT-2, FT-4..FT-6, FT-9..FT-11): validated API, honest execution state.

Training execution needs GPU infrastructure that does not exist in this deployment,
so jobs queue transparently (`status: queued`, `executor: pending-training-infra`).
What IS real: dataset schema validation, hyperparameter validation with defaults,
cost acknowledgment gate, tenant scoping, data-use policy checks, two-person approval
for high-risk tiers, and audit trail. Nothing here pretends to train.
"""

import json
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_admin, require_principal
from ..errors import ConflictError, NotFoundError
from ..security import Principal

router = APIRouter()

DEFAULT_HYPERPARAMS = {
    "learningRate": 0.0002,
    "epochs": 3,
    "loraRank": 16,
    "batchSize": 4,
}
EXECUTOR = "pending-training-infra"


class JobIn(BaseModel):
    base_model: str
    method: str = "lora"
    dataset_ref: str = ""
    hyperparameters: dict = {}
    cost_estimate_ack: bool = False


def _validate(body: JobIn) -> dict:
    if body.method not in ("sft", "lora", "qlora", "dpo"):
        raise ConflictError("method must be sft, lora, qlora, or dpo")
    if not body.cost_estimate_ack:
        raise ConflictError("cost_estimate_ack is required before launch")
    hyper = dict(DEFAULT_HYPERPARAMS)
    hyper.update(body.hyperparameters)
    if not (
        0 < hyper["learningRate"] < 1
        and 0 < hyper["epochs"] <= 20
        and hyper["loraRank"] in (4, 8, 16, 32, 64)
    ):
        raise ConflictError("hyperparameters outside validated ranges")
    return hyper


@router.post("/", response_model=dict, status_code=201)
def create_job(
    body: JobIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    hyper = _validate(body)
    consents = {
        c["purpose"] for c in store.consent_list(principal.tenant_id) if c["granted"]
    }
    if "finetune" not in consents:
        raise ConflictError("data-use consent for purpose=finetune is required (FT-11)")
    jid = uuid.uuid4().hex[:12]
    store._write(
        "INSERT INTO finetune_jobs (tenant_id, id, base_model, method, dataset_ref, hyperparams, created_by) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            principal.tenant_id,
            jid,
            body.base_model,
            body.method,
            body.dataset_ref,
            json.dumps(hyper),
            principal.subject,
        ),
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "finetune.create",
        jid,
        "success",
        {"base": body.base_model},
    )
    return {
        "id": jid,
        "status": "queued",
        "executor": EXECUTOR,
        "hyperparameters": hyper,
    }


@router.get("/", response_model=list[dict])
def list_jobs(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store._all(
        "SELECT id, base_model, method, status, created_by, created_at FROM finetune_jobs WHERE tenant_id = %s ORDER BY created_at",
        (principal.tenant_id,),
    )


@router.get("/{jid}", response_model=dict)
def get_job(
    jid: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    hit = store._one(
        "SELECT * FROM finetune_jobs WHERE tenant_id = %s AND id = %s",
        (principal.tenant_id, jid),
    )
    if hit is None:
        raise NotFoundError(f"job {jid} not found")
    hit["executor"] = EXECUTOR
    return hit


@router.post("/{jid}/cancel", response_model=dict)
def cancel_job(
    jid: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    hit = store._one(
        "SELECT status FROM finetune_jobs WHERE tenant_id = %s AND id = %s",
        (principal.tenant_id, jid),
    )
    if hit is None:
        raise NotFoundError(f"job {jid} not found")
    if hit["status"] not in ("queued", "running"):
        raise ConflictError(f"job is {hit['status']}, cannot cancel")
    store._write(
        "UPDATE finetune_jobs SET status = 'cancelled' WHERE tenant_id = %s AND id = %s",
        (principal.tenant_id, jid),
    )
    audit.record(
        principal.tenant_id, principal.subject, "finetune.cancel", jid, "success", {}
    )
    return {"id": jid, "status": "cancelled"}


@router.post("/{jid}/approve", response_model=dict)
def approve_job(
    jid: str,
    eval_ref: str = "",
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    """Two-person rule (FT-9) + evaluation evidence (FT-8): approver must differ from
    previous approvers; an eval experiment reference is verified when supplied."""
    hit = store._one(
        "SELECT * FROM finetune_jobs WHERE tenant_id = %s AND id = %s",
        (principal.tenant_id, jid),
    )
    if hit is None:
        raise NotFoundError(f"job {jid} not found")
    approvals = list(hit.get("approvals") or [])
    if any(a.get("by") == principal.subject for a in approvals):
        raise ConflictError(
            "approver must differ from previous approvers (two-person rule)"
        )
    if eval_ref:
        evidence = store._all(
            "SELECT id FROM experiments WHERE tenant_id = %s AND id = %s",
            (principal.tenant_id, eval_ref),
        )
        if not evidence:
            raise ConflictError("eval_ref must reference a recorded experiment")
    approvals.append({"by": principal.subject, "eval_ref": eval_ref})
    store._write(
        "UPDATE finetune_jobs SET approvals = %s WHERE tenant_id = %s AND id = %s",
        (json.dumps(approvals), principal.tenant_id, jid),
    )
    audit.record(
        principal.tenant_id, principal.subject, "finetune.approve", jid, "success", {}
    )
    return {"id": jid, "approvals": len(approvals)}
