#!/usr/bin/env python3
"""Validate Chinese/English README parity for the user-facing surface.

The two READMEs are not translations line-for-line, but they must expose the
same operational contract: the same reference docs, the same script inventory,
the same local/parent validation commands, and the same load-bearing workflow
artifacts. This checker keeps the bilingual surface from drifting silently.

Usage:
    python3 scripts/check_bilingual_docs.py
    python3 scripts/check_bilingual_docs.py --selftest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ZH_README = ROOT / "README.md"
EN_README = ROOT / "README.en.md"

REFERENCE_RE = re.compile(r"references/[A-Za-z0-9_.-]+\.md")
SCRIPT_TREE_RE = re.compile(r"(?:├──|└──)\s+([A-Za-z0-9_]+\.py)")

REQUIRED_SHARED_MARKERS = [
    "Stage 0",
    "Stage 0-9",
    "workflow_state.json",
    "analysis_backend.md",
    "backend_parity.json",
    "sample_audit.md",
    "design_register.md",
    "method_gate.md",
    "design_risk_ledger.md",
    "evidence_ledger.md",
    "quality_scorecard.md",
    "claim_integrity_audit.md",
    "citation_integrity_log.md",
    "data_governance.md",
    "REPLICATION.md",
    "DAS.md",
    "run_all.sh",
    "did_demo.ipynb",
    "RIGOR.md",
    "contract_matrix.json",
    "design_gate_contract.json",
    "method_failure_cases.json",
    "stage_scenario_contract.json",
    "stage_adversarial_cases.json",
    "backend_parity_cases.json",
    "check_backend_parity.py",
    "check_method_specific_failures.py",
    "check_method_gate_card.py",
    "check_runtime_fallbacks.py",
    "check_reproducibility_scaffold.py",
    "check_monthly_worklog.py",
    "check_rigor_registry.py",
    "check_bilingual_docs.py",
    "check_final_report_contract.py",
    "validate_skill.py",
    "scripts/smoke_workspace.py",
    "scripts/check_skillopt_packet.py --selftest",
    "python3 validate_skill.py",
    "make catalog",
    "make validate",
    "make check",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _normalise(text: str) -> str:
    return (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("×", "x")
        .replace("\u00a0", " ")
    )


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")


def _references(text: str) -> set[str]:
    return set(REFERENCE_RE.findall(text))


def _script_tree(text: str) -> set[str]:
    lines = text.splitlines()
    in_scripts = False
    scripts: set[str] = set()
    for line in lines:
        if "├── scripts/" in line or "scripts/" == line.strip():
            in_scripts = True
            continue
        if in_scripts and "├── evals/" in line:
            break
        if not in_scripts:
            continue
        match = SCRIPT_TREE_RE.search(line)
        if match:
            scripts.add(f"scripts/{match.group(1)}")
    return scripts


def evaluate(zh_text: str, en_text: str) -> dict:
    errors: list[str] = []
    zh_norm = _normalise(zh_text)
    en_norm = _normalise(en_text)

    if "README.en.md" not in zh_norm:
        errors.append("README.md must link to README.en.md")
    if "README.md" not in en_norm:
        errors.append("README.en.md must link to README.md")

    zh_refs = _references(zh_norm)
    en_refs = _references(en_norm)
    if zh_refs != en_refs:
        missing_en = sorted(zh_refs - en_refs)
        missing_zh = sorted(en_refs - zh_refs)
        if missing_en:
            errors.append("README.en.md missing reference link(s): " + ", ".join(missing_en))
        if missing_zh:
            errors.append("README.md missing reference link(s): " + ", ".join(missing_zh))

    zh_scripts = _script_tree(zh_norm)
    en_scripts = _script_tree(en_norm)
    if not zh_scripts or not en_scripts:
        errors.append("both READMEs must include a repository-layout scripts tree")
    if zh_scripts != en_scripts:
        missing_en = sorted(zh_scripts - en_scripts)
        missing_zh = sorted(en_scripts - zh_scripts)
        if missing_en:
            errors.append("README.en.md missing script-tree item(s): " + ", ".join(missing_en))
        if missing_zh:
            errors.append("README.md missing script-tree item(s): " + ", ".join(missing_zh))

    for marker in REQUIRED_SHARED_MARKERS:
        marker_norm = _normalise(marker)
        if marker_norm not in zh_norm:
            errors.append(f"README.md missing shared marker: {marker}")
        if marker_norm not in en_norm:
            errors.append(f"README.en.md missing shared marker: {marker}")

    return {
        "ok": not errors,
        "errors": errors,
        "reference_count": len(zh_refs | en_refs),
        "script_count": len(zh_scripts | en_scripts),
        "marker_count": len(REQUIRED_SHARED_MARKERS),
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow bilingual README parity",
        f"  reference links checked: {result['reference_count']}",
        f"  script-tree items checked: {result['script_count']}",
        f"  shared markers checked: {result['marker_count']}",
    ]
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  BILINGUAL DOCS OK" if result["ok"] else "  BILINGUAL DOCS FAILED")
    return "\n".join(lines)


def _good_readmes() -> tuple[str, str]:
    refs = "\n".join(
        f"- [ref](references/ref{i}.md)"
        for i in range(3)
    )
    scripts = """```text
Paper-WorkFlow/
├── scripts/
│   ├── check_a.py
│   ├── check_b.py
│   └── generate_rigor_report.py
├── evals/
```
"""
    markers = "\n".join(REQUIRED_SHARED_MARKERS)
    zh = f"中文 README.en.md\n{refs}\n{scripts}\n{markers}\n"
    en = f"English README.md\n{refs}\n{scripts}\n{markers}\n"
    return zh, en


def _selftest() -> int:
    zh, en = _good_readmes()
    assert evaluate(zh, en)["ok"], "complete synthetic bilingual surface must pass"

    bad_en = en.replace("references/ref1.md", "references/other.md")
    assert not evaluate(zh, bad_en)["ok"], "reference drift must fail"

    bad_en = en.replace("│   ├── check_b.py\n", "")
    assert not evaluate(zh, bad_en)["ok"], "script-tree drift must fail"

    bad_en = en.replace("make validate", "")
    assert not evaluate(zh, bad_en)["ok"], "missing shared marker must fail"

    bad_zh = zh.replace("README.en.md", "")
    assert not evaluate(bad_zh, en)["ok"], "missing counterpart link must fail"

    print("selftest OK: bilingual README parity invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    result = evaluate(_read(ZH_README), _read(EN_README))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
