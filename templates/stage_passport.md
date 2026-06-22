# Stage Passport

Project: <short name>
Created at (Beijing): <YYYY-MM-DD HH:MM>
Updated at (Beijing): <YYYY-MM-DD HH:MM>
Current stage: <0-9>

This file is the human-readable companion to `00_meta/workflow_state.json`.
Update it at every stage boundary; do not rely on chat history for resumability.

## Stage Ledger

| Stage | Status | Input accepted | Output artifacts | Gate result | Revision rounds | Fresh Evidence |
|---:|---|---|---|---|---:|---|
| 0 | pending |  | `00_meta/workflow_state.json` |  | 0 |  |
| 1 | pending |  | `01_proposal/proposal.md` |  | 0 |  |
| 2 | pending |  | `02_data/sample_audit.md` |  | 0 |  |
| 3 | pending |  | `03_analysis/method_gate.md` |  | 0 |  |
| 4 | pending |  | `04_results/` |  | 0 |  |
| 5 | pending |  | `05_draft/main.tex` |  | 0 |  |
| 6 | pending |  | `06_polish/main.tex` |  | 0 |  |
| 7 | pending |  | `07_dehumanize/main.tex` |  | 0 |  |
| 8 | pending |  | `08_review/response_letter.md` |  | 0 |  |
| 9 | pending |  | `09_submission/` |  | 0 |  |

## Fresh Evidence

For every `done` stage, cite one current proof: command output, tool report,
gate checker, file diff, rendered artifact, or explicit user decision.

- Latest recovery probe:
- Latest gate checker:
- Latest rebuild check:

## Revision Budget

The default cap is two whole-stage repair rounds for a blocking confirmation
point. Do not reset this count after a handoff or new conversation.

- Rounds used:
- Remaining:
- Known limitations converted from unresolved critical items:

## Known Limitations

-
