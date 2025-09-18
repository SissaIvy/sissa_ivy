#!/usr/bin/env bash
set -euo pipefail

# Find repo root from any subdirectory
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$PWD")"
cd "$ROOT"

# Trigger all main CI workflows via GitHub CLI
declare -a workflows=(
  "hygiene.yml"
  "schema-lint.yml"
  "bidi-guard.yml"
  "layout-guard.yml"
)

for wf in "${workflows[@]}"; do
  echo "Triggering $wf..."
  gh workflow run "$wf"
done
