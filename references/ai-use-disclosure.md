# AI-Use Disclosure & Authorship Integrity — 生成式 AI 使用声明契约

This pipeline is an AI orchestrator. Stage 5 drafts with an LLM, Stage 6 polishes
with an LLM, Stage 7 **removes the stylistic fingerprint of the LLM**, and every
stage in between dispatches sub-agents that read, summarise, and write. Every
major publisher now requires that this be declared, and none of them accept
"the prose does not read like AI" as evidence that AI was not used.

So the pipeline needs one contract that a checker can decide:

> **Stage 7 removes the AI *accent*. It must never remove the AI *disclosure*.**
> 去 AI 味是可读性工程，不是隐瞒工程。

That sentence is the whole reference. Everything below makes it enforceable.

## 0. Where It Sits

| Moment | Mode | What happens |
|---|---|---|
| Stage 0 Setup | `open` | create `00_meta/ai_use_disclosure.md`, record the venue policy family |
| every stage end | `open` | append one ledger row per AI-assisted artifact produced this stage |
| Stage 7 -> Stage 8 | `pre-review` | the de-AIGC stage **must** appear as a ledger row; blocking uses screened |
| Stage 9 finalization | `final` | render the venue-shaped statement; `ai_disclosure.status=pass` required for `replication_pack.status=ready` |

```bash
python3 scripts/check_ai_disclosure.py <workspace>           # human report
python3 scripts/check_ai_disclosure.py <workspace> --final   # Stage 9 strictness
python3 scripts/check_ai_disclosure.py --selftest            # verify the checker
```

State lands in `workflow_state.json.ai_disclosure`. A blocking finding sets
`status=not_pass`, which `check_workspace_gates.py` propagates: the submission
package cannot be `ready` and `orchestration.ethics_gate` cannot be `pass`.

## 1. What Venues Actually Require

Policies differ in *placement* and *wording*, not in substance. Four rules are
universal across ICMJE, COPE, Elsevier, Springer Nature, Wiley, Taylor & Francis,
SAGE, the AEA, and the 中文期刊 / 学位论文 side (中国科协《学术出版中 AIGC 使用
边界指南》、教育部学位论文 AI 使用规范):

1. **An AI system can never be an author or co-author.** It cannot take
   responsibility, cannot consent, cannot hold a conflict of interest.
2. **Substantive AI assistance must be declared** — drafting, translating,
   rewriting for style, generating or refactoring analysis code, summarising
   literature. Trivial assistance (spell-check, grammar-only correction,
   reference-manager formatting) generally need not be, but declaring it is
   never a violation.
3. **The authors remain fully accountable for every word, number and citation.**
   "The model produced it" is not a defence, and is treated as misconduct if the
   output turns out to be fabricated.
4. **AI must not fabricate or alter data, results, or images.** Generating a
   plausible-looking coefficient, table or figure is data fabrication regardless
   of intent.

The four policy families this pipeline routes to:

| `policy_family` | Typical venues | Placement of the statement |
|---|---|---|
| `elsevier` | Elsevier journals | a titled *Declaration of generative AI in scientific writing* section **before** the reference list; not in Acknowledgements |
| `springer-nature` | Springer / Nature portfolio | Methods (or Acknowledgements when there is no Methods); authorship section restates that AI is not an author |
| `wiley-sage-tf` | Wiley, SAGE, Taylor & Francis | Acknowledgements or a dedicated AI-use statement; disclose tool, version, purpose |
| `aea-econ` | AEA journals, most econ field journals | disclosure in the submission system + a note where research assistance is normally credited; the AEA data-and-code policy also covers AI-generated code |
| `cn-journal` | 中文期刊 / 学位论文 | 「研究过程中生成式人工智能使用说明」，置于致谢或附录；学位论文另需在诚信承诺书中声明；工具名 + 版本 + 用途 + 人工核验方式缺一不可 |

`policy_family: other` is allowed; it then requires a free-text
`policy_source` URL or citation so the choice is auditable rather than guessed.

## 2. The Ledger

`00_meta/ai_use_disclosure.md` (from [`templates/ai_use_disclosure.md`](../templates/ai_use_disclosure.md))
carries one row per AI-assisted artifact, not one row per prompt. Columns:

| Column | Rule |
|---|---|
| `Stage` | `0`–`9`, `1L`, `2.5` — must be a real pipeline stage |
| `Category` | one of `literature` / `code` / `analysis` / `text` / `translation` / `figure` / `data` |
| `Tool / model` | name **and** version or date, e.g. `Claude Opus 4.6 (2026-02)`; a bare vendor name is unfilled |
| `Used for` | what the assistance actually produced, in one clause |
| `Human verification` | how a human checked it — the load-bearing column |
| `Accountable` | a named human, not a role, not an agent id |
| `Disclose` | `yes` / `no`; `no` requires the row to be trivial by rule 2 above |

### 双语词表（中文台账是一等输入）

节标题、类别、核验方式与「是否声明」都接受中英两套写法，checker 会归一化：

| 位置 | 英文 | 中文 |
|---|---|---|
| 节标题 | `Venue Policy` / `AI-Use Ledger` / `Rendered Statement` | `期刊政策` / `AI 使用台账` / `声明正文` |
| 表头前两列 | `Stage` / `Category` | `阶段` / `类别` |
| 类别 | `literature` `code` `analysis` `text` `translation` `figure` `data` | `文献` `代码` `分析` `文本` `翻译` `图` `数据` |
| 核验 | `rerun` `recomputed` `source-checked` `read-and-edited` `spot-checked` `unverified` | `重跑` `重算` `核对原文` `人工通读并修改` `抽查` `未核验` |
| 布尔 | `yes` / `no` | `是` / `否` |

**列数必须是 7。** 少于 7 列的行不会被静默跳过，而是直接报错——一行 checker 读不懂的记录，
正是最适合藏 Stage 7 或未核验代码的地方。

### Verification vocabulary

`Human verification` is not free-text mood. It must name a check that leaves a
trace, and the checker recognises the vocabulary:

| Token | Means | Typical evidence |
|---|---|---|
| `rerun` | the code was executed and its outputs regenerated | `03_analysis/`, `REPLICATION.md` |
| `recomputed` | the number was recomputed independently | `03_analysis/results/` |
| `source-checked` | every citation resolved to a real, read source | `00_meta/citation_integrity_log.md` |
| `read-and-edited` | a human read the passage and rewrote what was wrong | draft diff |
| `spot-checked` | a sample was checked | must say the sampling rate |
| `unverified` | nobody checked it | **blocking for `code` / `analysis` / `data` / `literature`** |

`unverified` is a legal value on purpose. A ledger that cannot say "nobody
checked this" is a ledger that will lie instead.

## 3. Blocking Rules (what the checker refuses)

| # | Blocking condition | Why |
|---|---|---|
| B1 | an AI tool appears in the author list, or `ai_as_author` is not `no` | universally prohibited |
| B2 | a `data` or `figure` row whose `Used for` describes *generating* values, series, observations, or result images | fabrication, not assistance |
| B3 | `code` / `analysis` / `data` / `literature` row with `Human verification: unverified` | AI-produced results nobody re-ran |
| B4 | Stage 7 (`7_language_dehumanize`) is `done` but no Stage-7 ledger row exists | the de-AIGC stage erasing its own disclosure — the failure mode this gate exists for |
| B5 | a row with `Disclose: yes` whose category is absent from the rendered statement | the ledger and the statement disagree |
| B6 | `--final` and the statement still holds placeholders, or `policy_family` is unset/unknown | shipping a template as a declaration |
| B7 | a `literature` or `text` row is `source-checked`-free while `citation_integrity_log.md` reports unresolved citations | AI-suggested references that were never verified |
| B8 | `--final` and `Accountable` is empty, an agent id, or a placeholder on any disclosed row | nobody is answerable |

Non-blocking but reported: a run whose ledger has zero rows while Stages 5–7 are
`done` (`WARN`: an AI pipeline that used no AI is a bookkeeping failure, and the
checker says so rather than quietly passing).

## 4. Interaction With Stage 7 (de-AIGC)

Stage 7's contract is already narrow: **language only, numbers inert**
(`check_manuscript_numbers.py` enforces the numeric half). This reference adds
the disclosure half. Concretely, when Stage 7 finishes:

- append a `translation`/`text` row: tool, version, "rewrote Sections 1–6 for
  readability and non-formulaic phrasing", verification `read-and-edited`;
- if Stage 7 also touched a Chinese abstract or an EN<->CN translation, that is a
  separate `translation` row — translation is disclosable at every venue above;
- **do not** describe Stage 7 as "removing AI traces" in the statement itself.
  The venue-facing wording is about readability; the ledger keeps the mechanism.

The reason B4 is a hard fail and not a warning: Stage 7 is the one stage whose
*purpose* is to make AI authorship undetectable by inspection. If the pipeline
lets that stage run without forcing a disclosure row, it has automated exactly
the misconduct that every policy in §1 is written to prevent.

## 5. Rendering the Statement

The ledger is internal; the statement is what ships. `§Rendered Statement` in the
template holds the venue-shaped text. Rules:

- name the tool **and** version, the purpose, and that the authors reviewed and
  take responsibility;
- one statement covering all disclosed categories, not one per tool;
- never claim a category that has no ledger row (over-disclosure is still a
  ledger/statement mismatch and fails B5 in the other direction — the checker
  reports it as `WARN`, since over-disclosure is not misconduct);
- for `cn-journal`, render Chinese; otherwise render in the manuscript language.

A worked Elsevier-shaped rendering:

> **Declaration of generative AI in scientific writing.** During the preparation
> of this work the authors used Claude Opus 4.6 (2026-02) to draft and copy-edit
> the manuscript text, to translate the abstract into English, and to generate
> and refactor the Stata/Python estimation scripts. All estimation code was
> re-executed by the authors and its output reproduced from raw data
> (`REPLICATION.md`); all cited references were checked against the original
> sources. After using this tool the authors reviewed and edited the content as
> needed and take full responsibility for the content of the publication.

## 6. Anti-Patterns

- **"We did not use AI."** — asserted by a run whose own `logs/` show nine stages
  of sub-agent dispatch. The checker cannot read intent, but B4 catches the most
  common mechanical form of it.
- **Disclosing the writing, hiding the code.** Analysis code is the highest-stakes
  AI contribution in an empirical paper, because a subtle error becomes a
  published coefficient. `code` rows require `rerun` or `recomputed`.
- **"Verified by the agent."** `Accountable` is a person. An orchestrator
  verifying its own output is not verification (B8).
- **Deferring the ledger to Stage 9.** Retrospective reconstruction of what a
  model did eight stages ago is guesswork; the ledger is appended per stage.

## 7. Related

- [`integrity-and-claim-audit.md`](integrity-and-claim-audit.md) — claim faithfulness (what the prose says vs what evidence supports)
- [`citation-and-temporal-integrity.md`](citation-and-temporal-integrity.md) — citation existence, retraction, look-ahead
- [`data-governance.md`](data-governance.md) — restricted data, PII, IRB/DUA; AI tools that touch restricted data are a governance event, not just a disclosure event
- [`computational-reproducibility.md`](computational-reproducibility.md) — AI-generated code lands in the replication pack like any other code
