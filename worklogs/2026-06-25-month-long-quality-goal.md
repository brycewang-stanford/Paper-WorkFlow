# Worklog — Month-long repo quality goal

Start: 2026-06-25 18:47 PDT
Goal window: do not close before 2026-07-26.
Trigger: 用户要求设定一个一个月长的工作目标，整体提升整个 repo 的水平，不能几分钟内草草完成。

## Goal contract

Raise `Paper-WorkFlow` from a hardened skill package into a durable,
research-grade empirical-paper workflow platform. The run is complete only when
there is evidence of substantive improvement across at least four themes:

- workflow contract and workspace state
- runtime validators, evals, and rigor reporting
- reproducibility/example assets
- bilingual user-facing docs
- maintainer governance and release readiness

This is not a copyediting pass. A valid improvement must either tighten an
executable invariant, reduce ambiguity in a workflow handoff, improve
reproducibility evidence, or make maintenance safer for future agents.

## Baseline audit

Current branch: `feat/competitive-rigor-layer`.
Child repo status at start: clean and tracking `origin/feat/competitive-rigor-layer`.
Parent repo status at start: clean `main` tracking `origin/main`.

Baseline commands:

- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md` current and 13/13 checker selftests green
- `git diff --check` -> PASS
- parent `git status --short --branch` -> clean `main...origin/main`

Observed current strengths:

- Stage 0-9 contract exists in `SKILL.md`, `README.md`, and the schema-v10 state template.
- `validate_skill.py` is the fast master gate and already chains asset, template, cross-reference, workspace, complexity, and rigor selftests.
- `RIGOR.md` exposes 13 green runtime/maintenance checkers.
- Complexity ratchet holds the always-loaded `SKILL.md` at 30,935 bytes with 1,065 bytes of headroom below the 32 KB target.
- Parent-child validation path is known: child first, then parent `make catalog`, `make validate`, and `make check` when parent sync is in scope.

Initial risks / gaps to audit before patching:

- The package now has many gate artifacts; future work should test whether a real initialized workspace can move through a minimal end-to-end happy path without manual file invention.
- Bilingual documentation may drift as executable gates grow, especially when references and templates change faster than README summaries.
- `templates/run_all.sh` and demo/reproducibility assets should be checked against the current schema-v10 contract, not assumed correct from earlier hardening.
- Maintainer governance exists, but a month-long run needs recurring evidence checkpoints so later agents can tell which weekly packet is complete.
- Parent catalog sync must not be mixed into child changes until the child repo is stable and the parent checkout is clean.

## Month plan

### Week 0 / setup and measurement

- Create this progress artifact.
- Record baseline gate results and parent/child cleanliness.
- Build an audit matrix mapping `SKILL.md`, `assets/workflow_state.template.json`, `templates/`, `references/`, `scripts/`, and `evals/` to the invariants each one owns.
- Identify the first packet that can improve quality mechanically without broad churn.

### Week 1 / workflow-state contract hardening

- Audit schema-v10 state against every template and checker.
- Add or tighten targeted checks only where there is a real drift path.
- Verify `assets/init_workspace.sh` still creates every path that downstream gate checkers expect.

### Week 2 / reproducibility and example evidence

- Exercise the demo and replication-facing assets in a temp workspace.
- Check whether `templates/run_all.sh`, `templates/REPLICATION.md`, `templates/DAS.md`, and `did_demo.ipynb` still describe a coherent reproducibility story.
- Add focused fixtures or smoke checks if an executable gap is found.

### Week 3 / docs and bilingual consistency

- Align `README.md`, `README.en.md`, `SKILL.md`, and high-traffic references after any contract changes.
- Keep `SKILL.md` under the complexity ratchet; prefer references/templates/scripts for detail.
- Preserve backend discoverability for Python/StatsPAI, Stata, and R/fixest.

### Week 4 / maintainer governance and release readiness

- Re-run full child gates and, if needed, parent catalog validation.
- Check `RIGOR.md`, complexity baseline, cross-reference contract, and worklog completeness.
- Produce a final handoff with changed files, verification evidence, residual risks, and publish/parity status.

## Running evidence log

Append each packet here with:

- date and packet name
- files changed
- invariant strengthened
- commands run and results
- failures and fixes
- remaining risk

### 2026-06-25 Packet 0A — Stage 0 data-governance placeholder

Files changed:

- `assets/init_workspace.sh`
- `validate_skill.py`
- `references/workspace-and-state.md`
- `README.md`
- `README.en.md`

Invariant strengthened:

- New workspaces now start with `00_meta/data_governance.md`, matching
  `references/data-governance.md` guidance that unattended Stage 0 should create
  a governance placeholder with unknowns explicitly marked for later review.
- `validate_skill.py` now fails if `init_workspace.sh` does not create that
  placeholder, so the expectation is mechanical rather than advisory.

Why this is bounded:

- The patch does not pre-create later-stage proof artifacts such as
  `REPLICATION.md`, `09_submission/DAS.md`, or `run_all.sh`.
- Workflow state remains `pending` / `not_ready`; the new file is a governance
  register, not evidence that data policy review has passed.

Validation to run:

- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md` current and 13/13 checker selftests green
- `git diff --check` -> PASS

Failure / fix:

- The first patch attempt missed the exact `intake.md` context in
  `assets/init_workspace.sh`; the patch was split into smaller exact hunks.

Remaining risk:

- This only closes the Stage 0 governance placeholder gap. Later packets should
  still exercise a real temp workspace through data, method-gate, and
  reproducibility handoff paths.

### 2026-06-25 Packet 0B — Contract matrix maintenance gate

Files changed:

- `evals/contract_matrix.json`
- `scripts/check_contract_matrix.py`
- `scripts/generate_rigor_report.py`
- `validate_skill.py`
- `RIGOR.md`

Invariant strengthened:

- The month-goal themes are now explicit and machine-checkable:
  `workflow_contract_state`, `runtime_validators_evals`,
  `reproducibility_examples`, `bilingual_user_docs`, and
  `maintainer_governance_release`.
- The matrix maps each theme to owner files, executable validators, and docs.
  High-leverage artifacts such as `SKILL.md`, both READMEs,
  `assets/init_workspace.sh`, the state template, replication templates,
  `did_demo.ipynb`, `RIGOR.md`, and this worklog must be covered by at least
  one maintained invariant.
- `scripts/check_contract_matrix.py` has a synthetic selftest and a live matrix
  check; `validate_skill.py` now runs both.
- `scripts/generate_rigor_report.py` now registers the contract-matrix checker,
  so `RIGOR.md` reports 14/14 green checker selftests instead of 13/13.

Validation:

- `python3 scripts/check_contract_matrix.py --selftest` -> PASS
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 58 covered paths
- `python3 validate_skill.py` -> PASS; cross-reference linter confirms all 9
  `scripts/check_*.py` files are wired into the master gate
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 14/14 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- The matrix proves coverage ownership, not empirical-paper correctness. Week 1
  should use it to choose the next schema/template drift check; Week 2 should
  still exercise reproducibility assets in a temp workspace.

### 2026-06-25 Packet 0C — Reproducibility scaffold gate

Files changed:

- `scripts/check_reproducibility_scaffold.py`
- `scripts/generate_rigor_report.py`
- `validate_skill.py`
- `evals/contract_matrix.json`
- `RIGOR.md`

Invariant strengthened:

- `templates/run_all.sh` and `templates/check_outputs.py` are now tested as a
  real pair, not only syntax-checked.
- The new checker copies both templates into a temporary replication package and
  verifies three paths: no manifest logs an explicit unverified-output warning;
  a matching manifest succeeds; a corrupted manifest fails through the
  output-integrity branch.
- `validate_skill.py` runs the new checker selftest and live scaffold check.
- `scripts/generate_rigor_report.py` registers the checker, so `RIGOR.md`
  reports 15/15 green checker selftests.
- `evals/contract_matrix.json` ties the checker to the
  `reproducibility_examples` theme; the matrix now covers 59 repo paths.

Validation:

- `python3 scripts/check_reproducibility_scaffold.py --selftest` -> PASS
- `python3 scripts/check_reproducibility_scaffold.py` -> PASS
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 59 covered paths
- `python3 validate_skill.py` -> PASS; cross-reference linter confirms all 10
  `scripts/check_*.py` files are wired into the master gate
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 15/15 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- This proves the reusable replication scaffold behavior, not that
  `did_demo.ipynb` or a real empirical project rebuilds end to end. A later
  packet should execute the demo notebook in a temp copy or add a bounded demo
  rebuild check.

### 2026-06-25 Packet 0D — DiD demo execution gate

Files changed:

- `scripts/check_demo_execution.py`
- `scripts/generate_rigor_report.py`
- `validate_skill.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`

Invariant strengthened:

- The bundled `did_demo.ipynb` is now executed in a temporary workspace without
  requiring `jupyter-nbconvert`, `nbformat`, or `nbclient`.
- The checker verifies that the notebook regenerates
  `assets/fig_raw_trends.png`, `assets/fig_event_study.png`, and
  `assets/did_table.tex` away from the repo.
- It also checks the teaching invariants: `TRUE_ATT = 2.0`, 2x2 DiD and TWFE
  estimates remain near `1.953`, the pre-trend joint test remains non-rejecting,
  and the staggered-adoption TWFE bias warning remains visible.
- `validate_skill.py` now runs the demo execution checker, not just the older
  notebook structure check.
- `scripts/generate_rigor_report.py` registers the checker, so `RIGOR.md`
  reports 16/16 green checker selftests.
- `evals/contract_matrix.json` ties the checker to the
  `reproducibility_examples` theme; the matrix now covers 60 repo paths.

Validation:

- `python3 scripts/check_demo_execution.py --selftest` -> PASS
- `python3 scripts/check_demo_execution.py` -> PASS
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 60 covered paths
- `python3 validate_skill.py` -> PASS; cross-reference linter confirms all 11
  `scripts/check_*.py` files are wired into the master gate
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 16/16 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- The demo is synthetic by design. It now proves the teaching asset executes and
  regenerates its artifacts, but it is not a substitute for a real paper
  workspace run through Stage 0-9.

### 2026-06-25 Packet 0E — Bilingual checker inventory alignment

Files changed:

- `README.md`
- `README.en.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- The repository layout sections in both READMEs now reflect the current
  validation surface instead of the older three-script view.
- The script inventory now names the demo execution checker, citation and
  preregistration gates, cross-reference and contract-matrix checks,
  reproducibility scaffold check, verification-log check, and rigor-report
  generator.
- The READMEs now surface `RIGOR.md`, `RELATED-WORK.md`, and the `evals/`
  maintenance/evaluation layer, including `contract_matrix.json`.
- The Chinese README avoids a hard-coded checker count; `RIGOR.md` remains the
  authoritative count source.

Validation:

- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 16/16 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- The READMEs are now aligned with the current checker inventory, but future
  checker additions should still update the layout or keep details behind
  `RIGOR.md` / `evals/contract_matrix.json` to avoid another stale tree.

### 2026-06-25 Packet 1A — Workflow-state path contract

Files changed:

- `scripts/check_state_template_paths.py`
- `scripts/generate_rigor_report.py`
- `validate_skill.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`

Invariant strengthened:

- `workflow_state.template.json` path-like defaults are now checked against the
  directories created by `assets/init_workspace.sh`.
- The checker runs the real init script in a temp workspace and verifies Stage 0
  bootstrap files exist and are non-empty, including route/passport/status,
  handoff prompt/template, analysis backend, evidence ledger, citation/claim
  integrity logs, data governance, and design-risk ledger.
- Stage-produced paths such as `REPLICATION.md`, `03_analysis/method_gate.md`,
  and `09_submission/DAS.md` may remain absent at setup time, but their parent
  directories must exist in the init skeleton.
- `validate_skill.py` now runs the new checker selftest and live path check.
- `scripts/generate_rigor_report.py` registers the checker, so `RIGOR.md`
  reports 17/17 green checker selftests.
- `evals/contract_matrix.json` ties the checker to the
  `workflow_contract_state` theme; the matrix now covers 61 repo paths.

Validation:

- `python3 scripts/check_state_template_paths.py --selftest` -> PASS
- `python3 scripts/check_state_template_paths.py` -> PASS, 16 state path
  defaults, 13 bootstrap files, 18 init skeleton dirs
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 61 covered paths
- `python3 validate_skill.py` -> PASS; cross-reference linter confirms all 12
  `scripts/check_*.py` files are wired into the master gate
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 17/17 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- This closes state-template/default-path drift. It does not prove a real paper
  project completes Stage 0-9; later packets still need real workspace-level
  scenario coverage or staged fixtures.

### 2026-06-25 Packet 1B — Checker ownership coverage

Files changed:

- `scripts/check_contract_matrix.py`
- `evals/contract_matrix.json`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- `scripts/check_contract_matrix.py` now auto-discovers every
  `scripts/check_*.py` and `evals/check_*.py` file and fails if any checker is
  not claimed by at least one quality contract.
- The matrix now explicitly covers the previously unclaimed
  `scripts/check_preregistration.py`, `scripts/check_verification_log.py`, and
  `evals/check_quality_judge.py`.
- This prevents future additions from being wired into `validate_skill.py` /
  `RIGOR.md` while remaining ownerless in the month-goal contract map.

Validation:

- `python3 scripts/check_contract_matrix.py --selftest` -> PASS
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 64 covered paths, 15 discovered checkers covered
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 17/17 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- Checker ownership is now enforced, but the semantic quality of each invariant
  description still depends on maintainer judgment. Future packets should prefer
  adding scenario fixtures over only expanding the matrix.

### 2026-06-25 Packet 1C — Monthly worklog gate

Files changed:

- `scripts/check_monthly_worklog.py`
- `validate_skill.py`
- `scripts/generate_rigor_report.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- The month-long goal evidence is now mechanically checked instead of relying
  on the worklog as informal prose.
- `scripts/check_monthly_worklog.py` verifies the no-earlier-than
  `2026-07-26` goal window, baseline PASS evidence, Week 0-4 plan headings,
  packet-level files/invariant/validation/risk sections, PASS evidence, and
  anti-cheat guardrails.
- `validate_skill.py` runs the new checker selftest and live worklog check.
- `scripts/generate_rigor_report.py` registers the checker, so `RIGOR.md`
  reports 18/18 green checker selftests.
- `evals/contract_matrix.json` ties the checker to the
  `maintainer_governance_release` theme; the matrix now covers 65 repo paths
  and 16 discovered checkers.

Validation:

- `python3 -m py_compile scripts/check_monthly_worklog.py` -> PASS
- `python3 scripts/check_monthly_worklog.py --selftest` -> PASS
- `python3 scripts/check_monthly_worklog.py` -> PASS, 8 packet sections after
  this packet was appended
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 65
  covered paths, 16 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  18/18 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 18/18 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- The worklog gate enforces structure and local evidence, not calendar
  elapsed time. The active goal must still stay open until at least
  2026-07-26 and continue accumulating substantive packets across the month.

### 2026-06-25 Packet 1D — Stage 0-9 golden-path scenario gate

Files changed:

- `evals/stage_scenario_contract.json`
- `scripts/check_stage_scenario.py`
- `validate_skill.py`
- `scripts/generate_rigor_report.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- The repo now has a machine-readable Stage 0-9 scenario contract instead of
  proving only isolated init/template/gate fragments.
- `evals/stage_scenario_contract.json` maps every schema-v10 stage key to a
  required stage log, handoff card, and key artifacts.
- `scripts/check_stage_scenario.py` verifies the contract matches
  `workflow_state.template.json`, builds a temporary complete workspace with 10
  done stages and 32 key artifacts, checks logs/handoffs/artifact paths, and
  runs `scripts/check_workspace_gates.py --json --reconcile` on the final state.
- The checker selftest corrupts the scenario contract, removes a stage artifact,
  points `latest_handoff` at the wrong card, and strips a stage log's artifact
  evidence to prove those failures are caught.
- `validate_skill.py` now runs the checker selftest and live scenario; `RIGOR.md`
  reports 19/19 green checker selftests.
- `evals/contract_matrix.json` ties the scenario contract to the
  `workflow_contract_state` theme; the matrix now covers 67 repo paths and 17
  discovered checkers.

Validation:

- `python3 -m py_compile scripts/check_stage_scenario.py` -> PASS
- `python3 scripts/check_stage_scenario.py --selftest` -> PASS
- `python3 scripts/check_stage_scenario.py` -> PASS, 10 stages, 32 stage
  artifacts, 13 gate OK checks
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 67
  covered paths, 17 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  19/19 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 19/19 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- The scenario is still a synthetic golden path. It proves the Stage 0-9
  workspace contract can be represented and gate-checked coherently, but later
  packets should add held-out or adversarial workspace scenarios rather than
  relying only on the happy path.

### 2026-06-25 Packet 1E — Adversarial Stage 0-9 scenario cases

Files changed:

- `evals/stage_adversarial_cases.json`
- `scripts/check_stage_adversarial.py`
- `validate_skill.py`
- `scripts/generate_rigor_report.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- The Stage 0-9 scenario layer now has explicit negative controls instead of
  only proving the golden path.
- `evals/stage_adversarial_cases.json` defines seven common corruptions:
  missing Stage 3 results, stale `latest_handoff`, missing reset-boundary
  coverage, stage logs that omit required artifacts, table/result
  unreconciled numbers, non-final citation status, and a Draft Quality Gate
  remaining `pass` after Method Gate is downgraded.
- `scripts/check_stage_adversarial.py` builds a fresh golden-path workspace for
  each case, applies exactly one mutation, and requires the scenario checker to
  return the expected error fragment.
- The selftest validates the live manifest, runs all adversarial cases, rejects
  unknown mutation types, and proves a wrong expected-error fragment fails.
- `validate_skill.py` now runs the adversarial checker selftest and live cases;
  `RIGOR.md` reports 20/20 green checker selftests.
- `evals/contract_matrix.json` ties the adversarial cases to the
  `workflow_contract_state` theme; the matrix now covers 69 repo paths and 18
  discovered checkers.

Validation:

- `python3 -m py_compile scripts/check_stage_adversarial.py` -> PASS
- `python3 scripts/check_stage_adversarial.py --selftest` -> PASS
- `python3 scripts/check_stage_adversarial.py` -> PASS, 7 cases caught:
  missing Stage 3 results, stale latest handoff, missing reset boundary, stage
  log missing artifact, unreconciled table/results, citation not final-clean,
  and quality gate looser than method gate
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 69
  covered paths, 18 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  20/20 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 20/20 checker selftests green
- `git diff --check` -> PASS

Failure / fix:

- The first `table_results_unreconciled` mutation changed only
  `04_results/table_main.tex`, but `04_results/figure_event_study.md` still
  contained the same `0.123` coefficient, so the reconcile heuristic correctly
  stayed green.
- The mutation was changed to corrupt `03_analysis/results/main_results.json`
  instead; then the exhibits no longer reconciled to the source results and the
  adversarial case failed as intended.

Remaining risk:

- These cases are synthetic single-fault corruptions. Later packets should add
  held-out multi-fault workspace cases or method-specific adversarial fixtures
  so the gate layer is tested against messier empirical-project failures.

### 2026-06-25 Packet 1F — Design-gate-card contract

Files changed:

- `evals/design_gate_contract.json`
- `scripts/check_design_gate_contract.py`
- `templates/method_gate.md`
- `validate_skill.py`
- `scripts/generate_rigor_report.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- The reviewer-facing design cards are now mechanically checked instead of
  living only as prose in `references/design-gate-cards.md`.
- `evals/design_gate_contract.json` declares nine design families:
  DiD/Event Study, IV/2SLS, RDD/Kink, SC/SDID, Panel FE/HDFE, DML/HTE,
  DAG/refutation, Prediction/Text/Embeddings, and Time Series/VAR.
- `scripts/check_design_gate_contract.py` verifies each design-card section
  exists, has enough required-artifact rows, contains the contracted artifact
  labels, includes a `Hard fail` block, lists the required claim-strength levels,
  and has a matching label in `templates/method_gate.md`.
- The checker also requires the cross-design behavioral guardrails `G1`-`G10`
  and method-gate synchronization markers for
  `workflow_state.json.method_gate.required_artifacts`,
  `workflow_state.json.method_gate.missing_artifacts`, and
  `workflow_state.json.evidence_governance.claim_strength`.
- `templates/method_gate.md` now lists `Time Series-VAR` in `Design card used`,
  matching the newer Time Series / VAR design card in
  `references/design-gate-cards.md`.
- `validate_skill.py` now runs the design-gate checker selftest and live file
  check; `RIGOR.md` reports 21/21 green checker selftests.
- `evals/contract_matrix.json` ties the design-gate contract to the
  `runtime_validators_evals` theme; the matrix now covers 71 repo paths and 19
  discovered checkers.

Validation:

- `python3 -m py_compile scripts/check_design_gate_contract.py` -> PASS
- `python3 scripts/check_design_gate_contract.py --selftest` -> PASS
- `python3 scripts/check_design_gate_contract.py` -> PASS, 9 design cards and
  10 behavioral guardrails
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 71
  covered paths, 19 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  21/21 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 21/21 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- The design-card checker proves coverage and method-gate synchronization, not
  real empirical sufficiency for a specific paper. Later packets can add
  method-specific workspace fixtures, starting with one design family such as
  IV weak-instrument or RDD manipulation failure.

### 2026-06-25 Packet 1G — Runtime Method Gate card parser

Files changed:

- `scripts/check_method_gate_card.py`
- `validate_skill.py`
- `scripts/generate_rigor_report.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- A paper workspace can no longer rely only on `workflow_state.json` to claim
  the Method Gate passed while `03_analysis/method_gate.md` itself records a
  contradictory Design Gate Card.
- `scripts/check_method_gate_card.py` parses the workspace's
  `03_analysis/method_gate.md` Design Gate Card table, Hard Flags section,
  Decision line, and strongest-allowed-claim line.
- When `workflow_state.json.method_gate.status=pass`, the checker fails if a
  card row is still a placeholder, `Present?` or `Pass?` is negative, a card path
  is missing/non-concrete, the path is absent from
  `workflow_state.json.method_gate.required_artifacts`, a hard flag is `hit` or
  blocking, or `evidence_governance.claim_strength` exceeds the card's allowed
  claim level.
- The selftest covers a good Method Gate, missing/failed card rows, hard-flag
  hits, overclaiming, missing state `required_artifacts`, placeholder rows, and
  a non-passing Method Gate that is allowed to remain incomplete.
- `validate_skill.py` now runs the Method Gate card checker selftest; `RIGOR.md`
  reports 22/22 green checker selftests.
- `evals/contract_matrix.json` ties the checker to the
  `runtime_validators_evals` theme; the matrix now covers 72 repo paths and 20
  discovered checkers.

Validation:

- `python3 -m py_compile scripts/check_method_gate_card.py` -> PASS
- `python3 scripts/check_method_gate_card.py --selftest` -> PASS
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 72
  covered paths, 20 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  22/22 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 22/22 checker selftests green
- `git diff --check` -> PASS

Remaining risk:

- The checker validates the Method Gate card format and state/card consistency.
  It still does not judge whether an econometric diagnostic is substantively
  convincing; later method-specific fixtures should encode examples such as
  weak-IV robust inference or RDD manipulation failure.

### 2026-06-25 Packet 1H — Bilingual README parity gate

Files changed:

- `scripts/check_bilingual_docs.py`
- `validate_skill.py`
- `scripts/generate_rigor_report.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- The Chinese and English README surfaces can no longer drift silently on the
  operational contract exposed to users.
- `scripts/check_bilingual_docs.py` enforces that both READMEs link to each
  other, expose the same `references/*.md` set, list the same repository-layout
  script inventory, and contain the same load-bearing workflow markers,
  validation commands, parent publication commands, gate artifacts, and eval
  fixtures.
- The selftest covers a passing bilingual fixture, reference-link drift,
  script-tree drift, missing validation markers, and missing counterpart links.
- `validate_skill.py` now runs the checker selftest and the real README parity
  check; `RIGOR.md` reports 23/23 green checker selftests.
- `evals/contract_matrix.json` ties the checker to the
  `bilingual_user_docs` theme; the matrix now covers 73 repo paths and 21
  discovered checkers.

Validation:

- `python3 -m py_compile scripts/check_bilingual_docs.py validate_skill.py scripts/generate_rigor_report.py` -> PASS
- `python3 scripts/check_bilingual_docs.py --selftest` -> PASS
- `python3 scripts/check_bilingual_docs.py` -> PASS, 24 reference links, 20
  script-tree items, 33 shared markers
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 73
  covered paths, 21 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  23/23 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 23/23 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 13 packets
- `git diff --check` -> PASS

Remaining risk:

- This proves the two READMEs expose the same operating contract, reference
  links, scripts, and release commands. It does not prove paragraph-level
  translation quality, so future substantive copy changes should still be
  reviewed by a fluent human before publication.

### 2026-06-25 Packet 1I — Final report delivery-evidence contract

Files changed:

- `templates/FINAL_REPORT.md`
- `scripts/check_final_report_contract.py`
- `validate_skill.py`
- `scripts/generate_rigor_report.py`
- `scripts/check_bilingual_docs.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- A completed paper workflow can no longer treat `FINAL_REPORT.md` as a loose
  narrative summary. The template now requires validation evidence, a
  change/commit ledger, failures and fixes, and child/parent remote-parity
  status in addition to pipeline summary, gate results, deliverables,
  reproduction command, residual risks, and next actions.
- `scripts/check_final_report_contract.py` validates the template structure,
  required markers, validation/release commands, command-result-evidence table,
  commit/file/summary table, failure/fix table, and remote/parity table.
- The checker also supports `--filled` for real workspaces, where it rejects
  angle-bracket placeholders and unresolved choice lists in a completed report.
- `validate_skill.py` now runs the checker selftest and template check;
  `RIGOR.md` reports 24/24 green checker selftests.
- `evals/contract_matrix.json` ties the checker and template to the
  `maintainer_governance_release` theme; the matrix now covers 75 repo paths
  and 22 discovered checkers.

Validation:

- `python3 -m py_compile scripts/check_final_report_contract.py scripts/check_bilingual_docs.py validate_skill.py scripts/generate_rigor_report.py` -> PASS
- `python3 scripts/check_final_report_contract.py --selftest` -> PASS
- `python3 scripts/check_final_report_contract.py` -> PASS, 11 headings, 13
  markers, 6 validation/release commands
- `python3 scripts/check_bilingual_docs.py` -> PASS, 24 reference links, 21
  script-tree items, 34 shared markers
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 75
  covered paths, 22 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  24/24 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 24/24 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 14 packets
- `git diff --check` -> PASS

Remaining risk:

- The checker proves the final report contains the right evidence slots and can
  reject an unfilled workspace report. It does not prove the future evidence is
  true; maintainers still need to paste exact command output, commit SHAs, and
  remote parity hashes when a real workflow or publication handoff completes.

### 2026-06-25 Packet 1J — Stage 0-9 delivery packet scenario

Files changed:

- `scripts/check_stage_scenario.py`
- `scripts/check_stage_adversarial.py`
- `evals/stage_scenario_contract.json`
- `evals/stage_adversarial_cases.json`
- `scripts/generate_rigor_report.py`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- The Stage 0-9 golden-path fixture no longer treats `FINAL_REPORT.md` as a
  mere existing file. It now writes a filled final delivery report and validates
  it with `scripts/check_final_report_contract.py --filled`.
- `evals/stage_scenario_contract.json` now declares final delivery checks for
  both `check_workspace_gates --json --reconcile` and
  `check_final_report_contract --filled`.
- `scripts/check_stage_scenario.py` fails a completed workspace if the filled
  final report contains template placeholders or unresolved delivery fields.
- `evals/stage_adversarial_cases.json` adds a final-report placeholder
  corruption; `scripts/check_stage_adversarial.py` now proves that this failure
  is caught alongside missing artifacts, stale handoffs, broken reset coverage,
  unreconciled tables, non-final citations, and gate-order regressions.

Validation:

- `python3 -m py_compile scripts/check_stage_scenario.py scripts/check_stage_adversarial.py` -> PASS
- `python3 scripts/check_stage_scenario.py --selftest` -> PASS
- `python3 scripts/check_stage_scenario.py` -> PASS, 10 stages, 32 stage
  artifacts, 13 gate OK checks, 1 delivery check
- `python3 scripts/check_stage_adversarial.py --selftest` -> PASS
- `python3 scripts/check_stage_adversarial.py` -> PASS, 8/8 adversarial cases
  caught, including `final_report_unfilled_placeholder`
- `python3 scripts/check_bilingual_docs.py` -> PASS
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 75
  covered paths, 22 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  24/24 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 24/24 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 15 packets
- `git diff --check` -> PASS

Remaining risk:

- The delivery packet scenario proves a completed fixture cannot ship an
  unfilled final report. It remains synthetic; future packets should add
  method-specific completed workspaces such as weak-IV and RDD manipulation
  failures so the final handoff is tested against design-specific evidence.

### 2026-06-25 Packet 1K — IV/RDD method-specific failure fixtures

Files changed:

- `evals/method_failure_cases.json`
- `scripts/check_method_specific_failures.py`
- `validate_skill.py`
- `scripts/generate_rigor_report.py`
- `scripts/check_bilingual_docs.py`
- `evals/contract_matrix.json`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- Method Gate validation now includes method-specific held-out failures rather
  than only generic card consistency.
- `evals/method_failure_cases.json` defines two design-specific corruptions
  tied to `evals/design_gate_contract.json`: IV without weak-IV robust
  inference and RDD with a failed density/manipulation test.
- `scripts/check_method_specific_failures.py` builds good and bad workspace
  fixtures for each case, verifies the good fixture passes
  `check_method_gate_card.validate_workspace`, then verifies the bad fixture is
  rejected with the expected method-specific error.
- `validate_skill.py` now runs the checker selftest and live cases; `RIGOR.md`
  reports 25/25 green checker selftests.
- `evals/contract_matrix.json` ties the manifest and checker to the
  `runtime_validators_evals` theme; the matrix now covers 77 repo paths and 23
  discovered checkers.

Validation:

- `python3 -m py_compile scripts/check_method_specific_failures.py scripts/check_bilingual_docs.py validate_skill.py scripts/generate_rigor_report.py` -> PASS
- `python3 scripts/check_method_specific_failures.py --selftest` -> PASS
- `python3 scripts/check_method_specific_failures.py` -> PASS, 2/2 cases
  caught: `iv_weak_instrument_no_robust_inference` and
  `rdd_density_manipulation_hit`
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 77
  covered paths, 23 discovered checkers covered
- `python3 scripts/check_bilingual_docs.py` -> PASS, 24 reference links, 22
  script-tree items, 36 shared markers
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  25/25 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 25/25 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 16 packets
- `git diff --check` -> PASS

Remaining risk:

- The first method-specific fixtures cover IV and RDD only. Later packets should
  add additional families from `design_gate_contract.json`, especially
  staggered DiD negative-weight/pathology cases, synthetic-control donor-pool
  failures, and DML overlap/cross-fitting failures.

### 2026-06-25 Packet 1L — Expanded method-specific failure coverage

Files changed:

- `evals/method_failure_cases.json`
- `scripts/generate_rigor_report.py`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- Method-specific failure fixtures now cover five design families instead of
  only IV and RDD.
- `evals/method_failure_cases.json` adds three additional corruptions:
  staggered DiD without a modern staggered estimator, synthetic control/SDID
  with failed pre-fit fit, and DML/HTE with failed overlap or propensity
  support.
- The existing `scripts/check_method_specific_failures.py` proves each good
  fixture passes and each bad fixture is rejected by
  `check_method_gate_card.validate_workspace` with the expected
  design-specific error.
- `RIGOR.md` and the bilingual README now describe the checker as covering
  DiD/IV/RDD/SC/DML method-specific failures.

Validation:

- `python3 scripts/check_method_specific_failures.py --selftest` -> PASS
- `python3 scripts/check_method_specific_failures.py` -> PASS, 5/5 cases
  caught: `did_staggered_without_modern_estimator`,
  `iv_weak_instrument_no_robust_inference`, `rdd_density_manipulation_hit`,
  `synthetic_control_bad_prefit`, and `dml_overlap_support_failed`
- `python3 scripts/check_bilingual_docs.py` -> PASS, 24 reference links, 22
  script-tree items, 36 shared markers
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 77
  covered paths, 23 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  25/25 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 25/25 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 17 packets
- `git diff --check` -> PASS

Remaining risk:

- Five core causal-design families now have failure fixtures, but Panel FE,
  DAG/refuter, prediction-assisted/text-as-data, and time-series/VAR still need
  comparable held-out failures before the design-card suite is broadly
  adversarial across every contracted family.

### 2026-06-25 Packet 1M — Full design-family method failure coverage

Files changed:

- `evals/method_failure_cases.json`
- `scripts/generate_rigor_report.py`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- Method-specific failure fixtures now cover all 9 design families declared in
  `evals/design_gate_contract.json`.
- `evals/method_failure_cases.json` adds the remaining four families: Panel FE
  bad-control/covariate-timing failure, DAG/refuter missing refuters,
  prediction/text leakage-audit failure, and time-series/VAR failed
  stationarity/unit-root evidence.
- `scripts/check_method_specific_failures.py` now proves 9/9 good fixtures pass
  and 9/9 bad fixtures are rejected by the Method Gate card checker.
- `RIGOR.md` and both READMEs now describe this as all contracted design-family
  failure coverage rather than only DiD/IV/RDD/SC/DML.

Validation:

- `python3 -m py_compile scripts/check_method_specific_failures.py scripts/generate_rigor_report.py` -> PASS
- `python3 scripts/check_method_specific_failures.py --selftest` -> PASS
- `python3 scripts/check_method_specific_failures.py` -> PASS, 9/9 cases caught:
  `did_staggered_without_modern_estimator`,
  `iv_weak_instrument_no_robust_inference`, `rdd_density_manipulation_hit`,
  `synthetic_control_bad_prefit`, `dml_overlap_support_failed`,
  `panel_fe_bad_control_timing`, `dag_refuter_missing_refuters`,
  `prediction_text_leakage_audit_failed`, and `time_series_unit_root_failed`
- `python3 scripts/check_bilingual_docs.py` -> PASS, 24 reference links, 22
  script-tree items, 36 shared markers
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 77
  covered paths, 23 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  25/25 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 25/25 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 18 packets
- `git diff --check` -> PASS

Remaining risk:

- The 9 family fixtures still use one representative failure each. Later
  packets should add multi-fault combinations and estimator-specific fixtures
  inside each family, especially DiD negative weights, SC donor-pool leakage,
  and DML cross-fitting instability.

### 2026-06-25 Packet 1N — Method failure design-family coverage ratchet

Files changed:

- `evals/method_failure_cases.json`
- `scripts/check_method_specific_failures.py`
- `scripts/generate_rigor_report.py`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- `evals/method_failure_cases.json` now explicitly requires every contracted
  design card to have at least one method-specific failure fixture.
- `scripts/check_method_specific_failures.py` fails if any design card from
  `evals/design_gate_contract.json` has no corresponding failure case, or if
  the manifest minimum case count falls below the design-card count.
- The selftest now removes one design-family case to prove missing coverage is
  rejected, so future edits cannot silently shrink the 9-family fixture suite
  while leaving the checker green.
- `RIGOR.md` describes the checker as an every-design-family coverage contract,
  not just a count of currently listed fixtures.

Validation:

- `python3 scripts/check_method_specific_failures.py --selftest` -> PASS
- `python3 scripts/check_method_specific_failures.py` -> PASS, 9 cases caught
  and 9/9 design cards covered
- `python3 -m py_compile scripts/check_method_specific_failures.py scripts/generate_rigor_report.py` -> PASS
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 77
  covered paths, 23 discovered checkers covered
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  25/25 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 25/25 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 19 packets
- `git diff --check` -> PASS

Remaining risk:

- The ratchet guarantees one failure fixture per design family, but not yet
  multiple failure modes per family. Later packets should add within-family
  estimator and data-pathology fixtures.

### 2026-06-25 Packet 1O — Blocking RIGOR registry coverage

Files changed:

- `scripts/check_rigor_registry.py`
- `scripts/generate_rigor_report.py`
- `validate_skill.py`
- `evals/contract_matrix.json`
- `scripts/check_bilingual_docs.py`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- RIGOR registry drift is now a blocking maintenance failure instead of an
  advisory note. If a new `check_*`, `score_*`, or `validate_*` checker appears
  under `scripts/` or `evals/` without a registry entry, the report is not green.
- `scripts/check_rigor_registry.py` independently checks registry coverage,
  duplicate paths, missing registered files, thin invariant descriptions, and
  agreement with `generate_rigor_report._drift()`.
- `validate_skill.py` now runs the new registry checker, so missing RIGOR
  coverage fails the master child gate before publication.
- The contract matrix and bilingual README script inventory now include the new
  registry checker, keeping maintainer docs and executable ownership aligned.

Validation:

- `python3 scripts/check_rigor_registry.py --selftest` -> PASS
- `python3 -m py_compile scripts/check_rigor_registry.py scripts/generate_rigor_report.py validate_skill.py scripts/check_bilingual_docs.py` -> PASS
- `python3 -m json.tool evals/contract_matrix.json >/dev/null` -> PASS
- `python3 scripts/check_rigor_registry.py` -> PASS, 26 registered entries, 25
  discovered checkers, 0 unregistered checkers
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 78
  covered paths, 24 discovered checkers covered
- `python3 scripts/check_bilingual_docs.py` -> PASS, 24 reference links, 23
  script-tree items, 37 shared markers
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  26/26 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 26/26 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 20 packets
- `git diff --check` -> PASS

Remaining risk:

- The registry ratchet proves every checker is publicly registered, but it does
  not judge whether each checker is deep enough. That remains the role of
  targeted fixture expansion and held-out SkillOpt maintenance packets.

### 2026-06-25 Packet 1P — Runtime fallback honesty gate

Files changed:

- `scripts/check_runtime_fallbacks.py`
- `scripts/generate_rigor_report.py`
- `validate_skill.py`
- `evals/contract_matrix.json`
- `scripts/check_bilingual_docs.py`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- Tool, network, MCP, or statistical-backend fallback can no longer be treated
  as an invisible success path. If fallback evidence exists, the workspace must
  record it in `workflow_state.json.decisions`, `00_meta/analysis_backend.md`,
  and a `logs/stage_<N>.md` Runtime fallback block.
- `scripts/check_runtime_fallbacks.py` rejects blocked backends that still claim
  Method Gate pass, quality pass, or replication readiness.
- A fallback path cannot pass Method Gate or replication readiness unless
  artifact parity is explicitly checked as yes/equivalent.
- The checker caught and fixed a parser bug during implementation: the first
  `_line_value` regex consumed the next bullet after an empty field, so template
  placeholders looked like real fallback evidence. The parser now consumes only
  same-line spaces/tabs after the colon.

Validation:

- `python3 scripts/check_runtime_fallbacks.py --selftest` -> PASS
- `tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; bash assets/init_workspace.sh "$tmp/ws" >/dev/null; python3 scripts/check_runtime_fallbacks.py "$tmp/ws"` -> PASS, fallback detected: no
- `python3 -m py_compile scripts/check_runtime_fallbacks.py scripts/generate_rigor_report.py scripts/check_bilingual_docs.py validate_skill.py` -> PASS
- `python3 -m json.tool evals/contract_matrix.json >/dev/null` -> PASS
- `python3 scripts/check_rigor_registry.py` -> PASS, 27 registered entries, 26
  discovered checkers, 0 unregistered checkers
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 80
  covered paths, 25 discovered checkers covered
- `python3 scripts/check_bilingual_docs.py` -> PASS, 24 reference links, 24
  script-tree items, 38 shared markers
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  27/27 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 27/27 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 21 packets
- `git diff --check` -> PASS

Remaining risk:

- The checker enforces disclosure and gate consistency, not semantic equivalence
  of fallback estimates. Later packets should add backend-parity fixtures that
  compare concrete result files across Python/StatsPAI, Stata, and R routes.

### 2026-06-25 Packet 1Q — Backend parity result fixtures

Files changed:

- `evals/backend_parity_cases.json`
- `scripts/check_backend_parity.py`
- `scripts/generate_rigor_report.py`
- `validate_skill.py`
- `evals/contract_matrix.json`
- `scripts/check_bilingual_docs.py`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- Fallback or secondary backend parity now has a concrete result-summary
  comparison contract instead of relying only on prose fields such as
  `Artifact parity checked: yes`.
- `scripts/check_backend_parity.py` compares reference and candidate backend
  result bundles on estimator family, sample hash, N, cluster level, fixed
  effects, coefficients, standard errors, and diagnostics.
- `evals/backend_parity_cases.json` includes one passing Python/StatsPAI → R
  fixture plus four held-out failures: Stata cluster-level mismatch, R sample
  hash drift, RDD estimate drift, and DML missing candidate term.
- `validate_skill.py`, `RIGOR.md`, the contract matrix, and bilingual README
  script inventory all now include the backend-parity checker.

Validation:

- `python3 scripts/check_backend_parity.py --selftest` -> PASS
- `python3 scripts/check_backend_parity.py` -> PASS, 5 cases, 1 passing fixture,
  4/4 failing fixtures caught
- `python3 -m py_compile scripts/check_backend_parity.py scripts/generate_rigor_report.py scripts/check_bilingual_docs.py validate_skill.py` -> PASS
- `python3 -m json.tool evals/backend_parity_cases.json >/dev/null && python3 -m json.tool evals/contract_matrix.json >/dev/null` -> PASS
- `python3 scripts/check_rigor_registry.py` -> PASS, 28 registered entries, 27
  discovered checkers, 0 unregistered checkers
- `python3 scripts/check_contract_matrix.py` -> PASS, 5 contracts, 5 themes, 83
  covered paths, 26 discovered checkers covered
- `python3 scripts/check_bilingual_docs.py` -> PASS, 24 reference links, 25
  script-tree items, 40 shared markers
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  28/28 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 28/28 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 22 packets
- `git diff --check` -> PASS

Remaining risk:

- The fixture contract is offline and checks result-summary equivalence; it does
  not execute Stata or R live. Later packets should add a workspace-level
  `backend_parity.json` template and optional live backend replay when those
  runtimes are available.

### 2026-06-25 Packet 1R — Workspace backend parity report contract

Files changed:

- `templates/backend_parity.json`
- `assets/workflow_state.template.json`
- `assets/init_workspace.sh`
- `validate_skill.py`
- `scripts/check_backend_parity.py`
- `scripts/check_runtime_fallbacks.py`
- `scripts/check_state_template_paths.py`
- `scripts/smoke_workspace.py`
- `scripts/check_gate_integration.py`
- `scripts/check_final_report_contract.py`
- `scripts/check_stage_scenario.py`
- `scripts/generate_rigor_report.py`
- `references/workspace-and-state.md`
- `references/analysis-backends.md`
- `templates/analysis_backend.md`
- `templates/FINAL_REPORT.md`
- `evals/contract_matrix.json`
- `scripts/check_bilingual_docs.py`
- `README.md`
- `README.en.md`
- `RIGOR.md`
- `worklogs/2026-06-25-month-long-quality-goal.md`

Invariant strengthened:

- `00_meta/backend_parity.json` is now part of every initialized workspace and
  the canonical `workflow_state.json` analysis-backend contract.
- `scripts/check_backend_parity.py <workspace>` validates pending, pass, and
  not_pass workspace reports in addition to the offline fixture manifest.
- Runtime fallback paths that claim `Artifact parity checked: yes` while also
  passing Method Gate or replication readiness now require a workspace
  `backend_parity.json` report with `status: pass`.
- Smoke, init, state-template, final-report, stage-scenario, bilingual docs,
  and contract-matrix checks all now know about the backend parity report.
- `RIGOR.md` now describes the backend parity checker as both a fixture and
  workspace-report contract.

Validation:

- `python3 scripts/check_backend_parity.py --selftest` -> PASS
- `python3 scripts/check_backend_parity.py` -> PASS, 5 cases, 1 passing fixture,
  4/4 failing fixtures caught
- `tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT; bash assets/init_workspace.sh "$tmp/ws" >/dev/null; python3 scripts/check_backend_parity.py "$tmp/ws"; python3 scripts/check_runtime_fallbacks.py "$tmp/ws"` -> PASS,
  pending workspace report accepted and no fallback detected
- `python3 scripts/check_runtime_fallbacks.py --selftest` -> PASS
- `python3 scripts/check_state_template_paths.py` -> PASS, 17 state defaults,
  14 bootstrap files, 18 skeleton dirs
- `python3 scripts/smoke_workspace.py --quiet` -> PASS
- `python3 scripts/check_final_report_contract.py --selftest && python3 scripts/check_stage_scenario.py --selftest` -> PASS
- `python3 scripts/check_final_report_contract.py` -> PASS, 11 headings, 14
  markers, 6 commands
- `python3 scripts/check_stage_scenario.py` -> PASS, 10 stages, 32 artifacts,
  13 gate OK checks
- `python3 -m py_compile scripts/check_backend_parity.py scripts/check_runtime_fallbacks.py scripts/check_state_template_paths.py scripts/smoke_workspace.py scripts/check_gate_integration.py scripts/check_final_report_contract.py scripts/check_stage_scenario.py validate_skill.py` -> PASS
- `python3 -m json.tool templates/backend_parity.json >/dev/null && python3 -m json.tool assets/workflow_state.template.json >/dev/null && python3 -m json.tool evals/contract_matrix.json >/dev/null` -> PASS
- `python3 scripts/generate_rigor_report.py` -> PASS, wrote `RIGOR.md` with
  28/28 checker selftests green
- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS, `RIGOR.md`
  current and 28/28 checker selftests green
- `python3 scripts/check_monthly_worklog.py` -> PASS, 23 packets
- `git diff --check` -> PASS

Remaining risk:

- The workspace report is still an offline JSON contract. It blocks unsupported
  parity claims and makes fallback evidence inspectable, but live Stata/R replay
  remains a future enhancement for machines where those runtimes and example
  datasets are available.

## Anti-cheat

- Do not mark the month goal complete before 2026-07-26.
- Do not delete, skip, or relax validators to get a green run.
- Do not count pure wording polish as a theme unless it also fixes a documented drift or usability failure.
- Do not leave generated rigor/catalog outputs stale.
- Do not touch unrelated sibling skills or parent files unless a child change requires parent sync and the parent lane is clean.
