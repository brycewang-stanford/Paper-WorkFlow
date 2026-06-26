# Method Gate

Project: <short name>
Gate round: <k>
Audit time (Beijing): <YYYY-MM-DD HH:MM>
Auditor: method-gate critic subagent

## 1. Primary Design

- Primary design:
- Primary estimator:
- Analysis backend: python-statspai / stata / r
- Backend version report: 00_meta/analysis_backend.md
- Target estimand:
- Sample audit: 02_data/sample_audit.md
- Design register: 03_analysis/design_register.md
- Main result: 03_analysis/results/main_results.json

## 2. Required Artifact Table

| Requirement | Path | Present? | Pass? | Notes |
|---|---|---:|---:|---|
| Sample / estimand audit | 02_data/sample_audit.md | no | no |  |
| Design register | 03_analysis/design_register.md | no | no |  |
| Analysis backend report | 00_meta/analysis_backend.md | no | no |  |
| Main estimation script | 03_analysis/<script> | no | no |  |
| Main results summary | 03_analysis/results/summary.md | no | no |  |
| Identification diagnostic | 03_analysis/results/<diagnostic> | no | no |  |
| Robustness matrix | 03_analysis/robustness/ | no | no |  |
| Sensitivity / refuter | 03_analysis/robustness/<sensitivity> | no | no |  |
| Design risk ledger | 03_analysis/design_risk_ledger.md | no | no |  |
| Evidence ledger | 00_meta/evidence_ledger.md | no | no |  |
| Rebuild path | REPLICATION.md / run_all.sh | no | no |  |

## 3. Design Gate Card

Reference: `references/design-gate-cards.md`

Design card used: DiD / IV / RDD / SC-SDID / Panel FE / DML-HTE / DAG-refuter / Prediction-assisted / Time Series-VAR / other

| Gate item | Required artifact | Path | Present? | Pass? | Claim consequence |
|---|---|---|---:|---:|---|
| <item> | <artifact> | <path> | no | no | causal / qualified_causal / descriptive / exploratory / no_claim |

Claim Downgrade:

- Strongest allowed claim after this gate: causal / qualified_causal / descriptive / exploratory / no_claim
- Claims that must be downgraded in `00_meta/evidence_ledger.md`:
- Claims capped by `03_analysis/design_risk_ledger.md`:
- Manuscript sections affected:

## 4. Hard Flags

- Parallel trends / exclusion / continuity / overlap:
- Bad-control risk:
- Estimand / estimation-sample drift:
- Missingness, balance, or overlap:
- Inference level, weights, or clustering:
- P-hacking or researcher degrees of freedom:
- External validity / transportability:
- Spillover / SUTVA / interference:
- Attrition or sample selection:
- Design risk ledger blocking threats:
- Data governance or access restriction:
- Runtime fallback used:
- Backend parity / cross-validation:

## 5. Decision

Decision: PASS / NOT PASS

Allowed claim:

- Causal:
- Descriptive:
- Exploratory only:

## 6. Next Action

If NOT PASS, route back to:

- Stage:
- Required fix:
- Owner:
- Evidence needed before re-audit:
