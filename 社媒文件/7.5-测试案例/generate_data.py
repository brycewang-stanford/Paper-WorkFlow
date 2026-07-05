#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CFPS 风格的两期面板数据生成脚本
====================================
研究主题：个体互联网使用对个人收入的影响

设计：
  - 样本：N = 2000 个个体，2018 / 2020 两期平衡面板
  - 个体 ID (pid) 在两期稳定；家庭 ID (fid) 反映 CFPS 的家庭结构
  - 真效应：ln_income 对 internet_use 的弹性约为 +0.18
  - 工具变量：family_internet_2018（家庭2018年是否接入宽带）
  - 故意保留部分缺失值，模拟真实微观调查

输出：
  - cfps_internet_income_panel.csv   主数据集
  - codebook.md                       变量说明（中英文对照 + DGP 真值）
  - README.md                         数据集使用说明

DGP 真值（与代码中 beta 字典一一对应）：
  beta_int      = +0.18   (主效应：互联网使用 → ln(收入))
  beta_edu      = +0.07   (教育年限)
  beta_age      = +0.04   (年龄)
  beta_age2     = -0.04   (年龄^2/100，生命周期)
  beta_female   = -0.15   (性别，1=女)
  beta_health   = +0.08   (自评健康 1-5)
  beta_marital  = +0.05   (已婚)
  beta_urban    = +0.22   (城镇)
  beta_fatheredu = +0.02  (父亲教育年限)
  alpha_prov    = 省级固定效应（均值 0，sd 0.15）

  Internet 选择方程：
    prob(internet) = sigmoid(gamma0 + γ_edu·education + γ_age·(-age/40)
                              + γ_urban·urban + γ_fatheredu·father_edu
                              + γ_female·female + γ_health·health
                              + γ_family_int·family_internet_2018)
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


# ---------- 1. 参数设定 ----------
SEED = 20250705
N = 2000
YEARS = [2018, 2020]
N_PROV = 28  # 中国省级单位个数（含直辖市、自治区）

# 真实效应（DGP 真值；复现研究可以用此校准估计量）
BETA = {
    "int": 0.18,        # 互联网使用对 ln(收入) 的弹性
    "edu": 0.07,
    "age": 0.04,
    "age2": -0.04,      # 乘以 age^2/100
    "female": -0.15,
    "health": 0.08,
    "marital": 0.05,
    "urban": 0.22,
    "fatheredu": 0.02,
}

# Internet 选择方程系数（故意制造 OVB：受教育高的人更可能上网 → 选择偏差）
GAMMA = {
    "intercept": -2.5,
    "edu": 0.30,
    "age": -0.025,         # 乘以 age（年轻更可能上网）
    "urban": 0.50,
    "fatheredu": 0.04,
    "female": -0.10,
    "health": 0.10,
    "family_internet_2018": 1.20,   # 工具变量系数（强 IV）
}

# 年龄真实固定效应（基础截距 + 省份效应）
ALPHA_PROV_SD = 0.15
EPSILON_INCOME_SD = 0.45
EPSILON_SELECTION_SD = 1.0


# ---------- 2. 个体层面时不变变量 ----------
def draw_individual_characteristics(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """一次性画出个体层面时不变的变量（性别、出生年、父亲教育、初始省份）。"""
    pid = np.arange(1, n + 1)

    # 家庭结构：每个家庭 1-3 人；先抽家庭数，再让个体落入家庭
    fam_size = rng.integers(low=1, high=4, size=n)
    fid = np.empty(n, dtype=int)
    cur = 1
    fid_idx = 1
    for size in fam_size:
        for _ in range(size):
            if fid_idx - 1 >= n:
                break
            fid[fid_idx - 1] = cur
            fid_idx += 1
        cur += 1
    # 截断/补齐
    if fid_idx - 1 < n:
        # 把剩余个体补到最后一个家庭
        fid[fid_idx - 1:] = cur

    # 性别：1=男, 0=女（劳动力人口男性略多于女性，0.52/0.48）
    gender = rng.binomial(1, 0.52, size=n)

    # 出生年：劳动力 25-55 岁（2018 时），即 1963-1993
    birth_year = rng.integers(low=1963, high=1994, size=n)

    # 父亲教育年限：6/9/12 三峰（小学/初中/高中以上）
    father_edu = np.where(
        rng.random(n) < 0.35, 6,
        np.where(rng.random(n) < 0.65, 9, np.where(rng.random(n) < 0.9, 12,
        rng.integers(13, 17, size=n))),
    )

    # 省份（用于固定效应）
    provcode = rng.integers(1, N_PROV + 1, size=n)

    return pd.DataFrame({
        "pid": pid,
        "fid": fid,
        "gender_male": gender,
        "birth_year": birth_year,
        "father_edu": father_edu.astype(float),
        "provcode": provcode,
    })


def draw_family_iv(df_ind: pd.DataFrame, rng: np.random.Generator) -> np.ndarray:
    """为每个个体计算 2018 年家庭宽带接入（时不变工具变量）。
    与家庭背景（父亲教育、出生地代际网络）正相关，但与个人收入无关 → 满足相关性+排他性。
    """
    n = len(df_ind)
    family_int_latent = (
        0.05 * df_ind["father_edu"]
        + 0.03 * (2018 - df_ind["birth_year"])  # 年轻个体所在家庭更早接入网络
        + 0.005 * df_ind["provcode"]              # 省份网络基础设施差异
        + rng.normal(0, 1.0, size=n)
    )
    return (family_int_latent > 0.5).astype(int)


def draw_panel(df_ind: pd.DataFrame, family_int_2018: np.ndarray, rng: np.random.Generator) -> pd.DataFrame:
    """对每个个体每年生成一次观测，构造完整面板。"""
    n = len(df_ind)
    df_ind = df_ind.copy()
    df_ind["family_internet_2018"] = family_int_2018

    rows = []
    for yr in YEARS:
        df = df_ind.copy()
        df["year"] = yr
        # 年龄：2018 时年龄 = 2018 - birth_year；2020 时 +2
        df["age"] = yr - df["birth_year"]

        # 城乡：城镇比例约 0.45（CFPS 抽样口径近似）
        df["urban"] = rng.binomial(1, 0.45, size=n)

        # 教育年限：男女略不同；2018 已有教育随时间变化不大（CFPS 大多数受访者教育已完成）
        # 简化：education = max(0, 父教育 + 噪声 - 少量未完成)
        noise_edu = rng.normal(0, 1.5, size=n)
        # 让教育反映代际提升：年轻人比父辈多约 2-4 年
        gap_from_parent = rng.normal(3, 1.2, size=n) - (df["age"] - 30) * 0.02
        gap_from_parent = np.clip(gap_from_parent, 0, 12)
        df["education"] = np.clip(df["father_edu"] + gap_from_parent + noise_edu, 0, 22)

        # 婚姻：已婚概率随年龄上升
        p_marital = 1 / (1 + np.exp(-(df["age"] - 28) * 0.18))
        df["marital"] = (rng.random(n) < p_marital).astype(int)

        # 自评健康 1-5：年龄越大越差
        health_mean = 4.2 - 0.012 * (df["age"] - 25)
        health_mean = np.clip(health_mean, 1.5, 5)
        df["health"] = np.clip(np.round(rng.normal(health_mean, 0.7)), 1, 5).astype(int)

        # 家庭当年接入宽带
        if yr == 2018:
            df["family_internet"] = family_int_2018
        else:
            # 2020 期家庭接入是 2018 基线 + 缓慢扩散
            diffusion = rng.binomial(1, 0.12 + 0.05 * df["urban"], size=n)
            df["family_internet"] = np.maximum(family_int_2018, diffusion)

        # 选择方程：prob(internet_use)
        sel_z = (
            GAMMA["intercept"]
            + GAMMA["edu"] * df["education"]
            + GAMMA["age"] * df["age"]
            + GAMMA["urban"] * df["urban"]
            + GAMMA["fatheredu"] * df["father_edu"]
            + GAMMA["female"] * (1 - df["gender_male"])
            + GAMMA["health"] * df["health"]
            + GAMMA["family_internet_2018"] * family_int_2018
            + rng.normal(0, EPSILON_SELECTION_SD, size=n)
        )
        prob_internet = 1 / (1 + np.exp(-sel_z))
        df["internet_use"] = (rng.random(n) < prob_internet).astype(int)

        # ln(收入) DGP
        prov_effect = rng.normal(0, ALPHA_PROV_SD, size=N_PROV)[df["provcode"].values - 1]
        ln_income = (
            8.5  # 基础截距 ≈ ln(5000) 月薪水平
            + BETA["int"] * df["internet_use"]
            + BETA["edu"] * df["education"]
            + BETA["age"] * df["age"]
            + BETA["age2"] * (df["age"] ** 2) / 100
            + BETA["female"] * (1 - df["gender_male"])
            + BETA["health"] * df["health"]
            + BETA["marital"] * df["marital"]
            + BETA["urban"] * df["urban"]
            + BETA["fatheredu"] * df["father_edu"]
            + prov_effect
            + rng.normal(0, EPSILON_INCOME_SD, size=n)
        )
        df["income"] = np.round(np.exp(ln_income)).astype(int)  # 元/年
        df["ln_income"] = ln_income

        rows.append(df)

    panel = pd.concat(rows, ignore_index=True)

    # 引入一些缺失值，模拟真实调查 (5% 的收入缺失、3% 的健康缺失、2% 的 education)
    miss_income = rng.random(len(panel)) < 0.05
    panel.loc[miss_income, "income"] = np.nan
    panel.loc[miss_income, "ln_income"] = np.nan

    miss_health = rng.random(len(panel)) < 0.03
    panel.loc[miss_health, "health"] = np.nan

    miss_edu = rng.random(len(panel)) < 0.02
    panel.loc[miss_edu, "education"] = np.nan

    # 排序：pid, year（CFPS 风格）
    panel = panel.sort_values(["pid", "year"]).reset_index(drop=True)
    return panel


# ---------- 3. 期层面变量（含 DGP）----------


# ---------- 4. 写出 ----------
def write_outputs(panel: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    # 主数据集
    csv_path = out_dir / "cfps_internet_income_panel.csv"
    panel.to_csv(csv_path, index=False, encoding="utf-8")

    # codebook
    codebook = """# 变量说明（Codebook）

数据集：`cfps_internet_income_panel.csv`
样本量：N = 2000 个个体 × 2 期（2018、2020）= 4000 条观测（平衡面板）
设计：模拟 CFPS（China Family Panel Studies）个体层数据

| 变量 | 中文 | 类型 | 取值 / 单位 | 说明 |
|---|---|---|---|---|
| `pid` | 个体 ID | int | 1–2000 | 在两期稳定，可跨年追踪 |
| `fid` | 家庭 ID | int | 1–N | 反映家庭结构（1–3 人/家） |
| `year` | 年份 | int | 2018 / 2020 | 调查年份 |
| `gender_male` | 性别（男=1） | int | 0/1 | 1=男性, 0=女性 |
| `birth_year` | 出生年份 | int | 1963–1993 | 抽样框：劳动力人口 |
| `age` | 年龄 | int | 18–57 | 当年 = year − birth_year |
| `urban` | 城乡 | int | 0/1 | 1=城镇, 0=农村 |
| `education` | 教育年限 | float | 0–22 | 缺失率 2% |
| `marital` | 已婚 | int | 0/1 | 随年龄 logistic 概率 |
| `health` | 自评健康 | int | 1–5 | 缺失率 3%；5=最好 |
| `father_edu` | 父亲教育年限 | float | 6–16 | 时不变背景变量 |
| `provcode` | 省份代码 | int | 1–28 | 省级固定效应 |
| `family_internet` | 当年家庭接入宽带 | int | 0/1 | 家庭层面时变量 |
| `family_internet_2018` | (仅 2018 期) 2018 家庭接入 | int | 0/1 | **工具变量（IV）** |
| `internet_use` | 个体是否使用互联网 | int | 0/1 | 因变量（treatment） |
| `income` | 个人年收入 | int | 元 | 缺失率 5% |
| `ln_income` | ln(收入) | float | — | 主要被解释变量 |

注：`family_internet_2018` 仅在 `year == 2018` 的行出现；其他年份为 NaN。
请在做 IV 时先 `panel[panel.year == 2018]` 取 2018 期，或自行将 IV 合并为面板形态。

---

## DGP 真值（用于校准估计量）

### 结构方程（ln_income DGP）

```
ln_income = 8.5
         + 0.18 * internet_use            ← 主效应
         + 0.07 * education
         + 0.04 * age
         - 0.04 * age^2 / 100
         - 0.15 * female
         + 0.08 * health
         + 0.05 * marital
         + 0.22 * urban
         + 0.02 * father_edu
         + α_prov                            (α ~ N(0, 0.15^2))
         + ε_income                          (ε ~ N(0, 0.45^2))
```

### 选择方程（internet_use DGP）

```
z = -2.5
    + 0.30 * education
    - 0.025 * age
    + 0.50 * urban
    + 0.04 * father_edu
    - 0.10 * female
    + 0.10 * health
    + 1.20 * family_internet_2018          ← IV 系数（强工具）
    + ε_sel                              (ε ~ N(0, 1.0^2))

P(internet_use = 1) = σ(z),   σ 是 logistic 函数
```

### 故意制造的偏差（提醒：OLS 会高估）

OLS 直接回归 `ln_income ~ internet_use` 会**正向上偏**：
- 互联网使用者本来就 education 高、urban 多、health 好 → 这些都正向影响收入
- 因此 naive OLS 系数 ≈ 0.30–0.40，真值 0.18
- 这正是 selection-on-observables / OVB 的经典案例

### 修复路径（用户可自行验证）

| 方法 | 期望系数 |
|---|---|
| OLS（naive） | 约 0.30–0.40（高估） |
| FE / 控制完整 X | 约 0.20–0.22（接近真值） |
| 2SLS：IV = `family_internet_2018` | 约 0.18（恢复真值） |
| PSM（nearest neighbour on X） | 约 0.20 |
| 双重稳健 AIPW | 约 0.18–0.20 |

注：因为是平衡面板 + 时不变 X + 仅有 2 期，FE 退化为组间均值差；建议优先 IV。
"""
    (out_dir / "codebook.md").write_text(codebook, encoding="utf-8")

    # README
    readme = """# CFPS 风格数据集 · 个体互联网使用对收入的影响

> ⚠️ 这是**虚构**数据集，DGP 真值已知，**仅用于方法演示与教学**，不可作为真实研究发现。
> 真实研究请使用 [CFPS](https://www.isss.pku.edu.cn/cfps/) 官方公开数据。

## 文件清单

| 文件 | 用途 |
|---|---|
| `cfps_internet_income_panel.csv` | 主数据集（N=2000×2=4000 行平衡面板） |
| `codebook.md` | 变量说明 + DGP 真值 |
| `generate_data.py` | 可复现脚本 |
| `README.md` | 本文件 |

## 快速开始

```python
import pandas as pd

panel = pd.read_csv("cfps_internet_income_panel.csv")
print(panel.shape)   # (4000, 18)
print(panel.head())

# 朴素 OLS（会高估）
import statsmodels.formula.api as smf
print(smf.ols("ln_income ~ internet_use", data=panel).fit().summary())

# IV: 2SLS
from linearmodels.iv import IV2SLS
iv = IV2SLS.from_formula(
    "ln_income ~ 1 + education + age + urban + [internet_use ~ family_internet_2018]",
    data=panel[panel.year == 2018],   # IV 仅在 2018 期有值
).fit(cov_type="clustered", clusters=panel.loc[panel.year == 2018, "fid"])
print(iv.summary)
```

## 研究问题

**个体互联网使用对个人收入的影响有多大？**

这是个经典的**选择偏差 + 双向因果**问题：
- 反向因果：高收入者更可能买得起设备、负担得起流量费
- 遗漏变量：受教育程度高、城市居民更可能上网（也更高收入）
- 工具变量：家庭层面的宽带接入 (`family_internet_2018`) 外生影响个人互联网使用，但不影响个人收入

## 可用的识别策略

- OLS（含/不含控制）
- 固定效应（FE）
- 倾向得分匹配（PSM）
- 双重稳健估计（AIPW）
- 2SLS / IV（用 `family_internet_2018` 做工具）
- DID（如果构造处理时变的"是否上网"事件）

## 引用方式

```bibtex
@misc{cfps_synthetic_2026,
  title  = {{CFPS-style Synthetic Panel: Internet Use and Income (N=2000)}},
  year   = {2026},
  note   = {{Synthetic dataset for methods demonstration. DGP truth: beta\_int = 0.18.}}
}
```
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"[OK] 数据集已写入: {csv_path}")
    print(f"[OK] Codebook 已写入: {out_dir / 'codebook.md'}")
    print(f"[OK] README 已写入: {out_dir / 'README.md'}")


# ---------- 5. 主流程 ----------
def main() -> None:
    rng = np.random.default_rng(SEED)
    df_ind = draw_individual_characteristics(N, rng)
    family_int_2018 = draw_family_iv(df_ind, rng)
    panel = draw_panel(df_ind, family_int_2018, rng)
    out_dir = Path(__file__).resolve().parent
    write_outputs(panel, out_dir)

    # 摘要
    print("\n=== 数据集摘要 ===")
    print(f"个体数: {panel['pid'].nunique()}")
    print(f"年份:  {sorted(panel['year'].unique())}")
    print(f"总观测: {len(panel)}")
    print(f"平衡面板: {(panel.groupby('pid').size() == 2).all()}")
    print(f"互联网使用比例: {panel['internet_use'].mean():.3f}")
    print(f"收入均值 (有值): {panel['income'].mean():.0f} 元/年")
    print(f"收入缺失率: {panel['income'].isna().mean():.3f}")
    print(f"family_internet_2018 (IV) 非空率: {panel['family_internet_2018'].notna().mean():.3f}")


if __name__ == "__main__":
    main()