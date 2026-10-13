# APPROVALS.md

## Gate 1 — 2026-10-10: decision DEFERRED (pending, superseded by v2)

- Scope: Phase 0 foundation files listed in `docs/evidence/gate1-report.md` (v1) → `MrKyaw/Agentic-Ops-Services-Platform`, branch `main`.
- Report version: `docs/evidence/gate1-report.md` v1; sanitization: `docs/evidence/sanitization-report.md` (CLEAN).
- Decision: **later** — developer deferred approval. Superseded by v2 below.

## Gate 1 v2 — 2026-10-11: APPROVED WITH CHANGES (executed)

- Scope: full-stack tree per `docs/evidence/gate1-report.md` (v2) **plus** hygiene fixes requested in review.
- Decision: **Approve with changes → "proceed"** by the developer after reviewing the 144-file commit list.
- Constraints honored: no restricted organization name anywhere; PRD file stays local-only; commits under developer identity with no agent trailers.
- Executed 2026-10-11: 4 commits under `MrKyaw <kyaw.tech@gmail.com>`, rebased clean onto remote LICENSE commit, pushed `0f7183b..101452d main -> main`.

## Gate 1 v3 — 2026-10-12: APPROVED (executed)

- Scope: current tree per `docs/evidence/gate1-report.md` (v3): model gateway + dense retrieval + streaming + lifecycle batch + console growth + Vercel prep (not applied) + docs.
- Decisions recorded: Vercel frontend-only OK (AWS skipped), O1 model `liquid/lfm-2.5-2.6b:free` (ADR-015), Gate 1 approval yes.
- Constraints honored: keys never committed (git-ignored `.env.local` only), no agent trailers, developer identity.

## Gate 2 — Fly.io staging: APPROVED 2026-10-13

- Target: Fly.io `ord`, apps `agentic-ops-api`/`agentic-ops-db`/`agentic-ops-graph`, staging.
- Developer runs `docs/FLY_RUNBOOK.md` (account-bound steps); agent commits configs only.
- Execution: recorded below after push.
