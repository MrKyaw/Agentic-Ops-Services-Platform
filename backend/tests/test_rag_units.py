"""Unit tests for retrieval primitives (RG): chunking, scoring, fusion, grounding, normalization."""

from app.rag import chunk_text, ground, retrieval_query, rrf, tfidf_scores


def test_chunk_empty():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_overlap_covers_text():
    words = [f"w{i}" for i in range(250)]
    chunks = chunk_text(" ".join(words), target=100, overlap=20)
    assert len(chunks) == 3
    assert chunks[0].split()[0] == "w0"
    assert chunks[-1].split()[-1] == "w249"


def test_chunk_short_text_single():
    assert chunk_text("hello world") == ["hello world"]


def test_tfidf_prefers_term_match():
    docs = [
        {"id": "a", "content": "invoice triage queue"},
        {"id": "b", "content": "refund policy tiers"},
    ]
    scores = tfidf_scores("invoice triage", docs)
    assert scores["a"] > scores["b"]


def test_tfidf_no_match_zero():
    docs = [{"id": "a", "content": "invoice triage queue"}]
    assert tfidf_scores("zzzqqq", docs)["a"] == 0.0


def test_tfidf_empty_query():
    docs = [{"id": "a", "content": "something"}]
    assert tfidf_scores("", docs)["a"] == 0.0


def test_rrf_combines_rankings():
    fused = dict(rrf([["a", "b", "c"], ["b", "a", "c"]]))
    assert fused["a"] > fused["c"]
    assert fused["b"] > fused["c"]


def test_rrf_single_list_order():
    assert [d for d, _ in rrf([["x", "y"]])] == ["x", "y"]


def test_ground_full_and_empty():
    assert ground({"invoice", "triage"}, ["invoice triage queue"]) == 1.0
    assert ground(set(), ["anything"]) == 1.0
    assert ground({"zzz"}, ["invoice triage"]) == 0.0


def test_retrieval_query_drops_ids():
    assert (
        retrieval_query("Why was invoice 88123 flagged?") == "why was invoice flagged"
    )
    assert retrieval_query("88123") == "88123"


def test_retrieval_query_keeps_meaningful():
    assert "escalation" in retrieval_query("escalation policy refunds")


def test_fts_or_fallback_multiterm(client, auth):
    # No single chunk contains ALL of these terms; AND-only search abstains.
    resp = client.post(
        "/v1/kb/query",
        json={"kb_id": "kb-policy", "query": "invoice refunds outages triage tiers"},
        headers=auth,
    )
    assert resp.json()["abstained"] is False
    assert resp.json()["passages"], "OR fallback must recover ranked passages"


def test_embed_deterministic_and_normalized():
    from app.embeddings import DIM, embed, model_card

    assert model_card()["dim"] == DIM == 384
    first, second = embed(["invoice triage queue"]), embed(["invoice triage queue"])
    assert first == second
    import math

    assert math.isclose(sum(x * x for x in first[0]), 1.0, rel_tol=1e-3)
    assert embed([]) == []
