"""MCP tool framework (MC-1..MC-10, MC-13): typed schemas, risk tiers, idempotency, audit.

Servers register tools with JSON-Schema input/output contracts. The orchestrator may
only invoke registered tools (MC-2); every invocation is validated, risk-checked,
and audit-logged. Tool manifests are code-reviewed constants (anti-poisoning, MC-13).
"""

import hashlib
import json
from dataclasses import dataclass

import jsonschema

from .audit import AuditLogger
from .errors import ForbiddenError, NotFoundError

RISK_READONLY = "read-only"
RISK_REVERSIBLE = "reversible-write"
RISK_HIGH = "irreversible"


@dataclass
class ToolDef:
    server: str
    name: str
    version: str
    description: str
    input_schema: dict
    risk: str = RISK_READONLY
    idempotent: bool = True


@dataclass
class ToolCall:
    server: str
    tool: str
    arguments: dict
    idempotency_key: str = ""


class Registry:
    def __init__(self) -> None:
        self._tools: dict[tuple[str, str], ToolDef] = {}
        self._seen_keys: set[str] = set()

    def register(self, tool: ToolDef) -> None:
        self._tools[(tool.server, tool.name)] = tool

    def list(self, server: str | None = None) -> list[ToolDef]:
        return [
            t
            for (s, _), t in sorted(self._tools.items())
            if server is None or s == server
        ]

    def invoke(
        self,
        call: ToolCall,
        handler: "callable",
        tenant: str,
        actor: str,
        audit: AuditLogger,
        allow_write: bool = False,
    ) -> dict:
        tool = self._tools.get((call.server, call.tool))
        if tool is None:
            raise NotFoundError(f"tool {call.server}.{call.tool} not registered")
        try:
            jsonschema.validate(call.arguments, tool.input_schema)
        except jsonschema.ValidationError as exc:
            raise ForbiddenError(f"tool arguments invalid: {exc.message}") from exc
        if tool.risk == RISK_HIGH and not allow_write:
            raise ForbiddenError(
                f"tool {tool.name} is high-impact and requires approval"
            )
        if tool.risk != RISK_READONLY and not allow_write:
            raise ForbiddenError(f"tool {tool.name} is a write and requires approval")
        key = (
            call.idempotency_key
            or hashlib.sha256(
                json.dumps(
                    [tenant, call.server, call.tool, call.arguments], sort_keys=True
                ).encode()
            ).hexdigest()
        )
        if tool.risk != RISK_READONLY and key in self._seen_keys:
            # Writes deduplicate (AO-16); reads always re-execute and are tenant-bound by query.
            return {"deduped": True, "idempotency_key": key, "result": None}
        result = handler(tool, call.arguments)
        self._seen_keys.add(key)
        audit.record(
            tenant,
            actor,
            "tool.invoke",
            f"{call.server}.{call.tool}",
            "success",
            {"risk": tool.risk, "idempotency_key": key},
        )
        return {
            "deduped": False,
            "idempotency_key": key,
            "result": result,
            "risk": tool.risk,
        }


registry = Registry()
