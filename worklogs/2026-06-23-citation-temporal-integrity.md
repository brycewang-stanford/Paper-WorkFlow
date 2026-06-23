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

## Remaining (next coordinated window, optional)

- **evals scenario** exercising a hallucinated-citation / look-ahead rollout — deferred because `evals/*`
  is the parallel agent's territory (it just added an `integrity_checkpoint` scorer dimension); do it
  coordinated to avoid colliding with that dimension.
- A **specification-curve / multiple-testing** deepening only if the inference layer doesn't already cover it
  (it largely does via `inference-and-uncertainty.md` + StatsPAI `romano_wolf`/`wild_cluster_bootstrap`).
