#!/usr/bin/env bash
set -euo pipefail

# Purpose: Trigger a set of GitHub Actions workflows with robust diagnostics.
# Works from any subdirectory; falls back across refs; surfaces permission issues.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")"
cd "$ROOT"

REPO_SLUG="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo unknown/unknown)"
DEFAULT_BRANCH="$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || echo main)"
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "$DEFAULT_BRANCH")"

# Workflows we want to trigger (filenames as they exist in .github/workflows)
workflows=(
  hygiene.yml
  schema-lint.yml
  bidi-guard.yml
  layout-guard.yml
)

bold() { printf '\033[1m%s\033[0m' "$*"; }
warn() { printf '\033[33mWARN:\033[0m %s\n' "$*"; }
err()  { printf '\033[31mERR:\033[0m %s\n' "$*"; }
ok()   { printf '\033[32mOK:\033[0m %s\n' "$*"; }

echo "Repo: $(bold "$REPO_SLUG")  Default: $(bold "$DEFAULT_BRANCH")  Current: $(bold "$CURRENT_BRANCH")"

diagnose_scopes() {
  echo "Collecting token scope information..." >&2
  # Capture headers only; X-OAuth-Scopes reveals granted scopes
  if headers="$(gh api -i repos/$REPO_SLUG 2>/dev/null | sed -n '1,30p')"; then
    echo "$headers" | grep -i '^x-oauth-scopes' || warn "Could not read X-OAuth-Scopes header (token may be installation / GITHUB_TOKEN)."
  else
    warn "Unable to query API headers for scope diagnostics."
  fi
  cat <<'INFO' >&2
If you do NOT see 'workflow' in X-OAuth-Scopes, create a classic PAT with 'repo' and 'workflow' scopes and re-auth:
  gh auth login --with-token < token.txt
Or export GH_TOKEN / GITHUB_TOKEN to that PAT for this shell.
INFO
}

trigger_one() {
  local wf="$1"
  local ref_attempt
  echo "--- $(bold "Dispatch $wf") ---"

  # Quick existence check
  if ! gh workflow view "$wf" >/dev/null 2>&1; then
    err "Workflow $wf not visible via API (maybe filename mismatch or not pushed)."
    return 1
  fi

  for ref_attempt in "$CURRENT_BRANCH" "$DEFAULT_BRANCH"; do
    echo "Attempting dispatch on ref: $ref_attempt"
    if output_json="$(gh workflow run "$wf" --ref "$ref_attempt" --json 2>&1)"; then
      ok "Dispatched $wf on $ref_attempt"
      return 0
    else
      status=$?
      if grep -q 'Resource not accessible by integration' <<<"$output_json"; then
        err "403 permission issue dispatching $wf on $ref_attempt"
        diagnose_scopes
        return 2
      fi
      warn "Failed on $ref_attempt (exit $status). Raw output:"
      echo "$output_json" >&2
    fi
  done
  err "Unable to dispatch $wf on any ref (tried: $CURRENT_BRANCH, $DEFAULT_BRANCH)"
  return 3
}

failures=0
for wf in "${workflows[@]}"; do
  trigger_one "$wf" || failures=$((failures+1))
done

echo
if (( failures > 0 )); then
  err "$failures workflow(s) failed to dispatch. See above diagnostics."
  exit 1
fi
ok "All workflows dispatched successfully."

echo
echo "Recent runs (limit 12):"
gh run list --limit 12 --json databaseId,displayTitle,headBranch,status,conclusion,workflowName \
  --template '{{range .}}{{printf "%8d  %-22s %-18s %-10s %-10s %-18s\n" .databaseId .workflowName .headBranch .status .conclusion .displayTitle}}{{end}}' || true
