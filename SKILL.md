---
name: paper-workflow
description: >
  经管 / 社科**实证论文全流程总编排器（meta-orchestrator）**：把「选题 → 设计 → 数据 →
  计量识别与估计 → 表与图 → 写作初稿 → 全流程打磨 → 语言去 AI 味 → 模拟评审与修订 →
  选刊与投稿 → 复盘交付」这条端到端流水线自动跑通。本 skill **不重复实现任何子能力**，
  而是借鉴 `do-agent` 的「多代理 + 上下文保护」执行范式与 `paper-pipeline` 的「固定顺序 +
  可断点续跑 + 交互档位」编排范式，按阶段**调用既有 skill / 派发并行 subagent** 完成一篇
  可投稿的实证论文。触发场景：用户说 "/paper-workflow"、"帮我写一篇实证论文"、
  "从选题到投稿"、"实证论文全流程"、"经管社科论文工作流"、"端到端跑一篇 paper"、
  "automate an empirical paper"、"end-to-end empirical research pipeline"、"paper workflow"，
  或带着一个研究方向 / 一份计划书 / 一份数据 / 一份初稿希望「一条龙」推进到投稿。
allowed-tools: Skill, Agent, Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, WebSearch, WebFetch, NotebookEdit
argument-hint: "[研究方向 | proposal.md | 数据路径 | main.tex 目录] [目标期刊(可选)]"
---

# Paper-WorkFlow — 经管 / 社科实证论文全流程总编排器

## Overview

这是一个 **meta-orchestrator（总编排器）**。它的职责不是亲自完成研究的每一步，而是把一篇
实证论文从无到有需要的所有环节，编排成一条 **10 个阶段（Stage 0–9）** 的可控流水线，每个
阶段都通过 **`Skill` 工具调用既有 skill** 或 **`Agent` 工具派发并行 subagent** 来完成，主
代理只负责**规划、路由、状态跟踪、阶段间审阅与交付**。

它站在两套成熟范式的肩膀上：

- **`do-agent` 的多代理 + 上下文保护范式**（本仓库授权模仿）：子代理**自己把产出写盘**、
  只向主代理**回传状态摘要**，绝不回传完整内容；主代理上下文极其稀缺，必须做上下文工程。
- **`paper-pipeline` 的固定顺序 + 可断点续跑 + 交互档位范式**：用 `workflow_state.json`
  记录进度，每阶段有横幅、有快照备份、可中断后从断点恢复；开跑前一次性问清交互档位。

> **核心纪律：能调用就不要重写。** 本仓库 `skills/67-econfin-workflow-toolkit/` 已经提供了
> 覆盖全流程的 47 个 skill；本编排器的价值在于**把它们按正确顺序、用正确的上下文、在正确
> 的人类决策点串起来**，而不是复制它们的逻辑。每个阶段「调用哪个 skill」见
> [`references/skill-map.md`](references/skill-map.md)，「每阶段怎么跑」见
> [`references/stage-playbook.md`](references/stage-playbook.md)。

---

## 这条流水线（固定主线，可按入口跳入）

| Stage | 阶段 | 主要调用的 skill（位于 `67-econfin-workflow-toolkit/`，除非另注） | 产出落盘 |
|---|---|---|---|
| **0** | Intake & Setup | *(编排器本体)* | 工作区、`workflow_state.json`、入口路由 |
| **1** | 选题与设计 | `econfin-idea-finder` → `novelty-check` → `significance-search` → `journal-digest` → `econfin-proposal` | `01_proposal/proposal.md` |
| **2** | 数据 | `data-fetcher` → `data-cleaning` | `02_data/clean.parquet` + `codebook.md` |
| **3** | 计量识别与估计 | 按设计择一：`did-analysis` / `iv-estimation` / `rdd-analysis` / `synthetic-control` / `panel-data` / `ols-regression` / `time-series` / `ml-causal`（+ StatsPAI MCP） | `03_analysis/` 代码 + 原始结果 |
| **4** | 表与图 | `table` + `figure` | `04_results/*.tex` + `*.pdf/png` |
| **5** | 写作初稿 | `paper-writer` | `05_draft/main.tex` + `ref.bib` |
| **6** | 全流程打磨 | `paper-pipeline`（内部跑 polish→self-revise→style→polish→reference-verify） | 打磨后的 `main.tex` |
| **7** | 语言与去 AI 味 | `readability` / `fix-chinese` + （`44`/`47`/`48`/`49` 去 AIGC 集合） | 去味后的稿件 |
| **8** | 模拟评审与修订 | `referee-report` → `paper-referee-revise`（或 `paper-self-revise`） | 修订稿 + response letter |
| **9** | 选刊与投稿 | `paper-submission` + `reference-verify`（终审） | 期刊清单 + cover letter |
| **—** | 复盘与交付 | *(编排器本体)* | `FINAL_REPORT.md` + 打包交付物 |

> 完整阶段细节、每阶段的 plan→execute→review→revise 微循环、subagent 派发模板，全部在
> [`references/stage-playbook.md`](references/stage-playbook.md)。**主代理在进入某阶段时才去读
> 对应章节**（渐进式加载，省上下文）。

---

## Phase 0：Setup（在调用任何子 skill 之前，把下面这些全部做完）

1. **取北京时间**。`Bash: TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M'`，记为 `NOW`，用于命名与
   状态文件。（沿用 `do-agent` 的「先取日期时间」纪律。）

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
   07_dehumanize/ 08_review/ 09_submission/ logs/ backups/`）。若同名目录已存在，**另建新目录、
   绝不覆盖**（`do-agent` 纪律）。完整布局见
   [`references/workspace-and-state.md`](references/workspace-and-state.md)。

4. **一次性问清三件套**（用一个 `AskUserQuestion`，多选/多题，避免来回打断）：
   - **交互档位**：`全自动`（只在最终交付时汇报）/ `阶段确认`（**推荐缺省**：每阶段末给摘要、
     等放行再进下一阶段）/ `全程交互`（每个子 skill 跑自己原生的逐项审批，投稿前终版用）。
     —— 这个选择就是各子 skill「快速通道」所需的**显式 opt-in**。
   - **目标期刊**（Stage 1/6/9 都要用，提前问以免中途卡住）：给 JF/JFE/RFS/MS/QJE/AER/
     《经济研究》/《管理世界》等常见项 + "Other" 自由填；也可填「暂不确定，由 Stage 1 推荐」。
   - **语言**：英文稿 / 中文稿 / 中英双语 —— 决定 Stage 7 走 `readability` 还是 `fix-chinese`+
     去 AIGC 集合，以及 Stage 5/6 的写作规范。

5. **写状态文件** `00_meta/workflow_state.json`（复制
   [`assets/workflow_state.template.json`](assets/workflow_state.template.json) 后填写）。填入
   `project.{short_name, created_at_beijing=NOW, entry_stage, mode, target_journal, language}`，
   并把每个 Stage 置为 `pending|in_progress|done|skipped`（字段含义见
   [`references/workspace-and-state.md`](references/workspace-and-state.md)）。**每个阶段开始置
   `in_progress`、完成置 `done`，并刷新 `last_updated_beijing`**——这就是断点续跑的依据。

6. **断点续跑检查**。若工作区已存在 `workflow_state.json` 且有未完成阶段，展示进度并询问：
   从第一个未完成阶段继续，还是重头来？（与 `paper-pipeline` 一致。）

7. **不要为「计划」单独求批准**。Setup 完成后，**直接建任务跟踪并开跑**（`do-agent` 纪律：
   规划阶段结束即执行）。人类决策点交给「阶段确认 / 全程交互」档位去守，而不是在开跑前反复确认。

---

## 多代理 + 上下文保护协议（贯穿所有阶段，源自 `do-agent`）

主代理上下文是**最稀缺资源**。任何"重读大文件、跑长代码、扫一堆文献"的脏活累活，都**派给
subagent（`Agent` 工具）或交给子 skill**，主代理只持有指针与状态。硬规则：

1. **子代理自己写盘，只回传状态摘要**。给每个 subagent 显式指定它的**输入文件**和**输出文件**，
   要求它"处理完立即把结果写到指定文件，只向主代理回传 ≤10 行的状态摘要（做了什么、写到哪、
   关键数字、是否通过、下一步建议）"。**严禁把完整产出回传主代理。**
2. **主代理为子代理放行 Read + Write + Bash**（必要时含 Skill），让它能独立完成闭环。
3. **能并行就并行**。同一阶段内彼此独立的任务（如多个稳健性检验、多个候选期刊匹配、多份机制
   检验）一次性并行派发（每批 ≤10 个 subagent，参考 `do-agent` 的 10-agent 上限与
   `idea-finder` 的 `PARALLEL_BATCH_SIZE=5`）。有依赖的串行。
4. **每阶段是一个 `do-agent` 微循环**：`plan（规划/收集） → execute（执行/整合） →
   review（审阅/挑错） → revise（按审阅修订）`。重活阶段（1 选题、3 估计、6 打磨、8 评审）尤其
   要派一个**独立 critic subagent** 做对抗式审阅，再据其反馈修订。
5. **子 skill 的调用方式**：轻量、需要主线上下文的（如 `paper-style` 要顺着同一份 `main.tex`）
   直接用 `Skill` 工具在主代理里跑；重量、可隔离的（如多路文献扫描、批量稳健性）派 subagent，
   并在 subagent 的 prompt 里**强制要求它 `Skill` 调用对应子 skill**（参考 `idea-finder` 让每个
   subagent 强制加载 `econfin-proposal`+`novelty-check` 的做法）。
6. **日志**：每阶段把"调用了哪些 skill / 派了哪些 agent / 产出了哪些文件 / 关键决策"追加到
   `logs/stage_<N>.md`，作为复盘与续跑的审计轨迹。

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
   关键产物快照进 `backups/after_stage<N>/`，作为回滚路径。

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

## 收尾：复盘与交付

所有目标阶段 `done` 后，主代理产出 **`FINAL_REPORT.md`**（落在工作区根目录），含：

- **一页流水线复盘表**：每个 Stage 调用了什么、产出了什么、关键数字、走过哪些回退分支；
- **交付物清单**（带相对路径链接）：`proposal.md` / 清洗后数据 + codebook / 分析代码 /
  出版级表图 / `main.tex`+`ref.bib` / response letter / 期刊清单 + cover letter；
- **可复现说明**：环境依赖、一键重跑命令、数据来源与版权注记；
- **下一步建议**：还差哪些稳健性、投稿前最后检查清单。

最后把交付物打包路径告知用户。**全程不需要人工干预即可从 Setup 跑到交付**（`全自动` 档位）；
其余档位只在阶段闸门处征求放行。

---

## 关键约束（务必遵守）

- **绝不替子 skill 重新发明轮子**。识别策略、表格规范、查新逻辑、审稿口吻……都在既有 skill 里，
  本编排器只负责"在对的时点把对的 skill 喂对的输入"。
- **绝不伪造数据 / 结果 / 文献**。引用核验交给 `reference-verify`；数据来源交给 `data-fetcher`；
  计量结论以真实运行结果为准（可用 StatsPAI MCP 链路：`detect_design → preflight → recommend →
  fit(as_handle) → audit_result → sensitivity_from_result → bibtex`）。
- **人类决策点不可跳过**（除非 `全自动` 档位且用户已显式授权）：选题定标题、定目标期刊、识别
  策略拍板、投稿前终审——这些在阶段闸门处守住。
- **上下文保护优先于一切**：任何会把大段文本灌回主代理的操作，改成"写盘 + 回传摘要"。

---

## 进一步阅读（按需加载，别一次性全读进上下文）

- [`references/stage-playbook.md`](references/stage-playbook.md) — 10 个阶段的逐阶段操作手册
  （含每阶段的 skill 调用、subagent 派发模板、失败回退分支）。
- [`references/skill-map.md`](references/skill-map.md) — 「任务 → 用哪个 skill」的全量路由表，
  覆盖本仓库 69 个集合里所有跟实证论文相关的能力。
- [`references/workspace-and-state.md`](references/workspace-and-state.md) — 工作区目录布局、
  `workflow_state.json` 字段含义、subagent 输入/输出文件约定。
- 演示物料（可选教学用）：[`../Paper-WorkFlow/`](../Paper-WorkFlow/) 有一份 30 页流程 PPTX
  与一个可一键运行的 DiD 演示 Notebook，适合在讲解本流水线时配合展示。
