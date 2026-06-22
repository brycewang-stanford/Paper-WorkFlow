#!/usr/bin/env python3
"""Validate Paper-WorkFlow's load-bearing methods-claim verification log."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "_verification_log"
ALLOWED_STATUS = {"verified", "canonical", "to-verify"}
REQUIRED_FIELDS = ["claim-tag", "claim", "used-in", "source", "status", "checked"]
SECTION_RE = re.compile(r"^###\s+(?P<id>[A-Z]\d{2})\s+.+$", re.MULTILINE)


@dataclass(frozen=True)
class ClaimEntry:
    claim_id: str
    fields: dict[str, str]
    source_file: Path


def parse_entries(path: Path) -> list[ClaimEntry]:
    text = path.read_text(encoding="utf-8")
    matches = list(SECTION_RE.finditer(text))
    entries: list[ClaimEntry] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        fields: dict[str, str] = {}
        for line in block.splitlines():
            field_match = re.match(r"^-\s+([A-Za-z0-9_-]+):\s*(.*)$", line)
            if field_match:
                fields[field_match.group(1)] = field_match.group(2).strip()
        entries.append(ClaimEntry(match.group("id"), fields, path))
    return entries


def load_entries(root: Path = ROOT) -> list[ClaimEntry]:
    log_dir = root / "_verification_log"
    entries: list[ClaimEntry] = []
    for path in sorted(log_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        entries.extend(parse_entries(path))
    return entries


def validate_entries(entries: list[ClaimEntry], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_tags: set[str] = set()

    if not entries:
        return ["no verification-log claim entries found"]

    for entry in entries:
        label = f"{entry.source_file.relative_to(root)}:{entry.claim_id}"
        if entry.claim_id in seen_ids:
            errors.append(f"{label}: duplicate claim id")
        seen_ids.add(entry.claim_id)

        for field in REQUIRED_FIELDS:
            if not entry.fields.get(field):
                errors.append(f"{label}: missing field {field}")

        tag = entry.fields.get("claim-tag", "")
        if tag:
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", tag):
                errors.append(f"{label}: claim-tag must be kebab-case")
            if tag in seen_tags:
                errors.append(f"{label}: duplicate claim-tag {tag}")
            seen_tags.add(tag)

        status = entry.fields.get("status", "")
        source = entry.fields.get("source", "")
        if status not in ALLOWED_STATUS:
            errors.append(f"{label}: invalid status {status!r}")
        if status in {"verified", "canonical"} and not source:
            errors.append(f"{label}: {status} entry must have a source")
        if status == "to-verify" and "待补" not in source and "to verify" not in source.lower():
            errors.append(f"{label}: to-verify source must say what remains to verify")

        for used in re.split(r"\s*;\s*", entry.fields.get("used-in", "")):
            if not used:
                continue
            used_path = root / used
            try:
                used_path.resolve().relative_to(root)
            except ValueError:
                errors.append(f"{label}: used-in escapes skill root: {used}")
                continue
            if not used_path.exists():
                errors.append(f"{label}: used-in path does not exist: {used}")

    return errors


def selftest() -> None:
    valid = ClaimEntry(
        "M01",
        {
            "claim-tag": "few-cluster-wild-bootstrap",
            "claim": "Few clusters need corrected inference.",
            "used-in": "SKILL.md",
            "source": "Canonical source.",
            "status": "canonical",
            "checked": "2026-06-22",
        },
        ROOT / "_verification_log" / "methods-claims.md",
    )
    assert not validate_entries([valid], ROOT)

    duplicate = ClaimEntry("M01", {**valid.fields, "claim-tag": "few-cluster-wild-bootstrap"}, valid.source_file)
    assert validate_entries([valid, duplicate], ROOT)

    missing = ClaimEntry("M02", {"claim-tag": "bad tag", "status": "verified"}, valid.source_file)
    assert validate_entries([missing], ROOT)
    print("selftest OK: verification-log checker invariants hold")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run checker self-tests")
    args = parser.parse_args()

    if args.selftest:
        selftest()
        return 0

    errors = validate_entries(load_entries(ROOT), ROOT)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("verification log OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
