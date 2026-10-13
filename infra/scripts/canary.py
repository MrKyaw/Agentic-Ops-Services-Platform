#!/usr/bin/env python3
"""Synthetic monitoring probe (OB-6): healthz + classify + kb/query. Exit 0 when all pass.

Intended for cron/scheduler. No credentials in code: reads API_URL/API_TOKEN/API_TENANT.
"""

import json
import os
import sys
import urllib.request

BASE = os.environ.get("API_URL", "http://localhost:8000")
TOKEN = os.environ.get("API_TOKEN", "")
TENANT = os.environ.get("API_TENANT", "tenant-local-01")


def call(path: str, body: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "X-Tenant-ID": TENANT,
            "Content-Type": "application/json",
        },
        method="POST" if body is not None else "GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except Exception as exc:
        return 0, {"error": str(exc)[:120]}


def check_probe() -> list[str]:
    failures = []
    status, _ = call("/healthz")
    if status != 200:
        failures.append(f"healthz:{status}")
    status, body = call(
        "/v1/intents/classify", {"text": "Why was invoice 88123 flagged?"}
    )
    if status != 200 or body.get("intent_id") != "invoice.exception.triage":
        failures.append(f"classify:{status}")
    status, body = call(
        "/v1/kb/query", {"kb_id": "kb-policy", "query": "escalation policy", "top_k": 1}
    )
    if status != 200 or body.get("abstained") is not False:
        failures.append(f"kb:{status}")
    return failures


def main() -> int:
    failures = check_probe()
    if failures:
        print("CANARY FAIL:", ", ".join(failures))
        return 1
    print("CANARY OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
