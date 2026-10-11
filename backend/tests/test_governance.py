"""Governance tests: RBAC matrix (SC-2), quotas (MT-4/MT-8), usage (MT-5), memory (AO-12/PV-4), kill switches (TS-3)."""

import pytest
from fastapi.testclient import TestClient

from app.audit import AuditLogger
from app.config import Settings
from app.db import Store
from app.deps import get_audit, get_settings, get_store
from app.factory import create_app


@pytest.fixture()
def member_settings(tmp_path):
    import os

    url = os.environ.get(
        "TEST_DATABASE_URL",
        os.environ.get("DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/platform"),
    )
    return Settings(
        env="local",
        auth_mode="dev",
        dev_token="member-token-xyz",
        dev_tenant="tenant-test-01",
        dev_roles="member",
        audit_log_path=str(tmp_path / "audit-member.jsonl"),
        database_url=url,
    )


@pytest.fixture()
def member_client(member_settings):
    import os

    url = os.environ.get(
        "TEST_DATABASE_URL",
        os.environ.get("DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/platform"),
    )
    member_settings = member_settings.model_copy(update={"database_url": url})
    app = create_app(member_settings)
    app.dependency_overrides[get_settings] = lambda: member_settings
    app.dependency_overrides[get_audit] = lambda: AuditLogger(
        member_settings.audit_log_path
    )
    app.dependency_overrides[get_store] = lambda: Store(member_settings.database_url)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def member_auth():
    return {"Authorization": "Bearer member-token-xyz", "X-Tenant-ID": "tenant-test-01"}


def test_rbac_matrix_admin_vs_member(client, auth, member_client, member_auth):
    # member can read and run
    assert member_client.get("/v1/agents/", headers=member_auth).status_code == 200
    run = member_client.post(
        "/v1/runs/",
        json={"input": {"message": "Why was invoice 88123 flagged?"}},
        headers=member_auth,
    )
    assert run.status_code == 201
    # member cannot manage tenants, approve prompts, decide approvals, or flip kill switches
    assert (
        member_client.post(
            "/v1/tenants/", json={"id": "t-new", "name": "N"}, headers=member_auth
        ).status_code
        == 403
    )
    client.post(
        "/v1/prompts/",
        json={"id": "p-one", "template": "hi {x}", "variables": ["x"]},
        headers=auth,
    )
    assert (
        member_client.post(
            "/v1/prompts/p-one/1/approve", headers=member_auth
        ).status_code
        == 403
    )
    assert client.post("/v1/prompts/p-one/1/approve", headers=auth).status_code == 200
    assert (
        member_client.post(
            "/v1/admin/kill-switch",
            json={"scope": "platform", "on": True},
            headers=member_auth,
        ).status_code
        == 403
    )


def test_quota_429_and_usage(client, auth):
    client.put("/v1/admin/quotas", json={"rpm": 2, "runs_per_day": 100}, headers=auth)
    from app import quotas

    quotas.STATE.buckets.clear()
    headers = dict(auth)
    assert (
        client.post(
            "/v1/runs/", json={"input": {"message": "hi one"}}, headers=headers
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/v1/runs/", json={"input": {"message": "hi two"}}, headers=headers
        ).status_code
        == 201
    )
    limited = client.post(
        "/v1/runs/", json={"input": {"message": "hi three"}}, headers=headers
    )
    assert limited.status_code == 429
    assert limited.json()["title"] == "Too Many Requests"
    quotas.STATE.buckets.clear()
    client.put("/v1/admin/quotas", json={"rpm": 60, "runs_per_day": 1000}, headers=auth)
    summary = client.get("/v1/usage/summary", headers=auth).json()
    assert summary["runs"] >= 2
    assert summary["cost_usd"] > 0


def test_memory_round_trip_and_erase(client, auth):
    client.post(
        "/v1/runs/",
        json={
            "input": {
                "message": "Why was invoice 88123 flagged?",
                "session_id": "sess-1",
            }
        },
        headers=auth,
    )
    turns = client.get(
        "/v1/memory/pilot-triage", params={"session_id": "sess-1"}, headers=auth
    ).json()
    assert [t["role"] for t in turns] == ["user", "assistant"]
    cleared = client.delete(
        "/v1/memory/pilot-triage", params={"session_id": "sess-1"}, headers=auth
    ).json()
    assert cleared["cleared"] == 2
    assert (
        client.get(
            "/v1/memory/pilot-triage", params={"session_id": "sess-1"}, headers=auth
        ).json()
        == []
    )


def test_kill_switch_blocks_runs(client, auth):
    client.post(
        "/v1/admin/kill-switch",
        json={"scope": "tenant:tenant-test-01", "on": True},
        headers=auth,
    )
    try:
        resp = client.post(
            "/v1/runs/", json={"input": {"message": "hello"}}, headers=auth
        )
        assert resp.status_code == 503
    finally:
        client.post(
            "/v1/admin/kill-switch",
            json={"scope": "tenant:tenant-test-01", "on": False},
            headers=auth,
        )
    assert (
        client.post(
            "/v1/runs/", json={"input": {"message": "hello"}}, headers=auth
        ).status_code
        == 201
    )


def test_output_schema_validation(client, auth):
    # create agent then stamp a strict schema directly (manifest API arrives with builder UI)
    client.post(
        "/v1/agents/",
        json={"id": "strict-agent", "displayName": "S", "pattern": "react"},
        headers=auth,
    )
    import os

    from app.db import Store

    url = os.environ.get(
        "TEST_DATABASE_URL",
        os.environ.get("DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/platform"),
    )
    s = Store(url)
    row = s.agent_latest("tenant-test-01", "strict-agent")
    manifest = dict(row["manifest"] or {})
    manifest["output_schema"] = {
        "type": "object",
        "required": ["answer"],
        "properties": {"answer": {"type": "integer"}},
    }
    s._write(
        "UPDATE agents SET manifest = %s WHERE tenant_id = %s AND id = %s AND version = %s",
        (
            __import__("json").dumps(manifest),
            "tenant-test-01",
            "strict-agent",
            row["version"],
        ),
    )
    resp = client.post(
        "/v1/runs/",
        json={
            "agent_id": "strict-agent",
            "input": {"message": "Why was invoice 88123 flagged?"},
        },
        headers=auth,
    )
    assert resp.json()["status"] == "failed"
    assert resp.json()["reason"] == "output schema violation"
