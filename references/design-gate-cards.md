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

## 10. PSM-DID / 截面匹配 + DID（Heckman-Robbins 组合）

**适用**：横截面或单期处理数据 + 大量可观测协变量的政策评估；
经典场景是"处理非随机但有大量协变量"+ "同一处理时点"——中国实证中最常见的"两期 PSM-DID"。
**重要提示**：AER/QJE/JPE 这两年（2022-2026）对纯 PSM-DID 的口径已偏严——理由是 Rosenbaum / Abadie / Heckman 等早就指出 PSM 不能解决未观测异质性/选择。**只要数据有时间维度（哪怕只有 2 期），优先用 Callaway-Sant'Anna / Sun-Abraham / Borusyak-Jaravel-Spiess（见 §1）。纯截面 + 匹配 → 只能解释为"伪 DiD"或"反事实路径"**。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| 协变量平衡表 | `03_analysis/results/psm_balance.*` | 匹配前后 treated/control 在所有协变量上的 SMD 是否 < 0.1（或 0.25 for some journals） |
| 共同支持诊断 | `03_analysis/results/common_support.*` | propensity score 的共同区间；trim 掉的样本比例 |
| PS 模型设定 | `03_analysis/design_register.md` | logit/probit 用了哪些协变量；是否含 treatment 前/后的"坏控制" |
| 匹配方法 + caliper | `03_analysis/results/matching_method.*` | 1:1 / 1:K、with/without replacement、caliper 宽度；近邻法的距离 |
| 双重差分估计表 | `03_analysis/results/psm_did_main.*` | 4 个均值：treated_pre、treated_post、control_pre、control_post；或 DID 回归 |
| 共同支持可视化 | `03_analysis/results/ps_density.*` | 两组 propensity score 分布叠加图 |
| 替代匹配方法 | `03_analysis/robustness/alt_matching.*` | 近邻 / 卡尺 / 核匹配 / 半径匹配 / 优化匹配 / 加权 IPW 结果是否一致 |
| 替代协变量集 | `03_analysis/robustness/alt_covariates.*` | 加/减协变量后结果是否稳健 |
| 加权 vs 匹配对比 | `03_analysis/robustness/ipw_vs_psm.*` | IPW-DID 与 PSM-DID 结果是否一致 |
| **时间维度声明** | `03_analysis/design_register.md` | 显式说明"为什么不能用现代交错 DID"——若可（哪怕 2 期），应优先 CS/SA/BJS（§1） |
| 隐藏偏差诊断 | `03_analysis/robustness/rosenbaum_bounds.*` | Gamma 敏感性：多强未观测异质性才能推翻结论 |

**Hard fail**

- **横截面声称因果** 而没有显式承认"协变量控制了所有可观测选择"的局限。
- 协变量包含 **post-treatment / mediator** 变量（坏控制，G6）。
- 平衡表 SMD > 0.25 且不报告。
- 共同支持区间几乎为空（两组 propensity score 几乎不重叠）仍报 ATT。
- **未做 Rosenbaum bounds / Gamma 敏感性** 却报告精确 p 值。
- 用"PSM 解决了选择偏差"作为主论点（必须改用"在可观测协变量上平衡"的弱表述）。

**允许 claim**

- `causal`：仅在以下三个条件**同时满足**时：
  1. 数据**真有 2 期或更多**（建议改用 §1 现代 DiD 估计）；
  2. 平衡诊断与 Rosenbaum bounds 全部过关；
  3. 在 cover letter 显式说明局限。
- `qualified_causal`：标准情况——有合理平衡、稳健性一致、但承认"不可观测异质性未排除"。
- `descriptive`：单期横截面、平衡诊断不理想、或无敏感性分析时。
- `exploratory`：共同支持差 + Rosenbaum bounds 早推翻结果。

**降级触发**：任何 hard fail → 至少降 `descriptive`；未做敏感性 → 至少降 `qualified_causal` 且必须补做。

---

## 11. 空间计量（Spatial Durbin / SAR / SEM / SDM）

**适用**：数据存在空间依赖（地理邻近、区域溢出、网络效应）且研究问题涉及溢出。
中国实证常见场景：地方政府竞争（GDP 锦标赛）、区域创新扩散、环境污染溢出、城市群集聚效应。
**重要提示**：空间计量在国内顶刊（《经济研究》《管理世界》《中国工业经济》）接受度高，但在 AER/QJE 等英文顶刊中近年更倾向用 network interference / spillover 估计（见 `67/interference` 等）。**中国语境下写作时强调"空间溢出"和"区域协同"是常规路径**。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| 空间权重矩阵说明 | `03_analysis/design_register.md` + `02_data/spatial_weights.*` | queen/rook/distance/k-NN；行标准化方法；是否 row-standardized |
| 权重矩阵敏感性 | `03_analysis/robustness/w_specs.*` | 不同 k-NN（如 5/8/10）、不同距离阈值结果是否一致 |
| Moran I 检验 | `03_analysis/results/moran_i.*` | 残差与因变量是否空间相关；不显著时不该用 SDM |
| LM 检验序列 | `03_analysis/results/lm_tests.*` | LM-Lag、LM-Error、R-LM-Lag、R-LM-Error；按 Anselin 2005 决策表选模型 |
| Hausman 检验 | `03_analysis/results/spatial_hausman.*` | 固定 vs 随机效应选择 |
| 估计表 | `03_analysis/results/spatial_main.*` | SAR / SEM / SDM / SAC / SDEM 系数表 + 空间自回归系数 ρ |
| 直接/间接效应分解 | `03_analysis/results/spatial_decomposition.*` | LeSage & Pace 2009 偏微分分解：direct + indirect + total effect |
| **直接 vs 间接效应** | `03_analysis/results/spatial_decomposition.*` | SDM 中 indirect 才是空间溢出的核心；必须显式报告 |
| 共同因子检验 | `03_analysis/robustness/spatial_common_factor.*` | SDM 是否能 collapse 为 SAR / SEM；W*X 是否可忽略 |
| 异质性空间效应 | `03_analysis/robustness/heterogeneous_spatial.*` | 不同子样本/不同时期空间效应是否稳定 |
| ML vs GMM 对比 | `03_analysis/robustness/ml_vs_gmm.*` | ML（默认）vs GMM 在小样本下结果是否一致 |

**Hard fail**

- **未报告空间自回归系数 ρ**（这是空间计量的灵魂），只报 X 系数。
- 未做 LeSage-Pace 偏微分分解就把"空间系数"等同于"溢出效应"（混淆点估计与平均效应）。
- **Moran I 不显著** 但仍跑 SDM。
- 权重矩阵事后挑选（"试到显著为止"，G10）。
- 把空间系数解释为"该地区对其他地区的因果效应"（应该用 partial derivative 解释）。
- 权重矩阵未标准化（导致 ρ 数量级不可比）。

**允许 claim**

- `causal`：在以下条件**同时满足**时：
  1. 空间识别假设（空间 DGP）合理；
  2. ρ 显著、分解效应（特别是 indirect）显著且稳健；
  3. 权重矩阵有制度/地理依据。
- `qualified_causal`：标准情况——ρ 显著但权重矩阵选择有主观性；或空间 DGP 可能误设。
- `descriptive`：仅当 Moran I 显著、ρ 显著、但没做完整分解。
- `exploratory`：ρ 不显著，或权重矩阵过敏感。

**降级触发**：权重矩阵无制度依据 → 至少 `qualified_causal`；无偏微分分解 → 至少 `qualified_causal` 且补做；Moran I 不显著仍用 SDM → 强制降 `descriptive`。

---

## 12. 门槛面板回归（Threshold Panel — Hansen 1999 / Kremer et al. 2009）

**适用**：异质性效应依赖某个门槛变量（如收入、规模、年龄、环境规制强度）；中国实证最常用：环境规制 vs 企业创新、金融发展 vs 经济增长、政府规模 vs 民间投资。
**重要提示**：门槛面板在国内顶刊接受度极高，但**方法学批评也多**：
1. 单一门槛假设强（实际常有多门槛或未知函数形式）；
2. Bootstrap 临界值表在样本量 < 200 时不稳；
3. **门槛值是估计量而非已知值**，但很多论文误把门槛值当外生给定。
优先考虑 Hansen (2000) bootstrap 检验、Bai (1997) 多门槛、Caner-Hansen (2004) 渐近分布修正。

| Required artifact | Path pattern | 必须回答 |
|---|---|---|
| 门槛值显著性检验 | `03_analysis/results/threshold_test.*` | Hansen 1996 / Hansen 1999 bootstrap 检验 p 值；单一/多门槛的 LR 统计量 |
| 门槛值置信区间 | `03_analysis/results/threshold_ci.*` | Hansen (1999) LR 似然比法构造的 95% CI |
| 门槛效应分区间表 | `03_analysis/results/threshold_regimes.*` | regime 1 vs regime 2 系数表；系数跳变点 |
| Bootstrap 临界值表 | `03_analysis/results/bootstrap_critical.*` | 至少 1000 次（理想 5000+）bootstrap 后的 LR 统计量分布 |
| 多门槛检验 | `03_analysis/robustness/multi_threshold.*` | 是否检验双门槛、三门槛；不同门槛数下结果对比 |
| 线性 vs 门槛对比 | `03_analysis/robustness/linear_vs_threshold.*` | 门槛模型的 LR 检验拒绝线性吗？ |
| 门槛值稳健性 | `03_analysis/robustness/threshold_grids.*` | 改变门槛搜索网格（更细/更粗）结果是否一致 |
| 异质性分析 | `03_analysis/robustness/threshold_heterogeneity.*` | 不同子样本/不同时期门槛值是否稳定 |
| 内生性处理 | `03_analysis/design_register.md` | 门槛变量是内生的吗？若内生，需要 IV-threshold（如 Caner-Hansen 2004） |
| 时间/个体效应 | `03_analysis/design_register.md` | 是否控制了个体/时间固定效应；FE-threshold 模型还是 pooled threshold |
| 三种 estimator 对比 | `03_analysis/robustness/three_estimators.*` | Hansen (1999) vs Bai (1997) vs Caner-Hansen (2004) 结果是否一致 |

**Hard fail**

- **未做门槛显著性检验**（如直接报告"找到门槛值 X"）——这是门槛面板最常见的硬伤。
- Bootstrap 重数 < 500（结果不可信）。
- **把门槛值当作已知值**而非估计量（必须报告 CI）。
- 单门槛模型但门槛值选择不合理（如把样本均值当门槛）。
- 门槛内/外样本量 < 30（系数估计不可信）。
- 门槛值高度依赖样本期/子样本（说明模型过拟合）。
- 协变量含 post-treatment 变量（G6）。
- 跨门槛的系数差异**仅由样本量差异**驱动（如 regime 1 n=500、regime 2 n=20）。

**允许 claim**

- `causal`：门槛检验显著、CI 较窄、效应稳健。
- `qualified_causal`：门槛检验显著但 CI 较宽；或门槛值在不同子样本间略变；或 Bootstrap 临界值不稳。
- `descriptive`：门槛检验不显著、效应分区间异质但门槛值本身不稳。
- `exploratory`：多门槛模型结果矛盾；或 IV-threshold 与 OLS-threshold 矛盾。

**降级触发**：未做 bootstrap 检验 → 强制降 `descriptive`；门槛 CI 跨多个候选门槛值 → 至少 `qualified_causal`；门槛值因子样本大幅漂移 → 至少 `descriptive`。

---

## 13. 跨设计行为护栏（Behavioral Guardrails — 反模式黑名单）

> 上面每张卡管「这个设计需要哪些证据」；本节管「**不管哪个设计，都不许犯的操作错误**」。
> 思路来自 Econometrics-Agent（*Can AI Master Econometrics?* arXiv 2506.00856）的关键发现：
> LLM 跑计量最容易翻车的不是估计器选错，而是把**机器学习/预测的习惯**带进**因果估计**——
> 它在工具层硬编码了一批「行为护栏」（如禁止在计量任务里做 train/test split）。本节把这套护栏
> 上移到闸门层：命中任意一条即按「claim 后果」列降级或 `NOT PASS`，并在
> `03_analysis/method_gate.md` 的 **Hard Flags** 段逐条记 `clear/hit`。

| # | 反模式（命中即触发） | 为什么在因果语境是错的 | 正确默认 | claim 后果 |
|---|---|---|---|---|
| G1 | 把估计样本做 **train/test split** 去"验证"因果系数 | 因果 estimand 不是预测精度；split 不检验识别，只检验拟合 | 唯一正当用法：DML 对 **nuisance 函数**做 cross-fitting（不是对目标系数）；其余一律不切 | 主因果 claim → `NOT PASS` 或降 `exploratory` |
| G2 | 默认 **经典同方差 SE**（不报 robust/clustered） | 微观面板异方差/簇内相关几乎必然，经典 SE 系统性低估不确定性 | 默认 robust，聚类层级 **≥ 处理赋值层级**，并写进 `inference_report.md` | 显著性可疑 → 稳健性维度封顶；改聚类翻号未披露 → `NOT PASS` |
| G3 | 按 **因变量** 删"异常值"/截尾 | 基于 outcome 选样本 = 选择性截断，直接偏误系数 | 只基于协变量/预处理量对称 winsorize；删样本走 `sample_audit.md` 记原因 | 主 claim 降 `qualified_causal`；影响主结果未披露 → `NOT PASS` |
| G4 | **标准化/缩放 0/1 处理变量**（z-score treatment） | 破坏二元处理的可解释性与 LATE/ATT 含义，系数不再是"被处理 vs 未处理" | 处理 dummy 保持原始 0/1；只标准化连续协变量（若需要） | 解读维度封顶；量级解释失真 |
| G5 | 回归前对 **outcome / treatment 无依据插补** | 均值/常数插补因变量或处理是在**制造方差**，稀释或伪造效应 | 先按 `empirical-audit.md` 诊断 missingness 机制，再决定删/插补/建模 | `empirical_audit.status=not_pass`；插补驱动结果 → `NOT PASS` |
| G6 | 把 **post-treatment / mediator** 变量当 baseline control | 坏控制阻断或反转因果通道（见 `mechanism-and-channels.md` §3） | controls 必须 pre-treatment；中介移出主设定，单独做机制 | 主设定含坏控制 → 识别维度封顶 4 / `NOT PASS` |
| G7 | **不声明 FE 维度**、依赖 PanelOLS/HDFE 默认 | 默认吸收维度可能错配 estimand，singleton drop 静默改样本 | 显式声明 entity/time/吸收维度与 singleton 处理，记 `design_register.md` | 复现维度封顶；variation 被吸收未披露 → `NOT PASS` |
| G8 | 把 **高 R² / 拟合优度** 当因果或机制证据 | predictive fit ≠ identification；过拟合也能高 R² | 因果强度只由识别设计与稳健性决定，不引用 R² 作证 | 解读维度封顶；当主证据 → 降 `descriptive` |
| G9 | 少簇（G≲30–50）仍只报 **渐近 p 值** | 渐近近似在少簇下崩坏，t 比虚高 | wild cluster bootstrap / CR2，见 `inference-and-uncertainty.md` §3 | 稳健性维度封顶 5；主显著性靠它 → `NOT PASS` |
| G10 | 用同一数据 **既挑设定又做推断** 且不披露 | 研究者自由度 / specification search 制造假阳性 | 设定曲线 + 预指定主设定（`design-transparency.md`），进 `design_risk_ledger.md` | specification_search 为 blocking → Method Gate 不得 `PASS` |

**强制联动**

- 每条护栏在 `03_analysis/method_gate.md` 的 **Hard Flags** 段逐条记 `clear/hit/na`，命中项必须写缓解或降级。
- G1/G5/G6 同时是 `empirical-audit.md` §2b 的**直接 NOT PASS** 条件——样本/数据审计层与方法闸门双重拦截。
- 想把护栏从「规范」变成「可测」：Stage 3 估计出来后，用
  `python3 evals/check_replication_accuracy.py` 对已知真值（自包含 DiD 案例或已发表复现包）打
  **方向正确 / 完美复现 / 部分复现** 三档分——护栏防的是"方法对、数字错"，benchmark 量的就是数字对不对。

---

## 14. Method Gate 填写规则

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
