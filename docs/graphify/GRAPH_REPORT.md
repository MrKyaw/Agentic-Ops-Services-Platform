# Graph Report - Agentic-Ops-Services-Platform  (2026-10-10)

## Corpus Check
- 67 files · ~26,158 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 4, .env 2, .example 1)

## Summary
- 473 nodes · 918 edges · 32 communities (21 shown, 11 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 127 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- deps.py
- audit.py
- runs.py
- Store
- intent.py
- Sanitization Report — Gate 1 (Phase 0 scope)
- Principal
- create_app
- Communities (44 total, 10 thin omitted)
- TenantStore
- conftest.py
- Gate 1 Report — Implementation and Testing Status (Phase 0 scope, v1)
- PRD_UNDERSTANDING.md
- DECISIONS.md
- PLAN.md
- ARCHITECTURE.md
- RUNBOOK.md (Phase 0 baseline)
- THREAT_MODEL.md (Phase 0 baseline; STRIDE + LLM-specific)
- TOOLING.md
- COMPLIANCE.md (Phase 0 engineering mapping — not legal advice, not a certification)
- DATA_FLOW.md (Phase 0)
- Services AI Platform — Phase 0 (Foundations)
- backend/README.md
- CONTRIBUTING.md
- PRODUCT_OVERVIEW.md
- e2e/README.md
- frontend/README.md
- SECURITY.md

## God Nodes (most connected - your core abstractions)
1. `Store` - 70 edges
2. `Principal` - 35 edges
3. `Communities (44 total, 10 thin omitted)` - 35 edges
4. `AuditLogger` - 34 edges
5. `Settings` - 25 edges
6. `NotFoundError` - 19 edges
7. `create_app()` - 15 edges
8. `require_principal()` - 13 edges
9. `create_run()` - 13 edges
10. `get_audit()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Suggested Questions` --references--> `AuditLogger`  [INFERRED]
  docs/graphify/GRAPH_REPORT.md → backend/app/audit.py
- `Surprising Connections (you probably didn't know these)` --references--> `AuditLogger`  [INFERRED]
  docs/graphify/GRAPH_REPORT.md → backend/app/audit.py
- `God Nodes (most connected - your core abstractions)` --references--> `Settings`  [INFERRED]
  docs/graphify/GRAPH_REPORT.md → backend/app/config.py
- `God Nodes (most connected - your core abstractions)` --references--> `create_app()`  [INFERRED]
  docs/graphify/GRAPH_REPORT.md → backend/app/factory.py
- `Surprising Connections (you probably didn't know these)` --references--> `client()`  [INFERRED]
  docs/graphify/GRAPH_REPORT.md → backend/tests/conftest.py

## Import Cycles
- None detected.

## Communities (32 total, 11 thin omitted)

### Community 0 - "deps.py"
Cohesion: 0.10
Nodes (13): Settings, get_audit(), get_settings(), get_store(), require_admin(), require_principal(), AuthError, ForbiddenError (+5 more)

### Community 1 - "audit.py"
Cohesion: 0.06
Nodes (12): configure(), JsonFormatter, redact(), Registry, ToolDef, Budget, LocalPlanner, ReActRunner (+4 more)

### Community 2 - "runs.py"
Cohesion: 0.09
Nodes (19): ToolCall, ground(), retrieval_query(), rrf(), tfidf_scores(), ingest(), IngestIn, query() (+11 more)

### Community 3 - "Store"
Cohesion: 0.10
Nodes (5): connect(), _j(), Store, list_approvals(), list_intents()

### Community 4 - "intent.py"
Cohesion: 0.13
Nodes (8): Classification, classify(), tfidf_cosine(), tokens(), classify_text(), ClassifyIn, test_ambiguous_input_clarifies(), test_classifier_v1_measured()

### Community 5 - "Sanitization Report — Gate 1 (Phase 0 scope)"
Cohesion: 0.33
Nodes (5): Checklist (E1), Findings and dispositions, Sanitization Report — Gate 1 (Phase 0 scope), Tooling, Verdict

### Community 8 - "Principal"
Cohesion: 0.09
Nodes (29): AuditLogger, ConflictError, NotFoundError, AgentCreate, AgentOut, TenantCreate, TenantOut, TenantUpdate (+21 more)

### Community 12 - "create_app"
Cohesion: 0.11
Nodes (15): handlers(), _auth(), _cf(), _forbidden(), _nf(), problem(), create_app(), correlation() (+7 more)

### Community 20 - "Communities (44 total, 10 thin omitted)"
Cohesion: 0.05
Nodes (41): Communities (44 total, 10 thin omitted), Community 0 - "Services AI Platform", Community 10 - "Vector and Graph Data Layer", Community 11 - "Trust Safety Responsible AI", Community 12 - "Settings", Community 13 - "Python Backend", Community 14 - "Observability Requirements", Community 15 - "SME Collaboration and Workflow Authoring" (+33 more)

### Community 22 - "conftest.py"
Cohesion: 0.10
Nodes (11): _ensure_table(), migrate(), pending(), chunk_text(), seed(), auth(), client(), settings() (+3 more)

### Community 23 - "Gate 1 Report — Implementation and Testing Status (Phase 0 scope, v1)"
Cohesion: 0.09
Nodes (15): Gate 1 — 2026-10-10: decision DEFERRED (pending), 1. Implementation status, 2. Testing status, 3. Open risks and known issues (ranked), 4. What happens if approved (exact scope), 5. Sanitization result, Decision requested, Gate 1 Report — Implementation and Testing Status (Phase 0 scope, v1) (+7 more)

### Community 24 - "PRD_UNDERSTANDING.md"
Cohesion: 0.18
Nodes (9): AI behaviors (no separate AI-NNN series), Ambiguities, gaps, contradictions (with resolution), Assumptions, Data entities and relationships, Functional requirements (IDs), Non-functional requirements (IDs), Out of scope (initial release), Personas and user journeys (+1 more)

### Community 25 - "DECISIONS.md"
Cohesion: 0.14
Nodes (12): ADR-001: Stack default for planning (PRD-compatible), ADR-002: Requirement ID scheme, ADR-003: Tenant isolation default, ADR-004: Graph store tenancy (open question O2), ADR-005: Workflow engine (open question O3), ADR-006: PRD handling wrt repo hygiene, ADR-007: AWS region and model approvals (open questions O1, O8), ADR-008: License choice (+4 more)

### Community 27 - "PLAN.md"
Cohesion: 0.25
Nodes (6): Forward plan (not started; per PRD Sections 6/17 and master prompt Phases B–F), Gate A claim, Phase A (done this run), Phase scope reminder, Risks and mitigations (top, from PRD R1–R14), Test strategy (forward, per master prompt Section 12)

### Community 28 - "ARCHITECTURE.md"
Cohesion: 0.29
Nodes (5): Component responsibilities, Data flow (request path), Diagram (logical, per PRD Section 8), Stack rationale, Trust boundaries

### Community 29 - "RUNBOOK.md (Phase 0 baseline)"
Cohesion: 0.33
Nodes (5): Deployment, Incidents (Phase 0 scope), Local run, RUNBOOK.md (Phase 0 baseline), Verify

### Community 30 - "THREAT_MODEL.md (Phase 0 baseline; STRIDE + LLM-specific)"
Cohesion: 0.40
Nodes (4): Assets, Residual risks, THREAT_MODEL.md (Phase 0 baseline; STRIDE + LLM-specific), Threats and mitigations

### Community 31 - "TOOLING.md"
Cohesion: 0.40
Nodes (3): Graphify, Re-index policy, Setup performed (Phase A)

### Community 32 - "COMPLIANCE.md (Phase 0 engineering mapping — not legal advice, not a certification)"
Cohesion: 0.50
Nodes (3): COMPLIANCE.md (Phase 0 engineering mapping — not legal advice, not a certification), Control mapping (implemented Phase 0), Framework alignment (living document)

### Community 33 - "DATA_FLOW.md (Phase 0)"
Cohesion: 0.50
Nodes (3): DATA_FLOW.md (Phase 0), Future flows (not yet built), Personal data in Phase 0

### Community 34 - "Services AI Platform — Phase 0 (Foundations)"
Cohesion: 0.50
Nodes (3): Quickstart, Services AI Platform — Phase 0 (Foundations), Structure

## Knowledge Gaps
- **104 isolated node(s):** `Contributing`, `Quickstart`, `Structure`, `Security Policy`, `Backend (Phase 1)` (+99 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 234 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Store` connect `Store` to `deps.py`, `runs.py`, `intent.py`, `Principal`, `conftest.py`?**
  _High betweenness centrality (0.135) - this node is a cross-community bridge._
- **Why does `Graph Report - Agentic-Ops-Services-Platform  (2026-10-10)` connect `Communities (44 total, 10 thin omitted)` to `Principal`, `deps.py`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Why does `AuditLogger` connect `Principal` to `deps.py`, `audit.py`, `runs.py`, `create_app`, `conftest.py`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 27 inferred relationships involving `Store` (e.g. with `create_agent()` and `get_agent()`) actually correct?**
  _`Store` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `Principal` (e.g. with `require_admin()` and `require_principal()`) actually correct?**
  _`Principal` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `AuditLogger` (e.g. with `Registry` and `create_agent()`) actually correct?**
  _`AuditLogger` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Settings` (e.g. with `get_audit()` and `get_settings()`) actually correct?**
  _`Settings` has 12 INFERRED edges - model-reasoned connections that need verification._