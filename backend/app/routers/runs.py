"""Agent run execution (AO-2, AO-7..AO-11, AO-13, AO-15..AO-17) with HITL approvals (AO-11)."""

import uuid
from datetime import datetime, timezone

import jsonschema
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from ..audit import AuditLogger
from ..config import Settings
from ..db import Store
from ..deps import get_audit, get_settings, get_store, require_principal
from ..errors import NotFoundError, RateLimitError, UnavailableError
from ..intent import classify
from ..llm import DisabledBackend, GatewayError, select
from ..mcp import ToolCall, ToolDef, registry
from ..quotas import allow, cost_usd, estimate_tokens
from ..rag import retrieval_query, rrf, tfidf_scores
from ..react import Budget, LocalPlanner, ModelPlanner, ReActRunner, RunResult, Step
from ..security import Principal

router = APIRouter()

INVOICES = {
    "88123": {
        "invoice": "88123",
        "status": "flagged",
        "amount": 1240.0,
        "reason": "amount mismatch",
    },
    "1024": {
        "invoice": "1024",
        "status": "flagged",
        "amount": 88.5,
        "reason": "missing purchase order",
    },
}


def _register_tools() -> None:
    if registry.list():
        return
    registry.register(
        ToolDef(
            server="kb",
            name="search",
            version="1.0",
            description="Read-only knowledge base search with citations",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "kb_id": {"type": "string"},
                    "top_k": {"type": "integer"},
                },
                "required": ["query"],
            },
            risk="read-only",
        )
    )
    registry.register(
        ToolDef(
            server="catalog",
            name="lookup",
            version="1.0",
            description="Read-only invoice catalog lookup (synthetic pilot data)",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            risk="read-only",
        )
    )
    registry.register(
        ToolDef(
            server="cases",
            name="create",
            version="1.0",
            description="Open a support case (reversible write, approval required)",
            input_schema={
                "type": "object",
                "properties": {
                    "invoice": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["invoice"],
            },
            risk="reversible-write",
        )
    )


class RunIn(BaseModel):
    agent_id: str = "pilot-triage"
    input: dict = Field(default_factory=dict)
    mode: str = "sync"


def _tool_handlers(
    store: Store, tenant: str, audit: AuditLogger, actor: str, allow_write: bool
) -> dict:
    def kb_search(args: dict) -> str:
        hits = store.chunk_search_fts(
            tenant, args.get("kb_id", "kb-policy"), retrieval_query(args["query"]), 6
        )
        docs = [{"id": h["id"], "content": h["content"]} for h in hits]
        scores = tfidf_scores(args["query"], docs)
        tfidf_ranked = [
            doc_id
            for doc_id, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        ]
        ranked = [d for d, _ in rrf([[h["id"] for h in hits], tfidf_ranked])]
        cites = [
            next(h["content"] for h in hits if h["id"] == did) for did in ranked[:3]
        ]
        out = registry.invoke(
            ToolCall("kb", "search", args),
            lambda t, a: {"passages": cites},
            tenant,
            actor,
            audit,
            allow_write=True,
        )
        return " | ".join(out["result"]["passages"]) or "no evidence"

    def catalog_lookup(args: dict) -> str:
        def _run(tool: ToolDef, a: dict) -> dict:
            for inv_id, rec in INVOICES.items():
                if inv_id in a.get("query", ""):
                    return rec
            return {"match": "none"}

        out = registry.invoke(
            ToolCall("catalog", "lookup", args),
            _run,
            tenant,
            actor,
            audit,
            allow_write=True,
        )
        return str(out["result"])

    def case_create(args: dict) -> str:
        def _run(tool: ToolDef, a: dict) -> dict:
            return {
                "case_id": f"case-{a.get('invoice', 'unknown')}",
                "status": "opened",
            }

        out = registry.invoke(
            ToolCall("cases", "create", args),
            _run,
            tenant,
            actor,
            audit,
            allow_write=allow_write,
        )
        return str(out["result"])

    case_create.needs_approval = True  # type: ignore[attr-defined]

    def agent_invoke(args: dict) -> str:
        """Multi-agent composition (AO-14): depth-capped, cycle-safe (nested agent loses this tool)."""
        from ..react import Budget as _Budget
        from ..react import LocalPlanner as _Planner
        from ..react import ReActRunner as _Runner

        depth = int(args.get("depth", 0))
        if depth > 2:
            return "max composition depth exceeded"
        nested_tools = {"kb.search": kb_search, "catalog.lookup": catalog_lookup}
        nested = _Runner(_Planner(), _Budget(max_iterations=4)).run(
            str(args.get("message", "")), nested_tools
        )
        return nested.answer

    return {
        "kb.search": kb_search,
        "catalog.lookup": catalog_lookup,
        "case.create": case_create,
        "agent.invoke": agent_invoke,
    }


def _persist_trace(store: Store, tenant: str, rid: str, result, intent: dict) -> None:
    seq = 0
    store.step_add(tenant, rid, seq, "intent", intent)
    seq += 1
    for step in result.steps:
        store.step_add(tenant, rid, seq, step.kind, step.content)
        seq += 1


def _intent_dict(intent) -> dict:
    return {
        "workflow": intent.workflow_id,
        "confidence": intent.confidence,
        "resolution": intent.resolution,
    }


def _persist_steps(store: Store, tenant: str, rid: str, intent, steps: list) -> None:
    _persist_trace(
        store, tenant, rid, type("R", (), {"steps": steps})(), _intent_dict(intent)
    )


def _finish_run(
    store, tenant, rid, result, intent, manifest, message, principal, audit, body
) -> dict:
    _persist_trace(store, tenant, rid, result, _intent_dict(intent))
    from ..pii import redact_text, scan

    answer = result.answer
    dlp_redacted = False
    if scan(answer):
        answer = redact_text(answer)
        dlp_redacted = True
    schema = manifest.get("output_schema")
    if schema:
        try:
            jsonschema.validate({"answer": answer}, schema)
        except jsonschema.ValidationError:
            store.run_set(
                tenant,
                rid,
                "failed",
                {"answer": answer},
                {**result.usage, "schema_violation": True},
            )
            return {
                "id": rid,
                "status": "failed",
                "reason": "output schema violation",
                "deduped": False,
            }
    usage = {
        **result.usage,
        "tokens_in": estimate_tokens(message),
        "tokens_out": estimate_tokens(answer),
        "dlp_redacted": dlp_redacted,
    }
    store.run_set(tenant, rid, result.status, {"answer": answer}, usage)
    store.usage_add(
        tenant,
        datetime.now(timezone.utc).date().isoformat(),
        intent.workflow_id,
        1,
        usage["tokens_in"],
        usage["tokens_out"],
        cost_usd(usage["tokens_in"], usage["tokens_out"]),
    )
    session_id = str(body.input.get("session_id", ""))
    if session_id and result.status == "succeeded":
        store.memory_add(tenant, body.agent_id, session_id, "user", message[:2000])
        store.memory_add(tenant, body.agent_id, session_id, "assistant", answer[:2000])
    _deliver_webhooks(
        store, tenant, "run.completed", {"run_id": rid, "status": result.status}
    )
    from .system import record_run_outcome

    record_run_outcome(result.status)
    return {
        "id": rid,
        "status": result.status,
        "answer": result.answer,
        "deduped": False,
    }


def _deliver_webhooks(store: Store, tenant: str, event: str, payload: dict) -> None:
    """Best-effort signed webhook delivery (AP-7): failures never fail the run."""
    import hashlib
    import hmac
    import json as _json

    import httpx

    for hook in store.webhook_list(tenant):
        if event not in (hook.get("events") or []):
            continue
        body = _json.dumps({"event": event, **payload}).encode()
        signature = hmac.new(
            hook.get("secret", "").encode(), body, hashlib.sha256
        ).hexdigest()
        try:
            httpx.post(
                hook["url"],
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Signature": f"sha256={signature}",
                },
                timeout=5,
            )
        except Exception:
            continue


@router.post("/", response_model=dict, status_code=201)
def create_run(
    body: RunIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
    settings: Settings = Depends(get_settings),
    idempotency_key: str = Header(default="", alias="Idempotency-Key"),
) -> dict:
    _register_tools()
    tenant = principal.tenant_id
    quotas = store.quotas_get(tenant)
    if not allow(tenant, int(quotas.get("rpm", 60))):
        raise RateLimitError(
            f"tenant {tenant} exceeded {quotas.get('rpm', 60)} requests/minute"
        )
    agent_row = store.agent_latest(tenant, body.agent_id)
    manifest = (agent_row or {}).get("manifest") or {}
    registry_ref = (manifest.get("model") or {}).get("registry_ref", "")
    if registry_ref and "@" in registry_ref:
        mid, _, version = registry_ref.partition("@")
        entry = next(
            (
                m
                for m in store.model_list(tenant)
                if m["id"] == mid and m["version"] == version
            ),
            None,
        )
        if entry is not None and entry["status"] in ("deprecated", "retired"):
            raise UnavailableError(f"model {registry_ref} is {entry['status']}")
    secrets = {
        "api_key": settings.openrouter_api_key,
        "model": settings.openrouter_model,
        "base_url": settings.openrouter_base,
    }
    policy = manifest.get("model", {})
    candidates = [policy.get("primary", "local-standin")] + list(
        policy.get("fallbacks", ["local-standin"])
    )
    backend = None
    last_error: Exception | None = None
    for primary in dict.fromkeys(candidates):
        try:
            backend = select(
                tenant, body.agent_id, {**policy, "primary": primary}, secrets
            )
            break
        except GatewayError as exc:
            last_error = exc
    if backend is None:
        raise UnavailableError(str(last_error or "no model backend available"))
    if isinstance(backend, DisabledBackend):
        raise UnavailableError(f"model backend kill-switched ({backend.name})")
    if idempotency_key:
        existing = store._one(
            "SELECT id, status FROM runs WHERE tenant_id = %s AND idempotency_key = %s",
            (tenant, idempotency_key),
        )
        if existing:
            return {"id": existing["id"], "status": existing["status"], "deduped": True}
    message = str(body.input.get("message", ""))
    intent = classify(message, store.intent_list(tenant))
    rid = uuid.uuid4().hex[:12]
    store.run_create(tenant, rid, body.agent_id, "0.1.0", body.input, idempotency_key)
    from ..llm import LocalBackend as _Local

    planner = (
        ModelPlanner(backend) if not isinstance(backend, _Local) else LocalPlanner()
    )
    runner = ReActRunner(planner, Budget())
    tools = _tool_handlers(store, tenant, audit, principal.subject, allow_write=False)
    pattern = (agent_row or {}).get("pattern", "react")
    if pattern == "rewoo":
        from ..rewoo import ReWOORunner

        rewoo = ReWOORunner().run(
            message,
            {
                k: tools[k]
                for k in ("kb.search", "catalog.lookup", "case.create")
                if k in tools
            },
        )
        result_steps = [
            Step("model", {"plan": rewoo.plan.plan_text if rewoo.plan else ""})
        ]
        for key, value in rewoo.evidence.items():
            result_steps.append(Step("tool", {"evidence": key, "observation": value}))
        if rewoo.status == "waiting_approval":
            store.run_set_status(tenant, rid, "waiting_approval")
            aid = uuid.uuid4().hex[:12]
            store.approval_create(
                tenant,
                aid,
                rid,
                "case.create",
                {"plan": rewoo.plan.plan_text if rewoo.plan else ""},
            )
            audit.record(
                tenant, principal.subject, "approval.requested", aid, "success", {}
            )
            _persist_steps(store, tenant, rid, intent, result_steps)
            return {
                "id": rid,
                "status": "waiting_approval",
                "approval_id": aid,
                "deduped": False,
            }
        result = RunResult("succeeded", rewoo.answer, result_steps, rewoo.usage)
        return _finish_run(
            store,
            tenant,
            rid,
            result,
            intent,
            manifest,
            message,
            principal,
            audit,
            body,
        )
    # Planner trigger for the approval path: explicit case requests need a human (AO-11).
    if "open a case" in message.lower() or "create a case" in message.lower():
        result = runner.run(message, {"case.create": tools["case.create"]})
    else:
        result = runner.run(
            message,
            {
                "kb.search": tools["kb.search"],
                "catalog.lookup": tools["catalog.lookup"],
            },
        )
    if result.status == "waiting_approval" and result.needs_approval:
        store.run_set_status(tenant, rid, "waiting_approval")
        aid = uuid.uuid4().hex[:12]
        store.approval_create(
            tenant,
            aid,
            rid,
            result.needs_approval["action"],
            result.needs_approval["input"],
        )
        audit.record(
            tenant, principal.subject, "approval.requested", aid, "success", {}
        )
        return {
            "id": rid,
            "status": "waiting_approval",
            "approval_id": aid,
            "deduped": False,
        }
    return _finish_run(
        store, tenant, rid, result, intent, manifest, message, principal, audit, body
    )


@router.get("/", response_model=list[dict])
def list_runs(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store.run_list(principal.tenant_id)


@router.get("/{rid}", response_model=dict)
def get_run(
    rid: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    run = store.run_get(principal.tenant_id, rid)
    if run is None:
        raise NotFoundError(f"run {rid} not found")
    run["steps"] = store.steps(principal.tenant_id, rid)
    return run


@router.get("/{rid}/stream")
def stream_run(
    rid: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
):
    """Replay a completed run's answer as SSE (live token streaming pending background execution)."""
    import json as _json

    from fastapi.responses import StreamingResponse

    run = store.run_get(principal.tenant_id, rid)
    if run is None:
        raise NotFoundError(f"run {rid} not found")
    answer = (run.get("output") or {}).get("answer", "")

    def frames():
        words = answer.split()
        for i in range(0, max(len(words), 1), 8):
            yield f"data: {_json.dumps({'delta': ' '.join(words[i : i + 8])})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(frames(), media_type="text/event-stream")
    run["steps"] = store.steps(principal.tenant_id, rid)
    return run


@router.get("/by-idempotency/{key}", response_model=dict)
def get_by_idempotency(
    key: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    hit = store._one(
        "SELECT id, status FROM runs WHERE tenant_id = %s AND idempotency_key = %s",
        (principal.tenant_id, key),
    )
    if hit is None:
        raise NotFoundError("no run with that idempotency key")
    return hit
