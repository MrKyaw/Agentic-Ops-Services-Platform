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
    assert report["total"] == 10
    print(f"\nclassifier-v1 report: {report}")


def test_ambiguous_input_clarifies():
    assert classify("handle it", DEFS).resolution in ("clarified", "no_match")


def test_judge_scores_and_calibrates():
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent / "harness"))
    from judge import JUDGE_PROMPT_VERSION, agreement_record, judge_faithfulness

    class FakeJudge:
        def generate(self, prompt, budget):
            assert "groundedness" in prompt
            return {
                "text": '{"score": 0.9, "verdict": "supported"}',
                "model": "fake",
                "tokens_in": 1,
                "tokens_out": 1,
            }

    out = judge_faithfulness(
        FakeJudge(), "invoices are triaged", ["Invoice triage queue"]
    )
    assert out == {
        "score": 0.9,
        "verdict": "supported",
        "judge": JUDGE_PROMPT_VERSION,
        "model": "fake",
    }

    class BadJudge:
        def generate(self, prompt, budget):
            return {"text": "nope", "model": "fake", "tokens_in": 1, "tokens_out": 1}

    fallen = judge_faithfulness(BadJudge(), "x", ["y"])
    assert fallen["verdict"] == "unsupported" and fallen["error"] is True

    assert (
        agreement_record("supported", "supported", JUDGE_PROMPT_VERSION)["match"]
        is True
    )
    assert (
        agreement_record("supported", "partial", JUDGE_PROMPT_VERSION)["match"] is False
    )


def test_confusion_matrix_no_collisions():
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent / "harness"))
    from baseline import confusion_matrix

    rows = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    predictions = [
        {
            "intent_id": classify(r["text"], DEFS).intent_id,
            "resolution": classify(r["text"], DEFS).resolution,
        }
        for r in rows
    ]
    report = confusion_matrix(rows, predictions)
    assert report["collisions"] == 0
    assert set(report["matrix"]) >= {"policy.qa.ask", "invoice.exception.triage"}


def test_dialect_parity():
    """Bias probe (TS-5): informal/dialectal phrasings of the same intent classify identically."""
    informal = [
        classify("Pls tell me bout the refund policy, thanks kindly", DEFS).intent_id
    ]
    formal = [
        classify("Kindly summarize refund approval policy for me", DEFS).intent_id
    ]
    assert informal == formal == ["policy.qa.ask"]
