# Contributing to `sissa_ivy`

Thank you for your interest in improving this project. This repository provides lightweight endpoint
probes plus archetype specifications (e.g. `AutoLearnCorrectLLM`). We apply the **SISSA Mastermind Guardrails**
(see [`./.github/copilot-instructions.md`](./.github/copilot-instructions.md)) to keep changes
safe, evidence-based, and easy to review.

---
## Quick Start (Development Environment)

```bash
# (Optional) create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install any local dev dependencies once requirements file exists (placeholder)
# pip install -r requirements.txt

# Run the AutoLearnCorrectLLM spec viewer
python -m archetypes.auto_learn_correct_llm

# Run terminology normalizer in check mode at repo root
python normalize_terminology.py . --check
```

---
## Guardrail-Aware Contribution Flow

| Pipeline Stage | What Reviewers Expect | PR Template Hook |
| -------------- | --------------------- | ---------------- |
| A02 Alignment  | Problem & scope crisply stated | Checklist: Alignment |
| A04 Data Gather| Inputs, references, evidence or uncertainty labels | Data Gather |
| A06 Evaluate   | Alternatives & trade-offs briefly compared | Evaluation |
| A07 Risk       | Enumerated risks + mitigations (rollback, perf, security) | Risk |
| A08 Options    | At least 2 considered paths (even if one rejected) | Options |
| A09 Decision   | Chosen path + rollback clause | Decision Gate |
| A10 Execution  | Minimal, incremental change; test notes | Execution |
| A12 Review     | Follow-up ideas / deferred work logged | Review |

---
## Coding Guidelines

* Python >= 3.10 preferred (uses modern typing & structural features if added later).
* Keep scripts dependency-light; avoid heavy frameworks for simple operations.
* Favor pure functions; isolate side effects (filesystem, network) for future testing.
* Maintain atomic file operations when writing output (see `normalize_terminology.py`).
* Preserve existing license headers / authorship.

### Style & Linting

No strict formatter is enforced yet. If added later (e.g. `ruff`, `black`), update this file.
Keep functions short & intention-revealing. Add docstrings for modules and non-trivial functions.

---
## Testing

A minimal test suite will live under `tests/`. For any new module:

1. Provide at least one "happy path" test.
2. Provide one failure mode or edge case.
3. Avoid network / external service dependencies; mock if needed.

Example (planned) command to run tests:

```bash
pytest -q
```

---
## Submitting a Pull Request

1. Create a feature branch.
2. Make focused commits (logical units) — squash only if noisy.
3. Run: `python normalize_terminology.py . --check` and ensure no pending terminology drift.
4. Fill out every relevant checkbox in the PR template; if a section is N/A, state why.
5. Add a rollback note (e.g., revert commit hash, or remove feature flag).

---
## Security & Responsible Disclosure

Please do not open public issues for potential security vulnerabilities. Instead, create a minimal
private report (process defined in `SECURITY.md` once published). Avoid including exploit details in PRs.

---
## Deferred / Future Enhancements

* Add CI workflow (lint + tests + terminology check).
* Add `requirements.txt` or `pyproject.toml` once dependencies expand.
* Introduce structured logging for probes.
* Provide packaging / distribution guidance.

---
## Questions / Clarifications

When uncertain, pick the most conservative assumption, document it in the PR description under
"Assumptions", and proceed. Reviewers will guide adjustments.

Thank you for helping keep the project lean, auditable, and trustworthy.
