#!/usr/bin/env bash
set -euo pipefail
# Safely list and (optionally) delete remote branches merged into BASE (default: main).
# Default: DRY RUN (prints actions only).
# Usage:
#   scripts/delete_merged_branches.sh
#   BASE=main APPLY=1 scripts/delete_merged_branches.sh
BASE="${BASE:-main}"
APPLY="${APPLY:-0}"
git fetch --all --prune
merged=$(git branch -r --merged "origin/$BASE" | sed 's/^ *//' | grep -vE "origin/($BASE|HEAD)" || true)
if [[ -z "$merged" ]]; then
  echo "[info] nothing merged into $BASE"
  exit 0
fi
echo "[plan] merged into $BASE:"
echo "$merged"
if [[ "$APPLY" != "1" ]]; then
  echo "[dry-run] set APPLY=1 to delete the branches above from origin."
  exit 0
fi
while read -r b; do
  [[ -z "$b" ]] && continue
  name="${b#origin/}"
  echo "[delete] $name"
  git push origin --delete "$name" || true
done <<< "$merged"
echo "[ok] done."
