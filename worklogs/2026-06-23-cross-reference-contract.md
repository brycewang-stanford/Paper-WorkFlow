# Worklog — 2026-06-23 · Cross-reference contract linter (drift brake for parallel editing)

**Long-term goal set for the week.** The skill is prose-complete, template-complete, and already
carries three layers of maintenance harness (`validate_skill.py`, `evals/score_skill.py`,
`evals/check_complexity_budget.py`). The remaining frontier is **internal-contract integrity**:
the skill is a ~30-file web of mutual references (SKILL.md ↔ 29 references ↔ 24 templates ↔ 5
checkers ↔ `init_workspace.sh` ↔ state schema), and its correctness depends on all of them agreeing
about script-invocation commands, repo file paths, and workspace artifact paths. With **two agents
editing the same single-branch tree in parallel**, a rename or path change is the #1 silent-rot
risk — and the slices most exposed were entirely unguarded. The week's theme: **make the skill's
internal contract mechanically self-consistent and drift-proof, additively, without colliding.**

## Gap analysis (what was unguarded before this pass)

`validate_skill.py` guards two slices of the reference web — fully-formed markdown link targets
resolve, and required template/reference markers are present — but NOT the slices that rot silently
when prose is edited:

| Drift class | Guarded before? |
|---|---|
| inline ``python3 scripts/X.py`` / ``bash assets/Y.sh`` command names a renamed/moved script | **no** (inline code is invisible to the markdown-link checker) |
| backticked/bare ``references/X.md`` / ``templates/Y.md`` mention points at a missing file | **no** (only `[](…)` links checked) |
| workspace artifact path hard-coded in a gate checker whose top-level dir is not even in the `init_workspace.sh` skeleton | **no** |
| a new `scripts/check_*.py` added but never wired into the master harness (orphaned from CI) | **no** |

On the live tree there is currently **zero drift** (62 inline commands, 207 repo-path mentions, 52
checker workspace paths all resolve) — so this is **preventive** infrastructure, a brake that should
stay green and fire only when a future edit breaks the contract.

## What I shipped (mine, committed + pushed)

| Commit | What |
|---|---|
| `2f030e8` | `scripts/check_cross_references.py` — standalone, read-only, static linter for the four invariants above. `--selftest` builds a synthetic tree with injected drift (broken command, ghost path, out-of-skeleton checker path, orphan checker) and asserts each invariant fires, then a repaired tree passes. Self-wiring is a **WARN not a FAIL** (no bootstrap paradox: a freshly added checker can't require its own wiring to ship green); every *other* orphan checker is a FAIL. |
| `41ccfa6` | Wired it into `validate_skill.py` (`--selftest` + live check + py_compile). CI now fails on any inline-command / repo-path / checker-workspace-path drift. The linter's own `harness_wiring` WARN cleared (5/5 `check_*.py` wired). |

## Territory map (so we don't collide)

- **Mine (this pass):** `scripts/check_cross_references.py` (new file, sole owner); a 13-line additive
  wiring of it into `validate_skill.py` (one new function + one py_compile entry + one `main()` call).
- **Parallel agent's (observed active, do not contend):** `validate_skill.py` body, `evals/*`
  (complexity ratchet `b3fcbf0` landed 3 min before this pass), `references/skillopt-improvement-loop.md`,
  both READMEs, `SKILL.md`. My only touch to a contended file (`validate_skill.py`) was three minimal
  exact-match edits in distinct regions, staged explicit-path, committed in a verified clean window
  (`origin/main == b3fcbf0`, FF-safe), pushed immediately to minimize the entanglement window.

## Collision discipline followed

- Built standalone first (zero-collision new file), committed green, *then* wired in a confirmed clean
  window — the proven pattern from the citation-integrity layer (`fce5b01`).
- Never `git add -A`; staged only `scripts/check_cross_references.py`, then only `validate_skill.py`.
- The +249-byte reference growth the ratchet now reports is the parallel agent's `b3fcbf0`
  (`references/skillopt-improvement-loop.md` +5 lines), not mine — my footprint on the complexity
  ratchet is **zero** (a script, not SKILL.md/references).

## Verification (all green)

- `python3 scripts/check_cross_references.py --selftest` → invariants hold.
- `python3 scripts/check_cross_references.py` → `internal references are mutually consistent` (exit 0).
- `python3 validate_skill.py` → `OK: Paper-WorkFlow skill checks passed` (now includes the linter).
- FF-safe push: `b3fcbf0..41ccfa6 main -> main`; `origin/main == HEAD`.

## Roadmap for the rest of the window (non-contended candidates, in priority order)

1. **(done)** Cross-reference contract linter + CI wiring.
2. **Tighten invariant 2** — extend repo-path-mention checking to flag a *reference* doc that exists on
   disk but is orphaned (linked by nobody from SKILL.md or any sibling), catching dead references.
3. **Stage/gate-name agreement invariant** — assert the Stage 0–9 names in SKILL.md's pipeline table
   match `validate_skill.py:EXPECTED_STAGE_KEYS` and the state template (mechanizes a check now done by
   eye). New invariant in the same linter; no SKILL.md edit needed.
4. **Integration smoke** — a test that instantiates the *real* templates via `init_workspace.sh` into a
   temp workspace, writes a realistic passing state, and runs *all* checkers together (today's selftests
   use synthetic stubs; nothing exercises the real init script + real templates + all checkers as one).
5. **Template ↔ checker key agreement** — assert every `workflow_state.json` block key the checkers read
   exists in `assets/workflow_state.template.json` (catches a checker reading a field the template never ships).

All five are additive, new-file or single-linter edits, and avoid the parallel agent's hot zones
(`SKILL.md`, READMEs, `evals/*`, the ratchet).

## Update — increment 2 (same session): roadmap item 4 shipped

`scripts/check_gate_integration.py` (`23e7b37`) — the end-to-end gate integration test. The
per-checker selftests run on synthetic stubs and `smoke_workspace.py` instantiates the real
templates but never runs the gate checkers on them, so one contract was CI-unverified: do the real
`init_workspace.sh` skeleton + real templates, driven to a genuine PASS, actually satisfy the
checkers? The new test (a) asserts the born-at-init `citation_integrity_log.md` passes
`check_citation_integrity` (non-final) — a contract a prior pass verified only by hand; (b) builds a
PASS workspace from the real templates plus synthesized analysis artifacts and asserts
`check_workspace_gates` reports zero failures; (c) corrupts that real workspace three ways and asserts
the right check goes red, then restores green. Wired into `validate_skill.py` (run + py_compile);
the cross-reference linter's `harness_wiring` invariant now reports 6/6 `check_*.py` wired. Clean
window, explicit-path staged, FF push. Roadmap items 2/3/5 are covered by the increment below.

## Update — increment 3: dead-doc, stage, and state-block contracts

The linter now covers the remaining low-conflict roadmap invariants:

- `orphaned_references` walks from `SKILL.md`, `README.md`, and `README.en.md` through markdown links
  and bare `references/*.md` mentions, then fails if any top-level reference doc is unreachable.
- `stage_contract` compares the Stage table in `SKILL.md` with `assets/workflow_state.template.json`
  so Stage 0-9 prose and state schema cannot drift silently.
- `block_agreement` statically scans `scripts/check_workspace_gates.py` for top-level
  `state[...]` / `state.get(...)` reads and fails if the template does not ship those blocks.

`scripts/check_cross_references.py --selftest` now injects failures for all seven invariants and
then repairs the synthetic tree back to green, so the new checks are regression-tested rather than
only exercised on the currently clean live tree.
