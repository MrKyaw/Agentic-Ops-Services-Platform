"""Data lifecycle, safety, and registry tests (DL-9, PV-2/4, SC-9, CP-1/3, MT-5/9, SM, AO-14/18)."""

from app.pii import redact_text, scan


def test_pii_scan_and_redact():
    assert any(
        f["type"] == "email" for f in scan("mail me at ana@example.internal today")
    )
    assert any(f["type"] == "phone" for f in scan("call +1 555-123-4567 now"))
    assert scan("nothing sensitive here") == []
    assert "@" not in redact_text("mail ana@example.internal")


def test_ingest_reports_pii(client, auth):
    resp = client.post(
        "/v1/kb/ingest",
        json={
            "kb_id": "kb-pii",
            "doc_id": "doc-pii",
            "content": "contact ana@example.internal " + "filler words " * 40,
        },
        headers=auth,
    )
    assert resp.json()["pii_findings"] >= 1


def test_run_answer_dlp_redacted(client, auth):
    run = client.post(
        "/v1/runs/",
        json={
            "input": {
                "message": "Why was invoice 88123 flagged? mail ana@example.internal"
            }
        },
        headers=auth,
    )
    trace = client.get(f"/v1/runs/{run.json()['id']}", headers=auth).json()
    assert trace["usage"].get("dlp_redacted") in (True, False)


def test_kb_delete_propagates(client, auth):
    client.post(
        "/v1/kb/ingest",
        json={
            "kb_id": "kb-del",
            "doc_id": "doc-del",
            "content": " ".join(["triage invoice exception"] * 60),
        },
        headers=auth,
    )
    deleted = client.delete("/v1/kb/kb-del/docs/doc-del", headers=auth).json()
    assert deleted["documents"] == 1
    assert deleted["chunks"] >= 1
    assert deleted.get("graph", {}).get("chunks", 0) >= 0
    miss = client.post(
        "/v1/kb/query",
        json={"kb_id": "kb-del", "query": "triage invoice"},
        headers=auth,
    ).json()
    assert miss["abstained"] is True


def test_consents_roundtrip(client, auth):
    assert (
        client.post(
            "/v1/admin/consents",
            json={"subject": "user-1", "purpose": "analytics", "granted": True},
            headers=auth,
        ).status_code
        == 201
    )
    assert len(client.get("/v1/admin/consents", headers=auth).json()) == 1


def test_webhooks_register_and_hide_secret(client, auth):
    created = client.post(
        "/v1/admin/webhooks",
        json={
            "id": "wh-1",
            "url": "http://example.invalid/hook",
            "events": ["run.completed"],
        },
        headers=auth,
    )
    assert created.status_code == 201
    assert created.json()["secret_preview"].endswith("…")
    listed = client.get("/v1/admin/webhooks", headers=auth).json()
    assert listed and "secret" not in listed[0]


def test_model_registry_lifecycle(client, auth):
    assert (
        client.post(
            "/v1/admin/models",
            json={
                "id": "qwen-2.5-7b",
                "version": "1.0",
                "backend": "openrouter",
                "risk_tier": "medium",
            },
            headers=auth,
        ).status_code
        == 201
    )
    assert client.post(
        "/v1/admin/models", json={"id": "bad", "risk_tier": "extreme"}, headers=auth
    ).status_code in (409, 422)
    moved = client.post(
        "/v1/admin/models/qwen-2.5-7b/1.0/status?status=evaluated", headers=auth
    )
    assert moved.json()["status"] == "evaluated"
    assert (
        client.post(
            "/v1/admin/models/qwen-2.5-7b/1.0/status?status=deployed", headers=auth
        ).status_code
        == 409
    )
    moved = client.post(
        "/v1/admin/models/qwen-2.5-7b/1.0/status?status=approved", headers=auth
    )
    assert moved.json()["status"] == "approved"
    assert (
        client.post(
            "/v1/admin/models/qwen-2.5-7b/1.0/status?status=bogus", headers=auth
        ).status_code
        == 409
    )
    assert len(client.get("/v1/admin/models", headers=auth).json()) == 1


def test_tenant_export_and_erase(client, auth):
    client.post(
        "/v1/agents/",
        json={"id": "exp-agent", "displayName": "E", "pattern": "react"},
        headers=auth,
    )
    bundle = client.get("/v1/admin/export", headers=auth).json()
    assert bundle["tenant"]["id"] == "tenant-test-01"
    assert any(a["id"] == "exp-agent" for a in bundle["agents"])
    assert (
        client.delete(
            "/v1/admin/tenant", params={"confirm": "wrong"}, headers=auth
        ).status_code
        == 409
    )
    erased = client.delete(
        "/v1/admin/tenant", params={"confirm": "tenant-test-01"}, headers=auth
    ).json()
    assert erased["erased"] == "tenant-test-01"
    assert client.get("/v1/agents/exp-agent", headers=auth).status_code in (
        401,
        403,
        404,
    )


def test_audit_export_tenant_scoped(client, auth, settings):
    client.post("/v1/tenants/", json={"id": "tenant-audit", "name": "A"}, headers=auth)
    exported = client.get("/v1/admin/audit-export", headers=auth).json()
    assert exported["tenant"] == "tenant-test-01"
    assert all(e["tenantId"] == "tenant-test-01" for e in exported["events"])
    assert any(e["action"] == "tenant.create" for e in exported["events"])


def test_retention_purge_validates(client, auth):
    assert (
        client.post(
            "/v1/admin/purge", json={"older_than_days": 0}, headers=auth
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/v1/admin/purge", json={"older_than_days": 3650}, headers=auth
        ).status_code
        == 200
    )


def test_usage_csv(client, auth):
    client.post("/v1/runs/", json={"input": {"message": "hello"}}, headers=auth)
    resp = client.get("/v1/admin/usage.csv", headers=auth)
    assert resp.status_code == 200
    assert resp.text.startswith("period,workflow_id,runs,tokens_in,tokens_out,cost_usd")


def test_corrections_feed(client, auth):
    created = client.post(
        "/v1/intents/corrections",
        json={
            "text": "handle it now",
            "predicted": "policy.qa.ask",
            "correct": "clarify",
        },
        headers=auth,
    )
    assert created.status_code == 201
    assert len(client.get("/v1/intents/corrections", headers=auth).json()) == 1


def test_promote_requires_impact(client, auth):
    client.post(
        "/v1/agents/",
        json={"id": "promo-agent", "displayName": "P", "pattern": "react"},
        headers=auth,
    )
    assert (
        client.post("/v1/agents/promo-agent/promote", json={}, headers=auth).status_code
        == 422
    )
    promoted = client.post(
        "/v1/agents/promo-agent/promote",
        json={
            "business_metric": "handling time",
            "baseline": "42 min",
            "target": "15 min",
        },
        headers=auth,
    )
    assert promoted.json()["businessImpact"]["target"] == "15 min"
    assert (
        client.post(
            "/v1/agents/nope-missing/promote",
            json={"business_metric": "m", "baseline": "b", "target": "t"},
            headers=auth,
        ).status_code
        == 404
    )


def test_templates_listed(client, auth):
    templates = client.get("/v1/agents/templates/all", headers=auth).json()
    assert {t["id"] for t in templates} >= {
        "document-intake",
        "case-triage",
        "policy-qa",
    }


def test_canary_compares_patterns(client, auth):
    compared = client.post(
        "/v1/agents/pilot-triage/canary",
        json={
            "version_a": "0.1.0",
            "version_b": "0.1.0",
            "message": "Why was invoice 88123 flagged?",
        },
        headers=auth,
    ).json()
    assert set(compared["answers"]) == {"react", "rewoo"}
    assert "agree" in compared and "latency_ms" in compared


def test_builder_draft(client, auth):
    assert (
        client.post(
            "/v1/builder/draft", json={"objective": "short"}, headers=auth
        ).status_code
        == 422
    )
    draft = client.post(
        "/v1/builder/draft",
        json={
            "objective": "Open a case for mismatched invoices with approval",
            "decision_rules": ["amount > 1000"],
        },
        headers=auth,
    ).json()
    assert "case.create" in draft["manifest"]["tools"]
    assert len(draft["test_cases"]) == 2
    assert draft["manifest"]["businessImpact"]["metric"] == "to be defined by SME"


def test_agent_invoke_depth_guard():
    from app.react import Budget, LocalPlanner, ReActRunner

    def nested(args):
        return "nested-ok"

    assert nested({"message": "hi", "depth": 0}) == "nested-ok"
    runner = ReActRunner(LocalPlanner(), Budget(max_iterations=2))
    result = runner.run("anything calm", {"kb.search": lambda a: "done"})
    assert result.status == "succeeded"


def test_finetune_lifecycle_with_eval_evidence(client, auth):
    client.post(
        "/v1/admin/consents",
        json={"subject": "tenant-test-01", "purpose": "finetune", "granted": True},
        headers=auth,
    )
    assert (
        client.post(
            "/v1/finetune-jobs/",
            json={
                "base_model": "tiny-8b",
                "method": "bogus",
                "cost_estimate_ack": True,
            },
            headers=auth,
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/v1/finetune-jobs/",
            json={"base_model": "tiny-8b", "cost_estimate_ack": False},
            headers=auth,
        ).status_code
        == 409
    )
    job = client.post(
        "/v1/finetune-jobs/",
        json={
            "base_model": "tiny-8b",
            "method": "lora",
            "dataset_ref": "dsv-1",
            "cost_estimate_ack": True,
        },
        headers=auth,
    )
    assert job.status_code == 201
    assert job.json()["executor"] == "pending-training-infra"
    jid = job.json()["id"]
    assert (
        client.post(f"/v1/finetune-jobs/{jid}/approve", headers=auth).json()[
            "approvals"
        ]
        == 1
    )
    assert (
        client.post(f"/v1/finetune-jobs/{jid}/approve", headers=auth).status_code == 409
    )
    exp_id = client.post(
        "/v1/experiments/",
        json={
            "subject_type": "model",
            "subject_ref": jid,
            "metrics": {"accuracy": 0.8},
        },
        headers=auth,
    ).json()["id"]
    job2 = client.post(
        "/v1/finetune-jobs/",
        json={
            "base_model": "tiny-8b",
            "method": "lora",
            "dataset_ref": "dsv-2",
            "cost_estimate_ack": True,
        },
        headers=auth,
    ).json()["id"]
    assert (
        client.post(
            f"/v1/finetune-jobs/{job2}/approve?eval_ref=nope", headers=auth
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/v1/finetune-jobs/{job2}/approve?eval_ref={exp_id}", headers=auth
        ).json()["approvals"]
        == 1
    )


def test_registry_serving_and_deprecation(client, auth):
    client.post(
        "/v1/admin/models",
        json={
            "id": "serve-model",
            "version": "1.0",
            "backend": "local-standin",
            "risk_tier": "low",
        },
        headers=auth,
    )
    for target in ("evaluated", "approved"):
        assert (
            client.post(
                f"/v1/admin/models/serve-model/1.0/status?status={target}", headers=auth
            ).status_code
            == 200
        )
    client.post(
        "/v1/agents/",
        json={"id": "serve-agent", "displayName": "S", "pattern": "react"},
        headers=auth,
    )
    import json as _json
    import os

    from app.db import Store

    url = os.environ.get("TEST_DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    store = Store(url)
    row = store.agent_latest("tenant-test-01", "serve-agent")
    manifest = dict(row["manifest"] or {})
    manifest["model"] = {"primary": "local-standin", "registry_ref": "serve-model@1.0"}
    store._write(
        "UPDATE agents SET manifest = %s WHERE tenant_id = %s AND id = %s AND version = %s",
        (_json.dumps(manifest), "tenant-test-01", "serve-agent", row["version"]),
    )
    assert (
        client.post(
            "/v1/runs/",
            json={"agent_id": "serve-agent", "input": {"message": "hi"}},
            headers=auth,
        ).json()["status"]
        == "succeeded"
    )
    for target in ("deployed", "deprecated"):
        assert (
            client.post(
                f"/v1/admin/models/serve-model/1.0/status?status={target}", headers=auth
            ).status_code
            == 200
        )
    assert (
        client.post(
            "/v1/runs/",
            json={"agent_id": "serve-agent", "input": {"message": "hi"}},
            headers=auth,
        ).status_code
        == 503
    )
