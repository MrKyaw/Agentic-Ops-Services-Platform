# Sanitization Report — Gate 1 v2 (full-stack scope)

Date: 2026-10-11. Scope: working tree + git history. History: empty (no commits yet). No secret values below (file references only).

## Tooling

- `gitleaks detect` v8.30.1 per committable path (backend, evals, docs, infra/scripts, e2e, frontend/src + configs, openapi.yaml, compose, env example, CI, root docs): **no leaks found in every path**.
- Full-tree scan (including ignored): 61 findings, all dispositioned below — none committable.
- Banned-term sweep (restricted organization name): **zero matches** tree-wide.
- Email sweep: no real addresses in committable files (only synthetic `example.internal` inside the git-ignored PRD).

## Findings and dispositions

| # | Location | Finding | Disposition |
|---|---|---|---|
| 1 | `frontend/.angular/cache/**` (59) | `generic-api-key` on minified Angular internals (e.g. `i0.EnvironmentInjector`) | Build cache, git-ignored (`.angular/` added to `.gitignore` during this review). False positives. |
| 2 | `.env.local` (2) | Real generated `POSTGRES_PASSWORD`, `NEO4J_PASSWORD` | Git-ignored, never committable (verified via `git check-ignore`); pre-commit scans staged files only so the hook is unaffected. |
| 3 | `docs/evidence/phase1/port-map.env` (earlier rev) | Password copied into evidence | Fixed: rewritten to ports only; re-sweep clean. |
| 4 | Phase 0 items (prior report) | Redaction-key literal, provider binary, PRD synthetic owner, absolute tool path | Unchanged dispositions; tool path fixed then. |

## Checklist (E1)

- [x] No secrets in any committable file (scanned per path, all clean).
- [x] Only `.env.example` placeholders committed; real values live in git-ignored `.env.local`.
- [x] No real personal data; fixtures synthetic.
- [x] No company-confidential content in committable files (planning PRD git-ignored; `docs/PRODUCT_OVERVIEW.md` committed instead).
- [x] No metadata leaks in committable files.
- [x] Pre-commit hook installed (gitleaks + ruff); secret-scan CI job present.
- [x] `.gitignore` covers env files, caches (`__pycache__`, `.angular`, pytest/ruff caches), logs, `.terraform/`, `graphify-out/`, `node_modules/`, `dist/`, PRD file.
- [x] `git status` reviewed: only intended new files; zero commits (no history to rewrite).

## Verdict

**CLEAN — approved for Gate 1 v2 review.**
