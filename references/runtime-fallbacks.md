# Runtime Fallbacks — 工具缺失、网络不可用与执行退化路径

> Paper-WorkFlow 运行在用户本地环境，`Skill`、`Agent`、网络、MCP、Stata/R/Python/Zotero 等依赖可能
> 不齐。本文件规定退化时怎么继续、怎么记录、哪些退化会降低闸门分数。目标是“稳”，不是“假装一切可用”。

---

## 1. 总原则

1. **先走快路径，失败立刻走稳路径**：`Skill(<注册名>)` 报 not found 后，直接 `Read <SKILL.md>` 内联执行。
2. **退化要落日志**：每次 fallback 写入 `logs/stage_<N>.md`，并把影响研究结论的退化写入
   `workflow_state.json.decisions`。
3. **不能验证就降级 claim**：引用、数据、估计、复现无法真实验证时，论文里的主张必须降级或标红。
4. **不把工具缺失当作成功**：若缺失工具导致最低证据包无法生成，`method_gate.md` 必须 `NOT PASS`。
5. **不把敏感数据送到替代工具**：退化到 Web/LLM/浏览器前先检查 `data_governance.md`。

---

## 2. Fallback 矩阵

| 依赖缺失 | 首选 fallback | 必须记录 | 闸门影响 |
|---|---|---|---|
| `Skill` 工具未注册 | `Read` 对应 `SKILL.md`，按正文执行；subagent prompt 传绝对路径 | skill 名、回退路径 | 无，只要产物真实 |
| `Agent` 不可用 | 主代理串行执行，或缩小批次；大文件仍写盘只读摘要 | 哪些任务未并行 | 无，除非时间限制导致少做检验 |
| 网络 / WebSearch / WebFetch 不可用 | 使用用户给定文件、本地文献库、已有 DOI/bib；把政策刷新标 `blocked` | 未能刷新的 URL | 引用/政策相关维度封顶，投稿前必须补 |
| Zotero / 引用 MCP 不可用 | 跑 `reference-verify` 或手工 Crossref/OpenAlex 查验；保留核验报告 | 核验工具和覆盖率 | 引用维度按覆盖率评分 |
| 撤稿筛查（scite）/ `bibtex` 核验不可用 | 手工查 Retraction Watch / 出版商勘误页 + Crossref/OpenAlex 解析 DOI；把 `citation_integrity_log.md` §1 对应行标 `to-verify` 并写明缺什么，**绝不**默认 `verified` | 缺失的核验工具、降级的 bibkey | 见 [`citation-and-temporal-integrity.md`](citation-and-temporal-integrity.md)；终审仍残留 `to-verify` 则 Stage 9 不得 `ready` |
| real-time / vintage 数据源不可访问 | 用可得 vintage 跑代码结构、把 look-ahead 风险标 `risk`；真实 real-time 稳健性标 blocked | 缺失的 vintage、受影响特征 | look-ahead 无法排除时相关结论封顶 `descriptive`（同步 evidence ledger） |
| 选定分析后端不可用 | 按 `analysis-backends.md` 切到能复刻同等 artifact 的另一后端；若用户硬性指定则暂停确认 | 原后端、替代后端、差异 | artifact parity 齐则可过；否则 Method Gate `NOT PASS` |
| StatsPAI MCP 不可用 | 用 `statspai` 包或 Stata/R/Python 包复刻同等 artifact；写明包版本 | 缺失 MCP、替代 route | 若最低证据包齐，方法门可过 |
| Stata 不可用 | 若 Stata 是用户指定主后端，先记录 blocked；可用 Python/R 等价实现做 fallback 或 secondary validation | Stata 版本缺失、替代包 | 关键 artifact 缺失则 Method Gate `NOT PASS` |
| R/Python 包缺失 | 建安装脚本；若不能安装，用同类包或另一后端但保留差异说明 | 包名、版本、替代 | 数字不可复核时不得放行 |
| LaTeX / PDF 工具缺失 | 生成 `.tex`、`.md`、`.docx` 替代；投稿前补 PDF render | 缺失命令 | 写作可继续，submission checklist 不可过 |
| pandoc 缺失（Word 交付路径） | `assemble_manuscript_docx.py` 自动落到内置 stdlib 写入器，把 `manuscript.converter` 记成 `builtin`；保真度差异（citeproc、目标刊 `--reference-doc` 模板、行内公式）写进 `decisions` | 缺失命令、降级的转换能力 | `check_deliverable_contract.py` 照常跑——**降级的是转换器，不是闸门**；还须确认引用、数学表达和格式被正确保留；有未解析内容时构建失败并保留旧稿；结构检查通过不代表逐页视觉审阅通过 |
| 图只有 `.pdf`、没有 `.png` | 由绘图后端补出 `.png`（`graph export` / `savefig` / `ggsave`）；内置写入器无法把 PDF 塞进 `.docx` | 缺失的位图、受影响图号 | 组装器记 unresolved marker，`check_deliverable_contract.py` 判 `exhibits:figures` 红——Word 稿不得少图 |
| 受限数据不可访问 | 用公开样例/合成数据跑代码结构；真实估计标 blocked | 数据访问限制 | 主结果不可声称真实；复现 `not_ready` |
| 目标期刊政策页不可访问 | 用本文件官方入口 + 已知模板先占位；投稿前刷新 | policy URL blocked | Stage 9 checklist 未完成 |
| AJS 未安装 / 无精确期刊 skill / 调用失败 | 写 `09_submission/ajs/adapter_report.md` 标 `not_installed` / `no_exact_match` / `failed`，继续 `paper-submission` + 官网核验 + `reference-verify` | 发现方式、候选 pack、错误与降级原因 | AJS 本身不阻断；官网规则未核则 Stage 9 仍不得 `ready` |

---

## 2.1 独立安装也能执行的路线

只 clone 本仓库时，不要求 `67/` 工具箱存在。先发现真实可用的工具和技能；不存在就记录，
按下表读取当前阶段手册、使用可验证的本地代码完成任务。没有 Agent 时主代理串行执行。

| 阶段 | 本仓库执行依据 | 必须得到的证据 |
|---|---|---|
| idea → 可行研究问题 | `literature-and-positioning.md`、`stage-playbook.md` Stage 1 | 从用户约束列少量可比较问题；文献检索记录、数据可得性、分析单位、可估计量与识别威胁；不以“新颖度自评分”代替查新 |
| data → 可审计样本 | `measurement-and-data-quality.md`、`data-governance.md` | 保留 raw；实际运行导入/合并/清洗脚本；审计主键、合并倍增、时间单位、缺失和流失；codebook 与样本流量对齐 |
| 设计 → 估计 | `design-gate-cards.md`、`inference-and-uncertainty.md` | 按设计选真实统计包；报告系数、标准误/区间、N、聚类数、模型与样本 ID、诊断及运行命令；不能用默认 OLS 代替所有设计 |
| 结果 → 表图 → 正文 | `analysis-backends.md`、`writing-craft.md`、`integrity-and-claim-audit.md` | 同一结果对象生成表图与数字；正文主张连到 evidence ledger，空结果照实写；无证据不能补出发现 |
| 修订 → DOCX | `stage-playbook.md` Stage 6–9、`analysis-backends.md` §4.2 | 数字/引用复核；全文组装；结构与 freshness 检查；实际逐页渲染审阅；报告审核方式与剩余问题 |

只有 idea 而数据尚不可得时，交付可执行 proposal、数据获取与分析计划，以及明确缺数据的草稿；
不把模拟结果写成实证发现。有数据但无法建立可信识别时，按用户目的改为描述性/预测性研究并说明范围，
不继续换模型寻找显著性。描述性估计要定义总体/抽样权重；预测研究要按时间/实体划分验证集、防止泄漏；
它们不需要虚构处理组。社会学、教育学、政治学等使用各自构念、测量和投稿规范，不自动套 AER 标准。

`pw check` 检查现有状态一致性；`pw exit N` 要求该阶段工作完成；`pw final` 要求所有投稿义务完成。
可在方法受阻时生成标明“未完成研究”的 DOCX 供讨论，但相关 gate 保持 pending/not_pass，
最终报告清楚区分“文件已生成”“内容已审阅”“研究达到投稿标准”。


## 3. 记录格式

追加到 `logs/stage_<N>.md`：

```markdown
## Runtime fallback — <YYYY-MM-DD HH:MM Beijing>

- Missing dependency:
- Tried:
- Fallback used:
- Analysis backend before / after:
- Backend capability report: 00_meta/backend_capabilities.json
- Output files affected:
- Research claim affected: no / yes, describe
- Gate impact:
- Follow-up before submission:
```

写入 `workflow_state.json.decisions`：

```json
{
  "stage": 3,
  "decision": "StatsPAI unavailable; used PyFixest route for FE regression and retained identical method artifacts",
  "at": "2026-06-20 18:30"
}
```

---

## 4. 质量封顶规则

- 关键 policy、citation、data source 未联网刷新：引用真实性或复现维度最高 7，且 Stage 9 checklist 不能
  标 `ready`。
- 撤稿筛查或 `bibtex`/DOI 解析降级，`citation_integrity_log.md` §1 仍有 `to-verify`：引用真实性维度最高 7，
  且 `python3 scripts/check_citation_integrity.py <workspace> --final` 不得通过；real-time/vintage 源不可访问
  导致 look-ahead 无法排除时，相关结论封顶 `descriptive`（同步 evidence ledger）。
- 工具缺失导致缺少方法最低证据包：识别维度最高 6；若 `method_gate.md` 为 `NOT PASS`，识别维度最高 4。
- 工具缺失导致 design-risk threat 无法关闭：`design_risk.status` 标 `not_pass` 或在 claim consequence 中降级；
  不能把未知 spillover、attrition、external validity 或 specification-search 风险写成已排除。
- 只能用合成/样例数据验证代码结构，不能访问真实数据：结果、稳健、复现维度均不得超过 6。
- 无法执行 master script，也没有逐步复现命令：复现维度最高 6。
- 退化路径没有写日志：相关维度最高 7；若影响主 claim 却未披露，最高 4。

---

## 5. 给 subagent 的最短指令

当某个 subagent 可能遇到环境缺失时，把下面这段放进 prompt：

```text
如果指定 Skill/MCP/软件不可用，不要凭记忆脑补结果。按
skills/69-Paper-WorkFlow/references/runtime-fallbacks.md 选择 fallback：
优先 Read 对应 SKILL.md 或用等价本地包复刻同等 artifact；把 fallback 写入 logs/stage_<N>.md；
若最低证据包或 design-risk ledger 无法生成，把 method_gate / design_risk / quality_gate 标 NOT PASS，
并只回传阻断摘要。
```
