# Skill Coverage Map — 「47 个 skill 来自哪里」溯源表

> 入口：每条流水线声明的「**47 技能**」（README 中部 / `references/skill-map.md` / `SKILL.md` overview）都
> 在这里能查到来源、版本、路径、可替换选项。维护者改 README 数字前先来这里对账。
>
> **读法**：先看 §1 一表概览（每个上游库的「名字 / 数量 / 在 README 中扮演的角色」），再按需跳到 §2
> 拉清单。**§3 是给审计的**——任何对 "47" 这个数字的修改必须在这里留痕，RIGOR badge 才会一直可信。

---

## 1. 上游 skill 库概览

| 上游库 | 路径 | skill 数 | 在 README / SKILL.md 中的角色 |
|---|---|---|---|
| `67-econfin-workflow-toolkit` | `skills/67-econfin-workflow-toolkit/` | ~43 | **主线**——几乎所有 Stage 1–9 的默认 skill（粗体）来自这里，是唯一一套为实证论文全流程设计的、可彼此组合的 skill 集。 |
| `66-...-reviewers` | `skills/66-.../reviewers/` | 库内约 8 个资产（`did-reviewer`, `econ-reviewer`, `grillme`, `latex-table`, `citation-fidelity`, `codebook-pass`, `R-optimizer` + 1 套件）；**其中 5 个计入 47**（§2.4） | **专项增强**——Stage 8 模拟评审 / 引用核验 / LaTeX 表的 reviewer 集合。 |
| `00-Full-empirical-analysis-skill_*` | `skills/00-Full-empirical-analysis-skill_*` | 3 套件（Python / Stata / R）；Stata/R 两套以注册名计入 §2.1 | **三套分析后端**——Stage 3 默认走 StatsPAI Python，但 `.do` / `reghdfe` / `esttab`（Stata）和 `fixest` / `modelsummary`（R）也通过它们落地。 |
| `69-Paper-WorkFlow` | 本仓库 | **0 计入 47**（`defense_pptx.py` 与 references/templates/scripts/evals 均为编排器内部资产，见 §2 尾注） | **编排器自身**——不重复造子能力，只在每个阶段用 `Skill` / `Agent` 把上面的库串起来。 |
| 其余 0–65、68 等 68 个集合 | `skills/00–65, 68/` | ~20 处引用（基本只在「Stage N 增强 / 替代」列出现；例外见下） | **专项替换**——比如 Stage 1 选题可换 `25-HosungYou-Diverga`。**唯一的例外是 `48-de-AIGC-skills`**：它是 Stage 7 降 AIGC 的**第一顺位默认**（中英双语六步闭环），`44`–`47`、`49` 退为补充；因为它不属于 `67/`/`66/`，**不计入 47 个内置 skill**（与 Stage 9 的 AJS 适配器同例）。 |

**为什么是 47？** 把它分成 4 类加总（与 §2.1–2.4 一一对应，编排器自身资产不计入）：

| 类别 | 数 | 说明 |
|---|---|---|
| 主线 `67/` skill（含 Stata/R 后端注册名） | 33 | §2.1 = skill-map.md §A 主线路由的 Stage 1–9 默认列 |
| 横切 `67/` skill | 4 | §2.2：web-access / web-research / agent-browser / arxiv |
| 转换 / 演示配套 `67/` skill | 5 | §2.3：md-to-docx / markitdown / marp-slides-creator / marp-export / chinese-ppt2 |
| `66/` reviewer | 5 | §2.4：did-reviewer / econ-reviewer / grillme / latex-table / codebook-pass |
| **合计** | **47** | 33 + 4 + 5 + 5，与 README / SKILL.md 顶部 badge 一致 |

> **维护约定**：当上游任意库的 skill 数量变动 > 1，必须同步更新本文件 §2/§3 的清单与本表，并在
> [`worklogs/`](../worklogs/) 留一个 `chore(skill-count): ...` 工作日志，否则 RIGOR 计数 badge 会
> 与事实脱节。

---

## 2. 47 个 skill 完整清单

> **格式**：`#` = 序号（与 README badge 中的 "47" 对齐）；`SKILL.md 注册名` 即主代理调用
> `Skill(skill="...")` 用的字符串（≠ 文件夹名时另行标注）；`上游库` 给出该 skill 在母仓库
> `skills/<N>-<name>/SKILL.md` 中的位置。

### 2.1 主线（Stage 1–9 默认列）—— 33 项

| # | skill | 上游 | 主线阶段 |
|---|---|---|---|
| 1 | `econfin-idea-finder` | `67/econfin-idea-finder` | Stage 1 选题漏斗 |
| 2 | `Econfin-Proposal` | `67/econfin-proposal` | Stage 1 写计划书（注册名 ≠ 文件夹名） |
| 3 | `novelty-check` | `67/novelty-check` | Stage 1 查新 |
| 4 | `Significance-Search` | `67/significance-search` | Stage 1 重要性论证（注册名 ≠ 文件夹名） |
| 5 | `journal-digest` | `67/journal-digest` | Stage 1 目标期刊口味扫描 |
| 6 | `data-fetcher` | `67/data-fetcher` | Stage 2 取数 |
| 7 | `data-cleaning` | `67/data-cleaning` | Stage 2 清洗 |
| 8 | `did-analysis` | `67/did-analysis` | Stage 3 DiD |
| 9 | `iv-estimation` | `67/iv-estimation` | Stage 3 IV/2SLS |
| 10 | `rdd-analysis` | `67/rdd-analysis` | Stage 3 RDD |
| 11 | `synthetic-control` | `67/synthetic-control` | Stage 3 合成控制 |
| 12 | `panel-data` | `67/panel-data` | Stage 3 面板 |
| 13 | `ols-regression` | `67/ols-regression` | Stage 3 OLS |
| 14 | `time-series` | `67/time-series` | Stage 3 时间序列 |
| 15 | `ml-causal` | `67/ml-causal` | Stage 3 ML 因果 / HTE |
| 16 | `Full-empirical-analysis-skill-Stata` | `00.2-Full-empirical-analysis-skill_Stata` | Stage 3 Stata 后端（注册名 ≠ 文件夹名） |
| 17 | `Full-empirical-analysis-skill-R` | `00.3-Full-empirical-analysis-skill_R` | Stage 3 R 后端（注册名 ≠ 文件夹名） |
| 18 | `stats` | `67/stats` | Stage 3 通用统计 |
| 19 | `table` | `67/table` | Stage 4 回归表（LaTeX 三线为主） |
| 20 | `figure` | `67/figure` | Stage 4 图 |
| 21 | `paper-writer` | `67/paper-writer` | Stage 5 写作初稿 |
| 22 | `paper-pipeline` | `67/paper-pipeline` | Stage 6 全流程打磨编排 |
| 23 | `paper-polish` | `67/paper-polish` | Stage 6 单步：校对 |
| 24 | `paper-self-revise` | `67/paper-self-revise` | Stage 6 单步：自评修订 |
| 25 | `paper-style` | `67/paper-style` | Stage 6 单步：期刊风格 |
| 26 | `reference-verify` | `67/reference-verify` | Stage 6 单步：引用核验 |
| 27 | `readability` | `67/readability` | Stage 7 英文可读性 |
| 28 | `fix-chinese` | `67/fix-chinese` | Stage 7 中文去翻译腔 |
| 29 | `chinese-quote-converter` | `67/chinese-quote-converter` | Stage 7 中文混排引号 |
| 30 | `referee-report` | `67/referee-report` | Stage 8 模拟审稿 |
| 31 | `paper-referee-revise` | `67/paper-referee-revise` | Stage 8 按审稿意见修订 |
| 32 | `paper-submission` | `67/paper-submission` | Stage 9 选刊与投稿 |
| 33 | `master-thesis-review` | `67/master-thesis-review` | Stage 9 硕士论文评阅（学位场景） |

### 2.2 横切能力（任何阶段都可能用）—— 4 项

| # | skill | 上游 | 用途 |
|---|---|---|---|
| 34 | `web-access` | `67/web-access` | 联网 / 抓取 / 中文站点首选 |
| 35 | `web-research` | `67/web-research` | 联网检索 |
| 36 | `agent-browser` | `67/agent-browser` | 登录后浏览器操作 |
| 37 | `arxiv` | `67/arxiv` | arXiv / NBER / 预印本 |

### 2.3 转换 / 演示配套（独立 skill）—— 5 项

| # | skill | 上游 | 用途 |
|---|---|---|---|
| 38 | `md-to-docx` | `67/md-to-docx` | Markdown → Word |
| 39 | `markitdown` | `67/markitdown` | 文档/网页 → Markdown |
| 40 | `marp-slides-creator` | `67/marp-slides-creator` | Marp 演示稿 |
| 41 | `marp-export` | `67/marp-export` | Marp → PPT / PDF |
| 42 | `chinese-ppt2` | `67/chinese-ppt` | 中文 PPT 模板（注册名 ≠ 文件夹名） |

### 2.4 Reviewer 集合（Stage 8 并联使用）—— 5 项

| # | skill | 上游 | 用途 |
|---|---|---|---|
| 43 | `did-reviewer` | `66/.../did-reviewer` | DiD 专项审稿 |
| 44 | `econ-reviewer` | `66/.../econ-reviewer` | 经济学总审稿 |
| 45 | `grillme` | `66/.../grillme` | 反例驱动审稿 |
| 46 | `latex-table` | `66/.../latex-table` | LaTeX 表审稿 |
| 47 | `codebook-pass` | `66/.../codebook-pass` | Codebook 质量门 |

> **§2.1–2.4 合计 = 47 项**，与 README / SKILL.md 顶部「**47 技能**」badge 一致。
> 本仓库**自带**的 `defense_pptx.py`、`references/...`、`templates/...`、`scripts/...`、
> `evals/...`、`assets/...` 都是这个编排器的内部资产，**不计入 skill 数**，但与 `67–66` 库中的
> skill 一起承担编排职责。

---

## 3. 数字一致性维护清单

下游 reviewer / 招生官 / 招聘 HR 看到的「**10 阶段 · 47 技能 · 2 道硬闸门 · 3 套分析后端 · 1 个可审计
工作区**」是一个**硬数字 badge**。它的同步由 `scripts/check_numeric_claims.py` 自动
guard（见 `.github/workflows/ci.yml`）。任何修改触发下列流程：

| 触发场景 | 必须同步 |
|---|---|
| 上游 `67/` 增/减 1 个 skill | §2.1 / §2.2 / §2.3 表格 + §1 上游概览 + 顶部合计；如有删减 ≥ 2，在 `worklogs/` 写 `chore(skill-count): ratchet ...` |
| 上游 `66/` 增/减 reviewer | §2.4 表格 + §1；同样 ≥ 2 变更写 worklog |
| 新增 `00.*-Full-empirical-analysis-skill_*` 后端 | §1 + §2.1 的 Stage 3 后端列；考虑同步更新 README "3 套分析后端" 数字（如果增加第 4 套） |
| 把 §2.1–2.4 任意一行的 skill 名 / 上游路径改了 | §2 表格 + `references/skill-map.md` §0.1 注册名对照表 + `SKILL.md` overview（如有指代） |
| 删/合并 §2 任一行 | README 顶部 badge `47 技能` **不再准确** → 必须把 README 也改成新数字，或者补一个被合并/删除的 skill 回到 §2。 |
| 给 `defense_pptx.py` 拆成多 skill（拆仓库） | §2 加新行；如拆出 ≥ 2 个，顶部 badge 可能从 47 → 48+。 |

> 一句话：**改 §2 任何一行之前，先跑一遍
> `python3 scripts/check_numeric_claims.py --selftest && python3 scripts/check_numeric_claims.py`**，两个都绿了再 commit。

---

## 4. 与 skill-map.md 的对照

`references/skill-map.md` 是「任务 → skill」的**路由表**（A 节按阶段横切、B 节按能力横切），
本文件是「**skill → 来源**」的**溯源表**。两者关系：

- **skill-map.md §A / §B** = 「**这个阶段做什么 → 用哪个 skill**」
- **skill-coverage-map.md §1–§2** = 「**这个 skill 来自哪里、放在哪一级目录、归到哪一组**」

需要「**编排入口**」（在子代理 prompt 里写「读 `67/econfin-idea-finder/SKILL.md` 并执行」）时 → 翻
`skill-map.md` §0；需要「**审计来源 / 解释 47 这个数字**」时 → 翻本文件。

任何新增 skill 必须**两边同步登记**——这是编排器的双向台账纪律。

---

## 5. 验证 & 后续动作

- 本表数字 (47) 由 `scripts/check_numeric_claims.py` 自动校验：见该脚本 `skills_47` claim，
  子串 `47\s*(?:个\s*)?(?:skill|技能)s?` 必须同时在 `README.md`、`README.en.md`、`SKILL.md`
  中被找到；任何缺失都会让 `validate_skill.py` 红灯。
- 上游库增减请同时更新 `references/skill-map.md` §0.1 注册名对照表，否则 `Skill` 工具调用会因为
  「注册名 ≠ 文件夹名」找不到对应 skill 而报错。
- 如果未来把 `defense_pptx.py` 拆出多个 skill、或者新增第 4 套分析后端（Julia？Julia + Stan？），请在本
  文件顶部维护一节「changelog」，记下每一次数字调整与原因。这样 1 年后审计时能直接读到完整的演化轨迹。

### Changelog

- **2026-07-22**：修复 §1 内部矛盾（「Stage 0/9 配套」行计数写 4 却列 5 项；分类加总与 §2.1–2.4
  口径不一；`66/` 行库内资产数与计入数混写）。§1 加总现与 §2 严格一一对应：33 + 4 + 5 + 5 = 47，
  编排器自身资产计 0。同日起 executable-gates badge 数字由 `generate_rigor_report.REGISTRY` 动态
  派生，不再手工登记。
- **2026-07-08**：首版（worklog `2026-07-08-week-recap.md` 提议 → 本文件落地）。`scripts/check_numeric_claims.py`
  同步上线，把 47 / 10 / 2 / 3 / 29/29（后者现为动态 badge）五个数字纳入跨文档一致性 guard。
