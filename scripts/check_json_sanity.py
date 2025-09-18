#!/usr/bin/env python3
import os, sys, json
from pathlib import Path

def find_json_files(root):
    for path in Path(root).rglob("*.json"):
        if ".venv" in path.parts or "node_modules" in path.parts or "__pycache__" in path.parts:
            continue
        yield path

def main():
    root = Path(os.getcwd())
    errors = 0
    for f in find_json_files(root):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                json.load(fh)
        except Exception as e:
            print(f"[fail] {f}: {e}", file=sys.stderr)
            errors += 1
    if errors:
        print(f"[fail] {errors} invalid JSON file(s)", file=sys.stderr)
        sys.exit(1)
    print("[ok] all JSON files valid")

if __name__ == "__main__":
    main()
