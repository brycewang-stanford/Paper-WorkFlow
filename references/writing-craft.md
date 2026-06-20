# Writing-Craft Pack — 实证论文「学者级写作」增强层

> 在 Stage 1 锻造贡献句、Stage 5 写初稿、Stage 6 打磨、以及 Stage 7 后质量门打分（维度 ①④⑤）时加载。
> 本文件把顶刊经济学 / 金融 / 管理实证论文的**写作范式**落成可执行的清单与模板：
> **方法证据由 [`research-grade-methods.md`](research-grade-methods.md) 的 Method Gate 保证「是真的」；
> 本文件保证「写得像顶刊学者写的」。** 两者一个管证据、一个管表达，互不重复。

---

## 0. 这个增强层解决什么

Paper-WorkFlow 已经能把选题、估计、表图、写作串成一条线，但「调用 `paper-writer` / `paper-pipeline`
写出来」和「写得像 JF/QJE 的稿子」之间还差一层**显式的写作工程标准**。本层要求：

1. **贡献先于一切**：Intro 第一段就说清「我们做了什么、比谁前进了一步」，不许「清嗓子」（Cochrane）。
2. **结构是合同**：实证论文有固定解剖结构，每一节有它必须回答的问题；缺节即结构残缺。
3. **量级 > 星号**：结果段报经济量级（占均值/标准差几成），区分统计显著与经济重要（McCloskey-Ziliak）。
4. **克制 > 拔高**：因果语气不得强于 `method_gate.md` 支持的证据；政策建议不得外推出证据边界。
5. **可被引用**：标题、摘要、贡献句都要写成「五年后综述会引用」的样子（Edmans 的 survival test）。

> 本层是**写作标尺**，不是又一个写作工具。具体逐句改写仍调用既有 skill（`paper-writer`、
> `paper-pipeline`、`readability`、`56-hanlulong-econ-writing-skill` 等，见
> [`skill-map.md`](skill-map.md)）；本文件只规定「写成什么样才算达标」。

---

## 1. 外部写作锚点（实现/审稿/打分时的权威入口）

| 写作要件 | 首选入口 | 何时用 |
|---|---|---|
| Intro 五段公式 | Keith Head, "The Introduction Formula": https://blogs.ubc.ca/khead/research/research-advice/formula | Stage 5 写引言、Stage 6 重写引言 |
| 写作总纲（PhD 必读） | John Cochrane, "Writing Tips for PhD Students": https://www.johnhcochrane.com/research-all/writing-tips-for-phd-students | 全程：摘要、引言、结构、删废话 |
| 经济学修辞 | McCloskey, *Economical Writing*；McCloskey & Ziliak, *The Cult of Statistical Significance* | 结果段量级解读、去废话 |
| 应用经济写作清单 | Marc Bellemare, "How to Write Applied Papers in Economics": https://marcfbellemare.com/wordpress/wp-content/uploads/2020/02/BellemareHowToFebruary2020.pdf | Stage 5 各节解剖 |
| Intro 工程化讲法 | Jesse Shapiro, "How to Give an Applied Micro Talk" / writing notes（用于反推 Intro 的论证链） | Stage 1 贡献、Stage 5 引言 |
| 发展经济 Intro 范式 | David McKenzie (World Bank), CGD "How to Write the Introduction": https://www.cgdev.org/blog/how-write-introduction-your-development-economics-paper | Stage 5 引言 |
| 综合写作技巧（IZA） | "Writing Tips for Economics Research Papers", IZA DP 15057: https://docs.iza.org/dp15057.pdf | 全程参考 |
| 选题红线 | Edmans (2024), "The 1000 Rejections"（convex combination / survey test） | Stage 1 贡献、质量门维度① |
| 已封装的写作 skill | `56-hanlulong-econ-writing-skill`（综合 Cochrane/McCloskey/Head/Shapiro/Bellemare 等 50+ 指南）：https://github.com/hanlulong/econ-writing-skill | Stage 5/7 直接调用 |

> 这些是写作标准锚点，不是硬依赖。能调用 `56-hanlulong-econ-writing-skill` 或母仓库写作 skill 就调；
> 不可用时，subagent 按这些公开指南的结构自检，**不要凭印象拼一篇「AI 味」综述式引言**。

---

## 2. 引言：Keith Head 五段公式 ×  Cochrane 纪律

实证论文的引言是**决定 desk-reject 与否的单点**。固定写成五个功能段（Head's Formula），每段一个任务：

| 段 | 功能 | 写法要点 | 反面（命中即回退 Stage 5） |
|---|---|---|---|
| ① Hook | 让人想读 | Y 重要 / Y 反直觉 / Y 有争议 / Y 普遍——四选一，用一个具体事实或张力开场 | 用「随着……的发展」「在当今……背景下」起手；空泛宏大叙事 |
| ② Question | 本文问什么、做什么 | 一句话写清研究问题 + 一句话写清你的答案（**先说结论**，Cochrane） | 只说「本文研究 X 与 Y 的关系」却不给答案 |
| ③ Antecedents | 站在谁的肩膀上 | 点名 2–4 篇最相关的前作，**只为定位**，不写文献综述流水账 | 把引言写成 mini-lit-review；堆 20 个 citation |
| ④ Value-added | 比前作前进了哪一步 | 明确「他们做了 A，我们第一个做了 B」；点出识别/数据/机制上的具体增量 | 「本文丰富了……文献」这种无信息量套话 |
| ⑤ Roadmap | （可选）后文结构 | 现代顶刊常省略或压成一句；中文期刊保留 | 机械「第二节……第三节……」占半页 |

**Cochrane 三条硬纪律（违反即扣写作维度分）**：

1. **摘要写「你发现了什么」，不是「你研究了什么」**（"what you find, not what you look for"）。
2. **引言第一句就是最大贡献**，不要先铺政策重要性、不要先回顾文献——那叫「清嗓子」，浪费版面。
3. **一篇论文一个核心点**。把最重要的结果放最前面；次要结果往后排，不喧宾夺主。

> Stage 5 写完引言后，主代理（或 critic subagent）按本表逐段核对五功能是否齐、是否命中反面写法；
> 缺段或命中反面 → 回 Stage 5 重写引言段，再进 Stage 6 打磨。

---

## 3. 贡献段（Contribution Paragraph）——质量门维度①的命门

引言里通常有一个**显式贡献段**（"This paper makes three contributions ..."）。它是 Stage 1 选题漏斗
的产物在写作端的兑现，也是质量门维度①打分的主要依据。

**写法模板**（每条贡献都要能填满这三槽）：

```
我们是第一个 [动词: 识别/量化/证明/检验] 了 [具体对象] 的研究，
相对于 [最接近的前作]，本文的增量在于 [新数据 / 新识别 / 新机制 / 新场景]，
这一点重要是因为 [理论张力 / 政策含义 / 反直觉]。
```

**贡献句的四道自检（对应 Edmans 红线，命中任一 → 回 Stage 1）**：

- **Survey test**：五年后该主题的综述，会不会专门用一段引用本文？不会 → 贡献太薄。
- **Convex combination**：X→Z 已知、Z→Y 已知，本文只是 trivial 地推出 X→Y？是 → 不成立。
- **Just-another-determinant**：是否只证明「X 是 Y 的又一个驱动因素」，无机制、无张力？是 → 太弱。
- **Geographic replication**：是否只是把别国做过的搬到本国重做、无本土制度性新意？是 → 太弱。

> 这四道自检与 [`quality-rubric.md`](quality-rubric.md) 维度①的「致命红旗」一一对应。写作端先过这关，
> 能把质量门维度①的回炉提前消化在 Stage 1/5。

---

## 4. 摘要公式（Abstract）

顶刊摘要 ≈ 5 句话，**先结论后方法**：

1. **背景一句**：交代研究问题所在的张力（≤1 句，不展开）。
2. **做法一句**：数据 + 识别策略（"Using [data], we exploit [variation] to identify ..."）。
3. **主结果一句**：**带数字、带量级**（"a one-SD increase in X raises Y by Z%"）。
4. **机制/异质性一句**：为什么会这样 / 对谁更强。
5. **含义一句**：理论或政策含义（克制，不外推）。

**红线**：摘要不写「本文旨在研究……」（写你发现了什么）；不堆形容词（"significant", "important",
"novel" 自我表扬）；数字与正文 `summary.md` 一致。

---

## 5. 实证论文解剖结构（每节必须回答的问题）

Stage 5 让 `paper-writer` 产出的 `main.tex` 应覆盖下列结构；**缺节 = 结构残缺**（质量门维度⑤封顶）：

| 节 | 必须回答 | 常见硬伤 |
|---|---|---|
| **1. Introduction** | 见 §2/§3：问题、答案、贡献、定位 | 清嗓子、贡献埋没 |
| **2. Institutional Background / 制度背景** | 这个政策/市场/冲击是怎么运作的，为什么提供识别 | 写成新闻综述，与识别脱节 |
| **3. Data** | 样本怎么构造、关键变量怎么度量、样本期与频率 | 不交代样本筛选、变量来源 |
| **4. Empirical Strategy / 识别策略** | estimand 是什么、识别假设是什么、为什么可信（见 §6） | 只贴方法标签、不讲假设 |
| **5. Results** | 主结果 + 经济量级 + 机制 + 异质性（见 §7） | 只读星号、过度解读 |
| **6. Robustness** | 主结论经得起哪些扰动（对应 `03_analysis/robustness/`） | 罗列检验但不说明威胁 |
| **7. Conclusion** | 重述贡献、边界、未来方向 | 重复摘要、夸大政策含义 |

> 写作前先读 `04_results/exhibits_index.md`（每张表图对应哪个论点）与 `01_proposal/proposal.md`
> （贡献/假设），让结构与证据严格对齐；**论文里每个 claim 都要能指到一张表/图或一段引用**。

---

## 6. 识别策略段：怎么把「真证据」写成「可信叙事」

> **分工**：识别证据**是否成立**由 [`research-grade-methods.md`](research-grade-methods.md) 的 Method Gate
> 判定（DiD 的平行趋势、IV 的弱工具检验、RDD 的密度检验……）；本节只管**怎么把已通过的证据写成
> 让 reviewer 信服的段落**。证据没过，就别用因果措辞——这是质量门维度②的硬约束。

识别段的论证链（四步，缺一则说服力打折）：

1. **变异来源**：identifying variation 从哪来（政策时点、断点规则、工具的外生冲击、donor pool）。
2. **识别假设**：用一句话写死核心假设（平行趋势 / 排他性 / 断点处连续 / 无操纵）。
3. **为什么可信**：结合制度背景论证假设在本场景为何成立，并**正面给检验证据**（事件研究图、
   一阶段 F、McCrary 检验、安慰剂）——指向 `03_analysis/` 里的真实 artifact。
4. **威胁与排除**：列主要 confounding 威胁，逐一说明如何排除或为何不致命。

**措辞分级（必须与 `method_gate.md` 一致）**：

| method_gate 状态 | 允许的措辞 | 禁止的措辞 |
|---|---|---|
| PASS + 诊断干净 | "we identify the causal effect of ..." | — |
| PASS 但诊断偏弱 | "our estimates are consistent with a causal interpretation, though ..." | "proves", "causes"（无保留） |
| NOT PASS | "we document a robust association between ..." | 任何因果动词 |

---

## 7. 结果段：量级纪律（McCloskey-Ziliak）

结果段的核心病是「把统计显著当经济重要」。McCloskey 发现 1990 年代 AER 逾八成文章混淆二者。本层要求
**每个核心系数都配经济量级解读**：

- **标准化量级**：系数对应「X 上升一个标准差 → Y 变化占其均值/标准差几成」。
- **可感单位**：换算成读者能感知的单位（元、百分点、天、人）。
- **区分两种显著**：先说统计显著（star/CI），再单独说经济重要性（magnitude）；**不让星号替量级说话**。
- **基准对照**：把效应量与文献中可比效应或一个自然 benchmark 比，避免「孤零零一个数」。
- **克制外推**：样本内效应不直接当全国/长期效应；政策建议加边界条件。

> 这一节直接喂质量门维度④（解读克制度）：缺经济量级、把显著写成「重大影响」、政策建议超出证据 →
> 维度④封顶。Stage 6 用 `paper-self-revise` / `readability` 落实改写。

---

## 8. 表与图：写作端的「自解释」标准

Stage 4 产出出版级表图（由 `table`/`figure` skill 负责样式）；本层补**写作端验收**：每张表/图必须
**脱离正文也能读懂**。

- **标题自含**：题目说清样本、被解释变量、识别设定。
- **表注齐全**：样本量、R²/拟合、**聚类层级**、显著性星标定义、控制变量集合、固定效应。
- **图自解释**：坐标轴标签、置信带、参考线（如事件研究的 0 期）、图注说明读图方法。
- **数字一致**：表中每个数字都能在 `03_analysis/results/summary.md` 找到出处，且与正文叙述一致。
- **一表一论点**：`exhibits_index.md` 里每张表/图对应论文的一个具体 claim，不放「凑数」表。

---

## 9. 标题（Title）

- **信息密度**：标题点出 X、Y 与（可能的）识别场景，让人扫一眼知道这是关于什么的因果问题。
- **避免**：冒号后接空泛副标题、问句式标题（除非确有修辞效果）、塞方法缩写当卖点。
- **可引用**：好标题是综述里好引用的标题（"The Effect of [X] on [Y]: Evidence from [设置]"）。

---

## 10. 期刊「房风」（House Style）速查

写作规范因目标期刊而异（Stage 0 已问定 `target_journal`）。Stage 5/6 按下表对齐房风：

| 期刊群 | 引言风格 | 识别要求 | 结果呈现 | 语言 |
|---|---|---|---|---|
| **US Top-5**（QJE/AER/JPE/ECMA/ReStud） | 极简、贡献前置、roadmap 常省 | 识别是命门，事件研究/稳健性矩阵齐全 | 经济量级 + 机制叙事 | 英文，惜字如金 |
| **顶级金融**（JF/JFE/RFS） | 制度背景重、经济机制重 | 内生性处理（IV/DiD/RDD）+ 经济显著性 | 大量稳健性表、经济量级强调 | 英文 |
| **顶级管理 / 会计**（MS/JAR/TAR） | 理论假设 + 假设检验框架 | 识别 + 测量效度并重 | 假设逐条对照、边际效应 | 英文，结构化 |
| **国内顶刊**（《经济研究》《管理世界》《金融研究》《中国工业经济》） | 文献综述更完整、政策含义更突出 | 识别 + 内生性 + 稳健性「全家桶」 | 机制检验 + 异质性 + 政策建议 | 中文，规范见 `fix-chinese` |

> 国内顶刊与 US Top-5 的最大差异：国内期刊期待更完整的文献综述、更明确的政策落点、更全的稳健性套件；
> Stage 7 的中文分流（`fix-chinese` + `chinese-quote-converter` + 48/49）负责消除翻译腔与中英混排问题。

---

## 11. 接入点（写作层如何嵌进流水线与质量门）

| 接入点 | 本层做什么 | 落盘/判定 |
|---|---|---|
| **Stage 1 末** | 用 §3 四道自检锤炼贡献句，写进 `proposal.md` 的贡献模块 | `01_proposal/proposal.md` |
| **Stage 5 写作** | 喂 `paper-writer` 时附本文件 §2/§4/§5/§6 的结构要求 | `05_draft/main.tex` |
| **Stage 5 末 critic** | critic 按 §2 引言五段 + §5 结构 + §7 量级逐项挑错 | `05_draft/draft_audit.md` |
| **Stage 6 打磨** | `paper-pipeline` 内部打磨时对齐 §10 房风、§7 量级、§4 摘要 | `06_polish/main.tex` |
| **质量门维度①④⑤** | 贡献锋利度（§3）、解读克制度（§7）、写作与结构（§2/§5）三维按本文件标准打分 | `00_meta/quality_scorecard.md` |

> 写作层与方法层在质量门**合流**：维度②③（识别、稳健）查 `method_gate.md` 的真实 artifact（她那层），
> 维度①④⑤（贡献、克制、写作）查本层的写作标准。**证据为真 + 表达到位**，才是「可投稿级初稿」。
