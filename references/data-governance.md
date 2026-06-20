# Data Governance — 敏感数据、IRB/DUA、授权与存档边界

> 本层在 Stage 2 开始生效，贯穿 Stage 9 与收尾。目标不是增加合规口号，而是把「哪些数据能公开、
> 哪些只能脚本化、哪些会阻断投稿」写成可执行闸门。模板见
> [`../templates/data_governance.md`](../templates/data_governance.md) 与
> [`../templates/DAS.md`](../templates/DAS.md)。

---

## 1. 先分级，再取数

每个数据源进入 `02_data/raw/` 之前，先在 `00_meta/data_governance.md` 登记：

| 分级 | 典型情形 | 公共复现包怎么处理 |
|---|---|---|
| public | 官方公开下载、开放许可、可重新分发 | 可纳入包；仍需记录 URL、版本、访问日期、引用 |
| restricted | WRDS/CSMAR/CFPS 等需账号、付费、审批或 DUA | 不放原始数据；放获取流程、变量字典、清洗脚本、DAS |
| confidential | 企业/政府/IRB 限制环境，不能离开安全域 | 只放代码、合成样例、远程复现说明；`replication_pack.status` 通常为 `not_ready` 直到有受控复现方案 |
| PII / quasi-identifier | 个人、企业或地点可直接/间接重识别 | 公共包、日志、示例、截图、表格都不得包含可识别值 |

**硬规则**：

- 不把受限原始数据、PII、签名 URL、API key、cookie、token、许可证文件写入 git、日志或公开 archive。
- 不用 WebSearch/WebFetch、公开 LLM、外部浏览器上传受限或可识别数据；只能上传脱敏摘要或代码。
- 不为“看起来可复现”而伪装数据可得性。受限就写受限，审批成本、费用、等待时间照实写。
- 不做重识别、绕过 DUA、绕过 IRB/ethics 审批，或把未授权数据迁出批准环境。

---

## 2. 与当前期刊政策的运行时刷新

本文件只给工作流标准。Stage 9 或收尾面向具体期刊时，必须打开目标期刊官网最新政策页，写入
`09_submission/submission_checklist.md` 与 `workflow_state.json.decisions`。截至 2026-06-20 已核对的
权威入口包括：

- AEA Data and Code Availability Policy: https://www.aeaweb.org/journals/data/data-code-policy
- Office of the AEA Data Editor guidance: https://aeadataeditor.github.io/aea-de-guidance/
- Social Science Data Editors Template README: https://social-science-data-editors.github.io/template_README/
- Management Science Code and Data Disclosure Policy: https://pubsonline.informs.org/page/mnsc/code-and-data-disclosure-policy

这些政策的共同落点：

- DAS 必须讲清 source data 与 derivative data 的 provenance、获取条件、限制、成本和时间。
- 非公开数据不能公开时，必须解释原因并公开可公开的代码、元数据、获取流程和复现路径。
- README 需要包含软件/硬件、运行时间、程序到表图的映射、复现步骤、数据引用和缺失材料说明。
- 适用时必须披露 IRB/ethics board approval or exemption、RCT/preregistration、AsCollected 或等价 provenance。

---

## 3. Stage 接入点

| Stage | 必做治理动作 | 输出 |
|---|---|---|
| 0 | 若用户要求无人值守，缺省创建 `00_meta/data_governance.md` 占位并把未知项标 `TBD` | `00_meta/data_governance.md` |
| 2 | 每个数据源先登记分级、许可、DUA/IRB、再分发边界；清洗脚本不得复制受限原始数据到公开路径 | `02_data/codebook.md` + governance register |
| 3 | 估计脚本只读取批准路径；输出表图前检查 cell size、匿名化、聚合层级 | `03_analysis/method_gate.md` hard flags |
| 5/6/7 | 写作时不得泄露敏感样本、机构名或可识别案例；引用受限数据限制时用 DAS 语言 | `main.tex` |
| 8 | 模拟审稿把“数据能否被第三方获得”和“IRB/DUA 是否阻断复现”作为高优先级意见 | `08_review/referee_report.md` |
| 9 | 刷新目标刊 policy；生成 DAS、disclosures、AsCollected/等价 provenance | `09_submission/` |
| 收尾 | 复现包按 archive boundary 打包；公共包排除受限原始数据和 PII | `REPLICATION.md` + `FINAL_REPORT.md` |

---

## 4. 闸门联动

**Method Gate** 必须把数据治理列入 hard flags：

- 识别依赖的关键变量来自受限数据，但没有合法访问说明：`NOT PASS`。
- 样本选择、聚合或脱敏会改变 estimand，但 design register 未说明：`NOT PASS`。
- 输出 artifact 含 PII 或违反最小单元披露要求：停止，回 Stage 2/3。

**Draft Quality Gate 维度⑦** 的封顶规则：

- 没有 `00_meta/data_governance.md`：维度⑦最高 7。
- 使用受限/保密数据但 DAS 未写访问流程、成本、审批或不可分发原因：维度⑦最高 6。
- 公共包或日志里出现 PII、token、受限原始数据：维度⑦最高 4，且不得投稿。
- IRB/DUA/许可证状态未知：`replication_pack.status` 只能是 `not_ready`。

---

## 5. 最小可交付治理包

即便项目还没有跑完，也至少要有：

1. `00_meta/data_governance.md`：数据源分级、访问边界、IRB/DUA、公开包动作。
2. `02_data/codebook.md`：变量来源、构造、许可、访问日期。
3. `09_submission/DAS.md`：公开/受限数据的可得性声明。
4. `REPLICATION.md`：哪些文件可公开、哪些被排除、第三方如何获批后复现。
5. `FINAL_REPORT.md`：治理红旗和仍需人工确认的事项。

若以上任一项因真实限制无法完成，写清阻断原因，不得把状态标成 `ready`。
