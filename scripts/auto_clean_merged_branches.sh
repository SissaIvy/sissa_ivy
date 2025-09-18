#!/usr/bin/env bash
set -euo pipefail
# Automate remote branch cleanup: dry-run and apply modes.
# Usage:
#   scripts/auto_clean_merged_branches.sh [--apply]
#   --apply: actually delete merged branches (default is dry-run)

BASE="${BASE:-main}"
APPLY=0
if [[ "${1:-}" == "--apply" ]]; then
  APPLY=1
fi

echo "[info] Fetching all remotes and pruning..."
git fetch --all --prune
merged=$(git branch -r --merged "origin/$BASE" | sed 's/^ *//' | grep -vE "origin/($BASE|HEAD)" || true)
if [[ -z "$merged" ]]; then
  echo "[info] No remote branches merged into $BASE."
  exit 0
fi

echo "[plan] Remote branches merged into $BASE:"
echo "$merged"
if [[ "$APPLY" != "1" ]]; then
  echo "[dry-run] No branches deleted. Use --apply to actually delete."
  exit 0
fi

while read -r b; do
  [[ -z "$b" ]] && continue
  name="${b#origin/}"
  echo "[delete] $name"
  git push origin --delete "$name" || true
done <<< "$merged"
echo "[ok] Branch cleanup complete."
