#!/usr/bin/env python3
"""Validate a probe JSON record (file path or stdin) against endpoint_state.schema.json.

Usage:
  python validate_probe_record.py sample.json
  cat sample.json | python validate_probe_record.py -
"""
from __future__ import annotations
import sys, json
from pathlib import Path

try:
    import jsonschema  # type: ignore
except ImportError:
    print("jsonschema not installed. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

SCHEMA_PATH = Path(__file__).parent / "schema" / "endpoint_state.schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 1
    src = sys.argv[1]
    data = sys.stdin.read() if src == '-' else Path(src).read_text(encoding='utf-8')
    try:
        obj = json.loads(data)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}", file=sys.stderr)
        return 2
    try:
        jsonschema.validate(instance=obj, schema=SCHEMA)
    except jsonschema.ValidationError as ve:
        print(f"ValidationError: {ve.message}", file=sys.stderr)
        return 3
    print("VALID")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
