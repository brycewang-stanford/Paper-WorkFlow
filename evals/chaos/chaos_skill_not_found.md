# Chaos scenario: Skill tool reports "skill not found"

## What this scenario exercises

The orchestrator is documented in `references/skill-map.md` §0 as calling
child skills via the `Skill` tool with the registered name from the child
skill's `SKILL.md` front-matter. The `Skill` tool is the fast path. When
the runtime does not have that skill registered — for example, the user
installed the repo as a single-skill bundle, or the runtime is a fresh
clone whose plugin manifest has not picked up the new skill — the `Skill`
tool returns "skill not found" and aborts.

This is **the** most common failure mode for `skills/69-Paper-WorkFlow/` in
practice, because the repo's install instructions explicitly support a
single-skill install at the repo root, and not every runtime does
recursive skill discovery.

## The trigger

During Stage 1, the orchestrator calls
`Skill(skill="Econfin-Proposal", args=...)`. The runtime replies:

```
Skill not found: no skill registered with name 'Econfin-Proposal'.
Available skills: auto-empirical-research-skills, paper-workflow, stats-pai, ...
```

## Expected recovery path

Per `references/skill-map.md` §0.2, the orchestrator must immediately
fall back to the steady-state path: read the child skill's
`SKILL.md` in the repository and execute its instructions inline. The
fallback must:

1. Acknowledge the failure in the per-stage log file
   (`logs/stage_<N>.md`) so a human reviewer can see what happened.
2. Read `skills/67-econfin-workflow-toolkit/econfin-proposal/SKILL.md`
   (or whichever folder contains the target child skill) and load its
   instructions into the current context.
3. Execute the child skill's steps inline. The orchestrator must NOT
   retry the `Skill` tool more than once on the same call — repeated
   retries are a sign of forgetting that the steady-state path is the
   intended fallback.
4. Record in `workflow_state.json.decisions` that the fallback path
   was used, so the gate checkers can flag it for later review.

The recovery is considered failed if any of the following hold:

- the orchestrator retries the `Skill` tool more than once on the same
  target without falling back to `Read` (a sign of cognitive fixation);
- the orchestrator fabricates the child skill's behavior from memory
  instead of `Read`-ing its `SKILL.md` (a sign of "脑补" — the exact
  anti-pattern warned against in `references/skill-map.md` §0.2);
- the per-stage log does not record the fallback.

## How a maintainer verifies this scenario

Read `logs/stage_<N>.md` after a recovery. The line should read
approximately:

```
2026-07-21T... Skill tool reported not-found for "Econfin-Proposal"; falling
  back to read-and-inline per skill-map.md §0.2; executing
  skills/67-econfin-workflow-toolkit/econfin-proposal/SKILL.md directly.
```

If a future maintainer introduces a new child skill without adding
the `Skill` vs. `Read` fallback to the stage playbook, the next run
of Stage 1 will fail at the missing skill and the per-stage log will
not show the fallback. That is the test.

## Status

**Based on inference, refine on first real failure.** The recovery path
is documented in `references/skill-map.md` §0.2 and was clearly the
design intent, but no automated test currently exercises it. This
scenario file is the contract for the test that should be added in
`scripts/check_chaos_coverage.py`.
