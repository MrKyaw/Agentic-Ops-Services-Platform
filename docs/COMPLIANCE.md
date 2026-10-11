# COMPLIANCE.md (Phase 0 engineering mapping — not legal advice, not a certification)

## Control mapping (implemented Phase 0)

| Control family | Implementation | Evidence |
|---|---|---|
| Access control (MT-7, SC-2) | OIDC/dev auth, tenant binding, admin role gate | backend/tests/test_gateway.py, test_isolation.py |
| Auditability (SC-8, CP-3) | Hash-chained JSONL audit on mutations | test_isolation chain test |
| Data minimization (PV) | Only tenant/user/role metadata handled | DATA_FLOW.md |
| Secrets hygiene (SC-4) | Env-only config, `.env.example` placeholders, redaction | test_isolation redaction |
| Change control (LO-1) | Versioned APIs, contract tests, CI gates | test_contract.py, ci.yml |
| Synthetic test data (DG-5) | All fixtures synthetic | conftest.py, intent-golden-v1.jsonl |

## Framework alignment (living document)

NIST AI RMF, ISO/IEC 42001, SOC 2 control mapping begins in Phase 1 with the control
plane; model-risk inventory (CP-1) starts when the first model/agent version ships.
Privacy impact assessments required per new data-source category (PV-6) before ingestion work.
