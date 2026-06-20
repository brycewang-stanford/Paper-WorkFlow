# Literature & Positioning Pack — 文献检索与贡献定位增强层

> 在 Stage 1（查新与贡献锻造）、Stage 5（写引言与文献综述段）、Stage 8（被问「文献定位不准」时）加载。
> 本文件把「怎么系统地把相关文献找全、再把本文的贡献精确卡进文献空白」落成可执行流程：结构化检索 →
> 文献矩阵 → 定位句式 → 引用真实性。
>
> **分工**：[`writing-craft.md`](writing-craft.md) §2/§3 管「引言五段公式 + 贡献句怎么写」（是**写法**）；
> 本文件管「文献怎么找全、贡献相对哪几篇前进了一步、怎么用文献矩阵看出白space」（是**调研与定位**）。
> 查新与重要性论证仍调用既有 skill（`novelty-check`、`significance-search`、`36`/`52`/`59` 综述类，见
> [`skill-map.md`](skill-map.md)）；本文件规定「找到什么程度、定位准到什么程度才算达标」。

---

## 0. 这个增强层解决什么

引言里那段**贡献定位**（"this paper is most closely related to X, but differs in Y"）是 desk-reject 的高发区：
Edmans (2024) 统计 999 封拒稿里逾半是因贡献不清被**直接桌拒**。本层要求：

1. **检索要系统**：不靠记忆和零散搜索，用前向/后向滚雪球 + 引用图工具把相关文献找全。
2. **定位要显式**：点名最接近的 3–5 篇，逐篇说清本文在哪一维（数据/识别/机制/场景）前进了一步。
3. **白space要可见**：用文献矩阵把前作按（场景、数据、识别、发现）排开，让未被覆盖的格子一目了然。
4. **引用要真实**：每条引用核 DOI、对作者与年份，杜绝幻觉/张冠李戴文献（呼应质量门维度⑥）。

> 本层是**调研与定位标尺**，不替代写作或查新 skill。具体查新调 `novelty-check`，综述调 `36`/`52`/`59`，
> 入库配 Zotero MCP；本文件只规定「找全、定准、引真」三件事的验收标准。

---

## 1. 检索：结构化而非叙事式

**两种「文献综述」别混为一谈**：
- **定位型综述**（论文 intro / related-work 段）：**论证性**的，只引「承重」文献，funnel 到本文的空白。
- **系统综述**（综述本身就是论文）：**协议驱动**的，要按 PRISMA 2020 记录检索→筛选→纳入，可复现。
  仅当「综述即论文」时才用 PRISMA（https://www.prisma-statement.org/prisma-2020-statement）。

**结构化检索（hybrid 最佳实践）**：一次关键词数据库检索 + 滚雪球，迭代到不再冒出新相关文献：
- **后向滚雪球**：挖种子论文的参考文献列表（它站在谁的肩膀上）。
- **前向滚雪球**：找谁引用了种子论文（Google Scholar / OpenAlex 的 "cited by"）——这是发现最新进展的关键。
- 迭代：新发现的关键文献再做一轮前后向，直到收敛。

---

## 2. 文献发现与引用图工具

| 工具 | URL | 最适合 |
|---|---|---|
| OpenAlex | https://openalex.org （API: https://api.openalex.org） | 免费开放目录 + API，可程序化拉前后向引用 |
| Semantic Scholar | https://www.semanticscholar.org | AI 检索、2 亿+ 论文、引用上下文、免费 API |
| Google Scholar | https://scholar.google.com | 覆盖最广；"Cited by" 做前向滚雪球 |
| Connected Papers | https://www.connectedpapers.com | 共被引/文献耦合生成单图谱，快速找邻近工作 |
| Litmaps | https://www.litmaps.com | 迭代式种子图 + 新文提醒 |
| Research Rabbit | https://www.researchrabbitapp.com | 基于合集的「更早/更晚/相似」推荐 |
| NBER | https://www.nber.org | 美国经济前沿工作论文 |
| SSRN | https://www.ssrn.com | 金融/管理/经济早期工作论文 |
| RePEc / IDEAS | https://ideas.repec.org | 经济学专属索引，作者/引用追踪 |

> 工作流里：母仓库可调 `59-shiquda-openalex-skill`、`68/.../nber-working-papers-api`、`67/arxiv`、
> `67/web-research` 做检索；入库与去重配 Zotero MCP（`zotero_*`）。能调 MCP/skill 就别手抄。

---

## 3. 文献矩阵——让白space看得见

把候选前作排进一张矩阵（落 `01_proposal/lit_matrix.md`），列固定为：

| 列 | 记什么 |
|---|---|
| Citation / 年份 | bib key + 年 |
| Setting | 国家 / 时期 / 单位 |
| Data / Sample | 数据源与样本 |
| **Identification** | 识别策略（DiD/IV/RDD/SC/相关性…） |
| Outcome(s) | 被解释变量 |
| Key finding / 效应量 | 主结论与量级 |
| Limitation | 该文的短板 |
| **Relation to us** | 本文相对它前进在哪 |

> **把 "Identification" 与 "Finding" 两列对齐看**，未被覆盖的格子（没人做过的场景、更弱的识别、互相
> 矛盾的发现）就是你的白space。这张矩阵既是 Stage 1 找切口的工具，也是 Stage 5 写 related-work 段的原料。

---

## 4. 定位句式（可直接套用的贡献句模板）

顶刊引言用这些句式把贡献钉进文献（与 [`writing-craft.md`](writing-craft.md) §3 贡献段三槽配合）：

1. 「本文与 **[X]** 最相关，他们研究……；我们的不同在于 **[数据 / 识别 / 场景]**。」
2. 「大量文献记录了 **[A]**；我们是**第一个** **[B]**，利用 **[变异来源]**。」
3. 「既有工作确立了 **[发现]**，但无法区分 **[机制₁]** 与 **[机制₂]**；我们的 **[设计]** 能做到。」
4. 「我们**打通**了此前彼此孤立发展的 **[文献 1]** 与 **[文献 2]**。」
5. 「相对依赖 **[更弱设计]** 的 **[X, Y, Z]**，我们提供 **[更干净的识别 / 新数据]**。」
6. 「本文的贡献是 **[描述性 / 因果 / 方法性]** 的：我们 **[动词]**，而不只是 **[动词]**。」

**四个让 reviewer 一眼看到空白的动作**：
1. **点名最接近的 3–5 篇**，逐篇说清你在哪一维前进——别让 referee 猜。
2. **把空白写成「缺陷」而非「空缺」**：「X 无法识别 Y」强于「没人研究过 Y」。
3. **贡献摆成 ~3 条的带标记列表**，放引言靠前（Head's rule）。
4. **把空白接到你的设计上**：贡献句要让你的方法成为「填补该缺陷」的显然解。

> 反面（命中即回 Stage 1/5 重写）：把 related-work 写成**逐篇摘要的注释书目**（annotated bibliography），
> 而不是 funnel 到本文空白；堆 20 个 citation 却不说本文相对谁前进了一步。

---

## 5. 引用真实性——10 秒核查，省一次 desk-reject

LLM 辅助写作时极易混入**幻觉/张冠李戴**的引用。纪律：
- 每条引用核 **DOI**（Crossref: https://www.crossref.org/）并**对齐标题/作者/年份**——很多假引用 DOI 能解析
  但标题对不上。
- 关键文献过一遍 **Retraction Watch**（https://retractionwatch.com ，Crossref 托管）查撤稿。
- 工作流里把这步交给 `reference-verify`、`66/citation-fidelity`、`62-PHY041-...citation-checker`、Zotero MCP
  `scite_check_retractions`——**绝不让 subagent 凭记忆生成引用**。

---

## 6. 接入点（本层如何嵌进流水线与闸门）

| 接入点 | 本层做什么 | 落盘 / 判定 |
|---|---|---|
| **Stage 1 查新** | 结构化检索（§1/§2）+ 文献矩阵（§3），定位本文白space | `01_proposal/lit_matrix.md` |
| **Stage 1 贡献** | 用 §4 句式 + 四动作把贡献卡进空白，写进 proposal 贡献模块 | `01_proposal/proposal.md` |
| **Stage 5 related-work 段** | 按文献矩阵写 funnel 式定位段，点名最接近的 3–5 篇 | `05_draft/main.tex` |
| **Stage 5/9 引用核验** | 每条引用核 DOI + 撤稿检查（§5） | `06_polish/ref_verify_report.xlsx` |
| **Stage 8 被质疑定位** | 「文献定位不准/关键对标缺席」时回 Stage 5 补矩阵相关行 | `08_review/response_letter.md` |
| **质量门维度①⑥** | 贡献是否卡进真实空白（①）、引用是否真实+定位是否准（⑥） | `00_meta/quality_scorecard.md` |

**与 [`quality-rubric.md`](quality-rubric.md) 的硬挂钩**：
- related-work 写成注释书目、不点名最接近前作、不说本文前进在哪 → 维度①（贡献锋利度）最高 6。
- 存在幻觉/张冠李戴引用，或关键对标文献缺席导致贡献被高估 → 维度⑥（引用真实性）封顶 4（致命红旗）。

> 一句话：**贡献不是「我做了 X」，而是「相对最接近的那几篇，我在某一维前进了一步」。** 本层用结构化检索
> 把相关文献找全、用文献矩阵让白space可见、用定位句式把贡献钉进去——把质量门维度①⑥的回炉提前消化在
> Stage 1/5。
