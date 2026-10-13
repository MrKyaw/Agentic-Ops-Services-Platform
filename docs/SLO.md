# SLOs and alert thresholds (OB-4; targets, measurement pending staging)

| Service | SLO | Budget | Alert |
|---|---|---|---|
| Core inference/orchestration APIs | 99.9% monthly success | 0.1% | Burn-rate page at 2% budget/hour |
| Simple agent call P95 | < 3 s | — | Page when P95 > 3 s for 10 min |
| RAG first token P95 | < 2.5 s | — | Page when P95 > 2.5 s for 10 min |
| Intent fallback rate | < 5% | — | Ticket when > 5% for 1 h |
| Approval queue age | < 4 h P95 | — | Ticket when P95 > 4 h |

Local probe (2026-10-12, single replica): healthz p95 126 ms, kb-query p95 384 ms
(`docs/evidence/phase1/load-probe.txt`). Design-capacity proof requires staging hardware.
