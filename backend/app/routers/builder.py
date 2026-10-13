"""SME guided authoring (SM-1, SM-3, SM-5): objective + rules in, draft manifest + test cases out."""

import re
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_principal
from ..security import Principal

router = APIRouter()
_WORD = re.compile(r"[a-z0-9]+")


class DraftIn(BaseModel):
    objective: str = Field(min_length=10)
    decision_rules: list[str] = []
    escalation: str = "human approval for writes"
    pattern: str = "react"


@router.post("/draft", response_model=dict)
def draft_workflow(
    body: DraftIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    lowered = body.objective.lower()
    tools = ["kb.search"]
    if "case" in lowered or "invoice" in lowered:
        tools.append("catalog.lookup")
    if "create" in lowered or "open" in lowered or "write" in lowered:
        tools.append("case.create")
    pattern = body.pattern if body.pattern in ("react", "rewoo") else "react"
    manifest = {
        "pattern": pattern,
        "tools": tools,
        "decision_rules": body.decision_rules,
        "escalation": body.escalation,
        "businessImpact": {
            "metric": "to be defined by SME",
            "baseline": "tbd",
            "target": "tbd",
        },
    }
    test_cases = [
        {
            "id": f"tc-{uuid.uuid4().hex[:6]}",
            "input": {"message": body.objective},
            "expect": "runs without error",
        },
        {
            "id": f"tc-{uuid.uuid4().hex[:6]}",
            "input": {"message": "handle it"},
            "expect": "clarify, never misroute",
        },
    ]
    audit.record(
        principal.tenant_id,
        principal.subject,
        "builder.draft",
        body.objective[:40],
        "success",
        {},
    )
    return {
        "manifest": manifest,
        "test_cases": test_cases,
        "words": sorted(set(_WORD.findall(lowered))),
    }
