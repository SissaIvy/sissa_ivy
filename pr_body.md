feat(closed-loop): security orchestrator + tests/docs; AML battle-test + CI; cost/ROI knobs; submit-time gates

## Summary

Adds a closed-loop security orchestration component and supporting infra:
- `closed_loop_security.py` — persona + overlay orchestration, explainable deterministic output.
- AML artifacts: offline components, pipeline submit scripts, `README-aml`.
- Cost/ROI and submit-time gates: in-run accounting, evaluator with tunable thresholds (cost / explainability / fail-rate / token-cost).
- CI: new AML smoke job + FAISS smoke job; a path-scoped artifact upload step.
- Governance: CODEOWNERS, labeler workflow, LICENSE/NOTICE, README license badge.

This is primarily orchestration, CI and documentation + safety guardrails. No breaking API changes to existing CLI commands.

## Highlights / Why it matters

- Safety & cost control: submit-time gates let reviewers and infra enforce budget/explainability thresholds before compute-heavy runs.
- Tested: unit + smoke tests for FAISS and closed-loop flow. 10/10 unit tests pass locally.
- Production readiness: CI smoke jobs isolate heavy deps (FAISS/AML) to dedicated runners; meta persistence avoids repeated scans.
- Governance: CODEOWNERS + labeler automates ownership and PR triage; VS Code Mastermind guardrail seed added for IDE personas (`.vscode/SISSA_Mastermind_Seed.v1.json`).

## Changed / Added (high level)
- `closed_loop_security.py` (core)
- `tests/test_closed_loop.py`
- `tests/test_faiss_cli_meta.py`, `tests/test_persist_meta_e2e.py`
- `.github/workflows/ci.yml` (added: smoke-faiss, smoke-aml)
- `episodic_memory/faiss_index.py`, `memory_cli.py` (index meta persistence & search)
- `README.md` (ANN Index / Index Search flags, Allegory guides)
- `README-aml`, AML submit scripts
- `LICENSE`, `NOTICE`, packaging metadata updates, CODEOWNERS, labeler rules

## Validation
- Unit tests: `python -m unittest discover -s tests -p "test_*.py"` — OK (10/10)
- FAISS smoke tests: run under dedicated CI runner (Ubuntu, Python 3.11)
- Build: `python -m build` — wheel/sdist generated
- Twine: `python -m twine check dist/*` — passed
- Local AML chain: evaluator gates and overrides exercised; cost accounting tested

## How to test locally (quick)
1. Run unit tests (light):
   `python -m unittest discover -s tests -p "test_*.py" -v`
2. (Optional) FAISS smoke (requires faiss + numpy):
   `pip install -e ".[faiss]" numpy pytest`
   `pytest -k faiss_cli_meta -q`
3. (Optional) AML smoke: follow `README-aml` instructions (offline components simulate workspace)

## CI notes
- Normal unit tests run on PRs as before.
- Heavy smoke jobs run on Ubuntu/Py3.11 runners and are path-scoped to avoid extra cost.
- Labeler auto-applies `type:feature`, `area:security-orchestration`, `docs` when relevant files change.

## Merge & Release plan
- Merge: Squash & merge after CI green and review approvals.
- Tag: after merge, create a patch release for closed-loop/AML features:
```
git checkout main && git pull
git tag -a v0.2.2 -m "Closed-loop system, AML battle-test, CI guardrail, Cost/ROI knobs, submit-time gates"
git push origin v0.2.2
```
(Release will be created by existing release workflow which reads CHANGELOG.)

Reviewer checklist (copy for PR)
- CI (unit + lint) green
- smoke-faiss and smoke-aml jobs green on dedicated runners
- Spot-check closed_loop_security.py for deterministic outputs and privacy (no secret logs)
- README / AML docs adequate for oncall/runbook
- Approve license/packaging metadata changes (legal signoff if required)

Suggested reviewers & labels
- Reviewers: infra/CI owner, security-owner, embeddings/FAISS owner
- Labels: type:feature, area:security-orchestration, docs, ci
