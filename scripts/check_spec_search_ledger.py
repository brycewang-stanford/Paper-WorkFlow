#!/usr/bin/env python3
"""Specification-search ledger guard: count the forking paths an agent walked.

Why this exists
---------------
`check_preregistration.py` asks whether the primary specification was locked
before estimation. That is necessary but, for an *agent*, not sufficient. A
human analyst tires after a few dozen regressions; an agent can run five
hundred in an hour, and the garden of forking paths (Gelman & Loken 2013;
Simmons, Nelson & Simonsohn 2011) grows with every cheap call. A lock says
which path was planned; it does not say how many other paths were tried
before the write-up chose one. Brodeur et al. (2016, 2020) document the bunching
of published z-statistics just above 1.96 that such search produces.

So every estimate the agent runs is appended to one ledger, and this checker
turns that ledger into three load-bearing invariants:

  - every row is complete: id, timestamp, hypothesis, origin, p-value;
  - a headline result is either `preregistered`, or it carries an explicit
    `disclosed_exploratory` flag -- an exploratory spec cannot be promoted to
    the headline silently;
  - the disclosure file states the number of specifications actually run, and
    that number equals the ledger's row count, so the manuscript cannot
    report "we estimated 6 models" over a ledger of 240.

It also prints, for each headline, a Bonferroni-bounded p-value over the
non-preregistered search on the same hypothesis. A search-adjusted p above 0.05
is WARN (the reader deserves to know), not FAIL: the honest number is the point,
not a verdict on the paper.

Files (all under the workspace):
    03_analysis/spec_search_ledger.csv
        spec_id,run_at,hypothesis,origin,p_value,headline[,disclosed_exploratory]
        origin in {preregistered, robustness, exploratory}
    03_analysis/spec_search_disclosure.md
        must contain a line `specifications_run: <N>`

Usage:
    python3 check_spec_search_ledger.py <workspace>
    python3 check_spec_search_ledger.py <workspace> --json
    python3 check_spec_search_ledger.py --selftest

Exit code is non-zero iff a HARD violation is found. A workspace with no main
results yet and no ledger is INFO: an unfinished run is not a violation.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
from pathlib import Path

FAIL = "FAIL"
WARN = "WARN"
INFO = "INFO"
OKAY = "OK"

REL_LEDGER = "03_analysis/spec_search_ledger.csv"
REL_DISCLOSURE = "03_analysis/spec_search_disclosure.md"
REL_RESULTS = "03_analysis/results/main_results.json"

REQUIRED_COLUMNS = ["spec_id", "run_at", "hypothesis", "origin", "p_value", "headline"]
ORIGINS = {"preregistered", "robustness", "exploratory"}
TRUE = {"1", "true", "yes", "y"}
RUN_COUNT_RE = re.compile(r"specifications_run\s*:\s*(\d+)", re.IGNORECASE)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUE


def audit(ws: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    ledger = ws / REL_LEDGER
    has_results = (ws / REL_RESULTS).exists()

    if not ledger.exists():
        if has_results:
            findings.append((FAIL, f"main results exist but {REL_LEDGER} does not: "
                             "the number of specifications tried is unknowable"))
        else:
            findings.append((INFO, "no ledger and no main results yet: nothing to audit"))
        return findings

    with ledger.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            return [(FAIL, f"ledger is missing columns: {', '.join(missing)}")]
        rows = list(reader)

    if not rows:
        findings.append((FAIL if has_results else INFO, "ledger has no rows"))
        return findings

    seen: set[str] = set()
    for i, row in enumerate(rows, start=2):
        sid = (row.get("spec_id") or "").strip()
        blanks = [c for c in REQUIRED_COLUMNS if c != "headline" and not (row.get(c) or "").strip()]
        if blanks:
            findings.append((FAIL, f"line {i}: blank {', '.join(blanks)}"))
        if sid in seen:
            findings.append((FAIL, f"line {i}: duplicate spec_id {sid!r}"))
        seen.add(sid)
        origin = (row.get("origin") or "").strip().lower()
        if origin and origin not in ORIGINS:
            findings.append((FAIL, f"line {i}: origin {origin!r} not in {sorted(ORIGINS)}"))
        try:
            p = float(row.get("p_value") or "nan")
            if not 0.0 <= p <= 1.0:
                raise ValueError
        except ValueError:
            findings.append((FAIL, f"line {i}: p_value is not a probability"))

    headlines = [r for r in rows if _truthy(r.get("headline"))]
    if not headlines:
        findings.append((WARN, "no row is marked headline: the manuscript's claim is untraceable"))
    for r in headlines:
        sid = r.get("spec_id", "?")
        origin = (r.get("origin") or "").strip().lower()
        if origin != "preregistered" and not _truthy(r.get("disclosed_exploratory")):
            findings.append((FAIL, f"headline {sid} is {origin or 'unlabelled'} but not "
                             "disclosed_exploratory: a searched spec was promoted silently"))
        hyp = (r.get("hypothesis") or "").strip()
        searched = sum(1 for x in rows if (x.get("hypothesis") or "").strip() == hyp
                       and (x.get("origin") or "").strip().lower() != "preregistered")
        try:
            p = float(r.get("p_value") or "nan")
        except ValueError:
            continue
        k = max(searched, 1)
        adj = min(1.0, p * k)
        level = WARN if adj > 0.05 and p <= 0.05 else INFO
        findings.append((level, f"headline {sid}: p={p:.4g}; Bonferroni bound over {k} "
                         f"searched spec(s) on {hyp!r} = {adj:.4g}"))

    disclosure = ws / REL_DISCLOSURE
    if not disclosure.exists():
        findings.append((FAIL, f"{REL_DISCLOSURE} missing: the search size is not disclosed"))
    else:
        m = RUN_COUNT_RE.search(disclosure.read_text(encoding="utf-8"))
        if not m:
            findings.append((FAIL, f"{REL_DISCLOSURE} has no `specifications_run: N` line"))
        elif int(m.group(1)) != len(rows):
            findings.append((FAIL, f"disclosure says {m.group(1)} specifications, "
                             f"ledger has {len(rows)}"))

    if not any(level == FAIL for level, _ in findings):
        findings.append((OKAY, f"{len(rows)} specification(s) ledgered and disclosed"))
    return findings


def _write(ws: Path, rows: list[str], disclosed: int | None, results: bool = True) -> None:
    (ws / "03_analysis/results").mkdir(parents=True, exist_ok=True)
    if results:
        (ws / REL_RESULTS).write_text("{}", encoding="utf-8")
    header = "spec_id,run_at,hypothesis,origin,p_value,headline,disclosed_exploratory\n"
    (ws / REL_LEDGER).write_text(header + "\n".join(rows) + "\n", encoding="utf-8")
    if disclosed is not None:
        (ws / REL_DISCLOSURE).write_text(f"specifications_run: {disclosed}\n", encoding="utf-8")


def _fails(ws: Path) -> int:
    return sum(1 for level, _ in audit(ws) if level == FAIL)


def _selftest() -> int:
    good = [
        "s1,2026-10-01T10:00,H1,preregistered,0.012,yes,",
        "s2,2026-10-01T10:05,H1,robustness,0.030,no,",
        "s3,2026-10-01T10:09,H1,exploratory,0.200,no,",
    ]
    cases = {
        "clean ledger passes": (good, 3, 0),
        "silent promotion fails": (
            [good[0].replace(",yes,", ",no,"), good[1], "s3,2026-10-01T10:09,H1,exploratory,0.004,yes,"], 3, 1),
        "disclosed exploratory headline passes": (
            [good[1], "s3,2026-10-01T10:09,H1,exploratory,0.004,yes,yes"], 2, 0),
        "under-reported search size fails": (good, 2, 1),
        "missing disclosure fails": (good, None, 1),
        "bad origin, bad p and silent headline fail": (["s1,2026-10-01T10:00,H1,fishing,1.7,yes,"], 1, 3),
        "duplicate id fails": ([good[0], good[0]], 2, 1),
    }
    with tempfile.TemporaryDirectory(prefix="specledger-selftest-") as tmp:
        for i, (name, (rows, disclosed, want)) in enumerate(cases.items()):
            ws = Path(tmp) / f"ws{i}"
            _write(ws, rows, disclosed)
            got = _fails(ws)
            if got != want:
                print(f"selftest FAIL: {name}: expected {want} FAIL(s), got {got}: {audit(ws)}")
                return 1

        empty = Path(tmp) / "empty"
        empty.mkdir()
        if _fails(empty) != 0:
            print("selftest FAIL: an unstarted workspace must not fail")
            return 1
        no_ledger = Path(tmp) / "no_ledger"
        (no_ledger / "03_analysis/results").mkdir(parents=True)
        (no_ledger / REL_RESULTS).write_text("{}", encoding="utf-8")
        if _fails(no_ledger) != 1:
            print("selftest FAIL: results without a ledger must fail")
            return 1

        wide = Path(tmp) / "wide"
        rows = ["s0,2026-10-01T10:00,H1,exploratory,0.010,yes,yes"] + [
            f"s{j},2026-10-01T10:{j:02d},H1,exploratory,0.4,no," for j in range(1, 40)]
        _write(wide, rows, 40)
        if not any(level == WARN and "Bonferroni" in msg for level, msg in audit(wide)):
            print("selftest FAIL: a p=0.01 found after 40 searched specs must WARN")
            return 1

    print("selftest OK: specification-search ledger invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("workspace", nargs="?", help="Paper-WorkFlow workspace root")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--selftest", action="store_true", help="verify this checker on synthetic inputs")
    args = p.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.workspace:
        p.error("workspace is required unless --selftest")
    findings = audit(Path(args.workspace))
    if args.json:
        print(json.dumps([{"level": lv, "message": m} for lv, m in findings], ensure_ascii=False, indent=2))
    else:
        for lv, m in findings:
            print(f"[{lv}] {m}")
    return 1 if any(lv == FAIL for lv, _ in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
