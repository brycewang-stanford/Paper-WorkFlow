# Chaos scenario: a gate that can never pass, in 全自动 mode

## What this scenario exercises

The pipeline has two hard gates (Method Gate, Draft Quality Gate) and both
prescribe the same response to failure: **go back and redo the upstream stage.**
That is correct when the shortfall is fixable. It is a trap when it is not.

The un-fixable cases are real and common:

- the parallel-trends assumption is violated and the data admit no alternative
  comparison group — no amount of re-running Stage 3 creates one;
- the first stage is weak because the instrument genuinely is weak;
- the quality rubric's "contribution sharpness" dimension scores 5 because the
  paper's contribution *is* thin, and Stage 1 has no better idea to offer.

In `阶段确认` or `全程交互` a human sees the second failure and intervenes. In
`全自动` nobody does. Without a bound, the orchestrator re-runs Stage 3, fails
the Method Gate, re-runs Stage 3, forever — burning the entire budget on a
question that was answered on the first attempt.

## The trigger

`workflow_state.json`:

```json
{"project": {"mode": "auto", "scope": "submission"},
 "orchestration": {"method_gate_rounds": 2, "method_gate_rounds_cap": 2,
                   "budget_exhausted_action": "deliver-with-known-gaps"},
 "method_gate": {"status": "not_pass",
                 "missing_artifacts": ["pre-trend passes at conventional levels"]}}
```

Stage 3 has now failed the Method Gate twice for the same reason. The naive
next action — a third attempt — is the failure.

## Expected recovery path

Per SKILL.md (关键约束 · 绝不让回退无界) and
`references/orchestration-and-handoff.md` §schema_version 12 ④:

1. **Stop retrying.** `method_gate_rounds >= method_gate_rounds_cap` is a
   terminal condition, not a suggestion. The same bound governs
   `revision_rounds_cap` on the Draft Quality Gate side; the two counters are
   independent, so exhausting one does not license spending the other on the
   same defect.
2. **Apply `budget_exhausted_action`.** Default `deliver-with-known-gaps`:
   assemble what exists, and record the unresolved gate as a **known gap**, not
   as a pass.
3. **Do not launder the failure into the state file.** `method_gate.status`
   stays `not_pass`. `evidence_governance.claim_strength` drops to the level the
   surviving evidence actually supports (usually `descriptive`), and
   `00_meta/evidence_ledger.md` is rewritten so no manuscript claim exceeds it.
   `check_workspace_gates.py` will catch a `quality_gate=pass` sitting on top of
   `method_gate=not_pass`, so the temptation is mechanically foreclosed.
4. **Escalate visibly.** The stage summary card marks the gap in red and states
   plainly what failed, how many attempts were spent, and what a human would
   have to decide (submit with the limitation disclosed, change the design, or
   abandon). In `全自动` this is the report; the human reads it afterwards.
5. **Write the handoff.** `00_meta/handoff/` records the terminal state so a
   resumed session does not restart the loop from zero.

The recovery is considered failed if any of the following hold:

- a third Method Gate attempt runs for the same unresolved item;
- `method_gate.status` is flipped to `pass` or `pass_with_notes` without the
  missing artifact appearing on disk;
- the gate is "satisfied" by deleting the failing check from
  `required_artifacts` rather than by producing the evidence;
- `FINAL_REPORT.md` ships without the gap in Residual Risks;
- the round counters are reset to 0 to buy more attempts.

## How a maintainer verifies this scenario

Read `logs/quality_gate.md` and `logs/stage_3.md` after a capped run. The
attempt count must be visible and must stop at the cap:

```
round 1: method_gate NOT PASS — pre-trend fails at 5% in 3 of 4 leads
round 2: method_gate NOT PASS — same, after re-windowing and donut
CAP REACHED (method_gate_rounds_cap=2) -> budget_exhausted_action=deliver-with-known-gaps
  claim_strength: causal -> descriptive; evidence ledger rewritten
  Residual Risk recorded in FINAL_REPORT.md
```

Mechanically: `python3 scripts/pw.py check <workspace>` must still report the
Method Gate as failing after delivery. A run that ends green here has laundered
the failure and this scenario has not been honoured.

## Status

**Based on inference, refine on first real failure.** The caps, the exhaustion
action and the ordering constraint are all implemented and gate-enforced; what
is inferred is the *shape of the escalation report* a capped run should produce.
A real capped run should replace this section's example log with the real one.
