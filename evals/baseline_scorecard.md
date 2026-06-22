# Baseline scorecard

Latest measured: 2026-06-22 (Beijing) · generator: `python3 evals/score_skill.py`

This is the reference scorecard the SkillOpt-style improvement loop gates
against. Regenerate after any skill change and compare splits before adopting an
edit (selection mean must strictly rise; regression mean must not drop).

## Current scores (post adoption)

```text
scenario           split      routi gate_ conte repro user_ integ  total   status
---------------------------------------------------------------------------------
did_staggered      train       1.00  1.00  1.00  1.00  1.00  1.00   1.00  success
iv_2sls            train       1.00  1.00  1.00  1.00  1.00  1.00   1.00  success
rdd_sharp          train       1.00  1.00  1.00  1.00  1.00  1.00   1.00  success
synthetic_control  train       1.00  1.00  1.00  1.00  1.00  1.00   1.00  success
panel_fe           selection   1.00  1.00  1.00  1.00  1.00  1.00   1.00  success
ml_hte             selection   1.00  1.00  1.00  1.00  1.00  1.00   1.00  success
time_series_var    selection   1.00  1.00  1.00  1.00  1.00  1.00   1.00  success
dml_highdim        regression  1.00  1.00  1.00  1.00  1.00  1.00   1.00  success
causal_graph       regression  1.00  1.00  1.00  1.00  1.00  1.00   1.00  success

  train       mean = 1.000
  selection   mean = 1.000   <-- gate number
  regression  mean = 1.000
  overall     mean = 1.000
  gate self-test = pass   (scripts_run=True)

Dimension legend: routi=routing_fidelity, gate_=gate_integrity, conte=context_protection, repro=reproducibility, user_=user_burden, integ=integrity_checkpoint
```

All nine routed designs now pair documented routing with a Design Gate Card and
pass the gate self-test, smoke test, context/user-burden contracts, and the
claim-integrity checkpoint contract.

## Change log (the loop in action)

| Date | Selection mean | Regression mean | Edit | Packet |
|---|---|---|---|---|
| 2026-06-21 (initial) | 0.967 | 1.000 | — (baseline; harness landed) | — |
| 2026-06-21 (adopted) | **1.000** | 1.000 | add Time Series / VAR Design Gate Card | [packets/2026-06-21-time-series-gate-card.md](packets/2026-06-21-time-series-gate-card.md) |
| 2026-06-22 (adopted) | **1.000** | 1.000 | add integrity_checkpoint scorer dimension for claim-integrity gate preservation | — |

**Resolved finding.** The initial baseline surfaced a held-out miss:
`time_series_var` scored `0.90` because the skill routed time-series work to
`67/time-series` but had no matching Design Gate Card. The loop ran as designed —
the held-out selection split (not the inspiring example) caught it, a bounded
patch added the card to [../references/design-gate-cards.md](../references/design-gate-cards.md),
and the selection mean rose `0.967 → 1.000` with no regression. The gate
condition (candidate strictly beats baseline, regression holds) was met, so the
edit was accepted.

## How to reproduce

```bash
python3 evals/score_skill.py                       # full scored run (this table)
python3 evals/score_skill.py --packet-lines selection   # rollout lines for a packet
python3 evals/score_skill.py --selftest            # harness invariants
```
