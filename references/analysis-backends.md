# Analysis Backends — Python / Stata / R 路由契约

> Stage 0 选择分析后端，Stage 3–4 执行估计和出表时加载本文件。这里的 "backend" 指分析代码生态，
> 不是 `project.language` 的中英文稿件语言。三种后端共享同一套 research contract、Method Gate、
> Evidence Ledger 和 replication package，只改变脚本语言、估计包和出表工具。

---

## 1. 三种后端

| Backend value | 适合场景 | 子 skill / route | 主要脚本 | 出表出图 |
|---|---|---|---|---|
| `python-statspai` | 默认；需要 MCP 拍板、agent-native 诊断、Python/StatsPAI 三格式 bundle | StatsPAI MCP / `statspai` 包；显式 Python 可读 `skills/00.1-Full-empirical-analysis-skill/SKILL.md` | `03_analysis/*.py` | `statspai` result objects → `.tex/.docx/.xlsx`，plots → `.pdf/.png` |
| `stata` | coauthor、reviewer 或 replication office 要 `.do`；研究组已有 Stata pipeline | `Skill("Full-empirical-analysis-skill-Stata")`；not found 则 `Read skills/00.2-Full-empirical-analysis-skill_Stata/SKILL.md` | `03_analysis/*.do` + `.log` | `esttab`/`outreg2`/`collect`，figures `graph export` |
| `r` | 需要 tidyverse/fixest、Quarto/R Markdown、R-native causal packages 或 `renv` 锁环境 | `Skill("Full-empirical-analysis-skill-R")`；not found 则 `Read skills/00.3-Full-empirical-analysis-skill_R/SKILL.md` | `03_analysis/*.R` / `.qmd` | `modelsummary`/`fixest::etable`/Quarto，figures `ggsave` |

`python-statspai` 是保守默认。若用户明确说 "用 Stata"、"do-file"、"reghdfe"、"esttab"、"给审稿人 Stata
复现" 就选 `stata`。若用户明确说 "用 R"、"fixest"、"modelsummary"、"Quarto"、"renv"、"grf"、
"DoubleML R" 就选 `r`。

---

## 2. Stage 0 写入契约

Setup 的一次性询问除交互档位、目标期刊、稿件语言外，还要确定分析后端：

- `python-statspai`（推荐默认）
- `stata`
- `r`

如果用户要求全自动或已能从输入推断，不要阻断开跑。按下列优先级自动填：

1. 用户明确指定的后端。
2. 工作区已有主脚本：`.do` → `stata`，`.R`/`.qmd` → `r`，`.py`/StatsPAI handle → `python-statspai`。
3. 目标受众明确要求 Stata/R 复现时按受众选择。
4. 否则选 `python-statspai`。

写入三处：

- `00_meta/workflow_state.json.analysis_backend`：
  - `primary`: `python-statspai` / `stata` / `r`
  - `secondary_validation`: `none` 或另一个后端
  - `script_extension`: `.py` / `.do` / `.R`
  - `child_skill`: 使用的 registered skill 或 `Read` 回退路径
  - `environment_status`: `pending` / `available` / `fallback` / `blocked`
  - `version_report`: `00_meta/analysis_backend.md`
- `00_meta/analysis_backend.md`：记录选择理由、版本检查、包缺失和 fallback。
- `03_analysis/design_register.md` 的 Software route：写明同一识别设计用哪个后端实现。

---

## 3. Stage 3 执行规则

先按 `research-grade-methods.md` 定 estimand、识别假设和最低证据包，再选软件。软件不能倒推设计。

### `python-statspai`

- 默认走 StatsPAI MCP：`detect_design → preflight → recommend → fit(as_handle=true) → audit_result →
  *_from_result → bibtex`。
- 需要三格式表图或 8 段 bundle 时切 `statspai` 包。
- 所有脚本留在 `03_analysis/*.py`，将 `result_id`、包版本、seed、聚类口径写入脚本头或
  `method_gate.md`。

### `stata`

- 加载 `Full-empirical-analysis-skill-Stata`，用其 8-step Stata pipeline：sample log、data contract、
  `strategy.do`、`reghdfe`/`ivreg2`/`csdid`/`rdrobust`/`synth`、robustness、`esttab`/`outreg2`。
- 主脚本建议命名为 `03_analysis/master.do` 或 `03_analysis/estimate.do`，同时保存 `.log`。
- 必须导出一个后端无关的 `03_analysis/results/main_results.json`，包含 effect、SE/CI、N、FE、cluster、
  estimator、package versions。不要只留下 Stata Results 窗口输出。
- Stata 图必须同时 `graph export` 为 `.pdf` 和 `.png`，PNG 至少 300 dpi 或等价像素。

### `r`

- 加载 `Full-empirical-analysis-skill-R`，用其 8-step R pipeline：sample log、data contract、`strategy.md`、
  `fixest::feols`/`AER::ivreg`/`did::att_gt`/`rdrobust`/`synthdid`/`grf`/`DoubleML`、robustness、
  `modelsummary`/Quarto。
- 主脚本建议命名为 `03_analysis/master.R`、`03_analysis/estimate.R` 或 `03_analysis/master.qmd`。
- 使用 `renv` 或版本清单锁包；如果暂不启用 `renv`，在 `00_meta/analysis_backend.md` 和
  `REPLICATION.md` 写 `sessionInfo()` 摘要。
- 必须导出后端无关的 `03_analysis/results/main_results.json`，不要只留下 R 控制台输出。

---

## 4. Stage 4 出表出图规则

三种后端都必须满足相同输出合同：

- 表：`04_results/*.{tex,docx,xlsx}`，至少 Table 1、主结果表、稳健性表。
- 图：`04_results/*.{pdf,png}`，PNG ≥300 dpi。
- 索引：`04_results/exhibits_index.md`，列出每张表/图支持哪个 claim。
- Evidence Ledger：`00_meta/evidence_ledger.md` 的 Exhibit and Script Map 必须指向生成脚本。

后端差异：

- Python/StatsPAI：用 result objects 的 `.to_latex()` / `.to_word()` / `.to_excel()` 与 StatsPAI plotters。
- Stata：`.tex/.rtf` 用 `esttab`；`.xlsx/.docx` 用 `outreg2` 或 Stata 17+ `collect`；图用 `graph export`。
- R：优先 `modelsummary` / `fixest::etable` / Quarto；图用 `ggsave(..., dpi=300)`。

不得因为选了 Stata 或 R 就降低 Method Gate 或 Draft Quality Gate 标准。后端只改变实现，不改变证据门槛。

---

## 5. 交叉验证与 fallback

默认不要求三种后端都跑一遍；主后端跑通并产出同等 artifact 即可。以下情况建议设置
`secondary_validation`：

- 主结果争议大，或审稿人可能质疑实现口径。
- Stata/R/Python 之间已有可比脚本。
- MCP/包路径是 fallback，不是用户指定主路径。

交叉验证只比较核心对象：effect、SE/CI、N、样本限制、FE/cluster、关键诊断。若两后端数字不一致，
先停下查样本和聚类口径，不要让不同后端各自进入写作。

如果所选后端不可用，按 `runtime-fallbacks.md`：

1. 记录缺失工具、尝试命令、fallback 后端和受影响 artifact。
2. 用另一个后端复刻同等最低证据包。
3. 若无法复刻，`method_gate.md` 标 `NOT PASS`，主 claim 降级或回 Stage 1/2/3。
