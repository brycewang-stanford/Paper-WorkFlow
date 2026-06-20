# Research-Grade Methods Pack — 实证论文方法增强层

> 在 Stage 1 定设计、Stage 3 跑估计、Stage 7 后质量门打分时加载。本文件把现代应用计量与因果推断的
> 方法要求落成一个可执行的 evidence bundle：**没有证据包，就不能给论文贴上 DiD / IV / RDD /
> synthetic control / DML 等方法标签**。

---

## 0. 这个增强层解决什么

Paper-WorkFlow 原本已经能把选题、数据、估计、表图、写作和投稿串成一条线。本增强层进一步要求：

1. **先注册设计，再跑模型**：Stage 3 开始前写 `03_analysis/design_register.md`，明确 estimand、
   treatment、comparison group、识别假设、主估计量、替代估计量和失败回退。
2. **每种方法都有最低证据包**：例如交错 DiD 不能只给 TWFE；RDD 不能缺密度/操纵检验；DML 不能缺
   cross-fitting 与 nuisance diagnostics。
3. **方法选择与软件选择分离**：先问研究设计需要什么估计量，再选择 StatsPAI / Stata / R / Python /
   method package；不要因为某个包方便就倒推研究设计。
4. **质量门按证据而非标签打分**：`quality-rubric.md` 的识别、稳健、复现三维应检查本文件要求的
   artifact 是否真实存在。

---

## 1. 外部方法锚点（用于联网/引用/实现时的权威入口）

| 方法层 | 首选入口 | 何时接入 workflow |
|---|---|---|
| 交错 DiD / group-time ATT | Callaway & Sant'Anna DiD: https://bcallaway11.github.io/did/articles/multi-period-did.html | 多期、异时点处理；替代 naive TWFE |
| 动态事件研究异质性 | Sun & Abraham event-study paper: https://arxiv.org/abs/1804.05785 | 有 leads/lags 且 treatment timing 不一致 |
| RDD robust inference | `rdrobust`: https://github.com/rdpackages/rdrobust | running variable + cutoff；需要 bandwidth、RBC CI、density test |
| Synthetic DiD | Arkhangelsky et al. AER: https://www.aeaweb.org/articles?id=10.1257/aer.20190159 | 单一/少数 treated unit、长前期、SC 与 DiD 都有吸引力 |
| Quasi-experiment Python | CausalPy: https://causalpy.readthedocs.io/ | Bayesian/OLS quasi-experiment wrapper：DiD、SC、RDD、ITS |
| Double / debiased ML | DoubleML docs: https://docs.doubleml.org/stable/guide/basics.html | 高维 controls、orthogonal score、cross-fitting 需要显式产物 |
| HTE / CATE ML | EconML docs: https://www.pywhy.org/EconML/spec/motivation.html | 异质性处理效应、policy learning、CATE 估计 |
| Causal forest / GRF | GRF docs: https://grf-labs.github.io/grf/ | 非参数 HTE、instrumental forests、多处理臂/分位数/生存扩展 |
| Graph + refutation | DoWhy docs: https://www.pywhy.org/dowhy/v0.13/user_guide/intro.html | 需要 DAG、identify-estimate-refute、placebo/refuter 自动化 |
| 高维固定效应 | PyFixest: https://github.com/py-econometrics/pyfixest | Python 里复刻 fixest 风格 FE/IV/Poisson 与聚类稳健推断 |
| 复现与数据政策 | AEA Data & Code Policy（2026-02 版）: https://www.aeaweb.org/journals/data/data-code-policy | Stage 2 起就记录 data provenance；收尾写 replication README 并更新 `replication_pack` |

这些是方法锚点，不是硬依赖。若本机没有某个包，subagent 应优先用已有 StatsPAI/Stata/R/Python 工具复刻
同等诊断；无法复刻时在 `method_gate.md` 标红，而不是静默省略。

---

## 2. `design_register.md` 模板（Stage 1/3 之间的合同）

Stage 3 开始前必须写入 `03_analysis/design_register.md`：

```markdown
# Design Register — <研究短名>

## Estimand
- Target estimand: ATT / ATE / CATE / LATE / ITT / event-time ATT / other
- Unit of analysis:
- Treatment definition:
- Outcome definition:
- Time window:
- Comparison group:

## Assignment / Identification
- Source of identifying variation:
- Core identifying assumption:
- Why the assumption is plausible in this setting:
- Main threats:
- What evidence would falsify the design:

## Estimator Stack
- Primary estimator:
- Required diagnostics:
- Robustness estimators:
- Software route: StatsPAI / Stata / R / Python package / other
- Fallback if diagnostics fail:

## Artifact Contract
- Main result file:
- Diagnostic figures/tables:
- Robustness files:
- Replication scripts:
```

Stage 1 的 `proposal.md` 给方向；`design_register.md` 把方向变成可审计的计量合同。Stage 3 结束时如果估计
路线改变，必须更新这个文件并把变更写入 `workflow_state.json.decisions`。

---

## 3. 方法最低证据包（Stage 3 方法闸门）

| 设计 | 主估计量 | 必须落盘的证据 | 若失败怎么回退 |
|---|---|---|---|
| **2x2 DiD** | TWFE 或等价 DID | 处理/对照定义、pre-trend 图、事件研究图、聚类层级说明、placebo timing | 换窗口/对照组；若 pre-trend 不过，不能继续因果解读 |
| **交错 DiD** | CS / SA / BJS / imputation 类估计量 | group-time ATT、event-study aggregation、cohort composition、naive TWFE 对照及风险说明 | 改用 group-time 或 imputation；TWFE 只能作对照表 |
| **IV / 2SLS** | LATE / 2SLS | 第一阶段、弱工具稳健推断、排他性叙事、reduced form、over-ID（如适用） | 换工具；降级为相关性分析时必须改写论文措辞 |
| **RDD** | local polynomial + RBC CI | bandwidth choice、robust bias-corrected CI、McCrary/density、covariate continuity、donut、placebo cutoffs | 换 bandwidth / donut；若操纵严重，回 Stage 1 改设计 |
| **Synthetic Control / SDID** | SC / SDID | donor pool、unit/time weights、pre-fit RMSPE、in-space/in-time placebo、leave-one-out | donor pool 不稳则改 DiD/RDD 或缩小 claim |
| **Panel FE** | FE/HDFE | FE 结构、聚类层级、alternative SE、wild cluster/bootstrap（小 cluster 时）、样本进入退出 | 修聚类/SE；若核心 variation 被 FE 吸收，回 Stage 1 |
| **DML / Orthogonal ML** | PLR / IRM / IIVM / DR learner | cross-fitting folds、nuisance model metrics、overlap、orthogonal score、seed stability | 降级为传统估计 + ML robustness；不能只报黑箱 CATE |
| **HTE / Causal Forest / GRF** | CATE / forest-based effect | honesty/sample split、ATE 校准、heterogeneity test、policy subgroup stability、variable importance caveat | HTE 不稳则只保留主效应，异质性降为 exploratory appendix |
| **Causal Graph + Refutation** | DoWhy-style identify-estimate-refute | DAG/source assumptions、identified estimand、placebo refuter、random common cause、subset/refit checks | refuter 失败则缩小因果 claim 或回 Stage 1/3 |
| **Prediction-assisted empirics** | ML controls / text-as-data / embeddings | leakage audit、train/test split、feature provenance、post-treatment variable screen、human-valid labels | 泄漏/后处理变量风险未清，不能进入主识别设定 |

Stage 3 完成时写 `03_analysis/method_gate.md`：

```markdown
# Method Gate — <研究短名>

Primary design: <design>
Primary estimator: <estimator>
Status: PASS / NOT PASS

| Required artifact | Path | Present? | Notes |
|---|---|---|---|
| Design register | 03_analysis/design_register.md | yes/no | |
| Main estimate | 03_analysis/results/main_results.json | yes/no | |
| Identification diagnostic | ... | yes/no | |
| Robustness matrix | 03_analysis/robustness/ | yes/no | |
| Reproducible scripts | 03_analysis/<script> | yes/no | |

## Hard Flags
- <none, or exact blocker>

## Next Action
- If NOT PASS, route back to Stage <N> because ...
```

质量门可以比方法闸门更严，但不能比它更松：若 `method_gate.md` 是 `NOT PASS`，`quality_gate` 的识别维度
不得给到 7 分以上。

---

## 4. 新增/增强 skill 路由建议

把这些能力作为 `skill-map.md` 的增强项使用；若母仓库已存在同名 skill 或 MCP，优先调用；否则由 subagent
按官方文档实现最小可复现脚本。

| 能力 | 建议 skill 名 / route | 接入点 |
|---|---|---|
| design-register | `research-design-register`（新建时） | Stage 1 末 / Stage 3 初 |
| method-gate auditor | `causal-method-gate`（新建时） | Stage 3 末，写 `method_gate.md` |
| DiD modernizer | `modern-did` / StatsPAI `auto_did` | Stage 3 DiD 分支 |
| RDD diagnostics | `rdd-diagnostics` / `rdrobust` | Stage 3 RDD 分支 |
| DML/HTE runner | `doubleml-runner` / `econml-runner` / `grf-runner` | Stage 3 ML causal 分支 |
| DAG/refuter | `dowhy-refutation` | Stage 1 设计审查、Stage 3 稳健性 |
| replication pack | `aea-replication-pack` | Stage 2 起记录 provenance；Stage 9/收尾打包 |

这些 route 的共同 I/O 约定：读 `design_register.md`、`clean.parquet`、主设定脚本；写
`03_analysis/<method>/` 下的诊断、结果和日志；只向主代理返回短摘要。

---

## 5. 写作端如何使用方法增强层

- **Intro / identification 段**：只写 `design_register.md` 与 `method_gate.md` 已经通过的识别语言。
- **Results 段**：主结论必须对应 `main_results.json`；稳健性措辞必须对应 `robustness/` 真实结果。
- **Appendix**：把未进入主线但有解释价值的诊断图、placebo、refuter 结果放入附录，不要丢掉失败证据。
- **Cover letter / submission**：若目标是 AEA/AER/AEJ，一开始就按 AEA data/code policy 写 data
  provenance，不等 acceptance 后补；若目标刊有 submission-time disclosure（如 AsCollected / data-code
  form），Stage 9 前刷新官网政策并写入 `09_submission/submission_checklist.md`。

---

## 6. 对质量门的硬约束

质量门 critic 打分时：

- 找不到 `design_register.md`：识别维度封顶 6。
- 找不到 `method_gate.md`：识别维度封顶 6，稳健维度封顶 6。
- `method_gate.md` 为 `NOT PASS`：识别维度封顶 4。
- 缺本文件 §3 对应的最低证据包：对应维度不得过 7。
- 论文因果措辞强于证据包：结果解读维度最多 6。
