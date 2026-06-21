# Paper-WorkFlow

Research-grade orchestration for empirical social-science papers: idea -> design -> data -> identification -> exhibits -> manuscript -> review -> submission package.

[中文说明](README.md)

<div align="center">

<table>
  <tr>
    <td align="center">
      <a href="https://copaper.ai"><img src="assets/copaper-logo.png" alt="CoPaper.AI" width="240" /></a>
    </td>
    <td width="56"></td>
    <td align="center">
      <a href="https://sccei.fsi.stanford.edu/reap"><img src="assets/stanford-reap-logo.png" alt="Stanford REAP · Center on China's Economy and Institutions" width="340" /></a>
    </td>
  </tr>
</table>

<strong>Stanford REAP × CoPaper.AI</strong> · An academic–industrial AI toolkit for empirical research<br/>
<sub>The full pipeline from data cleaning to top-journal submission — Paper-WorkFlow is its manuscript-level orchestrator</sub>

</div>

`Paper-WorkFlow` is a meta-orchestrator. It does not reimplement the underlying research skills. It routes each stage to the right local skill, subagent, method gate, reproducibility artifact, and human decision point.

The old 30-page PDF lecture has been folded into this README. The durable content is now maintained as text: the eight-stage teaching map, the 47-skill map, the DiD teaching checklist, the exhibit standards, and the writing/review/submission path. The PDF file itself is no longer part of the package.

## Mental Model

An empirical paper is not just prose. It is an auditable research system: design, data provenance, identification assumptions, estimation scripts, tables, figures, draft, reviewer response, and replication package must agree with each other.

Paper-WorkFlow turns that system into:

- `Stage 0-9`: setup, routing, data, identification, exhibits, drafting, polishing, de-slopping, review, and submission.
- Two hard gates: a Method Gate after Stage 3 and a Draft Quality Gate after Stage 7.
- A resumable workspace controlled by `00_meta/workflow_state.json`.
- A first-class analysis backend choice for Python/StatsPAI, Stata, or R.
- A replication contract tracked through `REPLICATION.md`, `DAS.md`, `run_all.sh`, and `workflow_state.json.replication_pack`.

The core rule is simple: call existing skills instead of rewriting them. The orchestrator is valuable because it gives each skill the right input, at the right time, with the right context boundary.

## From Lecture Map To Executable Workflow

The lecture version presented eight teaching stages. The current skill keeps that teaching path but implements it as a stricter `Stage 0-9` execution protocol.

| Lecture stage | Current execution stage | Core question | Main skills and artifacts |
|---|---|---|---|
| 1. Ideation | Stage 1 | Is the question novel, important, and identifiable? | `econfin-idea-finder`, `novelty-check`, `significance-search` -> topic card |
| 2. Design | Stage 1 | Are the causal question, counterfactual, variation, and target journal clear? | `econfin-proposal`, `journal-digest` -> `proposal.md` |
| 3. Data | Stage 2 | Are sources, keys, frequency, and cleaning rules reproducible? | `data-fetcher`, `data-cleaning` -> `clean.parquet`, `codebook.md`, data log |
| 4. Estimation | Stage 3 | Where does the counterfactual come from, and is the evidence bundle complete? | **Backend router**: Python/StatsPAI by default, or Stata `.do`, or R/fixest/Quarto + design-specific skills -> `analysis_backend.md`, `design_register.md`, `method_gate.md` |
| 5. Tables/Figures | Stage 4 | Can reviewers read the result and identification logic quickly? | Backend-native Word/Excel/LaTeX tables and PDF/PNG figures: StatsPAI, Stata `esttab`/`outreg2`, or R `modelsummary`/Quarto |
| 6. Writing | Stage 5-7 | Is the draft complete, restrained, citation-faithful, and free of AI residue? | `paper-writer`, `paper-pipeline`, `readability` / `fix-chinese` -> `main.tex`, quality scorecard |
| 7. Review | Stage 8 | What would a reviewer attack before submission? | `referee-report`, `paper-referee-revise` -> referee report, response letter, revised draft |
| 8. Submission | Stage 9 | Is the journal fit right, and is the package complete? | `paper-submission`, `reference-verify` -> journal shortlist, cover letter, submission package |

Cross-cutting tools include `web-research` / `arxiv` for literature, `stata` / `stats` for estimation support, `reference-verify` for citation checks, and `markitdown` / `md-to-docx` for document conversion.

## Architecture

| Layer | Responsibility | Key artifacts |
|---|---|---|
| Orchestration | Entry routing, resumability, subagent dispatch, stage gates | `workflow_state.json`, `logs/stage_<N>.md` |
| Evidence | Data, identification design, analysis backend, estimation, robustness, method evidence | `analysis_backend.md`, `design_register.md`, `method_gate.md`, `main_results.json`, `robustness/` |
| Manuscript | Exhibits, draft, polish, de-slop, simulated review, submission materials | `main.tex`, `quality_scorecard.md`, `response_letter.md`, `journal_shortlist.md` |

The method layer is governed by [research-grade-methods.md](references/research-grade-methods.md). It turns modern applied econometrics and causal-inference expectations into stage-level evidence requirements: staggered DiD, RDD, Synthetic DiD, DML, EconML/DoubleML, GRF, DoWhy refuters, PyFixest, and replication-policy checks all have explicit artifacts and fallback rules.

Stages 3-4 now start with the backend router in [analysis-backends.md](references/analysis-backends.md): **Python/StatsPAI** is the default, **Stata** uses `00.2-Full-empirical-analysis-skill_Stata` for `.do` files and `reghdfe`/`ivreg2`/`csdid`/`esttab`/`outreg2`, and **R** uses `00.3-Full-empirical-analysis-skill_R` for tidyverse, `fixest`, `did`, `grf`, `modelsummary`, and Quarto. The default StatsPAI route is documented in [statspai-analysis.md](references/statspai-analysis.md): MCP handles design adjudication, fitting, diagnostics, robustness self-checks, and citations; the package handles publication-grade bundles. All three backends share the same Method Gate.

## The 47-Skill Map

Paper-WorkFlow orchestrates the research action; the underlying action comes from the parent repository's `67-econfin-workflow-toolkit/` and related skill collections.

| Capability group | Representative skills | Workflow role |
|---|---|---|
| Ideation and design | `econfin-idea-finder`, `novelty-check`, `significance-search`, `journal-digest`, `econfin-proposal` | Turn an interest into an executable proposal |
| Data | `data-fetcher`, `data-cleaning` | Build an auditable analysis table |
| Estimation | **Python/StatsPAI, Stata, or R backends**, plus `ols-regression`, `panel-data`, `iv-estimation`, `did-analysis`, `rdd-analysis`, `synthetic-control`, `time-series`, `ml-causal` | Generate method-specific evidence |
| Tables and figures | StatsPAI `regtable`/`collect`, Stata `esttab`/`outreg2`, R `modelsummary`/Quarto, `table`, `figure` | Produce publication-grade exhibits |
| Writing and polishing | `paper-writer`, `paper-style`, `paper-polish`, `paper-self-revise`, `paper-pipeline`, `readability` | Move from draft to journal-specific manuscript |
| Review and citations | `referee-report`, `paper-referee-revise`, `reference-verify` | Simulate review, revise, and verify references |
| Submission | `paper-submission` | Prepare the journal shortlist, cover letter, and submission materials |
| Cross-cutting tools | `web-research`, `arxiv`, `agent-browser`, `markitdown`, `md-to-docx`, `fix-chinese`, `marp-slides-creator`, `chinese-ppt` | Search, conversion, Chinese cleanup, and presentation support |

## Research Standards

Finishing stages is not enough. The workflow enforces four standards that reviewers care about:

| Standard | What it governs | Where it applies | Reference |
|---|---|---|---|
| Method evidence | Identification registry, method-specific diagnostics, robustness matrix, reproducible scripts | Stage 3 Method Gate | [research-grade-methods.md](references/research-grade-methods.md) |
| Scholarly writing | Introduction structure, contribution sharpness, economic magnitude, journal style | Stages 1, 5, 6 | [writing-craft.md](references/writing-craft.md) |
| Reproducibility | Data provenance, replication README, data availability statement, one-command rebuild | Stage 2 through delivery | [reproducibility-pack.md](references/reproducibility-pack.md) |
| Review and submission | Simulated review, response letter, journal decision order, cover letter | Stages 8, 9 | [peer-review-and-submission.md](references/peer-review-and-submission.md) |

The two hard gates make these standards executable:

- Method Gate: no causal claim advances unless the design register, diagnostics, robustness artifacts, transparency checks, and data-governance hard flags are addressed.
- Draft Quality Gate: an independent critic scores contribution, identification, robustness, interpretation, writing, citation fidelity, and reproducibility/governance. The draft must score at least 7 in every dimension, at least 56/70 overall, and have no fatal flags in identification, robustness, or citations.

If a gate fails, the workflow routes back to the right stage instead of turning weak evidence into polished prose.

## Entry Points

You do not need to start from an empty idea.

| User input | Start here |
|---|---|
| A one-line idea or broad research direction | Stage 1: topic and design |
| A mature proposal with X -> M -> Y, design, and sample | Stage 2: data |
| Cleaned data plus a design | Stage 3: estimation |
| Existing regression results or exhibits | Stage 5: draft |
| A `main.tex` draft | Stage 6: polishing |
| A draft plus reviewer comments | Stage 8: review and revision |
| A finished manuscript for submission | Stage 9: journal selection and submission |

## Quickstart

Use it from Claude Code with a research idea, proposal, dataset, results folder, or draft:

```text
/paper-workflow green credit policy and firm innovation, target: Management Science, language: en
/paper-workflow ./proposal.md, run from data stage
/paper-workflow data at ./panel.csv, design is DiD, estimate baseline and robustness first
/paper-workflow data at ./panel.dta, use Stata for a complete do-file replication
/paper-workflow data at ./panel.csv, use R/fixest and modelsummary
/paper-workflow draft at ./paper/main.tex, polish and prepare submission package
```

Before execution, the skill resolves the interaction mode, target journal, manuscript language, and analysis backend once:

| Mode | Meaning |
|---|---|
| `auto` | Runs without mid-stage approval and reports at final delivery |
| `stage-confirm` | Recommended default; each stage ends with a summary card and waits for approval |
| `interactive` | Lets each underlying skill use its native approval flow |

Backend choices are `python-statspai` (default), `stata`, and `r`. Backend choice controls Stage 3-4 scripts and export tools; it is separate from manuscript language.

If the user explicitly asks for autonomous execution, the skill infers conservative defaults, records assumptions in `00_meta/intake.md` and `00_meta/analysis_backend.md`, and continues without blocking on preferences.

## Workspace Outputs

All outputs are written to a self-contained workspace:

```text
paper_workspace/<short>_<YYYYMMDD-HHMM>/
├── 00_meta/workflow_state.json
├── 00_meta/analysis_backend.md
├── 00_meta/quality_scorecard.md
├── 00_meta/data_governance.md
├── 01_proposal/proposal.md
├── 02_data/clean.parquet + codebook.md
├── 03_analysis/design_register.md + method_gate.md
├── 03_analysis/results/ + robustness/
├── 04_results/*.{tex,docx,xlsx} + *.pdf + *.png
├── 05_draft/main.tex + ref.bib
├── 06_polish/
├── 07_dehumanize/
├── 08_review/response_letter.md
├── 09_submission/submission_checklist.md + DAS.md
├── REPLICATION.md + run_all.sh
├── logs/ + backups/
└── FINAL_REPORT.md
```

The final report links the proposal, cleaned data and codebook, analysis code, exhibits, draft, response letter, journal shortlist, cover letter, replication README, data availability statement, and rebuild command.

## DiD Demo

The package keeps one runnable teaching asset: [did_demo.ipynb](did_demo.ipynb). It implements the lecture's DiD focus as six teaching steps across the notebook cells:

| Topic | Preserved checklist |
|---|---|
| Method choice | First ask how treatment is assigned: policy shock -> DiD/event study, threshold -> RDD, external instrument -> IV, single treated unit -> SCM, observational design -> Panel FE / OLS / ML. |
| 2x2 DiD | `Treat x Post` estimates ATT; panel designs should use two-way fixed effects and clustered robust standard errors at the treatment level. |
| Parallel trends | Event studies replace one `Post` with relative-time coefficients; pre-treatment coefficients should be near zero and paired with a pre-trend joint test. |
| Staggered DiD | Do not blindly trust TWFE when timing is staggered and treatment effects are heterogeneous; diagnose Goodman-Bacon weights and consider Callaway-Sant'Anna, Sun-Abraham, BJS / imputation, or `did_multiplegt`. |
| Robustness | Parallel trends, placebo timing, placebo groups, alternative controls, staggered-bias checks, clustering / wild bootstrap, anticipation, spillovers, and dose response. |
| Exhibit standards | Regression tables need coefficients, clustered standard errors, fixed effects, sample size, and star notes; event-study plots need 95% CIs, relative time, a zero line, and a self-contained caption. |

The checked-in demo outputs are:

| Asset | Purpose |
|---|---|
| [assets/fig_raw_trends.png](assets/fig_raw_trends.png) | Raw treated/control trends |
| [assets/fig_event_study.png](assets/fig_event_study.png) | Event-study coefficients |
| [assets/did_table.tex](assets/did_table.tex) | Baseline OLS and TWFE table |

## Design Discipline

1. Call existing skills instead of copying their logic.
2. Protect context: subagents write full outputs to disk and return short status summaries.
3. Prefer verified data, citations, and estimation results over generated claims.
4. Do not attach method labels without evidence bundles.
5. Fail back to earlier stages instead of writing through design failures.
6. Keep human decisions at stage gates unless autonomous mode was explicitly requested.
7. Route child skills robustly: use registered skill names when available, otherwise read the local `SKILL.md` and execute it inline.
8. Treat quality as a scored gate, not a vague aspiration.
9. Start the replication package on day one.

## Repository Layout

```text
Paper-WorkFlow/
├── SKILL.md
├── README.md
├── README.en.md
├── validate_skill.py
├── scripts/
│   └── smoke_workspace.py
├── templates/
│   ├── design_register.md
│   ├── analysis_backend.md
│   ├── method_gate.md
│   ├── quality_scorecard.md
│   ├── data_governance.md
│   ├── DAS.md
│   ├── REPLICATION.md
│   ├── submission_checklist.md
│   ├── FINAL_REPORT.md
│   └── run_all.sh
├── references/
│   ├── stage-playbook.md
│   ├── skill-map.md
│   ├── worked-example.md
│   ├── research-grade-methods.md
│   ├── analysis-backends.md
│   ├── statspai-analysis.md
│   ├── threats-to-validity.md
│   ├── design-transparency.md
│   ├── writing-craft.md
│   ├── literature-and-positioning.md
│   ├── reproducibility-pack.md
│   ├── peer-review-and-submission.md
│   ├── quality-rubric.md
│   ├── data-governance.md
│   ├── runtime-fallbacks.md
│   ├── subagent-templates.md
│   └── workspace-and-state.md
├── assets/
│   ├── init_workspace.sh
│   ├── workflow_state.template.json
│   ├── workflow.svg
│   ├── did_table.tex
│   ├── fig_event_study.png
│   └── fig_raw_trends.png
├── did_demo.ipynb
└── LICENSE
```

## Key References

- [SKILL.md](SKILL.md): entrypoint and full execution protocol.
- [references/stage-playbook.md](references/stage-playbook.md): stage-by-stage operating manual.
- [references/skill-map.md](references/skill-map.md): task-to-skill routing and child-skill loading rules.
- [references/research-grade-methods.md](references/research-grade-methods.md): method evidence requirements.
- [references/analysis-backends.md](references/analysis-backends.md): Python/StatsPAI, Stata, and R backend routing for Stages 3-4.
- [references/statspai-analysis.md](references/statspai-analysis.md): StatsPAI estimation + publication-grade export engine for Stages 3-4 (MCP + package, three domain modes, estimator routing, seven-block robustness gauntlet).
- [references/writing-craft.md](references/writing-craft.md): scholarly writing standards.
- [references/reproducibility-pack.md](references/reproducibility-pack.md): replication packaging standard.
- [references/peer-review-and-submission.md](references/peer-review-and-submission.md): review and submission standard.
- [references/quality-rubric.md](references/quality-rubric.md): Draft Quality Gate scoring rubric.
- [references/subagent-templates.md](references/subagent-templates.md): reusable subagent prompts.
- [references/workspace-and-state.md](references/workspace-and-state.md): workspace layout and state contract.
- [templates/](templates/): reusable artifact templates.

## Local Checks

Run from this directory:

```bash
python3 validate_skill.py
python3 scripts/smoke_workspace.py
```

From the parent repository, regenerate and validate catalog metadata when publishing changes that affect discovery:

```bash
make catalog
make check
```

## Parent Repository

Paper-WorkFlow is the meta-orchestrator inside `Auto-Empirical-Research-Skills`, a collection of empirical research skills for economics, finance, management, and social-science workflows. It does not vendor every child skill into this package; it calls the parent repository's skill collections at runtime.

## License

This package is released under the [MIT License](LICENSE). Child skills from mixed upstream sources should be redistributed only under their own upstream license terms.

---

<div align="center">

<table>
  <tr>
    <td align="center">
      <a href="https://copaper.ai"><img src="assets/copaper-logo.png" alt="CoPaper.AI" width="200" /></a>
    </td>
    <td width="40"></td>
    <td align="center">
      <a href="https://sccei.fsi.stanford.edu/reap"><img src="assets/stanford-reap-logo.png" alt="Stanford REAP" width="300" /></a>
    </td>
  </tr>
</table>

<sub><strong>Stanford REAP × CoPaper.AI</strong> · An academic–industrial AI toolkit for empirical research</sub>

<br/>

<table>
  <tr>
    <td align="center">
      <a href="https://copaper.ai"><img src="assets/copaper-qrcode.png" alt="Visit copaper.ai" width="170" /></a><br/>
      <strong>Visit <a href="https://copaper.ai">copaper.ai</a></strong>
    </td>
    <td width="40"></td>
    <td align="center">
      <img src="assets/copaper-wechat.jpg" alt="CoPaper.AI WeChat" width="170" /><br/>
      <strong>WeChat: CoPaper.AI</strong>
    </td>
  </tr>
</table>

Maintained by <a href="https://copaper.ai"><strong>CoPaper.AI</strong></a>, incubated at <a href="https://sccei.fsi.stanford.edu/reap"><strong>Stanford REAP / SCCEI</strong></a> · AI Assistant for Empirical Research

</div>
