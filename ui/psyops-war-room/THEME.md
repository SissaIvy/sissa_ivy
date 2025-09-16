# War Room Theme & Accessibility

The War Room ships a dark theme optimized for dashboards and keyboard ergonomics.

## Tokens

Defined in `src/theme/tokens.css` under `:root[data-theme='dark']`:

- **Color**: `--c-bg-*`, `--c-surface-0`, `--c-border`, `--c-accent`, `--c-success`, `--c-warn`, `--c-danger`, `--c-text-*`, `--c-focus`  
- **Spacing**: `--sp-1..--sp-6`  
- **Typography**: `--font-sans`  
- **Shadow**: `--shadow-1`

## Accessibility targets

- Text contrast: **≥ 4.5:1** (body) and **≥ 3:1** (large text).  
- Focus visibility: visible `:focus-visible` outline on all interactive elements.  
- Motion: no non‑essential animations.  
- Navigation: all controls reachable via keyboard; current page has `aria-current="page"`.

## Gauge semantics

The **HealthGauge** conveys status (GREEN/YELLOW/RED) *and* text percentage inside the dial. The gauge container has:

- `role="img"` and `aria-label` describing the metric.  
- An adjacent badge shows the status word for screen readers that skip the dial.

## Tips

- Prefer `.badge` for compact status chips and `.sev.{green|yellow|red}` for severities.  
- Use `.card` for semantic groupings and `.grid` with `cols-3` for responsive KPI rows.
