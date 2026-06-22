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
| 选定分析后端不可用 | 按 `analysis-backends.md` 切到能复刻同等 artifact 的另一后端；若用户硬性指定则暂停确认 | 原后端、替代后端、差异 | artifact parity 齐则可过；否则 Method Gate `NOT PASS` |
| StatsPAI MCP 不可用 | 用 `statspai` 包或 Stata/R/Python 包复刻同等 artifact；写明包版本 | 缺失 MCP、替代 route | 若最低证据包齐，方法门可过 |
| Stata 不可用 | 若 Stata 是用户指定主后端，先记录 blocked；可用 Python/R 等价实现做 fallback 或 secondary validation | Stata 版本缺失、替代包 | 关键 artifact 缺失则 Method Gate `NOT PASS` |
| R/Python 包缺失 | 建安装脚本；若不能安装，用同类包或另一后端但保留差异说明 | 包名、版本、替代 | 数字不可复核时不得放行 |
| LaTeX / PDF 工具缺失 | 生成 `.tex`、`.md`、`.docx` 替代；投稿前补 PDF render | 缺失命令 | 写作可继续，submission checklist 不可过 |
| 受限数据不可访问 | 用公开样例/合成数据跑代码结构；真实估计标 blocked | 数据访问限制 | 主结果不可声称真实；复现 `not_ready` |
| 目标期刊政策页不可访问 | 用本文件官方入口 + 已知模板先占位；投稿前刷新 | policy URL blocked | Stage 9 checklist 未完成 |

---

## 3. 记录格式

追加到 `logs/stage_<N>.md`：

```markdown
## Runtime fallback — <YYYY-MM-DD HH:MM Beijing>

- Missing dependency:
- Tried:
- Fallback used:
- Analysis backend before / after:
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
