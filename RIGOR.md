# RIGOR.md — gate-coverage report

**Rigor checkers selftest: PASSING — 39/39 green.**

Paper-WorkFlow's differentiator is that research rigor is *executable*, not advisory. Every load-bearing invariant — about a paper run, and about this skill package itself — is enforced by a script with a built-in selftest. This report runs each checker's selftest and records the verdict. A failure here is a non-zero exit, not a soft warning. Regenerate with `python3 scripts/generate_rigor_report.py`; verify freshness in CI with `--check`.

> Context: our two closest peers do not have this layer. K-Dense `scientific-agent-skills` ships only a *security* scanner; Orchestra `AI-Research-SKILLs` self-grades rigor in markdown. See [`RELATED-WORK.md`](RELATED-WORK.md) for the evidence.

The master gate `validate_skill.py` chains every leaf checker below (plus asset, template-contract, link, and notebook checks) into a single `python3 validate_skill.py` run maintainers must pass before shipping.

## Run-time gates — verify a paper run

| Checker | Result | Enforced invariant |
|---|:--:|---|
| [`scripts/check_workspace_gates.py`](scripts/check_workspace_gates.py) | ✅ pass | Method Gate / Draft Quality Gate / replication pack / claim-integrity / design-risk: a gate marked `pass` must have its evidence on disk, and ordering holds (quality gate never looser than the method gate). |
| [`scripts/check_method_gate_card.py`](scripts/check_method_gate_card.py) | ✅ pass | Method Gate design-card honesty: a passed Method Gate cannot have missing/failed design-card rows, hit hard flags, placeholder paths, or evidence claims stronger than the card permits. |
| [`scripts/check_runtime_fallbacks.py`](scripts/check_runtime_fallbacks.py) | ✅ pass | Runtime fallback honesty: missing tools, networks, MCP services, or statistical backends must be recorded in state decisions, stage logs, and backend reports, and blocked or non-parity fallbacks cannot pass Method Gate or replication readiness. |
| [`scripts/check_backend_capabilities.py`](scripts/check_backend_capabilities.py) | ✅ pass | Backend capability reports: Python/StatsPAI, Stata, R, and export stack availability must be recorded as structured status, missing dependencies, fallback backend, and probe timestamp before execution. |
| [`scripts/check_backend_parity.py`](scripts/check_backend_parity.py) | ✅ pass | Backend parity fixtures and workspace reports: fallback or secondary Python/StatsPAI, Stata, and R result bundles must agree on sample hash, estimator family, clustering, fixed effects, coefficients, standard errors, and diagnostics before parity claims can pass. |
| [`scripts/check_table_style.py`](scripts/check_table_style.py) | ✅ pass | Three-line table (三线表) export contract: exported .docx tables carry a heavy top rule, a light header rule and a heavy closing rule with no vertical or stray interior rules, borders are explicit rather than inherited from a Word table style, and the paired .tex uses booktabs instead of \hline / '|' column specs. |
| [`scripts/make_three_line_tables.py`](scripts/make_three_line_tables.py) | ✅ pass | Three-line table normaliser: rewriting a .docx table's borders in place produces exactly the heavy-top / light-header / heavy-bottom rule structure check_table_style.py demands, preserves cell content and the header-repeat flag, is idempotent, and never leaves a partially-rewritten document behind. |
| [`scripts/check_manuscript_numbers.py`](scripts/check_manuscript_numbers.py) | ✅ pass | Manuscript numeric anchoring and rewrite inertness: every coefficient, standard error and sample size asserted in the manuscript must trace to 03_analysis/results or 04_results at the precision it is printed, and the Stage 6->7 de-AIGC rewrite must not change a single number in either direction. Unanchored figures are waived only by an in-text, referee-readable `% pw-number-ok:` comment. |
| [`scripts/check_ai_disclosure.py`](scripts/check_ai_disclosure.py) | ✅ pass | AI-use disclosure and authorship integrity: an AI system can never be an author, AI-generated data or result images are fabrication, AI-written code and AI-screened literature cannot be shipped unverified, the rendered venue statement must cover every disclosed category, and the de-AIGC stage that removes the AI accent must not also remove the AI disclosure. |
| [`scripts/check_citation_integrity.py`](scripts/check_citation_integrity.py) | ✅ pass | Citation existence + temporal integrity: DOI resolution, retraction screening, citation-laundering, and look-ahead / vintage / sample-vs-claim-period leakage. |
| [`scripts/check_verification_log.py`](scripts/check_verification_log.py) | ✅ pass | The load-bearing methods-claim verification log exists and every claim it makes is backed by a recorded check. |
| [`scripts/smoke_workspace.py`](scripts/smoke_workspace.py) | ✅ pass | A minimal workspace initialises and every template contract holds (templates instantiate with the fields the gates later require). |
| [`scripts/check_demo_execution.py`](scripts/check_demo_execution.py) | ✅ pass | Bundled DiD demo execution: the notebook's code cells run in a temporary workspace, regenerate the table/figures, and preserve the core teaching estimates and staggered-adoption caution. |
| [`scripts/check_defense_deck.py`](scripts/check_defense_deck.py) | ✅ pass | Defence-deck generation: the Stage 9 答辩 PPT builds from a real workspace, workspace content reaches the slides, --duration actually scales the slide budget, and the mandatory closing sections (机制 / 结论与贡献 / 局限与展望) are never rationed away by a long findings list -- the findings are what get truncated, and the truncation is announced. |
| [`scripts/check_preregistration.py`](scripts/check_preregistration.py) | ✅ pass | Pre-registration lock: the primary specification is committed before estimation, and any main result not pre-registered is labelled exploratory (researcher-degrees-of-freedom guard). |
| [`scripts/check_review_scorecard.py`](scripts/check_review_scorecard.py) | ✅ pass | L2 review scorecard: all 7 dimensions scored, every finding carries a severity + verbatim evidence span + locator, a blocking finding caps its dimension <=4, and a declared PASS is consistent with the scores. |
| [`evals/check_replication_accuracy.py`](evals/check_replication_accuracy.py) | ✅ pass | Stage 3 output correctness: candidate estimates are scored against sourced gold coefficients on sign-correct, perfect-reproduction, and partial-or-better metrics; template cases cannot be scored as truth. |
| [`evals/check_quality_judge.py`](evals/check_quality_judge.py) | ✅ pass | Reproducible LLM-as-judge bookkeeping: the Draft Quality Gate verdict is recomputed from dimension scores, red flags, integrity status, and frozen calibration anchors. |

## Maintenance gates — verify this skill package

| Checker | Result | Enforced invariant |
|---|:--:|---|
| [`scripts/check_gate_integration.py`](scripts/check_gate_integration.py) | ✅ pass | End-to-end: a real workspace init flowed through real templates is accepted by the gate checkers as a coherent whole. |
| [`scripts/check_stage_scenario.py`](scripts/check_stage_scenario.py) | ✅ pass | Stage 0-9 golden-path scenario: a completed workspace must have per-stage logs, handoffs, key artifacts, final handoff recovery, a green workspace-gate card with table-result reconciliation, and a filled final delivery report. |
| [`scripts/check_stage_adversarial.py`](scripts/check_stage_adversarial.py) | ✅ pass | Adversarial Stage 0-9 scenarios: common corruptions of a completed workspace (missing artifacts, stale handoffs, broken reset coverage, unreconciled tables, non-final citations, and gate-order regressions) or unfilled final reports must be rejected. |
| [`scripts/check_design_gate_contract.py`](scripts/check_design_gate_contract.py) | ✅ pass | Design-gate-card contract: every contracted empirical design family has required artifacts, hard-fail conditions, allowed claim levels, behavioral guardrails, and a matching Method Gate template label. |
| [`scripts/check_method_specific_failures.py`](scripts/check_method_specific_failures.py) | ✅ pass | Method-specific failure fixtures: every contracted design family must have a failure fixture, and each fixture rejects missing or failed design-specific diagnostics before a Method Gate can pass. |
| [`scripts/check_state_template_paths.py`](scripts/check_state_template_paths.py) | ✅ pass | Workflow-state path contract: default artifact paths are safe workspace-relative paths whose parent directories exist in the init skeleton, and Stage 0 bootstrap artifacts exist after init. |
| [`scripts/check_reproducibility_scaffold.py`](scripts/check_reproducibility_scaffold.py) | ✅ pass | Replication scaffold: the run_all master script captures environment state, warns when no expected manifest exists, accepts matching outputs, and fails corrupted output manifests. |
| [`scripts/check_final_report_contract.py`](scripts/check_final_report_contract.py) | ✅ pass | Final-report contract: delivery handoffs must include validation commands, changed files/commits, failures and fixes, residual risks, and child/parent remote-parity status. |
| [`scripts/check_cross_references.py`](scripts/check_cross_references.py) | ✅ pass | Cross-reference contract: every internal link, named artifact, and script path referenced from SKILL.md and references actually resolves. |
| [`scripts/check_bilingual_docs.py`](scripts/check_bilingual_docs.py) | ✅ pass | Bilingual README parity: the Chinese and English user surfaces expose the same reference docs, script inventory, validation commands, and load-bearing workflow artifacts. |
| [`scripts/check_numeric_claims.py`](scripts/check_numeric_claims.py) | ✅ pass | Numeric-claims cross-doc parity: load-bearing counts (10 stages / 47 skills / 2 hard gates / 3 backends / the live rigor-badge gate count) appear consistently across README.md, README.en.md, SKILL.md, and RIGOR.md; a drift fails CI. |
| [`scripts/check_contract_matrix.py`](scripts/check_contract_matrix.py) | ✅ pass | Contract matrix: each quality theme has named owner files, validators, and docs, and high-leverage repo artifacts are covered by at least one maintained invariant. |
| [`scripts/pw.py`](scripts/pw.py) | ✅ pass | Stage -> gate map: every workspace-scoped run-time checker registered here is reachable from at least one pipeline stage (or is explicitly declared non-stage-scoped with a reason), the map's stage keys match the state template's Stage 0-9 spine and the checker's own precondition table, and Stage 9 never runs a weaker variant of a gate than an earlier stage did. |
| [`scripts/check_rigor_registry.py`](scripts/check_rigor_registry.py) | ✅ pass | RIGOR registry completeness: every checker discovered under scripts/ or evals/ must be registered in this report, and registry drift is a blocking maintenance failure. |
| [`scripts/check_monthly_worklog.py`](scripts/check_monthly_worklog.py) | ✅ pass | Long-horizon maintenance evidence: the month-long worklog records the goal window, baseline PASS evidence, week plan, packet-level validation, and anti-cheat guards that prevent premature closure. |
| [`scripts/check_skillopt_packet.py`](scripts/check_skillopt_packet.py) | ✅ pass | SkillOpt improvement packets: >=3 train + >=2 held-out rollouts, a bounded edit budget, and accept requires a score gain + regression pass. |
| [`scripts/check_compactness.py`](scripts/check_compactness.py) | ✅ pass | Orphan and duplication detection: every references/*.md must be reachable from SKILL.md or another reference, and cross-file near-duplicate paragraphs are counted so 'the corpus grew' can be answered as accretion vs new material rather than guessed at. The ratchet is advisory and never blocks a maintenance edit. |
| [`scripts/check_cn_claim_audit.py`](scripts/check_cn_claim_audit.py) | ✅ pass | CN-claim audit gate: _verification_log/cn-data-claims.md must exist with >=10 entries and both China-context reference files must carry an audit-status banner; --update-banners rewrites the banner from the live ledger. |
| [`scripts/check_chaos_coverage.py`](scripts/check_chaos_coverage.py) | ✅ pass | Chaos-coverage pairing: every documented orchestrator failure mode in references/orchestration-and-handoff.md must have a matching evals/chaos/<scenario>.md with a real recovery path. The script is advisory by default; --strict is for new-failure-mode PRs. |
| [`evals/check_complexity_budget.py`](evals/check_complexity_budget.py) | ✅ pass | Complexity ratchet: the always-loaded SKILL.md and the reference-file count cannot grow past the recorded ceiling without a justified bump. |
| [`evals/score_skill.py`](evals/score_skill.py) | ✅ pass | Held-out scoring-harness invariants for the SkillOpt selection gate (baseline vs candidate scored on the same rubric). |

## How to reproduce

```bash
python3 scripts/generate_rigor_report.py        # regenerate this file
python3 scripts/generate_rigor_report.py --check # CI: fail if stale
```

_Generated 2026-08-27 by `scripts/generate_rigor_report.py`. The body is deterministic apart from this line.
