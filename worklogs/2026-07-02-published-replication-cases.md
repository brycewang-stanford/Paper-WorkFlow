# 2026-07-02 First Published Replication Cases

## Scope

Fill the replication-accuracy suite's declared gap: until now the suite shipped
one self-owned gold (`did_demo_self`) and an empty template, so the
"output-correctness against published results" claim had no published case
behind it. Competitive context: no repo in this space (K-Dense, Orchestra,
Imbad0202, Sakana in the ML domain) ships social-science replications whose
gold values are executable-checked; this is the differentiator RELATED-WORK.md
row 2 exists to defend.

## Change

- `evals/replication_cases/card_krueger_1994_minwage.json` — active DiD case.
  Golds transcribed directly from the published AER tables and re-verified
  against the paper's PDF on 2026-07-02: Table 3 row 3 col (iii)
  `did_fte = +2.76` (SE 1.36) and Table 4 model (ii)
  `nj_dummy_adjusted = +2.30` (SE 1.20). Default tolerances (5% / 20%).
- `evals/replication_cases/lalonde_nsw_experimental.json` — active case for the
  NSW experimental benchmark (`adjusted_att = +1794`, Dehejia & Wahba 1999).
  The constant and dataset ship in the parent AERS repo's audited numeric
  benchmark where a deterministic checker recomputes it. Wider tolerances
  (15% / 35%, abs floor $300) because an observational pipeline is scored on
  sign and rough magnitude, not on reproducing the experimental point.
- `evals/replication_cases/README.md` — "What ships" now lists both cases.

## Integrity Decision

The suite's rule is that a gold is a measured fact with a source, never a
guess. Card–Krueger golds were read from the published tables this session
(not quoted from memory); the NSW gold is pinned to a recomputable in-repo
dataset constant rather than to an unopened table. No tolerance was loosened
on the same-data replication case; the looser NSW tolerances are an estimand
decision (observational-vs-experimental), documented in the case file.

## Validation

- `python3 evals/check_replication_accuracy.py --validate-suite evals/replication_cases`
  reports 4 valid cases (3 active, 1 template).
- `python3 evals/check_replication_accuracy.py --selftest` passed.
- `python3 validate_skill.py` passed end-to-end.
