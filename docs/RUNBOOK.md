# RUNBOOK.md (Phase 0 baseline)

## Local run

```sh
cp .env.example .env   # then set DEV_TOKEN to a real secret value
python3 infra/scripts/preflight.py
docker compose --env-file .env.local up --build
curl localhost:$API_PORT/healthz
```

Without containers:

```sh
cd backend
AUTH_MODE=dev DEV_TOKEN=<secret> DEV_TENANT=tenant-local-01 \
  python3 -m uvicorn app.main:app --port 8000
```

## Verify

```sh
AUTH_MODE=dev DEV_TOKEN=test-token-abc DEV_TENANT=tenant-test-01 \
  python3 -m pytest backend/tests/ -q
python3 -m pytest evals/ -q
terraform -chdir=infra/terraform init -backend=false && terraform -chdir=infra/terraform validate
```

WARNING: the backend suite truncates and reseeds its target database (`TEST_DATABASE_URL`).
Never point it at a database holding data you care about — use the compose DB
(throwaway dev data) or a dedicated test database. Same for graph tests and Neo4j.

## Incidents (Phase 0 scope)

- 401 spike: check IdP/JWKS reachability (`AUTH_MODE=oidc`) or token rotation (`dev`).
- 403 spike: tenant claim mismatch — verify client sends the token's own tenant.
- Audit verification: each line's `hash` chains to the previous `prev`; recompute with sha256.

## Deployment

NOT DONE. Terraform is validated, never applied (no credentials in this environment).
Applying requires review-board approval, backend state, and a named environment —
see Gate 2 process in the master prompt. Frontend deployment target undecided until Phase 1.
