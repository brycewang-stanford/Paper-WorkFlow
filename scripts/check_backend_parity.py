#!/usr/bin/env python3
"""Check backend-parity fixtures for fallback and secondary validation routes.

Paper-WorkFlow supports Python/StatsPAI, Stata, and R backends. Runtime fallback
or secondary validation is only honest when the alternative backend reproduces
the same result bundle: locked sample, estimator family, clustering, fixed
effects, key coefficients, standard errors, and diagnostics.

This checker evaluates a fixture manifest and a workspace-level
00_meta/backend_parity.json report of reference/candidate backend result
summaries. It is intentionally offline and dependency-free; it does not run
Stata or R. Its job is to make the parity contract mechanical so a workspace
cannot claim "artifact parity checked" without a concrete comparison format.

Usage:
    python3 scripts/check_backend_parity.py
    python3 scripts/check_backend_parity.py path/to/workspace
    python3 scripts/check_backend_parity.py --selftest
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "backend_parity_cases.json"
WORKSPACE_REPORT_REL = "00_meta/backend_parity.json"
ALLOWED_BACKENDS = {"python-statspai", "stata", "r"}
REQUIRED_RESULT_FIELDS = {
    "estimator_family",
    "sample_hash",
    "nobs",
    "cluster_level",
    "fixed_effects",
    "coefficients",
    "diagnostics",
}
REQUIRED_TOLERANCES = {"estimate_abs", "std_error_abs", "diagnostic_abs"}
REQUIRED_COMPARISON_SCOPE = {
    "sample_hash",
    "nobs",
    "estimator_family",
    "cluster_level",
    "fixed_effects",
    "coefficients",
    "standard_errors",
    "diagnostics",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    if not math.isfinite(value):
        return None
    return value


def _validate_result_shape(case_id: str, label: str, result: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return [f"{case_id}: {label} must be an object"]
    missing = sorted(REQUIRED_RESULT_FIELDS - set(result))
    if missing:
        errors.append(f"{case_id}: {label} missing field(s): {', '.join(missing)}")
        return errors

    if not isinstance(result.get("estimator_family"), str) or not result["estimator_family"].strip():
        errors.append(f"{case_id}: {label}.estimator_family must be a non-empty string")
    if not isinstance(result.get("sample_hash"), str) or not result["sample_hash"].startswith("sha256:"):
        errors.append(f"{case_id}: {label}.sample_hash must start with sha256:")
    nobs = result.get("nobs")
    if isinstance(nobs, bool) or not isinstance(nobs, int) or nobs <= 0:
        errors.append(f"{case_id}: {label}.nobs must be a positive integer")
    if not isinstance(result.get("cluster_level"), str) or not result["cluster_level"].strip():
        errors.append(f"{case_id}: {label}.cluster_level must be a non-empty string")
    fixed_effects = result.get("fixed_effects")
    if not isinstance(fixed_effects, list) or any(not isinstance(item, str) or not item for item in fixed_effects):
        errors.append(f"{case_id}: {label}.fixed_effects must be a list of strings")

    coefficients = result.get("coefficients")
    if not isinstance(coefficients, dict) or not coefficients:
        errors.append(f"{case_id}: {label}.coefficients must be a non-empty object")
    else:
        for term, values in coefficients.items():
            if not isinstance(term, str) or not term:
                errors.append(f"{case_id}: {label}.coefficients has an empty term")
                continue
            if not isinstance(values, dict):
                errors.append(f"{case_id}: {label}.coefficients.{term} must be an object")
                continue
            for field in ("estimate", "std_error"):
                if _number(values.get(field)) is None:
                    errors.append(f"{case_id}: {label}.coefficients.{term}.{field} must be finite numeric")

    diagnostics = result.get("diagnostics")
    if not isinstance(diagnostics, dict):
        errors.append(f"{case_id}: {label}.diagnostics must be an object")
    else:
        for key, value in diagnostics.items():
            if not isinstance(key, str) or not key:
                errors.append(f"{case_id}: {label}.diagnostics has an empty key")
            elif _number(value) is None:
                errors.append(f"{case_id}: {label}.diagnostics.{key} must be finite numeric")
    return errors


def _compare_numbers(errors: list[str], label: str, left: float, right: float, tolerance: float) -> None:
    if abs(left - right) > tolerance:
        errors.append(f"{label} mismatch: reference={left} candidate={right} tolerance={tolerance}")


def compare_results(reference: dict, candidate: dict, tolerances: dict) -> list[str]:
    errors: list[str] = []

    for field in ("estimator_family", "sample_hash", "nobs", "cluster_level"):
        if reference.get(field) != candidate.get(field):
            errors.append(f"{field} mismatch: reference={reference.get(field)!r} candidate={candidate.get(field)!r}")

    if sorted(reference.get("fixed_effects", [])) != sorted(candidate.get("fixed_effects", [])):
        errors.append(
            "fixed_effects mismatch: "
            f"reference={sorted(reference.get('fixed_effects', []))!r} "
            f"candidate={sorted(candidate.get('fixed_effects', []))!r}"
        )

    ref_coeffs = reference.get("coefficients", {})
    cand_coeffs = candidate.get("coefficients", {})
    for term in sorted(set(ref_coeffs) - set(cand_coeffs)):
        errors.append(f"missing coefficient in candidate: {term}")
    for term in sorted(set(cand_coeffs) - set(ref_coeffs)):
        errors.append(f"extra coefficient in candidate: {term}")
    for term in sorted(set(ref_coeffs) & set(cand_coeffs)):
        _compare_numbers(
            errors,
            f"{term} estimate",
            float(ref_coeffs[term]["estimate"]),
            float(cand_coeffs[term]["estimate"]),
            tolerances["estimate_abs"],
        )
        _compare_numbers(
            errors,
            f"{term} std_error",
            float(ref_coeffs[term]["std_error"]),
            float(cand_coeffs[term]["std_error"]),
            tolerances["std_error_abs"],
        )

    ref_diag = reference.get("diagnostics", {})
    cand_diag = candidate.get("diagnostics", {})
    for key in sorted(set(ref_diag) - set(cand_diag)):
        errors.append(f"missing diagnostic in candidate: {key}")
    for key in sorted(set(cand_diag) - set(ref_diag)):
        errors.append(f"extra diagnostic in candidate: {key}")
    for key in sorted(set(ref_diag) & set(cand_diag)):
        _compare_numbers(
            errors,
            f"{key} diagnostic",
            float(ref_diag[key]),
            float(cand_diag[key]),
            tolerances["diagnostic_abs"],
        )

    return errors


def _validate_tolerances(raw: object, errors: list[str], prefix: str) -> dict:
    if not isinstance(raw, dict):
        errors.append(f"{prefix} must be an object")
        raw = {}
    tolerances: dict[str, float] = {}
    for key in REQUIRED_TOLERANCES:
        value = _number(raw.get(key))
        if value is None or value < 0:
            errors.append(f"{prefix}.{key} must be a non-negative finite number")
            tolerances[key] = 0.0
        else:
            tolerances[key] = value
    return tolerances


def evaluate_report(report: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    if report.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    status = report.get("status")
    if status not in {"pending", "pass", "not_pass"}:
        errors.append("status must be pending, pass, or not_pass")
        status = "not_pass"

    primary = report.get("primary_backend")
    candidate = report.get("candidate_backend")
    if status != "pending":
        if primary not in ALLOWED_BACKENDS:
            errors.append(f"primary_backend must be one of {sorted(ALLOWED_BACKENDS)}")
        if candidate not in ALLOWED_BACKENDS:
            errors.append(f"candidate_backend must be one of {sorted(ALLOWED_BACKENDS)}")
        if primary == candidate:
            errors.append("primary_backend and candidate_backend must differ")

    scope = report.get("comparison_scope")
    if not isinstance(scope, list) or any(not isinstance(item, str) or not item for item in scope):
        errors.append("comparison_scope must be a list of strings")
        scope_set: set[str] = set()
    else:
        scope_set = set(scope)
    missing_scope = sorted(REQUIRED_COMPARISON_SCOPE - scope_set)
    if missing_scope:
        errors.append("comparison_scope missing required item(s): " + ", ".join(missing_scope))

    tolerances = _validate_tolerances(report.get("tolerances"), errors, "tolerances")
    result_pairs = report.get("result_pairs")
    if not isinstance(result_pairs, list):
        errors.append("result_pairs must be a list")
        result_pairs = []
    blocking = report.get("blocking_differences")
    if not isinstance(blocking, list) or any(not isinstance(item, str) or not item.strip() for item in blocking):
        errors.append("blocking_differences must be a list of non-empty strings")
        blocking = []

    pair_results: list[dict] = []
    failed_pairs = 0
    seen: set[str] = set()
    for index, pair in enumerate(result_pairs):
        if not isinstance(pair, dict):
            errors.append(f"result_pairs[{index}] must be an object")
            continue
        pid = pair.get("id")
        if not isinstance(pid, str) or not pid.strip():
            pid = f"<missing-{index}>"
            errors.append(f"result_pairs[{index}] missing non-empty id")
        if pid in seen:
            errors.append(f"duplicate result pair id: {pid}")
        seen.add(pid)

        reference = pair.get("reference")
        candidate_result = pair.get("candidate")
        shape_errors = _validate_result_shape(pid, "reference", reference)
        shape_errors += _validate_result_shape(pid, "candidate", candidate_result)
        if shape_errors:
            errors.extend(shape_errors)
            failed_pairs += 1
            pair_results.append({"id": pid, "ok": False, "errors": shape_errors})
            continue
        compare_errors = compare_results(reference, candidate_result, tolerances)
        if compare_errors:
            failed_pairs += 1
        pair_results.append({"id": pid, "ok": not compare_errors, "errors": compare_errors})

    if status == "pending":
        if result_pairs:
            errors.append("status=pending but result_pairs is not empty")
        if blocking:
            errors.append("status=pending but blocking_differences is not empty")
    elif status == "pass":
        if not result_pairs:
            errors.append("status=pass requires at least one result pair")
        if failed_pairs:
            errors.append(f"status=pass but {failed_pairs} result pair(s) failed parity")
        if blocking:
            errors.append("status=pass but blocking_differences is not empty")
    elif status == "not_pass":
        if not result_pairs:
            errors.append("status=not_pass requires at least one result pair")
        if not failed_pairs and not blocking:
            errors.append("status=not_pass requires a failed result pair or blocking_differences")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "status": status,
        "result_pair_count": len(result_pairs),
        "failed_pair_count": failed_pairs,
        "pair_results": pair_results,
    }


def evaluate_workspace(workspace: Path) -> dict:
    report_path = workspace / WORKSPACE_REPORT_REL
    if not report_path.exists():
        return {
            "ok": False,
            "errors": [f"missing {WORKSPACE_REPORT_REL}"],
            "warnings": [],
            "status": "missing",
            "result_pair_count": 0,
            "failed_pair_count": 0,
            "pair_results": [],
        }
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "errors": [f"{WORKSPACE_REPORT_REL} is not valid JSON: {exc}"],
            "warnings": [],
            "status": "invalid",
            "result_pair_count": 0,
            "failed_pair_count": 0,
            "pair_results": [],
        }
    result = evaluate_report(data)
    result["path"] = WORKSPACE_REPORT_REL
    return result


def evaluate_manifest(data: dict) -> dict:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("checker") != "scripts/check_backend_parity.py":
        errors.append("checker must be scripts/check_backend_parity.py")

    tolerances = data.get("default_tolerances")
    if not isinstance(tolerances, dict):
        errors.append("default_tolerances must be an object")
        tolerances = {}
    for key in REQUIRED_TOLERANCES:
        value = _number(tolerances.get(key))
        if value is None or value < 0:
            errors.append(f"default_tolerances.{key} must be a non-negative finite number")

    minimum = data.get("minimum_case_count")
    if not isinstance(minimum, int) or minimum < 1:
        errors.append("minimum_case_count must be a positive integer")
        minimum = 1

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        cases = []
    if len(cases) < minimum:
        errors.append(f"expected at least {minimum} backend parity cases, found {len(cases)}")

    seen: set[str] = set()
    pass_cases = 0
    fail_cases = 0
    caught_failures = 0
    case_results: list[dict] = []

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{index}] must be an object")
            continue
        cid = case.get("id")
        if not isinstance(cid, str) or not cid.strip():
            cid = f"<missing-{index}>"
            errors.append(f"cases[{index}] missing non-empty id")
        if cid in seen:
            errors.append(f"duplicate case id: {cid}")
        seen.add(cid)

        for field in ("design", "primary_backend", "candidate_backend", "expected"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                errors.append(f"{cid}: {field} must be a non-empty string")
        if case.get("primary_backend") not in ALLOWED_BACKENDS:
            errors.append(f"{cid}: primary_backend must be one of {sorted(ALLOWED_BACKENDS)}")
        if case.get("candidate_backend") not in ALLOWED_BACKENDS:
            errors.append(f"{cid}: candidate_backend must be one of {sorted(ALLOWED_BACKENDS)}")
        if case.get("primary_backend") == case.get("candidate_backend"):
            errors.append(f"{cid}: primary_backend and candidate_backend must differ")

        expected = case.get("expected")
        if expected not in {"pass", "fail"}:
            errors.append(f"{cid}: expected must be pass or fail")
            expected = "fail"
        if expected == "pass":
            pass_cases += 1
        else:
            fail_cases += 1
            if not isinstance(case.get("expected_error"), str) or not case["expected_error"].strip():
                errors.append(f"{cid}: failing case must declare expected_error")

        reference = case.get("reference")
        candidate = case.get("candidate")
        shape_errors = _validate_result_shape(cid, "reference", reference)
        shape_errors += _validate_result_shape(cid, "candidate", candidate)
        if shape_errors:
            errors.extend(shape_errors)
            case_results.append({"id": cid, "expected": expected, "caught": False, "errors": shape_errors})
            continue

        compare_errors = compare_results(reference, candidate, tolerances)
        if expected == "pass" and compare_errors:
            errors.append(f"{cid}: expected pass but comparison failed: {compare_errors[0]}")
        elif expected == "fail":
            expected_error = case.get("expected_error", "")
            joined = "\n".join(compare_errors)
            if not compare_errors:
                errors.append(f"{cid}: expected fail but comparison passed")
            elif expected_error not in joined:
                errors.append(f"{cid}: expected error {expected_error!r} not found in comparison errors")
            else:
                caught_failures += 1
        case_results.append(
            {
                "id": cid,
                "expected": expected,
                "caught": bool(compare_errors) if expected == "fail" else not compare_errors,
                "errors": compare_errors,
            }
        )

    if pass_cases < 1:
        errors.append("at least one passing backend parity fixture is required")
    if fail_cases < 1:
        errors.append("at least one failing backend parity fixture is required")

    return {
        "ok": not errors,
        "errors": errors,
        "case_count": len(cases),
        "pass_case_count": pass_cases,
        "fail_case_count": fail_cases,
        "caught_failure_count": caught_failures,
        "case_results": case_results,
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow backend parity fixtures",
        f"  cases: {result['case_count']}",
        f"  passing fixtures: {result['pass_case_count']}",
        f"  failing fixtures caught: {result['caught_failure_count']}/{result['fail_case_count']}",
    ]
    for case in result["case_results"]:
        mark = "OK" if case["caught"] else "FAIL"
        lines.append(f"  [{mark}] {case['id']}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  BACKEND PARITY OK" if result["ok"] else "  BACKEND PARITY FAILED")
    return "\n".join(lines)


def render_report(result: dict) -> str:
    lines = [
        "Paper-WorkFlow workspace backend parity report",
        f"  path: {result.get('path', WORKSPACE_REPORT_REL)}",
        f"  status: {result['status']}",
        f"  result pairs: {result['result_pair_count']}",
        f"  failed pairs: {result['failed_pair_count']}",
    ]
    for pair in result["pair_results"]:
        mark = "OK" if pair["ok"] else "FAIL"
        lines.append(f"  [{mark}] {pair['id']}")
    for warning in result["warnings"]:
        lines.append(f"  WARN: {warning}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  BACKEND PARITY REPORT OK" if result["ok"] else "  BACKEND PARITY REPORT FAILED")
    return "\n".join(lines)


def _good_manifest() -> dict:
    return {
        "schema_version": 1,
        "checker": "scripts/check_backend_parity.py",
        "minimum_case_count": 2,
        "default_tolerances": {
            "estimate_abs": 1e-8,
            "std_error_abs": 1e-8,
            "diagnostic_abs": 1e-8,
        },
        "cases": [
            {
                "id": "good_equivalent",
                "design": "did_event_study",
                "primary_backend": "python-statspai",
                "candidate_backend": "r",
                "expected": "pass",
                "reference": {
                    "estimator_family": "twfe",
                    "sample_hash": "sha256:sample",
                    "nobs": 100,
                    "cluster_level": "firm",
                    "fixed_effects": ["firm", "year"],
                    "coefficients": {"x": {"estimate": 1.0, "std_error": 0.2}},
                    "diagnostics": {"pretrend_p": 0.5},
                },
                "candidate": {
                    "estimator_family": "twfe",
                    "sample_hash": "sha256:sample",
                    "nobs": 100,
                    "cluster_level": "firm",
                    "fixed_effects": ["year", "firm"],
                    "coefficients": {"x": {"estimate": 1.0, "std_error": 0.2}},
                    "diagnostics": {"pretrend_p": 0.5},
                },
            },
            {
                "id": "bad_nobs",
                "design": "did_event_study",
                "primary_backend": "python-statspai",
                "candidate_backend": "stata",
                "expected": "fail",
                "expected_error": "nobs mismatch",
                "reference": {
                    "estimator_family": "twfe",
                    "sample_hash": "sha256:sample",
                    "nobs": 100,
                    "cluster_level": "firm",
                    "fixed_effects": ["firm", "year"],
                    "coefficients": {"x": {"estimate": 1.0, "std_error": 0.2}},
                    "diagnostics": {},
                },
                "candidate": {
                    "estimator_family": "twfe",
                    "sample_hash": "sha256:sample",
                    "nobs": 101,
                    "cluster_level": "firm",
                    "fixed_effects": ["firm", "year"],
                    "coefficients": {"x": {"estimate": 1.0, "std_error": 0.2}},
                    "diagnostics": {},
                },
            },
        ],
    }


def _good_report(status: str = "pass") -> dict:
    manifest = _good_manifest()
    pair = manifest["cases"][0]
    return {
        "schema_version": 1,
        "status": status,
        "primary_backend": "python-statspai",
        "candidate_backend": "r",
        "comparison_scope": sorted(REQUIRED_COMPARISON_SCOPE),
        "tolerances": manifest["default_tolerances"],
        "result_pairs": [
            {
                "id": "main_result",
                "reference": deepcopy(pair["reference"]),
                "candidate": deepcopy(pair["candidate"]),
            }
        ],
        "blocking_differences": [],
        "last_checked": "2026-06-25 12:00",
    }


def _pending_report() -> dict:
    report = _good_report(status="pending")
    report["primary_backend"] = ""
    report["candidate_backend"] = ""
    report["result_pairs"] = []
    report["blocking_differences"] = []
    report["last_checked"] = ""
    return report


def _selftest() -> int:
    good = _good_manifest()
    assert evaluate_manifest(good)["ok"], "complete synthetic manifest must pass"

    bad = deepcopy(good)
    bad["cases"] = [good["cases"][0]]
    assert not evaluate_manifest(bad)["ok"], "manifest without failing fixture must fail"

    bad = deepcopy(good)
    bad["cases"][0]["candidate"]["sample_hash"] = "sha256:drifted"
    assert not evaluate_manifest(bad)["ok"], "passing fixture with sample drift must fail"

    bad = deepcopy(good)
    bad["cases"][1]["expected_error"] = "cluster_level mismatch"
    assert not evaluate_manifest(bad)["ok"], "failing fixture must assert the actual error"

    bad = deepcopy(good)
    del bad["cases"][0]["reference"]["coefficients"]["x"]["std_error"]
    assert not evaluate_manifest(bad)["ok"], "missing standard error must fail shape validation"

    assert evaluate_report(_pending_report())["ok"], "pending workspace template must pass"
    assert evaluate_report(_good_report())["ok"], "passing workspace report must pass"

    bad_report = _good_report()
    bad_report["result_pairs"][0]["candidate"]["coefficients"]["x"]["estimate"] = 1.5
    assert not evaluate_report(bad_report)["ok"], "status=pass with coefficient drift must fail"

    bad_report = _good_report(status="not_pass")
    assert not evaluate_report(bad_report)["ok"], "status=not_pass without a failed pair must fail"

    good_not_pass = _good_report(status="not_pass")
    good_not_pass["result_pairs"][0]["candidate"]["nobs"] = 101
    good_not_pass["blocking_differences"] = ["nobs mismatch"]
    assert evaluate_report(good_not_pass)["ok"], "status=not_pass with concrete mismatch must pass"

    print("selftest OK: backend parity fixture invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="?", help="Paper-WorkFlow run workspace to validate")
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.workspace:
        result = evaluate_workspace(Path(args.workspace))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(render_report(result))
        return 0 if result["ok"] else 1

    result = evaluate_manifest(_load_json(CASES_PATH))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
