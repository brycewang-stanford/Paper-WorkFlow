# StatsPAI 分析引擎 — Stage 3–4 的统一估计与出版级出表引擎

> **这是 Paper-WorkFlow 默认 `python-statspai` 后端的因果推断 / 应用计量主引擎手册。**
> Stage 3（识别与估计）与 Stage 4（表与图）在选择 Python/StatsPAI 后端、或需要 StatsPAI 交叉验证时加载本文。
> Stata 和 R 后端的同级路由见 [`analysis-backends.md`](analysis-backends.md)。StatsPAI 把「拟合 → 诊断 → 稳健性 → 出表/出图 → 取引用」串成
> 一条 agent-native 链路，恰好覆盖现代实证论文的 8 个产出段，与本编排器的 Stage 2→4 + 收尾几乎
> 1:1 对齐。
>
> **核心纪律不变**：StatsPAI 只是 Stage 3–4 的**引擎**，不替代两道闸门。它把
> [`research-grade-methods.md`](research-grade-methods.md) 的最低证据包**喂满**，再由 Method Gate
> 判定 PASS；它产出的表图供 Stage 4 audit 与 Stage 5 写作引用。**绝不贴空方法标签**——每个
> `did`/`iv`/`rdrobust`/`dml`/`causal_forest` 标签都必须对应下文 §6 稳健性闸门列出的真实 artifact。

---

## 0. 两条接入路径（先选路，再干活）

StatsPAI 有两面。本编排器在 `analysis_backend.primary=python-statspai` 时**默认 MCP 优先、包为重活路径**：

| 路径 | 是什么 | 何时用 | 入口 |
|---|---|---|---|
| **MCP（默认）** | 已连接的 `mcp__statspai__*` 工具，agent-native，**无需写 Python** | Stage 3 的设计识别、拟合、诊断、稳健性自检、取引用；Stage 8 计量复核 | `mcp__statspai__detect_design` / `preflight` / `recommend` / `audit_result` / `*_from_result` / `bibtex` |
| **`statspai` 包（重活）** | `pip install "statspai[fixest,plotting]"`，`import statspai as sp`，本机 Python 跑 | 需要**出版级三格式表图**（Word/Excel/LaTeX 同时出）与 **8 段论文级 artifact bundle** 时 | `sp.feols` / `sp.regtable` / `sp.paper_tables` / `sp.collect` / `sp.coefplot` … |

**怎么择路（决策一句话）**：
- 只想让 agent 把识别拍板、把系数和稳健性跑出来、把缺的诊断补齐、把引用取对 → **走 MCP**，全程不落 Python。
- 要把结果做成可直接进 `main.tex` 的三线表 + 期刊级图 + 一键复现的 `paper.docx/.xlsx/.tex` bundle → **切到 `statspai` 包**，因为出版级三格式导出与多面板 paper bundle 是包的能力，MCP 不替代。
- **两者结果必须一致**：同一设计先 MCP 拍板与拟合，再用包出表时，系数 / SE / N / 聚类必须对得上；对不上先停下查（多半是样本或聚类口径不一致），不要让两份产物各说各话。

> **退化**：本机没有 `statspai` 包、或 MCP 不可达时，按 [`runtime-fallbacks.md`](runtime-fallbacks.md)
> 退到已有 Stata/R/Python 脚本实现**同等 artifact**；实现不了就让 `method_gate.md` 明确 `NOT PASS`，
> 不得把工具缺失伪装成已验证。

---

## 1. 8 段流水线 ↔ 编排器阶段映射

StatsPAI 的标准实证论文结构是 8 段（§−1 … §8）；它们落到本编排器的阶段如下。**进入对应阶段时
按这一行干活**：

| StatsPAI 段 | 内容 | 编排器阶段 | 关键产物 / MCP·包入口 |
|---|---|---|---|
| §−1 Pre-Analysis Plan | 功效 / MDE、设计预登记 | Stage 3 plan | `design-transparency.md` 的 PAP；`sp.power(...)` / MCP `synth_mde`·`pretrends_power` |
| §0 Sample Construction | 样本限制日志 + 数据契约 | Stage 2 | `02_data/codebook.md`；五查门（形状/类型/缺失/重复/面板平衡） |
| §1 Descriptives（Table 1） | 描述统计、处理 vs 对照均值比较 | Stage 4 | `sp.sumstats` / `sp.mean_comparison` → `.to_word/.to_excel` |
| §2 Empirical Strategy | **冻结识别策略=预注册** | Stage 3 plan | `03_analysis/design_register.md`；`sp.causal_question(...).identify()` 落盘后才估计；MCP `detect_design`→`check_identification` |
| §3 Identification Graphics | 识别假设的可视化检验 | Stage 4 | 事件研究图 / RD 图 / Bacon 图（见 §5） |
| §4 Main Results（Table 2） | 基准主表 | Stage 3 估计 + Stage 4 出表 | `sp.regtable(M1..M5, template="aer")`；MCP `feols`/`did`/`ivreg`/`rdrobust`(as_handle) |
| §5 Heterogeneity（Table 3） | 子样本 / CATE 异质性 | Stage 3 + Stage 4 | 子样本 `regtable` 或 `sp.metalearner` CATE |
| §6 Mechanisms | 机制 / 中介 / 分解 | Stage 3 | `sp.mediation` / `sp.decompose`；MCP `mediate`/`gelbach` |
| §7 Robustness（Table A1） | 稳健性矩阵 | Stage 3 → Method Gate | Oster / HonestDiD / E-value / spec curve（见 §6） |
| §8 Replication Package | 一键复现 bundle | 收尾 | `sp.collect("Title").add_*.save(...)`；并入 `REPLICATION.md` |

> §2 的「先 `identify()` 落盘、再 `estimate()`」就是 StatsPAI 版的**预注册**——与
> [`design-transparency.md`](design-transparency.md) 的 PAP 纪律合流。**估计前必须把识别计划冻结到
> `03_analysis/design_register.md`**，否则等同事后挑设定。

---

## 2. 三种领域模式（扩展 Stage 3 的设计路由）

Stage 3 的方法路由（见 [`skill-map.md`](skill-map.md) §C）默认是应用计量。StatsPAI 再补两条领域支线，
**按用户措辞自动切换**：

| 模式 | 触发措辞 | 估计量栈 | 报告口径 |
|---|---|---|---|
| **默认 · 应用计量（AER/QJE/JPE）** | DiD / IV / RD / 合成控制 / event study / HDFE | `feols`·`did`·`ivreg`·`rdrobust`·`synth`·`sdid` | AER 三线表，8 段结构，系数 + 截距全显 |
| **Mode A · 流行病学 / 公共卫生** | target trial、IPTW、g-formula、TMLE、孟德尔随机化、survival | `msm`·`g_computation`·`tmle`·`mr`·`aft`·`kaplan_meier` | STROBE/TRIPOD；风险差 / 风险比 / 风险比率 / E-value / RMST，**不是 OLS β** |
| **Mode B · ML 因果** | DML、meta-learner、causal forest、CATE、policy、Dragonnet | `dml`·`metalearner`·`causal_forest`·`bcf`·`policy_tree` | CATE 分布图、policy-value 表、conformal 预测区间 |

- **Mode A 要点**：target-trial emulation（Hernán–Robins）先写协议（eligibility、treatment strategies、
  time-zero、causal contrast），再用 **IPTW + g-formula + TMLE 三个估计量同时报**（doubly-robust 收敛性）；
  敏感性用 E-value（MCP `evalue` / `evalue_from_result`）。
- **Mode B 要点**：per-row CATE 向量在 `ml.model_info['cate']`（**没有 `.cate_estimates` 属性**）；
  只有 DR/X/R/S/T-learner 与 `metalearner` 会填它，`causal_forest` 只给汇总 CATE。policy learning 用
  `policy_tree` / `policy_value`，不确定性用 conformal（MCP `conformal_ite`）。

---

## 3. 估计量路由（design → 函数）

下表的「MCP」列直接用 `mcp__statspai__<fn>`；「包」列是 `sp.<fn>`。**优先 MCP 拍板与拟合，要出版级
表图再切包。**

| 设计 | MCP（默认） | 包（重活出表时） | 公式 / 关键参数 |
|---|---|---|---|
| OLS（无 FE） | `regress` | `sp.regress("y ~ x1 + x2", df, cluster=...)` | — |
| 高维固定效应 | `feols` / `hdfe_ols` | `sp.feols("y ~ x | fe1 + fe2", df, vcov={"CRV1":"firm_id"})` | **需 `fixest` extra**；`\|` 是 FE 分隔符，OLS 里写 `\|` 会被误解析 |
| 2SLS / IV | `ivreg` / `iv` | `sp.ivreg("y ~ (x ~ z) + controls", df)` | 配 `effective_f_test`·`anderson_rubin_ci` 查弱工具 |
| 交错 DiD / 事件研究 | `callaway_santanna` / `sun_abraham` / `did` / `auto_did` | `sp.callaway_santanna(..., g=, t=, i=)` | **事件研究图从 CS/SA 结果出，不要用裸 TWFE** |
| RDD | `rdrobust` / `rdbwselect` / `rddensity` | `sp.rdrobust(...)` + `sp.rdplot(...)` | running var + cutoff；要 RBC CI + 密度/协变量连续性 |
| 合成控制 | `synth` / `sdid` / `scpi` | `sp.synth(...)` / `sp.sdid(...)` | treated unit + donor pool + 前期拟合 |
| DML | `dml` / `model_averaging_dml` | `sp.dml(..., model="plr")` | partialling-out / cross-fitting |
| Meta-learner / CATE | `metalearner` / `xlearner` | `sp.metalearner(..., learner="dr")` | CATE 在 `model_info['cate']` |
| 因果森林 | `causal_forest` / `rd_forest` | `sp.causal_forest(...)` | **只给汇总 CATE**；要逐行 CATE 画图用 meta-learner |
| 匹配 / 平衡 | `match` / `ebalance` / `psm` | `sp.match(...)` / `sp.ebalance(...)` | PSM / 熵平衡；配 love plot |
| TMLE（Epi） | `tmle` / `hal_tmle` | `sp.tmle(...)` | doubly-robust，需 SuperLearner |
| g-formula（Epi） | `g_computation` | `sp.g_computation(...)` | 参数 / MC g-computation |
| IPTW（Epi） | `msm` / `propensity_score` | `sp.msm(...)` | 边际结构模型 |
| 孟德尔随机化 | `mr` | `sp.mr_ivw(...)` / `sp.mr_egger(...)` | 暴露-结局汇总统计 |
| 生存 | `aft` / `kaplan_meier` / `ltmle_survival` | `sp.aft(...)` / `sp.kaplan_meier(...)` | 参数 AFT 或 doubly-robust LTMLE |

> **MCP 链路标准姿势**：`detect_design`（或显式 `design=`）→ `preflight` + `recommend`（暴露设计
> 问题、选估计量）→ 用 `as_handle=true` 拟合拿 `result_id` → `audit_result(result_id)` 列缺的稳健性
> → 逐个调它 emit 的 `suggest_function` → `honest_did_from_result` / `sensitivity_from_result` →
> `bibtex(keys=[...])` 取**已核验**引用。`paper.bib` 是引用的唯一真源，**绝不编造参考文献**。

---

## 4. 出版级出表栈（Stage 4 主路径，用 `statspai` 包）

Stage 4 要「三格式同出」（合作者改 Word、编辑要 Excel、CI 编 LaTeX），这是包的核心能力。**永远不要
从 pandas 手搓 Word/Excel**——每个结果对象都自带 `.to_word()` / `.to_latex()` / `.to_excel()`。

**Tier 1 · 单张多列表**
```python
rt = sp.regtable(M1, M2, M3, template="aer",
                 coef_labels={"training": "Training"},
                 model_labels=["OLS", "FE", "IV"],
                 stats=["N", "R2", "Cluster", "FE"])
rt.to_word("04_results/table2.docx"); rt.to_excel("04_results/table2.xlsx")
open("04_results/table2.tex", "w").write(rt.to_latex())
```
默认 AER 习惯**显示全部系数 + 截距**（除非有意 `keep=`/`drop=`）；混量级用 `fmt="auto"`。

**Tier 2 · 多面板 paper 表**（主表 + 异质性 + 稳健性一份 docx/xlsx）
```python
sp.paper_tables(main=[M1, ..., M5], heterogeneity=[H1, H2],
                robustness=[R1, ..., Rn], template="aer").to_docx("04_results/paper_tables.docx")
```

**Tier 3 · 整场 bundle**（§8 复现包，收尾用）
```python
c = sp.collect("Paper Title", template="aer")
c.add_heading("§1 Descriptives", level=1)
c.add_summary(df, vars=[...], stats=["mean", "sd", "n"])
c.add_regression(M1, M2, ..., title="Table 2")
c.save("paper.docx")   # 也可 .xlsx / .tex / .md（按扩展名自动判格式）
```

> Stage 4 把这套导出落到 `04_results/*.{tex,docx,xlsx}`，并照常生成 `04_results/exhibits_index.md`
> （每张表/图 → 论文哪个论点），供 Stage 5 写作引用。引文内嵌点估计用 `sp.cite(M3, "training")` →
> `"1.239*** (0.153)"`，避免手抄出错。

---

## 5. 标准图谱（Stage 4 出图，识别假设逐一可视化）

**铁律**：StatsPAI 的每个 plotter 和结果 `.plot()` 返回 **`(fig, ax)` 元组**——不是裸 Figure。解包再存：
```python
fig, ax = sp.parallel_trends_plot(df, y="wage", time="year", treat="training", treat_time=2015)
fig.savefig("04_results/fig1.png", dpi=300)
```
例外：`sp.binscatter(...)` 返回 **3 元组** `(fig, ax, binned_df)`，三个都要解包。脚本顶部先跑一次
retina + CJK 设置（`figure.dpi=144` / `savefig.dpi=300`，中文字体兜底），否则中文渲染成豆腐块、高 DPI 屏发糊。

| 图 | 内容 | 入口 | 段 |
|---|---|---|---|
| 1a | 原始趋势 | `sp.parallel_trends_plot(...)` | §1 |
| 1b | rollout 热力图 | `sp.treatment_rollout_plot(...)` | §1 |
| 2a | 事件研究系数 | `sp.enhanced_event_study_plot(cs)`（cs = CS 结果） | §3 |
| 2b | RD 分箱散点 | `sp.rdplot(...)` | §3 |
| 2c | love plot（匹配） | `sp.match(...).plot()` | §3 |
| 3 | 主设定系数森林 | `sp.coefplot(M1..M5, variables=["x"])` | §4 |
| 4a | 剂量-反应 | `sp.dose_response(...).plot()` | §5 |
| 4b | CATE 直方图 | `sp.cate_plot(ml, kind="hist")` | §5 |
| 5 | 稳健性森林 | `sp.coefplot(*robustness_models)` | §7 |
| 5b | 设定曲线 | `sp.spec_curve(...).plot()` | §7 |
| 6 | 敏感性（HonestDiD） | `sp.sensitivity_plot(sp.honest_did(cs, ...))` | §7 |

事件研究图配 [`design-transparency.md`](design-transparency.md) 的预趋势功效，设定曲线 / HonestDiD 配
[`threats-to-validity.md`](threats-to-validity.md) 的识别威胁回应。

---

## 6. 稳健性闸门（七块）↔ Method Gate 最低证据包

Stage 3 的 `03_analysis/method_gate.md` 的 artifact 表，由下面七块**逐块喂满**。每块都要有真实落盘路径
（`03_analysis/robustness/<name>.json|png`），缺一块对应行标 `no`、闸门不得 PASS：

1. **安慰剂**：假断点（RD）、in-time placebo（SCM）、假处理年（DiD）。
2. **替换样本**：剔极端值、平衡面板、早 cohort 排除。
3. **设定曲线**：`sp.spec_curve(df, y=, x=, controls=[...], subsets={...})` / MCP `spec_curve`。
4. **替换 SE**：双向聚类、Conley 空间、换聚类维度（MCP `twoway_cluster`/`conley`/`wild_cluster_bootstrap`）。
5. **Oster 界**：对未观测选择的敏感度，`sp.oster_bounds(..., r_max=1.3)` / MCP `oster_bounds`。
6. **HonestDiD**：Rambachan–Roth (2023) 平行趋势违背敏感度，`sp.honest_did(cs, method='smoothness')`
   / MCP `honest_did_from_result`。
7. **E-value**：翻转因果结论所需的未测混杂强度，`sp.evalue(estimate=, ci=(,), measure='RR')`
   / MCP `evalue_from_result`。

> 这七块正是 [`research-grade-methods.md`](research-grade-methods.md) 各分支「最低证据包」的 StatsPAI
> 实现入口。交错 DiD 至少要 CS/SA/BJS 之一 + 事件研究 + 第 6 块；RDD 要带宽 + RBC CI + 密度/协变量
> 连续性；DML/HTE 要 cross-fitting + nuisance 诊断 + overlap + seed 稳定性。**并行化**：把这些彼此独立的
> 检验按 [`subagent-templates.md`](subagent-templates.md) §S3 一次性派多个 subagent，各自写盘、只回传
> 「通过/不通过 + 关键系数」。

Stage 8 计量复核时，再用 MCP `audit_result(result_id)` 复跑一遍「还缺哪些稳健性」，与 `method_gate.md`
对账。

---

## 7. 结果对象接口（链式下游的关键）

每个估计量返回一个结果对象（`CausalResult` / `FeolsResult` / `DMLResult` …），统一暴露：

- `.summary()` → 文本摘要；
- `.estimate` / `.ci`（CausalResult）或 `.params[name]` / `.conf_int()`（计量类）；
- `.to_word()` / `.to_latex()` / `.to_excel()` → 导出；
- `.plot()` → `(fig, ax)`（若支持）；
- `.model_info` → 诊断字典（PT verdict、first-stage F、CATE 数组等）。

MCP 侧用 `as_handle=true` 拿 `result_id`，再把它喂给 `audit_result` / `*_from_result` 系列，**无需把 β/Σ
搬来搬去**。`detail='minimal'` 用于便宜的子步调用，默认 `'agent'` 会带 violations + next_steps。

---

## 8. 反模式清单（踩中即回炉）

- ❌ `sp.regress("y ~ x | firm_id")` 想要固定效应——`|` 在 `regress` 里不解析为 FE，**必须用
  `sp.feols`**（且装了 `fixest` extra）。
- ❌ 用裸 TWFE 画交错 DiD 的事件研究图——交错处理下 TWFE 有负权重污染，事件研究图要从 CS/SA 结果出。
- ❌ 取 `ml.cate_estimates`——不存在该属性；逐行 CATE 在 `ml.model_info['cate']`。
- ❌ 把 plotter 当成返回裸 Figure——它返回 `(fig, ax)`（`binscatter` 是 3 元组），不解包会报错或存错图。
- ❌ 从 pandas 手搓 Word/Excel 表——用结果对象的 `.to_word()/.to_excel()/.to_latex()`。
- ❌ 先 `estimate()` 后补 `identify()`——识别计划必须**先冻结落盘**，否则等于事后挑设定。
- ❌ 编造参考文献——引用一律走 `bibtex(keys=[...])`，`paper.bib` 是唯一真源。
- ❌ Mode A 报 OLS β——流行病学结局报风险差/风险比/HR/RMST + E-value，不是回归系数。
- ❌ 只跑出显著系数就收工——没喂满 §6 七块、`method_gate.md` 未 PASS，结果不得写成主因果发现。

---

## 9. 安装与一次性设置（用包路径时）

```bash
pip install "statspai[fixest,plotting]"   # 验证于 v1.16.1；neural/text 另装 extra
```
脚本/Notebook 顶部跑一次（CJK + retina）：
```python
import matplotlib as mpl
mpl.rcParams["font.sans-serif"] = ["PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC"]
mpl.rcParams["axes.unicode_minus"] = False
mpl.rcParams["figure.dpi"] = 144
mpl.rcParams["savefig.dpi"] = 300
```
所有估计脚本（`.py`）留在 `03_analysis/`，把包版本、seed、关键参数写进脚本头或 `method_gate.md`，
保证可复现。MCP 路径不写 Python，但同样要把 `result_id`、设计判定、稳健性结论记进
`method_gate.md` 与 `logs/stage_3.md`。

---

## 10. 一句话总结（怎么把 StatsPAI 用对）

1. **默认走 MCP** 把识别拍板、把系数和诊断跑出来、把缺的稳健性补齐、把引用取对（全程不落 Python）。
2. **要出版级三格式表图 + 8 段 paper bundle 时切到 `statspai` 包**，两条路径结果必须对得上。
3. **StatsPAI 喂满最低证据包，但不替闸门放行**：`method_gate.md` 仍须 PASS，质量门仍按 7 维打分。
4. **三种模式按措辞自动切**：默认应用计量；target trial→Mode A；causal forest→Mode B。
5. **踩中 §8 任一反模式 → 回炉**，绝不贴空方法标签、绝不伪造数据 / 结果 / 文献。
