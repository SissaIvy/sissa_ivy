PitCrew GUI — Rapid Assimilation Dashboard (Daytona Edition)

Quick start
- Requires Node 18+.
- From `ui/pitcrew-dashboard/` run:
  - `npm install`
  - `npm run dev`
- Open the local URL and click “Load JSON”, then pick `mech_out/mechanic_kpi.json` (or the security one under `mech_out_sec/mechanic_kpi.json`).

Notes
- The component tolerates missing `gates` and coerces numeric fields.
- Tailwind classes are included but optional; without Tailwind it still renders cleanly.
- All charts are pure SVG, no chart libraries.

Files
- `src/App.jsx` — the dashboard UI.
- `src/main.jsx` — React entry.
- `index.html` — Vite entry.

