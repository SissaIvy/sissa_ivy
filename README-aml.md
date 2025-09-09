# Azure ML Battle-Test for Closed-Loop Security System

This folder (`aml/`) contains an offline, deterministic battle-test for `closed_loop_security.py` using Azure Machine Learning components and a pipeline. It generates synthetic events, simulates strict vs exploratory profiles, evaluates gates, and optionally emits a bandit allocation suggestion.

## Contents

- Environment: `aml/env/conda.yml`
- Components:
  - `generate_scenarios` (JSONL synthetic events)
  - `simulate_closed_loop` (invokes orchestrator)
  - `evaluate_personas` (gates & metrics)
  - `bandit_allocator` (optional traffic split)
- Pipeline: `aml/pipelines/closed_loop_battletest.pipeline.yaml`
- Submitters: `aml/submit/submit_pipeline.sh`, `aml/submit/submit_pipeline.py`
- Sample data: `aml/data/scenarios.template.jsonl`

## Local quick check (no Azure account required)

```bash
python aml/components/generate_scenarios.py --n_events 50 --out_path /tmp/scenarios.jsonl
python aml/components/simulate_closed_loop.py --scenarios /tmp/scenarios.jsonl --profile strict --results_json /tmp/strict.json
python aml/components/simulate_closed_loop.py --scenarios /tmp/scenarios.jsonl --profile explore --results_json /tmp/explore.json
python aml/components/evaluate_personas.py --strict_results /tmp/strict.json --explore_results /tmp/explore.json --report_json /tmp/report.json
cat /tmp/report.json
```

## Azure ML (CLI) — one-time setup then submit

```bash
# Install ML extension
az extension add -n ml --yes

# (Optional) create compute
az ml compute create --name cpu-cluster --size STANDARD_DS3_V2 --min-instances 0 --max-instances 3 --type amlcompute || true

# Register env + components, then submit pipeline
bash aml/submit/submit_pipeline.sh
```

## Azure ML (SDK) alternative

```bash
export AZURE_SUBSCRIPTION_ID="<sub>"
export AZURE_RESOURCE_GROUP="<rg>"
export AZUREML_WORKSPACE_NAME="<ws>"
python aml/submit/submit_pipeline.py --seed 42 --n-events 500 --bandit-enable false
```

## Cost & ROI knobs (optional, but recommended)

You can model blended cloud costs, token budgets, and ROI/ROE directly in runs. The orchestrator reads environment variables and writes results to `meta.costs` and `meta.roi`.

### Knobs (env vars)
| Variable | Meaning | Example |
|---|---|---|
| `COST_APIM_MONTHLY` | APIM fixed monthly cost (USD) | `60` |
| `COST_FUNCTION_MONTHLY` | Functions fixed monthly (USD) | `0` |
| `COST_FRONTDOOR_MONTHLY` | Front Door/WAF fixed (USD) | `0` |
| `COST_APPINSIGHTS_MONTHLY` | App Insights fixed (USD) | `0` |
| `COST_AML_MONTHLY` | AML fixed (USD) | `0` |
| `COST_PER_EVENT_VAR` | Variable cost per event (USD) | `0.000001` |
| `COST_EXPECTED_EVENTS_MONTH` | Expected monthly events (blends fixed→per‑event) | `100000` |
| `TOKEN_ESCALATION_RATE` | Fraction of events that hit LLM | `0.05` |
| `TOKEN_AVG_PROMPT_TOKENS` / `TOKEN_AVG_COMPLETION_TOKENS` | Avg tokens if escalated | `1500` / `400` |
| `TOKEN_PRICE_PROMPT_PER_1K` / `TOKEN_PRICE_COMPLETION_PER_1K` | $/1K tokens | `0.00` / `0.00` (set if enabled) |
| `ROI_MTTR_BEFORE_MIN` / `ROI_MTTR_AFTER_MIN` | MTTR before/after (minutes) | `90` / `60` |
| `ROI_INCIDENTS_PER_MONTH` | Monthly incident count | `10` |
| `ROI_COST_PER_MINUTE_USD` | $/minute of downtime | `100` |
| `ROE_EQUITY_USD` | Equity invested (for ROE estimate) | `1500000` |

### Local run with cost/ROI knobs
```bash
export COST_APIM_MONTHLY=60 COST_EXPECTED_EVENTS_MONTH=100000
export ROI_MTTR_BEFORE_MIN=90 ROI_MTTR_AFTER_MIN=60 ROI_INCIDENTS_PER_MONTH=10 ROI_COST_PER_MINUTE_USD=100
python aml/components/generate_scenarios.py --n_events 50 --out_path /tmp/scenarios.jsonl
python aml/components/simulate_closed_loop.py --scenarios /tmp/scenarios.jsonl --profile strict --results_json /tmp/strict.json
python aml/components/evaluate_personas.py --strict_results /tmp/strict.json --explore_results /tmp/strict.json --report_json /tmp/report.json
# Optional: requires jq
jq '.strict.cost_per_event_usd, .strict.run_cost_usd, .strict.roi_monthly_savings_usd' /tmp/report.json
```

### Azure ML pipeline with knobs (CLI overrides)
Inject env vars into component steps when submitting the pipeline:
```bash
# Register env/components (first time):
az ml environment create --file aml/env/conda.yml || true
az ml component create --file aml/components/generate_scenarios.yaml
az ml component create --file aml/components/simulate_closed_loop.yaml
az ml component create --file aml/components/evaluate_personas.yaml

# Submit pipeline and set environment variables for sim steps
az ml job create --file aml/pipelines/closed_loop_battletest.pipeline.yaml \
  --set jobs.sim_strict.environment_variables.COST_APIM_MONTHLY=60 \
        jobs.sim_strict.environment_variables.COST_EXPECTED_EVENTS_MONTH=100000 \
        jobs.sim_explore.environment_variables.COST_APIM_MONTHLY=60 \
        jobs.sim_explore.environment_variables.COST_EXPECTED_EVENTS_MONTH=100000 \
        jobs.sim_strict.environment_variables.ROI_MTTR_BEFORE_MIN=90 \
        jobs.sim_strict.environment_variables.ROI_MTTR_AFTER_MIN=60 \
        jobs.sim_strict.environment_variables.ROI_INCIDENTS_PER_MONTH=10 \
        jobs.sim_strict.environment_variables.ROI_COST_PER_MINUTE_USD=100
```

### Tuning the budget gate
The evaluator enforces `max_cost_per_event_usd` (default `$0.001`). To change it, update the constant in `aml/components/evaluate_personas.py` and commit:
```python
gates = {
  "fail_rate_strict_max": 0.10,
  "fail_rate_explore_max": 0.15,
  "explainability_min": 0.95,
  "max_cost_per_event_usd": 0.001  # <-- adjust here
}
```
Tip: if you prefer this tunable at submit‑time, we can add a CLI arg or env to the evaluator and plumb it through.

## Gates and decisions

Evaluation reports PASS/HOLD based on:
- strict failure_rate <= 0.10
- explore failure_rate <= 0.15
- explainability_rate >= 0.95 for both

All steps operate in dry-run overlays; no external side effects.
