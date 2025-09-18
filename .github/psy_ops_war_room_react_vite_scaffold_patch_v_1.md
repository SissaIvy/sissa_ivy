# Psy Ops War Room React/Vite Scaffold Patch v1

Version: patch_v_1  
Date: 2025-09-15  
Status: APPROVED (Planning Artifact)  
Applies To: Initial UI scaffold introduction (no production feature enablement yet)  
Related Docs: `docs/architecture.md`, `.github/endpoint_telemetry_orchestration_architecture_v_1_0.md`, `.github/black_ops_psy_ops_refactor_patch_v_1.md`, `ui/README.md`

---
## 1. Purpose
Establish a governed, repeatable, low-risk introduction of the War Room (operations console) React + Vite UI layer while preserving backend stability, security posture, and rollback simplicity.

## 2. Scope
IN SCOPE:
- Baseline Vite + React + TypeScript scaffold
- Dark theme token system (CSS variables) with accessibility targets
- State management primitives (TanStack Query + lightweight context)
- API client abstraction (fetch wrapper, error normalization, retry policy)
- Action dispatch UX flow design (not fully wired yet)
- CI integration for lint, type-check, build (non-blocking initially, advisory only)
- Feature flag gating of any runtime mounts

OUT OF SCOPE (future phases):
- Real-time WebSocket streaming
- Advanced charting & analytics
- SSO / auth integration
- Signed action manifests & policy enforcement UI
- Multi-tenant RBAC controls

## 3. Non‑Goals
- No production bundling optimizations beyond defaults (e.g., code splitting strategy doc only) at v1
- No server-side rendering
- No theming override marketplace or dynamic user theme editing
- No GraphQL introduction (stick to REST façade for now)

## 4. Rationale
A minimal, isolated scaffold reduces integration risk, accelerates iterative development, and allows security & governance layers (signing, policy, audit) to mature before exposing high-risk features (remote actions). Isolation ensures easy rollback by pruning a single directory & CI step without database migrations.

## 5. High-Level Architecture Layer Placement
```
[Browser UI] → [UI API Client] → [REST Facade] → [Ingestion DB + Mechanic (actions)]
                                ↘ (Future) Event/WebSocket Stream
```
- The UI must remain a pure consumer; no business logic duplication.
- All mutation endpoints must be idempotent and auditable.

## 6. Directory Structure (Proposed)
```
ui/
  package.json
  tsconfig.json
  tsconfig.node.json (if needed for Vite config typing)
  vite.config.ts
  index.html
  public/
    favicon.svg
  src/
    main.tsx
    App.tsx
    routes/
      index.tsx
      actions.tsx (Phase 2)
      endpoints.tsx
    components/
      layout/
        Shell.tsx
        Sidebar.tsx
        TopBar.tsx
      primitives/
        Button.tsx
        Card.tsx
        Table.tsx
        Badge.tsx
      charts/
        PlaceholderSpark.tsx
      tables/
        EndpointsTable.tsx
      actions/
        ActionInvoker.tsx
        ActionResultStream.tsx (Phase 3)
    api/
      client.ts
      endpoints.ts (query fns)
      actions.ts (mutations)
      mocks/
        handlers.ts (MSW optional)
    state/
      queryClient.ts
      featureFlags.ts
    theme/
      tokens.css
      ThemeProvider.tsx
      global.css
    hooks/
      useFeatureFlag.ts
      useEndpoints.ts
      useInvokeAction.ts
    types/
      domain.ts
      api.ts
    utils/
      retry.ts
      time.ts
    test/
      setup.ts
```

## 7. Dependencies
PRODUCTION:
- react / react-dom
- @tanstack/react-query
- zod (runtime schema validation + parsing)
- ky or lightweight fetch wrapper (decision: custom minimal wrapper to retain control)
- clsx (conditional classnames)
- @radix-ui/colors (optional color scale seeds) OR self-managed token definitions

DEV / TOOLING:
- typescript
- vite
- eslint + @typescript-eslint + eslint-plugin-react-hooks
- prettier
- vitest + @testing-library/react + @testing-library/user-event
- msw (optional future for API mocking)
- postcss + autoprefixer (if needed)
- stylelint (optional in Phase 1; can defer)

## 8. NPM Scripts (Planned)
```
"scripts": {
  "dev": "vite",
  "build": "vite build",
  "preview": "vite preview",
  "typecheck": "tsc --noEmit",
  "lint": "eslint 'src/**/*.{ts,tsx}'",
  "format": "prettier --write .",
  "test": "vitest run",
  "test:watch": "vitest"
}
```

## 9. Feature Flags
- `UI_ENABLE_WAR_ROOM` (top-level mount guard)
- `UI_ENABLE_ACTIONS_PANEL`
- `UI_ENABLE_LIVE_STREAM`
Implementation: simple in-memory map (Phase 1) → environment injection (Phase 2) → remote config (Phase 4).

## 10. Theming & Tokens
Guiding Principles: reduced chroma, high contrast, semantic tokens, minimal brand hue.

Token Categories (CSS variables in `:root` + potential `[data-theme=dark]` scope):
```
--color-bg: #1E1E24;
--color-bg-alt: #24242B;
--color-surface: #2B2B33;
--color-border: #3A3A45;
--color-border-accent: #4D4D59;
--color-text: #E6E6E9;
--color-text-dim: #B0B0B8;
--color-text-inverse: #0F0F12;
--color-accent: #4F7DFF;     /* reserved minimal usage */
--color-accent-strong: #3465F4;
--color-critical: #E54848;   /* red */
--color-warning: #F5A524;    /* amber */
--color-success: #30A46C;    /* green */
--color-info: #4393D7;       /* blue/cyan */
--focus-ring: 0 0 0 2px #0F0F12, 0 0 0 4px #4F7DFF;

--radius-xs: 2px;
--radius-sm: 4px;
--radius-md: 6px;
--radius-lg: 10px;

--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-6: 24px;
--space-8: 32px;

--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', ui-monospace, monospace;

--text-xs: 11px;
--text-sm: 13px;
--text-md: 14px;
--text-lg: 16px;
--text-xl: 20px;

--line-height-tight: 1.15;
--line-height-default: 1.4;
--line-height-relaxed: 1.6;
```
Accessibility Targets:
- Minimum text contrast: 4.5:1 (body), 3:1 (large text ≥ 18px / 14px bold)
- Focus states visible on keyboard navigation (WCAG 2.1 AA)
- No color-only status signaling: pair with icon glyph or shape

## 11. State Management Strategy
- Server State: TanStack Query with staleTime tuned per domain (e.g., endpoints: 15s, actions: 5s)
- Client State: minimal React context for feature flags & theme
- Derived State: use memoized selectors inside hooks; avoid duplicating caches
- Avoid: global event bus, redundant Redux introduction (YAGNI at this phase)

## 12. API Client Abstraction
`api/client.ts` responsibilities:
- Base URL resolution
- Standard headers (version, content-type, optional request-id)
- Timeout (default 10s) with AbortController
- Retry (idempotent GET only; exponential backoff 250ms * 2^n up to 3 attempts)
- Error Normalization Shape:
```
{
  ok: false,
  status: number,
  code?: string,
  message: string,
  retryable: boolean,
  requestId?: string
}
```
Parsing: zod schemas for each endpoint; if parse fails, surface `code = 'SCHEMA_MISMATCH'`.

## 13. Planned REST Facade Endpoints (Consumption Layer)
```
GET  /api/endpoints?limit=&cursor=        → list endpoints (summary rows)
GET  /api/endpoints/{id}                  → detailed endpoint posture
GET  /api/actions/catalog                 → list available actions
POST /api/actions/invoke                  → { action, targetIds[], params } → { taskId }
GET  /api/actions/tasks/{taskId}          → status poll
GET  /api/actions/tasks/stream/{taskId}   → (Future) SSE/WebSocket upgrade
```
All mutation requests must return opaque `taskId` and never block on completion.

## 14. Actions Panel UX Flow (Phase 2)
1. User selects ≥1 endpoints (table row checkboxes)
2. Action picker (command palette or side drawer)
3. Parameter form (dynamic from action schema; not implemented yet)
4. Confirmation dialog summarizing scope & risk tier
5. Invoke → optimistic row annotation "Pending" + task badge
6. Background poll (5s) until terminal state (SUCCESS / ERROR / PARTIAL)
7. Optional: Navigate to task detail inspector (future streaming)

## 15. Security & Compliance (Initial Controls)
- Content Security Policy stub (documented; apply once headers manageable)
- Dependabot / npm audit CI advisory stage
- Disallow inline scripts (index.html hygiene)
- Strict TypeScript ("strict": true)
- Lint rules: no `any`, no floating promises, exhaustive deps for hooks
- Input handling: encode dynamic HTML (avoid dangerouslySetInnerHTML)
- Anti XSS: all external data passes through typed parse layer (zod)
- Threat Modeling Surfaces (Phase 1): API misuse, stale state leading to unsafe actions, supply-chain dependency risk

Future (Phase 3+):
- Subresource Integrity for CDN fonts (if used)
- Action signing & policy gating interface
- Role-based UI gating

## 16. Performance Baselines
- Initial bundle target: < 200KB gzip (excluding polyfills) — monitor via CI size check (Phase 2)
- Code splitting: route-level lazy for actions & analytics sections
- Avoid large chart libs until necessary; placeholder components only

## 17. Observability (Planned)
- Console warnings minimized; treat as CI lint failure (Phase 2)
- Structured client log wrapper (log level gating) before adding remote telemetry
- Basic perf marks: app start mount time metric (Phase 2)

## 18. CI Integration Plan
PHASE 1 (Advisory Only – non-blocking):
- Add steps: install deps, `npm run typecheck`, `npm run lint`, `npm run build`
PHASE 2 (Blocking):
- Include `npm run test` (Vitest) with coverage threshold (e.g., 60% lines initial)
PHASE 3:
- Bundle size check action (diff vs baseline)
PHASE 4:
- Lighthouse CI (optional) in performance profile stage

Workflow Snippet (future addition to `warroom-ci.yml`):
```
- name: UI Dependencies
  working-directory: ui
  run: npm ci
- name: UI Type Check
  working-directory: ui
  run: npm run typecheck
- name: UI Lint
  working-directory: ui
  run: npm run lint
- name: UI Build
  working-directory: ui
  run: npm run build
```

## 19. Migration & Deprecation Alignment
Legacy Items:
- `windows-probe.yml` → Deprecate after War Room reaches Phase 2 stabilization and unified workflow reliability confirmed across 3 consecutive successful runs.
- `psyops/agent.py` shim removal criteria:
  - All internal references migrated to Mechanic exports
  - Release notes published for 2 cycles
  - No external dependents flagged (search + doc audit)
  - THEN remove in a minor version bump

## 20. Rollout Phases & Gates
| Phase | Description | Exit Criteria |
|-------|-------------|---------------|
| 0 | Planning (this doc) | Doc merged, no blocking risks outstanding |
| 1 | Scaffold + Read-Only Endpoint List | CI green, accessibility smoke (keyboard nav), bundle < 200KB |
| 2 | Actions Panel (invoke, polling) | Action tasks auditable, no unhandled promise rejections, ≥60% test coverage core hooks |
| 3 | Live Streaming & Observability | Stable SSE/WebSocket, perf baseline captured |
| 4 | Advanced Analytics / Policy UI | Security review complete, dependency license scan |

## 21. Risk Register
| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| UI introduces build flakiness | Blocks pipeline | Medium | Start advisory; only block after stability proven |
| Action misfire due to stale selection | Incorrect scope | Medium | Re-validate selection server-side before enqueue |
| Bundle creep | Performance regression | High (long-term) | Track size in CI from Phase 2 |
| Token inconsistency | Visual drift | Medium | Single source `tokens.css` + style lint |
| Overfetching endpoints | Backend load | Low | Aggressive query dedupe + staleTime tuning |

## 22. Rollback Strategy
Rollback requires removing only `ui/` + CI steps:
1. Revert the UI introduction PR (no DB schema touched)
2. Remove added workflow steps referencing `ui`
3. Confirm `warroom-ci.yml` passes without UI tasks
4. Communicate rollback reason + next attempt plan
No data migrations; zero impact to ingestion or actions backend.

## 23. Acceptance Criteria (Phase 1)
- `ui/` directory present with scripts & tooling config
- `npm run build` produces artifact with no TypeScript errors
- Lint passes (no errors; warnings allowed initially ≤ 5)
- Basic endpoint list placeholder renders with mock data provider (in-memory array)
- Dark theme tokens load and apply to baseline layout shell

## 24. Open Questions / Deferred Decisions
- Should we adopt a design system library (e.g., Radix Primitives) early? Deferred until Phase 2.
- Do we need runtime i18n? Deferred; YAGNI at current scope.
- Will actions require optimistic UI? Unlikely (audit constraints) → default pessimistic pattern.

## 25. Next Steps Checklist (Execution Order)
1. Add `package.json`, TS configs, Vite config (strict mode)  
2. Add theming tokens + base global styles  
3. Introduce QueryClient + feature flag scaffold  
4. Mock endpoints data & render table placeholder  
5. Wire CI advisory steps  
6. Document feature flags in `README.md`  
7. Prepare Phase 1 closure review (accessibility + bundle snapshot)  

## 26. Governance & Traceability
- Changes referencing this scaffold must cite: `psy_ops_war_room_react_vite_scaffold_patch_v_1` in PR description.
- Any deviation from tokens or component primitives requires design note appended to this file (append-only section below).

## 27. Append-Only Change Log (Empty)
```
-- (no entries yet) --
```

---
End of Patch Document (v1)
