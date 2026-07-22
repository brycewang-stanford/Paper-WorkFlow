#!/usr/bin/env python3
"""Validate that load-bearing numeric claims agree across user-facing docs.

The README, SKILL.md and RIGOR.md each cite the same headline numbers:

  - 10 stages (Stage 0-9)
  - 47 skills
  - 2 hard gates (method gate + draft quality gate)
  - 3 analysis backends (Python/StatsPAI, Stata, R)
  - 1 audit-able workspace
  - N / N executable gates (the RIGOR badge; N is derived live from the
    rigor registry, so adding a gate never requires editing this checker)

The 47-skill claim is additionally anchored to disk: the numbered rows of
references/skill-coverage-map.md §2 (the skill provenance table) must
enumerate exactly 47 skills with sequential numbering, so the badge can
never drift from the auditable inventory.

If any of these drift independently in one doc but not the others, the
upstream reviewer / recruiter sees an inconsistent surface. This checker
guards against that drift.

Usage:
    python3 scripts/check_numeric_claims.py
    python3 scripts/check_numeric_claims.py --selftest
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
SKILL_MD = ROOT / "SKILL.md"
RIGOR_MD = ROOT / "RIGOR.md"


def _badge_count() -> int:
    """Live gate count from the rigor registry (no selftests are run).

    Mirrors generate_rigor_report.evaluate(): an entry is *active* unless it
    is optional AND its script is missing (that combination renders PLANNED).
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import generate_rigor_report as _grr  # noqa: PLC0415 -- deliberate lazy import

    return sum(
        1
        for entry in _grr.REGISTRY
        if not (entry.get("optional") and not (ROOT / entry["path"]).exists())
    )


BADGE_COUNT = _badge_count()
BADGE = f"{BADGE_COUNT}/{BADGE_COUNT}"

COVERAGE_MAP = ROOT / "references" / "skill-coverage-map.md"


def _coverage_map_count(text: str) -> int:
    """Count the numbered skill rows (`| N | \\`skill\\` | ...`) in the
    coverage map's §2 provenance tables.

    Returns -1 if the numbering is non-sequential (a corrupted or
    double-counted table must fail loudly, not pass with the right total).
    """
    nums = [int(m.group(1)) for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*`", text, re.MULTILINE)]
    if not nums:
        return 0
    if sorted(nums) != list(range(1, len(nums) + 1)):
        return -1
    return len(nums)


def _normalise(text: str) -> str:
    """Strip HTML markup, decode common entities, normalise dashes.

    The badges in README.md / README.en.md wrap numbers in <b>...</b> tags
    with non-breaking spaces; we want to match the underlying number + word
    regardless of which element wraps it.
    """
    text = text.replace("–", "-").replace("—", "-").replace("×", "x")
    text = text.replace(" ", " ")
    # URL-decode the common badge encoding.
    text = text.replace("%2F", "/")
    # Decode common HTML entities the README badges use.
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    # Drop simple inline tags so <b>47</b> skills becomes "47 skills".
    text = re.sub(r"</?[a-zA-Z][^>]*>", " ", text)
    # Collapse whitespace.
    text = re.sub(r"\s+", " ", text)
    return text


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"FAIL: cannot read {path}: {exc}", file=sys.stderr)
        raise SystemExit(1)


# Each claim: per_doc is a list of REGEX patterns. A doc passes the
# claim iff ANY pattern matches (after normalisation). A claim passes
# overall iff every required doc passes.
CLAIMS = [
    {
        "id": "stages_10",
        "value": 10,
        "summary": "10 stages (Stage 0-9)",
        "per_doc": {
            "README.md": [r"10\s*(?:个)?\s*阶段", r"Stage\s*0\s*[-–—]\s*9"],
            "README.en.md": [r"10\s*stages", r"Stage\s*0\s*[-–—]\s*9"],
            "SKILL.md": [r"Stage\s*0\s*[-–—]\s*9"],
            "RIGOR.md": [r"Stage\s*0\s*[-–—]\s*9"],
        },
    },
    {
        "id": "skills_47",
        "value": 47,
        "summary": "47 skills (the orchestrator's sub-skill library)",
        "per_doc": {
            "README.md": [r"47\s*(?:个\s*)?(?:skill|技能)s?"],
            "README.en.md": [r"47\s*(?:个\s*)?(?:skill|技能)s?"],
            "SKILL.md": [r"47\s*(?:个\s*)?(?:skill|技能)s?"],
        },
    },
    {
        "id": "gates_2",
        "value": 2,
        "summary": "2 hard gates (method + draft quality)",
        "per_doc": {
            "README.md": [r"(?:两道?\s*硬闸门|2\s*道硬闸门)"],
            "README.en.md": [r"2\s*hard\s*gates", r"hard\s*gates?"],
            "SKILL.md": [r"Method\s*Gate", r"Draft\s*Quality\s*Gate"],
        },
    },
    {
        "id": "backends_3",
        "value": 3,
        "summary": "3 analysis backends (Python/StatsPAI, Stata, R)",
        "per_doc": {
            "README.md": [r"3\s*套\s*分析后端", r"3\s*(?:个)?\s*分析后端"],
            "README.en.md": [r"3\s*analysis\s*backends", r"3\s*backends"],
            "SKILL.md": [r"Python.*Stata.*R", r"Stata.*R.*Python"],
        },
    },
    {
        "id": "executable_gates_badge",
        "value": BADGE,
        "summary": (
            f"{BADGE} executable gates (RIGOR badge -- count derived live "
            "from the rigor registry)"
        ),
        "per_doc": {
            "README.md": [rf"{BADGE_COUNT}\s*/\s*{BADGE_COUNT}"],
            "README.en.md": [rf"{BADGE_COUNT}\s*/\s*{BADGE_COUNT}"],
            # SKILL.md deliberately carries no badge (always-loaded byte
            # budget); the empty list means "no signal required here".
            "SKILL.md": [],
            "RIGOR.md": [rf"{BADGE_COUNT}\s*/\s*{BADGE_COUNT}"],
        },
    },
]


def _doc_present(text: str, patterns: list[str]) -> bool:
    if not patterns:
        return True
    return any(re.search(p, text) for p in patterns)


def evaluate(docs: dict[str, str], coverage_count: int | None = None) -> dict:
    errors: list[str] = []
    per_claim = []
    for claim in CLAIMS:
        missing_docs = []
        for doc_name, patterns in claim["per_doc"].items():
            if not _doc_present(docs[doc_name], patterns):
                missing_docs.append(doc_name)
        entry = {
            "id": claim["id"],
            "summary": claim["summary"],
            "value": claim["value"],
            "missing_docs": missing_docs,
        }
        per_claim.append(entry)
        for missing in missing_docs:
            errors.append(
                f"{claim['id']}: doc {missing!r} missing a recognised signal for "
                f"{claim['summary']}; looked for {claim['per_doc'][missing]!r}"
            )

    # Disk anchor for skills_47: the badge must equal the coverage map's
    # enumerated inventory, not merely agree across prose surfaces.
    if coverage_count is not None:
        claimed = next(c["value"] for c in CLAIMS if c["id"] == "skills_47")
        if coverage_count == -1:
            errors.append(
                "skills_47 anchor: skill-coverage-map.md §2 numbering is "
                "non-sequential (corrupted or double-counted table)"
            )
        elif coverage_count != claimed:
            errors.append(
                f"skills_47 anchor: skill-coverage-map.md §2 enumerates "
                f"{coverage_count} skills but the badge claims {claimed}"
            )

    return {
        "ok": not errors,
        "errors": errors,
        "per_claim": per_claim,
        "claim_count": len(CLAIMS),
        "doc_count": len(docs),
        "coverage_count": coverage_count,
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow numeric-claims cross-doc parity",
        f"  claims checked: {result['claim_count']}",
        f"  docs checked: {result['doc_count']}",
    ]
    if result.get("coverage_count") is not None:
        lines.append(
            f"  coverage-map inventory: {result['coverage_count']} enumerated skills"
        )
    for entry in result["per_claim"]:
        flag = "OK" if not entry["missing_docs"] else "MISS"
        lines.append(
            f"  [{flag}] {entry['id']} (value={entry['value']!s}): "
            f"{entry['summary']} -- missing={entry['missing_docs']}"
        )
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  NUMERIC CLAIMS OK" if result["ok"] else "  NUMERIC CLAIMS FAILED")
    return "\n".join(lines)


def _good_docs() -> dict[str, str]:
    """Build synthetic docs that satisfy every claim after normalisation.

    The test strings deliberately include HTML tags and mixed dashes to
    confirm the normaliser handles them.
    """
    return {
        "README.md": (
            "<b>10</b> 阶段 · <b>47</b> 技能 · "
            "<b>2</b> 道硬闸门 · <b>3</b> 套分析后端\n"
            "47 个技能如何被编排\n"
            "Stage 0–9 协议\n"
            f"{BADGE} 闸门\n"
        ),
        "README.en.md": (
            "<b>10</b> stages · <b>47</b> skills · "
            "<b>2</b> hard gates · <b>3</b> analysis backends\n"
            "Stage 0-9 execution protocol\n"
            "Two hard gates\n"
            f"{BADGE} gates\n"
        ),
        "SKILL.md": (
            "Stage 0–9 可断点续跑流水线\n"
            "47 个 skill 按正确顺序\n"
            "Method Gate 与 Draft Quality Gate\n"
            "Python/StatsPAI、Stata、R 三种分析后端\n"
        ),
        "RIGOR.md": (
            f"{BADGE} green\n"
            "Stage 0-9 黄金路径\n"
        ),
    }


def _selftest() -> int:
    good = _good_docs()
    normalised = {k: _normalise(v) for k, v in good.items()}
    result = evaluate(normalised)
    assert result["ok"], f"synthetic passing surface must pass: {result}"

    # Drift the 47 number on README.md -> strip every 47 signal.
    bad = dict(good)
    bad["README.md"] = (
        good["README.md"]
        .replace("47", "46")
        .replace("技能", "能力")
    )
    normalised = {k: _normalise(v) for k, v in bad.items()}
    result = evaluate(normalised)
    assert not result["ok"], "skills_47 drift in README.md must fail"
    assert any("skills_47" in e for e in result["errors"]), (
        f"errors should mention skills_47 drift: {result['errors']}"
    )

    # Drift the badge in RIGOR.md to a stale count -> must fail.
    bad = dict(good)
    stale = f"{BADGE_COUNT - 1}/{BADGE_COUNT - 1}"
    bad["RIGOR.md"] = good["RIGOR.md"].replace(BADGE, stale)
    normalised = {k: _normalise(v) for k, v in bad.items()}
    result = evaluate(normalised)
    assert not result["ok"], "executable_gates_badge drift in RIGOR.md must fail"
    assert any("executable_gates_badge" in e for e in result["errors"]), (
        f"errors should mention executable_gates_badge drift: {result['errors']}"
    )

    # Drop the Stage 0-9 from SKILL.md -> must fail.
    bad = dict(good)
    bad["SKILL.md"] = good["SKILL.md"].replace("Stage 0–9", "Stage 1-9")
    normalised = {k: _normalise(v) for k, v in bad.items()}
    result = evaluate(normalised)
    assert not result["ok"], "stages_10 drift in SKILL.md must fail"

    # Drift backends_3 in README.en.md -> must fail.
    bad = dict(good)
    bad["README.en.md"] = good["README.en.md"].replace("3", "2")
    normalised = {k: _normalise(v) for k, v in bad.items()}
    result = evaluate(normalised)
    assert not result["ok"], "backends_3 drift in README.en.md must fail"

    # Confirm the normaliser collapses HTML and mixed dashes.
    norm = _normalise("<b>10</b> 阶段 · <b>47</b> 技能 · Stage 0–9")
    for expected in ["10 阶段", "47 技能", "Stage 0-9"]:
        assert expected in norm, f"normaliser dropped {expected!r} from {norm!r}"

    # Coverage-map disk anchor: counting, sequencing, and mismatch detection.
    rows = "\n".join(f"| {i} | `skill_{i}` | `67/x` | Stage |" for i in range(1, 48))
    assert _coverage_map_count(rows) == 47
    good_docs = {k: _normalise(v) for k, v in _good_docs().items()}
    assert evaluate(good_docs, coverage_count=47)["ok"], "matching anchor must pass"
    result = evaluate(good_docs, coverage_count=46)
    assert not result["ok"] and any("skills_47 anchor" in e for e in result["errors"]), (
        f"anchor mismatch must fail: {result['errors']}"
    )
    gap = rows.replace("| 20 | `skill_20` | `67/x` | Stage |\n", "")
    assert _coverage_map_count(gap) == -1, "a numbering gap must be flagged, not recounted"
    assert not evaluate(good_docs, coverage_count=-1)["ok"], "corrupted table must fail"
    assert _coverage_map_count("no tables here") == 0

    # The live coverage map must anchor the live claim.
    live = _coverage_map_count(_read(COVERAGE_MAP))
    assert live == 47, f"live skill-coverage-map.md enumerates {live}, expected 47"

    print("selftest OK: numeric-claims cross-doc invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run synthetic selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    docs = {
        "README.md": _normalise(_read(ZH_README)),
        "README.en.md": _normalise(_read(EN_README)),
        "SKILL.md": _normalise(_read(SKILL_MD)),
        "RIGOR.md": _normalise(_read(RIGOR_MD)),
    }
    result = evaluate(docs, coverage_count=_coverage_map_count(_read(COVERAGE_MAP)))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())