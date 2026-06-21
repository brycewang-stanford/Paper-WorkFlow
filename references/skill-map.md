# Skill Map — 「任务 → 用哪个 skill」全量路由表

> 本编排器的"零件库"。**主线（粗体）几乎全部来自 `67-econfin-workflow-toolkit/`**，因为它是
> 唯一一套为实证论文全流程设计、彼此可组合的 skill 集；其余 68 个集合按需作为**增强 / 替代 /
> 专项**接入。路径 `67/x` = `skills/67-econfin-workflow-toolkit/x/SKILL.md`。
>
> 调用一个 skill = 让它的 `SKILL.md` 正文驱动这一步，按它自己的工作流跑到完成。**能调用就
> 不要重写。** 但「怎么调用」有讲究——见下面的「调用机制」，它决定了本编排器是否真的跑得通。
> 现代因果推断/应用计量的最低证据包见 [`research-grade-methods.md`](research-grade-methods.md)；
> Stage 3 的方法选择必须同时满足该文件的 Method Gate。**Stage 3–4 先按
> [`analysis-backends.md`](analysis-backends.md) 选择 Python/StatsPAI、Stata、R 后端**；默认后端是
> StatsPAI（MCP 优先、`statspai` 包做重活），用法见 [`statspai-analysis.md`](statspai-analysis.md)。

---

## 0. 调用机制（先读这个——决定编排器能否真的跑通）

被编排的子 skill（`67/` 工具箱、`66/` reviewer 等）**不在本编排器仓库内**——本目录
`69-Paper-WorkFlow` 是母仓库 [`Auto-Empirical-Research-Skills`](https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills)
的一个 **submodule**，子 skill 都在母仓库的 `skills/` 下。它们是**仓库内的文件夹**，不一定在用户运行时
里**注册**为可被 `Skill` 工具直接触发的 skill（母仓库根目录没有统一的 marketplace/plugin 清单）。
**因此运行本编排器前提是母仓库已 checkout**（`67/`、`66/` 等可达）；下文 `Read` 回退路径都相对母仓库
根目录。调用子 skill 有**两条路径**，编排器按下面的优先级择一：

1. **`Skill` 工具（快路径，仅当该 skill 已注册时可用）**：`Skill(skill="<注册名>", args=...)`。
   注册名是该 skill `SKILL.md` 前言里的 `name:` 字段，**不一定等于文件夹名**（见下表的大小写/改名
   差异）。若 `Skill` 调用报「skill not found」，立刻退回路径 2，不要反复试。
2. **`Read` + 内联执行（稳路径，永远可用）**：`Read skills/67-econfin-workflow-toolkit/<folder>/SKILL.md`
   把它的正文读进来，**当作本步的操作手册逐步执行**（轻量步骤在主代理里跑；重量步骤把「读这个
   SKILL.md 并按它执行」写进 subagent 的 prompt，由 subagent `Read` 后执行）。子 skill 自带的
   `references/`、`assets/` 也按其 SKILL.md 指引按需 `Read`。

> **派给 subagent 时务必传绝对路径**：subagent 的工作目录可能与主代理不同，prompt 里给
> `Read` 的 SKILL.md 路径要写成仓库内的完整相对/绝对路径，否则它找不到文件会「凭印象脑补」——
> 这正是 `econfin-idea-finder` 反复警告要避免的劣化模式。

### 0.1 注册名对照表（`Skill` 工具用这一列，别用文件夹名猜）

只有下列 skill 的**注册名 ≠ 文件夹名**，用 `Skill` 工具时必须用「注册名」列；其余 skill 注册名与
文件夹名一致（如 `did-analysis`、`paper-writer`、`reference-verify`…可直接用文件夹名）。

| 文件夹（`67/`，除非另注） | **`Skill` 注册名** | `Read` 回退路径 |
|---|---|---|
| `econfin-proposal` | **`Econfin-Proposal`** | `67/econfin-proposal/SKILL.md` |
| `significance-search` | **`Significance-Search`** | `67/significance-search/SKILL.md` |
| `chinese-ppt` | **`chinese-ppt2`** | `67/chinese-ppt/SKILL.md` |
| `command-development` | **`Command Development`** | `67/command-development/SKILL.md` |
| `China-CF-study` | **`China-CF-Study`** | `67/China-CF-study/SKILL.md` |
| `Foreign-CF-study` | **`Foreign-CF-Study`** | `67/Foreign-CF-study/SKILL.md` |

其余直接用文件夹名作注册名的常用 skill（注册名 = 文件夹名）：`econfin-idea-finder`、`novelty-check`、
`journal-digest`、`data-fetcher`、`data-cleaning`、`did-analysis`、`iv-estimation`、`rdd-analysis`、
`synthetic-control`、`panel-data`、`ols-regression`、`time-series`、`ml-causal`、`stata`、`stats`、
`table`、`figure`、`paper-writer`、`paper-pipeline`、`paper-polish`、`paper-self-revise`、`paper-style`、
`reference-verify`、`readability`、`fix-chinese`、`chinese-quote-converter`、`referee-report`、
`paper-referee-revise`、`paper-submission`、`master-thesis-review`、`md-to-docx`、`markitdown`、
`marp-slides-creator`、`marp-export`、`web-access`、`web-research`、`agent-browser`、`arxiv`、
`skill-creator`。`00.2-Full-empirical-analysis-skill_Stata` 的注册名是
`Full-empirical-analysis-skill-Stata`；`00.3-Full-empirical-analysis-skill_R` 的注册名是
`Full-empirical-analysis-skill-R`。`66/` 的 reviewer（`did-reviewer`、`econ-reviewer`、`grillme`、`latex-table`、
`citation-fidelity`、`codebook-pass`、`R-optimizer`）注册名均 = 文件夹名。

### 0.2 输出路径重定向（**两个 skill 会把产出写到仓库外，必须改写**）

有两个子 skill 在其 SKILL.md 里**硬编码了 Windows 绝对输出路径**（一个 Dropbox、一个 OneDrive），
被编排时会把产物写到工作区之外（在非 Windows 机器上甚至写不进去）。调用它们时，**必须在传入的
args / subagent prompt 里显式覆盖输出目录为本工作区路径**：

| skill | 它硬编码的输出根 | 编排时**强制改写**为 |
|---|---|---|
| `econfin-idea-finder` | `F:\Dropbox\CC\选题大全\<方向>\` | `01_proposal/candidates/`（工作区内） |
| `journal-digest` | `F:\OneDrive\研究发展部\期刊速递\`（期刊摘要落盘） | `01_proposal/journal_digest.md`（工作区内） |

调用模板见 [`subagent-templates.md`](subagent-templates.md) 的「Stage 1 选题漏斗」一节——其中已把
`OUTPUT_DIR` / `WORK_DIR` 覆盖为工作区子目录。**其余子 skill 默认接受外部传入的目标路径**，按各阶段
playbook 指定的工作区子目录落盘即可。

---

## A. 按阶段的主线路由（默认用这些）

| Stage | 任务 | 默认 skill | 关键增强 / 替代 |
|---|---|---|---|
| 1 | 选题漏斗 | **`67/econfin-idea-finder`** | `25-HosungYou-Diverga`、`61-phdemotions-research-methods` |
| 1 | 写计划书 | **`67/econfin-proposal`** | `14-luischanci-claude-code-research-starter` |
| 1 | 查新 / 重复性 | **`67/novelty-check`** | `59-shiquda-openalex-skill`、`62-PHY041-claude-skill-citation-checker` |
| 1 | 重要性 / 贡献论证 | **`67/significance-search`** | `11-James-Traina-compound-science` |
| 1 | 目标期刊口味扫描 | **`67/journal-digest`** | `09-meleantonio-awesome-econ-ai-stuff` |
| 2 | 取数 | **`67/data-fetcher`** | `57-dgunning-edgartools`(SEC/EDGAR)、`58-charlescoverdale-econstack`、`mcp__fred-mcp-server`、FRED/WRDS |
| 2 | 清洗 | **`67/data-cleaning`** | `66/codebook-pass` |
| 3 | DiD | **`67/did-analysis`** | `10-Jill0099-causal-inference-mixtape`、`13-scunning1975-MixtapeTools`、StatsPAI `auto_did`/`callaway_santanna`/`sun_abraham`、methods pack 的交错 DiD 证据包 |
| 3 | IV/2SLS | **`67/iv-estimation`** | StatsPAI `auto_iv`/`ivreg`/`anderson_rubin_ci` |
| 3 | RDD | **`67/rdd-analysis`** | StatsPAI `rdrobust`/`rdbwselect`/`rddensity`、`rdrobust` 官方包 |
| 3 | 合成控制 | **`67/synthetic-control`** | `51-pymc-labs-CausalPy`、StatsPAI `synth`/`sdid`/`scpi`、Synthetic DiD |
| 3 | 面板 | **`67/panel-data`** | `40-py-econometrics-pyfixest`、StatsPAI `feols`/`hdfe_ols`、PyFixest/fixest route |
| 3 | OLS / 基础 | **`67/ols-regression`** | `20-wenddymacro-python-econ-skill` |
| 3 | 时间序列 | **`67/time-series`** | StatsPAI `var`/`irf`/`arima`/`johansen` |
| 3 | ML 因果 / 异质效应 | **`67/ml-causal`** | `51-pymc-labs-CausalPy`、StatsPAI `causal_forest`/`dml`、DoubleML、EconML、GRF、DoWhy refuters |
| 3 | 分析后端选择 | **`69-Paper-WorkFlow/references/analysis-backends.md`** | `python-statspai`（StatsPAI MCP/包）、`Full-empirical-analysis-skill-Stata`（`skills/00.2-.../SKILL.md`）、`Full-empirical-analysis-skill-R`（`skills/00.3-.../SKILL.md`） |
| 3 | Stata 执行 | **`Full-empirical-analysis-skill-Stata`** | `67/stata`、`64-tmonk-mcp-stata`、`32-dylantmoore-stata-skill`、`18-jusi-aalto-stata-accounting-research`、`mcp__stata-code`/`mcp__stata-mcp` |
| 3 | R 执行 | **`Full-empirical-analysis-skill-R`** | `55-ab604-claude-code-r-skills`、`66/R-optimizer`、R `fixest`/`did`/`grf`/`DoubleML` |
| 3 | 通用统计 | **`67/stats`** | `00-Full-empirical-analysis-skill_*`（StatsPAI/Python/Stata/R 变体） |
| 4 | 回归表（三格式：LaTeX/Word/Excel 同出） | **按后端出表**：StatsPAI `regtable`/`paper_tables`/`collect`；Stata `esttab`/`outreg2`/`collect`；R `modelsummary`/`etable`/Quarto（见 [`analysis-backends.md`](analysis-backends.md)） | **`67/table`**（LaTeX 三线）、`66/latex-table` |
| 4 | 图 | **按后端出图**：StatsPAI plotters；Stata `graph export`；R `ggsave`（均需 PDF+PNG） | **`67/figure`**、`39-vincentarelbundock-marginaleffects`、`55-ab604-claude-code-r-skills` |
| 5 | 从表图写论文 | **`67/paper-writer`** | `01-lishix520-academic-paper-skills`、`04-K-Dense-AI-claude-scientific-writer`、`35-bahayonghang-academic-writing-skills` |
| 5 | 文献综述 | `36-taoyunudt-literature-review-skill` | `52-keemanxp-slr-prisma`、`53-keemanxp-thematic-analysis-skill`、`59-shiquda-openalex-skill` |
| 6 | 打磨流水线（编排级） | **`67/paper-pipeline`** | 其内部串：`paper-polish`/`paper-self-revise`/`paper-style`/`reference-verify` |
| 6 | 单步：校对 | `67/paper-polish` | `38-peternka-academic-proofreader` |
| 6 | 单步：自评修订 | `67/paper-self-revise` | — |
| 6 | 单步：期刊风格 | `67/paper-style` | — |
| 6 | 单步：引用核验 | `67/reference-verify` | `62-PHY041-claude-skill-citation-checker`、`66/citation-fidelity`、Zotero MCP `scite_check_retractions` |
| 7 | 英文可读性 | **`67/readability`** | `56-hanlulong-econ-writing-skill` |
| 7 | 英文去 AI 套话 | `44-matsuikentaro1-humanizer_academic` | `45-stephenturner-skill-deslop`、`46-hardikpandya-stop-slop`、`47-conorbronsdon-avoid-ai-writing` |
| 7 | 中文去翻译腔/混排 | **`67/fix-chinese`** + `67/chinese-quote-converter` | `48-copaper-ai-chinese-de-aigc`、`49-voidborne-d-humanize-chinese` |
| 8 | 模拟审稿 | **`67/referee-report`** | `66/grillme`、`66/econ-reviewer`、`66/did-reviewer`、`21-claesbackman-AI-research-feedback` |
| 8 | 按审稿意见修订 | **`67/paper-referee-revise`** | `67/paper-self-revise`（内部自评时） |
| 8 | 计量自检 | `41-sticerd-eee-sewage-econometrics-check` | StatsPAI `audit_result`/`sensitivity_from_result`、`03_analysis/method_gate.md` 复审 |
| 9 | 选刊 / 投稿评估 | **`67/paper-submission`** | `60-regisely-superpapers`、AEA replication/data-code policy pack |
| 9 | 硕士论文评阅（学位场景） | `67/master-thesis-review` | `66-zheng-siyao-empirical-research-skills`(整套) |
| — | 转 Word / 格式转换 | `67/md-to-docx`、`67/markitdown` | `08-ndpvt-web-latex-document-skill` |
| — | 做汇报 PPT | `67/marp-slides-creator`+`67/marp-export`、`67/chinese-ppt` | 演示物料见本仓库根目录 |

---

## B. 横切能力（任何阶段都可能用）

| 能力 | skill / 工具 |
|---|---|
| 联网搜索 / 抓取 / 登录后操作 | **`67/web-access`**（中文站点首选）、`67/web-research`、`67/agent-browser`、`WebSearch`/`WebFetch` |
| arXiv / NBER / 预印本 | `67/arxiv`、`68-research-productivity-skills/nber-working-papers-api`、`68/.../academic-paper-search`、`68/.../unpaywall-api` |
| 文献库管理 / 引用入库 | Zotero MCP（`zotero_*`、`scite_*`）、`59-shiquda-openalex-skill` |
| **Stage 3–4 分析后端** | [`analysis-backends.md`](analysis-backends.md)：Python/StatsPAI、Stata、R 三种后端的选择规则、子 skill 路径、输出合同、环境记录、fallback |
| **默认估计 + 出表引擎** | **StatsPAI**：[`statspai-analysis.md`](statspai-analysis.md)——MCP 优先（`detect_design → preflight → recommend → fit(as_handle) → audit_result → *_from_result → bibtex`），`statspai` 包做出版级三格式表图与 8 段 paper bundle；含三种领域模式、估计量路由、七块稳健性闸门、反模式清单 |
| 方法增强包 | `69-Paper-WorkFlow/references/research-grade-methods.md`：design register、method gate、最低证据包 |
| 识别威胁 / 审稿异议预案 | `69-Paper-WorkFlow/references/threats-to-validity.md`：威胁×诊断×预防×回应对照表（坏控制、预趋势功效、弱工具…，Stage 3/5/8） |
| 设计透明度 / 预分析 | `69-Paper-WorkFlow/references/design-transparency.md`：PAP/预注册、功效与 MDE、预趋势功效 + HonestDiD、设定曲线、研究者自由度披露（Stage 3） |
| 文献检索与贡献定位 | `69-Paper-WorkFlow/references/literature-and-positioning.md`：滚雪球 + 引用图工具、文献矩阵、定位句式、引用真实性（Stage 1/5） |
| 数据治理 / IRB / DUA | `69-Paper-WorkFlow/references/data-governance.md`：public/restricted/confidential/PII 分级、DAS、IRB/DUA、公开复现包边界（Stage 2/9/收尾） |
| 运行时退化路径 | `69-Paper-WorkFlow/references/runtime-fallbacks.md`：Skill/Agent/网络/MCP/Stata/R/Python/Zotero 缺失时的 fallback、日志与质量封顶 |
| 关键 artifact 模板 | `69-Paper-WorkFlow/templates/`：design register、method gate、quality scorecard、data governance、DAS、REPLICATION、submission checklist、FINAL_REPORT、run_all |
| 端到端示例 trace | `69-Paper-WorkFlow/references/worked-example.md`：黄金路径逐阶段产物 + 两道闸门触发 + 回退循环（编排器填空范本） |
| Stata MCP 执行 | `mcp__stata-code`（结构化输出优先）、`mcp__stata-mcp`（do-file 执行）|
| 宏观数据 MCP | `mcp__fred-mcp-server`（`fred_search`/`fred_get_series`） |
| 笔记 / 知识库 | Obsidian MCP（`create-note`/`search-vault`） |
| 新建 / 改 skill | `67/skill-creator`、`67/command-development` |

---

## B.1 外部方法 route（可用则调用，不可用则复刻最低证据包）

| route | 来源 / 软件 | workflow 用法 |
|---|---|---|
| modern-did | Callaway-Sant'Anna、Sun-Abraham、StatsPAI `auto_did` | 交错处理或动态事件研究时替代 naive TWFE；输出 group-time ATT 与事件研究诊断 |
| rdd-diagnostics | `rdrobust` / StatsPAI `rdrobust` | RDD 分支的 bandwidth、RBC CI、density/covariate continuity、donut/placebo cutoff |
| sdid-synth | Synthetic DiD / CausalPy / StatsPAI `sdid` | donor pool 与长前期场景；输出 weights、pre-fit RMSPE、placebo、leave-one-out |
| hdfed-regression | PyFixest / fixest / StatsPAI `feols` | 高维固定效应、IV/Poisson、聚类稳健与小 cluster 推断 |
| doubleml-runner | DoubleML / EconML / StatsPAI `dml` | 高维 controls 的 orthogonal score、cross-fitting、nuisance diagnostics |
| hte-forest | GRF / EconML causal forest | HTE/CATE、honesty split、ATE 校准、heterogeneity test、policy subgroup stability |
| dag-refuter | DoWhy / PyWhy | DAG/estimand/refuter：placebo treatment、random common cause、subset/refit |
| replication-pack | SSDE README / AEA Data Editor guidance / `aer-replication` 类 skill | Stage 2 起记录 data provenance 和 data governance，收尾生成 `REPLICATION.md`、DAS、master script，并更新 `replication_pack` |

不要把这些 route 当成“必装依赖”。它们是方法标准与实现入口：本机有包/MCP 就调，没有就用已有 Stata/R/Python
脚本实现同等 artifact；实现不了就让 `method_gate.md` 明确 `NOT PASS`。

---

## C. 选择原则（避免选择困难）

1. **先 67 主线，后其它增强**。`67/` 的 skill 彼此约定一致（文件名、表格规范、状态文件），混用
   其它集合时注意它们各自的输入/输出约定，必要时在 subagent 内做适配，别污染主线产物。
2. **方法路由决策树**（Stage 3）：
   - 有明确政策/事件时点 + 处理/对照可分 → **DiD**（交错处理→CS/SA/BJS）。
   - 有外生工具、X 内生 → **IV**。
   - 有连续 running variable + 断点规则 → **RDD**。
   - 单一处理单位 + 多对照 + 长前期 → **合成控制 / SDID**。
   - 多期面板、关注 FE → **panel-data**。
   - 纯时序 / 宏观 → **time-series**。
   - 关注异质效应 / 高维控制 → **ml-causal（因果森林 / DML）**。
   - 都不典型 → 退回 `67/stats` 做探索，或回 Stage 1 重审识别。
   选定主设计后，立即加载 `references/design-gate-cards.md` 的对应卡片，把 required artifacts、
   hard fail 与最强允许 claim 写进 `method_gate.md` 和 `evidence_ledger.md`。
3. **分析后端分流**（Stage 3–4）：默认 `python-statspai`；用户要 `.do` / `reghdfe` / `esttab` / Stata
   replication 就走 `Full-empirical-analysis-skill-Stata`；用户要 `fixest` / `modelsummary` / Quarto / `renv`
   就走 `Full-empirical-analysis-skill-R`。后端只改变实现，不降低 Method Gate。
4. **稿件语言分流**（Stage 7）：英文走 `readability` + 44/45/46/47；中文走 `fix-chinese` +
   `chinese-quote-converter` + 48/49。
5. **能用 MCP 验证就别凭记忆**：引用真实性、计量稳健性、宏观数据都有对应 MCP/skill 兜底。
6. **方法闸门优先于写作推进**：Stage 3 的 `method_gate.md` 没过，或 `evidence_ledger.md` 不允许该
   claim 强度，Stage 4–7 不应继续把结果包装成主发现；先回退补证据或降级因果 claim。

---

## D. 不纳入主线的（避免误用）

- 本仓库刻意不含 Anthropic 专有 office skills（docx/pdf/pptx/xlsx）与通用 UI skills
  （frontend-design / ui-ux-pro-max）——需要时从授权源安装，别复制进仓库（见 `67/README.md` 许可注记）。
- `65-game-theory-paper-writer`、HyperFrames/Remotion/前端类 skill 与实证论文流程无关，默认不接入。
