#!/usr/bin/env python3
"""Validate the Paper-WorkFlow maintenance contract matrix.

The month-long hardening lane needs a compact way to say which repo artifacts
own which invariants. A markdown checklist can drift silently; this checker
keeps the matrix mechanical:

- every contract has an id, theme, invariant, owner files, validators, and docs;
- every path in the matrix exists inside this repo;
- every `scripts/check_*.py` and `evals/check_*.py` checker is claimed by at
  least one contract;
- the declared themes cover the month-goal quality dimensions;
- required high-leverage files are covered by at least one contract;
- every contract has at least one executable validator.

Usage:
    python3 scripts/check_contract_matrix.py
    python3 scripts/check_contract_matrix.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "evals" / "contract_matrix.json"
REQUIRED_THEMES = {
    "workflow_contract_state",
    "runtime_validators_evals",
    "reproducibility_examples",
    "bilingual_user_docs",
    "maintainer_governance_release",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_matrix(path: Path = MATRIX_PATH) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
    if not isinstance(data, dict):
        fail("contract matrix root must be an object")
    return data


def _clean_path(raw: str) -> Path:
    if not raw or raw.startswith("/") or ".." in Path(raw).parts:
        fail(f"invalid repo-relative path in contract matrix: {raw!r}")
    return Path(raw)


def _path_exists(root: Path, rel: str) -> bool:
    return (root / _clean_path(rel)).exists()


def evaluate(data: dict, root: Path = ROOT) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    covered_paths: set[str] = set()

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    contracts = data.get("contracts")
    if not isinstance(contracts, list) or not contracts:
        errors.append("contracts must be a non-empty list")
        contracts = []

    seen_ids: set[str] = set()
    themes: set[str] = set()

    for index, contract in enumerate(contracts):
        if not isinstance(contract, dict):
            errors.append(f"contract[{index}] must be an object")
            continue
        cid = contract.get("id")
        if not isinstance(cid, str) or not cid.strip():
            errors.append(f"contract[{index}] missing non-empty id")
            cid = f"<missing-{index}>"
        if cid in seen_ids:
            errors.append(f"duplicate contract id: {cid}")
        seen_ids.add(cid)

        theme = contract.get("theme")
        if not isinstance(theme, str) or not theme.strip():
            errors.append(f"{cid}: missing non-empty theme")
        else:
            themes.add(theme)

        invariant = contract.get("invariant")
        if not isinstance(invariant, str) or len(invariant.strip()) < 40:
            errors.append(f"{cid}: invariant must be a substantive sentence")

        for field in ("owner_files", "validators", "docs"):
            values = contract.get(field)
            if not isinstance(values, list) or not values:
                errors.append(f"{cid}: {field} must be a non-empty list")
                continue
            for value in values:
                if not isinstance(value, str):
                    errors.append(f"{cid}: {field} contains a non-string path")
                    continue
                try:
                    rel = str(_clean_path(value))
                except SystemExit:
                    raise
                covered_paths.add(rel)
                if not _path_exists(root, rel):
                    errors.append(f"{cid}: {field} path does not exist: {rel}")

        validators = contract.get("validators", [])
        if isinstance(validators, list):
            executable = [
                v for v in validators
                if isinstance(v, str)
                and (v.endswith(".py") or v.endswith(".sh") or v == "validate_skill.py")
            ]
            if not executable:
                errors.append(f"{cid}: validators must include at least one executable checker/script")

    missing_themes = REQUIRED_THEMES - themes
    if missing_themes:
        errors.append("missing required theme coverage: " + ", ".join(sorted(missing_themes)))

    min_theme_count = data.get("minimum_theme_count", len(REQUIRED_THEMES))
    if not isinstance(min_theme_count, int) or min_theme_count < len(REQUIRED_THEMES):
        errors.append("minimum_theme_count must be an integer at least the required theme count")
    elif len(themes) < min_theme_count:
        errors.append(f"only {len(themes)} theme(s) covered; required {min_theme_count}")

    required_paths = data.get("required_paths", [])
    if not isinstance(required_paths, list):
        errors.append("required_paths must be a list")
        required_paths = []
    for raw in required_paths:
        if not isinstance(raw, str):
            errors.append("required_paths contains a non-string path")
            continue
        rel = str(_clean_path(raw))
        if not _path_exists(root, rel):
            errors.append(f"required path does not exist: {rel}")
        if rel not in covered_paths:
            errors.append(f"required path is not covered by any contract: {rel}")

    discovered_checkers = sorted(
        str(path.relative_to(root))
        for folder in ("scripts", "evals")
        for path in (root / folder).glob("check_*.py")
    )
    for rel in discovered_checkers:
        if rel not in covered_paths:
            errors.append(f"checker is not covered by any contract: {rel}")

    if len(contracts) < len(REQUIRED_THEMES):
        warnings.append("fewer contracts than themes; consider splitting overloaded contracts")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "contract_count": len(contracts),
        "theme_count": len(themes),
        "themes": sorted(themes),
        "covered_path_count": len(covered_paths),
        "discovered_checker_count": len(discovered_checkers),
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow contract matrix",
        f"  contracts: {result['contract_count']}",
        f"  themes: {result['theme_count']} ({', '.join(result['themes'])})",
        f"  covered paths: {result['covered_path_count']}",
        f"  discovered checkers covered: {result['discovered_checker_count']}",
    ]
    for warning in result["warnings"]:
        lines.append(f"  WARN: {warning}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  MATRIX OK" if result["ok"] else "  MATRIX FAILED")
    return "\n".join(lines)


def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="contract-matrix-selftest-") as tmp:
        root = Path(tmp)
        for rel in [
            "SKILL.md",
            "README.md",
            "README.en.md",
            "assets/init_workspace.sh",
            "scripts/check_workspace_gates.py",
            "scripts/check_preregistration.py",
            "references/workspace-and-state.md",
            "templates/run_all.sh",
            "validate_skill.py",
        ]:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x\n", encoding="utf-8")

        good = {
            "schema_version": 1,
            "minimum_theme_count": 5,
            "required_paths": ["SKILL.md", "README.md", "assets/init_workspace.sh"],
            "contracts": [
                {
                    "id": "c1",
                    "theme": "workflow_contract_state",
                    "invariant": "A substantive invariant that is long enough to be useful.",
                    "owner_files": ["assets/init_workspace.sh"],
                    "validators": ["validate_skill.py"],
                    "docs": ["references/workspace-and-state.md"],
                },
                {
                    "id": "c2",
                    "theme": "runtime_validators_evals",
                    "invariant": "A substantive invariant that is long enough to be useful.",
                    "owner_files": ["scripts/check_workspace_gates.py", "scripts/check_preregistration.py"],
                    "validators": ["scripts/check_workspace_gates.py"],
                    "docs": ["SKILL.md"],
                },
                {
                    "id": "c3",
                    "theme": "reproducibility_examples",
                    "invariant": "A substantive invariant that is long enough to be useful.",
                    "owner_files": ["templates/run_all.sh"],
                    "validators": ["validate_skill.py"],
                    "docs": ["README.md"],
                },
                {
                    "id": "c4",
                    "theme": "bilingual_user_docs",
                    "invariant": "A substantive invariant that is long enough to be useful.",
                    "owner_files": ["README.md", "README.en.md"],
                    "validators": ["validate_skill.py"],
                    "docs": ["README.en.md"],
                },
                {
                    "id": "c5",
                    "theme": "maintainer_governance_release",
                    "invariant": "A substantive invariant that is long enough to be useful.",
                    "owner_files": ["SKILL.md"],
                    "validators": ["validate_skill.py"],
                    "docs": ["SKILL.md"],
                },
            ],
        }
        assert evaluate(good, root)["ok"], "complete synthetic matrix must pass"

        bad = json.loads(json.dumps(good))
        bad["contracts"][0]["owner_files"] = ["missing.md"]
        assert not evaluate(bad, root)["ok"], "missing owner file must fail"

        bad = json.loads(json.dumps(good))
        bad["contracts"][1]["owner_files"] = ["scripts/check_workspace_gates.py"]
        assert not evaluate(bad, root)["ok"], "unclaimed discovered checker must fail"

        bad = json.loads(json.dumps(good))
        bad["contracts"][1]["theme"] = "workflow_contract_state"
        assert not evaluate(bad, root)["ok"], "missing theme coverage must fail"

        bad = json.loads(json.dumps(good))
        bad["required_paths"].append("README.en.md")
        bad["contracts"][3]["owner_files"] = ["README.md"]
        bad["contracts"][3]["docs"] = ["README.md"]
        assert not evaluate(bad, root)["ok"], "uncovered required path must fail"

    print("selftest OK: contract-matrix invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    result = evaluate(load_matrix())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
