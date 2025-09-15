"""Helper for viewing the AutoLearnCorrectLLM spec."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import re

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
    with SPEC_PATH.open("r", encoding="utf-8") as f:
        spec = json.load(f)
    json.dump(spec, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
