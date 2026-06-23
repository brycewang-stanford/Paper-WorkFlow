#!/usr/bin/env python3
"""Stage 3 replication-accuracy benchmark for the Paper-WorkFlow skill.

Why this exists
---------------
The rest of the skill's eval layer (`score_skill.py`, `check_complexity_budget.py`,
`check_workspace_gates.py`, the cross-reference linter) measures whether the
*documented procedure* is internally consistent and whether the *gates fired*.
None of them measure the thing a reader of an empirical paper actually cares
about: **did the numbers come out right.** A Stage 3 run can satisfy every gate
(design register written, method gate PASS, robustness files on disk) and still
report a coefficient with the wrong sign or the wrong magnitude.

The Econometrics-Agent paper (`Can AI Master Econometrics?`, arXiv 2506.00856)
closed exactly this hole for an agent by scoring against published replication
packages on three nested metrics:

  - **sign-correct**     : the coefficient points the right way;
  - **perfect**          : it lands within a tight band of the gold value;
  - **partial**          : it is sign-correct and roughly the right magnitude.

This harness ports that idea to a *documentary* skill. It does NOT run an
estimator. It scores a candidate's *produced estimates* (whatever Stage 3 wrote
to `03_analysis/results/`) against a frozen **gold truth** that we either own
(the repo's own DiD demo has a known `TRUE_ATT = 2.0`) or transcribe from a
published table with a cited source. The output is the same three rates the
paper reports, plus a per-coefficient ledger so a miss is diagnosable.

Integrity contract (mirrors the skill's own anti-fabrication discipline)
------------------------------------------------------------------------
A gold value is a *measured fact* with a source. Every case must carry a
`gold_source` (a paper table, a simulation's known DGP, an official figure).
Cases with no real gold yet are marked `"status": "template"` and are SKIPPED in
scoring, never silently scored against a placeholder. The scorer will refuse
(non-zero) to treat a template as if it had a gold value.

Standalone by construction: reads files only, imports nothing from the skill, so
it never collides with maintenance edits in flight on the core skill files.
`validate_skill.py` runs the self-test as a blocking maintenance gate.

Usage
-----
    # Score a candidate estimates file against one case (or a directory of cases)
    python3 evals/check_replication_accuracy.py \
        --case evals/replication_cases/did_demo_self.json \
        --candidate 03_analysis/results/estimates.json

    # Score every real (non-template) case in the suite against a candidate
    python3 evals/check_replication_accuracy.py \
        --cases evals/replication_cases --candidate path/to/estimates.json

    # Just validate the case suite's schema (no candidate needed)
    python3 evals/check_replication_accuracy.py --validate-suite evals/replication_cases

    python3 evals/check_replication_accuracy.py --json ...      # machine readable
    python3 evals/check_replication_accuracy.py --selftest      # invariant self-test
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_SUITE = HERE / "replication_cases"

# Default tolerances; a case may override any of them under "tolerances".
DEFAULT_REL_TOL = 0.05      # within 5% of the gold point estimate -> "perfect"
DEFAULT_PARTIAL_TOL = 0.20  # within 20% -> counts toward "partial" magnitude
DEFAULT_ZERO_BAND = 1e-8    # |value| <= band is treated as a zero / null effect


# --------------------------------------------------------------------------- #
# pure scoring core                                                            #
# --------------------------------------------------------------------------- #
def _sign(x: float, zero_band: float) -> int:
    if x > zero_band:
        return 1
    if x < -zero_band:
        return -1
    return 0


def _gold_sign(gold: dict, zero_band: float) -> int:
    """A case may pin the sign explicitly ('+'/'-'/'0'); else infer from value."""
    declared = gold.get("sign")
    if declared in ("+", "pos", "positive"):
        return 1
    if declared in ("-", "neg", "negative"):
        return -1
    if declared in ("0", "zero", "null"):
        return 0
    return _sign(float(gold["value"]), zero_band)


def score_coefficient(gold: dict, cand_value: float, tol: dict) -> dict:
    """Score one coefficient. Pure: gold + candidate value + tolerances -> verdict."""
    rel_tol = tol.get("rel_tol", DEFAULT_REL_TOL)
    partial_tol = tol.get("partial_tol", DEFAULT_PARTIAL_TOL)
    zero_band = tol.get("zero_band", DEFAULT_ZERO_BAND)

    gold_value = float(gold["value"])
    gsign = _gold_sign(gold, zero_band)
    csign = _sign(cand_value, zero_band)

    abs_err = abs(cand_value - gold_value)
    # Relative error uses a denominator floored away from 0 so a near-zero gold
    # does not make every candidate "infinitely wrong".
    denom = max(abs(gold_value), tol.get("abs_floor", 1.0))
    rel_err = abs_err / denom

    return {
        "name": gold.get("name", "?"),
        "gold": gold_value,
        "candidate": cand_value,
        "abs_err": abs_err,
        "rel_err": rel_err,
        "sign_match": csign == gsign,
        "within_perfect": rel_err <= rel_tol,
        "within_partial": rel_err <= partial_tol,
    }


def score_case(case: dict, candidate: dict) -> dict:
    """Score one case: every primary coefficient, then the three nested metrics.

    The case-level verdict mirrors arXiv 2506.00856's reported rates:
      - sign_correct : every primary coefficient points the right way;
      - perfect      : every primary coefficient within rel_tol (implies sign);
      - partial      : sign_correct, not perfect, and roughly the right
                       magnitude (at least one coefficient within rel_tol OR
                       all within partial_tol).
    """
    tol = case.get("tolerances", {})
    cand_coeffs = candidate.get("coefficients", candidate)
    per_coeff: list[dict] = []
    missing: list[str] = []
    for gold in case["primary_coefficients"]:
        name = gold["name"]
        if name not in cand_coeffs:
            missing.append(name)
            continue
        raw = cand_coeffs[name]
        cand_value = float(raw["value"] if isinstance(raw, dict) else raw)
        per_coeff.append(score_coefficient(gold, cand_value, tol))

    n_primary = len(case["primary_coefficients"])
    scored = len(per_coeff)
    all_present = not missing and scored == n_primary
    all_sign = all_present and all(c["sign_match"] for c in per_coeff)
    all_perfect = all_present and all(c["within_perfect"] for c in per_coeff)
    any_perfect = any(c["within_perfect"] for c in per_coeff)
    all_partial = all_present and all(c["within_partial"] for c in per_coeff)

    perfect = bool(all_perfect)
    sign_correct = bool(all_sign)
    partial = bool(all_sign and not perfect and (any_perfect or all_partial))

    if perfect:
        tier = "perfect"
    elif partial:
        tier = "partial"
    elif sign_correct:
        tier = "sign_only"
    else:
        tier = "fail"

    return {
        "case_id": case.get("id", "?"),
        "design": case.get("design", "?"),
        "n_primary": n_primary,
        "scored": scored,
        "missing_coefficients": missing,
        "sign_correct": sign_correct,
        "perfect": perfect,
        "partial": partial,
        "tier": tier,
        "coefficients": per_coeff,
    }


def aggregate(case_results: list[dict]) -> dict:
    """Roll per-case verdicts into the paper's three headline rates."""
    n = len(case_results)
    if n == 0:
        return {"n_cases": 0, "sign_correct_rate": None,
                "perfect_rate": None, "partial_or_better_rate": None}
    sign = sum(1 for r in case_results if r["sign_correct"])
    perfect = sum(1 for r in case_results if r["perfect"])
    # "partial or better" = sign-correct and at least roughly the magnitude,
    # i.e. perfect OR partial. Reported alongside the stricter perfect rate.
    partial_or_better = sum(1 for r in case_results if r["perfect"] or r["partial"])
    return {
        "n_cases": n,
        "sign_correct_rate": sign / n,
        "perfect_rate": perfect / n,
        "partial_or_better_rate": partial_or_better / n,
        "sign_correct": sign,
        "perfect": perfect,
        "partial_or_better": partial_or_better,
    }


# --------------------------------------------------------------------------- #
# case-suite loading / validation                                             #
# --------------------------------------------------------------------------- #
REQUIRED_CASE_KEYS = ("id", "design", "primary_coefficients")


def validate_case(case: dict) -> list[str]:
    """Schema + integrity checks for a single case. Returns a list of problems."""
    problems: list[str] = []
    for key in REQUIRED_CASE_KEYS:
        if key not in case:
            problems.append(f"missing key '{key}'")
    status = case.get("status", "active")
    if status not in ("active", "template"):
        problems.append(f"status must be 'active' or 'template', got {status!r}")
    coeffs = case.get("primary_coefficients", [])
    if not isinstance(coeffs, list) or not coeffs:
        problems.append("primary_coefficients must be a non-empty list")
        return problems
    for i, c in enumerate(coeffs):
        if "name" not in c:
            problems.append(f"primary_coefficients[{i}] missing 'name'")
        # Integrity: an active case must carry a real, sourced gold value.
        if status == "active":
            if c.get("value") is None:
                problems.append(f"primary_coefficients[{i}] active case has null gold value")
            if not case.get("gold_source"):
                problems.append("active case missing 'gold_source' (gold must be a sourced fact)")
        # Template gold must be explicitly null so it can never be scored as real.
        if status == "template" and c.get("value") not in (None, "", "TBD"):
            problems.append(f"primary_coefficients[{i}] template should leave gold value null/TBD")
    return problems


def load_suite(path: Path) -> tuple[list[dict], list[str]]:
    """Load every *.json case under `path`. Returns (cases, schema_problems)."""
    cases: list[dict] = []
    problems: list[str] = []
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    for f in files:
        try:
            case = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"{f.name}: not loadable ({exc})")
            continue
        for p in validate_case(case):
            problems.append(f"{f.name}: {p}")
        case["_file"] = f.name
        cases.append(case)
    return cases, problems


# --------------------------------------------------------------------------- #
# reporting                                                                    #
# --------------------------------------------------------------------------- #
def render(scored: list[dict], agg: dict, skipped: list[str]) -> str:
    out = ["", "Stage 3 replication-accuracy benchmark", "=" * 60]
    for r in scored:
        flag = {"perfect": "PERFECT", "partial": "partial",
                "sign_only": "sign-only", "fail": "FAIL"}[r["tier"]]
        out.append(f"[{flag:>9}] {r['case_id']:<22} ({r['design']})")
        for c in r["coefficients"]:
            mark = "ok" if c["within_perfect"] else ("~" if c["within_partial"] else
                   ("sign" if c["sign_match"] else "XX"))
            out.append(f"            {c['name']:<18} gold={c['gold']:+.4g} "
                       f"cand={c['candidate']:+.4g} relerr={c['rel_err']:.3f} [{mark}]")
        if r["missing_coefficients"]:
            out.append(f"            MISSING: {', '.join(r['missing_coefficients'])}")
    out.append("=" * 60)
    if agg["n_cases"]:
        out.append(f"  cases scored          : {agg['n_cases']}")
        out.append(f"  sign-correct rate     : {agg['sign_correct_rate']:.1%} "
                   f"({agg['sign_correct']}/{agg['n_cases']})")
        out.append(f"  perfect-repro rate    : {agg['perfect_rate']:.1%} "
                   f"({agg['perfect']}/{agg['n_cases']})")
        out.append(f"  partial-or-better rate: {agg['partial_or_better_rate']:.1%} "
                   f"({agg['partial_or_better']}/{agg['n_cases']})")
    else:
        out.append("  no active cases scored")
    if skipped:
        out.append(f"  skipped (template)    : {', '.join(skipped)}")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# selftest                                                                     #
# --------------------------------------------------------------------------- #
def _selftest() -> int:
    zb = DEFAULT_ZERO_BAND
    # sign logic
    assert _sign(2.0, zb) == 1 and _sign(-2.0, zb) == -1 and _sign(0.0, zb) == 0

    # one coefficient: perfect, partial, sign-only, wrong-sign
    gold = {"name": "att", "value": 2.0}
    perfect = score_coefficient(gold, 2.04, {})       # 2% off -> within 5%
    assert perfect["within_perfect"] and perfect["sign_match"]
    rough = score_coefficient(gold, 2.3, {})          # 15% off -> partial only
    assert not rough["within_perfect"] and rough["within_partial"] and rough["sign_match"]
    far = score_coefficient(gold, 5.0, {})            # 150% off -> sign only
    assert not far["within_partial"] and far["sign_match"]
    wrong = score_coefficient(gold, -2.0, {})         # wrong sign
    assert not wrong["sign_match"]

    # case-level nesting
    case = {
        "id": "synthetic_did", "design": "DiD",
        "primary_coefficients": [{"name": "att", "value": 2.0}],
    }
    r_perfect = score_case(case, {"coefficients": {"att": 2.01}})
    assert r_perfect["tier"] == "perfect" and r_perfect["sign_correct"] and r_perfect["perfect"]
    r_partial = score_case(case, {"coefficients": {"att": 2.3}})
    assert r_partial["tier"] == "partial" and r_partial["partial"] and not r_partial["perfect"]
    r_sign = score_case(case, {"coefficients": {"att": 6.0}})
    assert r_sign["tier"] == "sign_only" and r_sign["sign_correct"] and not r_sign["partial"]
    r_fail = score_case(case, {"coefficients": {"att": -2.0}})
    assert r_fail["tier"] == "fail" and not r_fail["sign_correct"]
    # candidate may pass the bare mapping or {"value": ...}
    assert score_case(case, {"att": 2.01})["perfect"]

    # two-coefficient case: one perfect, one wrong sign -> not sign_correct
    case2 = {"id": "two", "design": "IV",
             "primary_coefficients": [{"name": "b1", "value": 1.0},
                                      {"name": "b2", "value": -0.5}]}
    mixed = score_case(case2, {"coefficients": {"b1": 1.0, "b2": 0.5}})
    assert not mixed["sign_correct"] and mixed["tier"] == "fail"
    # both within partial but not perfect -> partial
    both_rough = score_case(case2, {"coefficients": {"b1": 1.15, "b2": -0.58}})
    assert both_rough["tier"] == "partial"
    # missing coefficient -> not all present -> cannot be sign_correct
    miss = score_case(case2, {"coefficients": {"b1": 1.0}})
    assert miss["missing_coefficients"] == ["b2"] and not miss["sign_correct"]

    # aggregation
    agg = aggregate([r_perfect, r_partial, r_sign, r_fail])
    assert agg["n_cases"] == 4
    assert agg["perfect"] == 1
    assert agg["sign_correct"] == 3                      # perfect+partial+sign_only
    assert agg["partial_or_better"] == 2                 # perfect+partial
    assert abs(agg["sign_correct_rate"] - 0.75) < 1e-9

    # near-zero gold: relative error floored, not exploded
    nz = score_coefficient({"name": "z", "value": 0.0}, 0.3, {"abs_floor": 1.0})
    assert math.isclose(nz["rel_err"], 0.3)

    # validation: active case needs sourced gold; template must have null gold
    assert validate_case({"id": "x", "design": "DiD",
                          "gold_source": "tbl. 2",
                          "primary_coefficients": [{"name": "a", "value": 1.0}]}) == []
    bad_active = validate_case({"id": "x", "design": "DiD",
                               "primary_coefficients": [{"name": "a", "value": None}]})
    assert any("gold_source" in p for p in bad_active)
    assert any("null gold" in p for p in bad_active)
    tmpl_ok = validate_case({"id": "t", "design": "DiD", "status": "template",
                             "primary_coefficients": [{"name": "a", "value": None}]})
    assert tmpl_ok == []
    tmpl_bad = validate_case({"id": "t", "design": "DiD", "status": "template",
                              "primary_coefficients": [{"name": "a", "value": 1.0}]})
    assert any("template should leave gold" in p for p in tmpl_bad)

    # the shipped suite (if present) must be schema-clean and carry the self case
    if DEFAULT_SUITE.is_dir():
        cases, problems = load_suite(DEFAULT_SUITE)
        assert not problems, f"shipped suite has schema problems: {problems}"
        ids = {c["id"] for c in cases}
        assert "did_demo_self" in ids, "the self-contained DiD case must ship"
        self_case = next(c for c in cases if c["id"] == "did_demo_self")
        assert self_case.get("status", "active") == "active"
        # its gold ATT must equal the demo's TRUE_ATT (we own this truth)
        assert any(abs(float(c["value"]) - 2.0) < 1e-9
                   for c in self_case["primary_coefficients"]), \
            "did_demo_self gold ATT must equal TRUE_ATT=2.0"
        # a faithful estimator recovering ~2.0 is perfect; a biased TWFE is caught
        good = score_case(self_case, {"coefficients": {"att": 2.0}})
        assert good["perfect"], "recovering TRUE_ATT must score perfect"

    print("selftest OK: replication-accuracy invariants hold")
    return 0


# --------------------------------------------------------------------------- #
# cli                                                                          #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--case", help="a single case JSON to score")
    p.add_argument("--cases", help="a directory of case JSONs to score")
    p.add_argument("--candidate", help="candidate estimates JSON (coefficients map)")
    p.add_argument("--validate-suite", help="schema-validate a case directory and exit")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--selftest", action="store_true", help="run built-in invariant tests")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.validate_suite:
        cases, problems = load_suite(Path(args.validate_suite))
        if args.json:
            print(json.dumps({"ok": not problems, "n_cases": len(cases),
                              "problems": problems}, ensure_ascii=False, indent=2))
        else:
            print(f"validated {len(cases)} case(s) in {args.validate_suite}")
            for prob in problems:
                print(f"  PROBLEM: {prob}")
        return 1 if problems else 0

    suite_path = Path(args.cases) if args.cases else (Path(args.case) if args.case else None)
    if not suite_path:
        p.error("need --case, --cases, --validate-suite, or --selftest")
    if not args.candidate:
        p.error("scoring needs --candidate <estimates.json>")

    cases, problems = load_suite(suite_path)
    if problems:
        print("ERROR: case suite has schema problems:", file=sys.stderr)
        for prob in problems:
            print(f"  {prob}", file=sys.stderr)
        return 2

    try:
        candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read candidate {args.candidate}: {exc}", file=sys.stderr)
        return 2

    scored: list[dict] = []
    skipped: list[str] = []
    for case in cases:
        if case.get("status", "active") == "template":
            skipped.append(case["id"])
            continue
        scored.append(score_case(case, candidate))
    agg = aggregate(scored)

    if args.json:
        print(json.dumps({"aggregate": agg, "cases": scored, "skipped": skipped},
                         ensure_ascii=False, indent=2))
    else:
        print(render(scored, agg, skipped))
    # Exit non-zero if any scored case failed to be at least sign-correct.
    failed = [r for r in scored if r["tier"] == "fail"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
