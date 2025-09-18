.SHELLFLAGS := -eu -o pipefail -c

# Set shell and recipe prefix at the very top (required for correct parsing)

ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)SHELL := bash

.SHELLFLAGS := -eu -o pipefail -c

.PHONY: repo-hygiene drift-report-local# Avoid tabs entirely: any recipe line starting with "|" is treated as a command

.RECIPEPREFIX := |


SHELL := bash
ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)

.PHONY: repo-hygiene drift-report-local

repo-hygiene:
	cd $(ROOT)
	python scripts/normalize_unicode.py
	python scripts/check_no_bidi.py
	python scripts/check_repo_layout.py
	test -f scripts/check_json_sanity.py && python scripts/check_json_sanity.py || true
	test -f scripts/check_yaml_sanity.py && python scripts/check_yaml_sanity.py || true
	command -v pre-commit >/dev/null 2>&1 && pre-commit run --all-files || true
	echo "[ok] repo hygiene checks complete"


	cd $(ROOT)
	bash scripts/branch_cleanup_status.sh | tee branch_drift.txt
	echo "[ok] wrote branch_drift.txt"
drift-report-local:ROOT := $(shell git rev-parse --show-toplevel 2>/dev/null || pwd)

	cd "$(ROOT)"ENV ?= DEV

	bash scripts/branch_cleanup_status.sh | tee branch_drift.txt

	echo "[ok] wrote branch_drift.txt"

.PHONY: help snow-bridge snow-sync snow-bridge-prod snow-sync-prod

help:
| echo "make snow-bridge ENV=PROD    # DRY-RUN: no ServiceNow calls"
| echo "make snow-sync               # Show/refresh DRY-RUN status files"
| echo "make snow-bridge-prod ENV=PROD   # REAL run (needs SNOW_* creds + non-placeholder instance)"
| echo "make snow-sync-prod              # REAL status sync"


# DRY-RUN (always safe). The bootstrap ensures intel exists and writes ticket files.
snow-bridge:
| cd "$(ROOT)" && SNOW_DRY_RUN=1 ENV_SCOPE="$(ENV)" bash scripts/bootstrap.sh


# DRY-RUN status helper (bootstrap already produced the files)
snow-sync:
| cd "$(ROOT)" && { ls -l reports/tickets || true; } && \
  { test -f reports/tickets/snow_incidents_status.json && head -n 40 reports/tickets/snow_incidents_status.json || true; }


# REAL runs (opt-in). You must export valid SNOW_* env and use a non-placeholder instance.
snow-bridge-prod:
| cd "$(ROOT)" && SNOW_DRY_RUN=0 ENV_SCOPE="$(ENV)" bash scripts/bootstrap.sh



# Repo hygiene and branch drift reporting
.PHONY: repo-hygiene drift-report-local

repo-hygiene:
| cd "$(ROOT)"
| python scripts/normalize_unicode.py
| python scripts/check_no_bidi.py
| python scripts/check_repo_layout.py
| command -v pre-commit >/dev/null 2>&1 && pre-commit run --all-files || true
| echo "[ok] repo hygiene checks complete"


# local branch-drift report (no writes to remote)
drift-report-local:
| cd "$(ROOT)"
| bash scripts/branch_cleanup_status.sh | tee branch_drift.txt
| echo "[ok] wrote branch_drift.txt"


.PHONY: onboard
onboard:
| chmod +x scripts/onboard.sh
| bash scripts/onboard.sh

trigger_all_ci:
	@ROOT="$(shell git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$$PWD")"; \
	mkdir -p "$$ROOT/scripts"; \
	cat > "$$ROOT/scripts/trigger_all_ci.sh" <<'SH' ; \
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$$PWD")"
cd "$$ROOT"

DEFAULT_BRANCH="$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo main)"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

workflows=(
  "hygiene.yml"
  "schema-lint.yml"
  "bidi-guard.yml"
  "layout-guard.yml"
)

dispatch() {
  local wf="$$1"
  echo "→ Triggering $$wf on $${DEFAULT_BRANCH}..."
  if gh workflow run "$$wf" --ref "$${DEFAULT_BRANCH}" >/dev/null 2>&1; then
    echo "✓ $$wf dispatched on $${DEFAULT_BRANCH}"
    return 0
  fi
  echo "…not on $${DEFAULT_BRANCH}; trying $${CURRENT_BRANCH}..."
  if gh workflow run "$$wf" --ref "$${CURRENT_BRANCH}" >/dev/null 2>&1; then
    echo "✓ $$wf dispatched on $${CURRENT_BRANCH}"
    return 0
  fi
  echo "✗ $$wf not found on $${DEFAULT_BRANCH} or $${CURRENT_BRANCH} — skip"
  return 1
}

for wf in "$${workflows[@]}"; do
  dispatch "$$wf" || true
done

echo
echo "Latest workflow runs:"
gh run list --limit 10 --json databaseId,displayTitle,headBranch,status,conclusion \
  --template '{{range .}}{{printf "%8d  %-24s  %-24s  %-10s  %-10s\n" .databaseId .displayTitle .headBranch .status .conclusion}}{{end}}'
SH
	chmod +x "$$ROOT/scripts/trigger_all_ci.sh"; \
	echo "[ok] wrote $$ROOT/scripts/trigger_all_ci.sh"

# Run existing enhanced workflow dispatcher script (requires PAT with repo+workflow if not using UI token)
.PHONY: ci-dispatch
ci-dispatch:
| cd "$(ROOT)" && bash scripts/trigger_all_ci.sh || { echo "Hint: ensure 'gh auth login' with a PAT that includes 'workflow' scope"; exit 1; }
