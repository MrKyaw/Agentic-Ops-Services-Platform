# API versioning and deprecation policy (AP-5)

- All APIs versioned under `/v1/`; breaking changes ship as `/v2/` with a 6-month overlap.
- Deprecations announced via changelog + `Sunset` response header with a date (format: RFC 1123).
- Compatibility guarantee: additive fields anytime; renames/removals only in major versions.
- Contract tests (`backend/tests/test_contract.py`) fail CI on any undocumented route change.

No deprecations active. Current contract: `openapi.yaml` (33+ paths, regenerated from the app).
