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
