"""Per-tenant agent catalog (MT-1..MT-3, AO-5): versioned, immutable, strictly tenant-scoped."""

from fastapi import APIRouter, Depends

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_principal
from ..errors import ConflictError, NotFoundError
from ..models import AgentCreate, AgentOut
from ..security import Principal

router = APIRouter()


def _out(row: dict) -> AgentOut:
    return AgentOut(
        id=row["id"],
        tenantId=row["tenant_id"],
        displayName=row["display_name"],
        pattern=row["pattern"],
        version=row["version"],
        status=row["status"],
    )


@router.get("/", response_model=list[AgentOut])
def list_agents(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[AgentOut]:
    return [_out(a) for a in store.agent_list(principal.tenant_id)]


@router.post("/", response_model=AgentOut, status_code=201)
def create_agent(
    body: AgentCreate,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> AgentOut:
    if store.agent_latest(principal.tenant_id, body.id):
        raise ConflictError(f"agent {body.id} already exists")
    store.agent_save(
        principal.tenant_id,
        body.id,
        "0.1.0",
        body.displayName,
        body.pattern,
        {"pattern": body.pattern},
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "agent.create",
        body.id,
        "success",
        {"pattern": body.pattern},
    )
    return _out(store.agent_latest(principal.tenant_id, body.id) or {})


@router.get("/{agent_id}", response_model=AgentOut)
def get_agent(
    agent_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> AgentOut:
    hit = store.agent_latest(principal.tenant_id, agent_id)
    if hit is None:
        raise NotFoundError(f"agent {agent_id} not found")
    return _out(hit)
