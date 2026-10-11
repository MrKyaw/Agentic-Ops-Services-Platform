"""Shared FastAPI dependencies: authn, tenant binding, RBAC."""

from fastapi import Depends, Header

from .audit import AuditLogger
from .config import Settings, settings
from .db import Store
from .errors import ForbiddenError
from .security import Principal, authenticate
from .tenancy import current_tenant


def get_settings() -> Settings:
    return settings


def get_audit(s: Settings = Depends(get_settings)) -> AuditLogger:
    return AuditLogger(s.audit_log_path)


def get_store(s: Settings = Depends(get_settings)) -> Store:
    return Store(s.database_url)


def get_graph(s: Settings = Depends(get_settings)):
    if not s.neo4j_uri:
        return None
    from .graph_rag import GraphStore

    return GraphStore(s.neo4j_uri, s.neo4j_user, s.neo4j_password)


def require_principal(
    authorization: str | None = Header(default=None),
    tenant_header: str | None = Header(default=None, alias="X-Tenant-ID"),
    s: Settings = Depends(get_settings),
) -> Principal:
    principal = authenticate(authorization, s)
    if not tenant_header:
        raise ForbiddenError("X-Tenant-ID header is required")
    if tenant_header != principal.tenant_id:
        raise ForbiddenError("tenant header does not match authenticated tenant")
    current_tenant.set(principal.tenant_id)
    return principal


def require_admin(principal: Principal = Depends(require_principal)) -> Principal:
    if (
        "tenant-admin" not in principal.roles
        and "platform-admin" not in principal.roles
    ):
        raise ForbiddenError("tenant-admin role is required")
    return principal
