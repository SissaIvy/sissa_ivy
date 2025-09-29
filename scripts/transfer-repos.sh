#!/usr/bin/env bash
# Transfer repositories using GitHub CLI
# Prerequisites: 
# - Install GitHub CLI (gh)
# - Authenticate with: gh auth login

echo "Transferring repositories from SissaIvy to mrobot787..."

# Array of repositories to transfer
repos=(
  "SissaIvy/Episodic-Memory-System-Python-"
  "SissaIvy/nlp-landing"
)

for repo in "${repos[@]}"; do
  echo "Transferring $repo to mrobot787..."
  if gh repo transfer "$repo" --to mrobot787; then
    echo "✓ Successfully initiated transfer of $repo"
  else
    echo "✗ Failed to transfer $repo"
  fi
done

echo "Done. Check your GitHub notifications for any transfer confirmations required."