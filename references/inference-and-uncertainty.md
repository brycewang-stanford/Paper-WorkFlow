# Inference & Uncertainty Pack — 标准误、抽样不确定性与多重检验

> 在 Stage 3 定稳健性矩阵、跑估计、Stage 4 出表、Stage 5 写结果段、Stage 8 模拟评审时加载。
> 本文件补足一个独立于「识别」和「样本」的第三类失分点：**点估计可能没错、识别也站得住，但
> 不确定性量化（标准误、置信区间、p 值、多重检验）做错，结论照样被推翻。**
>
> **分工**（与三个相邻层正交，互不重复）：
> - [`research-grade-methods.md`](research-grade-methods.md) 管「这个设计需要哪个**估计量**、落盘哪些
>   识别诊断」（点估计的正确性）。
> - [`empirical-audit.md`](empirical-audit.md) 管「进入估计器的**样本**是否支持 estimand」。
> - [`threats-to-validity.md`](threats-to-validity.md) 管「识别**偏误**（点估计有没有偏）怎么堵」。
> - **本文件管「围绕点估计的不确定性**：SE 该怎么聚类、cluster 太少怎么办、要不要用随机化推断、
>   检验了一堆假设怎么校正、弱工具下区间怎么算、p 值/CI 怎么报」。
>
> 一句话：前三层决定 **β̂ 对不对、偏不偏**；本层决定 **β̂ 周围那根误差棒画得对不对、星标可不可信**。

---

## 0. 这个增强层解决什么

实证论文最常见、也最容易被一审一句话毙掉的不确定性错误：

1. **聚类层级反射性地选错**：政策在省级分配却按个体聚类 → SE 虚低、星标虚高；或反过来在没有聚类
   结构时硬聚类到最高层 → SE 虚高、把真效应做没。聚类是**设计问题**不是「越高越保险」（AAIW 2023）。
2. **cluster 太少仍用大样本渐近**：cluster 数只有 10–30 个还用普通 cluster-robust SE，过度拒绝严重；
   需要 wild cluster bootstrap / CR2-CR3 / t(G−1) 临界值。
3. **检验了几十个系数却不校正**：多个 outcome × 多个子样本 × 多个设定 = 几十次检验，总有几个偶然显著；
   不做 family-wise / FDR 校正、不预先指定主结果，就是 [`threats-to-validity.md`](threats-to-validity.md)
   §2 第 10 行的「分叉路径 / p-hacking」。
4. **弱工具下还用 2SLS 的 t 比**：第一阶段弱时常规 IV 置信区间严重失真，要用 Anderson–Rubin / tF 等
   弱工具稳健区间（与 threats §2 第 12 行联动）。
5. **把 p<0.05 当真理、只贴星标**：不报置信区间、不报效应量级、把「marginally significant」当证据、
   把统计显著当经济重要——这是 ASA (2016) 明确反对的报告方式。

本层要求：**每个主结果的不确定性都有可辩护的口径，并把口径落成可审计的 `inference_report.md`。**
缺口径或口径与 claim 不匹配 → 质量门维度②③④对应封顶（见 §9）。

> 本层是**不确定性标尺**，不替代任何估计 skill。具体 SE / bootstrap / 校正怎么算，路由到 StatsPAI /
> Stata / R 的真实函数（见各节末「实现路由」）；本文件只规定「做到什么程度、报成什么样才算达标」。

---

## 1. 外部锚点（评估 / 实现 / 反驳时的权威入口）

| 议题 | 首选入口 | 何时用 |
|---|---|---|
| 该不该聚类、聚到哪一层 | Abadie, Athey, Imbens & Wooldridge (2023, QJE) *When Should You Adjust SEs for Clustering?*: https://academic.oup.com/qje/article/138/1/1/6750017 | 决定聚类层级；判定聚类是抽样还是设计问题 |
| 聚类推断实操总纲 | Cameron & Miller (2015, JHR) *A Practitioner's Guide to Cluster-Robust Inference*: https://jhr.uwpress.org/content/50/2/317 | 聚类 SE、双向聚类、few-cluster 全景 |
| few-cluster wild bootstrap | Cameron, Gelbach & Miller (2008, REStat); MacKinnon & Webb (2017, *J. Appl. Econometrics*) `boottest`: https://github.com/droodman/boottest | cluster 数少（<≈30–50）时的稳健推断 |
| 小样本 cluster 修正 (CR2/CR3) | Pustejovsky & Tipton (2018, JBES); `clubSandwich`: https://cran.r-project.org/package=clubSandwich | bias-reduced cluster SE + Satterthwaite 自由度 |
| 随机化 / 置换推断 | Young (2019, QJE) *Channeling Fisher*: https://academic.oup.com/qje/article/134/2/557/5195544 ; Athey & Imbens (2017) | 实验、few-cluster、合成控制的设计型推断 |
| 多重检验（family-wise） | Romano & Wolf (2005, JASA) stepdown: https://www.tandfonline.com/doi/abs/10.1198/016214504000000539 （经济学实现见 `rwolf`） | 多 outcome / 多处理臂的 FWER 控制（用 bootstrap 利用检验间相依结构，渐近上不弱于逐一校正、通常更有力） |
| 多重检验（sharpened FDR） | Anderson (2008, JASA) sharpened q-values: https://www.tandfonline.com/doi/abs/10.1198/016214508000000841 ; Benjamini-Hochberg (1995) | 多 outcome 探索性发现的 FDR 控制 |
| 弱工具检验（effective F 源头） | Montiel Olea & Pflueger (2013, JBES): https://www.tandfonline.com/doi/abs/10.1080/00401706.2013.806694 | effective F 统计量的原始来源与临界值 |
| 弱工具稳健推断（综述） | Andrews, Stock & Sun (2019, ARE): https://www.annualreviews.org/doi/10.1146/annurev-economics-080218-025643 | effective F、Anderson–Rubin 区间的实践总纲 |
| tF（单工具弱 IV 校正） | Lee, McCrary, Moreira & Porter (2022, AER): https://www.aeaweb.org/articles?id=10.1257/aer.20201063 | 单内生变量时按第一阶段 F 调整 t 临界值 |
| p 值 / 显著性报告规范 | ASA Statement on p-values (Wasserstein & Lazar 2016): https://www.tandfonline.com/doi/full/10.1080/00031305.2016.1154108 | 结果段措辞、CI vs 星标、显著性二分谬误 |

> 这些是判定与实现的标准锚点，不是硬依赖。本机不能联网时，subagent 按本文件各节的决策规则自检并路由
> 到已装的 StatsPAI / Stata / R 函数，**不要凭印象写「标准误已稳健聚类」这种空话**——每个口径都要指向
> `03_analysis/` 里跑出来的真实数字与脚本行号。

---

## 2. 标准误与聚类层级——先回答「为什么聚类」，再回答「聚到哪一层」

聚类不是越高越保险。AAIW (2023) 把它讲清楚：聚类调整针对的是**两类相关来源**——(a) 抽样设计按 cluster
抽（sampling-based），(b) 处理在 cluster 层级分配（design/assignment-based）。**两者都不存在时，聚类往往
（而非必然）把 SE 放大成过度保守、把真效应做没**；存在时不聚类则 SE 虚低、星标虚高。

**决策规则（写进 `design_register.md` 与 `inference_report.md`）：**

1. **先问处理分配层级**：处理/政策在哪个层级变动（个体 / 企业 / 城市 / 省 / 行业×年）？**聚类层级至少
   等于处理分配层级**——这是稳妥缺省。政策在省级，就不能按个体聚类。（AAIW 的精确条件是：当处理效应
   异质、且只抽到 cluster 总体的一部分时才必须聚到分配层级；抽到全体 cluster 且效应同质时，设计型推断可
   不聚类。实务上按缺省聚到分配层级，再把这一判断写进 `inference_report.md`。）
2. **再问抽样层级**：数据是不是按 cluster 抽样、cluster 内是否同质？是则该层也要纳入考虑。
3. **多个层级都可能相关 → 双向 / 多向聚类**（如同时按企业和年份），但要确认每个维度的 cluster 数都够大。
4. **不要无脑聚到最高层**：层级越高 cluster 越少，渐近越不可靠（见 §3）。在「正确层级」和「够多 cluster」
   之间权衡，并把权衡写进 `inference_report.md`。
5. **空间 / 时间相关**：截面有空间自相关用 Conley SE；面板有序列相关默认按个体聚类已部分处理，必要时叠加。

**稳健性（进 StatsPAI §6 第 4 块「替换 SE」）**：主表报一个口径，附录报「换聚类维度 / 双向聚类 / 不聚类」
对照，证明显著性不靠某一个聚类选择撑着。**聚类口径换了显著性就翻，必须在正文如实说明，不能只报最有利的那个。**

**实现路由**：

| 口径 | StatsPAI MCP | StatsPAI 包 / Stata / R |
|---|---|---|
| 单向 cluster-robust | `cluster_robust_se` | `sp.feols(..., vcov={"CRV1":"id"})` / Stata `reghdfe, cluster()` / R `feols(..., cluster=~id)` |
| 双向 / 多向聚类 | `twoway_cluster` / `multiway_cluster_vcov` | `vcov={"CRV1":"firm+year"}` / `reghdfe, cluster(firm year)` / `feols(..., cluster=~firm+year)` |
| 空间相关 (Conley) | `conley` | Stata `acreg`/`ols_spatial_HAC` / R `conleyreg` |

---

## 3. cluster 太少 / 小样本——别再用大样本渐近

cluster 数少（经验阈值 **G ≲ 30–50**，越不平衡越要小心）时，普通 cluster-robust SE **系统性过度拒绝**
（把不显著做成显著）。命中以下任一情形，主结果**必须**升级推断方法，并在 `inference_report.md` 注明
cluster 数与所用方法：

- 处理在少数几个 cluster（如 1 个省试点、少数城市、几个行业）；
- cluster 数 < 50 且 cluster 大小高度不平衡；
- 双向聚类中某一维的 cluster 数很少；
- 处理变量在 cluster 层级几乎不变（"few treated clusters"，MacKinnon-Webb 警告的过度拒绝重灾区）。

**研究级三选一（按强度递增）：**

1. **Wild cluster bootstrap**（首选，`boottest` 的核心）：对 few clusters 最稳健；**few treated clusters 时
   用 WCR（restricted）+ 6-point 权重**（cluster 极少时 Rademacher 两点权重可取的 bootstrap 统计量太少），
   并报告 bootstrap 的 p 值/CI，而不是只报渐近 t。注意：**treated cluster 极少时 WCR 会偏保守（功效低）、
   WCU 又过度拒绝，bootstrap 没有完美解**——此时 §4 的随机化推断才是真正的兜底。
2. **CR2 / CR3 bias-reduced SE + Satterthwaite 自由度**（`clubSandwich`）：解析路径，cluster 中等偏少时好用。
3. **t(G−1) 临界值**：自由度按 cluster 数而非观测数取，最低限度的小样本修正。

> **铁律**：few-cluster 情形只报渐近 cluster-robust SE 与星标，等于把过度拒绝藏起来。质量门维度③对此
> 封顶（见 §9）。处理只落在极少数 cluster 时，往往还应叠加 §4 的随机化推断作为主推断或交叉验证。

**实现路由**：

| 方法 | StatsPAI MCP | 包 / Stata / R |
|---|---|---|
| wild cluster bootstrap | `wild_cluster_bootstrap` / `wild_cluster_boot` / `wild_cluster_ci_inv` | `sp.wild_cluster_boot(...)` / Stata `boottest` / R `fwildclusterboot::boottest` |
| few-treated-cluster subcluster | `subcluster_wild_bootstrap` | Stata `boottest, ...` |
| CR2 / CR3 | `cr2_se` / `cr3_jackknife_vcov` | R `clubSandwich::coef_test(vcov="CR2")` |
| jackknife SE | `jackknife_se` | — |

---

## 4. 随机化 / 置换推断——设计型不确定性

当处理分配本身是（准）随机、或 cluster 太少使渐近不可信时，**随机化推断（RI）/ 置换检验**直接从设计出发，
不依赖大样本渐近，常常是最有说服力的主推断或交叉验证。Young (2019) 显示：不少「显著」结果在 RI 下变弱，
因为渐近 SE 低估了不确定性。

**何时用（命中即应做，至少作为交叉验证）：**

- **实验 / RCT**：Fisher 锐零假设下的置换检验是标配。
- **few-cluster / 单一处理单位**：合成控制的 in-space placebo 本质就是 RI（见 research-grade-methods §3 SCM 行）。
- **离散处理时点 / staggered**：随机重排 treatment timing 做 placebo。
- **任何渐近可疑、想给一个不依赖分布假设的稳健 p 值时。**

**怎么报**：报 RI 的 p 值（基于多少次重排、重排的是什么——处理标签 / 处理时点 / 处理单位），并和渐近 p 值
并列，让读者看到两者是否一致。重排次数与随机种子登记进 [`reproducibility-pack.md`](reproducibility-pack.md) §4。

**实现路由**：StatsPAI MCP `ri_test`；合成控制的安慰剂用 `synth_time_placebo` / `synth` 的 in-space placebo；
Stata `ritest`；R `ri2` / 自写置换循环（固定 seed）。

---

## 5. 多重检验——检验一堆假设就得校正

只要**同一篇论文围绕同一组假设做了多次检验**（多个 outcome、多个子样本/异质性维度、多个处理臂、多个
设定），单次 5% 的显著性就不再是整体 5%：检验 20 次，纯偶然也约有 1 次「显著」。这是 reviewer 的高频杀招
（[`threats-to-validity.md`](threats-to-validity.md) §2 第 10 行）。

**决策规则：**

1. **先预先指定主结果**（呼应 [`design-transparency.md`](design-transparency.md) §2 PAP）：哪个是主 outcome、
   哪些是次要 / 探索性。主结果不受多重检验拖累；次要结果按下面校正。
2. **划定检验族（family）**：把「概念上属于同一假设」的检验归为一族（如「6 个创新产出指标」是一族）。
   校正在族内做，不是对全文所有 p 值一锅端。
3. **选校正方法**：
   - **确证性、要控制「有没有任何假阳性」（FWER）** → **Romano–Wolf stepdown**（用 bootstrap 利用检验间
     相依结构，渐近上不弱于、通常强于逐一校正）。兜底用 **Holm**（在 FWER 下一致地不弱于 Bonferroni、且
     不需相依假设），Bonferroni 是最保守的下限。
   - **探索性、容忍少量假阳性但要控制假阳性比例（FDR）** → **Benjamini–Hochberg**，或 **Anderson (2008)
     sharpened q-values**（社科多 outcome 的事实标准，比朴素 BH 更有力）。
4. **子样本异质性同样适用**：报了 10 个子样本的处理效应，就别只挑显著的那个讲故事——要么预先指定、要么
   对这一族做校正、要么把它降为探索性附录。
5. **报告**：把校正前 p 值、校正后 p/q 值、所属族、校正方法并列成表；正文结论用校正后的显著性。

> 一句话：**「我们额外发现 X 子样本里效应显著」如果没有预先指定、也没做族内校正，在现代审稿口径下基本
> 不算证据。** 把多重检验前置成自检，能省掉 Stage 8 一整轮回炉。

**实现路由**：StatsPAI MCP `romano_wolf` / `benjamini_hochberg` / `holm` / `bonferroni` / `adjust_pvalues`；
Stata `rwolf2` / `wyoung` / `qqvalue`；R `multcomp` / 自算 sharpened q-values。

---

## 6. 弱工具稳健推断（IV 专项，与 threats §12 联动，不重复）

第一阶段弱时，2SLS 的常规 t 比和 Wald 区间严重失真。**只报第一阶段 F 还不够，要给弱工具稳健区间**：

- **判弱**：报 **effective F**（Montiel Olea–Pflueger），别只用经验阈值 10；
- **单内生变量** → **tF 校正**（Lee et al. 2022）：按第一阶段 F 平滑地放大 t 临界值（等价于把 SE 乘上一个
  调整因子、加宽 CI），调整的是临界值/区间宽度而非点 SE 本身；
- **稳健区间** → **Anderson–Rubin**（对弱工具完全稳健，过度识别时仍有效），必要时用 conditional likelihood
  ratio（CLR）区间；
- 报告这些区间，而不是把弱工具的 2SLS 点估计当定论。

**实现路由**：StatsPAI MCP `effective_f_test` / `anderson_rubin_ci` / `anderson_rubin_test` /
`tF_adjustment` / `tF_critical_value` / `conditional_lr_ci` / `weakrobust`；Stata `weakiv` / `ivreg2` /
`tf`；R `ivmodel` / `ivDiag`。

> 识别叙事（排他性是否可信）仍归 [`threats-to-validity.md`](threats-to-validity.md) §2 第 12 行；本节只管
> **弱工具下的区间怎么算对**。两者一起：排他性讲故事 + AR/tF 算区间。

---

## 7. 报告纪律——CI 优先，别只贴星标

按 ASA (2016)：**统计显著 ≠ 重要，不显著 ≠ 无效应；不要把 p=0.049 和 p=0.051 当成两个世界。**

- **报置信区间 + 点估计**，星标可保留但不是主角；让读者看到效应的**幅度与精度**，而不是只看过没过 0.05。
- **报效应的经济量级**（占均值/标准差几成、政策口径下意味着什么）——与质量门维度④「解读克制度」直接挂钩。
- **不写「marginally significant / 接近显著」**当作支持证据；不显著就如实说不显著，必要时配 §3 的
  [`design-transparency.md`](design-transparency.md) MDE：「我们能排除大于 X 的效应」。
- **p 值用精确值或区间**（如 p=0.03、p<0.01），不要只有星标。
- **主推断口径在表注里写清**：SE 类型、聚类层级与 cluster 数、是否 bootstrap/RI、是否多重检验校正。
  表注是 reviewer 判断推断可信度的第一落点。

---

## 8. 落盘：`inference_report.md`（Stage 3 推断口径合同）

Stage 3 估计完成时，除 `method_gate.md` 外，写一份 `03_analysis/inference_report.md`
（模板见 [`../templates/inference_report.md`](../templates/inference_report.md)），把主结果与每个关键检验的
不确定性口径定死，作为表注、写作和质量门的统一真源。至少包含：

- **聚类决策**：处理分配层级、所选聚类层级、cluster 数、为什么这样选（§2 的设计型理由）。
- **小样本修正**：cluster 数是否触发 few-cluster？用了 wild bootstrap / CR2 / t(G−1) 哪种？（§3）
- **随机化推断**：是否做了 RI？重排的是什么、多少次、种子、p 值，与渐近是否一致？（§4）
- **多重检验**：检验族划分、主 vs 次要 outcome、校正方法、校正前后 p/q 值表。（§5）
- **弱工具推断**（如适用）：effective F、AR / tF 区间。（§6）
- **报告口径**：主表报 CI 还是只报星标、效应量级解读位置。（§7）

`inference_report.md` 与 `method_gate.md` 的 artifact 表对账：method gate 的「替换 SE / 稳健性」行必须指向
本文件记录的真实口径与 `03_analysis/robustness/` 文件。

> **机械闸门自检**：写完闸门 artifact 后，在方法闸门 / 质量门 / 收尾处跑一次
> `python3 scripts/check_workspace_gates.py <workspace>`（详见 [`../scripts/check_workspace_gates.py`](../scripts/check_workspace_gates.py)）。
> 它机械校验「某道闸门标了 `pass`/`ready`，但所需 artifact 文件不在盘上、或上游闸门没过（质量门不得松于方法闸门）」
> 这类 critic 读 prose 保证不了的硬不一致；返回非零即说明闸门**名不副实**，必须先补齐再放行。加 `--reconcile`
> 还会启发式核对 `main_results.json` 的系数是否出现在 `04_results/` 表里。这是对 critic 主观打分的**机械兜底**，不替代它。

---

## 9. 接入点（本层如何嵌进流水线与闸门）

| 接入点 | 本层做什么 | 落盘 / 判定 |
|---|---|---|
| **Stage 3 设计注册** | 在 `design_register.md` 写死聚类层级与推断口径的设计型理由（§2） | `03_analysis/design_register.md` |
| **Stage 3 估计** | 按 §2–§6 跑对 SE / few-cluster 修正 / RI / 多重检验 / 弱工具区间，写 `inference_report.md` | `03_analysis/inference_report.md` |
| **Stage 3 稳健性矩阵** | 「替换 SE」块按 §2 出对照；few-cluster 出 wild bootstrap；多 outcome 出校正表 | `03_analysis/robustness/` |
| **Stage 4 出表** | 表注写清 SE 类型 / 聚类层级 / cluster 数 / 校正方法；主表报 CI（§7） | `04_results/*` + `exhibits_index.md` |
| **Stage 5 结果段** | 按 §7 报 CI + 经济量级，不堆星标；多重检验用校正后显著性措辞 | `05_draft/main.tex` |
| **Stage 8 模拟评审** | critic 按 §2/§3/§5/§6 逐项找「推断口径有没有错」 | `08_review/referee_report.md` |
| **质量门维度②③④** | 见下方硬挂钩 | `00_meta/quality_scorecard.md` |

**与 [`quality-rubric.md`](quality-rubric.md) 的硬挂钩**（把模糊的「推断稳健」变成可核验闸门）：

- 聚类层级低于处理分配层级、或聚类口径换了就翻却只报最有利的一个（§2）→ 维度③（稳健）封顶 5；
  若因此把不显著做成显著 → 等同维度③致命红旗「SE 聚类层级错误导致显著性虚高」，≤4。
- few-cluster（G ≲ 30–50）仍只报渐近 cluster-robust SE、无 wild bootstrap / CR2 / t(G−1)（§3）→ 维度③封顶 6；
  处理只落在极少数 cluster 且无 RI 交叉验证 → 维度②（识别）封顶 6。
- 多 outcome / 多子样本检验无预先指定、无族内校正、却挑显著的讲故事（§5）→ 维度③封顶 5、维度④封顶 6。
- 弱工具（effective F 远低于阈值）只报 2SLS t 比、无 AR / tF 区间（§6）→ 维度②封顶 4（与 threats §6 一致）。
- 通篇只报星标、不报 CI、把统计显著当经济重要、用「marginally significant」当证据（§7）→ 维度④封顶 6。
- 缺 `03_analysis/inference_report.md` 且主结果涉及聚类 / few-cluster / 多重检验任一情形 → 维度③封顶 6。

> 一句话：**识别对了、样本对了，不确定性也得量化对。** 本层把「SE 怎么聚、cluster 少了怎么办、检验多了
> 怎么校正、弱工具下区间怎么算、p 值怎么报」前置成作者自检，让稿子在「推断」这条独立的审稿杀招上提前免疫。
