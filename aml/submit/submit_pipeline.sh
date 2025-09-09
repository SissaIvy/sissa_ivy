#!/usr/bin/env bash
set -euo pipefail

# Prereqs: Azure CLI + ML extension
# az extension add -n ml --yes

# Register environment (uses conda.yml contents). If your CLI requires explicit name/image, create via SDK alternative.
az ml environment create --file aml/env/conda.yml || true

# Register components
az ml component create --file aml/components/generate_scenarios.yaml
az ml component create --file aml/components/simulate_closed_loop.yaml
az ml component create --file aml/components/evaluate_personas.yaml
az ml component create --file aml/components/bandit_allocator.yaml

# Ensure compute exists
az ml compute create --name cpu-cluster --size STANDARD_DS3_V2 --min-instances 0 --max-instances 3 --type amlcompute || true

# Submit pipeline
az ml job create --file aml/pipelines/closed_loop_battletest.pipeline.yaml

# Example with budget/quality overrides at submit-time:
# az ml job create --file aml/pipelines/closed_loop_battletest.pipeline.yaml \
#   --set inputs.max_cost_per_event_usd=0.0008 \
#         inputs.max_token_cost_usd=0.10 \
#         inputs.explainability_min=0.97 \
#         inputs.fail_rate_strict_max=0.08 \
#         inputs.fail_rate_explore_max=0.12
