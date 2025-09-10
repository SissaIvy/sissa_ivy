import React, { useRef, useState, useMemo } from "react";

// PitCrew GUI – Rapid Assimilation Dashboard (Daytona Edition)
// See README in this folder for usage. Tailwind classes are present but optional.

const PAL = {
  asphalt: "#0D1117",
  grid: "#1F2937",
  label: "#E5E7EB",
  muted: "#9CA3AF",
  strict: "#2563EB",
  explore: "#F59E0B",
  pass: "#2EA44F",
  hold: "#D73A49",
  redline: "#EF4444",
  lane: "#9CA3AF88",
  rumble: "#AA2B2B",
};

const DEFAULT_GATES = { fr_strict: 0.10, fr_explore: 0.15, xai_min: 0.95 };
const DEFAULT_PROFILE = { events: 0, actions: 0, failure_rate: 0, explainability_rate: 0, kpi: 0 };
const DEFAULT_DATA = {
  evaluated_at_et: new Date().toISOString(),
  decision: "HOLD",
  decision_src: "recomputed",
  strict: { ...DEFAULT_PROFILE },
  explore: { ...DEFAULT_PROFILE },
  overall_kpi: 0,
  weights: { strict: 0.7, explore: 0.3 },
  gates: { ...DEFAULT_GATES },
};

function num(n, d = 0) {
  const x = typeof n === "string" ? Number(n) : n;
  return Number.isFinite(x) ? x : d;
}

function normalize(raw) {
  const r = raw || {};
  const gates = { ...DEFAULT_GATES, ...(r.gates || {}) };
  const strict = { ...DEFAULT_PROFILE, ...(r.strict || {}) };
  const explore = { ...DEFAULT_PROFILE, ...(r.explore || {}) };
  strict.failure_rate = num(strict.failure_rate);
  strict.explainability_rate = num(strict.explainability_rate);
  strict.kpi = num(strict.kpi);
  explore.failure_rate = num(explore.failure_rate);
  explore.explainability_rate = num(explore.explainability_rate);
  explore.kpi = num(explore.kpi);
  const weights = { strict: num(r?.weights?.strict, 0.7), explore: num(r?.weights?.explore, 0.3) };
  return {
    ...DEFAULT_DATA,
    ...r,
    gates,
    strict,
    explore,
    overall_kpi: num(r.overall_kpi),
    weights,
  };
}

const previewData = normalize({
  evaluated_at_et: "2025-09-10T12:00:00Z",
  decision: "PASS",
  decision_src: "report",
  strict: { events: 200, actions: 222, failure_rate: 0.0186, explainability_rate: 0.9687, kpi: 60.0 },
  explore:{ events: 200, actions: 211, failure_rate: 0.0339, explainability_rate: 0.9729, kpi: 56.1 },
  overall_kpi: 58.8,
  weights: { strict: 0.7, explore: 0.3 },
  gates: { fr_strict: 0.05, fr_explore: 0.05, xai_min: 0.95 },
});

const pct = (n, digits = 1) => `${(num(n)*100).toFixed(digits)}%`;
const clamp01 = (x) => Math.max(0, Math.min(1, num(x)));
const bevelPath = (x,y,w,h,bevel=3) => (w<=0 ? `M${x},${y+h}Z` : `M${x},${y+h} L${x},${y+bevel} L${x+bevel},${y} L${x+w},${y} L${x+w},${y+h} Z`);

const SvgDefs = ({ id, exploreColor = PAL.explore }) => (
  <defs>
    <pattern id={`expHatch-${id}`} patternUnits="userSpaceOnUse" width={6} height={6} patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="6" stroke={exploreColor} strokeWidth={2} strokeOpacity={0.6}/>
    </pattern>
    <pattern id={`checkers-${id}`} width={6} height={6} patternUnits="userSpaceOnUse">
      <rect x={0} y={0} width={3} height={3} fill="#fff"/>
      <rect x={3} y={3} width={3} height={3} fill="#fff"/>
      <rect x={3} y={0} width={3} height={3} fill="#000"/>
      <rect x={0} y={3} width={3} height={3} fill="#000"/>
    </pattern>
  </defs>
);

const StatusBadge = ({ decision }) => {
  const fill = decision === "PASS" ? PAL.pass : PAL.hold;
  const glyph = decision === "PASS" ? "✓" : "!";
  return (
    <div className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-white" style={{background:fill}}>
      <span aria-label={decision} className="font-semibold tracking-wide">{decision}</span>
      <span aria-hidden>{glyph}</span>
    </div>
  );
};
const KpiBadge = ({ label, value }) => (
  <div className="flex items-center gap-2 rounded-xl bg-neutral-800/60 text-gray-100 px-3 py-1">
    <span className="text-xs uppercase tracking-wide text-gray-300">{label}</span>
    <span className="font-semibold">{value}</span>
  </div>
);

const PitLanes = ({ data, width=820, height=260 }) => {
  const margin = {t:34,r:18,b:34,l:150};
  const plotW = width - margin.l - margin.r;
  const rowH = 56, barH = 16, gap = 8;
  const g = data.gates || DEFAULT_GATES;
  const cats = [
    {label:"KPI", s:data.strict.kpi, e:data.explore.kpi, gate:null, type:"kpi"},
    {label:"Explainability", s:data.strict.explainability_rate*100, e:data.explore.explainability_rate*100, gate:g.xai_min*100, type:"xai"},
    {label:"Failure rate", s:data.strict.failure_rate*100, e:data.explore.failure_rate*100, gate:Math.min(g.fr_strict,g.fr_explore)*100, type:"fr"},
  ];
  const toX = (p) => margin.l + (Math.max(0,Math.min(100,p))/100)*plotW;
  return (
    <svg width={width} height={height} role="img" aria-label="Pit Lanes – strict vs explore" className="rounded-2xl shadow-md">
      <rect width={width} height={height} fill={PAL.asphalt}/>
      <SvgDefs id="pit"/>
      <text x={margin.l} y={margin.t-14} fill={PAL.label} fontSize={14} textAnchor="start" dominantBaseline="middle">Pit Lanes — Strict vs Explore</text>
      {[0,50,100].map((lab)=>{
        const x = toX(lab);
        return (
          <g key={lab}>
            <line x1={x} y1={margin.t-2} x2={x} y2={height-margin.b} stroke={PAL.grid} strokeWidth={1} opacity={0.7}/>
            <text x={x} y={height-margin.b+14} fill={PAL.muted} fontSize={10} textAnchor="middle" dominantBaseline="middle">{lab}</text>
          </g>
        );
      })}
      <line x1={toX(g.xai_min*100)} y1={margin.t} x2={toX(g.xai_min*100)} y2={height-margin.b} stroke={PAL.redline} strokeWidth={1.5} strokeDasharray="4,3" opacity={0.9}/>
      <line x1={toX(Math.min(g.fr_strict,g.fr_explore)*100)} y1={margin.t} x2={toX(Math.min(g.fr_strict,g.fr_explore)*100)} y2={height-margin.b} stroke={PAL.redline} strokeWidth={1.5} opacity={0.9}/>
      <g transform={`translate(${width-30},${margin.t-10})`}><circle cx={10} cy={10} r={9} fill={data.decision==="PASS"?PAL.pass:PAL.hold}/><text x={10} y={11} fill="#fff" fontSize={12} textAnchor="middle">{data.decision==="PASS"?"✓":"!"}</text></g>
      {cats.map((c)=>{
        const y0 = margin.t + cats.indexOf(c)*rowH + 6;
        const wS = Math.max(0,Math.min(100,c.s))/100*plotW;
        const wE = Math.max(0,Math.min(100,c.e))/100*plotW;
        const pathS = bevelPath(margin.l, y0, wS, barH, 3);
        const pathE = bevelPath(margin.l, y0+barH+gap, wE, barH, 3);
        const capS = (c.type==="xai" && c.s >= g.xai_min*100) || (c.type==="kpi" && c.s >= 90);
        const capE = (c.type==="xai" && c.e >= g.xai_min*100) || (c.type==="kpi" && c.e >= 90);
        return (
          <g key={c.label}>
            <text x={margin.l-12} y={y0+barH/2} fill={PAL.label} fontSize={13} textAnchor="end" dominantBaseline="middle">{c.label}</text>
            <path d={pathS} fill={PAL.strict} opacity={0.95}/>
            {capS && <rect x={margin.l+wS-10} y={y0} width={10} height={barH} fill="url(#checkers-pit)"/>}
            <text x={margin.l+wS+6} y={y0+barH/2} fill={PAL.label} fontSize={10} dominantBaseline="middle">S {(c.s).toFixed(1)}%</text>
            <path d={pathE} fill={PAL.explore} opacity={0.95}/>
            <rect x={margin.l} y={y0+barH+gap} width={wE} height={barH} fill="url(#expHatch-pit)" opacity={0.9}/>
            {capE && <rect x={margin.l+wE-10} y={y0+barH+gap} width={10} height={barH} fill="url(#checkers-pit)"/>}
            <text x={margin.l+wE+6} y={y0+barH+gap+barH/2} fill={PAL.label} fontSize={10} dominantBaseline="middle">E {(c.e).toFixed(1)}%</text>
          </g>
        );
      })}
      <g>
        <rect x={margin.l} y={height-margin.b+8} width={14} height={10} fill={PAL.strict}/>
        <text x={margin.l+22} y={height-margin.b+13} fill={PAL.label} fontSize={10} dominantBaseline="middle">Strict</text>
        <rect x={margin.l+76} y={height-margin.b+8} width={14} height={10} fill={PAL.explore}/>
        <rect x={margin.l+76} y={height-margin.b+8} width={14} height={10} fill="url(#expHatch-pit)" opacity={0.9}/>
        <text x={margin.l+96} y={height-margin.b+13} fill={PAL.label} fontSize={10} dominantBaseline="middle">Explore</text>
        <text x={width-margin.r} y={height-margin.b+13} fill={PAL.muted} fontSize={10} textAnchor="end" dominantBaseline="middle">0–100%</text>
      </g>
    </svg>
  );
};

const RedlineStacks = ({ data, width=520, height=180 }) => {
  const margin = {t:34,r:18,b:24,l:120};
  const barW = width - margin.l - margin.r;
  const barH = 16, gap = 26;
  const g = data.gates || DEFAULT_GATES;
  const rows = [
    {label:"strict", fr:data.strict.failure_rate},
    {label:"explore", fr:data.explore.failure_rate, hatch:true},
  ];
  return (
    <svg width={width} height={height} role="img" aria-label="Redline Stacks – outcome mix" className="rounded-2xl shadow-md">
      <rect width={width} height={height} fill={PAL.asphalt}/>
      <SvgDefs id="stack"/>
      <text x={margin.l} y={margin.t-14} fill={PAL.label} fontSize={14} textAnchor="start" dominantBaseline="middle">Outcome mix — Redline Stacks</text>
      {rows.map((r,i)=>{
        const y = margin.t + i*(barH+gap);
        const succ = 1 - clamp01(r.fr), fail = clamp01(r.fr);
        const x0 = margin.l; const sW = barW*succ, fW = barW*fail;
        return (
          <g key={r.label}>
            <rect x={x0} y={y} width={sW} height={barH} fill={i===0?PAL.strict:PAL.explore} opacity={0.95}/>
            {r.hatch && <rect x={x0} y={y} width={sW} height={barH} fill="url(#expHatch-stack)" opacity={0.9}/>}      
            <rect x={x0+sW} y={y} width={fW} height={barH} fill={PAL.hold} opacity={0.95}/>
            <text x={margin.l-10} y={y+barH/2} fill={PAL.label} fontSize={12} textAnchor="end" dominantBaseline="middle">{r.label}</text>
            <line x1={x0 + barW* Math.min(g.fr_strict,g.fr_explore)} y1={y-4} x2={x0 + barW* Math.min(g.fr_strict,g.fr_explore)} y2={y+barH+4} stroke={PAL.redline} strokeWidth={2}/>
            <text x={x0+barW+8} y={y+barH/2} fill={PAL.muted} fontSize={10} dominantBaseline="middle">{pct(succ)} ok / {pct(fail)} fail</text>
          </g>
        );
      })}
    </svg>
  );
};

const TelemetryBars = ({ data, width=520, height=180 }) => {
  const margin = {t:34,r:18,b:24,l:120};
  const plotW = width - margin.l - margin.r;
  const barH = 16, gap = 26;
  const g = data.gates || DEFAULT_GATES;
  const rows = [
    {label:"strict", xai:data.strict.explainability_rate, color:PAL.strict},
    {label:"explore", xai:data.explore.explainability_rate, color:PAL.explore, hatch:true},
  ];
  const toX = (p) => margin.l + clamp01(p)*plotW;
  return (
    <svg width={width} height={height} role="img" aria-label="Telemetry – explainability" className="rounded-2xl shadow-md">
      <rect width={width} height={height} fill={PAL.asphalt}/>
      <SvgDefs id="tele"/>
      <text x={margin.l} y={margin.t-14} fill={PAL.label} fontSize={14} textAnchor="start" dominantBaseline="middle">Explainability — Telemetry</text>
      <line x1={toX(g.xai_min)} y1={margin.t-8} x2={toX(g.xai_min)} y2={height-margin.b+8} stroke={PAL.redline} strokeDasharray="4,3" strokeWidth={2}/>
      {rows.map((r,i)=>{
        const y = margin.t + i*(barH+gap);
        const w = plotW * clamp01(r.xai);
        return (
          <g key={r.label}>
            <path d={bevelPath(margin.l,y,w,barH,3)} fill={r.color} opacity={0.95}/>
            {r.hatch && <rect x={margin.l} y={y} width={w} height={barH} fill="url(#expHatch-tele)" opacity={0.9}/>} 
            {r.xai >= g.xai_min && <rect x={margin.l+w-10} y={y} width={10} height={barH} fill="url(#checkers-tele)"/>}
            <text x={margin.l-10} y={y+barH/2} fill={PAL.label} fontSize={12} textAnchor="end" dominantBaseline="middle">{r.label}</text>
            <text x={margin.l+w+6} y={y+barH/2} fill={PAL.label} fontSize={10} dominantBaseline="middle">{pct(r.xai)}</text>
          </g>
        );
      })}
    </svg>
  );
};

const DaytonaBackdrop = () => (
  <svg className="fixed inset-0 -z-10" aria-hidden width="100%" height="100%" preserveAspectRatio="none">
    <defs>
      <linearGradient id="asphalt" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stopColor="#0B0F17"/><stop offset="100%" stopColor="#0D1117"/>
      </linearGradient>
      <pattern id="checkers-bg" width="12" height="12" patternUnits="userSpaceOnUse">
        <rect x="0" y="0" width="6" height="6" fill="#fff"/><rect x="6" y="6" width="6" height="6" fill="#fff"/>
        <rect x="6" y="0" width="6" height="6" fill="#000"/><rect x="0" y="6" width="6" height="6" fill="#000"/>
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#asphalt)"/>
    <g opacity="0.25">
      <ellipse cx="50%" cy="52%" rx="44%" ry="35%" fill="none" stroke={PAL.lane} strokeWidth="10"/>
      <ellipse cx="50%" cy="52%" rx="40%" ry="31%" fill="none" stroke={PAL.lane} strokeWidth="2"/>
      <ellipse cx="50%" cy="52%" rx="36%" ry="28%" fill="none" stroke={PAL.lane} strokeWidth="2"/>
    </g>
    <rect x="10%" y="80%" width="80%" height="8" fill={PAL.rumble} opacity="0.25"/>
    <rect x="50%" y="18%" width="18" height="12%" fill="url(#checkers-bg)" transform="translate(-9,0)" opacity="0.35"/>
  </svg>
);

const FileLoader = ({ onLoaded }) => {
  const inputRef = useRef(null);
  return (
    <div className="flex gap-3 items-center">
      <button className="px-3 py-2 rounded-xl bg-neutral-200 hover:bg-neutral-300 text-neutral-900" onClick={()=>inputRef.current?.click()}>Load JSON</button>
      <input ref={inputRef} type="file" accept="application/json" hidden onChange={(e)=>{
        const f = e.target.files?.[0]; if(!f) return;
        const r = new FileReader(); r.onload = ()=>{ try{ onLoaded(normalize(JSON.parse(String(r.result)))); }catch{ alert("Invalid JSON"); } }; r.readAsText(f);
      }}/>
      <span className="text-xs text-neutral-500">Drop in <code>mech_out/mechanic_kpi.json</code></span>
    </div>
  );
};

const MetaRow = ({label,value}) => (
  <div className="flex items-center justify-between py-1"><span className="text-sm text-neutral-400">{label}</span><span className="text-sm font-medium text-neutral-100">{value}</span></div>
);

function runSelfTests() {
  const cases = [
    { name: "fills gates when missing", in: { decision:"PASS", strict:{kpi:55}, explore:{kpi:50} }, expect: d=> d.gates && typeof d.gates.xai_min === 'number' },
    { name: "coerces numbers", in: { strict:{failure_rate:"0.02"}, explore:{failure_rate:"0.04"} }, expect: d=> d.strict.failure_rate===0.02 && d.explore.failure_rate===0.04 },
    { name: "weights default", in: {}, expect: d=> d.weights.strict===0.7 && d.weights.explore===0.3 },
  ];
  return cases.map(tc => ({ name: tc.name, pass: !!tc.expect(normalize(tc.in)) }));
}

export default function App() {
  const [data, setData] = useState(previewData);
  const decisionColor = data.decision === "PASS" ? PAL.pass : PAL.hold;
  const tests = useMemo(runSelfTests, []);

  return (
    <div className="min-h-screen w-full text-white p-6 md:p-10" style={{background:"transparent"}}>
      <DaytonaBackdrop/>
      <div className="mx-auto max-w-7xl grid grid-cols-1 gap-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-semibold tracking-tight">PitCrew — Rapid Assimilation Dashboard</h1>
            <p className="text-neutral-300 text-sm">Strict vs Explore KPIs • Deterministic • Explainable</p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge decision={data.decision}/>
            <KpiBadge label="Overall KPI" value={data.overall_kpi.toFixed(1)}/>
            <KpiBadge label="Weights" value={`S:${(data.weights.strict*100).toFixed(0)}% / E:${(data.weights.explore*100).toFixed(0)}%`}/>
            <FileLoader onLoaded={setData}/>
          </div>
        </div>
        <div className="grid lg:grid-cols-2 gap-6">
          <PitLanes data={data}/>
          <div className="grid grid-rows-2 gap-6">
            <RedlineStacks data={data}/>
            <TelemetryBars data={data}/>
          </div>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="rounded-2xl bg-neutral-900/70 p-5 shadow-md">
            <h2 className="text-lg font-semibold mb-2">Meta</h2>
            <MetaRow label="Evaluated" value={new Date(data.evaluated_at_et ?? Date.now()).toLocaleString()}/>
            <MetaRow label="Decision source" value={data.decision_src ?? "report"}/>
            <MetaRow label="Events (S/E)" value={`${data.strict.events} / ${data.explore.events}`}/>
            <MetaRow label="Actions (S/E)" value={`${data.strict.actions} / ${data.explore.actions}`}/>
          </div>
          <div className="rounded-2xl bg-neutral-900/70 p-5 shadow-md">
            <h2 className="text-lg font-semibold mb-2">Gates</h2>
            <MetaRow label="Failure max (S/E)" value={`${pct((data.gates||DEFAULT_GATES).fr_strict)} / ${pct((data.gates||DEFAULT_GATES).fr_explore)}`}/>
            <MetaRow label="Explainability min" value={pct((data.gates||DEFAULT_GATES).xai_min)}/>
            <MetaRow label="Outcome" value={<span className="px-2 py-0.5 rounded-md" style={{background:decisionColor}}>{data.decision}</span>}/>
          </div>
          <div className="rounded-2xl bg-neutral-900/70 p-5 shadow-md">
            <h2 className="text-lg font-semibold mb-2">Profile KPIs</h2>
            <MetaRow label="Strict KPI" value={data.strict.kpi.toFixed(1)}/>
            <MetaRow label="Explore KPI" value={data.explore.kpi.toFixed(1)}/>
            <MetaRow label="Explainability (S/E)" value={`${pct(data.strict.explainability_rate)} / ${pct(data.explore.explainability_rate)}`}/>
            <MetaRow label="Failure rate (S/E)" value={`${pct(data.strict.failure_rate)} / ${pct(data.explore.failure_rate)}`}/>
          </div>
        </div>
        <div className="rounded-2xl bg-neutral-900/60 p-4 text-sm text-neutral-300">
          <div className="font-semibold mb-1">Self-checks</div>
          <ul className="list-disc pl-5">
            {tests.map(t => <li key={t.name} className={t.pass?"text-green-400":"text-red-400"}>{t.pass?"✔":"✖"} {t.name}</li>)}
          </ul>
        </div>
        <div className="text-xs text-neutral-400">
          Visual grammar: lanes + redlines + checkered caps; strict = blue, explore = amber; dashed = min gate, solid = max gate.
        </div>
      </div>
    </div>
  );
}

