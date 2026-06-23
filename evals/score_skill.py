#!/usr/bin/env python3
"""Held-out evaluation harness for the Paper-WorkFlow SkillOpt-style loop.

The SkillOpt improvement loop (references/skillopt-improvement-loop.md) gates
every maintenance edit on a *held-out selection score*. That reference and the
SKILLOPT_PACKET.md template describe the score but leave it to be filled in by
hand. This harness makes the number mechanical and reproducible: it scores the
skill DOCUMENT against the five dimensions named in that loop, over the frozen
scenario suite in scenarios.json, and prints rollout lines in the exact packet
format so they can be pasted straight into a SKILLOPT_PACKET.md.

It does not run live agent trajectories. For a skill-as-trainable-state, the
"rollout outcome" that matters is whether the documented procedure still
satisfies its own contracts on each task archetype. Each dimension reduces to a
checkable signal:

  routing_fidelity   per-scenario : design -> child-skill -> tool anchors are
                                    documented in the routing references.
  gate_integrity     per-scenario : the gate self-test passes AND the design has
                                    a Design Gate Card.
  context_protection global       : subagent contract = write to disk, return a
                                    short summary.
  reproducibility    global       : a fresh workspace passes the smoke test.
  user_burden        global       : SKILL.md documents autonomy gears and a
                                    minimal-question / authorization discipline.
  integrity_checkpoint global     : the document, template, and checker expose
                                    the Stage 7 pre-review and Stage 9 final
                                    claim-integrity audit contract.

A scenario's total is the mean of the five dimension scores in [0, 1]. The
selection-split mean is the gate number. Run with --help for options.

This file is intentionally standalone: it imports nothing from the skill and is
not wired into validate_skill.py, so it cannot collide with maintenance work in
flight on the core skill files. Wiring it into validate_skill.py is an optional
follow-up for whoever owns that file.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCENARIOS_PATH = HERE / "scenarios.json"

# Files searched when checking whether a routing anchor is documented.
ROUTING_CORPUS = [
    "references/skill-map.md",
    "references/analysis-backends.md",
    "references/statspai-analysis.md",
    "references/design-gate-cards.md",
    "references/research-grade-methods.md",
]
GATE_CARD_FILE = "references/design-gate-cards.md"

# Global-dimension anchor groups. Each inner list is one "credit": the group is
# satisfied if ANY of its members is present (resilient to rephrasing). The
# dimension score is the fraction of groups satisfied.
CONTEXT_PROTECTION_FILES = ["references/subagent-templates.md", "SKILL.md"]
CONTEXT_PROTECTION_GROUPS = [
    ["写盘", "写到磁盘", "写入", "写到"],   # subagent writes outputs to disk
    ["摘要", "summary", "状态摘要"],          # returns only a concise summary
    ["工作区", "workspace"],                  # outputs land in the workspace
    ["输出文件", "output file", "输入文件"],  # explicit input/output files
]
USER_BURDEN_FILES = ["SKILL.md"]
USER_BURDEN_GROUPS = [
    ["交互档位", "档位", "autonom", "自主"],   # autonomy / interaction gears
    ["授权", "authoriz"],                       # respects standing authorization
    ["只问", "必要", "minimal", "确认"],        # minimal-question discipline
]
INTEGRITY_CHECKPOINT_FILES = [
    "SKILL.md",
    "references/integrity-and-claim-audit.md",
    "templates/claim_integrity_audit.md",
    "scripts/check_workspace_gates.py",
]
INTEGRITY_CHECKPOINT_GROUPS = [
    ["Claim Integrity Audit", "claim 忠实度", "claim integrity"],
    ["pre-review"],
    ["final-check"],
    ["integrity_audit"],
    ["quality_gate:integrity", "replication_pack"],
]

DIMENSIONS = [
    "routing_fidelity",
    "gate_integrity",
    "context_protection",
    "reproducibility",
    "user_burden",
    "integrity_checkpoint",
]
SUCCESS_THRESHOLD = 0.70  # per the rubric: >=0.7 is "meets bar"


def _read(rel: str) -> str:
    path = ROOT / rel
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _fraction_groups_present(corpus: str, groups: list[list[str]]) -> float:
    if not groups:
        return 0.0
    hits = sum(1 for group in groups if any(token in corpus for token in group))
    return round(hits / len(groups), 4)


def _run_script_ok(rel: str, args: list[str]) -> bool:
    path = ROOT / rel
    if not path.exists():
        return False
    try:
        completed = subprocess.run(
            [sys.executable, str(path), *args],
            cwd=ROOT,
            capture_output=True,
            timeout=300,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return completed.returncode == 0


def compute_global_scores(run_scripts: bool) -> dict:
    """Dimensions that do not vary by scenario."""
    context_corpus = "\n".join(_read(f) for f in CONTEXT_PROTECTION_FILES)
    burden_corpus = "\n".join(_read(f) for f in USER_BURDEN_FILES)
    integrity_corpus = "\n".join(_read(f) for f in INTEGRITY_CHECKPOINT_FILES)

    if run_scripts:
        smoke_ok = _run_script_ok("scripts/smoke_workspace.py", ["--quiet"])
        gate_selftest_ok = _run_script_ok(
            "scripts/check_workspace_gates.py", ["--selftest"]
        )
    else:
        # selftest / fast mode: assume the mechanical checks pass so the harness
        # can be exercised without paying their runtime. Real baselines run them.
        smoke_ok = True
        gate_selftest_ok = True

    return {
        "context_protection": _fraction_groups_present(
            context_corpus, CONTEXT_PROTECTION_GROUPS
        ),
        "reproducibility": 1.0 if smoke_ok else 0.0,
        "user_burden": _fraction_groups_present(burden_corpus, USER_BURDEN_GROUPS),
        "integrity_checkpoint": _fraction_groups_present(
            integrity_corpus, INTEGRITY_CHECKPOINT_GROUPS
        ),
        "_gate_selftest_ok": gate_selftest_ok,
    }


def score_scenario(scenario: dict, routing_corpus: str, gate_card_corpus: str,
                   globals_: dict) -> dict:
    anchors = scenario.get("routing_anchors", [])
    if anchors:
        found = [a for a in anchors if a in routing_corpus]
        routing = round(len(found) / len(anchors), 4)
        missing = [a for a in anchors if a not in routing_corpus]
    else:
        routing, missing = 0.0, []

    gate_card_kw = scenario.get("gate_card_keyword", "")
    gate_card_present = bool(gate_card_kw) and gate_card_kw in gate_card_corpus
    gate_integrity = round(
        ((1.0 if globals_["_gate_selftest_ok"] else 0.0)
         + (1.0 if gate_card_present else 0.0)) / 2.0,
        4,
    )

    dims = {
        "routing_fidelity": routing,
        "gate_integrity": gate_integrity,
        "context_protection": globals_["context_protection"],
        "reproducibility": globals_["reproducibility"],
        "user_burden": globals_["user_burden"],
        "integrity_checkpoint": globals_["integrity_checkpoint"],
    }
    total = round(sum(dims[d] for d in DIMENSIONS) / len(DIMENSIONS), 4)
    notes = []
    if missing:
        notes.append("undocumented routing anchors: " + ", ".join(missing))
    if gate_card_kw and not gate_card_present:
        notes.append(f"no Design Gate Card for '{gate_card_kw}'")
    return {
        "id": scenario["id"],
        "split": scenario.get("split", "train"),
        "dimensions": dims,
        "total": total,
        "status": "success" if total >= SUCCESS_THRESHOLD else "failure",
        "notes": "; ".join(notes) if notes else "all contracts satisfied",
    }


def evaluate(run_scripts: bool = True) -> dict:
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    routing_corpus = "\n".join(_read(f) for f in ROUTING_CORPUS)
    gate_card_corpus = _read(GATE_CARD_FILE)
    globals_ = compute_global_scores(run_scripts)
    results = [
        score_scenario(s, routing_corpus, gate_card_corpus, globals_)
        for s in scenarios
    ]
    splits: dict[str, list[float]] = {}
    for r in results:
        splits.setdefault(r["split"], []).append(r["total"])
    split_means = {
        k: round(sum(v) / len(v), 4) for k, v in splits.items() if v
    }
    return {
        "results": results,
        "split_means": split_means,
        "overall_mean": round(
            sum(r["total"] for r in results) / len(results), 4
        ),
        "gate_selftest_ok": globals_["_gate_selftest_ok"],
        "scripts_run": run_scripts,
    }


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def packet_lines(report: dict, split: str | None) -> list[str]:
    """Rollout lines in SKILLOPT_PACKET.md format.

    check_skillopt_packet.py requires each rollout line to contain `evidence=`
    and a `score=` field; these lines satisfy that contract exactly.
    """
    chosen = [
        r for r in report["results"]
        if split in (None, "all") or r["split"] == split
    ]
    lines = []
    for i, r in enumerate(chosen, start=1):
        prefix = (split if split and split != "all" else r["split"])[:6]
        lines.append(
            f"- [ ] {prefix}-{i:03d} | status={r['status']} | "
            f"score={r['total']:.2f} | evidence=evals/scenarios.json#{r['id']} | "
            f"note={r['notes']}"
        )
    return lines


def render_table(report: dict) -> str:
    out = []
    header = f"{'scenario':<18} {'split':<10} " + " ".join(
        f"{d[:5]:>5}" for d in DIMENSIONS
    ) + f" {'total':>6} {'status':>8}"
    out.append(header)
    out.append("-" * len(header))
    for r in report["results"]:
        dims = " ".join(f"{r['dimensions'][d]:>5.2f}" for d in DIMENSIONS)
        out.append(
            f"{r['id']:<18} {r['split']:<10} {dims} "
            f"{r['total']:>6.2f} {r['status']:>8}"
        )
    out.append("")
    for split in ("train", "selection", "regression"):
        if split in report["split_means"]:
            out.append(f"  {split:<11} mean = {report['split_means'][split]:.3f}")
    out.append(f"  {'overall':<11} mean = {report['overall_mean']:.3f}")
    out.append(
        f"  gate self-test = {'pass' if report['gate_selftest_ok'] else 'FAIL'}"
        f"   (scripts_run={report['scripts_run']})"
    )
    out.append("")
    out.append("Dimension legend: " + ", ".join(
        f"{d[:5]}={d}" for d in DIMENSIONS
    ))
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Selftest
# --------------------------------------------------------------------------- #

def _selftest() -> int:
    import re

    # Scenarios file is well-formed and split-complete.
    data = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
    scenarios = data["scenarios"]
    assert len(scenarios) >= 5, "need a non-trivial scenario suite"
    splits = {s["split"] for s in scenarios}
    assert {"train", "selection", "regression"} <= splits, "all splits required"

    # Fast structural pass (no subprocess) yields bounded, well-typed scores.
    report = evaluate(run_scripts=False)
    assert len(report["results"]) == len(scenarios)
    for r in report["results"]:
        assert 0.0 <= r["total"] <= 1.0, f"total out of range for {r['id']}"
        for d in DIMENSIONS:
            assert 0.0 <= r["dimensions"][d] <= 1.0, f"{d} out of range"
        assert r["status"] in {"success", "failure"}

    # Emitted packet lines match check_skillopt_packet.py's expectations.
    score_re = re.compile(r"score\s*=\s*([0-9]+(?:\.[0-9]+)?)", re.IGNORECASE)
    for line in packet_lines(report, "selection"):
        assert line.strip().startswith("- ["), "must be a checklist rollout line"
        assert "evidence=" in line, "packet checker requires evidence="
        assert score_re.search(line), "packet checker requires a score= field"

    # The scorer must discriminate, independent of current skill content: a
    # scenario whose routing anchor and gate card are both absent loses exactly
    # those credits; a fully-present one keeps them. Tested on synthetic corpora
    # so this invariant does not break when the skill legitimately closes a gap.
    g = {"context_protection": 1.0, "reproducibility": 1.0, "user_burden": 1.0,
         "integrity_checkpoint": 1.0, "_gate_selftest_ok": True}
    miss = score_scenario(
        {"id": "_miss", "split": "selection",
         "routing_anchors": ["__NO_SUCH_ANCHOR__"],
         "gate_card_keyword": "__NO_SUCH_CARD__"},
        routing_corpus="", gate_card_corpus="", globals_=g)
    assert miss["dimensions"]["routing_fidelity"] == 0.0, "absent anchor must zero routing"
    assert miss["dimensions"]["gate_integrity"] == 0.5, "absent card must halve gate credit"
    hit = score_scenario(
        {"id": "_hit", "split": "selection",
         "routing_anchors": ["ANCHOR_X"],
         "gate_card_keyword": "CARD_Y"},
        routing_corpus="lead ANCHOR_X trail", gate_card_corpus="lead CARD_Y trail",
        globals_=g)
    assert hit["dimensions"]["routing_fidelity"] == 1.0, "present anchor must score routing"
    assert hit["dimensions"]["gate_integrity"] == 1.0, "present card + selftest must full gate"

    print("selftest OK: eval harness invariants hold")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Score the Paper-WorkFlow skill on held-out scenarios."
    )
    parser.add_argument(
        "--packet-lines",
        nargs="?",
        const="selection",
        choices=["train", "selection", "regression", "all"],
        help="emit SKILLOPT_PACKET.md rollout lines for a split (default selection)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--no-scripts",
        action="store_true",
        help="skip smoke/gate subprocess checks (faster, structural-only)",
    )
    parser.add_argument("--selftest", action="store_true", help="run built-in selftests")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    report = evaluate(run_scripts=not args.no_scripts)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    if args.packet_lines:
        print("\n".join(packet_lines(report, args.packet_lines)))
        return 0
    print(render_table(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
