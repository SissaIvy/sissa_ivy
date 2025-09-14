"""Helper for viewing the AutoLearnCorrectLLM spec."""
from __future__ import annotations

import json
from pathlib import Path
import sys

SPEC_PATH = Path(__file__).with_name("auto_learn_correct.llm.v0.1.0.json")


def main() -> None:
    """Pretty-print the AutoLearnCorrectLLM specification."""
    with SPEC_PATH.open("r", encoding="utf-8") as f:
        spec = json.load(f)
    json.dump(spec, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
