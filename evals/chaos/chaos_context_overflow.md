# Chaos scenario: Context budget exhausted mid-Stage-3

## What this scenario exercises

The orchestrator's instructions are explicit that the main agent's
context is "the most scarce resource" and that heavy reads, long
literature scans, and full-dataset computations must be delegated to
subagents. In practice, however, the main agent may absorb a long
running log, a verbose `analysis_backend.md` history, or a chain of
skill-map cross-references during Stage 3 (estimation) and approach
its context budget before the method gate completes.

This is **the** failure mode for which the subagent delegation
contract exists, but the contract has never been exercised as a
chaos test. A real failure looks like: the model emits a "context
length exceeded" or quietly truncates its last response, leaving the
main agent with a partial method_gate.md and a confused gate
verifier.

## The trigger

During Stage 3, the main agent has accumulated the following in its
own context: the full SKILL.md (32 KB), the stage-playbook chapter
for Stage 3 (≈ 12 KB), the user's proposal.md (≈ 25 KB), the full
methods ledger from prior stages (≈ 18 KB), and several rounds of
output from subagents that were not strictly "≤10 lines" because the
subagent emitted long table excerpts instead of pointers. Approximate
context pressure: > 75 % of the model's effective window.

The next subagent call is interrupted by the runtime with a
"context_length_exceeded` error.

## Expected recovery path

The orchestrator must:

1. Stop emitting long blocks into the main context. From now on,
   every subagent must use the strict ≤10-line summary contract;
   larger outputs go to disk under `00_meta/`.
2. Re-read `workflow_state.json.orchestration.latest_handoff` and
   determine the last stage that was marked `done`. Resume from
   exactly the next stage, not from the top of Stage 0.
3. Compress the in-context information: discard the methods ledger
   from the main context, replace long paths with a single
   `Read references/orchestration-and-handoff.md#fresh-evidence` lookup.
4. Resume Stage 3 with a subagent that re-reads the design register
   and method gate; the main agent only carries pointers.
5. After recovery, write a handoff card noting the context overflow
   and the recovery steps, so the next agent can avoid re-loading
   the same content.

The recovery is considered failed if any of the following hold:

- the orchestrator resumes Stage 0 from the top (a sign of losing
  the workflow_state.json pointer);
- the orchestrator retries the heavy subagent in the main context
  rather than re-dispatching it (a sign of forgetting the
  context-protection contract);
- `00_meta/workflow_state.json` is missing or stale after the
  recovery (a sign of state corruption).

## How a maintainer verifies this scenario

Force a near-full context by injecting a dummy 200 KB of noise into
the main agent's prior turn (e.g. via a `Read` of a large file
that the orchestrator is forced to absorb). On the next subagent
call, the recovery path should fire and the workflow_state.json
should remain consistent. If a maintainer finds the orchestrator
restarting from Stage 0, the recovery is broken.

## Status

**Based on inference, refine on first real failure.** The
context-protection protocol is documented in `SKILL.md` and
`references/orchestration-and-handoff.md`, but the
context-overflow-specific recovery branch is not currently exercised.
