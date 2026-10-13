"""Graph RAG + summary-tree endpoints (RG-8, RG-10, RG-11): build, neighborhood, themes.

Extraction is heuristic and summaries extractive (see graph_rag honesty notes).
The strategy router selects hybrid / graph / summary by query shape; the chosen
strategy is always reported so behavior stays observable (RG-11, RG-13).
"""

from fastapi import APIRouter, Depends
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from ..audit import AuditLogger
from ..config import Settings
from ..db import Store
from ..deps import get_audit, get_graph, get_settings, get_store, require_principal
from ..errors import NotFoundError, UnavailableError
from ..graph_rag import extractive_summary
from ..security import Principal

router = APIRouter()


def _graph_or_503(graph, settings: Settings):
    if graph is None:
        raise UnavailableError("graph store not configured (NEO4J_PASSWORD unset)")
    return graph


@router.post("/{kb_id}/build-graph", response_model=dict)
def build_graph(
    kb_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
    graph=Depends(get_graph),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    graph = _graph_or_503(graph, settings)
    chunks = store._all(
        "SELECT id, content FROM chunks WHERE tenant_id = %s AND kb_id = %s ORDER BY document_id, seq",
        (principal.tenant_id, kb_id),
    )
    entities = 0
    try:
        for chunk in chunks:
            entities += len(
                graph.ingest_chunk(
                    principal.tenant_id, chunk["id"], kb_id, chunk["content"]
                )
            )
    finally:
        graph.close()
    audit.record(
        principal.tenant_id,
        principal.subject,
        "graph.build",
        kb_id,
        "success",
        {"chunks": len(chunks)},
    )
    return {"kb_id": kb_id, "chunks": len(chunks), "entity_mentions": entities}


@router.post("/{kb_id}/summaries", response_model=dict)
def build_summaries(
    kb_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    chunks = store._all(
        "SELECT id, content FROM chunks WHERE tenant_id = %s AND kb_id = %s ORDER BY document_id, seq",
        (principal.tenant_id, kb_id),
    )
    if not chunks:
        raise NotFoundError(f"no chunks for kb {kb_id}")
    texts = [c["content"] for c in chunks]
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(texts)
    n_clusters = max(1, min(3, len(texts)))
    labels = KMeans(n_clusters=n_clusters, n_init=10, random_state=42).fit_predict(
        matrix
    )
    terms = vectorizer.get_feature_names_out()
    groups: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        groups.setdefault(int(label), []).append(idx)
    node_ids = []
    for level, (label, members) in enumerate(sorted(groups.items())):
        group_texts = [texts[i] for i in members]
        summary = extractive_summary(group_texts)
        centroid = matrix[members].mean(axis=0).A1
        weights = {
            terms[i]: round(float(w), 4) for i, w in enumerate(centroid) if w > 0
        }
        sid = f"{kb_id}-l0-{label}"
        store.summary_save(
            principal.tenant_id,
            kb_id,
            0,
            sid,
            [chunks[i]["id"] for i in members],
            summary,
            weights,
        )
        node_ids.append(sid)
    root_texts = [
        store._one(
            "SELECT summary FROM summary_nodes WHERE tenant_id = %s AND id = %s",
            (principal.tenant_id, sid),
        )["summary"]
        for sid in node_ids
    ]
    root = extractive_summary(root_texts, max_sentences=5)
    store.summary_save(
        principal.tenant_id, kb_id, 1, f"{kb_id}-root", node_ids, root, {}
    )
    audit.record(
        principal.tenant_id,
        principal.subject,
        "raptor.build",
        kb_id,
        "success",
        {"nodes": len(node_ids) + 1},
    )
    return {"kb_id": kb_id, "level0_nodes": node_ids, "root": f"{kb_id}-root"}


@router.post("/query-graph", response_model=dict)
def query_graph(
    body: dict,
    principal: Principal = Depends(require_principal),
    settings: Settings = Depends(get_settings),
    graph=Depends(get_graph),
) -> dict:
    graph = _graph_or_503(graph, settings)
    try:
        neighbors = graph.neighborhood(
            principal.tenant_id, str(body.get("query", "")), int(body.get("top_k", 8))
        )
    finally:
        graph.close()
    return {"strategy": "graph", "neighbors": neighbors}


@router.get("/{kb_id}/themes", response_model=dict)
def themes(
    kb_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
    graph=Depends(get_graph),
) -> dict:
    graph = _graph_or_503(graph, settings)
    try:
        terms = graph.community_terms(principal.tenant_id, kb_id)
    finally:
        graph.close()
    roots = store.summary_list(principal.tenant_id, kb_id, 1)
    return {
        "strategy": "community",
        "terms": terms,
        "summary": roots[0]["summary"] if roots else None,
    }


@router.post("/{kb_id}/reconcile", response_model=dict)
def reconcile(
    kb_id: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    settings: Settings = Depends(get_settings),
    graph=Depends(get_graph),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    """Consistency check (DL-5): Postgres chunks vs Neo4j chunk nodes, drift reported."""
    pg_ids = {
        r["id"]
        for r in store._all(
            "SELECT id FROM chunks WHERE tenant_id = %s AND kb_id = %s",
            (principal.tenant_id, kb_id),
        )
    }
    graph_ids: set[str] = set()
    if graph is not None:
        try:
            with graph.driver.session() as session:
                rows = session.run(
                    "MATCH (c:Chunk {tenant: $tenant, kb: $kb}) RETURN c.id AS id",
                    tenant=principal.tenant_id,
                    kb=kb_id,
                )
                graph_ids = {r["id"] for r in rows}
        finally:
            graph.close()
    missing_in_graph = sorted(pg_ids - graph_ids)
    orphan_in_graph = sorted(graph_ids - pg_ids)
    audit.record(
        principal.tenant_id,
        principal.subject,
        "graph.reconcile",
        kb_id,
        "success",
        {"drift": len(missing_in_graph) + len(orphan_in_graph)},
    )
    return {
        "kb_id": kb_id,
        "pg_chunks": len(pg_ids),
        "graph_chunks": len(graph_ids),
        "missing_in_graph": missing_in_graph,
        "orphan_in_graph": orphan_in_graph,
    }


@router.post("/{kb_id}/drift", response_model=dict)
def drift_check(
    kb_id: str,
    body: dict,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    """Embedding drift (LO-4, TS-7): cosine distance between a baseline centroid and current summaries."""
    import math as _math

    nodes = store.summary_list(principal.tenant_id, kb_id, 0)
    if not nodes:
        raise NotFoundError(f"no summaries for kb {kb_id}")
    current: dict[str, float] = {}
    for node in nodes:
        for term, weight in (node.get("centroid") or {}).items():
            current[term] = current.get(term, 0.0) + float(weight)
    baseline = {k: float(v) for k, v in (body.get("baseline") or {}).items()}
    dot = sum(baseline.get(t, 0.0) * w for t, w in current.items())
    bn = _math.sqrt(sum(v * v for v in baseline.values()))
    cn = _math.sqrt(sum(v * v for v in current.values()))
    distance = 1.0 - (dot / (bn * cn) if bn and cn else 0.0)
    return {
        "kb_id": kb_id,
        "distance": round(distance, 4),
        "drifted": distance > 0.5,
        "threshold": 0.5,
    }
