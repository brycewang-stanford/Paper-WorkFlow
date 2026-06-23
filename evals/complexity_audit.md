# Complexity drift audit — is SkillOpt pulling this repo off course?

> Companion to [`check_complexity_budget.py`](check_complexity_budget.py).
> Read when deciding whether the next maintenance wave should *add* or *consolidate*.

## The question

This skill now formally invokes SkillOpt (SKILL.md references a "SkillOpt-style
优化协议"; [`../references/skillopt-improvement-loop.md`](../references/skillopt-improvement-loop.md)
adapts its loop). SkillOpt's headline empirical result is the opposite of what
this repo has been doing: its winning artifact is **compact** (300–2000 tokens)
and generalizes, precisely *because* the optimizer prunes as hard as it adds.

So: has importing SkillOpt's vocabulary, without its pruning half, been pulling
the repo off course?

## The evidence (measured, not guessed)

As of 2026-06-23:

| Layer | Size | Note |
|---|---|---|
| SKILL.md (**always loaded**) | ~42.9 KB ≈ 10.7k tokens | ~5× the top of SkillOpt's compact range |
| references | 29 files ≈ 95k tokens | on-demand; most were born within a few days |
| templates | 24 files ≈ 15.6k tokens | on-demand |

Trend across the recent waves:

- SKILL.md grew **~23% in one wave** (34.8 KB → 42.9 KB) and kept climbing.
- inserted lines outnumbered deleted by **~5–6 : 1**.
- additive commits outnumbered consolidating ones by **~20 : 1**.

## The mechanism (why it drifts)

The loop is well built — held-out gate, bounded patches, rejected-edit memory.
But its objective is **one-directional**: every scoring dimension (routing
fidelity, gate integrity, reproducibility, the integrity checkpoints) can only be
*raised by adding* content. None of them ever rewards removal. Faithfully running
such a loop must inflate the skill monotonically.

Two compounding factors:

1. **Mechanics without telos.** The repo adopted SkillOpt's *loop* (gate, packet,
   split) but not its *goal* (compactness, generalization). Citing a
   compactness paper while growing is a credibility gap a SkillOpt-literate
   reader will notice.
2. **A self-graded proxy with no external truth.** SkillOpt's benchmarks score
   against objective accuracy. Here the "score" is the repo's own definition of
   structural completeness. Optimizing a proxy you define and grade yourself is
   the classic Goodhart trap — it can feel rigorous while drifting from real
   research quality. (The held-out eval saturating at ~1.0 is the tell: a metric
   with no gradient left.)

## What is actually fine

- **Progressive disclosure works.** The ~95k reference corpus is loaded on
  demand, not every run. A real run pays SKILL.md plus the few references its
  route hits. So the cost is maintainability and coherence, not per-run context.
- **Not all of the growth is waste.** Design-risk ledger, gate cards, the
  inference and integrity layers are genuine rigor. The domain is genuinely deep.
- **The loop's locality rules are the good half of SkillOpt** and should stay.

## The fix: give the loop a second direction

[`check_complexity_budget.py`](check_complexity_budget.py) is the missing brake.
It does not score quality; it ratchets footprint:

```bash
python3 evals/check_complexity_budget.py            # report; exit 1 if footprint grew
python3 evals/check_complexity_budget.py --json
python3 evals/check_complexity_budget.py --selftest
# deliberate, justified growth only:
python3 evals/check_complexity_budget.py --update-baseline --note "why this must grow"
```

- The always-loaded SKILL.md and the reference-file **count** may not grow past
  the recorded ceiling ([`complexity_baseline.json`](complexity_baseline.json))
  without a justified `--update-baseline`.
- It reports headroom toward an aspirational SKILL.md target (32 KB ≈ 8k tokens):
  currently **~10.9 KB over**, which is the concrete goal for a consolidation pass.

The ratchet is a brake, not a demand to shrink today — flat edits pass; only
growth trips it. It stops the bleeding now; the slimming is a separate,
deliberate pass (see below).

## Recommended next steps (in order)

1. **Stop adding layers.** Make the next wave a **consolidation pass**, not a
   feature pass.
2. **Wire the ratchet into CI** so growth is caught automatically (snippet below).
3. **Slim SKILL.md toward the 32 KB target** by moving detail into the on-demand
   references it already owns — pure relocation, no information lost.
4. **De-saturate the quality eval** by adding the parsimony dimension (snippet
   below) so the held-out score regains a gradient and gains subtraction-pressure.
5. **Aim for ~4:1 add:consolidate**, not 20:1.

## Wiring snippets — NOT applied here (they touch shared files)

This pass adds only net-new files in `evals/`, so it cannot collide with
maintenance in flight. The snippets below edit files other sessions own
(`validate_skill.py`, `score_skill.py`, `skillopt-improvement-loop.md`); apply
them deliberately, when no parallel edit is in flight.

**(a) Enforce the ratchet in `validate_skill.py`** — add a check and call it from `main()`:

```python
def check_complexity_ratchet() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "evals" / "check_complexity_budget.py")],
        check=True,
    )
```

**(b) Give the quality eval subtraction-pressure** — in `evals/score_skill.py`,
add `"parsimony"` to `DIMENSIONS`, compute it in `compute_global_scores`, and
surface it per scenario:

```python
# in compute_global_scores(...), before the return:
skill_bytes = len((ROOT / "SKILL.md").read_bytes())
parsimony = round(min(1.0, 32_000 / max(1, skill_bytes)), 4)  # 1.0 iff within target
# add to the returned dict:           "parsimony": parsimony,
# add to score_scenario's dims dict:  "parsimony": globals_["parsimony"],
# add to the _selftest globals dict:  "parsimony": 1.0,
```

This makes the score drop below 1.0 while SKILL.md is over target, and rise as it
is slimmed — restoring the gradient the presence-only dimensions lost.

**(c) Make the loop bidirectional** — add to the Adoption rules in
`references/skillopt-improvement-loop.md`:

```markdown
- Footprint ratchet: an edit that grows SKILL.md or the reference-file count must
  justify why it cannot be a consolidation. Run
  `python3 evals/check_complexity_budget.py` before adopting; growth requires a
  deliberate `--update-baseline` with a recorded reason. SkillOpt's own result is
  that compact skills win — keep the always-loaded layer bounded.
```
