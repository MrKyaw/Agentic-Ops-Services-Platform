"""LLM-as-judge (EV-2): faithfulness scoring with a versioned judge prompt.

Calibration against human labels is tracked as agreement records (judge version,
human verdict, match) — the dataset for calibration ships with the harness and
grows from production sampling (privacy-reviewed). Judge prompts are versioned
constants (EV-8); changing the prompt version invalidates prior comparisons.
"""

import json

JUDGE_PROMPT_VERSION = "judge-faithfulness-v1"

JUDGE_TEMPLATE = (
    "You grade groundedness. Reply with EXACTLY one JSON object "
    '{"score": <0..1>, "verdict": "<supported|partial|unsupported>"} and nothing else.\n'
    "Answer: {answer}\nEvidence:\n{evidence}"
)


def judge_faithfulness(
    backend, answer: str, passages: list[str], max_tokens: int = 512
) -> dict:
    prompt = JUDGE_TEMPLATE.replace("{answer}", answer).replace(
        "{evidence}", "\n".join(passages)
    )
    try:
        raw = backend.generate(prompt, {"max_tokens": max_tokens, "json_mode": True})
        parsed = json.loads(raw["text"])
        score = max(0.0, min(1.0, float(parsed.get("score", 0.0))))
        verdict = str(parsed.get("verdict", "unsupported"))
        if verdict not in ("supported", "partial", "unsupported"):
            verdict = "unsupported"
    except Exception:
        return {
            "score": 0.0,
            "verdict": "unsupported",
            "judge": JUDGE_PROMPT_VERSION,
            "error": True,
        }
    return {
        "score": score,
        "verdict": verdict,
        "judge": JUDGE_PROMPT_VERSION,
        "model": raw.get("model"),
    }


def agreement_record(
    human_verdict: str, judge_verdict: str, judge_version: str
) -> dict:
    return {
        "human": human_verdict,
        "judge": judge_verdict,
        "match": human_verdict == judge_verdict,
        "judge_version": judge_version,
    }
