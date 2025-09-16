# S-4 Patch Recon

## Purpose
Operational after-action style recon for the latest UI evolution (routing + async loading + test stabilization) to inform S-4 (sustainment) decisions: readiness, rollback ease, and follow‑on maintenance tasks.

## Patch Window Summary
Date (UTC): 2025-09-15
Scope: PsyOps War Room UI codebase (`ui/psyops-war-room`).

## Change Inventory
1. Added lazy route loading via React Router with `Suspense` fallbacks (`Spinner`).
2. Introduced route chunk prefetch helper `prefetchRoute` for hover-based warming.
3. Replaced interval-based `useActionTask` simulation with timeout-driven deterministic progression (test-stable).
4. Added pages wrappers (`src/pages/OperationsOverview.tsx`, `Endpoints.tsx`, `Actions.tsx`).
5. Refactored `App.tsx` into a router layout with navigation links + prefetch triggers.
6. Added size report script `scripts/size_report.cjs` and CI artifact upload step.
7. Introduced `Spinner` component for consistent loading states.
8. Updated CI workflow to emit `dist/size-report.json` artifact.
9. Stabilized actions lifecycle test (`actions.smoke.test.tsx`) by switching to deterministic model & ambiguity-safe assertion (`findAllByText`).

## Rationale Highlights
- Lazy loading reduces initial bundle size and isolates future feature growth behind split points.
- Deterministic action task simulation removes flakiness from timer drift and fake timers.
- Prefetch on intent (hover) balances perceived performance while avoiding unconditional eager hydration.
- Size report artifact creates longitudinal data for regression tracking beyond single hard budget gate.

## Risk & Blast Radius
| Area | Risk | Mitigation | Rollback Ease |
|------|------|-----------|---------------|
| Routing refactor | Potential navigation or 404 issues | Minimal scope; single router config | Revert `main.tsx`, `App.tsx`, restore previous static layout |
| Action simulation rewrite | Downstream components expecting interval updates | API surface (returned fields) preserved | Reapply prior file version (one file) |
| Prefetch helper | Unused bundle growth if mis-typed import | Narrow switch + void import | Delete `prefetch.ts` + remove hover handlers |
| Size report script | Failing CI step if missing file | Script writes deterministically | Remove CI steps & script |

## Rollback Strategy
1. Revert `main.tsx` & `App.tsx` to pre-router static render.
2. Restore old `useActionTask.ts` from git history.
3. Delete `src/pages/*`, `components/Spinner.tsx`, `utils/prefetch.ts`.
4. Remove size report script & CI steps; drop `size:report` from `package.json`.
5. Confirm build & tests pass (`npm run typecheck && npm test && npm run build`).

Rollback is surgical (no schema/data migrations). Estimated mean time < 10 minutes.

## Metrics & Validation
- CI green: lint, typecheck, unit tests, build, size budget.
- Bundle budget unchanged (still enforced by `size:check`).
- New artifact: `size-report.json` (track `total_gzip_bytes`).
- Test stability: actions lifecycle test passes consistently (previously timing out).

## Follow-Ups / Backlog Alignment
- Replace placeholder `Endpoints` page with real table view (reuse prior component logic if any).
- Add route-level error boundaries for failed chunk loads.
- Expand synthetic actions simulation to accept failure & cancel states for richer UX and test coverage.
- Incorporate RUM hook (later) to measure actual user-perceived load after split introduction.
- Integrate feature flag gating at route-level (e.g., hide Actions nav if disabled) to reduce dead code fetch.
- Document prefetch strategy in `README.md` (section: Performance).

## Sustainment Notes (S-4 View)
- Watch for growth of `Actions` chunk; set sub-budget thresholds derived from size reports.
- Timeout-driven simulation avoids hidden intervals; simpler for resource cleanup.
- Prefetch calls are passive; safe under reduced bandwidth—but consider heuristic to disable on `save-data` (future enhancement).

## Appendix: File Diffs (Conceptual)
- Added: `src/components/Spinner.tsx`, `src/utils/prefetch.ts`, `src/pages/*`, `scripts/size_report.cjs`.
- Modified: `main.tsx`, `App.tsx`, `hooks/useActionTask.ts`, `package.json`, `.github/workflows/warroom-ci.yml`, test file.

---
Owner: (auto-generated)
Status: Draft – update when production deploy occurs.
