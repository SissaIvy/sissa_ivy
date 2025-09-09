# MIGRATION: console script alias -> `closed-loop-security`

This change adds a new console script alias: `closed-loop-security` which points to
the same CLI entrypoint as the existing `episodic-memory` script. We keep the
existing `episodic-memory` script as a shim for backward compatibility for at
least one release cycle.

## Why
- Provide a clearer, brand-aligned binary name without immediately breaking users.

## What changed
- Added `closed-loop-security = "memory_cli:main"` to `[project.scripts]`
  in `pyproject.toml`. The old `episodic-memory` entry remains.

## How to test locally
1. Install editable package and list console scripts:
   ```bash
   pip install -e .
   python - <<'PY'
from importlib.metadata import entry_points
try:
    eps = entry_points().select(group="console_scripts")
    names = [e.name for e in eps]
except Exception:
    eps = entry_points()
    names = [e.name for e in eps.get("console_scripts", [])]
print("console_scripts:", sorted(names))
PY
   ```
   You should see both `episodic-memory` and `closed-loop-security`.

2. Try the two help outputs:
   ```bash
   closed-loop-security --help
   episodic-memory --help
   ```

3. Run unit tests:
   ```bash
   python -m unittest discover -s tests -p "test_*.py" -v
   ```

## Deprecation plan
- Keep the shim for one release cycle. Mark `episodic-memory` as deprecated in the next minor release notes
  and remove it in a future breaking release (documented in CHANGELOG).

## Rollback
- Revert the commit that adds the new script and republish:
  ```bash
  git revert <commit-sha>
  git push origin main
  ```
