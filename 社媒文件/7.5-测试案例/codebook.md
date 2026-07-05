# 变量说明（Codebook）

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
