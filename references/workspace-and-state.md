# Workspace & State — 工作区布局、状态文件、子代理 I/O 约定

> 本编排器把"一篇论文项目"落成一个自包含的工作区目录。所有阶段读/写都在这个目录内，保证
> **可断点续跑、可复现、可打包交付**。本文是工作区与状态文件的**权威字段定义**，与
> [`../assets/init_workspace.sh`](../assets/init_workspace.sh)、
> [`../assets/workflow_state.template.json`](../assets/workflow_state.template.json) 严格对齐。

---

## 1. 工作区目录布局

Setup 阶段用 `init_workspace.sh <workspace-dir>` 铺出下列骨架。工作区根目录名建议为
`paper_workspace/<研究短名>_<YYYYMMDD-HHMM>/`（北京时间）。脚本**拒绝覆盖已存在路径**——
撞名就另选一个新的时间戳目录。脚本会自动复制
`assets/workflow_state.template.json` 到 `00_meta/workflow_state.json`，并写一个
`00_meta/intake.md` 占位；带 ★ 的具体研究产物由各阶段在运行中写入。

```text
paper_workspace/<short>_<YYYYMMDD-HHMM>/
├── README.md                      # init 脚本自动写入的占位说明
├── REPLICATION.md                 # ★收尾生成的复现包 README（SSDE/AEA 风格）
├── run_all.sh / master.do / Makefile # ★一键重跑入口（至少三选一）
├── 00_meta/
│   ├── workflow_state.json        # ★唯一权威进度文件（断点续跑依据）
│   ├── analysis_backend.md        # ★Python/StatsPAI、Stata、R 后端选择与环境检查
│   ├── quality_scorecard.md       # ★初稿质量门 7 维评分卡（决定放行/回炉）
│   ├── data_governance.md         # ★数据分级、PII、IRB/DUA、公开包边界
│   ├── evidence_ledger.md         # ★claim→data→estimate→exhibit→script 总账
│   └── intake.md                  # 入口判定、交互档位、目标期刊、语言
├── 01_proposal/
│   ├── candidates/                # idea-finder 保留的 ≥9 分候选（每个一份 md；输出已重定向到此）
│   ├── journal_digest.md          # journal-digest 目标期刊口味扫描（输出已重定向到此）
│   ├── critique.md                # critic subagent 的选题审阅
│   └── proposal.md                # ★定稿计划书：后续所有阶段的"合同"
├── 02_data/
│   ├── raw/                       # data-fetcher 取回的原始数据
│   ├── clean.parquet              # ★分析就绪数据（或 .dta/.csv）
│   ├── codebook.md                # 变量定义/来源/单位/缺失处理
│   ├── sample_audit.md            # ★样本流失、estimand 对齐、missingness/balance/overlap 审计
│   ├── <cleaning>.py|.do|.R       # 清洗脚本（保证可复现）
│   └── data_audit.md
├── 03_analysis/
│   ├── design_register.md         # ★方法合同：estimand、识别假设、估计量、诊断证据、回退
│   ├── method_gate.md             # ★方法闸门：最低证据包是否齐全、是否 PASS
│   ├── <estimation>.py|.do|.R     # 估计代码
│   ├── results/                   # ★main_results.json + summary.md
│   ├── robustness/                # 每个稳健性检验一份 json/png（subagent 各自写盘）
│   └── results_audit.md
├── 04_results/
│   ├── *.tex                      # 出版级三线表
│   ├── *.pdf / *.png              # 图
│   └── exhibits_index.md          # 每张表/图对应论文哪个论点
├── 05_draft/
│   ├── main.tex                   # ★初稿
│   ├── ref.bib
│   └── draft_audit.md
├── 06_polish/                     # paper-pipeline 的工作副本与产出
│   ├── main.tex / ref.bib
│   ├── ref_verify_report.xlsx
│   └── pipeline_state.json        # paper-pipeline 自己的状态文件（嵌套，互不干扰）
├── 07_dehumanize/
│   └── main.tex                   # 去 AI 味后的稿
├── 08_review/
│   ├── referee_report.md
│   ├── response_letter.md
│   └── main.tex                   # 按审稿意见修订后的稿
├── 09_submission/
│   ├── journal_shortlist.md       # ~20 本目标期刊 + 1主2备
│   ├── cover_letter.md
│   ├── DAS.md                     # 数据可得性声明（如需；受限数据时必填）
│   ├── submission_checklist.md    # 目标刊政策刷新与投稿文件清单
│   └── ref_verify_final.xlsx
├── logs/
│   ├── stage_<N>.md               # 每阶段审计轨迹：调了哪些 skill / 派了哪些 agent / 关键决策
│   └── quality_gate.md            # 初稿质量门历轮打分与回退记录（分数随修订上升的轨迹）
├── backups/
│   └── after_stage<N>/            # 每阶段末关键产物快照（回滚路径）
└── FINAL_REPORT.md                # ★收尾产出：复盘表 + 交付清单 + 复现说明
```

★ = 阶段间传递的关键交付物。后一阶段只需读前一阶段的 ★ 文件，不必重读整目录（省上下文）。

---

## 2. `workflow_state.json` 字段含义

Setup 时由 [`../assets/init_workspace.sh`](../assets/init_workspace.sh) 自动把
[`../assets/workflow_state.template.json`](../assets/workflow_state.template.json) 复制到
`00_meta/workflow_state.json`；主代理随后只填值、不改字段名。字段（**与模板一一对应，勿自创字段名**）：

| 字段 | 含义 |
|---|---|
| `schema_version` | 模板版本号（当前 `6`；v2 新增 `quality_gate`，v3 新增 `method_gate`，v4 新增 `replication_pack`，v5 新增 `analysis_backend`，v6 新增 `empirical_audit`） |
| `project.short_name` | 研究短名（工作区目录名的一部分） |
| `project.created_at_beijing` | 北京时间字符串（`TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M'`） |
| `project.entry_stage` | 入口路由判定的起始阶段编号 0–9（见 SKILL.md Phase 0 第 2 步） |
| `project.mode` | `auto` / `stage-confirm` / `interactive`（交互档位） |
| `project.target_journal` | 目标期刊（未定则填 `"TBD-by-stage1"`） |
| `project.language` | `en` / `zh` / `bilingual`（决定 Stage 7 分流） |
| `analysis_backend.primary` | Stage 3–4 的主分析后端：`python-statspai` / `stata` / `r` |
| `analysis_backend.secondary_validation` | 交叉验证后端；无则 `none` |
| `analysis_backend.script_extension` | 主估计脚本扩展名：`.py` / `.do` / `.R` / `.qmd` |
| `analysis_backend.child_skill` | 选定后端调用的 child skill 或 Read 回退路径 |
| `analysis_backend.environment_status` | `pending` / `available` / `fallback` / `blocked` |
| `analysis_backend.version_report` | 后端选择、版本检查和 fallback 记录路径（`00_meta/analysis_backend.md`） |
| `empirical_audit.status` | `pending` / `pass` / `not_pass`——样本、变量构造、missingness/balance/overlap 审计状态 |
| `empirical_audit.sample_audit` | 样本审计报告路径（默认 `02_data/sample_audit.md`） |
| `empirical_audit.estimand_alignment` | `pending` / `pass` / `not_pass`——估计样本是否仍对应目标 estimand |
| `empirical_audit.missingness_balance` | `pending` / `pass` / `not_pass`——缺失、attrition、baseline balance、overlap 是否可接受 |
| `empirical_audit.construct_validity` | `pending` / `pass` / `not_pass`——outcome/treatment/control 构造与 codebook、bad-control screen 是否一致 |
| `empirical_audit.blocking_issues` | 仍阻断 Method Gate 的样本/变量/推断层级问题列表 |
| `empirical_audit.last_audit` | 最近一次样本审计时间/摘要 |
| `stages` | 10 个阶段键（`0_intake_setup` … `9_submission`）各自的状态 |
| `method_gate.status` | `pending` / `pass` / `not_pass`——Stage 3 方法闸门判定 |
| `method_gate.primary_design` | 主识别设计（如 staggered_did / iv / rdd / sdid / dml） |
| `method_gate.primary_estimator` | 主估计量或实现 route（如 Callaway-Santanna / rdrobust / DoubleML PLR） |
| `method_gate.design_register` | 设计注册文件路径（`03_analysis/design_register.md`） |
| `method_gate.method_gate_report` | 方法闸门报告路径（`03_analysis/method_gate.md`） |
| `method_gate.required_artifacts` | 本设计要求的最低证据包 artifact 列表 |
| `method_gate.missing_artifacts` | 最近一次方法闸门仍缺失的 artifact |
| `method_gate.last_audit` | 最近一次方法闸门审计时间/摘要 |
| `quality_gate.draft_milestone` | `pending` / `done`——「可投稿级初稿」核心里程碑是否达成（质量门 `pass` 时置 `done`） |
| `quality_gate.status` | `pending` / `pass` / `not_pass`——最近一轮质量门判定 |
| `quality_gate.rounds` | 已执行的质量门轮次（含回退；上限 2） |
| `quality_gate.last_total_score` | 最近一轮总分（满分 70） |
| `quality_gate.last_dimension_scores` | 最近一轮 7 维分数映射（如 `{"identification": 7, ...}`） |
| `quality_gate.scorecard` | 评分卡文件相对路径（`00_meta/quality_scorecard.md`） |
| `replication_pack.status` | `pending` / `ready` / `not_ready`——收尾复现包是否达到可移交标准 |
| `replication_pack.readme` | 复现包 README 路径（默认 `REPLICATION.md`） |
| `replication_pack.master_script` | 一键重跑入口（如 `run_all.sh` / `master.do` / `Makefile` target） |
| `replication_pack.data_availability_statement` | DAS 路径（默认 `09_submission/DAS.md`） |
| `replication_pack.archive_plan` | 存档位置/计划：AEA Data and Code Repository、trusted repository、OSF/Zenodo/Dataverse 等 |
| `replication_pack.runtime_minutes` | 最近一次端到端重跑耗时；未知则 `null`，不得虚填 |
| `replication_pack.last_rebuild_check` | 最近一次“删派生产物后重跑”或等价检查的时间/摘要 |
| `artifacts` | **名称→工作区相对路径** 的映射（= 交付物清单，对应布局里的 ★ 文件） |
| `decisions` | 数组，记录影响后续阶段的人类/自动决策：选刊、识别策略变更、失败回退分支 |
| `last_updated_beijing` | 每次写入时刷新的北京时间 |

**阶段状态取值**：`pending` / `in_progress` / `done` / `skipped`。

**写入纪律**：阶段开始置 `in_progress`、完成（产出 + 审阅闸门都过）才置 `done`、入口前置被跳过的
阶段置 `skipped`；每次写入同时刷新 `last_updated_beijing`。这是断点续跑的唯一依据——续跑时读它，
从第一个非 `done`/`skipped` 的阶段恢复。

**`artifacts` 示例**：

```json
{
  "proposal": "01_proposal/proposal.md",
  "analysis_backend": "00_meta/analysis_backend.md",
  "clean_data": "02_data/clean.parquet",
  "sample_audit": "02_data/sample_audit.md",
  "main_results": "03_analysis/results/main_results.json",
  "design_register": "03_analysis/design_register.md",
  "method_gate": "03_analysis/method_gate.md",
  "evidence_ledger": "00_meta/evidence_ledger.md",
  "draft": "05_draft/main.tex",
  "submission_grade_draft": "07_dehumanize/main.tex",
  "quality_scorecard": "00_meta/quality_scorecard.md",
  "data_governance": "00_meta/data_governance.md",
  "replication_readme": "REPLICATION.md",
  "master_script": "run_all.sh",
  "data_availability_statement": "09_submission/DAS.md"
}
```

**`decisions` 示例**（每次失败回退也记这里，取代单独的 fallback 字段）：

```json
[
  {"stage": 1, "decision": "选定标题 T3，novelty=9", "at": "2026-06-19 14:02"},
  {"stage": 3, "decision": "平行趋势不过 → 改用 Callaway-Santanna 交错估计量", "at": "2026-06-19 15:40"}
]
```

---

## 3. 子代理（subagent）输入/输出约定 —— 上下文保护的落地细则

核心原则是「子代理自己写盘、只回传状态摘要」。每次用 `Agent` 派 subagent，prompt **必须**显式给：

1. **角色与目标**：一句话说清它在哪个阶段做什么。
2. **输入文件**：明确路径，告诉它该读什么（如 `01_proposal/proposal.md`、`02_data/clean.parquet`）。
3. **输出文件**：明确它该写到哪（如 `03_analysis/robustness/placebo_time.json`），并要求**处理完
   立即写盘**。
4. **强制调用的子 skill（如适用）**：例如"你必须用 `Skill` 工具加载 `67/novelty-check` 完成查新"。
5. **回传契约**：**只回传 ≤10 行状态摘要**——做了什么、写到哪个文件、关键数字（系数/SE/p/分数）、
   通过与否、一句话下一步建议。**严禁回传完整产出。**
6. **工具放行**：主代理确保 subagent 可用 Read + Write + Bash（必要时 Skill）。

**并行批次**：同阶段彼此独立的任务一次性并行派发，每批 ≤10 个（选题漏斗用 5，
沿用 `idea-finder`）。有依赖的串行，并把上游产物路径写进下游 subagent 的输入清单。

**主代理侧**：拿到摘要后只更新 `workflow_state.json` / `logs/` / `backups/`，**不把摘要里引用的大
文件读回上下文**，除非下一步确实需要其中的具体数字——那也只 `Read` 需要的那几行/那个 json，而非整份。

---

## 4. 复现与交付

- 所有脚本（清洗、估计、画图、建表）留在工作区内对应阶段目录，配 `FINAL_REPORT.md` 里的
  "一键重跑命令"，并同步写入 `workflow_state.json.replication_pack.master_script`，确保第三方能从
  `02_data/raw/` 复跑到 `04_results/`。
- 数据版权 / 来源在 `02_data/codebook.md`、`00_meta/data_governance.md` 与 `FINAL_REPORT.md` 注明；
  不可分发的数据只留拉取脚本与说明，不入库原始文件。目标 AEA/AER/AEJ 时，从 Stage 2 起按 AEA
  data/code policy 记录 provenance、访问成本、权限限制与预计重跑时间，避免投稿前补 replication package。
- `templates/` 下的 sample audit、design register、method gate、evidence ledger、quality scorecard、data governance、
  DAS、REPLICATION、submission checklist、FINAL_REPORT、run_all 可作为工作区 artifact 的起始模板；实例化后仍以工作区文件
  为准，模板本身不代表研究已通过闸门。
- 收尾时写 `REPLICATION.md`、DAS（如需）、archive plan 与最近一次重跑耗时；若任何一项缺失，
  `replication_pack.status` 只能是 `not_ready`，质量门维度⑦不得放水。
- 打包交付时以工作区根目录为单位；`backups/` 与 `logs/` 可选保留作审计。
