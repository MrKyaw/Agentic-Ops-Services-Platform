"""Conversation memory (AO-12, short-term): tenant/agent/session scoped, erasable (PV-4)."""

from fastapi import APIRouter, Depends

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_principal
from ..security import Principal

router = APIRouter()


@router.get("/{agent_id}", response_model=list[dict])
def read_memory(
    agent_id: str,
    session_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> list[dict]:
    return store.memory_list(principal.tenant_id, agent_id, session_id)


@router.delete("/{agent_id}", response_model=dict)
def clear_memory(
    agent_id: str,
    session_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    removed = store.memory_clear(principal.tenant_id, agent_id, session_id)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "memory.clear",
        f"{agent_id}/{session_id}",
        "success",
        {},
    )
    return {"cleared": removed}
