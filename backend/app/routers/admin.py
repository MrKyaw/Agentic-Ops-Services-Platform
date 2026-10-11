"""Tenant administration: quotas (MT-4), kill switches (TS-3). Platform/tenant admins only."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_admin
from ..llm import flip
from ..security import Principal

router = APIRouter()


class QuotasIn(BaseModel):
    rpm: int = 60
    runs_per_day: int = 1000


class KillIn(BaseModel):
    scope: str  # platform | tenant:<id> | agent:<tenant>:<id>
    on: bool = True


@router.get("/quotas", response_model=dict)
def get_quotas(
    principal: Principal = Depends(require_admin), store: Store = Depends(get_store)
) -> dict:
    return store.quotas_get(principal.tenant_id)


@router.put("/quotas", response_model=dict)
def set_quotas(
    body: QuotasIn,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    quotas = {"rpm": max(1, body.rpm), "runs_per_day": max(1, body.runs_per_day)}
    store.quotas_set(principal.tenant_id, quotas)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "quotas.set",
        principal.tenant_id,
        "success",
        quotas,
    )
    return quotas


@router.post("/kill-switch", response_model=dict)
def kill_switch(
    body: KillIn,
    principal: Principal = Depends(require_admin),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    if body.scope != "platform" and not (
        body.scope.startswith("tenant:") or body.scope.startswith("agent:")
    ):
        from ..errors import ConflictError

        raise ConflictError(
            "scope must be platform, tenant:<id>, or agent:<tenant>:<id>"
        )
    flip(body.scope, body.on)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "kill.switch",
        body.scope,
        "success",
        {"on": body.on},
    )
    return {"scope": body.scope, "killed": body.on}
