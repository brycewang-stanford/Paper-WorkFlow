#!/usr/bin/env python3
"""Validate the design-gate-card maintenance contract.

The design gate cards are the reviewer-facing rules that keep method labels
honest. This checker makes the card surface mechanical: every contracted design
family must have a section, a substantive required-artifact table, hard-fail
conditions, allowed claim levels, and a matching label in the Method Gate
template. The cross-design behavioral guardrails G1-G10 must also remain present.

Usage:
    python3 scripts/check_design_gate_contract.py
    python3 scripts/check_design_gate_contract.py --selftest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "evals" / "design_gate_contract.json"


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


def _section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## \d+\. {re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    next_match = re.search(r"^## \d+\. ", text[match.end():], re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(text)
    return text[match.start():end]


def _required_artifact_rows(section: str) -> list[str]:
    lines = section.splitlines()
    rows: list[str] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("| Required artifact |"):
            in_table = True
            continue
        if not in_table:
            continue
        if stripped.startswith("|---"):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            rows.append(stripped)
            continue
        if rows:
            break
    return rows


def evaluate_manifest(data: dict) -> dict:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("source") != "references/design-gate-cards.md":
        errors.append("source must be references/design-gate-cards.md")
    if data.get("template") != "templates/method_gate.md":
        errors.append("template must be templates/method_gate.md")

    cards = data.get("design_cards")
    if not isinstance(cards, list) or not cards:
        errors.append("design_cards must be a non-empty list")
        cards = []
    minimum_design_count = data.get("minimum_design_count")
    if not isinstance(minimum_design_count, int) or minimum_design_count < 1:
        errors.append("minimum_design_count must be a positive integer")
        minimum_design_count = 1
    if len(cards) < minimum_design_count:
        errors.append(f"expected at least {minimum_design_count} design cards, found {len(cards)}")

    seen_ids: set[str] = set()
    seen_labels: set[str] = set()
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            errors.append(f"design_cards[{index}] must be an object")
            continue
        cid = card.get("id")
        if not isinstance(cid, str) or not cid.strip():
            errors.append(f"design_cards[{index}] missing id")
            cid = f"<missing-{index}>"
        if cid in seen_ids:
            errors.append(f"duplicate design card id: {cid}")
        seen_ids.add(cid)
        for field in ("heading", "method_gate_label"):
            if not isinstance(card.get(field), str) or not card[field].strip():
                errors.append(f"{cid}: {field} must be non-empty")
        label = card.get("method_gate_label")
        if isinstance(label, str):
            if label in seen_labels:
                errors.append(f"duplicate method gate label: {label}")
            seen_labels.add(label)
        minimum = card.get("minimum_required_artifacts")
        if not isinstance(minimum, int) or minimum < 1:
            errors.append(f"{cid}: minimum_required_artifacts must be positive")
            minimum = 1
        required_items = card.get("required_items")
        if not isinstance(required_items, list) or len(required_items) < minimum:
            errors.append(f"{cid}: required_items must have at least minimum_required_artifacts entries")
        elif len(set(required_items)) != len(required_items):
            errors.append(f"{cid}: required_items contains duplicates")
        levels = card.get("claim_levels")
        if not isinstance(levels, list) or "causal" not in levels:
            errors.append(f"{cid}: claim_levels must include causal")

    guardrails = data.get("behavioral_guardrails")
    minimum_guardrails = data.get("minimum_guardrail_count")
    if not isinstance(minimum_guardrails, int) or minimum_guardrails < 1:
        errors.append("minimum_guardrail_count must be positive")
        minimum_guardrails = 1
    if not isinstance(guardrails, list) or len(guardrails) < minimum_guardrails:
        errors.append(f"behavioral_guardrails must contain at least {minimum_guardrails} entries")
    elif guardrails != [f"G{i}" for i in range(1, len(guardrails) + 1)]:
        errors.append("behavioral_guardrails must be sequential G1..Gn")

    markers = data.get("required_template_markers")
    if not isinstance(markers, list) or not markers:
        errors.append("required_template_markers must be a non-empty list")

    return {
        "ok": not errors,
        "errors": errors,
        "design_count": len(cards),
        "guardrail_count": len(guardrails) if isinstance(guardrails, list) else 0,
    }


def evaluate_files(root: Path = ROOT, data: dict | None = None) -> dict:
    data = data or _load_json(CONTRACT_PATH)
    errors: list[str] = []
    source_path = root / data["source"]
    template_path = root / data["template"]
    if not source_path.exists():
        errors.append(f"source file missing: {data['source']}")
        source = ""
    else:
        source = source_path.read_text(encoding="utf-8")
    if not template_path.exists():
        errors.append(f"template file missing: {data['template']}")
        template = ""
    else:
        template = template_path.read_text(encoding="utf-8")

    for card in data.get("design_cards", []):
        cid = card["id"]
        section = _section(source, card["heading"])
        if not section:
            errors.append(f"{cid}: missing design-card section: {card['heading']}")
            continue
        rows = _required_artifact_rows(section)
        if len(rows) < card["minimum_required_artifacts"]:
            errors.append(
                f"{cid}: required-artifact table has {len(rows)} row(s), "
                f"expected at least {card['minimum_required_artifacts']}"
            )
        for item in card["required_items"]:
            if item not in section:
                errors.append(f"{cid}: missing required artifact item: {item}")
        if "**Hard fail**" not in section:
            errors.append(f"{cid}: missing Hard fail block")
        for level in card["claim_levels"]:
            if f"`{level}`" not in section:
                errors.append(f"{cid}: missing claim level marker: {level}")
        if card["method_gate_label"] not in template:
            errors.append(f"{cid}: method gate template missing label: {card['method_gate_label']}")

    guardrails_section = _section(source, "跨设计行为护栏（Behavioral Guardrails — 反模式黑名单）")
    if not guardrails_section:
        errors.append("missing cross-design behavioral guardrails section")
    for guardrail in data.get("behavioral_guardrails", []):
        if f"| {guardrail} |" not in guardrails_section:
            errors.append(f"missing behavioral guardrail row: {guardrail}")

    for marker in data.get("required_template_markers", []):
        if marker not in template and marker not in source:
            errors.append(f"missing required template/source marker: {marker}")

    return {
        "ok": not errors,
        "errors": errors,
        "design_count": len(data.get("design_cards", [])),
        "guardrail_count": len(data.get("behavioral_guardrails", [])),
    }


def render(manifest_result: dict, file_result: dict) -> str:
    lines = [
        "Paper-WorkFlow design gate contract",
        f"  design cards: {file_result['design_count']}",
        f"  behavioral guardrails: {file_result['guardrail_count']}",
    ]
    for error in manifest_result["errors"]:
        lines.append(f"  FAIL: {error}")
    for error in file_result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  DESIGN GATES OK" if manifest_result["ok"] and file_result["ok"] else "  DESIGN GATES FAILED")
    return "\n".join(lines)


def _selftest() -> int:
    data = _load_json(CONTRACT_PATH)
    assert evaluate_manifest(data)["ok"], "live design-gate manifest must pass schema checks"

    bad = deepcopy(data)
    bad["design_cards"][0]["required_items"] = ["Adoption/cohort table"]
    assert not evaluate_manifest(bad)["ok"], "too few required_items must fail"

    with tempfile.TemporaryDirectory(prefix="design-gate-selftest-") as tmp:
        root = Path(tmp)
        source = root / "references" / "design-gate-cards.md"
        template = root / "templates" / "method_gate.md"
        source.parent.mkdir(parents=True, exist_ok=True)
        template.parent.mkdir(parents=True, exist_ok=True)

        source_sections: list[str] = [
            "# Design Gate Cards\n",
            "## 10. 跨设计行为护栏（Behavioral Guardrails — 反模式黑名单）\n",
            "| # | guardrail |\n|---|---|\n",
            *[f"| G{i} | synthetic guardrail |\n" for i in range(1, 11)],
        ]
        for card in data["design_cards"]:
            rows = "\n".join(f"| {item} | `x` | answer |" for item in card["required_items"])
            levels = "\n".join(f"- `{level}`: ok" for level in card["claim_levels"])
            source_sections.append(
                f"\n## 1. {card['heading']}\n\n"
                "| Required artifact | Path pattern | Must answer |\n"
                "|---|---|---|\n"
                f"{rows}\n\n"
                "**Hard fail**\n\n- synthetic hard fail\n\n"
                "**允许 claim**\n\n"
                f"{levels}\n"
            )
        source.write_text("".join(source_sections), encoding="utf-8")
        template.write_text(
            "Design Gate Card\nDesign card used: "
            + " / ".join(card["method_gate_label"] for card in data["design_cards"])
            + "\nHard Flags\nClaim Downgrade\n"
            + "\n".join(data["required_template_markers"])
            + "\n",
            encoding="utf-8",
        )
        assert evaluate_files(root, data)["ok"], "synthetic complete docs must pass"

        broken = source.read_text(encoding="utf-8").replace("**Hard fail**", "**Soft warning**", 1)
        source.write_text(broken, encoding="utf-8")
        assert not evaluate_files(root, data)["ok"], "missing Hard fail block must fail"

    print("selftest OK: design-gate contract invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    data = _load_json(CONTRACT_PATH)
    manifest_result = evaluate_manifest(data)
    file_result = evaluate_files(ROOT, data)
    result = {
        "ok": manifest_result["ok"] and file_result["ok"],
        "manifest": manifest_result,
        "files": file_result,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(manifest_result, file_result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
