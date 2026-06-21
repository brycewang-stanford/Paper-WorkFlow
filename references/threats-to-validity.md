# Threats-to-Validity Pack — 识别威胁与审稿异议预案

> 在 Stage 3 定稳健性矩阵、Stage 5 写识别与稳健性段、Stage 8 模拟评审与写 response letter 时加载。
> 本文件把现代因果推断里 reviewer **一定会问**的那组识别威胁，做成一张「威胁 → 审稿口径 → 诊断/稳健性
> → 预先在正文里堵上 → 被问到怎么回应」的对照表。
>
> **分工**：[`research-grade-methods.md`](research-grade-methods.md) 的 Method Gate 规定**每种方法要落盘哪些
> 诊断证据**（是科学性）；本文件规定**把这些证据组织成「先发制人的叙事 + 逐条回应」**（是说服力）。
> 证据成不成立看 method gate；怎么写得让审稿人没话说看本文件。两者一个管「有没有证据」，一个管
> 「怎么用证据堵住异议」，互不重复。
>
> **不确定性配套**：本文件第 10 行（多重检验）与第 12 行（弱工具）只点到威胁；**怎么把 SE 聚类对、
> few-cluster 怎么修、多重检验怎么校正、弱工具区间（AR/tF）怎么算**，见
> [`inference-and-uncertainty.md`](inference-and-uncertainty.md)。Stage 3 跑稳健性时两者一起加载：本文件出
> 「威胁清单」，inference pack 出「不确定性口径」。

---

## 0. 这个增强层解决什么

很多稿子的识别**其实站得住**，却仍被一审毙掉——因为作者没有把 reviewer 心里那本「异议清单」逐条
预先堵上。审稿人评估识别可信度时，脑子里跑的是一份**固定的威胁清单**（遗漏变量、反向因果、选择、
测量误差、溢出、坏控制、外部效度……）。本层要求：

1. **先发制人**：写识别段/稳健性段时，对照本清单**主动**列出主要威胁并逐一排除，而不是等审稿人来问。
2. **威胁→诊断一一对应**：每个威胁都有标准诊断；缺这个诊断，对应的稳健性维度在质量门就过不了 7 分。
3. **回应有章法**：Stage 8 被问到时，按「同意/部分同意/谨慎不同意 + 指向具体修改位置」的格式回应。
4. **措辞与证据匹配**：威胁没排除干净，就别用满格因果措辞（措辞分级见
   [`writing-craft.md`](writing-craft.md) §6）。

> 本层是**异议预案标尺**，不替代任何估计或写作 skill。诊断怎么跑见各估计 skill 与
> [`research-grade-methods.md`](research-grade-methods.md)；逐条回应怎么写见
> [`peer-review-and-submission.md`](peer-review-and-submission.md) §3。

---

## 1. 外部锚点（评估/实现/反驳时的权威入口）

| 要件 | 首选入口 | 何时用 |
|---|---|---|
| 应用识别总纲 + 坏控制 (§3.2.3) | Angrist & Pischke, *Mostly Harmless Econometrics*: https://press.princeton.edu/books/paperback/9780691120355/mostly-harmless-econometrics | 全程：识别策略、控制变量取舍 |
| 直觉版识别教材 | Angrist & Pischke, *Mastering 'Metrics*: https://www.masteringmetrics.com/ | RCT/IV/RD/DiD 的识别叙事 |
| 因果推断 + 代码 | Cunningham, *Causal Inference: The Mixtape*: https://mixtape.scunning.com/ | DAG、IV、DiD、RD、SC 的实现 |
| 「好控制 vs 坏控制」DAG 分类 | Cinelli, Forney & Pearl, *A Crash Course in Good and Bad Controls* (SMR 2024): https://journals.sagepub.com/doi/full/10.1177/00491241221099552 | 判定每个控制变量是否会引入偏误 |
| OVB 敏感性 / 系数稳定性 | Oster (2019, JBES): https://www.tandfonline.com/doi/abs/10.1080/07350015.2016.1227711 | 用 δ 与 R²_max 量化「遗漏变量要多强才能翻盘」 |
| 平行趋势预检验的功效陷阱 | Roth (2022, AER:Insights): https://www.aeaweb.org/articles?id=10.1257/aeri.20210236 | DiD 的 pre-trend 不能只靠「看起来平」 |
| 弱工具稳健推断 | Andrews, Stock & Sun (2019, ARE): https://www.annualreviews.org/doi/abs/10.1146/annurev-economics-080218-025643 | effective F、Anderson-Rubin 区间 |
| 样本选择/磨损上下界 | Lee (2009, ReStud): https://academic.oup.com/restud/article-abstract/76/3/1071/1590707 | 差异性磨损时的 trimming bounds |
| 潜在结果 / SUTVA 基础 | Imbens & Rubin (2015): https://www.cambridge.org/core/books/causal-inference-for-statistics-social-and-biomedical-sciences/71126BE90C58F1A431FE9B2DD07938AB | 溢出、干涉、估计量定义 |

> 这些是判定与反驳的标准锚点，不是硬依赖。本机不能联网时，subagent 按本文件 §2 的对照表自检，
> **不要凭印象写「本文已充分排除内生性」这种空话**——每个排除都要指向 `03_analysis/` 里的真实 artifact。

---

## 2. 识别威胁 × 审稿异议 主对照表（核心）

> 用法：Stage 3 跑稳健性时照「诊断/稳健性」列补 artifact；Stage 5 写识别/稳健性段时照「正文里先堵上」
> 列写预防段；Stage 8 被问到时照「被问到怎么回应」列写 response。每条都要能指到工作区真实文件。

| # | 威胁 | 审稿人会怎么说 | 标准诊断 / 稳健性 | 正文里先堵上（一句话预防） |
|---|---|---|---|---|
| 1 | **遗漏变量 / 混淆 (OVB)** | 「有个没控制的因素同时驱动 X 和 Y，你的系数有偏。」 | 系数随控制集稳定性；**Oster (2019)** δ 与 β-bounds（δ=1, R_max≈1.3R̃²）；Cinelli-Hazlett 敏感性 | 「系数在逐步加控制下稳定，Oster δ>1，说明未观测因素需强于已观测才足以翻盘。」 |
| 2 | **反向因果 / 联立** | 「会不会是 Y 导致 X，而非 X 导致 Y？」 | 时序/滞后结构、预定回归元、事件时点、IV、Granger | 「处理在时点上预定且外生，排除了来自结果的反馈。」 |
| 3 | **选择 / 自选择进入处理** | 「处理组与对照组本就系统性不同，这是选择不是效应。」 | 平衡表、PSM/加权、RD/IV 求准随机分配、安慰剂组 | 「分配由[外生规则]驱动，处理/对照在可观测维度上平衡。」 |
| 4 | **测量误差 / 衰减偏误** | 「核心变量有噪声，把估计往零方向压。」 | 信度检查、替换度量、对误测变量做 IV、上下界 | 「换一个独立度量与一个净化经典衰减的 IV 后结论不变。」 |
| 5 | **SUTVA 违背 / 溢出 / 一般均衡** | 「对照单位被处理污染，潜在结果不稳定。」 | 部分干涉设计、距离/网络暴露映射、donut 控制、GE 感知估计量 | 「剔除受暴露的对照、且无溢出梯度，本聚合层级上 SUTVA 可信。」 |
| 6 | **坏控制 / 后处理变量 / 对撞 (M-bias)** | 「那个控制是处理的结果，控制它反而引入偏误。」 | 用 DAG 给每个控制分类；报告有/无可疑控制；避免后处理条件化（**Cinelli-Forney-Pearl**） | 「所有控制均为处理前变量；加入后处理变量（附录）只印证它们是应当剔除的对撞因子。」 |
| 7 | **函数形式 / 设定敏感** | 「结果是你这套设定凑出来的 artifact。」 | 设定曲线/multiverse、替换 FE、对数 vs 水平、多项式/非参 | 「估计在整条设定曲线上保持同号同量级。」 |
| 8 | **外部效度 (LATE vs ATE)** | 「这只是 complier/单一场景的局部效应，推广不了。」 | 刻画 complier、报边际效应、多场景复制、按目标总体重加权 | 「我们刻画了 complier/LATE 总体，并展示其协变量分布与政策相关总体重叠。」 |
| 9 | **磨损 / 幸存者 / 样本选择** | 「差异性磨损选择了你的样本。」 | 磨损平衡、**Lee (2009) bounds**（trimming）、Heckman 校正、IPW | 「磨损在两组间平衡，Lee 上下界不含零，选择无法解释该效应。」 |
| 10 | **多重检验 / p-hacking / 分叉路径** | 「检验做这么多，总有几个『显著』是偶然。」 | Romano-Wolf / Westfall-Young / FDR(BH)、预先指定主结果、族错误率控制 | 「主结果预先指定，且经 Romano-Wolf 多重检验校正后仍成立。」 |
| 11 | **平行趋势 / 预趋势违背 (DiD)** | 「你的 pre-trend 检验只是功效太低——没证据不等于平行。」 | 事件研究图；**不要只靠 pre-test 通过 (Roth 2022)**；报预检验功效；用 **HonestDiD** 做敏感性 | 「除事件研究图外，我们报告了预检验对经济意义违背的功效，并在 HonestDiD 下给出结论的破点 M。」 |
| 12 | **弱工具 / 排他性失效 (IV)** | 「第一阶段太弱 / 工具直接影响 Y。」 | effective F（Montiel-Olea-Pflueger）、Anderson-Rubin 稳健区间、过度识别、排他性叙事 | 「第一阶段强（effective F 远超阈值），并用 Anderson-Rubin 做弱工具稳健推断，排他性有制度叙事支撑。」 |

> 这张表是 Stage 3 稳健性矩阵的**需求清单**：你的设计命中哪几行，就必须在 `03_analysis/robustness/`
> 里有对应 artifact。命中而无对应真实文件 → 质量门维度③（稳健）封顶 5（见
> [`quality-rubric.md`](quality-rubric.md) 维度③）。

---

## 3. 「坏控制」专题——最常被忽视、最容易被一票否决

控制变量不是越多越好。**控制一个本身受处理影响的变量（后处理变量 / 中介 / 对撞因子）会引入偏误**，
这是近年顶刊 reviewer 的高频杀招。判定规则（按 Cinelli-Forney-Pearl 的 DAG 分类）：

| 控制类型 | 该不该控制 | 后果 |
|---|---|---|
| **混淆因子**（同时影响 X 和 Y 的前置变量） | **要** | 不控制 → OVB |
| **前处理协变量**（影响 Y、与 X 无因果关系） | 可控（提精度） | 一般无害 |
| **中介**（X→M→Y 的 M） | **不要** 放进主设定 | 控制它 = 吸收掉部分处理效应 |
| **对撞因子 / 选择变量**（X 和 U 共同影响的变量） | **绝不** | 控制它 = 打开后门，制造 M-bias |
| **工具变量** | 不作控制 | 误作控制 → 放大偏误 |

**操作纪律**：① Stage 3 写 `design_register.md` 时，把控制集每个变量标注「前处理/混淆/中介/对撞」，
后处理变量一律移出主设定，最多进「机制分解」附录；② 主表与「逐步加控制」表并列，证明系数不靠某个
可疑控制撑着；③ 若必须用某个临界变量，在正文用一句话交代它是前处理的、给出度量时点。

> **想把中介 M 做成机制证据（而非赶出主设定就完事）？** X→M→Y 是一个**独立的因果问题**：怎么分清
> 「描述性分解 / 因果中介 / 异质性即机制」三类主张、各自需要什么识别、措辞退到哪一档，见
> [`mechanism-and-channels.md`](mechanism-and-channels.md)。本节管「M 不能进主设定」，那份 pack 管「机制怎么做才可信」。

---

## 4. DiD 时代的平行趋势——别再只贴一张「看起来平」的图

Roth (2022) 之后，**「pre-trend 检验没拒绝 → 平行趋势成立」已经不能说服 reviewer**：预检验功效往往太低，
真正会让你有偏的那种缓慢趋势恰恰检不出来。现在的研究级做法是三件套：

1. **事件研究图**：leads 系数≈0 且置信带不宽（宽到什么都包不住没意义）。
2. **预检验功效**：报告该预检验能在 50%/80% 功效下侦测到多大的线性违背（用 `pretrends` 工具，见
   [`design-transparency.md`](design-transparency.md) §3）——让读者知道「检验没拒绝」到底多有力。
3. **HonestDiD 敏感性**：报告「平行趋势违背要多大（破点 M）才会让结论翻盘」，把因果结论从「假设成立」
   改写成「除非违背大到 M 以上，否则结论稳健」。

> 交错处理（多期、异时点）还要叠加负权重问题：用 Callaway-Sant'Anna / Sun-Abraham / BJS 等
> group-time 估计量，naive TWFE 只能进对照表。这条属 method gate 的最低证据包（见
> [`research-grade-methods.md`](research-grade-methods.md) §3 交错 DiD 行）。

---

## 5. 把威胁清单写进论文的两个位置

**A. 识别策略段（Stage 5，正文 §Empirical Strategy）**——先发制人：
- 用一段「Threats to Identification」列出本设计命中的 3–5 个威胁（查 §2 对照表），逐一说明如何排除或为何
  不致命，每个排除指向一张稳健性表/图。这正是把 reviewer 的提问提前在正文里回答掉。

**B. 稳健性段（Stage 5/6，正文 §Robustness）**——证据落地：
- 稳健性矩阵不是「又跑了几个回归」，而是「针对每个具体威胁的回应」。每个稳健性小节标题直接写它对应
  哪个威胁（「Addressing concurrent policies」「Alternative treatment definition」「Placebo timing」），
  让 reviewer 一眼看到威胁已被系统应对。

---

## 6. 接入点（本层如何嵌进流水线与闸门）

| 接入点 | 本层做什么 | 落盘 / 判定 |
|---|---|---|
| **Stage 3 设计注册** | 控制集按 §3 标注「前/混淆/中介/对撞」，后处理变量移出主设定 | `03_analysis/design_register.md` |
| **Stage 3 稳健性矩阵** | 按 §2 命中行补齐对应诊断 artifact（与 method gate 联动） | `03_analysis/robustness/` |
| **Stage 5 识别/稳健性段** | 按 §5 写「Threats to Identification」预防段 + 威胁导向的稳健性小节 | `05_draft/main.tex` |
| **Stage 8 模拟评审** | critic 按 §2 对照表逐行找「哪个威胁没堵上」 | `08_review/referee_report.md` |
| **Stage 8 回应信** | 被问到的威胁按 §2 末列 + [`peer-review-and-submission.md`](peer-review-and-submission.md) §3 逐条回应 | `08_review/response_letter.md` |
| **质量门维度②③** | 命中威胁却无对应 artifact → 识别/稳健封顶；坏控制未清 → 识别封顶 | `00_meta/quality_scorecard.md` |

**与 [`quality-rubric.md`](quality-rubric.md) 的硬挂钩**：
- §2 命中的威胁缺对应 `03_analysis/robustness/` 真实文件 → 维度③（稳健）封顶 5。
- 主设定含后处理/对撞控制（§3）→ 维度②（识别）封顶 4（等同「把相关性当因果」红旗）。
- DiD 只给一张事件研究图、无预检验功效或 HonestDiD（§4）→ 维度②最高 7。
- 弱工具（effective F 远低于阈值）却用满格因果措辞 → 维度②封顶 4。

> 一句话：**reviewer 的异议清单是固定的，本文件把它前置成作者的自检清单。** 先把每个威胁在正文里
> 堵上、在工作区里留下证据，Stage 8 的模拟评审与真实投稿就少一轮回炉。
