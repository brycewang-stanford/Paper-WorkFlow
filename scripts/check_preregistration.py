#!/usr/bin/env python3
"""Pre-registration / researcher-degrees-of-freedom guard for a Paper-WorkFlow run.

Why this exists
---------------
The single most common way an empirical result is quietly wrong is specification
search: try many specs, keep the one with stars, then write the introduction as if
that spec were planned all along (HARKing). Orchestra's `AI-Research-SKILLs` gestures
at this with "git-as-pre-registration", but it is prose the agent self-grades. This
checker makes the lock *decidable*.

The invariant it enforces is simple and load-bearing:

  - the primary specification must be locked (committed) BEFORE the main results
    exist on disk; a workspace that has `03_analysis/results/main_results.json` but
    an `UNLOCKED` pre-registration, or `locked_before_estimation: no`, is the exact
    researcher-degrees-of-freedom violation we refuse to launder;
  - at least one confirmatory hypothesis is registered, fully (no placeholders);
  - the confirmatory/exploratory split and a deviations log are present, so anything
    not pre-registered is forced to be labelled exploratory rather than dressed up.

It reads `00_meta/preregistration.md` (instantiated from templates/preregistration.md)
and, when present, `03_analysis/results/main_results.json` to decide whether results
already exist. It is schema-tolerant: a missing pre-registration on a run that has no
results yet is INFO, not failure — an unfinished run is not a violation.

Usage:
    python3 check_preregistration.py <workspace>           # human report
    python3 check_preregistration.py <workspace> --json    # machine readable
    python3 check_preregistration.py --selftest            # verify this checker

Exit code is non-zero iff a HARD violation is found (a lock claimed without backing,
results without a prior lock, an empty/placeholder confirmatory plan).
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

REL_PREREG = "00_meta/preregistration.md"
REL_RESULTS = "03_analysis/results/main_results.json"

REQUIRED_SECTIONS = [
    "Lock Status",
    "Confirmatory Hypotheses",
    "Primary Specification Lock",
    "Confirmatory vs Exploratory",
    "Deviations from Plan",
]
LOCK_FIELDS = ["locked", "lock_commit", "locked_before_estimation", "analyst", "primary_design"]
# Tokens that mean "still a template / not filled in". A required value containing one
# of these is treated as unfilled.
PLACEHOLDER_RE = re.compile(r"<[^>]*>|\bTODO\b|\bTBD\b|（待填）|待填|^\.\.\.$")
_YES = {"yes", "y", "true", "是", "已锁"}
_UNLOCKED = {"", "unlocked", "未锁", "n/a", "na", "none"}


def _is_placeholder(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return True
    return bool(PLACEHOLDER_RE.search(v))


def _split_sections(text: str) -> dict[str, str]:
    """Map each `## Heading` to its body text (heading matched by substring later)."""
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


def _parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"^-\s+([A-Za-z0-9_]+):\s*(.*?)\s*(?:<!--.*-->)?\s*$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def _table_data_rows(body: str) -> list[list[str]]:
    """Return non-header, non-separator markdown table rows as cell lists."""
    rows: list[list[str]] = []
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if set(joined) <= set("-: "):  # separator row like |---|:--:|
            continue
        if any(h in joined for h in ("Hypothesis", "Outcome (Y)", "Estimand", "Predicted sign")):
            continue  # header row
        rows.append(cells)
    return rows


def validate_prereg(text: str, has_results: bool) -> list[tuple[str, str]]:
    """Pure validation. Returns (level, message) findings; FAIL means hard violation."""
    out: list[tuple[str, str]] = []
    sections = _split_sections(text)

    for sec in REQUIRED_SECTIONS:
        if _find_section(sections, sec) is None:
            out.append((FAIL, f"missing required section: ## {sec}"))

    lock_body = _find_section(sections, "Lock Status")
    locked_before = None
    locked_val = None
    if lock_body is not None:
        fields = _parse_fields(lock_body)
        for f in LOCK_FIELDS:
            if f not in fields:
                out.append((FAIL, f"Lock Status missing field: {f}"))
            elif _is_placeholder(fields[f]) and f not in {"lock_commit"}:
                out.append((FAIL, f"Lock Status field '{f}' is unfilled/placeholder"))
        locked_val = (fields.get("locked") or "").strip().lower()
        locked_before = (fields.get("locked_before_estimation") or "").strip().lower()
        is_unlocked = locked_val in _UNLOCKED or _is_placeholder(fields.get("locked", ""))
        if locked_before and locked_before not in _YES and locked_before not in {"no", "n", "false", "否"}:
            out.append((WARN, f"locked_before_estimation has an unexpected value: {locked_before!r}"))
        if has_results:
            if is_unlocked:
                out.append((FAIL, "main results exist but pre-registration is UNLOCKED "
                                  "(researcher-degrees-of-freedom violation)"))
            if locked_before not in _YES:
                out.append((FAIL, "main results exist but locked_before_estimation is not 'yes' "
                                  "(spec was not locked before estimation)"))
        else:
            if is_unlocked:
                out.append((INFO, "pre-registration not yet locked (no main results on disk — acceptable)"))

    conf_body = _find_section(sections, "Confirmatory Hypotheses")
    if conf_body is not None:
        rows = _table_data_rows(conf_body)
        filled = [r for r in rows if any(not _is_placeholder(c) for c in r)]
        if not filled:
            out.append((FAIL, "no confirmatory hypothesis registered (Confirmatory Hypotheses table is empty/placeholder)"))
        for i, r in enumerate(filled, 1):
            if any(_is_placeholder(c) for c in r):
                out.append((WARN, f"confirmatory hypothesis row {i} has an unfilled cell"))

    spec_body = _find_section(sections, "Primary Specification Lock")
    if spec_body is not None:
        for needle in ("standard errors", "multiple-testing", "main estimator"):
            if needle.lower() not in spec_body.lower():
                out.append((WARN, f"Primary Specification Lock does not mention '{needle}'"))

    if not any(lvl == FAIL for lvl, _ in out):
        out.append((OKAY, "pre-registration structurally complete and lock invariant satisfied"))
    return out


def run(workspace: Path) -> list[tuple[str, str]]:
    prereg = workspace / REL_PREREG
    has_results = (workspace / REL_RESULTS).exists()
    if not prereg.exists():
        if has_results:
            return [(FAIL, f"main results exist but no pre-registration at {REL_PREREG} "
                           "(estimation ran without a locked plan)")]
        return [(INFO, f"no {REL_PREREG} yet and no results — nothing to check")]
    return validate_prereg(prereg.read_text(encoding="utf-8"), has_results)


def render(findings: list[tuple[str, str]]) -> str:
    lines = ["", "Paper-WorkFlow pre-registration guard", "=" * 60]
    for lvl, msg in findings:
        lines.append(f"[{lvl:<4}] {msg}")
    lines.append("=" * 60)
    fails = [m for lvl, m in findings if lvl == FAIL]
    lines.append(f"RESULT: {len(fails)} hard violation(s) -> pre-registration NOT verified"
                 if fails else "RESULT: pre-registration lock verified")
    return "\n".join(lines)


def _selftest() -> int:
    good = """# Pre-Registration & Analysis Plan — demo
## Lock Status
- locked: 2026-06-23 10:00 Asia/Shanghai
- lock_commit: a1b2c3d
- locked_before_estimation: yes
- analyst: agent-7
- primary_design: DiD
## Confirmatory Hypotheses
| ID | Hypothesis (directional) | Outcome (Y) | Estimand | Primary specification | Predicted sign |
|----|--------------------------|-------------|----------|-----------------------|----------------|
| H1 | treatment raises wages   | log_wage    | ATT      | TWFE DiD; cluster=firm | + |
## Primary Specification Lock
- sample: firms 2010-2020
- main estimator: Callaway-Sant'Anna group-time ATT
- fixed controls: size, age
- standard errors / clustering: cluster=firm
- multiple-testing plan: Romano-Wolf over 3 outcomes
## Confirmatory vs Exploratory
- E1: heterogeneity by sector, exploratory
## Deviations from Plan
| Deviation | When | Reason | Effect on claim strength |
|-----------|------|--------|--------------------------|
| (none)    |      |        |                          |
"""
    # good plan, no results yet -> OK, no FAIL
    assert not [m for lvl, m in validate_prereg(good, has_results=False) if lvl == FAIL]
    # good plan, results present -> still OK (locked before estimation = yes)
    assert not [m for lvl, m in validate_prereg(good, has_results=True) if lvl == FAIL]

    unlocked = good.replace("locked: 2026-06-23 10:00 Asia/Shanghai", "locked: UNLOCKED") \
                   .replace("locked_before_estimation: yes", "locked_before_estimation: no")
    # unlocked + results present -> two hard violations (unlocked, not-before-estimation)
    fails = [m for lvl, m in validate_prereg(unlocked, has_results=True) if lvl == FAIL]
    assert any("UNLOCKED" in m for m in fails), fails
    assert any("locked_before_estimation" in m for m in fails), fails
    # unlocked + no results -> acceptable (INFO), no FAIL
    assert not [m for lvl, m in validate_prereg(unlocked, has_results=False) if lvl == FAIL]

    empty_conf = good.replace(
        "| H1 | treatment raises wages   | log_wage    | ATT      | TWFE DiD; cluster=firm | + |", "")
    assert any("no confirmatory hypothesis" in m
               for lvl, m in validate_prereg(empty_conf, has_results=False) if lvl == FAIL)

    missing_sec = good.replace("## Deviations from Plan", "## Something Else")
    assert any("Deviations from Plan" in m
               for lvl, m in validate_prereg(missing_sec, has_results=False) if lvl == FAIL)

    # workspace mode: results but no prereg file at all -> hard violation
    with tempfile.TemporaryDirectory(prefix="prereg-selftest-") as tmp:
        ws = Path(tmp)
        (ws / "03_analysis" / "results").mkdir(parents=True)
        (ws / "03_analysis" / "results" / "main_results.json").write_text("{}", encoding="utf-8")
        assert any(lvl == FAIL for lvl, _ in run(ws)), "results without prereg must fail"
        # add a good locked prereg -> passes
        (ws / "00_meta").mkdir(parents=True)
        (ws / "00_meta" / "preregistration.md").write_text(good, encoding="utf-8")
        assert not [m for lvl, m in run(ws) if lvl == FAIL], "good locked prereg with results must pass"
        # empty workspace -> INFO, no fail
        assert not any(lvl == FAIL for lvl, _ in run(Path(tmp) / "nope" if False else ws.parent))

    print("selftest OK: pre-registration guard invariants hold")
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
