# Design Register

Project: <short name>
Stage: 3
Status: draft / locked / revised
Last updated (Beijing): <YYYY-MM-DD HH:MM>

## 1. Research Contract

- Question:
- Target estimand:
- Treatment / exposure:
- Outcome:
- Unit of observation:
- Estimation sample:
- Sample window:
- Primary comparison group:
- Sample audit: 02_data/sample_audit.md
- Target journal / audience:

## 2. Identification Design

- Primary design: DiD / IV / RDD / synthetic control / panel / DML / other
- Primary estimator:
- Analysis backend: python-statspai / stata / r
- Backend version report: 00_meta/analysis_backend.md
- Core identifying assumption:
- Why this assumption is plausible here:
- Main threats to validity:
- Design transparency commitments:
  - Pre-analysis plan or design memo:
  - Researcher degrees of freedom locked before seeing results:
  - Power / MDE or detectable effect note:
  - Random seeds and version pinning:

## 3. Variable Construction

| Role | Variable | Construction | Source | Timing | Notes |
|---|---|---|---|---|---|
| Outcome | <Y> | <formula> | <source> | <pre/post> | <notes> |
| Treatment | <D> | <formula> | <source> | <pre/post> | <notes> |
| Control | <X> | <formula> | <source> | <pre-treatment/confounder/mediator/collider> | <notes> |

Bad-control screen:

- Controls measured after treatment:
- Candidate mediators excluded from baseline controls:
- Colliders or selection variables excluded:
- Time-varying controls justified:

## 4. Required Artifacts

| Artifact | Required? | Path | Status |
|---|---:|---|---|
| Sample / estimand audit | yes | 02_data/sample_audit.md | missing / present |
| Main estimation script | yes | 03_analysis/<script> | missing / present |
| Analysis backend report | yes | 00_meta/analysis_backend.md | missing / present |
| Main results JSON | yes | 03_analysis/results/main_results.json | missing / present |
| Diagnostic plot/table | yes | 03_analysis/results/<artifact> | missing / present |
| Robustness matrix | yes | 03_analysis/robustness/ | missing / present |
| Sensitivity / refuter | design-specific | 03_analysis/robustness/<artifact> | missing / present |

## 5. Fallback Plan

If the primary design fails, do not write a causal claim as if it passed.

| Failure trigger | Fallback action | Return stage | Decision log entry |
|---|---|---:|---|
| <e.g. pre-trends fail> | <e.g. alter window or estimator> | 3 | <decision text> |
| <e.g. weak instrument> | <e.g. find stronger IV or downgrade claim> | 1/3 | <decision text> |

## 6. Method Gate Summary

- Current gate status: pending / pass / not_pass
- Blocking missing artifacts:
- Claim allowed in draft: causal / descriptive / exploratory
- Next action:
