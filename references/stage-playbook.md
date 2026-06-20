# Stage Playbook — 逐阶段操作手册

> 主代理在**进入某阶段时**才读对应章节（渐进式加载，省上下文）。每一阶段都按 SKILL.md 的
> 「阶段执行协议」跑：**横幅 → in_progress → plan → execute → review → revise → 快照 → done →
> 阶段闸门**。本手册给出每阶段「调哪个 skill / 派哪种 subagent / 产出什么 / 失败怎么回退」。
>
> 所有路径里的 `67/` = `skills/67-econfin-workflow-toolkit/`；调用某 skill 即用 `Skill` 工具
> 加载它的 `SKILL.md` 并按它自己的工作流跑到完成，再回主线。

---

## Stage 1 · 选题与设计

**目的**：把一个研究方向收敛成一份可直接进入实证的 proposal（X→M→Y、识别策略、样本、贡献边际、
目标期刊）。

**plan**
- 若用户已给方向，直接用；否则 `AskUserQuestion` 问方向 + 想要的候选标题数 N（缺省 5）。
- 读 `67/econfin-idea-finder/SKILL.md`，按其漏斗逻辑运行。

**execute（并行 subagent，强制调用子 skill）**
- 用 `Agent` 派 N 路并行 subagent（每批 ≤5），**每个 subagent 的 prompt 必须强制它**：
  1. `Skill` 调用 `67/econfin-proposal` 生成该候选的计划书；
  2. `Skill` 调用 `67/novelty-check` 查新打分；
  3. 只有 novelty ≥ 9（顶刊层次）才把「proposal + 查新」合并 md **写入**
     `01_proposal/candidates/<短名>-<分数>.md`，否则内部丢弃、不写盘、不回传全文；
  4. 只向主代理回传 ≤8 行摘要（标题、分数、是否保留、一句话贡献）。
- 主代理再 `Skill` 调用 `67/significance-search` 给保留下来的候选补「学术 + 现实」重要性证据，
  `67/journal-digest` 扫目标期刊近年口味，辅助定刊。

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
- **稳健性矩阵并行化**：把"安慰剂、替换样本、替换度量、加/减控制变量、改聚类层级、子样本异质性、
  机制中介"等彼此独立的检验，一次性派多个 subagent 并行跑，**每个 subagent 自己把系数/SE/图
  写盘**到 `03_analysis/robustness/<name>.json|png`，只回传"通过/不通过 + 关键系数"。
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
- `Skill` 调用 `67/paper-writer`，喂入 `04_results/`（表图）+ `01_proposal/proposal.md`（动机/贡献/
  假设），让它按"Intro → 文献/制度背景 → 数据 → 识别策略 → 结果 → 机制 → 稳健性 → 结论"写出
  `05_draft/main.tex` 与 `05_draft/ref.bib`。
- 文献综述薄弱时，配合 `36-taoyunudt-literature-review-skill`、`52-keemanxp-slr-prisma`、
  `59-shiquda-openalex-skill` 补做结构化综述；引用入库可配 Zotero MCP。

**review**：critic 通读——贡献句是否锋利、识别策略段是否说服力够、结果段是否克制（不过度解读）。
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
  引用），落 `09_submission/ref_verify_final.xlsx`。
- 生成 cover letter / highlights / 作者贡献声明等投稿材料到 `09_submission/`。
- 需要排版成 Word / 提交版 PDF 时用 `67/md-to-docx`、`67/markitdown`、`08-ndpvt-web-latex-document-skill`。

**review**：critic 走一遍目标期刊的 submission checklist（字数、匿名化、利益冲突声明、数据可得性声明）。

**revise / 交付**：定稿投稿包到 `09_submission/`。

---

## 收尾（编排器本体，不调子 skill）

汇总所有阶段日志与产出，写 `FINAL_REPORT.md`（见 SKILL.md「收尾」节的清单），打包并告知用户
交付物路径与一键重跑命令。
