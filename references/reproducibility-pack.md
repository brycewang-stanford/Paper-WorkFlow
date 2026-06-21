# Reproducibility Pack — 复现包与数据治理增强层

> 从 Stage 2 取数起持续记录、在收尾时打包、在质量门维度⑦打分时核验。本文件把现代顶刊「**可复现是
> 投稿的必要条件**」落成一套可执行标准：data provenance → 复现包结构 → README 模板 → data
> availability statement → 一键重跑契约。
>
> **分工**：[`research-grade-methods.md`](research-grade-methods.md) 的 Method Gate 管「方法 artifact
> 是否齐」（识别诊断、稳健性矩阵）；本文件管「整个项目能不能被第三方一键复跑、数据来源是否交代
> 清楚」。[`data-governance.md`](data-governance.md) 进一步管 public/restricted/confidential/PII、
> IRB/DUA 与公开 archive boundary。前者是科学性，后者是可复现性与合规边界——AEA/AEJ/AER 等期刊
> 已把后者列为**强制**。

---

## 0. 这个增强层解决什么

实证论文被接收后的最后一道关、很多顶刊投稿时的**第一道关**，是 replication package。本层要求：

1. **从 Stage 2 就记 provenance**，而不是接收后补——补的代价远高于随手记。
2. **复现包有标准结构**：原始数据 / 清洗 / 估计 / 表图 一条龙脚本化，最少手工干预。
3. **README 是合同**：第三方照着 README 就能从 `raw/` 跑到 `04_results/` 的每张表图。
4. **数据可得性声明（DAS）说真话**：受限/付费/审批数据如实写访问条件，不可分发的只留拉取脚本。
5. **治理边界先行**：PII、IRB/DUA、许可证、保密环境、不可公开原始数据先登记到
   `00_meta/data_governance.md`，再决定公开包包含什么。
6. **质量门维度⑦按真实文件打分**：有没有 codebook、有没有一键重跑命令、AEA 场景有没有 DAS、
   有没有治理登记。

> 本层是**打包标准**，落地实现仍调用既有能力（清洗 `data-cleaning`、估计各 skill、转换 `md-to-docx`，
> 见 [`skill-map.md`](skill-map.md)）。本文件规定「打包成什么样才算可复现」。

---

## 1. 外部复现锚点（权威标准入口）

| 标准 | 入口 | 在 workflow 的用法 |
|---|---|---|
| 社科复现包 README 模板（**首选**） | Social Science Data Editors, Template README: https://social-science-data-editors.github.io/template_README/ | 收尾时生成复现包 README 的骨架；联网时取最新 release / release-candidate |
| AEA 数据与代码政策 | AEA Data & Code Availability Policy（2026-02 版）: https://www.aeaweb.org/journals/data/data-code-policy | 目标为 AEA 体系期刊时的强制要求；deposit、license、unzip、version-of-record 都按此核 |
| AEA Data Editor 操作指引 | https://aeadataeditor.github.io/aea-de-guidance/ | 投稿前自检 deposit 是否合规；Prepare 步骤可在投稿前就开始 |
| AEA FAQ / verification | https://www.aeaweb.org/journals/data/faq | 预期 Data Editor 会在合理资源内运行代码，核软件、数据、代码清晰度、资源与耗时 |
| Management Science code/data disclosure | https://pubsonline.informs.org/page/mnsc/code-and-data-disclosure-policy | 目标为 MS/INFORMS 时，Stage 9 同步准备 AsCollected disclosure 与 submission-time disclosure plan |
| 模板 README 仓库（可下载） | https://github.com/social-science-data-editors/template_README | 取最新 `template-README.md` 填空 |
| 透明与可复现总则 | BITSS（Berkeley Initiative for Transparency in the Social Sciences）: https://www.bitss.org/ | 一般性 reproducibility 培训与清单 |
| 教学型复现协议 | Project TIER Protocol: https://www.projecttier.org/tier-protocol/ | 学位论文 / 教学场景的目录规范 |
| DOI 化存档 | Zenodo / OSF / Harvard Dataverse | 给复现包发一个可引用 DOI |

> 这些是标准锚点，不是硬依赖。目标期刊属 AEA 体系 → 直接套模板 README + DAS；否则用社科模板的
> 通用结构。本机不能联网时，subagent 按本文件 §3 的结构离线生成 README，**不要省略 DAS**。

**政策刷新纪律（运行时）**：Stage 9 或收尾前若要面向具体期刊投稿，必须打开目标期刊官网的最新
Author Guidelines / Data & Code policy 核一次，不得只依赖本文件。政策页若要求 AsCollected、Data
and Code Availability Form、特定仓库或匿名化格式，把要求写进 `09_submission/submission_checklist.md`
与 `workflow_state.json.decisions`。

---

## 2. Data Provenance：从 Stage 2 就开始记（不要等接收后补）

每引入一个数据源，立即在 `02_data/codebook.md` 追加一条 provenance 记录（也是 DAS 的原料）：
同时在 `00_meta/data_governance.md`（模板：
[`../templates/data_governance.md`](../templates/data_governance.md)）记录数据分级、PII、IRB/DUA、
再分发边界与公开包动作。

```markdown
## 数据源：<名称>
- 提供方 / URL：
- 访问方式：公开下载 / 注册后下载 / 付费 / 审批 / 保密专网
- 访问成本与时延：免费即时 / $X / 审批约 N 周
- 版权与再分发：可否随论文打包分发（能→打包；不能→只留拉取脚本）
- 获取日期与版本 / vintage：
- 引用（bib key）：
- 原始文件落点：02_data/raw/<...>（不可分发的不入库，仅记拉取脚本路径）
```

**纪律**：① 不可分发的原始数据**不入库**，只留 `02_data/<fetch>.py|.do` 拉取脚本 + 说明；
② 每个派生变量在 codebook 里写清「由哪些原始字段、怎么算出来」；③ 取数脚本固定随机性（见 §4）。
④ Dropbox / OneDrive / 个人网站 / GitHub 仓库本身通常不是长期可信 archive；若用于开发协作，收尾仍需
写清正式 archive plan（AEA Data and Code Repository、OSF、Zenodo、Dataverse 或目标刊认可的 trusted repository）。
⑤ PII、签名 URL、API key、cookie、DUA/IRB 限制材料不得进入公开包、日志或 git；受限数据只能通过
脚本、变量字典、申请流程和 DAS 说明支持复现。

---

## 3. 复现包结构与 README（收尾时生成）

收尾阶段把工作区整理成一个**自包含复现包**。目录沿用工作区布局
（见 [`workspace-and-state.md`](workspace-and-state.md)），并在工作区根写一份 `REPLICATION.md`，
按社科模板 README 的 15 节填写（带 ✔ 的为**必填**，✚ 为推荐）：

| # | README 节 | 必须写清 |
|---|---|---|
| 1 | Overview ✔ | 一段话：从头到尾怎么跑、产出在哪 |
| 2 | Data Availability & Provenance ✔ | 每个数据源的来源、位置、可得性（取自 §2） |
| 3 | Statement about Rights ✔ | 作者有合法访问与（可能的）再分发权 |
| 4 | License for Data ✚ | 数据使用许可（如适用） |
| 5 | Summary of Availability ✔ | 数据是「全部公开/部分受限/不可分发」三选一 |
| 6 | Details on each Data Source ✔ | 每个源的格式、字典、引用 |
| 7 | Dataset List ✔ | 所有数据文件清单 + 来源 + 是否随包提供 |
| 8 | Computational Requirements ✔ | 软件 + 版本、依赖包 + 版本、安装脚本 |
| 9 | Controlled Randomness ✔* | 所有 `set seed` 的位置与值（有随机性时必填，见 §4） |
| 10 | Memory/Runtime/Storage ✔ | 作者机器规格、跑完总时长、磁盘占用 |
| 11 | Description of Programs/Code ✔ | 每个脚本的作用与依赖顺序 |
| 12 | License for Code ✚ | 代码许可（建议 MIT/BSD） |
| 13 | Instructions to Replicators ✔ | 人能照做的分步复现步骤（含一键 master script） |
| 14 | List of Tables/Figures and Programs ✔ | **每张表/图 ↔ 生成它的脚本与行号** |
| 15 | References ✚ | 所有数据源与材料的引用 |

> 第 14 节是审稿/数据编辑最看重的一节：它把论文里 Table 3、Figure 2 精确映射到
> `03_analysis/<script>:line`。本工作区的 `04_results/exhibits_index.md` 与
> `00_meta/evidence_ledger.md` 正好是它的原料：前者管表图索引，后者管 claim 到数据、估计和脚本的全链路。

### 3.1 Master script（一键重跑契约）

复现包必须有**一个**入口脚本（`run_all.sh` / `master.do` / `make`），最少手工干预，按固定顺序：

```text
00_meta/        # 环境检查、随机种子登记
02_data/raw/    →  02_data/<clean>.py|.do|.R   →  02_data/clean.parquet
                →  03_analysis/<estimate>       →  03_analysis/results/
                →  04_results/<maketables>      →  04_results/*.tex + *.png
```

`FINAL_REPORT.md` 的「一键重跑命令」就是调用这个 master script。**复现的验收标准 = 删掉所有派生产物后，
只跑 master script，能重建 `04_results/` 的全部表图，且数字与论文一致。**

同时更新 `00_meta/workflow_state.json.replication_pack`：

```json
{
  "status": "ready",
  "readme": "REPLICATION.md",
  "master_script": "run_all.sh",
  "data_availability_statement": "09_submission/DAS.md",
  "archive_plan": "AEA Data and Code Repository draft deposit / OSF / Zenodo / Dataverse / other trusted repository",
  "runtime_minutes": 42,
  "last_rebuild_check": "2026-06-20 18:30 Beijing: rebuilt all tables and figures from clean workspace"
}
```

无法真实重跑时，`status` 只能写 `not_ready`，并在 `last_rebuild_check` 说明阻断原因；不得用空泛的
"should reproduce" 替代重跑证据。

---

## 4. Controlled Randomness（可复现的随机性）

任何用到随机性的步骤（bootstrap、cross-fitting fold 划分、随机安慰剂、ML nuisance、模拟）都必须：

- **显式 `set seed` / `np.random.seed` / `set.seed`**，把种子值与位置登记进 README 第 9 节。
- 与 Method Gate 联动：DML 的 cross-fitting、causal forest 的 honesty split、合成控制的安慰剂、
  wild cluster bootstrap 的种子，都要可复现（呼应
  [`research-grade-methods.md`](research-grade-methods.md) 的 seed stability 要求）。
- 软件随机数生成器版本敏感时（如 Stata `version` / R `RNGkind`），在 README 写清版本。

---

## 5. Data Availability Statement（DAS）—— 说真话

投稿/接收时随论文提交的 DAS，必须**明确、准确**地交代独立研究者如何、在何处、在何条件下获得数据：

```markdown
# Data Availability Statement
本文使用的数据来自 [来源]。
- [公开数据]：可在 [URL] 免费/注册后获取，随复现包提供拉取脚本与 codebook。
- [受限数据]：来自 [提供方]，需 [付费 $X / 审批约 N 周 / 保密专网] 方可访问；本文不可随包分发，
  仅提供获取流程、变量字典与构造脚本，第三方获批后可用相同脚本复现。
- 所有派生数据的构造脚本见 02_data/，估计脚本见 03_analysis/。
```

**红线**：① 不夸大可得性（受限就写受限）；② 不隐瞒处理成本与时延；③ 不可分发数据**绝不**为了「看起来
可复现」而把原始文件塞进库；④ DAS 与 `02_data/codebook.md` 的 provenance 必须一致。

---

## 6. 接入点与质量门维度⑦联动

| 接入点 | 本层做什么 | 落盘/判定 |
|---|---|---|
| **Stage 2 取数/清洗** | 每个数据源记 provenance（§2）；不可分发数据只留拉取脚本 | `02_data/codebook.md` |
| **Stage 2 数据治理** | public/restricted/confidential/PII 分级，记录 DUA/IRB/许可证与公开包动作 | `00_meta/data_governance.md` |
| **Stage 3 估计** | 登记所有随机种子（§4）；脚本留在 `03_analysis/` | README 第 9/11 节原料 |
| **Stage 4 表图** | `exhibits_index.md` 充当 README 第 14 节「表图↔脚本行号」映射 | `04_results/exhibits_index.md` |
| **Stage 9 投稿** | 目标 AEA 体系 → 生成 DAS（§5）随投稿；其它期刊按其 data policy | `09_submission/DAS.md`（如需） |
| **Stage 9 投稿** | 目标 Management Science / INFORMS → 准备 AsCollected URL / disclosure plan | `09_submission/ascollected.md` 或 checklist |
| **收尾** | 生成 `REPLICATION.md`（§3 的 15 节）+ master script + 一键重跑命令 + `replication_pack` 状态 | 工作区根 `REPLICATION.md` |
| **质量门维度⑦** | 按真实文件核验：codebook 全否、脚本齐否、一键重跑通否、AEA 场景 DAS 在否 | `00_meta/quality_scorecard.md` |

**与 [`quality-rubric.md`](quality-rubric.md) 维度⑦的硬挂钩**（把模糊的「可复现」变成可核验闸门）：

- 无 `02_data/codebook.md` 或重跑路径断裂 → 维度⑦封顶 6。
- 无 `00_meta/data_governance.md`，或受限/保密/PII 数据未登记公开包边界 → 维度⑦封顶 7；IRB/DUA/许可
  状态未知时 `replication_pack.status` 只能是 `not_ready`。
- 公共包、日志或示例中出现 PII、token、签名 URL、受限原始数据 → 维度⑦最高 4，且不得提交公开 archive。
- 结果无法从工作区代码复现，或数据来源/版权完全未交代 → 维度⑦ ≤ 4。
- 目标 AEA 体系但缺 DAS / data provenance / 访问成本说明 / 运行时间说明 → 维度⑦最高 7；
  完全没有 replication README → 最高 6。

> 一句话验收：**「把派生产物全删掉，只跑 master script，能不能重建论文里的每张表图、且数字对得上。」**
> 能 → 维度⑦达标；不能 → 回 Stage 2/3 补脚本、回收尾补一键重跑命令。
