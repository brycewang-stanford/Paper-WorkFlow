# Pre-Registration & Analysis Plan — <研究短名 / study short name>

> **Lock the primary specification BEFORE you estimate.** This artifact is the
> executable guard against specification search / HARKing (choosing the spec after
> seeing which one gives stars). Instantiate it at the end of Stage 1 (design) or the
> very start of Stage 3 (estimation), commit it, then run
> `python3 scripts/check_preregistration.py <workspace>`. The Method Gate will not
> PASS without either a prospective lock or an explicitly disclosed retrospective record.
> Existing-result entry: follow references/design-transparency.md §2.1; never backdate a plan.
>
> Confirmatory ≠ exploratory. Anything not registered below is **exploratory** and
> must be labelled as such in the manuscript. Honest exploration is welcome; it just
> may not be dressed up as a pre-planned confirmatory finding.

## Lock Status

- locked: <YYYY-MM-DD HH:MM Asia/Shanghai | UNLOCKED>
- lock_commit: <git short sha at lock time | n/a>
- locked_before_estimation: <yes | no>   <!-- yes for prospective; no for disclosed retrospective analysis -->
- analyst: <name / agent id>
- primary_design: <DiD | IV | RDD | SC | event-study | panel-FE | OLS | ...>

## Existing-result mode (optional)

For an existing-result study, add these fields to Lock Status, remove H-rows from the next table,
and list the actual E-analyses under Confirmatory vs Exploratory. Keep the two state/file records consistent:

```text
- analysis_mode: retrospective
- prior_results_seen: describe earlier exposure and provenance
- analysis_history: describe previous analysis choices, unknown history, and remediation
- prospective_validation: describe independent future validation, or explicitly state none
```

Use `design_lock.status=retrospective`, `locked_before_estimation=false`, `confirmatory_count=0`.
This is disclosure, not preregistration; the current record cannot authenticate historical timing.

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
- Every other result is **exploratory**. Disclose its timing; causal wording separately requires
  a defensible identification design and corresponding evidence in the Method Gate.
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
