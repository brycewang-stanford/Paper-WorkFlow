# SkillOpt Improvement Packet

Worked instance of the improvement loop, produced from measured eval scores.
Validate with:

```bash
python3 scripts/check_skillopt_packet.py evals/packets/2026-06-21-time-series-gate-card.md
```

## Candidate

- Target skill files: references/design-gate-cards.md
- Source SkillOpt snapshot: https://github.com/microsoft/SkillOpt main branch, methodology reference, not vendored
- Change scope: add a Time Series / VAR Design Gate Card so the documented 67/time-series routing has reviewer-facing evidence gates
- Edit budget L: 2
- Protected areas: SKILL.md, README.md, README.en.md, validate_skill.py and the SkillOpt-loop trio (references/skillopt-improvement-loop.md, scripts/check_skillopt_packet.py, templates/SKILLOPT_PACKET.md) are owned by a parallel agent and were not touched

## Rollout Split

### Train rollouts

- [x] train-001 | status=success | score=1.00 | evidence=evals/scenarios.json#did_staggered | note=DiD routing and gate card documented
- [x] train-002 | status=success | score=1.00 | evidence=evals/scenarios.json#iv_2sls | note=IV routing and gate card documented
- [x] train-003 | status=success | score=1.00 | evidence=evals/scenarios.json#rdd_sharp | note=RDD routing and gate card documented
- [x] train-004 | status=success | score=1.00 | evidence=evals/scenarios.json#synthetic_control | note=synthetic-control routing and gate card documented

### Held-out selection rollouts

- [x] select-001 | status=success | score=1.00 | evidence=evals/scenarios.json#panel_fe | note=baseline already passing
- [x] select-002 | status=success | score=1.00 | evidence=evals/scenarios.json#ml_hte | note=baseline already passing
- [x] select-003 | status=failure | score=0.90 | evidence=evals/scenarios.json#time_series_var | note=baseline miss, time-series routing had no Design Gate Card

## Reflection

### Failure patterns

- A documented Stage-3 routing target (67/time-series) lacked a matching Design Gate Card, so a time-series paper could reach the Method Gate without a design-specific evidence checklist. This is general: every routed design label should have a peer gate card, or the gate is unenforceable for that branch.

### Success patterns

- The eight causal-identification designs each pair a routing entry with a gate card; the gate self-test and smoke test pass. The mechanical eval harness caught the single mismatch on a held-out scenario rather than on the inspiring example.

## Proposed Bounded Patch

- [x] edit_1 | op=insert_after | target=references/design-gate-cards.md after section 8 Prediction-Assisted | rationale=add a Time Series / VAR / cointegration gate card (unit-root, lag selection, cointegration, stability, residual diagnostics, shock identification, ordering sensitivity, structural-break, IRF inference) mirroring the existing card format
- [x] edit_2 | op=replace | target=references/design-gate-cards.md Method Gate canonical design list | rationale=add Time Series-VAR so method_gate.md recognizes the new card

## Gate Decision

- Baseline selection score: 0.967
- Candidate selection score: 1.000
- Gate decision: accept
- Regression check: pass
- Selection rubric: routing fidelity, gate integrity, context protection, reproducibility, user burden, each in 0.0-1.0, averaged per scenario (see evals/README.md)

## Adoption Record

- Accepted files: references/design-gate-cards.md
- Rejected edit memory: none. The fix is a real coverage gap, not an overfit; no edit was declined this cycle.
- Validation commands: python3 evals/score_skill.py selection mean 0.967 then 1.000 and regression mean 1.000 unchanged; python3 scripts/check_skillopt_packet.py on this packet pass; validate_skill.py required markers for design-gate-cards.md preserved
- Follow-up: if structural-macro SVAR work becomes common, consider a dedicated identification sub-card; otherwise the time-series branch is now gated
