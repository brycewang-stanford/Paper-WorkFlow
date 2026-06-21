# Measurement & Data-Quality Pack — 变量测量、构造与数据质量

> 在 Stage 2 数据清洗结束、Stage 3 估计开始前加载（与 [`empirical-audit.md`](empirical-audit.md) 同时）；
> Stage 3 方法闸门与 Stage 7 质量门也要引用。本文件补足一个被反复低估的短板：再干净的识别策略也救不了
> **被测错或构造错的变量**——处理变量误分类、outcome 是噪声代理、winsorize 砍出来的显著、selective merge、
> differential missingness，都会让「方法对、结论错」。**Garbage in 击穿任何 identification。**

---

## 0. 这个增强层解决什么（分工）

实证可信度有三条腿，缺一条都塌：

| 层 | 文件 | 管什么 |
|---|---|---|
| **识别** | [`research-grade-methods.md`](research-grade-methods.md) · [`design-gate-cards.md`](design-gate-cards.md) · [`inference-and-uncertainty.md`](inference-and-uncertainty.md) | 这个设计需要哪些方法证据、推断口径对不对 |
| **测量** | **本文件** + [`empirical-audit.md`](empirical-audit.md) | 进入估计器的**每个数字**是否测得准、构造得住、清洗得有纪律 |
| **可复现** | [`reproducibility-pack.md`](reproducibility-pack.md) | 第三方能不能一键重跑、数据来源是否交代清楚 |

与 [`empirical-audit.md`](empirical-audit.md) 的边界要分清：

- `empirical-audit.md` 管 **样本会计与 estimand 对齐**——raw→clean→estimation sample 的流失、treated/control 计数、
  聚类层级，是「数据**够不够**支持那个 estimand」。
- **本文件**管 **测量计量学**——每个变量测得准不准、误差往哪个方向偏、异常值/缺失/合并处理得有没有纪律，
  是「这些数字**可不可信**、偏到哪里去」。两者都过，结果才进写作。

**最低标准（5 条）：**

1. **构念效度可辩护**：每个关键变量（treatment、outcome、核心 control、mechanism proxy）都说清「想测的构念
   → 实际用的代理 → 两者的缺口」，并交代缺口会引入什么偏。
2. **测量误差被刻画**：是 classical 还是 non-classical / differential；偏向 0 还是不定向；尤其 **treatment 端**
   的误分类要单独评估，不能默认「测准了」。
3. **异常值/winsorize/变换有纪律**：阈值在看处理-结果关系**之前**定好、对称施加、并报告对该选择的稳健性。
4. **合并/缺失/面板完整性有诊断**：match rate、`_merge` 分布、differential missingness、重复键、look-ahead 泄漏
   都落表/落图，不是口头「数据干净」。
5. **测量决策回流**：写入 `02_data/measurement_audit.md`，并喂给 `sample_audit.md` §3–4 与
   `workflow_state.json.empirical_audit.{construct_validity, missingness_balance}`。

---

## 1. 构念效度与操作化（construct validity）

论文测的从来不是构念本身，而是一个**代理（proxy）**。代理与构念之间的楔子（wedge）就是偏误的来源。

- **三步交代**：① 想测的构念是什么；② 实际用的变量是什么；③ 两者差在哪、这个差会让估计**偏向哪**。
  例：用「专利数」代理「创新」→ 漏掉不申请专利的创新、混入策略性低质量专利 → 若处理同时刺激申请倾向，
  treatment 会通过**测量**而非**实质**抬高 outcome（measurement-induced effect）。
- **效度类型（应用化，别堆术语）**：face/content（这个代理合不合常识与制度）、criterion/convergent
  （和已知 benchmark、另一个独立代理对得上吗）、discriminant（会不会其实在测别的东西）。能拿到第二个独立代理做
  相关性核对就核一次。
- **多代理与指数**：同一构念有多个噪声代理时，**预先**说明合成规则——标准化后取均值、Anderson (2008) 的
  inverse-covariance 加权指数、或 PCA 第一主成分；**先定权重再看结果**，避免在多个代理里挑最显著的那个
  （这是 specification search 的一种，见 [`design-risk-ledger.md`](design-risk-ledger.md)）。指数方向要统一（高=更多构念）。
- **代理在不同角色后果不同**：代理当 **control** → 控制不全（proxy control 残留混淆）；当 **treatment** →
  误分类/attenuation（见 §2）；当 **outcome** → 见 §2 因变量端。

---

## 2. 测量误差：后果与补救（计量内核）

测量误差的偏误方向取决于它落在方程哪一端、是不是 classical。把下面这张表当作 Stage 3 解释系数前的强制对照。

| 误差落点 | 类型 | 对 OLS/2SLS 的后果 |
|---|---|---|
| **自变量 X**（核心回归元） | classical（与真值独立、均值 0） | **衰减偏误**：系数偏向 0，bias 因子 = reliability ratio λ = Var(X\*)/Var(X) ∈ (0,1)；多元回归中偏误**会外溢**到其它系数，符号不保证 |
| 自变量 X | non-classical（mean-reverting、与真值/其它变量相关；如自报收入、bracketed、top-coded） | 偏误**方向不定**，可放大也可反向——最危险的一类，不能假设「顶多衰减」 |
| **因变量 Y** | classical | **不偏系数**，只抬高残差方差与标准误（噪声 outcome 损功效但不致命） |
| 因变量 Y | non-classical / **differential by treatment**（处理组与对照组测量精度不同） | **偏误**：differential reporting/recall 直接伪造效应 |
| **处理 D（二元）** | 误分类（misclassification） | **非差异性**（与真值/outcome 独立）误分类 → 衰减；**differential** 误分类则方向不定；DiD 里若**处理时点**测错（误记 first-treated cohort、漏记退出），偏误可能很严重 |

**补救阶梯（按可得性从强到弱）：**

1. **Validation sample / 外部 benchmark**：有一小批「金标准」测量时，估 reliability ratio 或直接校正。
2. **用第二个独立测量做工具变量**：两个含独立误差的代理互为 IV，可一致估计（经典 ME-IV）。路由
   [`statspai-analysis.md`](statspai-analysis.md) 的 `iv` / `ivreg`。
3. **部分识别 / bounds**：没有 instrument 时，给出 set identification 而非硬报点估计（见 §5 缺失界与
   [`design-risk-ledger.md`](design-risk-ledger.md) 的 bounds 讨论）。
4. **误分类专用估计**：DiD 处理误分类用 `did_misclassified`；处理-时点不确定的稳健设定见 `bauer_sinning`。
5. **报告 reliability / 做敏感性**：已知或可估 λ 时报告校正区间；SIMEX 等模拟外推法在 λ 未知时给方向性证据。

> **纪律**：声称「X→Y 因果」前，先回答「如果 X（或 D）测错了，我的估计会偏向哪？这个偏向会不会刚好制造出
> 我看到的结果？」无法排除时，把 claim 退到 `inference-and-uncertainty.md` 与 `evidence_ledger.md` 允许的档位。

---

## 3. 异常值、winsorize、trim 与变换

「在 1/99 winsorize」不是免责声明——**关键是次序与稳健性**。

- **先定规则，再看关系**：异常值/winsorize 阈值（常见 1/99 或 0.5/99.5）、对称性、施加分组，必须在检视
  treatment-outcome 关系**之前**确定并写进 codebook；否则就是 outcome-dependent 的研究者自由度。
- **winsorize vs trim vs robust regression**：winsorize 改值保样本量、trim 删行变 estimand、robust/quantile/Huber
  回归对厚尾更稳。说明为什么选这个，并**报告主结果对该选择的稳健性**（spec curve 思路）。
- **影响诊断**：跑 Cook's distance / DFBETA / leverage，确认主效应不是被极少数单位驱动；报告 with/without 关键单位。
- **变换的坑**：
  - log 处理零值要披露（`log(1+x)` 引入尺度依赖）；
  - **asinh / IHS** 常被当作「能处理 0 的 log」滥用——Chen & Roth (2024) 指出其弹性解释**依赖测量单位**、
    在极端值上行为像线性，半弹性/弹性结论会随单位缩放而变，必须报告单位与稳健性，别直接读成 log 弹性；
  - 比率/人均/平减：分母异常会制造比率 outlier；real vs nominal、PPP vs 名义汇率、base year、季节调整要一致（见 §7）。

---

## 4. 合并 / 匹配 / record linkage 诊断

合并是实证数据集最常见的隐性 bug 源。每一步 join 都要留诊断。

- **键唯一性与粒度**：声明每张表的 grain（unit×time），核两侧键唯一；**`m:1` / `1:1` 明确写出，`m:m` 几乎总是 bug**
  （会做笛卡尔积、悄悄改变 N 与 estimand）。
- **match rate 与 `_merge` 分布**：制表 matched / master-only / using-only 三类计数；问一句**非匹配是否选择性**
  （没匹配上的单位系统性地更小/更穷/更早退出？）——selective non-match = selection on observables/unobservables。
- **模糊匹配 / record linkage**：false-match 与 missed-match 的权衡要交代；linkage error 会变成被链变量的**测量误差**
  （回到 §2）；用 blocking + 抽样人工复核估错配率，别把概率匹配当确定匹配。
- **crosswalk / 时序对照**：行业代码（SIC↔NAICS）、行政区划随时间变更、汇率/价格并表——记清版本与 vintage，
  对照表本身的误差会传导进结果。

---

## 5. 缺失（missingness）

- **机制三分**：MCAR（完全随机）/ MAR（给定观测变量后随机）/ MNAR（与未观测/自身取值相关）。**MNAR 无法被数据
  完全检验**，只能从设计与制度论证——所以要先论证、再选方法。
- **诊断**：missingness by treatment（处理组缺失率显著不同 = differential missingness → 选择性）、缺失模式矩阵、
  缺失与协变量/outcome 的相关。落 `02_data/<missingness_table>`。
- **处理与对应假设**：
  - complete-case（listwise）：仅当缺失对误差**外生**（近 MCAR 或缺失与 outcome 误差独立）才无偏；
  - 多重插补（MI，MAR 下）：impute→estimate→Rubin 合并方差；**不要为因果 estimand 草率插补 outcome**；
  - missing-indicator / dummy-for-missing：除非缺失独立于真值，否则有偏，仅在 control 端谨慎使用并披露；
- **选择性缺失/流失的界**：differential attrition 或 selective missingness 无法消除时，给 **bounds** 而非装作点识别——
  Lee (2009) 在**单调（单边）选择**下的 trimming bounds、Manski / Horowitz-Manski worst-case bounds。路由
  [`statspai-analysis.md`](statspai-analysis.md) 的 `lee_bounds` / `manski_bounds` / `horowitz_manski`；
  与 [`design-risk-ledger.md`](design-risk-ledger.md) 的 selection/attrition 行同源。
- **纪律**：绝不静默 drop 缺失行；每一类缺失都进 `sample_audit.md` §2 的流失流。

---

## 6. 面板与时间结构完整性

- **键与平衡**：核 (unit, time) 无重复；显式 gaps、unbalanced vs balanced、单位进入/退出；说明所选估计器对面板结构的假设
  （FE 吸收、singleton drop、interpolation 是否引入伪变异）。
- **staggered 时点完整性**：first-treated cohort 编码正确、处理**反转/退出**如何处理、never-treated 是否存在
  （决定能否用 CS/SA/BJS，见 [`design-gate-cards.md`](design-gate-cards.md)）。处理时点测错直接污染事件研究坐标。
- **无未来信息泄漏（look-ahead）**：pre-period 不得含处理后才可知的信息；outcome 测量窗口不被处理本身污染；
  滚动/滞后特征不得越界取未来值（ML 辅助实证尤其要查 feature leakage）。
- **日历对齐**：fiscal vs calendar year、时区、季节性、报告期与事件期错位都要核。

---

## 7. 聚合、权重与单位

- **聚合/生态推断偏误**：分析单位与 estimand 目标层级不一致时（个体效应却用地区聚合数据），系数不可外推到个体。
- **权重的 estimand 含义**：analytic / sampling / survey 权重不是一回事——survey/design 权重把样本估计映回目标总体，
  WLS 权重改的是有效率与（异方差下的）estimand。**说清用哪种、为什么，以及加权是否改变了 estimand**。
- **单位一致性**：per-capita 归一、deflator base year、PPP vs 名义、币种、千/百万级别 scale change 全程统一，并与
  codebook 对齐。

---

## 8. Stage 2 输出合同 → `measurement_audit.md`

Stage 2 在 `02_data/clean.parquet`、`codebook.md`、`sample_audit.md` 之外，再生成
`02_data/measurement_audit.md`（模板见 [`../templates/measurement_audit.md`](../templates/measurement_audit.md)），
按 §1–7 逐项填写。它与 `sample_audit.md` 互补：后者管样本流与 estimand 对齐，本表管**每个变量的测量与构造质量**。

写完后更新：

- `workflow_state.json.empirical_audit.construct_validity`（构念效度与测量误差刻画的判定）；
- `workflow_state.json.empirical_audit.missingness_balance`（缺失/合并/面板诊断的判定）；
- `workflow_state.json.artifacts.measurement_audit = "02_data/measurement_audit.md"`；
- `02_data/codebook.md` 的每个派生变量回指构造公式与测量决策。

真实数据未到位时可标 `pending`，但与 `sample_audit.md` 同规则——不得让 Method Gate `PASS`。

---

## 9. 方法闸门与质量门联动（caps，与 `empirical-audit.md` §4 同构）

**Method Gate 直接 `NOT PASS`（必须回退）：**

- 处理 D 的**时点/状态**测错或可能误分类，却无诊断、无 `did_misclassified`/`bauer_sinning`/bounds 补救；
- 面板 (unit, time) 键重复、或 pre-period 含 look-ahead 信息泄漏；
- `m:m` 合并、或非匹配明显选择性却被静默丢弃。

**质量门维度封顶（mirror `empirical-audit.md` §4 的写法）：**

- 关键 treatment/outcome 是噪声代理、且**测量误差方向未刻画** → 识别可信度（维度②）封顶 5；
- non-classical / differential 测量误差**可信存在且未处理** → 识别可信度封顶 4；
- winsorize/trim 在看结果后才定、或不报告对该选择的稳健性 → 稳健性（维度③）封顶 6；
- differential missingness / 选择性 attrition 未处理也未给界 → 结果解读（维度④）封顶 6；
- 变量构造（公式、变换、合并、缺失规则）未在 codebook/measurement_audit 记录 → 可复现性（维度⑦）封顶 6。

> 质量门可比方法闸门严、不可松：`measurement_audit.md` 暴露的硬测量问题若影响主结论，对应维度按上表封顶，
> 不得靠语言包装绕过。

---

## 10. 反模式清单（出现即标红）

- 「我们在 1/99 winsorize」当免责声明，却不报告对截断点的稳健性；
- 把 asinh / IHS 当「能吃 0 的 log」，直接读成弹性，不报单位与稳健性；
- 自报 / 调查 / 平台抓取代理当 ground truth，从不评估测量误差；
- `m:m` 合并；或只报 match rate、不查非匹配是否选择性；
- 为做因果 estimand 草率插补 outcome，再跑回归；
- 「missing at random」当口头结论下，无机制论证、无 differential-missingness 诊断；
- 删异常值删到显著为止（outlier mining）；
- 处理变量明显误分类，却默认「衰减顶多让我保守」——non-classical 误差并不保证只衰减。

---

## 11. 锚点（按需查证，别凭记忆脑补）

- 测量误差综述与后果：Bound, Brown & Mathiowetz, "Measurement Error in Survey Data," *Handbook of Econometrics* Vol. 5 (2001), pp. 3705–3843；
  Schennach, "Recent Advances in the Measurement Error Literature," *Annual Review of Economics* 8 (2016), 341–377。
- 指数合成：Anderson, "Multiple Inference and Gender Differences in the Effects of Early Intervention," *JASA* 103(484) (2008), 1481–1495（inverse-covariance 加权指数）。
- 变换尺度依赖：Chen & Roth, "Logs with Zeros? Some Problems and Solutions," *QJE* 139(2) (2024), 891–936（asinh/IHS 单位敏感）。
- 选择性流失的界：Lee, "Training, Wages, and Sample Selection: Estimating Sharp Bounds on Treatment Effects," *REStud* 76(3) (2009), 1071–1102（单调选择 trimming bounds）；
  Manski 部分识别系列（worst-case bounds）。
- 处理误分类：参见 `statspai` 的 `did_misclassified` / `bauer_sinning` 工具文档与其引用。

> 引用以真实查证为准（`reference-verify` / `bibtex`），上面是定位锚点而非可直接粘贴的参考文献；写进论文前必须核验
> 卷期页与作者。
</content>
</invoke>
