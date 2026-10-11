"""Intent classifier v1 (PI-1..PI-5, PI-10): layered rules + TF-IDF similarity, never silent on ambiguity.

Tiers: keyword rules first, then cosine similarity over registered examples, then
low-confidence adjudication (clarify/escalate). LLM adjudication is a planned tier
(pending model selection, O1) and is NOT claimed here.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass

_WORD = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def tfidf_cosine(query: str, example: str, doc_freq: Counter, n_docs: int) -> float:
    qt, et = Counter(tokens(query)), Counter(tokens(example))
    if not qt or not et:
        return 0.0
    score = 0.0
    q_norm = e_norm = 0.0
    for term, qtf in qt.items():
        idf = math.log((1 + n_docs) / (1 + doc_freq.get(term, 0))) + 1.0
        qw = qtf * idf
        q_norm += qw * qw
        if term in et:
            score += qw * (et[term] * idf)
    for term, etf in et.items():
        idf = math.log((1 + n_docs) / (1 + doc_freq.get(term, 0))) + 1.0
        e_norm += (etf * idf) ** 2
    if q_norm == 0 or e_norm == 0:
        return 0.0
    return score / (math.sqrt(q_norm) * math.sqrt(e_norm))


@dataclass
class Classification:
    workflow_id: str
    intent_id: str
    confidence: float
    resolution: str  # matched | clarified | escalated | no_match


def classify(text: str, definitions: list[dict]) -> Classification:
    """definitions: [{id, workflow_id, examples[], keywords[], min_confidence}]."""
    lowered = text.lower()
    keywords_first = sorted(
        ((d, k) for d in definitions for k in (d.get("keywords") or [])),
        key=lambda dk: (0 if " " in dk[1] else 1, -len(dk[1])),
    )
    for d, keyword in keywords_first:
        if keyword.lower() in lowered:
            return Classification(d["workflow_id"], d["id"], 0.9, "matched")
    corpus = [ex for d in definitions for ex in (d.get("examples") or [])]
    doc_freq: Counter = Counter()
    for ex in corpus:
        doc_freq.update(set(tokens(ex)))
    n_docs = max(len(corpus), 1)
    best: Classification | None = None
    second = 0.0
    for d in definitions:
        top = 0.0
        for ex in d.get("examples") or []:
            top = max(top, tfidf_cosine(text, ex, doc_freq, n_docs))
        conf = min(top, 0.89)  # similarity tier never claims rule-level certainty
        if best is None or conf > best.confidence:
            second = best.confidence if best else 0.0
            best = Classification(d["workflow_id"], d["id"], round(conf, 3), "matched")
        elif conf > second:
            second = conf
    if best is None or best.confidence < 0.3:
        if len(tokens(text)) <= 3:
            # Short ambiguous input: clarify rather than reject (PI-2).
            return Classification(
                "none",
                "clarify",
                round(best.confidence if best else 0.0, 3),
                "clarified",
            )
        return Classification(
            "none", "no_match", round(best.confidence if best else 0.0, 3), "no_match"
        )
    threshold = next(
        (d["min_confidence"] for d in definitions if d["id"] == best.intent_id),
        0.8,
    )
    if best.confidence < threshold or (best.confidence - second) < 0.08:
        # Collision or low confidence: clarify, never silently misroute (PI-2).
        return Classification("none", "clarify", best.confidence, "clarified")
    return best
