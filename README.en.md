# Paper-WorkFlow

Research-grade orchestration for empirical social-science papers: idea -> design -> data -> identification -> exhibits -> manuscript -> review -> submission package.

This skill is a meta-orchestrator. It does not reimplement the underlying research skills; it routes each stage to the right local skill, subagent, method gate, and reproducibility artifact.

## Quickstart

Use it from Claude Code with a research idea, proposal, dataset, results folder, or draft:

```text
/paper-workflow green credit policy and firm innovation, target: Management Science, language: en
/paper-workflow ./proposal.md, run from data stage
/paper-workflow draft at ./paper/main.tex, polish and prepare submission package
```

If the user asks for autonomous mode, the skill infers conservative defaults, records assumptions in `00_meta/intake.md`, and runs without pausing for preference questions.

## What It Produces

All outputs are written to a self-contained workspace:

```text
paper_workspace/<short>_<YYYYMMDD-HHMM>/
├── 00_meta/workflow_state.json
├── 00_meta/data_governance.md
├── 01_proposal/proposal.md
├── 02_data/clean.parquet + codebook.md
├── 03_analysis/design_register.md + method_gate.md
├── 04_results/
├── 05_draft/main.tex + ref.bib
├── 07_dehumanize/main.tex
├── 08_review/response_letter.md
├── 09_submission/submission_checklist.md + DAS.md
├── REPLICATION.md + run_all.sh
└── FINAL_REPORT.md
```

## Hard Gates

- Method Gate: the causal design must have a design register, diagnostics, robustness artifacts, reproducible scripts, transparency checks, and data-governance hard-flag review.
- Draft Quality Gate: an independent critic scores the draft on contribution, identification, robustness, interpretation, writing, citation fidelity, and reproducibility/governance.

If a gate does not pass, the workflow routes back to the right stage instead of turning weak evidence into polished prose.

## Key References

- Stage execution: `references/stage-playbook.md`
- Skill routing: `references/skill-map.md`
- Method evidence: `references/research-grade-methods.md`
- Threats to validity: `references/threats-to-validity.md`
- Design transparency: `references/design-transparency.md`
- Reproducibility: `references/reproducibility-pack.md`
- Data governance: `references/data-governance.md`
- Runtime fallbacks: `references/runtime-fallbacks.md`
- Templates: `templates/`

## Local Checks

Run from this directory:

```bash
python3 validate_skill.py
python3 scripts/smoke_workspace.py
```

From the parent repository, run:

```bash
make check
```
