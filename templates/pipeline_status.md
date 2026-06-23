# Pipeline Status

Project: <short name>
Updated at (Beijing): <YYYY-MM-DD HH:MM>
Owner: main orchestrator

Purpose: give humans and follow-on agents a compact, current dashboard without
requiring them to reread chat history or every stage log.

## 1. Stage Dashboard

| Stage | Status | Mode | Key outputs | Gate / checkpoint | Next action |
|---:|---|---|---|---|---|
| 0 | pending |  | `00_meta/workflow_state.json` | route pending | fill intake |
| 1 | pending |  | `01_proposal/proposal.md` | topic/design checkpoint |  |
| 2 | pending |  | `02_data/sample_audit.md` | sample audit checkpoint |  |
| 3 | pending |  | `03_analysis/method_gate.md` | Method Gate |  |
| 4 | pending |  | `04_results/` | exhibit reconciliation |  |
| 5 | pending |  | `05_draft/main.tex` | draft checkpoint |  |
| 6 | pending |  | `06_polish/main.tex` | polish checkpoint |  |
| 7 | pending |  | `07_dehumanize/main.tex` | Draft Quality Gate + claim integrity audit |  |
| 8 | pending |  | `08_review/response_letter.md` | revision checkpoint |  |
| 9 | pending |  | `09_submission/` | final integrity + submission checklist |  |

## 2. Materials

| Material | Path | Available? | Last verified |
|---|---|---:|---|
| Entry routing | `00_meta/entry_routing.md` | no |  |
| Stage passport | `00_meta/stage_passport.md` | no |  |
| Latest handoff | `00_meta/handoff/` | no |  |
| Evidence ledger | `00_meta/evidence_ledger.md` | no |  |
| Claim integrity audit | `00_meta/claim_integrity_audit.md` | no |  |
| Citation integrity log | `00_meta/citation_integrity_log.md` | no |  |
| Method gate | `03_analysis/method_gate.md` | no |  |
| Quality scorecard | `00_meta/quality_scorecard.md` | no |  |
| Replication README | `REPLICATION.md` | no |  |

## 3. Checkpoint Policy

- FULL checkpoint: first checkpoint, hard gates, after any recovery, and before submission.
- SLIM checkpoint: allowed only after repeated user "continue" decisions on non-hard gates.
- MANDATORY checkpoint: Method Gate failure, Draft Quality Gate failure, final integrity failure, review decision, and submission package handoff.
- Reset Boundary: when a long session or context handoff is needed, write a handoff card and update `workflow_state.json.orchestration.reset_boundaries`.

## 4. Open Flags

| Flag | Source | Blocking? | Owner | Resolution |
|---|---|---:|---|---|
| <flag> | <file/check> | yes / no | <owner> | <action> |

## 5. One-Line Status

Pipeline: [ ]0 -> [ ]1 -> [ ]2 -> [ ]3 -> [ ]4 -> [ ]5 -> [ ]6 -> [ ]7 -> [ ]8 -> [ ]9

