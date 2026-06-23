#!/usr/bin/env python3
"""L2 review-scorecard verifier — make the semantic quality review checkable.

Why this exists
---------------
The Draft Quality Gate is a 7-dimension semantic review (references/quality-rubric.md)
run by a critic subagent. Orchestra's `AI-Research-SKILLs` has a comparable rubric, but
nothing executable backs it: the critic self-grades in markdown and could declare PASS
while a fatal flag sits in the prose. This checker is the L1 (structural, executable)
half of an L1/L2 split: it does not re-judge credibility — it enforces that the L2 card
obeys its own rules so a green verdict cannot be hand-waved.

The invariants, all mechanical and decidable:

  - all 7 dimensions carry a numeric score in 0..10 (an incomplete card is not a verdict);
  - every finding carries a severity in {blocking, major, minor}, a non-placeholder
    *verbatim evidence span* (the exact quoted text), and a locator — a red flag with no
    quoted text is inadmissible (the anti-hallucination device);
  - a blocking finding caps its dimension at <= 4 (the rubric's "fatal flag" rule), and a
    dimension marked `fatal flag = yes` must be scored <= 4;
  - a declared PASS is only consistent if every dimension >= 7, the total >= 56, and the
    register holds zero blocking findings.

It reads `00_meta/quality_scorecard.md` (from templates/quality_scorecard.md). A missing
card on a run that has not reached the quality gate is INFO, not failure.

Usage:
    python3 check_review_scorecard.py <workspace>          # human report
    python3 check_review_scorecard.py <workspace> --json   # machine readable
    python3 check_review_scorecard.py --selftest           # verify this checker

Exit code is non-zero iff a HARD inconsistency is found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

FAIL = "FAIL"
WARN = "WARN"
INFO = "INFO"
OKAY = "OK"

REL_CARD = "00_meta/quality_scorecard.md"
SEVERITIES = {"blocking", "major", "minor"}
PLACEHOLDER_RE = re.compile(r"<[^>]*>|\bTODO\b|\bTBD\b|（待填）|待填")
DECISION_RE = re.compile(r"Decision:\s*\**\s*(NOT[ _]?PASS|PASS)", re.IGNORECASE)


def _is_placeholder(value: str) -> bool:
    v = (value or "").strip().strip('"').strip()
    if not v:
        return True
    return bool(PLACEHOLDER_RE.search(v))


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "_preamble"
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*\S)\s*$", line)
        if m:
            sections[current] = "\n".join(buf)
            current = m.group(1).strip()
            buf = []
        else:
            buf.append(line)
    sections[current] = "\n".join(buf)
    return sections


def _find_section(sections: dict[str, str], needle: str) -> str | None:
    for head, body in sections.items():
        if needle.lower() in head.lower():
            return body
    return None


def _rows(body: str) -> list[list[str]]:
    out: list[list[str]] = []
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):  # separator
            continue
        out.append(cells)
    return out


def _first_int(text: str) -> int | None:
    m = re.search(r"-?\d+", text or "")
    return int(m.group()) if m else None


def parse_card(text: str) -> dict:
    sections = _split_sections(text)
    scores: dict[int, int] = {}
    fatal: dict[int, bool] = {}
    total: int | None = None

    score_body = _find_section(sections, "Dimension Scores") or ""
    for cells in _rows(score_body):
        if not cells:
            continue
        head = cells[0]
        m = re.match(r"^(\d)\.", head)
        if m:
            idx = int(m.group(1))
            sc = _first_int(cells[1]) if len(cells) > 1 else None
            if sc is not None:
                scores[idx] = sc
            if len(cells) > 3:
                fatal[idx] = cells[3].strip().lower() in {"yes", "y", "true", "是"}
        elif head.lower().startswith("total"):
            total = _first_int(cells[1]) if len(cells) > 1 else None

    findings: list[dict] = []
    find_body = _find_section(sections, "Findings Register") or ""
    for cells in _rows(find_body):
        if len(cells) < 5:
            continue
        if "Severity" in cells or "Verbatim" in " ".join(cells):
            continue  # header
        findings.append({
            "id": cells[0],
            "severity": cells[1].strip().lower(),
            "dim": _first_int(cells[2]),
            "verbatim": cells[3],
            "locator": cells[4],
        })

    decision = None
    dm = DECISION_RE.search(text)
    if dm:
        decision = "not_pass" if "not" in dm.group(1).lower() else "pass"
    return {"scores": scores, "fatal": fatal, "total": total,
            "findings": findings, "decision": decision}


def validate_card(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    card = parse_card(text)
    scores = card["scores"]

    missing = [d for d in range(1, 8) if d not in scores]
    if missing:
        out.append((FAIL, f"missing numeric score for dimension(s): {missing}"))
    for d, sc in scores.items():
        if not (0 <= sc <= 10):
            out.append((FAIL, f"dimension {d} score {sc} out of range 0..10"))

    if card["total"] is not None and scores and not missing:
        s = sum(scores[d] for d in range(1, 8))
        if card["total"] != s:
            out.append((WARN, f"declared total {card['total']} != sum of dimensions {s}"))

    blocking_dims: set[int] = set()
    for f in card["findings"]:
        label = f"finding {f['id']}"
        if f["severity"] not in SEVERITIES:
            out.append((FAIL, f"{label}: severity {f['severity']!r} not in {sorted(SEVERITIES)}"))
        if _is_placeholder(f["verbatim"]):
            out.append((FAIL, f"{label}: verbatim evidence span is empty/placeholder "
                              "(a finding must quote the exact text)"))
        if _is_placeholder(f["locator"]):
            out.append((FAIL, f"{label}: locator is empty/placeholder"))
        if f["severity"] == "blocking" and f["dim"] is not None:
            blocking_dims.add(f["dim"])

    # rubric rule: a blocking finding caps its dimension at <= 4
    for d in blocking_dims:
        if d in scores and scores[d] > 4:
            out.append((FAIL, f"dimension {d} has a blocking finding but is scored {scores[d]} (>4); "
                              "a fatal flag caps the dimension at 4"))
    # inline fatal-flag column must agree with the score cap
    for d, is_fatal in card["fatal"].items():
        if is_fatal and d in scores and scores[d] > 4:
            out.append((FAIL, f"dimension {d} is marked fatal-flag=yes but scored {scores[d]} (>4)"))
        if is_fatal and d not in blocking_dims:
            out.append((WARN, f"dimension {d} marked fatal-flag=yes but no blocking finding "
                              "documents it in the register (add a verbatim span)"))

    decision = card["decision"]
    if decision is None:
        out.append((FAIL, "no `Decision: PASS / NOT PASS` line found"))
    elif decision == "pass":
        if missing:
            out.append((FAIL, "declared PASS but not every dimension is scored"))
        else:
            below = [d for d in range(1, 8) if scores.get(d, 0) < 7]
            if below:
                out.append((FAIL, f"declared PASS but dimension(s) {below} score < 7"))
            if card["total"] is not None and card["total"] < 56:
                out.append((FAIL, f"declared PASS but total {card['total']} < 56"))
            if blocking_dims:
                out.append((FAIL, f"declared PASS but {len(blocking_dims)} blocking finding(s) remain"))

    if not any(lvl == FAIL for lvl, _ in out):
        out.append((OKAY, f"scorecard internally consistent (decision={decision})"))
    return out


def run(workspace: Path) -> list[tuple[str, str]]:
    card = workspace / REL_CARD
    if not card.exists():
        return [(INFO, f"no {REL_CARD} yet (quality gate not reached — nothing to check)")]
    return validate_card(card.read_text(encoding="utf-8"))


def render(findings: list[tuple[str, str]]) -> str:
    lines = ["", "Paper-WorkFlow L2 review-scorecard verifier", "=" * 60]
    for lvl, msg in findings:
        lines.append(f"[{lvl:<4}] {msg}")
    lines.append("=" * 60)
    fails = [m for lvl, m in findings if lvl == FAIL]
    lines.append(f"RESULT: {len(fails)} hard inconsistency(ies) -> scorecard NOT verified"
                 if fails else "RESULT: scorecard internally consistent")
    return "\n".join(lines)


_GOOD = """# Draft Quality Gate Scorecard
## Dimension Scores
| Dimension | Score / 10 | Evidence | Fatal flag? |
|---|---:|---|---|
| 1. Contribution sharpness | 8 | sec1 | no |
| 2. Identification credibility | 8 | fig2 | no |
| 3. Robustness completeness | 8 | rob | no |
| 4. Interpretation discipline | 8 | t3 | no |
| 5. Writing and structure | 8 | intro | no |
| 6. Citation fidelity and positioning | 8 | refs | no |
| 7. Reproducibility and governance | 8 | repro | no |
| Total | 56 / 70 |  |  |
## Findings Register
| ID | Severity | Dim | Verbatim evidence span | Locator | Required fix |
|---|---|---:|---|---|---|
| F1 | minor | 5 | "the transition in section 4 is abrupt" | main.tex:88 | smooth it |
## Pass Decision
- Decision: PASS
"""


def _selftest() -> int:
    assert not [m for lvl, m in validate_card(_GOOD) if lvl == FAIL], \
        [m for lvl, m in validate_card(_GOOD) if lvl == FAIL]

    # declared PASS but a dimension < 7
    low = _GOOD.replace("| 3. Robustness completeness | 8 |", "| 3. Robustness completeness | 6 |") \
               .replace("| Total | 56 / 70 |", "| Total | 54 / 70 |")
    fails = [m for lvl, m in validate_card(low) if lvl == FAIL]
    assert any("dimension(s) [3] score < 7" in m for m in fails), fails

    # blocking finding but PASS declared, and dimension scored > 4
    blk = _GOOD.replace('| F1 | minor | 5 | "the transition in section 4 is abrupt" | main.tex:88 | smooth it |',
                        '| F1 | blocking | 2 | "we estimate the causal effect" | main.tex:12 | soften |')
    fails = [m for lvl, m in validate_card(blk) if lvl == FAIL]
    assert any("blocking finding" in m and ">4" in m for m in fails), fails
    assert any("declared PASS but" in m and "blocking" in m for m in fails), fails

    # finding missing its verbatim span
    nov = _GOOD.replace('"the transition in section 4 is abrupt"', "<exact sentence>")
    assert any("verbatim evidence span is empty/placeholder" in m
               for lvl, m in validate_card(nov) if lvl == FAIL)

    # bad severity
    bad = _GOOD.replace("| F1 | minor |", "| F1 | nit |")
    assert any("severity 'nit' not in" in m for lvl, m in validate_card(bad) if lvl == FAIL)

    # missing a dimension score
    miss = _GOOD.replace("| 7. Reproducibility and governance | 8 | repro | no |", "")
    assert any("missing numeric score" in m for lvl, m in validate_card(miss) if lvl == FAIL)

    # no decision line
    nodec = _GOOD.replace("- Decision: PASS", "- Decision: ")
    assert any("no `Decision:" in m for lvl, m in validate_card(nodec) if lvl == FAIL)

    # NOT PASS with a low dimension is consistent (stricter is fine)
    notpass = low.replace("- Decision: PASS", "- Decision: NOT PASS")
    assert not [m for lvl, m in validate_card(notpass) if lvl == FAIL], \
        [m for lvl, m in validate_card(notpass) if lvl == FAIL]

    # workspace mode: missing card -> INFO, no fail
    with tempfile.TemporaryDirectory(prefix="scorecard-selftest-") as tmp:
        ws = Path(tmp)
        assert not any(lvl == FAIL for lvl, _ in run(ws))
        (ws / "00_meta").mkdir(parents=True)
        (ws / "00_meta" / "quality_scorecard.md").write_text(_GOOD, encoding="utf-8")
        assert not [m for lvl, m in run(ws) if lvl == FAIL]

    print("selftest OK: L2 review-scorecard verifier invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("workspace", nargs="?", help="path to the paper_workspace/<run> directory")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p.add_argument("--selftest", action="store_true", help="verify this checker on synthetic inputs")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.workspace:
        p.error("workspace path is required (or pass --selftest)")

    findings = run(Path(args.workspace).expanduser().resolve())
    fails = [m for lvl, m in findings if lvl == FAIL]
    if args.json:
        print(json.dumps({"ok": not fails,
                          "findings": [{"level": l, "detail": m} for l, m in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print(render(findings))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
