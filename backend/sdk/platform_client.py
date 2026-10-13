"""Minimal typed Python client for the platform API (AP-6). Example in examples/agent_run.py."""

from __future__ import annotations

import json
import urllib.request


class PlatformClient:
    def __init__(self, base_url: str, token: str, tenant: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.tenant = tenant

    def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        idempotency_key: str = "",
    ) -> dict:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body or {}).encode()
            if body is not None or method != "GET"
            else None,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Tenant-ID": self.tenant,
                "Content-Type": "application/json",
                **({"Idempotency-Key": idempotency_key} if idempotency_key else {}),
            },
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            text = response.read().decode()
            return json.loads(text) if text else {}

    def classify(self, text: str) -> dict:
        return self._request("POST", "/v1/intents/classify", {"text": text})

    def query(self, kb_id: str, query: str, strategy: str = "auto") -> dict:
        return self._request(
            "POST",
            "/v1/kb/query",
            {"kb_id": kb_id, "query": query, "strategy": strategy},
        )

    def run(self, agent_id: str, message: str, idempotency_key: str = "") -> dict:
        return self._request(
            "POST",
            "/v1/runs/",
            {"agent_id": agent_id, "input": {"message": message}},
            idempotency_key,
        )

    def get_run(self, run_id: str) -> dict:
        return self._request("GET", f"/v1/runs/{run_id}")
