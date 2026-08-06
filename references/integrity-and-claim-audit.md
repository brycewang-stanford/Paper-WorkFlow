# Integrity & Claim Audit — 引文、数字与 claim 忠实度

This reference adapts the strongest useful pattern from the ARS academic
pipeline: separate "the reference exists" from "the manuscript claim is faithful
to what the evidence actually supports." For empirical papers, the second check
must also cover the project's own estimates, exhibits, data provenance, and
allowed claim strength.

## Where It Sits

Run the audit at two points:

| Moment | Mode | Blocking rule |
|---|---|---|
| Stage 7 -> Stage 8 | `pre-review` | no unsupported central claim or negative-constraint violation can enter simulated review |
| Stage 9 finalization | `final-check` | all abstract/introduction/results/conclusion/cover-letter claims plus all numerical and causal claims must be checked |

This audit complements, not replaces:

- `03_analysis/method_gate.md` for method validity;
- `00_meta/evidence_ledger.md` for allowed wording and claim strength;
- `00_meta/quality_scorecard.md` for draft-level quality;
- `REPLICATION.md` and `09_submission/DAS.md` for reproducibility and data access.

## Numbers Are Audited Mechanically First

This audit is a judgement task performed by a critic reading prose, and prose
judgement does not scale to *every digit in the paper*. Before it runs, one
purely mechanical question must already be answered:

```bash
python3 scripts/check_manuscript_numbers.py <workspace>          # Stage 7 -> 8
python3 scripts/check_manuscript_numbers.py <workspace> --strict # Stage 9
```

It settles two things no human reviewer can reliably settle by eye:

1. **Anchoring.** Every coefficient, standard error and sample size the
   manuscript asserts must appear in `03_analysis/results/` or `04_results/` at
   the precision it is printed (`0.123` is satisfied by `0.12345`). A figure that
   matches nothing is not a wording problem for the critic to weigh — it is a
   number with no known origin.
2. **Rewrite inertness.** The Stage 6 -> Stage 7 boundary is contractually
   language-only, so any numeric delta across it, in either direction, is a hard
   violation of the de-AIGC red line.

Results land in `workflow_state.json.manuscript_numbers`; `unanchored_claims` or
`inert_boundary_drift` above zero blocks the Draft Quality Gate via
`check_workspace_gates.py`'s `quality_gate:numbers` row, before any dimension is
scored. The critic's remaining job on numbers is the part a script cannot judge:
whether an anchored number is being *interpreted* faithfully.

A number that is genuinely correct but has no analysis output behind it (a figure
quoted from a cited paper, an institutional constant) is waived in the manuscript
itself, where a referee can see the justification:

```latex
% pw-number-ok: 4.7 -- 2019 urban unemployment rate, quoted from Chen (2021) Table 2
```

Waivers are counted in `manuscript_numbers.waived_claims`; a draft that waives
many of its own figures is itself a signal worth reading.

## Claim Locator Manifest

Before judging prose, create or refresh the claim locator manifest in
`00_meta/claim_integrity_audit.md`.

Each row needs:

- stable `Claim ID` matching `00_meta/evidence_ledger.md`;
- manuscript location and exact claim text;
- evidence ledger row or result ID;
- source locator: DOI/bibkey/page/quote for literature claims, or
  script/result/exhibit path for project-owned empirical claims;
- required verdict (`supported`, `minor_distortion`, `unsupported`, etc.).

Do not judge from memory. If the source passage or result path cannot be
located, record `retrieval_failed` or `unsupported` and lower the gate status.

## Verdicts

| Verdict | Use when | Consequence |
|---|---|---|
| `supported` | claim is faithful to located evidence and allowed wording | pass |
| `minor_distortion` | rounding or paraphrase is repairable without changing meaning | revise before final-check |
| `major_distortion` | evidence says something materially different | blocking |
| `unsupported` | no located source/result supports the claim | blocking |
| `retrieval_failed` | source exists but could not be checked | disclose; central claims block final-check |
| `constraint_violation` | wording exceeds evidence ledger strength or violates forbidden wording | blocking |

## Sampling Discipline

Pre-review may sample peripheral claims, but must always audit:

- every claim in abstract, introduction contribution paragraphs, results topic
  sentences, conclusion, cover letter, and response letter;
- every numerical claim, effect size, p-value, sample size, date range, trend,
  and "largest/first/only" factual superlative;
- every sentence using causal language;
- every claim with `Strength` above `descriptive` in the evidence ledger.

Final-check is not sampled for central claims: all central, numerical, and
causal claims must be checked. Peripheral background claims may be sampled only
if the sampling rule and counts are recorded in the Summary section.

## State Contract

`workflow_state.json.integrity_audit` records:

- `status`: `pending` / `pass` / `pass_with_notes` / `not_pass`;
- `claim_integrity_audit`: default `00_meta/claim_integrity_audit.md`;
- `claim_locator_manifest`: default `00_meta/claim_integrity_audit.md#claim-locator-manifest`;
- `audit_mode`: `pre-review` / `final-check`;
- checked and failed claim counts;
- `blocking_findings`;
- `last_audit`.

If `quality_gate.status=pass`, then the latest `integrity_audit.status` must be
`pass` or `pass_with_notes`. If `replication_pack.status=ready`, the final-check
audit must be `pass` and `blocking_findings` must be empty.

