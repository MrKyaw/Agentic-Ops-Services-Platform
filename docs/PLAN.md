# PLAN.md

## Phase scope reminder

This run implements **Phase A only** (master prompt Sections 3 + Gate A). No UI, backend, integration, commit, or deploy work is included. Phase A exit requires: Graphify smoke test, 100% PRD read, understanding doc, traceability matrix, architecture doc, and this plan.

## Phase A (done this run)

- A1 Graphify 0.9.72 verified + smoke test (`docs/graphify/smoke-test.txt`), pinned in `TOOLING.md`.
- A2 PRD read 100% → `PRD_UNDERSTANDING.md` + `TRACEABILITY.md` (202 rows).
- A3 Knowledge graph built (267 nodes / 489 edges / 21 communities) with verified example queries (`docs/graphify/query-*.txt`, `god-nodes.txt`, `GRAPH_REPORT.md`).
- A4 Architecture + this plan + ADRs (`DECISIONS.md`).

## Forward plan (not started; per PRD Sections 6/17 and master prompt Phases B–F)

- Phase 0 Foundations (wks 0–6): landing zone, IAM/KMS/network, CI/CD + IaC, tenant/auth skeleton, golden datasets + eval skeleton, ADRs, security design review. Exit M0.
- Phase 1 MVP (wks 6–18): ReAct runtime, intent v1, read-only MCP, baseline RAG on pgvector, console v1, 2–3 pilot workflows behind approvals. Exit M1.
- Phase 2 Advanced (wks 18–32): ReWOO + plug-in SDK, Neo4j + KG/LightRAG/RAPTOR, write-capable MCP with approvals, experiment dashboards, eval gates, quota hardening. Exit M2 + 1x load.
- Phase 3 Self-service (wks 32–48): fine-tuning UI→registry→gateway, SME builder, impact/chargeback dashboards, DR + 2x load/soak + pen test. Exit M3.
- Phase 4 GA (wk 52+): marketplace, auto-eval/drift/A-B, PRR + evidence package. Exit M4.

## Risks and mitigations (top, from PRD R1–R14)

| Risk | Mitigation in plan |
|---|---|
| Provider outage/throttle/deprecation | LLM gateway + fallbacks, queues, provisioned throughput, migration tests |
| Injection / exfiltration | Hierarchy, isolation, MCP policy, red-team suites, DLP, least privilege |
| Cross-tenant leakage | RLS + scoped graphs + KMS + IAM conditions + isolation test suite + pen test |
| Retrieval quality | Golden sets early, strategy router, hybrid baseline, SME feedback loop |
| Graph extraction errors | Extraction evals, thresholds, human review, provenance + citations |
| Cost overrun | Budgets/caps, routing, caching, spot training, dashboards/alerts |
| Collisions/misrouting | Layered classifier, disambiguation policy, collision metrics, correction loop |
| Scope creep / platform-without-users | Pilot-driven exits, tenant success metrics, PM ownership |
| Talent gaps | Staffing plan (17.1), pairing, standards, vendor spikes |
| Governance delays | Early risk/compliance engagement, evidence automation, tiered rollout |
| Tuning data misuse | Policy checks, tenant scoping, approvals, lineage, PII scans |
| Stateful-store ops load | Managed services, IaC, runbooks, SRE ownership, reconciliation jobs |
| Runaway loops/cost | Per-run budgets, caps, timeouts, breakers, alerts |
| OSS churn | Thin abstractions, pinning, cadence, contract tests |

## Test strategy (forward, per master prompt Section 12)

Every FR/NFR row gets ≥1 automated test; 100% journeys E2E in containers; Gate C coverage (≥85% business logic, 100% authz/crypto); SAST/DAST/dep/secret/container scans clean; a11y scans + manual checks; eval + red-team gates; resilience fault-injection; 2x load + soak; export/delete/retention/backup/restore verified; README commands executed.

## Gate A claim

Graphify smoke PASS, PRD fully read, understanding + traceability (202/202 IDs) + architecture + plan present. Re-index policy recorded. Ready for review; no commit or deploy attempted.
