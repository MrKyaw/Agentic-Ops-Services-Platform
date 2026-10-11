"""Problem-details errors (RFC 7807) and auth errors."""

from fastapi import Request
from fastapi.responses import JSONResponse


class AuthError(Exception):
    pass


class ForbiddenError(Exception):
    pass


class RateLimitError(Exception):
    pass


class UnavailableError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


def problem(
    status: int, title: str, detail: str, instance: str, correlation_id: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "type": f"https://platform.local/errors/{title.lower().replace(' ', '-')}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": instance,
            "correlationId": correlation_id,
        },
    )


def handlers(app) -> None:
    from .logging import correlation_id

    @app.exception_handler(AuthError)
    async def _auth(_: Request, exc: AuthError) -> JSONResponse:
        return problem(401, "Unauthorized", str(exc), _.url.path, correlation_id.get())

    @app.exception_handler(ForbiddenError)
    async def _forbidden(_: Request, exc: ForbiddenError) -> JSONResponse:
        return problem(403, "Forbidden", str(exc), _.url.path, correlation_id.get())

    @app.exception_handler(RateLimitError)
    async def _ratelimit(_: Request, exc: RateLimitError) -> JSONResponse:
        return problem(
            429, "Too Many Requests", str(exc), _.url.path, correlation_id.get()
        )

    @app.exception_handler(UnavailableError)
    async def _unavail(_: Request, exc: UnavailableError) -> JSONResponse:
        return problem(
            503, "Service Unavailable", str(exc), _.url.path, correlation_id.get()
        )

    @app.exception_handler(NotFoundError)
    async def _nf(_: Request, exc: NotFoundError) -> JSONResponse:
        return problem(404, "Not Found", str(exc), _.url.path, correlation_id.get())

    @app.exception_handler(ConflictError)
    async def _cf(_: Request, exc: ConflictError) -> JSONResponse:
        return problem(409, "Conflict", str(exc), _.url.path, correlation_id.get())
