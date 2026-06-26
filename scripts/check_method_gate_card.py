#!/usr/bin/env python3
"""Validate a workspace Method Gate's Design Gate Card.

`check_workspace_gates.py` verifies cheap state/file ordering invariants. This
checker reads the actual `03_analysis/method_gate.md` card so a workspace cannot
claim `method_gate.status=pass` while the card itself records missing artifacts,
failed rows, hit hard flags, placeholder paths, or a stronger claim level than
the card permits.

Usage:
    python3 scripts/check_method_gate_card.py <workspace>
    python3 scripts/check_method_gate_card.py <workspace> --json
    python3 scripts/check_method_gate_card.py --selftest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path


METHOD_GATE_RELPATH = "03_analysis/method_gate.md"
STATE_RELPATH = "00_meta/workflow_state.json"
CLAIM_ORDER = {
    "no_claim": 0,
    "exploratory": 1,
    "descriptive": 2,
    "qualified_causal": 3,
    "causal": 4,
}
BAD_ROW_VALUES = {"no", "n", "false", "fail", "failed", "not_pass", "missing", "hit", "blocking"}
BAD_HARD_FLAG_VALUES = {"hit", "blocking", "fail", "failed", "not_pass"}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _norm(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+\d*\.?\s*{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    next_match = re.search(r"^##\s+", text[match.end():], re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(text)
    return text[match.start():end]


def _parse_design_rows(text: str) -> list[dict[str, str]]:
    section = _section(text, "Design Gate Card")
    if not section:
        return []
    lines = section.splitlines()
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("| Gate item |"):
            header = [_norm(cell) for cell in _split_table_row(stripped)]
            in_table = True
            continue
        if not in_table:
            continue
        if stripped.startswith("|---"):
            continue
        if stripped.startswith("|") and stripped.endswith("|") and header:
            cells = _split_table_row(stripped)
            if len(cells) == len(header):
                rows.append(dict(zip(header, cells)))
            continue
        if rows:
            break
    return rows


def _parse_decision(text: str) -> str:
    match = re.search(r"^Decision:\s*(.+)$", text, re.MULTILINE)
    if not match:
        return ""
    raw = match.group(1).strip()
    if "/" in raw:
        return ""
    return _norm(raw)


def _parse_allowed_claim(text: str) -> str:
    match = re.search(r"Strongest allowed claim after this gate:\s*([A-Za-z_]+)", text)
    if match:
        return _norm(match.group(1))
    match = re.search(r"Allowed claim:\s*\n(?:- .+\n)*?- (Causal|Descriptive|Exploratory only):\s*(yes|no|true|false)", text, re.IGNORECASE)
    if match and _norm(match.group(2)) in {"yes", "true"}:
        label = _norm(match.group(1))
        return "exploratory" if label == "exploratory_only" else label
    return ""


def _parse_hard_flags(text: str) -> list[tuple[str, str]]:
    section = _section(text, "Hard Flags")
    flags: list[tuple[str, str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        val = _norm(value.split(";", 1)[0].split(",", 1)[0])
        flags.append((key.strip(), val))
    return flags


def _load_state(workspace: Path) -> dict:
    state_path = workspace / STATE_RELPATH
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"_error": f"{STATE_RELPATH} is not valid JSON: {exc}"}


def _path_exists(workspace: Path, raw: str) -> bool:
    path = raw.strip().split("#", 1)[0]
    if not path or "<" in path or ">" in path or "*" in path:
        return False
    if path.startswith("/"):
        return False
    if ".." in Path(path).parts:
        return False
    return (workspace / path).exists()


def validate_workspace(workspace: Path) -> list[str]:
    errors: list[str] = []
    gate_path = workspace / METHOD_GATE_RELPATH
    if not gate_path.exists():
        return [f"missing {METHOD_GATE_RELPATH}"]
    text = gate_path.read_text(encoding="utf-8")
    state = _load_state(workspace)
    if "_error" in state:
        errors.append(state["_error"])
        state = {}
    method = state.get("method_gate", {}) if isinstance(state.get("method_gate"), dict) else {}
    evidence = state.get("evidence_governance", {}) if isinstance(state.get("evidence_governance"), dict) else {}
    method_pass = _norm(method.get("status")) in {"pass", "passed"}
    decision = _parse_decision(text)

    if method_pass and decision != "pass":
        errors.append("method_gate.status=pass but method_gate.md Decision is not PASS")

    rows = _parse_design_rows(text)
    if method_pass and not rows:
        errors.append("method_gate.status=pass but Design Gate Card table has no rows")

    state_required = set(method.get("required_artifacts", []) if isinstance(method.get("required_artifacts"), list) else [])
    state_missing = method.get("missing_artifacts", []) if isinstance(method.get("missing_artifacts"), list) else []
    if method_pass and state_missing:
        errors.append(f"method_gate.status=pass but missing_artifacts is not empty: {state_missing}")

    substantive_rows = 0
    for index, row in enumerate(rows, start=1):
        gate_item = row.get("gate_item", "")
        required = row.get("required_artifact", "")
        path = row.get("path", "")
        present = _norm(row.get("present?", ""))
        passed = _norm(row.get("pass?", ""))
        consequence = _norm(row.get("claim_consequence", ""))
        placeholder = any("<" in cell and ">" in cell for cell in row.values())

        if placeholder:
            if method_pass:
                errors.append(f"row {index} is still a placeholder while method_gate.status=pass")
            continue
        substantive_rows += 1

        if method_pass and present in BAD_ROW_VALUES:
            errors.append(f"row {index} ({gate_item}) has Present?={row.get('present?')!r} while method_gate.status=pass")
        if method_pass and passed in BAD_ROW_VALUES:
            errors.append(f"row {index} ({gate_item}) has Pass?={row.get('pass?')!r} while method_gate.status=pass")
        if method_pass and not _path_exists(workspace, path):
            errors.append(f"row {index} ({gate_item}) path is missing or non-concrete: {path}")
        if method_pass and path and "*" not in path and "<" not in path and path not in state_required:
            errors.append(f"row {index} ({gate_item}) path is absent from workflow_state.method_gate.required_artifacts: {path}")
        if consequence and consequence not in CLAIM_ORDER:
            errors.append(f"row {index} ({gate_item}) has unknown claim consequence: {consequence}")

    if method_pass and substantive_rows == 0:
        errors.append("method_gate.status=pass but Design Gate Card has no substantive filled row")

    for key, value in _parse_hard_flags(text):
        if method_pass and value in BAD_HARD_FLAG_VALUES:
            errors.append(f"hard flag is {value} while method_gate.status=pass: {key}")

    allowed = _parse_allowed_claim(text)
    claim_strength = _norm(evidence.get("claim_strength"))
    if method_pass:
        if not allowed:
            errors.append("method_gate.status=pass but strongest allowed claim is not recorded")
        elif allowed not in CLAIM_ORDER:
            errors.append(f"unknown strongest allowed claim: {allowed}")
        elif claim_strength and claim_strength in CLAIM_ORDER and CLAIM_ORDER[claim_strength] > CLAIM_ORDER[allowed]:
            errors.append(
                f"evidence_governance.claim_strength={claim_strength} exceeds method gate allowed claim={allowed}"
            )
        elif claim_strength and claim_strength not in CLAIM_ORDER:
            errors.append(f"unknown evidence_governance.claim_strength: {claim_strength}")

    return errors


def render(errors: list[str]) -> str:
    lines = ["Paper-WorkFlow method gate card"]
    for error in errors:
        lines.append(f"  FAIL: {error}")
    lines.append("  METHOD GATE CARD OK" if not errors else "  METHOD GATE CARD FAILED")
    return "\n".join(lines)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _state(status: str = "pass", claim_strength: str = "qualified_causal") -> dict:
    return {
        "method_gate": {
            "status": status,
            "required_artifacts": [
                "02_data/sample_audit.md",
                "03_analysis/design_register.md",
                "03_analysis/results/event_study.csv",
            ],
            "missing_artifacts": [],
        },
        "evidence_governance": {"claim_strength": claim_strength},
    }


def _good_card() -> str:
    return """# Method Gate

## 3. Design Gate Card

Design card used: DiD

| Gate item | Required artifact | Path | Present? | Pass? | Claim consequence |
|---|---|---|---:|---:|---|
| Sample / estimand | Sample audit | 02_data/sample_audit.md | yes | yes | qualified_causal |
| Design register | Design register | 03_analysis/design_register.md | yes | yes | qualified_causal |
| Event study | Event-study plot/table | 03_analysis/results/event_study.csv | yes | yes | qualified_causal |

Claim Downgrade:

- Strongest allowed claim after this gate: qualified_causal

## 4. Hard Flags

- Parallel trends / exclusion / continuity / overlap: clear
- Bad-control risk: clear
- Inference level, weights, or clustering: clear

## 5. Decision

Decision: PASS
"""


def _build_workspace(root: Path, card: str, state: dict) -> Path:
    ws = root / "workspace"
    for rel in state["method_gate"]["required_artifacts"]:
        _write(ws / rel, "evidence\n")
    _write(ws / METHOD_GATE_RELPATH, card)
    _write(ws / STATE_RELPATH, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return ws


def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="method-gate-card-selftest-") as tmp:
        root = Path(tmp)
        good = _build_workspace(root / "good", _good_card(), _state())
        assert not validate_workspace(good), validate_workspace(good)

        bad = _build_workspace(
            root / "missing_row",
            _good_card().replace("| Event study | Event-study plot/table | 03_analysis/results/event_study.csv | yes | yes | qualified_causal |",
                                 "| Event study | Event-study plot/table | 03_analysis/results/event_study.csv | no | no | descriptive |"),
            _state(),
        )
        assert any("Present?" in e for e in validate_workspace(bad)), validate_workspace(bad)

        bad = _build_workspace(
            root / "hard_flag",
            _good_card().replace("- Bad-control risk: clear", "- Bad-control risk: hit"),
            _state(),
        )
        assert any("hard flag" in e for e in validate_workspace(bad)), validate_workspace(bad)

        bad = _build_workspace(root / "overclaim", _good_card(), _state(claim_strength="causal"))
        assert any("exceeds method gate allowed claim" in e for e in validate_workspace(bad)), validate_workspace(bad)

        bad_state = _state()
        bad_state["method_gate"]["required_artifacts"] = ["02_data/sample_audit.md"]
        bad = _build_workspace(root / "state_required", _good_card(), bad_state)
        assert any("absent from workflow_state.method_gate.required_artifacts" in e for e in validate_workspace(bad)), validate_workspace(bad)

        bad = _build_workspace(
            root / "placeholder",
            _good_card().replace(
                "| Event study | Event-study plot/table | 03_analysis/results/event_study.csv | yes | yes | qualified_causal |",
                "| <item> | <artifact> | <path> | no | no | no_claim |",
            ),
            _state(),
        )
        assert any("placeholder" in e for e in validate_workspace(bad)), validate_workspace(bad)

        pending = _build_workspace(
            root / "pending",
            _good_card().replace("Decision: PASS", "Decision: NOT PASS"),
            _state(status="not_pass", claim_strength="descriptive"),
        )
        assert not validate_workspace(pending), validate_workspace(pending)

    print("selftest OK: method-gate card invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="?", help="path to a Paper-WorkFlow workspace")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.workspace:
        parser.error("workspace path is required unless --selftest is passed")

    errors = validate_workspace(Path(args.workspace).expanduser().resolve())
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    else:
        print(render(errors))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
