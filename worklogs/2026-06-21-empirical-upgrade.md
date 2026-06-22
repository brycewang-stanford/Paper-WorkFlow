# 2026-06-21 Empirical Upgrade Worklog

Scope: `skills/69-Paper-WorkFlow` only. Parent catalog, commits, and pushes were intentionally left untouched because another agent may be working in parallel.

## Audit Findings

1. The skill already had strong Stage 3 method evidence: sample audit, design register, method gate, inference report, mechanism pack, evidence ledger, and gate verifier.
2. The remaining empirical-analysis gap was not another estimator route. It was a missing stateful contract for reviewer-style design risks that cut across methods: OVB, selection, bad controls, spillovers/SUTVA, external validity, attrition, specification search, selective reporting, and overbroad policy claims.
3. Existing prose covered many of these risks in `threats-to-validity.md` and `design-transparency.md`, but no runtime state block or mechanical gate invariant forced them to be closed before Method Gate pass.

## Upgrade Implemented

- Added `references/design-risk-ledger.md` and `templates/design_risk_ledger.md`.
- Bumped workflow state to schema v8 with `workflow_state.json.design_risk`.
- Updated `init_workspace.sh`, `smoke_workspace.py`, `validate_skill.py`, and `check_workspace_gates.py` so design risk is part of setup, smoke testing, local validation, and runtime gate consistency.
- Wired the ledger through `SKILL.md`, `stage-playbook.md`, `subagent-templates.md`, `research-grade-methods.md`, `threats-to-validity.md`, `design-transparency.md`, `quality-rubric.md`, final-report/submission/replication templates, and bilingual READMEs.

## Residual Risks

- Parent-repo catalog metadata was not regenerated in this pass because edits stayed inside the child skill and no publish was requested.
- The design-risk checker is intentionally mechanical: it verifies status/order/file existence/blocking lists, but substantive judgment still belongs to the Method Gate and critic subagents.
- Existing worktree is ahead of `origin/main`; do not push or rewrite until the user explicitly asks.
