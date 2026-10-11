# TOOLING.md

## Graphify

- Version: **0.9.72** (pinned; verified via `graphify --version`)
- Binary: `graphify` on PATH (conda env, package `graphifyy` 0.9.72, Python 3.12)
- Interpreter record: `graphify-out/.graphify_python`
- Scan root record: `graphify-out/.graphify_root`
- Outputs: `graphify-out/graph.json` (267 nodes, 489 edges, 21 communities), `graphify-out/graph.html`, `graphify-out/GRAPH_REPORT.md`, mirrored to `docs/graphify/GRAPH_REPORT.md`

## Setup performed (Phase A)

1. Located Graphify via installed binary and bundled skill reference (no install guesswork; already present, no upgrade performed to keep the build reproducible).
2. Smoke test: synthetic 3-node extraction → build → cluster. Result saved to `docs/graphify/smoke-test.txt` (PASS).
3. Full PRD ingestion: `graphify.detect` on the work folder (1 document, ~11,478 words), programmatic extraction of 202 requirement IDs plus sections, personas, entities, and cross-cutting concepts, then `build_from_json` + `cluster` + `to_json` + `export html`.
4. No `GEMINI_API_KEY` / `GOOGLE_API_KEY` set in this environment; per Graphify skill, semantic extraction fell back to host-agent extraction (deterministic, audit-logged in `graphify-out/.graphify_extract.json`). No API key was requested or required.
5. Verification queries (saved under `docs/graphify/`):
   - `query-auth.txt`: "which requirements touch authentication?" → SC-1, SC-2, AP-2, MT-2, plus OB/SC neighbors.
   - `query-tenancy-mcp.txt`: "which requirements govern tenant isolation and MCP API boundaries?" → MT-1/2/3/4/5/8, MC-1/2/8, SC-1/2/8, CP-1..6.
   - `god-nodes.txt`: top hubs (platform node degree 261; orchestration 19; RAG 18; MCP 16).
6. Manifest (`graphify-out/manifest.json`) and cost tracker (`graphify-out/cost.json`) written so later `graphify update` runs are incremental.

## Re-index policy

Re-run detection + update at the end of every phase per the master prompt, and refresh `docs/graphify/` query outputs when source or code changes.
