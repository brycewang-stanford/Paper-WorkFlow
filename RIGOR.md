# RIGOR.md — gate-coverage report

**Rigor checkers selftest: PASSING — 13/13 green.**

Paper-WorkFlow's differentiator is that research rigor is *executable*, not advisory. Every load-bearing invariant — about a paper run, and about this skill package itself — is enforced by a script with a built-in selftest. This report runs each checker's selftest and records the verdict. A failure here is a non-zero exit, not a soft warning. Regenerate with `python3 scripts/generate_rigor_report.py`; verify freshness in CI with `--check`.

> Context: our two closest peers do not have this layer. K-Dense `scientific-agent-skills` ships only a *security* scanner; Orchestra `AI-Research-SKILLs` self-grades rigor in markdown. See [`RELATED-WORK.md`](RELATED-WORK.md) for the evidence.

The master gate `validate_skill.py` chains every leaf checker below (plus asset, template-contract, link, and notebook checks) into a single `python3 validate_skill.py` run maintainers must pass before shipping.

## Run-time gates — verify a paper run

| Checker | Result | Enforced invariant |
|---|:--:|---|
| [`scripts/check_workspace_gates.py`](scripts/check_workspace_gates.py) | ✅ pass | Method Gate / Draft Quality Gate / replication pack / claim-integrity / design-risk: a gate marked `pass` must have its evidence on disk, and ordering holds (quality gate never looser than the method gate). |
| [`scripts/check_citation_integrity.py`](scripts/check_citation_integrity.py) | ✅ pass | Citation existence + temporal integrity: DOI resolution, retraction screening, citation-laundering, and look-ahead / vintage / sample-vs-claim-period leakage. |
| [`scripts/check_verification_log.py`](scripts/check_verification_log.py) | ✅ pass | The load-bearing methods-claim verification log exists and every claim it makes is backed by a recorded check. |
| [`scripts/smoke_workspace.py`](scripts/smoke_workspace.py) | ✅ pass | A minimal workspace initialises and every template contract holds (templates instantiate with the fields the gates later require). |
| [`scripts/check_preregistration.py`](scripts/check_preregistration.py) | ✅ pass | Pre-registration lock: the primary specification is committed before estimation, and any main result not pre-registered is labelled exploratory (researcher-degrees-of-freedom guard). |
| [`scripts/check_review_scorecard.py`](scripts/check_review_scorecard.py) | ✅ pass | L2 review scorecard: all 7 dimensions scored, every finding carries a severity + verbatim evidence span + locator, a blocking finding caps its dimension <=4, and a declared PASS is consistent with the scores. |
| [`evals/check_replication_accuracy.py`](evals/check_replication_accuracy.py) | ✅ pass | Stage 3 output correctness: candidate estimates are scored against sourced gold coefficients on sign-correct, perfect-reproduction, and partial-or-better metrics; template cases cannot be scored as truth. |
| [`evals/check_quality_judge.py`](evals/check_quality_judge.py) | ✅ pass | Reproducible LLM-as-judge bookkeeping: the Draft Quality Gate verdict is recomputed from dimension scores, red flags, integrity status, and frozen calibration anchors. |

## Maintenance gates — verify this skill package

| Checker | Result | Enforced invariant |
|---|:--:|---|
| [`scripts/check_gate_integration.py`](scripts/check_gate_integration.py) | ✅ pass | End-to-end: a real workspace init flowed through real templates is accepted by the gate checkers as a coherent whole. |
| [`scripts/check_cross_references.py`](scripts/check_cross_references.py) | ✅ pass | Cross-reference contract: every internal link, named artifact, and script path referenced from SKILL.md and references actually resolves. |
| [`scripts/check_skillopt_packet.py`](scripts/check_skillopt_packet.py) | ✅ pass | SkillOpt improvement packets: >=3 train + >=2 held-out rollouts, a bounded edit budget, and accept requires a score gain + regression pass. |
| [`evals/check_complexity_budget.py`](evals/check_complexity_budget.py) | ✅ pass | Complexity ratchet: the always-loaded SKILL.md and the reference-file count cannot grow past the recorded ceiling without a justified bump. |
| [`evals/score_skill.py`](evals/score_skill.py) | ✅ pass | Held-out scoring-harness invariants for the SkillOpt selection gate (baseline vs candidate scored on the same rubric). |

## How to reproduce

```bash
python3 scripts/generate_rigor_report.py        # regenerate this file
python3 scripts/generate_rigor_report.py --check # CI: fail if stale
```

_Generated 2026-06-24 by `scripts/generate_rigor_report.py`. The body is deterministic apart from this line.
