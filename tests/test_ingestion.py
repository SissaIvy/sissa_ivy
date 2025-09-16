import json
from pathlib import Path
import subprocess
import sys
import pathlib

import pytest

# Ensure repository root is on sys.path for editable-style imports when not installed.
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cogsec_platform import ingestion_service as ing

SAMPLE = {
    "schema_version": "1.1.1",
    "host": "TESTHOST",
    "timestamp": "2025-01-01T00:00:00Z",
    "os": "Windows",
    "cpu": 12.5,
    "mem": 50.0,
    "disk": 33.3,
    "net_in_bps": 0,
    "net_out_bps": 0,
    "net_in": 0,
    "net_out": 0,
    "firewall_enabled": True,
    "rdp_enabled": False,
    "rdp_nla_enabled": None,
    "controls": {"av_vendor": "Windows Defender", "services": {}},
    "patch": {"missing": [], "required_total": 0, "missing_count": 0},
}

def test_validate_and_ingest(tmp_path, monkeypatch):
    db = tmp_path / "ingestion.sqlite"
    monkeypatch.setenv("INGESTION_DB", str(db))  # (Not used currently but reserved)
    # ingest via module function
    ing.ingest_record(SAMPLE)
    rec = ing.get_latest("TESTHOST")
    assert rec["host"] == "TESTHOST"
    assert rec["schema_version"].startswith("1.")


def test_cli_roundtrip(tmp_path, monkeypatch):
    sample_file = tmp_path / "sample.json"
    sample_file.write_text(json.dumps(SAMPLE), encoding="utf-8")
    # call CLI ingest
    proc = subprocess.run(
        [sys.executable, "-m", "cogsec_platform.ingestion_service", "ingest", str(sample_file)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    # get record
    proc2 = subprocess.run(
        [sys.executable, "-m", "cogsec_platform.ingestion_service", "get", "TESTHOST"],
        capture_output=True,
        text=True,
    )
    assert proc2.returncode == 0
    obj = json.loads(proc2.stdout)
    assert obj["host"] == "TESTHOST"


def test_validator_script(tmp_path):
    sample_file = tmp_path / "sample.json"
    sample_file.write_text(json.dumps(SAMPLE), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "validate_probe_record.py", str(sample_file)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "VALID" in proc.stdout


def test_schema_missing_required(tmp_path):
    bad = dict(SAMPLE)
    bad.pop("host")
    bf = tmp_path / "bad.json"
    bf.write_text(json.dumps(bad), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "validate_probe_record.py", str(bf)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "ValidationError" in proc.stderr
