# Pre-Registration & Analysis Plan — <研究短名 / study short name>

> **Lock the primary specification BEFORE you estimate.** This artifact is the
> executable guard against specification search / HARKing (choosing the spec after
> seeing which one gives stars). Instantiate it at the end of Stage 1 (design) or the
> very start of Stage 3 (estimation), commit it, then run
> `python3 scripts/check_preregistration.py <workspace>`. The Method Gate will not
> PASS while this is `UNLOCKED` or while main results exist without a prior lock.
>
> Confirmatory ≠ exploratory. Anything not registered below is **exploratory** and
> must be labelled as such in the manuscript. Honest exploration is welcome; it just
> may not be dressed up as a pre-planned confirmatory finding.

## Lock Status

- locked: <YYYY-MM-DD HH:MM Asia/Shanghai | UNLOCKED>
- lock_commit: <git short sha at lock time | n/a>
- locked_before_estimation: <yes | no>   <!-- must be `yes`: lock precedes main_results.json -->
- analyst: <name / agent id>
- primary_design: <DiD | IV | RDD | SC | event-study | panel-FE | OLS | ...>

## Confirmatory Hypotheses (registered before outcomes are seen)

Each row is a pre-committed test. Fill every cell; no placeholders survive the checker.

| ID | Hypothesis (directional) | Outcome (Y) | Estimand | Primary specification | Predicted sign |
|----|--------------------------|-------------|----------|-----------------------|----------------|
| H1 | <treatment raises Y>     | <y_var>     | <ATT>    | <TWFE DiD; FE=unit+time; cluster=unit> | <+> |

## Primary Specification Lock

The single specification each hypothesis is judged on. Robustness variants are listed
but do not replace the primary.

- sample: <inclusion / exclusion rules, time window, unit of analysis>
- main estimator: <e.g. Callaway–Sant'Anna group-time ATT, then aggregate>
- fixed controls: <covariate set held constant across the confirmatory tests>
- standard errors / clustering: <cluster level ≥ treatment-assignment level>
- multiple-testing plan: <family of outcomes; correction = Romano–Wolf | BH | none + why>
- pre-specified robustness: <list the variants planned in advance>

## Confirmatory vs Exploratory

- Confirmatory analyses are exactly the H-rows above. Their wording in the paper may
  claim a pre-planned test.
- Every other result is **exploratory** and must be worded as descriptive / suggestive.
- Exploratory analyses (registered post-hoc, for transparency):
  - E1: <what, and why it is exploratory>

## Deviations from Plan

Record every departure from the lock. An empty table is fine; a hidden deviation is not.

| Deviation | When | Reason | Effect on claim strength |
|-----------|------|--------|--------------------------|
| (none)    |      |        |                          |

## Provenance (decision attribution)

Tag who drove each load-bearing choice, so the audit trail survives handoff.

- `[human]` decisions: <title, target journal, identification strategy sign-off, ...>
- `[ai-suggested]` decisions: <...>
- `[ai-executed]` decisions: <...>
- `[user-revised]` decisions: <...>
