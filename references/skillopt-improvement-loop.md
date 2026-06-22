# SkillOpt-style improvement loop

> Load this reference only when maintaining or improving this skill package.
> It adapts the SkillOpt discipline (rollout -> reflect -> bounded patch ->
> held-out selection gate) to `Paper-WorkFlow` without vendoring the SkillOpt
> runtime.

## Why this exists

`Paper-WorkFlow` is itself a skill document plus bundled resources. Treat changes
to it as training updates: useful edits should come from observed trajectories,
be small enough to inspect, and pass a held-out gate before adoption.

This reference is for maintainers, not for ordinary paper runs. Ordinary users
should not see a maintenance prompt during Stage 0-9 execution.

## Loop

1. **Rollout**: collect real or replayed task traces where the skill was used.
   Include both successful and failed cases. Store links to raw transcripts,
   workspaces, logs, validation output, or reviewer feedback.
2. **Split**: separate evidence into a train set and a held-out selection set.
   Do not score a proposed edit only on the examples that inspired it.
3. **Reflect**: summarize common failure patterns and success patterns. Prefer
   general procedural rules over task-specific patches.
4. **Bounded patch**: propose at most `L` edits. Use add / insert_after /
   replace / delete operations and state the exact target files.
5. **Gate**: compare baseline and candidate behavior on held-out selection
   cases. Accept only if the candidate improves the selected score and passes
   regression checks.
6. **Adopt**: apply accepted edits, run local checks, and record what changed.
   Rejected edits become negative evidence for later maintenance.

## Scoring dimensions

For this skill, use a mixed gate rather than a single accuracy number:

| Dimension | What to score |
|---|---|
| Routing fidelity | Correct entry stage, child skill path, and backend choice |
| Context protection | Subagents write outputs to disk and return concise summaries |
| Gate integrity | Method Gate / Draft Quality Gate cannot pass without evidence |
| Reproducibility | Workspace state, templates, scripts, and rebuild path stay coherent |
| User burden | The workflow asks only necessary questions and respects autonomy mode |

Keep scoring coarse but explicit, for example `0.0-1.0` or `0-10`. The same
rubric must be used for baseline and candidate scores inside one packet.

## Packet requirements

Every non-trivial maintenance change should create a filled copy of
[`templates/SKILLOPT_PACKET.md`](../templates/SKILLOPT_PACKET.md), then validate
it with:

```bash
python3 scripts/check_skillopt_packet.py path/to/SKILLOPT_PACKET.md
```

The checker enforces:

- at least three train rollouts and two held-out selection rollouts;
- an explicit edit budget `L`;
- proposed edit count no larger than `L`;
- accept decisions require `candidate_score > baseline_score`;
- accept decisions require `Regression check: pass`;
- placeholders must be removed before the packet can pass.

Use `python3 scripts/check_skillopt_packet.py --selftest` when changing the
checker itself.

## Adoption rules

- Do not accept train-only improvements.
- Do not accept broad rewrites when a bounded patch fixes the observed failure.
- Do not duplicate existing guidance; replace stale or misleading guidance.
- Keep `SKILL.md` lean. Move detailed maintenance mechanics into references,
  templates, or scripts.
- If `SKILL.md` frontmatter changes, refresh the parent repository catalog from
  the parent checkout after the child repo is stable.
- If another agent is working in parallel, keep maintenance edits path-scoped
  and avoid parent catalog regeneration unless explicitly assigned.

## Rejected-edit memory

When an edit is rejected, record the failure mode in the packet's Adoption
Record. Rejected edits are useful negative evidence: they prevent the same
overfit rule from being proposed again after future runs.

