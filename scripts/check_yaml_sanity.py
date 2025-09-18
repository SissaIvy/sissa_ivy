#!/usr/bin/env python3
import os, sys
from pathlib import Path
try:
    import yaml
except ImportError:
    print("[fail] PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

def find_yaml_files(root):
    for path in Path(root).rglob("*.yml"):
        if ".venv" in path.parts or "node_modules" in path.parts or "__pycache__" in path.parts:
            continue
        yield path
    for path in Path(root).rglob("*.yaml"):
        if ".venv" in path.parts or "node_modules" in path.parts or "__pycache__" in path.parts:
            continue
        yield path

def main():
    root = Path(os.getcwd())
    errors = 0
    for f in find_yaml_files(root):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                yaml.safe_load(fh)
        except Exception as e:
            print(f"[fail] {f}: {e}", file=sys.stderr)
            errors += 1
    if errors:
        print(f"[fail] {errors} invalid YAML file(s)", file=sys.stderr)
        sys.exit(1)
    print("[ok] all YAML files valid")

if __name__ == "__main__":
    main()
