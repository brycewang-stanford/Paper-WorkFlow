# Peer-Review & Submission Pack — 模拟评审 · 回应 · 选刊 · 投稿增强层

> 在 Stage 8（模拟评审与修订）、Stage 9（选刊与投稿）加载。本文件把「先把自己当 reviewer 毙一遍、
> 再把回应写得像老练学者、最后把刊投对地方」落成可执行标准：审稿口径 → response letter 模板 →
> 选刊决策 → cover letter → desk-reject 自检。
>
> **分工**：审稿/回应/投稿仍调用既有 skill（`referee-report`、`paper-referee-revise`、
> `paper-submission`、`reference-verify`，见 [`skill-map.md`](skill-map.md)）；本文件规定「审到什么深度、
> 回应写成什么样、投稿包齐到什么程度才算达标」。识别硬伤的判定回到
> [`research-grade-methods.md`](research-grade-methods.md) 与 [`quality-rubric.md`](quality-rubric.md)。

---

## 0. 这个增强层解决什么

很多稿子不是「研究不行」，而是**投错刊、回应外行、cover letter 触发 desk-reject**。本层要求：

1. **模拟评审要狠**：Stage 8 的自审要按真 reviewer 的口径（major revision 心态）暴露硬伤，而非自夸。
2. **回应是隐性合同**：R&R = 「你认真解决核心问题，我就建议接收」；回应必须逐条、可追溯、有礼。
3. **选刊是策略**：fit > 影响因子；先看识别口味与近年选稿，再排 1 主 + 2 备的下投链。
4. **cover letter 决定生死**：高拒稿率刊靠它过初筛；写清 fit 与「为什么该送外审」，别写模板腔。
5. **投稿包齐全**：匿名化、利益冲突、数据可得性声明、highlights——缺一项可能直接退回。

---

## 1. 外部锚点（审稿/回应/投稿的权威入口）

| 要件 | 入口 | 用法 |
|---|---|---|
| 怎样写有效审稿报告 | Berk, Harvey & Hirshleifer, "How to Write an Effective Referee Report"（JEP 2017）: https://eml.berkeley.edu/~saez/course/effective_referee_report.pdf | Stage 8 设定模拟审稿口径 |
| 编辑在最大化什么 | Card & DellaVigna, "What Do Editors Maximize?"（NBER w23282）: https://www.nber.org/papers/w23282 | 理解 desk-reject 与选稿逻辑 |
| R&R 怎么修怎么回 | JME "Revise and Resubmit" 作者指南: https://jmeonline.org/5-2/authors/revise-and-resubmit/ | Stage 8 修订与 response letter |
| 写作/审稿手艺 | "Coding for Economists" — Writing/Referee 章: https://aeturrell.github.io/coding-for-economists/craft-referee.html | 审稿与回应的工程化清单 |
| 投稿信范式 | Editage, journal cover letter 指南: https://www.editage.com/insights/writing-an-effective-cover-letter-for-journal-submission | Stage 9 cover letter |
| AEA 数据与代码政策 | https://www.aeaweb.org/journals/data/data-code-policy | AEA/AER/AEJ 投稿前核 Data and Code Availability Form、deposit 与 verification 预期 |
| Management Science Code and Data Disclosure Policy | https://pubsonline.informs.org/page/mnsc/code-and-data-disclosure-policy | MS/INFORMS 投稿前核 AsCollected disclosure、replication package plan 与替代披露方案 |
| 期刊投稿细则 | 各刊官网 Author Guidelines（投前必读，覆盖一切通用建议） | Stage 9 按目标刊定制 |

> 母仓库可叠加更狠的对抗审阅 skill：`66/grillme`、`66/econ-reviewer`、`66/did-reviewer`、
> `21-claesbackman-AI-research-feedback`、`41-sticerd-eee-sewage-econometrics-check`（计量自检）。

---

## 2. Stage 8 模拟评审：按真 reviewer 口径

Stage 8 用 `referee-report` 生成审稿报告。本层要求审稿覆盖五个维度（呼应 Berk-Harvey-Hirshleifer 的
建设性审稿原则），并**先给 major revision 心态的建设性意见**，而非一棒打死：

| 审稿维度 | 要问的问题 |
|---|---|
| **贡献** | 相对最近前作，增量够不够顶刊？是否 convex / just-another-determinant？ |
| **识别** | 核心假设成立吗？诊断齐吗？（对照 `method_gate.md` 与 `design_register.md`） |
| **稳健性** | 主结论经得起合理扰动吗？关键威胁应对了吗？ |
| **写作/解读** | 引言抓人吗？结果是否过度解读、缺经济量级？ |
| **可复现** | 数据来源清楚吗？复现包齐吗？（对照 [`reproducibility-pack.md`](reproducibility-pack.md)） |

**意见分级**：每条意见标 **Essential（不解决不接收）/ Desirable（锦上添花）**。这个分级直接决定 Stage 8
修订的优先级——先把所有 Essential 关掉，再处理 Desirable。审稿报告落 `08_review/referee_report.md`。

> 模拟评审若暴露**根本性识别缺陷** → 不要硬修，回 Stage 3（补检验/换策略）甚至 Stage 1（改设计），
> 并在闸门标红（与 stage-playbook 的失败回退一致）。

---

## 3. Response Letter（回应信）：逐条 · 可追溯 · 有礼

R&R 是作者与审稿人之间的**隐性合同**：把 Essential 问题令人满意地解决，审稿人就会建议接收；编辑和
审稿人都希望「复审成本尽量低、修订稿尽量接近终稿」。回应信据此写：

**结构模板**（`08_review/response_letter.md`，每个 reviewer 一节）：

```markdown
# Response to Reviewer 1

我们感谢审稿人富有建设性的意见。下文逐条回应（**R1.1, R1.2, ...** 编号），审稿原文用引用块，
我们的回应紧随其后，并标注**正文中对应的修改位置（页/节/表号）**。

> **R1.1（原文）**：[审稿人意见原文]
**回应**：我们同意/部分同意/谨慎不同意。我们做了 [具体动作：补了 Table X / 加了 §Y 段 /
重跑了 Z]，结果见修订稿 §__ 第 __ 行 / Table __。[若不同意，给有理有据的解释，不顶撞。]
```

**回应纪律**：

1. **逐条编号**：把每份报告拆成带编号的点，**一点一回**，不合并、不漏点。
2. **可追溯**：每条回应都指向修订稿的**具体位置**（页/节/表号/行号），让复审一眼能核对。
3. **区分能改与不能改**：能改的改、并致谢；确实不该改的，礼貌地给证据反驳，**绝不情绪化、绝不无视**。
4. **致谢但不谄媚**：开头一句真诚致谢即可，不堆赞美。
5. **改稿用变更标记**：修订稿用颜色/划线标出改动，response 与改动位置一一对应。
6. **不引入新矛盾**：改一处要检查交叉引用、表号、数字是否还自洽（critic 复核这一项）。

---

## 4. Stage 9 选刊：fit 优先于影响因子

`paper-submission` 给出 ~20 本候选 + 星级匹配；本层用一个**决策序**把它收敛成 **1 主投 + 2 备投** 的下投链：

1. **领域匹配**：论文的实证问题属于该刊的核心议题吗（看近 2 年目录，不是看刊名）？
2. **方法口味**：该刊近年对识别严格度的偏好与本文的 `method_gate` 强度匹配吗？
3. **贡献量级**：贡献够该刊的层级吗（顶刊/旗舰 field / 一般 field）？匹配 SSCI/ABS 星级。
4. **周转与风险**：审稿周期、desk-reject 率、对中国数据/场景的接受度——影响下投顺序。
5. **下投链**：排 1 主（最匹配且够得着）+ 2 备（被拒后的下一站），写进 `09_submission/journal_shortlist.md`。

> Stage 0 已问定的 `target_journal` 是主投锚点；本层做的是「在它周围排一条理性的下投链」，避免被拒后
> 临时慌乱投错刊。国内稿与英文稿的候选池不同（见 [`writing-craft.md`](writing-craft.md) §10 房风表）。

---

## 5. Cover Letter：过初筛的单点

高拒稿率刊（desk-reject 50–80%）的编辑读每封 cover letter，并在**找停下读的理由**。cover letter 要在
30 秒内让编辑看到「这篇该送外审」：

**结构模板**（`09_submission/cover_letter.md`，**每刊定制、绝不通用模板**）：

```markdown
尊敬的 [Editor 姓名]：

我们谨向 [期刊] 投稿《[标题]》。

[一句话研究问题 + 一句话主结果（带量级）]。本文的核心贡献是 [一句话贡献]，相对于 [最近前作]
前进了 [具体增量]。

本文契合 [期刊] 的原因：[点名该刊近年发表的 1–2 篇相关文 / 该刊关心的议题]，本文在
[识别严格度 / 政策相关性 / 新数据] 上正属该刊读者关心的范畴。

本文为原创、未一稿多投；所有作者同意投稿；[利益冲突声明]；数据与代码可得性见随附 DAS。

顺颂编安，
[作者]
```

**desk-reject 自检（投前逐项过）**：

- [ ] **fit 写清了吗**：明确点出与该刊的契合点，而非泛泛说「贵刊声誉卓著」。
- [ ] **不是通用模板**：编辑一眼能认出模板腔；针对该刊定制了内容。
- [ ] **一句话贡献 + 一句话结果**在信里，编辑不读全文也懂。
- [ ] **没有方法炫技无问题**：不是「有个新方法，找个数据套一下」（编辑常据此 desk-reject）。
- [ ] **合规声明齐**：原创性、未一稿多投、利益冲突、作者同意、数据可得性。

---

## 6. 投稿包 checklist（Stage 9 交付前逐项核）

critic 走一遍目标期刊的 submission checklist，缺项即补。**先刷新目标刊官网**：Author Guidelines、
data/code policy、匿名化规则、word/LaTeX 模板、supplement / replication package 要求都以官网为准；
本文件只给默认骨架。

| 项 | 要求 | 落点 |
|---|---|---|
| 匿名化 | 双盲刊去掉作者信息、致谢、可识别的自引措辞 | `09_submission/` 匿名稿 |
| 字数/格式 | 符合目标刊字数、参考文献格式、figure 规格 | 按 Author Guidelines |
| 利益冲突声明 | COI / funding 声明 | cover letter 或单独文件 |
| 数据可得性声明 | DAS（见 [`reproducibility-pack.md`](reproducibility-pack.md) §5） | `09_submission/DAS.md` |
| 数据/代码表单 | AEA Data and Code Availability Form、MS AsCollected URL、或目标刊等价 disclosure | `09_submission/submission_checklist.md` |
| Highlights / 贡献声明 | 部分刊要求 3–5 条 highlights、作者贡献声明 | `09_submission/highlights.md` |
| 终审引用 | 投前最后一次 `reference-verify`，确保改稿没动坏引用 | `09_submission/ref_verify_final.xlsx` |
| 复现包 | 随投或接收后提交的 `REPLICATION.md` + 数据/代码 | 工作区根 `REPLICATION.md` |

---

## 7. 接入点小结

| Stage | 本层做什么 | 落盘 |
|---|---|---|
| **8 模拟评审** | 按 §2 五维 + Essential/Desirable 分级生成审稿报告 | `08_review/referee_report.md` |
| **8 修订与回应** | 按 §3 逐条、可追溯、有礼地写 response letter | `08_review/response_letter.md` |
| **9 选刊** | 按 §4 决策序收敛成 1 主 + 2 备下投链 | `09_submission/journal_shortlist.md` |
| **9 cover letter** | 按 §5 每刊定制 + desk-reject 自检 | `09_submission/cover_letter.md` |
| **9 投稿包** | 按 §6 checklist 备齐并终审引用 | `09_submission/` |

> 一句话：**先把自己当审稿人毙一遍（Stage 8），再把刊投对、把信写对（Stage 9）。** 研究的可信度由
> 前面的方法闸门与质量门保证；本层保证「可信的研究被投到对的地方、以专业的方式」。
