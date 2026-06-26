#!/usr/bin/env python3
"""Run adversarial Stage 0-9 scenario cases.

`check_stage_scenario.py` proves the golden path can be represented and
gate-checked. This companion proves common corruptions are rejected: missing
stage artifacts, stale handoff recovery, incomplete reset boundaries, stage logs
that omit required evidence, unreconciled result tables, non-final citations,
quality gates looser than method gates, and unfilled final delivery reports.

Usage:
    python3 scripts/check_stage_adversarial.py
    python3 scripts/check_stage_adversarial.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import check_stage_scenario


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "stage_adversarial_cases.json"
STATE_RELPATH = Path("00_meta/workflow_state.json")
KNOWN_MUTATIONS = {
    "delete_path",
    "replace_text",
    "set_latest_handoff",
    "remove_reset_boundary",
    "strip_log_artifact",
    "set_state_value",
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


def _clean_path(raw: str) -> Path:
    if not raw or raw.startswith("/") or ".." in Path(raw).parts:
        fail(f"invalid workspace-relative path in adversarial case: {raw!r}")
    return Path(raw)


def evaluate_manifest(data: dict) -> dict:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("base_contract") != "evals/stage_scenario_contract.json":
        errors.append("base_contract must point to evals/stage_scenario_contract.json")
    minimum = data.get("minimum_case_count")
    if not isinstance(minimum, int) or minimum < 1:
        errors.append("minimum_case_count must be a positive integer")
        minimum = 1

    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        cases = []
    if len(cases) < minimum:
        errors.append(f"expected at least {minimum} adversarial cases, found {len(cases)}")

    seen_ids: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{index}] must be an object")
            continue
        cid = case.get("id")
        if not isinstance(cid, str) or not cid.strip():
            errors.append(f"cases[{index}] missing non-empty id")
            cid = f"<missing-{index}>"
        if cid in seen_ids:
            errors.append(f"duplicate case id: {cid}")
        seen_ids.add(cid)

        if not isinstance(case.get("description"), str) or len(case["description"].strip()) < 40:
            errors.append(f"{cid}: description must explain the corruption")
        if not isinstance(case.get("expected_error"), str) or not case["expected_error"].strip():
            errors.append(f"{cid}: expected_error must be a non-empty string")

        mutation = case.get("mutation")
        if not isinstance(mutation, dict):
            errors.append(f"{cid}: mutation must be an object")
            continue
        mtype = mutation.get("type")
        if mtype not in KNOWN_MUTATIONS:
            errors.append(f"{cid}: unknown mutation type: {mtype!r}")
            continue
        if mtype in {"delete_path", "replace_text", "set_latest_handoff"}:
            path = mutation.get("path")
            if not isinstance(path, str):
                errors.append(f"{cid}: mutation.path must be a string")
            else:
                _clean_path(path)
        if mtype == "replace_text":
            if not isinstance(mutation.get("old"), str) or not mutation["old"]:
                errors.append(f"{cid}: replace_text.old must be non-empty")
            if not isinstance(mutation.get("new"), str):
                errors.append(f"{cid}: replace_text.new must be a string")
        if mtype in {"remove_reset_boundary", "strip_log_artifact"}:
            if not isinstance(mutation.get("stage"), int):
                errors.append(f"{cid}: mutation.stage must be an integer")
        if mtype == "strip_log_artifact" and not isinstance(mutation.get("artifact"), str):
            errors.append(f"{cid}: strip_log_artifact.artifact must be a string")
        if mtype == "set_state_value":
            path = mutation.get("path")
            if not isinstance(path, list) or not path or not all(isinstance(part, str) and part for part in path):
                errors.append(f"{cid}: set_state_value.path must be a non-empty string list")

    return {
        "ok": not errors,
        "errors": errors,
        "case_count": len(cases),
    }


def _load_state(workspace: Path) -> dict:
    return json.loads((workspace / STATE_RELPATH).read_text(encoding="utf-8"))


def _write_state(workspace: Path, state: dict) -> None:
    (workspace / STATE_RELPATH).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _apply_mutation(workspace: Path, contract: dict, case: dict) -> None:
    mutation = case["mutation"]
    mtype = mutation["type"]

    if mtype == "delete_path":
        target = workspace / _clean_path(mutation["path"])
        if not target.exists():
            fail(f"{case['id']}: target path does not exist before delete_path: {mutation['path']}")
        target.unlink()
        return

    if mtype == "replace_text":
        target = workspace / _clean_path(mutation["path"])
        text = target.read_text(encoding="utf-8")
        old = mutation["old"]
        if old not in text:
            fail(f"{case['id']}: replace_text.old not found in {mutation['path']!r}")
        target.write_text(text.replace(old, mutation["new"], 1), encoding="utf-8")
        return

    if mtype == "set_latest_handoff":
        state = _load_state(workspace)
        state["orchestration"]["latest_handoff"] = mutation["path"]
        _write_state(workspace, state)
        return

    if mtype == "remove_reset_boundary":
        state = _load_state(workspace)
        stage = mutation["stage"]
        state["orchestration"]["reset_boundaries"] = [
            item for item in state["orchestration"]["reset_boundaries"]
            if item.get("stage") != stage
        ]
        _write_state(workspace, state)
        return

    if mtype == "strip_log_artifact":
        stage = next((s for s in contract["stages"] if s["number"] == mutation["stage"]), None)
        if not stage:
            fail(f"{case['id']}: stage not found: {mutation['stage']}")
        log = workspace / stage["log"]
        text = log.read_text(encoding="utf-8")
        artifact = mutation["artifact"]
        if artifact not in text:
            fail(f"{case['id']}: artifact not found in stage log before strip: {artifact}")
        log.write_text(text.replace(artifact, "removed-artifact-reference", 1), encoding="utf-8")
        return

    if mtype == "set_state_value":
        state = _load_state(workspace)
        cursor = state
        parts = mutation["path"]
        for part in parts[:-1]:
            cursor = cursor[part]
        cursor[parts[-1]] = mutation.get("value")
        _write_state(workspace, state)
        return

    fail(f"{case['id']}: unsupported mutation type {mtype!r}")


def run_cases(manifest: dict) -> dict:
    manifest_result = evaluate_manifest(manifest)
    if not manifest_result["ok"]:
        return {
            "ok": False,
            "manifest": manifest_result,
            "cases": [],
            "caught": 0,
            "errors": manifest_result["errors"],
        }

    contract = _load_json(ROOT / manifest["base_contract"])
    contract_result = check_stage_scenario.evaluate_contract(contract)
    errors: list[str] = list(contract_result["errors"])
    case_results: list[dict] = []
    caught = 0

    with tempfile.TemporaryDirectory(prefix="stage-adversarial-") as tmp:
        base = Path(tmp)
        for case in manifest["cases"]:
            workspace = check_stage_scenario.build_workspace(base / case["id"], contract)
            clean = check_stage_scenario.evaluate_workspace(workspace, contract)
            if not clean["ok"]:
                errors.append(f"{case['id']}: clean base workspace failed before mutation: {clean['errors']}")
                case_results.append({"id": case["id"], "caught": False, "errors": clean["errors"]})
                continue

            _apply_mutation(workspace, contract, case)
            result = check_stage_scenario.evaluate_workspace(workspace, contract)
            blob = "\n".join(result["errors"])
            case_ok = (not result["ok"]) and case["expected_error"] in blob
            if case_ok:
                caught += 1
            else:
                errors.append(
                    f"{case['id']}: expected error fragment {case['expected_error']!r}; "
                    f"got ok={result['ok']} errors={result['errors']}"
                )
            case_results.append({"id": case["id"], "caught": case_ok, "errors": result["errors"]})

    return {
        "ok": not errors,
        "manifest": manifest_result,
        "cases": case_results,
        "caught": caught,
        "errors": errors,
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow adversarial Stage 0-9 scenarios",
        f"  cases: {result['manifest']['case_count']}",
        f"  caught: {result['caught']}",
    ]
    for case in result["cases"]:
        marker = "OK" if case["caught"] else "FAIL"
        lines.append(f"  [{marker}] {case['id']}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  ADVERSARIAL OK" if result["ok"] else "  ADVERSARIAL FAILED")
    return "\n".join(lines)


def _selftest() -> int:
    manifest = _load_json(CASES_PATH)
    assert evaluate_manifest(manifest)["ok"], "live adversarial manifest must pass schema checks"
    result = run_cases(manifest)
    assert result["ok"], result["errors"]

    bad = deepcopy(manifest)
    bad["cases"][0]["mutation"]["type"] = "unknown"
    assert not evaluate_manifest(bad)["ok"], "unknown mutation type must fail manifest validation"

    bad = deepcopy(manifest)
    bad["cases"][0]["expected_error"] = "this fragment should not be present"
    bad_result = run_cases(bad)
    assert not bad_result["ok"], "wrong expected_error must fail adversarial run"

    print("selftest OK: adversarial Stage 0-9 scenarios are caught")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    result = run_cases(_load_json(CASES_PATH))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
