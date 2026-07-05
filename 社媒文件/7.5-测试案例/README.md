# CFPS 风格数据集 · 个体互联网使用对收入的影响

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
