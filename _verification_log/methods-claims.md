# Methods Claims Verification Log

This file records load-bearing empirical-method claims used by Paper-WorkFlow.
Entries marked `canonical` cite standard references from the field but were not
re-verified live in this maintenance pass. Entries marked `to-verify` are
allowed placeholders only when the source line explicitly says what remains to
be pinned down.

### M01 · Few-cluster inference
- claim-tag: few-cluster-wild-bootstrap
- claim: When the number of treated or assignment-level clusters is small, cluster-robust inference needs few-cluster corrections such as wild cluster bootstrap rather than default asymptotic t tests.
- used-in: references/inference-and-uncertainty.md; references/design-gate-cards.md; templates/inference_report.md
- source: Cameron, Gelbach & Miller (2008), Review of Economics and Statistics; Cameron & Miller (2015), Journal of Human Resources; MacKinnon & Webb (2017), Journal of Applied Econometrics.
- status: canonical
- checked: 2026-06-22 · standard econometrics references; not live-web reverified in this pass

### M02 · Cluster at assignment level
- claim-tag: cluster-at-assignment-level
- claim: Standard errors should be clustered at the level where treatment or policy shocks are assigned, unless a stronger dependence structure is justified.
- used-in: references/inference-and-uncertainty.md; references/design-gate-cards.md
- source: Bertrand, Duflo & Mullainathan (2004), Quarterly Journal of Economics; Abadie, Athey, Imbens & Wooldridge (2023), Quarterly Journal of Economics.
- status: canonical
- checked: 2026-06-22 · standard econometrics references; not live-web reverified in this pass

### M03 · Staggered DiD TWFE weights
- claim-tag: staggered-did-negative-weights
- claim: In staggered adoption designs with heterogeneous treatment effects, TWFE can place negative or otherwise non-convex weights on group-time effects; modern DiD estimators are required for the main claim.
- used-in: references/design-gate-cards.md; references/research-grade-methods.md; SKILL.md
- source: Goodman-Bacon (2021), Journal of Econometrics; Sun & Abraham (2021), Journal of Econometrics; Callaway & Sant'Anna (2021), Journal of Econometrics; Borusyak, Jaravel & Spiess (2024), Review of Economic Studies.
- status: canonical
- checked: 2026-06-22 · standard DiD references; not live-web reverified in this pass

### M04 · Pre-trend tests have low power
- claim-tag: pretrend-tests-low-power
- claim: Failure to reject pre-trends is not proof of parallel trends, because common pre-trend tests have limited power and can be distorted by conditioning on passing.
- used-in: references/design-gate-cards.md; references/threats-to-validity.md
- source: Roth (2022), American Economic Review: Insights; Rambachan & Roth (2023), Review of Economic Studies.
- status: canonical
- checked: 2026-06-22 · standard DiD sensitivity references; not live-web reverified in this pass

### M05 · Honest DiD sensitivity
- claim-tag: honest-did-sensitivity
- claim: Event-study designs should report sensitivity to violations of parallel trends when the identifying assumption is central to the headline claim.
- used-in: references/design-gate-cards.md; references/inference-and-uncertainty.md; templates/inference_report.md
- source: Rambachan & Roth (2023), Review of Economic Studies.
- status: canonical
- checked: 2026-06-22 · standard DiD sensitivity reference; not live-web reverified in this pass

### M06 · RDD robust bias-corrected inference
- claim-tag: rdd-robust-bias-corrected-ci
- claim: Regression discontinuity estimates should use bandwidth-aware robust bias-corrected confidence intervals rather than only conventional local-polynomial intervals.
- used-in: references/design-gate-cards.md; references/inference-and-uncertainty.md
- source: Calonico, Cattaneo & Titiunik (2014), Econometrica; Calonico, Cattaneo, Farrell & Titiunik (2019), Econometrics Journal.
- status: canonical
- checked: 2026-06-22 · standard RDD references; not live-web reverified in this pass

### M07 · RDD density manipulation
- claim-tag: rdd-density-manipulation-test
- claim: RDD requires checking continuity of the running-variable density at the cutoff because manipulation threatens the identifying comparison.
- used-in: references/design-gate-cards.md; references/inference-and-uncertainty.md
- source: McCrary (2008), Journal of Econometrics; Cattaneo, Jansson & Ma (2020), Journal of the American Statistical Association.
- status: canonical
- checked: 2026-06-22 · standard RDD references; not live-web reverified in this pass

### M08 · Weak-IV robust inference
- claim-tag: weak-iv-robust-inference
- claim: Instrumental-variable designs with weak first stages need weak-IV robust inference such as Anderson-Rubin or conditional likelihood-ratio intervals, not only conventional 2SLS t tests.
- used-in: references/design-gate-cards.md; references/inference-and-uncertainty.md
- source: Staiger & Stock (1997), Econometrica; Stock & Yogo (2005), Testing for Weak Instruments; Andrews, Moreira & Stock (2006), Econometrica.
- status: canonical
- checked: 2026-06-22 · standard IV references; not live-web reverified in this pass

### M09 · Effective first-stage strength
- claim-tag: effective-first-stage-strength
- claim: First-stage diagnostics must match the IV design, including multiple instruments, heteroskedasticity, clustering, or fixed effects; a single naive F statistic is not always sufficient.
- used-in: references/design-gate-cards.md; references/inference-and-uncertainty.md
- source: Stock & Yogo (2005), Testing for Weak Instruments; Olea & Pflueger (2013), Journal of Business & Economic Statistics.
- status: canonical
- checked: 2026-06-22 · standard IV references; not live-web reverified in this pass

### M10 · Multiple testing control
- claim-tag: multiple-testing-control
- claim: Families of outcomes, subgroups, or mechanisms require declared multiplicity control such as family-wise error or false-discovery-rate adjustment.
- used-in: references/inference-and-uncertainty.md; references/mechanism-and-channels.md; templates/inference_report.md
- source: Holm (1979), Scandinavian Journal of Statistics; Benjamini & Hochberg (1995), Journal of the Royal Statistical Society Series B; Romano & Wolf (2005), Econometrica.
- status: canonical
- checked: 2026-06-22 · standard multiplicity references; not live-web reverified in this pass

### M11 · Randomization inference
- claim-tag: randomization-inference-design
- claim: When treatment assignment is known or plausibly randomized, randomization inference should respect the actual assignment mechanism.
- used-in: references/inference-and-uncertainty.md; references/design-gate-cards.md
- source: Fisher (1935), The Design of Experiments; Rosenbaum (2002), Observational Studies; Young (2019), Quarterly Journal of Economics.
- status: canonical
- checked: 2026-06-22 · standard randomization-inference references; not live-web reverified in this pass

### M12 · Spatial correlation
- claim-tag: spatial-correlation-conley
- claim: Designs with spatially correlated shocks or outcomes need spatially robust inference, commonly Conley-style standard errors or an explicitly justified alternative.
- used-in: references/inference-and-uncertainty.md; references/threats-to-validity.md
- source: Conley (1999), Journal of Econometrics; Conley (2008), in The New Palgrave Dictionary of Economics.
- status: canonical
- checked: 2026-06-22 · standard spatial-inference references; not live-web reverified in this pass

### M13 · Oster coefficient stability
- claim-tag: oster-coefficient-stability
- claim: Selection-on-unobservables sensitivity checks such as Oster bounds are robustness evidence, not a substitute for a credible research design.
- used-in: references/design-gate-cards.md; references/threats-to-validity.md
- source: Oster (2019), Journal of Business & Economic Statistics.
- status: canonical
- checked: 2026-06-22 · standard omitted-variable sensitivity reference; not live-web reverified in this pass

### M14 · E-value sensitivity
- claim-tag: evalue-unmeasured-confounding
- claim: For risk-ratio style epidemiological claims, E-values quantify the minimum unmeasured-confounding strength needed to explain away an association but do not prove causality.
- used-in: references/inference-and-uncertainty.md; references/threats-to-validity.md
- source: VanderWeele & Ding (2017), Annals of Internal Medicine.
- status: canonical
- checked: 2026-06-22 · standard epidemiology sensitivity reference; not live-web reverified in this pass

### M15 · Synthetic control inference
- claim-tag: synthetic-control-placebo-inference
- claim: Synthetic-control claims need transparent donor-pool construction, pre-period fit diagnostics, and placebo or permutation-style inference.
- used-in: references/design-gate-cards.md; references/research-grade-methods.md
- source: Abadie, Diamond & Hainmueller (2010), Journal of the American Statistical Association; Abadie, Diamond & Hainmueller (2015), American Journal of Political Science.
- status: canonical
- checked: 2026-06-22 · standard synthetic-control references; not live-web reverified in this pass

### M16 · Synthetic DiD
- claim-tag: synthetic-did-reweighting
- claim: Synthetic DiD combines outcome modeling and unit/time weighting; reports should distinguish it from both ordinary TWFE and classic synthetic control.
- used-in: references/design-gate-cards.md; references/research-grade-methods.md
- source: Arkhangelsky, Athey, Hirshberg, Imbens & Wager (2021), American Economic Review.
- status: canonical
- checked: 2026-06-22 · standard synthetic-DiD reference; not live-web reverified in this pass

### M17 · Double machine learning cross-fitting
- claim-tag: dml-cross-fitting
- claim: Double/debiased machine learning relies on orthogonal scores and cross-fitting to reduce overfitting bias in nuisance estimation.
- used-in: references/research-grade-methods.md; references/statspai-analysis.md
- source: Chernozhukov et al. (2018), Econometrics Journal.
- status: canonical
- checked: 2026-06-22 · standard DML reference; not live-web reverified in this pass

### M18 · Bad controls
- claim-tag: bad-control-screen
- claim: Controls affected by treatment or colliders can bias causal estimates; design registration must screen controls before estimation.
- used-in: references/design-transparency.md; references/threats-to-validity.md; templates/design_register.md
- source: Angrist & Pischke (2009), Mostly Harmless Econometrics; Cinelli, Forney & Pearl (2022), Sociological Methods & Research.
- status: canonical
- checked: 2026-06-22 · standard causal-design references; not live-web reverified in this pass

### M19 · Pre-analysis plan
- claim-tag: preregistration-specification-search
- claim: Pre-analysis plans and design registries reduce undisclosed specification search but do not remove the need for robustness and evidence governance.
- used-in: references/design-transparency.md; references/skillopt-improvement-loop.md; SKILL.md
- source: Miguel et al. (2014), Science; Olken (2015), Journal of Economic Perspectives.
- status: canonical
- checked: 2026-06-22 · standard transparency references; not live-web reverified in this pass

### M20 · Specification curve
- claim-tag: specification-curve-reporting
- claim: Specification-curve or multiverse reporting is useful for exposing design sensitivity, but the allowed specification family must be justified before reading the curve.
- used-in: references/design-transparency.md; references/threats-to-validity.md
- source: Simonsohn, Simmons & Nelson (2020), Nature Human Behaviour; Young & Holsteen (2017), Sociological Methods & Research.
- status: canonical
- checked: 2026-06-22 · standard specification-curve references; not live-web reverified in this pass
