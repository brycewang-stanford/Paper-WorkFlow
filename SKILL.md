---
name: paper-workflow
description: >
  经管 / 社科**实证论文全流程总编排器（meta-orchestrator）**：把「选题 → 设计 → 数据 →
  计量识别与估计 → 方法闸门 → 表与图 → 写作初稿 → 全流程打磨 → 语言去 AI 味 →
  初稿质量门 → 模拟评审与修订 → 选刊与投稿 → 复盘交付」这条端到端流水线自动跑通。本 skill **不重复实现任何子能力**，
  而是采用「多代理 + 上下文保护」执行范式与 `paper-pipeline` 的「固定顺序 +
  可断点续跑 + 交互档位」编排范式，按阶段**调用既有 skill / 派发并行 subagent** 完成一篇
  可投稿的实证论文，并在 Stage 3–4 提供 Python/StatsPAI、Stata、R 三种分析后端选择。触发场景：用户说 "/paper-workflow"、"帮我写一篇实证论文"、
  "从选题到投稿"、"实证论文全流程"、"经管社科论文工作流"、"端到端跑一篇 paper"、
  "automate an empirical paper"、"end-to-end empirical research pipeline"、"paper workflow"，
  或带着一个研究方向 / 一份计划书 / 一份数据 / 一份初稿希望「一条龙」推进到投稿；也适用于用户要求
  "用 Stata 跑完整实证"、"用 R/fixest/Quarto 复现" 或 "Python/StatsPAI、Stata、R 三选一"。
allowed-tools: Skill, Agent, Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, WebSearch, WebFetch, NotebookEdit
argument-hint: "[研究方向 | proposal.md | 数据路径 | main.tex 目录] [目标期刊(可选)]"
---

# Paper-WorkFlow — 经管 / 社科实证论文全流程总编排器

## Overview

这是一个 **meta-orchestrator（总编排器）**。它的职责不是亲自完成研究的每一步，而是把一篇
实证论文从无到有需要的所有环节，编排成一条 **10 个阶段（Stage 0–9）+ 2 道硬闸门** 的可控流水线，每个
阶段都通过 **`Skill` 工具调用既有 skill** 或 **`Agent` 工具派发并行 subagent** 来完成，主
代理只负责**规划、路由、状态跟踪、阶段间审阅与交付**。

它的设计建立在两条核心范式上：

- **多代理 + 上下文保护范式**：子代理**自己把产出写盘**、
  只向主代理**回传状态摘要**，绝不回传完整内容；主代理上下文极其稀缺，必须做上下文工程。
- **`paper-pipeline` 的固定顺序 + 可断点续跑 + 交互档位范式**：用 `workflow_state.json`
  记录进度，每阶段有横幅、有快照备份、可中断后从断点恢复；开跑前一次性问清交互档位。

> **核心纪律：能调用就不要重写。** 本仓库 `skills/67-econfin-workflow-toolkit/` 已经提供了
> 覆盖全流程的 47 个 skill；本编排器的价值在于**把它们按正确顺序、用正确的上下文、在正确
> 的人类决策点串起来**，而不是复制它们的逻辑。每个阶段「调用哪个 skill」见
> [`references/skill-map.md`](references/skill-map.md)，「每阶段怎么跑」见
> [`references/stage-playbook.md`](references/stage-playbook.md)，「现代因果推断与应用计量的最低证据包」见
> [`references/research-grade-methods.md`](references/research-grade-methods.md)，「样本、变量与 estimand 对齐审计」见
> [`references/empirical-audit.md`](references/empirical-audit.md)，「Stage 3–4 的 Python/Stata/R
> 分析后端选择」见 [`references/analysis-backends.md`](references/analysis-backends.md)，「默认 Python/StatsPAI 估计 +
> 出版级出表引擎（StatsPAI 包 + MCP）」见 [`references/statspai-analysis.md`](references/statspai-analysis.md)，
> 「Stage 0 路由、stage passport 与 handoff 断点交接」见
> [`references/orchestration-and-handoff.md`](references/orchestration-and-handoff.md)。

---

## 这条流水线（固定主线，可按入口跳入）

| Stage | 阶段 | 主要调用的 skill（位于 `67-econfin-workflow-toolkit/`，除非另注） | 产出落盘 |
|---|---|---|---|
| **0** | Intake & Setup | *(编排器本体)* | 工作区、`workflow_state.json`、入口路由 |
| **1** | 选题与设计 | `econfin-idea-finder` → `novelty-check` → `significance-search` → `journal-digest` → `econfin-proposal` | `01_proposal/proposal.md` |
| **2** | 数据 | `data-fetcher` → `data-cleaning` + sample/estimand audit | `02_data/clean.parquet` + `codebook.md` + `sample_audit.md` |
| **3** | 计量识别、估计与方法闸门 | **分析后端路由**：默认 Python/StatsPAI（MCP 优先：`detect_design→preflight→recommend→fit(as_handle)→audit_result→sensitivity_from_result→bibtex`），也可按用户/复现要求切到 Stata（`00.2` `.do` pipeline）或 R（`00.3` tidyverse/fixest/Quarto pipeline）；再按设计配 `did-analysis` / `iv-estimation` / `rdd-analysis` / `synthetic-control` / `panel-data` / `ols-regression` / `time-series` / `ml-causal` + empirical audit + research-grade methods pack + design gate cards | `03_analysis/` 代码 + `design_register.md` + `method_gate.md` + `00_meta/evidence_ledger.md` |
| **4** | 表与图 | 按同一分析后端生成出版级表图：Python/StatsPAI `regtable`/`paper_tables`/`collect`，Stata `esttab`/`outreg2`/`collect`，R `modelsummary`/`etable`/Quarto；均需 Word/Excel/LaTeX 同出 + PDF/PNG 图 | `04_results/*.{tex,docx,xlsx}` + `*.pdf/png` |
| **5** | 写作初稿 | `paper-writer` | `05_draft/main.tex` + `ref.bib` |
| **6** | 全流程打磨 | `paper-pipeline`（内部跑 polish→self-revise→style→polish→reference-verify） | 打磨后的 `main.tex` |
| **7** | 语言与去 AI 味 | `readability` / `fix-chinese` + （`44`/`47`/`48`/`49` 去 AIGC 集合） | 去味后的稿件 |
| **8** | 模拟评审与修订 | `referee-report` → `paper-referee-revise`（或 `paper-self-revise`） | 修订稿 + response letter |
| **9** | 选刊与投稿 | `paper-submission` + `reference-verify`（终审） | 期刊清单 + cover letter |
| **—** | 复盘与交付 | *(编排器本体)* | `FINAL_REPORT.md` + 打包交付物 |

> 完整阶段细节、每阶段的 plan→execute→review→revise 微循环、subagent 派发模板，全部在
> [`references/stage-playbook.md`](references/stage-playbook.md)。**主代理在进入某阶段时才去读
> 对应章节**（渐进式加载，省上下文）。

> **双硬闸门 = 方法闸门 + 初稿质量门。** Stage 3 结束必须先过
> [`research-grade-methods.md`](references/research-grade-methods.md) 的 **Method Gate**：设计注册、
> 最低诊断证据、稳健性矩阵与复现脚本齐了，且
> [`design-risk-ledger.md`](references/design-risk-ledger.md) 把适用识别威胁、选择性报告、外部效度、SUTVA/溢出
> 和 attrition 风险逐项关掉或降级，才能把结果送进表图和写作。Stage 7 跑完再过
> **Draft Quality Gate**：结构完整、识别可信、表图齐备、语言无 AI 味的初稿，必须由独立 critic
> 按 7 维 rubric 打分达标，才算「可投稿级初稿」。**任何闸门未达标都按回退指令重做**，绝不把
> 「流程跑完」当成「研究可信」。

---

## Phase 0：Setup（在调用任何子 skill 之前，把下面这些全部做完）

1. **取北京时间**。`Bash: TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M'`，记为 `NOW`，用于命名与
   状态文件。（开跑前先取日期时间，保证命名与时间戳一致。）

2. **判定入口（entry-point routing）**。用户带来的东西决定从哪个 Stage 进入——不要一律从
   Stage 1 开始：

   | 用户带来的 | 从哪进入 | 说明 |
   |---|---|---|
   | 只有一个研究方向 / 一句话想法 | **Stage 1** | 完整走选题漏斗 |
   | 一份已成形的 proposal（X→M→Y、识别策略、样本） | **Stage 2** | 跳过选题，直接取数 |
   | 已清洗好的数据 + 设计 | **Stage 3** | 直接估计 |
   | 已有回归结果 / 表图 | **Stage 5** | 直接写初稿 |
   | 一份 `main.tex` 初稿 | **Stage 6** | 直接进打磨流水线 |
   | 一份初稿 + 审稿意见 | **Stage 8** | 直接按意见修订 |
   | 一份成稿要投稿 | **Stage 9** | 直接选刊 |

   入口不明确时用 `AskUserQuestion` 一次问清；能从 `$ARGUMENTS`（路径后缀 `.tex`/`.md`/
   数据扩展名、是否像期刊名）推断就别问。

3. **建工作区**。在用户指定目录（缺省为当前工作目录）下创建
   `paper_workspace/{研究短名}_{NOW紧凑时间戳}/`，内部用 `assets/init_workspace.sh` 铺出标准
   骨架（`00_meta/ 01_proposal/ 02_data/ 03_analysis/ 04_results/ 05_draft/ 06_polish/
   07_dehumanize/ 08_review/ 09_submission/ logs/ backups/`），并自动生成
   `00_meta/workflow_state.json`、`00_meta/entry_routing.md`、`00_meta/stage_passport.md`、
   `00_meta/handoff/`、`00_meta/analysis_backend.md`、`00_meta/evidence_ledger.md` 与
   `00_meta/intake.md`。若同名目录已存在，**另建新目录、
   绝不覆盖**。完整布局见
   [`references/workspace-and-state.md`](references/workspace-and-state.md)。关键交付物优先从
   [`templates/`](templates/) 实例化（样本审计、设计注册、方法闸门、质量评分卡、数据治理、DAS、复现 README、
   投稿 checklist、最终报告、stage passport 与 handoff card），不要临场自创格式。

4. **写 Stage 0 路由与续跑台账**。把入口判断、用户材料、推断假设、仍需人类决策的分支写进
   `00_meta/entry_routing.md`，并初始化 `00_meta/stage_passport.md`。这两份文件是
   `workflow_state.json.orchestration` 的人工可读 companion：handoff、断点恢复、并行 agent 接手时先读它们。

5. **一次性问清四件套**（用一个 `AskUserQuestion`，多选/多题，避免来回打断）：
   - **交互档位**：`全自动`（只在最终交付时汇报）/ `阶段确认`（**推荐缺省**：每阶段末给摘要、
     等放行再进下一阶段）/ `全程交互`（每个子 skill 跑自己原生的逐项审批，投稿前终版用）。
     —— 这个选择就是各子 skill「快速通道」所需的**显式 opt-in**。
   - **目标期刊**（Stage 1/6/9 都要用，提前问以免中途卡住）：给 JF/JFE/RFS/MS/QJE/AER/
     《经济研究》/《管理世界》等常见项 + "Other" 自由填；也可填「暂不确定，由 Stage 1 推荐」。
   - **语言**：英文稿 / 中文稿 / 中英双语 —— 决定 Stage 7 走 `readability` 还是 `fix-chinese`+
     去 AIGC 集合，以及 Stage 5/6 的写作规范。
   - **分析后端**：`python-statspai`（推荐缺省）/ `stata` / `r` —— 决定 Stage 3–4 的估计脚本、
     表图出口和复现入口；这不是稿件语言。完整选择规则见
     [`references/analysis-backends.md`](references/analysis-backends.md)。

   若用户明确说“全自动 / 不要讨论 / 不要中途问我”，或 `$ARGUMENTS` 已足够推断四件套，则按保守缺省
   自动填值（`mode=auto` 或用户指定档位、`target_journal=TBD-by-stage1`、`language` 依输入语言推断），
   `analysis_backend` 依用户措辞/已有脚本推断，缺省 `python-statspai`），并把假设写入
   `00_meta/intake.md`、`00_meta/analysis_backend.md` 与 `workflow_state.json.decisions`；不要为了偏好问题阻断开跑。

6. **填写状态文件** `00_meta/workflow_state.json`（由 init 脚本从
   [`assets/workflow_state.template.json`](assets/workflow_state.template.json) 复制而来）。填入
   `project.{short_name, created_at_beijing=NOW, entry_stage, mode, target_journal, language}` 与
   `orchestration.{status, entry_routing, stage_passport, handoff_dir, fresh_evidence_required, self_review_gate, ethics_gate}`、
   `analysis_backend.{primary, secondary_validation, script_extension, child_skill, environment_status, version_report}`，
   并把每个 Stage 置为 `pending|in_progress|done|skipped`；`empirical_audit`、`method_gate`、
   `evidence_governance`、`design_risk`、`quality_gate` 与 `replication_pack` 起始置 `pending`（字段含义见
   [`references/workspace-and-state.md`](references/workspace-and-state.md)）。**每个阶段开始置
   `in_progress`、完成置 `done`，并刷新 `last_updated_beijing`**——这就是断点续跑的依据。

7. **断点续跑检查**。若工作区已存在 `workflow_state.json` 且有未完成阶段，先读
   `00_meta/stage_passport.md` 和 `workflow_state.json.orchestration.latest_handoff`，再刷新当前
   `git status` / 当前产物 / gate 证据，展示进度并询问：从第一个未完成阶段继续，还是重头来？
   handoff card 只是指针，**不能**当成当前事实；缺少 fresh evidence 时不得宣称阶段已完成。

8. **不要为「计划」单独求批准**。Setup 完成后，**直接建任务跟踪并开跑**（规划阶段
   结束即执行）。人类决策点交给「阶段确认 / 全程交互」档位去守，而不是在开跑前反复确认。

---

## 多代理 + 上下文保护协议（贯穿所有阶段）

主代理上下文是**最稀缺资源**。任何"重读大文件、跑长代码、扫一堆文献"的脏活累活，都**派给
subagent（`Agent` 工具）或交给子 skill**，主代理只持有指针与状态。硬规则：

1. **子代理自己写盘，只回传状态摘要**。给每个 subagent 显式指定它的**输入文件**和**输出文件**，
   要求它"处理完立即把结果写到指定文件，只向主代理回传 ≤10 行的状态摘要（做了什么、写到哪、
   关键数字、是否通过、下一步建议）"。**严禁把完整产出回传主代理。**
2. **主代理为子代理放行 Read + Write + Bash**（必要时含 Skill），让它能独立完成闭环。
3. **能并行就并行**。同一阶段内彼此独立的任务（如多个稳健性检验、多个候选期刊匹配、多份机制
   检验）一次性并行派发（每批 ≤10 个 subagent；选题漏斗沿用
   `idea-finder` 的 `PARALLEL_BATCH_SIZE=5`）。有依赖的串行。
4. **每阶段是一个微循环**：`plan（规划/收集） → execute（执行/整合） →
   review（审阅/挑错） → revise（按审阅修订）`。重活阶段（1 选题、3 估计、6 打磨、8 评审）尤其
   要派一个**独立 critic subagent** 做对抗式审阅，再据其反馈修订。
5. **子 skill 的调用方式**：轻量、需要主线上下文的（如 `paper-style` 要顺着同一份 `main.tex`）
   直接在主代理里调；重量、可隔离的（如多路文献扫描、批量稳健性）派 subagent，并在 subagent 的
   prompt 里**强制要求它按下文「子 skill 调用协议」加载对应子 skill**（优先 `Skill(<注册名>)`、
   not found 则 `Read` 该 SKILL.md），**绝不许它凭记忆脑补**（参考 `idea-finder` 让每个 subagent
   强制加载 `econfin-proposal`+`novelty-check` 的做法）。
6. **日志**：每阶段把"调用了哪些 skill / 派了哪些 agent / 产出了哪些文件 / 关键决策"追加到
   `logs/stage_<N>.md`，并同步更新 `00_meta/stage_passport.md`，作为复盘与续跑的审计轨迹。
7. **交接**：阶段切换、长任务暂停、上下文变薄或并行 agent 接手前，在 `00_meta/handoff/` 写一张
   handoff card，并把路径写入 `workflow_state.json.orchestration.latest_handoff`。下一位 agent 先刷新现实再继续。

---

## 子 skill 调用协议（怎么把被编排的 skill 真正跑起来）

本编排器的全部价值都建立在「能正确调起子 skill」上。子 skill 是**仓库内的文件夹**，**不保证**在
用户运行时里注册为可被 `Skill` 工具直接触发的 skill。因此每次调用按下面的优先级走（权威细节见
[`references/skill-map.md`](references/skill-map.md) 第 0 节）：

1. **优先 `Skill` 工具**——`Skill(skill="<注册名>", args=...)`。**注册名 = 该 skill `SKILL.md`
   前言的 `name:` 字段，不一定等于文件夹名**。已知大小写/改名差异：`econfin-proposal`→
   `Econfin-Proposal`、`significance-search`→`Significance-Search`、`chinese-ppt`→`chinese-ppt2`、
   `command-development`→`Command Development`。**用注册名，别用文件夹名猜。**
2. **`Skill` 报「not found」就立刻退回 `Read` 内联执行**（稳路径，永远可用）：
   `Read skills/67-econfin-workflow-toolkit/<folder>/SKILL.md`，把它的正文当作本步操作手册逐步执行
   ——轻量步骤在主代理里跑，重量步骤把「`Read` 这个 SKILL.md 并按它执行」写进 subagent 的 prompt。
   **不要反复重试 `Skill`，也不要凭记忆脑补子 skill 的逻辑**（这正是 `idea-finder` 反复警告的劣化）。
3. **覆盖会写到仓库外的输出路径**：`econfin-idea-finder`（`F:\Dropbox\CC\选题大全\`）与 `journal-digest`
   （`F:\OneDrive\研究发展部\期刊速递\`）在其 SKILL.md 里硬编码了 Windows 绝对输出路径。调用它们时
   **必须**在 args / subagent prompt 里把输出目录改写为工作区内路径（候选→`01_proposal/candidates/`，
   期刊摘要→`01_proposal/journal_digest.md`）。模板见
   [`references/subagent-templates.md`](references/subagent-templates.md)。

> **派 subagent 调子 skill 时，SKILL.md 路径必须是仓库内完整路径**——subagent 的工作目录可能与主
> 代理不同，给错路径它就找不到文件、转而脑补，产出不可复现的劣化结果。

---

## 阶段执行协议（每个 Stage 都按这个走）

进入任一阶段时，按固定四步执行（细节在 playbook 对应章节）：

1. **打横幅**，让用户始终知道流水线在哪：

   ```
   ════════════════════════════════════════
     Stage N/9 · <阶段名>  —  <一句话目的>
     调用：<本阶段要用的 skill 列表>
   ════════════════════════════════════════
   ```

2. **置状态 `in_progress`** → 读 [`references/stage-playbook.md`](references/stage-playbook.md) 的
   对应章节 → 按其 plan→execute→review→revise 跑（该用 `Skill` 用 `Skill`，该派 `Agent` 派
   `Agent`，全程守上面的上下文保护协议）。

3. **冲突 / 退化检查**（沿用 `paper-pipeline`）：若工作区被多端编辑（Overleaf/Dropbox），每阶段
   前后 `Glob` 一次 `*冲突副本*`/`*conflicted copy*`，发现就停下让用户定夺哪份为准。每阶段末把
   关键产物快照进 `backups/after_stage<N>/`，作为回滚路径。若 `Skill` / `Agent` / 网络 / MCP /
   Stata/R/Python/Zotero 等不可用，按
   [`references/runtime-fallbacks.md`](references/runtime-fallbacks.md) 选择 fallback，并把影响写入日志、
   `decisions` 与对应闸门；不可把工具缺失伪装成结果已验证。

4. **阶段闸门**：置状态 `done` → 按交互档位决定是否暂停：
   - `全自动`：直接进下一阶段；
   - `阶段确认`（缺省）：输出本阶段**摘要卡**（产出文件清单 + 关键数字 + 红旗 + 下阶段计划），
     等用户放行；
   - `全程交互`：本阶段内各子 skill 已逐项审批过，这里再做一次阶段级确认。

   遇到**硬阻断**（平行趋势不过、IV 弱工具、查新发现撞车、数据取不到）时：不要硬往下走——
   按 playbook 的「失败回退」分支处理（换识别策略 / 换样本 / 退回 Stage 1 改设计），并在摘要卡
   里**显著标红**告诉用户发生了什么、采取了什么回退。（参考 `China-CF-study` 的「预期实证结果
   无法实现时自动切换备选方案」纪律。）

---

## 研究级方法闸门（Method Gate）—— Stage 3 之后、Stage 4 之前强制执行

Stage 3 的目标不是「跑出显著系数」，而是把识别设计、估计量、诊断证据、设计风险和稳健性矩阵落成可审计产物。
因此 Stage 3 必须加载 [`references/research-grade-methods.md`](references/research-grade-methods.md)
与 [`references/design-gate-cards.md`](references/design-gate-cards.md)（按设计分支列 required artifacts、
hard fail 和 claim 降级规则）、[`references/empirical-audit.md`](references/empirical-audit.md)（样本、变量与 estimand 对齐）、
[`references/inference-and-uncertainty.md`](references/inference-and-uncertainty.md)（标准误/聚类层级、few-cluster 修正、
随机化推断、多重检验、弱工具稳健区间、p 值报告纪律）、[`references/mechanism-and-channels.md`](references/mechanism-and-channels.md)
（X→M→Y 机制主张的分类与识别，把中介挡在主设定之外）、
[`references/design-risk-ledger.md`](references/design-risk-ledger.md)（把识别威胁、选择性报告、外部效度、SUTVA/溢出、
attrition 风险落成逐项状态表）、
[`references/analysis-backends.md`](references/analysis-backends.md)（Python/StatsPAI、Stata、R 三种后端选择），
若主后端为 `python-statspai` 还要加载 [`references/statspai-analysis.md`](references/statspai-analysis.md)
（StatsPAI 引擎：MCP 优先拍板+拟合+诊断，`statspai` 包做出版级出表；其七块稳健性闸门正是下面最低证据包的实现入口），并完成：

1. **设计注册**：写 `03_analysis/design_register.md`，明确 estimand、处理定义、比较组、识别假设、
   主估计量、替代估计量和失败回退。
2. **样本审计**：写/刷新 `02_data/sample_audit.md`，确认 estimation sample、treated/control 数、
   treatment timing、missingness/balance/overlap、cluster level 和变量构造与 estimand 对齐。
3. **最低证据包**：按方法分支补齐必需 artifact。交错 DiD 需 CS/SA/BJS 等 group-time 或事件研究稳健
   估计；RDD 需 bandwidth、robust bias-corrected CI、density/covariate continuity；DML/HTE 需
   cross-fitting、nuisance diagnostics、overlap 与 seed stability；其它分支见 methods pack。
   **推断口径与机制**：按 `inference-and-uncertainty.md` 把聚类层级、few-cluster 修正、多重检验校正、
   弱工具区间定死并写 `03_analysis/inference_report.md`；若有机制主张，按 `mechanism-and-channels.md`
   分类（描述性分解 / 因果中介 / 异质性）并把中介移出主设定，机制证据落 `03_analysis/mechanism/`。
4. **方法闸门报告**：写 `03_analysis/method_gate.md`，逐项列出必需证据是否存在、路径在哪里、是否
   `PASS`，并按 `design-gate-cards.md` 填好 **Design Gate Card** 与最强允许 claim 等级。若 `NOT PASS`，
   不得进入 Stage 4；必须按报告回 Stage 1/2/3 修设计、数据或估计。
5. **Design risk ledger**：写/刷新 `03_analysis/design_risk_ledger.md`，逐项审计 OVB、反向因果、选择、
   测量误差、spillover/SUTVA、坏控制、specification search、外部效度、attrition 与多重检验/选择性报告。
   任何 blocking threat 未关掉时，`workflow_state.json.design_risk.status` 必须是 `not_pass`，Method Gate 不得
   标 `PASS`；若风险只限制外推，必须把 claim consequence 写进 ledger 和 evidence ledger。
6. **Evidence ledger**：写/刷新 `00_meta/evidence_ledger.md`，把每个 manuscript claim 连接到 estimand、
   样本审计、结果文件、稳健性、表图、脚本和允许措辞。摘要、引言、结果、结论、cover letter 的 claim
   不得强于 ledger 的 `Strength`。
7. **治理与透明度 hard flags**：同步检查
   [`references/data-governance.md`](references/data-governance.md)（受限数据、PII、IRB/DUA、存档边界）
   与 [`references/design-transparency.md`](references/design-transparency.md)（预分析、MDE、研究者自由度）。
   关键治理或透明度材料缺失时，方法闸门不得静默放行。
8. **写入状态**：更新 `workflow_state.json.analysis_backend`、`empirical_audit`、`method_gate`、
   `evidence_governance`、`design_risk` 与 `decisions`，记录分析后端、主设计、主估计量、适用威胁、blocking
   threats、缺失 artifact、最强 claim 等级、open discrepancies 与是否放行。
9. **机械闸门自检**：跑 `python3 scripts/check_workspace_gates.py <workspace>`，机械校验「某道闸门标了
   `pass`/`ready` 但所需 artifact 不在盘上、或上游闸门未过（质量门不得松于方法闸门）」这类 critic 读 prose
   保证不了的硬不一致；同时检查 Stage 0 route、stage passport 与 latest handoff 的路径一致性。返回非零必须先补齐再放行。
   这是对 critic 主观判定的机械兜底，不替代它。

质量门可以比方法闸门更严，但不能更松：若 `method_gate.md` 未通过，初稿质量门的「识别可信度」不得
达标；若 `evidence_ledger.md` 中存在影响主结论的 open discrepancy，质量门和投稿包不得标 ready。这个约束把现代实证研究的 reviewer 标准前置到写作之前，避免后面用语言包装弥补方法硬伤。

---

## 初稿质量门（Draft Quality Gate）—— 把「高质量」从口号变成可验收的闸门

Stage 7 结束、Stage 8 开始之前，**强制插入一道质量门**。这是本编排器兑现「**高质量**初稿」承诺
的地方：不靠主代理自我感觉良好，而是**派一个独立的「顶刊 AE」critic subagent**，按
[`references/quality-rubric.md`](references/quality-rubric.md) 的 7 维评分卡对当前初稿打分。

**怎么跑（一次 `Agent` 派发，模板见 [`subagent-templates.md`](references/subagent-templates.md) §QG）：**

1. critic subagent 读 `07_dehumanize/main.tex`（含表图、`ref.bib`）+ `01_proposal/proposal.md`（对照
   贡献承诺）+ `03_analysis/results/summary.md`（对照真实结果），**逐维打分并写入
   `00_meta/quality_scorecard.md`**，只向主代理回传「总分 / 各维分 / 是否达标 / 最关键的 3 条短板」。
2. **7 个维度**（满分各 10，细则见 rubric）：① 选题与贡献锋利度 ② 识别可信度 ③ 稳健性完整度
   ④ 结果与解读克制度 ⑤ 写作与结构 ⑥ 引用真实性与文献定位 ⑦ 可复现性。
3. **达标线**：每维 ≥ 7 **且** 总分 ≥ 56/70 **且** 第②③⑥维（识别 / 稳健 / 引用）无任何「致命红
   旗」。三者全满足 → 标记 `quality_gate=pass`、`draft_milestone=done`，进入可选的 Stage 8–9。
4. **未达标 → 按 rubric 的「短板 → 回退阶段」映射退回重做**（识别问题回 Stage 3、贡献单薄回
   Stage 1、写作问题回 Stage 5/6、AI 味回 Stage 7、引用问题回 reference-verify），**最多回退 2 轮**；
   2 轮后仍卡在某维，则在质量门记录「已知短板」并显著标红告知用户，由用户裁决是否带病进入投稿。
5. 每轮打分都追加进 `logs/quality_gate.md`，让用户看到分数如何随修订上升（审计轨迹）。

> 质量门**不是**重跑 Stage 6 的打磨，也不替代 Stage 8 的模拟评审：打磨改语言、评审挑学术硬伤、
> 质量门**只做一件事——按统一 rubric 量化「这份初稿够不够格」并决定放行还是回炉**。它把「高质量」
> 落成一个有阈值、可回退、可审计的闸门。

---

## 收尾：复盘与交付

所有目标阶段 `done` 后（**初稿质量门已 `pass`**），主代理产出 **`FINAL_REPORT.md`**（落在工作区
根目录），含：

- **一页流水线复盘表**：每个 Stage 调用了什么、产出了什么、关键数字、走过哪些回退分支；
- **方法闸门报告**：嵌入或链接 `03_analysis/design_register.md` 与 `03_analysis/method_gate.md`，
  说明主设计、主估计量、最低证据包、缺失/回退历史；
- **初稿质量门评分卡**（嵌入或链接 `00_meta/quality_scorecard.md`）：7 维终评分 + 达标判定 +
  回退历史，证明「高质量」不是自我宣称而是过了闸门；
- **交付物清单**（带相对路径链接）：`proposal.md` / 清洗后数据 + codebook / 分析代码 /
  出版级表图 / `main.tex`+`ref.bib` / response letter / 期刊清单 + cover letter；
- **可复现说明**：`REPLICATION.md`、环境依赖、一键重跑命令、数据来源与版权注记、DAS、存档计划、
  最近一次重跑耗时、数据治理红旗；并更新 `workflow_state.json.replication_pack`；
- **下一步建议**：还差哪些稳健性、投稿前最后检查清单。

最后把交付物打包路径告知用户。**全程不需要人工干预即可从 Setup 跑到交付**（`全自动` 档位）；
其余档位只在阶段闸门处征求放行。

---

## 关键约束（务必遵守）

- **绝不替子 skill 重新发明轮子**。识别策略、表格规范、查新逻辑、审稿口吻……都在既有 skill 里，
  本编排器只负责"在对的时点把对的 skill 喂对的输入"。
- **绝不伪造数据 / 结果 / 文献**。引用核验交给 `reference-verify` / StatsPAI `bibtex`（`paper.bib` 为唯一
  真源）；数据来源交给 `data-fetcher`；计量结论以真实运行结果为准。Stage 3–4 先按
  [`references/analysis-backends.md`](references/analysis-backends.md) 选择 Python/StatsPAI、Stata 或 R 后端；
  默认 Python/StatsPAI 路径见 [`references/statspai-analysis.md`](references/statspai-analysis.md)。
- **绝不贴空方法标签**。DiD / IV / RDD / SDID / DML / causal forest 等标签必须对应
  `research-grade-methods.md` 与 `design-gate-cards.md` 要求的证据包；缺 `method_gate.md`、闸门未过、
  或 evidence ledger 不允许该 claim 强度，就不得把相关结果写成主因果发现。
- **绝不让估计样本漂移**。`sample_audit.md` 未说明 raw→clean→estimation sample 的 N、drop 原因、
  treated/control 数、missingness/balance/overlap 与聚类层级时，不得把结果写成已通过方法闸门。
- **绝不让不确定性量化错位**。聚类层级要至少等于处理分配层级；cluster 少（G≲30–50）要 wild bootstrap /
  CR2 / 随机化推断；多 outcome / 多子样本要预先指定或族内校正；弱工具要 AR/tF 区间——口径写进
  `inference_report.md`，缺则按 [`references/inference-and-uncertainty.md`](references/inference-and-uncertainty.md) 在质量门封顶。
- **绝不把机制当主回归的赠品**。X→M→Y 是独立因果问题：按 [`references/mechanism-and-channels.md`](references/mechanism-and-channels.md)
  分清「描述性分解 / 因果中介 / 异质性」，中介绝不进主设定，措辞退到证据支持的档位。
- **绝不把识别威胁留在散文里**。OVB、反向因果、选择、坏控制、spillover/SUTVA、external validity、
  attrition、specification search 和选择性报告风险必须进
  [`references/design-risk-ledger.md`](references/design-risk-ledger.md) 与 `03_analysis/design_risk_ledger.md`；
  有 blocking threat 时 Method Gate 不能 `PASS`。
- **人类决策点不可跳过**（除非 `全自动` 档位且用户已显式授权）：选题定标题、定目标期刊、识别
  策略拍板、投稿前终审——这些在阶段闸门处守住。
- **数据治理不可绕过**：受限数据、PII、IRB/DUA、许可证、archive boundary 按
  [`references/data-governance.md`](references/data-governance.md) 记录；公共复现包不得包含不可公开材料。
- **运行时退化必须披露**：工具、网络、MCP 或统计软件缺失时按
  [`references/runtime-fallbacks.md`](references/runtime-fallbacks.md) 退化执行；影响最低证据包或复现的，
  必须降低闸门状态/分数。
- **上下文保护优先于一切**：任何会把大段文本灌回主代理的操作，改成"写盘 + 回传摘要"。
- **断点交接必须可恢复**：阶段完成不只更新聊天摘要；必须更新 `00_meta/stage_passport.md`。长期暂停、
  阶段切换或接手前写 `00_meta/handoff/`，并在续跑时用 fresh evidence 重新核当前事实。
- **自我改进不靠训练集幻觉**：维护或改造本 skill 时，按
  [`references/skillopt-improvement-loop.md`](references/skillopt-improvement-loop.md) 收集 rollout、拆分 train /
  held-out selection、提出有界 patch、过 selection gate；不得只凭触发本次修改的样例接受改动。
- **自检不靠感觉**：维护或改造本 skill 时，先后运行 `python3 validate_skill.py` 与仓库级验证；若有
  SkillOpt-style 改进包，还要跑 `python3 scripts/check_skillopt_packet.py <packet>`。若自检失败，必须修到通过再宣称可交付。

---

## 进一步阅读（按需加载，别一次性全读进上下文）

- [`references/stage-playbook.md`](references/stage-playbook.md) — 10 个阶段的逐阶段操作手册
  （含每阶段的 skill 调用、subagent 派发模板、失败回退分支）。
- [`references/skill-map.md`](references/skill-map.md) — 第 0 节是**子 skill 调用机制 + 注册名对照表
  + 输出路径重定向**（编排能否跑通的关键）；其余是「任务 → 用哪个 skill」的全量路由表。
- [`references/statspai-analysis.md`](references/statspai-analysis.md) — **Stage 3–4 的统一估计 + 出版级
  出表引擎**：StatsPAI 两条接入路径（MCP 默认 / `statspai` 包做重活）、8 段流水线 ↔ 阶段映射、三种领域模式
  （应用计量 / 流行病学 / ML 因果）、估计量路由、三格式出表栈、标准图谱、七块稳健性闸门 ↔ 最低证据包、反模式清单。
- [`references/analysis-backends.md`](references/analysis-backends.md) — **Stage 3–4 的三语言后端路由**：
  `python-statspai` / `stata` / `r` 的选择规则、子 skill 调用路径、输出合同、环境记录、交叉验证与 fallback。
- [`references/empirical-audit.md`](references/empirical-audit.md) — **样本、变量与 estimand 对齐层**：
  raw→clean→estimation sample 流失、变量构造、missingness/balance/overlap、cluster/weights 的审计标准。
- [`references/dataset-cards.md`](references/dataset-cards.md) — **Stage 2 选源目录**：经管/社科常用数据源
  （Compustat/CRSP/CSMAR/FRED-MD/IPUMS/PSID/PatentsView/Comtrade/EDGAR…）的覆盖、链接键、已知陷阱与
  **触发的设计风险**；配 [`templates/dataset_card.md`](templates/dataset_card.md) 对每个实际用源实例化项目卡。
- [`references/design-gate-cards.md`](references/design-gate-cards.md) — **设计分支证据卡**：
  DiD/IV/RDD/SC-SDID/Panel FE/DML-HTE/DAG/refuter/预测辅助实证的 required artifacts、hard fail 与 claim 降级规则。
- [`references/quality-rubric.md`](references/quality-rubric.md) — **初稿质量门的 7 维评分卡**：每维
  评分细则、致命红旗清单、达标阈值、「短板 → 回退阶段」映射。
- [`references/subagent-templates.md`](references/subagent-templates.md) — **可直接复制的 subagent
  派发模板**：Stage 1 选题漏斗、Stage 3 稳健性矩阵、各阶段 critic、初稿质量门评分器，均已内置
  上下文保护契约与输出路径重定向。
- [`references/workspace-and-state.md`](references/workspace-and-state.md) — 工作区目录布局、
  `workflow_state.json` 字段含义、subagent 输入/输出文件约定。
- [`references/orchestration-and-handoff.md`](references/orchestration-and-handoff.md) — Stage 0
  入口路由、stage passport、fresh evidence、handoff card 与 schema v9 编排字段。
- [`references/worked-example.md`](references/worked-example.md) — 一条端到端「黄金路径」trace
  （绿色信贷→企业创新）：逐阶段产物、两道闸门如何触发、`NOT PASS → 回退 → PASS` 的完整循环（数字均为
  **示意**，真实运行由真实估计填充）。新人理解整条流水线、编排器照着填空都从这里看起。
- [`references/skillopt-improvement-loop.md`](references/skillopt-improvement-loop.md) — **维护本 skill 的
  SkillOpt-style 优化协议**：rollout 证据、train/held-out split、有界 patch、selection gate、rejected-edit memory。
- **研究深化层（按阶段加载）**：[`references/threats-to-validity.md`](references/threats-to-validity.md)
  （识别威胁 × 审稿异议预案 · Stage 3/5/8）、
  [`references/inference-and-uncertainty.md`](references/inference-and-uncertainty.md)（标准误/聚类层级 ·
  few-cluster 修正 · 随机化推断 · 多重检验 · 弱工具区间 · CI 报告纪律 · Stage 3/4/5/8）、
  [`references/mechanism-and-channels.md`](references/mechanism-and-channels.md)（X→M→Y 机制主张三分类 ·
  Gelbach 分解 · 因果中介 + 敏感性 · 坏控制 · Stage 1/3/5/8）、
  [`references/design-transparency.md`](references/design-transparency.md)（预分析 · 功效/MDE · 预趋势功效 ·
  设定曲线 · 研究者自由度 · Stage 3）、
  [`references/design-risk-ledger.md`](references/design-risk-ledger.md)（识别威胁/选择性报告/外部效度/SUTVA/attrition
  的逐项状态表 · Stage 1/3/5/8）、
  [`references/literature-and-positioning.md`](references/literature-and-positioning.md)（结构化检索 ·
  文献矩阵 · 贡献定位句式 · Stage 1/5）。它们与样本/方法/写作/复现/评审标准合流到两道闸门打分。
- **运行与治理横切层**：[`references/runtime-fallbacks.md`](references/runtime-fallbacks.md)
  （Skill/Agent/网络/MCP/统计软件缺失时的退化路径与质量封顶）、
  [`references/data-governance.md`](references/data-governance.md)（敏感数据、PII、IRB/DUA、授权、
  公开复现包边界）。
- [`templates/`](templates/) — 可复制到工作区的关键 artifact 模板：sample audit、design register、method gate、
  quality scorecard、data governance、DAS、REPLICATION、submission checklist、FINAL_REPORT、run_all。
- [`validate_skill.py`](validate_skill.py) — 本 skill 的本地自检：模板 schema、工作区初始化、Markdown
  本地链接、核心资产、模板契约、smoke workspace 与 DiD Notebook 结构。
- [`scripts/smoke_workspace.py`](scripts/smoke_workspace.py) — 在临时目录生成最小工作区并实例化模板，
  验证 Stage 0 初始化 + 状态文件 + 模板路径契约。
- [`scripts/check_skillopt_packet.py`](scripts/check_skillopt_packet.py) — **维护期 SkillOpt-style 改进包
  机械校验器**：检查 train / held-out selection 证据、edit budget、accept/reject gate 与 placeholder 清理。
- [`scripts/check_workspace_gates.py`](scripts/check_workspace_gates.py) — **运行期闸门机械校验器**：在方法闸门 /
  质量门 / 收尾处跑 `python3 scripts/check_workspace_gates.py <workspace>`，校验某道闸门标了 `pass`/`ready` 时
  所需 artifact 是否真的在盘上、gate 顺序是否一致（质量门不得松于方法闸门）；`--reconcile` 还会核对结果数字与表图。带 `--selftest`。
- 演示物料（可选教学用）：README 已整合原流程讲义的 8 阶段教学主线、47 个技能地图与 DiD 自检清单；
  本仓库另保留一个可一键运行的 DiD 演示 Notebook，适合在讲解本流水线时配合展示。
