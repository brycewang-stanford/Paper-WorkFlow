# Citation Integrity Log

Project: <short name>
Last updated (Beijing): <YYYY-MM-DD HH:MM>
Owner: main orchestrator / citation critic
Literature search cutoff: <YYYY-MM-DD> (库: <Google Scholar / Semantic Scholar / Web of Science / ...>)

Purpose: keep every citation real and correctly identified (§1), and every
temporal claim free of look-ahead / vintage / survivorship leakage (§2). Mirrors
[`references/citation-and-temporal-integrity.md`](../references/citation-and-temporal-integrity.md).
Validated by `python3 scripts/check_citation_integrity.py <workspace>` (`--final` before submission).

Scope boundary: whether a manuscript *claim* is faithful to the evidence it cites
(supported / distortion / unsupported verdicts) is audited separately in
`00_meta/claim_integrity_audit.md` (see `references/integrity-and-claim-audit.md`).
This log covers the half that audit brackets out — does the reference exist and is
it the right one, and is the timing honest.

Single source of truth for citations is `05_draft/ref.bib` (a.k.a. `paper.bib`).
A `\cite` is allowed in the manuscript only when its bibkey is `verified` below.

## 1. Citation Verification

Status ∈ {verified, to-verify, flagged}. `to-verify` must say what remains;
`flagged` must say the disposition (撤稿/掠夺刊/不匹配 → 换源 or 删).

| Bibkey | Cited claim (short) | Identifier (DOI/arXiv) | Metadata match | Version | Retraction/erratum | Status | Checked (date / by) | Note / disposition |
|---|---|---|---|---|---|---|---|---|
| `<bibkey>` | <what it supports> | <doi/arxiv/handle> | ok / mismatch:<field> | published / wp / preprint | clean / retracted / corrected | verified / to-verify / flagged | <YYYY-MM-DD / who> | <e.g. 缺 DOI, 待 reference-verify> |

Citation-specific fidelity (beyond existence) to also confirm per row:

- No **citation laundering**: a primary result is cited to its primary source, not to a survey/second-hand cite.
- **Number fidelity**: when the manuscript transcribes another paper's coefficient/sign/significance/N, it matches the source.
- **Quote fidelity**: direct quotes are verbatim with a page number; edits bracketed.

## 2. Temporal Integrity

Each row concludes `pass` / `na` / `risk`. A `risk` must link to a claim
consequence (claim id in `evidence_ledger.md` or a wording downgrade).

### 2.1 Literature timing

| Check | Detail | Conclusion | Consequence if risk |
|---|---|---|---|
| Motivation cites predate design | <which cites / when design fixed> | pass / na / risk | <move to related work / discussion> |
| "First / no prior work" has cutoff | <cutoff date + library> | pass / na / risk | <add cutoff or soften claim> |
| Cite years consistent with narrative | <which> | pass / na / risk | <fix> |

### 2.2 Data timing (look-ahead / vintage)

| Risk | Source(s) | Requirement met? | Conclusion | Consequence if risk |
|---|---|---|---|---|
| Feature look-ahead (t uses only info known at t) | <source / vars> | yes / partial / no | pass / na / risk | downgrade to descriptive / robustness |
| Vintage vs final (real-time data) | <FRED-MD/QD, Compustat PIT, ...> | yes / partial / no | pass / na / risk | add real-time robustness |
| Event-window peeking | <design> | yes / partial / no | pass / na / risk | redefine window |
| Train/test time-respecting split | <ML setup> | yes / partial / no | pass / na / risk | re-split by time |
| Survivorship / backfill | <index/firm membership> | yes / partial / no | pass / na / risk | use point-in-time |

### 2.3 Sample period vs claim period

| Check | Detail | Conclusion | Consequence if risk |
|---|---|---|---|
| Claim time-bound = data time-bound | <data window vs claim scope> | pass / na / risk | bound the claim |
| Structural break disclosed | <COVID/regime/reform> | pass / na / risk | segment or robustness |

## 3. Open Citation / Timing Issues

| Issue | Affected bibkey / claim | Blocking submission? | Owner | Resolution |
|---|---|---|---|---|
| <hallucinated cite / retraction / look-ahead / vintage> | `<bibkey>` / L<n> | yes / no | <owner> | <action> |

---

Hard rules (enforced by the checker and the rubric ⑥ gate):

- No `\cite` in the manuscript whose bibkey is not `verified` here.
- `--final` (Stage 9) must show zero `to-verify` and zero un-dispositioned `flagged`.
- Any unresolved look-ahead caps the related claim at `descriptive` (sync `evidence_ledger.md`).
- Never upgrade a `to-verify` to `verified` because a tool was unavailable — log the degradation instead.
- Claim-to-evidence faithfulness verdicts live in `claim_integrity_audit.md`, not here.
