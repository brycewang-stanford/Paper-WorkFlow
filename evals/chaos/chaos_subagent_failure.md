# Chaos scenario: Subagent crashes or hangs mid-task

## What this scenario exercises

The orchestrator's context-protection protocol mandates that every
subagent "writes to disk and returns a ≤10-line summary". The summary
contract is the only window into what happened in the subagent. When
the subagent crashes before writing its summary, or when it hangs past
a reasonable timeout, the orchestrator must recover without
re-spawning the subagent blindly.

This is a real failure mode because Claude Code's subagent runtime can
hit a number of failure modes the orchestrator has no visibility into:
out-of-context limits, tool permission errors, the subagent
misinterpreting its brief, MCP server timeouts, the subagent writing
to the wrong path. The orchestrator's recovery path is the only line
of defence.

## The trigger

A Stage-3 subagent was launched with the brief
`/prompts/stage3_aipw.md`, running the AIPW estimator for the
treatment effect. The subagent emits no summary line within 600
seconds, and the orchestrator's process-monitoring hook notes that
the subagent process is no longer writing to its scratch file
(`/tmp/subagent_<id>.out`).

## Expected recovery path

The orchestrator must:

1. Re-read the workflow_state.json for the stage and the subagent
   task description. Determine the subagent's input files (analysis
   script template, design_register.md, method_gate.md) and output
   files (the AIPW .csv estimates, the chunked summary file).
2. Check whether the output files exist and are non-empty. If yes,
   the subagent wrote the bulk of the work before crashing — treat the
   crash as benign, harvest the outputs, and proceed.
3. If output files are missing or empty, retry the subagent **once**
   with the same brief but a short, explicit instruction at the top:
   "Previous subagent crashed without writing its summary file.
   Write all artifacts to the listed paths and end with a ≤10-line
   status summary. If you cannot, write a single line with the reason
   and exit."
4. After the second attempt, regardless of outcome, write a
   `00_meta/handoff/subagent_recovery_<N>.md` card summarising what
   was retried, what survived, and what the operator needs to do by
   hand.
5. Update `workflow_state.json.empirical_audit` (or the appropriate
   sub-status) to `pending` so the method-gate cannot pass on
   unverified evidence.

The recovery is considered failed if any of the following hold:

- the orchestrator retries the subagent more than once without a
  human handoff card in between (a sign of infinite retry loops);
- the orchestrator's per-stage log file does not record the crash and
  the recovery attempt;
- output files are claimed as "recovered" but the on-disk content is
  empty or zero-byte.

## How a maintainer verifies this scenario

After a forced timeout (e.g. by injecting a `sleep 999` into the
AIPW subagent script), the orchestrator's per-stage log should
contain the timeout detection and a single retry. If a manual review
finds the subagent retried three or more times, the recovery path is
broken.

## Status

**Based on inference, refine on first real failure.** The
context-protection protocol is documented in `SKILL.md` but the
specific subagent-recovery protocol (single retry, handoff card on
second failure) has not been exercised end-to-end.
