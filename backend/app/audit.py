"""Append-only audit log with hash chaining and field redaction. Never stores secrets."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .logging import redact


class AuditLogger:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._prev = self._tail_hash()

    def _tail_hash(self) -> str:
        if not self.path.exists():
            return "GENESIS"
        last = ""
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last = line
        if not last:
            return "GENESIS"
        try:
            return json.loads(last).get("hash", "GENESIS")
        except json.JSONDecodeError:
            return "GENESIS"

    def record(
        self,
        tenant: str,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        fields: dict | None = None,
    ) -> dict:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenantId": tenant,
            "actor": actor,
            "action": action,
            "resource": resource,
            "outcome": outcome,
            "fields": redact(fields or {}),
            "prev": self._prev,
        }
        body = json.dumps(event, sort_keys=True)
        digest = hashlib.sha256(f"{self._prev}|{body}".encode()).hexdigest()
        event["hash"] = digest
        self._prev = digest
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")
        return event
