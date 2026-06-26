#!/usr/bin/env python3
"""Run method-specific Method Gate failure fixtures.

`check_method_gate_card.py` proves generic card/state consistency. This checker
adds method-specific held-out failures tied to `design_gate_contract.json` and
can require every contracted design family to have at least one failure fixture.

Usage:
    python3 scripts/check_method_specific_failures.py
    python3 scripts/check_method_specific_failures.py --selftest
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

import check_method_gate_card


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "method_failure_cases.json"
DESIGN_CONTRACT_PATH = ROOT / "evals" / "design_gate_contract.json"


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


def _slug(text: str) -> str:
    out = []
    for char in text.lower():
        out.append(char if char.isalnum() else "_")
    return "_".join("".join(out).split("_"))


def _design_cards(contract: dict) -> dict[str, dict]:
    cards = contract.get("design_cards")
    if not isinstance(cards, list):
        return {}
    return {card.get("id"): card for card in cards if isinstance(card, dict)}


def evaluate_manifest(data: dict, design_contract: dict) -> dict:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("design_gate_contract") != "evals/design_gate_contract.json":
        errors.append("design_gate_contract must point to evals/design_gate_contract.json")
    if data.get("checker") != "scripts/check_method_gate_card.py":
        errors.append("checker must be scripts/check_method_gate_card.py")
    require_all = data.get("require_all_design_cards")
    if require_all is not True:
        errors.append("require_all_design_cards must be true")
    minimum = data.get("minimum_case_count")
    if not isinstance(minimum, int) or minimum < 1:
        errors.append("minimum_case_count must be positive")
        minimum = 1
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("cases must be a non-empty list")
        cases = []
    if len(cases) < minimum:
        errors.append(f"expected at least {minimum} method failure cases, found {len(cases)}")

    cards = _design_cards(design_contract)
    seen: set[str] = set()
    covered_cards: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{index}] must be an object")
            continue
        cid = case.get("id")
        if not isinstance(cid, str) or not cid.strip():
            errors.append(f"cases[{index}] missing non-empty id")
            cid = f"<missing-{index}>"
        if cid in seen:
            errors.append(f"duplicate case id: {cid}")
        seen.add(cid)

        card_id = case.get("design_card_id")
        card = cards.get(card_id)
        if not card:
            errors.append(f"{cid}: unknown design_card_id: {card_id!r}")
            continue
        covered_cards.add(card_id)
        if case.get("method_gate_label") != card.get("method_gate_label"):
            errors.append(f"{cid}: method_gate_label does not match design contract")
        gate_item = case.get("gate_item")
        if not isinstance(gate_item, str) or gate_item not in card.get("required_items", []):
            errors.append(f"{cid}: gate_item must be one of the design card required_items")
        for field in ("bad_present", "bad_pass", "bad_claim_consequence", "hard_flag", "expected_error"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                errors.append(f"{cid}: {field} must be a non-empty string")

    missing_cards = sorted(set(cards) - covered_cards)
    if missing_cards:
        errors.append("missing method failure case(s) for design card(s): " + ", ".join(missing_cards))
    if minimum < len(cards):
        errors.append(f"minimum_case_count={minimum} must be at least design card count {len(cards)}")

    return {
        "ok": not errors,
        "errors": errors,
        "case_count": len(cases),
        "design_card_count": len(cards),
        "covered_design_card_count": len(covered_cards),
    }


def _path_for(item: str) -> str:
    return f"03_analysis/method_checks/{_slug(item)}.md"


def _state(card: dict) -> dict:
    required = ["02_data/sample_audit.md", "03_analysis/design_register.md"]
    required.extend(_path_for(item) for item in card["required_items"])
    return {
        "method_gate": {
            "status": "pass",
            "primary_design": card["method_gate_label"],
            "primary_estimator": "fixture estimator",
            "required_artifacts": required,
            "missing_artifacts": [],
        },
        "evidence_governance": {"status": "pass", "claim_strength": "qualified_causal"},
    }


def _card_text(card: dict, case: dict | None = None) -> str:
    rows = [
        ("Sample / estimand", "Sample audit", "02_data/sample_audit.md", "yes", "yes", "qualified_causal"),
        ("Design register", "Design register", "03_analysis/design_register.md", "yes", "yes", "qualified_causal"),
    ]
    for item in card["required_items"]:
        present = "yes"
        passed = "yes"
        consequence = "qualified_causal"
        if case and item == case["gate_item"]:
            present = case["bad_present"]
            passed = case["bad_pass"]
            consequence = case["bad_claim_consequence"]
        rows.append((item, item, _path_for(item), present, passed, consequence))

    table = "\n".join(
        f"| {item} | {artifact} | {path} | {present} | {passed} | {consequence} |"
        for item, artifact, path, present, passed, consequence in rows
    )
    hard_flag_value = "clear"
    hard_flag_label = "Parallel trends / exclusion / continuity / overlap"
    if case:
        hard_flag_label = case["hard_flag"]
        hard_flag_value = "hit"
    return f"""# Method Gate

## 3. Design Gate Card

Design card used: {card['method_gate_label']}

| Gate item | Required artifact | Path | Present? | Pass? | Claim consequence |
|---|---|---|---:|---:|---|
{table}

Claim Downgrade:

- Strongest allowed claim after this gate: qualified_causal

## 4. Hard Flags

- {hard_flag_label}: {hard_flag_value}
- Bad-control risk: clear
- Inference level, weights, or clustering: clear

## 5. Decision

Decision: PASS
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build_workspace(root: Path, card: dict, *, case: dict | None = None) -> Path:
    workspace = root / "workspace"
    state = _state(card)
    for rel in state["method_gate"]["required_artifacts"]:
        _write(workspace / rel, "fixture evidence\n")
    _write(workspace / "03_analysis" / "method_gate.md", _card_text(card, case))
    _write(workspace / "00_meta" / "workflow_state.json", json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return workspace


def run_cases(manifest: dict, design_contract: dict) -> dict:
    manifest_result = evaluate_manifest(manifest, design_contract)
    errors: list[str] = list(manifest_result["errors"])
    cards = _design_cards(design_contract)
    case_results: list[dict] = []
    caught = 0

    if not manifest_result["ok"]:
        return {
            "ok": False,
            "manifest": manifest_result,
            "cases": case_results,
            "caught": 0,
            "errors": errors,
        }

    with tempfile.TemporaryDirectory(prefix="method-specific-failures-") as tmp:
        base = Path(tmp)
        for case in manifest["cases"]:
            card = cards[case["design_card_id"]]
            good = _build_workspace(base / f"{case['id']}_good", card)
            good_errors = check_method_gate_card.validate_workspace(good)
            if good_errors:
                errors.append(f"{case['id']}: good {card['method_gate_label']} fixture failed: {good_errors}")
                case_results.append({"id": case["id"], "caught": False, "errors": good_errors})
                continue

            bad = _build_workspace(base / f"{case['id']}_bad", card, case=case)
            bad_errors = check_method_gate_card.validate_workspace(bad)
            blob = "\n".join(bad_errors)
            case_ok = bool(bad_errors) and case["expected_error"] in blob
            if case_ok:
                caught += 1
            else:
                errors.append(
                    f"{case['id']}: expected {case['expected_error']!r}; got errors={bad_errors}"
                )
            case_results.append({"id": case["id"], "caught": case_ok, "errors": bad_errors})

    return {
        "ok": not errors,
        "manifest": manifest_result,
        "cases": case_results,
        "caught": caught,
        "errors": errors,
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow method-specific failure fixtures",
        f"  cases: {result['manifest']['case_count']}",
        f"  design cards covered: {result['manifest']['covered_design_card_count']}/{result['manifest']['design_card_count']}",
        f"  caught: {result['caught']}",
    ]
    for case in result["cases"]:
        mark = "OK" if case["caught"] else "FAIL"
        lines.append(f"  [{mark}] {case['id']}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  METHOD-SPECIFIC FAILURES OK" if result["ok"] else "  METHOD-SPECIFIC FAILURES FAILED")
    return "\n".join(lines)


def _selftest() -> int:
    manifest = _load_json(CASES_PATH)
    design_contract = _load_json(DESIGN_CONTRACT_PATH)
    assert evaluate_manifest(manifest, design_contract)["ok"], "live method failure manifest must pass"
    assert run_cases(manifest, design_contract)["ok"], "live method failure cases must be caught"

    bad_manifest = deepcopy(manifest)
    bad_manifest["cases"][0]["gate_item"] = "Not in design contract"
    assert not evaluate_manifest(bad_manifest, design_contract)["ok"], "unknown gate item must fail"

    bad_manifest = deepcopy(manifest)
    bad_manifest["cases"] = [case for case in bad_manifest["cases"] if case["design_card_id"] != "time_series_var"]
    assert not evaluate_manifest(bad_manifest, design_contract)["ok"], "missing design-family coverage must fail"

    bad_manifest = deepcopy(manifest)
    bad_manifest["cases"][0]["expected_error"] = "not the actual error"
    assert not run_cases(bad_manifest, design_contract)["ok"], "wrong expected error must fail"

    print("selftest OK: method-specific failure fixtures are caught")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    result = run_cases(_load_json(CASES_PATH), _load_json(DESIGN_CONTRACT_PATH))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
