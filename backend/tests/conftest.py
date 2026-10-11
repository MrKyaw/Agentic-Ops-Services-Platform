"""Shared pytest fixtures: Postgres-backed app with seeded intents and KB."""

import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("AUTH_MODE", "dev")
os.environ.setdefault("DEV_TOKEN", "test-token-abc")
os.environ.setdefault("DEV_TENANT", "tenant-test-01")

TEST_DB = os.environ.get(
    "TEST_DATABASE_URL",
    os.environ.get("DATABASE_URL", "postgresql://postgres@127.0.0.1:5432/platform"),
)
TEST_NEO4J_URI = os.environ.get("TEST_NEO4J_URI", os.environ.get("NEO4J_URI", ""))
TEST_NEO4J_USER = os.environ.get(
    "TEST_NEO4J_USER", os.environ.get("NEO4J_USER", "neo4j")
)
TEST_NEO4J_PASSWORD = os.environ.get(
    "TEST_NEO4J_PASSWORD", os.environ.get("NEO4J_PASSWORD", "")
)

from app.config import Settings  # noqa: E402
from app.db import Store  # noqa: E402
from app.factory import create_app  # noqa: E402
from app.migrate import migrate  # noqa: E402
from app.seed import seed  # noqa: E402

TABLES = [
    "run_steps",
    "approvals",
    "runs",
    "chunks",
    "documents",
    "agents",
    "intents",
    "prompts",
    "tenants",
]


@pytest.fixture()
def settings(tmp_path):
    migrate(TEST_DB)
    store = Store(TEST_DB)
    for table in TABLES:
        store._write(f"DELETE FROM {table}")
    seed(store, "tenant-test-01")
    return Settings(
        env="local",
        auth_mode="dev",
        dev_token="test-token-abc",
        dev_tenant="tenant-test-01",
        audit_log_path=str(tmp_path / "audit.jsonl"),
        database_url=TEST_DB,
        neo4j_uri=TEST_NEO4J_URI,
        neo4j_user=TEST_NEO4J_USER,
        neo4j_password=TEST_NEO4J_PASSWORD,
    )


@pytest.fixture()
def client(settings):
    from app.audit import AuditLogger
    from app.deps import get_audit, get_settings, get_store

    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_audit] = lambda: AuditLogger(settings.audit_log_path)
    app.dependency_overrides[get_store] = lambda: Store(settings.database_url)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth():
    return {"Authorization": "Bearer test-token-abc", "X-Tenant-ID": "tenant-test-01"}
