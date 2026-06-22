# Orchestration & Handoff — 编排、路由与断点交接

This reference translates the useful engineering patterns from full research
skill suites into Paper-WorkFlow's empirical-paper contract. It does not lower
the method gate; it makes stage routing and continuation auditable.

## Entry Routing

Stage 0 must write `00_meta/entry_routing.md` before executing a later stage.
The route decision records what the user brought, which stage is safe to enter,
which assumptions were inferred, and which decisions remain human-owned.

Use the route file to separate similar requests:

| Request shape | Route |
|---|---|
| "Continue / pick up / another agent stopped" | Recovery probe first, then the first incomplete stage |
| "Write or polish this paragraph" | Stage 5/6/7 only; do not start the full pipeline |
| "From idea/data to submission" | Full Stage 0-9 pipeline |
| "I already have results" | Stage 5 only after Method Gate evidence exists |
| "Submit this completed draft" | Stage 9 after citation, data-governance, and policy refresh |

## Stage Passport

`00_meta/stage_passport.md` is the human-readable stage ledger. It complements
`workflow_state.json`; it is not a replacement. Update both at each stage
boundary.

Each completed stage needs:

- input accepted from the previous stage;
- output artifact paths;
- gate result and evidence;
- revision rounds used;
- known limitations or open gaps.

If the passport and `workflow_state.json` disagree, treat that as a recovery
problem and refresh current evidence before proceeding.

## Fresh Evidence

Do not declare a stage done from memory. A current proof must exist in one of
these forms:

- command output with exit status;
- `scripts/check_workspace_gates.py` report;
- a gate report or scorecard written in the workspace;
- a file diff or generated artifact;
- an explicit user decision recorded in `workflow_state.json.decisions`.

Old handoff notes are pointers, not proof. On recovery, refresh `git status`,
`workflow_state.json`, the stage passport, and the current stage artifact.

## Handoff Card

Use `00_meta/handoff/` for handoff cards whenever a long run pauses, a stage
switches, context is getting thin, or another agent takes over. A card must say:

- current stage;
- completed artifacts and how they were verified;
- worktree state;
- next smallest action;
- blocking risks;
- files the next agent must read;
- explicit "Do Not" boundaries.

The latest card path should be written to
`workflow_state.json.orchestration.latest_handoff`. If that field is set, the
runtime checker verifies the file exists.

## Runtime Discipline

- `orchestration.fresh_evidence_required` stays `true`.
- `orchestration.revision_rounds_cap` defaults to `2`; do not reset it after a
  handoff.
- `orchestration.self_review_gate` and `orchestration.ethics_gate` record whether
  the current stage had a fresh self-review and research-integrity pass.
- Any fallback or unavailable probe goes into `logs/stage_<N>.md` and
  `workflow_state.json.decisions`.

## schema_version 9

Schema v9 adds the `orchestration` block plus the Stage 0 artifacts:

- `00_meta/entry_routing.md`
- `00_meta/stage_passport.md`
- `00_meta/handoff/`
- `00_meta/handoff_prompt.md`

These files are created by `assets/init_workspace.sh`, exercised by
`scripts/smoke_workspace.py`, and checked by `validate_skill.py`.
