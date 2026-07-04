# 2026-07-04 Card (1995) IV Replication Case

## Scope

Second published-replication case for the August-plan week 4. The replication
suite now has Card-Krueger 1994 (DiD, gold re-verified against the AER PDF)
and Card 1995 (IV, gold pinned to the committed numeric benchmark that
recomputes on the shipped `demo-StatsPAI-skill/data/card.csv`).

## Change

- `evals/replication_cases/card_1995_iv_schooling.json` — active case.
  Headline coefficients (ols_return = 0.0747, iv_return = 0.1315) pinned to
  the committed numeric benchmark `card-iv-recovery`, which is the
  recomputable-in-repo source of truth (no transcription from tables:
  Card 1995 is an NBER WP / book chapter, not a paper with one canonical
  table row). 5% rel_tol on both coefficients, the partial_tol 20% band
  gives room for legitimate solver drift on the IV estimate.

## Integrity Decision

Unlike Card-Krueger (gold transcribed from the published AER tables this
session), Card 1995 is referenced by a recomputable in-repo artifact: the
parent AERS numeric benchmark `card-iv-recovery` recomputes the numbers
from the shipped CSV. That makes the gold a *measured fact on the same
data the agent will see*, not a memory, which the suite's "gold must be a
measured fact with a source" rule prefers. The case file documents this
explicitly so the next maintainer sees why this case pins to the
benchmark rather than a table.

## Validation

- `python3 evals/check_replication_accuracy.py --validate-suite evals/replication_cases`
  reports 5 valid cases (4 active, 1 template).
- `python3 evals/check_replication_accuracy.py --selftest` passed.
- `python3 validate_skill.py` passed end-to-end.
