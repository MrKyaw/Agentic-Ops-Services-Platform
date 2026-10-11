# PROGRESS.md

## 2026-10-10 — Phase A (first phase only, per developer request)

- Read `final_app_master_prompt.md` (364 lines) and `Agentic-Ops-Services-Platform_PRD.md` (1,114 lines) in full.
- Verified restricted-name sweep clean on both source files and the work tree (grep clean); recorded the no-commit-without-approval and no-restricted-name constraints.
- Confirmed work folder is not a git repo; GitHub `MrKyaw/Agentic-Ops-Services-Platform` exists (public, `main`, LICENSE only).
- Graphify 0.9.72: smoke test PASS (`docs/graphify/smoke-test.txt`); full PRD graph built (267 nodes, 489 edges, 21 communities; `graphify-out/graph.json`, `graph.html`, `GRAPH_REPORT.md`); example queries verified (`query-auth.txt`, `query-tenancy-mcp.txt`, `god-nodes.txt`); manifest + cost saved for incremental updates.
- Wrote Phase A docs: `PRD_UNDERSTANDING.md`, `TRACEABILITY.md` (202 rows), `ARCHITECTURE.md`, `PLAN.md`, `TOOLING.md`, `DECISIONS.md` (7 ADRs).
- Gate A: PASS (local evidence only). No commit, push, or deploy performed — awaiting explicit Gate 1 approval when that scope is presented.

### Next (out of scope for this run)

- Phase 0/B onward only on developer instruction; Gate 1 report + sanitization review required before any commit.

## 2026-10-10 — Phase 0 (Foundations)
- Backend skeleton (FastAPI): env config with fail-fast guards, dev-token + OIDC-JWKS auth, mandatory tenant binding, tenant-scoped stores, hash-chained audit, redacted structured logs, RFC 7807 errors, `/healthz` `/readyz`, tenants + agents endpoints. Contract: `openapi.yaml` generated from the app.
- Tests: 14 backend (gateway, isolation, audit chain/redaction, contract) + 3 eval gates — all green. `ruff check` clean. Evidence: `docs/evidence/phase0/test-run.txt`.
- Containers: image builds; live smoke test passed (healthz ok, empty agent list authed, 401 unauth with problem details). Port 8000 was occupied by an unrelated process — preflight shifted to 8001 without touching it (port map in `docs/evidence/phase0/port-map.env`). Preflight fixed to probe 0.0.0.0 as well as 127.0.0.1; compose documented with `--env-file .env.local`.
- Infra: Terraform landing-zone skeleton (`terraform validate` clean; NOT APPLIED — no credentials, needs approval). CI workflow (backend/evals/terraform).
- Evals: synthetic intent golden set (5 rows) + deterministic baseline harness; PRD targets (F1 95%+, collision <0.5%) recorded as future gates, not claimed.
- Docs: THREAT_MODEL, DATA_FLOW, COMPLIANCE, RUNBOOK, PRODUCT_OVERVIEW (sanitized), README, SECURITY, CONTRIBUTING, CODEOWNERS, MIT LICENSE (matches remote), backend/frontend/e2e READMEs (frontend/e2e honestly marked not started).
- Traceability: 15 rows Partial (Phase 0 skeleton), 187 Not started, of 202.
- `git init` done; zero commits. PRD file remains local-only pending Gate 1 review.

## 2026-10-10 — Phase 1 backend slice (in progress, uncommitted)

- Postgres + pgvector compose service; versioned SQL migrations auto-applied at startup; tenant-scoped Store (RLS deferred, documented).
- Prompt registry (versioned, immutable, approve), intent classifier v1 (phrase-first rules + TF-IDF similarity, thresholds, clarify-never-misroute, instruction dedup), MCP framework (typed schemas, risk tiers, tenant-scoped idempotency for writes, audit, unregistered-tool rejection) with kb/catalog/cases tools.
- Baseline RAG: chunking, FTS + TF-IDF + RRF, query normalization, citations, grounding abstention. Dense embeddings pending (ADR-011).
- ReAct loop with budgets, timeout, repeat-action guard, full step traces, run history, idempotent creation, HITL approval inbox (approve/reject). Model backend is a labeled local stand-in (ADR-010).
- Tests: 21 backend + 3 eval gates green; seed-set intent accuracy 5/5 with targets explicitly unproven at scale; ruff clean; terraform valid.
- Live verification in container `Agentic-Ops-Services-phase1` (API :8001, DB :5433): classify, KB query with citations, grounded run, waiting_approval HITL path. Fixed en route: missing jsonschema dep, missing migrations in image, non-root audit write, FTS empty on IDs, planner/tool mismatch, tenant-unscoped idempotency cache.
- Traceability: 64 Partial (Phase 1 backend), 15 Partial (Phase 0 skeleton), 123 Not started, of 202.
- Hygiene: no committed secrets (trust-auth loopback DB, required compose password git-ignored); gitleaks clean on committable trees; one self-caught finding (password copied into evidence port-map) fixed and documented.
- Pending: ReWOO, KG/LightRAG/RAPTOR, dense embeddings + rerank, streaming, Angular console, fine-tuning, experiments, quotas/cost, HA/backups, RBAC matrix, red-team. Working tree now exceeds Gate 1 v1 scope — fresh report required before any commit.

## 2026-10-11 — Phase 1 full-stack (in progress, uncommitted)

- Governance batch: per-tenant quotas + 429s, usage/cost showback, short-term memory with erase, model gateway with kill switches (platform/tenant/agent), output-schema validation, member-vs-admin RBAC matrix (prompt approve + approval decide now admin-only), OIDC happy/edge-path tests. Removed dead in-memory store code. Backend coverage ~90%.
- ReWOO runner (plan → parallel bounded workers → extractive solve), selectable per-agent pattern; trace shows plan + evidence.
- Knowledge graph on composed Neo4j (URI-gated, tenant-scoped Cypher, heuristic extractor labeled as such) + extractive RAPTOR-style summary trees in Postgres + strategy router (auto/hybrid/summary/graph, always reported).
- Angular 19 console (login, runs + trace viewer, approvals inbox, agents, playground with citations, usage, tenants), message catalog, route guards, CSP headers via nginx, 2 headless-Chrome specs green, production build verified.
- Compose now: api (`Agentic-Ops-Services-phase1`), db (`Agentic-Ops-Services-db`), web (`Agentic-Ops-Services-web`), graph (`Agentic-Ops-Services-graph`). No committed secrets (required passwords from git-ignored env; CI uses trust/auth-none ephemerals).
- Traceability: 25 full-stack + 63 backend + 15 skeleton Partial, 99 Not started, of 202.
- Still out of reach locally: dense embeddings + reranker and LLM tiers (blocked on model approvals O1), hosted fine-tuning, write-capable enterprise MCPs, streaming, multi-AZ/HA, load/soak/chaos/pen tests, E2E browser journeys. Each is labeled pending where it bites.
