#!/usr/bin/env python3
"""Validate a Linux probe JSON against schema/linux_probe.schema.json.

Usage:
  python scripts/validate_linux_probe.py path/to/probe.json
  python cogsec/collectors/cogsec_probe_linux.py | python scripts/validate_linux_probe.py -

Exit codes:
  0 valid
  1 schema validation failure
  2 usage / IO / dependency error
"""
from __future__ import annotations
import json, sys
from pathlib import Path

SCHEMA_PATH = Path('schema/linux_probe.schema.json')

try:
    import jsonschema  # type: ignore
except Exception:  # pragma: no cover
    print("[validate] error: 'jsonschema' not installed. Run: pip install jsonschema", file=sys.stderr)
    raise SystemExit(2)


def load_schema():
    if not SCHEMA_PATH.exists():
        print(f"[validate] schema missing: {SCHEMA_PATH}", file=sys.stderr)
        raise SystemExit(2)
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"[validate] failed reading schema: {e}", file=sys.stderr)
        raise SystemExit(2)


def load_record(arg: str):
    if arg == '-':
        try:
            return json.load(sys.stdin)
        except Exception as e:
            print(f"[validate] stdin JSON load error: {e}", file=sys.stderr)
            raise SystemExit(2)
    p = Path(arg)
    if not p.exists():
        print(f"[validate] file not found: {p}", file=sys.stderr)
        raise SystemExit(2)
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"[validate] JSON load error: {e}", file=sys.stderr)
        raise SystemExit(2)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: validate_linux_probe.py <probe.json|->", file=sys.stderr)
        return 2
    record = load_record(argv[1])
    schema = load_schema()
    try:
        jsonschema.validate(instance=record, schema=schema)  # type: ignore
    except jsonschema.ValidationError as ve:  # type: ignore
        print(f"[validate] schema validation FAILED: {ve.message}\nPATH: {'/'.join(str(p) for p in ve.path)}", file=sys.stderr)
        return 1
    print("[validate] OK")
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main(sys.argv))
