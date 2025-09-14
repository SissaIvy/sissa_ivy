"""Helper for viewing the AutoLearnCorrectLLM spec."""
from __future__ import annotations

import json
import re
from pathlib import Path
import sys


def find_latest_spec_file() -> Path:
    """Find the latest version of the auto_learn_correct.llm spec file."""
    spec_dir = Path(__file__).parent
    pattern = "auto_learn_correct.llm.v*.json"
    candidates = list(spec_dir.glob(pattern))
    if not candidates:
        raise FileNotFoundError(f"No spec files matching {pattern} found in {spec_dir}")
    def version_key(p: Path):
        m = re.search(r"v(\d+)\.(\d+)\.(\d+)", p.name)
        if m:
            return tuple(int(x) for x in m.groups())
        return (0, 0, 0)
    return max(candidates, key=version_key)


SPEC_PATH = find_latest_spec_file()


def main() -> None:
    """Pretty-print the AutoLearnCorrectLLM specification."""
    try:
        with SPEC_PATH.open("r", encoding="utf-8") as f:
            spec = json.load(f)
    except FileNotFoundError:
        print(f"Error: Specification file '{SPEC_PATH}' not found.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON in '{SPEC_PATH}': {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: Could not open specification file '{SPEC_PATH}': {e}", file=sys.stderr)
        sys.exit(1)
    json.dump(spec, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()