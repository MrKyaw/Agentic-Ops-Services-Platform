"""Prompt registry endpoints (PI-6, PI-7): versioned, immutable, referenced by id/version."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..audit import AuditLogger
from ..config import Settings
from ..db import Store
from ..deps import get_audit, get_settings, get_store, require_admin, require_principal
from ..errors import ConflictError, NotFoundError
from ..security import Principal

router = APIRouter()


class PromptCreate(BaseModel):
    id: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    template: str = Field(min_length=1)
    variables: list[str] = []


@router.get("/", response_model=list[dict])
def list_prompts(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store.prompt_list(principal.tenant_id)


@router.post("/", response_model=dict, status_code=201)
def create_prompt(
    body: PromptCreate,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    latest = store.prompt_latest(principal.tenant_id, body.id)
    version = (latest["version"] + 1) if latest else 1
    try:
        store.prompt_save(
            principal.tenant_id,
            body.id,
            version,
            body.template,
            body.variables,
            principal.subject,
        )
    except Exception as exc:
        raise ConflictError(str(exc)) from exc
    audit.record(
        principal.tenant_id,
        principal.subject,
        "prompt.create",
        f"{body.id}@{version}",
        "success",
        {},
    )
    return {"id": body.id, "version": version, "status": "draft"}


@router.get("/{pid}/{version}", response_model=dict)
def get_prompt(
    pid: str,
    version: int,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    hit = store.prompt_get(principal.tenant_id, pid, version)
    if hit is None:
        raise NotFoundError(f"prompt {pid}@{version} not found")
    return hit


@router.post("/{pid}/{version}/approve", response_model=dict)
def approve_prompt(
    pid: str,
    version: int,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    _ = settings
    hit = store.prompt_get(principal.tenant_id, pid, version)
    if hit is None:
        raise NotFoundError(f"prompt {pid}@{version} not found")
    store.prompt_set_status(principal.tenant_id, pid, version, "approved")
    audit.record(
        principal.tenant_id,
        principal.subject,
        "prompt.approve",
        f"{pid}@{version}",
        "success",
        {},
    )
    return {"id": pid, "version": version, "status": "approved"}
