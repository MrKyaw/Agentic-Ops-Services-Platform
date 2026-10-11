# DECISIONS.md

Architectural Decision Records (Phase A). Conservative interpretations where the PRD is ambiguous. No irreversible action taken.

## ADR-001: Stack default for planning (PRD-compatible)

- Status: Proposed
- Context: PRD mandates Python/FastAPI async backend, Angular LTS frontend, pgvector on Aurora/RDS, Neo4j, LLM gateway over Bedrock + SageMaker hosted models, containers on EKS (or ECS Fargate), Terraform/CDK, SQS/EventBridge + Step Functions (or Temporal).
- Decision: Plan against exactly that stack. No substitution. Build-vs-adopt items (orchestration runtime, workflow engine, experiment tracker) default to thin internal abstractions over proven libraries, decided in Phase 0/1 with benchmarks.
- Consequences: Hiring and infra assumptions in PRD Section 17/19 hold; added abstraction cost is small and preserves portability.

## ADR-002: Requirement ID scheme

- Status: Accepted
- Context: PRD uses prefixed IDs (MT, AO, PI, MC, RG, DL, FT, ET, FE, BE, AP, SM, EV, NF-X, SC, PV, CP, TS, IN, LO, OB, OR, DG). No separate AI-NNN series.
- Decision: Keep PRD IDs verbatim in `TRACEABILITY.md`. AI behaviors trace via AO/PI/RG/FT/TS/EV rows; no invented AI-001 numbering.
- Consequences: 202 rows, 100% ID coverage without scope invention.

## ADR-003: Tenant isolation default

- Status: Proposed
- Context: PRD allows logical isolation by default with optional dedicated resources (MT-6).
- Decision: Design for logical isolation first (RLS, label-scoped graph, per-tenant S3 prefixes, per-tenant KMS where required), with a dedicated-resource escape hatch behind a tenant tier flag.
- Consequences: Lower initial cost; dedicated path must still be tested before offering it.

## ADR-004: Graph store tenancy (open question O2)

- Status: Open
- Context: PRD asks database-per-tenant vs label scoping for Neo4j.
- Decision (interim): Design the data-access layer to support both; default to label/property scoping with automated isolation tests, since the PRD's 12-month scale (20M nodes) does not force per-tenant clusters on day one.
- Consequences: Revisit with cost/isolation evidence in Phase 2.

## ADR-005: Workflow engine (open question O3)

- Status: Open
- Context: Step Functions vs Temporal; build vs adopt agent runtime.
- Decision (interim): No pick in Phase A. Phase 0 spike must compare operability, replay/resume semantics, and local-dev fidelity.
- Consequences: Orchestrator stays behind a stable internal interface regardless of pick.

## ADR-006: PRD handling wrt repo hygiene

- Status: Proposed
- Context: Master prompt sanitization rule: `prd.md` may hold confidential business content.
- Decision: Keep the PRD file local-only for now; do not commit it until Gate 1 sanitization review. `docs/PRODUCT_OVERVIEW.md` (sanitized) will be the committed substitute if needed.
- Consequences: Current folder has no git history; nothing to scrub yet.

## ADR-007: AWS region and model approvals (open questions O1, O8)

- Status: Open
- Context: Approved models per data classification and residency constraints are undecided.
- Decision: Treat model-to-classification mapping as configuration with deny-by-default; block any data class without an approval entry.
- Consequences: Unblocks design without assuming approvals.

## ADR-008: License choice
- Status: Accepted
- Context: Master prompt requires a LICENSE and asks the developer if unspecified. The existing GitHub remote already carries MIT (2026 PRIME).
- Decision: Use MIT locally to match the remote, avoiding a license conflict at first push.
- Consequences: If a different license is wanted, say so before Gate 1 and it will be swapped.

## ADR-009: Versioned SQL migration runner (no Alembic in Phase 1)

- Status: Accepted
- Context: BE-6 asks for versioned migrations (names Alembic). The schema is small and SQL-first (extensions, tsvector, RLS later).
- Decision: Ship `backend/migrations/*.sql` + `app/migrate.py` runner with a `schema_migrations` table, applied at container startup. Alembic adoption deferred to the phase that needs Pedantic autogenerate.
- Consequences: Migration up/down tests pending; down migrations not supported yet (forward-only).

## ADR-010: Local planner stand-in for the ReAct model backend

- Status: Accepted
- Context: No hosted-model credentials exist (O1 open); ReAct loop mechanics can be built and tested without them.
- Decision: Provider-agnostic planner interface with a deterministic keyword planner for dev/tests, clearly labeled non-LLM. Hosted backends arrive with model approvals; loop budgets, traces, HITL, and idempotency hold regardless.
- Consequences: AO-2/AO-17 stay Partial until a real model backend lands and passes evals.

## ADR-011: Lexical hybrid retrieval before dense embeddings

- Status: Accepted
- Context: No approved embedding model (O1); dense vectors would be fake without one.
- Decision: Baseline is Postgres FTS + local TF-IDF with RRF, query normalization, citations, and abstention. `chunks` schema reserves extension points; pgvector extension enabled. Dense embeddings, rerankers, KG/LightRAG/RAPTOR are later phases.
- Consequences: RG-7/RG-12/RG-16 stay Partial; recall/groundedness targets unproven at scale.

## ADR-012: Local Postgres trust auth, required password in compose

- Status: Accepted
- Context: Committed passwords violate the sanitization gate; local dev still needs a working DB.
- Decision: Loopback dev/test DB uses trust auth (no secret committed anywhere); compose requires `POSTGRES_PASSWORD` from git-ignored `.env.local`; CI uses ephemeral trust auth. No password appears in the repo.
- Consequences: Trust auth is loopback-only and documented as such; shared environments must use authenticated URLs via secret managers.

## ADR-013: Neo4j as a composed service, URI-gated

- Status: Accepted
- Context: Graph retrieval needs a real store; managed Neo4j is a deployment decision (O2 open).
- Decision: Self-hosted Neo4j 5 in compose for dev/tests; backend treats an empty `NEO4J_URI` as "graph disabled" with explicit 503s. Tenant scoping enforced in every Cypher statement; no secrets committed (compose password required from git-ignored env; CI uses auth-disabled ephemeral service).
- Consequences: Database-per-tenant vs label scoping still open for production; local proves the access pattern, not the tenancy model.

## ADR-014: Heuristic extraction, extractive summaries

- Status: Accepted
- Context: No approved extraction/summarization models (O1); LLM-backed KG/RAPTOR would be fake.
- Decision: Pattern-based entity extraction + TF-IDF extractive summaries behind the same interfaces the model versions will implement. Limits documented in code and measured where possible (extraction sampling in tests).
- Consequences: RG-8/RG-10 stay Partial until model-backed upgrades pass eval comparison.
