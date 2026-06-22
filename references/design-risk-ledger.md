# Design Risk Ledger — 设计风险总账

> 在 Stage 1 锁定 proposal、Stage 3 写设计注册和方法闸门、Stage 5 写识别/稳健性段、Stage 8 模拟评审时加载。
> 本文件把 `threats-to-validity.md` 和 `design-transparency.md` 的要求落成一个可审计 artifact：
> `03_analysis/design_risk_ledger.md`。

---

## 0. 为什么需要这一层

已有文件分工如下：

- `design_register.md`：研究者打算估计什么。
- `method_gate.md`：每种方法的最低证据包是否齐全。
- `evidence_ledger.md`：论文里的 claim 是否有结果、表图和脚本支撑。

缺口在于：很多一审问题不是“缺一个固定方法 artifact”，而是“某个设计风险有没有被承认、诊断、并转化为
claim 边界”。例如 SUTVA/溢出、外部效度、差异性磨损、后看结果换设定、空结果不报 MDE、机制证据被写成主
因果发现。`design_risk_ledger.md` 专门记录这些风险。

---

## 1. 何时写、谁来写

| 时点 | 动作 | 输出 |
|---|---|---|
| Stage 1 末 | 初步列出 proposal 命中的识别风险和目标 claim 边界 | `03_analysis/design_risk_ledger.md` 草稿 |
| Stage 2 数据后 | 更新 attrition、sample selection、overlap、data-governance 风险 | 同一文件 |
| Stage 3 方法闸门前 | 由独立 critic subagent 逐项判定 applicable/pass/not_pass | 同一文件 + `workflow_state.json.design_risk` |
| Stage 5 写作前 | 用 ledger 限制识别段、结果段、政策含义和 cover letter 措辞 | `00_meta/evidence_ledger.md` 同步降级 |
| Stage 8 模拟评审 | 按 ledger 中剩余风险生成 reviewer objections 和 response plan | `08_review/referee_report.md` / `response_letter.md` |

模板见 [`../templates/design_risk_ledger.md`](../templates/design_risk_ledger.md)。

---

## 2. 逐项审计规则

### 内部效度风险

从 [`threats-to-validity.md`](threats-to-validity.md) §2 抽取适用威胁。命中某一行但没有真实 artifact：

- 主 claim 不能高于 `qualified_causal`；
- 若该威胁直接击穿识别假设（如 bad control、弱工具、操纵性 RDD、明显 spillover），`design_risk.status`
  必须为 `not_pass`，Method Gate 不得 `PASS`；
- 对应 manuscript wording 要在 `evidence_ledger.md` 降级。

### 选择性报告与 specification search

从 [`design-transparency.md`](design-transparency.md) 抽取 PAP、MDE、researcher degrees of freedom、
specification curve / multiverse 和多重检验计划。若主结果是在看过结果后换 outcome、样本、控制集或
聚类口径得到，且未披露：

- `specification_search = not_pass`；
- 质量门维度③（稳健）最高 5；
- 结果段必须写成 exploratory，直到有全规格曲线或预先指定的主设定。

### 外部效度与 transport

每个因果 claim 必须说明估计适用的 population/time/treatment version。LATE、local RDD、single treated
unit 或 donor-pool 设计尤其要写清：

- complier / cutoff / treated unit / donor pool 是谁；
- 不能推广到哪些单位；
- 是否有 reweighting、replication、heterogeneity 或 transport evidence。

缺边界不一定阻断 Method Gate，但会限制 `claim_strength` 和政策含义。

### Spillover、interference 与 attrition

SUTVA 不是默认成立。若处理可能通过地理、网络、市场或一般均衡影响对照组：

- 要有 exposure mapping、buffer/donut、neighbor exclusion 或 partial-interference 设计；
- 没有这些检查时，`spillover_interference` 不能是 `pass`；
- 差异性 attrition 或 panel survival 风险要接 `sample_audit.md`、Lee bounds、IPW 或等价敏感性。

---

## 3. 状态文件字段

`workflow_state.json.design_risk` 是运行时摘要，不替代 ledger 全文：

```json
{
  "status": "pending",
  "risk_ledger": "03_analysis/design_risk_ledger.md",
  "threats_reviewed": [],
  "blocking_threats": [],
  "external_validity": "pending",
  "specification_search": "pending",
  "spillover_interference": "pending",
  "selection_attrition": "pending",
  "last_review": ""
}
```

状态取值：`pending` / `pass` / `not_pass` / `not_applicable`。`status=pass` 要求：

1. `risk_ledger` 文件存在；
2. `blocking_threats` 为空；
3. `external_validity`、`specification_search`、`spillover_interference`、`selection_attrition` 没有
   `not_pass` / `blocking` / `fail`；
4. `evidence_governance.claim_strength` 不强于本 ledger 允许的 claim consequence。

---

## 4. 与 Method Gate / Quality Gate 的硬挂钩

- Method Gate 标 `PASS` 时，`design_risk.status` 也必须 `pass`；否则运行
  `python3 scripts/check_workspace_gates.py <workspace>` 应报 hard inconsistency。
- `design_risk.blocking_threats` 非空时，不得进入 Stage 4 出表写作，除非先把 claim 降到 ledger 允许的等级。
- Draft Quality Gate 评分时，critic 必须同时读取
  `03_analysis/design_risk_ledger.md`、`03_analysis/method_gate.md` 与 `00_meta/evidence_ledger.md`。
- Stage 8 response letter 要把 ledger 中未完全关闭的风险转成主动回应，不要等真实 reviewer 第一次指出。

---

## 5. 反模式

- 把 `design_risk.status` 标 `pass`，但 `Blocking Threats` 表里仍有项。
- 只写“我们做了大量稳健性检验”，却不把每个适用威胁连到 artifact。
- 外部效度边界空白，cover letter 却写成一般政策结论。
- 主结果来自后验 specification search，正文却声称是预先指定。
- 溢出/干涉可能很强，却把对照组污染当作普通 measurement noise。
