# Workspace & State — 工作区布局、状态文件、子代理 I/O 约定

> 本编排器把"一篇论文项目"落成一个自包含的工作区目录。所有阶段读/写都在这个目录内，保证
> **可断点续跑、可复现、可打包交付**。本文是工作区与状态文件的**权威字段定义**，与
> [`../assets/init_workspace.sh`](../assets/init_workspace.sh)、
> [`../assets/workflow_state.template.json`](../assets/workflow_state.template.json) 严格对齐。

---

## 1. 工作区目录布局

Setup 阶段用 `init_workspace.sh <workspace-dir>` 铺出下列骨架。工作区根目录名建议为
`paper_workspace/<研究短名>_<YYYYMMDD-HHMM>/`（北京时间）。脚本**拒绝覆盖已存在路径**——
撞名就另选一个新的时间戳目录（`do-agent` 纪律）。脚本只建目录骨架；带 ★ 的具体文件由各阶段
在运行中写入。

```text
paper_workspace/<short>_<YYYYMMDD-HHMM>/
├── README.md                      # init 脚本自动写入的占位说明
├── 00_meta/
│   ├── workflow_state.json        # ★唯一权威进度文件（断点续跑依据）
│   └── intake.md                  # 入口判定、交互档位、目标期刊、语言
├── 01_proposal/
│   ├── candidates/                # idea-finder 保留的 ≥9 分候选（每个一份 md）
│   ├── critique.md                # critic subagent 的选题审阅
│   └── proposal.md                # ★定稿计划书：后续所有阶段的"合同"
├── 02_data/
│   ├── raw/                       # data-fetcher 取回的原始数据
│   ├── clean.parquet              # ★分析就绪数据（或 .dta/.csv）
│   ├── codebook.md                # 变量定义/来源/单位/缺失处理
│   ├── <cleaning>.py|.do|.R       # 清洗脚本（保证可复现）
│   └── data_audit.md
├── 03_analysis/
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
│   └── ref_verify_final.xlsx
├── logs/
│   └── stage_<N>.md               # 每阶段审计轨迹：调了哪些 skill / 派了哪些 agent / 关键决策
├── backups/
│   └── after_stage<N>/            # 每阶段末关键产物快照（回滚路径）
└── FINAL_REPORT.md                # ★收尾产出：复盘表 + 交付清单 + 复现说明
```

★ = 阶段间传递的关键交付物。后一阶段只需读前一阶段的 ★ 文件，不必重读整目录（省上下文）。

---

## 2. `workflow_state.json` 字段含义

Setup 时把 [`../assets/workflow_state.template.json`](../assets/workflow_state.template.json) 复制到
`00_meta/workflow_state.json` 并填写。字段（**与模板一一对应，勿自创字段名**）：

| 字段 | 含义 |
|---|---|
| `schema_version` | 模板版本号（当前 `1`） |
| `project.short_name` | 研究短名（工作区目录名的一部分） |
| `project.created_at_beijing` | 北京时间字符串（`TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M'`） |
| `project.entry_stage` | 入口路由判定的起始阶段编号 0–9（见 SKILL.md Phase 0 第 2 步） |
| `project.mode` | `auto` / `stage-confirm` / `interactive`（交互档位） |
| `project.target_journal` | 目标期刊（未定则填 `"TBD-by-stage1"`） |
| `project.language` | `en` / `zh` / `bilingual`（决定 Stage 7 分流） |
| `stages` | 10 个阶段键（`0_intake_setup` … `9_submission`）各自的状态 |
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
  "clean_data": "02_data/clean.parquet",
  "main_results": "03_analysis/results/main_results.json",
  "draft": "05_draft/main.tex"
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

源自 `do-agent`「子代理自己写盘、只回传状态摘要」。每次用 `Agent` 派 subagent，prompt **必须**显式给：

1. **角色与目标**：一句话说清它在哪个阶段做什么。
2. **输入文件**：明确路径，告诉它该读什么（如 `01_proposal/proposal.md`、`02_data/clean.parquet`）。
3. **输出文件**：明确它该写到哪（如 `03_analysis/robustness/placebo_time.json`），并要求**处理完
   立即写盘**。
4. **强制调用的子 skill（如适用）**：例如"你必须用 `Skill` 工具加载 `67/novelty-check` 完成查新"。
5. **回传契约**：**只回传 ≤10 行状态摘要**——做了什么、写到哪个文件、关键数字（系数/SE/p/分数）、
   通过与否、一句话下一步建议。**严禁回传完整产出。**
6. **工具放行**：主代理确保 subagent 可用 Read + Write + Bash（必要时 Skill）。

**并行批次**：同阶段彼此独立的任务一次性并行派发，每批 ≤10 个（参考 `do-agent` 上限；
`idea-finder` 用 5）。有依赖的串行，并把上游产物路径写进下游 subagent 的输入清单。

**主代理侧**：拿到摘要后只更新 `workflow_state.json` / `logs/` / `backups/`，**不把摘要里引用的大
文件读回上下文**，除非下一步确实需要其中的具体数字——那也只 `Read` 需要的那几行/那个 json，而非整份。

---

## 4. 复现与交付

- 所有脚本（清洗、估计、画图、建表）留在工作区内对应阶段目录，配 `FINAL_REPORT.md` 里的
  "一键重跑命令"，确保第三方能从 `02_data/raw/` 复跑到 `04_results/`。
- 数据版权 / 来源在 `02_data/codebook.md` 与 `FINAL_REPORT.md` 注明；不可分发的数据只留拉取脚本
  与说明，不入库原始文件。
- 打包交付时以工作区根目录为单位；`backups/` 与 `logs/` 可选保留作审计。
