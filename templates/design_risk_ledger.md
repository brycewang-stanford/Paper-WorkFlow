# Design Risk Ledger

Project: <short name>
Review round: <k>
Last updated (Beijing): <YYYY-MM-DD HH:MM>
Reviewer: design-risk critic subagent

Purpose: make every identification threat, design choice, and reporting-risk
claim auditable before the Method Gate passes. This ledger complements
`03_analysis/design_register.md` and `03_analysis/method_gate.md`: the design
register states the intended design, the method gate checks required evidence,
and this ledger records whether remaining design risks cap or block claims.

## 1. Design Boundary

- Primary claim ID(s): C1 / C2 / ...
- Target estimand:
- Population, geography, and time window:
- Treatment or exposure version:
- Comparison group:
- Main identifying assumption:
- Strongest claim sought: causal / qualified_causal / descriptive / exploratory
- Strongest claim allowed after this review: causal / qualified_causal / descriptive / exploratory / no_claim

## 2. Threat Register

| Threat | Applies? | Why it matters here | Required diagnostic or refuter | Artifact path | Status | Claim Consequence |
|---|---:|---|---|---|---|---|
| Omitted variables / confounding | yes/no |  |  | 03_analysis/robustness/<artifact> | pending / pass / not_pass / not_applicable | causal / qualified_causal / descriptive / exploratory / no_claim |
| Reverse causality / simultaneity | yes/no |  |  | 03_analysis/robustness/<artifact> | pending / pass / not_pass / not_applicable |  |
| Selection into treatment | yes/no |  |  | 02_data/sample_audit.md | pending / pass / not_pass / not_applicable |  |
| Measurement error | yes/no |  |  | 03_analysis/robustness/<artifact> | pending / pass / not_pass / not_applicable |  |
| Spillover / interference / SUTVA | yes/no |  |  | 03_analysis/robustness/<artifact> | pending / pass / not_pass / not_applicable |  |
| Bad controls / post-treatment conditioning | yes/no |  |  | 03_analysis/design_register.md | pending / pass / not_pass / not_applicable |  |
| Functional form / specification search | yes/no |  |  | 03_analysis/robustness/spec_curve.* | pending / pass / not_pass / not_applicable |  |
| External validity / transportability | yes/no |  |  | 03_analysis/robustness/<artifact> | pending / pass / not_pass / not_applicable |  |
| Attrition / survivor selection | yes/no |  |  | 02_data/sample_audit.md | pending / pass / not_pass / not_applicable |  |
| Multiple testing / selective reporting | yes/no |  |  | 03_analysis/inference_report.md | pending / pass / not_pass / not_applicable |  |

## 3. Specification Search and Selective Reporting

- Pre-analysis plan or design memo: 01_proposal/pre_analysis_plan.md / none
- Primary outcome and primary specification locked before seeing results? yes / no / not_applicable
- Researcher degrees-of-freedom table: 03_analysis/researcher_dof.md / none
- Specification curve or multiverse artifact: 03_analysis/robustness/spec_curve.* / none
- Multiple-testing family and correction: 03_analysis/inference_report.md / none
- Null-result interpretation includes MDE when relevant? yes / no / not_applicable
- Any outcome, sample, or control-set switch after seeing results:

## 4. External Validity and Transport

- Local effect type: ATT / ATE / LATE / local RDD / CATE / descriptive contrast
- Units the estimate directly applies to:
- Units or settings the manuscript must not generalize to:
- Complier / treated / cutoff / donor-pool characterization:
- Reweighting, replication, or subgroup transport evidence:
- Required wording boundary for manuscript and cover letter:

## 5. Spillover, Interference, and Attrition

- Interference structure assumed: none / partial interference / network / geographic / market-level / unknown
- Exposure mapping or spillover diagnostic:
- Donut / buffer / neighbor-exclusion check:
- Attrition or panel-survival diagnostic:
- Lee bounds / IPW / selection correction if needed:
- Claim cap if these checks fail:

## 6. Blocking Threats

List only threats that block the Method Gate or cap the main claim below the
manuscript's current wording.

| Blocking threat | Affected claim | Required fix | Return stage | Owner |
|---|---|---|---:|---|
| <threat> | C1 | <diagnostic / rewrite / design change> | 1/2/3/5 | <owner> |

## 7. Gate Decision

Design risk status: pending / pass / not_pass

- Pass criteria:
  - Every applicable threat in the register is `pass` or has an explicit claim consequence.
  - `Blocking Threats` is empty.
  - Manuscript wording in `00_meta/evidence_ledger.md` is no stronger than this ledger allows.
- If `not_pass`, route back to:
  - Stage:
  - Required fix:
  - Evidence needed before re-audit:
