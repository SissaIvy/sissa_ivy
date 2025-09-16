# PsyOps War Room – Alignment Brief

Date: 2025-09-15  
Owner: (draft)  
Status: Working Document

## 1. Vision
Provide a real‑time, operator‑centric command surface to observe endpoint health, orchestrate corrective / hardening actions, and measure operational resilience—while remaining lightweight, testable, and secure by default.

## 2. Strategic Objectives
| Code | Objective | Success Signal (Lag) | Leading Indicators |
|------|-----------|----------------------|--------------------|
| O1 | Rapid Situational Awareness | MTTA (Mean Time To Awareness) < 60s | Page interactive < 2s; health gauge freshness < 10s | 
| O2 | Safe Action Orchestration | >95% successful mock→real action parity | Deterministic simulation; action schema stable |
| O3 | Performance & Footprint Discipline | Main (initial) gzip bundle <= 50KB sustained | Chunk growth delta < +5KB / sprint |
| O4 | Reliability in CI | <1% flaky test reruns | Zero test timeouts over 30 runs |
| O5 | Security Posture | No critical OWASP issues in quarterly review | CSP baseline + dependency audit clean |
| O6 | Progressive Delivery & Rollback | Rollback in <10 min with single revert | Automated artifact traceability |

## 3. Current State Snapshot
| Area | Current | Target Gap | Notes |
|------|---------|-----------|-------|
| Routing | Lazy loaded + prefetch hover | Add error boundaries | Add route-level suspense error UI |
| Actions Simulation | Deterministic timeout model | Failure + cancel paths | Needed for realism & resilience drills |
| Feature Flags | Env-based static evaluation at load | Server-driven diff (future) | Fine for Phase 1 |
| Testing | Smoke + lifecycle test | Coverage >60% lines | Add endpoints + error path tests |
| Size Budget | Hard cap + report | Per-chunk guardrails | Track chunk trending |
| Security Docs | Initial SECURITY.md | Threat model doc + CSP sample | Include dependency review workflow |

## 4. Feature Mapping (Implemented → Objective)
- Lazy Routing & Prefetch: O1, O3  
- Size Budget + Report: O3, O6  
- Deterministic Action Simulation: O2, O4  
- Feature Flags (psyops/blackops): O6  
- Actions Lifecycle Test: O4  

## 5. Key Gaps / Risks
| Risk | Impact | Prob | Mitigation | Owner (TBD) |
|------|--------|------|------------|-------------|
| Missing failure simulation for actions | Under-tested error resiliency | M | Extend simulator states |  |
| No route error boundary | Blank UI on chunk/network failure | M | Add <ErrorBoundary> wrappers |  |
| Growing actions chunk size | Performance regression | M | Sub-bundle internal deps, budget per chunk |  |
| Absent threat model | Hidden attack surface risk | M | Conduct STRIDE-lite pass |  |
| Manual rollback only | Slower recovery | L | Scripted revert helper + doc |  |

## 6. KPIs & Metrics Detail
| KPI | Formula | Instrumentation Plan |
|-----|---------|----------------------|
| MTTA | First paint -> operator sees health gauge | Add perf marks + optional RUM hook |
| Action Success Simulation Rate | succeeded / total simulated tasks | Track in test logs summary |
| Bundle Growth Delta | (current main gzip - baseline) | Compare size-report.json in CI artifact history |
| Test Flake Rate | (# retries) / total test runs | CI workflow annotation parser |
| Rollback Time | Start revert -> green CI | Timebox DR drill quarterly |

## 7. Phased Roadmap (30/60/90)
### Phase 0 (Now → 30d)
- Add endpoints real view + table sorting.
- Failure & cancel simulation events.
- Route error boundaries + fallback UI.
- Threat model draft + CSP example header doc.

Exit: Actions simulation supports 3 terminal states; error boundaries in place; size report baseline stored.

### Phase 1 (30d → 60d)
- Per-chunk size guardrails (CI fail if > threshold).
- Add test coverage for error states & endpoints interactions.
- Introduce basic RUM/perf instrumentation (marks for paint & hydration).

Exit: Coverage >50%; size guardrails active; perf marks recorded.

### Phase 2 (60d → 90d)
- Optional server-fed feature flag hydration.
- Integrate action backend (if available) behind toggle.
- Automated rollback script + doc.

Exit: Live backend action path behind flag; rollback script validated in dry run.

## 8. Prioritized Backlog Slice (Next Up)
1. Failure & cancel states in `useActionTask`.
2. Endpoints page real implementation (reuse mock client).
3. Route error boundaries.
4. Threat model & CSP guidance.
5. Per-chunk size thresholds.

## 9. Alignment Checks
- Every new feature must map to at least one Objective code.
- CI additions require explicit rollback note in PR description.
- Reject PRs increasing main bundle >5KB unless objective justification references O1 or O2.

## 10. Governance Hooks
| Hook | Policy |
|------|--------|
| PR Template | Include Objective mapping + rollback step |
| Size Report | Fails if delta > threshold; posts trend graph (future) |
| Test Matrix | Gate merges on zero timeouts |

## 11. Next Actions (Immediate)
| Action | When | Owner |
|--------|------|-------|
| Implement failure/cancel in simulator | <7d | TBD |
| Build Endpoints table | <7d | TBD |
| Draft threat model | <14d | TBD |
| Add error boundaries | <14d | TBD |

## 12. Appendix
Reference docs: `S-4 Patch Recon.md`, `SECURITY.md`, `Next steps.md`.

---
(End of Alignment Brief)
