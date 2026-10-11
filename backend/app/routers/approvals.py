"""Human-in-the-loop approval inbox (AO-11, FE-5): pending actions with approve/reject/edit."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_admin, require_principal
from ..errors import ConflictError, NotFoundError
from ..security import Principal

router = APIRouter()


class DecideIn(BaseModel):
    decision: str  # approved | rejected


@router.get("/", response_model=list[dict])
def list_approvals(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store.approval_list(principal.tenant_id)


@router.post("/{aid}/decide", response_model=dict)
def decide(
    aid: str,
    body: DecideIn,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    if body.decision not in ("approved", "rejected"):
        raise ConflictError("decision must be approved or rejected")
    approval = store.approval_get(principal.tenant_id, aid)
    if approval is None:
        raise NotFoundError(f"approval {aid} not found")
    if approval["status"] != "pending":
        raise ConflictError(f"approval {aid} already {approval['status']}")
    store.approval_decide(principal.tenant_id, aid, body.decision, principal.subject)
    run_status = "succeeded" if body.decision == "approved" else "rejected"
    output = {
        "answer": f"action {approval['action']} {body.decision} by {principal.subject}"
    }
    store.run_set(
        principal.tenant_id,
        approval["run_id"],
        run_status,
        output,
        {"decided": body.decision},
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "approval.decide",
        aid,
        "success",
        {"decision": body.decision},
    )
    return {"id": aid, "status": body.decision, "run_id": approval["run_id"]}
