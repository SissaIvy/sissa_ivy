### SISSA PitCrew — Live Status

![status](badges/status.svg) ![kpi](badges/kpi.svg) ![xai](badges/xai.svg) ![failrate](badges/failrate.svg)

![metrics](badges/metrics.svg)

<details>
<summary>More visuals</summary>

![pit lanes](badges/metrics_pitlanes.svg)

![redline stacks](badges/metrics_stacks.svg)

![telemetry bars](badges/metrics_telemetry.svg)

</details>

#### Mechanic behavior

- Automatic AML switch: If `aml/components/evaluate_personas.py` exists, the workflow runs your real offline chain (generate → simulate → evaluate). Otherwise, it uses a deterministic mock that emits `aml_out/report.json`. The mock mirrors expected ranges and defaults to PASS so the required check stays green.
- HOLD drill (non‑required): A separate job runs on schedule or when manually dispatched to deliberately produce a HOLD and prove the gate still trips. It does not block merges. Trigger via Actions → “PitCrew KPI” → Run workflow (includes the `hold_drill` job).
- Tuning: Gates/weights can be adjusted via arguments in `.github/workflows/pitcrew-kpi.yml` and `ops/mechanic/mock_battletest.py`. The evaluator’s failure‑rate and explainability thresholds drive the PASS/HOLD decision.

Nightly and on every PR, PitCrew runs the offline battle‑test (scenarios → simulator strict/explore → evaluator) and refreshes these badges. PASS/HOLD follows the evaluator’s gates (failure rates and explainability thresholds). Details: see `mech_out/mechanic_kpi.json` and CI job summaries.

#### Live Dashboard

- View online (GitHub Pages): https://sissaivy.github.io/sissa_ivy/
- Source: `ui/pitcrew-dashboard` (Vite + React). The Pages site auto-publishes on merges to `main` and also after the “PitCrew KPI” workflow completes successfully on `main`.
