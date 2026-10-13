"""API edge cases: validation (422), not-found (404), conflicts (409), empty states."""


def test_tenant_id_pattern_rejected(client, auth):
    resp = client.post(
        "/v1/tenants/", json={"id": "BAD ID!", "name": "X"}, headers=auth
    )
    assert resp.status_code == 422


def test_tenant_duplicate_conflict(client, auth):
    client.post("/v1/tenants/", json={"id": "tenant-dup", "name": "D"}, headers=auth)
    assert (
        client.post(
            "/v1/tenants/", json={"id": "tenant-dup", "name": "D"}, headers=auth
        ).status_code
        == 409
    )


def test_tenant_missing_404(client, auth):
    assert client.get("/v1/tenants/nope-missing", headers=auth).status_code == 404
    assert (
        client.post("/v1/tenants/nope-missing/suspend", headers=auth).status_code == 404
    )


def test_tenant_update_name(client, auth):
    client.post("/v1/tenants/", json={"id": "tenant-u", "name": "Old"}, headers=auth)
    updated = client.patch("/v1/tenants/tenant-u", json={"name": "New"}, headers=auth)
    assert updated.status_code == 200
    assert updated.json()["name"] == "New"


def test_agent_pattern_rejected(client, auth):
    resp = client.post(
        "/v1/agents/",
        json={"id": "bad-agent", "displayName": "B", "pattern": "swarm"},
        headers=auth,
    )
    assert resp.status_code == 422


def test_agent_missing_404(client, auth):
    assert client.get("/v1/agents/nope-missing", headers=auth).status_code == 404


def test_run_missing_404(client, auth):
    assert client.get("/v1/runs/nope-missing", headers=auth).status_code == 404


def test_idempotency_lookup_missing_404(client, auth):
    assert (
        client.get("/v1/runs/by-idempotency/never-used", headers=auth).status_code
        == 404
    )


def test_approval_missing_404(client, auth):
    assert (
        client.post(
            "/v1/approvals/nope-missing/decide",
            json={"decision": "approved"},
            headers=auth,
        ).status_code
        == 404
    )


def test_approval_bad_decision_409(client, auth):
    run = client.post(
        "/v1/runs/",
        json={"input": {"message": "Please open a case for invoice 5"}},
        headers=auth,
    )
    aid = run.json()["approval_id"]
    assert client.post(
        f"/v1/approvals/{aid}/decide", json={"decision": "maybe"}, headers=auth
    ).status_code in (409, 422)


def test_approval_double_decide_409(client, auth):
    run = client.post(
        "/v1/runs/",
        json={"input": {"message": "Please open a case for invoice 6"}},
        headers=auth,
    )
    aid = run.json()["approval_id"]
    assert (
        client.post(
            f"/v1/approvals/{aid}/decide", json={"decision": "rejected"}, headers=auth
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/v1/approvals/{aid}/decide", json={"decision": "approved"}, headers=auth
        ).status_code
        == 409
    )


def test_approval_reject_marks_run(client, auth):
    run = client.post(
        "/v1/runs/",
        json={"input": {"message": "Please open a case for invoice 7"}},
        headers=auth,
    )
    aid = run.json()["approval_id"]
    client.post(
        f"/v1/approvals/{aid}/decide", json={"decision": "rejected"}, headers=auth
    )
    assert (
        client.get(f"/v1/runs/{run.json()['id']}", headers=auth).json()["status"]
        == "rejected"
    )


def test_prompt_missing_404(client, auth):
    assert client.get("/v1/prompts/nope-missing/9", headers=auth).status_code == 404
    assert (
        client.post("/v1/prompts/nope-missing/9/approve", headers=auth).status_code
        == 404
    )


def test_prompt_empty_template_422(client, auth):
    assert (
        client.post(
            "/v1/prompts/", json={"id": "bad-prompt", "template": ""}, headers=auth
        ).status_code
        == 422
    )


def test_kb_ingest_and_query_roundtrip(client, auth):
    created = client.post(
        "/v1/kb/ingest",
        json={
            "kb_id": "kb-test",
            "doc_id": "doc-1",
            "title": "T",
            "content": " ".join(["alpha beta gamma"] * 60),
        },
        headers=auth,
    )
    assert created.status_code == 201
    assert created.json()["chunks"] >= 2
    hit = client.post(
        "/v1/kb/query", json={"kb_id": "kb-test", "query": "alpha beta"}, headers=auth
    )
    assert hit.json()["abstained"] is False


def test_kb_ingest_empty_422(client, auth):
    assert (
        client.post(
            "/v1/kb/ingest",
            json={"kb_id": "k", "doc_id": "d", "content": ""},
            headers=auth,
        ).status_code
        == 422
    )


def test_query_top_k_clamped(client, auth):
    resp = client.post(
        "/v1/kb/query",
        json={"kb_id": "kb-policy", "query": "policy", "top_k": 500},
        headers=auth,
    )
    assert resp.status_code == 200
    assert len(resp.json()["passages"]) <= 20


def test_query_without_citations(client, auth):
    resp = client.post(
        "/v1/kb/query",
        json={"kb_id": "kb-policy", "query": "policy refunds", "citations": False},
        headers=auth,
    )
    assert resp.json()["passages"] == []
    assert resp.json()["abstained"] is False


def test_usage_empty_for_fresh_tenant(client, auth):
    assert client.get("/v1/usage/", headers=auth).status_code == 200


def test_memory_empty_for_unknown_session(client, auth):
    assert (
        client.get(
            "/v1/memory/none-agent", params={"session_id": "nope"}, headers=auth
        ).json()
        == []
    )


def test_memory_clear_empty(client, auth):
    assert client.delete(
        "/v1/memory/none-agent", params={"session_id": "nope"}, headers=auth
    ).json() == {"cleared": 0}


def test_quotas_clamped_minimum(client, auth):
    assert client.put(
        "/v1/admin/quotas", json={"rpm": 0, "runs_per_day": -5}, headers=auth
    ).json() == {
        "rpm": 1,
        "runs_per_day": 1,
    }
    client.put("/v1/admin/quotas", json={"rpm": 60, "runs_per_day": 1000}, headers=auth)


def test_kill_invalid_scope_409(client, auth):
    assert (
        client.post(
            "/v1/admin/kill-switch",
            json={"scope": "planet:earth", "on": True},
            headers=auth,
        ).status_code
        == 409
    )


def test_intents_seeded_three(client, auth):
    assert len(client.get("/v1/intents/", headers=auth).json()) == 3


def test_classify_gibberish_no_match(client, auth):
    body = client.post(
        "/v1/intents/classify",
        json={"text": "qxwrt zplunk florp blarg quux"},
        headers=auth,
    ).json()
    assert body["resolution"] == "no_match"


def test_runs_list_grows(client, auth):
    before = len(client.get("/v1/runs/", headers=auth).json())
    client.post("/v1/runs/", json={"input": {"message": "hello"}}, headers=auth)
    assert len(client.get("/v1/runs/", headers=auth).json()) == before + 1


def test_problem_shape_on_404(client, auth):
    body = client.get("/v1/runs/nope-missing", headers=auth).json()
    assert {"type", "title", "status", "detail", "instance", "correlationId"} <= set(
        body
    )
    assert body["status"] == 404
