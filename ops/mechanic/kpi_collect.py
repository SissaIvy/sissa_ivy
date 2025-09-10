#!/usr/bin/env python3
"""
PitCrew KPI collector (visuals upgraded)
- Consumes offline evaluator output (report.json) from aml/components/evaluate_personas.py
- Computes KPIs with gate-aware shaping; surfaces strict/explore + overall.
- Emits:
  - mech_out/mechanic_kpi.json
  - mech_out/summary.md
  - badges/*.svg : status, kpi, xai, failrate + three visual charts
Design:
- Pure stdlib, offline, deterministic. Matches battle-test flow (gen → sim → eval).  # Source: repo plan
"""
import argparse, json, math, pathlib, sys
from datetime import datetime

# ------------------------------- Palette --------------------------------------
PAL = {
    "asphalt": "#0D1117",
    "grid":    "#1F2937",
    "label":   "#E5E7EB",
    "muted":   "#9CA3AF",
    "strict":  "#2563EB",   # Racing Blue
    "explore": "#F59E0B",   # Safety Amber
    "pass":    "#2EA44F",
    "hold":    "#D73A49",
    "redline": "#EF4444",
}

# ----------------------------- Badge generator --------------------------------
def _badge_svg(label: str, value: str, color: str) -> str:
    label_w = max(60, 7 * len(label) + 20)
    value_w = max(60, 7 * len(value) + 20)
    total_w = label_w + value_w
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="20" role="img" aria-label="{label}: {value}">
  <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <mask id="m"><rect width="{total_w}" height="20" rx="3" fill="#fff"/></mask>
  <g mask="url(#m)">
    <rect width="{label_w}" height="20" fill="#555"/>
    <rect x="{label_w}" width="{value_w}" height="20" fill="{color}"/>
    <rect width="{total_w}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_w/2:.1f}" y="14">{label}</text>
    <text x="{label_w + value_w/2:.1f}" y="14">{value}</text>
  </g>
</svg>'''

def _write_badge(path: pathlib.Path, label: str, value: str, color: str):
    path.write_text(_badge_svg(label, value, color), encoding="utf-8")

def _color_scale(score: float) -> str:
    # 0..100 → red/yellow/green
    if score >= 90: return PAL["pass"]
    if score >= 75: return "#dfb317"
    return PAL["hold"]

# ------------------------------- KPI calc -------------------------------------
def _kpi_from_metrics(
    m: dict,
    weight_rel: float = 0.75,
    weight_xai: float = 0.25,
    fr_gate: float = 0.10,
    xai_gate: float = 0.95,
    k_shape: float = 12.0,
) -> float:
    """
    Gate-aware blended KPI in [0,100].
    - Reliability (failure_rate lower is better) shaped around fr_gate.
    - Explainability (explainability_rate higher is better) shaped around xai_gate.
    """
    fr = float(m.get("failure_rate", 0.2))           # 0..1 (lower is better)
    ex = float(m.get("explainability_rate", 0.0))    # 0..1
    # Gate-aware shaping (steep around thresholds)
    rel = 1.0 / (1.0 + math.exp(k_shape * (fr - fr_gate)))           # high when fr << gate
    xai = 1.0 / (1.0 + math.exp(-k_shape * (ex - xai_gate)))         # high when ex >> gate
    rel = max(0.0, min(1.0, rel))
    xai = max(0.0, min(1.0, xai))
    wr = max(0.0, min(1.0, weight_rel)); wx = max(0.0, min(1.0, weight_xai))
    if wr + wx == 0: wr, wx = 1.0, 0.0
    score = (wr * rel + wx * xai) / (wr + wx)
    return round(100.0 * score, 1)

# --------------------------- SVG helper primitives ----------------------------
def _svg_text(x, y, t, anchor='start', size=11, fill=None):
    fill = fill or PAL["label"]
    return (f"<text x='{x:.1f}' y='{y:.1f}' fill='{fill}' font-size='{size}' "
            f"font-family='-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif' "
            f"text-anchor='{anchor}' dominant-baseline='middle'>{t}</text>")

def _bevel_bar_path(x, y, w, h, bevel=3):
    # speed-bevel leading edge (left)
    if w <= 0: return f"M{x},{y+h}Z"
    x2 = x + w
    return f"M{x},{y+h} L{x},{y+bevel} L{(x+bevel)},{y} L{x2},{y} L{x2},{y+h} Z"

def _defs_common(def_id_suffix="a"):
    # Hatch (45°) for explore; Checkered pattern for finish caps; tiny flag glyph.
    return f"""
    <defs>
      <pattern id="expHatch-{def_id_suffix}" patternUnits="userSpaceOnUse" width="6" height="6"
               patternTransform="rotate(45)">
        <line x1="0" y1="0" x2="0" y2="6" stroke="{PAL['explore']}" stroke-width="2" stroke-opacity="0.6"/>
      </pattern>
      <pattern id="checkers-{def_id_suffix}" width="6" height="6" patternUnits="userSpaceOnUse">
        <rect x="0" y="0" width="3" height="3" fill="#fff"/><rect x="3" y="3" width="3" height="3" fill="#fff"/>
        <rect x="3" y="0" width="3" height="3" fill="#000"/><rect x="0" y="3" width="3" height="3" fill="#000"/>
      </pattern>
    </defs>
    """

# ------------------------------ Pit Lanes (grouped) ---------------------------
def _pit_lanes_svg(kpi_s, kpi_e, fr_s, fr_e, ex_s, ex_e, fr_gate, xai_gate,
                   kpi_finish=90.0, decision="HOLD") -> str:
    """Grouped horizontal bars for KPI, Explainability, FailRate (Strict vs Explore)."""
    width, height = 720, 236
    margin = dict(t=34, r=18, b=30, l=132)
    plot_w = width - margin['l'] - margin['r']
    row_h, bar_h, gap = 48, 14, 6

    cats = [
        ("KPI", kpi_s, kpi_e, None),                               # threshold drawn as finish flags
        ("Explainability", ex_s * 100.0, ex_e * 100.0, xai_gate*100.0),
        ("Failure rate", fr_s * 100.0, fr_e * 100.0, fr_gate*100.0),
    ]

    def to_x(pct): return margin['l'] + (max(0.0, min(100.0, pct)) / 100.0) * plot_w

    parts = []
    parts.append(f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' role='img' aria-label='PitCrew — Strict vs Explore'>")
    parts.append(f"<rect width='{width}' height='{height}' fill='{PAL['asphalt']}'/>")
    parts.append(_defs_common("pit"))
    # Title + PASS/HOLD token
    title_y = margin['t'] - 16
    parts.append(_svg_text(margin['l'], title_y, 'PitCrew — Strict vs Explore', 'start', 12))
    badge_fill = PAL['pass'] if decision == "PASS" else PAL['hold']
    glyph = "✓" if decision == "PASS" else "!"
    parts.append(f"<g transform='translate({width-28},{title_y-8})'>"
                 f"<circle cx='10' cy='10' r='9' fill='{badge_fill}'/>"
                 f"{_svg_text(10, 10.5, glyph, 'middle', 12, '#fff')}"
                 f"</g>")

    # Lanes grid + ticks (0, 50, 100)
    for lab in (0, 50, 100):
        x = to_x(lab)
        parts.append(f"<line x1='{x:.1f}' y1='{margin['t']-2:.1f}' x2='{x:.1f}' y2='{height-margin['b']:.1f}' stroke='{PAL['grid']}' stroke-width='1' opacity='0.75' />")
        parts.append(_svg_text(x, height - margin['b'] + 12, str(lab), 'middle', 10, PAL['muted']))

    # Threshold redlines
    # - Explainability min: dashed
    x_xai = to_x(xai_gate*100.0)
    parts.append(f"<line x1='{x_xai:.1f}' y1='{margin['t']:.1f}' x2='{x_xai:.1f}' y2='{height-margin['b']:.1f}' "
                 f"stroke='{PAL['redline']}' stroke-width='1.5' stroke-dasharray='4,3' opacity='0.85'/>")
    # - Failure-rate max: solid
    x_fr = to_x(fr_gate*100.0)
    parts.append(f"<line x1='{x_fr:.1f}' y1='{margin['t']:.1f}' x2='{x_fr:.1f}' y2='{height-margin['b']:.1f}' "
                 f"stroke='{PAL['redline']}' stroke-width='1.5' opacity='0.85'/>")

    # Bars
    def draw_pair(y0, label, v_s, v_e, gate_pct, is_explain=False, is_fail=False, is_kpi=False):
        # Label
        parts.append(_svg_text(margin['l'] - 10, y0 + bar_h/2, label, 'end', 12))
        # Strict bar (solid)
        w_s = max(0.0, min(100.0, v_s))/100.0 * plot_w
        path_s = _bevel_bar_path(margin['l'], y0, w_s, bar_h, bevel=3)
        parts.append(f"<path d='{path_s}' fill='{PAL['strict']}' opacity='0.95'/>")
        parts.append(_svg_text(margin['l'] + w_s + 6, y0 + bar_h/2, f"S {v_s:.1f}%", 'start', 10))
        # Explore bar (amber + hatch overlay)
        w_e = max(0.0, min(100.0, v_e))/100.0 * plot_w
        y_e = y0 + bar_h + gap
        path_e = _bevel_bar_path(margin['l'], y_e, w_e, bar_h, bevel=3)
        parts.append(f"<path d='{path_e}' fill='{PAL['explore']}' opacity='0.95'/>")
        # hatch overlay
        parts.append(f"<rect x='{margin['l']:.1f}' y='{y_e:.1f}' width='{w_e:.1f}' height='{bar_h:.1f}' fill='url(#expHatch-pit)' opacity='0.9'/>")
        parts.append(_svg_text(margin['l'] + w_e + 6, y_e + bar_h/2, f"E {v_e:.1f}%", 'start', 10))

        # Checkered caps when meeting targets
        if is_kpi:
            for w in (w_s,):
                if v_s >= kpi_finish:
                    parts.append(f"<rect x='{margin['l'] + w - 10:.1f}' y='{y0:.1f}' width='10' height='{bar_h:.1f}' fill='url(#checkers-pit)'/>")
            for w in (w_e,):
                if v_e >= kpi_finish:
                    parts.append(f"<rect x='{margin['l'] + w - 10:.1f}' y='{y_e:.1f}' width='10' height='{bar_h:.1f}' fill='url(#checkers-pit)'/>")
        if is_explain:
            if v_s >= xai_gate*100.0:
                parts.append(f"<rect x='{margin['l'] + w_s - 10:.1f}' y='{y0:.1f}' width='10' height='{bar_h:.1f}' fill='url(#checkers-pit)'/>")
            if v_e >= xai_gate*100.0:
                parts.append(f"<rect x='{margin['l'] + w_e - 10:.1f}' y='{y_e:.1f}' width='10' height='{bar_h:.1f}' fill='url(#checkers-pit)'/>")

    for idx, (label, vs, ve, gate) in enumerate(cats):
        y0 = margin['t'] + idx * row_h + 6
        draw_pair(y0, label, vs, ve,
                  gate, is_explain=(label=="Explainability"),
                  is_fail=(label=="Failure rate"),
                  is_kpi=(label=="KPI"))

    # Legend
    lx = margin['l']; ly = height - margin['b'] + 6
    parts.append(f"<rect x='{lx:.1f}' y='{ly:.1f}' width='14' height='10' fill='{PAL['strict']}'/>")
    parts.append(_svg_text(lx + 20, ly + 5, 'Strict', 'start', 10))
    parts.append(f"<rect x='{lx + 70:.1f}' y='{ly:.1f}' width='14' height='10' fill='{PAL['explore']}'/>")
    parts.append(f"<rect x='{lx + 70:.1f}' y='{ly:.1f}' width='14' height='10' fill='url(#expHatch-pit)' opacity='0.9'/>")
    parts.append(_svg_text(lx + 90, ly + 5, 'Explore', 'start', 10))
    parts.append(_svg_text(width - margin['r'], ly + 5, '0–100%', 'end', 10, PAL['muted']))

    parts.append("</svg>")
    return "".join(parts)

# ------------------------------ Redline Stacks --------------------------------
def _redline_stacks_svg(fr_s, fr_e, fr_gate, decision="HOLD") -> str:
    """Stacked bars: Success vs Failure per profile, with failure gate tick."""
    width, height = 420, 160
    margin = dict(t=38, r=18, b=24, l=90)
    bar_w, bar_h, gap = 280, 16, 22

    def bar(x, y, w, h, fill, opacity=0.95):
        return f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{fill}' opacity='{opacity}'/>"

    parts = []
    parts.append(f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' role='img' aria-label='PitCrew — Redline Stacks'>")
    parts.append(f"<rect width='{width}' height='{height}' fill='{PAL['asphalt']}'/>")
    parts.append(_defs_common("stack"))
    parts.append(_svg_text(margin['l'], margin['t'] - 18, 'Redline Stacks — outcome mix', 'start', 12))

    def draw_row(y, label, fr, color, hatch=False):
        succ = 1.0 - max(0.0, min(1.0, fr))
        fail = 1.0 - succ
        x0 = margin['l']
        # success segment
        parts.append(bar(x0, y, bar_w * succ, bar_h, color))
        if hatch:
            parts.append(f"<rect x='{x0:.1f}' y='{y:.1f}' width='{bar_w*succ:.1f}' height='{bar_h:.1f}' fill='url(#expHatch-stack)' opacity='0.9'/>")
        # failure segment
        parts.append(bar(x0 + bar_w*succ, y, bar_w * fail, bar_h, PAL["hold"]))
        parts.append(_svg_text(margin['l'] - 10, y + bar_h/2, label, 'end', 12))
        # failure gate tick
        gate_x = x0 + bar_w * fr_gate
        parts.append(f"<line x1='{gate_x:.1f}' y1='{y-4:.1f}' x2='{gate_x:.1f}' y2='{y+bar_h+4:.1f}' stroke='{PAL['redline']}' stroke-width='2'/>")
        # values
        parts.append(_svg_text(x0 + bar_w + 8, y + bar_h/2, f"{(succ*100):.1f}% ok / {(fail*100):.1f}% fail", 'start', 10, PAL["muted"]))

    draw_row(margin['t'], "strict", fr_s, PAL["strict"], hatch=False)
    draw_row(margin['t'] + bar_h + gap, "explore", fr_e, PAL["explore"], hatch=True)

    parts.append("</svg>")
    return "".join(parts)

# ------------------------------ Telemetry Bars --------------------------------
def _telemetry_bars_svg(ex_s, ex_e, xai_gate, decision="HOLD") -> str:
    """Explainability per profile with dashed min-line and checkered caps."""
    width, height = 420, 160
    margin = dict(t=38, r=18, b=24, l=90)
    plot_w, bar_h, gap = 280, 16, 22

    def to_x(pct): return margin['l'] + (max(0.0, min(100.0, pct))/100.0) * plot_w

    parts = []
    parts.append(f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' role='img' aria-label='PitCrew — Telemetry Bars'>")
    parts.append(f"<rect width='{width}' height='{height}' fill='{PAL['asphalt']}'/>")
    parts.append(_defs_common("tele"))
    parts.append(_svg_text(margin['l'], margin['t'] - 18, 'Telemetry — explainability', 'start', 12))

    # Gate line (dashed)
    x_gate = to_x(xai_gate*100.0)
    parts.append(f"<line x1='{x_gate:.1f}' y1='{margin['t']-10:.1f}' x2='{x_gate:.1f}' y2='{height-margin['b']+10:.1f}' stroke='{PAL['redline']}' stroke-dasharray='4,3' stroke-width='2'/>")

    def row(y, label, pct, color, hatch=False):
        pct = max(0.0, min(1.0, pct))
        x0 = margin['l']; w = plot_w * (pct*100.0/100.0)
        # base bar
        parts.append(f"<path d='{_bevel_bar_path(x0, y, w, bar_h, bevel=3)}' fill='{color}' opacity='0.95'/>")
        if hatch:
            parts.append(f"<rect x='{x0:.1f}' y='{y:.1f}' width='{w:.1f}' height='{bar_h:.1f}' fill='url(#expHatch-tele)' opacity='0.9'/>")
        # checkered cap if ≥ gate
        if pct >= xai_gate:
            parts.append(f"<rect x='{x0 + w - 10:.1f}' y='{y:.1f}' width='10' height='{bar_h:.1f}' fill='url(#checkers-tele)'/>")
        parts.append(_svg_text(margin['l'] - 10, y + bar_h/2, label, 'end', 12))
        parts.append(_svg_text(x0 + w + 6, y + bar_h/2, f"{pct*100:.1f}%", 'start', 10))

    row(margin['t'], "strict", ex_s, PAL["strict"], hatch=False)
    row(margin['t'] + bar_h + gap, "explore", ex_e, PAL["explore"], hatch=True)

    parts.append("</svg>")
    return "".join(parts)

# ------------------------------------ Main ------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="aml_out/report.json")
    ap.add_argument("--out_dir", default="mech_out")
    ap.add_argument("--badges_dir", default="badges")
    ap.add_argument("--strict_weight", type=float, default=0.7)
    ap.add_argument("--explore_weight", type=float, default=0.3)
    # KPI shaping/weights
    ap.add_argument("--weight_rel", type=float, default=0.75)
    ap.add_argument("--weight_xai", type=float, default=0.25)
    ap.add_argument("--fr_gate", type=float, default=0.10)
    ap.add_argument("--xai_gate", type=float, default=0.95)  # default matches eval gate
    ap.add_argument("--k_shape", type=float, default=12.0)
    args = ap.parse_args()

    out_dir = pathlib.Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    badges_dir = pathlib.Path(args.badges_dir); badges_dir.mkdir(parents=True, exist_ok=True)

    rpt = json.loads(pathlib.Path(args.report).read_text(encoding="utf-8"))
    strict = rpt.get("strict", {})
    explore = rpt.get("explore", {})
    decision = rpt.get("decision", "HOLD")
    et = rpt.get("evaluated_at_et", datetime.utcnow().isoformat()+"Z")

    kpi_args = dict(weight_rel=args.weight_rel, weight_xai=args.weight_xai,
                    fr_gate=args.fr_gate, xai_gate=args.xai_gate, k_shape=args.k_shape)
    kpi_s = _kpi_from_metrics(strict, **kpi_args)
    kpi_e = _kpi_from_metrics(explore, **kpi_args)
    # blend
    sw = max(0.0, min(1.0, args.strict_weight)); ew = max(0.0, min(1.0, args.explore_weight))
    if sw + ew == 0: sw, ew = 1.0, 0.0
    overall = round(sw * kpi_s + ew * kpi_e, 1)

    # Compact JSON for downstream steps
    mech = {
        "evaluated_at_et": et,
        "decision": decision,
        "strict": {**strict, "kpi": kpi_s},
        "explore": {**explore, "kpi": kpi_e},
        "overall_kpi": overall,
        "weights": {"strict": sw, "explore": ew}
    }
    (out_dir / "mechanic_kpi.json").write_text(json.dumps(mech, indent=2), encoding="utf-8")

    # Badges (kept stable)
    status_color = PAL["pass"] if decision == "PASS" else PAL["hold"]
    _write_badge(badges_dir / "status.svg", "Status", decision, status_color)
    _write_badge(badges_dir / "kpi.svg", "KPI", f"{overall:.0f}", _color_scale(overall))

    # Derived display metrics
    fr_s = float(strict.get("failure_rate", 0.0)); fr_e = float(explore.get("failure_rate", 0.0))
    ex_s = float(strict.get("explainability_rate", 0.0)); ex_e = float(explore.get("explainability_rate", 0.0))
    ex_s_pct = f"{round(ex_s * 100)}%" if isinstance(ex_s, (int, float)) else "?"
    ex_e_pct = f"{round(ex_e * 100)}%" if isinstance(ex_e, (int, float)) else "?"
    fr_s_pct = f"{round(fr_s * 100, 1)}%" if isinstance(fr_s, (int, float)) else "?"
    fr_e_pct = f"{round(fr_e * 100, 1)}%" if isinstance(fr_e, (int, float)) else "?"
    _write_badge(badges_dir / "xai.svg", "XAI", f"S:{ex_s_pct}|E:{ex_e_pct}",
                 _color_scale(100 * (ex_s + ex_e)/2.0))
    _write_badge(badges_dir / "failrate.svg", "FailRate", f"S:{fr_s_pct}|E:{fr_e_pct}",
                 _color_scale(100 * (1 - (fr_s + fr_e)/2.0)))

    # Visuals — Pit Lanes (grouped), Redline Stacks, Telemetry
    pit = _pit_lanes_svg(kpi_s, kpi_e, fr_s, fr_e, ex_s, ex_e, args.fr_gate, args.xai_gate, decision=decision)
    (out_dir / "metrics_pitlanes.svg").write_text(pit, encoding="utf-8")
    (badges_dir / "metrics_pitlanes.svg").write_text(pit, encoding="utf-8")
    # Back-compat alias
    (out_dir / "metrics.svg").write_text(pit, encoding="utf-8")
    (badges_dir / "metrics.svg").write_text(pit, encoding="utf-8")

    stacks = _redline_stacks_svg(fr_s, fr_e, args.fr_gate, decision=decision)
    (out_dir / "metrics_stacks.svg").write_text(stacks, encoding="utf-8")
    (badges_dir / "metrics_stacks.svg").write_text(stacks, encoding="utf-8")

    tele = _telemetry_bars_svg(ex_s, ex_e, args.xai_gate, decision=decision)
    (out_dir / "metrics_telemetry.svg").write_text(tele, encoding="utf-8")
    (badges_dir / "metrics_telemetry.svg").write_text(tele, encoding="utf-8")

    # Human summary (for PR job summary)
    md = []
    md.append(f"### PitCrew — Mechanic Summary\n")
    md.append(f"- **Decision:** `{decision}`  \n")
    md.append(f"- **Evaluated at (ET):** {et}\n")
    md.append("")
    md.append("| Profile | KPI | Failure Rate | Explainability | Events | Actions |")
    md.append("|---|---:|---:|---:|---:|---:|")
    def row(name, m, kpi):
        md.append(f"| {name} | {kpi:.1f} | {m.get('failure_rate',0.0):.3f} | {m.get('explainability_rate',0.0):.2f} | "
                  f"{m.get('events','?')} | {m.get('actions','?')} |")
    row("strict", strict, kpi_s)
    row("explore", explore, kpi_e)
    md.append(f"\n**Overall KPI (weights strict={sw:.2f}, explore={ew:.2f}):** `{overall:.1f}`\n")

    # Inline the Pit Lanes chart; link the others
    md.append("\n<sup>Visual summary — Pit Lanes</sup>\n")
    md.append(pit)
    md.append("\n<sup>Outcome mix (Redline Stacks)</sup>\n")
    md.append(stacks)
    md.append("\n<sup>Explainability (Telemetry)</sup>\n")
    md.append(tele)

    (out_dir / "summary.md").write_text("\n".join(md), encoding="utf-8")

    print(json.dumps({"status":"ok","decision":decision,"overall_kpi":overall}))

if __name__ == "__main__":
    sys.exit(main())
