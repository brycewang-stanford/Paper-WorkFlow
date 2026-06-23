# 初稿质量门 · 7 维评分卡（Draft Quality Rubric）

> 这是本编排器把「**高质量**初稿」从口号变成可验收闸门的标尺。Stage 7 之后、Stage 8 之前，由一个
> 独立的「顶刊 AE」critic subagent 拿这份 rubric 给初稿打分（派发模板见
> [`subagent-templates.md`](subagent-templates.md) §QG），结果写入 `00_meta/quality_scorecard.md`。
>
> **打分纪律**：① 只依据稿件与工作区里的**真实产物**（`main.tex`、表图、`results/summary.md`、
> `proposal.md`、`sample_audit.md`、`design_register.md`、`method_gate.md`、`evidence_ledger.md`、
> `ref.bib`、`data_governance.md`），不脑补；② 每维先找证据再给分，分数后面必须附 1–2 句**带行号/表号的
> 具体依据**；③ 命中「致命红旗」直接把该维封顶到 ≤ 4 分，无论其它方面多好；④ 宁可严格，不可放水
> ——质量门的意义就是拦住「跑完了但不够格」的稿子。

---

## L1 / L2 两级评审（这份 rubric 在第几层）

质量门是**两级**的，本 rubric 是其中的 **L2**：

- **L1 — 结构层（可执行）**：`scripts/check_workspace_gates.py` 等 checker 机械校验「闸门标了 pass，证据就必须
  在盘上、上下游顺序不许颠倒」。L1 不判断好坏，只判断**结构自洽**。L1 不绿，L2 不得 PASS。
- **L2 — 语义层（critic 判断）**：本 rubric——由「顶刊 AE」critic 判断脚本判断不了的可信度。

> 对标 Orchestra 的「ARA 印章」也是结构/语义两级，但**它的两级都是 LLM 读清单自评**；我们的 L1 是真代码、
> L2 的产出又被 `scripts/check_review_scorecard.py` 反过来机械校验（见下「评分卡机械校验」）。这就是差异化：
> **严谨性可执行，而非自评散文。**

**严重度三档（severity）**——每条 finding 必须归一档，对应本 rubric 既有的「致命红旗」：

| 严重度 | 含义 | 闸门后果 |
|---|---|---|
| **blocking** | 致命红旗 / 硬不一致 | 该维封顶 ≤4；只要还在，**PASS 不可能** |
| **major** | 投稿前必须修的实质缺陷 | 不单独逼停 PASS（若该维仍 ≥7） |
| **minor** | 打磨项 | 不影响闸门 |

**逐条 finding 必须带 verbatim 证据 span**：任何红旗 / 封顶 / blocking，都必须在评分卡的「Findings Register」里
**原文引用它针对的那句稿件或 artifact 文本** + locator（file:line / 表号 / claim-id）。**没有 verbatim 引用的
finding 不予采信**——这是反幻觉装置：critic 不能凭印象说「引言过度声称」，必须把那句话原样贴出来。

**评分卡机械校验**：评分卡写成 [`templates/quality_scorecard.md`](../templates/quality_scorecard.md) 结构后，跑
`python3 scripts/check_review_scorecard.py <workspace>`。它机械验证：7 维都给了 0–10 分、每条 finding 有
severity + 非占位 verbatim + locator、blocking finding 的维度分必须 ≤4、声明 PASS 必须与分数自洽（每维 ≥7、
总分 ≥56、register 无 blocking）。返回非零即评分卡内部不自洽，必须修正再放行。

---

## 0. 评分尺度（所有维度通用锚点）

| 分段 | 含义 | 顶刊语境下的画像 |
|---|---|---|
| **9–10** | 顶刊水准 | 放进 JF/JFE/RFS/QJE/AER/MS 的当期也不掉档 |
| **7–8** | 达标（质量门门槛） | 扎实的 field journal 水准，硬伤已清，主要是打磨空间 |
| **5–6** | 半成品 | 有明显短板，需要实质修订才能投稿 |
| **3–4** | 不及格 / 命中红旗 | 存在会被 desk-reject 或一审毙掉的硬伤 |
| **0–2** | 缺失 | 该维内容基本不存在或完全站不住 |

**达标线（三个条件同时满足才算 `pass`）**：
1. **每一维 ≥ 7**；
2. **总分 ≥ 56 / 70**；
3. **第 ②（识别）③（稳健）⑥（引用）维都没有任何「致命红旗」**——这三维是实证论文的命门，带病不放行。

---

## 维度 ① 选题与贡献锋利度（Contribution Sharpness）

**测什么**：贡献是否清晰、单一、可被五年后的综述引用；是否踩中 Edmans (2024) "1000 Rejections" 红线。

**评分锚点**
- **9–10**：一句话能说清「我们第一个证明了 X」，贡献落在文献的真实空白，反直觉或有 trade-off 张力。
- **7–8**：贡献明确且非平凡，但新意更多来自新数据/新场景而非新机制。
- **5–6**：贡献能讲，但偏「又一个 determinant」或增量较薄。
- **≤4**：命中致命红旗。

**致命红旗（命中即 ≤4）**
- **Convex combination**：X→Z 已知 + Z→Y 已知 → X→Y 只是 trivial 推导。
- **Just-another-determinant**：通篇只证明「X 是 Y 的又一个驱动因素」，无机制/无张力。
- **地理复制**：「把 US 做过的搬到国家 Z 再做一遍」，无本土制度性新意。
- **Survey test 不过**：五年后该主题的综述不会专门用一段引用本文。

**回退**：→ Stage 1（重收选题漏斗 / 换差异化切口 / 强化贡献句）。

---

## 维度 ② 识别可信度（Identification Credibility）

**测什么**：因果识别策略是否真的成立，而非贴个 DiD/IV 标签了事。

**评分锚点**
- **9–10**：识别假设被正面检验且通过（平行趋势事件研究图干净、IV 既相关又有可信排他性叙事、RDD
  密度无操纵），并预先排除了主要混淆。
- **7–8**：识别策略恰当、核心诊断到位，排他性/外生性叙事可信但非铁证。
- **5–6**：策略合理但关键诊断缺失或偏弱（如只给平均处理效应、没给事件研究）。
- **≤4**：命中致命红旗。

**方法闸门联动**
- 找不到 `03_analysis/design_register.md`：本维封顶 6。
- 找不到 `02_data/sample_audit.md`：本维封顶 6。
- `sample_audit.md` 为 `NOT PASS` 或暴露 estimation sample 与 estimand 不一致但未改写 claim：本维封顶 4。
- 找不到 `03_analysis/method_gate.md`：本维封顶 6。
- `method_gate.md` 为 `NOT PASS`：本维封顶 4。
- 找不到 `00_meta/evidence_ledger.md`，或 ledger 没有把主因果 claim 指到 result / exhibit / script：
  本维封顶 6。
- ledger 的 claim strength 低于正文措辞（例如 ledger 只允许 descriptive，正文写 causal effect）：
  本维封顶 4。
- 找不到 `03_analysis/design_risk_ledger.md`：本维封顶 6。
- `workflow_state.json.design_risk.status = not_pass`，或 design risk ledger 仍有 blocking threat：本维封顶 4。
- external validity / transport 边界未写清，但正文或 cover letter 写成一般政策结论：本维封顶 6。
- 方法标签缺 [`research-grade-methods.md`](research-grade-methods.md) 对应最低证据包：本维最高 6。
- 方法闸门记录了 runtime fallback，但缺 [`runtime-fallbacks.md`](runtime-fallbacks.md) 要求的等价 artifact：
  本维最高 6；若 fallback 影响主因果 claim 却未披露，本维最高 4。
- 关键数据的合法访问、IRB/DUA 或公开包边界未知，且影响 estimand 或样本选择：本维最高 6。
- treatment timing、missingness/balance/overlap、cluster level 或 weights 未通过样本审计，且影响主结果：
  本维最高 6。
- 弱工具（effective F 远低阈值）只报 2SLS t 比、无 AR/tF 区间，或处理只落少数 cluster 却无随机化推断
  交叉验证（[`inference-and-uncertainty.md`](inference-and-uncertainty.md) §3/§6）：本维最高 6。
- 主设定含后处理中介 M 当控制（[`mechanism-and-channels.md`](mechanism-and-channels.md) §3 坏控制）：本维封顶 4。

**致命红旗（命中即 ≤4）**
- **平行趋势证据缺失或明显违背**，却仍按 DiD 解读因果。
- **弱工具**：第一阶段 F 远低于经验阈值（如 < 10 甚至更激进的近期标准），或排他性叙事不成立。
- **交错 DiD 未处理负权重**：多期、异时点处理却仍用双向固定效应 TWFE，未用 CS/SA/BJS 等稳健估计量。
- **RDD 操纵未检验**或密度检验显著不连续却无视。
- **把相关性当因果**：无可信外生变异，却通篇因果措辞。

**回退**：→ Stage 3（补诊断 / 换识别策略 / 换工具 / 换对照），严重时 → Stage 1 改设计。

---

## 维度 ③ 稳健性完整度（Robustness Completeness）

**测什么**：主结果是否经得起合理的扰动；稳健性矩阵是否覆盖到位且**真实跑出来**。

**评分锚点**
- **9–10**：稳健性矩阵系统覆盖——安慰剂/证伪检验、替换度量、替换样本、增减控制、改聚类层级、
  子样本异质性、机制中介——且主结论在其中稳定；异常处反而能解释。
- **7–8**：覆盖主要威胁，主结果稳定，少数次要检验可补。
- **5–6**：只有零星稳健性，关键威胁（如遗漏变量/选择性样本）未应对。
- **≤4**：命中致命红旗。

**方法闸门联动**
- `method_gate.md` 缺失：本维封顶 6。
- `method_gate.md` 列出缺失必需 artifact 但正文仍说稳健：本维封顶 5。
- 稳健性矩阵没有对应 `03_analysis/robustness/` 真实文件：本维封顶 5。
- `design_risk_ledger.md` 命中的 OVB、选择、spillover/SUTVA、attrition、specification-search 或多重检验风险
  缺对应诊断 artifact，且没有在 claim consequence 中降级：本维封顶 5。
- `sample_audit.md` 的 final estimation sample、N、treated/control 数或 cluster level 与主结果/表图不一致：
  本维封顶 5。
- 聚类口径换了显著性就翻却只报最有利的一个、或 few-cluster（G≲30–50）仍只报渐近 SE 无 wild bootstrap/CR2，
  或多 outcome/多子样本无族内校正却挑显著讲故事（[`inference-and-uncertainty.md`](inference-and-uncertainty.md) §2/§3/§5）：本维封顶 5。

**致命红旗（命中即 ≤4）**
- **稳健性结果与主表数字对不上 / 疑似挑样本拼出来的**（p-hacking 嫌疑）。
- **SE 聚类层级错误**（如政策在省级却按个体聚类）导致显著性虚高。
- **结果不显著却被写成显著**，或反向回退分支未执行就硬写成功。
- 表中数字与 `03_analysis/results/summary.md` 的真实运行结果**不一致**。

**回退**：→ Stage 3（补稳健性 subagent 矩阵 / 修聚类 / 据 StatsPAI `audit_result` 补缺）。

---

## 维度 ④ 结果与解读克制度（Interpretation Discipline）

**测什么**：结果段是否就事论事、不过度解读、效应量有经济意义解释、不把统计显著当重要性。

**评分锚点**
- **9–10**：每个系数都给经济量级解读（占均值/标准差几成），区分统计显著与经济重要，谨慎对待外推。
- **7–8**：解读基本克制，个别地方略有拔高。
- **5–6**：频繁把显著当「重大影响」，缺经济量级，因果语气过满。
- **≤4**：通篇过度解读 / 政策建议远超证据能支撑的范围。

**Evidence ledger 联动**
- 摘要、引言主贡献、结果段或结论中的每个 empirical claim 都必须能在 `00_meta/evidence_ledger.md` 找到
  Claim ID、allowed wording、primary evidence、exhibit 和 script。
- `evidence_ledger.md` 的 Open Discrepancies 有 blocking 项且影响主结论：本维封顶 5。
- 任何 policy implication 超过 Estimand-to-Claim Map 的 population/time/treatment boundary：本维封顶 6。
- 任何 policy implication 超过 `design_risk_ledger.md` 的 external-validity 或 transport boundary：本维封顶 6。
- 通篇只报星标、不报 CI、把统计显著当经济重要、用「marginally significant」当证据
  （[`inference-and-uncertainty.md`](inference-and-uncertainty.md) §7）：本维封顶 6。
- 机制用因果措辞却无 sequential ignorability 说明/敏感性，或「系数下降即渠道」无 Gelbach 正式分解
  （[`mechanism-and-channels.md`](mechanism-and-channels.md) §3/§4）：本维封顶 6。

**回退**：→ Stage 5/6（改写结果与结论段，配 `paper-self-revise` / `readability`）。

---

## 维度 ⑤ 写作与结构（Writing & Structure）

**测什么**：引言张力、结构完整、逻辑连贯、表图自解释、行文符合经济学规范。

**评分锚点**
- **9–10**：引言四段式（问题—难点—做法—贡献）张力十足；各节衔接自然；表图注齐全自解释。
- **7–8**：结构完整、可读，引言贡献句清晰，少量段落待打磨。
- **5–6**：结构齐但平铺直叙，引言不抓人或贡献埋没，表图注不全。
- **≤4**：结构残缺（缺识别/稳健性章节）、或表图无法自解释、或前后自相矛盾。

**回退**：→ Stage 5（重写薄弱章节）/ Stage 6（`paper-pipeline` 打磨）/ Stage 4（补表图注）。

---

## 维度 ⑥ 引用真实性与文献定位（Citation Fidelity & Positioning）

**测什么**：引用是否真实存在、与论点匹配、是否引对（非撤稿、非二手转引）；论断是否存在**时序穿越**
（look-ahead / 用 final 修订值冒充实时可得 / 训练-测试时序泄漏）；文献综述是否准确定位本文贡献。

**评分锚点**
- **9–10**：引用全部真实、年份/作者/出处准确，关键文献无遗漏，定位精准（说清相对谁前进了一步）。
- **7–8**：引用真实、定位清楚，个别次要文献可补。
- **5–6**：文献定位偏弱或有少量元数据错误。
- **≤4**：命中致命红旗。

**致命红旗（命中即 ≤4）**
- **存在编造/张冠李戴的引用**（幻觉文献、作者或年份错配、引用与论点不符）。
- **引用了已撤稿 / 勘误后失效的结果**当作有效证据。
- **时序穿越未排除却作主因果论断**（look-ahead / 用 final 修订值冒充实时可得 / 训练-测试时序泄漏）。
- 关键对标文献缺席，导致贡献被高估。

> 引用存在性（DOI / 撤稿 / 版本核验）与时序完整性的逐项标准见
> [`citation-and-temporal-integrity.md`](citation-and-temporal-integrity.md)，落 `00_meta/citation_integrity_log.md`，
> 终审跑 `python3 scripts/check_citation_integrity.py <workspace> --final`。（claim↔证据忠实另由
> [`integrity-and-claim-audit.md`](integrity-and-claim-audit.md) 审计。）

**回退**：→ `reference-verify`（终审核验）+ Stage 5 文献综述（配 `36`/`52`/`59` 补做结构化综述）。

---

## 维度 ⑦ 可复现性与治理（Reproducibility & Governance）

**测什么**：从原始数据到表图能否被第三方一键复跑；数据来源、版权、受限访问、PII、IRB/DUA 与
公开 archive boundary 是否交代清楚。

**评分锚点**
- **9–10**：清洗 + 估计 + 建表脚本齐全、`codebook.md` 和 `sample_audit.md` 完整、`design_register.md` 与 `method_gate.md`
  能解释每个方法 artifact，`FINAL_REPORT.md` 有一键重跑命令；`00_meta/data_governance.md` 与 DAS 清楚说明
  public/restricted/confidential 数据边界，不可分发数据只留拉取脚本与说明。
- **7–8**：脚本基本齐全，少量手工步骤未脚本化。
- **5–6**：有代码但缺 codebook / sample audit 或重跑路径断裂。
- **≤4**：结果无法从工作区代码复现，或数据来源/版权完全未交代。

**AEA/AEJ/AER 场景加严**：若目标期刊属于 AEA 体系但没有 data availability statement、data provenance、
访问成本/权限说明、运行时间说明，本维最高 7；若完全没有 replication README，本维最高 6。
若目标为 Management Science / INFORMS 且缺 AsCollected disclosure 或等价 code/data disclosure plan，
本维最高 7。

**数据治理加严**
- 找不到 `00_meta/data_governance.md`：本维最高 7。
- 使用 restricted/confidential/PII 数据但没有访问边界、DUA/IRB/ethics、再分发说明：本维最高 6。
- 公共复现包、日志、表格或示例中出现 PII、token、签名 URL、受限原始数据：本维最高 4，且投稿包不得
  标 ready。
- IRB/DUA/许可证状态未知，或目标刊政策页未刷新：`workflow_state.json.replication_pack.status` 只能是
  `not_ready`。

**运行时 fallback 加严**
- 无法执行 master script，也没有逐步复现命令：本维最高 6。
- 只能用合成/样例数据验证代码结构，不能访问真实数据：本维最高 6。
- 网络/政策/引用核验工具不可用且未按 [`runtime-fallbacks.md`](runtime-fallbacks.md) 记录：本维最高 7；
  若影响主结论却未披露，本维最高 4。

**状态文件联动**
- `workflow_state.json.replication_pack.status` 缺失或为 `pending`：本维封顶 7。
- `replication_pack.status = not_ready`：本维封顶 6；若阻断原因涉及无法重建主表图，本维 ≤4。
- 没有 `replication_pack.master_script` 或 `last_rebuild_check` 为空：本维封顶 7。
- `workflow_state.json.evidence_governance.status = not_pass` 或
  `evidence_governance.open_discrepancies` 仍有 blocking 项：本维封顶 6。

**回退**：→ Stage 2（补 codebook / 清洗脚本）/ Stage 3（补估计脚本）/ 收尾（补一键重跑命令）。

---

## 评分卡输出格式（critic subagent 写入 `00_meta/quality_scorecard.md`）

```markdown
# 初稿质量门评分卡 — <研究短名>
评分轮次: round <k>    评分时间(北京): <YYYY-MM-DD HH:MM>    评分人: 质量门 critic subagent

| 维度 | 分数/10 | 关键依据（带行号/表号） | 命中致命红旗? |
|---|---|---|---|
| ① 选题与贡献锋利度 | 8 | 贡献句见 §1 第 3 段，落在 X 空白；无 convex 嫌疑 | 否 |
| ② 识别可信度 | 7 | 事件研究图 Fig.2 平行趋势干净；IV 一阶段 F=23 | 否 |
| ③ 稳健性完整度 | 6 | 缺替换聚类层级与子样本异质性两项 | 否 |
| ④ 结果与解读克制度 | 8 | 系数均给经济量级（§5 Table 3 下方） | 否 |
| ⑤ 写作与结构 | 8 | 引言四段式到位；§4 衔接略生硬 | 否 |
| ⑥ 引用真实性与文献定位 | 9 | reference-verify 全绿，定位见 §2 | 否 |
| ⑦ 可复现性与治理 | 8 | 脚本齐、codebook 全、待补一键重跑命令 | 否 |
| **总分** | **54 / 70** | — | — |

## Findings Register（每条带 severity + verbatim span + locator）

| ID | Severity | Dim | Verbatim evidence span | Locator | Required fix |
|---|---|---|---|---|---|
| F1 | major | 3 | "we cluster standard errors at the firm level" | main.tex:212 | 政策在省级，补省级聚类稳健性 |
| F2 | minor | 5 | "Section 4 turns to the mechanism." | main.tex:188 | §4↔§5 衔接重写一段 |

## 达标判定
- 每维 ≥ 7? **否**（③ = 6）
- 总分 ≥ 56? **否**（54）
- ②③⑥ 无致命红旗? **是**
- **结论: NOT PASS（卡在维度 ③ 稳健性）**

## 最关键的 3 条短板（按回退优先级）
1. [③→Stage 3] 补「替换聚类层级 + 子样本异质性」两项稳健性 subagent。
2. [⑤→Stage 6] §4 与 §5 衔接重写一段。
3. [⑦→收尾] 在 FINAL_REPORT 写一键重跑命令。

## 回退指令（主代理据此调度）
- 本轮回退到: **Stage 3**（次要短板 ⑤⑦ 顺带在其回合处理）
- 累计回退轮次: 1 / 2
```

---

## 可复现的 LLM-as-judge 协议（让"AE critic"不只是凭感觉）

质量门本质是一个 **LLM-as-judge**：派一个 critic subagent 当"顶刊 AE"给初稿打分。裸 LLM 评审有两个
硬伤——**不可复现**（两次跑可能给不同结论）和**可作弊**（一个心软的 critic 在分数不达标时照样写 PASS）。
open_deep_research 给它的 Deep Research Bench 评审定了规矩才可信：固定 judge prompt + 冻结的 gold
标准报告 + 当作 dataset 跑的打分脚本。本节把同样的工程搬到质量门，分两层：

**第 1 层 · 判定是纯算术，可被独立重算。** 上面的达标线（每维 ≥7 且总分 ≥56 且 ②③⑥ 无致命红旗 且
Stage 7 claim-integrity pre-review 干净）不依赖 critic 的"判断"，而是一条确定性规则。critic 写完
`00_meta/quality_scorecard.md` 后跑：

```bash
python3 evals/check_quality_judge.py --scorecard 00_meta/quality_scorecard.md
```

它会**独立重算**总分与 PASS/NOT_PASS，并机械抓出三类"评分卡不守自己规矩"的情形：总分对不上各维之和、
某维命中红旗（标"是"）却给了 >4 分（违反封顶规则）、以及 critic 写的结论与规则重算结果矛盾。任何一项
不一致即非零退出——评分卡的**簿记**从此不可糊弄。（pre-review 有 blocking finding 时加
`--integrity-not-clean`，让判定把诚信联锁也算进去。）

**第 2 层 · 规则对照 gold 校准。** [`../evals/quality_calibration.json`](../evals/quality_calibration.json)
冻结了一组**金标准锚点评分卡**（含本文件上面那张 total=54 的示例、一张刚好 55 分的边界卡、一张识别红旗
封顶卡、一张诚信阻断卡），每张都标了规则**必须**给出的结论。`check_quality_judge.py` 的校准会断言确定性
判定能复现每个锚点——也就是说，如果有人改了散文里的阈值（比如把 56 改成别的数），校准会立刻失败，逼你把
规则和锚点重新对齐。这让"达标线"本身成为一个**被测量的不变量**，而不是会随手漂移的口号。

```bash
python3 evals/check_quality_judge.py --calibration   # 跑金标准校准
python3 evals/check_quality_judge.py --selftest       # 验证判定器与解析逻辑本身
```

> 它**不替** critic 判分（读稿给每维打分仍是不可约的阅读任务）；它让**分数周围的一切**可复现：算术、
> 红旗封顶、诚信联锁、最终结论。critic 仍要按本 rubric 逐维找证据给分，但它再也不能写出一张自相矛盾的卡。

---

## 「短板 → 回退阶段」速查（主代理据此路由）

| 卡在哪一维 | 回退到 | 主要动作 |
|---|---|---|
| ① 贡献 | Stage 1 | 重收选题漏斗 / 强化贡献句 / 换差异化切口 |
| ② 识别 | Stage 3（重则 Stage 1） | 补诊断 / 换识别策略 / 换工具或对照 |
| ③ 稳健 | Stage 3 | 补稳健性矩阵 subagent / 修聚类 / StatsPAI `audit_result` 补缺 |
| ④ 解读 | Stage 5/6 | 重写结果与结论段，克制因果语气 |
| ⑤ 写作 | Stage 5/6（表图问题→Stage 4） | 重写薄弱章节 / `paper-pipeline` 打磨 / 补表图注 |
| ⑥ 引用 | `reference-verify` + Stage 5 | 终审核验 / 补结构化文献综述 |
| ⑦ 复现与治理 | Stage 2/3/9 + 收尾 | 补 codebook / 脚本 / 一键重跑命令 / DAS / 数据治理登记 |

**回退上限**：同一维最多回退 **2 轮**。2 轮后仍不达标 → 在 `logs/quality_gate.md` 记「已知短板」，
质量门摘要卡里**显著标红**告知用户，由用户裁决是否带病进入 Stage 8/9（绝不静默放行）。
