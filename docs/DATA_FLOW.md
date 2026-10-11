# DATA_FLOW.md (Phase 0)

```mermaid
flowchart LR
  Client["Console / partner client"] -->|HTTPS: Bearer + X-Tenant-ID + X-Correlation-ID| GW["API Gateway (FastAPI middleware)"]
  GW -->|authenticate: dev-token compare or OIDC JWKS verify| P["Principal (tenant, subject, roles)"]
  P -->|header == claim? else 403| T["Tenant-bound handlers"]
  T -->|tenant-keyed read/write| S[("In-memory stores (Phase 0)\nPostgres RLS in Phase 1")]
  T -->|hash-chained, redacted| A[("Audit JSONL")]
  GW -->|JSON + correlation id| L["Structured logs (PII-redacted)"]
```

## Personal data in Phase 0

Minimal: tenant ids, user subjects, role names, tenant display names. No document content,
no prompts, no embeddings. Audit and logs redact credential-shaped keys. All Phase 0
fixtures use synthetic values (`tenant-test-01`, `test-token-abc`).

## Future flows (not yet built)

Retrieval content, prompt/response capture, fine-tuning datasets — each gets a data-flow
update and privacy review in its own phase (PV-1..PV-6, DL-9).
