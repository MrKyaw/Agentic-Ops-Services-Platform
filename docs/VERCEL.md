# Vercel deployment (frontend only — Gate 2 scope, NOT DONE)

## Architecture split

Vercel hosts the static Angular console only. It cannot run the API (FastAPI container),
Postgres, or Neo4j. Those need a container-capable host (undecided — see options below)
with managed Postgres + Neo4j, fronted by HTTPS. The console calls same-origin `/api/*`,
which `vercel.json` rewrites to `https://API_BACKEND_HOST/:path*`.

## Prerequisites (developer actions — cannot be done from here)

1. `npm i -g vercel && vercel login` (your account; no credentials in repo).
2. Decide the backend host: Fly.io / Render / Railway / AWS ECS are all compatible
   (Dockerfile + `DATABASE_URL` + `NEO4J_*` env). Record the choice in an ADR first.
3. Deploy Postgres + Neo4j (managed), run migrations (`backend/migrations/` in order),
   seed the pilot tenant, set secrets (`DEV_TOKEN` or OIDC, DB/Neo4j passwords) in the
   host secret manager — never in the repo.
4. Set `API_BACKEND_HOST` in `vercel.json` (replace the placeholder), then:
   `vercel --prod` (preview per PR first: `vercel`).
5. Post-deploy: smoke test (healthz, login, grounded run), attach uptime monitoring,
   verify rollback (`vercel rollback` / previous deployment promote).

## Why not done

No Vercel credentials exist in this environment, no backend host is chosen, and Gate 2
requires its own report + explicit approval per target. This file is the prepared
configuration — claiming a deployment without performing it would violate project rules.
