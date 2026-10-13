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
from ..errors import NotFoundError, UnavailableError
from ..rag import ground, retrieval_query, rrf, tfidf_scores
from ..security import Principal

router = APIRouter()


def select_strategy(query: str, requested: str, summaries_built: bool) -> str:
    """Declarative strategy router v1 (RG-11): thematic queries prefer summaries."""
    if requested in ("hybrid", "summary", "graph", "dual"):
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
    classification: str = "internal"  # DG-4: classification recorded at onboarding


class QueryIn(BaseModel):
    kb_id: str = "kb-policy"
    query: str = Field(min_length=1)
    top_k: int = 5
    citations: bool = True
    strategy: str = "auto"  # auto | hybrid | summary | graph | dual
    config: str = (
        ""  # versioned retrieval config id (RG-13); overrides strategy/top_k when set
    )
    max_classification: str = "restricted"  # PV-1: retrieve at or below this class only


@router.post("/ingest", response_model=dict, status_code=201)
def ingest(
    body: IngestIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    from ..pii import scan
    from ..rag import chunk_text

    findings = scan(body.content)
    allowed_classifications = {"internal", "public", "confidential", "restricted"}
    classification = (
        body.classification
        if body.classification in allowed_classifications
        else "internal"
    )
    store.doc_save(
        principal.tenant_id,
        body.doc_id,
        body.kb_id,
        body.title,
        body.acl,
        source="api-ingest-v1",
        classification=classification,
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
        {"chunks": len(chunks), "pii_findings": len(findings)},
    )
    return {"doc_id": body.doc_id, "chunks": len(chunks), "pii_findings": len(findings)}


@router.delete("/{kb_id}/docs/{doc_id}", response_model=dict)
def delete_doc(
    kb_id: str,
    doc_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    """Erasure propagation (DL-9, PV-4): chunks, embeddings, summaries, graph nodes."""
    result = store.kb_delete_doc(principal.tenant_id, kb_id, doc_id)
    graph_deleted: dict = {}
    if settings.neo4j_uri:
        from ..deps import get_graph as _get_graph

        graph = _get_graph(settings)
        try:
            graph_deleted = (
                graph.delete_doc(principal.tenant_id, kb_id, doc_id) if graph else {}
            )
        finally:
            if graph:
                graph.close()
    audit.record(
        principal.tenant_id, principal.subject, "kb.delete", doc_id, "success", result
    )
    return {**result, "graph": graph_deleted}


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


@router.post("/{kb_id}/embeddings", response_model=dict)
def backfill_embeddings(
    kb_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    from ..embeddings import embed, model_card

    missing = store.chunks_missing_embeddings(principal.tenant_id, kb_id)
    if missing:
        vectors = embed([c["content"] for c in missing])
        for chunk, vector in zip(missing, vectors):
            store.chunk_set_embedding(principal.tenant_id, chunk["id"], vector)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "kb.embed",
        kb_id,
        "success",
        {**model_card(), "embedded": len(missing)},
    )
    return {"kb_id": kb_id, "embedded": len(missing), **model_card()}


@router.post("/query", response_model=dict)
def query(
    body: QueryIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
) -> dict:
    top_k = max(1, min(body.top_k, 20))
    requested = body.strategy
    if body.config:
        config = store.rconfig_latest(principal.tenant_id, body.config)
        if config is None:
            raise NotFoundError(f"retrieval config {body.config} not found")
        requested = config["strategy"]
        top_k = max(1, min(int(config["top_k"]), 20))
    summaries = store.summary_list(principal.tenant_id, body.kb_id, 0)
    strategy = select_strategy(body.query, requested, bool(summaries))
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
    if strategy == "dual":
        # Dual level (RG-9): local entity neighborhood + global community/summary context.
        from ..deps import get_graph as _get_graph

        local, globs = [], []
        graph = _get_graph(settings)
        if graph is not None:
            try:
                local = graph.neighborhood(principal.tenant_id, body.query, top_k)
                globs = graph.community_terms(principal.tenant_id, body.kb_id, top_k)
            finally:
                graph.close()
        roots = store.summary_list(principal.tenant_id, body.kb_id, 1)
        combined = " ".join(
            [n.get("name", "") or "" for n in local]
            + [g or "" for g in globs]
            + [r["summary"] for r in roots[:1]]
        )
        if not combined.strip():
            return {
                "strategy": "dual",
                "answer": None,
                "abstained": True,
                "reason": "insufficient evidence",
                "passages": [],
            }
        return {
            "strategy": "dual",
            "answer": combined[:2000],
            "abstained": False,
            "local": local,
            "global_terms": globs,
            "passages": [],
        }
    fts_hits = store.chunk_search_fts(
        principal.tenant_id,
        body.kb_id,
        retrieval_query(body.query),
        top_k * 2,
        body.max_classification,
    )
    docs = [{"id": h["id"], "content": h["content"]} for h in fts_hits]
    tfidf = tfidf_scores(body.query, docs)
    tfidf_ranked = [
        doc_id
        for doc_id, _ in sorted(tfidf.items(), key=lambda kv: kv[1], reverse=True)
    ]
    fts_ranked = [h["id"] for h in fts_hits]
    by_id = {h["id"]: h for h in fts_hits}
    rank_lists = [fts_ranked, tfidf_ranked]
    try:
        from ..embeddings import embed

        dense_hits = store.chunk_search_dense(
            principal.tenant_id,
            body.kb_id,
            embed([body.query])[0],
            top_k * 2,
            body.max_classification,
        )
        if dense_hits:
            rank_lists.append([h["id"] for h in dense_hits])
            for h in dense_hits:
                by_id.setdefault(h["id"], h)
    except Exception:
        dense_hits = []
    fused = rrf(rank_lists)[:top_k]
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
        "dense": bool(dense_hits),
        "answer": answer,
        "abstained": False,
        "faithfulness": round(faith, 3),
        "passages": passages if body.citations else [],
    }


class RetrievalConfigIn(BaseModel):
    id: str
    strategy: str = "auto"
    top_k: int = 5
    min_faithfulness: float = 0.0


@router.post("/configs", response_model=dict, status_code=201)
def save_retrieval_config(
    body: RetrievalConfigIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    if body.strategy not in ("auto", "hybrid", "summary", "graph", "dual"):
        from ..errors import ConflictError

        raise ConflictError("unknown strategy")
    version = store.rconfig_save(
        principal.tenant_id,
        body.id,
        body.strategy,
        max(1, min(body.top_k, 20)),
        body.min_faithfulness,
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "retrieval.config",
        f"{body.id}@{version}",
        "success",
        {},
    )
    return {"id": body.id, "version": version}


@router.get("/catalog", response_model=list[dict])
def catalog(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> dict:
    """Data catalog entries (DG-1): sources with classification, chunk counts, provenance."""
    docs = store._all(
        "SELECT d.id, d.kb_id, d.title, d.classification, d.source_ref, d.created_at, COUNT(c.id) AS chunks "
        "FROM documents d LEFT JOIN chunks c ON c.tenant_id = d.tenant_id AND c.document_id = d.id "
        "WHERE d.tenant_id = %s GROUP BY d.id, d.kb_id, d.title, d.classification, d.source_ref, d.created_at ORDER BY d.id",
        (principal.tenant_id,),
    )
    return {
        "sources": docs,
        "retention_note": "see tenant retention policy; purge via /v1/admin/purge",
    }


@router.get("/stats", response_model=dict)
def kb_stats(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> dict:
    """Quality monitoring basics (DG-3): chunk counts, staleness, per-kb breakdown."""
    rows = store._all(
        "SELECT kb_id, COUNT(*) AS chunks, MAX(created_at) AS freshest FROM chunks WHERE tenant_id = %s GROUP BY kb_id",
        (principal.tenant_id,),
    )
    return {"kbs": rows}


class FlagIn(BaseModel):
    doc_id: str
    reason: str = Field(min_length=3)


@router.post("/flag", response_model=dict, status_code=201)
def flag_content(
    body: FlagIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    """SME curation (SM-2): flag incorrect or outdated content for review."""
    import uuid as _uuid

    cid = _uuid.uuid4().hex[:12]
    store.correction_add(
        principal.tenant_id,
        cid,
        f"doc:{body.doc_id}",
        "",
        f"flagged: {body.reason}",
        principal.subject,
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "kb.flag",
        body.doc_id,
        "success",
        {"reason": body.reason[:80]},
    )
    return {"id": cid, "doc_id": body.doc_id}
