# Design-Transparency Pack — 设计透明度与预分析纪律

> 在 Stage 1 末/Stage 3 初定分析方案、Stage 3 跑稳健性、Stage 5 写结果段（尤其空结果）、收尾打包时加载。
> 本文件把「可信性革命」之后顶刊看重的**过程纪律与透明度**落成可执行清单：预分析计划 → 功效/最小可测
> 效应 → 预趋势功效 → 设定曲线 → 研究者自由度披露。
>
> **分工**：[`research-grade-methods.md`](research-grade-methods.md) 管「选哪个估计量、每种方法落盘哪些诊断」
> （是识别的**内容**）；本文件管「**何时**锁定决策、**预先**指定什么、**披露**了什么」（是过程的**时序与
> 透明度**）。换句话说：method gate 问「证据对不对」，本层问「你是不是先定方案再看结果、有没有把研究者
> 自由度摊在阳光下」。两者正交，互不重复。
>
> **不确定性配套**：本文件 §2 PAP 要求**预先指定多重检验校正方案**、§3 报 MDE；这些方案的**具体推断口径**
> （family 怎么划、Romano-Wolf / sharpened q-value 怎么选、空结果的 MDE 与 few-cluster 推断怎么算）见
> [`inference-and-uncertainty.md`](inference-and-uncertainty.md)。本层管「先承诺什么」，inference pack 管「承诺的口径怎么落地」。

---

## 0. 这个增强层解决什么

同一份数据，换几个「都说得通」的设定，常常能把任何结果跑成显著——这就是 p-hacking 与「分叉路径」。
现代顶刊（尤其 AEA 体系）越来越用**过程透明度**而非单一显著系数来判断可信度。本层要求：

1. **先定方案再看结果**：估计前把假设、主结果、设定、子样本写死（预分析计划/预注册），事后区分
   「预先指定」与「探索性」。
2. **空结果要报功效**：不显著 ≠ 无效应；必须报最小可测效应（MDE），说明「能排除多大的效应」。
3. **DiD 预趋势要报功效**：不靠「pre-trend 看起来平」，而是报预检验功效 + HonestDiD 破点（呼应
   [`threats-to-validity.md`](threats-to-validity.md) §4）。
4. **设定不挑樱桃**：用设定曲线/multiverse 展示**整条**设定阶梯，而非最漂亮的那一格。
5. **研究者自由度摊开**：把样本切分、控制集、变量编码、剔除规则这些「自由度」列成披露表，注明哪些
   是预先指定的。

> 本层是**透明度标尺**，不替代任何估计 skill。预注册落到 OSF/AEA registry；功效与设定曲线由估计脚本
> 产出；本文件只规定「做到什么程度、披露成什么样才算达标」。

---

## 1. 外部锚点（透明度实践的权威入口）

| 实践 | 首选入口 | 何时用 |
|---|---|---|
| 预分析计划 / 预注册 | AEA RCT Registry: https://www.socialscienceregistry.org/ ｜ OSF: https://osf.io/ ｜ J-PAL 指南: https://www.povertyactionlab.org/resource/pre-analysis-plans | Stage 3 估计前登记 |
| 「设计先于分析」原则 | Rubin (2008), *For objective causal inference, design trumps analysis*: https://arxiv.org/pdf/0811.1640 | Stage 1/3 分离设计与分析 |
| 透明度与可复现总览 | Christensen & Miguel (2018, JEL): https://www.aeaweb.org/articles?id=10.1257/jel.20171350 | 全程：透明度规范 |
| 预趋势功效 | Roth (2022, AER:Insights): https://www.aeaweb.org/articles?id=10.1257/aeri.20210236 | DiD/事件研究的预趋势 |
| 平行趋势敏感性 | Rambachan & Roth (2023, ReStud): https://academic.oup.com/restud/article-abstract/90/5/2555/7039335 | 报告平行趋势违背的破点 M |
| 设定曲线分析 | Simonsohn, Simmons & Nelson (2020, Nat Hum Behav): https://www.nature.com/articles/s41562-020-0912-z | 设定敏感性、稳健性附录 |
| Multiverse 分析 | Steegen et al. (2016, PPS): https://journals.sagepub.com/doi/10.1177/1745691616658637 | 数据构造选择的多重宇宙 |
| 研究者自由度 / 分叉路径 | Simmons-Nelson-Simonsohn (2011): https://journals.sagepub.com/doi/abs/10.1177/0956797611417632 ｜ Gelman & Loken (2013): https://sites.stat.columbia.edu/gelman/research/unpublished/p_hacking.pdf | 披露自由度、控制假阳性 |
| AEA 透明度/可复现政策 | AEA Data Editor: https://www.aeaweb.org/research/transparency-reproducibility-credibility-economics | 目标 AEA 体系期刊时 |

> 这些是透明度标准锚点，不是硬依赖。能联网就按官方入口实现；不能就用工作区脚本产出 MDE 与设定曲线，
> **缺了就在 `method_gate.md`/质量门标明，而不是静默省略**。

---

## 2. 预分析计划（PAP）与预注册——先定方案再看结果

**核心原则（Rubin）**：把研究分成**设计阶段**（不看结果数据，定样本、匹配、控制、设定）与**分析阶段**
（看结果跑估计）。设计阶段做的决策天然不受结果驱动，因此可信。

**PAP 应写清**（估计前登记到 OSF 或 AEA registry，时间戳是它的全部价值）：
- 研究假设（主 + 次）；
- 主结果变量与次要结果变量（**预先点名**，避免事后挑最显著的当主结果）；
- 估计方程与识别策略；
- 控制变量集合；
- 子样本/异质性维度；
- 多重检验校正方案；
- 样本纳入/剔除/磨损处理规则。

**实验 vs 观察性**：
- **实验/RCT**：PAP 是标配，登记 AEA RCT Registry。
- **观察性**：在拿到结果数据前**锁定设计**（匹配方案、控制集、样本窗口），并在论文里声明哪些分析是
  预先指定、哪些是探索性。即便不正式预注册，这种「design-before-outcomes」的纪律也是可信度信号。

**落盘**：PAP 副本或外部预注册链接（OSF/AEA registry）放 `01_proposal/pre_analysis_plan.md`；论文方法段加
一句「Deviations from PAP」说明任何偏离及原因。

---

## 2.1 可执行预注册锁（executable lock）——把「先定方案」变成机械闸门

PAP 的全部价值在于**时间戳**：方案锁定在看结果之前。但散文承诺可被事后悄悄改写，因此本 skill 用一个
**可执行的锁**把这条不变量做成 `exit 1`，而不是靠自觉。这正是相对 Orchestra「git 即预注册（纯散文自评）」
的差异化——我们让它**可被脚本判定**。

1. **实例化** `templates/preregistration.md` → 工作区 `00_meta/preregistration.md`（与其它治理锁同住 00_meta）。
   填 Lock Status（`locked` 时间戳、`lock_commit`、`locked_before_estimation: yes`、analyst、primary_design）、
   至少一条 **Confirmatory Hypotheses**（含 Y/estimand/主设定/预测符号）、Primary Specification Lock（含聚类、
   多重检验方案）、Confirmatory vs Exploratory 与 Deviations from Plan。
2. **锁定**：在跑出 `03_analysis/results/main_results.json` **之前**提交，记下 `lock_commit`。
3. **校验**：`python3 scripts/check_preregistration.py <workspace>`。硬不变量——**有主结果却没锁、或
   `locked_before_estimation` 非 yes，即研究者自由度违规，直接 FAIL**；未锁但还没有结果只是 INFO（未完成不算违规）。

> **与 Method Gate 的硬挂钩**：DiD/IV/RDD 等确认性主张要写成「预先指定的检验」，前提是它在
> `00_meta/preregistration.md` 锁内；**任何不在锁内的主结果一律降级为 exploratory（描述性/提示性措辞）**。
> 锁未通过（`check_preregistration.py` 返回非零）→ 选择性报告风险未关 → Method Gate 不得 `PASS`
> （记入 `03_analysis/design_risk_ledger.md` 的 specification_search / 选择性报告行）。

---

## 3. 功效与最小可测效应（MDE）——空结果的必修课

「系数不显著」可能是**真的无效应**，也可能是**样本太小检不出来**。reviewer 会直接问：你的零结果是不是
功效不足？答案就是报告 **MDE（minimum detectable effect）**：在给定样本、方差、80% 功效下，本设计能可靠
侦测到的最小效应。

- **空/精确零结果**：在结果段写「我们能排除大于 X 的效应」（X = MDE），把「没找到」变成「找到了一个有
  信息量的上界」。
- **报 MDE 而非事后功效**：事后用观测效应算的 power 不可靠；MDE 是**事前**设计量，才有意义。
- **DiD/事件研究**：MDE 思路延伸到「预趋势能侦测多大的违背」（见 §4）。

> 工具：功效/MDE 可用各估计 skill 或 StatsPAI 的功效相关函数（如 `synth_mde`、`rdpower`、`pretrends_power`）
> 产出；脚本与种子登记进 [`reproducibility-pack.md`](reproducibility-pack.md) §4。

---

## 4. 预趋势功效与平行趋势敏感性（DiD 专项）

Roth (2022)：**预趋势检验「没拒绝」常常只是功效太低**——真正会让你有偏的缓慢趋势恰好检不出来。研究级做法：

1. **`pretrends`**（https://github.com/jonathandroth/pretrends）：报告预检验在 50%/80% 功效下能侦测到多大的
   线性预趋势——让读者知道「pre-trend 平」到底多有力。
2. **`HonestDiD`**（https://github.com/asheshrambachan/HonestDiD ；Stata 口: https://github.com/mcaceresb/stata-honestdid）：
   报告平行趋势违背要多大（破点 **M**）才会使结论翻盘，把因果结论写成「除非违背超过 M，否则稳健」。

**落盘**：`03_analysis/robustness/pretrends_power.json` + `honest_did.json`；正文识别段引用其数值。这两项是
DiD 设计在质量门维度②拿到 8+ 的实质门槛（只有一张事件研究图最高 7，见
[`threats-to-validity.md`](threats-to-validity.md) §4）。

---

## 5. 设定曲线 / Multiverse——不挑樱桃

**设定曲线分析**（Simonsohn et al. 2020）：把所有「都站得住」的设定（控制集、FE、样本、度量、聚类）组合
**全部**跑一遍，把估计排序画成一条曲线，并标出哪些设定选择驱动了符号/显著性。**Multiverse 分析**
（Steegen et al. 2016）把同样的思路用在**数据构造**选择上（变量编码、剔除规则）。

- **怎么呈现**：附录放一张设定曲线图（系数排序 + 下方面板标注每个设定开关），再做整条曲线的联合推断
  （多少比例的设定显著、同号）。
- **作用**：证明主结果不是某一格设定凑出来的——直接回应 [`threats-to-validity.md`](threats-to-validity.md)
  §2 第 7 行「设定敏感」与第 10 行「分叉路径」。
- **落盘**：`03_analysis/robustness/spec_curve.json` + `spec_curve.png`；正文稳健性段引用「估计在整条
  设定曲线上保持同号同量级」。

---

## 6. 研究者自由度披露——把分叉路径摊在阳光下

即使没有故意 fishing、即使有预先假设，**未披露的分析弹性**也会抬高假阳性（Gelman-Loken「分叉路径」）。
本层要求一张**研究者自由度披露表**（放附录或复现包），逐项列出并标注是否预先指定：

| 自由度类别 | 本文的选择 | 预先指定? | 备选已在稳健性中检验? |
|---|---|---|---|
| 样本窗口 / 纳入剔除 | <如 2007–2021，剔除金融业> | 是/否 | 见 robustness/<...> |
| 处理/对照定义 | <如两高行业列表 X> | 是/否 | 替换列表见 robustness/<...> |
| 控制变量集合 | <baseline 控制集> | 是/否 | 逐步加控制表 |
| 结果变量编码 | <如绿色专利申请数 +1 取对数> | 是/否 | 替换度量见 robustness/<...> |
| 聚类层级 | <如省级> | 是/否 | 替换聚类见 robustness/<...> |
| 异常值处理 | <如 1% winsorize> | 是/否 | 见 robustness/<...> |

> 这张表与设定曲线（§5）是一对：自由度表说「我有哪些选择」，设定曲线说「换这些选择结果如何」。两者一起
> 把「研究者自由度」从隐患变成可信度信号。

---

## 7. 接入点（本层如何嵌进流水线与闸门）

| 接入点 | 本层做什么 | 落盘 / 判定 |
|---|---|---|
| **Stage 1 末 / Stage 3 初** | 写预分析计划，登记 OSF/AEA registry（如适用），锁定设计 | `01_proposal/pre_analysis_plan.md` |
| **Stage 3 估计前（锁）** | 实例化 `templates/preregistration.md`，填锁 + 确认性假设，跑 `python3 scripts/check_preregistration.py <ws>` | `00_meta/preregistration.md`（FAIL 则 Method Gate 不得 PASS） |
| **Stage 3 估计** | 空结果算 MDE；DiD 跑 `pretrends`+`HonestDiD`；跑设定曲线 | `03_analysis/robustness/{mde,pretrends_power,honest_did,spec_curve}.*` |
| **Stage 3 末** | 写研究者自由度披露表 | `03_analysis/researcher_dof.md`（进复现包附录） |
| **Stage 3 设计风险总账** | 把 PAP/MDE、设定曲线、研究者自由度和选择性报告风险写入 design-risk ledger | `03_analysis/design_risk_ledger.md` |
| **Stage 5 结果段** | 空结果报「能排除大于 X 的效应」；稳健性段引设定曲线 | `05_draft/main.tex` |
| **Stage 5 方法段** | 写「Deviations from PAP」说明 | `05_draft/main.tex` |
| **收尾 / 复现包** | 自由度表 + 种子登记并入 `REPLICATION.md` | 工作区根 `REPLICATION.md` |
| **质量门维度②③④⑦** | 见下方硬挂钩 | `00_meta/quality_scorecard.md` |

**与 [`quality-rubric.md`](quality-rubric.md) 的硬挂钩**：
- DiD 设计无预趋势功效/HonestDiD（§4）→ 维度②（识别）最高 7。
- 主张「无效应/精确零」却不报 MDE（§3）→ 维度④（解读克制度）封顶 6。
- 稳健性只报最优设定、无设定曲线/multiverse 证据（§5）且 reviewer 可质疑挑樱桃 → 维度③（稳健）最高 7。
- 目标 AEA 体系但无预注册/自由度披露/复现包（§2/§6）→ 与 [`reproducibility-pack.md`](reproducibility-pack.md)
  维度⑦联动封顶。

> 一句话：**可信度不只来自「证据对」，也来自「你先定方案、把选择摊开、把功效说清」。** 本层把这套
> 过程纪律前置进流水线，让稿子在「研究者自由度」这条现代审稿杀招上提前免疫。
