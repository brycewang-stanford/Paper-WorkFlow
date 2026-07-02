# Stage 3 replication-accuracy cases

A frozen suite of **replication cases** for `evals/check_replication_accuracy.py`.
Each case pins a **gold truth** — a coefficient value that is an established fact
— and the scorer reports, across cases, the three nested rates from the
Econometrics-Agent paper (`Can AI Master Econometrics?`, arXiv 2506.00856):

| Metric | Meaning | When a case counts |
|---|---|---|
| **sign-correct** | the coefficient points the right way | every primary coefficient's sign matches gold |
| **perfect** | it lands on the gold value | every primary coefficient within `rel_tol` (default 5%) |
| **partial-or-better** | sign-correct and roughly the right magnitude | perfect, or sign-correct with at least one coefficient within `rel_tol` / all within `partial_tol` (default 20%) |

These are exactly the dimensions that the rest of the eval layer cannot see: a
Stage 3 run can pass every gate and still produce a wrong-signed estimate. This
suite is the "did the numbers come out right" check.

## Why this is different from the other evals

`score_skill.py` and the gate checkers measure whether the *documented procedure*
is consistent and whether the *gates fired*. This one measures **output
correctness** against ground truth — the only eval here that can fail a run whose
paperwork is immaculate but whose econometrics is wrong.

## The integrity rule (non-negotiable)

A gold value is a **measured fact with a source**, never a guess. Every `active`
case must carry a `gold_source` naming where the number comes from (a published
table, a simulation's known DGP, an official figure). A case with no real gold
yet must be `"status": "template"` with `value: null` — the scorer **skips
templates and refuses to score a placeholder as if it were real**. This mirrors
the skill's own anti-fabrication discipline: we never invent a number to grade
against.

## What ships

- [`did_demo_self.json`](did_demo_self.json) — the one case whose gold we **own**.
  The repo's `did_demo.ipynb` simulates a staggered panel with `TRUE_ATT = 2.0`,
  so a faithful Callaway-Sant'Anna / Sun-Abraham / BJS estimate must recover
  ~2.0 and a naive TWFE is the cautionary contrast. Use it to confirm the scorer
  and a Stage 3 backend agree before trusting transcribed cases.
- [`card_krueger_1994_minwage.json`](card_krueger_1994_minwage.json) — the first
  **published** case: Card & Krueger (1994, AER) Table 3's +2.76 FTE
  difference-in-differences (and Table 4's regression-adjusted +2.30), both
  transcribed directly from the published tables and re-verified against the
  paper's PDF on 2026-07-02. A replication on the public survey data must land
  a POSITIVE NJ−PA differential of this magnitude.
- [`lalonde_nsw_experimental.json`](lalonde_nsw_experimental.json) — the NSW
  experimental benchmark (~+$1,794, Dehejia & Wahba 1999). The gold constant and
  the data ship in the parent AERS repo's audited numeric benchmark, where a
  deterministic checker recomputes it — a recomputable fact, not a memory.
  Deliberately looser tolerances: observational adjustment is scored on sign
  and rough magnitude, not on nailing the experimental point.
- [`published_case_template.json`](published_case_template.json) — copy-to-extend
  template for a published-replication case (gold transcribed from a paper that
  ships a replication package). Left as a template on purpose: it has no real
  gold until you read one from a cited table.

## Adding a published case

1. Pick a paper that ships a replication package (gold is then an established
   fact, not your own re-estimate).
2. Copy the template, set `status: "active"`, fill `gold_source` with the exact
   table/column, and set each primary coefficient's `value`.
3. Point Stage 3 at the same data; let it write `03_analysis/results/estimates.json`.
4. Score it:

   ```bash
   python3 evals/check_replication_accuracy.py \
       --cases evals/replication_cases \
       --candidate 03_analysis/results/estimates.json
   ```

5. Validate schema any time (no candidate needed):

   ```bash
   python3 evals/check_replication_accuracy.py --validate-suite evals/replication_cases
   ```

Keep `rel_tol` tight enough to catch a wrong specification, loose enough to
tolerate solver/rounding differences. List only the coefficients the paper's
headline claim hinges on under `primary_coefficients`.
