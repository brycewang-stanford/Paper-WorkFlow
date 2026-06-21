# Inference Report — <short name>

Last updated (Beijing): <YYYY-MM-DD HH:MM>
Owner: Stage 3 estimation / inference critic
Reference: [`../references/inference-and-uncertainty.md`](../references/inference-and-uncertainty.md)

Purpose: lock the uncertainty-quantification choices for every main result so that
table notes, the manuscript, and the quality gate all read from one source. Point estimates
live in `03_analysis/results/main_results.json`; this file documents the standard errors,
confidence intervals, p-values, and multiple-testing corrections **around** them.

## 1. Standard Errors and Clustering Decision

| Result ID | Treatment assignment level | Chosen cluster level | # clusters (per dim) | Sampling- or design-based reason | Script / MCP handle |
|---|---|---|---:|---|---|
| R1 | <e.g. province × year> | <e.g. province> |  | <why this level, per inference pack §2> | 03_analysis/<script>:<line> |

Rules:

- Cluster level is at least the treatment-assignment level (a policy assigned at the province level
  is not clustered at the individual level).
- Not clustered higher than justified — record the trade-off between correct level and enough clusters.
- If the headline significance flips when the clustering dimension changes, that is disclosed in the
  manuscript, not hidden behind the most favorable specification.

Alternative SE robustness (inference pack §2, StatsPAI robustness block 4):

| Result ID | Alternative | SE / CI | Conclusion stable? | Artifact |
|---|---|---|---|---|
| R1 | two-way / dropped clustering / Conley | <se or ci> | yes / no | 03_analysis/robustness/<file> |

## 2. Few-Cluster / Small-Sample Correction

Trigger check: is any main result based on few clusters (G ≲ 30–50, unbalanced, or few treated clusters)?

| Result ID | # clusters | Few-cluster trigger? | Method used | Bootstrap/CI p-value | Artifact |
|---|---:|---|---|---|---|
| R1 |  | yes / no | wild cluster bootstrap (WCR, 6-pt) / CR2 / CR3 / t(G−1) / n.a. |  | 03_analysis/robustness/<file> |

If triggered and no correction is applied, the result cannot be reported as significant on asymptotic SEs alone.

## 3. Randomization / Permutation Inference

| Result ID | Used? | What is permuted | # permutations | Seed | RI p-value | Matches asymptotic? | Artifact |
|---|---|---|---:|---|---|---|---|
| R1 | yes / no | treatment labels / timing / unit |  |  |  | yes / no | 03_analysis/robustness/<file> |

Required when assignment is (quasi-)random, clusters are very few, or for the synthetic-control in-space placebo.
Seeds and permutation counts are also registered in `REPLICATION.md` (controlled randomness).

## 4. Multiple Hypothesis Testing

Pre-specified primary outcome(s): <name(s)>  (see `01_proposal/pre_analysis_plan.md` if registered)

| Test family | Members (outcomes / subgroups) | Confirmatory (FWER) or exploratory (FDR)? | Correction | Raw p | Adjusted p / q | Artifact |
|---|---|---|---|---|---|---|
| <e.g. innovation outcomes> | <list> | FWER / FDR | Romano-Wolf / Holm / Bonferroni / BH / sharpened q | <p> | <adj> | 03_analysis/robustness/<file> |

Rules:

- Families group conceptually-related tests; correction is within-family, not over every p-value in the paper.
- Subgroup heterogeneity claims are pre-specified, family-corrected, or demoted to exploratory appendix.
- The manuscript uses the corrected significance, not the raw p-value.

## 5. Weak-Instrument-Robust Inference (IV only)

| Result ID | First-stage effective F | Weak? | tF-adjusted SE/CI (single endog.) | Anderson-Rubin CI | CLR CI | Artifact |
|---|---:|---|---|---|---|---|
| R1 |  | yes / no |  |  |  | 03_analysis/robustness/<file> |

Report a weak-IV-robust interval, not just the 2SLS t-ratio, whenever the first stage is weak.

## 6. Reporting Discipline (carried into tables and text)

- [ ] Main tables report confidence intervals (or SEs) alongside point estimates, not only stars.
- [ ] Each headline coefficient has an economic-magnitude reading (share of mean / SD).
- [ ] No "marginally significant" language; null results are stated as nulls (with MDE if relevant).
- [ ] Table notes state SE type, cluster level and count, bootstrap/RI use, and any MT correction.

## 7. Open Inference Issues

| Issue | Affected result | Blocking? | Resolution |
|---|---|---:|---|
| <issue> | R1 | yes / no | <action> |
