#!/usr/bin/env python3
"""Validate the month-long quality-goal worklog.

The worklog is part of the maintenance surface for this repo, not an informal
note. This checker makes the long-horizon goal auditable: it verifies the goal
window, baseline evidence, week plan, packet structure, PASS evidence, and the
anti-cheat rule that the goal must not be closed before 2026-07-26.

Usage:
    python3 scripts/check_monthly_worklog.py
    python3 scripts/check_monthly_worklog.py --selftest
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKLOG_PATH = ROOT / "worklogs" / "2026-06-25-month-long-quality-goal.md"
GOAL_NOT_BEFORE = "2026-07-26"
MIN_PACKET_COUNT = 5

REQUIRED_TOP_SECTIONS = [
    "## Goal contract",
    "## Baseline audit",
    "## Month plan",
    "## Running evidence log",
    "## Anti-cheat",
]
REQUIRED_WEEK_HEADINGS = [
    "### Week 0 / setup and measurement",
    "### Week 1 / workflow-state contract hardening",
    "### Week 2 / reproducibility and example evidence",
    "### Week 3 / docs and bilingual consistency",
    "### Week 4 / maintainer governance and release readiness",
]
REQUIRED_BASELINE_COMMANDS = [
    "python3 validate_skill.py",
    "python3 scripts/generate_rigor_report.py --check",
    "git diff --check",
]
REQUIRED_PACKET_LABELS = [
    "Files changed:",
    "Invariant strengthened:",
    "Remaining risk:",
]

PACKET_RE = re.compile(r"^### (?P<date>\d{4}-\d{2}-\d{2}) Packet (?P<packet>[0-9A-Z]+) .+$", re.MULTILINE)
VALIDATION_RE = re.compile(r"^Validation(?: to run)?:$", re.MULTILINE)
FORBIDDEN_MARKER_RE = re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")


def _packet_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(PACKET_RE.finditer(text))
    packets: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        candidates: list[int] = []
        if index + 1 < len(matches):
            candidates.append(matches[index + 1].start())
        next_top = re.search(r"^## ", text[match.end():], re.MULTILINE)
        if next_top:
            candidates.append(match.end() + next_top.start())
        end = min(candidates) if candidates else len(text)
        packets.append((match.group(0).strip(), text[match.start():end]))
    return packets


def evaluate(text: str, *, min_packet_count: int = MIN_PACKET_COUNT) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if "# Worklog" not in text or "Month-long repo quality goal" not in text:
        errors.append("worklog title must identify the month-long repo quality goal")

    if f"Goal window: do not close before {GOAL_NOT_BEFORE}." not in text:
        errors.append(f"goal window must state do not close before {GOAL_NOT_BEFORE}")

    for heading in REQUIRED_TOP_SECTIONS:
        if heading not in text:
            errors.append(f"missing top-level section: {heading}")

    for heading in REQUIRED_WEEK_HEADINGS:
        if heading not in text:
            errors.append(f"missing month-plan heading: {heading}")

    for command in REQUIRED_BASELINE_COMMANDS:
        pattern = re.compile(rf"- `{re.escape(command)}` -> PASS\b")
        if not pattern.search(text):
            errors.append(f"baseline command is missing PASS evidence: {command}")

    anti_cheat_start = text.find("## Anti-cheat")
    anti_cheat = text[anti_cheat_start:] if anti_cheat_start >= 0 else ""
    if f"Do not mark the month goal complete before {GOAL_NOT_BEFORE}" not in anti_cheat:
        errors.append(f"anti-cheat section must forbid completion before {GOAL_NOT_BEFORE}")
    for phrase in [
        "Do not delete, skip, or relax validators",
        "Do not leave generated rigor/catalog outputs stale",
        "Do not touch unrelated sibling skills or parent files",
    ]:
        if phrase not in anti_cheat:
            errors.append(f"anti-cheat section missing guardrail: {phrase}")

    packets = _packet_blocks(text)
    if len(packets) < min_packet_count:
        errors.append(f"expected at least {min_packet_count} packet evidence sections, found {len(packets)}")

    seen_headings: set[str] = set()
    for heading, block in packets:
        if heading in seen_headings:
            errors.append(f"duplicate packet heading: {heading}")
        seen_headings.add(heading)

        for label in REQUIRED_PACKET_LABELS:
            if label not in block:
                errors.append(f"{heading}: missing required subsection: {label}")

        if not VALIDATION_RE.search(block):
            errors.append(f"{heading}: missing Validation or Validation to run subsection")
        if "-> PASS" not in block:
            errors.append(f"{heading}: validation subsection must contain at least one PASS command")
        if not re.search(r"- `[^`]+`", block):
            errors.append(f"{heading}: Files changed should list concrete repo paths")

        unresolved = sorted({m.group(0).upper() for m in FORBIDDEN_MARKER_RE.finditer(block)})
        if unresolved:
            errors.append(f"{heading}: unresolved marker(s) in packet evidence: {', '.join(unresolved)}")

    if len(packets) == min_packet_count:
        warnings.append("packet count is exactly at the minimum; keep appending dated evidence")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "packet_count": len(packets),
        "goal_not_before": GOAL_NOT_BEFORE,
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow monthly worklog",
        f"  goal window: not before {result['goal_not_before']}",
        f"  packets: {result['packet_count']}",
    ]
    for warning in result["warnings"]:
        lines.append(f"  WARN: {warning}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  WORKLOG OK" if result["ok"] else "  WORKLOG FAILED")
    return "\n".join(lines)


def _packet(number: str) -> str:
    return f"""### 2026-06-25 Packet {number} -- Synthetic packet

Files changed:

- `scripts/example.py`

Invariant strengthened:

- The synthetic packet records a bounded invariant with executable evidence.

Validation:

- `python3 validate_skill.py` -> PASS

Remaining risk:

- Synthetic fixture only.
"""


def _good_worklog() -> str:
    packets = "\n".join(_packet(str(i)) for i in range(1, 6))
    return f"""# Worklog -- Month-long repo quality goal

Start: 2026-06-25 18:47 PDT
Goal window: do not close before {GOAL_NOT_BEFORE}.

## Goal contract

Raise the repo quality across workflow, validators, reproducibility, docs, and governance.

## Baseline audit

- `python3 validate_skill.py` -> PASS
- `python3 scripts/generate_rigor_report.py --check` -> PASS
- `git diff --check` -> PASS

## Month plan

### Week 0 / setup and measurement
### Week 1 / workflow-state contract hardening
### Week 2 / reproducibility and example evidence
### Week 3 / docs and bilingual consistency
### Week 4 / maintainer governance and release readiness

## Running evidence log

{packets}

## Anti-cheat

- Do not mark the month goal complete before {GOAL_NOT_BEFORE}.
- Do not delete, skip, or relax validators to get a green run.
- Do not leave generated rigor/catalog outputs stale.
- Do not touch unrelated sibling skills or parent files unless needed.
"""


def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="monthly-worklog-selftest-") as tmp:
        root = Path(tmp)
        good_path = root / "worklog.md"
        good = _good_worklog()
        good_path.write_text(good, encoding="utf-8")
        assert evaluate(_read(good_path))["ok"], "complete synthetic worklog must pass"

        bad = good.replace("Goal window: do not close before 2026-07-26.", "Goal window: open.")
        assert not evaluate(bad)["ok"], "missing goal window must fail"

        bad = good.replace("- `git diff --check` -> PASS", "- `git diff --check` -> FAIL")
        assert not evaluate(bad)["ok"], "baseline PASS evidence must be required"

        bad = good.replace("Validation:\n\n- `python3 validate_skill.py` -> PASS", "Validation:\n\n- `python3 validate_skill.py` -> FAIL", 1)
        assert not evaluate(bad)["ok"], "packet PASS evidence must be required"

        bad = good.replace("Synthetic fixture only.", "TODO: fill this in.", 1)
        assert not evaluate(bad)["ok"], "unresolved markers must fail"

    print("selftest OK: monthly-worklog invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    result = evaluate(_read(WORKLOG_PATH))
    if args.json:
        import json

        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
