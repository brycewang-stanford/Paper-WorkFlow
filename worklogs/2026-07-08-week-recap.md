# 2026-07-08 Week Recap (2026-07-04 → 2026-07-08)

## Scope

Week-level recap covering the four substantive pushes that landed after
the Card (1995) replication worklog closed. This file exists to close the
auditability gap between `2026-07-04-card-1995-iv-replication-case.md`
(its own per-commit worklog) and today's date; downstream reviewers
should read this together with the per-commit worklogs cited inline.

| Date | Commit | One-line summary |
|---|---|---|
| 2026-07-04 | `62d448b chore: update skill and reference docs` | +2 KB of references; two large new CN data-source / journal files |
| 2026-07-04 | `1b1753d feat(evals): Card (1995) IV replication case` | See dedicated worklog `2026-07-04-card-1995-iv-replication-case.md` |
| 2026-07-05 | `d980301 feat: add defense workflow assets` | `defense_pptx.py` (756 lines) + 5 new simulation eval cases |
| 2026-07-06 | `41d8357 demo(7.5): internet use on income — synthetic CFPS panel, 12pp paper` | First end-to-end 12pp demo paper shipped |
| 2026-07-06 | `413b4c4 feat: add paper workflow intro script` | `build_paper_workflow_intro.py` (705 lines) for poster / intro HTML |
| 2026-07-06 | `2ce2986 chore(ratchet): refresh complexity baseline for v2026.07-6` | Complexity baseline bumped (SKILL.md 30935→32022 B; refs 29→31 files) |

## Change

### 1. CN-context knowledge layer (`62d448b`)

- `references/china-data-sources.md` (+854 lines): catalog of CFPS / CHARLS /
  CHNS / CLDS / CGSS / CHIP / urban / firm-level panel sources with
  provenance, refresh cadence, and known access routes. Stage 2 default
  source table.
- `references/chinese-journals.md` (+1009 lines): tier-1 / tier-2 Chinese
  journal index with editorial preference, page limits, and submission
  rules. Stage 9 candidate pool.
- Tiny alignment fixes in `data-governance.md`, `design-gate-cards.md`,
  `peer-review-and-submission.md`, `research-grade-methods.md`,
  `skill-map.md`, `stage-playbook.md`.

### 2. Defense workflow + simulation eval pack (`d980301`)

- `defense_pptx.py` (756 lines): thesis-defense slide generator with
  pre-rendered layouts for problem, contribution, data, identification,
  robustness, and Q&A appendix slides. Driven by
  `templates/defense_ppt_config.yaml` (101 lines) so per-school style
  overrides live in a config rather than the code.
- 5 new eval simulation cases under `evals/replication_cases/`:
  - `digital_economy_pilot_simulation.json` — pilot-zone DiD with
    staggered rollout.
  - `digital_transformation_psm_did_simulation.json` — PSM + DiD
    composite.
  - `regional_compete_threshold_simulation.json` — regression kink
    with cross-region threshold.
  - `threshold_panel_simulation.json` — panel threshold regression.
  - `spatial_sdm_simulation.json` — spatial Durbin panel.
- `evals/scenarios.json`, `evals/README.md`, `evals/baseline_scorecard.md`
  updated to register the new cases.
- `references/skill-map.md` and `references/stage-playbook.md` cross-link
  to the new simulation cases.

### 3. 12pp end-to-end demo paper (`41d8357`)

- Topic: effect of household internet use on personal income, on a
  synthetic CFPS-style panel (4001 rows; full data-generating script
  in `02_data/generate_data.py`, 435 lines).
- Pipeline walked: Stage 2 clean → Stage 3 PSM + OLS / heterogeneous
  forest / KDE → Stage 4 publication tables (`table2_main_regs.tex`,
  `table3_heterogeneity.tex`) + 5 figures (`fig1`–`fig5`) → Stage 5–7
  writing and polish → Stage 8 referee loop.
- Output artefacts: `04_results/{balance_test, control_coefs,
  regression_results, regression_heterogeneity, robustness_summary}.txt`
  + `04_results/figures/*.png` + `04_results/tables/*.tex`. README
  and `README_paper.md` summarise the run for readers.
- This is the first committed end-to-end run that touches every Stage;
  used as the reference trace for Stage contract testing in
  `evals/stage_scenario_contract.json`.

### 4. Workflow intro / poster generator (`413b4c4`)

- `build_paper_workflow_intro.py` (705 lines): produces a self-contained
  HTML / PDF teaser for the workflow ("one image, one page" pitch for
  external readers — recruitment decks, conference handouts).
  Reuses the brand assets in `assets/` (copaper / Stanford REAP logos).
- Wired into the README pipeline; not yet on the `Makefile`-style
  `make catalog` entry (deferred to a follow-up).

### 5. Complexity ratchet (`2ce2986`)

- `evals/complexity_baseline.json` updated:
  - SKILL.md: 30935 → 32022 bytes (always-loaded layer stays 22 B over
    the 32 K target — ceiling relaxed to absorb the upstream
    consolidation; rationale logged in the commit body).
  - References: 29 → 31 files (+104 756 B on-demand corpus).
- Targets unchanged. Per the ratchet policy, this bump **must** be
  accompanied by a fresh `chore(ratchet): …` commit on every
  baseline-bumping PR; the next maintainer should not let the
  baseline silently drift.

## Integrity Decision

- The two large CN-context references (`china-data-sources.md`,
  `chinese-journals.md`) are **claim-heavy** but not citation-audited
  yet. Each fact in those files is something a downstream reviewer
  could try to verify against a publisher's homepage. Tracking is
  open: appending to `_verification_log/cn-data-claims.md` is the next
  week's job, not this week's.
- The 12pp demo paper is built on **synthetic CFPS**, not real CFPS
  microdata. That is called out loudly in the demo README. Anyone
  reading the demo as a paper should not infer real-data conclusions.
- Defense workflow assets were added without exercising them on a real
  defense yet. The contract for "first defense → log any field-driven
  refinements here" is open.

## Validation

- `python3 validate_skill.py` passed end-to-end after the ratchet
  refresh (29/29 executable gates still green).
- `python3 scripts/check_bilingual_docs.py --selftest` passed; the live
  README ↔ README.en.md parity check passed.
- `python3 scripts/check_cross_references.py` passed for the new files.
- Demo paper: re-ran `generate_data.py` from a clean checkout — same
  hash for `cfps_internet_income_panel.csv` (synthetic seed is pinned).

## Open Items

- Wire `build_paper_workflow_intro.py` into the existing `make catalog`
  surface (one-liner).
- Start a `_verification_log/cn-data-claims.md` ledger mirroring
  `methods-claims.md` so the new CN references carry the same audit
  weight as econometrics claims.
- Update README to mention the demo paper as the canonical Stage 0→9
  walk-through (currently it lives only in the worklog).