"""Authentication: dev static-token mode and OIDC JWT mode. Fail closed."""

import hmac
import time
from dataclasses import dataclass, field

import httpx
import jwt

from .config import Settings
from .errors import AuthError

_jwks_cache: dict[str, dict] = {"keys": {}, "fetched_at": 0.0}
JWKS_TTL_SECONDS = 600


@dataclass
class Principal:
    tenant_id: str
    subject: str
    roles: list[str] = field(default_factory=list)
    scopes: list[str] = field(default_factory=list)


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("missing or malformed Authorization header")
    token = authorization[7:].strip()
    if not token:
        raise AuthError("empty bearer token")
    return token


def _fetch_jwks(settings: Settings) -> dict:
    now = time.time()
    if now - _jwks_cache["fetched_at"] < JWKS_TTL_SECONDS and _jwks_cache["keys"]:
        return _jwks_cache["keys"]
    try:
        resp = httpx.get(settings.jwks_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise AuthError(f"unable to fetch JWKS: {exc}") from exc
    keys = {k["kid"]: k for k in data.get("keys", []) if "kid" in k}
    _jwks_cache.update({"keys": keys, "fetched_at": now})
    return keys


def authenticate(authorization: str | None, settings: Settings) -> Principal:
    token = _bearer_token(authorization)
    if settings.auth_mode == "dev":
        if not settings.dev_token or not hmac.compare_digest(token, settings.dev_token):
            raise AuthError("invalid token")
        roles = [r.strip() for r in settings.dev_roles.split(",") if r.strip()]
        return Principal(
            tenant_id=settings.dev_tenant, subject="dev-user", roles=roles or ["member"]
        )
    keys = _fetch_jwks(settings)
    try:
        header = jwt.get_unverified_header(token)
        key = keys.get(header.get("kid", ""))
        if key is None:
            raise AuthError("unknown key id")
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=settings.oidc_issuer,
            audience=settings.oidc_audience,
            options={"require": ["exp", "iss", "sub"]},
        )
    except AuthError:
        raise
    except Exception as exc:
        raise AuthError(f"token validation failed: {exc}") from exc
    tenant = claims.get("tenant") or claims.get("tid") or ""
    if not tenant:
        raise AuthError("token carries no tenant claim")
    roles = claims.get("roles", []) or []
    return Principal(
        tenant_id=str(tenant), subject=str(claims["sub"]), roles=list(roles)
    )
