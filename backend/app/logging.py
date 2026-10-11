"""Structured JSON logging with correlation IDs and secret redaction."""

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any

correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

REDACT_KEYS = {
    "authorization",
    "token",
    "password",
    "secret",
    "api_key",
    "apikey",
    "client_secret",
}


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: ("***" if k.lower() in REDACT_KEYS else redact(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact(v) for v in obj]
    return obj


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get() or None,
        }
        if hasattr(record, "fields") and isinstance(record.fields, dict):
            payload["fields"] = redact(record.fields)
        return json.dumps(payload)


def configure(level: str = "INFO") -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("platform")
    root.handlers = [handler]
    root.setLevel(level.upper())
    return root


def new_correlation_id(provided: str | None = None) -> str:
    cid = provided.strip() if provided else ""
    if not cid:
        cid = uuid.uuid4().hex[:16]
    correlation_id.set(cid)
    return cid
