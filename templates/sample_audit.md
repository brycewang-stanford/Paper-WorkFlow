# Sample and Estimand Audit

Project: <short name>
Audit time (Beijing): <YYYY-MM-DD HH:MM>
Owner: data / method critic
Status: pending / pass / not_pass

Purpose: prove that the estimation sample, treatment timing, outcome construction,
and inference level match the target estimand. This file is required before the
Method Gate can pass.

## 1. Estimand Alignment

- Target population:
- Estimation sample:
- Unit of observation:
- Unit of treatment assignment:
- Time frequency:
- Treatment start rule:
- Outcome measurement window:
- Comparison group:
- Does the estimation sample change the estimand? yes / no
- If yes, explain the new estimand:

## 2. Sample Construction Flow

| Step | Input | Output | N rows | N units | N treated | N control | Drop / transform reason | Script and line |
|---|---|---|---:|---:|---:|---:|---|---|
| Raw import | 02_data/raw/<file> | 02_data/<intermediate> |  |  |  |  |  | 02_data/<script>:<line> |
| Merge | 02_data/<left>, 02_data/<right> | 02_data/<intermediate> |  |  |  |  |  | 02_data/<script>:<line> |
| Analysis file | 02_data/<intermediate> | 02_data/clean.parquet |  |  |  |  |  | 02_data/<script>:<line> |
| Estimation sample | 02_data/clean.parquet | 03_analysis/results/main_sample.json |  |  |  |  |  | 03_analysis/<script>:<line> |

Required checks:

- Merge keys are unique at the declared unit and frequency.
- Dropped units/periods are explained before outcomes are inspected.
- Treatment timing is not inferred from post-treatment outcomes.
- Panel balance or attrition rules are explicit.
- Public outputs satisfy the data governance disclosure boundary.

## 3. Variable and Construct Audit

| Construct | Variable | Role | Source | Formula / transform | Timing | Missing rule | Bad-control status |
|---|---|---|---|---|---|---|---|
| <construct> | <var> | outcome / treatment / control / mechanism | <source> | <formula> | pre / post / time-varying | <drop/impute/flag> | ok / mediator / collider / review |

Hard checks:

- Outcomes are defined without using treatment status unless the design requires it.
- Controls are pre-treatment confounders or explicitly justified time-varying controls.
- Mediators and colliders are not included in the baseline control set.
- Transformations, winsorization, deflation, and scaling match `02_data/codebook.md`.

## 4. Missingness, Balance, and Overlap

| Check | Artifact | Result | Pass? | Notes |
|---|---|---|---:|---|
| Missingness by treatment/control | 02_data/<missingness_table> |  | no |  |
| Attrition or sample survival | 02_data/<attrition_table> |  | no |  |
| Baseline balance / standardized differences | 03_analysis/results/<balance_table> |  | no |  |
| Overlap / common support | 03_analysis/results/<overlap_plot> |  | no |  |
| Pre-period outcome levels/trends | 03_analysis/results/<pre_period_artifact> |  | no |  |

## 5. Inference-Level Check

- Assignment or policy level:
- Planned clustering level:
- Number of clusters:
- Small-cluster correction needed? yes / no
- Weights used? none / survey / sampling / propensity / other
- Does the clustering or weighting choice match the estimand? yes / no

## 6. Decision

Decision: PASS / NOT PASS

Blocking issues:

- <none, or exact sample/construct blocker>

Required fix before Method Gate:

- Stage:
- Owner:
- Evidence needed:
