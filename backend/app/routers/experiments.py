"""Experiment tracking (ET-1..ET-4): record params/metrics, list, compare, reproduce-info."""

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..audit import AuditLogger
from ..db import Store
from ..deps import get_audit, get_store, require_principal
from ..security import Principal

router = APIRouter()


class ExperimentIn(BaseModel):
    subject_type: str = Field(pattern=r"^(prompt|retrieval|agent|model)$")
    subject_ref: str = ""
    params: dict = {}
    metrics: dict = {}


@router.post("/", response_model=dict, status_code=201)
def record_experiment(
    body: ExperimentIn,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
    audit: AuditLogger = Depends(get_audit),
) -> dict:
    eid = uuid.uuid4().hex[:12]
    store.experiment_record(
        principal.tenant_id,
        eid,
        body.subject_type,
        body.subject_ref,
        body.params,
        body.metrics,
        principal.subject,
    )
    audit.record(
        principal.tenant_id, principal.subject, "experiment.record", eid, "success", {}
    )
    return {"id": eid}


@router.get("/", response_model=list[dict])
def list_experiments(
    subject_type: str = "",
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> list[dict]:
    _ = principal
    return store.experiment_list(principal.tenant_id, subject_type)


@router.get("/compare", response_model=dict)
def compare_experiments(
    ids: str,
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    wanted = [i.strip() for i in ids.split(",") if i.strip()][:10]
    rows = [r for r in store.experiment_list(principal.tenant_id) if r["id"] in wanted]
    metric_keys = sorted({k for r in rows for k in (r["metrics"] or {})})
    return {
        "experiments": rows,
        "metric_keys": metric_keys,
        "table": [
            {**{"id": r["id"]}, **{k: (r["metrics"] or {}).get(k) for k in metric_keys}}
            for r in rows
        ],
    }


@router.get("/trends", response_model=dict)
def metric_trends(
    metric: str = "accuracy",
    principal: Principal = Depends(require_principal),
    store: Store = Depends(get_store),
) -> dict:
    """Quality trends (EV-7, ET-7): daily averages per metric from recorded experiments."""
    rows = store._all(
        "SELECT created_at::date AS day, AVG((metrics->>%s)::float) AS avg, COUNT(*) AS n FROM experiments "
        "WHERE tenant_id = %s AND metrics ? %s GROUP BY day ORDER BY day",
        (metric, principal.tenant_id, metric),
    )
    return {
        "metric": metric,
        "points": [
            {"day": str(r["day"]), "avg": round(float(r["avg"]), 4), "n": r["n"]}
            for r in rows
        ],
    }
