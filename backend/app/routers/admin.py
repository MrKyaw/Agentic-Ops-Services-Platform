"""Tenant administration: quotas (MT-4), kill switches (TS-3). Platform/tenant admins only."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..audit import AuditLogger
from ..config import Settings
from ..db import Store
from ..deps import get_audit, get_settings, get_store, require_admin, require_principal
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


class ConsentIn(BaseModel):
    subject: str
    purpose: str
    granted: bool = True
    policy_version: str = "v1"


class WebhookIn(BaseModel):
    id: str
    url: str
    events: list[str] = []


class ModelIn(BaseModel):
    id: str
    version: str = "1.0"
    backend: str = "local-standin"
    risk_tier: str = "low"
    metadata: dict = {}


class PurgeIn(BaseModel):
    older_than_days: int = 90


@router.post("/consents", response_model=dict, status_code=201)
def set_consent(
    body: ConsentIn,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    store.consent_set(
        principal.tenant_id,
        body.subject,
        body.purpose,
        body.granted,
        body.policy_version,
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "consent.set",
        body.subject,
        "success",
        {"purpose": body.purpose},
    )
    return {"subject": body.subject, "purpose": body.purpose, "granted": body.granted}


@router.get("/consents", response_model=list[dict])
def list_consents(
    principal: Principal = Depends(require_admin), store: Store = Depends(get_store)
) -> list[dict]:
    return store.consent_list(principal.tenant_id)


@router.post("/webhooks", response_model=dict, status_code=201)
def add_webhook(
    body: WebhookIn,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    import secrets as _secrets

    secret = _secrets.token_urlsafe(24)
    store.webhook_add(principal.tenant_id, body.id, body.url, body.events, secret)
    audit.record(
        principal.tenant_id, principal.subject, "webhook.add", body.id, "success", {}
    )
    return {"id": body.id, "secret_preview": secret[:4] + "…"}


@router.get("/webhooks", response_model=list[dict])
def list_webhooks(
    principal: Principal = Depends(require_admin), store: Store = Depends(get_store)
) -> list[dict]:
    return [
        {k: v for k, v in hook.items() if k != "secret"}
        for hook in store.webhook_list(principal.tenant_id)
    ]


@router.post("/models", response_model=dict, status_code=201)
def register_model(
    body: ModelIn,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    if body.risk_tier not in ("low", "medium", "high"):
        from ..errors import ConflictError

        raise ConflictError("risk_tier must be low, medium, or high")
    store.model_register(
        principal.tenant_id,
        body.id,
        body.version,
        body.backend,
        body.risk_tier,
        body.metadata,
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "model.register",
        f"{body.id}@{body.version}",
        "success",
        {},
    )
    return {"id": body.id, "version": body.version, "status": "candidate"}


@router.get("/models", response_model=list[dict])
def list_models(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store.model_list(principal.tenant_id)


TRANSITIONS = {
    "candidate": {"evaluated"},
    "evaluated": {"approved", "deprecated"},
    "approved": {"deployed", "deprecated"},
    "deployed": {"deprecated"},
    "deprecated": {"retired"},
    "retired": set(),
}


@router.post("/models/{mid}/{version}/status", response_model=dict)
def model_status(
    mid: str,
    version: str,
    status: str,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    from ..errors import ConflictError, NotFoundError

    if status not in TRANSITIONS:
        raise ConflictError(f"status must be one of {sorted(TRANSITIONS)}")
    current = next(
        (
            m
            for m in store.model_list(principal.tenant_id)
            if m["id"] == mid and m["version"] == version
        ),
        None,
    )
    if current is None:
        raise NotFoundError(f"model {mid}@{version} not found")
    if status not in TRANSITIONS[current["status"]]:
        raise ConflictError(f"illegal transition {current['status']} -> {status}")
    store.model_set_status(principal.tenant_id, mid, version, status)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "model.status",
        f"{mid}@{version}",
        "success",
        {"status": status},
    )
    return {"id": mid, "version": version, "status": status}


@router.get("/export", response_model=dict)
def export_tenant(
    principal: Principal = Depends(require_admin), store: Store = Depends(get_store)
) -> dict:
    return store.tenant_export(principal.tenant_id)


@router.delete("/tenant", response_model=dict)
def erase_tenant(
    confirm: str = "",
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    if confirm != principal.tenant_id:
        from ..errors import ConflictError

        raise ConflictError("confirm must equal your tenant id")
    counts = store.tenant_erase(principal.tenant_id)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "tenant.erase",
        principal.tenant_id,
        "success",
        {},
    )
    return {"erased": principal.tenant_id, "tables": counts}


@router.get("/audit-export")
def audit_export(
    principal: Principal = Depends(require_admin),
    settings: Settings = Depends(get_settings),
):
    from pathlib import Path

    from fastapi.responses import JSONResponse

    path = Path(settings.audit_log_path)
    events = []
    if path.exists():
        import json as _json

        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = _json.loads(line)
            except ValueError:
                continue
            if event.get("tenantId") == principal.tenant_id:
                events.append(event)
    return JSONResponse({"tenant": principal.tenant_id, "events": events})


@router.post("/purge", response_model=dict)
def purge_retention(
    body: PurgeIn,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    if body.older_than_days < 1:
        from ..errors import ConflictError

        raise ConflictError("older_than_days must be >= 1")
    memories = store._write_and_count(
        "DELETE FROM memories WHERE tenant_id = %s AND created_at < now() - (%s || ' days')::interval",
        (principal.tenant_id, str(body.older_than_days)),
    )
    runs = store._write_and_count(
        "DELETE FROM runs WHERE tenant_id = %s AND created_at < now() - (%s || ' days')::interval AND status IN ('succeeded','failed','rejected')",
        (principal.tenant_id, str(body.older_than_days)),
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "retention.purge",
        principal.tenant_id,
        "success",
        {"days": body.older_than_days},
    )
    return {"memories": memories, "runs": runs}


@router.get("/usage.csv")
def usage_csv(
    principal: Principal = Depends(require_admin), store: Store = Depends(get_store)
):
    from datetime import datetime, timezone

    from fastapi.responses import PlainTextResponse

    rows = store.usage_get(
        principal.tenant_id, datetime.now(timezone.utc).date().isoformat()
    )
    lines = ["period,workflow_id,runs,tokens_in,tokens_out,cost_usd"]
    lines += [
        f"{r['period']},{r['workflow_id']},{r['runs']},{r['tokens_in']},{r['tokens_out']},{r['cost_usd']}"
        for r in rows
    ]
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/csv")


class FlagIn(BaseModel):
    key: str
    value: dict = {}


@router.get("/flags", response_model=list[dict])
def list_flags(
    principal: Principal = Depends(require_admin), store: Store = Depends(get_store)
) -> list[dict]:
    return store.flag_list(principal.tenant_id)


@router.put("/flags", response_model=dict)
def set_flag(
    body: FlagIn,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    store.flag_set(principal.tenant_id, body.key, body.value)
    audit.record(
        principal.tenant_id, principal.subject, "flag.set", body.key, "success", {}
    )
    return {"key": body.key, "value": body.value}
