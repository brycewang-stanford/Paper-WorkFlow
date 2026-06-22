#!/usr/bin/env python3
"""Validate a SkillOpt-style improvement packet for Paper-WorkFlow.

The checker is intentionally mechanical. It does not judge the quality of the
skill edit; it catches common process failures before a maintenance patch is
treated as evidence-backed:

  - no held-out selection cases;
  - accepted candidate score is not better than baseline;
  - regression check failed;
  - proposed edit count exceeds the declared budget;
  - placeholders are still present.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = [
    "Candidate",
    "Rollout Split",
    "Reflection",
    "Proposed Bounded Patch",
    "Gate Decision",
    "Adoption Record",
]

PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|PLACEHOLDER|REPLACE_ME)\b|<[^>\n]+>")
SCORE_RE = re.compile(r"score\s*=\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
EDIT_LINE_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s*edit[_-]?\d+\b", re.MULTILINE)


class PacketError(Exception):
    """Raised for packet validation failures."""


def _heading_block(text: str, heading: str, level: int = 2) -> str:
    hashes = "#" * level
    pattern = re.compile(
        rf"^{re.escape(hashes)}\s+{re.escape(heading)}\s*$"
        rf"(?P<body>.*?)"
        rf"(?=^{re.escape(hashes)}\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        raise PacketError(f"missing heading: {hashes} {heading}")
    return match.group("body").strip()


def _subheading_block(section: str, heading: str) -> str:
    pattern = re.compile(
        rf"^###\s+{re.escape(heading)}\s*$"
        rf"(?P<body>.*?)"
        rf"(?=^###\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(section)
    if not match:
        raise PacketError(f"missing subheading: ### {heading}")
    return match.group("body").strip()


def _parse_int(label: str, text: str) -> int:
    match = re.search(rf"{re.escape(label)}\s*:\s*(\d+)", text, re.IGNORECASE)
    if not match:
        raise PacketError(f"missing integer field: {label}")
    return int(match.group(1))


def _parse_score(label: str, text: str) -> float:
    match = re.search(
        rf"{re.escape(label)}\s*:\s*([0-9]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE,
    )
    if not match:
        raise PacketError(f"missing score field: {label}")
    return float(match.group(1))


def _parse_choice(label: str, choices: set[str], text: str) -> str:
    match = re.search(rf"{re.escape(label)}\s*:\s*([A-Za-z_-]+)", text, re.IGNORECASE)
    if not match:
        raise PacketError(f"missing choice field: {label}")
    value = match.group(1).strip().lower().replace("_", "-")
    normalized = {c.lower().replace("_", "-") for c in choices}
    if value not in normalized:
        raise PacketError(f"{label} must be one of {sorted(choices)}, got {match.group(1)!r}")
    return value


def _rollout_count(block: str) -> int:
    count = 0
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ["):
            continue
        if "evidence=" not in stripped or not SCORE_RE.search(stripped):
            continue
        count += 1
    return count


def validate_packet(text: str) -> list[str]:
    errors: list[str] = []

    if "# SkillOpt Improvement Packet" not in text:
        errors.append("missing title: # SkillOpt Improvement Packet")

    for heading in REQUIRED_HEADINGS:
        try:
            _heading_block(text, heading)
        except PacketError as exc:
            errors.append(str(exc))

    if PLACEHOLDER_RE.search(text):
        errors.append("packet still contains placeholders such as <...>, TBD, TODO, or REPLACE_ME")

    try:
        candidate = _heading_block(text, "Candidate")
        budget = _parse_int("Edit budget L", candidate)
        if budget < 0 or budget > 8:
            errors.append("Edit budget L must be between 0 and 8")
    except PacketError as exc:
        errors.append(str(exc))
        budget = 0

    try:
        split = _heading_block(text, "Rollout Split")
        train = _subheading_block(split, "Train rollouts")
        selection = _subheading_block(split, "Held-out selection rollouts")
        train_count = _rollout_count(train)
        selection_count = _rollout_count(selection)
        if train_count < 3:
            errors.append(f"need at least 3 train rollouts, found {train_count}")
        if selection_count < 2:
            errors.append(f"need at least 2 held-out selection rollouts, found {selection_count}")
    except PacketError as exc:
        errors.append(str(exc))

    try:
        patch = _heading_block(text, "Proposed Bounded Patch")
        edit_count = len(EDIT_LINE_RE.findall(patch))
        if edit_count > budget:
            errors.append(f"proposed edit count {edit_count} exceeds edit budget L={budget}")
    except PacketError as exc:
        errors.append(str(exc))
        edit_count = 0

    try:
        gate = _heading_block(text, "Gate Decision")
        baseline = _parse_score("Baseline selection score", gate)
        candidate_score = _parse_score("Candidate selection score", gate)
        decision = _parse_choice("Gate decision", {"accept", "reject"}, gate)
        regression = _parse_choice("Regression check", {"pass", "fail"}, gate)
        if decision == "accept":
            if candidate_score <= baseline:
                errors.append(
                    f"accept requires candidate score > baseline, got {candidate_score} <= {baseline}"
                )
            if regression != "pass":
                errors.append("accept requires Regression check: pass")
            if edit_count == 0:
                errors.append("accept requires at least one proposed edit")
    except PacketError as exc:
        errors.append(str(exc))

    return errors


def _selftest() -> int:
    good = """# SkillOpt Improvement Packet

## Candidate

- Target skill files: SKILL.md
- Source SkillOpt snapshot: https://github.com/microsoft/SkillOpt fc1f827
- Change scope: add a bounded update gate
- Edit budget L: 2
- Protected areas: parent repo catalog

## Rollout Split

### Train rollouts

- [ ] train-001 | status=failure | score=0.30 | evidence=logs/a.md | note=route failed
- [ ] train-002 | status=success | score=0.80 | evidence=logs/b.md | note=gate held
- [ ] train-003 | status=failure | score=0.40 | evidence=logs/c.md | note=context leak

### Held-out selection rollouts

- [ ] select-001 | status=success | score=0.70 | evidence=logs/d.md | note=route fixed
- [ ] select-002 | status=success | score=0.75 | evidence=logs/e.md | note=gate fixed

## Reflection

### Failure patterns

- Maintenance edits lacked held-out checks.

### Success patterns

- Existing mechanical validators caught schema drift.

## Proposed Bounded Patch

- [ ] edit_1 | op=append | target=SKILL.md#constraints | rationale=add held-out gate
- [ ] edit_2 | op=append | target=validate_skill.py | rationale=check packet process

## Gate Decision

- Baseline selection score: 0.62
- Candidate selection score: 0.70
- Gate decision: accept
- Regression check: pass
- Selection rubric: routing, gate integrity, validation

## Adoption Record

- Accepted files: SKILL.md, validate_skill.py
- Rejected edit memory: none
- Validation commands: python3 validate_skill.py pass
- Follow-up: parent catalog refresh later
"""
    assert not validate_packet(good)

    bad_train_only = good.replace(
        "- [ ] select-001 | status=success | score=0.70 | evidence=logs/d.md | note=route fixed\n"
        "- [ ] select-002 | status=success | score=0.75 | evidence=logs/e.md | note=gate fixed\n",
        "",
    )
    assert any("held-out selection" in e for e in validate_packet(bad_train_only))

    bad_over_budget = good.replace("Edit budget L: 2", "Edit budget L: 1")
    assert any("exceeds edit budget" in e for e in validate_packet(bad_over_budget))

    bad_accept = good.replace("Candidate selection score: 0.70", "Candidate selection score: 0.50")
    assert any("accept requires candidate score" in e for e in validate_packet(bad_accept))

    bad_regression = good.replace("Regression check: pass", "Regression check: fail")
    assert any("Regression check: pass" in e for e in validate_packet(bad_regression))

    print("selftest OK: SkillOpt packet checker invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Paper-WorkFlow SkillOpt packet.")
    parser.add_argument("packet", nargs="?", help="path to a filled SKILLOPT_PACKET.md")
    parser.add_argument("--selftest", action="store_true", help="run built-in checker selftests")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.packet:
        parser.error("packet path is required unless --selftest is used")

    path = Path(args.packet).expanduser().resolve()
    if not path.exists():
        print(f"FAIL: packet does not exist: {path}", file=sys.stderr)
        return 1
    errors = validate_packet(path.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(f"OK: SkillOpt packet passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

