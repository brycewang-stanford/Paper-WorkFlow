#!/usr/bin/env python3
"""
check_chaos_coverage.py — verify every documented failure mode has a chaos test.

The orchestrator documents several failure modes in
`SKILL.md` (multi-agent + context-protection protocol), in
`references/skill-map.md` §0 (Skill vs. Read fallback), and in
`references/orchestration-and-handoff.md` (handoff / fresh evidence /
runtime discipline). For each documented failure mode there should be a
matching `evals/chaos/<scenario>.md` file describing:
  - the trigger
  - the expected recovery path
  - the maintenance check

This script enforces the mapping. The contract is "advisory first" --
exit code is non-zero only when the `--strict` flag is set, so a brand-new
chaos folder can pass with zero coverage and improve over time without
breaking the main gate. With `--strict`, the script fails when any
documented failure mode lacks a chaos scenario.

The failure-mode list is intentionally hardcoded. New failure modes
should be added in three places:
  1. this script (FAILURE_MODES list)
  2. the corresponding prose in SKILL.md / references/*.md
  3. an evals/chaos/<scenario>.md file

Usage:
    python3 scripts/check_chaos_coverage.py            # report; exit 0 (advisory)
    python3 scripts/check_chaos_coverage.py --strict  # exit 1 if any failure mode lacks a scenario
    python3 scripts/check_chaos_coverage.py --selftest
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAOS_DIR = ROOT / "evals" / "chaos"
SKILL_MD = ROOT / "SKILL.md"
SKILL_MAP = ROOT / "references" / "skill-map.md"
ORCH_HANDOFF = ROOT / "references" / "orchestration-and-handoff.md"

# Each entry: (failure_mode_id, scenario_filename, regex anchors that
# the prose must mention for the failure mode to be considered
# "documented"). The list is intentionally small and stable; new failure
# modes go in the next entry.
FAILURE_MODES = [
    {
        "id": "skill_not_found",
        "scenario": "chaos_skill_not_found.md",
        "anchors": [
            (SKILL_MAP, r"not[\- ]found"),
            (SKILL_MAP, r"Skill.*[Rr]ead|稳路径|inline"),
        ],
    },
    {
        "id": "subagent_failure",
        "scenario": "chaos_subagent_failure.md",
        "anchors": [
            (SKILL_MD, r"子代理自己写盘|主代理只持有指针与状态|≤\s*10\s*行"),
            (ORCH_HANDOFF, r"handoff|fresh evidence|fresh_evidence"),
        ],
    },
    {
        "id": "context_overflow",
        "scenario": "chaos_context_overflow.md",
        "anchors": [
            (SKILL_MD, r"上下文保护|context[- ]protection|主代理上下文"),
            (ORCH_HANDOFF, r"context|上下文"),
        ],
    },
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _anchor_present(path: Path, pattern: str) -> bool:
    return bool(re.search(pattern, _read(path)))


def _scenario_present(filename: str) -> bool:
    return (CHAOS_DIR / filename).is_file()


def build_coverage() -> dict:
    rows = []
    documented = 0
    scenarios = 0
    for entry in FAILURE_MODES:
        doc_ok = all(_anchor_present(p, pat) for p, pat in entry["anchors"])
        scen_ok = _scenario_present(entry["scenario"])
        if doc_ok:
            documented += 1
        if scen_ok:
            scenarios += 1
        rows.append(
            {
                "id": entry["id"],
                "scenario": entry["scenario"],
                "documented_in_prose": doc_ok,
                "scenario_present": scen_ok,
                "covered": doc_ok and scen_ok,
            }
        )
    return {
        "chaos_dir": str(CHAOS_DIR),
        "total_failure_modes": len(FAILURE_MODES),
        "documented": documented,
        "scenarios_present": scenarios,
        "covered": sum(1 for r in rows if r["covered"]),
        "rows": rows,
    }


def render_text(cov: dict) -> str:
    lines = [
        "Paper-WorkFlow chaos coverage",
        "-------------------------",
        f"chaos dir      : {cov['chaos_dir']}",
        f"failure modes  : {cov['total_failure_modes']}",
        f"documented     : {cov['documented']}",
        f"scenarios      : {cov['scenarios_present']}",
        f"fully covered  : {cov['covered']}",
        "",
    ]
    for r in cov["rows"]:
        doc = "OK " if r["documented_in_prose"] else "?? "
        scen = "OK " if r["scenario_present"] else "?? "
        cov_mark = "OK" if r["covered"] else "??"
        lines.append(f"  [{doc}] [{scen}] [{cov_mark}] {r['id']:<22} {r['scenario']}")
    lines.append("")
    if cov["covered"] == cov["total_failure_modes"]:
        lines.append("OK -- every documented failure mode has a chaos scenario.")
    else:
        missing = [r["id"] for r in cov["rows"] if not r["covered"]]
        lines.append(
            f"GAP -- {len(missing)} failure mode(s) without coverage: {', '.join(missing)}"
        )
    return "\n".join(lines) + "\n"


def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="chaos-cov-selftest-") as tmp:
        root = Path(tmp)
        # Build a fake orchestrator tree
        (root / "SKILL.md").write_text("上下文保护 subagent ≤10 行 handoff", encoding="utf-8")
        (root / "references").mkdir()
        (root / "references" / "skill-map.md").write_text("not found Read inline", encoding="utf-8")
        (root / "references" / "orchestration-and-handoff.md").write_text(
            "handoff fresh evidence context", encoding="utf-8"
        )
        (root / "evals" / "chaos").mkdir(parents=True)
        for entry in FAILURE_MODES:
            (root / "evals" / "chaos" / entry["scenario"]).write_text(
                "# placeholder\n", encoding="utf-8"
            )

        # Monkey-patch the module's constants
        old_chaos = CHAOS_DIR
        old_skill = SKILL_MD
        old_skillmap = SKILL_MAP
        old_orch = ORCH_HANDOFF
        try:
            globals()["CHAOS_DIR"] = root / "evals" / "chaos"
            globals()["SKILL_MD"] = root / "SKILL.md"
            globals()["SKILL_MAP"] = root / "references" / "skill-map.md"
            globals()["ORCH_HANDOFF"] = root / "references" / "orchestration-and-handoff.md"
            full = build_coverage()
            assert full["covered"] == full["total_failure_modes"], (
                f"fake tree with all scenarios must fully cover: {full}"
            )

            # Drop one scenario -> gap must be reported
            (root / "evals" / "chaos" / FAILURE_MODES[0]["scenario"]).unlink()
            gap = build_coverage()
            assert gap["covered"] == full["total_failure_modes"] - 1, "missing scenario must drop coverage"
            missing = [r for r in gap["rows"] if not r["covered"]]
            assert len(missing) == 1 and missing[0]["id"] == FAILURE_MODES[0]["id"]
        finally:
            globals()["CHAOS_DIR"] = old_chaos
            globals()["SKILL_MD"] = old_skill
            globals()["SKILL_MAP"] = old_skillmap
            globals()["ORCH_HANDOFF"] = old_orch

    print("selftest OK: chaos-coverage invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any failure mode lacks a chaos scenario (default: advisory only)",
    )
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    cov = build_coverage()
    if args.json:
        import json as _json
        print(_json.dumps(cov, indent=2, ensure_ascii=False))
    else:
        print(render_text(cov))

    if args.strict and cov["covered"] < cov["total_failure_modes"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())