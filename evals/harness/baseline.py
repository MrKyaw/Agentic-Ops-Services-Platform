"""Phase 0 eval harness skeleton: deterministic keyword baseline over synthetic golden data.

This is a starting point for PI-1/PI-4, not the production classifier. Thresholds from
the PRD (F1 95%+, collision <0.5%) are asserted as targets so CI fails until the real
layered classifier lands — an honest red gate, not a vanity pass.
"""

import json
from dataclasses import dataclass
from pathlib import Path

RULES = [
    (("invoice", "flag", "exception"), "invoice.exception.triage", 0.83),
    (("escalation", "polic"), "policy.qa.ask", 0.81),
    (("open a case", "create a case"), "case.create", 0.86),
]


@dataclass
class Prediction:
    intent: str
    confidence: float


def classify(text: str) -> Prediction:
    lowered = text.lower()
    for keywords, intent, confidence in RULES:
        if isinstance(keywords, str):
            keywords = (keywords,)
        if any(k in lowered for k in keywords):
            return Prediction(intent, confidence)
    if len(lowered.split()) <= 3:
        return Prediction("clarify", 0.4)
    return Prediction("no_match", 0.35)


def evaluate(dataset: Path) -> dict:
    rows = [
        json.loads(line)
        for line in dataset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    correct, collisions = 0, 0
    for row in rows:
        pred = classify(row["text"])
        if pred.intent == row["expected"] and pred.confidence >= row["min_confidence"]:
            correct += 1
        elif pred.intent not in ("clarify", "no_match") and row["expected"] in (
            "clarify",
            "no_match",
        ):
            collisions += 1
    total = len(rows)
    return {
        "dataset": dataset.name,
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "collisions": collisions,
        "collision_rate": collisions / total if total else 0.0,
    }


def confusion_matrix(gold: list[dict], predictions: list[dict]) -> dict:
    """Confusion telemetry (PI-11): per-expected counts of matched/clarified/no_match + collisions."""
    matrix: dict[str, dict[str, int]] = {}
    collisions = 0
    for row, pred in zip(gold, predictions):
        expected = row["expected"]
        cell = matrix.setdefault(
            expected, {"matched": 0, "clarified": 0, "no_match": 0}
        )
        resolution = pred.get("resolution", "no_match")
        cell[resolution] = cell.get(resolution, 0) + 1
        if (
            resolution == "matched"
            and expected in ("clarify", "no_match")
            and pred.get("intent_id") != expected
        ):
            collisions += 1
    return {"matrix": matrix, "collisions": collisions}
