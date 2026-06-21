# Empirical Audit Pack — 样本、变量与 estimand 对齐

> 在 Stage 2 数据清洗结束、Stage 3 估计开始前加载；Stage 3 方法闸门和 Stage 7 质量门也要引用。
> 本文件补足一个常见短板：实证论文不只会因为估计器选错而失败，也会因为样本构造、处理时点、
> 变量编码、missingness、balance/overlap 或聚类层级与 claim 不一致而失败。

---

## 0. 这个增强层解决什么

`research-grade-methods.md` 管“这个识别设计需要哪些方法证据”；本文件管“进入估计器的数据是否真的支持
那个 estimand”。两者同时通过，结果才可进入写作。

最低标准：

1. **样本流失可追踪**：从 raw import 到 clean data 再到 estimation sample，每一步 N、单位数、
   treated/control 数、drop 原因和脚本位置都要记录。
2. **estimand 不漂移**：目标总体、估计样本、处理定义、outcome window 和比较组必须一致；若清洗限制改变
   estimand，必须在 `design_register.md` 和论文中改写。
3. **变量构造可辩护**：outcome、treatment、controls、mechanisms 的来源、公式、时点和缺失处理必须与
   `codebook.md` 对上；post-treatment controls、mediators、colliders 不能混入 baseline controls。
4. **missingness/balance/overlap 有证据**：不是口头说“样本稳定”，而是落表/落图。
5. **推断层级匹配赋值层级**：聚类、权重、小 cluster 修正要和政策/处理分配层级、抽样设计及 estimand 对齐。

---

## 1. Stage 2 输出合同

Stage 2 除 `02_data/clean.parquet` 和 `02_data/codebook.md` 外，还必须生成
`02_data/sample_audit.md`（模板见 [`../templates/sample_audit.md`](../templates/sample_audit.md)）。

`sample_audit.md` 至少包含：

- raw → intermediate → clean → estimation sample 的行数、单位数、treated/control 数；
- 合并键唯一性、单位-时间粒度、重复记录处理；
- 样本限制、缺失值、winsorization、deflation、scale change、聚合规则；
- treatment timing / exposure window，尤其是 staggered treatment 的 first-treated cohort；
- baseline balance、missingness by treatment、attrition / panel survival、overlap / common support；
- cluster level、cluster count、weights，以及 small-cluster correction 是否需要。

如果真实数据尚不可访问，可以用 `pending` 标注，但不得让 Method Gate `PASS`。若只能用合成数据跑结构，
把 `empirical_audit.status` 置 `not_pass` 或在 `blocking_issues` 写明真实数据阻断。

---

## 2. Stage 3 方法闸门联动

Method Gate 必须把 `sample_audit.md` 作为必需 artifact。以下情况直接 `NOT PASS`：

- estimation sample 与 `design_register.md` 的 target population / comparison group 不一致，且未改写 estimand；
- treatment timing 用了 outcome 或 post-treatment information；
- merge keys 不唯一，或 duplicates 被静默丢弃；
- missingness/attrition 明显与 treatment 相关，但没有诊断或回退；
- baseline controls 含 mediator/collider/post-treatment variable；
- overlap/common support 不足，却继续解释为全样本 ATE/ATT；
- 聚类层级低于处理赋值层级，且无 wild/bootstrap/small-cluster 处理；
- survey/propensity/sample weights 改变 estimand，但未披露。

通过时更新：

- `workflow_state.json.empirical_audit.status = "pass"`；
- `workflow_state.json.empirical_audit.last_audit` 写时间和摘要；
- `workflow_state.json.artifacts.sample_audit = "02_data/sample_audit.md"`；
- `00_meta/evidence_ledger.md` 的 Data and Sample Provenance 表指向同一套脚本路径。

---

## 3. 设计分支重点

| 设计 | 样本/变量审计重点 |
|---|---|
| DiD / event study | cohort 定义、never-treated/not-yet-treated 对照、anticipation window、pre-period coverage、平衡面板需求 |
| IV | first-stage 样本是否等于 reduced-form 样本、工具变量缺失、complier population 是否缩窄 |
| RDD | running variable 清洗、cutoff 附近 heaping、bandwidth 内样本、donut 后样本变化 |
| Synthetic control / SDID | donor pool 纳入排除、pre-period 长度、treated unit 唯一性、outcome scale |
| Panel FE / HDFE | singleton drops、absorbed variation、cluster count、单位进入退出 |
| DML / HTE | train/test or cross-fit splits、overlap、rare treatment cells、feature leakage |
| Text / ML-assisted | label provenance、train/test leakage、embeddings 或 features 是否 post-treatment |

---

## 4. 写作端使用

- Table 1 或 Appendix 的 sample construction table 必须能追溯到 `sample_audit.md`。
- 方法段的 sample restriction 句子必须和 `sample_audit.md` 的 final estimation sample 一致。
- 所有效应量解释必须使用 estimation sample 的均值/基准率，而不是 raw sample 的均值。
- 若 sample restriction 改变 estimand，摘要、引言和结论都要用更窄的 claim。

质量门联动：

- 没有 `02_data/sample_audit.md`：识别可信度和可复现性维度封顶 6。
- `sample_audit.md` 为 `NOT PASS`：识别可信度封顶 4。
- 样本构造与主结果 N、Table 1 或 `main_results.json` 不一致：稳健性和可复现性维度封顶 5。
- 关键 missingness、attrition、overlap 或 cluster 问题未披露：结果解读维度封顶 6。
