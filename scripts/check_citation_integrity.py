#!/usr/bin/env python3
"""Validate a paper workspace's citation_integrity_log.md.

Scope: the *user's paper* citation/temporal/faithfulness log
(`00_meta/citation_integrity_log.md`), NOT the skill's own `_verification_log/`
(that is checked by `check_verification_log.py`). See
`references/citation-and-temporal-integrity.md`.

Usage:
    python3 scripts/check_citation_integrity.py <workspace>      # gate check
    python3 scripts/check_citation_integrity.py <workspace> --final   # Stage 9 terminal check
    python3 scripts/check_citation_integrity.py --selftest       # checker invariants
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LOG_RELPATH = "00_meta/citation_integrity_log.md"

# §1 citation existence/correctness and §2 temporal integrity are this layer's
# own territory and are required. §3 claim-to-source faithfulness is owned by the
# separate claim-integrity audit (`claim_integrity_audit.md`); if a project keeps
# a faithfulness table in this same log it is validated too, but it is optional.
REQUIRED_SECTIONS = [
    "Citation Verification",
    "Temporal Integrity",
]

CITATION_STATUS = {"verified", "to-verify", "flagged"}
SUPPORT_TYPES = {"direct", "paraphrase", "inference", "contested"}
CONCLUSIONS = {"pass", "na", "risk"}


def _is_placeholder(cell: str) -> bool:
    """A scaffolding/option cell, not a real asserted value."""
    c = cell.strip().strip("`").strip()
    if not c:
        return True
    if "<" in c and ">" in c:
        return True
    # enumerated option cells like "verified / to-verify / flagged"
    if "/" in c and len(c.split()) > 1:
        return True
    return False


def _parse_tables(text: str) -> list[list[dict[str, str]]]:
    """Return a list of tables; each table is a list of row dicts keyed by header."""
    tables: list[list[dict[str, str]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            block: list[str] = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            if len(block) >= 2 and set(block[1].replace("|", "").strip()) <= set("-: "):
                header = [c.strip().lower() for c in block[0].strip("|").split("|")]
                rows: list[dict[str, str]] = []
                for raw in block[2:]:
                    cells = [c.strip() for c in raw.strip("|").split("|")]
                    if len(cells) != len(header):
                        continue
                    rows.append(dict(zip(header, cells)))
                tables.append(rows)
        else:
            i += 1
    return tables


def _col(header: list[str], *needles: str) -> str | None:
    for h in header:
        for n in needles:
            if n in h:
                return h
    return None


def validate_text(text: str, final: bool = False) -> list[str]:
    errors: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing required section: {section}")

    tables = _parse_tables(text)
    asserted_citations = 0

    for rows in tables:
        if not rows:
            continue
        header = list(rows[0].keys())

        status_col = _col(header, "status")
        support_col = _col(header, "support type")
        concl_col = _col(header, "conclusion")

        if status_col:
            note_col = _col(header, "note", "disposition")
            for r in rows:
                val = r.get(status_col, "").strip().strip("`")
                if _is_placeholder(val):
                    continue
                if val not in CITATION_STATUS:
                    errors.append(f"citation row: invalid status {val!r}")
                    continue
                asserted_citations += 1
                note = r.get(note_col, "").strip() if note_col else ""
                if val == "flagged" and _is_placeholder(note):
                    errors.append("flagged citation must record a disposition")
                if val == "to-verify" and _is_placeholder(note):
                    errors.append("to-verify citation must say what remains to verify")
                if final and val == "to-verify":
                    errors.append("--final: citation still to-verify")
                if final and val == "flagged" and _is_placeholder(note):
                    errors.append("--final: flagged citation not dispositioned")

        elif support_col:
            span_col = _col(header, "source span")
            for r in rows:
                val = r.get(support_col, "").strip()
                if _is_placeholder(val):
                    continue
                if val not in SUPPORT_TYPES:
                    errors.append(f"faithfulness row: invalid support type {val!r}")
                if span_col and _is_placeholder(r.get(span_col, "")):
                    errors.append("faithfulness claim missing a source span")

        elif concl_col:
            conseq_col = _col(header, "consequence")
            for r in rows:
                val = r.get(concl_col, "").strip()
                if _is_placeholder(val):
                    continue
                if val not in CONCLUSIONS:
                    errors.append(f"temporal row: invalid conclusion {val!r}")
                if val == "risk" and conseq_col and _is_placeholder(r.get(conseq_col, "")):
                    errors.append("temporal risk row must record a consequence")

    if final and asserted_citations == 0:
        errors.append("--final: no verified citations asserted in the log")

    return errors


def validate_workspace(workspace: Path, final: bool = False) -> list[str]:
    log = workspace / LOG_RELPATH
    if not log.exists():
        return [f"missing {LOG_RELPATH} under {workspace}"]
    return validate_text(log.read_text(encoding="utf-8"), final=final)


_GOOD = """
## 1. Citation Verification
| Bibkey | Cited claim | Identifier | Metadata match | Version | Retraction/erratum | Status | Checked | Note |
|---|---|---|---|---|---|---|---|---|
| smith2020 | green credit raises R&D | 10.1/x | ok | published | clean | verified | 2026-06-22 | ok |
| jones2019 | weak IV warning | 10.1/y | ok | wp | clean | flagged | 2026-06-22 | 换更权威源 done |

## 2. Temporal Integrity
| Risk | Source | Requirement met? | Conclusion | Consequence if risk |
|---|---|---|---|---|
| Feature look-ahead | CSMAR | yes | pass | na |
| Vintage vs final | FRED-MD | partial | risk | add real-time robustness |

## 3. Claim-to-Source Faithfulness
| Claim ID | Manuscript loc | Claim wording | Source | Source span | Support type | Overclaim? | Fix |
|---|---|---|---|---|---|---|---|
| L1 | intro | prior work finds positive link | smith2020 | p.5 | paraphrase | no | na |
"""

_BAD = """
## 1. Citation Verification
| Bibkey | Cited claim | Identifier | Metadata match | Version | Retraction/erratum | Status | Checked | Note |
|---|---|---|---|---|---|---|---|---|
| smith2020 | x | 10.1/x | ok | published | clean | bogus | 2026-06-22 | ok |
| jones2019 | y | 10.1/y | ok | wp | clean | flagged | 2026-06-22 |  |

## 2. Temporal Integrity
| Risk | Source | Requirement met? | Conclusion | Consequence if risk |
|---|---|---|---|---|
| Vintage vs final | FRED-MD | no | risk |  |

## 3. Claim-to-Source Faithfulness
| Claim ID | Manuscript loc | Claim wording | Source | Source span | Support type | Overclaim? | Fix |
|---|---|---|---|---|---|---|---|
| L1 | intro | strong claim | smith2020 | p.5 | wishful | no | na |
"""


def selftest() -> None:
    assert not validate_text(_GOOD), validate_text(_GOOD)
    assert not validate_text(_GOOD, final=True), validate_text(_GOOD, final=True)

    bad = validate_text(_BAD)
    assert any("invalid status" in e for e in bad), bad
    assert any("flagged citation must record a disposition" in e for e in bad), bad
    assert any("temporal risk row must record a consequence" in e for e in bad), bad
    assert any("invalid support type" in e for e in bad), bad

    # a to-verify log is fine pre-final but fails --final
    tv = _GOOD.replace("| verified | 2026-06-22 | ok |", "| to-verify | 2026-06-22 | 待 reference-verify |")
    assert not validate_text(tv), validate_text(tv)
    assert any("to-verify" in e for e in validate_text(tv, final=True))

    # missing a required section is caught
    assert any("missing required section" in e for e in validate_text("## 1. Citation Verification\n"))
    print("selftest OK: citation-integrity checker invariants hold")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="?", help="paper workspace directory")
    parser.add_argument("--final", action="store_true", help="Stage 9 terminal check")
    parser.add_argument("--selftest", action="store_true", help="run checker self-tests")
    args = parser.parse_args()

    if args.selftest:
        selftest()
        return 0

    if not args.workspace:
        parser.error("workspace path required (or use --selftest)")

    errors = validate_workspace(Path(args.workspace), final=args.final)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("citation integrity log OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
