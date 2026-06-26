#!/usr/bin/env python3
"""Validate the FINAL_REPORT template and optional filled reports.

The final handoff for a research workflow must be more than a prose summary. It
needs enough evidence for another maintainer, reviewer, or future agent to see
what changed, which commands ran, what failed, which risks remain, and whether
anything was pushed. This checker keeps that contract mechanical.

Usage:
    python3 scripts/check_final_report_contract.py
    python3 scripts/check_final_report_contract.py --selftest
    python3 scripts/check_final_report_contract.py <workspace>/FINAL_REPORT.md --filled
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "templates" / "FINAL_REPORT.md"

REQUIRED_HEADINGS = [
    "# Final Report",
    "## 1. Pipeline Summary",
    "## 2. Gate Results",
    "## 3. Deliverables",
    "## 4. Reproduction Command",
    "## 5. Validation Evidence",
    "## 6. Change / Commit Ledger",
    "## 7. Failures and Fixes",
    "## 8. Remote / Parity Status",
    "## 9. Residual Risks",
    "## 10. Next Actions",
]

REQUIRED_MARKERS = [
    "Commands run",
    "Result",
    "Evidence / notes",
    "Files changed",
    "Commit / SHA",
    "Change summary",
    "Failures encountered",
    "Fix / outcome",
    "Child repo status",
    "Parent repo status",
    "Remote / parity status",
    "No push requested",
    "Residual Risks",
    "Backend parity report",
]

REQUIRED_COMMANDS = [
    "python3 validate_skill.py",
    "python3 scripts/generate_rigor_report.py --check",
    "git diff --check",
    "make catalog",
    "make validate",
    "make check",
]

PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
UNRESOLVED_CHOICE_RE = re.compile(
    r"\b(?:PASS / NOT PASS|ready / not_ready|recorded / missing|current / stale / missing|"
    r"clear / restricted / blocked|pushed / not pushed / no push requested)\b"
)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")


def _heading_order_errors(text: str) -> list[str]:
    errors: list[str] = []
    pos = -1
    for heading in REQUIRED_HEADINGS:
        found = text.find(heading)
        if found < 0:
            errors.append(f"missing heading: {heading}")
            continue
        if found < pos:
            errors.append(f"heading out of order: {heading}")
        pos = found
    return errors


def evaluate(text: str, *, filled: bool = False) -> dict:
    errors = _heading_order_errors(text)

    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append(f"missing required marker: {marker}")

    for command in REQUIRED_COMMANDS:
        if command not in text:
            errors.append(f"missing validation/release command: {command}")

    if "| Command | Result | Evidence / notes |" not in text:
        errors.append("Validation Evidence must include the command/result/evidence table")
    if "| Commit / SHA | Files changed | Change summary |" not in text:
        errors.append("Change / Commit Ledger must include commit, file, and summary columns")
    if "| Scope | Status | Evidence / notes |" not in text:
        errors.append("Remote / Parity Status must include scope/status/evidence columns")

    if filled:
        placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
        if placeholders:
            errors.append("filled final report still contains placeholder(s): " + ", ".join(placeholders[:8]))
        unresolved = sorted(set(UNRESOLVED_CHOICE_RE.findall(text)))
        if unresolved:
            errors.append("filled final report still contains unresolved choice(s): " + ", ".join(unresolved))
        if "<command>" in text or "1. <action>" in text:
            errors.append("filled final report still contains template command/action placeholders")

    return {
        "ok": not errors,
        "errors": errors,
        "heading_count": len(REQUIRED_HEADINGS),
        "marker_count": len(REQUIRED_MARKERS),
        "command_count": len(REQUIRED_COMMANDS),
        "filled": filled,
    }


def render(result: dict) -> str:
    mode = "filled report" if result["filled"] else "template"
    lines = [
        f"Paper-WorkFlow FINAL_REPORT contract ({mode})",
        f"  headings checked: {result['heading_count']}",
        f"  markers checked: {result['marker_count']}",
        f"  commands checked: {result['command_count']}",
    ]
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  FINAL REPORT OK" if result["ok"] else "  FINAL REPORT FAILED")
    return "\n".join(lines)


def _good_report() -> str:
    return """# Final Report

Project: example
Completed at (Beijing): 2026-06-25 12:00
Workspace: paper_workspace/example

## 1. Pipeline Summary

| Stage | Status | Key outputs | Red flags / fallback |
|---|---|---|---|
| 0. Intake & setup | pass | 00_meta/workflow_state.json | none |

## 2. Gate Results

- Method gate: pass

## 3. Deliverables

| Deliverable | Path | Ready? |
|---|---|---:|
| Proposal | 01_proposal/proposal.md | yes |
| Backend parity report | 00_meta/backend_parity.json | yes |

## 4. Reproduction Command

```bash
bash run_all.sh
```

Last rebuild check: pass

## 5. Validation Evidence

Commands run:

| Command | Result | Evidence / notes |
|---|---|---|
| `python3 validate_skill.py` | PASS | child gate |
| `python3 scripts/generate_rigor_report.py --check` | PASS | rigor fresh |
| `git diff --check` | PASS | whitespace clean |
| `make catalog` | not in scope | parent not touched |
| `make validate` | not in scope | parent not touched |
| `make check` | not in scope | parent not touched |

## 6. Change / Commit Ledger

| Commit / SHA | Files changed | Change summary |
|---|---|---|
| no commit | scripts/check_x.py | local validation change |

## 7. Failures and Fixes

| Failures encountered | Fix / outcome | Follow-up |
|---|---|---|
| none | none | none |

## 8. Remote / Parity Status

| Scope | Status | Evidence / notes |
|---|---|---|
| Child repo status | clean | local only |
| Parent repo status | not in scope | no parent files changed |
| Remote / parity status | No push requested | no remote parity claim |

## 9. Residual Risks

- Identification: none
- Design risks / external validity: none

## 10. Next Actions

1. Continue monitoring.
"""


def _selftest() -> int:
    good = _good_report()
    assert evaluate(good)["ok"], "complete synthetic report template must pass"
    assert evaluate(good, filled=True)["ok"], "complete synthetic filled report must pass"

    bad = good.replace("## 5. Validation Evidence\n", "")
    assert not evaluate(bad)["ok"], "missing validation section must fail"

    bad = good.replace("make validate", "parent validation")
    assert not evaluate(bad)["ok"], "missing parent validation command must fail"

    bad = good.replace("Remote / parity status", "Remote status")
    assert not evaluate(bad)["ok"], "missing remote parity marker must fail"

    bad = good.replace("Project: example", "Project: <short name>")
    assert evaluate(bad)["ok"], "template placeholders are allowed in template mode"
    assert not evaluate(bad, filled=True)["ok"], "filled mode must reject placeholders"

    with tempfile.TemporaryDirectory(prefix="final-report-contract-") as tmp:
        path = Path(tmp) / "FINAL_REPORT.md"
        path.write_text(good, encoding="utf-8")
        assert evaluate(_read(path), filled=True)["ok"], "path read should validate"

    print("selftest OK: final-report contract invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", help="report path; defaults to templates/FINAL_REPORT.md")
    parser.add_argument("--filled", action="store_true", help="reject placeholders and unresolved choice lists")
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    path = Path(args.report) if args.report else TEMPLATE_PATH
    result = evaluate(_read(path), filled=args.filled)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
