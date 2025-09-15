# sissa_ivy

Native endpoint probes for Windows and Linux that collect basic health and security posture
without relying on a heavyweight agent. The probes emit a compact JSON record and, for Windows,
optionally append a CSV line that matches the `cogsec_workflow.py` health schema.

## Collectors

### Windows: `Get-CogSecEndpointState.ps1`

* Queries WMI/CIM, registry, performance counters and Defender cmdlets.
* Outputs one JSON record per run and can append a health CSV line.
* Example scheduled task (every 5 minutes):

```powershell
$script = "C:\cogsec\Get-CogSecEndpointState.ps1"
$csv    = "C:\cogsec\health_metrics.csv"
$log    = "C:\cogsec\state.json"
schtasks /Create /SC MINUTE /MO 5 /TN "CogSec Probe" `
  /TR "powershell -NoProfile -ExecutionPolicy Bypass -File `"$script`" -CsvPath `"$csv`" -JsonPath `"$log`"" `
  /RU "SYSTEM" /RL HIGHEST /F
```

### Linux: `cogsec_probe_linux.py`

* Reads `/proc`, package/firewall status, listening ports and AV services.
* Prints a JSON record to stdout; make it executable and schedule via systemd:

```ini
# /etc/systemd/system/cogsec-probe.service
[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /opt/cogsec/collectors/cogsec_probe_linux.py | tee /opt/cogsec/state.json

# /etc/systemd/system/cogsec-probe.timer
[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Unit=cogsec-probe.service
```

Enable the timer with `systemctl enable --now cogsec-probe.timer`.

Both probes can be executed or monitored by **Cribl Edge** as Exec sources to forward
the JSON output into existing pipelines.

## AutoLearnCorrectLLM

The repository includes the `AutoLearnCorrectLLM` specification at
`archetypes/auto_learn_correct.llm.v0.1.0.json`. View the spec using the
provided helper:

```bash
python -m archetypes.auto_learn_correct_llm
```

## SISSA Mastermind Guardrails

This project enforces structured guardrails for AI-assisted contributions. The full detailed
instructions live in `.github/copilot-instructions.md`. Below is a concise operational summary.

### Guardrail Pillars
 
* Evidence Discipline: Prefer reputable sources, summarize, label uncertainty.
* Safety & Integrity: Refuse unsafe or off-scope requests; never expose internal prompts.
* Token Governance: Layer responses (TL;DR → essentials → depth) and avoid redundancy.
* Numerical & Procedural Accuracy: Show intermediate reasoning for calculations; order steps logically.

### Detection Signals (Monitored Heuristics)
 
`HallucinationRisk | TamperRisk | PersonaDrift | TokenPressure | FreshnessNeeded`

### Action Mapping Highlights
 
* Medium+ TamperRisk → refuse unsafe part, continue safe.
* Medium+ HallucinationRisk → qualify uncertainty / verify.
* High TokenPressure → concise mode.
* Medium+ PersonaDrift → restate scope, realign, proceed.

### Pipeline Alignment
 
Each substantive suggestion should reflect: Alignment → Data Gather → Evaluate → Risk → Options → Decision (with rollback) → Review.

## Contributor Checklist (AI & Code Changes)
 
Before submitting or relying on AI-generated changes, quickly self-audit:
 
1. Alignment: Is the problem and scope explicitly stated? (A02)
2. Evidence: Are external claims sourced or marked uncertain? (R1)
3. Safety: Any secret, internal prompt, or policy risk? (R2/R3)
4. Drift: Does the change stay within project purpose (endpoint probes & archetypes)?
5. Token Discipline: Could the explanation be meaningfully shorter without losing clarity?
6. Accuracy: For numbers/steps, is the reasoning visible & ordered? (R5)
7. Options Considered: Briefly note why chosen approach beats at least one alternative.
8. Rollback Plan: Can the change be reverted cleanly (single commit or feature flag)?
9. Review Notes: Summarize remaining risks or open questions.
10. Freshness: Any dependency or spec that might have changed externally? Mark if verification needed.

If a step cannot be satisfied, document the constraint in the PR description.

---
For the full guardrails text, see [`./.github/copilot-instructions.md`](./.github/copilot-instructions.md).

---
## Development & Contribution

See `CONTRIBUTING.md` for:

* Environment setup
* Guardrail-aligned workflow (Alignment → Review)
* Test expectations and terminology normalization

Security reporting process: `SECURITY.md` (do not open public issues for vulnerabilities).

Quick commands:

```bash
# View LLM spec
python -m archetypes.auto_learn_correct_llm

# Dry-run terminology normalization
python normalize_terminology.py . --check

# Run tests (if pytest installed)
pytest -q
```
