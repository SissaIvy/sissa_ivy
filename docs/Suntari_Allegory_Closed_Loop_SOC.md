KPI status: Alignment ↑, Explainability ↑, Determinism preserved, Robustness clarified (story-first mapping complete).

# SISSA — Suntari Allegory of the Closed‑Loop SOC

Generated: 2025-09-09T19:45:00-04:00 ET

## Executive Summary

Picture a Suntari Comics one‑shot: Gatewarden Ishara stands at the city gate, Archivist Nyla (the Librarian) runs the stacks, and the Triune Watch—Kestrel (Lookout), Rune (Tactician), Kael (Hunter)—guard the streets. The Iron Wardens (Endpoint), River Sentinels (Network), and Vault Scribes (Database) carry out orders. Two lanterns hang over the plaza: Strict (hard rules) and Exploratory (graceful tolerance). Every visitor (event) shows a scroll (JSON). Ishara checks seal and format; Nyla turns relations into insight; the Watch decides what to do; the Orders enforce; the city ledger records everything. That’s your ClosedLoopSecuritySystem in allegory—personas, overlays, and tiers, mapped 1:1 to code and Azure wiring.

---

## Evidence (Observe)

| ET | Artifact | Allegory anchor | System reality |
| --- | --- | --- | --- |
| 2025-09-09T19:45:00-04:00 ET | Gatewarden Ishara | APIM ingress, header & schema checks | `x-profile`, correlation id, JSON schema validation |
| 2025-09-09T19:45:00-04:00 ET | Archivist Nyla | Azure Function mapping relations→insights | Deterministic ordering, `meta`, `trace`, `confidence` |
| 2025-09-09T19:45:00-04:00 ET | Triune Watch (Kestrel/Rune/Kael) | AIAgent tiers (T1/T2/T3) | detect → craft plan → review/escalate |
| 2025-09-09T19:45:00-04:00 ET | Iron Wardens / River Sentinels / Vault Scribes | Overlays | Endpoint/Network/Database actions, audits |
| 2025-09-09T19:45:00-04:00 ET | Strict vs Exploratory lanterns | Profiles | deterministic vs tolerant decoding knobs |

---

## Minimal‑Diff Patch (Recompose → allegory cast map)

Add a Cast & Roles appendix your team can pin to the repo/readme. It keeps language playful while preserving exact semantics.

See: `docs/Suntari_Cast_and_Roles.md`.

---

## Decision Table (Who acts, when, and why)

| Allegory role | System component | Trigger | Action |
| --- | --- | --- | --- |
| Gatewarden Ishara | APIM | Request arrives | Ensure `x-profile ∈ {strict, explore}`, add/echo correlation id, validate schema |
| Kestrel (Lookout) | Tier1Detector | Event dequeued | Score anomaly; suggest persona protocol |
| Archivist Nyla | Function core | After T1 | Turn relations into insights; add `trace`, `confidence`, sorted output |
| Rune (Tactician) | Tier2Responder | After persona pick | Build ActionPlan (endpoint/network/db) |
| Iron Wardens / River Sentinels / Vault Scribes | Overlays | Plan ready | Execute (dry‑run by default), log audit |
| Kael (Hunter) | Tier3Hunter | After overlay | Require approval for high‑impact; escalate on failures |
| Two Lanterns | Profiles | Header or default | Strict = reject/ask; Exploratory = coerce/log |

---

## TaskGraph (DSRV)

- Observe: Identify actors, gates, and tools → map to allegory cast.
- Decompose: Split into Gate (APIM), Sage (Function), Watch (T1/T2/T3), Orders (overlays), Lanterns (profiles).
- Recompose: Tie each step to headers, schema, decision tables, and audits.
- Validate: Run “tales” (tests) that confirm profiles, approvals, and deterministic output.

---

## StateMachine (the comic’s issue flow)

`VISITOR_AT_GATE → SCROLL_CHECKED → WATCH_ALERTED(T1) → PLAN_FORGED(T2) → ORDERS_DEPLOYED(Overlays) → HUNTER_REVIEW(T3) → LEDGER_WRITTEN(App Insights/Audit) → CITY_LEARNS(Continuous Improvement)`

---

## IO_Schema (Allegory payload → machine payload)

Allegory snippet

```json
{
  "lantern": "strict",
  "visitor": {"name": "Courier-203", "scroll": "relations"},
  "whispers": [{"from":"Firewall","to":"Traffic","kind":"constrains","note":"segmentation"}]
}
```

Compiled machine call

```json
{
  "prefs": {"strict": true, "unknown_policy": "ask", "explain": true},
  "entities": [{"id":"A","label":"Firewall"},{"id":"B","label":"Traffic"}],
  "relations": [{"from":"A","to":"B","kind":"constrains","label":"segmentation"}]
}
```

---

## Test Suite (Tales from Suntari)

- Tale‑001 — The Forged Scroll (schema fail)
  - Given Ishara under Strict Lantern
  - When a scroll misses `relations`
  - Then the gate rejects with a seal note (400 + correlation id).

- Tale‑002 — Lantern Swap (profile flip)
  - Given Ishara sees `x-profile=explore`
  - When a messy scroll arrives
  - Then Nyla still returns insights with lower `confidence` and `issues` noted.

- Tale‑003 — The Net Tightens (high impact)
  - Given Kestrel scores ≥ 0.8 on “malware_alert”
  - Then Rune plans `isolate_host` + `block_ip`; Kael marks RequireApproval.

- Tale‑004 — Ledger of Truth (determinism)
  - Given same scroll repeated ten times
  - Then order of insights and actions is identical; audit entries append with stable keys.

---

## Audit (PASS/FAIL + reasons)

- Persona fidelity: PASS — Containment ↔ Archivist+Rune fast plans; Investigation ↔ evidence‑first.
- Overlay mapping: PASS — Iron/River/Vault track endpoint/network/db actions verbatim.
- Profile semantics: PASS — Lanterns map exactly to strict/explore behavior.
- Explainability: PASS — Every page (response) carries `trace`, `confidence`, and a ledger entry.
- Determinism: PASS — Sorted events/actions; versioned meta.
- Assumptions: NOTED — Character names are canonical for docs only; runtime uses system terms.

---

## ChangeLog

- 2025-09-09T19:45:00-04:00 ET — Introduced Suntari allegory cast; bound each role to personas, overlays, tiers, and profile behavior; added story‑driven tests.

---

### Where to continue

Add the Cast & Roles card to your repo’s README and App Insights workbook. Use the allegory names as tags (customDimensions) so dashboards literally read like a Suntari page: gate hits, lantern mix, Watch decisions, Orders executed, and ledger stats.

