# Lit-Review 接入说明 — `literature-review-tools` 在本流水线里的位置与调用协议

> 本编排器的文献能力由外部 skill **[`literature-review-tools`](https://github.com/brycewang-stanford/lit-review-agent-tools)**
> 提供：它既是一份 70+ 开源文献工具的**选型目录（Recommend）**，又自带一个**能真正装起来跑的
> 启动器（Run）** `scripts/litrun.py`——把 arXiv / OpenAlex / PubMed 检索、PDF→Markdown、
> PaperQA2 带引用问答、ASReview PRISMA 筛选、arxiv/zotero MCP 串成命名工作流。
>
> **本编排器不内置它**（遵循「能调用就不要重写 / 不复制他人 skill 进仓库」的仓库纪律）——运行时
> 按下文协议**安装 + 调用**。上游许可为 **CC0-1.0**，可自由使用与再分发。

---

## 1. 它补上了流水线的哪块空缺

原流水线的文献工作散落在三处、且都只有「路由到某个 skill」的粗指引：Stage 1 的查新靠
`novelty-check` 单点判断、Stage 5 的文献综述只写了「薄弱时配合 36/52/59」、Stage 6/9 的引用核验
靠 `reference-verify` 事后补救。**缺的是一个贯穿全程的「真实文献语料底座」**——一堆真的下载下来、
能被反复检索与引用的论文，而不是靠模型记忆生成的文献名。

接入后新增一个**前置微阶段 Stage 1L（文献底座）**，并在三个既有节点复用它的产物：

| 节点 | 用 lit-review 做什么 | 落到工作区哪 |
|---|---|---|
| **Stage 1L**（新增，Stage 1 之前） | 按研究方向检索 arXiv+OpenAlex（生物医学加 PubMed），下载语料，用 PaperQA2 产出**带引用的文献扫描**（Saturated / Opportunity / 关键对标文献） | `01_proposal/literature/` |
| **Stage 1**（选题漏斗） | 扫描摘要填进 §S1 模板里一直空着的 `{{LITERATURE_SCAN_DIGEST}}`；`novelty-check` 的判断有真实语料兜底 | `01_proposal/candidates/` |
| **Stage 5**（写作初稿） | `topic-to-related-work` 起草**带引用的 related-work 段落**，交 `paper-writer` 消化成正式文献综述节 | `05_draft/related_work_draft.md` |
| **Stage 6 / 9**（引用核验） | `01_proposal/literature/corpus/manifest.json` 作为「这些引用确实存在且我们真读过」的物证，供 `reference-verify` 与质量门维度 ⑥ 对照 | `06_polish/` `09_submission/` |

> **它不替代什么**：不替代 `novelty-check`（查新判分）、不替代 `paper-writer`（成文）、不替代
> `reference-verify`（逐条核验元数据）。它只负责**把真实文献变成可检索的本地语料 + 带引用的结论**。

---

## 2. 调用协议（三级回退，与 skill-map §0 同构）

`literature-review-tools` **不在母仓库 `Auto-Empirical-Research-Skills` 内**，因此比其它子 skill 多一步
「先确认可达」。按下面顺序走，**任一级成功就停，不要往下试**：

### 级别 1 — `Skill` 工具（已安装为插件 / 个人 skill 时）

```
Skill(skill="literature-review-tools", args="<自然语言任务，如：检索并下载「绿色信贷 企业创新」近五年文献，产出带引用的文献扫描>")
```

注册名 = 其 `SKILL.md` 前言的 `name:` 字段 = **`literature-review-tools`**（与文件夹同名）。

### 级别 2 — `Read` 内联执行（已 clone 到本地但未注册）

按下列顺序 `Glob`/`Read` 第一个存在的路径，把正文当作本步操作手册执行：

```
~/.claude/skills/literature-review-tools/SKILL.md
.claude/skills/literature-review-tools/SKILL.md
~/.claude/plugins/**/lit-review-agent-tools/skills/literature-review-tools/SKILL.md
<用户 clone 目录>/lit-review-agent-tools/skills/literature-review-tools/SKILL.md
```

找到后，启动器路径 = 同目录下的 `scripts/litrun.py`，记为 `{{LITRUN}}`，后续所有 Bash 调用都用它。

### 级别 3 — 现装（都找不到时，在闸门问一次用户再装）

```text
# 作为 Claude Code 插件（推荐，一步装好 skill + 启动器）
/plugin marketplace add brycewang-stanford/lit-review-agent-tools
/plugin install lit-review-agent-tools@lit-review-marketplace

# 或直接 clone（编排器可用 Bash 自己做，装到工作区外的固定位置）
git clone --depth 1 https://github.com/brycewang-stanford/lit-review-agent-tools ~/.lit-review-agent-tools
cp -r ~/.lit-review-agent-tools/skills/literature-review-tools ~/.claude/skills/
```

**装不上 / 用户拒绝装 → 降级，不阻断流水线**：Stage 1L 退化为用 `WebSearch` + `67/arxiv` +
`59-shiquda-openalex-skill` 做一次轻量文献扫描，并在 `logs/stage_1L.md` 与阶段闸门**显著标注
「文献底座为降级模式，引用需在 Stage 6 加倍核验」**。绝不因为装不上就凭记忆编文献。

---

## 3. `litrun.py` 命令速查（编排器实际会用到的那几条）

```bash
python3 {{LITRUN}} doctor                       # 先跑这条：查工具链 + 哪些 API key 已配
python3 {{LITRUN}} workflow list                # 可用的命名工作流
python3 {{LITRUN}} workflow run <id> ... --dry-run   # 先干跑看解析出的真实命令，再去掉 --dry-run
python3 {{LITRUN}} env --set OPENAI_API_KEY=...      # 写入 ~/.lit-review-tools/.env（绝不回显全值）
python3 {{LITRUN}} run <tool-id> -- <tool args>      # 单工具直跑（首次自动装进独立 venv）
python3 {{LITRUN}} mcp zotero-mcp                    # 打印 MCP 配置块（MCP 服务器不要「run」）
```

**本流水线用到的命名工作流**（参数与默认值以上游 `recipes/workflows.json` 为准）：

| workflow id | 参数 | 用在哪个 Stage | 语料落在 workdir 的 | 要 API key? |
|---|---|---|---|---|
| `topic-to-pdfs` | `--query` `--max`(默认10) | **1L 降级主用**：只取语料不问答 | **`pdfs/`** | **否**（arXiv 免钥） |
| `topic-to-review-multi` | `--query` `--question` `--max`(默认8/源) | **1L 主用**：arXiv+OpenAlex 合并语料 → 带引用回答 | **`corpus/`** | 是（`OPENAI_API_KEY`） |
| `topic-to-review` | `--query` `--question` `--max`(默认10) | 1L 备用（只要 arXiv，更快） | **`corpus/`** | 是 |
| `topic-to-related-work` | `--query` `--max`(默认10) | **5 主用**：检索 → 起草带引用 related-work 段 | **`corpus/`** | 是 |
| `pdf-corpus-qa` | `--input`(PDF 目录) `--question` | 1L/5 复用已有语料再问一次，**不重复下载** | 原地（`--input`） | 是 |
| `pdf-to-markdown` | `--input` | 需要把 PDF 喂给别的 skill 时（MinerU） | `markdown/` | 否 |

> ⚠️ **子目录名按 workflow 而异**（已实测）：`topic-to-review*` / `topic-to-related-work` 落 `corpus/`，
> 但 `topic-to-pdfs` 落 **`pdfs/`**。拷贝时**照着上表取对应子目录**，别一律写 `corpus/`——写错了
> `cp` 会静默拷不到东西，这一轮就白跑了。两者内部结构一致（PDF + `manifest.json`），拷进工作区
> 后统一归到 `01_proposal/literature/corpus/` 即可。

单工具直跑里本流水线可能用到：`arxiv-fetch` / `openalex-fetch` / `pubmed-fetch`（均免钥，生物医学
或中文经管主题走 OpenAlex/PubMed 覆盖更好）、`asreview`（真要做 PRISMA 系统综述时）。

---

## 4. ⚠️ 输出重定向（**必做**，与 skill-map §0.2 的两个 Windows 路径同性质）

`litrun.py workflow run` 把语料写到**固定的用户级目录**、把答案打到 **stdout**：

```text
语料 / 中间产物 → ~/.lit-review-tools/workspace/runs/<workflow-id>/
带引用的回答     → stdout（不落盘）
```

两个后果，编排时必须处理：

1. **workdir 按 workflow id 命名，重跑会覆盖**——同一个 workflow 跑第二次（换 query）会冲掉上一次的语料。
2. **答案不落盘**——不接管就等于没产出。

所以**每次调用后立刻做两件事**（写进 subagent 的 prompt，不要指望它自觉）：

```bash
# ① 答案落盘：用 tee 接住 stdout，绝不只留在上下文里
python3 {{LITRUN}} workflow run topic-to-review-multi \
  --query "<检索式>" --question "<问题>" --max 8 \
  2>&1 | tee "{{WS}}/01_proposal/literature/scan_raw.txt"

# ② 语料落盘：把 run workdir 整份拷进工作区，之后所有引用都指向工作区内副本
#    ⚠️ 子目录名按 workflow 而异：topic-to-review* / topic-to-related-work → corpus/
#                                  topic-to-pdfs                          → pdfs/
cp -R ~/.lit-review-tools/workspace/runs/topic-to-review-multi/corpus/. \
      "{{WS}}/01_proposal/literature/corpus/"

# 降级路径（无 OPENAI_API_KEY 时）——注意源目录是 pdfs/ 不是 corpus/
python3 {{LITRUN}} workflow run topic-to-pdfs --query "<检索式>" --max 10
cp -R ~/.lit-review-tools/workspace/runs/topic-to-pdfs/pdfs/. \
      "{{WS}}/01_proposal/literature/corpus/"
```

> **纪律**：凡是 `~/.lit-review-tools/` 下的东西都视作**临时缓存**，可能被下一次运行覆盖。
> 工作区内的 `01_proposal/literature/` 才是权威副本，`FINAL_REPORT.md` 的可复现说明只引用后者。

---

## 5. 护栏（写进每个用到它的 subagent prompt）

1. **先 `doctor` 再跑重活**。缺 `OPENAI_API_KEY` 就**先问用户**，用 `litrun.py env --set` 写入，
   **绝不回显 key 全值、绝不编造 key**。
   > ⚠️ **实测：缺 key 时 workflow 是「fail-fast」——一步都不会跑，语料一篇也不会下来。**
   > 报错形如 `litrun: missing API keys for this workflow: OPENAI_API_KEY`。
   > 所以**不存在「检索照跑、只是问答步跳过」这回事**：用户不给 key，就必须**换成免钥的
   > `topic-to-pdfs`**（或直接 `run arxiv-fetch` / `run openalex-fetch`）先把语料拿到手，
   > 再把「带引用扫描」降级为主代理基于语料 `manifest.json` + 摘要的人工归纳，并标 `degraded=true`。
2. **重装警告**：`marker` / `docling` 会拉 PyTorch，首次安装是**几个 GB 的网络下载**。跑之前先告知
   用户，别在无人值守档位里静默拉。默认优先用免装或轻装路径（`arxiv-fetch`/`openalex-fetch`/`mineru`）。
3. **先 `--dry-run`**：重活（下载 N 篇 PDF、跑 QA）先干跑一次，把解析出的真实命令与目标路径在
   闸门给用户看，确认无误再实跑。全自动档位下可跳过确认，但**仍要把 dry-run 结果写进 `logs/stage_1L.md`**。
4. **失败要如实报**。`run` 报错就把**真实报错**写进日志并回传，**绝不声称成功、绝不用记忆里的文献
   顶包**。这是本编排器「真实优先」纪律在文献环节的落地。
5. **只回传摘要**。语料动辄几十兆、QA 答案动辄上千词——subagent 一律**写盘 + 回传 ≤10 行**，
   严禁把语料内容或完整答案灌回主代理上下文。
6. **引用不等于核验**。PaperQA2 的引用来自真实语料，但**格式/年份/卷期仍要过 `reference-verify`**；
   质量门维度 ⑥ 以 `reference-verify` 报告为准，`manifest.json` 只作「确有此文且我们真读过」的旁证。

---

## 6. 与既有 skill 的分工（别重复劳动）

| 场景 | 用 lit-review | 用既有 skill |
|---|---|---|
| 建可检索的本地文献语料 | ✅ `topic-to-*` 系列 | — |
| 判「这个选题有没有被做过」并打分 | 提供语料与证据 | ✅ `67/novelty-check` |
| 论证「学术 + 现实重要性」 | 提供可引用的证据段 | ✅ `67/significance-search` |
| 扫目标期刊近年口味 | — | ✅ `67/journal-digest` |
| 把综述写成论文里的正式一节 | 提供带引用的初稿段 | ✅ `67/paper-writer` |
| 逐条核验引用元数据真伪 | 提供语料旁证 | ✅ `67/reference-verify`、`66/citation-fidelity` |
| 千级摘要的 PRISMA 系统筛选 | ✅ `asreview` | `52-keemanxp-slr-prisma`（方法学） |
| PDF → 干净 Markdown 喂给别的 skill | ✅ `mineru`/`docling`/`marker` | `67/markitdown`（轻量场景） |
| 文献库入库与去重 | ✅ `zotero-mcp`（经 `litrun.py mcp` 配置） | Zotero MCP（若已直连） |

---

## 7. 相关文件

- 阶段操作：[`stage-playbook.md`](stage-playbook.md) 的 **Stage 1L** 章节与 Stage 5 文献综述条目。
- 派发模板：[`subagent-templates.md`](subagent-templates.md) **§S1L**（文献底座）、**§S5L**（related work）。
- 路由总表：[`skill-map.md`](skill-map.md) §0.3（外部 skill 接入）、§A（Stage 1L/1/5 行）、§B（横切）。
- 工作区布局与状态字段：[`workspace-and-state.md`](workspace-and-state.md) 的 `01_proposal/literature/`
  与 `workflow_state.json` 的 `literature` 块。
