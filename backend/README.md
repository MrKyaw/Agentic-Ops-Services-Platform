# Backend (Phase 1)

FastAPI service: env-driven config with fail-fast validation, dev-token and OIDC-JWKS
auth, mandatory tenant binding, Postgres-backed tenant-scoped stores (versioned SQL
migrations), hash-chained audit log, structured redacted logging, RFC 7807 errors.

Phase 1 slice: prompt registry, intent classifier v1, MCP tool framework + read-only
pilot tools, baseline hybrid retrieval, ReAct runtime (local planner stand-in),
run history/traces, HITL approvals. Contract: `openapi.yaml` (19 paths).

Run: `AUTH_MODE=dev DEV_TOKEN=<secret> DEV_TENANT=tenant-local-01 python3 -m uvicorn app.main:app`
Test (needs the compose DB up): `docker compose --env-file .env.local up -d db` then
`TEST_DATABASE_URL=postgresql://postgres:$POSTGRES_PASSWORD@127.0.0.1:5433/platform AUTH_MODE=dev DEV_TOKEN=test-token-abc DEV_TENANT=tenant-test-01 python3 -m pytest tests/ -q`
(CI provides Postgres on 5432 via a service container instead.)
