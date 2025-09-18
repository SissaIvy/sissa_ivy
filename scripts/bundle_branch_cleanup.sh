#!/usr/bin/env bash
set -euo pipefail

# ------------------------------
# Config (override via env)
# ------------------------------
AUTO_STASH="${AUTO_STASH:-1}"      # 1 = stash uncommitted changes automatically
PUSH="${PUSH:-0}"                  # 1 = push with --force-with-lease
SQUASH="${SQUASH:-0}"              # 1 = squash branch into a single commit
SQUASH_MSG="${SQUASH_MSG:-chore: compress branch history after hygiene & rebase}"
BASE="${BASE:-}"                   # default branch name; auto-detected if empty
GIT_NOISE_PATHS=(
  "node_modules"
  "ui/psyops-war-room/dist"
  "dist" "build"
  "reports"
  ".venv" "__pycache__" ".pytest_cache" ".mypy_cache"
  "coverage*" "*.log" "dashboard.log"
)

# Strong .gitignore block (idempotent)
read -r -d '' GITIGNORE_BLOCK <<'EOF' || true
### repo-hygiene (managed)
__pycache__/
.venv/
*.pyc
.pytest_cache/
.mypy_cache/
coverage*
*.log
node_modules/
ui/psyops-war-room/dist/
dist/
build/
reports/
!reports/.gitkeep
EOF

# ------------------------------
# Helpers
# ------------------------------
step(){ printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
warn(){ printf '\033[1;33m[warn]\033[0m %s\n' "$*"; }
die(){ printf '\033[1;31m[fail]\033[0m %s\n' "$*"; exit 1; }

# ------------------------------
# Preconditions
# ------------------------------
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a Git repo."
CUR_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
[[ "$CUR_BRANCH" != "main" && "$CUR_BRANCH" != "master" ]] || die "Refusing to run on $CUR_BRANCH. Checkout a feature branch."

git fetch --all --prune

if [[ -z "$BASE" ]]; then
  # Try origin/HEAD → origin/<default>
  BASE="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@' || true)"
  [[ -n "$BASE" ]] || BASE="main"
fi
BASE_REMOTE="origin/$BASE"
git rev-parse --verify "$BASE_REMOTE" >/dev/null 2>&1 || die "Cannot find $BASE_REMOTE"

# ------------------------------
# Optional stash
# ------------------------------
STASH_REF=""
if [[ "$AUTO_STASH" == "1" ]]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    step "Stashing local changes"
    STASH_REF="$(git stash push -u -m "bundle_cleanup_$(date +%Y%m%d-%H%M%S)" || true)"
  fi
fi

# ------------------------------
# Safety backup
# ------------------------------
BACKUP="backup/$(date +%Y%m%d-%H%M)-$CUR_BRANCH"
step "Creating safety backup branch: $BACKUP"
git branch "$BACKUP" >/dev/null 2>&1 || warn "Backup branch already exists: $BACKUP"

# ------------------------------
# .gitignore hygiene + untrack noise
# ------------------------------
step "Ensuring .gitignore hygiene and untracking generated outputs"
if [[ ! -f .gitignore ]] || ! grep -q "repo-hygiene (managed)" .gitignore; then
  printf "%s\n" "$GITIGNORE_BLOCK" >> .gitignore
  git add .gitignore
fi

# Untrack known noisy paths (safe if absent)
for p in "${GIT_NOISE_PATHS[@]}"; do
  git ls-files -z -- "$p" 2>/dev/null | xargs -0 -r git rm -r --cached --quiet || true
done

if ! git diff --cached --quiet; then
  git commit -m "chore: untrack generated/build outputs; add .gitignore" || true
else
  warn "No index changes to commit for hygiene step."
fi

# ------------------------------
# Rebase onto base
# ------------------------------
step "Rebasing $CUR_BRANCH onto $BASE_REMOTE"
set +e
git rebase "$BASE_REMOTE"
REB=$?
set -e
if [[ $REB -ne 0 ]]; then
  die "Rebase stopped with conflicts. Resolve them, run: git rebase --continue (or --abort), then re-run this script."
fi

# ------------------------------
# Optional squash
# ------------------------------
if [[ "$SQUASH" == "1" ]]; then
  step "Squashing branch to a single commit relative to $BASE_REMOTE"
  git reset --soft "$BASE_REMOTE"
  git commit -m "$SQUASH_MSG"
fi

# ------------------------------
# Optional push
# ------------------------------
if [[ "$PUSH" == "1" ]]; then
  step "Pushing with --force-with-lease"
  git push --force-with-lease
else
  warn "Not pushing. When satisfied, run: git push --force-with-lease"
fi

# ------------------------------
# Optional unstash
# ------------------------------
if [[ -n "$STASH_REF" ]]; then
  step "Restoring stashed changes"
  set +e
  git stash pop || warn "Stash pop had conflicts; resolve manually."
  set -e
fi

# ------------------------------
# Summary
# ------------------------------
step "Done"
git status -sb
echo
echo "Ahead/behind vs $BASE_REMOTE:"
git rev-list --left-right --count "$BASE_REMOTE"...HEAD | awk '{print "behind/ahead:",$1"/"$2}'
echo
echo "Tip: review your PR; the diff should now be minimal and sane."
