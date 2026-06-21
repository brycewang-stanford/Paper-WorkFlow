# Measurement and Data-Quality Audit

Project: <short name>
Audit time (Beijing): <YYYY-MM-DD HH:MM>
Owner: data / measurement critic
Status: pending / pass / not_pass

Purpose: prove that every key variable is measured and constructed well enough that
the estimate is not driven by measurement error, undisciplined outlier/winsorize
choices, selective merges, or differential missingness. Complements
`02_data/sample_audit.md` (which proves sample-to-estimand alignment). Required
methodology: `references/measurement-and-data-quality.md`.

## 1. Construct Validity

| Construct | Proxy / variable | Role | Wedge (proxy vs construct) | Likely bias direction from the wedge |
|---|---|---|---|---|
| <e.g. innovation> | <e.g. patent count> | outcome / treatment / control / mechanism | <what the proxy misses or adds> | toward 0 / away / ambiguous |

- Second independent proxy checked for the key variable(s)? yes / no — result:
- Index/aggregation rule pre-specified before seeing results? yes / no — rule:

## 2. Measurement Error Characterization

| Variable | Equation side (X / Y / D) | Error type (classical / non-classical / misclassification) | Consequence for estimate | Remedy applied |
|---|---|---|---|---|
| <var> | X / Y / D | classical / non-classical / differential / misclassified | attenuation / ambiguous / SE-only / severe | validation sample / IV / bounds / did_misclassified / none |

- Treatment timing/status verified against an independent source? yes / no / n.a.
- If treatment may be misclassified: remedy or bound reported? yes / no — where:

## 3. Outliers, Winsorizing, and Transformations

- Outlier/winsorize/trim rule (percentile, symmetric?, group): <e.g. winsorize 1/99, two-sided, within year>
- Rule fixed BEFORE inspecting the treatment-outcome relationship? yes / no
- Main result robust to {no winsorize, alternative cut, robust regression}? artifact: 03_analysis/robustness/<...>
- Influence diagnostics (Cook's D / DFBETA / leverage) — result drives off a few units? yes / no — artifact:
- Transformations (log/IHS/asinh/ratio/deflation): variable -> transform -> units caveat noted? 

## 4. Merge / Linkage Diagnostics

| Merge step | Left grain | Right grain | Type (1:1 / m:1 / m:m) | Match rate | Master-only | Using-only | Non-match selective? |
|---|---|---|---|---:|---:|---:|---|
| <step> | <unit×time> | <unit×time> | 1:1 / m:1 | <%> |  |  | yes / no — evidence |

- Any `m:m` merge? yes / no  (if yes: justify or fix — usually a bug)
- Fuzzy/record linkage error rate estimated (sampled manual review)? yes / no / n.a.

## 5. Missingness

| Variable | % missing | Missing by treatment vs control | Assumed mechanism (MCAR/MAR/MNAR) + argument | Handling | Bounds if selective? |
|---|---:|---|---|---|---|
| <var> | <%> | <t: x% / c: y%> | <mechanism + why> | complete-case / MI / indicator | Lee / Manski / none |

- Differential missingness or attrition present? yes / no — addressed how:
- Outcome imputed for any causal estimand? yes / no  (if yes: justify carefully)

## 6. Panel and Temporal Integrity

- Duplicate (unit, time) keys checked and resolved? yes / no
- Balanced / unbalanced; entry-exit handling:
- Look-ahead leakage check (no future info in pre-period / features)? pass / fail
- First-treated cohort coding and treatment reversals/exits verified? yes / no / n.a.

## 7. Aggregation, Weights, and Units

- Analysis unit matches the estimand level (no ecological/aggregation bias)? yes / no
- Weights used (none / analytic / sampling / survey) — does weighting change the estimand?
- Units / deflator base year / PPP-vs-nominal / scale consistent with codebook? yes / no

## 8. Decision

Decision: PASS / NOT PASS

Blocking issues:

- <none, or exact measurement/construction blocker>

Quality-gate caps triggered (see `measurement-and-data-quality.md` §9):

- <none, or e.g. "identification capped at 5: outcome proxy is noisy, ME direction uncharacterized">

Required fix before Method Gate:

- Stage:
- Owner:
- Evidence needed:

State writeback: workflow_state.json.empirical_audit.construct_validity = <pass/not_pass>;
.missingness_balance = <pass/not_pass>; artifacts.measurement_audit = "02_data/measurement_audit.md".
</content>
