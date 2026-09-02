# Paper-WorkFlow 使用指南（详细版）

> 本文是 Paper-WorkFlow 的实操说明，面向第一次用它写论文的人。
> 只讲「怎么用」和「该说什么 prompt」；方法学细节见 [`SKILL.md`](../SKILL.md) 与
> [`references/`](../references/)，逐项闸门清单见 [`RIGOR.md`](../RIGOR.md)。

---

## 一、它是什么（30 秒）

Paper-WorkFlow 是一个**总编排器（meta-orchestrator）**，不是一个「帮你写论文」的聊天助手。

它把一篇经管 / 社科实证论文拆成 **Stage 0–9 + 两道硬闸门**，在每个阶段调用已有的子 skill、
派并行 subagent，并把全部中间产物沉淀到一个**可审计、可断点续跑**的工作区里。

| 你要理解的三件事 | 说明 |
|---|---|
| **它不重写轮子** | 选题、查新、清洗、估计、表图、打磨、去 AI 味、评审、投稿都由既有的 47 个子 skill 完成；它负责在对的时点喂对的输入。 |
| **它有硬闸门** | Stage 3 后的**方法闸门**、Stage 7 后的**初稿质量门**。闸门不过就必须回炉，不允许用文字包装糊过去。 |
| **它不承诺结果** | 「端到端」指覆盖研究链条，不保证数据可得、结果显著、平行趋势通过、论文录用。失败也会写成可审计记录。 |

---

## 二、安装与触发

### 安装

```bash
# 推荐：克隆母仓库（含被编排的 47 个子 skill；本仓库是其中的
# skills/69-Paper-WorkFlow/ 子模块）
git clone --recurse-submodules https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills.git

# 或：只要编排器本体（子 skill 需另行提供）
git clone https://github.com/brycewang-stanford/Paper-WorkFlow.git
```

在 Claude Code 里：**进入母仓库目录直接开聊**即可（仓库根的路由 `SKILL.md` 会注册 `/paper-workflow`）；
或把需要的 `skills/` 子目录放进项目的 `.claude/skills/`（全局则放 `~/.claude/skills/`）。

### 触发方式

三种都行，效果一样：

```text
/paper-workflow <你的材料和诉求>          ← 最稳，显式触发
帮我写一篇实证论文，主题是……                ← 自然语言触发
我有一份 proposal，想从选题一路做到投稿      ← 自然语言触发
```

---

## 三、开跑前，它会一次性问你六件事

理解这六项，你就能在第一条 prompt 里直接写全，省掉一轮问答。

| # | 选项 | 取值 | 建议 |
|---|---|---|---|
| 1 | **交互档位** | `全自动` / `阶段确认` / `全程交互` | 首次跑用 `阶段确认` |
| 2 | **严格度 scope** | `draft` / `working-paper` / `submission` | 内部讨论稿用 `draft`，投稿用 `submission` |
| 3 | **目标期刊** | 如《经济研究》/ *China Economic Review* | 越早定越好，影响 Stage 9 与写作风格 |
| 4 | **稿件语言** | 中文 / 英文 | 与分析后端无关 |
| 5 | **分析后端** | `python-statspai`（默认）/ `stata` / `r` | 手上有 `.dta` 且团队用 Stata 就选 `stata` |
| 6 | **表格格式** | 默认三线表 | 一般不用改 |

**交互档位和 scope 是正交的两个旋钮**：

- 交互档位管**多久停下来问你一次**
  - `全自动`：无人值守，只在最终交付时汇报
  - `阶段确认`（推荐）：每阶段末给一张摘要卡，等你放行才进下一阶段
  - `全程交互`：每个子 skill 跑自己原生的逐项审批，投稿终版用

- scope 管**「做完」的标准是什么**
  - `draft` → 只欠方法闸门
  - `working-paper` → + 设计风险、初稿质量门
  - `submission`（缺省）→ + claim 完整性、数字锚定、复现包

> scope 只决定**这次交付欠哪几道闸门**，**不会放松**任何已声明 `pass` 的闸门的证据验证。
> 少过几道闸门可以；把没过的说成过了不行。

---

## 四、你带什么进来，就从哪一站上车

不用每次从头跑。它会根据你手上已有的材料自动选入口：

| 你带来的 | 入口 |
|---|---|
| 一句话想法 / 一个研究方向 | Stage 1 · 完整选题漏斗 |
| 一份成形 proposal（X→M→Y、识别策略、样本） | Stage 2 · 直接取数 |
| 已清洗数据 + 设计 | Stage 3 · 直接估计 |
| 已有回归结果 / 表图 | Stage 5 · 直接写初稿 |
| 一份 `main.tex` 初稿 | Stage 6 · 直接进打磨流水线 |
| 初稿 + 审稿意见 | Stage 8 · 按意见修订 |
| 一份成稿要投稿 | Stage 9 · 选刊 + 投稿包 |

---

## 五、详细 Prompt 案例

以下每个案例给出**完整可复制的 prompt**、它会做什么、产出什么。
prompt 写得越具体（路径、变量名、设计、期刊、档位），前置问答越少。

---

### 案例 1 · 从一句话想法做到投稿（最完整的一条龙）

**适用**：手上只有研究方向，想看完整流水线。

```text
/paper-workflow

研究方向：绿色信贷政策对企业绿色创新的影响
数据设想：A 股上市公司 2010–2023 年面板，绿色专利数作被解释变量
识别思路：2012 年《绿色信贷指引》作为准自然实验，DiD

目标期刊：《经济研究》
稿件语言：中文
分析后端：python-statspai
交互档位：阶段确认
严格度：submission

请从选题开始，先做查新和文献基座，再往下走。
```

**它会做**：Stage 1 选题漏斗（idea-finder → novelty-check → significance-search → proposal）；
Stage 1L 先建一次文献语料，供查新打分、related work、引用终审三处复用；
然后 Stage 2 取数清洗 → Stage 2.5 设计锁定 → Stage 3 估计 + 方法闸门 → … → Stage 9 投稿包。

**你会看到**：每个阶段末一张摘要卡（产出清单 + 关键数字 + 红旗 + 下阶段计划），等你回「继续」。

---

### 案例 2 · 已有 proposal，直接取数往下跑

**适用**：开题报告 / 计划书已经写好。

```text
/paper-workflow

计划书在 ./proposal.md，里面已经写清楚了 X→M→Y、识别策略和样本范围。
请从 Stage 2 取数开始，一条龙做到投稿。

目标期刊：China Economic Review
稿件语言：英文
分析后端：python-statspai
交互档位：阶段确认
严格度：submission

补充约束：
- 数据只能用公开可得来源（CSMAR/WIND 我有权限，请在数据卡里注明）
- 不要用任何需要付费 API 的文献检索
```

**它会做**：读 proposal → 校验它是否够格当「合同」→ 缺失项一次问清 → 进入数据阶段。

**产出**：`02_data/clean.parquet` + `codebook.md` + `sample_audit.md` + `measurement_audit.md`。

---

### 案例 3 · 数据已清洗，只想跑估计 + 方法闸门（最常用的短跑）

**适用**：想快速拿到一版可信的基准结果 + 稳健性矩阵。

```text
/paper-workflow

数据在 ./data/panel.csv（已清洗），面板结构：firm_id × year，2010–2023。
- 被解释变量：green_patent（绿色专利申请数，计数）
- 处理变量：treat（高污染行业=1）× post（year>=2012）
- 控制变量：size, lev, roa, age, soe
- 固定效应：firm + year
- 聚类层级：industry（约 40 个 cluster）

设计：交错 DiD。请先跑基准，再补齐稳健性矩阵，最后过方法闸门。

分析后端：python-statspai
交互档位：阶段确认
严格度：draft

跑到 Stage 3 方法闸门为止，先不要写稿。
```

**它会做**：Stage 2.5 先锁设计（在第一个估计值出现之前）→ Stage 3 估计 →
按设计卡补齐必需证据（交错 DiD 需要 CS / SA / BJS 等异质性稳健估计量）→
写 `design_register.md`、`inference_report.md`、`design_risk_ledger.md`、`method_gate.md`。

**注意**：cluster 数约 40，它会按 `inference-and-uncertainty.md` 自动上 wild bootstrap / CR2，
并把推断口径写死在 `inference_report.md` 里。

---

### 案例 4 · 换分析后端（Stata / R）

**适用**：团队用 Stata 复现，或期刊要求交 `.do` 文件。

```text
/paper-workflow

数据在 ./data/panel.dta，设计是 DiD（交错处理）。
分析后端用 Stata：所有估计写成可一键重跑的 .do 文件，表格用 esttab 出三线表。
Stata 版本 18，已安装 reghdfe / csdid / eventstudyinteract。

交互档位：阶段确认
严格度：working-paper

跑到表图（Stage 4）为止。
```

R 版本：

```text
/paper-workflow

数据在 ./data/panel.csv，设计 DiD。
分析后端用 R：fixest 估计 + modelsummary 出表 + Quarto 组织脚本。
表格要 LaTeX 和 Word 同出。

交互档位：全自动
严格度：working-paper
```

> 分析后端只决定 Stage 3–4 的脚本和导出工具，**与稿件语言无关**——可以用 Stata 跑、写英文稿。

---

### 案例 5 · 已有结果，只写初稿

**适用**：回归都跑完了，要一份结构完整的 `main.tex`。

```text
/paper-workflow

回归结果和表图已经在 ./results/ 里（regression_main.csv、event_study.png、robustness/）。
研究背景和贡献见 ./notes/idea.md。

请从 Stage 5 开始写初稿：
- 语言：中文
- 目标期刊：《管理世界》，按它的结构惯例组织章节
- 稿件里每一个数字都必须能在 ./results/ 里找到来源，不许自己编

交互档位：阶段确认
严格度：working-paper
```

**它会做**：先把你的结果登记进 `evidence_ledger.md`（claim ↔ 数据 ↔ 估计 ↔ 表图 ↔ 脚本），
再写稿。写完跑 `check_manuscript_numbers.py` 做数字锚定校验——**没来源的数字会被直接拦下**。

---

### 案例 6 · 已有初稿，只做打磨 + 去 AI 味

**适用**：稿子写完了，读起来一股 AI 味 / 结构松散。

```text
/paper-workflow

初稿在 ./paper/main.tex，参考文献在 ./paper/ref.bib。
从 Stage 6 开始：
1. 先做结构层打磨（段落及以上：逻辑链、主题句、章节配比）
2. 再做语言层去 AI 味（句子及以下，中英双语六步闭环）
3. 最后过初稿质量门，给我 7 维评分卡

硬要求：只改语言和结构，一个数字都不许动。
交互档位：阶段确认
严格度：working-paper
```

**它会做**：Stage 6 跑 `paper-pipeline` 全量基线（polish → self-revise → style → polish → reference-verify）；
Stage 7 跑去 AI 味六步闭环 + 可读性收尾；
然后**机械校验 Stage 6→7 零数字漂移**，再派一个独立「顶刊 AE」critic 按 7 维打分。

**产出**：`00_meta/quality_scorecard.md`（7 维评分 + 是否放行 + 最关键 3 条短板）。

---

### 案例 7 · 收到审稿意见，做修订 + response letter

**适用**：R&R 或拒稿后改投。

```text
/paper-workflow

- 稿件：./revision/main.tex
- 审稿意见：./revision/referee_1.pdf、referee_2.pdf、AE_letter.pdf
- 原投期刊：《经济研究》，结果是 R&R

请从 Stage 8 开始：
1. 把每条意见拆成可执行 action item，标注「需要重跑分析 / 只需改写 / 需要辩护不改」
2. 需要重跑的部分回 Stage 3 补做，跑完更新表图
3. 逐条写 response letter，中文，语气克制、逐条对应
4. 最后给我一份修订前后对照表

交互档位：全程交互
严格度：submission
```

**它会做**：`referee-report` 解析意见 → `paper-referee-revise` 修订 →
需要新证据的回退到 Stage 3 并重新过方法闸门 → 生成 response letter。

---

### 案例 8 · 成稿了，只做选刊 + 投稿包

**适用**：稿子定稿，要选刊、写 cover letter、准备投稿材料。

```text
/paper-workflow

稿件已定稿：./final/main.tex + ref.bib，主题是绿色信贷与企业创新（中文实证）。
从 Stage 9 开始：
1. 给我 8 本候选期刊，按 fit / 影响力 / 审稿周期 / 录用难度排序，说明推荐理由
2. 对前 3 本做期刊专属预检（格式、字数、结构、伦理与数据政策）
3. 写 cover letter（中文）
4. 跑引用终审：每一条参考文献都要验证真实存在、引对、无时序穿越
5. 按目标刊政策渲染 AI 使用声明

交互档位：阶段确认
严格度：submission
```

**产出**：`09_submission/` 下的期刊清单、逐刊预检报告、cover letter、`submission_checklist.md`、`DAS.md`。

---

### 案例 9 · 无人值守跑一版工作论文

**适用**：晚上挂机，第二天看结果。

```text
/paper-workflow

./proposal.md + ./data/panel.csv 都在。
全自动模式，严格度 working-paper，分析后端 python-statspai，中文稿。
不要中途问我任何问题：需要拍板的地方按保守缺省走，把所有假设写进
00_meta/entry_routing.md 和 decisions，最后一次性汇报。

如果方法闸门过不了，不要硬往下写——停在那里，把「为什么过不了、缺什么证据」
写清楚给我。
```

> ⚠️ `全自动` 的唯一风险是在一个永远过不了的闸门上打转。skill 内置了
> `revision_rounds_cap` / `method_gate_rounds_cap`（各缺省 2），触顶后按
> `deliver-with-known-gaps` 交付并标红，不会无界循环。

---

### 案例 10 · 断点续跑（第二天接着做）

**适用**：上次跑到一半，换了 session 或改了主意。

```text
/paper-workflow

继续上次的工作区：./paper_workspace/green_credit_20260901-1430/
先读 00_meta/stage_passport.md 和最新的 handoff card，再核对盘上真实产物和
git status，确认现在到底做到哪一步（不要只信 handoff）。

确认后从下一个未完成阶段继续。如果上次卡在方法闸门，先告诉我缺哪几项证据。
```

**它会做**：passport + handoff 只当指针，**必须重新核对盘上事实**（fresh evidence）才能宣称某阶段已完成。

---

## 六、运行中你会看到什么

### 阶段横幅

每进一个阶段会打一条横幅，你随时知道流水线在哪：

```text
════════════════════════════════════════
  Stage 3/9 · 计量识别、估计与方法闸门  —  把设计与证据落成可审计产物
  调用：did-analysis, empirical-audit, methods-pack
════════════════════════════════════════
```

### 阶段摘要卡（`阶段确认` 档位）

每阶段末给你：**产出清单 + 关键数字 + 红旗 + 下阶段计划**，等你放行。

### 硬阻断会显著标红

平行趋势不过、IV 弱工具、查新撞车、数据取不到 —— 它**不会硬往下走**，
而是走「失败回退」分支，并在摘要卡里标红说明发生了什么、做了什么回退。

---

## 七、两道硬闸门（这是它区别于「让 AI 写论文」的地方）

### 方法闸门（Method Gate）· Stage 3 之后、Stage 4 之前

必须齐的东西：

1. **设计锁前置**：`design_lock.status=locked` 且 `locked_before_estimation=true`
   —— 设计没锁不许开始估计；事后补的锁不算锁
2. **设计注册** `design_register.md`：estimand、处理定义、比较组、识别假设、主/替代估计量、失败回退
3. **样本审计** `sample_audit.md`：raw→clean→estimation 的 N、drop 原因、treated/control 数、
   missingness / balance / overlap、聚类层级
4. **按设计的最低证据包**（交错 DiD → CS/SA/BJS group-time；RDD → bandwidth + robust bias-corrected CI +
   密度检验 + 协变量连续性；IV → 弱工具 AR/tF 区间；等等）
5. **设计风险总账** `design_risk_ledger.md`：OVB、反向因果、选择、坏控制、spillover/SUTVA、
   外部效度、attrition、specification search 逐项关掉或降级
6. **证据总账** `evidence_ledger.md`：每条 claim → estimand → 结果文件 → 稳健性 → 表图 → 脚本 → 允许措辞

**未过不得进 Stage 4。**

### 初稿质量门（Draft Quality Gate）· Stage 7 之后、Stage 8 之前

**机械前置**（先跑，不过就直接不用打分）：

- `check_manuscript_numbers.py`：每个系数 / 标准误 / 样本量都要能在结果文件里按显示精度找到来源；
  Stage 6→7 只改语言不改数字，**零漂移**
- `check_ai_disclosure.py`：去 AI 味可以抹掉 AI 腔，**不能抹掉 AI 声明**

**7 维评分**（独立「顶刊 AE」critic subagent 打分，各满分 10）：

① 选题与贡献锋利度 ② 识别可信度 ③ 稳健性完整度 ④ 结果与解读克制度
⑤ 写作与结构 ⑥ 引用真实性与文献定位 ⑦ 可复现性

**达标线**：每维 ≥7 **且** 总分 ≥56/70 **且** ②③⑥ 无致命红旗 **且** claim 完整性审计无 blocking finding。

未达标按「短板 → 回退阶段」映射重做，最多 2 轮。

---

## 八、工作区结构与手动检查

所有产物在 `paper_workspace/<研究短名>_<时间戳>/`：

```text
00_meta/          workflow_state.json（唯一权威进度）、intake、entry_routing、
                  stage_passport、pipeline_status、handoff/、quality_scorecard、
                  evidence_ledger、claim_integrity_audit、ai_use_disclosure
01_proposal/      proposal.md（后续所有阶段的「合同」）+ lit/
02_data/          clean.parquet + codebook.md + sample_audit.md
03_analysis/      design_register.md + method_gate.md + design_risk_ledger.md
                  + inference_report.md + results/ + robustness/
04_results/       *.tex / *.docx / *.xlsx + *.pdf / *.png（出版级表图）
05_draft/         main.tex + ref.bib
06_polish/  07_dehumanize/  08_review/  09_submission/
REPLICATION.md + run_all.sh     复现包 + 一键重跑
logs/  backups/                 审计轨迹 + 每阶段快照（回滚路径）
FINAL_REPORT.md                 全程复盘 + 交付清单
```

### 自己动手查闸门

不想信它的自述？直接跑机械校验（在本仓库根目录下）：

```bash
python3 scripts/pw.py list                      # 看完整的 stage → gate 映射
python3 scripts/pw.py plan 3                    # Stage 3 欠哪些闸门
python3 scripts/pw.py enter 3 <workspace>       # Stage 3 能不能开工（前置条件）
python3 scripts/pw.py exit  3 <workspace>       # Stage 3 做完没有（退出闸门）
python3 scripts/pw.py check <workspace>         # 当前阶段及之前欠的所有闸门
python3 scripts/pw.py final <workspace>         # 投稿终审全扫
```

返回非零 = 有闸门没过。加 `-v` 看每个 checker 的完整输出，加 `--json` 拿机器可读结果。

---

## 九、中途干预的常用 prompt 片段

流水线跑起来之后，你随时可以插话。以下都是有效指令：

```text
# 改档位
后面全部改成全自动，不用再问我了。

# 改 scope
scope 降到 draft，我只要一版内部讨论稿，方法闸门过了就交付。

# 质疑某个结果
Stage 3 的平行趋势检验我不认可，把事件研究图的 pre-trend 系数和置信区间列给我看。

# 要求补稳健性
再补三个稳健性：① 替换被解释变量为专利授权数 ② 剔除 2015 年股灾样本
③ 用 PSM-DiD 重做，全部并行跑。

# 要求解释闸门为什么没过
方法闸门为什么是 NOT PASS？逐项列出缺哪些证据、各自要怎么补。

# 只看状态不干活
读 00_meta/pipeline_status.md，用一段话告诉我现在做到哪、下一步是什么。

# 回退重做
Stage 5 的引言写得太满，claim 强于证据。回 Stage 5 重写，
措辞不许强于 evidence_ledger 里的 Strength 等级。

# 换目标期刊
目标期刊从《经济研究》改成《中国工业经济》，把 Stage 9 的预检重跑一遍。
```

---

## 十、注意事项 / 常见坑

| 现象 | 原因与处理 |
|---|---|
| **它一直在问问题** | 交互档位是 `全程交互`。改成 `阶段确认` 或 `全自动`。 |
| **卡在方法闸门反复回炉** | 通常是识别设计本身有硬伤（平行趋势、弱工具）。让它列缺失证据，人来拍板改设计还是降级 claim。 |
| **稿件里的数字对不上** | 这是设计如此：数字漂移只能**把稿件改回结果值**，绝不允许反过来改结果文件迁就稿件。 |
| **子 skill 报 not found** | 正常。它会自动退回「`Read` 那份 SKILL.md 并按它执行」的稳路径，不会凭记忆脑补。 |
| **想跑完整流程但只 clone 了独立仓库** | 独立仓库只有编排器本体，47 个子 skill 在母仓库里。用 `--recurse-submodules` 克隆母仓库。 |
| **网络 / MCP / Stata 不可用** | 按 `runtime-fallbacks.md` 退化执行，并**必须披露**——影响证据包的会降低闸门状态，不会伪装成已验证。 |

### 三条绝对不能绕的红线

1. **绝不伪造数据 / 结果 / 文献** —— 引用交给 `reference-verify`，结论以真实运行为准
2. **绝不在没锁设计的情况下开始估计** —— 事后补的锁让选择性报告不可检验
3. **AI 使用必须声明** —— 去 AI 味是去掉 AI 腔，不是隐瞒 AI 参与；AI 永远不能署名

---

## 十一、延伸阅读

| 想了解 | 读哪份 |
|---|---|
| 完整编排逻辑 | [`SKILL.md`](../SKILL.md) |
| 逐阶段操作手册 | [`references/stage-playbook.md`](../references/stage-playbook.md) |
| 47 个子 skill 调用表 | [`references/skill-map.md`](../references/skill-map.md) |
| 工作区与状态字段语义 | [`references/workspace-and-state.md`](../references/workspace-and-state.md) |
| 按设计的证据卡 | [`references/design-gate-cards.md`](../references/design-gate-cards.md) |
| 质量门 7 维细则 | [`references/quality-rubric.md`](../references/quality-rubric.md) |
| 一个跑通的完整例子 | [`references/worked-example.md`](../references/worked-example.md) |
| 39 项可执行闸门清单 | [`RIGOR.md`](../RIGOR.md) |
| 英文说明 | [`README.en.md`](../README.en.md) |
