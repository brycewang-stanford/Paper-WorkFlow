# Subagent 派发模板 — 可直接复制套用

> 本编排器靠 `Agent` 工具派发 subagent 干重活（源自 `do-agent` 的「多代理 + 上下文保护」范式）。
> 这里给出**可直接复制**的 prompt 模板，覆盖最常用的几类派发。每个模板都已内置三件事，缺一不可：
>
> 1. **上下文保护契约**：subagent 自己写盘，**只回传 ≤10 行状态摘要**，严禁回传完整产出。
> 2. **强制调用子 skill**：写明用 `Skill(<注册名>)`；并给出 `Read` 回退路径（注册名见
>    [`skill-map.md`](skill-map.md) §0.1）——subagent 必须真的加载子 skill，不许凭记忆脑补。
> 3. **绝对路径**：所有输入/输出文件、要 `Read` 的 SKILL.md，一律写**仓库内 / 工作区内完整路径**。
>
> 用法：把 `{{...}}` 占位符替换为真实值后，作为 `Agent` 工具的 `prompt`。`{{REPO}}` =
> `skills/67-econfin-workflow-toolkit`，`{{WS}}` = 本次工作区根（如 `paper_workspace/绿色信贷_20260619-1430`），
> `{{LITRUN}}` = 外部 skill `literature-review-tools` 的启动器绝对路径（`.../skills/literature-review-tools/scripts/litrun.py`，
> 定位方式见 [`lit-review-integration.md`](lit-review-integration.md) §2）。
> 并行批次 ≤10 个/批（`do-agent` 上限；选题漏斗沿用 `idea-finder` 的 5/批）。

---

## §S1L · Stage 1L 文献底座（**串行 1 个**，含 litrun 输出重定向）

> 建真实文献语料 + 带引用的文献扫描，供 Stage 1 查新、Stage 5 related work、Stage 6/9 引用核验复用。
> 多组检索式必须**串行**跑——litrun 的 workdir 按 workflow id 命名，并发/连跑会互相覆盖。
> 完整协议见 [`lit-review-integration.md`](lit-review-integration.md)。

```text
你负责为本研究建立「真实文献语料底座」。**只用真的检索到、真的下载下来的文献**——
任何情况下都不许凭记忆写文献名、作者或年份充数；宁可少、宁可标降级，也不要假语料。

# 输入
- 研究方向：{{DIRECTION}}
- 检索式（英文，按顺序串行跑，每组跑完先拷贝再跑下一组）：{{QUERIES}}
- 扫描问题：本领域已被做透的问题(Saturated)有哪些？尚存的空白(Opportunity)有哪些？必须对标的关键文献是哪几篇？
- 启动器：{{LITRUN}}

# 强制工作流
## Step A — 确认可达与配置
1. `Bash: python3 {{LITRUN}} doctor` —— 看工具链与已配 API key。
2. 缺 OPENAI_API_KEY：**停下来回传「需要 key」**，不要自己编、不要跳过就硬跑 QA 步。
   （主代理会问用户后用 `litrun.py env --set` 写入；用户不给则改跑免钥的 `topic-to-pdfs`，问答步跳过并标注。）
3. 重活先干跑：对第一组检索式加 `--dry-run` 跑一次，把解析出的真实命令写进
   {{WS}}/logs/stage_1L.md，再去掉 --dry-run 实跑。

## Step B — 逐组检索（串行）+ **立刻重定向输出**
对每组检索式 Q，依次跑这两条 Bash（顺序不能颠倒）：

    python3 {{LITRUN}} workflow run topic-to-review-multi \
      --query "Q" --max 8 --question "<扫描问题>" \
      2>&1 | tee -a "{{WS}}/01_proposal/literature/scan_raw.txt"

    cp -R ~/.lit-review-tools/workspace/runs/topic-to-review-multi/corpus/. \
          "{{WS}}/01_proposal/literature/corpus/"

**这两步缺一不可**：litrun 把语料写在 ~/.lit-review-tools/（按 workflow id 命名、**下一轮就被覆盖**），
把答案打到 stdout（**不落盘**）。不 tee + 不 cp 就等于这一轮白跑。
生物医学主题改用 `pubmed-fetch`；只要语料不要问答用 `topic-to-pdfs`（免钥）。

## Step C — 归并成结构化扫描
把各轮答案归并写入 {{WS}}/01_proposal/literature/scan_digest.md，固定三节：
- **Saturated（已做透）**：每条一句话 + 出处（corpus 内文件名或 DOI）
- **Opportunity（空白）**：每条一句话 + 为什么还没被做
- **Key references（关键对标文献）**：每条「作者-年份-标题-出处」，必须能在 corpus/manifest.json 里找到
**无出处的论断一律删掉，不要写进 digest。**

# 失败处理
- litrun 报错：把**真实报错原文**写进 {{WS}}/logs/stage_1L.md 并回传，**绝不声称成功**。
- 检索几乎无结果：换更宽的上位词 / 换英文表述，最多换 3 轮，仍无果就如实回传。
- marker/docling 这类会拉 PyTorch 的重装工具**不要自作主张装**（几个 GB），本阶段用不到。

# 回传（≤10 行，严禁回传语料内容或完整答案）
跑了几组检索式 / 语料共几篇（corpus 文件数）/ digest 写到哪 / Saturated 与 Opportunity 各几条 /
关键对标文献几篇 / 是否降级(degraded) / 遇到的真实报错（若有）/ 一句话下一步建议。
```

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
- 主设定与基准结果：{{WS}}/03_analysis/results/main_results.json
- 估计脚本范式（照其风格）：{{WS}}/03_analysis/（已有 .py/.do/.R）
- 本检验：{{CHECK_NAME}}（如「替换聚类到省级」/「剔除危机年份子样本」/「安慰剂：随机分配处理时点」）

# 执行
- 复用主设定，只改本检验对应的那一处；用 {{ESTIMATOR_SKILL}}（优先 `Skill`，not found 则
  `Read {{REPO}}/{{ESTIMATOR_FOLDER}}/SKILL.md` 按其流程）跑。可选 StatsPAI MCP 链路做交叉验证。
- 把系数/SE/p/样本量/必要图写盘到 {{WS}}/03_analysis/robustness/{{CHECK_NAME}}.json（图同名 .png）。

# 回传（≤6 行）
做了什么 / 写到哪个文件 / 核心系数与 SE / 相对基准是否稳健（稳/不稳）/ 一句话判断。
```

---

## §S5L · Stage 5 related work 起草（**1 个**，复用 1L 语料、不重复下载）

> 在 Stage 1L 已建好的语料上起草一段**带引用**的 related work，作为 `paper-writer` 的素材。
> 1L 处于降级模式（`literature.degraded=true`）时**不要派这个 subagent**——没有真实语料就没有真实引用。

```text
你负责起草论文的 related work 段落。**每一条引用都必须来自工作区内已下载的真实语料**——
不许凭记忆加文献、不许把语料里没有的文章写进去。

# 输入
- 已建好的语料（**直接复用，不要重新下载**）：{{WS}}/01_proposal/literature/corpus/（含 manifest.json）
- 文献扫描：{{WS}}/01_proposal/literature/scan_digest.md
- 本文的贡献承诺（决定「相对谁前进了一步」）：{{WS}}/01_proposal/proposal.md
- 启动器：{{LITRUN}}

# 执行
## Step A — 在既有语料上问出综述素材
优先复用语料，避免重复下载与重复花 API：
    python3 {{LITRUN}} workflow run pdf-corpus-qa \
      --input "{{WS}}/01_proposal/literature/corpus" \
      --question "围绕 {{TOPIC}}：现有文献分成哪几条主线？各自用什么识别策略？留下什么空白？" \
      2>&1 | tee "{{WS}}/05_draft/related_work_raw.txt"
语料覆盖不足（manifest 少于 ~10 篇或明显跑题）时，才补跑一次检索：
    python3 {{LITRUN}} workflow run topic-to-related-work --query "{{TOPIC}}" --max 10 \
      2>&1 | tee -a "{{WS}}/05_draft/related_work_raw.txt"
    cp -R ~/.lit-review-tools/workspace/runs/topic-to-related-work/corpus/. \
          "{{WS}}/01_proposal/literature/corpus/"

## Step B — 成稿 + 补 bib
- 把答案整理成 {{WS}}/05_draft/related_work_draft.md：按 2–4 条**主线**组织（不要按时间流水账），
  每条主线末尾点明「本文相对这条主线前进了一步在哪」，与 proposal.md 的贡献承诺对齐。
- 把命中的文献条目按 BibTeX 追加到 {{WS}}/05_draft/ref.bib（已存在的 key 不重复添加）。
- **凡是在 corpus/manifest.json 里找不到出处的条目，一律删掉**，并在 draft 末尾的
  「待补文献」小节列出「想引但语料里没有」的主题，交给主代理决定是否补检索。

# 回传（≤8 行，严禁回传段落全文）
整理出几条主线 / 引用几篇（全部有出处？是/否）/ 写到哪两个文件 / 补进 ref.bib 几条 /
是否补跑了检索 / 待补文献几条 / 一句话给 paper-writer 的提醒。
```

---

## §CR · 阶段 critic（对抗式审阅，每个重活阶段末派 1 个）

> Stage 1/3/5/6/8 这些重活阶段，派一个独立 critic 做对抗审阅再据其修订（`do-agent` 微循环的
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
- 引用核验报告（若有）：{{WS}}/06_polish/ref_verify_report.xlsx

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
