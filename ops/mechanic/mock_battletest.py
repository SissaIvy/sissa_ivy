#!/usr/bin/env python3
"""
Mock offline battle-test generator
- Emits aml_out/report.json compatible with ops/mechanic/kpi_collect.py
- No external deps; deterministic defaults; thresholds control PASS/HOLD.
"""
import argparse, json, pathlib, random
from datetime import datetime

def decide(fr: float, ex: float, fr_gate: float, xai_gate: float) -> bool:
    return (fr <= fr_gate) and (ex >= xai_gate)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="aml_out/report.json")
    ap.add_argument("--events", type=int, default=200)
    ap.add_argument("--strict_fr", type=float, default=0.02)
    ap.add_argument("--explore_fr", type=float, default=0.035)
    ap.add_argument("--strict_xai", type=float, default=0.97)
    ap.add_argument("--explore_xai", type=float, default=0.96)
    ap.add_argument("--fr_gate", type=float, default=0.05)
    ap.add_argument("--xai_gate", type=float, default=0.95)
    args = ap.parse_args()

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Deterministic actions count with small variance
    random.seed(42)
    s_actions = args.events * 5 + random.randint(-3, 3)
    e_actions = args.events * 5 + random.randint(-3, 3)

    s_ok = decide(args.strict_fr, args.strict_xai, args.fr_gate, args.xai_gate)
    e_ok = decide(args.explore_fr, args.explore_xai, args.fr_gate, args.xai_gate)
    decision = "PASS" if (s_ok and e_ok) else "HOLD"

    report = {
        "evaluated_at_et": datetime.utcnow().isoformat()+"Z",
        "decision": decision,
        "strict": {
            "failure_rate": round(float(args.strict_fr), 6),
            "explainability_rate": round(float(args.strict_xai), 6),
            "events": int(args.events),
            "actions": int(s_actions),
        },
        "explore": {
            "failure_rate": round(float(args.explore_fr), 6),
            "explainability_rate": round(float(args.explore_xai), 6),
            "events": int(args.events),
            "actions": int(e_actions),
        }
    }
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status":"ok","decision":decision}))

if __name__ == "__main__":
    raise SystemExit(main())
