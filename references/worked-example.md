# Worked Example — 一条完整的「黄金路径」端到端跑通示例

> 本文件把抽象的 10 阶段 + 2 闸门**落成一条具体的 trace**：用一个示例研究问题，逐阶段展示
> **每步调了什么 skill、产出了哪个文件、文件里大概长什么样、闸门检查了什么、遇到回退怎么切**。
> 它有两个用途：① 给用户看「跑完到底得到什么」；② 给编排器当**填空范本**——`proposal.md`、
> `design_register.md`、`method_gate.md`、`quality_scorecard.md`、`response_letter.md` 该写成什么样，
> 照着仿写即可。
>
> **⚠️ 关于数字**：本文件里所有系数、SE、分数都标了「示意」`<illustrative>`，是**占位演示**，不是真实
> 估计结果。真实运行时这些数字必须来自 `03_analysis/` 的真实估计（本编排器的铁律：**真实优先，绝不
> 编造**，见 [SKILL.md](../SKILL.md)「关键约束」）。本示例只示范**流程与产物形态**，不示范结论。

---

## 0. 示例设定

| 项 | 值 |
|---|---|
| **研究问题** | 中国绿色信贷政策对企业（绿色）创新的影响 |
| **用户输入** | 「我想做绿色信贷政策对企业创新的影响，目标期刊《经济研究》或 *J. of Corporate Finance*」 |
| **入口路由** | 只有一句话方向 → **从 Stage 1 进入**（完整选题漏斗） |
| **交互档位** | `阶段确认`（缺省推荐） |
| **目标期刊** | 主：*Journal of Corporate Finance*；备：《经济研究》（双语候选池） |
| **语言** | 中英双语（先英文稿，后出中文版） |
| **分析后端** | `python-statspai`（缺省；Stata/R 可在 Stage 0 改选） |

> 触发后 Stage 0 静默完成：取北京时间、判入口、`AskUserQuestion` 一次问清五件套、`init_workspace.sh`
> 铺骨架、写 `00_meta/workflow_state.json`（`entry_stage=1, mode=stage-confirm`）。

---

## 1. Stage 1 · 选题与设计 → `01_proposal/proposal.md`

**调用**：`econfin-idea-finder`（输出重定向到 `01_proposal/candidates/`）→ 并行 subagent 各调
`Econfin-Proposal`+`novelty-check` → `Significance-Search` → `journal-digest`（重定向）。Stage 1 同时加载
[`literature-and-positioning.md`](literature-and-positioning.md) 做结构化检索 + 文献矩阵。

### Stage 1L · 文献基座（先于查新打分）

5 路并行 subagent 各走一条检索通路（关键词 / 引文滚雪球 / 顶刊目录 / 对照设计 / 中文专线），
去重后 `01_proposal/lit/corpus.md` 收 118 条、核心集 12 条。**查新分数就是对着这 12 条打的**——
`novelty-check` 给 9.2 分时注明「相对 JCF 2023 / HSSC 2024 / FRL 2024 三条前作」，分数因此可复核。
`literature_base.reused_by` 最终记满三项：`novelty`（本阶段）、`related_work`（Stage 5）、
`reference_verify`（Stage 9 用 corpus 当白名单，筛出 1 条 `ref.bib` 里查无实据的条目）。

**文献矩阵**（`01_proposal/lit/lit_matrix.md`，节选）让白space可见：

| Citation | Setting | Identification | Outcome | Relation to us |
|---|---|---|---|---|
| JCF 2023 (green credit obstacles) | 中国 A 股 | 2012 GCG DiD | 融资约束 | 他们看融资约束，我们看**绿色创新产出** |
| HSSC 2024 (real vs fake green) | 中国 A 股 | DiD | ESG 表现 | 他们提「策略性漂绿」，我们**区分实质 vs 策略性绿色专利** |
| FRL 2024 | 中国 A 股 | DiD | 绿色创新 | 他们只看总量，我们做**专利质量分解 + HonestDiD** |

→ 白space：**区分实质性 vs 策略性绿色创新，并用现代 DiD 稳健性（HonestDiD）做识别**。

**贡献句**（按 [`writing-craft.md`](writing-craft.md) §3 三槽 + [`literature-and-positioning.md`](literature-and-positioning.md) §4）：
> 我们是第一个**区分**绿色信贷政策对**实质性**与**策略性**企业绿色创新差异影响的研究；相对最接近的
> FRL(2024)，增量在于**绿色专利质量分解 + 现代 DiD 稳健性**；这一点重要，因为「漂绿」会让总量效应高估
> 政策的真实环境收益。

**critic 审阅**（`01_proposal/critique.md`）：用 Edmans 红线查——非 convex（机制是「信贷约束→创新方向重配」
而非 trivial 推导）、非 just-another-determinant（有「质量 vs 数量」张力）、非纯地理复制（有制度性新意）。
✅ 贡献过关。

**定稿 `proposal.md` 写死合同**：
```
Y = 企业绿色创新（绿色专利申请数，分实质性[发明]/策略性[实用新型]）
X = 受绿色信贷政策约束（两高行业 × 2012 后）
M = 信贷融资约束（机制）
识别 = 政策 DiD（2012 绿色信贷指引，两高行业为处理组）
样本 = 中国 A 股上市公司 2007–2021
目标期刊 = JCF（主）/《经济研究》（备）
```

**阶段闸门摘要卡**（阶段确认档）：3 个 ≥9 分候选 → 用户选定上述题；红旗：无。→ 放行 Stage 2。

---

## 2. Stage 2 · 数据 → `02_data/clean.parquet` + `codebook.md` + `sample_audit.md`

**调用**：`data-fetcher` → `data-cleaning`；同时加载 [`reproducibility-pack.md`](reproducibility-pack.md) §2
从这一步就记 provenance。

**数据源 + provenance**（`02_data/codebook.md`，每源一条）：
- 企业财务：**CSMAR**（注册后下载，付费机构授权）→ 不可随包分发，只留拉取脚本。
- 绿色专利：**CNRDS 绿色专利库** + CNIPA（按 WIPO IPC 绿色清单标记）。
- 两高行业清单：**生态环境部重污染行业目录**（2008 分类）映射到 CSRC 行业码。

**派生变量**：`green_patent_app`（绿色专利申请数+1 取对数）、`treat`（两高=1）、`post`（≥2012=1）、
控制集（size, lev, age, roa, soe，**均为处理前度量**——按 [`threats-to-validity.md`](threats-to-validity.md) §3
标注「前处理」，无后处理变量进主设定）。

**⚠️ 时序回退演示（look-ahead）**：初版 codebook 把 size/lev/roa 取在**处理年（t=2012）年末**。按
[`citation-and-temporal-integrity.md`](citation-and-temporal-integrity.md) §2.2 落 `00_meta/citation_integrity_log.md`
§2 时发现：2012 年内的政策冲击使「年末」控制变量**偷看了处理后信息**（feature look-ahead），该行判 `risk`。
修复：控制集统一滞后到 **t−1（2011 年末）**，并在 `sample_audit.md` 与 evidence ledger 同步；重跑
`python3 scripts/check_citation_integrity.py <ws>` 的 §2 全部回到 `pass` 后才放行。绿色专利用**申请数**
（`green_patent_app`）而非授权数，规避「授权滞后回填到申请年」的另一处 look-ahead。

**sample_audit**：合并键（stkcd×year）唯一；raw→clean→estimation sample 的 N、treated/control 数、
2012 treatment timing、近似平衡面板、winsorize 1%、省级聚类数均已落表。✅ → 放行 Stage 2.5。

**测量效度**（[`measurement-and-data-quality.md`](measurement-and-data-quality.md)）：绿色专利用 IPC 绿色清单
识别，属**代理变量**——清单口径 2017 年扩容过一次，跨年不可比。处理：全样本统一用 2017 版清单回溯重编，
差异写进 `02_data/measurement_audit.md`，并把「测量误差（分类误差，可能低估处理效应）」这一行登记进
design risk ledger。

---

## 2.5. Stage 2.5 · 设计锁定 → `00_meta/preregistration.md`

数据到手、**一个估计都还没跑**的时点锁主设定。这是全流程唯一一个「什么都还看不到」的位置，
也正因如此它才有约束力。

```
locked: 2026-03-14 09:20 Asia/Shanghai
lock_commit: 7c1f9ab
locked_before_estimation: yes
primary_design: staggered DiD (2012 GCG rollout)

Confirmatory Hypotheses (2 条)
| H1 | 绿色信贷指引提高实质性绿色专利 | green_patent_sub | ATT | CS(2021) group-time; cluster=province | + |
| H2 | 对策略性绿色专利无显著影响       | green_patent_util| ATT | 同上                                   | 0 |

Primary Specification Lock
- main estimator: Callaway-Sant'Anna group-time ATT（not TWFE：交错处理）
- 控制集: 规模、杠杆、ROA、产权性质（**锁定；事后不再增删**）
- standard errors / clustering: cluster = province（30 个 → 同时报 wild bootstrap）
- multiple-testing plan: 2 个 outcome 做 Romano-Wolf
- 异质性维度（预先指定）: 产权性质、地区环境规制强度。**其余异质性一律 exploratory**
- MDE: 当前样本对 H1 的 MDE = 0.061（α=.05, power=.8）
```

派一个 §S2_5 审阅 subagent 挑「锁不住」的地方，它退回一条：控制集写着「必要时加入行业趋势」——
这是个未登记的研究者自由度，改成锁定「行业×年份固定效应」后再锁。

**锁之后发生了什么**：Stage 3 跑出来平行趋势对 `green_patent_util` 不成立，改用 stacked DiD。
这是**偏离**，登记进 Deviations 表（原因、时点、对 claim 强度的影响）。因为登记了，H2 仍算确认性结果；
若不登记，它只能降级为 exploratory。同一阶段还发现「地区数字化水平」的异质性很漂亮——
**它不在锁内，所以只能写成 exploratory**，不能进摘要当主发现。

**这一步买到了什么**：Stage 8 审稿人问「你们是不是试了很多设定」时，答案是一份带 commit hash、
时间戳早于所有结果的锁 + 一张偏离表，而不是一句「我们没有」。

---

## 3. Stage 3 · 识别、估计与方法闸门 → `03_analysis/` + 🔬 Method Gate

**先注册设计**（`03_analysis/design_register.md`，按 [`research-grade-methods.md`](research-grade-methods.md) §2）：
```
Estimand: ATT（两高企业因政策的绿色创新增量）
Treatment: 两高行业 × post-2012；Comparison: 非两高 A 股企业
识别假设: 平行趋势（政策前两高/非两高绿色创新趋势平行）
主估计量: TWFE DiD（firm + year FE, 省级聚类）
必需诊断: 事件研究图、预趋势功效、HonestDiD、PSM-DiD、安慰剂时点
替代估计量: PSM-DiD；若交错性显现 → Callaway-Sant'Anna
失败回退: 预趋势不过 → HonestDiD 报破点 + 缩 claim / 换 PSM-DiD
```

**估计 + 稳健性矩阵并行**（§S3 模板，每个 subagent 自己写盘到 `03_analysis/robustness/`）：
- 基准 TWFE：`treat×post` 系数 `0.18***`<illustrative>（绿色专利申请弹性）。
- 事件研究：leads≈0（图 `event_study.png`）。
- **预趋势功效**（`pretrends`，按 [`design-transparency.md`](design-transparency.md) §4）：80% 功效下可侦测斜率
  0.03<illustrative>。
- **HonestDiD**：破点 `M=1.4`<illustrative>——违背需超 1.4× 最大预期违背才翻盘。
- 质量分解：实质性（发明）`0.06`<illustrative> vs 策略性（实用新型）`0.21***`<illustrative> →
  **印证「漂绿」张力**。
- PSM-DiD、安慰剂时点（2009 假政策）、替换两高清单、剔除碳交易试点城市（应对**并发政策**，
  [`threats-to-validity.md`](threats-to-validity.md) §2 第 5 行）。

> **⚠️ 回退演示**：假设初轮事件研究发现 **2010–2011 轻微预趋势**。按 design_register 的失败回退分支：
> 不硬写因果 → 加 HonestDiD 报破点 + 把主 claim 从「提升绿色创新」收紧为「提升**策略性**绿色创新、对
> 实质性创新无稳健证据」。回退记入 `logs/stage_3.md` 与 `workflow_state.json.decisions`。

**🔬 Method Gate**（`03_analysis/method_gate.md`，§MG subagent 审计）：

| Required artifact | Path | Present? |
|---|---|---|
| Sample / estimand audit | 02_data/sample_audit.md | yes |
| Design register | 03_analysis/design_register.md | yes |
| Main estimate | 03_analysis/results/main_results.json | yes |
| Event study + pretrend power | robustness/event_study.png, pretrends_power.json | yes |
| HonestDiD | robustness/honest_did.json | yes |
| Robustness matrix (≥6 项) | robustness/ | yes |
| Reproducible scripts | 03_analysis/did_estimate.py | yes |

**Status: PASS** · Hard flags: none（预趋势经 HonestDiD 处理，claim 已相应收紧）→ 写
`workflow_state.json.method_gate.status=pass`。→ 放行 Stage 4。

---

## 4. Stage 4 · 表与图 → `04_results/`

**调用**：`table`（三线表）+ `figure`。产出主表（OLS/TWFE/PSM-DiD 三列）、事件研究图、机制图、
质量分解表，并写 `04_results/exhibits_index.md`（每张表/图 ↔ 论点 ↔ 生成脚本行号，兼作复现包第 14 节原料）。
critic 检查表注齐全（样本量、聚类层级、星标定义）。→ 放行 Stage 5。

---

## 5. Stage 5 · 写作初稿 → `05_draft/main.tex`

**调用**：`paper-writer`，加载 [`writing-craft.md`](writing-craft.md)（引言五段、解剖结构、量级纪律）+
[`threats-to-validity.md`](threats-to-validity.md)（识别段写「Threats to Identification」预防段）。

**引言五段**（Head 公式）：Hook（漂绿争议）→ Question（绿色信贷是否真提升实质创新 + 先给答案）→
Antecedents（点名 JCF2023/HSSC2024/FRL2024）→ Value-added（3 条贡献列表）→ Roadmap（英文稿压一句）。

**识别段**先发制人列威胁：并发政策（剔碳交易试点）、两高分类粗糙（替换清单）、漂绿（质量分解）、
预趋势（HonestDiD 破点）——每条指向 `robustness/` 真实 artifact。

**结果段量级纪律**（[`writing-craft.md`](writing-craft.md) §7）：策略性绿色专利 `+0.21`<illustrative> 换算成
「约 1.2 件/企业·年」<illustrative>，并明说「实质性创新无稳健证据，政策的环境收益可能被专利总量高估」。

critic 审阅 `draft_audit.md`：引言五段齐、贡献句锋利、结果克制。→ 放行 Stage 6。

---

## 6–7. Stage 6 结构层打磨 + Stage 7 语言层去 AI 味

- **Stage 6（结构层，段落及以上）**：调 `paper-pipeline`（内部 polish→self-revise→style→polish→reference-verify），
  对齐 JCF 房风（[`writing-craft.md`](writing-craft.md) §10）。**prompt 里写明本阶段只做结构层**：
  论证链、节内完整性、表图指代——逐句措辞留给 Stage 7 一次做完，否则这轮润色会被 Stage 7 重写覆盖。
  本阶段的 `reference-verify` 是**全量基线**，建立 `citation_integrity_log.md` 初始台账；
  Stage 7/8 此后只验 diff 触及的条目。产出 `06_polish/main.tex` + `ref_verify_report.xlsx`。
- **Stage 7**：先跑 `de-aigc-skills`（`48-de-AIGC-skills`，中英双语六步闭环）——英文正文与中文版都走它，
  第 1 步先出 `07_dehumanize/aigc_audit.md` 审计表（本例命中 EN02 -ing 尾巴 ×7、EN10 过度断言 ×3、
  ZH01 四字套话 ×5），第 2 步把"proves that the reform caused"降级为"is associated with"（DiD 平行趋势
  只支持这一强度，与 `evidence_ledger.md` 一致），第 4 步五维加权 44 分放行。再做机械收尾：英文
  `readability`、中文 `fix-chinese`+`chinese-quote-converter`。并行 subagent 分章节处理，写回
  `07_dehumanize/main.tex`。**只动句子及以下**——段落顺序和小节归 Stage 6。
- **Stage 7 出口的数字零漂移闸门**：`python3 scripts/check_manuscript_numbers.py <workspace>`。
  本例第一次跑就抓到一处：并行改写第 4 节的 subagent 把样本量 `24,518` 写成了 `24,158`
  （`drift:inert` + `anchors` 双双 FAIL）。人工逐项 diff 两百段稿子不可能可靠发现这一处，
  机械闸门 3 秒定位。改回 `24,518` 后复跑通过，
  `manuscript_numbers` 记 `unanchored_claims=0 / inert_boundary_drift=0 / waived_claims=1`
  （那 1 条是引自《中国工业统计年鉴》的行业均值，用稿内 `% pw-number-ok:` 注明来源）。

- **Stage 7 出口的 AI 使用声明**：本阶段刚刚把整篇稿子的语言重写了一遍，所以它必须在离开之前把
  自己写进台账——`00_meta/ai_use_disclosure.md` 追加
  `| 7 | text | Claude Opus 4.6 (2026-02) | 重写第 1–6 节以提升可读性 | read-and-edited | 王磊 | yes |`，
  中文版摘要另起一行 `translation`。跑 `python3 scripts/check_ai_disclosure.py <workspace>`：
  本例第一次跑 **B4 FAIL**——并行 subagent 只写了降味稿、没碰台账，而 `stages.7_language_dehumanize`
  已置 `done`。补行后通过。**这条闸门存在的全部理由就是这一幕**：Stage 7 的职责是让 AI 痕迹消失，
  如果没人拦着，它会连声明一起消掉。

---

## 🏁 初稿质量门（Draft Quality Gate）—— 演示一次 NOT PASS → 回炉 → PASS

**Round 1**（§QG critic 按 [`quality-rubric.md`](quality-rubric.md) 打分，写 `00_meta/quality_scorecard.md`）：

| 维度 | 分 | 依据 |
|---|---|---|
| ① 贡献锋利度 | 8 | 质量分解张力清晰 |
| ② 识别可信度 | 8 | HonestDiD 破点 + 事件研究 |
| ③ 稳健性完整度 | **6** | 缺「替换聚类层级 + 子样本（国企 vs 民企）异质性」 |
| ④ 解读克制度 | 8 | 量级 + 漂绿边界 |
| ⑤ 写作与结构 | 8 | 五段式到位 |
| ⑥ 引用真实性 | 9 | reference-verify 全绿 |
| ⑦ 可复现性 | 7 | 待补一键重跑命令 |
| **总分** | **54/70** | — |

**判定：NOT PASS**（卡在维度③=6，总分<56）。回退指令：→ Stage 3 补两项稳健性。累计回退 1/2。

**回炉**：派 2 个 subagent 补「省级↔行业聚类」「国企/民企子样本」，写盘 `robustness/`。

**Round 2 重评**：③ 升到 8，⑦ 补一键重跑命令后升 8 → 总分 `58/70`<illustrative>，每维≥7，②③⑥无红旗
→ **PASS** → `quality_gate.status=pass`、`draft_milestone=done`。分数轨迹记入 `logs/quality_gate.md`。
→ 进入 Stage 8。

---

## 8. Stage 8 · 模拟评审与修订 → `08_review/`

**调用**：`referee-report`（major-revision 口吻）+ `paper-referee-revise`，加载
[`peer-review-and-submission.md`](peer-review-and-submission.md) §2/§3。

**审稿报告**（五维 + Essential/Desirable 分级）：
- **R1.1 [Essential]**：两高分类太粗，担心 misclassification。
- **R1.2 [Essential]**：2013 碳交易试点并发，DiD 可能捕捉政策包。
- **R2.1 [Desirable]**：能否报实质性创新的 MDE，证明零结果不是功效不足？

**Response Letter**（逐条、可追溯、有礼）节选：
> **R1.2（原文）**：The 2013 ETS pilots overlap your window...
> **回应**：我们同意。已加稳健性：剔除 7 个碳交易试点城市企业后重估，`treat×post` 系数从 0.21 变为
> 0.19<illustrative>（修订稿 §6.3，Table 7 第 3 列），政策包担忧不改变结论。

> R2.1 触发补 **MDE**（[`design-transparency.md`](design-transparency.md) §3）：实质性创新 MDE=0.05<illustrative>，
> 「能排除大于 0.05 的效应」写进结果段——把零结果变成有信息量的上界。

critic 复核：每条 Essential 都有实质回应、改稿未引入交叉引用/表号矛盾。→ 放行 Stage 9。

---

## 9. Stage 9 · 选刊与投稿 → `09_submission/`

**调用**：`paper-submission` + 终审 `reference-verify`，加载 [`peer-review-and-submission.md`](peer-review-and-submission.md) §4/§5/§6。

- **选刊决策序** → 1 主（*J. of Corporate Finance*，识别口味匹配）+ 2 备（*China Economic Review*、《经济研究》中文版）→ `journal_shortlist.md`。
- **Cover letter**（每刊定制 + desk-reject 自检）：一句话问题 + 一句话结果（带量级）+ fit（点名 JCF 近年绿色金融文）+ 合规声明。
- **DAS**（[`reproducibility-pack.md`](reproducibility-pack.md) §5）：CSMAR 受限如实写、CNRDS 公开留拉取脚本 → `09_submission/DAS.md`。
- **AI 使用声明终审**：JCF 属 Elsevier 政策族 → `policy_family: elsevier`、
  `statement_placement: 参考文献前的独立小节`。渲染出的 *Declaration of generative AI in scientific
  writing* 覆盖台账里全部 5 个 `Disclose: yes` 类别（literature / code / figure / text / translation），
  写明「作者已审阅并对本文内容负全责」，并**落进 `09_submission/main.tex` 正文**——只留在 `00_meta/`
  等于没写，审稿人看不到工作区。跑 `python3 scripts/check_ai_disclosure.py <workspace> --final` 通过，
  `ai_disclosure.status=pass`，投稿包才允许 `replication_pack.status=ready`。
- 投稿包 checklist：匿名稿、COI、**生成式 AI 使用声明**、highlights、终审引用 `ref_verify_final.xlsx` 全绿。

---

## 收尾 · 复盘与交付 → `FINAL_REPORT.md` + `REPLICATION.md`

- **`FINAL_REPORT.md`**：一页流水线复盘表（每阶段调了什么/产出什么/关键数字/回退分支）+ 嵌入 method gate
  与质量门评分卡 + 交付清单 + 一键重跑命令。
- **`REPLICATION.md`**（[`reproducibility-pack.md`](reproducibility-pack.md) §3，社科模板 15 节）+ master script
  `run_all.sh`：删掉派生产物只跑它，能重建 `04_results/` 全部表图。

**最终工作区**（节选）：
```text
绿色信贷创新_20260620-0430/
├── 00_meta/{workflow_state.json, quality_scorecard.md, intake.md}
├── 01_proposal/{proposal.md, lit_matrix.md, pre_analysis_plan.md, candidates/, critique.md}
├── 02_data/{clean.parquet, codebook.md, sample_audit.md, fetch_csmar.py, data_audit.md}
├── 03_analysis/{design_register.md, method_gate.md, researcher_dof.md,
│                did_estimate.py, results/, robustness/{event_study.png,
│                pretrends_power.json, honest_did.json, spec_curve.png, ...}}
├── 04_results/{main_table.tex, event_study.pdf, exhibits_index.md}
├── 05_draft/ 06_polish/ 07_dehumanize/main.tex
├── 08_review/{referee_report.md, response_letter.md}
├── 09_submission/{journal_shortlist.md, cover_letter.md, DAS.md, highlights.md}
├── logs/{stage_1..9.md, quality_gate.md}
├── REPLICATION.md  +  run_all.sh
└── FINAL_REPORT.md
```

---

## 这条 trace 演示了什么（给编排器的自检）

1. **入口路由**按用户手头的东西选起点（这里 Stage 1）。
2. **两道硬闸门真的会拦**：Method Gate 因预趋势收紧了 claim；Quality Gate Round 1 因稳健性不全 NOT PASS、
   回炉后 Round 2 才 PASS——**「跑完」不等于「达标」**。
3. **失败回退是常态**：预趋势轻微违背 → HonestDiD + 缩 claim，而不是硬写成功；控制变量 look-ahead →
   滞后到 t−1 并重跑 `check_citation_integrity.py`，而不是装作没看见。
4. **每个数字都指到真实 artifact**：`main_results.json`、`robustness/*.json`——本示例的 `<illustrative>` 占位在
   真实运行时全部由真实估计填充。**并且这件事是机械验的**：Stage 7 出口的
   `check_manuscript_numbers.py` 抓到了一处改写引入的样本量笔误（24,518→24,158），
   而人工逐项 diff 不可能可靠发现它。
5. **两个前置阶段各自买到了具体的东西**：Stage 1L 让查新分数可复核、让 Stage 9 的引用终审有白名单；
   Stage 2.5 让「你们是不是试了很多设定」这个问题有一份带 commit hash 的答案，而不是一句辩解。
   注意它们的位置不可挪动——晚一步，两者都退化成事后叙述。
6. **四道标准 + 两个新层全程在场**：写作（贡献/量级）、复现（provenance/DAS/master script）、评审投稿
   （Essential 分级/response/cover letter）、识别威胁（坏控制/并发政策/预趋势）、设计透明度（PAP/MDE/
   HonestDiD/设定曲线）、文献定位（矩阵/白space）。

> 一句话：**这就是「从一句话 idea 到可复现投稿包」长什么样。** 照着这条 trace 的产物形态填空，
> 就能把任何一个研究方向跑成同样可审计的工程。
