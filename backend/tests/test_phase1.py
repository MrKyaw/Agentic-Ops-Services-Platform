"""Phase 1 journey tests: classify → run → trace → approve (PI, AO, RG, MC)."""


def test_classify_matched_and_dedup(client, auth):
    first = client.post(
        "/v1/intents/classify",
        json={"text": "Why was invoice 88123 flagged?", "instruction_id": "ins-1"},
        headers=auth,
    )
    assert first.status_code == 200
    body = first.json()
    assert body["intent_id"] == "invoice.exception.triage"
    assert body["resolution"] == "matched"
    assert body["deduplicated"] is False
    second = client.post(
        "/v1/intents/classify",
        json={"text": "Why was invoice 88123 flagged?", "instruction_id": "ins-1"},
        headers=auth,
    )
    assert second.json()["deduplicated"] is True


def test_classify_ambiguous_clarifies(client, auth):
    resp = client.post("/v1/intents/classify", json={"text": "handle it"}, headers=auth)
    assert resp.json()["resolution"] in ("clarified", "no_match")


def test_prompt_registry_versioned(client, auth):
    created = client.post(
        "/v1/prompts/",
        json={"id": "triage-system", "template": "You triage {x}", "variables": ["x"]},
        headers=auth,
    )
    assert created.status_code == 201
    assert created.json()["version"] == 1
    again = client.post(
        "/v1/prompts/",
        json={"id": "triage-system", "template": "v2 {x}", "variables": ["x"]},
        headers=auth,
    )
    assert again.json()["version"] == 2
    fetched = client.get("/v1/prompts/triage-system/1", headers=auth)
    assert fetched.json()["template"] == "You triage {x}"
    approved = client.post("/v1/prompts/triage-system/2/approve", headers=auth)
    assert approved.json()["status"] == "approved"


def test_kb_query_citations_and_abstention(client, auth):
    hit = client.post(
        "/v1/kb/query",
        json={"kb_id": "kb-policy", "query": "escalation policy refunds", "top_k": 3},
        headers=auth,
    )
    assert hit.status_code == 200
    body = hit.json()
    assert body["abstained"] is False
    assert len(body["passages"]) >= 1
    assert all("content" in p and "document_id" in p for p in body["passages"])
    miss = client.post(
        "/v1/kb/query",
        json={"kb_id": "kb-policy", "query": "zzzqqq nonexistent", "top_k": 3},
        headers=auth,
    )
    assert miss.json()["abstained"] is True


def test_react_run_end_to_end_with_trace(client, auth):
    created = client.post(
        "/v1/runs/",
        json={
            "agent_id": "pilot-triage",
            "input": {"message": "Why was invoice 88123 flagged?"},
        },
        headers={**auth, "Idempotency-Key": "run-key-1"},
    )
    assert created.status_code == 201
    rid = created.json()["id"]
    assert created.json()["status"] == "succeeded"
    assert "88123" in created.json()["answer"] or "flagged" in created.json()["answer"]
    trace = client.get(f"/v1/runs/{rid}", headers=auth)
    kinds = [s["kind"] for s in trace.json()["steps"]]
    assert kinds[0] == "intent"
    assert "tool" in kinds and "model" in kinds
    replay = client.post(
        "/v1/runs/",
        json={
            "agent_id": "pilot-triage",
            "input": {"message": "Why was invoice 88123 flagged?"},
        },
        headers={**auth, "Idempotency-Key": "run-key-1"},
    )
    assert replay.json()["deduped"] is True
    assert replay.json()["id"] == rid


def test_hitl_approval_flow(client, auth):
    created = client.post(
        "/v1/runs/",
        json={
            "agent_id": "pilot-triage",
            "input": {"message": "Please open a case for invoice 1024"},
        },
        headers=auth,
    )
    assert created.json()["status"] == "waiting_approval"
    aid = created.json()["approval_id"]
    inbox = client.get("/v1/approvals/", headers=auth)
    assert any(a["id"] == aid for a in inbox.json())
    decided = client.post(
        f"/v1/approvals/{aid}/decide", json={"decision": "approved"}, headers=auth
    )
    assert decided.json()["status"] == "approved"
    run = client.get(f"/v1/runs/{created.json()['id']}", headers=auth)
    assert run.json()["status"] == "succeeded"


def test_tool_poisoning_rejected(
    client, auth
):  # Unregistered tools are unreachable through the API (MC-2/MC-13): runs only use the registry.
    from app.mcp import ToolCall, registry

    from app.audit import AuditLogger

    audit = AuditLogger("/tmp/poison-audit.jsonl")
    try:
        registry.invoke(
            ToolCall("evil", "drop", {}),
            lambda t, a: {},
            "tenant-test-01",
            "tester",
            audit,
        )
    except Exception as exc:
        assert "not registered" in str(exc)
    else:
        raise AssertionError("unregistered tool must be rejected")


def test_rewoo_run_plan_solve_trace(client, auth):
    client.post(
        "/v1/agents/",
        json={"id": "rewoo-agent", "displayName": "R", "pattern": "rewoo"},
        headers=auth,
    )
    created = client.post(
        "/v1/runs/",
        json={
            "agent_id": "rewoo-agent",
            "input": {"message": "Why was invoice 88123 flagged?"},
        },
        headers=auth,
    )
    assert created.json()["status"] == "succeeded"
    assert "Plan:" in created.json()["answer"]
    trace = client.get(f"/v1/runs/{created.json()['id']}", headers=auth).json()
    kinds = [s["kind"] for s in trace["steps"]]
    assert kinds[0] == "intent"
    assert kinds.count("model") == 1  # plan only: fewer model calls than ReAct
    assert "Evidence:" in created.json()["answer"]


def test_run_stream_sse_frames(client, auth):
    created = client.post(
        "/v1/runs/",
        json={"input": {"message": "Why was invoice 88123 flagged?"}},
        headers=auth,
    )
    stream = client.get(f"/v1/runs/{created.json()['id']}/stream", headers=auth)
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    assert "event: done" in stream.text
    assert "data:" in stream.text
    assert client.get("/v1/runs/nope-missing/stream", headers=auth).status_code == 404


def test_experiments_record_list_compare(client, auth):
    first = client.post(
        "/v1/experiments/",
        json={
            "subject_type": "prompt",
            "subject_ref": "triage-system@2",
            "params": {"k": 5},
            "metrics": {"accuracy": 0.8},
        },
        headers=auth,
    )
    assert first.status_code == 201
    second = client.post(
        "/v1/experiments/",
        json={
            "subject_type": "prompt",
            "subject_ref": "triage-system@3",
            "params": {"k": 8},
            "metrics": {"accuracy": 0.85},
        },
        headers=auth,
    )
    listed = client.get("/v1/experiments/?subject_type=prompt", headers=auth).json()
    assert len(listed) == 2
    compared = client.get(
        f"/v1/experiments/compare?ids={first.json()['id']},{second.json()['id']}",
        headers=auth,
    ).json()
    assert compared["metric_keys"] == ["accuracy"]
    assert [row["accuracy"] for row in compared["table"]] == [0.8, 0.85]
    assert (
        client.post(
            "/v1/experiments/", json={"subject_type": "nope"}, headers=auth
        ).status_code
        == 422
    )
