# Stage Playbook — 逐阶段操作手册

> 主代理在**进入某阶段时**才读对应章节（渐进式加载，省上下文）。每一阶段都按 SKILL.md 的
> 「阶段执行协议」跑：**横幅 → in_progress → plan → execute → review → revise → 快照 → done →
> 阶段闸门**。本手册给出每阶段「调哪个 skill / 派哪种 subagent / 产出什么 / 失败怎么回退」。
>
> 所有路径里的 `67/` = `skills/67-econfin-workflow-toolkit/`。**调用某 skill 一律按
> [`skill-map.md`](skill-map.md) §0 的调用协议**：优先 `Skill(<注册名>)`，报 not found 就退回
> `Read <folder>/SKILL.md` 内联执行，绝不凭记忆脑补。可直接复制的 subagent 派发模板见
> [`subagent-templates.md`](subagent-templates.md)。

---

## Stage 1L · 文献底座（Literature Base）— Stage 1 之前的前置微阶段

**目的**：在动选题漏斗之前，先用真实文献**建一个可反复检索的本地语料底座**，产出一份**带引用的
文献扫描**。它是后面所有文献动作的地基：Stage 1 的查新有证据、Stage 5 的 related work 有出处、
Stage 6/9 的引用核验有物证、质量门维度 ⑥ 有旁证。

> **入口规则**：从 Stage 1 或 Stage 2 进入流水线时**必跑**；从 Stage 5 及之后进入时，若
> `01_proposal/literature/` 不存在而又需要写/补文献综述，则**按需补跑一次**（只跑检索+语料，
> 扫描问题换成 related-work 视角）。从 Stage 6+ 进入且不动文献综述时可 `skipped`。

**plan**
- 从用户给的研究方向（或已有 `proposal.md`）抽出 **2–4 组检索式**：核心主题、识别方法、
  被解释变量领域、制度背景。中文选题要**同时给英文检索式**（arXiv/OpenAlex 主要索引英文）。
- **确认 skill 可达**：按 [`skill-map.md`](skill-map.md) §0.3 的三级回退拿到 `literature-review-tools`
  与启动器路径 `{{LITRUN}}`；先 `python3 {{LITRUN}} doctor` 看工具链与已配的 API key。
  缺 `OPENAI_API_KEY` 就在闸门问用户一次（`litrun.py env --set`，**绝不回显全值**）；用户不给 →
  只跑免钥的检索/下载步，问答步跳过并标注。
- **重活先干跑**：`--dry-run` 看解析出的真实命令与目标路径，确认无误再实跑（全自动档位可不等确认，
  但 dry-run 结果仍要写进 `logs/stage_1L.md`）。

**execute**（派 **1 个** subagent，模板见 [`subagent-templates.md`](subagent-templates.md) §S1L）
- 主用工作流 **`topic-to-review-multi`**（arXiv + OpenAlex 合并语料，单源被限流时仍能出结果）：

  ```bash
  python3 {{LITRUN}} workflow run topic-to-review-multi \
    --query "<英文检索式>" --max 8 \
    --question "本领域已被做透的问题(Saturated)有哪些？尚存的空白(Opportunity)有哪些？必须对标的关键文献是哪几篇？" \
    2>&1 | tee "{{WS}}/01_proposal/literature/scan_raw.txt"
  ```

- 生物医学主题改走 `pubmed-fetch`；只要语料不要问答用 `topic-to-pdfs`（免钥）。
- **⚠️ 输出重定向（必做）**：litrun 把语料写在 `~/.lit-review-tools/workspace/runs/<workflow-id>/`
  （**按 id 命名、重跑即覆盖**）、把答案打到 stdout（不落盘）。所以每轮跑完立刻
  `cp -R .../corpus/. {{WS}}/01_proposal/literature/corpus/`，并把 stdout `tee` 成文件。
  **工作区内副本才是权威**，`~/.lit-review-tools/` 一律视作可被覆盖的临时缓存。
- 多组检索式**串行**跑（同名 workdir 会互相覆盖），每轮拷完再跑下一轮；语料合并进同一个
  `corpus/`，`manifest.json` 逐轮追加。
- 最后由 subagent 把各轮答案归并成结构化的
  `{{WS}}/01_proposal/literature/scan_digest.md`，固定三节：**Saturated（已做透）/ Opportunity
  （空白）/ Key references（关键对标文献，每条带出处）**。

**review**
- 主代理抽查 `scan_digest.md`：每条论断是否都指向 `corpus/` 里真实存在的文件？关键对标文献是否
  在 `manifest.json` 里？发现无出处的论断就打回重跑，**不要放行**。

**交付**
- `01_proposal/literature/corpus/`（PDF/txt + `manifest.json`）、`scan_digest.md`、`scan_raw.txt`；
  在 `workflow_state.json` 的 `literature` 块记 `corpus_dir` / `scan_digest` / `n_items` /
  `tools_used` / `degraded`。

**失败回退**
- skill 装不上 / 用户拒装 / 网络不通 → **降级模式**：`WebSearch` + `Skill(67/arxiv)` +
  `59-shiquda-openalex-skill` 做一次轻量扫描，`literature.degraded=true`，并在闸门**显著标注
  「文献底座为降级模式，引用需在 Stage 6 加倍核验」**。
- 检索几乎无结果 → 换检索式（更宽的上位词 / 换英文表述 / 换数据库），最多换 3 轮；仍无果则标红，
  提示用户这个方向可能过窄或表述不对。
- **任何情况下都不允许凭记忆编造文献名充数**——宁可降级并标注，也不要假语料。

---

## Stage 1 · 选题与设计

**目的**：把一个研究方向收敛成一份可直接进入实证的 proposal（X→M→Y、识别策略、样本、贡献边际、
目标期刊）。

**plan**
- 若用户已给方向，直接用；否则 `AskUserQuestion` 问方向 + 想要的候选标题数 N（缺省 5）。
- **先确认 Stage 1L 已完成**：`01_proposal/literature/scan_digest.md` 就是下面 §S1 模板里
  `{{LITERATURE_SCAN_DIGEST}}` 的**唯一来源**（只取其 Saturated / Opportunity 两节，别灌全文）。
  没跑 1L 就先跑 1L——**不要让 subagent 凭记忆想象文献版图**。
- 读 `67/econfin-idea-finder/SKILL.md`，按其漏斗逻辑运行。

**execute（并行 subagent，强制调用子 skill）** — 直接套用
[`subagent-templates.md`](subagent-templates.md) §S1：
- 用 `Agent` 派 N 路并行 subagent（每批 ≤5），**每个 subagent 的 prompt 必须强制它**：
  1. `Skill(skill="Econfin-Proposal")`（注册名大写，见 skill-map §0.1）生成计划书；not found 则
     `Read 67/econfin-proposal/SKILL.md` 执行；
  2. `Skill(skill="novelty-check")` 查新打分；not found 则 `Read 67/novelty-check/SKILL.md`；
  3. 只有 novelty ≥ 9（顶刊层次）才把「proposal + 查新」合并 md **写入工作区**
     `01_proposal/candidates/<短名>-<分数>.md`——**这是对 `econfin-idea-finder` 硬编码
     `F:\Dropbox\CC\选题大全\` 输出根的强制覆盖**（见 skill-map §0.2）；否则内部丢弃、不写盘、不回传全文；
  4. 只向主代理回传 ≤8 行摘要（标题、分数、是否保留、一句话贡献）。
- 主代理再 `Skill(skill="Significance-Search")`（注册名大写）给保留候选补「学术 + 现实」重要性证据；
  `Skill(skill="journal-digest")` 扫目标期刊近年口味——**调用时显式要求它把摘要写到
  `01_proposal/journal_digest.md`**（同样覆盖其 Dropbox 硬编码输出）。

**review（独立 critic subagent）**
- 派一个「资深 AE」critic subagent，拿 Edmans (2024) "1000 Rejections" 红线对每个保留候选挑刺
  （是不是 convex combination、贡献是否单薄、识别是否可信），把意见写入 `01_proposal/critique.md`。

**revise / 交付**
- 主代理据 critique 让用户（或在全自动档位下自行）选定 1 个标题，把最终计划书定稿为
  `01_proposal/proposal.md`，并在其中**显式写死**：被解释变量 Y、核心解释变量 X、机制 M、
  识别策略（DiD/IV/RDD/SC/...）、样本与政策冲击、目标期刊。这份 `proposal.md` 是后续所有阶段的合同。

**失败回退**：N 个候选全 < 9 分 → 扩大方向或换角度重跑一轮；查新发现已被做过 → 标红，回到 plan
另寻差异化切口。

---

## Stage 2 · 数据

**目的**：依 proposal 的变量与样本，拿到**分析就绪**的数据集 + codebook。

**plan**：从 `proposal.md` 抽出需要的变量、频率、地域、时间窗、合并键，列一张「变量→数据源」需求表。

**execute**
- `Skill` 调用 `67/data-fetcher` 取数（FRED / World Bank / BLS / OECD / Yahoo Finance；A 股/中国
  宏观等可配合 `57-dgunning-edgartools`、`58-charlescoverdale-econstack`、`59-shiquda-openalex-skill`
  等集合，见 skill-map）。多个独立数据源可并行 subagent 各取一段、各自写盘到 `02_data/raw/`。
- `Skill` 调用 `67/data-cleaning` 做清洗、对齐、合并、构造变量，产出 `02_data/clean.parquet`
  （或 `.dta/.csv`）与 `02_data/codebook.md`（每个变量的定义、来源、单位、缺失处理）。

**review**：critic subagent 核对——合并键唯一性、面板是否平衡、极端值/缺失处理是否记录在 codebook、
处理与对照如何界定（若是 DiD/SC）。意见写 `02_data/data_audit.md`。

**revise / 交付**：据审计修清洗脚本，重跑到干净。**清洗脚本必须留在 `02_data/`**，保证可复现。

**失败回退**：关键数据取不到 → 标红，给替代代理变量方案或缩小样本，必要时回 Stage 1 调整设计。

---

## Stage 3 · 计量识别与估计

**目的**：按 proposal 的识别策略，跑出基准 + 机制 + 异质性 + 稳健性的**真实**结果。

**plan（先定方法）**
- 从 `proposal.md` 读识别策略，按下表择一主 skill（决策树细节见 skill-map 的「方法路由」）：

  | 设计 | 主 skill（`67/`） | 配套 |
  |---|---|---|
  | 政策评估 / 自然实验 / 双重差分 | `did-analysis` | 平行趋势、事件研究、交错估计量 CS/SA/BJS |
  | 内生性 / 工具变量 | `iv-estimation` | 弱工具检验、过度识别 |
  | 断点 | `rdd-analysis` | 带宽、操纵检验、密度检验 |
  | 单一处理单位 / 政策试点 | `synthetic-control` | 安慰剂、RMSPE |
  | 一般面板 | `panel-data` | FE/RE、聚类稳健 SE |
  | 截面 / 基础回归 | `ols-regression` | 稳健 SE |
  | 时间序列 / 宏观 | `time-series` | 单位根、协整、VAR/IRF |
  | 异质处理效应 / 高维 | `ml-causal` | 因果森林、DML |

- **可选增强**：用 StatsPAI MCP 链路做 agent-native 因果推断与稳健性自检：
  `detect_design → preflight → recommend → 用 as_handle=true 拟合得 result_id →
  audit_result(result_id) 列出缺的稳健性 → 逐个调它建议的函数 →
  honest_did_from_result / sensitivity_from_result → bibtex(keys) 取可信引用`。

**execute**
- `Skill` 调用选定的估计 skill，按其工作流跑基准回归（用 `64-tmonk-mcp-stata` / `mcp__stata-*`
  跑 Stata，或 Python statsmodels/linearmodels/pyfixest=`40-py-econometrics-pyfixest`）。
- **稳健性矩阵并行化**（套用 [`subagent-templates.md`](subagent-templates.md) §S3）：把"安慰剂、
  替换样本、替换度量、加/减控制变量、改聚类层级、子样本异质性、机制中介"等彼此独立的检验，一次性
  派多个 subagent 并行跑，**每个 subagent 自己把系数/SE/图写盘**到
  `03_analysis/robustness/<name>.json|png`，只回传"通过/不通过 + 关键系数"。
- 所有代码留在 `03_analysis/`（`.py`/`.do`/`.R`），结果存 `03_analysis/results/`。

**review**：派一个 `66-zheng-siyao-empirical-research-skills` 风格的 critic（`did-reviewer` /
`econ-reviewer`）做对抗审阅——识别假设是否真的成立、SE 聚类是否正确、是否 p-hacking 嫌疑。
意见写 `03_analysis/results_audit.md`。

**revise / 交付**：据审阅补检验、修设定，定稿 `03_analysis/results/main_results.json` 与一份
`03_analysis/results/summary.md`（人话版结论）。

**失败回退（关键）**：平行趋势不过 / IV 弱工具 / 系数不显著 / 机制不成立 → **不要硬写成功**。
按 `China-CF-study` 纪律自动切备选：换识别策略、换工具变量、换对照组、改窗口；连续失败则在闸门
标红，回 Stage 1/2 调设计或数据。每次回退都记进 `logs/stage_3.md`。

---

## Stage 4 · 表与图

**目的**：把 Stage 3 的结果做成**出版级**三线表与图（事件研究图、系数图、机制图）。

**execute**
- `Skill` 调用 `67/table` 生成 LaTeX 三线回归表（主表 + 稳健性表 + 描述性统计表），落 `04_results/*.tex`。
  Stata 用户可配合 `18-jusi-aalto-stata-accounting-research`、`32-dylantmoore-stata-skill` 的表格规范，
  或 `66/latex-table`。
- `Skill` 调用 `67/figure` 画事件研究 / 系数 / 机制图，落 `04_results/*.pdf` + `*.png`。
- `39-vincentarelbundock-marginaleffects` 可用于边际效应图。

**review**：critic 检查——表注是否齐（样本量、R²、聚类层级、显著性星标说明）、图是否自解释、
数字与 Stage 3 结果一致。意见写 `04_results/figtab_audit.md`。

**revise / 交付**：定稿 `04_results/`，并生成一份 `04_results/exhibits_index.md` 列出每张表/图对应
论文的哪个论点，供 Stage 5 写作直接引用。

---

## Stage 5 · 写作初稿

**目的**：从表图产出一份结构完整的 LaTeX 初稿。

**execute**
- **先起草 related work（派 1 个 subagent，模板见 [`subagent-templates.md`](subagent-templates.md) §S5L）**：
  用 `literature-review-tools` 在 **Stage 1L 已建好的语料上**跑
  `workflow run topic-to-related-work`（或 `pdf-corpus-qa --input {{WS}}/01_proposal/literature/corpus`
  复用语料、**不重复下载**），产出一段**带引用**的 related-work 初稿到
  `05_draft/related_work_draft.md`，同时把命中的文献条目补进 `05_draft/ref.bib`。
  1L 是降级模式（`literature.degraded=true`）时**跳过本步**并在日志标注，改由 `paper-writer`
  按 `scan_digest.md` 保守成文。
- `Skill` 调用 `67/paper-writer`，喂入 `04_results/`（表图）+ `01_proposal/proposal.md`（动机/贡献/
  假设）+ `05_draft/related_work_draft.md`（文献综述素材），让它按"Intro → 文献/制度背景 → 数据 →
  识别策略 → 结果 → 机制 → 稳健性 → 结论"写出 `05_draft/main.tex` 与 `05_draft/ref.bib`。
  **related-work 初稿是素材不是成品**——由 `paper-writer` 消化成正式一节、并把定位写成
  「相对谁前进了一步」，不要整段照抄。
- 真要做**系统综述式**的文献工作（千级摘要筛选）时，用 `literature-review-tools` 的 `asreview`
  做 PRISMA 主动学习筛选，方法学规范配 `52-keemanxp-slr-prisma`；其余场景配
  `36-taoyunudt-literature-review-skill`、`59-shiquda-openalex-skill`；引用入库可配 Zotero MCP
  （`litrun.py mcp zotero-mcp` 打印配置块）。

**review**：critic 通读——贡献句是否锋利、识别策略段是否说服力够、结果段是否克制（不过度解读）、
**文献综述里每条引用是否能在 `01_proposal/literature/corpus/manifest.json` 或 `ref.bib` 里找到出处
（找不到出处的一律标为疑似幻觉，留给 Stage 6 的 `reference-verify` 处置）**。
意见写 `05_draft/draft_audit.md`。

**revise / 交付**：据审阅改一轮，定稿初稿。**注意**：此处只求"完整且自洽的初稿"，精修留给 Stage 6。

---

## Stage 6 · 全流程打磨

**目的**：把初稿过一遍成熟的固定打磨流水线。

**execute**
- **直接 `Skill` 调用 `67/paper-pipeline`**，把 `05_draft/`（或复制到 `06_polish/`）和目标期刊
  传给它。它内部会按固定顺序自动跑：`paper-polish → paper-self-revise → paper-style →
  paper-polish（二轮）→ reference-verify`，并自带它**自己的** `pipeline_state.json`、阶段备份、
  交互档位。**不要在这里重复它的逻辑**——本编排器只负责把输入喂对、把它的产出收回主线。
- 把 `paper-pipeline` 的交互档位与本编排器的档位对齐（全自动↔全自动 / 阶段确认↔stage-confirm）。

**交付**：打磨后的 `06_polish/main.tex` + `ref.bib` + `ref_verify_report.xlsx` + pipeline 报告。

**失败回退**：`paper-pipeline` 内部中断 → 它自身可断点续跑，本编排器记录其状态后在闸门提示用户。

---

## Stage 7 · 语言与去 AI 味

**目的**：消除 AI 腔 / 翻译腔，达到人类学者写作质感（按 Stage 0 选定的语言分流）。

**execute**
- **英文稿**：`Skill` 调用 `67/readability` 做语法/可读性逐项修；再按需用
  `44-matsuikentaro1-humanizer_academic`、`45-stephenturner-skill-deslop`、`46-hardikpandya-stop-slop`、
  `47-conorbronsdon-avoid-ai-writing` 去 AI 套话；经济学行文规范配 `56-hanlulong-econ-writing-skill`。
- **中文稿**：`Skill` 调用 `67/fix-chinese`（去翻译腔 + 中英混排规范）+ `67/chinese-quote-converter`
  （直引号转弯引号）；再按需用 `48-copaper-ai-chinese-de-aigc`、`49-voidborne-d-humanize-chinese`
  做中文去 AIGC。
- 去味是"逐句改写"性质，独立段落可并行 subagent 处理，各自写盘回 `07_dehumanize/`。

**review**：critic 抽查——是否仍有"首先/其次/综上所述/值得注意的是"等套话、是否破坏了术语准确性。

**revise / 交付**：定稿到 `07_dehumanize/main.tex`，回灌主稿。

---

## 🏁 里程碑 · 初稿质量门（Draft Quality Gate）—— Stage 7 之后、Stage 8 之前强制执行

**目的**：兑现「**高质量**初稿」承诺。不靠主代理自评，而是**派一个独立「顶刊 AE」critic subagent**，
按 [`quality-rubric.md`](quality-rubric.md) 的 7 维评分卡量化打分，决定「放行进投稿」还是「回炉重做」。

**execute**（套用 [`subagent-templates.md`](subagent-templates.md) §QG，**只派 1 个**）
- critic 必读 `references/quality-rubric.md`，读初稿（`07_dehumanize/main.tex` + `04_results/` 表图 +
  `05_draft/ref.bib`）+ 对照 `01_proposal/proposal.md`（贡献承诺）与 `03_analysis/results/summary.md`
  （真实结果），**逐维打分写入 `00_meta/quality_scorecard.md`**，本轮分数追加进 `logs/quality_gate.md`。
- 7 维：① 贡献锋利度 ② 识别可信度 ③ 稳健性完整度 ④ 解读克制度 ⑤ 写作与结构 ⑥ 引用真实性 ⑦ 可复现性。

**达标判定（三条同时满足才 `pass`）**：每维 ≥ 7 **且** 总分 ≥ 56/70 **且** ②③⑥ 无任何致命红旗。

**revise / 回退**
- `pass` → `workflow_state.json` 置 `quality_gate=pass`、`draft_milestone=done`；进入可选 Stage 8–9。
- `not pass` → 按评分卡的「短板 → 回退阶段」映射退回对应阶段重做（识别→Stage 3、贡献→Stage 1、
  写作→Stage 5/6、引用→reference-verify、复现→Stage 2/3）。**同一维最多回退 2 轮**；2 轮后仍卡，
  在闸门**显著标红**告知用户「已知短板 + 当前分」，由用户裁决是否带病进入投稿（绝不静默放行）。
- 每次回退记入 `logs/quality_gate.md` 与 `workflow_state.json` 的 `decisions`。

> 质量门 ≠ Stage 6 打磨（改语言）≠ Stage 8 评审（挑学术硬伤）；它只做一件事——**按统一 rubric
> 量化「这份初稿够不够格」并决定放行/回炉**。它是「可投稿级初稿」这一核心交付里程碑的验收闸门。

---

## Stage 8 · 模拟评审与修订

**目的**：在投稿前先自做一轮"审稿—回应—修订"，把硬伤暴露在自己手里。

**execute**
- `Skill` 调用 `67/referee-report` 生成审稿报告（可设 normal/high-level 档与意见条数；
  推荐先按 Major Revision 口吻拿到建设性意见），落 `08_review/referee_report.md`。
- `Skill` 调用 `67/paper-referee-revise`，按审稿意见**逐条**修订 `main.tex`，并生成 response letter
  落 `08_review/response_letter.md`。若是内部自评则用 `67/paper-self-revise`。
- 想要更狠的对抗审阅可叠加 `66/grillme`、`66/econ-reviewer`、`21-claesbackman-AI-research-feedback`、
  `41-sticerd-eee-sewage-econometrics-check`（计量自检）。

**review**：critic 核对——每条审稿意见是否都有实质回应、修订是否引入新矛盾（交叉引用、表号）。

**revise / 交付**：定稿修订稿 + response letter 到 `08_review/`。

**失败回退**：审稿暴露根本性识别缺陷 → 回 Stage 3（补检验/换策略）甚至 Stage 1（改设计），并标红。

---

## Stage 9 · 选刊与投稿

**目的**：定目标期刊、备齐投稿材料、做最后一次引用终审。

**execute**
- `Skill` 调用 `67/paper-submission`，评估贡献新颖度、匹配 SSCI/ABS 星级、给出 ~20 本目标期刊清单，
  落 `09_submission/journal_shortlist.md`。结合 Stage 0 选定的目标期刊收敛到 1 主 + 2 备。
- **终审引用**：再 `Skill` 调用一次 `67/reference-verify`（投稿前最后一次，确保此前所有修订没动坏
  引用），落 `09_submission/ref_verify_final.xlsx`。把 `01_proposal/literature/corpus/manifest.json`
  一并喂给它作「确有此文且我们真读过」的旁证；**核验结论仍以 `reference-verify` 为准**，manifest
  只减少误判、不替代核验。
- 生成 cover letter / highlights / 作者贡献声明等投稿材料到 `09_submission/`。
- 需要排版成 Word / 提交版 PDF 时用 `67/md-to-docx`、`67/markitdown`、`08-ndpvt-web-latex-document-skill`。

**review**：critic 走一遍目标期刊的 submission checklist（字数、匿名化、利益冲突声明、数据可得性声明）。

**revise / 交付**：定稿投稿包到 `09_submission/`。

---

## 收尾（编排器本体，不调子 skill）

汇总所有阶段日志与产出，写 `FINAL_REPORT.md`（见 SKILL.md「收尾」节的清单），打包并告知用户
交付物路径与一键重跑命令。
