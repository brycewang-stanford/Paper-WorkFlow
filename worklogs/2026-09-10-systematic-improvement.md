# 2026-09-10 Systematic improvement — active work record

## Objective and acceptance
Improve the social-science empirical-research skill from idea/data/existing results to a complete, traceable DOCX. User provided a one-week work window; this record reports actual execution, not elapsed-week claims. Work stays local; no external submission, data upload, or publication is authorized by this maintenance task.

Acceptance: preserve existing regression checks and frozen scores; demonstrate repaired failures with executable positive/negative cases; validate standalone routing, honest retrospective analysis, stage transitions, source-to-DOCX fidelity, and clear incomplete-versus-ready reporting. Record rendering evidence and limits. Mechanical checks do not certify research validity.

## Baseline
- Initial git working tree: clean.
- `python3 validate_skill.py`: FAIL, generated RIGOR.md stale (41 registered entries / 40 discovered checkers). Full output captured at `/tmp/pw-baseline-validation.log`; this is a local transient log.
- Existing evaluation is largely structural and saturated; no performance percentage will be inferred from it.
- Inspection: Stage 7 precondition hardcodes main.tex despite the Word path recommending main.md; 1L is normalized to lowercase against uppercase map keys; unknown enter stages succeed.
- Inspection: all existing-result studies require a pre-estimation lock, with no honest retrospective route. A local timestamp/boolean is currently described as proof of pre-registration, which it cannot establish.
- Inspection: Pandoc path strips Markdown structure, enables citeproc only when CSL is configured, and appends a second manually formatted bibliography; raw citation keys can survive without failing the delivery checker.
- Method correction: MDE describes detection probability at chosen alpha/power; effect exclusion requires confidence bounds/equivalence tests, not MDE. Primary references checked 2026-09-10: https://www.povertyactionlab.org/resource/power-calculations and https://www.cos.io/initiatives/prereg.

## Work packages
1. Stage CLI and completion integrity; structured diagnostics.
2. Multi-entry research and honest retrospective design records; standalone operation and proportional intake.
3. DOCX conversion fidelity, freshness evidence, failure behavior, and visual review.
4. Executed end-to-end acceptance cases, final regression, bilingual usage and handoff.

## Verification and final review
Pending. Do not interpret this file or the goal contract as completed work.
