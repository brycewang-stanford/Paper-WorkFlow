# 数据源卡片库（Dataset Cards）—— 经管 / 社科实证常用数据的结构化目录

> 灵感来自 [Light-skills](https://github.com/Light0305/Light-skills) 的 db04「数据集卡片」，
> 但**为实证设计而改造**：每张卡片除了「在哪、多大、什么许可」，还写清**链接键**（怎么 merge）、
> **已知陷阱**和**这个数据源会给 design-risk-ledger 带来哪些威胁**——选源不是中性动作，**选源即选偏误**。

**何时加载**：Stage 2（数据）选源与取数时；Stage 3 方法闸门做样本/测量审计时；写 DAS 与复现包时。
它**不替代** [`data-governance.md`](data-governance.md)（受限数据/PII/IRB/DUA 合规）与
[`measurement-and-data-quality.md`](measurement-and-data-quality.md)（测量误差、单位、键规范化），
而是**前置**于它们：先用本目录挑对源、识别它自带的坑，再用那两份做治理与测量审计，最后落到
[`empirical-audit.md`](empirical-audit.md) 的 raw→clean→estimation sample 对齐。

> **本目录不是数据获取工具**：真正取数仍走 Stage 2 的 `data-fetcher` / WRDS / 官方接口。卡片只回答
> 「该用哪个源、它能不能支撑这个 estimand、它会带进来什么偏误」。

---

## 卡片 schema

每张卡片字段固定，便于在 proposal 与 sample_audit 里对照填写：

| 字段 | 含义 |
|---|---|
| **单位 / 领域** | 观测单位（firm-year / 个人 / 国家-年 …）与领域 |
| **覆盖** | 地理、时间跨度、频率、规模量级 |
| **典型设计** | 这个源常支撑哪些识别设计 / 研究问题 |
| **获取 / 许可** | 公开 / 订阅（WRDS 等）/ 受限；再分发与商用边界 |
| **链接键** | 与其它源 merge 的主键（gvkey/permno/cusip/ISO3/统一社会信用代码 …） |
| **已知陷阱** | survivorship、look-ahead、backfill、修订、覆盖偏、单位口径等 |
| **触发的设计风险** | 映射到 [`design-risk-ledger.md`](design-risk-ledger.md) 的威胁项（选择/测量/外部效度/attrition/SUTVA …） |
| **引用** | 数据源应当如何被引用（DAS 与正文都要） |

> **URL 纪律**：卡片只给我有把握的官方入口；订阅库（Compustat/CRSP/CSMAR/WIND）多经 WRDS 或厂商
> 平台获取，许可随机构合同，**以你机构的实际授权为准**，不要把卡片当授权依据。拿不准的链接/条款标「待核查」。

---

## 1 · 公司财务 / 资产定价

### Compustat（North America / Global）
- **单位 / 领域**：firm-year / firm-quarter；公司基本面与财务报表。
- **覆盖**：北美约 1950s 起、全球库另算；上市（及部分非上市）公司；年/季频。
- **典型设计**：公司金融、会计、政策冲击对企业行为的 DiD/面板 FE。
- **获取 / 许可**：订阅，多经 WRDS；再分发受限，复现包通常只能给 `gvkey` + 代码、不能给原始面板。
- **链接键**：`gvkey`（公司）、`cusip`/`cik`/`tic`；与 CRSP 经 CRSP/Compustat Merged（CCM）的 `lpermno` 链接。
- **已知陷阱**：**backfill / 幸存者偏误**（历史只含最终存活样本时）；财务重述与数据修订；会计口径跨期/跨国不一致；fiscal year ≠ calendar year。
- **触发的设计风险**：选择（survivorship）、测量误差（口径/重述）、外部效度（仅上市公司）。→ design-risk-ledger 的 selection / measurement / external-validity 行。
- **引用**：Compustat, S&P Global Market Intelligence（注明库与提取日期/vintage）。

### CRSP（Center for Research in Security Prices）
- **单位 / 领域**：security-day/month；股票价格、收益、市值、退市。
- **覆盖**：美股 NYSE/AMEX/NASDAQ，1925/1962 起；日/月频。
- **典型设计**：资产定价、事件研究（abnormal returns）、市场反应。
- **获取 / 许可**：订阅（WRDS）；再分发受限。
- **链接键**：`permno`/`permco`；经 CCM 的 `gvkey` 与 Compustat 合并；`cusip`（注意历史 cusip 变更）。
- **已知陷阱**：**退市收益（delisting returns）处理**不当会高估存活组收益；幸存者偏误；cusip 随时间变更导致 merge 漏配。
- **触发的设计风险**：选择（delisting/survivorship）、测量误差（delisting return）、look-ahead（用未来调整后的代码回溯 merge）。
- **引用**：CRSP, University of Chicago Booth（注明产品与日期）。

### Fama–French 因子库（Kenneth French Data Library）
- **单位 / 领域**：因子-期；市场/规模/价值/盈利/投资/动量等因子收益与组合收益。
- **覆盖**：美股最充分，另有国际/行业组合；日/周/月频。
- **典型设计**：因子模型、风险调整、组合收益解释、资产定价检验。
- **获取 / 许可**：**免费公开**；再分发/商用核对网站条款。
- **链接键**：按日期对齐；与个股收益对齐无风险利率与频率。
- **已知陷阱**：因子构造会更新（同一日期不同 vintage 可能不同）；底层依赖 CRSP/Compustat 的清洗细节；百分比单位易错；避免 look-ahead。
- **触发的设计风险**：测量误差（因子重构 vintage）、外部效度（美股为主）。
- **引用**：Kenneth R. French Data Library（注明下载日期）；方法见 Fama & French。

### IBES（分析师预测）
- **单位 / 领域**：firm-analyst-period；分析师盈利预测与推荐。
- **覆盖**：全球，覆盖度随时间与地区上升。
- **典型设计**：信息环境、预期管理、盈余意外（SUE）。
- **获取 / 许可**：订阅（WRDS）。
- **链接键**：`ticker`(IBES) / `cusip`；与 CRSP/Compustat merge 需对齐 cusip 历史。
- **已知陷阱**：**前瞻/激活日期**（announcement vs activation date）；analyst stop/coverage 选择；汇总文件 vs detail 文件口径差异；**stock split 调整**导致每股口径不一致。
- **触发的设计风险**：选择（coverage）、测量误差（split/口径）、look-ahead（用修订后预测）。
- **引用**：IBES, Refinitiv（注明 summary/detail 与日期）。

### CSMAR / WIND / RESSET / CNRDS（中国）
- **单位 / 领域**：firm-year/quarter、个股、债券、基金、宏观等；中国资本市场与公司财务主力库。
- **覆盖**：中国 A 股及衍生数据，1990s 起；上市公司为主。
- **典型设计**：中国制度冲击（政策/监管/试点）对企业行为的 DiD/面板；公司治理；绿色金融等。
- **获取 / 许可**：订阅；机构授权各异；再分发受限（复现包给代码 + 股票代码列表，不给原始面板）。
- **链接键**：股票代码（6 位）+ 交易所；公司层用统一社会信用代码 / 证券代码；与专利/工商库 merge 需做**公司名标准化**（曾用名、简称、母子公司）。
- **已知陷阱**：**同一变量多库口径不一**（需固定单一库或交叉核对）；ST/退市/借壳导致代码复用；**公司名 merge 误配**（中文名匹配）；指标定义随版本变化。
- **触发的设计风险**：测量误差（跨库口径）、选择（仅上市）、linkage error（名称匹配）、外部效度（A 股制度特定）。
- **引用**：CSMAR/WIND/RESSET/CNRDS（注明库、字段集与提取日期）。

---

## 2 · 宏观 / 金融时间序列

### FRED / FRED-MD / FRED-QD（St. Louis Fed）
- **单位 / 领域**：宏观指标时间序列；FRED-MD/QD 为打包的月/季度宏观面板。
- **覆盖**：以美国为主（FRED 含部分国际/区域序列）；FRED-MD 百余月度变量、FRED-QD 数百季度变量。
- **典型设计**：宏观预测、nowcasting、因子模型、VAR / 局部投影、机器学习预测比较。
- **获取 / 许可**：多数**公开**；API（含 ALFRED vintages）；再分发遵守来源机构条款。
- **链接键**：按日期；跨序列对齐频率与季节调整口径。
- **已知陷阱**：**数据修订**（实时预测必须用 ALFRED **vintages**，不能用最终值回测）；季节调整/transformation code 必须固定并记录；序列会停更/改基期。
- **触发的设计风险**：look-ahead（用修订后终值做实时预测）、测量误差（基期/季调）。
- **引用**：FRED, Federal Reserve Bank of St. Louis；FRED-MD/QD 见 McCracken & Ng。
- **入口**：https://fred.stlouisfed.org ；FRED-MD/QD 见 St. Louis Fed McCracken 数据页。

### World Bank WDI / IMF IFS / Penn World Table / OECD
- **单位 / 领域**：country-year（部分 country-quarter）；跨国宏观、发展、贸易、价格、PPP。
- **覆盖**：全球；WDI 1960 起、PWT 跨国可比 PPP 与实际产出。
- **典型设计**：跨国增长/制度回归、panel FE、跨国 DiD（政策采纳）。
- **获取 / 许可**：**公开**（注明版本）。
- **链接键**：`ISO3` 国家码 + year；注意国家边界/合并（如德国统一、苏联解体）与口径变更。
- **已知陷阱**：**缺失非随机**（弱国家少报）；同一指标跨源不一致；PWT 版本间实际值可大改；汇率/PPP 口径选择影响结论。
- **触发的设计风险**：测量误差（跨源/版本）、选择（缺失非随机）、外部效度。
- **引用**：World Bank WDI / IMF IFS / Penn World Table 10.x / OECD（务必注明**版本号**）。
- **入口**：https://databank.worldbank.org ；https://www.rug.nl/ggdc/productivity/pwt 。

---

## 3 · 微观调查 / 人口面板

### IPUMS（USA / International / CPS）
- **单位 / 领域**：个人 / 家户；普查与劳动力调查的协调化微观样本。
- **覆盖**：美国普查与 ACS、CPS，及多国普查（International）。
- **典型设计**：劳动经济、人口、移民、政策评估；重复横截面 DiD、合成队列。
- **获取 / 许可**：**公开**（需注册、遵守 IPUMS 引用与再分发条款）。
- **链接键**：`SERIAL`/`PERNUM`（户/人）；CPS 经 `CPSIDP` 做短面板链接（链接率有限）。
- **已知陷阱**：**抽样权重必须用**（含 replicate weights 做方差）；变量跨年协调但仍有 break；top-coding；CPS 月度链接的**匹配失败非随机**。
- **触发的设计风险**：测量误差（top-coding/协调）、选择（匹配失败/无回应）、加权不当致推断错位。
- **引用**：Steven Ruggles et al., IPUMS（注明产品与版本 DOI）。
- **入口**：https://ipums.org 。

### PSID / CFPS / CHFS / CHARLS / CHNS / LSMS / DHS（纵向 / 发展中国家）
- **单位 / 领域**：个人/家户纵向面板（PSID 美、CFPS/CHFS/CHARLS/CHNS 中、LSMS/DHS 多国）。
- **覆盖**：长期追踪（PSID 1968 起）；中国家户面板 2010s 起；发展库覆盖低收入国家。
- **典型设计**：收入/财富/健康/养老动态、代际流动、家庭决策；个体 FE、事件研究。
- **获取 / 许可**：多为**公开/申请**；部分敏感模块受限（见 data-governance）。
- **链接键**：家户 + 个人 ID（注意分户/合户、追访规则）；跨波链接需用官方 cross-wave ID。
- **已知陷阱**：**样本流失（attrition）非随机**——必须报告流失率与权重修正；追访规则决定谁留在样本；自报变量测量误差；中国库**村/社区抽样**影响聚类。
- **触发的设计风险**：**attrition**（核心）、选择、测量误差（自报）、聚类层级。→ design-risk-ledger 的 attrition 行必须逐波填。
- **引用**：各库官方引用格式（注明 wave 与 release）。

---

## 4 · 行政 / 登记 / 专利 / 贸易 / 文本

### USPTO PatentsView / PATSTAT / 专利（创新研究）
- **单位 / 领域**：专利 / 申请人 / 引用；创新产出与知识流动。
- **覆盖**：USPTO（美）、PATSTAT（全球 EPO）；可回溯数十年。
- **典型设计**：创新政策评估、知识溢出、企业创新（绿色专利等）。
- **获取 / 许可**：**公开**（PatentsView API/批量；PATSTAT 订阅）。注意 PatentsView 旧 API 已迁移，**入口以 USPTO 官方为准（待核查具体端点）**。
- **链接键**：`patent_id`、`assignee`；与公司库 merge 靠**申请人名消歧**（disambiguation）——误差大。
- **已知陷阱**：**申请人消歧错误**（同名/改名/母子公司）；**truncation**（近年专利引用/授权未完成，右截断）；分类体系（CPC/IPC）跨期变化；专利≠创新质量。
- **触发的设计风险**：linkage error（消歧）、测量误差（truncation/质量代理）、外部效度（可专利领域）。
- **引用**：PatentsView, USPTO / PATSTAT, EPO（注明版本与提取日期）。

### UN Comtrade / 海关 / 贸易
- **单位 / 领域**：国家(对)-产品-年/月；双边贸易流。
- **覆盖**：全球，HS/SITC 分类，1960s/1990s 起。
- **典型设计**：贸易冲击（Bartik/shift-share）、关税、全球价值链。
- **获取 / 许可**：**公开**（API 有速率/额度限制）。
- **链接键**：报告国×伙伴国×HS code×year；**镜像数据不一致**（出口报 vs 进口报）。
- **已知陷阱**：**reporter/partner 不对称**与漏报；HS 修订版（HS1992/96/02/07/12/17）需 concordance；转口贸易扭曲来源国。
- **触发的设计风险**：测量误差（镜像/分类）、选择（漏报国）、shift-share 的设计风险（见 design-gate-cards 的 Bartik 卡）。
- **引用**：UN Comtrade（注明 release）；HS concordance 注明来源。
- **入口**：https://comtradeplus.un.org 。

### SEC EDGAR（10-K/8-K 等文本）/ 另类数据（GDELT、夜间灯光、Google Trends）
- **单位 / 领域**：文件-公司 / 事件 / 栅格-时点；非结构化与另类数据。
- **覆盖**：EDGAR 1993/94 起；夜间灯光 DMSP(1992–2013)/VIIRS(2012–)；GDELT/Trends 近十余年。
- **典型设计**：文本度量（语气/可读性/相似度）、关注度、经济活动代理（灯光→GDP）。
- **获取 / 许可**：EDGAR **公开**（API）；灯光/GDELT **公开**；Google Trends 公开但为相对/抽样指数。
- **链接键**：EDGAR `cik`↔`gvkey`/`permno`（需 crosswalk）；栅格经行政边界做 zonal 统计。
- **已知陷阱**：EDGAR **boilerplate/模板效应**与口径变化；**DMSP 与 VIIRS 不可直接拼接**（传感器、饱和、跨标定）；Google Trends 是**抽样的相对指数**（同一查询不同日抓取值会变）；文本度量对预处理高度敏感。
- **触发的设计风险**：测量误差（构造/传感器/抽样）、look-ahead（用修订后文本/标定）、外部效度。
- **引用**：SEC EDGAR；DMSP/VIIRS（NOAA/Earth Observation Group）；GDELT Project；Google Trends（注明抓取日期）。
- **入口**：https://www.sec.gov/edgar 。

---

## 选源原则（落到两道闸门）

1. **选源即选样本**：每张卡片的「覆盖」决定 estimation sample 的外部效度边界；把它写进
   [`empirical-audit.md`](empirical-audit.md) 的 sample_audit 与 proposal 的 scope。
2. **选源即选偏误**：把卡片「触发的设计风险」逐项抄进 `03_analysis/design_risk_ledger.md`
   （见 [`design-risk-ledger.md`](design-risk-ledger.md)）——survivorship/look-ahead/attrition/linkage error
   不是数据细节，是识别威胁，blocking 时 Method Gate 不得 `PASS`。
3. **选源即定 vintage**：凡会修订的源（FRED、WDI、PWT、IBES、专利），DAS 与复现包必须记录
   **提取日期 / 版本号 / vintage**，否则复现不可达（见 [`computational-reproducibility.md`](computational-reproducibility.md)）。
4. **受限源走治理**：订阅/受限/含 PII 的源按 [`data-governance.md`](data-governance.md) 处理公开复现包边界——
   只发代码 + 键列表 + 取数脚本，不发原始受限面板。
5. **跨库口径要钉死**：同一变量多源不一致时，固定单一权威源或交叉核对，并把口径写进
   [`measurement-and-data-quality.md`](measurement-and-data-quality.md) 的测量审计。

> **卡片是活的**：新增一个常用源就加一张卡（保持字段固定）；某源条款/端点变化就更新该卡并在
> DAS 注明核查日期。卡片里任何拿不准的链接或许可，**标「待核查」而不是猜**——这与本 skill
> 对用户「不伪造来源」的要求是同一条纪律。
