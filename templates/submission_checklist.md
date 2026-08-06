# Submission Checklist

Project: <short name>
Target journal: <journal>
Checked at (Beijing): <YYYY-MM-DD HH:MM>

## 1. Journal Policy Refresh

- Author guidelines URL:
- Data/code policy URL:
- Anonymization policy:
- Word/page limit:
- Table format required by the journal (three-line / journal template / full grid):
- File format:
- Supplement / appendix format:
- Conflict of interest / funding disclosure:
- Data availability statement:
- IRB / ethics disclosure:
- Preregistration / trial registration:
- AsCollected or equivalent provenance disclosure:

## 2. Files

| Required file | Path | Ready? | Notes |
|---|---|---:|---|
| Manuscript | 09_submission/main.pdf or main.tex | no |  |
| Cover letter | 09_submission/cover_letter.md | no |  |
| Highlights / abstract | 09_submission/highlights.md | no |  |
| Data availability statement | 09_submission/DAS.md | no |  |
| Replication package | REPLICATION.md + code/data | no |  |
| Author disclosures | 09_submission/disclosures.md | no |  |
| Table style audit | 04_results/table_style_audit.md | no |  |

## 3. Final Gates

- Reference verification final pass:
- Citation integrity log `--final` clean (no to-verify, no un-dispositioned flagged, retraction screen done): `python3 scripts/check_citation_integrity.py <workspace> --final`
- Temporal integrity: no unresolved look-ahead / vintage / survivorship leakage behind any causal claim:
- Method gate still valid after revisions:
- Design risk ledger still allows abstract / cover letter external-validity claims:
- Evidence ledger supports abstract / highlights / cover letter claims:
- Quality scorecard accepted:
- Table style gate clean on the final Word/LaTeX package (three-line tables, booktabs `.tex`): `python3 scripts/check_table_style.py <workspace>`
- Manuscript numbers anchored and rewrite-inert (no figure without analysis output behind it; every waiver justified in-text): `python3 scripts/check_manuscript_numbers.py <workspace> --strict`
- Design lock still honoured: every main result is inside the Stage 2.5 lock, or registered in the deviations log and worded as exploratory: `python3 scripts/check_preregistration.py <workspace>`
- Stage preconditions clean for the submission stage: `python3 scripts/check_workspace_gates.py <workspace> --preconditions 9`
- Scope satisfied: `project.scope` gates all present (`submission` requires method gate, design risk, quality gate, integrity audit, manuscript numbers, replication pack)
- No restricted data in public package:
- No credentials, API keys, or personal identifiers in logs:

## 4. Decision

- Submit now:
- Hold for fixes:
- Blocking fixes:
