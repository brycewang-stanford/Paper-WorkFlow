# Worklog — Competitive analysis + executable rigor layer (Phases 1–2)

Date: 2026-06-23 (Asia/Shanghai)
Trigger: 用户要求「借鉴 K-Dense + Orchestra 两个明星 skills 库，发挥本项目优势，继续打造特色」，
给出一个月时间，要求把工作做扎实。

## Context — why this work

GitHub 上「全流程自动化科研」最直接的两个同形态竞品：
- **K-Dense `scientific-agent-skills`** (29.1k★, 147 skills) — 生物/化学/医药；扁平 catalog，无编排器。
- **Orchestra `AI-Research-SKILLs`** (10.0k★, 98 skills) — ML/AI 工程；有自主两环编排器 + 「ARA 印章」严谨性评审。

两个 repo 全量 clone 后逐项分析（见 `RELATED-WORK.md` §2，证据可复现）。**关键发现**：
两者都没有「可执行的、确定性的科研严谨性闸门」。K-Dense 全仓唯一的自动化关卡是**安全扫描**；
Orchestra 的「ARA 印章」是 LLM 读清单自评的**纯散文**，repo 里唯一的真实脚本是数文件数量的
`check-inventory.sh`。两者都**没有**计量经济学/因果识别、引用诚信/撤稿/时序、可复现性的强制把关。

→ 差异化命题锁定：**别人卷「能不能写出论文」，我们卷「写出来的东西能不能信」**，且我们的严谨性是
**可执行**的（checker 返回非零，闸门就不过），这是两个竞品当前都不玩的品类。

## Phase 1 — make the moat legible & credible

- `RELATED-WORK.md`（仓库顶层，**不计入 complexity ratchet**）：landscape、两竞品逐项解剖、
  13 维能力覆盖矩阵（我方 vs 两竞品）、差异化命题、借鉴清单（注明出处）、五阶段路线图。
- `scripts/generate_rigor_report.py` + `RIGOR.md`：对标 K-Dense 自动生成的 `SECURITY.md` 信任徽章，
  但证明的是他们**做不到**的东西——把仓库内**每一个 rigor checker 的 `--selftest` 跑一遍**，
  逐项落成公开的「门禁覆盖报告」。`--check` 供 CI 检测 RIGOR.md 是否过期；任一 selftest 失败即非零退出。
  master 聚合器 `validate_skill.py` 串起全部 leaf checker，单独列为 master（不进 leaf 表，避免重复跑）。

generate_rigor_report 首跑就抓出两个真问题（selftest harness 的价值）：① `check_gate_integration.py`
裸跑才是它的 selftest（不是 `--selftest`）；② cross-reference linter 抓到 RELATED-WORK/RIGOR 前向引用了
Phase 2 尚未存在的文件。两者都已修复（后者通过实际交付 Phase 2 而非软化引用）。

## Phase 2 — pre-registration / researcher-DOF guard（可执行预注册锁）

借鉴 Orchestra 的「git 即预注册」，但做成**可被脚本判定**的硬不变量（他们最弱的地方）：

- `templates/preregistration.md`：预注册/分析计划模板（Lock Status / Confirmatory Hypotheses /
  Primary Specification Lock / Confirmatory vs Exploratory / Deviations / Provenance 标签）。
- `scripts/check_preregistration.py`（带 `--selftest`）：读工作区 `00_meta/preregistration.md` 与
  `03_analysis/results/main_results.json`。**硬不变量**——有主结果却 UNLOCKED、或 `locked_before_estimation`
  非 yes，即研究者自由度违规，直接 FAIL；未锁但还没结果只是 INFO（未完成 ≠ 违规）；确认性假设为空/占位也 FAIL。
- 接入 `validate_skill.py`：REQUIRED_TEMPLATES + check_assets + check_python_compile + 新 wiring 函数 +
  main() 调用（满足 cross-ref `harness_wiring` 契约：现在 7 个 `scripts/check_*.py` 全部 wired）。
- 扩 `references/design-transparency.md` §2.1 + §7：把执行锁写成 Method Gate 硬挂钩——锁未过 → 选择性报告
  风险未关 → Method Gate 不得 PASS；任何不在锁内的主结果降级为 exploratory。**扩现有 reference，未新增文件**。

## Verification（evidence before claims）

- `python3 scripts/check_preregistration.py --selftest` → OK
- `python3 scripts/generate_rigor_report.py` → **10/10 checkers pass their selftest (all green)**
- `python3 scripts/check_cross_references.py` → 全 7 项 OK（harness_wiring 7/7、repo_path_mentions 232 resolve）
- `python3 validate_skill.py`（master）→ `OK: Paper-WorkFlow skill checks passed`
- `python3 evals/check_complexity_budget.py` → **RATCHET OK**。SKILL.md **未改**（35304 B，resident 层持平）；
  reference 文件数持平 29；reference bytes +2033（design-transparency 扩写，仅 WARN，非违规）。

## Design discipline

- 严守 complexity ratchet：所有新增 load-bearing 逻辑进 `scripts/` + `templates/`（不计棘轮），
  指南进**已有** reference（不新增 reference 文件），**完全不动 SKILL.md**。
- 每个新 checker 自带 `--selftest`，纳入 master 聚合器，保持「严谨性可执行」的统一纪律。

## Phase 3 — two-tier L1/L2 review + severity + verbatim-evidence（可执行的语义评审）

借鉴 Orchestra 的「ARA 印章」六维评审设计（评分锚点 + severity + verbatim 证据 + accept/reject），但把它的最弱
环节——**纯 LLM 自评**——换成可执行校验：

- `references/quality-rubric.md`：新增「L1/L2 两级评审」节（L1=结构可执行 / L2=语义 critic，L1 不绿 L2 不得 PASS）、
  severity 三档（blocking/major/minor，对应既有「致命红旗」）、**逐条 finding 必须带 verbatim 证据 span + locator**
  的硬要求；并把「评分卡输出格式」示例升级为含 Findings Register。**扩现有 reference，未新增文件**。
- `templates/quality_scorecard.md`：升级为 L1/L2 框架 + 机器可解析的 **Findings Register**（severity / verbatim span /
  locator / fix）+ Review Grade（STRONG-PASS…REJECT，沟通用，非闸门）。
- `scripts/check_review_scorecard.py`（带 `--selftest`）：读 `00_meta/quality_scorecard.md`，机械校验——7 维都给 0–10、
  每条 finding 有 severity + 非占位 verbatim + locator、**blocking finding 的维度分必须 ≤4**、**声明 PASS 必须与分数
  自洽（每维 ≥7、总分 ≥56、register 无 blocking）**。这把 rubric 里原本只是散文的「致命红旗封顶」「PASS 需无红旗」
  变成 `exit 1`——critic 无法一边藏致命红旗一边宣称 PASS。
- 接 `validate_skill.py`（8 个 check_*.py 全 wired）+ `generate_rigor_report.py`（新增 run-time gate）。

**集成测试（不只 selftest）**：把真实模板拷进临时工作区跑 checker——未填模板正确 FAIL（缺分数 + 占位 verbatim）；
「作弊卡」（声明 PASS 却在 dim2 藏 blocking finding 且给 8 分）被三处抓住（blocking 封顶、fatal-flag 与分数矛盾、
PASS 与 blocking 并存）。证明 parser 与真实模板结构对齐、防作弊不变量生效。

## Phase 5 — consolidate / self-check / commit（no push）

- 验证：`generate_rigor_report.py` → **11/11 green**；`check_cross_references.py` → harness_wiring 8/8、全一致；
  `validate_skill.py`（master）→ OK；`check_complexity_budget.py` → RATCHET OK。
- 棘轮：SKILL.md **始终未改**（35304 B）；reference 文件数持平 29；reference bytes 增长仅触发 WARN（design-transparency
  +2033、quality-rubric +~2585，均为 load-bearing 新增、非重复），未越硬天花板。
- **未填 SKILLOPT_PACKET**：本轮全部改动是「可执行门禁 + 模板 + reference 扩写 + 顶层文档」基础设施，**常驻路由层
  SKILL.md 字节未变**，held-out 评分对象未动；按 loop「不靠训练集幻觉自评」纪律，不为基础设施伪造 rollout 凑包。
- 提交：本地 commit，**不 push**（遵用户指令）。

## Parallel-work note（避免与并行 agent 撞车）

收尾时发现同一工作树里有并行 agent 正实时新增文件：`evals/check_replication_accuracy.py`（Stage-3
复现准确度基准，sign-correct/perfect/partial）、`evals/check_quality_judge.py`、`evals/replication_cases/`。
处理原则（按「path-scoped、勿撞车」）：**我不改、不依赖、不提交它们**，由对方自行提交。

为此把 `generate_rigor_report.py` 的 **drift 检测改为 advisory**：未注册的 checker 只在报告里列为「Registry
drift (advisory)」提示后续注册，**不再 flip 报告为红、不失败 CI**；`--check` 的新鲜度比对**排除 drift 段**，
使并行 agent 在 `evals/` 持续加文件时本报告与 CI 都不抖动（已用临时 fake checker 验证 `--check` 不 flap）。
待这些 sibling checker 稳定落盘后，再把它们注册进 `generate_rigor_report.py`（删掉对应豁免即可）。

## Still queued

- **P4（用户暂缓）**：引用诚信深化（quote-vs-source 忠实度、citation laundering 深度）+ identification/estimation 契约
  （借 K-Dense `retrieval-contract` 模式，但脚本强制）。
- **注册 sibling checkers**：并行 agent 的 `evals/check_replication_accuracy.py` / `check_quality_judge.py` 稳定后纳入 rigor 索引。
