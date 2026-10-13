"""Per-tenant agent catalog (MT-1..MT-3, AO-5): versioned, immutable, strictly tenant-scoped."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_admin, require_principal
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


class PromoteIn(BaseModel):
    business_metric: str
    baseline: str
    target: str


@router.post("/{agent_id}/promote", response_model=dict)
def promote_agent(
    agent_id: str,
    body: PromoteIn,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    """Production promotion requires a business impact definition (SM-5)."""
    hit = store.agent_latest(principal.tenant_id, agent_id)
    if hit is None:
        raise NotFoundError(f"agent {agent_id} not found")
    manifest = dict(hit.get("manifest") or {})
    manifest["businessImpact"] = {
        "metric": body.business_metric,
        "baseline": body.baseline,
        "target": body.target,
    }
    store.agent_save(
        principal.tenant_id,
        agent_id,
        hit["version"],
        hit["display_name"],
        hit["pattern"],
        manifest,
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "agent.promote",
        agent_id,
        "success",
        manifest["businessImpact"],
    )
    return {
        "id": agent_id,
        "version": hit["version"],
        "businessImpact": manifest["businessImpact"],
    }


@router.get("/templates/all", response_model=list[dict])
def list_templates(store: Store = Depends(get_store)) -> list[dict]:
    _ = store
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "description": t["description"],
            "manifest": t["manifest"],
        }
        for t in store.template_list()
    ]


class CanaryIn(BaseModel):
    version_a: str = "0.1.0"
    version_b: str = "0.1.0"
    message: str


@router.post("/{agent_id}/canary", response_model=dict)
def canary_compare(
    agent_id: str,
    body: CanaryIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    """Shadow execution (AO-18, ET-6): same input through two patterns, agreement reported."""
    import time as _time

    from ..react import Budget, LocalPlanner, ReActRunner
    from ..rewoo import ReWOORunner
    from .runs import _register_tools, _tool_handlers

    _register_tools()
    tools = _tool_handlers(
        store, principal.tenant_id, audit, principal.subject, allow_write=False
    )
    readonly = {
        "kb.search": tools["kb.search"],
        "catalog.lookup": tools["catalog.lookup"],
    }
    started = _time.time()
    react = ReActRunner(LocalPlanner(), Budget()).run(body.message, dict(readonly))
    rewoo = ReWOORunner().run(body.message, dict(readonly))
    latency_ms = int((_time.time() - started) * 1000)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "agent.canary",
        agent_id,
        "success",
        {"versions": [body.version_a, body.version_b]},
    )
    return {
        "agent_id": agent_id,
        "versions": [body.version_a, body.version_b],
        "answers": {"react": react.answer, "rewoo": rewoo.answer},
        "agree": react.answer == rewoo.answer,
        "latency_ms": latency_ms,
    }
