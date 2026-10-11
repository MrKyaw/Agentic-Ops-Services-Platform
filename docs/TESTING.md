# Testing guide (Phase 1 slice)

## Start the stack

```sh
cd Agentic-Ops-Services-Platform
python3 infra/scripts/preflight.py          # writes .env.local (ports)
DEV_TOKEN=<secret> docker compose --env-file .env.local up --build -d
```

Seed the pilot tenant once per fresh DB:

```sh
docker exec Agentic-Ops-Services-phase1 python -c "
import os; from app.db import Store; from app.seed import seed
s = Store(os.environ['DATABASE_URL']); seed(s, 'tenant-local-01')"
```

Shell setup (adjust port/token to yours):

```sh
API=http://localhost:8001
H1="Authorization: Bearer <DEV_TOKEN>"; H2="X-Tenant-ID: tenant-local-01"; CT="Content-Type: application/json"
```

## URL list (in test order)

| # | Request | Expect |
|---|---|---|
| 1 | `GET $API/healthz` | 200 `{"status":"ok"}` |
| 2 | `GET $API/readyz` | 200 `{"status":"ready"}` |
| 3 | `GET $API/docs` (browser) | Swagger UI, 19 paths |
| 4 | `GET $API/v1/agents/` (no auth) | 401 problem JSON |
| 5 | `GET $API/v1/agents/` (auth, no `X-Tenant-ID`) | 403 |
| 6 | `GET $API/v1/agents/` (auth, wrong tenant) | 403 |
| 7 | `POST $API/v1/tenants/` `{"id":"tenant-x","name":"X"}` | 201 |
| 8 | `GET $API/v1/intents/` | 3 seeded intents |
| 9 | `POST $API/v1/intents/classify` `{"text":"Why was invoice 88123 flagged?"}` | `invoice.exception.triage`, matched |
| 10 | `POST $API/v1/intents/classify` `{"text":"handle it"}` | clarify (never silent misroute) |
| 11 | `POST $API/v1/prompts/` `{"id":"triage-system","template":"You triage {x}","variables":["x"]}` | 201 version 1 |
| 12 | `POST $API/v1/prompts/triage-system/1/approve` | approved |
| 13 | `POST $API/v1/kb/query` `{"kb_id":"kb-policy","query":"escalation policy refunds","top_k":2}` | passages with citations |
| 13b | same body + `"strategy":"summary"` (after #21) | summary strategy + cited summaries |
| 13c | same body + `"strategy":"graph"` | graph neighbors (needs Neo4j) |
| 14 | `POST $API/v1/kb/query` `{"kb_id":"kb-policy","query":"zzzqqq nonexistent"}` | `abstained: true` |
| 15 | `POST $API/v1/runs/` `{"agent_id":"pilot-triage","input":{"message":"Why was invoice 88123 flagged?"}}` + `Idempotency-Key: k1` | `succeeded` + grounded answer |
| 16 | repeat #15 with same key | same id, `deduped: true` |
| 17 | `GET $API/v1/runs/<id>` | run + step trace (`intent` first) |
| 18 | `POST $API/v1/runs/` `{"input":{"message":"Please open a case for invoice 1024"}}` | `waiting_approval` + `approval_id` |
| 19 | `GET $API/v1/approvals/` | pending item listed |
| 20 | `POST $API/v1/approvals/<aid>/decide` `{"decision":"approved"}` | approved; run `succeeded` |

## Suites + stop

```sh
TEST_DATABASE_URL=postgresql://postgres:$POSTGRES_PASSWORD@127.0.0.1:5433/platform \
  AUTH_MODE=dev DEV_TOKEN=test-token-abc DEV_TENANT=tenant-test-01 \
  python3 -m pytest backend/tests/ -q
python3 -m pytest evals/ -q
docker compose --env-file .env.local down
```

## Graph + console (Phase 1 full-stack)

```sh
# 21. build graph + summaries, then query strategies
curl -s -H "$H1" -H "$H2" -XPOST $API/v1/graph/kb-policy/build-graph; echo
curl -s -H "$H1" -H "$H2" -XPOST $API/v1/graph/kb-policy/summaries; echo
curl -s -H "$H1" -H "$H2" $API/v1/graph/kb-policy/themes; echo
# 22. quotas + usage + kill switch (admin)
curl -s -H "$H1" -H "$H2" -H "$CT" -d '{"rpm":60,"runs_per_day":1000}' -XPUT $API/v1/admin/quotas; echo
curl -s -H "$H1" -H "$H2" $API/v1/usage/summary; echo
# 23. console: open http://localhost:$FRONTEND_PORT, sign in with token + tenant
```
