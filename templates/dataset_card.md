<!--
  Dataset Card — 每个 *实际用到* 的数据源填一张，落在 02_data/source_cards/<source>.md。
  在 Stage 2（选源/取数）填，喂 Stage 2 的 sample_audit.md 与 Stage 3 的 design_risk_ledger.md。
  目录与 schema 见 references/dataset-cards.md。把方括号占位全部替换；拿不准的写「待核查」，不要猜。
-->

# Dataset Card — [数据源名称 + 库/版本]

| 字段 | 内容 |
|---|---|
| **单位 / 领域** | [观测单位，如 firm-year / 个人 / 国家-年；领域] |
| **覆盖** | [地理 · 时间跨度 · 频率 · 规模量级] |
| **本项目用途** | [在本研究里支撑哪个 estimand / 哪一步] |
| **获取 / 许可** | [公开 / 订阅(WRDS等) / 受限；再分发与复现包边界] |
| **提取日期 / vintage** | [YYYY-MM-DD + 版本号/快照——会修订的源必填] |
| **链接键** | [与其它源 merge 的主键，如 gvkey/permno/cusip/ISO3/证券代码/统一社会信用代码] |
| **链接方式与匹配率** | [怎么合并；名称消歧/crosswalk；匹配成功率与失败是否非随机] |

## 已知陷阱（逐项标 适用 / 不适用 / 已处理）

- [ ] survivorship / 幸存者偏误 — [状态与处理]
- [ ] look-ahead / 用修订后值回测 — [状态与处理]
- [ ] backfill / 历史补录 — [状态与处理]
- [ ] attrition / 样本流失（面板） — [流失率 + 权重修正]
- [ ] linkage error / 合并误配 — [匹配率 + 稳健性]
- [ ] 口径 / 单位 / 分类版本（HS、CPC、季调、基期） — [状态与处理]
- [ ] 覆盖偏（仅上市 / 仅报告国 / 仅可专利领域等） — [对外部效度的限制]

## 触发的设计风险（抄进 design_risk_ledger.md）

| 威胁（→ design-risk-ledger 行） | 本源是否触发 | 处理 / 后果（claim 是否需降级） |
|---|---|---|
| 选择 (selection/survivorship) | [是/否] | [...] |
| 测量误差 (measurement) | [是/否] | [...] |
| 外部效度 (external validity) | [是/否] | [...] |
| attrition | [是/否] | [...] |
| linkage error | [是/否] | [...] |
| look-ahead / vintage | [是/否] | [...] |

## 引用（DAS 与正文都要）

> [数据源标准引用 + 库/产品 + 提取日期/版本；订阅源在复现包只发代码+键列表，不发原始面板]

---
*填完一张即把「触发的设计风险」逐行同步到 `03_analysis/design_risk_ledger.md`，把「覆盖」同步到
`02_data/sample_audit.md` 的目标总体/外部效度边界。任何 blocking 威胁未关掉，Method Gate 不得 PASS。*
