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
- Design register: 03_analysis/design_register.md
- Main result: 03_analysis/results/main_results.json

## 2. Required Artifact Table

| Requirement | Path | Present? | Pass? | Notes |
|---|---|---:|---:|---|
| Design register | 03_analysis/design_register.md | no | no |  |
| Analysis backend report | 00_meta/analysis_backend.md | no | no |  |
| Main estimation script | 03_analysis/<script> | no | no |  |
| Main results summary | 03_analysis/results/summary.md | no | no |  |
| Identification diagnostic | 03_analysis/results/<diagnostic> | no | no |  |
| Robustness matrix | 03_analysis/robustness/ | no | no |  |
| Sensitivity / refuter | 03_analysis/robustness/<sensitivity> | no | no |  |
| Evidence ledger | 00_meta/evidence_ledger.md | no | no |  |
| Rebuild path | REPLICATION.md / run_all.sh | no | no |  |

## 3. Hard Flags

- Parallel trends / exclusion / continuity / overlap:
- Bad-control risk:
- P-hacking or researcher degrees of freedom:
- Data governance or access restriction:
- Runtime fallback used:
- Backend parity / cross-validation:

## 4. Decision

Decision: PASS / NOT PASS

Allowed claim:

- Causal:
- Descriptive:
- Exploratory only:

## 5. Next Action

If NOT PASS, route back to:

- Stage:
- Required fix:
- Owner:
- Evidence needed before re-audit:
