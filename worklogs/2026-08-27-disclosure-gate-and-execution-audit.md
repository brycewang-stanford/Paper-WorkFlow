# 2026-08-27 AI-Use Disclosure Gate + Execution Audit — `agent/literature-base-workflow`

## Scope

Two halves. The first added the coverage the package was missing; the second
found out what was broken by **running things instead of reading them**. Eight
commits, `35 → 39` executable gates, battery green on Python 3.11 / 3.12 / 3.13
after each.

The second half is the one worth remembering. Every defect below was invisible
to review and obvious within seconds of execution:

| Defect | Found by |
|---|---|
| The thesis defence deck shipped with no conclusion, mechanism or limitations slide | building a deck with six findings |
| A correct Chinese-authored AI-use ledger produced four false blocking findings | writing one the way a user would |
| `build_paper_workflow_intro.py` wrote its output into a *different repository* | running it and reading the success line |
| `make_three_line_tables.py` had a passing selftest nothing had ever run | widening checker discovery past the filename |
| `validate_skill.py --help` ran the entire battery instead of printing help | invoking `--help` from a new checker |

The same habit applies to worries, not just code. The "reference corpus needs
consolidating" note in this file's first draft was a guess; measuring it (see
*What the next wave should look at*) showed it was wrong.

## Part 1 — what was missing

### 1. AI-use disclosure & authorship integrity (schema v13, gate #36)

The gap this pipeline **creates for itself**. Stage 5 drafts with an LLM,
Stage 6 polishes with an LLM, and Stage 7 exists to remove the stylistic
fingerprint of the LLM — so the run best equipped to look like it never used AI
was also the run under no obligation to say it had. ICMJE, COPE, Elsevier,
Springer Nature, Wiley, SAGE, T&F, the AEA and the 中文期刊 / 学位论文 rules all
require disclosure and all forbid an AI author. The repo mentioned none of it.

Load-bearing invariant, made mechanical as B4:

> **Stage 7 removes the AI accent. It must never remove the AI disclosure.**

`stages.7_language_dehumanize = done` without a Stage-7 ledger row — or without
the ledger file at all — is a hard failure. Eight blocking rules in total (B1–B8)
covering AI-as-author (both the policy field and the manuscript's own `\author`
line), AI-generated data and result images as fabrication, unverified AI-written
code and AI-screened literature, ledger↔statement disagreement in both
directions, `--final` placeholder and accountability strictness, and
AI-suggested citations that never resolved.

Ships as: `references/ai-use-disclosure.md`, `templates/ai_use_disclosure.md`
(instantiated by `init_workspace.sh`), `scripts/check_ai_disclosure.py`, a new
`workflow_state.json.ai_disclosure` block, and ordering in
`check_workspace_gates.py` — Stage 9 precondition, `submission` scope
requirement, and a prerequisite for both `replication_pack` readiness and
`orchestration.ethics_gate`, a field that until now nothing enforced.

Wired into the places a run actually reads: playbook Stage 7 and Stage 9,
`templates/submission_checklist.md`, quality-rubric dimension ⑦ (as capping
rules, not an eighth dimension — the 7-dimension contract holds), and the
worked example, where the trace shows B4 firing on first run because the
parallel Stage 7 subagent wrote the de-AIGC draft and never touched the ledger.

### 2. Two missing design families (12 → 14 gate cards)

The card set covered observational econometrics thoroughly and randomised
designs not at all, despite 社科实证 routinely meaning exactly that.

- **RCT / 田野实验**: randomisation protocol, balance with a joint test,
  *ex-ante* MDE (post-hoc power is a monotone transform of the effect size and
  carries no information), CONSORT-style flow N, differential attrition with
  bounds, ITT before LATE, pre-registered primary outcome, clustering at the
  randomisation level, spillover.
- **调查实验 / Conjoint / Vignette / List**: the risks distinctive to the form —
  sample provenance, *pre-registered* exclusion rules (post-hoc attention-check
  screening is the p-hacking channel here), AMCE profile distributions, and the
  stated-to-behavioural extrapolation that forces a claim downgrade.

### 3. `scripts/pw.py` — stage-aware front door (gate #37)

36 checkers is the point, but "which does Stage 7 owe, with which flags?" lived
in prose, so the orchestrator could skip a gate by not remembering it — the
failure mode these gates exist to prevent. `pw enter/exit/check/final/plan/list`
runs a stage → gate table.

Because the map is data, it is checkable, and its selftest enforces the converse:
**no run-time checker may sit outside the stage flow.** It caught two of my own
omissions during this wave (`check_defense_deck.py`, `make_three_line_tables.py`)
before either could ship registered-but-never-run.

### 4. Chaos coverage doubled, and made to mean something

`_scenario_present()` only asked whether the file existed; the selftest proved
the point by writing `# placeholder` into every scenario and asserting full
coverage. Scenarios now require five sections, a length floor, and an explicit
*"the recovery is considered failed if"* clause — a recovery contract that never
says what counts as failing it is a description, not a contract.

The three existing scenarios were all about the agent runtime. Added the three
about the research process: `gate_deadlock` (an unsatisfiable gate plus an
unattended run), `backend_unavailable` (Stage 0 picks Stata, Stage 3 discovers
the machine disagrees, and the danger is the *silent substitution*, not the
crash), `state_artifact_drift` (`workflow_state.json` is a description of the
workspace, not the workspace — recovery is demote-don't-delete, `pending` not
`not_pass`, because work that was done and then lost is a different fact from
work that failed).

## Part 2 — what execution found

### 5. The defence deck dropped its conclusions (`defense_pptx.py`)

The playbook calls the Stage 9 答辩 PPT a **hard deliverable** — "不能因脚本报错
就跳过答辩 PPT" — which made it the largest load-bearing artifact in a package
about executable rigor with no gate behind it.

Both templates rationed a fixed slide budget in first-come order
(`if page < total - 1`), and findings is the only variable-length section. With
six findings the thesis deck jumped from robustness straight to the thank-you
slide: **no 机制分析, no 研究结论与主要贡献, no 研究局限与未来展望** — the three
slides a committee is guaranteed to ask about. Journal-talk was worse: five
findings dropped both Robustness and Contribution. Exit code 0 either way.

The priority was backwards. A findings list can be merged; a conclusion cannot
be omitted. `_findings_budget()` reserves the mandatory sections first, gives
findings the remainder (never fewer than one), and reports what it dropped.
Second bug found the same way: `total_slides` ignored `duration_min`, so the
natural remedy — run it longer — did nothing, and the hint suggesting it would
have been a lie. Anchored so 15 minutes still yields exactly the documented
22/18.

`scripts/check_defense_deck.py` (gate #38) builds real decks from a real
workspace and asserts the conclusion comes *after* the findings rather than
merely existing somewhere. Reverting the fix fails it with the three section
names. `python-pptx` was an undeclared dependency of a documented hard
deliverable; it is now in `requirements-dev.txt`.

### 6. The Chinese ledger that could not pass

Stress-testing the new gate against a document written the way this repo's users
write produced four blocking findings on a *correct* ledger — three "missing
required section" plus a B4 claiming Stage 7 had not disclosed itself, two lines
above where it had.

That is worse than a missing gate: a gate that blocks correct work teaches
people to switch the gate off. Both vocabularies are now accepted and
normalised, with `GOOD_CN` as a golden fixture plus three negative cases proving
the rules still bite through Chinese (B1 via 是, B3 via 未核验, B4 via a removed
row) — a translation layer that also disabled enforcement would be the worse bug.

Same commit fixed a real evasion: `parse_ledger` silently skipped rows with
fewer than seven columns, so a malformed Stage-7 row satisfied B4 *by
disappearing*.

### 7. The package was committing the anti-pattern it polices

SKILL.md warns that two orchestrated child skills "硬编码了仓库外输出路径".
`build_paper_workflow_intro.py` did exactly that — absolute paths into the
*parent* repository under one developer's home directory, so running it on this
machine silently wrote a .pptx into a sibling checkout instead of the
`社媒文件/7.5-测试案例/` directory this repo ships.

Fixed to resolve from `__file__`, plus `check_cross_references.py` invariant 8:
no `.py`/`.sh` may hard-code a path under /Users, /home or a drive letter.
`/tmp` is runtime scratch and is not flagged; prose may quote the anti-pattern
since only executables are scanned; genuine needs waive in line with
`# pw-abs-path-ok: <reason>`, which is reviewable rather than invisible.

### 8. A checker is one because it verifies itself, not because of its name

Both discovery paths matched the prefixes `check_` / `score_` / `validate_`.
`make_three_line_tables.py` ships a full selftest covering border rewriting,
content preservation, idempotence and partial-write safety. It passes. Nothing
had ever run it. Discovery now also matches any script declaring `--selftest`.

### 9. Documented commands must actually parse (invariant 9)

Invariant 1 checked that a documented `python3 scripts/X.py` names a real
script. Nothing checked the rest of the line, across 113 documented flags.
Invariant 9 reads each script's own `--help` and verifies every long flag
exists. Building it surfaced the last defect: `validate_skill.py` had no
argument parser, so `--help` ran the entire battery and a typo'd flag was
ignored — in the one command every contributor is told to run before shipping.

## Complexity ledger

SKILL.md **32244 → 31931 bytes**, back under the 32000-byte always-loaded
target, while gaining the disclosure wiring. Paid for by deduplicating the
double-gate blockquote, Method Gate items 0/3/5/7/8, the quality-gate rollback
map, the claim-integrity paragraph and the demo-materials footer against the
references that already own them. The reference count is the only ceiling that
moved (32 → 33, `--update-baseline` with the reason recorded).

## Validation

```bash
python3 validate_skill.py          # green on 3.11, 3.12 and 3.13
python3 scripts/pw.py list         # 39/39 registered; no orphaned run-time gate
```

CI now runs a 3.11/3.12/3.13 matrix, the two new selftests, and one step that
puts a workspace built by the real `init_workspace.sh` through the real gate
runner — the only step that exercises the user-facing path end to end rather
than a fixture.

## What the next wave should look at

- ~~The reference corpus needs a consolidation pass.~~ **Checked, and it does
  not.** `check_compactness.py` gained a cross-file near-duplicate paragraph
  scan (token-shingle Jaccard) precisely so this question stops being a worry
  and starts being a number. The answer for 591 KB across 33 files: **zero**
  cross-file near-duplicates above 0.45, once the two intentional
  `cn-data-claims` banners are exempted. The corpus is large because the subject
  is large, not because the same paragraph lives in three files. The ratchet's
  "+80 KB this wave" warning was measuring new material, and now says so.
  Re-run the scan before assuming otherwise next time.
- `check_defense_deck.py` verifies the shipped *generator*, not a user's
  workspace. A `--workspace` mode would make the playbook's Stage 9 hard
  requirement enforceable per run, but only if it can tell a thesis run from a
  journal submission without guessing.
- Six chaos scenarios are all still marked *"based on inference, refine on first
  real failure."* That label is honest and should stay until a real failure
  replaces one.
