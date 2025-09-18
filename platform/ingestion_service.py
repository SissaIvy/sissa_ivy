"""Minimal local ingestion prototype.

Features:
- Validates incoming probe JSON against local JSON Schema (draft 2020-12)
- Stores latest record per host plus an append-only events table (SQLite)
- Exposes a simple CLI for ingesting from a file/stdin and querying state

Usage:
  python -m platform.ingestion_service ingest sample.json
  cat sample.json | python -m platform.ingestion_service ingest -
  python -m platform.ingestion_service get HOSTNAME
  python -m platform.ingestion_service list

Note: This is a prototype: no auth, no concurrency controls.
"""
from __future__ import annotations
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

try:
    import jsonschema  # type: ignore
except ImportError as e:  # pragma: no cover
    print("jsonschema package required. Install with: pip install jsonschema", file=sys.stderr)
    raise

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "endpoint_state.schema.json"
DB_PATH = Path(__file__).resolve().parent / "ingestion.sqlite"

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    ENDPOINT_STATE_SCHEMA = json.load(f)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS endpoint_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL,
            ts TEXT NOT NULL,
            record TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS endpoint_latest (
            host TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            record TEXT NOT NULL
        )
        """
    )
    return conn


def validate_record(obj: dict) -> None:
    jsonschema.validate(instance=obj, schema=ENDPOINT_STATE_SCHEMA)


def ingest_record(obj: dict) -> None:
    validate_record(obj)
    host = obj["host"]
    ts = obj["timestamp"]
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO endpoint_events(host, ts, record) VALUES (?,?,?)",
            (host, ts, json.dumps(obj)),
        )
        cur.execute(
            "INSERT INTO endpoint_latest(host, ts, record) VALUES (?,?,?) ON CONFLICT(host) DO UPDATE SET ts=excluded.ts, record=excluded.record",
            (host, ts, json.dumps(obj)),
        )
        conn.commit()
    finally:
        conn.close()


def load_json(source: str) -> dict:
    data = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    return json.loads(data)


def get_latest(host: str) -> dict | None:
    conn = _connect()
    try:
        cur = conn.cursor()
        row = cur.execute(
            "SELECT record FROM endpoint_latest WHERE host=?", (host,)
        ).fetchone()
        if not row:
            return None
        return json.loads(row[0])
    finally:
        conn.close()


def list_hosts() -> list[str]:
    conn = _connect()
    try:
        cur = conn.cursor()
        return [r[0] for r in cur.execute("SELECT host FROM endpoint_latest ORDER BY host").fetchall()]
    finally:
        conn.close()


def cli(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="ingestion_service")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest", help="Ingest a JSON record (file path or - for stdin)")
    p_ing.add_argument("source")

    p_get = sub.add_parser("get", help="Get latest record for host")
    p_get.add_argument("host")

    sub.add_parser("list", help="List known hosts")

    args = p.parse_args(argv)

    try:
        if args.cmd == "ingest":
            obj = load_json(args.source)
            ingest_record(obj)
            print(f"Ingested host={obj['host']} ts={obj['timestamp']}")
            return 0
        if args.cmd == "get":
            rec = get_latest(args.host)
            if not rec:
                print("Not found", file=sys.stderr)
                return 1
            print(json.dumps(rec, indent=2))
            return 0
        if args.cmd == "list":
            for h in list_hosts():
                print(h)
            return 0
    except jsonschema.ValidationError as ve:
        print(f"ValidationError: {ve.message}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as je:
        print(f"JSONDecodeError: {je}", file=sys.stderr)
        return 2
    except Exception as e:  # pragma: no cover
        print(f"Error: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(cli(sys.argv[1:]))
