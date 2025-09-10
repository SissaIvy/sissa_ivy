#!/usr/bin/env python3
"""
Security bridge — runs closed_loop_security.py (strict & explore)
and emits a compact evaluator-style report that the KPI collector understands.

Outputs (default): aml_out/security_report.json
Schema mirrors aml_out/report.json used by ops/mechanic/kpi_collect.py:
{
  "evaluated_at_et": "...",
  "decision": "PASS|HOLD",
  "strict": { "failure_rate": 0.x, "explainability_rate": 0.x, "events": N, "actions": M },
  "explore": { ... },
  "gates": { "fail_rate_strict_max": 0.05, "fail_rate_explore_max": 0.05, "explainability_min": 0.95 },
  "source": "closed_loop_security"
}

Pure stdlib; imports closed_loop_security from repo root.
"""
import argparse, json, random, time
from pathlib import Path
from datetime import datetime

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root for import
try:
    import closed_loop_security as cls
except Exception as e:
    raise RuntimeError("closed_loop_security.py not found/importable at repo root") from e


def _gen_events(n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    types = ["login_attempt", "db_query", "api_call", "file_access", "net_flow"]
    events: list[dict] = []
    now = time.time()
    for i in range(n):
        sev = rng.choices([0, 1, 2, 3], weights=[55, 25, 15, 5])[0]  # mostly benign
        events.append({
            "id": f"ev-{seed}-{i}",
            "source": f"sensor-{1 + (i % 3)}",
            "type": rng.choice(types),
            "severity": sev,
            "timestamp": now - rng.uniform(0, 3600),
            "payload": {"user": f"u{rng.randint(1,9)}", "host": f"h{rng.randint(1,5)}"},
        })
    return events


def _run_profile(name: str, events: list[dict]) -> tuple[dict, dict]:
    sysm = cls.build_system(profile_name=name, audit_mode=False, dry_run_default=True)
    for ev in events:
        sysm.ingest_event(ev)
    res = sysm.process_events()
    imp = sysm.continuous_improvement()
    return res, imp


def _metrics_from_result(res: dict, imp: dict) -> dict:
    counts = dict(res.get("meta", {}).get("counts", {}))
    events = int(counts.get("events", 0)) or len(res.get("insights", []))
    actions = int(counts.get("actions", 0))
    failures = float(counts.get("failures", 0))
    if not actions:
        # fallback: count actions in insights
        for ins in res.get("insights", []):
            plan = (ins.get("metrics", {}) or {}).get("plan_notes")  # not reliable; keep 0 if missing
        # leave as 0 if not in counts
    # failure_rate via improvement if present
    fr = float(imp.get("failure_rate", (failures / max(1, events))))
    explains = sum(1 for ins in res.get("insights", []) if ins.get("explain"))
    ex_rate = (explains / events) if events else 0.0
    return {
        "events": events,
        "actions": actions,
        "failure_rate": round(fr, 4),
        "explainability_rate": round(ex_rate, 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="aml_out/security_report.json")
    ap.add_argument("--events", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--fr_gate_strict", type=float, default=0.05)
    ap.add_argument("--fr_gate_explore", type=float, default=0.05)
    ap.add_argument("--xai_gate", type=float, default=0.95)
    args = ap.parse_args()

    evs = _gen_events(args.events, args.seed)
    res_s, imp_s = _run_profile("strict", evs)
    res_e, imp_e = _run_profile("explore", evs)

    m_s = _metrics_from_result(res_s, imp_s)
    m_e = _metrics_from_result(res_e, imp_e)

    gates = {
        "fail_rate_strict_max": args.fr_gate_strict,
        "fail_rate_explore_max": args.fr_gate_explore,
        "explainability_min": args.xai_gate,
    }
    decision = "PASS"
    issues = []
    if m_s["failure_rate"] > gates["fail_rate_strict_max"]:
        decision = "HOLD"; issues.append("Strict failure rate above gate")
    if m_e["failure_rate"] > gates["fail_rate_explore_max"]:
        decision = "HOLD"; issues.append("Explore failure rate above gate")
    if min(m_s["explainability_rate"], m_e["explainability_rate"]) < gates["explainability_min"]:
        decision = "HOLD"; issues.append("Explainability below threshold")

    out = {
        "evaluated_at_et": datetime.utcnow().isoformat()+"Z",
        "decision": decision,
        "strict": m_s,
        "explore": m_e,
        "gates": gates,
        "source": "closed_loop_security",
    }
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"status":"ok","decision":decision,"out":str(outp)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

