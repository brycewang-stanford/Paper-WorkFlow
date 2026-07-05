/*==========================================================================
  analysis.do
  ======================================================================
  论文：互联网使用对个人收入的影响 — 基于 CFPS 风格合成面板数据
  后端：Stata 17+
  数据：cfps_internet_income_panel.csv (N=2000, T=2)
  ====================================================================== */

clear all
set more off
set scheme s2color
set seed 20250705

* --- 路径 ---
global ROOT "/Users/brycewang/Documents/GitHub/Auto-Empirical-Research-Skills/skills/69-Paper-WorkFlow/社媒文件/7.5-测试案例/paper_workspace"
global DATA "${ROOT}/02_data/cfps_internet_income_panel.csv"
global OUT_TAB "${ROOT}/04_results/tables"
global OUT_FIG "${ROOT}/04_results/figures"
global LOG "${ROOT}/logs/analysis.log"

capture mkdir "${ROOT}/04_results/tables"
capture mkdir "${ROOT}/04_results/figures"
capture mkdir "${ROOT}/logs"

* --- 打开日志 ---
log using "${LOG}", replace

* =================================================================
* 0. 加载并检查数据
* =================================================================
import delimited "${DATA}", delimiter(",") varnames(1) encoding(utf8) clear

* 强制数值化
destring pid fid gender_male birth_year father_edu provcode year age urban ///
       education marital health family_internet internet_use income ln_income ///
       family_internet_2018, replace force

describe
summarize

* =================================================================
* 1. 样本审计
* =================================================================
* 平衡面板
bysort pid: gen _nper = _N
tab _nper
drop _nper

* 缺失率
mdesc

* 互联网使用率（按年）
tab year, sum(internet_use)

* 收入分布（按 internet_use 分组对比）
bysort internet_use: summarize income ln_income, detail

* =================================================================
* 2. 描述性统计表（Table 1）
* =================================================================
* 安装 estout（如果还没有）
capture ssc install estout, replace
capture ssc install reghdfe, replace
capture ssc install ivreg2, replace
capture ssc install ranktest, replace

* 全部样本的描述统计
estpost summarize ///
    age gender_male urban education marital health father_edu ///
    internet_use family_internet income ln_income, ///
    detail listwise

esttab using "${OUT_TAB}/table1_summary.rtf", ///
    replace cells("count mean sd min p25 p50 p75 max") ///
    title("Descriptive statistics (N = `e(N)')") ///
    label noobs

esttab using "${OUT_TAB}/table1_summary.tex", ///
    replace cells("count mean sd min p25 p50 p75 max") ///
    title("Descriptive statistics (N = `e(N)')") ///
    label noobs

* 按互联网使用分组的均值差异
estpost ttest age gender_male urban education marital health father_edu ///
    income ln_income, by(internet_use) unequal

esttab using "${OUT_TAB}/table1_bygroup.tex", ///
    replace cells("mu_1 mu_2 b se p") ///
    title("Group means by internet use") ///
    label noobs

* =================================================================
* 3. 主回归（基准组）
* =================================================================
* (1) OLS 朴素：不加任何控制
* 因变量：ln_income（处理缺失值）
regress ln_income internet_use if ln_income != .
estimates store m1_naive

* (2) OLS + 个体特征
regress ln_income internet_use age i.gender_male urban c.education ///
    i.marital health father_edu if ln_income != .
estimates store m2_ols_x

* (3) OLS + 个体特征 + 省份固定效应
regress ln_income internet_use age i.gender_male urban c.education ///
    i.marital health father_edu i.provcode if ln_income != .
estimates store m3_ols_fe

* (4) reghdfe 高维固定效应（双向 FE：个体 + 年份）
reghdfe ln_income internet_use age i.gender_male urban c.education ///
    i.marital health father_edu, ///
    absorb(pid year) vce(cluster fid)
estimates store m4_hdfe

* (5) 2SLS：family_internet_2018 作为工具变量
* 由于家庭互联网接入是 2018 基线，在两期都成立，但个人收入不直接影响家庭接入
* 注：把 family_internet_2018 跨期对齐到面板
bysort pid: egen fam_int_2018_panel = max(family_internet_2018)
replace family_internet_2018 = fam_int_2018_panel
drop fam_int_2018_panel

ivreg2 ln_income age i.gender_male urban c.education i.marital health ///
    father_edu i.provcode (internet_use = family_internet_2018), ///
    cluster(fid) first ffirst
estimates store m5_iv

* =================================================================
* 4. 异质性分析
* =================================================================
* (6) 按城乡分样本
ivreg2 ln_income age i.gender_male c.education i.marital health father_edu ///
    i.provcode (internet_use = family_internet_2018) if urban == 1, ///
    cluster(fid) first
estimates store m6_iv_urban

ivreg2 ln_income age i.gender_male c.education i.marital health father_edu ///
    i.provcode (internet_use = family_internet_2018) if urban == 0, ///
    cluster(fid) first
estimates store m6_iv_rural

* (7) 按性别分样本
ivreg2 ln_income age urban c.education i.marital health father_edu ///
    i.provcode (internet_use = family_internet_2018) if gender_male == 1, ///
    cluster(fid) first
estimates store m7_iv_male

ivreg2 ln_income age urban c.education i.marital health father_edu ///
    i.provcode (internet_use = family_internet_2018) if gender_male == 0, ///
    cluster(fid) first
estimates store m7_iv_female

* (8) 按教育分样本（高中以下 vs 高中及以上）
gen edu_high = (education >= 12) if education != .
ivreg2 ln_income age i.gender_male urban i.marital health father_edu ///
    i.provcode (internet_use = family_internet_2018) if edu_high == 1, ///
    cluster(fid) first
estimates store m8_iv_eduhigh

ivreg2 ln_income age i.gender_male urban i.marital health father_edu ///
    i.provcode (internet_use = family_internet_2018) if edu_high == 0, ///
    cluster(fid) first
estimates store m8_iv_edulow

* =================================================================
* 5. 稳健性检验
* =================================================================
* (9) 控制个体固定效应（panel FE）
xtset pid year
xtreg ln_income internet_use age i.marital health, ///
    fe vce(cluster fid)
estimates store m9_fe

* (10) 一阶段 F 单独报告
ivreg2 ln_income age i.gender_male urban c.education i.marital health ///
    father_edu i.provcode (internet_use = family_internet_2018) if year == 2018, ///
    cluster(fid) first
estimates store m10_iv_2018

* (11) 仅用 2018 期 OLS（横截面）
regress ln_income internet_use age i.gender_male urban c.education ///
    i.marital health father_edu i.provcode if year == 2018 & ln_income != .
estimates store m11_ols_2018

* =================================================================
* 6. 输出回归表
* =================================================================
* 主回归表（5 个模型）
esttab m1_naive m2_ols_x m3_ols_fe m4_hdfe m5_iv ///
    using "${OUT_TAB}/table2_main_regs.tex", ///
    replace ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    keep(internet_use age 1.gender_male urban c.education i.marital health father_edu) ///
    order(internet_use age 1.gender_male urban c.education i.marital health father_edu) ///
    stats(N r2 within_r2, fmt(%9.0fc %9.3fc %9.3fc) ///
    labels("N" "R-squared" "Within R-sq.")) ///
    b(%9.3fc) se(%9.3fc) ///
    title("Main regressions: ln(income) on internet use") ///
    mtitles("(1) OLS" "(2) OLS+X" "(3) OLS+X+FE" "(4) HD-FE" "(5) IV-2SLS") ///
    label ///
    compress ///
    note("Standard errors clustered at household level in parentheses. * p<0.10, ** p<0.05, *** p<0.01.")

esttab m1_naive m2_ols_x m3_ols_fe m4_hdfe m5_iv ///
    using "${OUT_TAB}/table2_main_regs.rtf", ///
    replace ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    keep(internet_use) ///
    stats(N r2 within_r2, fmt(%9.0fc %9.3fc %9.3fc) ///
    labels("N" "R-squared" "Within R-sq.")) ///
    b(%9.3fc) se(%9.3fc) ///
    title("Main regressions: internet use coefficient") ///
    mtitles("(1) OLS" "(2) OLS+X" "(3) OLS+X+FE" "(4) HD-FE" "(5) IV-2SLS") ///
    compress

* 异质性表
esttab m6_iv_urban m6_iv_rural m7_iv_male m7_iv_female m8_iv_eduhigh m8_iv_edulow ///
    using "${OUT_TAB}/table3_heterogeneity.tex", ///
    replace ///
    star(* 0.10 ** 0.05 *** 0.01) ///
    keep(internet_use) ///
    stats(N r2, fmt(%9.0fc %9.3fc) labels("N" "R-squared")) ///
    b(%9.3fc) se(%9.3fc) ///
    title("Heterogeneous effects (IV-2SLS)") ///
    mtitles("Urban" "Rural" "Male" "Female" "High Edu" "Low Edu") ///
    label ///
    note("All specifications include age, education, marital status, health, father education, and province fixed effects. Standard errors clustered at household level.")

* =================================================================
* 7. 输出描述统计到 LaTeX
* =================================================================
* 用 file write 直接输出
file open fh using "${OUT_TAB}/table1_summary_v2.tex", write replace
file write fh "\begin{table}[!htbp]" _n
file write fh "\centering" _n
file write fh "\caption{描述性统计}" _n
file write fh "\label{tab:summary}" _n
file write fh "\begin{tabular}{lcccccc}" _n
file write fh "\hline\hline" _n
file write fh "变量 & 样本量 & 均值 & 标准差 & 最小值 & 中位数 & 最大值 \\" _n
file write fh "\hline" _n

foreach v in age gender_male urban education marital health father_edu internet_use family_internet income ln_income {
    quietly summarize `v'
    file write fh "`v' & " %9.0fc (r(N)) " & " %9.3fc (r(mean)) " & " %9.3fc (r(sd)) " & " %9.3fc (r(min)) " & " %9.3fc (r(p50)) " & " %9.3fc (r(max)) " \\" _n
}

file write fh "\hline\hline" _n
file write fh "\end{tabular}" _n
file write fh "\end{table}" _n
file close fh

* =================================================================
* 8. 导出 IV 一阶段与排他性检验（稳健性讨论）
* =================================================================
* 显示一阶段 F 与 IV 系数
di "=========================================="
di "工具变量强度"
di "=========================================="
di "OLS 估计 (true = 0.18):"
regress ln_income internet_use if ln_income != .
di "IV-2SLS 估计 (true = 0.18):"
ivreg2 ln_income age i.gender_male urban c.education i.marital health father_edu ///
    i.provcode (internet_use = family_internet_2018), ///
    cluster(fid) first

* =================================================================
* 9. 保存清理后的数据供后续使用
* =================================================================
save "${ROOT}/02_data/clean.dta", replace

log close
di "=== 分析完成，回归表已保存到 ${OUT_TAB}/ ==="