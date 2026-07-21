#!/usr/bin/env python3
"""
check_compactness.py — orphan-reference detector for the paper-workflow skill.

Scans every `.md` file under `references/` and reports whether each one is
referenced from `SKILL.md` or from any other reference. Files that are not
referenced anywhere are flagged as "orphans" — the ratchet is advisory; this
script exits 0 in either case so it can run in pre-commit without blocking work.

Usage:
    python3 scripts/check_compactness.py            # human-readable report
    python3 scripts/check_compactness.py --json     # JSON output
    python3 scripts/check_compactness.py --strict   # exit 1 if any orphan found

The script never modifies files. Pair it with `validate_skill.py` for the full
always-loaded-layer check; pair it with `evals/check_complexity_budget.py` for
the footprint ratchet.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
REFERENCES_DIR = SKILL_ROOT / "references"

# Match a markdown link whose visible text is anything, pointing at `xxx.md`
# (relative or absolute within the repo). Also catch the bare filename form
# some inline references use, e.g. "see design-risk-ledger.md".
LINK_TO_MD_RE = re.compile(r"\]\(([^)]*\.md)(?:#[^)]*)?\)")
BARE_BASENAME_RE = re.compile(r"\b([a-z0-9][a-z0-9\-_]*\.md)\b", re.IGNORECASE)


def _is_self_link(link_target: str, current_file: Path) -> bool:
    """True when the link points to the file that contains the link."""
    target = (SKILL_ROOT / link_target).resolve() if not link_target.startswith("/") else Path(link_target)
    try:
        return target.resolve() == current_file.resolve()
    except (OSError, ValueError):
        return False


def collect_referenced_basenames(source_paths: list[Path]) -> set[str]:
    """Return the union of md basenames referenced anywhere in source_paths."""
    referenced: set[str] = set()
    for src in source_paths:
        if not src.exists() or not src.is_file():
            continue
        try:
            text = src.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # Markdown links like ](path/to/foo.md)
        for match in LINK_TO_MD_RE.finditer(text):
            target = match.group(1)
            if _is_self_link(target, src):
                continue
            # Resolve to basename so cross-directory links still register
            referenced.add(Path(target).name)
        # Bare filename mentions (less reliable — false positives if e.g.
        # the word "skill-map.md" appears in prose; we accept the noise here
        # because the orphan list is advisory, not gating)
        for match in BARE_BASENAME_RE.finditer(text):
            referenced.add(match.group(1))
    return referenced


def discover_reference_files() -> list[Path]:
    if not REFERENCES_DIR.is_dir():
        return []
    return sorted(p for p in REFERENCES_DIR.glob("*.md") if p.is_file())


def build_report() -> dict:
    refs = discover_reference_files()
    referenced = collect_referenced_basenames([SKILL_MD, *refs])
    orphans: list[str] = []
    referenced_list: list[str] = []
    for ref in refs:
        name = ref.name
        if name in referenced:
            referenced_list.append(name)
        else:
            orphans.append(name)
    return {
        "skill_md": str(SKILL_MD),
        "references_dir": str(REFERENCES_DIR),
        "total_references": len(refs),
        "referenced": sorted(referenced_list),
        "orphans": sorted(orphans),
    }


def render_text(report: dict) -> str:
    lines = [
        "paper-workflow compactness check",
        "-----------------------------",
        f"references dir : {report['references_dir']}",
        f"SKILL.md       : {report['skill_md']}",
        f"references     : {report['total_references']} files",
        f"orphans        : {len(report['orphans'])}",
        "",
    ]
    if report["orphans"]:
        lines.append("ORPHAN references (not linked from SKILL.md or any other reference):")
        for o in report["orphans"]:
            lines.append(f"  - {o}")
        lines.append("")
        lines.append(
            "Action: either (a) add a cross-link from SKILL.md or another reference, "
            "(b) remove the orphan if its content has been merged elsewhere, or "
            "(c) accept the orphan explicitly by linking it from a placeholder doc."
        )
    else:
        lines.append("OK — every reference is reachable from SKILL.md or another reference.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any orphan reference is found (default: advisory only)",
    )
    args = parser.parse_args(argv)

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))
    if args.strict and report["orphans"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())