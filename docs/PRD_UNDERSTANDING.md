# PRD_UNDERSTANDING.md

Source: `Agentic-Ops-Services-Platform_PRD.md`, Draft v1.0, dated October 10, 2026. Read in full (all 21 sections + appendices A–E).

## Product summary

The Services AI Platform is a multi-tenant, production-grade foundation for building, evaluating, deploying, and operating agentic AI workflows at enterprise scale on AWS. It replaces ad hoc per-team agent work with shared guardrails: agents reach enterprise systems only through governed MCP servers and APIs, retrieval runs on a hybrid vector/graph stack (pgvector + Neo4j, with Knowledge Graph RAG, LightRAG, and RAPTOR), orchestration supports ReAct and ReWOO behind a plug-in interface, and every change (prompt, model, retrieval config, agent version) passes evaluation gates with auditability, quotas, and cost attribution built in. A full-stack console (Angular + Python/FastAPI) serves platform engineers, agent developers, SMEs, ML practitioners, tenant admins, business sponsors, risk/audit, SRE, and partner UI/API teams.

## Personas and user journeys

- Platform Engineer / Technical Lead: defines architecture, ships core services, owns SLOs and safe rollout.
- Agent Developer: scaffolds an agent from a template, tests locally, promotes versions through eval gates.
- SME: describes a workflow in guided UI, curates knowledge, authors golden sets, reviews low-confidence outputs.
- ML / Applied Scientist: manages datasets, launches fine-tuning jobs, compares experiments, promotes models.
- Tenant Administrator: manages users, roles, keys, connectors, quotas, and cost views.
- Business Stakeholder: defines impact metric per workflow, reads impact dashboards.
- Risk / Compliance / Audit: reviews inventory, evidence packages, approvals, and traces.
- SRE / Operations: runs runbooks, on-call, capacity, DR, incident comms.
- UI and API Partner Teams: integrate via versioned APIs/SDKs and sandboxes.

Core journeys: tenant onboarding → connector/MCP registration → knowledge ingestion → agent authoring → playground testing → evaluation gate → approval (HITL) → canary/shadow → production with tracing → impact measurement → feedback loop into datasets.

## Functional requirements (IDs)

PRD Section 9, MUST/SHOULD/MAY with P0–P2. Full row list in `TRACEABILITY.md` (202 rows). Groups:

- 9.1 Multi-tenancy (MT-1..MT-10): isolation, tenant-ID propagation, RLS/scoped graphs/S3 prefixes/KMS, quotas, cost attribution, dedicated tier, admin, noisy-neighbor, lifecycle, flags.
- 9.2 Orchestration (AO-1..AO-18): plug-in runtime, ReAct, ReWOO, declarative versioned manifests, durability/resume/replay, sync+async, budgets, parallelism, HITL, memory, structured outputs, multi-agent limits, traces, idempotency, policy model selection, canary/shadow.
- 9.3 Prompt/intent (PI-1..PI-12): classifier with confidence, collision resolution (clarify/priority/escalate, never silent misroute), tenant scoping, layered design, thresholds, versioned prompt registry, review gates, injection defense, instruction precedence, exactly-once handling, dashboards, correction loop.
- 9.4 MCP (MC-1..MC-15): server framework, API-only access (direct DB technically impossible), typed versioned tools, identity-propagated authz, policy enforcement, risk tagging, idempotency/dry-run, audit logs, registry, independent deployability, test harness, retrieval-as-MCP, anti-poisoning, remote-only prod transport, size limits.
- 9.5 RAG (RG-1..RG-17): ingestion (parse/OCR/chunk/metadata/PII), provenance + ACL labels, idempotent incremental pipelines, retrieval-time ACL, embedding versioning; hybrid baseline, KG RAG, LightRAG, RAPTOR, strategy router, rewriting/decomposition/HyDE; citations, grounding/abstention, token budgets, untrusted-content isolation.
- 9.6 Data layer (DL-1..DL-9): pgvector HNSW + RLS, Neo4j schemas + isolation, HA/backups/PITR, 2x capacity proof, consistency reconciliation, retrieval-service-only access, store abstraction, migrations, erasure propagation.
- 9.7 Fine-tuning (FT-1..FT-13): internal UI+API, dataset management, SFT/LoRA/DPO, hyperparams, SageMaker execution with cost estimates, monitoring, registry, eval-before-promote, approval workflow, tenant scoping, policy checks, comparison UI, gateway serving.
- 9.8 Experiments (ET-1..ET-8): tracking, comparison dashboards, quality/ops/safety metrics, reproducibility, tracker abstraction, A/B support, offline-to-online linkage, human feedback.
- 9.9 App (FE-1..FE-10, BE-1..BE-7): Angular LTS strict + 14 console modules + trace viewer + playground + approval inbox + RBAC views + realtime + perf/i18n + tests; Python 3.11+ async typed + modular 12-factor + BFF + durable jobs + SDK + Alembic + pinned deps/SBOM.
- 9.10 APIs (AP-1..AP-8): OpenAPI 3.1 + streaming, OAuth2/OIDC + mTLS + keys, pagination/idempotency/correlation/RFC7807, gateway enforcement, versioning policy, SDKs, webhooks, contract tests. Resource groups enumerated (`/tenants` … `/audit-events`).
- 9.11 SME (SM-1..SM-7): guided workflow authoring, knowledge curation, golden-set tools, review queues, mandatory impact definition, collaboration metadata, template library.
- 9.12 Evaluation (EV-1..EV-8): harness, mixed methods incl. calibrated LLM-judge, CI/CD gates, offline+online, red-team suites, versioned datasets, trend dashboards, versioned judge configs.

## Non-functional requirements (IDs)

- Scalability (NF-S1..S4): stateless autoscale; design capacity 500 concurrent runs, 100 rps gateway, 50M chunks, 20M nodes; 2x load + 24h soak pre-GA; provider-limit management.
- Performance (NF-P1..P3): Section 4.3 latencies (3 s simple agent P95, 2.5 s RAG first token), streaming backpressure, ACL-aware caching, parallelism/batching.
- Availability/resilience (NF-A1..A6): 99.9%, multi-AZ, graceful degradation, timeouts/retries/circuit-breakers/bulkheads/DLQ, RTO ≤1h / RPO ≤15min, zero-downtime + auto-rollback, chaos tests.
- Maintainability (NF-M1..M3): module boundaries, ADRs, extension points; one-command local env + templates + CLI; 15% debt budget.
- Usability (NF-U1..U2): WCAG 2.1 AA, SME task benchmark (simple workflow in 60 min).
- Cost (NF-C1..C2): per-request/workflow/tenant metering, alerts/caps, routing/caching/compression/spot/right-sizing.
- Quality gates (Section 4): intent F1 95%+, collision <0.5%, groundedness 95%+, recall@10 90%+, task success 85%+, hallucination <2%.

## AI behaviors (no separate AI-NNN series)

The PRD embeds AI behavior in AO (planning/acting/solving, memory, budgets, fallbacks), PI (classification, precedence, injection defense), RG (rewriting, HyDE, reranking, summarization, grounding), FT (tuning lifecycle), EV (judges, red-teaming), TS (guardrails, autonomy tiers, kill switches, abstention). These rows are the AI scope; see traceability groups AO/PI/RG/FT/EV/TS.

## Data entities and relationships

Tenant → Users, Agents/Versions, Prompts/Versions, Intents, Runs/Steps, MCP servers/Tools, KnowledgeBases → Documents/Chunks → embeddings, Graph entities/relations, RAPTOR summary nodes; Datasets/Versions → FineTuneJobs → ModelRegistry entries; Experiments/Runs, EvaluationRuns, Approvals, AuditEvents (hash-chained), UsageRecords. Relationships: tenant-scoping on all rows; run → steps → tool calls → retrieval hits → model calls; dataset → job → artifact → eval → approval → deployment; chunk → graph nodes → summaries → citations.

## Out of scope (initial release)

Foundation-model pretraining; consumer chat product; replacing systems of record; unsupervised high-risk actions; multi-cloud portability in v1 (AWS target, portable abstractions).

## Ambiguities, gaps, contradictions (with resolution)

1. Neo4j isolation (O2): database-per-tenant vs labels — resolve via ADR-004 (design for both, default labels + isolation tests).
2. Engine picks (O3/O4): Step Functions vs Temporal; MLflow vs custom — resolve via ADR-001/005 (abstractions + Phase 0 spikes, no Phase A pick).
3. Approved models per classification (O1): unknown — resolve via ADR-007 (deny-by-default config).
4. Pilot scope (O5/O7): first MCP systems and impact baselines TBD — resolve by requiring SM-5 impact definition before any production promotion.
5. Regions/DR (O8): active-active need unknown — resolve by building to RTO/RPO targets with optional warm standby flag.
6. Chargeback policy (O9) and tuning scope (O10): TBD — resolve via MT-5/FT metering hooks and approval-gated model lists.
7. WCAG version: PRD says 2.1 AA (FE-1/NF-U1) while the master prompt default says 2.2 AA — PRD governs; 2.2 deltas treated as engineering-added hardening and noted in traceability.
8. Coverage threshold: PRD says 80%+ core lines (Section 4.4); master prompt Gate C says 85% business logic / 100% authz-crypto — the stricter gate applies; recorded as added-by-engineering.

## Assumptions

IdP/SSO, enterprise API owners, Bedrock/hosted model access with data-handling terms, AWS accounts/network/quotas, review-board availability, partner/SME bandwidth, and budget for LLM/GPU/managed services (PRD Section 19) are available when Phase 0 starts. Initial tenants bring high-value workflows with accessible data.
