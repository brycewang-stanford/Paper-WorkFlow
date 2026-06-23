#!/usr/bin/env python3
"""Reproducible LLM-as-judge harness for the Stage 7 Draft Quality Gate.

Why this exists
---------------
The quality gate (references/quality-rubric.md) asks an independent "top-journal
AE" critic subagent to score a draft on 7 dimensions and declare PASS / NOT PASS.
That is an LLM-as-judge, and a bare LLM judge is not reproducible: two runs can
disagree, and nothing stops a generous critic from writing "PASS" under a
scorecard whose own numbers say otherwise.

open_deep_research made its Deep Research Bench judge trustworthy by pinning the
judge against a frozen gold standard (RACE rubric + reference reports + a scoring
script run as a dataset). This harness ports that engineering to the quality
gate, in two layers:

  1. **Deterministic verdict.** The PASS rule is pure arithmetic over the rubric:
     PASS iff every dimension >= 7 AND total >= 56 AND dimensions 2/3/6
     (identification, robustness, citation) carry no fatal red flag AND the
     Stage 7 claim-integrity pre-review is clean. compute_verdict() recomputes
     this independently of whatever verdict the critic typed, so a scorecard
     whose stated verdict, total, or red-flag capping is internally inconsistent
     is mechanically caught.

  2. **Calibration against gold.** evals/quality_calibration.json freezes anchor
     scorecards with known verdicts (including the rubric's own worked example).
     The harness asserts compute_verdict() reproduces every gold verdict, so the
     rule itself is a measured invariant -- if someone edits the thresholds in
     the prose, this fails until the anchors are reconciled.

It does NOT replace the critic's judgment on the *scores* (that is irreducibly a
reading task). It makes the *bookkeeping around the scores* reproducible: the
arithmetic, the red-flag caps, the integrity interlock, and the final verdict.

Standalone by construction: reads files only, imports nothing from the skill.
validate_skill.py runs the self-test as a blocking maintenance gate.

Usage
-----
    python3 evals/check_quality_judge.py --scorecard 00_meta/quality_scorecard.md
    python3 evals/check_quality_judge.py --calibration evals/quality_calibration.json
    python3 evals/check_quality_judge.py --json ...
    python3 evals/check_quality_judge.py --selftest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CALIBRATION = HERE / "quality_calibration.json"

# The rubric's pass rule, encoded once.
N_DIMENSIONS = 7
DIM_MIN = 7              # every dimension must be >= this
TOTAL_MIN = 56          # out of 70
RED_FLAG_CAP = 4        # a dimension carrying a fatal red flag must be <= this
CRITICAL_DIMENSIONS = (2, 3, 6)  # identification / robustness / citation

# Circled numerals the rubric uses to label dimensions in the scorecard table.
_CIRCLED = {"①": 1, "②": 2, "③": 3, "④": 4, "⑤": 5, "⑥": 6, "⑦": 7}


# --------------------------------------------------------------------------- #
# pure verdict core                                                           #
# --------------------------------------------------------------------------- #
def compute_verdict(dimensions: dict, red_flags: dict | None = None,
                    integrity_clean: bool = True) -> dict:
    """Recompute PASS / NOT_PASS from dimension scores. Pure function.

    `dimensions` maps dimension number (int or str 1..7) to score (int 1..10).
    `red_flags` maps dimension number to True when a fatal red flag was hit.
    Returns the verdict plus the list of reasons it failed (empty iff PASS) and
    any *internal inconsistencies* (e.g. a red-flagged dimension scored above the
    cap) that mean the scorecard does not obey its own rules.
    """
    red_flags = {int(k): bool(v) for k, v in (red_flags or {}).items()}
    dims = {int(k): int(v) for k, v in dimensions.items()}

    reasons: list[str] = []
    inconsistencies: list[str] = []

    if sorted(dims) != list(range(1, N_DIMENSIONS + 1)):
        inconsistencies.append(
            f"expected dimensions 1..{N_DIMENSIONS}, got {sorted(dims)}")

    total = sum(dims.values())

    for d in sorted(dims):
        if dims[d] < DIM_MIN:
            reasons.append(f"dimension {d} below {DIM_MIN}")
    if total < TOTAL_MIN:
        reasons.append(f"total {total} below {TOTAL_MIN}")
    for d in CRITICAL_DIMENSIONS:
        if red_flags.get(d):
            reasons.append(f"fatal red flag in critical dimension {d}")
    if not integrity_clean:
        reasons.append("integrity pre-review not clean")

    # A red flag in ANY dimension caps that dimension at RED_FLAG_CAP; a critic
    # who recorded a red flag but a score above the cap broke the rubric's rule.
    for d, hit in red_flags.items():
        if hit and dims.get(d, 0) > RED_FLAG_CAP:
            inconsistencies.append(
                f"dimension {d} has a fatal red flag but score "
                f"{dims.get(d)} > cap {RED_FLAG_CAP}")

    passed = not reasons
    return {
        "verdict": "PASS" if passed else "NOT_PASS",
        "total": total,
        "passed": passed,
        "reasons": reasons,
        "inconsistencies": inconsistencies,
    }


# --------------------------------------------------------------------------- #
# scorecard parsing                                                           #
# --------------------------------------------------------------------------- #
_DIM_ROW_RE = re.compile(
    r"^\|\s*([①②③④⑤⑥⑦])[^|]*\|\s*\*{0,2}(\d{1,2})\b[^|]*\|.*?\|\s*([^|]+?)\s*\|\s*$",
    re.MULTILINE,
)
_TOTAL_RE = re.compile(r"总分[^0-9]*?(\d{1,3})\s*/\s*70")
_VERDICT_RE = re.compile(r"结论[:：]?\s*\**\s*(NOT\s*PASS|PASS)", re.IGNORECASE)


def _flag_hit(cell: str) -> bool:
    """A red-flag cell reads 是 (hit) or 否 (clear) in the rubric template."""
    return "是" in cell and "否" not in cell


def parse_scorecard(text: str) -> dict:
    """Extract dimension scores, red flags, total, and the stated verdict.

    Returns {dimensions, red_flags, total (or None), stated_verdict (or None)}.
    Tolerant of surrounding prose; keys off the rubric's fixed table shape.
    """
    dimensions: dict = {}
    red_flags: dict = {}
    for m in _DIM_ROW_RE.finditer(text):
        d = _CIRCLED[m.group(1)]
        dimensions[d] = int(m.group(2))
        red_flags[d] = _flag_hit(m.group(3))

    total = None
    mt = _TOTAL_RE.search(text)
    if mt:
        total = int(mt.group(1))

    stated = None
    mv = _VERDICT_RE.search(text)
    if mv:
        stated = "NOT_PASS" if "NOT" in mv.group(1).upper().replace(" ", "") \
            else "PASS"

    return {"dimensions": dimensions, "red_flags": red_flags,
            "total": total, "stated_verdict": stated}


def check_scorecard(text: str, integrity_clean: bool = True) -> dict:
    """Validate a real scorecard: arithmetic, red-flag caps, and stated verdict
    must all agree with the deterministic rule. Returns discrepancies."""
    parsed = parse_scorecard(text)
    dims = parsed["dimensions"]
    discrepancies: list[str] = []

    if len(dims) != N_DIMENSIONS:
        discrepancies.append(
            f"parsed {len(dims)} dimension rows, expected {N_DIMENSIONS}")
        return {"ok": False, "parsed": parsed, "discrepancies": discrepancies,
                "computed": None}

    computed = compute_verdict(dims, parsed["red_flags"], integrity_clean)
    discrepancies.extend(computed["inconsistencies"])

    # total written in the card must equal the sum of the dimensions
    if parsed["total"] is not None and parsed["total"] != computed["total"]:
        discrepancies.append(
            f"stated total {parsed['total']} != sum of dimensions "
            f"{computed['total']}")

    # stated verdict must match the recomputed one
    if parsed["stated_verdict"] and parsed["stated_verdict"] != computed["verdict"]:
        discrepancies.append(
            f"stated verdict {parsed['stated_verdict']} != computed "
            f"{computed['verdict']} (reasons: {'; '.join(computed['reasons']) or 'none'})")

    return {"ok": not discrepancies, "parsed": parsed,
            "computed": computed, "discrepancies": discrepancies}


# --------------------------------------------------------------------------- #
# calibration                                                                 #
# --------------------------------------------------------------------------- #
def run_calibration(path: Path) -> dict:
    """Assert compute_verdict reproduces every gold anchor's expected verdict."""
    data = json.loads(path.read_text(encoding="utf-8"))
    anchors = data.get("anchors", [])
    failures: list[str] = []
    for a in anchors:
        got = compute_verdict(a["dimensions"], a.get("red_flags", {}),
                              a.get("integrity_clean", True))
        if got["verdict"] != a["expected_verdict"]:
            failures.append(
                f"{a['id']}: expected {a['expected_verdict']}, got "
                f"{got['verdict']} (reasons: {'; '.join(got['reasons']) or 'none'})")
        if got["inconsistencies"]:
            failures.append(f"{a['id']}: unexpected inconsistencies "
                            f"{got['inconsistencies']}")
    return {"ok": not failures, "n_anchors": len(anchors), "failures": failures}


# --------------------------------------------------------------------------- #
# selftest                                                                     #
# --------------------------------------------------------------------------- #
def _scorecard(rows: list[tuple[int, int, bool]], total: int, verdict: str) -> str:
    """Build a synthetic scorecard in the rubric's table format for testing."""
    circ = {v: k for k, v in _CIRCLED.items()}
    lines = [
        "# 初稿质量门评分卡 — selftest",
        "| 维度 | 分数/10 | 关键依据 | 命中致命红旗? |",
        "|---|---|---|---|",
    ]
    for d, score, flag in rows:
        lines.append(f"| {circ[d]} 维度{d} | {score} | 依据 | {'是' if flag else '否'} |")
    lines.append(f"| **总分** | **{total} / 70** | — | — |")
    lines.append("")
    lines.append(f"## 达标判定")
    lines.append(f"- **结论: {verdict}**")
    return "\n".join(lines)


def _selftest() -> int:
    # deterministic verdict: clean pass
    p = compute_verdict({1: 8, 2: 8, 3: 8, 4: 8, 5: 8, 6: 8, 7: 8})
    assert p["verdict"] == "PASS" and p["total"] == 56 and not p["reasons"]

    # one dimension below 7 -> NOT_PASS even if total clears
    sub = compute_verdict({1: 9, 2: 9, 3: 6, 4: 9, 5: 9, 6: 9, 7: 9})
    assert sub["verdict"] == "NOT_PASS"
    assert any("dimension 3 below 7" in r for r in sub["reasons"])

    # total below 56 with every dimension >= 7
    lowtot = compute_verdict({1: 8, 2: 8, 3: 8, 4: 8, 5: 8, 6: 8, 7: 7})
    assert lowtot["verdict"] == "NOT_PASS" and lowtot["total"] == 55
    assert any("total 55 below 56" in r for r in lowtot["reasons"])

    # red flag in a critical dimension (capped at 4)
    rf = compute_verdict({1: 9, 2: 4, 3: 8, 4: 9, 5: 9, 6: 9, 7: 9}, {"2": True})
    assert rf["verdict"] == "NOT_PASS"
    assert any("critical dimension 2" in r for r in rf["reasons"])
    assert not rf["inconsistencies"]

    # red flag recorded but score left above the cap -> internal inconsistency
    bad = compute_verdict({1: 9, 2: 9, 3: 8, 4: 9, 5: 9, 6: 9, 7: 9}, {"2": True})
    assert any("cap" in i for i in bad["inconsistencies"])

    # integrity interlock
    integ = compute_verdict({1: 8, 2: 8, 3: 8, 4: 8, 5: 8, 6: 8, 7: 8},
                            integrity_clean=False)
    assert integ["verdict"] == "NOT_PASS"
    assert any("integrity" in r for r in integ["reasons"])

    # parse + check a consistent NOT_PASS scorecard (the rubric's worked example)
    card = _scorecard([(1, 8, False), (2, 7, False), (3, 6, False), (4, 8, False),
                       (5, 8, False), (6, 9, False), (7, 8, False)], 54, "NOT PASS")
    res = check_scorecard(card)
    assert res["ok"], f"consistent scorecard flagged: {res['discrepancies']}"
    assert res["computed"]["verdict"] == "NOT_PASS"
    assert res["parsed"]["total"] == 54

    # arithmetic lie: total says 60 but dims sum to 54
    liar = _scorecard([(1, 8, False), (2, 7, False), (3, 6, False), (4, 8, False),
                       (5, 8, False), (6, 9, False), (7, 8, False)], 60, "NOT PASS")
    res2 = check_scorecard(liar)
    assert not res2["ok"] and any("stated total 60" in d for d in res2["discrepancies"])

    # verdict lie: dims fail but card claims PASS
    fibber = _scorecard([(1, 8, False), (2, 7, False), (3, 6, False), (4, 8, False),
                         (5, 8, False), (6, 9, False), (7, 8, False)], 54, "PASS")
    res3 = check_scorecard(fibber)
    assert not res3["ok"] and any("stated verdict PASS" in d for d in res3["discrepancies"])

    # red-flag cap lie parsed from the table: dim 2 flagged 是 but scored 9
    capcard = _scorecard([(1, 9, False), (2, 9, True), (3, 8, False), (4, 9, False),
                          (5, 9, False), (6, 9, False), (7, 9, False)], 62, "PASS")
    res4 = check_scorecard(capcard)
    assert not res4["ok"] and any("cap" in d for d in res4["discrepancies"])

    # a genuinely clean PASS scorecard passes the checker
    good = _scorecard([(1, 8, False), (2, 8, False), (3, 8, False), (4, 8, False),
                       (5, 8, False), (6, 8, False), (7, 8, False)], 56, "PASS")
    res5 = check_scorecard(good)
    assert res5["ok"] and res5["computed"]["verdict"] == "PASS"

    # calibration: the shipped gold anchors must all reproduce
    if DEFAULT_CALIBRATION.exists():
        cal = run_calibration(DEFAULT_CALIBRATION)
        assert cal["ok"], f"calibration anchors failed: {cal['failures']}"
        assert cal["n_anchors"] >= 4, "expected the shipped anchor set"

    print("selftest OK: quality-judge verdict + calibration invariants hold")
    return 0


# --------------------------------------------------------------------------- #
# cli                                                                          #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--scorecard", help="a quality_scorecard.md to validate")
    p.add_argument("--integrity-not-clean", action="store_true",
                   help="treat the Stage 7 claim-integrity pre-review as having a blocking finding")
    p.add_argument("--calibration", nargs="?", const=str(DEFAULT_CALIBRATION),
                   help="run the gold-anchor calibration (default suite if no path)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--selftest", action="store_true", help="run built-in invariant tests")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.calibration:
        cal = run_calibration(Path(args.calibration))
        if args.json:
            print(json.dumps(cal, ensure_ascii=False, indent=2))
        else:
            print(f"calibration: {cal['n_anchors']} anchor(s), "
                  f"{'OK' if cal['ok'] else 'FAILED'}")
            for f in cal["failures"]:
                print(f"  FAIL: {f}")
        return 0 if cal["ok"] else 1

    if args.scorecard:
        text = Path(args.scorecard).read_text(encoding="utf-8")
        res = check_scorecard(text, integrity_clean=not args.integrity_not_clean)
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            comp = res["computed"]
            if comp:
                print(f"computed verdict: {comp['verdict']} (total {comp['total']})")
                for r in comp["reasons"]:
                    print(f"  - {r}")
            if res["discrepancies"]:
                print("DISCREPANCIES (scorecard does not obey its own rules):")
                for d in res["discrepancies"]:
                    print(f"  ! {d}")
            else:
                print("scorecard is internally consistent with the rubric rule")
        return 0 if res["ok"] else 1

    p.error("need --scorecard, --calibration, or --selftest")


if __name__ == "__main__":
    raise SystemExit(main())
