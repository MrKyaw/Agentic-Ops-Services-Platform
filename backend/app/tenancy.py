"""Tenant context for the current request (MT-2). Set by the auth dependency after verification."""

from contextvars import ContextVar

current_tenant: ContextVar[str] = ContextVar("current_tenant", default="")
