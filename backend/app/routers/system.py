"""Unauthenticated liveness/readiness probes."""

import time

from fastapi import APIRouter

router = APIRouter()
_started = time.time()


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "uptimeSeconds": int(time.time() - _started)}


@router.get("/readyz")
def readyz() -> dict:
    return {"status": "ready"}


@router.get("/")
def root() -> dict:
    return {
        "service": "services-ai-platform",
        "version": "0.1.0",
        "links": {
            "docs": "/docs",
            "health": "/healthz",
            "ready": "/readyz",
            "openapi": "/openapi.json",
        },
    }


@router.get("/status")
def status() -> dict:
    """Public status rollup (OR-6): component health, no tenant data."""

    checks: dict[str, str] = {"api": "ok"}
    try:
        import psycopg as _psycopg

        from ..config import settings as _settings

        conn = _psycopg.connect(_settings.database_url, connect_timeout=3)
        conn.execute("SELECT 1")
        conn.close()
        checks["db"] = "ok"
    except Exception:
        checks["db"] = "down"
    return {
        "status": "ok" if all(v == "ok" for v in checks.values()) else "degraded",
        "components": checks,
    }


_metrics: dict[str, int] = {"runs_started": 0, "runs_succeeded": 0, "runs_failed": 0}


def record_run_outcome(status: str) -> None:
    _metrics["runs_started"] += 1
    if status == "succeeded":
        _metrics["runs_succeeded"] += 1
    elif status in ("failed", "rejected"):
        _metrics["runs_failed"] += 1


@router.get("/metrics")
def metrics() -> dict:
    """Golden-signal counters (OB-2, single-replica scope)."""
    return dict(_metrics)
