#!/usr/bin/env python3
"""Bidirectional complexity ratchet for the Paper-WorkFlow skill.

Why this exists
---------------
The SkillOpt improvement loop (references/skillopt-improvement-loop.md) gates
every edit on a held-out quality score. But each of that loop's scoring
dimensions -- routing fidelity, gate integrity, reproducibility, the two
integrity checkpoints -- can only be *raised by adding* content. Nothing in the
loop pushes back on size. So faithfully running it inflates the skill
monotonically, which is the exact opposite of SkillOpt's own central finding:
compact skills (its deployment artifact is 300-2000 tokens) transfer best.

The evidence that this is already happening, not hypothetical:
  - the always-loaded SKILL.md grew ~23% in a single improvement wave;
  - the reference corpus went from a handful of files to ~30 in days;
  - across the recent waves, inserted lines outnumbered deleted ~5-6 to 1, and
    additive commits outnumbered consolidating ones by roughly 20 to 1.

This tool supplies the missing direction. It does NOT score quality (score_skill.py
does that). It enforces a footprint *ratchet*:

  - The ALWAYS-LOADED layer (SKILL.md) and the reference-file *count* may not grow
    past a recorded ceiling without a deliberate, justified --update-baseline.
  - It reports headroom toward an aspirational target so a future consolidation
    pass has a concrete goal, instead of "smaller, somehow".

The ratchet is a brake, not a demand to shrink today: the recorded ceiling is
current reality, so an ordinary edit that keeps the footprint flat passes. Only
*growth* trips it. To grow on purpose, run --update-baseline and write down why.

Design notes
------------
Standalone by construction: reads files only, imports nothing from the skill,
writes nothing except complexity_baseline.json (and only under --update-baseline).
It therefore cannot collide with maintenance in flight on the core skill files,
and is not wired into validate_skill.py. A one-line wiring snippet for whoever
owns that file lives in evals/complexity_audit.md.

The aspirational SKILL.md target is a pragmatic middle ground, not SkillOpt's
literal 2000-token figure: this is a meta-orchestrator, legitimately heavier than
a single-task benchmark skill. The number encodes one rule -- SKILL.md is the
routing spine; detail belongs in on-demand references -- so the always-loaded
cost stays bounded while the on-demand corpus can be as deep as the work needs.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASELINE_PATH = HERE / "complexity_baseline.json"

# Aspirational target for the always-loaded layer. Report-only: never enforced,
# so it never forces an edit to a file another agent may be holding. ~8k tokens.
SKILL_MD_TARGET_BYTES = 32_000
# Byte metrics tolerate small drift so a typo fix or reflow does not trip the
# ratchet; the file *count* is strict because a new file is always deliberate.
BYTE_TOLERANCE = 1_024


def _bytes(path: Path) -> int:
    try:
        return len(path.read_bytes())
    except OSError:
        return 0


def compute_metrics(root: Path = ROOT) -> dict:
    """Current footprint. Pure measurement; no comparison, no I/O beyond reads."""
    refs = sorted((root / "references").glob("*.md"))
    tmpls = sorted((root / "templates").glob("*.md"))
    skill_md = _bytes(root / "SKILL.md")
    return {
        "skill_md_bytes": skill_md,
        "skill_md_tokens_est": round(skill_md / 4),
        "reference_count": len(refs),
        "reference_bytes": sum(_bytes(p) for p in refs),
        "template_count": len(tmpls),
        "template_bytes": sum(_bytes(p) for p in tmpls),
    }


def evaluate_ratchet(current: dict, baseline: dict, tolerance: int = BYTE_TOLERANCE) -> dict:
    """Compare current footprint to the recorded ceiling. Pure function.

    Hard violations (exit non-zero): the always-loaded layer grew, or a new
    reference file appeared. Warnings (advisory): the on-demand corpus grew,
    since editing references is routine; it is surfaced, not blocked.
    """
    ceiling = baseline.get("ceiling", {})
    violations: list[str] = []
    warnings: list[str] = []

    sm_ceil = ceiling.get("skill_md_bytes")
    if sm_ceil is not None and current["skill_md_bytes"] > sm_ceil + tolerance:
        violations.append(
            f"SKILL.md grew {current['skill_md_bytes'] - sm_ceil:+d} bytes past "
            f"the ceiling ({sm_ceil} -> {current['skill_md_bytes']}); this is the "
            f"ALWAYS-LOADED layer. Consolidate, or --update-baseline with a reason."
        )

    rc_ceil = ceiling.get("reference_count")
    if rc_ceil is not None and current["reference_count"] > rc_ceil:
        violations.append(
            f"reference count grew {rc_ceil} -> {current['reference_count']}: a new "
            f"reference file was added. Prefer extending an existing one; if a new "
            f"file is truly warranted, --update-baseline with a reason."
        )

    rb_ceil = ceiling.get("reference_bytes")
    if rb_ceil is not None and current["reference_bytes"] > rb_ceil + tolerance:
        warnings.append(
            f"on-demand reference corpus grew {current['reference_bytes'] - rb_ceil:+d} "
            f"bytes ({rb_ceil} -> {current['reference_bytes']}). Routine, but check it "
            f"is consolidation-neutral, not accretion."
        )

    target = baseline.get("targets", {}).get("skill_md_bytes", SKILL_MD_TARGET_BYTES)
    over_target = current["skill_md_bytes"] - target
    headroom = {
        "skill_md_target_bytes": target,
        "skill_md_over_target_bytes": over_target,
        "skill_md_within_target": over_target <= 0,
    }
    return {
        "ok": not violations,
        "violations": violations,
        "warnings": warnings,
        "headroom": headroom,
        "current": current,
        "ceiling": ceiling,
    }


def _load_baseline() -> dict | None:
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_baseline(note: str) -> dict:
    current = compute_metrics()
    baseline = {
        "recorded": datetime.date.today().isoformat(),
        "note": note,
        "ceiling": current,
        "targets": {"skill_md_bytes": SKILL_MD_TARGET_BYTES},
        "tolerance_bytes": BYTE_TOLERANCE,
        "rationale": (
            "Footprint ceiling for the SkillOpt complexity ratchet. Growth past "
            "this requires a deliberate update recording why. See "
            "evals/check_complexity_budget.py and evals/complexity_audit.md."
        ),
    }
    BASELINE_PATH.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return baseline


def render(result: dict, baseline: dict) -> str:
    cur, hd = result["current"], result["headroom"]
    out = []
    out.append("Paper-WorkFlow complexity ratchet")
    out.append(f"  baseline recorded: {baseline.get('recorded', '?')}  "
               f"(note: {baseline.get('note', '-')})")
    out.append("")
    out.append("  metric                  current        ceiling      target")
    out.append("  ----------------------------------------------------------------")
    ceil = result["ceiling"]
    out.append(f"  SKILL.md bytes        {cur['skill_md_bytes']:>9}    "
               f"{ceil.get('skill_md_bytes','-'):>9}   {hd['skill_md_target_bytes']:>9}")
    out.append(f"  SKILL.md tokens~      {cur['skill_md_tokens_est']:>9}")
    out.append(f"  reference files       {cur['reference_count']:>9}    "
               f"{ceil.get('reference_count','-'):>9}")
    out.append(f"  reference bytes       {cur['reference_bytes']:>9}    "
               f"{ceil.get('reference_bytes','-'):>9}")
    out.append("")
    if hd["skill_md_within_target"]:
        out.append(f"  SKILL.md is within the always-loaded target "
                   f"({-hd['skill_md_over_target_bytes']} bytes of headroom).")
    else:
        out.append(f"  SKILL.md is {hd['skill_md_over_target_bytes']} bytes OVER the "
                   f"always-loaded target -> consolidation goal.")
    out.append("")
    for w in result["warnings"]:
        out.append(f"  WARN: {w}")
    for v in result["violations"]:
        out.append(f"  FAIL: {v}")
    out.append("")
    out.append("  RATCHET OK (footprint did not grow past the ceiling)"
               if result["ok"] else "  RATCHET VIOLATED (footprint grew; see FAIL above)")
    return "\n".join(out)


def _selftest() -> int:
    # Ratchet logic is pure; test it on synthetic footprints so the invariant
    # does not depend on the live skill's current size.
    base = {
        "ceiling": {"skill_md_bytes": 40_000, "reference_count": 29,
                    "reference_bytes": 380_000},
        "targets": {"skill_md_bytes": 32_000},
    }
    flat = evaluate_ratchet(
        {"skill_md_bytes": 40_000, "skill_md_tokens_est": 10_000,
         "reference_count": 29, "reference_bytes": 380_000,
         "template_count": 0, "template_bytes": 0}, base)
    assert flat["ok"], "flat footprint must pass the ratchet"
    assert flat["headroom"]["skill_md_over_target_bytes"] == 8_000

    grew_skill = evaluate_ratchet(
        {"skill_md_bytes": 45_000, "skill_md_tokens_est": 11_250,
         "reference_count": 29, "reference_bytes": 380_000,
         "template_count": 0, "template_bytes": 0}, base)
    assert not grew_skill["ok"], "SKILL.md growth must trip the ratchet"
    assert any("SKILL.md grew" in v for v in grew_skill["violations"])

    grew_refs = evaluate_ratchet(
        {"skill_md_bytes": 40_000, "skill_md_tokens_est": 10_000,
         "reference_count": 30, "reference_bytes": 380_000,
         "template_count": 0, "template_bytes": 0}, base)
    assert not grew_refs["ok"], "a new reference file must trip the ratchet"
    assert any("reference count grew" in v for v in grew_refs["violations"])

    tiny = evaluate_ratchet(
        {"skill_md_bytes": 40_500, "skill_md_tokens_est": 10_125,
         "reference_count": 29, "reference_bytes": 380_000,
         "template_count": 0, "template_bytes": 0}, base)
    assert tiny["ok"], "sub-tolerance drift must not trip the ratchet"

    shrank = evaluate_ratchet(
        {"skill_md_bytes": 31_000, "skill_md_tokens_est": 7_750,
         "reference_count": 25, "reference_bytes": 300_000,
         "template_count": 0, "template_bytes": 0}, base)
    assert shrank["ok"] and shrank["headroom"]["skill_md_within_target"], \
        "shrinking under target must pass and report within-target"

    # compute_metrics returns well-typed, non-negative numbers on the real tree.
    m = compute_metrics()
    for k, v in m.items():
        assert isinstance(v, int) and v >= 0, f"{k} must be a non-negative int"

    print("selftest OK: complexity ratchet invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p.add_argument("--update-baseline", action="store_true",
                   help="record the current footprint as the new ceiling (deliberate act)")
    p.add_argument("--note", default="",
                   help="reason for --update-baseline (recorded in the baseline file)")
    p.add_argument("--selftest", action="store_true", help="run built-in selftests")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.update_baseline:
        if not args.note:
            print("refusing to update the baseline without --note "
                  "(record WHY the footprint may grow)", file=sys.stderr)
            return 2
        baseline = _write_baseline(args.note)
        print(f"baseline updated -> {BASELINE_PATH.name}")
        print(json.dumps(baseline, ensure_ascii=False, indent=2))
        return 0

    baseline = _load_baseline()
    if baseline is None:
        print("no complexity_baseline.json yet; seed it with:\n"
              "  python3 evals/check_complexity_budget.py --update-baseline "
              "--note 'initial ceiling'", file=sys.stderr)
        return 2

    result = evaluate_ratchet(compute_metrics(), baseline)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    print(render(result, baseline))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
