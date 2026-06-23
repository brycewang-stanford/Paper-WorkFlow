# Held-out evaluation harness (`evals/`)

Automated, reproducible scoring for the SkillOpt-style improvement loop in
[`../references/skillopt-improvement-loop.md`](../references/skillopt-improvement-loop.md).

## Why this exists

The improvement loop and [`../templates/SKILLOPT_PACKET.md`](../templates/SKILLOPT_PACKET.md)
gate every maintenance edit on a **held-out selection score**, but leave that
score to be filled in by hand. In real [SkillOpt](https://github.com/microsoft/SkillOpt)
the selection score is computed by an `evaluator.py` over frozen train/val/test
splits — that automated substrate is what made the gate trustworthy.

This directory supplies the missing half: a mechanical scorer over a frozen
scenario suite, so the "held-out selection score" is a measured number instead
of a vibe. It is the validation set, not a replacement for the loop's judgment.

It is **standalone on purpose** — it imports nothing from the skill, so it never
collides with maintenance edits in flight on the core skill files. The full
scored run remains an explicit maintenance command, while `validate_skill.py`
now runs the scorer self-test plus the complexity ratchet so the local gate
catches broken eval machinery and always-loaded-layer regrowth.

## What it measures

A skill is a *document*, so the "rollout outcome" that matters is whether the
documented procedure still satisfies its own contracts on each task archetype.
The dimensions are the ones named in the improvement loop plus the ARS-inspired
claim-integrity checkpoint added for long paper workflows:

| Dimension | Scope | Signal |
|---|---|---|
| `routing_fidelity` | per-scenario | design → child-skill → tool anchors are documented in the routing references (`skill-map.md`, `analysis-backends.md`, `statspai-analysis.md`, …) |
| `gate_integrity` | per-scenario | the gate self-test passes **and** the design has a Design Gate Card |
| `context_protection` | global | subagent contract present: write outputs to disk, return a concise summary |
| `reproducibility` | global | a fresh workspace passes `scripts/smoke_workspace.py --quiet` |
| `user_burden` | global | `SKILL.md` documents autonomy gears + a minimal-question / authorization discipline |
| `integrity_checkpoint` | global | `SKILL.md`, `references/integrity-and-claim-audit.md`, the template, and the gate checker preserve the Stage 7 `pre-review` and Stage 9 `final-check` claim-integrity contract |
| `citation_temporal_integrity` | global | the complementary citation-existence + temporal-integrity layer is present: `references/citation-and-temporal-integrity.md`, `templates/citation_integrity_log.md`, `scripts/check_citation_integrity.py`, the look-ahead/vintage discipline, and the `--final` gate |

A scenario's total is the mean of the seven dimensions in `[0, 1]` (two
per-scenario + five global). A scenario is `success` at `total >= 0.70` (the
rubric's "meets bar"). The **selection-split mean** is the number a candidate
edit must strictly beat.

## Scenario splits

[`scenarios.json`](scenarios.json) freezes nine research-task archetypes split
the SkillOpt way — do not move a scenario between splits to flatter a number:

- **train** (`did_staggered`, `iv_2sls`, `rdd_sharp`, `synthetic_control`) — may
  motivate an edit; never gate on these alone.
- **selection** (`panel_fe`, `ml_hte`, `time_series_var`) — held out; gates
  acceptance.
- **regression** (`dml_highdim`, `causal_graph`) — held out; guards designs the
  current edit does not target.

## Usage

```bash
# Full scored run (runs smoke + gate self-test): the canonical baseline view
python3 evals/score_skill.py

# Structural-only, fast (skips the subprocess checks)
python3 evals/score_skill.py --no-scripts

# Machine-readable
python3 evals/score_skill.py --json

# Rollout lines ready to paste into a SKILLOPT_PACKET.md (default: selection)
python3 evals/score_skill.py --packet-lines selection

# Invariant self-test (no skill content required to pass)
python3 evals/score_skill.py --selftest
```

`--packet-lines` emits lines in exactly the format
`scripts/check_skillopt_packet.py` expects (`evidence=` + `score=`), so a
maintenance packet's Rollout Split can be populated from measured scores rather
than guessed ones.

## How it plugs into the loop

1. Before an edit, run the scorer and record the **baseline selection score**.
2. Propose a bounded patch (SkillOpt loop step 4).
3. After the edit, run the scorer again on a clean tree. Adopt only if the
   **selection mean strictly increases** and the **regression mean does not
   drop** — then paste the before/after into the packet's Gate Decision.
   When the score is already saturated at `1.000`, do not manufacture a score
   increase; use the complexity ratchet, validation gates, and worklog evidence
   to justify maintenance edits whose value is measurement or consolidation.

## Current baseline & active guardrails

See [`baseline_scorecard.md`](baseline_scorecard.md) for the captured baseline.
The first held-out miss has been resolved: `time_series_var` now has a matching
Design Gate Card, and the current train / selection / regression means are all
`1.000` under the seven-dimension scorer.

The active guardrail is now bidirectional: `validate_skill.py` runs
[`check_complexity_budget.py`](check_complexity_budget.py), which blocks
unjustified growth of `SKILL.md` or the reference-file count. That ratchet keeps
the saturated quality score from becoming an additive-only incentive.

## Extending the suite

Add a scenario to `scenarios.json` with a distinctive (case-sensitive)
`routing_anchors` list and a `gate_card_keyword`. Keep anchors specific enough
not to false-positive on common words. Re-run `--selftest` after any change.
