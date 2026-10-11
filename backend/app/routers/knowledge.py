"""Knowledge base endpoints (RG-1..RG-7, RG-11, RG-13..RG-15): ingest + routed query with citations."""

import math
import re
from collections import Counter

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..audit import AuditLogger
from ..config import Settings
from ..db import Store
from ..deps import get_audit, get_settings, get_store, require_principal
from ..errors import UnavailableError
from ..rag import ground, retrieval_query, rrf, tfidf_scores
from ..security import Principal

router = APIRouter()


def select_strategy(query: str, requested: str, summaries_built: bool) -> str:
    """Declarative strategy router v1 (RG-11): thematic queries prefer summaries."""
    if requested in ("hybrid", "summary", "graph"):
        return requested
    lowered = query.lower()
    if (
        "theme" in lowered or "summar" in lowered or len(query.split()) > 12
    ) and summaries_built:
        return "summary"
    if "relat" in lowered or "connect" in lowered:
        return "graph"
    return "hybrid"


class IngestIn(BaseModel):
    kb_id: str = "kb-policy"
    doc_id: str
    title: str = ""
    content: str = Field(min_length=1)
    acl: list[str] = []


class QueryIn(BaseModel):
    kb_id: str = "kb-policy"
    query: str = Field(min_length=1)
    top_k: int = 5
    citations: bool = True
    strategy: str = "auto"  # auto | hybrid | summary | graph


@router.post("/ingest", response_model=dict, status_code=201)
def ingest(
    body: IngestIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    from ..rag import chunk_text

    store.doc_save(
        principal.tenant_id,
        body.doc_id,
        body.kb_id,
        body.title,
        body.acl,
        source="api-ingest-v1",
    )
    chunks = chunk_text(body.content)
    for seq, text in enumerate(chunks):
        store.chunk_save(
            principal.tenant_id,
            f"{body.doc_id}-c{seq}",
            body.kb_id,
            body.doc_id,
            seq,
            text,
            {"source": "api-ingest-v1"},
        )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "kb.ingest",
        body.doc_id,
        "success",
        {"chunks": len(chunks)},
    )
    return {"doc_id": body.doc_id, "chunks": len(chunks)}


def _rank_summaries(query: str, summaries: list[dict]) -> list[tuple[float, dict]]:
    qterms = Counter(re.findall(r"[a-z0-9]+", query.lower()))

    def cosine(centroid: dict) -> float:
        dot = sum(qterms[t] * w for t, w in centroid.items() if t in qterms)
        qn = math.sqrt(sum(v * v for v in qterms.values()))
        cn = math.sqrt(sum(w * w for w in centroid.values()))
        return dot / (qn * cn) if qn and cn else 0.0

    ranked = sorted(
        ((cosine(s.get("centroid") or {}), s) for s in summaries),
        key=lambda kv: kv[0],
        reverse=True,
    )
    return [(score, s) for score, s in ranked if score > 0]


@router.post("/query", response_model=dict)
def query(
    body: QueryIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
) -> dict:
    top_k = max(1, min(body.top_k, 20))
    summaries = store.summary_list(principal.tenant_id, body.kb_id, 0)
    strategy = select_strategy(body.query, body.strategy, bool(summaries))
    if strategy == "graph":
        from ..deps import get_graph as _get_graph

        graph = _get_graph(settings)
        if graph is None:
            raise UnavailableError("graph store not configured (NEO4J_PASSWORD unset)")
        try:
            neighbors = graph.neighborhood(principal.tenant_id, body.query, top_k)
        finally:
            graph.close()
        return {
            "strategy": "graph",
            "abstained": not neighbors,
            "neighbors": neighbors,
            "passages": [],
        }
    if strategy == "summary":
        scored = _rank_summaries(body.query, summaries)[:top_k]
        if not scored:
            return {
                "strategy": "summary",
                "answer": None,
                "abstained": True,
                "reason": "summaries not built",
                "passages": [],
            }
        answer = " ".join(s["summary"] for _, s in scored[:2])
        return {
            "strategy": "summary",
            "answer": answer,
            "abstained": False,
            "faithfulness": round(
                ground(
                    set(body.query.lower().split()), [s["summary"] for _, s in scored]
                ),
                3,
            ),
            "passages": [
                {"chunk_id": s["id"], "document_id": s["id"], "content": s["summary"]}
                for _, s in scored
            ]
            if body.citations
            else [],
        }
    fts_hits = store.chunk_search_fts(
        principal.tenant_id, body.kb_id, retrieval_query(body.query), top_k * 2
    )
    docs = [{"id": h["id"], "content": h["content"]} for h in fts_hits]
    tfidf = tfidf_scores(body.query, docs)
    tfidf_ranked = [
        doc_id
        for doc_id, _ in sorted(tfidf.items(), key=lambda kv: kv[1], reverse=True)
    ]
    fts_ranked = [h["id"] for h in fts_hits]
    fused = rrf([fts_ranked, tfidf_ranked])[:top_k]
    by_id = {h["id"]: h for h in fts_hits}
    passages = [
        {
            "chunk_id": did,
            "document_id": by_id[did]["document_id"],
            "content": by_id[did]["content"],
            "score": round(s, 4),
        }
        for did, s in fused
        if did in by_id
    ]
    # Grounding abstention (RG-15): refuse when nothing relevant retrieved.
    if not passages:
        return {
            "answer": None,
            "abstained": True,
            "reason": "insufficient evidence",
            "passages": [],
        }
    answer = " ".join(p["content"] for p in passages[:2])
    faith = ground(set(body.query.lower().split()), [p["content"] for p in passages])
    return {
        "strategy": "hybrid",
        "answer": answer,
        "abstained": False,
        "faithfulness": round(faith, 3),
        "passages": passages if body.citations else [],
    }
