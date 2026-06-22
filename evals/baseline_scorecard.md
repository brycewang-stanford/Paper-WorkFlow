# Baseline scorecard

Captured: 2026-06-21 (Beijing) · generator: `python3 evals/score_skill.py`

This is the measured baseline the SkillOpt-style improvement loop gates against.
Regenerate after any skill change and compare splits before adopting an edit.

## Scores

```
scenario           split      routi gate_ conte repro user_  total   status
---------------------------------------------------------------------------
did_staggered      train       1.00  1.00  1.00  1.00  1.00   1.00  success
iv_2sls            train       1.00  1.00  1.00  1.00  1.00   1.00  success
rdd_sharp          train       1.00  1.00  1.00  1.00  1.00   1.00  success
synthetic_control  train       1.00  1.00  1.00  1.00  1.00   1.00  success
panel_fe           selection   1.00  1.00  1.00  1.00  1.00   1.00  success
ml_hte             selection   1.00  1.00  1.00  1.00  1.00   1.00  success
time_series_var    selection   1.00  0.50  1.00  1.00  1.00   0.90  success
dml_highdim        regression  1.00  1.00  1.00  1.00  1.00   1.00  success
causal_graph       regression  1.00  1.00  1.00  1.00  1.00   1.00  success

  train       mean = 1.000
  selection   mean = 0.967   <-- gate number
  regression  mean = 1.000
  overall     mean = 0.989
  gate self-test = pass   (scripts_run=True)
```

## Held-out selection rollout lines (packet-ready)

```
- [ ] select-001 | status=success | score=1.00 | evidence=evals/scenarios.json#panel_fe | note=all contracts satisfied
- [ ] select-002 | status=success | score=1.00 | evidence=evals/scenarios.json#ml_hte | note=all contracts satisfied
- [ ] select-003 | status=success | score=0.90 | evidence=evals/scenarios.json#time_series_var | note=no Design Gate Card for 'Time Series'
```

## Reading the baseline

- **Causal-identification designs are fully gated.** DiD, IV, RDD, synthetic
  control, panel FE, DML/HTE, and causal-graph scenarios all score `1.00`: their
  routing is documented end to end and each has a Design Gate Card.
- **One held-out miss.** `time_series_var` loses half its `gate_integrity`
  credit (`0.50`) — the skill routes time-series work to `67/time-series`, but
  `references/design-gate-cards.md` has **no Time Series card**. The other eight
  cards are causal-identification designs, so this may be a deliberate scope
  boundary rather than an oversight.
- **Net effect.** Selection mean is `0.967`, not a vacuous `1.000` — evidence
  the harness discriminates. Any future edit claiming to improve the skill must
  beat `0.967` on the selection split without dropping the `1.000` regression
  mean.

## Surfaced finding (for the loop owner)

> **Decision needed, not auto-applied.** If time-series papers are in scope for
> Stage 3, add a Time Series / VAR / cointegration Design Gate Card (stationarity
> & unit-root checks, lag-order selection, VAR stability, cointegration rank,
> structural-break diagnostics) to `references/design-gate-cards.md`. That would
> raise the selection mean from `0.967` to `1.000`. If time-series is
> intentionally out of scope, drop or relabel the `time_series_var` scenario and
> record the rationale here so the gap is not re-flagged each run.

The harness measures and surfaces; adopting or declining this is a skill-scope
call left to whoever runs the improvement loop.
