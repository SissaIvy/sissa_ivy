# #SISSA Mastermind Memory Seed (VS Code)

This ready-to-use JSON seed provides a persona guardrail for supervising intent detection, safety, token budgeting, and evidence discipline when working in VS Code.

- File: `.vscode/SISSA_Mastermind_Seed.v1.json`
- Purpose: high-priority guidance for all #SISSA personas; prevents tampering and instruction hierarchy reversals; enforces explainable, budget-aware answers.

## How to use

1. Keep the JSON file in `.vscode/` (already added).
2. If your VS Code AI extension supports custom “system” or “memory” seeds, point it to this file or paste the JSON into its system prompt field.
3. Prefer “read-only” usage: treat it as a top-level, non-editable memory block.

Notes
- The seed is domain-agnostic and pairs well with the Closed-Loop SOC orchestrator and the Suntari allegory guides.
- Signals to track in your prompts or tool metadata: `HallucinationRisk`, `TamperRisk`, `PersonaDrift`, `TokenPressure`, `FreshnessNeeded`.
- Budget modes: Tight / Standard / Deep Dive.

## Maintenance

- Versioned as `SISSA_Mastermind_Seed.v1.json`.
- Update sparingly; keep rules concise and consistent with README/Allegory.
