# Patch: Patching Page + JSON Schema + Validator

## 1. Objectives

Provide a unified enhancement that introduces:
1. A War Room "Patching" page (UI) showing patch status insights (scopes, counts, recency, compliance percentages) with copy‑to‑clipboard query scopes.
2. A formal JSON Schema for Linux probe output (extensible to Windows) enabling structural validation.
3. A lightweight validator CLI (`validate_probe_record.py`) wired into CI to fail fast on schema drift.

## 2. Scope

In Scope:
- New frontend route: `#/patching` (or React Router path `/patching`) with lazy load.
- Patch status model (placeholder / simulated until real ingestion exists).
- Copy-to-clipboard buttons for common patching scopes (e.g., `host:alpha AND missing_critical>0`).
- JSON Schema file `schema/linux_probe.schema.json` describing current Linux probe JSON.
- Validator script referencing the schema; integration test using a captured sample.
- CI job addition: run validator against probe output (Linux + synthetic).

Out of Scope (Future):
- Real-time ingestion backend, historical patch trend charts, signed attestations, Windows schema unification, remediation orchestration.

## 3. Patching Page Design

### 3.1 UX Goals
- Fast interpretation: expose aggregate compliance at a glance.
- Low friction export: one-click copy of scopes for search/analytics tools.
- Progressive enhancement: loads even if data endpoint unavailable (fallback to mock dataset).

### 3.2 Components
- `PatchingPage.tsx` (lazy): orchestrates fetch + layout.
- `PatchComplianceSummary.tsx`: KPI tiles (e.g., `Critical Outstanding`, `Average Age (days)`, `% Fully Patched`).
- `PatchScopeClipboard.tsx`: renders a label + query + copy button; success toast or inline confirmation.
- `PatchTable.tsx` (optional initial placeholder): list hosts with critical/high/medium outstanding counts and last patch timestamp.

### 3.3 Data Shape (Mock)
```jsonc
{
  "generated_at": "2025-09-15T12:34:56Z",
  "summary": {
    "total_hosts": 5,
    "fully_patched": 2,
    "critical_outstanding": 7,
    "high_outstanding": 13,
    "avg_patch_age_days": 4.6
  },
  "hosts": [
    {"host": "alpha", "critical": 0, "high": 1, "medium": 2, "last_patch": "2025-09-14T18:00:00Z"},
    {"host": "beta",  "critical": 2, "high": 3, "medium": 1, "last_patch": "2025-09-12T09:00:00Z"}
  ],
  "scopes": [
    {"label": "Critical Outstanding", "query": "critical>0"},
    {"label": "Needs Attention", "query": "critical>0 OR high>2"},
    {"label": "Fully Patched", "query": "critical=0 AND high=0 AND medium=0"}
  ]
}
```

## 4. JSON Schema (Linux Probe v1)

File: `schema/linux_probe.schema.json`

Key constraints:
- Required: `host`, `timestamp`, `os`, `cpu`, `mem`, `disk`, `net_in`, `net_out`, `firewall`, `controls`, `listening_ports`.
- `os` enum: `["linux"]`.
- `cpu|mem|disk`: number, min 0, max 100.
- `net_in|net_out`: integer, min 0.
- `firewall.enabled`: boolean or null.
- `controls.av_services`: array of strings (uniqueItems true).
- `listening_ports`: array of integers (1–65535) unique.

(Will implement as draft 2020‑12 with `$id` for reuse.)

## 5. Validator CLI

Script: `validate_probe_record.py` (update or create if absent):
- Accepts filename or `-` stdin.
- Loads JSON, validates against schema using `jsonschema`.
- Non-zero exit on validation error; prints path + message.
- `--schema` override flag (default auto-detect in `schema/`).

## 6. CI Integration

Add step to existing War Room / probe workflow:
1. Run Linux probe once: `python cogsec/collectors/cogsec_probe_linux.py > sample_probe.json`.
2. Validate: `python validate_probe_record.py sample_probe.json`.
3. (Optional) Also validate synthetic JSON fixtures in `tests/fixtures/`.

Fail build on any schema violation.

## 7. Testing Strategy

- Unit: Synthetic records (already added) now pipe through schema validator (new test file `tests/test_linux_probe_schema.py`).
- Round-trip: Capture actual runtime sample to ensure no divergence.
- Negative tests: mutate one field (e.g., set `cpu=150`) expect validator failure.

## 8. Rollout Plan

Phase 1 (This Patch): Schema + validator + mock patching page with static JSON.
Phase 2: Wire mock page to back-end once ingestion service exposes patch aggregates.
Phase 3: Add per-host drilldown + export (CSV/JSON) + delta trend spark bars.

## 9. Rollback Plan

Single-commit revert safe: remove new schema file, validator, and UI route + components.
No existing runtime contracts altered; probe output semantics unchanged.

## 10. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema drift without version bump | Validation failures | Add `schema_version` field placeholder soon |
| Overly strict bounds causing false negatives | CI noise | Start minimally strict, log leniencies |
| Patching UI assumptions diverge from future backend | Refactor churn | Keep mock adapter layer | 

## 11. Acceptance Criteria
- `schema/linux_probe.schema.json` exists and validates a live probe sample.
- `validate_probe_record.py` exits 0 for valid, non-zero for invalid sample.
- CI fails if probe JSON invalid.
- New route `/patching` lazy loads and displays mock metrics + three copy scope buttons.
- Tests include at least one positive + one negative validator case.

## 12. Open Questions
- Add `schema_version` now (default `1.0.0`) or defer until first additive change?
- Should we sign schema with hash to detect tampering? (Future security hardening.)
- Should Windows & Linux unify under a single superset schema later?

## 13. Next Steps After Acceptance
- Implement patch according to this spec.
- Introduce schema versioning + deprecation window guidance in README.
- Expand patching mock to simulate aging (increment `avg_patch_age_days`).

---
Generated: 2025-09-15
