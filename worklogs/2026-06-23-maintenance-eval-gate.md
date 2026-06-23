# 2026-06-23 Maintenance Eval Gate

## Scope

Path-scoped maintenance pass for `Paper-WorkFlow` while other agents may be
working in adjacent lanes.

## Finding

The held-out scorer was saturated at `1.000` across train, selection, and
regression splits, but the complexity ratchet was still an advisory script.
That left a gap: a future maintenance edit could pass `validate_skill.py` while
growing the always-loaded `SKILL.md` or reference-file count past the recorded
ceiling.

## Change

- `validate_skill.py` now compiles the maintenance eval scripts.
- `validate_skill.py` now runs `evals/score_skill.py --selftest`.
- `validate_skill.py` now runs `evals/check_complexity_budget.py --selftest`.
- `validate_skill.py` now runs `evals/check_complexity_budget.py` as a blocking
  gate.
- Eval documentation now treats the time-series gate-card miss as resolved and
  describes the complexity ratchet as an active validation guardrail.
- `references/skillopt-improvement-loop.md` now requires the complexity ratchet
  before adoption.

## Validation

- `python3 validate_skill.py` passed. The run now includes
  `evals/score_skill.py --selftest`, `evals/check_complexity_budget.py
  --selftest`, and the blocking complexity ratchet.
- `python3 evals/score_skill.py` passed with train / selection / regression
  means all `1.000`.
- `python3 evals/check_complexity_budget.py` passed: `SKILL.md` stayed at the
  recorded ceiling (`38,733` bytes), reference file count stayed at `29`, and
  reference bytes increased only within tolerance (`381,513 -> 381,762`).
- `git diff --check` passed.
