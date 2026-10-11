"""OIDC verification paths (SC-1): unknown kid, missing tenant claim, JWKS failure, happy path."""

import time

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import Settings
from app.errors import AuthError
from app.security import _jwks_cache, authenticate


def _settings() -> Settings:
    return Settings(
        env="local",
        auth_mode="oidc",
        oidc_issuer="https://idp.test",
        oidc_audience="api",
        jwks_url="https://idp.test/.well-known/jwks.json",
        audit_log_path="/tmp/oidc-audit.jsonl",
        database_url="postgresql://postgres@127.0.0.1:5432/platform",
    )


def _keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwk(public_key, kid: str) -> dict:
    numbers = public_key.public_numbers()
    import base64

    def b64(n: int) -> str:
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    return {"kty": "RSA", "kid": kid, "n": b64(numbers.n), "e": b64(numbers.e)}


def _token(private_key, kid: str, claims: dict) -> str:
    pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return pyjwt.encode(claims, pem, algorithm="RS256", headers={"kid": kid})


@pytest.fixture()
def oidc_env(monkeypatch):
    key = _keypair()
    jwk = _jwk(key.public_key(), "kid-1")
    _jwks_cache.update({"keys": {"kid-1": jwk}, "fetched_at": time.time()})

    def fake_get(url, timeout=10):
        raise AssertionError("JWKS cache must prevent network access")

    monkeypatch.setattr("app.security.httpx.get", fake_get)
    return key


def _claims(**over):
    base = {
        "iss": "https://idp.test",
        "aud": "api",
        "sub": "user-1",
        "tenant": "tenant-oidc-01",
        "exp": int(time.time()) + 300,
    }
    base.update(over)
    return base


def test_oidc_happy_path(oidc_env):
    token = _token(oidc_env, "kid-1", _claims())
    principal = authenticate(f"Bearer {token}", _settings())
    assert principal.tenant_id == "tenant-oidc-01"
    assert principal.subject == "user-1"


def test_oidc_unknown_kid_rejected(oidc_env):
    token = _token(oidc_env, "kid-unknown", _claims())
    with pytest.raises(AuthError, match="unknown key id"):
        authenticate(f"Bearer {token}", _settings())


def test_oidc_missing_tenant_rejected(oidc_env):
    claims = _claims()
    del claims["tenant"]
    token = _token(oidc_env, "kid-1", claims)
    with pytest.raises(AuthError, match="no tenant claim"):
        authenticate(f"Bearer {token}", _settings())


def test_oidc_jwks_failure_rejected(monkeypatch):
    _jwks_cache.update({"keys": {}, "fetched_at": 0.0})

    def boom(url, timeout=10):
        raise ConnectionError("idp down")

    monkeypatch.setattr("app.security.httpx.get", boom)
    with pytest.raises(AuthError, match="unable to fetch JWKS"):
        authenticate("Bearer anything", _settings())
    _jwks_cache.update({"keys": {}, "fetched_at": 0.0})
