# Services AI Platform — Solution Brochure

## The problem

Enterprise service work is document-heavy, rules-heavy, and scattered across systems.
Teams build one-off AI pilots that duplicate effort, open uncontrolled data paths
(agents reaching straight into databases), stall at proof-of-concept, and leave
security, audit, and cost as afterthoughts. There is no shared foundation for taking
an agentic workflow from approval to production in weeks instead of quarters.

## The solution

A multi-tenant agentic AI platform: declare an agent, connect it through governed
API boundaries, ground it in your knowledge base, evaluate every change, and operate
it with full traces, approvals, quotas, and cost showback.

- **Orchestration:** ReAct and ReWOO runtimes behind a pluggable interface, with budgets,
  timeouts, durable traces, idempotent tools, and human-in-the-loop approvals.
- **Guardrailed access:** agents touch enterprise systems only through typed,
  risk-tiered MCP tools — no direct database access, by construction and by test.
- **Grounded answers:** hybrid retrieval (full-text + TF-IDF + dense vectors with RRF),
  knowledge-graph and summary strategies behind an observable router, citations on
  every answer, explicit abstention when evidence is missing.
- **Trust controls:** tenant isolation enforced at every layer, RBAC, hash-chained audit
  log, PII redaction, kill switches, versioned prompts with approval workflow.
- **Measured impact:** per-workflow usage, token, and cost metering from the first run.

## Tech stack

Python/FastAPI · Angular · PostgreSQL + pgvector · Neo4j · Docker · Terraform ·
GitHub Actions CI · Vercel (console) + container hosting (API) · OpenAI-compatible
model gateway (provider-swappable; evaluated with open models in dev).

## Outcomes (measured, staging/dev environment)

- **147 automated checks green** across backend, evals, console specs, and browser
  journeys; 91% backend line coverage; OpenAPI contract drift-fails CI.
- **Golden-set intent routing:** 10/10 with zero silent misroutes (ambiguous input
  clarifies; gibberish abstains). Production targets (F1 95%+) require scale-up sets.
- **Grounded QA:** citations on every answer; abstention verified on no-evidence queries;
  LLM-as-judge pilot agreement 3/3 on calibration samples.
- **Local latency:** health p95 ~126 ms, grounded-query p95 ~384 ms (single replica;
  design targets require staging hardware proof).
- **Resilience behaviors verified:** quota 429s, kill-switch 503s, approval-gated writes,
  idempotent replays, fault-contained dependency failures, backup roundtrip.

*Figures are staging/dev measurements, not production SLAs. Production claims require
the deployment, load, and evaluation program described in the project runbook.*
