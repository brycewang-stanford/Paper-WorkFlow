# Final Report

Project: <short name>
Completed at (Beijing): <YYYY-MM-DD HH:MM>
Workspace: <paper_workspace/...>

## 1. Pipeline Summary

| Stage | Status | Key outputs | Red flags / fallback |
|---|---|---|---|
| 0. Intake & setup |  | 00_meta/workflow_state.json |  |
| 1. Topic & design |  | 01_proposal/proposal.md |  |
| 2. Data |  | 02_data/clean.parquet, 02_data/codebook.md, 02_data/sample_audit.md |  |
| 3. Identification & estimation |  | 03_analysis/design_register.md, 03_analysis/design_risk_ledger.md, 03_analysis/method_gate.md |  |
| 4. Tables & figures |  | 04_results/ |  |
| 5. Draft |  | 05_draft/main.tex |  |
| 6. Polish |  | 06_polish/main.tex |  |
| 7. Language & de-AI |  | 07_dehumanize/main.tex |  |
| 8. Review & revision |  | 08_review/response_letter.md |  |
| 9. Submission |  | 09_submission/ |  |

## 2. Gate Results

- Orchestration route: recorded / missing
- Stage passport: current / stale / missing
- Pipeline status: current / stale / missing
- Latest handoff: recorded / missing / not needed
- Method gate: PASS / NOT PASS
- Analysis backend: python-statspai / stata / r
- Sample / estimand audit: PASS / NOT PASS
- Design risk ledger: PASS / NOT PASS
- Draft quality gate: PASS / NOT PASS
- Replication pack: ready / not_ready
- Data governance: clear / restricted / blocked
- Evidence ledger: complete / incomplete
- Evidence governance: pass / not_pass
- Claim integrity audit: pass / pass_with_notes / not_pass
- Strongest allowed claim: causal / qualified_causal / descriptive / exploratory / no_claim

## 3. Deliverables

| Deliverable | Path | Ready? |
|---|---|---:|
| Proposal | 01_proposal/proposal.md | no |
| Entry routing | 00_meta/entry_routing.md | no |
| Stage passport | 00_meta/stage_passport.md | no |
| Pipeline status | 00_meta/pipeline_status.md | no |
| Latest handoff | 00_meta/handoff/ | no |
| Analysis backend report | 00_meta/analysis_backend.md | no |
| Backend parity report | 00_meta/backend_parity.json | no |
| Clean data and codebook | 02_data/clean.parquet, 02_data/codebook.md | no |
| Sample / estimand audit | 02_data/sample_audit.md | no |
| Design risk ledger | 03_analysis/design_risk_ledger.md | no |
| Main results | 03_analysis/results/main_results.json | no |
| Evidence ledger | 00_meta/evidence_ledger.md | no |
| Claim integrity audit | 00_meta/claim_integrity_audit.md | no |
| Tables and figures | 04_results/ | no |
| Manuscript | 07_dehumanize/main.tex | no |
| Review response | 08_review/response_letter.md | no |
| Submission package | 09_submission/ | no |
| Replication README | REPLICATION.md | no |

## 4. Reproduction Command

```bash
<command>
```

Last rebuild check:

## 5. Validation Evidence

Commands run:

| Command | Result | Evidence / notes |
|---|---|---|
| `python3 validate_skill.py` | PASS / FAIL / not in scope | <child gate output summary> |
| `python3 scripts/generate_rigor_report.py --check` | PASS / FAIL / not in scope | <RIGOR freshness output> |
| `git diff --check` | PASS / FAIL / not in scope | <whitespace/path hygiene output> |
| `make catalog` | PASS / FAIL / not in scope | <parent catalog refresh evidence, if child catalog-visible metadata changed> |
| `make validate` | PASS / FAIL / not in scope | <parent validation evidence, if parent sync is in scope> |
| `make check` | PASS / FAIL / not in scope | <parent end-to-end evidence, if parent sync is in scope> |

## 6. Change / Commit Ledger

| Commit / SHA | Files changed | Change summary |
|---|---|---|
| <no commit / short sha> | <repo-relative paths> | <what changed and why> |

## 7. Failures and Fixes

| Failures encountered | Fix / outcome | Follow-up |
|---|---|---|
| <command / gate / review finding> | <fix applied or reason deferred> | <remaining action or none> |

## 8. Remote / Parity Status

| Scope | Status | Evidence / notes |
|---|---|---|
| Child repo status | clean / dirty / committed / pushed / No push requested | <branch, HEAD, origin, or known dirty files> |
| Parent repo status | clean / dirty / not in scope | <gitlink/catalog state and validation evidence> |
| Remote / parity status | pushed / not pushed / No push requested | <remote SHA parity, ls-remote evidence, or explicit no-push note> |

## 9. Residual Risks

- Identification:
- Design risks / external validity:
- Sample / estimand alignment:
- Robustness:
- Evidence-to-claim alignment:
- Claim/citation/number integrity:
- Citation:
- Data access / IRB / DUA:
- Journal formatting:
- Handoff / continuation:

## 10. Next Actions

1. <action>
2. <action>
3. <action>
