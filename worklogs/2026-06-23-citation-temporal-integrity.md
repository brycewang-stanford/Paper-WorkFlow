# Worklog — 2026-06-23 · Citation-existence & Temporal-integrity layer (ARS-inspired, collision-navigated)

**Goal of this pass.** Reference [`Imbad0202/academic-research-skills`](https://github.com/Imbad0202/academic-research-skills)
(ARS) to raise the Paper-WorkFlow skill one tier, **without colliding** with a second agent that is
**actively editing the same single-branch working tree in parallel** (its in-flight set at handoff time
included `SKILL.md`, both READMEs, `evals/*`, `assets/*`, `validate_skill.py`, `scripts/{check_workspace_gates,
smoke_workspace}.py`, `references/{orchestration-and-handoff,workspace-and-state}.md`, `templates/FINAL_REPORT.md`).

## Gap analysis (what ARS has that we lacked)

ARS's headline credibility mechanisms are deterministic citation verification, **temporal integrity audit**,
and claim-faithfulness locators. Grep of our tree (`*.md`) before this pass:

- `temporal` / `anachron` = **0 files** — temporal-integrity was entirely missing.
- `faithful` = 1 file — claim↔source faithfulness barely present.
- citation existence/retraction mechanics — implied via `reference-verify`/`bibtex` but no written standard.

Our skill is **method-strong** (design-risk-ledger, empirical-audit, inference-and-uncertainty, …) but
**citation/temporal-integrity-weak**. That is the clean "improve by referencing ARS" story.

## Collision (independently converged with the parallel agent — again)

While I was building, the parallel agent was **also** adapting ARS and **also** converged on the integrity
idea. Its in-flight (uncommitted at the time) files:

- `references/integrity-and-claim-audit.md` + `templates/claim_integrity_audit.md` — **claim→evidence
  faithfulness**: claim locator manifest + verdict taxonomy (supported / minor_distortion / major_distortion /
  unsupported / retrieval_failed / constraint_violation) + sampling discipline + `workflow_state.json.integrity_audit`.
- `templates/pipeline_status.md` — a stage dashboard.

**Resolution — clean complementary split using ARS's own framing.** ARS separates *"the reference exists"*
from *"the claim is faithful."* The parallel agent owns the **faithfulness** half. So I **de-duplicated my
work to own the two halves it brackets out**:

1. **Citation existence & correctness** — DOI/arXiv resolution, metadata match, version, **retraction screen
   (scite)**, predatory-venue flag, no citation laundering, number/quote fidelity when transcribing others'.
2. **Temporal integrity** — the wholly-missing layer: literature timing (no future-as-motivation, search
   cutoff for "first/no prior work"), data timing (look-ahead, real-time vs final **vintage**, event-window
   peeking, time-respecting train/test split, survivorship/backfill), sample-period vs claim-period.

I **dropped my original §3 faithfulness content** (it duplicated their `claim_integrity_audit.md`) and replaced
it with an explicit scope-boundary pointer. **No git-level collision: zero shared file paths.**

## What I shipped (mine, committed)

- `references/citation-and-temporal-integrity.md` (`91cb2b4`) — the standard for §1 citation existence/correctness
  and §2 temporal integrity; explicit boundary deferring claim-faithfulness to the sibling layer; tool map
  (StatsPAI `bibtex`, zotero MCP `scite_check_retractions`/`scite_enrich_*`, WebFetch DOI), gate wiring, anti-patterns.
- `templates/citation_integrity_log.md` (`91cb2b4`) — per-paper `00_meta/citation_integrity_log.md`: §1 citation
  verification table + §2 temporal checklist (`pass/na/risk`).
- `scripts/check_citation_integrity.py` (`91cb2b4`) — standalone deterministic checker. Validates the **workspace
  log only** (touches no contended skill file). `--selftest` (invariants) + `--final` (Stage 9: no `to-verify`,
  no un-dispositioned `flagged`, ≥1 asserted citation). §3 faithfulness validated only if present (optional).
- `references/empirical-audit.md` + `references/dataset-cards.md` (`6c57c53`) — two surgical inbound pointers
  from the natural thematic homes (sample-boundary ⊃ time-boundary; vintage = look-ahead, not just reproducibility).

## Territory map (so we don't collide again)

- **Mine (this pass):** `references/citation-and-temporal-integrity.md`, `templates/citation_integrity_log.md`,
  `scripts/check_citation_integrity.py`; the temporal-integrity pointers inside `empirical-audit.md` and
  `dataset-cards.md`. (Plus prior: `references/dataset-cards.md`, `templates/dataset_card.md`.)
- **Parallel agent's (do not touch):** `references/integrity-and-claim-audit.md`, `templates/claim_integrity_audit.md`,
  `templates/pipeline_status.md`, `references/{orchestration-and-handoff,workspace-and-state}.md`, `SKILL.md`,
  both READMEs, `evals/*`, `assets/*`, `validate_skill.py`, `scripts/{check_workspace_gates,smoke_workspace,
  check_verification_log}.py`, `_verification_log/*`.

## Deferred → ALL RESOLVED same-day (see "Full hardening pass" at the bottom)

- **SKILL.md wiring**: add one「进一步阅读」bullet + (optionally) one citation/temporal「关键约束」line, via the
  proven **exact-match Edit in a clean-tree window** (a contended region fails the match harmlessly). Deferred
  because SKILL.md is mid-flight in the parallel agent's set and the further-reading region is exactly where the
  parallel agent is likely adding its own integrity bullet — same-region editing would collide.
- **Wire `check_citation_integrity.py` into the run-time gate** (`scripts/check_workspace_gates.py` /
  `validate_skill.py`) — both are the parallel agent's territory; defer to a coordinated/clean window.
- **submission_checklist / quality-rubric ⑥** could gain a citation-integrity row/pointer — safe non-contended
  edits for a later pass.

## Roadmap for the rest of the window (ARS-inspired, non-contended candidates)

1. **(done this pass)** Citation-existence + temporal-integrity layer.
2. Temporal-integrity **worked example** — extend `worked-example.md` golden path with a look-ahead/vintage
   NOT-PASS→fix loop (read-only-ish; coordinate since worked-example may be touched).
3. **CITATION.cff** for the skill (ARS ships one) — additive, safe, low effort.
4. **Retraction-screen runtime fallback** note in `runtime-fallbacks.md` (scite/zotero MCP down → manual path).
5. Consider a **specification-curve / multiple-testing** deepening only if not already covered by inference layer.

## Verification

- `python3 scripts/check_citation_integrity.py --selftest` → invariants hold.
- Template instantiated into a temp workspace: non-final OK; `--final` correctly fails a bare template.
- `python3 validate_skill.py` → `OK: Paper-WorkFlow skill checks passed` (incl. parallel agent's checkers;
  all markdown local links resolve).

Net: one coherent ARS-inspired credibility layer (citation-existence + the previously-absent temporal-integrity)
shipped end-to-end in 2 commits, **zero git collisions** after de-duplicating against the parallel claim-audit
layer. Staged only explicit paths; never `git add -A`.

---

## Full hardening pass (same day, after the parallel agent pushed and the tree went clean)

The parallel agent committed + pushed its whole change set (schema v10 claim-integrity audit,
pipeline-status, README redesign, evals integrity dimension); the working tree went **clean** and
`HEAD == origin/main` (its batched push carried my first 3 commits up too). That opened the clean
window, so every deferred item was shipped and the layer was made **first-class across the whole skill
surface**:

| Commit | What |
|---|---|
| `fce5b01` | **Load-bearing**: wired `check_citation_integrity.py` into `validate_skill.py` (required-file list + py_compile + `--selftest` CI), and added the SKILL.md key-constraint + further-reading bullet (complementary to the claim-audit layer, anchored on its own line 391 "citation 存在不等于 claim 忠实"). |
| `a06192b` | `CITATION.cff` (CFF 1.2.0; MIT / Bryce Wang; integrity keywords). |
| `1fa0b8d` | Surface wiring: quality-rubric ⑥ (retraction + temporal red flags + checker pointer), runtime-fallbacks (scite/bibtex/DOI-down + real-time/vintage-down matrix rows + §4 cap rule), subagent-templates §CT (citation/temporal critic dispatch), submission_checklist §3 (`--final` + temporal final gates), worked-example (Stage 2 look-ahead NOT-PASS→fix loop + self-check bullet). |
| `9da92a3` | Operational loop in stage-playbook: Stage 8 dispatches the §CT critic; Stage 9 adds the `--final` gate beside reference-verify. |

**Integration now closed end-to-end:** Stage 1 init log → Stage 2 vintage (dataset-cards) → Stage 3
look-ahead → quality-rubric ⑥ gate → Stage 8 §CT critic → Stage 9 `--final` → submission checklist.
`check_citation_integrity.py` is exercised by CI (`validate_skill.py`).

**Boundary held throughout:** claim↔evidence faithfulness stays the parallel agent's
`integrity-and-claim-audit` layer; I own citation **existence/correctness** + **temporal integrity**.
Every cross-reference between the two layers points outward by name; zero shared file paths; every commit
staged explicit paths only. `validate_skill.py` green after each commit.

**Session total: 7 commits** (`91cb2b4`, `6c57c53`, `62707dd`, `fce5b01`, `a06192b`, `1fa0b8d`, `9da92a3`),
zero collisions.

## Third pass (same day) — checker hardening + an eval-harness crash fixed

- **Checker hardened** (`3655226`): duplicate-bibkey guard in §1; `--final` now also requires the §2
  temporal audit to have been performed (≥1 conclusion) — closing a doc-vs-code gap with the Stage 9 gate
  I documented in `stage-playbook.md`. Reference §3 + template hard-rules synced; selftest expanded.
- **Eval-harness crash fixed** (`e06480d`): the parallel agent's just-added `integrity_checkpoint` dimension
  was read by `score_scenario` but missing from the synthetic globals dict in `score_skill.py`'s `_selftest`,
  so `python3 evals/score_skill.py --selftest` crashed with `KeyError: 'integrity_checkpoint'`. Added the
  missing key (1.0, like the other global dims). **Objective crash, one-line fix, no scoring/baseline change**
  — collaborative repair, not a scope decision. `--selftest` and the full run are green again.

## Division-of-labor decision on the evals dimension (deliberate, not deferred-by-omission)

I evaluated adding a `citation_temporal_integrity` global dimension to the eval scorer and **decided against
applying it myself**, because:

1. `score_skill.py` totals are `sum(dims)/len(DIMENSIONS)` — adding a 7th dimension shifts the divisor (6→7),
   moving **every** scenario total and split mean, which **invalidates the just-committed `baseline_scorecard.md`**.
2. The harness README explicitly frames scope/dimension changes as the **loop owner's** call ("the harness
   measures; it does not unilaterally expand the skill's scope"), and the harness is "standalone on purpose".
3. My layer already has a **stronger** guarantee than an eval dimension: `validate_skill.py` CI runs
   `check_citation_integrity.py --selftest` as a hard gate (`fce5b01`).

**Drop-in spec for whoever owns the eval harness** (one coherent edit, then refresh the baseline):

```python
# add to score_skill.py
CITATION_TEMPORAL_FILES = [
    "SKILL.md", "references/citation-and-temporal-integrity.md",
    "templates/citation_integrity_log.md", "scripts/check_citation_integrity.py",
]
CITATION_TEMPORAL_GROUPS = [
    ["citation_integrity_log", "Citation Integrity Log"],
    ["look-ahead", "时序穿越", "temporal integrity"],
    ["check_citation_integrity"],
    ["vintage", "real-time"],
    ["--final"],
]
# then: append "citation_temporal_integrity" to DIMENSIONS, add it to compute_global_scores'
# return (via _fraction_groups_present), add it to score_scenario's dims dict, AND add
# "citation_temporal_integrity": 1.0 to the synthetic g dict in _selftest. Re-baseline.
```

## Fourth pass — deep integration (user authorized finishing ALL remaining work)

With the parallel agent idle ~50 min and the user owning the repo and explicitly authorizing the
remaining work, I did the deeper integration previously held back for collision-avoidance — but made
a deliberate scope call on the schema.

**Decision: NO schema v11 bump.** A `citation_integrity` block in `workflow_state.json` would have
been "symmetric" with the claim-audit `integrity_audit` block, but it couples the layer to the
version-gated substrate across **~11 files** (`workflow_state.template.json`, `validate_skill.py` ×3,
`smoke_workspace.py` ×2, `check_workspace_gates.py`, `orchestration-and-handoff.md`,
`workspace-and-state.md`, both README badges, `SKILL.md`) for modest added substance — the
`citation_integrity_log.md` artifact + the deterministic `check_citation_integrity.py` already carry
the state, and the checker is a *stronger* guarantee than a hand-maintained JSON field. Senior call:
maximal surface ≠ solid. Skipped it deliberately, documented here.

**What I did instead (first-class without the bump):**

| Commit | What |
|---|---|
| `8b16663` | `citation_integrity_log.md` is now **born at Stage 0** (`init_workspace.sh`), **enforced in CI** (`validate_skill.py` asserts init creates it), shown in the **dashboard** (`pipeline_status.md`), and **documented** (`workspace-and-state.md` init list + directory tree; `SKILL.md` Phase 0 artifact list). |
| `53a1509` | **evals `citation_temporal_integrity` dimension** — the drop-in from the third pass, now applied: a global regression guard scoring 1.0 only while the layer is present (reference + template + checker + look-ahead/vintage + `--final`). `score_skill.py` (incl. the `_selftest` globals dict — the exact key the integrity_checkpoint dimension forgot, causing `e06480d`'s crash), `baseline_scorecard.md` re-baselined to 7 dims (means stay 1.000), `README.md` table + "mean of the seven dimensions" (was stale at "five"). |

Stage 9 enforcement of the layer stays via `check_citation_integrity.py --final` (wired into
`stage-playbook.md` + `submission_checklist.md` in the earlier passes), not a gate-checker block.

**Final verification (all green):** `validate_skill.py`, `smoke_workspace.py --quiet`,
`check_citation_integrity.py --selftest`, `check_workspace_gates.py --selftest`,
`check_verification_log.py --selftest`, `evals/score_skill.py --selftest`, and a live
`init_workspace.sh` run whose fresh workspace passes the citation checker.

## Remaining

- **Nothing required.** The layer is complete and first-class: standard, per-paper template, hardened
  CI-wired checker, born-at-init artifact, dashboard + state docs, both gates (rubric ⑥ + Stage 9
  `--final`), runtime fallbacks, subagent §CT critic, worked-example loop, evals regression guard,
  CITATION.cff.
- **Not needed:** specification-curve / multiple-testing (already covered by `inference-and-uncertainty.md`
  + StatsPAI `romano_wolf`/`wild_cluster_bootstrap`/`benjamini_hochberg`); schema v11 bump (deliberate, above).

**Session total: 11 commits** — the 9 prior + `8b16663` (born-at-init/first-class) + `53a1509` (evals
dimension). Zero collisions across the whole effort; every commit explicit-path staged; the parallel
agent's claim-audit layer and orchestration substrate untouched except the one objective crash fix
(`e06480d`) and the symmetric additive rows that compose with — never overwrite — its work.
