#!/usr/bin/env python3
"""
check_cn_claim_audit.py — CN-context claim audit gate for paper-workflow.

The two China-context references — `references/china-data-sources.md` and
`references/chinese-journals.md` — are claim-heavy (the week-recap called
this out explicitly). This checker turns that risk into explicit metadata:

  1. The ledger `_verification_log/cn-data-claims.md` must exist and have
     >= MIN_ROWS rows. Each row is a single auditable claim with a
     canonical / verified / to-verify status.
  2. The two reference files must each carry an "Audit status" banner
     pointing readers at the ledger. (A `--update-banners` flag
     regenerates the banners from the live ledger counts.)

Default gate threshold: ledger must have >= MIN_ROWS (currently 10) rows.
If the ledger falls below the threshold the script exits 1; otherwise it
exits 0 and prints a short summary.

Usage:
    python3 scripts/check_cn_claim_audit.py            # report; exit 0/1 per gate
    python3 scripts/check_cn_claim_audit.py --json     # machine-readable
    python3 scripts/check_cn_claim_audit.py --update-banners  # rewrite the audit banner in both references
    python3 scripts/check_cn_claim_audit.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "_verification_log" / "cn-data-claims.md"
CHINA_DATA_REFS = [
    ROOT / "references" / "china-data-sources.md",
    ROOT / "references" / "chinese-journals.md",
]

MIN_ROWS = 10
BANNER_MARKER = "<!-- CN-CLAIM-AUDIT-BANNER -->"
BANNER_TEMPLATE = (
    "{marker}\n"
    "## Claim audit status\n"
    "\n"
    "> The claims in this document are tracked in [`_verification_log/cn-data-claims.md`]"
    "({ledger_rel}). {total} claims logged as of {today}; full audit status"
    " (`canonical` / `verified` / `to-verify`) lives in the ledger.\n"
    "\n"
    "Run `python3 scripts/check_cn_claim_audit.py` for a live audit; the"
    " `--update-banners` flag rewrites this banner from the current"
    " ledger state. Coverage below the gate threshold ({min_rows} rows)"
    " is a blocking maintenance failure.\n"
    "{marker_end}\n"
)
BANNER_END = "<!-- /CN-CLAIM-AUDIT-BANNER -->"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _ledger_counts(ledger_text: str) -> dict:
    """Count entries by their `status:` tag."""
    statuses = {"canonical": 0, "verified": 0, "to-verify": 0}
    for line in ledger_text.splitlines():
        m = re.match(r"\s*-\s*status:\s*(\S+)", line)
        if m:
            tag = m.group(1).strip().lower()
            if tag in statuses:
                statuses[tag] += 1
    return {
        "total": sum(statuses.values()),
        **statuses,
    }


def _entry_rows(ledger_text: str) -> int:
    """Number of entry headers (e.g. '### C01 ...') in the ledger."""
    return sum(1 for line in ledger_text.splitlines() if re.match(r"\s*###\s+C\d+\b", line))


def build_report() -> dict:
    ledger_text = _read_text(LEDGER)
    counts = _ledger_counts(ledger_text)
    rows = _entry_rows(ledger_text)
    banners = {str(p): BANNER_MARKER in _read_text(p) for p in CHINA_DATA_REFS}
    gate_pass = (
        rows >= MIN_ROWS and all(banners.values())
    )
    return {
        "ledger_path": str(LEDGER),
        "ledger_exists": LEDGER.exists(),
        "ledger_rows": rows,
        "ledger_status_counts": counts,
        "min_rows": MIN_ROWS,
        "banners": banners,
        "gate_pass": gate_pass,
    }


def render_text(report: dict) -> str:
    ledger_present = "yes" if report["ledger_exists"] else "NO"
    rows = report["ledger_rows"]
    sc = report["ledger_status_counts"]
    lines = [
        "Paper-WorkFlow CN-claim audit",
        "--------------------------",
        f"ledger            : {report['ledger_path']}",
        f"ledger present    : {ledger_present}",
        f"entry rows        : {rows} (min {report['min_rows']})",
        f"status counts     : canonical={sc['canonical']}  "
        f"verified={sc['verified']}  to-verify={sc['to-verify']}",
        "banners:",
    ]
    for ref, present in report["banners"].items():
        marker = "OK " if present else "MISSING"
        lines.append(f"  [{marker}] {ref}")
    lines.append("")
    lines.append("GATE PASS" if report["gate_pass"] else "GATE FAIL")
    return "\n".join(lines) + "\n"


def update_banners() -> int:
    ledger_text = _read_text(LEDGER)
    counts = _ledger_counts(ledger_text)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = BANNER_TEMPLATE.format(
        marker=BANNER_MARKER,
        ledger_rel="../_verification_log/cn-data-claims.md",
        total=counts["total"],
        today=today,
        min_rows=MIN_ROWS,
        marker_end=BANNER_END,
    )
    for ref in CHINA_DATA_REFS:
        if not ref.exists():
            continue
        text = _read_text(ref)
        # Replace an existing banner block, otherwise insert after the first
        # blockquote (`>`) or after the first heading.
        pattern = re.compile(
            re.escape(BANNER_MARKER) + r".*?" + re.escape(BANNER_END) + r"\n*",
            re.DOTALL,
        )
        new_text, n = pattern.subn(body, text)
        if n == 0:
            # Insert after the first blockquote or first heading.
            lines = text.splitlines(keepends=True)
            insert_at = 0
            for i, line in enumerate(lines[:30]):
                if line.startswith(">") or line.startswith("#"):
                    insert_at = i + 1
            lines.insert(insert_at, "\n" + body)
            new_text = "".join(lines)
        ref.write_text(new_text, encoding="utf-8")
    return 0


def _selftest() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="cn-claim-audit-selftest-") as tmp:
        root = Path(tmp)
        # Build a fake ledger with 60 status rows
        ledger = root / "_verification_log" / "cn-data-claims.md"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            f"### C{idx:02d} · fake claim {idx}\n"
            f"- status: {'verified' if idx % 3 == 0 else 'to-verify' if idx % 3 == 1 else 'canonical'}\n"
            f"- used-in: ref.md\n"
            f"- claim: example claim {idx}\n"
            for idx in range(60)
        ]
        ledger.write_text("# ledger\n\n" + "\n".join(rows))

        good_ref = root / "ref.md"
        good_ref.write_text("# ref\n\n> initial quote\n")

        # Pretend ROOT by monkey-patching the module's constants
        old_ledger = LEDGER
        old_refs = list(CHINA_DATA_REFS)
        try:
            # Step 1: build banner on good_ref so the gate has all banners present.
            globals()["LEDGER"] = ledger
            globals()["CHINA_DATA_REFS"] = [good_ref]
            update_banners()
            good_report = build_report()
            assert good_report["gate_pass"], "60-row ledger with banner must pass"
            assert good_report["ledger_rows"] == 60

            # Step 2: drop to 5 rows (below MIN_ROWS=10) -> gate must fail
            ledger.write_text("# ledger\n\n" + "".join(rows[:5]))
            bad_report = build_report()
            assert not bad_report["gate_pass"], "5-row ledger must fail"
        finally:
            globals()["LEDGER"] = old_ledger
            globals()["CHINA_DATA_REFS"] = old_refs

    print("selftest OK: cn-claim-audit invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--update-banners",
        action="store_true",
        help="rewrite the audit-status banner in both China-context references",
    )
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.update_banners:
        return update_banners()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))
    return 0 if report["gate_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())