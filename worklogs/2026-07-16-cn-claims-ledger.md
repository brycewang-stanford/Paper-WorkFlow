# 2026-07-16 · CN-context claims ledger + demo walk-through surfaced

Closes two of the three Open Items from `2026-07-08-week-recap.md`.

## What changed

### 1. `_verification_log/cn-data-claims.md` (new)

- 12-entry ledger (C01-C12) mirroring `methods-claims.md`, covering the
  load-bearing facts in `references/china-data-sources.md` and
  `references/chinese-journals.md`: CID citation + threshold break +
  coverage window, survey institutional designs (CFPS/CHARLS/CHFS/CGSS),
  data-export legal framework, GB/T 7714-2015, customs HS concordance.
- Status honesty: mutable facts (CSMAR vendor field docs, per-journal
  turnaround/fees) are `to-verify` with an explicit "待补" note; stable
  institutional/legal facts are `canonical`; one entry (`C01`) is
  `verified` live this pass.
- Passes `scripts/check_verification_log.py` (same contract as the
  methods ledger: stable IDs, kebab-case tags, valid `used-in` paths).

### 2. Two factual fixes in `references/china-data-sources.md`

- §6.3 CID recommended citation was garbled ("Brandt, Loren, John
  Litwack, and Yifan Zhang… Growth and structural transformation…").
  Live-verified and corrected to Brandt, **Van Biesebroeck** & Zhang
  (2014), "Challenges of working with the Chinese NBS firm-level data",
  *China Economic Review* 30, 339-352; added 聂辉华-江艇-杨汝岱 (2012,
  《世界经济》) as the Chinese-language companion.
- §3.1 CHARLS "2008 基线" corrected to 2008 two-province pilot
  (Gansu/Zhejiang) + 2011 national baseline.

### 3. README demo-paper surfacing (zh + en)

- The 7.5 synthetic-CFPS 12pp paper (`社媒文件/7.5-测试案例/`) is now
  linked from both READMEs as the canonical Stage 0-9 walk-through,
  with the synthetic-data caveat repeated at the link site.

## Deferred

- "Wire `build_paper_workflow_intro.py` into `make catalog`" is a
  **parent-repo** surface (no Makefile in this repo); left open for a
  maintenance pass that touches the parent catalog.

## Validation

- `python3 validate_skill.py` end-to-end green.
- `python3 scripts/check_verification_log.py` green with the new ledger.
- `python3 scripts/check_bilingual_docs.py` green after the paired
  README edits.
- `python3 evals/check_complexity_budget.py` green (SKILL.md untouched;
  `_verification_log/` and `worklogs/` are outside the reference-budget
  scope).
