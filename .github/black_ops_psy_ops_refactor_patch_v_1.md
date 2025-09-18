# Refactor Patch Plan (Codename: black_ops_psy_ops) v1

> Purpose: Provide a structured, auditable plan for strategic refactors without implying any covert or abusive intent. The codename is legacy/internal and carries **no operational meaning** beyond grouping related engineering changes.

## Scope (v1)
- Consolidate ingestion & orchestration naming (completed: `cogsec_platform`).
- Introduce orchestration (PitCrew) and action execution (Mechanic) scaffolds.
- Establish versioned architecture snapshot & schema governance.

## Non-Goals
- No production security bypass logic.
- No remote execution beyond registered, explicit safe actions.
- No behavioral obfuscation or anti-analysis code.

## Guiding Principles
1. Transparency: Every structural change paired with documentation and tests.
2. Reversibility: Single-commit rollback possible for each major refactor step.
3. Compatibility: Provide alias fields & migration notes for at least one minor version.
4. Minimal Surface: Avoid premature abstraction until a second concrete use appears.

## Completed Items
- [x] Rename repository branding to `CogSecEndpointSecurity`.
- [x] Migrate ingestion package (`platform` -> `cogsec_platform`).
- [x] Add schema contract & validator.
- [x] Add PitCrew & Mechanic scaffolds with tests.

## Upcoming (Candidate) Items
- [ ] Introduce action safety policy layer (allow/deny list + schema per action).
- [ ] Add signed command manifest format (detached signature JSON envelope).
- [ ] Provide REST facade for scheduler & action registry.
- [ ] Implement integrity hash chain for ingestion event log.
- [ ] Add performance benchmarks (baseline ingestion latency & memory).

## Rollback Strategy
| Change | Rollback | Notes |
|--------|----------|-------|
| Package rename | Reintroduce old dir; adjust imports | Keep alias tests during transition |
| PitCrew/Mechanic | Delete new packages + tests | Low coupling currently |
| Schema updates | Revert schema file & bump patch version | Maintain alias fields |

## Risk Register
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Over-abstraction | Slower iteration | Enforce YAGNI + code review flag |
| Missing migration path | Downstream breakage | Alias + documented deprecation schedule |
| Test gap on new modules | Silent regressions | Mandate coverage before expansion |

## Metrics (Track Post-Merge)
- Test runtime (< 5s target local).
- Schema validation failures (expect 0 in CI).
- Action registry size vs. documented actions (parity index 100%).

---
This document is versioned; new major changes will produce `black_ops_psy_ops_refactor_patch_v_2.md`.
