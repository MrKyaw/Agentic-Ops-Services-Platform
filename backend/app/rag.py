"""Baseline retrieval (RG-1..RG-7, RG-13..RG-17): chunking, hybrid TF-IDF + Postgres FTS with RRF.

Dense embeddings and rerankers are pending model selection (O1); the two lexical
signals below are both real, and the strategy config is declarative + versioned.
Retrieved content is returned with provenance and treated as untrusted by callers.
"""

import math
import re
from collections import Counter

_WORD = re.compile(r"[a-z0-9]+")


def retrieval_query(text: str) -> str:
    """Query normalization for lexical search: drop digits and short tokens.

    Rationale: invoice numbers and IDs almost never appear in prose passages;
    keeping them forces FTS conjunctions to empty. TF-IDF ranking still sees
    the full query. Documented heuristic, not a relevance claim.
    """
    kept = [w for w in _WORD.findall(text.lower()) if not w.isdigit() and len(w) > 2]
    return " ".join(kept) or text


def chunk_text(text: str, target: int = 120, overlap: int = 20) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks, start = [], 0
    while start < len(words):
        end = min(start + target, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(end - overlap, start + 1)
    return chunks


def tfidf_scores(query: str, docs: list[dict]) -> dict[str, float]:
    """docs: [{id, content}]. Cosine over TF-IDF, computed locally (RG: lexical signal)."""
    qterms = Counter(_WORD.findall(query.lower()))
    doc_terms = [Counter(_WORD.findall(d["content"].lower())) for d in docs]
    df: Counter = Counter()
    for terms in doc_terms:
        df.update(set(terms))
    n = max(len(docs), 1)
    out = {}
    for doc, terms in zip(docs, doc_terms):
        score = q_norm = d_norm = 0.0
        for term, qtf in qterms.items():
            idf = math.log((1 + n) / (1 + df.get(term, 0))) + 1.0
            qw = qtf * idf
            q_norm += qw * qw
            if term in terms:
                score += qw * (terms[term] * idf)
        for term, tf in terms.items():
            idf = math.log((1 + n) / (1 + df.get(term, 0))) + 1.0
            d_norm += (tf * idf) ** 2
        out[doc["id"]] = (
            score / (math.sqrt(q_norm) / math.sqrt(d_norm))
            if q_norm and d_norm
            else 0.0
        )
    return out


def rrf(rank_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    fused: Counter = Counter()
    for ranks in rank_lists:
        for rank, doc_id in enumerate(ranks, start=1):
            fused[doc_id] += 1.0 / (k + rank)
    return fused.most_common()


def ground(answer_terms: set[str], cited_contents: list[str]) -> float:
    """Faithfulness proxy: fraction of answer terms present in cited passages (RG-15)."""
    if not answer_terms:
        return 1.0
    haystack = " ".join(cited_contents).lower()
    hit = sum(1 for t in answer_terms if t in haystack)
    return hit / len(answer_terms)
