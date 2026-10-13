"""Graph RAG + summary-tree tests (RG-8, RG-10, RG-11). Neo4j tests skip when unconfigured."""

import os

import pytest

from app.graph_rag import extract_entities, extractive_summary

NEO4J_URI = os.environ.get("TEST_NEO4J_URI", os.environ.get("NEO4J_URI", ""))
NEO4J_PASSWORD = os.environ.get(
    "TEST_NEO4J_PASSWORD", os.environ.get("NEO4J_PASSWORD", "")
)
NEO4J_USER = os.environ.get("TEST_NEO4J_USER", os.environ.get("NEO4J_USER", "neo4j"))

needs_graph = pytest.mark.skipif(not NEO4J_URI, reason="graph store not configured")


def test_extractor_finds_invoice_entities():
    entities = extract_entities(
        "Why was invoice 88123 flagged? Escalation Policy applies."
    )
    assert "invoice-88123" in entities
    assert "Escalation Policy" in entities


def test_extractive_summary_selects_sentences():
    texts = [
        "Refund policy approvals depend on amount tiers. Small refunds are automatic.",
        "Unrelated filler sentence about nothing important here today.",
    ]
    summary = extractive_summary(texts, max_sentences=1)
    assert summary and summary in " ".join(texts)
    assert len(summary.split(". ")) <= 1 or summary.count(".") <= 2


@needs_graph
def test_graph_build_and_neighborhood(client, auth):
    built = client.post("/v1/graph/kb-policy/build-graph", headers=auth)
    assert built.status_code == 200, built.text[:200]
    assert built.json()["entity_mentions"] > 0
    neighbors = client.post(
        "/v1/graph/query-graph",
        json={"query": "invoice escalation policy", "top_k": 5},
        headers=auth,
    )
    assert neighbors.status_code == 200
    assert neighbors.json()["strategy"] == "graph"


def test_raptor_build_and_summary_strategy(client, auth):
    built = client.post("/v1/graph/kb-policy/summaries", headers=auth)
    assert built.status_code == 200, built.text[:200]
    assert built.json()["root"] == "kb-policy-root"
    answer = client.post(
        "/v1/kb/query",
        json={
            "kb_id": "kb-policy",
            "query": "What are the themes across escalation policies?",
            "strategy": "summary",
        },
        headers=auth,
    )
    assert answer.status_code == 200
    body = answer.json()
    assert body["strategy"] == "summary"
    assert body["abstained"] is False
    assert body["passages"], "summary strategy must cite summary nodes"


def test_hybrid_strategy_reported(client, auth):
    resp = client.post(
        "/v1/kb/query",
        json={"kb_id": "kb-policy", "query": "invoice 88123"},
        headers=auth,
    )
    assert resp.json()["strategy"] == "hybrid"


def test_embedding_backfill_and_dense_flag(client, auth):
    backfill = client.post("/v1/kb/kb-policy/embeddings", headers=auth)
    assert backfill.status_code == 200
    assert backfill.json()["dim"] == 384
    second = client.post("/v1/kb/kb-policy/embeddings", headers=auth)
    assert second.json()["embedded"] == 0  # idempotent
    hit = client.post(
        "/v1/kb/query",
        json={"kb_id": "kb-policy", "query": "escalation policy refunds", "top_k": 3},
        headers=auth,
    )
    assert hit.json()["dense"] is True
    assert hit.json()["abstained"] is False


def test_reconcile_reports_drift(client, auth):
    report = client.post("/v1/graph/kb-policy/reconcile", headers=auth).json()
    assert report["pg_chunks"] >= 3
    assert "missing_in_graph" in report and "orphan_in_graph" in report
