"""Usage and cost showback (MT-5, NF-C1): per-tenant, per-workflow records."""

from datetime import date

from fastapi import APIRouter, Depends

from ..db import Store
from ..deps import get_store, require_principal
from ..security import Principal

router = APIRouter()


@router.get("/", response_model=list[dict])
def my_usage(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> list[dict]:
    return store.usage_get(principal.tenant_id, date.today().isoformat())


@router.get("/summary", response_model=dict)
def usage_summary(
    principal: Principal = Depends(require_principal), store: Store = Depends(get_store)
) -> dict:
    rows = store.usage_get(principal.tenant_id, date.today().isoformat())
    return {
        "period": date.today().isoformat(),
        "runs": sum(r["runs"] for r in rows),
        "tokens_in": sum(r["tokens_in"] for r in rows),
        "tokens_out": sum(r["tokens_out"] for r in rows),
        "cost_usd": round(sum(r["cost_usd"] for r in rows), 6),
        "by_workflow": rows,
    }
