# Submission Checklist

Project: <short name>
Target journal: <journal>
Checked at (Beijing): <YYYY-MM-DD HH:MM>

## 1. Journal Policy Refresh

- Author guidelines URL:
- Data/code policy URL:
- Anonymization policy:
- Word/page limit:
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

## 3. Final Gates

- Reference verification final pass:
- Citation integrity log `--final` clean (no to-verify, no un-dispositioned flagged, retraction screen done): `python3 scripts/check_citation_integrity.py <workspace> --final`
- Temporal integrity: no unresolved look-ahead / vintage / survivorship leakage behind any causal claim:
- Method gate still valid after revisions:
- Design risk ledger still allows abstract / cover letter external-validity claims:
- Evidence ledger supports abstract / highlights / cover letter claims:
- Quality scorecard accepted:
- No restricted data in public package:
- No credentials, API keys, or personal identifiers in logs:

## 4. Decision

- Submit now:
- Hold for fixes:
- Blocking fixes:
