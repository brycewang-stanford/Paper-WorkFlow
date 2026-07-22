# 2026-07-22 Project-Wide Audit & Polish — feat/week-polish-2026-07

## Scope

A four-agent parallel audit of the whole skill (SKILL.md + references corpus,
validator harness + CI, bilingual docs, templates + evals) followed by two
fix waves: P0/P1 (urgent + correctness, 8 commits) and P2 (refactor + dedup +
docs + eval depth, 7 commits). Everything landed on `feat/week-polish-2026-07`
with the full 33-gate battery green after each wave.

Headline findings the audit surfaced (all fixed this wave):

1. **CI red on `main` since 2026-07-11** — the workflow never installed
   `requirements-dev.txt`, so the notebook gate failed on missing numpy.
2. **Gold-value error in the SDM replication case** — `indirect_effect` was
   pinned at 0.5, but the analytic LeSage-Pace value implied by its own DGP
   (ρ=0.3, β=0.5, θ=0.4, row-standardized queen W) is ≈0.75. A *correct*
   replication would have scored `fail`. Surfaced by writing the DGP
   generator; corrected with the computation documented in the case note.
3. **Symmetric README drift** — both directory trees were missing 5 checkers,
   9 templates, 9 reference docs, and the evals subdirs; invisible to the
   bilingual checker because it only compared zh vs en, never vs disk.
4. **"29-of-29" vs "33/33" self-contradiction** inside RIGOR.md, rooted in
   hand-synced badge counts across 5 locations.
5. **9-vs-12 design-card gap** — the three China cards (PSM-DID, spatial,
   threshold panel) had scenarios and replication cases but no gate contract
   and no failure fixtures.

## Change ledger

| Commit | One-line summary |
|---|---|
| `3f9ca6d fix(ci)` | Install requirements-dev.txt + pip cache; CI can run the notebook gate again |
| `3ac202c refactor(skill)` | SKILL.md 32,230 → 31,893 B — back under both the 32,000 target and the 31,966 ceiling |
| `d9840ce fix(claims)` | Rigor-badge count derived live from `generate_rigor_report.REGISTRY`; claim id renamed count-free; RIGOR.md regenerated |
| `8166790 docs(readme)` | Both README trees regenerated against disk; `check_bilingual_docs.py` gains a tree-vs-disk invariant so symmetric staleness can never recur |
| `744273d feat(design-cards)` | Design-gate contract + failure fixtures extended to 12/12 cards (PSM-DID / Spatial / Threshold Panel); `method_gate.md` enumeration updated |
| `3e02949 chore(harness)` | Compile gate now globs; advisory checkers run `check=True` (crashes no longer masked); chaos coverage graduates to `--strict`; cn-claim selftest wired + docstring threshold reconciled |
| `33893e9 chore(citation)` | CITATION.cff gains `version: 2026.07-21`; `date-released` refreshed |
| `a5fd24f feat(replication)` | `--case-id` filter (flat coefficient namespace made whole-directory scoring unusable); README documents all 10 cases in provenance classes |
| `504579b refactor(harness)` | validate_skill.py: ~35 wrapper functions → one `CHECKER_RUNS` table; notebook executes once per validation instead of twice |
| `edfd819 refactor(references)` | dataset-cards China cards → pointers to china-data-sources.md; stage-playbook quality-gate rules → pointers to quality-rubric.md; skill-coverage-map "why 47" table contradictions fixed; CN-banner insertion bug fixed + banners moved to document intros |
| `cdb153a docs(readme)` | Install sections in both READMEs (two-repo relationship explained); mermaid pipeline + orchestrator-vs-writing-tool table ported to EN |
| `03360c4 docs` | complexity_audit.md gains a "goal reached" status update; RELATED-WORK.md counts refreshed and roadmap Phases 1–5 marked shipped |
| `6fad5c4 feat(replication)` | Deterministic DGP generators for the 5 simulation cases (seed=42, `--verify` cross-checks golds, wired into the battery); SDM `indirect_effect` gold corrected 0.5 → 0.75 |
| *(this commit)* | dataset_card.md placeholders unified to `<...>`; `skills_47` claim anchored to the coverage map's enumerated inventory; this worklog |

## Verification

- `python3 validate_skill.py` — full battery green after each wave
  (33/33 gates; RIGOR badge current; complexity ratchet within ceiling with
  107 bytes of SKILL.md headroom).
- `python3 scripts/check_method_specific_failures.py` — 12/12 design cards
  covered, 12/12 failure fixtures caught.
- `python3 evals/replication_cases/generate_simulation_data.py --selftest` —
  DGP truths match case golds; generation deterministic under seed=42.
- `python3 scripts/check_numeric_claims.py` — badge derived live (33/33);
  skills_47 anchored to the 47-row coverage-map inventory.

## Deliberately not done

- Parsimony scoring dimension for `evals/score_skill.py` (the remaining
  "wiring snippet" in `evals/complexity_audit.md`) — changes the eval
  objective; apply in a dedicated eval wave.
- Estimation-side verification of the simulation cases (running actual
  spatial-ML / Hansen-threshold estimators against generated data) — the
  generators pin the DGP truths; estimator recovery remains the candidate
  pipeline's job.
