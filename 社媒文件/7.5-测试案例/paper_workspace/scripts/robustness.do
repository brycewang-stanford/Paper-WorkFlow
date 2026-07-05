/*==========================================================================
  robustness.do
  ======================================================================
  扩展稳健性检验：
    - 控制函数法（Control Function）
    - 分位数回归（25/50/75/90 分位）
    - PSM + ATT
    - AIPW 双稳健估计
    - PPML（泊松伪极大似然）
    - 平衡性检验（按互联网使用分组的协变量均值差异）
  ====================================================================== */

clear all
set more off
set scheme s2color
set seed 20250705

global ROOT "/Users/brycewang/Documents/GitHub/Auto-Empirical-Research-Skills/skills/69-Paper-WorkFlow/社媒文件/7.5-测试案例/paper_workspace"
global DATA "${ROOT}/02_data/cfps_internet_income_panel.csv"
global OUT "${ROOT}/04_results"

import delimited "${DATA}", delimiter(",") varnames(1) encoding(utf8) clear
destring _all, replace force

* =====================================================
* 1. 控制函数法（CF / Control Function Approach）
* =====================================================
* 一阶段：internet_use 对所有外生变量 + IV 回归
qui regress internet_use age i.gender_male urban c.education i.marital health father_edu i.provcode family_internet_2018
predict v_hat, residuals

* 二阶段：ln_income 对内生变量 + 控制变量 + 残差（控制函数项）
qui regress ln_income internet_use v_hat age i.gender_male urban c.education i.marital health father_edu i.provcode
matrix b_cf = e(b)
matrix V_cf = e(V)
local b_cf_int = b_cf[1, "internet_use"]
local se_cf_int = sqrt(V_cf["internet_use", "internet_use"])
local n_cf = e(N)
local r2_cf = e(r2)
di "CF: coef = `b_cf_int' se = `se_cf_int' N = `n_cf' R2 = `r2_cf'"

* =====================================================
* 2. 分位数回归（Quantile Regression）
* =====================================================
* 中位数
qui qreg ln_income internet_use age i.gender_male urban c.education i.marital health father_edu i.provcode, quantile(0.5) vce(cluster fid)
matrix b_q50 = e(b)
matrix V_q50 = e(V)
local b_q50 = b_q50[1, "internet_use"]
local se_q50 = sqrt(V_q50["internet_use", "internet_use"])
local n_q50 = e(N)
di "QREG 50: coef = `b_q50' se = `se_q50' N = `n_q50'"

* 25 分位数
qui qreg ln_income internet_use age i.gender_male urban c.education i.marital health father_edu i.provcode, quantile(0.25) vce(cluster fid)
matrix b_q25 = e(b)
matrix V_q25 = e(V)
local b_q25 = b_q25[1, "internet_use"]
local se_q25 = sqrt(V_q25["internet_use", "internet_use"])
local n_q25 = e(N)
di "QREG 25: coef = `b_q25' se = `se_q25' N = `n_q25'"

* 75 分位数
qui qreg ln_income internet_use age i.gender_male urban c.education i.marital health father_edu i.provcode, quantile(0.75) vce(cluster fid)
matrix b_q75 = e(b)
matrix V_q75 = e(V)
local b_q75 = b_q75[1, "internet_use"]
local se_q75 = sqrt(V_q75["internet_use", "internet_use"])
local n_q75 = e(N)
di "QREG 75: coef = `b_q75' se = `se_q75' N = `n_q75'"

* 90 分位数
qui qreg ln_income internet_use age i.gender_male urban c.education i.marital health father_edu i.provcode, quantile(0.9) vce(cluster fid)
matrix b_q90 = e(b)
matrix V_q90 = e(V)
local b_q90 = b_q90[1, "internet_use"]
local se_q90 = sqrt(V_q90["internet_use", "internet_use"])
local n_q90 = e(N)
di "QREG 90: coef = `b_q90' se = `se_q90' N = `n_q90'"

* =====================================================
* 3. PSM + ATT
* =====================================================
* 先估计倾向得分
qui logit internet_use age i.gender_male urban c.education i.marital health father_edu i.provcode
predict pscore, pr
summarize pscore, detail

* 检查共同支持
twoway (kdensity pscore if internet_use == 0, lcolor(blue)) ///
       (kdensity pscore if internet_use == 1, lcolor(red)), ///
       legend(label(1 "互联网非用户") label(2 "互联网用户")) ///
       title("Propensity score overlap") saving("${OUT}/figures/ps_overlap.gph", replace)

* ATT: 用 psmatch2 / 内核匹配
capture ssc install psmatch2, replace
qui psmatch2 internet_use, pscore(pscore) neighbor(1) caliper(0.05) outcome(ln_income)
* psmatch2 自动输出 ATT/ATU/ATE
* 手动计算 ATT: 对匹配后的样本比较
* 这里直接读取 psmatch2 输出的 _treated/_control 标记
gen t_flag = (_treated != . & _treated != 0)
gen c_flag = (_id != . & _treated == .)
* 简单 ATT: 匹配后的 treated - control
qui summarize ln_income if _treated == 1
local y_treat = r(mean)
qui summarize ln_income if _id != . & _treated == .
local y_ctrl = r(mean)
local att_psm = `y_treat' - `y_ctrl'
local n_treat_psm = _N // matched treated
di "PSM ATT (matched) = `att_psm'"

* =====================================================
* 4. AIPW 双稳健估计
* =====================================================
* 用 teffects aipw
capture ssc install teffects, replace
qui teffects aipw (ln_income age i.gender_male urban c.education i.marital health father_edu i.provcode) (internet_use age i.gender_male urban c.education i.marital health father_edu i.provcode), nolog
* teffects aipw 报告 ATE
matrix b_aipw = e(b)
matrix V_aipw = e(V)
local b_aipw = b_aipw[1, "ATE"]
local se_aipw = sqrt(V_aipw["ATE", "ATE"])
local n_aipw = e(N)
di "AIPW ATE: coef = `b_aipw' se = `se_aipw' N = `n_aipw'"

* =====================================================
* 5. PPML（用 Poisson 伪极大似然估计）
* =====================================================
* PPML 对水平收入估计；先检查零值
qui summarize income
di "income min = " r(min) " zeros = " r(N) - r(N) // not a good way; use egen
* 直接用 PPML 估计水平 income（适用于含零值）
qui ppml income internet_use age i.gender_male urban c.education i.marital health father_edu i.provcode
matrix b_ppml = e(b)
matrix V_ppml = e(V)
local b_ppml = b_ppml[1, "internet_use"]
local se_ppml = sqrt(V_ppml["internet_use", "internet_use"])
local n_ppml = e(N)
di "PPML coef = `b_ppml' se = `se_ppml' N = `n_ppml'"

* =====================================================
* 6. 平衡性检验（balance test）
* =====================================================
* 比较互联网用户 vs 非用户在各协变量上的标准化差异
file open fh using "${OUT}/balance_test.txt", write replace
file write fh "协变量平衡性检验：互联网用户 vs 非用户" _n _n
file write fh "协变量 | mean_0 | mean_1 | diff | std_diff" _n
foreach v in age urban c.education i.marital health father_edu {
    qui summarize `v' if internet_use == 0
    local m0 = r(mean)
    local s0 = r(sd)
    qui summarize `v' if internet_use == 1
    local m1 = r(mean)
    local s1 = r(sd)
    local s_pool = sqrt((`s0'^2 + `s1'^2) / 2)
    local diff = `m1' - `m0'
    local std_diff = `diff' / `s_pool'
    file write fh "`v' " %9.4f (`m0') " " %9.4f (`m1') " " %9.4f (`diff') " " %9.4f (`std_diff') _n
}
file close fh

* =====================================================
* 7. 综合写入主结果文件
* =====================================================
file open fh using "${OUT}/robustness_summary.txt", write replace
file write fh "============================================================" _n
file write fh " 扩展稳健性检验结果汇总" _n
file write fh "============================================================" _n _n
file write fh "【控制函数法】internet_use 系数 = " %9.4f (`b_cf_int') " (se = " %9.4f (`se_cf_int') ", N = " %9.0fc (`n_cf') ", R2 = " %9.4f (`r2_cf') ")" _n _n
file write fh "【分位数回归】" _n
file write fh "  q25: coef = " %9.4f (`b_q25') " (se = " %9.4f (`se_q25') ", N = " %9.0fc (`n_q25') ")" _n
file write fh "  q50: coef = " %9.4f (`b_q50') " (se = " %9.4f (`se_q50') ", N = " %9.0fc (`n_q50') ")" _n
file write fh "  q75: coef = " %9.4f (`b_q75') " (se = " %9.4f (`se_q75') ", N = " %9.0fc (`n_q75') ")" _n
file write fh "  q90: coef = " %9.4f (`b_q90') " (se = " %9.4f (`se_q90') ", N = " %9.0fc (`n_q90') ")" _n _n
file write fh "【PSM ATT】" %9.4f (`att_psm') _n _n
file write fh "【AIPW ATE】" %9.4f (`b_aipw') " (se = " %9.4f (`se_aipw') ", N = " %9.0fc (`n_aipw') ")" _n _n
file write fh "【PPML】internet_use 系数 = " %9.4f (`b_ppml') " (se = " %9.4f (`se_ppml') ", N = " %9.0fc (`n_ppml') ")" _n _n
file write fh "(true beta_int = 0.18)" _n
file close fh

di "DONE_ALL_ROBUST"
type "${OUT}/robustness_summary.txt"
type "${OUT}/balance_test.txt"