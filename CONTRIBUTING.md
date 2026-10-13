# Contributing

- Conventional commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`), small logical units.
- `ruff check` + `ruff format` clean; backend `pytest` and `evals` green before pushing.
- No secrets, real user data, or internal hostnames in commits. The full PRD file stays local-only.
- Every user-facing change needs a test and a traceability row update in `docs/TRACEABILITY.md`.

## Technical debt (NF-M3)

At least 15% of sprint capacity goes to debt: coverage gaps, TODO burn-down, dependency
upgrades, and flake fixes. Debt items live in the tracker with severity; silent TODOs in
shipped paths are not accepted.
