"""Intent classification endpoints (PI-1..PI-3, PI-10): tenant-scoped, versioned, deduplicated."""

import hashlib
import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..db import Store
from ..deps import get_store, require_principal
from ..intent import classify
from ..security import Principal

router = APIRouter()
_seen_instructions: set[str] = set()


class ClassifyIn(BaseModel):
    text: str
    instruction_id: str = ""


@router.get("/", response_model=list[dict])
def list_intents(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store.intent_list(principal.tenant_id)


@router.post("/classify", response_model=dict)
def classify_text(
    body: ClassifyIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    definitions = store.intent_list(principal.tenant_id)
    result = classify(body.text, definitions)
    dedup = False
    if body.instruction_id:
        key = hashlib.sha256(
            f"{principal.tenant_id}|{body.instruction_id}".encode()
        ).hexdigest()
        if key in _seen_instructions:
            dedup = True
        _seen_instructions.add(key)
    return {
        "workflow_id": result.workflow_id,
        "intent_id": result.intent_id,
        "confidence": result.confidence,
        "resolution": result.resolution,
        "deduplicated": dedup,
        "handled_by": f"workflow-instance:{json.dumps(body.instruction_id)[:16]}"
        if body.instruction_id
        else None,
    }


class CorrectionIn(BaseModel):
    text: str
    predicted: str
    correct: str


@router.post("/corrections", response_model=dict, status_code=201)
def add_correction(
    body: CorrectionIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    import uuid as _uuid

    cid = _uuid.uuid4().hex[:12]
    store.correction_add(
        principal.tenant_id,
        cid,
        body.text,
        body.predicted,
        body.correct,
        principal.subject,
    )
    return {"id": cid}


@router.get("/corrections", response_model=list[dict])
def list_corrections(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store.correction_list(principal.tenant_id)
