# Skill Map — 「任务 → 用哪个 skill」全量路由表

> 本编排器的"零件库"。**主线（粗体）几乎全部来自 `67-econfin-workflow-toolkit/`**，因为它是
> 唯一一套为实证论文全流程设计、彼此可组合的 skill 集；其余 68 个集合按需作为**增强 / 替代 /
> 专项**接入。路径 `67/x` = `skills/67-econfin-workflow-toolkit/x/SKILL.md`。
>
> 调用一个 skill = 用 `Skill` 工具加载它、按它自己的工作流跑到完成。能调用就不要重写。

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
| 3 | DiD | **`67/did-analysis`** | `10-Jill0099-causal-inference-mixtape`、`13-scunning1975-MixtapeTools`、StatsPAI `auto_did`/`callaway_santanna`/`sun_abraham` |
| 3 | IV/2SLS | **`67/iv-estimation`** | StatsPAI `auto_iv`/`ivreg`/`anderson_rubin_ci` |
| 3 | RDD | **`67/rdd-analysis`** | StatsPAI `rdrobust`/`rdbwselect`/`rddensity` |
| 3 | 合成控制 | **`67/synthetic-control`** | `51-pymc-labs-CausalPy`、StatsPAI `synth`/`sdid`/`scpi` |
| 3 | 面板 | **`67/panel-data`** | `40-py-econometrics-pyfixest`、StatsPAI `feols`/`hdfe_ols` |
| 3 | OLS / 基础 | **`67/ols-regression`** | `20-wenddymacro-python-econ-skill` |
| 3 | 时间序列 | **`67/time-series`** | StatsPAI `var`/`irf`/`arima`/`johansen` |
| 3 | ML 因果 / 异质效应 | **`67/ml-causal`** | `51-pymc-labs-CausalPy`、StatsPAI `causal_forest`/`dml` |
| 3 | Stata 执行 | **`67/stata`** | `64-tmonk-mcp-stata`、`32-dylantmoore-stata-skill`、`18-jusi-aalto-stata-accounting-research`、`mcp__stata-code`/`mcp__stata-mcp` |
| 3 | 通用统计 | **`67/stats`** | `00-Full-empirical-analysis-skill_*`（StatsPAI/Python/Stata/R 四语言变体） |
| 4 | 回归表（LaTeX 三线） | **`67/table`** | `66/latex-table` |
| 4 | 图 | **`67/figure`** | `39-vincentarelbundock-marginaleffects`、`55-ab604-claude-code-r-skills` |
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
| 8 | 计量自检 | `41-sticerd-eee-sewage-econometrics-check` | StatsPAI `audit_result`/`sensitivity_from_result` |
| 9 | 选刊 / 投稿评估 | **`67/paper-submission`** | `60-regisely-superpapers` |
| 9 | 硕士论文评阅（学位场景） | `67/master-thesis-review` | `66-zheng-siyao-empirical-research-skills`(整套) |
| — | 转 Word / 格式转换 | `67/md-to-docx`、`67/markitdown` | `08-ndpvt-web-latex-document-skill` |
| — | 做汇报 PPT | `67/marp-slides-creator`+`67/marp-export`、`67/chinese-ppt` | 演示物料见 `../Paper-WorkFlow/` |

---

## B. 横切能力（任何阶段都可能用）

| 能力 | skill / 工具 |
|---|---|
| 联网搜索 / 抓取 / 登录后操作 | **`67/web-access`**（中文站点首选）、`67/web-research`、`67/agent-browser`、`WebSearch`/`WebFetch` |
| arXiv / NBER / 预印本 | `67/arxiv`、`68-research-productivity-skills/nber-working-papers-api`、`68/.../academic-paper-search`、`68/.../unpaywall-api` |
| 文献库管理 / 引用入库 | Zotero MCP（`zotero_*`、`scite_*`）、`59-shiquda-openalex-skill` |
| 因果推断 MCP（agent-native） | **StatsPAI MCP**：`detect_design → preflight → recommend → fit(as_handle) → audit_result → *_from_result → bibtex` |
| Stata MCP 执行 | `mcp__stata-code`（结构化输出优先）、`mcp__stata-mcp`（do-file 执行）|
| 宏观数据 MCP | `mcp__fred-mcp-server`（`fred_search`/`fred_get_series`） |
| 笔记 / 知识库 | Obsidian MCP（`create-note`/`search-vault`） |
| 多代理执行范式 | **`67/do-agent`** / `68/.../do-agent`（本编排器的设计母本） |
| 新建 / 改 skill | `67/skill-creator`、`67/command-development` |

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
3. **语言分流**（Stage 7）：英文走 `readability` + 44/45/46/47；中文走 `fix-chinese` +
   `chinese-quote-converter` + 48/49。
4. **能用 MCP 验证就别凭记忆**：引用真实性、计量稳健性、宏观数据都有对应 MCP/skill 兜底。

---

## D. 不纳入主线的（避免误用）

- 本仓库刻意不含 Anthropic 专有 office skills（docx/pdf/pptx/xlsx）与通用 UI skills
  （frontend-design / ui-ux-pro-max）——需要时从授权源安装，别复制进仓库（见 `67/README.md` 许可注记）。
- `65-game-theory-paper-writer`、HyperFrames/Remotion/前端类 skill 与实证论文流程无关，默认不接入。
