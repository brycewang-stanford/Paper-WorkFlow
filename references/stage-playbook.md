# Stage Playbook — 逐阶段操作手册

> 主代理在**进入某阶段时**才读对应章节（渐进式加载，省上下文）。每一阶段都按 SKILL.md 的
> 「阶段执行协议」跑：**横幅 → in_progress → plan → execute → review → revise → 快照 → done →
> 阶段闸门**。本手册给出每阶段「调哪个 skill / 派哪种 subagent / 产出什么 / 失败怎么回退」。
>
> 所有路径里的 `67/` = `skills/67-econfin-workflow-toolkit/`。**调用某 skill 一律按
> [`skill-map.md`](skill-map.md) §0 的调用协议**：优先 `Skill(<注册名>)`，报 not found 就退回
> `Read <folder>/SKILL.md` 内联执行，绝不凭记忆脑补。可直接复制的 subagent 派发模板见
> [`subagent-templates.md`](subagent-templates.md)。进入 Stage 3 前还必须加载
> [`research-grade-methods.md`](research-grade-methods.md)，用它定义现代因果推断/应用计量的最低证据包。
> Stage 2 结束、Stage 3 开始前还要加载 [`empirical-audit.md`](empirical-audit.md)，确保样本构造、
> 变量口径、missingness/balance/overlap 与目标 estimand 对齐。
> Stage 3–4 的 Python/StatsPAI、Stata、R 三种分析后端按
> [`analysis-backends.md`](analysis-backends.md) 选择；默认后端为 `python-statspai`。
> 每个因果设计还必须加载 [`design-gate-cards.md`](design-gate-cards.md)，把设计分支的 required artifacts、
> hard fail 与 claim 降级规则写进 `method_gate.md` 和 `evidence_ledger.md`。
> **想先看一条完整跑通的 trace**（每阶段产物 + 两道闸门如何触发 + NOT PASS→回退→PASS 循环），见
> [`worked-example.md`](worked-example.md)——它就是下面这套协议的填空范本。
> 工具、网络、MCP 或统计软件不可用时按 [`runtime-fallbacks.md`](runtime-fallbacks.md) 退化执行；
> 涉及受限数据、PII、IRB/DUA 或 archive boundary 时按 [`data-governance.md`](data-governance.md) 先登记再推进。
> 识别威胁、选择性报告、external validity、SUTVA/溢出和 attrition 风险按
> [`design-risk-ledger.md`](design-risk-ledger.md) 写入 `03_analysis/design_risk_ledger.md`，作为 Method Gate 的上游硬约束。

---

## Stage 1 · 选题与设计

**目的**：把一个研究方向收敛成一份可直接进入实证的 proposal（X→M→Y、识别策略、样本、贡献边际、
目标期刊）。

**plan**
- 若用户已给方向，直接用；否则 `AskUserQuestion` 问方向 + 想要的候选标题数 N（缺省 5）。
- 读 `67/econfin-idea-finder/SKILL.md`，按其漏斗逻辑运行。
- 加载 [`literature-and-positioning.md`](literature-and-positioning.md)：用滚雪球 + 引用图工具把相关文献
  找全，建 `01_proposal/lit_matrix.md` 让贡献白space可见；贡献句按 [`writing-craft.md`](writing-craft.md)
  §3 三槽 + 该文件 §4 定位句式锻造，命中 Edmans 红线就回炉。

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
- 若已经能判断识别路线，顺手写一版 `03_analysis/design_register.md` 草稿；Stage 3 开始时再按
  [`research-grade-methods.md`](research-grade-methods.md) 补齐 estimand、诊断证据与回退方案。
- 同时从 [`templates/design_risk_ledger.md`](../templates/design_risk_ledger.md) 起草
  `03_analysis/design_risk_ledger.md`：至少列出 proposal 可能命中的 OVB、选择、bad controls、spillover/SUTVA、
  external validity、attrition 和 specification-search 风险。此时可为 `pending`，但不能空白。

**失败回退**：N 个候选全 < 9 分 → 扩大方向或换角度重跑一轮；查新发现已被做过 → 标红，回到 plan
另寻差异化切口。

---

## Stage 2 · 数据

**目的**：依 proposal 的变量与样本，拿到**分析就绪**的数据集 + codebook。

**plan**：从 `proposal.md` 抽出需要的变量、频率、地域、时间窗、合并键，列一张「变量→数据源」需求表。
加载 [`data-governance.md`](data-governance.md) 与 [`empirical-audit.md`](empirical-audit.md)，先从
`templates/data_governance.md` 生成 `00_meta/data_governance.md`，从 `templates/sample_audit.md` 生成
`02_data/sample_audit.md`。前者记录 public / restricted / confidential / PII、DUA、IRB/ethics、许可证、
再分发边界；后者预留 raw→clean→estimation sample 的 N、单位数、treated/control 数、drop 原因和脚本行号。

**execute**
- `Skill` 调用 `67/data-fetcher` 取数（FRED / World Bank / BLS / OECD / Yahoo Finance；A 股/中国
  宏观等可配合 `57-dgunning-edgartools`、`58-charlescoverdale-econstack`、`59-shiquda-openalex-skill`
  等集合，见 skill-map）。多个独立数据源可并行 subagent 各取一段、各自写盘到 `02_data/raw/`。
- `Skill` 调用 `67/data-cleaning` 做清洗、对齐、合并、构造变量，产出 `02_data/clean.parquet`
  （或 `.dta/.csv`）与 `02_data/codebook.md`（每个变量的定义、来源、单位、缺失处理）。
- 同步填写 `02_data/sample_audit.md`：合并键唯一性、样本限制、缺失/attrition、baseline balance、
  overlap/common support、treatment timing、cluster level/cluster count 与权重口径必须落到表格或图。
- 受限数据只保留 fetch/clean 脚本、变量字典和访问说明；不得把原始数据、PII、token、签名 URL 或
  DUA/IRB 限制材料放进公开包、日志或仓库。

**review**：critic subagent 核对——合并键唯一性、面板是否平衡、极端值/缺失处理是否记录在 codebook、
处理与对照如何界定（若是 DiD/SC）、`sample_audit.md` 的样本流失/estimand 对齐/missingness-balance/overlap
是否足以支撑下一阶段、数据治理登记是否与 codebook/DAS 原料一致。意见写 `02_data/data_audit.md`，
并更新 `workflow_state.json.empirical_audit`。

**revise / 交付**：据审计修清洗脚本，重跑到干净。**清洗脚本必须留在 `02_data/`**，保证可复现。
`sample_audit.md` 若为 `NOT PASS`，Stage 3 只能做探索或修数据，不能把 Method Gate 标 `PASS`。

**失败回退**：关键数据取不到 → 标红，给替代代理变量方案或缩小样本，必要时回 Stage 1 调整设计。

---

## Stage 3 · 计量识别、估计与方法闸门

**目的**：按 proposal 的识别策略，先注册设计，再跑出基准 + 机制 + 异质性 + 稳健性的**真实**结果，
最后用方法闸门确认最低证据包齐全。

**plan（先定设计，再定方法）**
- 必读 [`research-grade-methods.md`](research-grade-methods.md) + [`design-gate-cards.md`](design-gate-cards.md) +
  [`empirical-audit.md`](empirical-audit.md) + [`inference-and-uncertainty.md`](inference-and-uncertainty.md)（推断口径）+
  [`mechanism-and-channels.md`](mechanism-and-channels.md)（机制主张分类）+
  [`design-risk-ledger.md`](design-risk-ledger.md)（设计风险总账）+ [`analysis-backends.md`](analysis-backends.md)。先用 empirical audit 确认 estimation sample、变量构造、
  missingness/balance/overlap 与 estimand 对齐，再用 methods pack 定识别合同，最后用 backend 文件选择
  `python-statspai` / `stata` / `r`；若选
  `python-statspai` 或需要 StatsPAI 交叉验证，再读 [`statspai-analysis.md`](statspai-analysis.md)。StatsPAI 引擎（MCP 优先拍板/拟合/诊断，
  `statspai` 包做出版级出表）的 §1 8 段映射、§3 估计量路由、§6 七块稳健性闸门是本阶段的操作主线。
  把 proposal 的识别路线翻译成 `03_analysis/design_register.md`：
  estimand、treatment、comparison group、识别假设、主估计量、必需诊断、替代估计量、失败回退。
  同时确定本研究使用哪张 design gate card，并在 `design_register.md` 写清最强目标 claim、样本/时窗/处理版本
  边界，以及触发降级的条件。
  立刻刷新 `03_analysis/design_risk_ledger.md`：把 threats-to-validity 命中的威胁、design-transparency 的
  PAP/MDE/设定曲线/研究者自由度要求、external validity/transport 边界、spillover/SUTVA 和 attrition 风险逐项
  标为 `pending` / `pass` / `not_pass` / `not_applicable`，并写明每项的 claim consequence。
- **分析后端分流**（analysis-backends）：默认 `workflow_state.json.analysis_backend.primary=python-statspai`。
  用户或既有脚本指定 Stata 时加载 `Full-empirical-analysis-skill-Stata`（not found 则
  `Read skills/00.2-Full-empirical-analysis-skill_Stata/SKILL.md`）并产出 `.do` + `.log`；指定 R 时加载
  `Full-empirical-analysis-skill-R`（not found 则
  `Read skills/00.3-Full-empirical-analysis-skill_R/SKILL.md`）并产出 `.R` / `.qmd`。三种后端都必须生成
  后端无关的 `03_analysis/results/main_results.json`、`summary.md`、`method_gate.md` 和复现脚本。
- **领域模式分流**（statspai-analysis §2）：默认应用计量；用户措辞含 target trial / IPTW / TMLE / 孟德尔
  随机化 → Mode A（流行病学，报风险差/比/HR/RMST + E-value）；含 causal forest / DML / CATE / policy →
  Mode B（ML 因果，CATE 分布 + policy value + conformal）。
- 同时加载 [`threats-to-validity.md`](threats-to-validity.md)（把稳健性矩阵设计成「针对每个识别威胁的
  回应」，并按 §3 给控制集标注前处理/混淆/中介/对撞、剔除坏控制）与
  [`design-transparency.md`](design-transparency.md)（估计前写预分析计划锁定设计；空结果报 MDE；DiD 跑
  预趋势功效 + HonestDiD、设定曲线，登记随机种子）。
  这些透明度和识别威胁不是散文备注：适用项必须同步进入 `design_risk_ledger.md` 的 Threat Register。
- 若估计工具、StatsPAI MCP、Stata/R/Python 包或网络不可用，按
  [`runtime-fallbacks.md`](runtime-fallbacks.md) 选择等价 route；若无法生成最低证据包，`method_gate.md`
  必须 `NOT PASS`，不得把 fallback 当作完整验证。
- 从 `proposal.md` 读识别策略，按下表择一主 skill（决策树细节见 skill-map 的「方法路由」）：

  | 设计 | 主 skill（`67/`） | 配套 |
  |---|---|---|
  | 政策评估 / 自然实验 / 双重差分 | `did-analysis` | 平行趋势、事件研究、交错估计量 CS/SA/BJS、TWFE 风险对照 |
  | 内生性 / 工具变量 | `iv-estimation` | 弱工具检验、过度识别 |
  | 断点 | `rdd-analysis` | 带宽、robust bias-corrected CI、操纵/密度检验、协变量连续性 |
  | 单一处理单位 / 政策试点 | `synthetic-control` | donor weights、pre-fit RMSPE、安慰剂、SDID 备选 |
  | 一般面板 | `panel-data` | FE/RE、聚类稳健 SE、wild cluster/bootstrap（小 cluster） |
  | 截面 / 基础回归 | `ols-regression` | 稳健 SE |
  | 时间序列 / 宏观 | `time-series` | 单位根、协整、VAR/IRF |
  | 异质处理效应 / 高维 | `ml-causal` | DML、EconML/DoubleML、因果森林/GRF、overlap 与 cross-fitting |

- **默认主引擎 = StatsPAI（MCP 优先）**：当后端为 `python-statspai` 时走 MCP 链路做 agent-native 拍板 / 拟合 / 诊断 / 稳健性自检，
  全程不落 Python：`detect_design → preflight → recommend → 用 as_handle=true 拟合得 result_id →
  audit_result(result_id) 列出缺的稳健性 → 逐个调它 emit 的 suggest_function →
  honest_did_from_result / sensitivity_from_result → bibtex(keys) 取可信引用`（`paper.bib` 为唯一真源）。
  设计→函数路由见 [`statspai-analysis.md`](statspai-analysis.md) §3。
- **需要出版级三格式表图 / 8 段 paper bundle 时切到 `statspai` 包**（`sp.feols`/`sp.regtable`/`sp.collect`，
  见 statspai-analysis §4–5）：MCP 拍板拟合后用包出表，两条路径的系数 / SE / N / 聚类**必须对得上**，
  对不上先停下查口径。若改用 Stata/R/Python 方法包（Stata `reghdfe`/`ivreg2`/`csdid`/`rdrobust`，R
  `fixest`/`did`/`grf`/`DoubleML`，或 Python DoubleML、EconML、DoWhy、GRF、PyFixest、rdrobust、
  CausalPy），按对应 child skill 和 methods pack §1 的官方入口核对 API；无论走哪条，都把包版本、seed、关键参数（或 MCP 的
  `result_id` 与设计判定）写入估计脚本或 `method_gate.md`。

**execute**
- **按后端跑基准回归**：
  - `python-statspai`：按 statspai-analysis §3，用 MCP `fit(as_handle)` 拿 `result_id`，或本机
    `statspai` 包跑 `sp.feols`/`sp.callaway_santanna`/`sp.ivreg`/`sp.rdrobust` 等。
  - `stata`：按 `Full-empirical-analysis-skill-Stata` 跑 `03_analysis/estimate.do` / `master.do`，用
    `reghdfe`、`ivreg2`、`csdid`、`eventstudyinteract`、`sdid`、`rdrobust`、`synth` 等；保存 `.log` 和
    标准化 `main_results.json`。
  - `r`：按 `Full-empirical-analysis-skill-R` 跑 `03_analysis/estimate.R` / `master.qmd`，用
    `fixest::feols`、`did::att_gt`、`rdrobust`、`synthdid`、`grf`、`DoubleML` 等；保存 `sessionInfo()` /
    `renv.lock` 信息和标准化 `main_results.json`。
  可按需 `Skill` 调用选定的 `67/` 估计 skill、Stata MCP、PyFixest 或 R route 做交叉验证——但同一主结果
  只认一份口径一致的系数。
- **稳健性矩阵并行化**（套用 [`subagent-templates.md`](subagent-templates.md) §S3）：按 statspai-analysis §6
  的**七块稳健性闸门**（安慰剂 / 替换样本 / 设定曲线 / 替换 SE / Oster 界 / HonestDiD / E-value）+ 机制中介
  把彼此独立的检验一次性派多个 subagent 并行跑，**每个 subagent 自己把系数/SE/图写盘**到
  `03_analysis/robustness/<name>.json|png`，只回传"通过/不通过 + 关键系数"。这七块正是下面 `method_gate.md`
  artifact 表的实现入口，缺一块对应行标 `no`。
- 所有代码留在 `03_analysis/`（`.py`/`.do`/`.R`/`.qmd`），结果存 `03_analysis/results/`，并把后端选择、
  脚本扩展名、版本检查写入 `00_meta/analysis_backend.md` 与 `workflow_state.json.analysis_backend`。
- 同步写 `03_analysis/method_gate.md` 的 artifact 表：主结果、识别诊断、稳健性矩阵、复现脚本都必须
  有路径；`02_data/sample_audit.md` 也必须作为必需 artifact 进入表格，且其 final estimation sample 的 N、
  treated/control 数、cluster level 必须与 `main_results.json` 对上。缺失项标 `no`，不得用空话替代。
  同步写 `03_analysis/inference_report.md`（聚类层级与 cluster 数、few-cluster 修正、随机化推断、多重检验族与
  校正、弱工具区间，见 [`inference-and-uncertainty.md`](inference-and-uncertainty.md)）；有机制主张则按
  [`mechanism-and-channels.md`](mechanism-and-channels.md) 把它分类、把中介移出主设定、结果落 `03_analysis/mechanism/`。
  同步更新 `03_analysis/design_risk_ledger.md`：每个适用 threat 必须指向真实诊断或 refuter artifact；仍未关闭的
  blocking threat 写入 `Blocking Threats`，并同步到 `workflow_state.json.design_risk.blocking_threats`。
  还要按 `design-gate-cards.md` 填写 **Design Gate Card**：列出当前设计卡每个 required artifact 的路径、
  是否通过、以及对应 claim consequence（causal / qualified_causal / descriptive / exploratory / no_claim）。
  方法闸门给出的最强 claim 等级必须同步写入 `workflow_state.json.evidence_governance.claim_strength`。
  方法闸门还要检查 `00_meta/data_governance.md`：合法访问、公开包边界、PII/小样本披露、IRB/DUA 状态若阻断主结果，列入 hard flags。
- 同步刷新 `00_meta/evidence_ledger.md`：为每个主结果写 claim row、estimand-to-claim map、result ID、
  robustness/threat matrix；若任何 claim 强于 design gate card 允许等级，把该行标成 `no_claim` 或降级，并在
  Open Discrepancies 中记录。
  如果 `design_risk_ledger.md` 对某个 claim 的 consequence 更低，以更低者为准。

**review**：派一个 `66-zheng-siyao-empirical-research-skills` 风格的 critic（`did-reviewer` /
`econ-reviewer`）做对抗审阅——识别假设是否真的成立、SE 聚类是否正确、是否 p-hacking 嫌疑、methods
pack 对应的最低证据包是否齐全。意见写 `03_analysis/results_audit.md`，方法闸门判定写
`03_analysis/method_gate.md`；设计风险判定写 `03_analysis/design_risk_ledger.md` 并刷新
`workflow_state.json.design_risk`。若样本审计暴露 estimand 漂移、bad-control、overlap 或聚类层级问题，
先回 Stage 2/3 修数据或设定，不得用更多稳健性表掩盖。

**revise / 交付**：据审阅补检验、修设定，定稿 `03_analysis/results/main_results.json` 与一份
`03_analysis/results/summary.md`（人话版结论）。置 `done` 前跑一次
`python3 scripts/check_workspace_gates.py <workspace>` 机械核对（method_gate 标 PASS 时所需 artifact 必须真的在盘上）。
只有 `method_gate.md` 为 `PASS`、`workflow_state.json.design_risk.status=pass`、且机械核对无 hard 不一致时，Stage 3 才能置
`done` 并进入 Stage 4；否则按 `method_gate.md` 的 Next Action 回退。

**失败回退（关键）**：平行趋势不过 / IV 弱工具 / 系数不显著 / 机制不成立 → **不要硬写成功**。
按 `China-CF-study` 纪律自动切备选：换识别策略、换工具变量、换对照组、改窗口；连续失败则在闸门
标红，回 Stage 1/2 调设计或数据。每次回退都记进 `logs/stage_3.md`。

---

## Stage 4 · 表与图

**目的**：把 Stage 3 的结果按所选分析后端做成**出版级**三格式表（LaTeX/Word/Excel 同出）与图
（事件研究图、系数图、机制图）。

**execute**
- **先读 `workflow_state.json.analysis_backend.primary`**，再按
  [`analysis-backends.md`](analysis-backends.md) §4 选出表路径。所有后端都必须落
  `04_results/*.{tex,docx,xlsx}` 和 `04_results/*.{pdf,png}`，并生成 `04_results/exhibits_index.md`。
  每张表图还必须回填 `00_meta/evidence_ledger.md` 的 Exhibit and Script Map，保证每个 exhibit 都能追溯到
  claim、result、生成脚本和重建状态。
- **`python-statspai` 主路径 = StatsPAI 出表栈**（statspai-analysis §4，用 `statspai` 包）：把 Stage 3 的结果对象喂给
  `sp.regtable(M1..M5, template="aer")`（Tier 1 单表）/ `sp.paper_tables(main=, heterogeneity=, robustness=)`
  （Tier 2 多面板）/ `sp.collect("Title")`（Tier 3 整场 bundle），用 `.to_word()/.to_excel()/.to_latex()`
  **同时**落 `04_results/*.{tex,docx,xlsx}`（合作者改 Word、编辑要 Excel、CI 编 LaTeX）。**永远不要从 pandas
  手搓 Word/Excel**。需纯 LaTeX 三线表时 `Skill` 调用 `67/table`（或 `66/latex-table`）作替代/补充；Stata
  用户可配 `18-jusi-aalto-stata-accounting-research`、`32-dylantmoore-stata-skill` 的表格规范。
- **`stata` 路径**：用 `esttab`/`estout` 输出 `.tex/.rtf`，用 `outreg2` 或 Stata 17+ `collect` 输出
  `.xlsx/.docx`，图用 `graph export` 同时输出 `.pdf` + `.png`。表注必须包含 FE、cluster、N、星标和样本说明。
- **`r` 路径**：用 `modelsummary` / `fixest::etable` / Quarto 输出 `.tex/.docx/.xlsx`，图用
  `ggsave(..., dpi=300)` 同时输出 `.pdf` + `.png`。如果用 Quarto，渲染脚本也留在 `03_analysis/` 或收尾
  master script 中。
- **图：StatsPAI 标准图谱**（statspai-analysis §5）：`sp.enhanced_event_study_plot(cs)`（事件研究，从 CS/SA
  结果出）、`sp.coefplot(...)`（系数森林）、`sp.rdplot`、`sp.cate_plot`、`sp.spec_curve(...).plot()`、
  `sp.sensitivity_plot(sp.honest_did(...))`。每个 plotter 返回 `(fig, ax)`（`binscatter` 是 3 元组），解包后
  `fig.savefig(..., dpi=300)` 落 `04_results/*.pdf` + `*.png`；脚本顶部先跑一次 CJK+retina 设置。需要时
  `Skill` 调用 `67/figure` 或 `39-vincentarelbundock-marginaleffects`（边际效应图）作补充。

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
  写作 prompt 必须附 `00_meta/evidence_ledger.md`，要求每个摘要、引言、结果和结论 claim 使用不高于 ledger
  允许等级的措辞；ledger 中 `descriptive` / `exploratory` / `no_claim` 的内容不得被包装成主因果发现。
  还必须附 `03_analysis/design_risk_ledger.md`：识别段、稳健性段、政策含义和 cover letter 的外推边界不得
  强于 design risk ledger 的 claim consequence。
- 文献综述薄弱时，配合 `36-taoyunudt-literature-review-skill`、`52-keemanxp-slr-prisma`、
  `59-shiquda-openalex-skill` 补做结构化综述；引用入库可配 Zotero MCP。
- **写作标尺**：按 [`writing-craft.md`](writing-craft.md)（引言五段公式、解剖结构、量级纪律）写；识别段按
  [`threats-to-validity.md`](threats-to-validity.md) §5 加一段「Threats to Identification」先发制人、把每个
  威胁指到 `robustness/` 真实 artifact；related-work 段按
  [`literature-and-positioning.md`](literature-and-positioning.md) §4 点名最接近的 3–5 篇、说清本文前进在哪。

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

## 🏁 里程碑 · 初稿质量门（Draft Quality Gate）—— Stage 7 之后、Stage 8 之前强制执行

**目的**：兑现「**高质量**初稿」承诺。不靠主代理自评，而是**派一个独立「顶刊 AE」critic subagent**，
按 [`quality-rubric.md`](quality-rubric.md) 的 7 维评分卡量化打分，决定「放行进投稿」还是「回炉重做」。

**execute**（套用 [`subagent-templates.md`](subagent-templates.md) §QG，**只派 1 个**）
- critic 必读 `references/quality-rubric.md`，读初稿（`07_dehumanize/main.tex` + `04_results/` 表图 +
  `05_draft/ref.bib`）+ 对照 `01_proposal/proposal.md`（贡献承诺）与 `03_analysis/results/summary.md`
  （真实结果）+ `03_analysis/design_register.md` / `03_analysis/method_gate.md`（方法证据）+
  `00_meta/evidence_ledger.md`（claim strength 和表图/脚本追溯），**逐维打分写入
  `00_meta/quality_scorecard.md`**，本轮分数追加进 `logs/quality_gate.md`。
  若存在 `03_analysis/design_risk_ledger.md`，critic 也必须读取；有 blocking threat 时识别/稳健/解读相关维度按
  rubric 封顶，不能因为稿件写得顺就放行。
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
- 加载 [`peer-review-and-submission.md`](peer-review-and-submission.md)（五维审稿 + Essential/Desirable
  分级、逐条可追溯的 response letter 模板）与 [`threats-to-validity.md`](threats-to-validity.md)（审稿命中
  识别威胁时，按其 §2 末列「被问到怎么回应」逐条回应、指向具体修改位置）。
  同时加载 [`design-risk-ledger.md`](design-risk-ledger.md)，把 `03_analysis/design_risk_ledger.md` 中未完全关闭
  或只允许降级措辞的风险转成模拟 reviewer objections 和主动回应。
- `Skill` 调用 `67/referee-report` 生成审稿报告（可设 normal/high-level 档与意见条数；
  推荐先按 Major Revision 口吻拿到建设性意见），落 `08_review/referee_report.md`。
- `Skill` 调用 `67/paper-referee-revise`，按审稿意见**逐条**修订 `main.tex`，并生成 response letter
  落 `08_review/response_letter.md`。若是内部自评则用 `67/paper-self-revise`。
- 想要更狠的对抗审阅可叠加 `66/grillme`、`66/econ-reviewer`、`21-claesbackman-AI-research-feedback`、
  `41-sticerd-eee-sewage-econometrics-check`（计量自检）。计量复核可再用 StatsPAI MCP
  `audit_result(result_id)` 复跑「还缺哪些稳健性」，与 `03_analysis/method_gate.md` 对账（statspai-analysis §6）。
  审稿人还必须抽查 `00_meta/evidence_ledger.md`：摘要、贡献段、结果段、cover letter 的每个 claim 是否都有
  result/exhibit/script 支撑，且措辞没有超过 design gate card 允许等级。

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
- 从 `templates/submission_checklist.md` 生成 `09_submission/submission_checklist.md`，并按目标刊官网实时刷新：
  author guidelines、data/code policy、匿名化、DAS、IRB/ethics、disclosure、AsCollected 或等价 provenance。
  若政策页无法访问，按 [`runtime-fallbacks.md`](runtime-fallbacks.md) 标 blocked，投稿包不得标 ready。
- 需要排版成 Word / 提交版 PDF 时用 `67/md-to-docx`、`67/markitdown`、`08-ndpvt-web-latex-document-skill`。

**review**：critic 走一遍目标期刊的 submission checklist（字数、匿名化、利益冲突声明、数据可得性声明、
IRB/DUA 与公开复现包边界）。

**revise / 交付**：定稿投稿包到 `09_submission/`。

---

## 收尾（编排器本体，不调子 skill）

汇总所有阶段日志与产出，优先用 `templates/FINAL_REPORT.md` 写 `FINAL_REPORT.md`（见 SKILL.md「收尾」
节的清单），并按 [`reproducibility-pack.md`](reproducibility-pack.md) 与
[`data-governance.md`](data-governance.md) 生成 `REPLICATION.md`、DAS（如需）、data governance register
与 master script（模板见 `templates/REPLICATION.md`、`templates/DAS.md`、`templates/run_all.sh`）。
能真实重跑就删派生产物后跑一次；不能重跑就把阻断原因写进
`workflow_state.json.replication_pack.last_rebuild_check`，且 `status` 只能是 `not_ready`。

最终打包并告知用户交付物路径、一键重跑命令、复现包状态、投稿前仍需人工确认的事项。
