# THREAT_MODEL.md (Phase 0 baseline; STRIDE + LLM-specific)

Scope: API gateway skeleton, tenant model, auth, audit, landing-zone skeleton.
Out of scope for this review: orchestration runtime, MCP servers, retrieval, fine-tuning (each gets its own review in its build phase).

## Assets

Tenant records, agent catalog, bearer tokens/OIDC claims, audit chain, eval datasets.

## Threats and mitigations

| # | STRIDE | Threat | Mitigation (implemented Phase 0) | Test |
|---|---|---|---|---|
| T1 | Spoofing | Forged tenant identity | Bearer/OIDC validation + mandatory X-Tenant-ID match; fail closed | test_gateway tenant tests |
| T2 | Spoofing | Cross-tenant read via guessed IDs | Tenant-keyed stores; header-vs-claim equality enforced pre-access | test_isolation |
| T3 | Tampering | Audit log edited | Hash-chained append-only JSONL | test_isolation chain test |
| T4 | Tampering | Privilege escalation (non-admin creates tenants) | `tenant-admin` role gate on mutations | (Phase 1: authz-matrix tests) |
| T5 | Repudiation | Action denied by actor | Audit record on every mutation with actor + tenant | test_isolation |
| T6 | Information disclosure | Secrets in logs | Key-based redaction in logger + audit writer | test_isolation redaction |
| T7 | DoS | Runaway request volume | Gateway rate-limit/quotas — NOT YET (Phase 1, MT-4/MT-8) | open |
| T8 | Elevation | dev auth in production | Fail-fast config guard (`prod`+`dev` refused) | test_isolation |
| T9 | LLM-01 | Prompt injection | No AI surface in Phase 0; harness tracks PI-8 as future gate | evals |
| T10 | LLM-06 | Sensitive data in training | Datasets synthetic-only policy (DG-5); documented in COMPLIANCE.md | test_gates schema |

## Residual risks

T4 needs a full RBAC matrix test suite; T7 needs gateway quotas + WAF (infra NOT APPLIED). Both tracked in PLAN/next-phase scope, not claimed done.
