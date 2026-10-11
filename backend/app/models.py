"""Pydantic models for the Phase 0 skeleton API."""

from typing import Literal

from pydantic import BaseModel, Field

TenantStatus = Literal["active", "suspended"]


class TenantCreate(BaseModel):
    id: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    name: str = Field(min_length=1, max_length=128)


class TenantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    status: TenantStatus | None = None


class TenantOut(BaseModel):
    id: str
    name: str
    status: TenantStatus = "active"


class AgentCreate(BaseModel):
    id: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    displayName: str = Field(min_length=1, max_length=128)
    pattern: Literal["react", "rewoo"] = "react"


class AgentOut(BaseModel):
    id: str
    tenantId: str
    displayName: str
    pattern: str
    version: str = "0.1.0"
    status: str = "draft"
