"""Tenant management endpoints. Tenant records are global but every mutation is audited."""

import logging

from fastapi import APIRouter, Depends

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_admin, require_principal
from ..errors import ConflictError, NotFoundError
from ..models import TenantCreate, TenantOut, TenantUpdate
from ..security import Principal

log = logging.getLogger("platform")
router = APIRouter()


@router.get("/", response_model=list[TenantOut])
def list_tenants(
    _: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[TenantOut]:
    return [TenantOut(**t) for t in store.tenant_list()]


@router.post("/", response_model=TenantOut, status_code=201)
def create_tenant(
    body: TenantCreate,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> TenantOut:
    if store.tenant_get(body.id):
        raise ConflictError(f"tenant {body.id} already exists")
    stored = store.tenant_upsert(body.id, body.name)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "tenant.create",
        body.id,
        "success",
        {"name": body.name},
    )
    log.info("tenant created", extra={"fields": {"tenant": body.id}})
    return TenantOut(**stored)


@router.get("/{tenant_id}", response_model=TenantOut)
def get_tenant(
    tenant_id: str,
    _: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> TenantOut:
    hit = store.tenant_get(tenant_id)
    if hit is None:
        raise NotFoundError(f"tenant {tenant_id} not found")
    return TenantOut(**hit)


@router.patch("/{tenant_id}", response_model=TenantOut)
def update_tenant(
    tenant_id: str,
    body: TenantUpdate,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> TenantOut:
    hit = store.tenant_get(tenant_id)
    if hit is None:
        raise NotFoundError(f"tenant {tenant_id} not found")
    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    stored = store.tenant_upsert(
        tenant_id, patch.get("name", hit["name"]), patch.get("status", hit["status"])
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "tenant.update",
        tenant_id,
        "success",
        patch,
    )
    return TenantOut(**stored)


@router.post("/{tenant_id}/suspend", response_model=TenantOut)
def suspend_tenant(
    tenant_id: str,
    principal: Principal = Depends(require_admin),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> TenantOut:
    hit = store.tenant_get(tenant_id)
    if hit is None:
        raise NotFoundError(f"tenant {tenant_id} not found")
    stored = store.tenant_upsert(tenant_id, hit["name"], "suspended")
    audit.record(
        principal.tenant_id,
        principal.subject,
        "tenant.suspend",
        tenant_id,
        "success",
        {},
    )
    return TenantOut(**stored)
