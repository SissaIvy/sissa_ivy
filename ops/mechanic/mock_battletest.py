#!/usr/bin/env python3
"""
Deterministic, self-contained battle-test mock
- Emits aml_out/report.json with strict/explore metrics + gates + decision
- Models a realistic trade-off: lower failure_rate tends to reduce explainability (tunable rho)
- Pure stdlib; reproducible via --seed
"""
import argparse, json, math, random
from pathlib import Path
from datetime import datetime

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def bivar(norm_mu1, norm_mu2, norm_sd1, norm_sd2, rho, rng):
    # two correlated standard normals via Cholesky
    z1 = rng.gauss(0, 1)
    z2p = rng.gauss(0, 1)
    z2 = rho * z1 + math.sqrt(max(0.0, 1 - rho*rho)) * z2p
    return norm_mu1 + norm_sd1 * z1, norm_mu2 + norm_sd2 * z2

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="aml_out/report.json")
    ap.add_argument("--events", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)

    # Gates (used for decision + drawn by KPI collector)
    ap.add_argument("--fr_gate_strict", type=float, default=0.05)
    ap.add_argument("--fr_gate_explore", type=float, default=0.05)
    ap.add_argument("--xai_gate", type=float, default=0.95)

    # Means (default PASS)
    ap.add_argument("--fr_s_mean", type=float, default=0.020)
    ap.add_argument("--fr_e_mean", type=float, default=0.035)
    ap.add_argument("--xai_s_mean", type=float, default=0.970)
    ap.add_argument("--xai_e_mean", type=float, default=0.960)

    # Variation & correlation
    ap.add_argument("--fr_sd", type=float, default=0.010)     # absolute (0..1)
    ap.add_argument("--xai_sd", type=float, default=0.020)    # absolute (0..1)
    ap.add_argument("--rho", type=float, default=-0.55)       # FR↓ ↔ XAI↑ (negative)

    args = ap.parse_args()
    rng = random.Random(args.seed)

    # Draw one sample per profile with correlation (trade-off)
    fr_s, xai_s = bivar(args.fr_s_mean, args.xai_s_mean, args.fr_sd, args.xai_sd, args.rho, rng)
    fr_e, xai_e = bivar(args.fr_e_mean, args.xai_e_mean, args.fr_sd, args.xai_sd, args.rho, rng)
    fr_s = clamp(fr_s, 0.0, 1.0); fr_e = clamp(fr_e, 0.0, 1.0)
    xai_s = clamp(xai_s, 0.0, 1.0); xai_e = clamp(xai_e, 0.0, 1.0)

    # Counts (lightly noisy for realism)
    ev = max(1, int(args.events))
    act_s = int(ev * 1.1 + rng.uniform(-5, 5))
    act_e = int(ev * 1.05 + rng.uniform(-5, 5))

    strict = {
        "events": ev, "actions": act_s,
        "failure_rate": round(fr_s, 4),
        "avg_severity": 2.3,
        "explainability_rate": round(xai_s, 4)
    }
    explore = {
        "events": ev, "actions": act_e,
        "failure_rate": round(fr_e, 4),
        "avg_severity": 2.1,
        "explainability_rate": round(xai_e, 4)
    }

    gates = {
        "fail_rate_strict_max": args.fr_gate_strict,
        "fail_rate_explore_max": args.fr_gate_explore,
        "explainability_min": args.xai_gate
    }

    decision = "PASS";
    issues = []
    if strict["failure_rate"] > gates["fail_rate_strict_max"]:
        decision = "HOLD"; issues.append("Strict failure rate above gate")
    if explore["failure_rate"] > gates["fail_rate_explore_max"]:
        decision = "HOLD"; issues.append("Explore failure rate above gate")
    if min(strict["explainability_rate"], explore["explainability_rate"]) < gates["explainability_min"]:
        decision = "HOLD"; issues.append("Explainability below threshold")

    report = {
        "evaluated_at_et": datetime.utcnow().isoformat()+"Z",
        "strict": strict,
        "explore": explore,
        "gates": gates,
        "decision": decision,
        "issues": issues,
        "mock": {
            "seed": args.seed, "rho": args.rho,
            "fr_sd": args.fr_sd, "xai_sd": args.xai_sd
        }
    }

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status":"ok","decision":decision,"out":str(outp)}))

if __name__ == "__main__":
    main()
