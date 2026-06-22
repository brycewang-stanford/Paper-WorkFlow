# Design Gate Cards — 设计分支证据卡

> Stage 3 写 `03_analysis/method_gate.md` 时加载；Stage 5 写作、Stage 7 质量门、Stage 8 模拟评审也要引用。
> 本文件把 `research-grade-methods.md` 的最低证据包压成可执行的 reviewer-facing gate cards：
> **每个因果标签都必须对应一张设计卡，卡上每个 required artifact 都要有真实路径，否则 claim 降级。**

---

## 0. 使用协议

每个设计卡都按同一套输入和输出落地：

- 输入：`01_proposal/proposal.md`、`02_data/sample_audit.md`、`03_analysis/design_register.md`、
  `00_meta/analysis_backend.md`、`00_meta/evidence_ledger.md`。
- 输出：`03_analysis/method_gate.md` 的 **Design Gate Card**、`workflow_state.json.method_gate.required_artifacts`、
  `workflow_state.json.method_gate.missing_artifacts`、`workflow_state.json.evidence_governance`。
- 写作约束：只有卡片 `PASS` 且 evidence ledger 对应 claim 行无 blocking discrepancy 时，正文才可用因果措辞。

**Claim strength ladder**

| Strength | 允许进入的位置 | 最低条件 | 禁止事项 |
|---|---|---|---|
| `causal` | 摘要、引言主贡献、结果、结论、cover letter | Method Gate `PASS`；样本审计 `PASS`；核心稳健性通过；ledger 行指向真实结果和表图 | 无保留地外推到样本外、时窗外或不同 treatment |
| `qualified_causal` | 引言和结果，但必须带边界条件 | Method Gate `PASS` 但存在弱诊断、局部外推或敏感性边界 | 用 "proves"、"establishes" 或无边界政策建议 |
| `descriptive` | 结果、附录、机制探索 | 真实估计可复现，但识别证据不足以支撑因果 | "effect"、"causes"、"impact" 等因果动词 |
| `exploratory` | 附录、未来研究、稳健性补充 | 有真实 artifact，但设计或数据限制明显 | 放进摘要或作为主贡献 |
| `no_claim` | 不进入稿件 | artifact 缺失、样本/变量/治理阻断、或结果与 ledger 冲突 | 用语言包装成发现 |

---

## 1. DiD / Event Study / Staggered Adoption

**适用**：政策评估、自然实验、异时点处理、事件研究。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| Adoption/cohort table | `02_data/sample_audit.md` 或 `03_analysis/results/cohorts.*` | 谁何时被处理；never-treated/not-yet-treated 是否足够 |
| Pre-period coverage | `02_data/sample_audit.md` | treated/control 在处理前是否有共同支持 |
| Event-study plot/table | `03_analysis/results/event_study.*` | leads 是否接近 0；置信区间和基准期是否清楚 |
| Staggered estimator | `03_analysis/results/group_time_att.*` | 多期异时点时是否用了 CS/SA/BJS/imputation 类估计 |
| Naive TWFE contrast | `03_analysis/results/twfe_contrast.*` | TWFE 是否只作风险对照，而非唯一主结果 |
| Anticipation/placebo timing | `03_analysis/robustness/placebo_timing.*` | 提前处理/假政策日期是否不显著 |
| Sensitivity | `03_analysis/robustness/honest_did.*` 或等价 | 预趋势偏弱时，结论对 violation 有多脆弱 |

**Hard fail**

- 异时点处理只报 TWFE，未解释负权重/异质效应风险。
- pre-trend 明显违背且没有 HonestDiD、窗口调整或 claim 降级。
- treatment timing 由 outcome 或 post-treatment 信息构造。
- cluster level 低于政策赋值层级且无 small-cluster 处理。

**允许 claim**

- `causal`：仅限通过卡片的 ATT / event-time ATT、样本和时窗。
- `qualified_causal`：pre-trend 轻微偏弱但敏感性边界披露清楚。
- `descriptive`：pre-trend 不过或只剩 TWFE 相关性。

---

## 2. IV / 2SLS / LATE

**适用**：内生 treatment、工具变量、准随机暴露。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| First stage | `03_analysis/results/first_stage.*` | 相关性、方向、F 统计或弱工具稳健指标 |
| Reduced form | `03_analysis/results/reduced_form.*` | 工具是否移动 outcome |
| Weak-IV robust inference | `03_analysis/robustness/weak_iv.*` | AR/CLR/Anderson-Rubin 或等价稳健区间 |
| Exclusion narrative | `03_analysis/design_register.md` | 工具只通过 treatment 影响 outcome 的制度理由 |
| Balance / falsification | `03_analysis/robustness/iv_balance.*` | 工具是否预测 pre-treatment covariates |
| Over-ID / multiple IV checks | `03_analysis/robustness/overid.*` | 多工具时是否检查一致性 |
| Complier boundary | `00_meta/evidence_ledger.md` | claim 是否明确是 LATE / complier effect |

**Hard fail**

- 第一阶段弱且仍用常规 2SLS p 值做主结论。
- 排他性通道被制度背景或 placebo 明确否定。
- LATE 被写成全样本 ATE/ATT。

**允许 claim**

- `causal`：LATE for compliers，边界写清。
- `qualified_causal`：弱工具稳健区间较宽但方向和制度逻辑仍支撑谨慎解读。
- `descriptive`：工具不稳或排他性缺证据。

---

## 3. RDD / Kink / Threshold Designs

**适用**：running variable、cutoff、评分或资格阈值。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| Running variable audit | `02_data/sample_audit.md` | cutoff 附近是否有 heaping、rounding、缺失 |
| Density/manipulation test | `03_analysis/results/density_test.*` | cutoff 附近是否有排序/操纵 |
| Bandwidth report | `03_analysis/results/bandwidth.*` | 主 bandwidth、备选 bandwidth、kernel/order |
| RBC estimate | `03_analysis/results/rdd_main.*` | robust bias-corrected CI 是否报告 |
| Covariate continuity | `03_analysis/robustness/covariate_continuity.*` | 预处理变量是否连续 |
| Donut and placebo cutoffs | `03_analysis/robustness/donut_placebo.*` | 结果是否靠 cutoff 附近异常点驱动 |
| Plot | `04_results/rdd_plot.*` | binning、置信带、样本窗是否清楚 |

**Hard fail**

- 密度检验显示操纵且无可信解释。
- cutoff 或 running variable 在事后选择。
- 用全样本线性模型替代局部估计当主结果。

**允许 claim**

- `causal`：local treatment effect at cutoff。
- `qualified_causal`：局部估计通过但 bandwidth 敏感。
- `descriptive`：continuity 或 manipulation 证据不足。

---

## 4. Synthetic Control / SDID

**适用**：少数 treated unit、长前期、政策试点、区域/公司案例。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| Donor pool log | `02_data/sample_audit.md` | 纳入/排除 donor 的规则是否预先明确 |
| Pre-fit fit report | `03_analysis/results/prefit_rmspe.*` | 处理前拟合是否足够好 |
| Unit/time weights | `03_analysis/results/weights.*` | 权重是否集中在少数 donor 或异常时期 |
| In-space placebo | `03_analysis/robustness/in_space_placebo.*` | treated 效应在 donor placebo 中是否异常 |
| In-time placebo | `03_analysis/robustness/in_time_placebo.*` | 假政策时点是否不产生同样效应 |
| Leave-one-out | `03_analysis/robustness/leave_one_out.*` | 结论是否依赖单个 donor |
| SDID/DiD contrast | `03_analysis/results/sdid_or_did_contrast.*` | 替代估计是否方向一致或差异可解释 |

**Hard fail**

- pre-fit 很差却把 post gap 写成因果。
- donor pool 事后挑选且无日志。
- placebo 显示 treated 不特殊。

**允许 claim**

- `causal`：treated unit/time window 的局部政策效应。
- `qualified_causal`：pre-fit 或 placebo 边界需显式披露。
- `descriptive`：case-study pattern only。

---

## 5. Panel FE / HDFE / Observational Controls

**适用**：面板固定效应、相关性主分析、高维固定效应。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| Variation audit | `03_analysis/results/variation_audit.*` | treatment variation 是否被 FE 吸收 |
| Singleton/drop log | `02_data/sample_audit.md` | HDFE 或清洗是否改变 estimation sample |
| FE/specification curve | `03_analysis/robustness/spec_curve.*` | 控制和 FE 选择是否驱动结果 |
| Alternative SE | `03_analysis/robustness/alt_se.*` | cluster、two-way、wild/bootstrap 是否合理 |
| Covariate timing screen | `03_analysis/design_register.md` | controls 是否 pre-treatment，是否误控 mediator |
| Influence/outlier check | `03_analysis/robustness/influence.*` | 单位/年份/行业是否驱动结果 |

**Hard fail**

- FE 后核心 variation 几乎不存在。
- post-treatment controls 被当作 baseline controls。
- 聚类层级错配导致主显著性消失但未披露。

**允许 claim**

- `causal`：仅当有独立外生变异或自然实验逻辑补足。
- `descriptive`：一般 FE + controls 的默认强度。
- `exploratory`：spec curve 不稳或强依赖控制集。

---

## 6. DML / HTE / Causal Forest / ML Causal

**适用**：高维 controls、orthogonal scores、CATE/HTE、policy learning。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| Split/cross-fitting log | `03_analysis/results/crossfit.*` | folds、seed、sample split 是否固定 |
| Nuisance diagnostics | `03_analysis/results/nuisance_metrics.*` | outcome/treatment nuisance 是否有合理性能 |
| Overlap / propensity support | `03_analysis/results/overlap.*` | 稀有 treatment cells 是否支撑估计 |
| Orthogonal score check | `03_analysis/results/orthogonal_score.*` | estimator 是否确为 DML/DR/orthogonal |
| Seed/model stability | `03_analysis/robustness/seed_stability.*` | 结论是否依赖随机种子或 learner |
| HTE calibration | `03_analysis/results/hte_calibration.*` | CATE 是否校准，分组效应是否稳定 |
| Policy value / subgroup guardrail | `03_analysis/robustness/policy_value.*` | policy claim 是否超出 HTE 稳定区域 |

**Hard fail**

- train/test leakage 或 post-treatment features 混入。
- 只展示 variable importance，却把它写成机制。
- CATE 不稳定仍作为主贡献。

**允许 claim**

- `causal`：orthogonal ATE/LATE 且 overlap 与 seed stability 过关。
- `qualified_causal`：HTE/CATE 作为带不确定性的机制线索。
- `exploratory`：policy/subgroup 结果未通过稳定性。

---

## 7. Causal Graph + Refutation

**适用**：DAG-driven identification、DoWhy-style identify-estimate-refute、复杂因果路径。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| DAG source | `03_analysis/design_register.md` 或 `03_analysis/results/dag.*` | 节点、边、假设来源是否清楚 |
| Adjustment set | `03_analysis/results/identified_estimand.*` | 识别集是否不含 mediator/collider |
| Refuters | `03_analysis/robustness/refuters.*` | placebo treatment、random common cause、subset/refit 是否稳 |
| Sensitivity | `03_analysis/robustness/sensitivity.*` | unobserved confounding 需要多强才推翻 |
| Claim boundary | `00_meta/evidence_ledger.md` | graph claim 是否限定在图假设成立条件下 |

**Hard fail**

- DAG 边凭空假设，无文献/制度/数据来源。
- adjustment set 包含 mediator/collider。
- refuter 失败但不降级。

**允许 claim**

- `causal`：only under stated graph assumptions。
- `qualified_causal`：refuter 边界披露。
- `descriptive`：graph 只作理论组织工具。

---

## 8. Prediction-Assisted / Text-as-Data / Embeddings

**适用**：ML controls、文本变量、LLM/embedding features、预测辅助实证。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| Label/data provenance | `02_data/codebook.md` | 标签或文本来源、标注规则、版权/隐私边界 |
| Leakage audit | `02_data/sample_audit.md` 或 `03_analysis/results/leakage_audit.*` | features 是否含 outcome/post-treatment 信息 |
| Train/test or validation split | `03_analysis/results/validation.*` | 预测任务是否有 out-of-sample 评估 |
| Human-valid labels | `03_analysis/results/label_audit.*` | 标签质量、inter-rater 或 spot check |
| Feature timing screen | `03_analysis/design_register.md` | embedding/text features 的时间戳是否早于 treatment/outcome |
| Sensitivity to model choice | `03_analysis/robustness/ml_model_stability.*` | 不同模型/embedding 是否改变结论 |
| Interpretability boundary | `00_meta/evidence_ledger.md` | 预测特征是否只作 measurement，而非未经验证的机制 |

**Hard fail**

- leakage 存在且影响主估计。
- LLM/embedding 产物无法复现、版本不可追踪。
- 文本/标签含 PII 或受限内容却进入公开包。

**允许 claim**

- `causal`：只有当预测变量只是 pre-treatment measurement 且主识别设计独立通过。
- `qualified_causal`：measurement error 和 model stability 已披露。
- `exploratory`：文本机制或 subgroup 发现未通过稳定性。

---

## 9. Time Series / VAR / 协整 / 单位根

**适用**：宏观或金融时间序列、VAR/SVAR、脉冲响应、Granger 因果、协整/VECM、预测辅助实证。
对应路由 `67/time-series`（StatsPAI `var`/`irf`/`arima`/`johansen`/`vecm`）。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| Stationarity / unit-root test | `03_analysis/results/unit_root.*` | 每条序列的 ADF/PP/KPSS 与单整阶数 `I(d)`；差分决策是否一致 |
| Lag-order selection | `03_analysis/results/lag_select.*` | AIC/BIC/HQ 选阶过程是否报告，而非默认拍脑袋 |
| Cointegration check | `03_analysis/results/cointegration.*` | 若序列 `I(1)`，是否做 Johansen/Engle-Granger 并据此选 VAR-in-diff vs VECM |
| Model stability | `03_analysis/results/stability.*` | 伴随矩阵特征根是否在单位圆内；系统是否平稳可逆 |
| Residual diagnostics | `03_analysis/robustness/residual_diag.*` | 残差自相关(LM)、异方差、正态是否检验并通过 |
| Shock identification | `03_analysis/design_register.md` | IRF 的识别方案（Cholesky 排序 / 符号或零约束）及其制度理由 |
| Ordering / scheme sensitivity | `03_analysis/robustness/irf_ordering.*` | 改变排序或识别约束后 IRF 结论是否稳健 |
| Structural break screen | `03_analysis/robustness/structural_break.*` | 全样本是否含 Bai-Perron/Zivot-Andrews 断点，是否分段或控制 |
| IRF/forecast inference | `04_results/irf_plot.*` | 脉冲响应/预测的 bootstrap 或解析置信带是否报告 |

**Hard fail**

- 对 `I(1)` 且不协整的序列直接跑水平 VAR（伪回归风险）。
- 报告 IRF 却无任何识别方案或排序理由，把 reduced-form 相关写成结构冲击。
- 完全未做单位根/平稳性检验就建模。
- 系统不稳定（特征根在单位圆外）仍按常规区间做推断。
- 样本跨越明显结构断点却既不分段也不控制。
- 把 Granger 因果（预测性）直接写成结构性/政策性因果。

**允许 claim**

- `causal`：仅限识别可信的结构冲击（SVAR 的零/符号约束有制度或文献支撑）且系统稳定、诊断通过。
- `qualified_causal`：reduced-form IRF，排序/识别敏感性已显式披露且方向稳健。
- `descriptive`：Granger 因果、动态相关、预测表现——不得用结构性因果措辞。
- `exploratory`：系统不稳、协整结论摇摆或诊断不过。

---

## 10. Method Gate 填写规则

`03_analysis/method_gate.md` 必须把本文件对应设计卡复制或摘要成一张表：

```markdown
## Design Gate Card

Design card used: DiD / IV / RDD / SC-SDID / Panel FE / DML-HTE / DAG-refuter / Prediction-assisted / Time Series-VAR

| Gate item | Required artifact | Path | Present? | Pass? | Claim consequence |
|---|---|---|---:|---:|---|
| <item> | <artifact> | <path> | yes/no | yes/no | causal / qualified_causal / descriptive / exploratory / no_claim |
```

填完后同步：

- `workflow_state.json.method_gate.required_artifacts`：列出本设计卡的 required artifact 路径。
- `workflow_state.json.method_gate.missing_artifacts`：列出 `Present? = no` 或 `Pass? = no` 的项。
- `workflow_state.json.evidence_governance.claim_strength`：主 claim 最强允许等级。
- `00_meta/evidence_ledger.md`：每条 manuscript claim 只能使用不高于该等级的措辞。

若存在任何 hard fail，`method_gate.status` 必须是 `not_pass`，或者主 claim 必须降级到
`descriptive` / `exploratory` 并在 evidence ledger 的 Open Discrepancies 中写明。
