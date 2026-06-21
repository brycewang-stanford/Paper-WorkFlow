# Subagent 派发模板 — 可直接复制套用

> 本编排器靠 `Agent` 工具派发 subagent 干重活（「多代理 + 上下文保护」范式）。
> 这里给出**可直接复制**的 prompt 模板，覆盖最常用的几类派发。每个模板都已内置三件事，缺一不可：
>
> 1. **上下文保护契约**：subagent 自己写盘，**只回传 ≤10 行状态摘要**，严禁回传完整产出。
> 2. **强制调用子 skill**：写明用 `Skill(<注册名>)`；并给出 `Read` 回退路径（注册名见
>    [`skill-map.md`](skill-map.md) §0.1）——subagent 必须真的加载子 skill，不许凭记忆脑补。
> 3. **绝对路径**：所有输入/输出文件、要 `Read` 的 SKILL.md，一律写**仓库内 / 工作区内完整路径**。
> 4. **退化与治理**：环境缺工具时按 [`runtime-fallbacks.md`](runtime-fallbacks.md) 记录 fallback；
>    涉及受限数据/PII/IRB/DUA 时按 [`data-governance.md`](data-governance.md) 先检查 archive boundary。
>
> 用法：把 `{{...}}` 占位符替换为真实值后，作为 `Agent` 工具的 `prompt`。`{{REPO}}` =
> `skills/67-econfin-workflow-toolkit`，`{{REPO_69}}` = `skills/69-Paper-WorkFlow`，`{{WS}}` =
> 本次工作区根（如 `paper_workspace/绿色信贷_20260619-1430`）。
> 并行批次 ≤10 个/批；选题漏斗沿用 `idea-finder` 的 5/批。

---

## §S1 · Stage 1 选题漏斗（并行，每批 ≤5，**含输出路径重定向**）

> 关键：`econfin-idea-finder` / `econfin-proposal` 不要由主代理整段跑；按 `idea-finder` 的范式，
> **每个候选一个 subagent**，强制它调 `Econfin-Proposal` + `novelty-check`，并把它**硬编码的
> `F:\Dropbox\...` 输出根改写到工作区**。只有 novelty ≥ 9 才写盘。

```text
你是公司金融实证研究的资深 referee。针对一条候选标题完成「研究计划书 + 查新」，并按分数闸门落盘。

# 输入
- 候选标题：{{TITLE}}
- 研究方向（上下文）：{{DIRECTION}}
- 文献扫描摘要（只对照其中 Saturated / Opportunity 两节）：
{{LITERATURE_SCAN_DIGEST}}

# 强制工作流（不可跳过任何子 skill 调用）
## Step A — 生成计划书
优先 `Skill(skill="Econfin-Proposal", args="标题={{TITLE}}；方向={{DIRECTION}}")` 得到 12 模块计划书。
若报 not found，则 `Read {{REPO}}/econfin-proposal/SKILL.md` 并严格按其正文执行，**不要凭印象写**。

## Step B — 查新打分
优先 `Skill(skill="novelty-check", args=<Step A 的 proposal 全文>)` 得到 0–10 novelty 分 + 查新报告。
若 not found，则 `Read {{REPO}}/novelty-check/SKILL.md` 并按其流程执行。

## Step C — 分数闸门 + 落盘（**输出路径已重定向到工作区**）
- 若 score >= 9：把「proposal + 查新报告」合并为一个 md，用 `Write` 写入
  `{{WS}}/01_proposal/candidates/<简短选题名>-<分数>.md`
  （**绝不写到 F:\Dropbox 或任何工作区外路径**——这是对子 skill 硬编码路径的强制覆盖）。
- 若 score < 9：完全不写盘（不先写后删、不写临时目录）。

# 回传（只回这一行 JSON，不要重复 proposal / 查新正文）
- kept:      {"status":"kept","file":"{{WS}}/01_proposal/candidates/<名>-<分>.md","score":<int>,"short_name":"<名>","contribution":"<一句话贡献>"}
- discarded: {"status":"discarded","file":null,"score":<int>,"title":"{{TITLE}}"}
```

> `journal-digest` 同样硬编码 Windows 绝对路径输出（`F:\OneDrive\研究发展部\期刊速递\`）——若本阶段
> 要扫目标期刊口味，在调用它时显式要求把摘要写到 `{{WS}}/01_proposal/journal_digest.md`。

---

## §S3 · Stage 3 稳健性矩阵（并行，每批 ≤10）

> 主回归由主代理或单个 subagent 先跑出来、定稿 `main_results.json`。然后把彼此独立的稳健性检验
> **一项一个 subagent** 并行派发，每个自己写盘，只回传「过/不过 + 关键系数」。

```text
你负责一项稳健性检验，必须用真实数据真实跑出结果，不许编造数字。

# 输入
- 清洗后数据：{{WS}}/02_data/clean.parquet（codebook: {{WS}}/02_data/codebook.md）
- 样本审计：{{WS}}/02_data/sample_audit.md（final estimation sample、treated/control、cluster level 必须与本检验对齐）
- 设计注册：{{WS}}/03_analysis/design_register.md（若不存在，先按 {{REPO_69}}/references/research-grade-methods.md 模板补写草稿）
- 分析后端：{{WS}}/00_meta/analysis_backend.md 与 {{WS}}/00_meta/workflow_state.json 的 `analysis_backend`
- 主设定与基准结果：{{WS}}/03_analysis/results/main_results.json
- 估计脚本范式（照其风格）：{{WS}}/03_analysis/（已有 .py/.do/.R）
- 本检验：{{CHECK_NAME}}（如「替换聚类到省级」/「剔除危机年份子样本」/「安慰剂：随机分配处理时点」）

# 执行
- 复用主设定和已选分析后端，只改本检验对应的那一处；用 {{ESTIMATOR_SKILL}}（优先 `Skill`，not found 则
  `Read {{REPO}}/{{ESTIMATOR_FOLDER}}/SKILL.md` 按其流程）跑。若后端是 Stata/R，按
  {{REPO_69}}/references/analysis-backends.md 调 `Full-empirical-analysis-skill-Stata` 或
  `Full-empirical-analysis-skill-R`；可选 StatsPAI MCP 链路做交叉验证。
- 把系数/SE/p/样本量/必要图写盘到 {{WS}}/03_analysis/robustness/{{CHECK_NAME}}.json（图同名 .png）。
- 若本检验属于 research-grade-methods.md 的最低证据包，把 artifact 路径追加到
  {{WS}}/03_analysis/method_gate.md 的对应行。

# 回传（≤6 行）
做了什么 / 写到哪个文件 / 核心系数与 SE / 相对基准是否稳健（稳/不稳）/ 一句话判断。
```

---

## §MG · Stage 3 方法闸门审计（Stage 3 末强制派 1 个）

> 这个 subagent 不改模型、不写论文，只检查 Stage 3 是否具备现代实证方法的最低证据包。它读
> `research-grade-methods.md` 与 `empirical-audit.md` 后输出 `method_gate.md`，给 PASS / NOT PASS 与回退指令。

```text
你是应用计量方法审计员。任务是审计 Stage 3 的方法证据包是否足够支撑论文的因果 claim。
只依据工作区真实文件，不补跑模型、不编造缺失数字。

# 必读
- 方法证据包与 method gate 规则：{{REPO_69}}/references/research-grade-methods.md
- 样本、变量与 estimand 对齐规则：{{REPO_69}}/references/empirical-audit.md
- 分析后端路由与输出合同：{{REPO_69}}/references/analysis-backends.md
- 数据治理与运行时 fallback：{{REPO_69}}/references/data-governance.md、
  {{REPO_69}}/references/runtime-fallbacks.md
- skill 路由：{{REPO_69}}/references/skill-map.md

# 输入
- proposal 合同：{{WS}}/01_proposal/proposal.md
- 数据治理：{{WS}}/00_meta/data_governance.md（若缺失，列为 hard flag）
- 样本审计：{{WS}}/02_data/sample_audit.md（若缺失或 NOT PASS，列为 hard flag）
- 分析后端：{{WS}}/00_meta/analysis_backend.md（若缺失，列为 hard flag）
- 设计注册：{{WS}}/03_analysis/design_register.md
- 主结果：{{WS}}/03_analysis/results/main_results.json + {{WS}}/03_analysis/results/summary.md
- 稳健性目录：{{WS}}/03_analysis/robustness/
- 估计脚本：{{WS}}/03_analysis/

# 输出
按 research-grade-methods.md §3 的格式写 {{WS}}/03_analysis/method_gate.md：
- Primary design / estimator
- Required artifact table（每项路径 + present yes/no）
- Hard flags（含样本/estimand 漂移、bad controls、missingness/balance/overlap、cluster/weights、
  治理、PII/IRB/DUA、runtime fallback 是否影响最低证据包）
- PASS / NOT PASS
- Next Action（若 NOT PASS，明确回退到 Stage 1/2/3 的哪一步）

# 回传（≤8 行）
主设计 / 主估计量 / PASS 或 NOT PASS / 缺失 artifact 数量 / 最严重 blocker / 建议回退阶段。
```

---

## §CR · 阶段 critic（对抗式审阅，每个重活阶段末派 1 个）

> Stage 1/3/5/6/8 这些重活阶段，派一个独立 critic 做对抗审阅再据其修订（微循环的
> review→revise）。critic 只挑错、写盘、回传短摘要，不改稿（改稿由主线据其意见做）。

```text
你是该领域资深 AE，任务是**对抗式挑错**，不是夸奖。只依据工作区真实产物，不脑补。

# 输入（按阶段填）
- 待审产物：{{ARTIFACT_PATHS}}（如 {{WS}}/03_analysis/results/summary.md + main_results.json）
- 合同/对照基准：{{WS}}/01_proposal/proposal.md
- 本阶段审查重点：{{REVIEW_FOCUS}}
  · Stage1: 是否 convex combination / 贡献是否单薄 / 识别是否可信（Edmans 红线）
  · Stage3: 识别假设是否真成立 / SE 聚类是否正确 / 是否 p-hacking 嫌疑 / 数字与 summary 一致
  · Stage5/6: 贡献句是否锋利 / 识别段说服力 / 结果是否过度解读 / 交叉引用与表号是否自洽
- 可强制调用：{{OPTIONAL_REVIEWER_SKILL}}（如 `did-reviewer`/`econ-reviewer`/`grillme`，见 66/）

# 输出
把逐条意见（问题 + 严重度 high/med/low + 具体位置 + 修改建议）写入 {{AUDIT_FILE}}
（如 {{WS}}/03_analysis/results_audit.md）。

# 回传（≤8 行）
共几条意见 / 其中 high 几条 / 最致命的 2–3 条一句话 / 是否建议回退到更早阶段（哪个）。
```

---

## §QG · 初稿质量门评分器（Stage 7 之后强制派 1 个）

> 这是兑现「高质量初稿」承诺的关键派发。critic 按 [`quality-rubric.md`](quality-rubric.md) 的 7 维
> 评分卡打分、写盘、回传判定。详见 SKILL.md「初稿质量门」节。

```text
你是顶刊（JF/JFE/RFS/QJE/AER/MS）的资深 AE。用统一 rubric 给这份初稿打质量分，决定放行还是回炉。
只依据真实产物，每个分数后面必须附「带行号/表号的具体依据」；命中致命红旗的维度直接封顶 ≤4 分。
宁严勿松。

# 必读
- 评分标尺与 7 维细则、致命红旗、达标线、回退映射：{{REPO_69}}/references/quality-rubric.md
  （= skills/69-Paper-WorkFlow/references/quality-rubric.md，先完整 Read 它再打分）

# 待评产物
- 初稿正文 + 表图 + 参考文献：{{WS}}/07_dehumanize/main.tex、{{WS}}/04_results/、{{WS}}/05_draft/ref.bib
- 贡献承诺（对照）：{{WS}}/01_proposal/proposal.md
- 真实结果（对照表中数字）：{{WS}}/03_analysis/results/summary.md + main_results.json
- 样本证据（对照 N、treated/control、cluster/weights）：{{WS}}/02_data/sample_audit.md
- 方法证据（识别与稳健性对照）：{{WS}}/03_analysis/design_register.md + {{WS}}/03_analysis/method_gate.md
- 引用核验报告（若有）：{{WS}}/06_polish/ref_verify_report.xlsx
- 复现证据：{{WS}}/00_meta/workflow_state.json 的 replication_pack、{{WS}}/REPLICATION.md、
  {{WS}}/09_submission/DAS.md、{{WS}}/00_meta/data_governance.md（若目标刊或数据限制要求）

# 输出
按 quality-rubric.md 末尾的「评分卡输出格式」把 7 维评分 + 达标判定 + 最关键 3 条短板 +
回退指令写入 {{WS}}/00_meta/quality_scorecard.md，并把本轮分数追加进 {{WS}}/logs/quality_gate.md。

# 回传（≤10 行）
总分 X/70 / 各维一行分数 / PASS 还是 NOT PASS / 卡在哪一维 / 本轮建议回退到哪个 Stage /
当前累计回退轮次。
```

---

## §S7 · Stage 7 去 AI 味（并行，按段落/章节切分）

> 去味是「逐句改写」性质，独立章节可并行。英文走 `readability` + 44/45/46/47；中文走 `fix-chinese`
> + `chinese-quote-converter` + 48/49（语言分流见 skill-map §C）。

```text
你负责把初稿的某一部分去 AI 味，保持学术准确性与术语不变，只改腔调与可读性。

# 输入
- 待改部分：{{WS}}/07_dehumanize/section_{{K}}.tex（从 main.tex 切出的第 {{K}} 节）
- 语言：{{LANG}}（en / zh）

# 执行
- en：优先 `Skill(skill="readability")`；再按需 `Skill` 调 humanizer/de-slop（44/45/46/47）。
- zh：优先 `Skill(skill="fix-chinese")` + `Skill(skill="chinese-quote-converter")`；再按需 48/49。
- 任一 not found → `Read` 对应 SKILL.md（路径见 skill-map §0.1）按其流程执行。
- 重点清除：「首先/其次/综上所述/值得注意的是/总而言之」等套话、翻译腔、过度对仗、空泛形容词。
- 改完写回 {{WS}}/07_dehumanize/section_{{K}}.tex（原地覆盖）。

# 回传（≤6 行）
改了哪节 / 清除了几类套话 / 是否动到术语（应为否）/ 一句话风险提示。
```

---

## 主代理侧纪律（收到摘要之后）

- 拿到 subagent 的 ≤10 行摘要后，**只更新** `00_meta/workflow_state.json`（`stages`/`artifacts`/
  `decisions`）、`logs/stage_<N>.md`、必要的 `backups/`。
- **不要把摘要里引用的大文件读回主代理上下文**；确需某个具体数字时，只 `Read` 那个 json 的那几行，
  不读整份稿件。
- 并行批返回后解析摘要：格式不符 / 失败的**只对失败那一条**重派一次；连续失败记入 `logs/` 并在
  闸门标红，不要静默吞掉。
