"""FastAPI application factory with gateway concerns: CORS, correlation, problem errors."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import logging as plog
from .config import Settings
from .errors import handlers
from .logging import new_correlation_id
from .routers import (
    admin,
    agents,
    approvals,
    builder,
    experiments,
    finetune,
    graph,
    intents,
    knowledge,
    memory,
    prompts,
    runs,
    system,
    tenants,
    usage,
)

log = plog.configure()


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    if settings.cors_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_list,
            allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-Tenant-ID",
                "X-Correlation-ID",
            ],
            max_age=600,
        )

    @app.middleware("http")
    async def correlation(request: Request, call_next):  # type: ignore[no-untyped-def]
        cid = new_correlation_id(request.headers.get("X-Correlation-ID"))
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = cid
        return response

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", extra={"fields": {"path": request.url.path}})
        return JSONResponse(
            status_code=500,
            content={
                "type": "https://platform.local/errors/internal",
                "title": "Internal Error",
                "status": 500,
                "detail": "unexpected failure",
                "instance": request.url.path,
                "correlationId": plog.correlation_id.get(),
            },
        )

    handlers(app)
    app.include_router(system.router, tags=["system"])
    app.include_router(tenants.router, prefix="/v1/tenants", tags=["tenants"])
    app.include_router(agents.router, prefix="/v1/agents", tags=["agents"])
    app.include_router(prompts.router, prefix="/v1/prompts", tags=["prompts"])
    app.include_router(intents.router, prefix="/v1/intents", tags=["intents"])
    app.include_router(knowledge.router, prefix="/v1/kb", tags=["knowledge"])
    app.include_router(runs.router, prefix="/v1/runs", tags=["runs"])
    app.include_router(approvals.router, prefix="/v1/approvals", tags=["approvals"])
    app.include_router(usage.router, prefix="/v1/usage", tags=["usage"])
    app.include_router(graph.router, prefix="/v1/graph", tags=["graph"])
    app.include_router(memory.router, prefix="/v1/memory", tags=["memory"])
    app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
    app.include_router(
        experiments.router, prefix="/v1/experiments", tags=["experiments"]
    )
    app.include_router(builder.router, prefix="/v1/builder", tags=["builder"])
    app.include_router(finetune.router, prefix="/v1/finetune-jobs", tags=["finetune"])
    return app
