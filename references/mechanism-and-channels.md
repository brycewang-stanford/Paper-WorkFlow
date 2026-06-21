# Mechanism & Channels Pack — 机制、中介与渠道的可信分析

> 在 Stage 1 写 X→M→Y 设计、Stage 3 跑机制/中介、Stage 5 写 §Mechanisms 段、Stage 8 模拟评审时加载。
> 本文件补足实证论文里**最常被一票否决、却最少被认真对待**的一段：机制分析。主效应（X→Y）识别得再干净，
> 一句「我们发现效应通过 M 起作用」如果是用一组朴素中介回归凑出来的，reviewer 会立刻把整段机制打回——
> 严重时连累主结论的可信度。
>
> **分工**（与相邻层正交，互不重复）：
> - [`research-grade-methods.md`](research-grade-methods.md) 管主效应（X→Y）的识别与最低证据包。
> - [`threats-to-validity.md`](threats-to-validity.md) §3 管「不要把中介/对撞当控制塞进主设定」（坏控制）。
> - [`inference-and-uncertainty.md`](inference-and-uncertainty.md) 管机制检验的 SE / 多重检验校正。
> - **本文件管「当你确实想论证 M 是渠道时，这个 X→M→Y 的主张本身需要什么识别、怎么做才算可信、
>   做不到时措辞要退到哪一档」**。
>
> 一句话：主效应识别 X→Y；本层识别 X→M→Y。**后者是一个独立的、通常更难的因果问题，不能搭主设定的便车。**

---

## 0. 这个增强层解决什么

机制段的三个高频死法：

1. **「系数下降即渠道」谬误**：加入 M 后 X 的系数变小，就宣称「效应通过 M 传导」。这在多中介、控制集相关
   时**顺序依赖、可正可负**，不做正式分解就是讲故事（正确做法见 §2 的 Gelbach 分解）。
2. **把中介当因果，却没有中介的识别**：中介效应（ACME）要成立需要 **sequential ignorability**（给定 X 和
   前处理协变量，M 对 Y 如同随机）——这是个**强且通常不可检验**的假设。直接报「M 解释了 60% 的效应」而
   不谈这个假设、不做敏感性，等于把相关性写成因果。
3. **坏控制 / 后处理变量**：M 是处理的结果，**绝不能进主设定**（否则吸收掉部分处理效应、或打开对撞后门，
   见 [`threats-to-validity.md`](threats-to-validity.md) §3）。机制分析在**独立的设定**里做，不污染主表。

本层要求：**先把「机制主张属于哪一类」说清，再按那一类的识别标准做，做不到就把措辞退到「suggestive」。**

> 本层是**机制可信度标尺**，不替代任何估计 skill。具体中介/分解怎么跑，路由到 StatsPAI / Stata / R 的真实
> 函数（见 §5 末「实现路由」）；本文件只规定「哪类主张需要什么假设、做到什么程度、写成什么措辞才算达标」。

---

## 1. 外部锚点（评估 / 实现 / 反驳时的权威入口）

| 议题 | 首选入口 | 何时用 |
|---|---|---|
| 为什么 Baron-Kenny 已过时 | Baron & Kenny (1986) 的乘积/逐步法在有混淆或非线性时有偏；见下方现代替代 | 判断一篇稿子的中介是不是停留在 1986 年的做法 |
| 因果中介框架与设计 | Imai, Keele & Tingley (2010, *Psych. Methods* 15(4):309–334); Imai, Keele, Tingley & Yamamoto (2011, *APSR* 105(4):765–789) | 现代因果中介的总体框架与「识别机制」的实验设计 |
| 序贯可忽略性 + ACME/ADE + 敏感性 | Imai, Keele & Yamamoto (2010, *Stat. Sci.* 25(1):51–71)；实现见 `mediation` 包: https://cran.r-project.org/package=mediation | 把效应分解成「经 M / 不经 M」并报 ACME 对 M-Y 误差相关 ρ 的敏感性 |
| 回归型机制分解（计量首选） | Gelbach (2016, *J. Labor Econ.* 34(2):509–543) *When Do Covariates Matter?*: https://www.journals.uchicago.edu/doi/10.1086/683668 | 把 reduced-form 系数的**总变化**做顺序无关分解（描述性 OVB 会计，非因果中介） |
| 控制直接效应 / 序贯 g | Acharya, Blackwell & Sen (2016, *APSR* 110(3):512–529) sequential g-estimation: https://www.mattblackwell.org/files/papers/direct-effects.pdf | 当 M-Y 间有处理后混淆时估直接效应 |
| 中介的工具变量（单工具） | Dippel, Ferrara & Heblich (2020, *Stata Journal* 20(3):613–626) `ivmediate` | 单一工具 + 结构假设下识别 X→M→Y 渠道 |
| 中介总纲 | VanderWeele (2015) *Explanation in Causal Inference*, OUP: https://global.oup.com/academic/product/explanation-in-causal-inference-9780199325870 | 中介与交互的定义、四分解、敏感性全景 |
| 坏控制 / 后处理偏误 | Cinelli, Forney & Pearl (2024, *Soc. Methods & Research* 53(3); online 2022): https://journals.sagepub.com/doi/full/10.1177/00491241221099552 | 判定 M 该不该进主设定（不该） |

> 这些是判定与实现的标准锚点，不是硬依赖。不能联网时按本文件 §2–§4 的决策规则自检，并路由到已装的
> StatsPAI / Stata / R 函数；**不要凭印象写「机制检验证明 M 是主要渠道」这种空话**——每个机制主张都要指向
> `03_analysis/mechanism/` 里真实跑出来的分解/中介结果与其识别假设。

---

## 2. 先分清三类「机制」主张——它们的识别标准完全不同

| 主张类型 | 你实际在说什么 | 需要的识别 | 可信度上限 |
|---|---|---|---|
| **A. 描述性分解（accounting）** | 「主效应里有多大比例，在统计上由 M 解释」 | Gelbach 分解（顺序无关地分解系数的**总变化**；单个中介份额仍依赖纳入的协变量集合，整体是 OVB 会计） | 描述性：说「与 M 一致」，不等于「经 M 因果传导」 |
| **B. 因果中介（ACME/ADE）** | 「X 对 Y 的效应有多少**因果地**经过 M」 | sequential ignorability（强、通常不可检验）+ 敏感性分析；或 ACS 序贯 g、或中介 IV | 取决于假设可信度 + 敏感性；几乎总要 hedge |
| **C. 异质性即机制（suggestive）** | 「在 M 渠道更活跃的子样本里效应更大」 | 主效应识别 + 预先指定的子样本（见 inference pack §5 多重检验） | suggestive：一致性证据，不是分解 |

**操作纪律**：在 `design_register.md` 里**点名**你的机制主张属于 A / B / C 哪一类；不同类用不同方法、不同措辞。
最常见的错误是嘴上说 C（suggestive），表里做 A（系数下降），却用 B（因果）的措辞写。

---

## 3. 反模式清单（踩中即回炉）

- ❌ **「加 M 后 X 系数从 0.5 掉到 0.2，所以 60% 经 M」**——多中介/相关控制下顺序依赖，必须用 Gelbach 分解
  （§2 类型 A），且仍只是描述性。
- ❌ **把 M（后处理变量）放进主回归当控制**——坏控制：控制纯中介会按构造吸收掉间接效应，**且**当 M 同时是
  对撞因子（如存在 M-Y 共同混淆）时还会打开后门、令直接/总效应有偏（threats §3）。机制在独立设定里做。
- ❌ **报 ACME / 中介比例却不提 sequential ignorability、不做敏感性**——把不可检验的强假设当默认成立。
- ❌ **用 Baron-Kenny 乘积/逐步法**当主要证据——有混淆或非线性时有偏，现代审稿不接受其作为因果中介。
- ❌ **M 本身是 Y 的另一种度量、或测于处理之后且可能反向因果**——这不是机制，是同义反复或内生中介。
- ❌ **机制段用满格因果措辞**，而识别只到 A/C 档——措辞必须与识别档位匹配（writing-craft §6 量级/措辞纪律）。

---

## 4. 怎么做对（决策规则）

1. **定类型**（§2）：A 描述分解 / B 因果中介 / C 异质性。写进 `design_register.md`。
2. **M 永远不进主设定**：主表是 X→Y；机制证据在独立小节/独立表（`03_analysis/mechanism/`）。
3. **类型 A** → 用 **Gelbach 分解**报「各中介对 reduced-form 系数**总变化**的贡献」（总分解顺序无关；单个份额
   依赖纳入协变量、且只是描述性会计）；措辞用「consistent with the M channel」，不写「causally operates through M」。
4. **类型 B** → 报 **ACME/ADE + 敏感性**（Imai 的 ρ 误差相关敏感性，或 E-value 思路），或当 M-Y 有处理后混淆时
   用 **ACS 序贯 g-estimation**；有可信工具时用**中介 IV**（Dippel-Ferrara-Heblich 的单工具结构法 `ivmediate`，
   或主效应与中介各有工具的设定）。**正文必须写出识别假设这一句**，并给敏感性破点。
5. **类型 C** → 框成 suggestive：预先指定渠道代理的子样本（多重检验校正见 inference pack §5），说「效应在
   渠道更强处更大，与 M 一致」，不做比例分解。
6. **多个候选渠道** → 横向比较各渠道证据强度，别只报最配合故事的那个（呼应设定曲线/挑樱桃纪律）。
7. **失败回退**：机制证据不支持预期渠道 → 如实写「未找到 M 渠道的证据」或保留为探索性附录，**不要硬把
   主效应的功劳安到一个站不住的渠道上**（参考主线「预期实证结果无法实现时切备选」纪律）。

---

## 5. 落盘与写作

- **落盘**：机制结果存 `03_analysis/mechanism/`（分解表、ACME、敏感性、子样本异质性 + 各自识别假设说明）；
  与 `inference_report.md` 的多重检验族对账（多个渠道/子样本是一族）。
- **写作（§Mechanisms 段）**：① 一句话点明机制主张类型（A/B/C）；② 给方法与**识别假设**；③ 给结果与敏感性；
  ④ 措辞严格匹配识别档位。机制段的标题直接写所检验的渠道，让 reviewer 一眼看到你在分清渠道而非堆回归。
- **Evidence ledger**：机制类 claim 在 [`../templates/evidence_ledger.md`](../templates/evidence_ledger.md) 的
  Claim Register 里 strength 一栏标 `descriptive`（类型 A/C）或仅在 B 档识别可信时标 `causal`。

**实现路由**：

| 做法 | StatsPAI MCP | 包 / Stata / R |
|---|---|---|
| Gelbach 分解 | `gelbach` | Stata `b1x2` / `gelbach`；R 自实现 OVB 分解 |
| 因果中介 ACME/ADE + 敏感性 | `mediate` / `mediation` / `mediate_interventional` | Stata `medeff`/`gsem`；R `mediation::mediate` |
| 中介分解（通用） | `mediation_decompose` / `decompose` | R `DirectEffects` / `gformula` |
| 序贯 g-estimation（处理后混淆） | `g_estimation` | R `DirectEffects::sequential_g`；Stata `gformula` |
| 中介 IV / 前门 / 代理 | `front_door` / `frontdoor` / `proximal` | 单工具 `ivmediate`(Stata)；前门需完全中介；proximal 需双代理 |
| 异质性即机制（子样本/CATE） | `metalearner` / `subgroup_analysis` | 见 statspai-analysis §3 |

---

## 6. 接入点（本层如何嵌进流水线与闸门）

| 接入点 | 本层做什么 | 落盘 / 判定 |
|---|---|---|
| **Stage 1 设计** | 在 `proposal.md` / `design_register.md` 点名机制主张类型 A/B/C | `03_analysis/design_register.md` |
| **Stage 3 机制** | 按类型跑 Gelbach / ACME+敏感性 / 子样本；M 不进主设定 | `03_analysis/mechanism/` |
| **Stage 5 §Mechanisms** | 写「类型 + 识别假设 + 结果 + 敏感性」，措辞匹配档位 | `05_draft/main.tex` |
| **Stage 8 模拟评审** | critic 按 §3 反模式逐条找「机制是不是凑出来的」 | `08_review/referee_report.md` |
| **质量门维度②④** | 见下方硬挂钩 | `00_meta/quality_scorecard.md` |

**与 [`quality-rubric.md`](quality-rubric.md) 的硬挂钩**：

- 主设定里含后处理中介 M 当控制（§3）→ 维度②（识别）封顶 4（等同坏控制红旗，与 threats §3 一致）。
- 机制用因果措辞（类型 B），但无 sequential ignorability 说明、无敏感性（§4）→ 维度④（解读克制度）封顶 6。
- 「系数下降即渠道」无 Gelbach 正式分解（§3）→ 机制段证据降为 suggestive；若正文仍按因果写 → 维度④封顶 6。
- 多个候选渠道只报最配合故事的一个、无横向比较（§4.6）→ 维度③（稳健）按挑樱桃处理，封顶 7。

> 一句话：**机制分析是第二个因果问题，不是主回归的赠品。** 先分清 A/B/C，按那一类的识别标准做，把 M 挡在
> 主设定之外，措辞退到证据支持的档位——机制段就从「最易被毙」变成「加分项」。
