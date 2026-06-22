# Claim Integrity Audit

Project: <short name>
Audit mode: pre-review / final-check
Updated at (Beijing): <YYYY-MM-DD HH:MM>
Owner: integrity critic

Purpose: verify that manuscript claims, citations, numerical statements, and
negative constraints remain faithful to the evidence ledger and source material.
This complements `00_meta/evidence_ledger.md`: the ledger records allowed claims;
this audit checks the current prose against that contract.

## 1. Audit Scope

| Scope item | Rule | Status |
|---|---|---|
| Abstract, introduction, conclusion, cover letter claims | Always audited | pending |
| Numerical claims, effect sizes, p-values, N, dates | Always audited | pending |
| Causal language (`effect`, `impact`, `causes`, `leads to`) | Must be allowed by evidence ledger | pending |
| Cited factual claims | Source passage or retrieved text required | pending |
| Uncited factual assertions | Must be moved to evidence ledger or softened | pending |
| Negative constraints / forbidden wording | Must not be violated | pending |

## 2. Claim Locator Manifest

| Claim ID | Manuscript location | Exact claim text | Evidence ledger row | Source / result locator | Required verdict |
|---|---|---|---|---|---|
| C1 | main.tex:<section> | <claim> | `00_meta/evidence_ledger.md#c1` | `03_analysis/results/main_results.json` / <bibkey> | supported |

Locator rules:

- Use exact manuscript text when possible; otherwise record the shortest unique quote.
- Record result paths with enough detail for a follow-on agent to find the number.
- Record citation support as DOI, bibkey, page, section, table, quote, or explicit retrieval failure.
- Claims backed by the project's own experiment or estimate must point to data/code provenance, not just a citation.

## 3. Verdict Taxonomy

| Verdict | Meaning | Gate consequence |
|---|---|---|
| supported | Claim matches the evidence ledger and cited/source artifact | pass |
| minor_distortion | Meaning preserved but wording/rounding needs a small correction | revise before final-check |
| major_distortion | Claim exaggerates, reverses, or changes the evidence | blocking |
| unsupported | No located evidence supports the claim | blocking |
| retrieval_failed | Source exists but could not be checked | disclose; final-check cannot pass if central |
| constraint_violation | Claim violates forbidden wording or an allowed-strength boundary | blocking |

## 4. Claim Review Table

| Claim ID | Claim text | Support artifact | Source locator | Verdict | Severity | Required edit |
|---|---|---|---|---|---|---|
| C1 | <claim> | <result/citation> | <page/quote/path> | supported / minor_distortion / major_distortion / unsupported / retrieval_failed / constraint_violation | none / low / medium / high | <edit> |

## 5. Uncited Assertions and Drift

| Location | Assertion | Why it matters | Action |
|---|---|---|---|
| main.tex:<section> | <assertion> | numerical / causal / trend / factual | add evidence row / cite / soften / delete |

## 6. Summary

- Checked claims:
- Supported:
- Minor distortions:
- Major distortions:
- Unsupported:
- Retrieval failures:
- Constraint violations:
- Blocking findings:
- Final verdict: PASS / PASS_WITH_NOTES / NOT_PASS

Pass criteria:

- `pre-review`: no major distortion, unsupported central claim, or constraint violation in abstract, introduction, results, conclusion, or cover letter.
- `final-check`: 100% of central claims and all numerical/causal claims checked; zero major distortions, unsupported claims, or constraint violations.

