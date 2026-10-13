"""Usage and cost showback (MT-5, NF-C1): per-tenant, per-workflow records."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from ..db import Store
from ..deps import get_store, require_principal
from ..security import Principal

router = APIRouter()


def _today() -> str:
    # UTC everywhere: usage_add records UTC dates, so reads must match (TZ-boundary bug class).
    return datetime.now(timezone.utc).date().isoformat()


@router.get("/", response_model=list[dict])
def my_usage(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store.usage_get(principal.tenant_id, _today())


@router.get("/summary", response_model=dict)
def usage_summary(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> dict:
    rows = store.usage_get(principal.tenant_id, _today())
    return {
        "period": _today(),
        "runs": sum(r["runs"] for r in rows),
        "tokens_in": sum(r["tokens_in"] for r in rows),
        "tokens_out": sum(r["tokens_out"] for r in rows),
        "cost_usd": round(sum(r["cost_usd"] for r in rows), 6),
        "by_workflow": rows,
    }
