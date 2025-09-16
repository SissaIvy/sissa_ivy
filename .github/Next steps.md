# Next Steps: War Room UI & Operational Roadmap

_Last updated: 2025-09-15_

## 1. Immediate Technical Fixes (Week 1)
- TypeScript path alias setup (`@/*`) in `tsconfig.json` to resolve import errors introduced by new hooks/components.
- ESLint override for Node/CJS scripts (`scripts/size_check.cjs`) to suppress false positives (env: node). 
- Remove `any` casts in `buildFeatureFlags()` and strongly type `import.meta.env` via declaration merging.
- Integrate `ActionTaskPanel` with `ActionsForm` (show task timeline after invocation; conditional mount on active task id).
- Validate `package.json` for accidental comments or malformed JSON due to manual patch insertion.

## 2. Feature Enhancements (Weeks 2–3)
- Actions UX Flow: Multi-endpoint selection, confirmation modal, streaming logs (Server-Sent Events or simulated incremental updates).
- Endpoint Filtering & Status Badges: Add search, grouping (by region / role), and status chip colors.
- Health Gauge Improvements: Tooltips, trend mini-sparkline, ARIA live region for significant state changes.
- Runtime Flag Toggle (Dev Only): Small panel to flip feature flags without browser reload (context + localStorage persistence).
- Dark Theme Refinement: Finalize contrast ratios (WCAG AA large text ≥ 3:1, normal text ≥ 4.5:1), document token usage in THEME.md extension.

## 3. Governance & Reliability (Weeks 3–4)
- Security Checklist Formalization: Map threats → mitigations (XSS, CSRF, SSRF via backend, dependency risk). Add to `SECURITY.md` with status matrix.
- Rollback Strategy Document: New `docs/rollback-warroom-ui.md` referencing isolation in `ui/psyops-war-room` and CI gating toggle.
- Bundle Budget Evolution: Per-chunk thresholds + historical tracking (store last build sizes in JSON artifact, fail on >10% growth).
- Observability Hook: Lightweight metrics collection (load time, action latency) behind `UI_ENABLE_TELEMETRY` flag.
- Error Boundary & Fault Injection: Controlled chaos mode to test resilience of polling & action flows.

## 4. Deprecations & Migration (Draft Timelines)
| Item | Criteria to Start | Expected Start | Sunset Target |
|------|-------------------|----------------|---------------|
| `windows-probe.yml` workflow | War Room UI stable + parity metrics | Week 5 | Week 8 |
| `psyops/agent.py` shim | All new endpoints registered via new orchestration | Week 6 | Week 9 |
| Legacy labels (Dashboard/Agents) | Replacement labels merged + docs updated | Week 2 | Week 3 |

## 5. State Management Strategy
- Keep TanStack Query for server/cache domain data (endpoints, health, tasks).
- Use React context for feature flags + ephemeral UI theme.
- Avoid global client store (Redux/Zustand) until >3 cross-cutting non-cache concerns emerge.
- Document boundaries in new `docs/state-boundaries.md` (TBD).

## 6. Risks & Mitigations
| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Import alias unresolved | Build & lint failures | High | Add `paths` + test build early |
| Expanding bundle size | Slow loads | Medium | Enforce granular budgets & analyze `rollup-plugin-visualizer` |
| Mock divergence from real API | Integration friction | Medium | Introduce schema contract tests consuming future OpenAPI spec |
| Feature flag sprawl | Complexity | Medium | Central registry + doc generation script |
| Action polling infinite loop on backend errors | Resource waste | Low | Add max attempts + backoff |

## 7. Backlog (Unscheduled)
- Accessibility audit pass (axe + keyboard trap tests).
- Server-driven events channel (SSE/WebSocket) for real-time task updates.
- CLI parity script for bulk actions (generate reproducible curl sets from UI interactions).
- Theming: High-contrast mode & reduced motion preference detection.
- Security headers enforcement sample (Helmet config in future backend integration doc).

## 8. Ownership / Roles (Provisional)
| Area | Owner | Backup |
|------|-------|--------|
| UI Architecture | TBD | TBD |
| Feature Flags & Governance | TBD | TBD |
| Security & Compliance | TBD | TBD |
| Performance Budgets | TBD | TBD |
| Actions Orchestration | TBD | TBD |

## 9. Success Metrics
- TTI (Time to Interactive) < 2.5s on cold load (local baseline with mock data).
- Bundle (initial JS) < 180KB gzip (current) and < 220KB with actions/sparkline features.
- Action task status latency (mock → UI) < 500ms average update interval.
- < 5 open high severity accessibility issues at first audit.

## 10. Next Execution Step
Execute Immediate Fixes list (alias + lint overrides + action panel integration), then open a tracking issue referencing this document.

---
_Amend this file as priorities shift; keep latest date in header._
