# War Room UI (Placeholder)

A future Vite-based UI will provide an operations center dashboard ("War Room") with:

- Endpoint posture overview (aggregated metrics)
- Compliance / patch status slices
- Action dispatch panel (integrated with Mechanic registry)
- Dark theme optimized for low-glare operations contexts

## Planned Theme Adjustments
- Dark neutral background (near #1E1E24) with constrained accent palette
- Accessible contrast for tabular and alert elements (WCAG AA minimum)
- Avoid excessive chroma; rely on shape + iconography for status signaling

## File Structure (Planned)
```
ui/
  package.json
  tsconfig.json
  vite.config.ts
  index.html
  src/
    main.tsx
    App.tsx
    routes/
      index.tsx
    components/
      layout/
      charts/
      tables/
      actions/
    api/
      client.ts
      mocks/
    theme/
      tokens.css
      ThemeProvider.tsx
    state/
      queryClient.ts
    hooks/
      useActions.ts
      useEndpoints.ts
    utils/
    types/
      domain.ts
```

## JS Loader Label Changes (Upcoming)
Legacy labels to be replaced:
- "Dashboard" → "Operations Overview"
- "Agents" → "Endpoints"
- "PsyOps" → "Mechanic"
- "Platform" → "Ingestion"

## Integration Notes
- API layer will call a lightweight REST facade exposing summary + action invoke endpoints.
- WebSocket (optional) for live task completion updates.
- Feature flags: initial release hides experimental mesh/relay metrics.

## Contributing (UI Scope)
Until scaffold lands, contributions should focus on data contract stability and REST design.

---
This is a placeholder only; no build system is wired yet.

from psyops.agent import DEFAULT_AGENT
print(DEFAULT_AGENT.run("echo", {"msg": "hello"}))
