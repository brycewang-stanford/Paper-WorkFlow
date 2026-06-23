# Draft Quality Gate Scorecard

> **L2 semantic review.** The L1 *structural* gate is executable — `check_workspace_gates.py`
> plus the other checkers prove a declared gate has its evidence on disk. This card is the L2
> *semantic* layer: a top-journal-AE critic judging credibility a script cannot. The two tiers
> compose — L1 must be green before L2 can PASS.
>
> **Verbatim discipline (load-bearing):** every fatal flag, every dimension capped below 7, and
> every blocking issue MUST appear in the Findings Register below with a `Severity` and a
> **verbatim evidence span** — the exact quoted text it refers to — plus a locator. A red flag
> with no quoted text is not admissible. Validate this card with
> `python3 scripts/check_review_scorecard.py <workspace>`.

Project: <short name>
Round: <k>
Scored at (Beijing): <YYYY-MM-DD HH:MM>
Scorer: quality-gate critic subagent (L2 semantic review)

## Dimension Scores

| Dimension | Score / 10 | Evidence with ledger/table/path | Fatal flag? |
|---|---:|---|---|
| 1. Contribution sharpness |  |  | no |
| 2. Identification credibility |  |  | no |
| 3. Robustness completeness |  |  | no |
| 4. Interpretation discipline |  |  | no |
| 5. Writing and structure |  |  | no |
| 6. Citation fidelity and positioning |  |  | no |
| 7. Reproducibility and governance |  |  | no |
| Total |  / 70 |  |  |

## Findings Register

Severity taxonomy:

- **blocking** — a fatal flag / hard inconsistency. PASS is impossible while it stands; it caps
  its dimension at <= 4 (the checker enforces both rules).
- **major** — a real defect that must be fixed before submission, but does not by itself force
  NOT PASS if the dimension still clears 7.
- **minor** — polish; does not gate.

| ID | Severity | Dim | Verbatim evidence span (exact quote) | Locator (file:line / table / claim) | Required fix |
|---|---|---:|---|---|---|
| F1 | minor | 5 | "<exact sentence from the manuscript or artifact>" | main.tex:120 | <fix> |

## Pass Decision

- Every dimension >= 7:
- Total >= 56:
- No fatal flags in identification / robustness / citation:
- No blocking finding in the register:
- Governance red flags absent:
- Evidence ledger claim strength matches manuscript wording:
- Design risk ledger has no blocking threats:
- Decision: PASS / NOT PASS

## Review Grade

Communication grade, not the gate (the gate is the binary PASS / NOT PASS above):

- STRONG-PASS (all dimensions >= 8, no major findings) / PASS / PASS-WITH-NOTES (passes but
  majors remain) / REVISE / REJECT
- Grade:

## Top 3 Shortfalls

1. [dimension -> stage] <shortfall and required fix>
2. [dimension -> stage] <shortfall and required fix>
3. [dimension -> stage] <shortfall and required fix>

## Return Instruction

- Return stage:
- Maximum return rounds used:
- Files to fix:
- Evidence required before re-scoring:
