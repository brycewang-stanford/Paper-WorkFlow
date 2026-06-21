# Computational Reproducibility Pack — 确定性、环境固定与产出核验

> [`reproducibility-pack.md`](reproducibility-pack.md) 的**技术姊妹篇**。前者管「复现包**完整不完整**」
> （provenance、README 15 节、DAS、archive）；本文件管「把派生产物删掉、重跑，**数字能不能真的对上**」——
> 环境能否重建、随机性与并行能否确定、产出能否自动比对到容差内。和 [`measurement-and-data-quality.md`](measurement-and-data-quality.md)
> （数据本身质量）一起，构成可复现性的三个技术面。在 Stage 2 起就配置、收尾时验收、质量门维度⑦据此打分。

---

## 0. 这个增强层解决什么

「数字和论文一致」不能靠口头。三道技术关，任一不过都会让「跑完」≠「可复现」：

1. **环境能不能重建**——只列版本号会腐坏；要 lockfile 或容器。
2. **随机性与并行能不能确定**——`set seed` 是必要不充分；线程、BLAS、hash、locale、GPU 都会改末位。
3. **产出能不能机器核验**——要有 expected-output manifest + checksum + 浮点容差，而非肉眼比对。

落地实现仍调用既有清洗/估计/出表能力；本文件规定「复现跑要配置成什么样、验收要核到什么程度」。

---

## 1. 环境固定阶梯（environment pinning ladder）

| 级别 | 做法 | 何时够用 |
|---|---|---|
| **L0** 列版本 | README §8 列 Python/Stata/R + 主要包版本 | 最低，单独用易腐坏 |
| **L1** lockfile | `requirements.txt`（`pip freeze`）/ `environment.yml` / `renv.lock` / `Manifest.toml`；Stata 记 `version` + ado/ssc 包版本 | **默认要求** |
| **L2** 容器 | `Dockerfile` / Apptainer / Code Ocean capsule，固定 OS + 库 + 随机 | 受限计算、长期存档、AEA Data Editor 核验偏好 |
| **L3** 声明式 | Nix / Binder 完全可重建 | 加分 |

- **至少 L1**；目标 AEA 体系或追求长期可复现 → L2。所用级别写进 `workflow_state.json.replication_pack.env_level` 与
  [`repro_environment.md`](../templates/repro_environment.md)。
- **Stata 特例**：`version 18` 锁定语法版本；社区包（`reghdfe`/`csdid`/`did_imputation` 等）更新会改数字，必须记
  ado 版本与来源（`which`、`net describe`、`ssc` 安装日期）。
- **R 特例**：`renv.lock` 锁包；记 `RNGkind` 与 `R.version`。注意 **R 3.6.0 改了 `sample()` 默认算法**
  （新增 `sample.kind="Rejection"`）——跨 R 版本复现随机抽样必须显式设 `RNGkind(sample.kind=...)`。
- **Python 特例**：`pip freeze` 或 `conda env export`；记 **BLAS 实现**（OpenBLAS / MKL），因为线性代数后端换实现会改末位。

---

## 2. 确定性，不止 `set seed`（determinism beyond seeds）

种子只是第一层。下面每一项不锁，都可能让重跑结果在末位甚至更高位漂移：

- **种子全登记**：bootstrap、cross-fitting fold、随机 placebo、ML nuisance、模拟——每个随机点显式设种子并登记
  （呼应 [`reproducibility-pack.md`](reproducibility-pack.md) §4 与 [`inference-and-uncertainty.md`](inference-and-uncertainty.md)）。
- **hash 随机化**：设 `PYTHONHASHSEED=0` 固定 `str`/`bytes`/`datetime` 的 hash——否则 **`set` 迭代顺序**及依赖该
  hash 的分组在不同进程间不稳定（注意：CPython ≥3.7 的 `dict` 按**插入序**，本身不受该 seed 影响）。
- **线程 / BLAS 非确定性**：多线程归约的浮点求和**顺序不定 → 末位漂移**。复现跑固定线程：
  `OMP_NUM_THREADS=1`、`OPENBLAS_NUM_THREADS=1`、`MKL_NUM_THREADS=1`、`VECLIB_MAXIMUM_THREADS=1`、`NUMEXPR_NUM_THREADS=1`。
- **GPU 非确定性**：ML 用 GPU 时，cuDNN / atomic 归约默认非确定；设 deterministic 标志
  （PyTorch `torch.use_deterministic_algorithms(True)` + `CUBLAS_WORKSPACE_CONFIG=:4096:8`），或在 README 声明
  GPU 结果仅在容差内可复现。
- **排序 / locale 稳定**：依赖行序的操作（groupby 后取首行、tie-breaking、字符串排序）用**稳定排序 + 显式 tie-break 键**；
  设 `LC_ALL=C` 固定排序与数字格式。
- **时间 / 路径不入产出**：wall-clock、随机 tmp 路径、绝对路径不得写进表图或结果文件；用相对路径，run 时间戳由 master script 统一注入。

---

## 3. 产出核验与浮点容差（output integrity & tolerance）

让「数字一致」可被机器核：

- **expected-output manifest**：把每张表/图的关键数字（点估计、SE、N、关键诊断）抽到 `04_results/expected/`
  的小 JSON/CSV，作为 ground truth。
- **checksum**：对发布的派生数据与表图存 sha256（`04_results/MANIFEST.sha256`、`02_data/raw/MANIFEST.sha256`），
  重跑后比对，检测 silent data drift / 文件被悄悄改。
- **浮点容差**：**不强求 bit-identical**（跨平台 BLAS 末位本就会差）；定一个容差——相对误差 ≤ 1e-6，或「四舍五入到
  论文报告位数后相等」——用 [`check_outputs.py`](../templates/check_outputs.py) 比对，超容差非零退出。
- **图核底层数值**：图难做像素级比对（字体/后端会变）；**核生成图的底层数值（导出 CSV）**，而非 PNG 像素。
- **diff harness**：master script 末尾跑 `check_outputs.py` 对 manifest 逐项比对，非零退出即判复现失败。

> 与质量门维度⑦联动：有 manifest + 容差核验通过 = ⑦ 达标的**硬证据**；只有口头「should reproduce」按
> [`reproducibility-pack.md`](reproducibility-pack.md) §6 封顶。

---

## 4. Master script 合同强化

master script（`run_all.sh` / `master.do`）除
[`reproducibility-pack.md`](reproducibility-pack.md) §3.1 的固定顺序外，应：

1. **step 0 捕获环境**到 `00_meta/env_capture.txt`（`pip freeze` / `sessionInfo()` / `creturn`、`uname -a`、
   线程与 seed env 变量）；
2. **设确定性 env**（§2 的线程 / hash / locale 变量）；
3. **每步时间戳日志**到 `logs/run_all_<stamp>.log`，记录起止与耗时（喂 README §10 的 runtime 字段）；
4. **末步跑 `check_outputs.py`** 比对 manifest；
5. 全程**相对路径** + `set -euo pipefail`，失败即停。

模板见 [`../templates/run_all.sh`](../templates/run_all.sh)、[`../templates/check_outputs.py`](../templates/check_outputs.py)、
[`../templates/repro_environment.md`](../templates/repro_environment.md)。

---

## 5. 接入点（与阶段、状态、质量门挂钩）

| 接入点 | 本层做什么 | 落盘 / 判定 |
|---|---|---|
| **Stage 2 取数** | 起 env 记录、设确定性 env、原始数据 checksum | `00_meta/env_capture.txt`、`02_data/raw/MANIFEST.sha256` |
| **Stage 3 估计** | 全部随机点登记 seed；复现跑固定线程（单线程或固定数） | `inference_report.md` / `logs/` |
| **Stage 4 表图** | 导出表图底层数值到 `expected/` 并生成 manifest + checksum | `04_results/expected/`、`MANIFEST.sha256` |
| **收尾** | 跑通 master script、`check_outputs.py` 通过、记录环境固定级别 | `workflow_state.json.replication_pack.{status, env_level}` |
| **质量门⑦** | 按真实核验打分：manifest 通过否、env 固定级别、确定性是否配置 | `00_meta/quality_scorecard.md` |

---

## 6. 反模式清单

- 只 `set seed` 不锁线程 / BLAS，跨机末位漂移就当「天生不可复现」；
- `pip` 不 freeze、`conda` 不 export、Stata 不记 ado 版本——「装最新版」让包升级**悄悄改数字**；
- 比对 PNG 像素而非图的底层数值；
- 把绝对路径 / wall-clock / 随机 tmp 路径写进产出；
- 声称 "should reproduce" 却没有 manifest / 容差核验脚本；
- ML 用 GPU 出主结果，却不设 deterministic 标志也不声明只在容差内可复现。

---

## 7. 锚点（按需查证）

- ACM, "Artifact Review and Badging — Current"（Reproduced / Replicated 的术语定义）。
- AEA Data Editor guidance（环境捕获与运行核验，入口见 [`reproducibility-pack.md`](reproducibility-pack.md) §1）。
- NumPy / OpenBLAS 多线程归约导致的末位非确定性，是「同代码同机器多次结果略不同」的常见根因；固定线程数消除
  **单实现内**的非确定，但**跨实现 / 跨平台**（OpenBLAS vs MKL vs Accelerate、FMA、架构差异）末位仍会差——所以
  §3 仍要靠**容差**而非苛求 bit-identical。
- R `sample()` 算法变更：R 3.6.0 release notes（`sample.kind`）。
</content>
