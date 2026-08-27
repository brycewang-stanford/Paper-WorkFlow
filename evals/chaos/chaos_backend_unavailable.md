# Chaos scenario: the chosen analysis backend is not installed

## What this scenario exercises

Stage 0 asks the user to pick an analysis backend — `python-statspai`, `stata`,
or `r` — and records it in `workflow_state.json.analysis_backend.primary`. That
decision is taken *before* any code runs, often on the basis of what the user is
used to rather than what the machine has. Stata in particular is licensed, and
"I use Stata" and "Stata is installed and on PATH in this environment" are
different claims.

The failure surfaces at Stage 3, several stages after the decision, when the
first `.do` file is executed and there is no `stata` binary. The dangerous
response is not the crash. It is the quiet substitution: silently switching to
Python, producing plausible numbers, and leaving `analysis_backend.primary:
"stata"` in the state file — so the replication package tells a reader to run
something that never ran.

## The trigger

At Stage 3, with `analysis_backend.primary = "stata"`:

```
$ stata-mp -b do 03_analysis/main.do
bash: stata-mp: command not found
```

Equivalently: `r` chosen and `fixest` unavailable; `python-statspai` chosen and
the StatsPAI MCP server failing to connect; any backend chosen and the export
stack (`docx`/`xlsx` writers) missing at Stage 4.

## Expected recovery path

Per `references/runtime-fallbacks.md` and `references/analysis-backends.md`:

1. **Probe before executing, not after.** The capability report
   `00_meta/backend_capabilities.json` exists precisely so this is discovered at
   the *start* of Stage 3. `python3 scripts/check_backend_capabilities.py
   <workspace>` is a Stage 3 exit gate; the probe belongs at the entry.
2. **Record the unavailability as structured status**, not prose: which runtime,
   which missing dependency, the probe timestamp, and the fallback selected.
3. **Fall back explicitly and visibly.** Switch `analysis_backend.primary` to
   the available backend, set `secondary_validation` to record what could not be
   run, and append to `workflow_state.json.decisions` a line naming the original
   choice, the reason it failed, and who (or what) decided the substitution.
4. **Do not claim parity you did not measure.** `00_meta/backend_parity.json`
   may only report agreement between two backends that *both actually ran*. A
   fallback with no parity check is a fallback with `parity: not_checked`, and
   `check_backend_parity.py` refuses to let an unmeasured claim pass.
5. **Propagate the consequence to the gates.** Per `runtime-fallbacks.md`, a
   degradation that touches the design's minimum-evidence pack or the
   reproducibility of the results lowers the gate status — it does not leave it
   untouched. `check_runtime_fallbacks.py` enforces that a blocked or
   non-parity fallback cannot sit under a passing Method Gate or a `ready`
   replication pack.
6. **Fix the replication package to match reality.** `REPLICATION.md` and
   `run_all.sh` describe what a replicator must install to reproduce *these*
   numbers. If the run happened in Python, the instructions say Python.

The recovery is considered failed if any of the following hold:

- results appear from a backend that the state file does not name;
- `analysis_backend.primary` still names the unavailable backend after delivery;
- `backend_parity.json` claims agreement between a backend that ran and one that
  could not;
- the substitution appears nowhere in `decisions` or `logs/stage_3.md`;
- the tool's absence is described in the manuscript as a robustness choice.

## How a maintainer verifies this scenario

`00_meta/backend_capabilities.json` after the probe:

```json
{"status": "degraded", "probed_at": "2026-08-27T10:04:00+08:00",
 "backends": {"stata": {"available": false, "missing": ["stata binary not on PATH"]},
              "python-statspai": {"available": true, "version": "..."}},
 "fallback_backend": "python-statspai"}
```

and `decisions` carrying the matching line. Then:

```bash
python3 scripts/pw.py exit 3 <workspace>
```

`check_backend_capabilities.py`, `check_backend_parity.py` and
`check_runtime_fallbacks.py` all run at Stage 3; a workspace that substituted
silently fails at least one of them.

## Status

**Based on inference, refine on first real failure.** The capability report, the
parity contract and the fallback-honesty gate are implemented and enforced. What
is inferred is the *ordering* recommendation in step 1 — probing at Stage 3
entry rather than discovering the gap at the exit gate. A real occurrence should
record how much work was lost between the two points.
