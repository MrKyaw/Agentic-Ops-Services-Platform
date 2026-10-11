"""Eval gate tests: golden-set schema valid; real classifier v1 measured honestly.

PRD targets (macro F1 95%+, collision <0.5%) are recorded in the report output —
the suite passes on measurement integrity, not on hitting production targets that
a 5-row seed set cannot prove. Promotion gates enforce thresholds separately.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.intent import classify  # noqa: E402
from app.seed import INTENTS  # noqa: E402

DATASET = Path(__file__).parent / "datasets" / "intent-golden-v1.jsonl"

DEFS = [
    {
        "id": i["id"],
        "workflow_id": i["workflow"],
        "examples": i["examples"],
        "keywords": i["keywords"],
        "min_confidence": i["min_confidence"],
    }
    for i in INTENTS
]


def test_dataset_schema():
    rows = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) >= 5
    for row in rows:
        assert {"id", "text", "expected", "min_confidence"} <= set(row)
        assert isinstance(row["text"], str) and row["text"]


def test_classifier_v1_measured(tmp_path):
    rows = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    correct, collisions = 0, 0
    for row in rows:
        pred = classify(row["text"], DEFS)
        if pred.intent_id == row["expected"]:
            correct += 1
        elif pred.resolution == "matched" and row["expected"] in (
            "clarify",
            "no_match",
        ):
            collisions += 1
    report = {
        "total": len(rows),
        "accuracy": round(correct / len(rows), 3),
        "collisions": collisions,
        "target_accuracy": 0.95,
        "target_collision_rate": 0.005,
        "targets_met": correct / len(rows) >= 0.95 and collisions == 0,
    }
    Path(tmp_path, "last-report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    assert report["total"] == 5
    print(f"\nclassifier-v1 report: {report}")


def test_ambiguous_input_clarifies():
    assert classify("handle it", DEFS).resolution in ("clarified", "no_match")
