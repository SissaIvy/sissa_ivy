# CogSecEndpointSecurity

![Windows Probe Validation](https://github.com/${{github.repository}}/actions/workflows/windows-probe.yml/badge.svg)
![War Room CI](https://github.com/${{github.repository}}/actions/workflows/warroom-ci.yml/badge.svg)

Native endpoint probes for Windows and Linux that collect basic health and security posture
without relying on a heavyweight agent. The probes emit a compact JSON record and, for Windows,
optionally append a CSV line that matches the `cogsec_workflow.py` health schema.

> Project Renamed: Formerly `sissa_ivy`. References to the old name in historical commits, tags, or external scripts should be updated. Backward compatibility notes:
>
> * Python package previously at `platform` → now `cogsec_platform` (to avoid stdlib clash)
> * Repository level branding updated; functional module names for probes unchanged.
>

## Repository Index

* **archetypes/** — LLM specs & personas (e.g., AutoLearnCorrectLLM, SISSA guardrails)

* **cogsec/** — collectors/probes (Linux/Windows), validators, schemas
* **integrations/** — external clients (e.g., ServiceNow)
* **scripts/** — automation (bootstrap, hygiene, drift, normalization)
* **reports/** — generated artifacts (intel, tickets, health)
* **ui/psyops-war-room/** — War Room frontend (Vite/React) and preview
* **.github/workflows/** — CI pipelines (hygiene, layout, bidi guard, drift report, schema lint)

### Quick Links

* Developer onboarding: [`docs/DEVELOPER_QUICKSTART.md`](docs/DEVELOPER_QUICKSTART.md)

* Build log (current state): [`docs/BUILD_LOG.md`](docs/BUILD_LOG.md)

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

### Windows Probe CI

The GitHub Actions workflow `windows-probe.yml` runs on `windows-latest` to:

1. Execute the probe in quick + diagnostics mode (ensuring `schema_version` and required fields).
2. Install and run Pester tests in `tests/windows`.
3. Archive a sample JSON artifact (`probe_sample.json`).

If you extend the probe schema, increment `schema_version` and update or add Pester tests validating new fields. Retain deprecated alias fields (e.g. `net_in`, `net_out`) for at least one minor version before removal.

Badge above reflects latest workflow status. To run locally on Windows:

```powershell
pwsh -NoProfile -File .\cogsec\collectors\Get-CogSecEndpointState.ps1 -Quick -Diagnostics -JsonPath - | ConvertFrom-Json | Format-List *
Invoke-Pester -Path tests/windows -CI
```

### Linux Probe Synthetic Tests

A lightweight unit test (`tests/test_cogsec_probe_linux.py`) validates the shape and bounds of the Linux probe JSON using two synthetic records (normal + edge). This guards against accidental contract drift (field removal, type changes, or out-of-range percentages) without requiring privileged system calls during CI.

Run just those tests:

```bash
pytest -q tests/test_cogsec_probe_linux.py
```

All percentage fields (`cpu`, `mem`, `disk`) are asserted to be within 0–100 and network counters non-negative integers. Add new assertions here if you extend the emitted record.

### Linux Probe Schema & Validation

The Linux probe output is validated by a permissive JSON Schema (`schema/linux_probe.schema.json`). Use the validator script to catch contract drift:

```bash
# Generate a live sample and validate via stdin
python cogsec/collectors/cogsec_probe_linux.py | python scripts/validate_linux_probe.py -

# Or validate an existing capture
python scripts/validate_linux_probe.py sample_probe.json
```

Pretty-print and strict sampling checks:

```bash
python cogsec/collectors/cogsec_probe_linux.py --pretty --json-path -
python cogsec/collectors/cogsec_probe_linux.py --strict --json-path probe.json || echo "strict gate tripped"
```

The strict gate returns exit code 2 when CPU, MEM, and DISK are all reported as 0.0 (heuristic sampling failure indicator).

### Ingestion Prototype & Schema Validation

An experimental local ingestion prototype is included to illustrate downstream processing patterns:

* Schema: `schema/endpoint_state.schema.json` (JSON Schema draft 2020-12)
* Ingestion service (SQLite): `cogsec_platform/ingestion_service.py` (formerly `platform/`)
* Validator helper: `validate_probe_record.py`

Run example:

```bash
python validate_probe_record.py sample.json
python -m cogsec_platform.ingestion_service ingest sample.json
python -m cogsec_platform.ingestion_service list
python -m cogsec_platform.ingestion_service get HOSTNAME
```

Sample generation (Linux host) piping into validator:

```bash
python cogsec/collectors/cogsec_probe_linux.py | python validate_probe_record.py -
```

Schema Versioning Strategy:

* Patch bump (1.1.1 -> 1.1.2): purely additive / non-breaking fields.
* Minor bump (1.1.x -> 1.2.0): may deprecate alias fields (e.g. `net_in`, `net_out`).
* Major bump (1.x.x -> 2.0.0): structural changes requiring client updates.

Backward compatibility window: alias fields retained for at least one full minor cycle after introduction of canonical replacements.

SLA (Prototype Phase):

* Probe execution time: < 2s (Quick mode) / < (SampleSeconds + 2)s with sampling.
* Data freshness target for summaries (future service): ≤ 5 minutes.
* Validation failure response: reject ingestion with `ValidationError` (non-retryable without fix).

Security Notes (Prototype):

* No authentication or signing yet; production design should include message signing + transport TLS.
* SQLite used for simplicity—replace with a durable store (PostgreSQL/ClickHouse) for scale.

### War Room CI Workflows

The unified CI workflow `warroom-ci.yml` runs both Python tests (Linux) and probe tests (Windows). The older `windows-probe.yml` remains temporarily for transition and will be deprecated after one stable release.

Deprecation timeline:

* Current release: Both workflows active.
* Next minor: `windows-probe.yml` marked deprecated (README update).
* Following minor: Legacy workflow removed.

Use the War Room badge above to track consolidated status.

## Ops Cadence & Ownership

**BlackOps (platform):**
* Owns all CI gates: `hygiene.yml`, `schema-lint.yml`, `bidi-guard.yml`, `layout-guard.yml`.
* Responsible for weekly Branch Drift Reports and remote branch clean-ups.
* Maintains the onboarding path (`make onboard`) and Codespaces defaults.

**PsyOps (remediation):**
* Owns Ordnance intel generation and auto-resolve policy.
* Manages ServiceNow integration (dry-run for PRs, real runs on protected branches).
* Maintains incident taxonomy and framework mapping updates.

## CI Workflow Dispatch (Manual Triggering)

To manually (re)run core guardrail workflows (`hygiene`, `schema-lint`, `bidi-guard`, `layout-guard`) from any subdirectory:

```bash
# Requires a PAT with 'repo' and 'workflow' scopes if the default GITHUB_TOKEN 403s.
make ci-dispatch
```

The underlying script (`scripts/trigger_all_ci.sh`) will:

1. Resolve repo root.
2. Enumerate target workflow files.
3. Attempt dispatch on the current branch, then fallback to the default branch.
4. Provide colored diagnostics and token scope hints if a 403 (permission) error occurs.
5. Summarize the latest runs (ID, workflow name, branch, status, conclusion, title).

Direct usage without Make:

```bash
bash scripts/trigger_all_ci.sh
```

If you see: `Resource not accessible by integration`, authenticate with a classic Personal Access Token:

```bash
gh auth login --with-token < token.txt   # token must include: repo, workflow
```

Verify scopes via response headers (script prints `X-OAuth-Scopes`).
