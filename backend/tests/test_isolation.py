"""Tenant isolation: A can never read or modify B's agents (MT-2, MT-3). Tenant lifecycle audited (MT-9)."""

import json


def test_agent_isolation_between_tenants(client, auth, settings):
    client.post(
        "/v1/agents",
        json={"id": "agent-a", "displayName": "A", "pattern": "react"},
        headers=auth,
    )
    # same tenant sees it
    assert client.get("/v1/agents/agent-a", headers=auth).status_code == 200
    # a principal bound to another tenant header is rejected before any data access
    forged = {"Authorization": "Bearer test-token-abc", "X-Tenant-ID": "tenant-evil-02"}
    assert client.get("/v1/agents/agent-a", headers=forged).status_code == 403
    assert client.get("/v1/agents", headers=forged).status_code == 403


def test_agent_duplicate_conflict(client, auth):
    client.post(
        "/v1/agents",
        json={"id": "dup", "displayName": "D", "pattern": "rewoo"},
        headers=auth,
    )
    resp = client.post(
        "/v1/agents",
        json={"id": "dup", "displayName": "D", "pattern": "rewoo"},
        headers=auth,
    )
    assert resp.status_code == 409


def test_tenant_lifecycle_audited(client, auth, settings):
    created = client.post(
        "/v1/tenants", json={"id": "tenant-x", "name": "X"}, headers=auth
    )
    assert created.status_code == 201
    suspended = client.post("/v1/tenants/tenant-x/suspend", headers=auth)
    assert suspended.json()["status"] == "suspended"
    assert client.get("/v1/tenants/tenant-x", headers=auth).status_code == 200
    lines = open(settings.audit_log_path, encoding="utf-8").read().strip().split("\n")
    actions = [json.loads(line)["action"] for line in lines]
    assert "tenant.create" in actions and "tenant.suspend" in actions
    hashes = [json.loads(line)["hash"] for line in lines]
    assert len(set(hashes)) == len(hashes)


def test_audit_redacts_secrets(settings):
    from app.audit import AuditLogger

    audit = AuditLogger(settings.audit_log_path)
    event = audit.record(
        "t",
        "actor",
        "test.action",
        "res",
        "success",
        {"token": "s3cr3t", "note": "fine"},
    )
    assert event["fields"]["token"] == "***"
    assert event["fields"]["note"] == "fine"
    assert "s3cr3t" not in open(settings.audit_log_path, encoding="utf-8").read()


def test_prod_dev_auth_forbidden():
    from app.config import Settings

    try:
        Settings(env="prod", auth_mode="dev", dev_token="x")
    except ValueError as exc:
        assert "forbidden" in str(exc)
    else:
        raise AssertionError("prod+dev auth must fail fast")
