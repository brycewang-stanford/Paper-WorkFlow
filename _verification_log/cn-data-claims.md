# China-Context Claims Verification Log

This file records load-bearing factual claims in the two China-context
references (`references/china-data-sources.md`, `references/chinese-journals.md`),
mirroring the format and status vocabulary of `methods-claims.md`. Mutable facts
(prices, review turnaround, application queues, URLs) default to `to-verify`
until re-checked against the primary source; stable institutional and legal
facts anchored in published documents are `canonical`; entries re-checked live
against the publisher in a maintenance pass are `verified`.

### C01 · CID canonical data-quality citation
- claim-tag: cid-brandt-vbz-2014-citation
- claim: The standard reference for cleaning and comparability issues in the Chinese industrial enterprise database (CID) is Brandt, Van Biesebroeck & Zhang (2014), "Challenges of working with the Chinese NBS firm-level data", China Economic Review 30, 339-352.
- used-in: references/china-data-sources.md
- source: China Economic Review vol. 30 (2014) pp. 339-352; publisher landing page (ScienceDirect S1043951X14000340) and RePEc record eee:chieco:v:30:y:2014:i:c:p:339-352 both confirm the author list Brandt / Van Biesebroeck / Zhang.
- status: verified
- checked: 2026-07-16 · live web re-check; fixed a garbled author list ("John Litwack") that previously appeared in china-data-sources.md §6.3

### C02 · CID above-scale sales threshold change
- claim-tag: cid-above-scale-threshold-2011
- claim: The CID "above-scale" inclusion threshold was 5 million RMB in annual sales for 1998-2010 and was raised to 20 million RMB from 2011, so time-series comparisons must adjust for the sampling-frame break.
- used-in: references/china-data-sources.md
- source: National Bureau of Statistics reporting-scope adjustment (规模以上工业企业统计起点调整, effective 2011); discussed in Brandt, Van Biesebroeck & Zhang (2014), China Economic Review.
- status: canonical
- checked: 2026-07-16 · consistent with the canonical CID literature; NBS circular not live re-verified in this pass

### C03 · CID usable coverage window
- claim-tag: cid-coverage-1998-2013
- claim: CID coverage is most complete for roughly 1998-2013, with well-documented deterioration in key financial fields after 2013, which is why the reference caps its recommended sample window there.
- used-in: references/china-data-sources.md
- source: 聂辉华、江艇、杨汝岱 (2012), 《中国工业企业数据库的使用现状和潜在问题》, 《世界经济》第5期; Brandt, Van Biesebroeck & Zhang (2014), China Economic Review.
- status: canonical
- checked: 2026-07-16 · standard CID-usage references; not live-web reverified in this pass

### C04 · CSMAR default industry classification
- claim-tag: csmar-csrc-2012-industry-codes
- claim: CSMAR company data defaults to the CSRC 2012 industry classification while some fields retain GB/T 4754 national-economy codes, so merges must confirm which scheme each field uses.
- used-in: references/china-data-sources.md
- source: 待补 — to verify against CSMAR's current field documentation (data.csmar.com) before relying on it in a merge script.
- status: to-verify
- checked: 2026-07-16 · flagged at ledger creation; matches common practice but the vendor doc was not pulled

### C05 · CFPS institutional design
- claim-tag: cfps-pku-2010-biennial
- claim: CFPS is run by Peking University (Institute of Social Science Survey), with a 2010 national baseline and biennial follow-ups (2012-2022), covering all-age household samples.
- used-in: references/china-data-sources.md
- source: CFPS official documentation, Institute of Social Science Survey, Peking University (isss.pku.edu.cn/cfps).
- status: canonical
- checked: 2026-07-16 · stable institutional facts from the survey's own documentation; not live re-verified in this pass

### C06 · CHARLS institutional design
- claim-tag: charls-2008-pilot-2011-baseline
- claim: CHARLS is run by Peking University's National School of Development, targets residents aged 45+, with a 2008 two-province pilot (Gansu/Zhejiang) and a 2011 national baseline followed by waves in 2013/2015/2018/2020/2023.
- used-in: references/china-data-sources.md
- source: CHARLS official documentation (charls.charlsdata.com); Zhao et al. (2014), "Cohort Profile: The China Health and Retirement Longitudinal Study", International Journal of Epidemiology 43(1).
- status: canonical
- checked: 2026-07-16 · corrected the reference file, which previously described 2008 as the baseline rather than the pilot

### C07 · CHFS institutional design
- claim-tag: chfs-swufe-2011-biennial
- claim: CHFS is run by Southwestern University of Finance and Economics with a 2011 baseline and biennial waves, and is the primary Chinese household survey for detailed asset/liability/income modules.
- used-in: references/china-data-sources.md
- source: CHFS official documentation, Survey and Research Center for China Household Finance, SWUFE (chfs.swufe.edu.cn).
- status: canonical
- checked: 2026-07-16 · stable institutional facts; not live re-verified in this pass

### C08 · CGSS institutional design
- claim-tag: cgss-ruc-repeated-cross-section
- claim: CGSS is run by Renmin University of China, is primarily a repeated cross-section (not a panel), and rotates topical modules across years.
- used-in: references/china-data-sources.md
- source: CGSS official documentation, National Survey Research Center, Renmin University (cgss.ruc.edu.cn).
- status: canonical
- checked: 2026-07-16 · stable institutional facts; not live re-verified in this pass

### C09 · Data-export legal framework
- claim-tag: china-data-export-legal-framework
- claim: Cross-border transfer of Chinese research data is governed by the Data Security Law (2021), the Personal Information Protection Law (2021), and subsequent CAC cross-border data-flow regulations, so restricted microdata must not leave approved environments in a public replication pack.
- used-in: references/china-data-sources.md; references/data-governance.md
- source: 《中华人民共和国数据安全法》(2021 施行); 《中华人民共和国个人信息保护法》(2021 施行); 国家网信办《促进和规范数据跨境流动规定》(2024).
- status: canonical
- checked: 2026-07-16 · statutory texts; specific 2024-2026 implementation details in §1.4 remain summarized, not quoted

### C10 · GB/T 7714-2015 two citation systems
- claim-tag: gbt7714-2015-two-systems
- claim: GB/T 7714-2015 defines two citation systems — numeric (顺序编码制, the domestic mainstream) and author-date (著者-出版年制) — and Chinese journals specify which one they require.
- used-in: references/chinese-journals.md
- source: GB/T 7714-2015《信息与文献 参考文献著录规则》, Standardization Administration of China.
- status: canonical
- checked: 2026-07-16 · standard text; formatting examples in §2 follow the standard but were not re-checked character-by-character

### C11 · Top-5 Chinese journal process facts
- claim-tag: cn-top5-journal-process-facts
- claim: Per-journal mutable facts in chinese-journals.md §1 and §3 (review turnaround, fees, submission-portal details, formatting quirks for 经济研究/管理世界/经济学季刊/中国工业经济/数量经济技术经济研究) reflect recent practice but change year to year.
- used-in: references/chinese-journals.md
- source: 待补 — to verify against each journal's official submission notice for the target year before quoting any turnaround/fee number to a user; treat current text as planning heuristics only.
- status: to-verify
- checked: 2026-07-16 · flagged at ledger creation; the skill must not present these numbers as verified facts at submission time

### C12 · Customs data HS-version concordance
- claim-tag: customs-hs-version-concordance
- claim: China customs transaction data uses HS codes whose international revisions (HS1996/2002/2007/2012/2017/2022) require concordance tables for any cross-year product-level analysis.
- used-in: references/china-data-sources.md
- source: World Customs Organization HS revision cycle; UN Trade Statistics HS correspondence tables.
- status: canonical
- checked: 2026-07-16 · WCO revision cycle is stable public record; not live re-verified in this pass
