# Citation & Temporal Integrity — 引用存在性 · 时序完整性层

> 在 Stage 1（文献定位）、Stage 2（数据 vintage 登记）、Stage 5–6（写作与打磨）、Stage 9（投稿终审）加载。
> 本文件规定**论文里每一条引用必须真实且被正确识别**，以及**论断在时间上不穿越未来**，并把它落成一份
> 可机械校验的工作区 artifact（`00_meta/citation_integrity_log.md`）。
>
> **作用域边界（重要，避免和姊妹层重复）**：研究可信度的「引文环节」可拆成两半——
> **(a) 这条引用是不是真的、是不是引对了**（存在性 / 正确性 / 时序），**(b) 正文论断是否忠实于它所引证据**
> （supported / distortion / unsupported 判定）。**本文件只管 (a)**；**(b) 由姊妹层
> `integrity-and-claim-audit.md` + `claim_integrity_audit.md` 承担**（claim locator manifest + verdict
> taxonomy）。两层合起来才是完整的引文可信度闸门，互不覆盖。
>
> **执行分工**：引用核验的**执行**仍调用 `reference-verify` 与 StatsPAI `bibtex`（`paper.bib` 为唯一真源）；
> 证据↔结果对齐仍由 [`templates/evidence_ledger.md`](../templates/evidence_ledger.md) 承担。本文件规定的是
> 「核到什么程度算核完、时序上不能犯哪些错」的验收口径。
>
> **与 `_verification_log/` 的区别**：`_verification_log/` 记录**本 skill 自身**对方法学的声称（给维护者
> 审计 skill 用）；本文件记录的是**用户论文**对外部文献的引用与时序（给论文过 reviewer 用）。

---

## 0. 这个层解决什么

实证论文最容易在两处**非方法性、却同样致命**的地方崩塌引文可信度：

1. **引用是假的或错的**：LLM 辅助写作会产出**不存在的文献**（幻觉 DOI/作者/年份）、**张冠李戴**
   （把 A 的结论挂到 B 名下）、**引用已撤稿/勘误后失效**的结果，或**把综述当一手证据**引。一处假引用
   足以触发 desk-reject 或投稿后撤稿。
2. **时序穿越（anachronism / look-ahead）**：用**未来才知道的信息**支撑当下的设计或论断——既包括
   **文献时序**（把晚于设计的工作说成「研究动机」），也包括**数据时序**（特征里混入决策时点之后才公布的
   信息、用 restated/revised 数据当实时可得、训练/测试切分不尊重时间、样本期外强行外推、生存偏差回填）。

> 第三类失败——**论断超出来源支撑（overclaim beyond source）**——由姊妹层 `claim_integrity_audit.md`
> 的 verdict taxonomy 处置；本层不重复，只在 §1 收口「引用层面」的数字/引语忠实（转述他人系数、直接引语逐字）。

---

## 1. 引用存在性与正确性（Citation Existence & Correctness）

**真源纪律**：`paper.bib` / `ref.bib` 是引用的**唯一真源**；正文 `\cite` 只能引用 bib 里**已核验**的条目。
新增引用先进 bib、核验、再进正文，绝不反过来。

**逐条核验协议**（每个 bibkey 走一遍，落入 `citation_integrity_log.md` §1）：

| 核验项 | 通过标准 | 工具 |
|---|---|---|
| **存在性** | DOI / arXiv ID / handle 能解析到真实记录；非幻觉、非两条记录拼接 | StatsPAI `bibtex`（keys=[...] 返回 verified 条目）；zotero MCP `search`/`fetch`；WebFetch 解析 DOI |
| **元数据匹配** | 作者、年份、题名、刊物/会议与解析记录一致（容许卷期页的版本差异） | 同上；交叉比对 bib 字段 |
| **版本一致** | 区分 working paper / 预印本 / 正式发表版；引用了哪一版就标哪一版、年份对应 | 解析记录 + 出版商页 |
| **撤稿/勘误筛查** | 不引用已撤稿结果；被勘误的引用对应**勘误后**的数字 | zotero MCP `scite_check_retractions`；`scite_enrich_item` |
| **掠夺性/可疑刊** | 标记掠夺性期刊、被合并/停办刊物的引用，能换更权威来源就换 | 人工 + venue 核（见 [`peer-review-and-submission.md`](peer-review-and-submission.md)） |
| **自引合规** | 双盲投稿阶段，自引措辞匿名化（「如 X(2020) 所示」而非「如我们先前工作」） | Stage 9 匿名化检查 |

**引用层面的忠实（存在之外还要对）**——这三项属「引用是否引对」，留在本层：

- **无引用洗白（citation laundering）**：一手结果要引一手来源，不引综述/二手转引。
- **数字忠实**：正文转述他人论文的系数/符号/显著性/样本量时，必须与原文一致；不确定就核原文。
- **引语忠实**：直接引语逐字、给页码；改动用方括号标注。

> 论断**整体**是否忠实于证据（含本项目自己的估计），由 `claim_integrity_audit.md` 的 claim locator
> manifest 统一判定，本层不重复其 verdict 流程。

**状态机**：每条引用在 log 里取 `verified`（已核全部项）/ `to-verify`（待补，须写明缺什么）/
`flagged`（命中撤稿/掠夺性/不匹配，须处置）。**进入 Stage 9 终审时，正文引用不得有 `to-verify` 或
未处置的 `flagged`。**

---

## 2. 时序完整性（Temporal Integrity）—— 不穿越、不偷看未来

这是现有流程与姊妹 claim-audit 层都**未覆盖**的横切线，也是经管/金融实证最高频的隐性硬伤。分三个时间面，
逐项进 `citation_integrity_log.md` §2。

### 2.1 文献时序（不把未来当动机）

- **动机/设计的支撑文献必须先于设计存在**：不要把晚于数据期/设计定型的工作写成「我们据此设计」。
  晚出现的相关工作放进「与并行工作的关系」或讨论，而非动机链。
- **「据我们所知」要标知识截止**：声称「首次」「尚无文献」时，注明检索截止日期与库（见
  [`literature-and-positioning.md`](literature-and-positioning.md)），别把检索盲区说成空白。
- **引用年份与所述事实自洽**：政策、制度背景、统计口径的引用年份要与正文叙述的时点对得上。

### 2.2 数据时序（look-ahead / 实时可得性）—— 实证论文的高频杀手

| 风险 | 要求 | 关联 |
|---|---|---|
| **特征泄漏（look-ahead）** | 预测/决策类设定里，t 时刻的特征只能用 t 时刻**已公布、已可得**的信息；不得混入事后修订值或公告滞后期内的数据 | [`dataset-cards.md`](dataset-cards.md) 各源「公布滞后/vintage」；[`design-risk-ledger.md`](design-risk-ledger.md) |
| **数据 vintage / 修订** | 宏观与会计数据区分**实时（real-time / as-reported）**与**最终修订值**；用 final 值做「当时可知」的推断要显式说明并做稳健性（如 FRED-MD/QD 的 real-time vintage） | [`dataset-cards.md`](dataset-cards.md)（FRED-MD/QD、Compustat point-in-time） |
| **事件窗口偷看** | 事件研究/资产定价的窗口不得纳入事件公布前未知的信息；估计期与事件期边界清楚 | [`design-gate-cards.md`](design-gate-cards.md) |
| **训练/测试切分** | ML / 预测辅助实证里，切分尊重时间顺序（不随机打乱跨期）；样本内调参不外溢到样本外 | [`statspai-analysis.md`](statspai-analysis.md) ML-因果模式 |
| **生存偏差 / 回填** | 数据库的当前成分（指数成分、存活公司）不得回填到历史；区分 point-in-time 与 as-of-today | [`dataset-cards.md`](dataset-cards.md)（CRSP/Compustat/指数成分） |

### 2.3 样本期与论断期（不超出数据窗外推）

- **论断的时间边界 = 数据的时间边界**：不要把基于 2010–2019 的估计写成「长期成立」或外推到结构断裂
  之后（COVID、政策切换、制度改革）。
- **结构断裂披露**：样本横跨明显断裂期时，说明是否分段、是否做断点稳健性。
- 与 [`empirical-audit.md`](empirical-audit.md) 的样本边界、[`threats-to-validity.md`](threats-to-validity.md)
  的外部效度合流。

> 时序违规的后果接 evidence ledger 的 claim 强度阶梯：若 look-ahead 无法排除，相关结果至多 `descriptive`
> 或进稳健性附录，绝不作为主因果发现。

---

## 3. 落地工具：`citation_integrity_log.md` + 机械校验器

- **工作区 artifact**：从 [`templates/citation_integrity_log.md`](../templates/citation_integrity_log.md)
  实例化到 `00_meta/citation_integrity_log.md`。§1 引用核验表、§2 时序清单。
- **机械校验**：`python3 scripts/check_citation_integrity.py <workspace>` 检查——
  - §1 Citation Verification 与 §2 Temporal Integrity 两个必备小节都在；
  - 每条引用 `status ∈ {verified, to-verify, flagged}`，`flagged` 必须写处置、`to-verify` 必须写缺什么；
  - 终审模式 `--final`（Stage 9）下不得残留 `to-verify` 或未处置 `flagged`，且至少有一条已核引用；
  - 时序清单每项有明确 `pass/na/risk` 结论，`risk` 必须连到 claim 后果。
  - 带 `--selftest` 自测校验器不变量。

---

## 4. 闸门接入（哪个 Stage 做什么）

| Stage | 本层做什么 | 落盘 |
|---|---|---|
| **1 文献定位** | 记 §2.1 的检索截止日期与「首次/空白」声称证据；初始化 log | `00_meta/citation_integrity_log.md` |
| **2 数据** | 按 §2.2 把每个用源的 vintage / 公布滞后 / 生存偏差风险登记（与 dataset-card 同步） | log §2 + `dataset_card.md` |
| **3 估计** | look-ahead / 训练-测试时序违规若不能排除，按 §2 降 claim 强度（同步 evidence ledger） | log §2 + `evidence_ledger.md` |
| **5–6 写作打磨** | 每条引用进 §1 核验；`reference-verify` 跑一遍 | log §1 |
| **8 模拟评审** | critic 抽查随机 N 条引用复核存在性与撤稿；命中假引用即 rubric ⑥ 致命红旗 | `referee_report.md` |
| **9 投稿终审** | `--final` 跑校验器：无 `to-verify`、无未处置 `flagged`、撤稿筛查通过 | `ref_verify_final` + log 全绿 |

**rubric 第⑥维致命红旗**（任一即封顶）：存在无法核验/幻觉引用、引用了撤稿结果、未排除的 look-ahead
却作主因果论断。（论断 overclaim-beyond-source 的封顶由 `claim_integrity_audit.md` 触发。）

---

## 5. 工具映射（用什么核）

| 任务 | 首选 | 退化 |
|---|---|---|
| bib 条目核验 / 取规范引用 | StatsPAI `bibtex(keys=[...])` | zotero MCP `search`+`fetch`；WebFetch 解析 DOI |
| 撤稿/勘误筛查 | zotero MCP `scite_check_retractions` | 人工查 Retraction Watch / 出版商勘误页 |
| 文献元数据补全 | zotero MCP `scite_enrich_item` / `scite_enrich_search` | WebSearch 作者+题名+年份比对 |
| DOI/题名解析 | WebFetch（解析 doi.org / 出版商页） | WebSearch |
| 数据 vintage / 公布滞后 | [`dataset-cards.md`](dataset-cards.md) 各源卡 | 数据源官方文档 |

> MCP/网络缺失时按 [`runtime-fallbacks.md`](runtime-fallbacks.md) 退化执行，并在 log 标注「核验降级」，
> 质量门相应封顶——**绝不**因为工具不可用就把 `to-verify` 直接标成 `verified`。

---

## 6. 反模式（critic 见到即扣分）

- 「先写满引用、投稿前再核」——核验必须随写随做，终审只是抽查兜底。
- 把 LLM 生成的 bib 直接 `\cite`，不过 `bibtex`/`reference-verify`。
- 宏观/会计实证用 final 修订值却宣称「实时可预测」，不做 real-time 稳健性。
- 「首次研究」「尚无文献」无检索截止日期、无库范围。
- 把综述里的二手转引当一手证据。
- 工具不可用就把核验项默认通过，不在 log 留降级痕迹。

---

## 7. 一句话

**前面的方法闸门保证「我的结果可信」；姊妹 claim-audit 层保证「我的话忠实于证据」；本层保证「我引的别人
真实存在、引对了、我没穿越时间偷看未来」。** 三层合流到 rubric ⑥ 与 Stage 9 终审，稿子才经得起 reviewer
逐条抠引用与时序。
