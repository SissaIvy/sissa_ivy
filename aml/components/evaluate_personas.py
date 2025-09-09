import argparse, json, os
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict_results", type=str, required=True)
    ap.add_argument("--explore_results", type=str, required=True)
    ap.add_argument("--report_json", type=str, required=True)
    # Submit-time tunables (CLI wins; fallback to env; then defaults)
    ap.add_argument(
        "--max-cost-per-event-usd",
        type=float,
        default=float(os.getenv("EVAL_MAX_COST_PER_EVENT_USD", "0.001")),
    )
    ap.add_argument(
        "--max-token-cost-usd",
        type=float,
        default=float(os.getenv("EVAL_MAX_TOKEN_COST_USD", "1000000000")),
    )
    ap.add_argument(
        "--explainability-min",
        type=float,
        default=float(os.getenv("EVAL_EXPLAINABILITY_MIN", "0.95")),
    )
    ap.add_argument(
        "--fail-rate-strict-max",
        type=float,
        default=float(os.getenv("EVAL_FAIL_RATE_STRICT_MAX", "0.10")),
    )
    ap.add_argument(
        "--fail-rate-explore-max",
        type=float,
        default=float(os.getenv("EVAL_FAIL_RATE_EXPLORE_MAX", "0.15")),
    )
    args = ap.parse_args()

    strict = json.loads(Path(args.strict_results).read_text(encoding="utf-8"))
    explore = json.loads(Path(args.explore_results).read_text(encoding="utf-8"))

    def metrics(r):
        m = r["meta"]["counts"]
        actions = m.get("actions", 0)
        events = m.get("events", 1)
        failures = m.get("failures", 0)
        frate = failures / max(1, events)
        # crude proxies; refine with labeled truth later
        insights = r.get("insights", [])
        severity_weight = sum(i.get("trace", {}).get("severity", 0) for i in insights) / max(1, len(insights))
        explainability = sum(1 for i in insights if i.get("trace") and i.get("explain")) / max(1, len(insights))
        costs = r["meta"].get("costs", {})
        roi = r["meta"].get("roi", {})
        return {
            "events": events,
            "actions": actions,
            "failure_rate": frate,
            "avg_severity": round(severity_weight, 2),
            "explainability_rate": round(explainability, 2),
            "cost_per_event_usd": costs.get("blended_per_event_usd", 0),
            "run_cost_usd": costs.get("run_total_cost_usd", 0),
            "token_cost_usd": costs.get("token_cost_usd", 0),
            "roi_monthly_savings_usd": roi.get("monthly_savings_usd", 0),
        }

    s = metrics(strict)
    e = metrics(explore)
    # gates (overridable)
    gates = {
        "fail_rate_strict_max": args.fail_rate_strict_max,
        "fail_rate_explore_max": args.fail_rate_explore_max,
        "explainability_min": args.explainability_min,
        "max_cost_per_event_usd": args.max_cost_per_event_usd,
        "max_token_cost_usd": args.max_token_cost_usd,
    }
    decision = "PASS"
    issues = []
    if s["failure_rate"] > gates["fail_rate_strict_max"]:
        decision = "HOLD"
        issues.append("Strict failure rate too high")
    if e["failure_rate"] > gates["fail_rate_explore_max"]:
        decision = "HOLD"
        issues.append("Explore failure rate too high")
    if min(s["explainability_rate"], e["explainability_rate"]) < gates["explainability_min"]:
        decision = "HOLD"
        issues.append("Explainability below threshold")
    if max(s["cost_per_event_usd"], e["cost_per_event_usd"]) > gates["max_cost_per_event_usd"]:
        decision = "HOLD"
        issues.append("Cost per event above budget")
    if max(s.get("token_cost_usd", 0), e.get("token_cost_usd", 0)) > gates["max_token_cost_usd"]:
        decision = "HOLD"
        issues.append("Token cost above budget")

    report = {
        "evaluated_at_et": strict["meta"]["generated_at_et"],
        "strict": s,
        "explore": e,
        "gates": gates,
        "decision": decision,
        "issues": issues,
    }
    Path(args.report_json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report_json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
