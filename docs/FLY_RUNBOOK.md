# Fly.io runbook — backend staging deploy (Gate 2 scope)

All commands run by the developer (needs Fly account + payment method). Nothing below
has been executed from here. Target: staging API + Postgres + Neo4j in `ord`.

## 0. Install and login

```sh
brew install flyctl
fly auth login
```

## 1. Postgres and Neo4j

```sh
fly postgres create --name agentic-ops-db --region ord
fly volumes create neodata --region ord --size 10 -a agentic-ops-graph
fly deploy --config infra/fly/neo4j.toml
```

## 2. API app with secrets (never in the repo)

```sh
fly apps create agentic-ops-api
fly secrets set -a agentic-ops-api \
  DEV_TOKEN="$(openssl rand -hex 24)" \
  DEV_TENANT=tenant-staging-01 \
  DATABASE_URL="postgresql://postgres:<db-password>@agentic-ops-db.internal:5432/platform" \
  NEO4J_URI="bolt://agentic-ops-graph.internal:7687" \
  NEO4J_USER="neo4j" \
  NEO4J_PASSWORD="<neo4j-password>" \
  OPENROUTER_API_KEY="<key>" \
  OPENROUTER_MODEL="liquid/lfm-2.5-2.6b:free"
```

Get the Postgres password: `fly secrets list -a agentic-ops-db` / attach with
`fly postgres attach -a agentic-ops-api agentic-ops-db` (preferred — sets `DATABASE_URL` itself).

## 3. Deploy, migrate, seed

```sh
fly deploy --config infra/fly/api.toml --dockerfile backend/Dockerfile
fly ssh console -a agentic-ops-api -C "python -c \"from app.migrate import migrate; import os; print(migrate(os.environ['DATABASE_URL']))\""
fly ssh console -a agentic-ops-api -C "python -c \"import os; from app.db import Store; from app.seed import seed, seed_templates; s=Store(os.environ['DATABASE_URL']); seed(s,'tenant-staging-01'); seed_templates(s)\""
```

## 4. Smoke tests (must all pass before opening traffic)

```sh
HOST=https://agentic-ops-api.fly.dev
curl $HOST/healthz
curl -H "Authorization: Bearer <DEV_TOKEN>" -H "X-Tenant-ID: tenant-staging-01" \
  -H 'Content-Type: application/json' -d '{"text":"Why was invoice 88123 flagged?"}' \
  $HOST/v1/intents/classify
```

## 5. Point Vercel at it

Set `API_BACKEND_HOST` in `vercel.json` rewrites to `agentic-ops-api.fly.dev`, commit, push
(auto-redeploys the console).

## 6. Rollback

```sh
fly releases -a agentic-ops-api        # list
fly releases rollback -a agentic-ops-api <version>   # one-command rollback
```

Database rollback: restore from the Fly Postgres snapshot taken before deploy
(`fly postgres backup` cadence: daily in staging).
