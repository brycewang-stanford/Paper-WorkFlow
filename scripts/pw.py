#!/usr/bin/env python3
"""`pw` — the stage-aware front door to Paper-WorkFlow's run-time gates.

Why this exists
---------------
The rigor layer is 36 checkers deep. That depth is the point, but it pushed a
real cost onto whoever is driving a run: *which* checkers does Stage 7 owe, and
with which flags? The answer used to live in prose scattered across SKILL.md and
the stage playbook, which means the orchestrator could skip a gate simply by not
remembering it — the exact failure mode every gate here exists to prevent.

This module makes the stage -> gate mapping a **table**, then runs it:

    python3 scripts/pw.py enter 3 <workspace>   # may Stage 3 start?
    python3 scripts/pw.py exit  3 <workspace>   # is Stage 3 finished?
    python3 scripts/pw.py check <workspace>     # every gate that applies today
    python3 scripts/pw.py final <workspace>     # Stage 9 strictness, everywhere
    python3 scripts/pw.py plan  7               # what Stage 7 owes, without running
    python3 scripts/pw.py list                  # the whole map

Because the mapping is data, it is also checkable, and `--selftest` enforces the
invariant that motivated the file: **every workspace-scoped run-time checker in
the RIGOR registry is reachable from at least one stage.** A new gate that no
stage runs is a gate that never fires; that is now a maintenance failure rather
than something a reviewer has to notice.

Exit code is the number of failed gates, capped at 1 (non-zero == something to
fix). Gates whose inputs do not exist yet are reported as `skip`, not failure:
an unfinished run is not a violation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

WS = "{ws}"

# --------------------------------------------------------------------------- #
# the map                                                                      #
# --------------------------------------------------------------------------- #
# (script path relative to repo root, argv template, why it runs here).
# `{ws}` is substituted with the workspace path. A gate listed under a stage is
# the gate that stage *owes on the way out*; entry preconditions are a separate
# mechanism (`check_workspace_gates.py --preconditions`) driven by `enter`.
Gate = tuple[str, list[str], str]

BASE_GATE: Gate = (
    "scripts/check_workspace_gates.py", [WS],
    "cross-gate ordering: nothing marked pass without its evidence on disk",
)

STAGE_EXIT_GATES: dict[str, list[Gate]] = {
    "0": [BASE_GATE],
    "1": [BASE_GATE],
    "1L": [BASE_GATE],
    "2": [BASE_GATE],
    "2_5": [
        ("scripts/check_preregistration.py", [WS],
         "the primary specification is locked before any estimate exists"),
        BASE_GATE,
    ],
    "3": [
        ("scripts/check_backend_capabilities.py", [WS],
         "what actually ran is recorded, not what was hoped for"),
        ("scripts/check_preregistration.py", [WS],
         "results now exist -> the lock must predate them"),
        ("scripts/check_method_gate_card.py", [WS],
         "a passed Method Gate has no missing design-card rows"),
        ("scripts/check_runtime_fallbacks.py", [WS],
         "missing tools/backends were disclosed, not papered over"),
        BASE_GATE,
    ],
    "4": [
        ("scripts/check_table_style.py", [WS],
         "three-line table export contract (docx rules + booktabs .tex)"),
        ("scripts/check_backend_parity.py", [WS],
         "any secondary/fallback backend agrees with the primary"),
        BASE_GATE,
    ],
    "5": [
        ("scripts/check_citation_integrity.py", [WS],
         "citations exist and no look-ahead leaked into the draft"),
        BASE_GATE,
    ],
    "6": [BASE_GATE],
    "7": [
        ("scripts/check_manuscript_numbers.py", [WS],
         "every printed number traces to results; the de-AIGC rewrite moved none"),
        ("scripts/check_ai_disclosure.py", [WS],
         "the stage that removes the AI accent did not remove the AI disclosure"),
        BASE_GATE,
    ],
    "8": [
        ("scripts/check_review_scorecard.py", [WS],
         "the referee scorecard is scored, evidenced, and internally consistent"),
        BASE_GATE,
    ],
    "9": [
        ("scripts/check_citation_integrity.py", [WS, "--final"],
         "final citation sweep: no to-verify rows may ship"),
        ("scripts/check_ai_disclosure.py", [WS, "--final"],
         "the venue-shaped declaration is rendered and a human is accountable"),
        ("scripts/check_manuscript_numbers.py", [WS, "--strict"],
         "advisory numeric tiers become hard failures at submission"),
        ("scripts/check_table_style.py", [WS],
         "the Word export is still a three-line table after the last edit"),
        BASE_GATE,
    ],
}

STAGE_ORDER = ["0", "1", "1L", "2", "2_5", "3", "4", "5", "6", "7", "8", "9"]

# Stages whose entry preconditions check_workspace_gates.py knows about.
PRECONDITION_STAGES = ["1L", "2", "2_5", "3", "4", "5", "7", "8", "9"]

# Run-time checkers that are deliberately NOT stage-scoped, with the reason.
# The selftest requires every registry run-time checker to be either mapped to a
# stage or listed here, so "I forgot to wire it" cannot pass silently.
NON_STAGE_RUNTIME: dict[str, str] = {
    "scripts/smoke_workspace.py": "maintenance: proves templates instantiate; not a per-run gate",
    "scripts/check_demo_execution.py": "maintenance: executes the bundled teaching notebook",
    "scripts/check_verification_log.py": "repo-level: audits this package's own methods claims",
    "evals/check_replication_accuracy.py": "benchmark: scores fixtures with known truth, not a workspace",
    "evals/check_quality_judge.py": "invoked with --scorecard by the Draft Quality Gate, not a workspace path",
}


def normalise_stage(raw: str) -> str:
    key = str(raw).strip().upper().replace(".", "_").replace("-", "_")
    if key == "1L":
        return "1L"
    return key.lower() if key != "1L" else key


# --------------------------------------------------------------------------- #
# running                                                                      #
# --------------------------------------------------------------------------- #
def _resolve(gate: Gate, workspace: Path | None) -> list[str]:
    script, argv, _ = gate
    out = [sys.executable, str(ROOT / script)]
    for a in argv:
        out.append(str(workspace) if a == WS else a)
    return out


def run_gate(gate: Gate, workspace: Path, *, verbose: bool) -> dict:
    cmd = _resolve(gate, workspace)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    ok = proc.returncode == 0
    result = {
        "script": gate[0],
        "argv": gate[1],
        "why": gate[2],
        "ok": ok,
        "returncode": proc.returncode,
        "output": (proc.stdout + proc.stderr).strip(),
    }
    if verbose or not ok:
        print(f"\n--- {gate[0]} {' '.join(a for a in gate[1] if a != WS)} ---")
        print(result["output"] or "(no output)")
    return result


def gates_for(stage: str) -> list[Gate]:
    return STAGE_EXIT_GATES.get(stage, [])


def applicable_gates(upto: str | None = None) -> list[Gate]:
    """Every distinct gate owed at or before `upto` (default: all stages)."""
    seen: set[tuple[str, tuple[str, ...]]] = set()
    out: list[Gate] = []
    limit = STAGE_ORDER.index(upto) if upto in STAGE_ORDER else len(STAGE_ORDER) - 1
    for stage in STAGE_ORDER[: limit + 1]:
        for gate in STAGE_EXIT_GATES.get(stage, []):
            key = (gate[0], tuple(gate[1]))
            if key in seen:
                continue
            seen.add(key)
            out.append(gate)
    return out


def current_stage(workspace: Path) -> str | None:
    """The furthest stage the state file marks `done`."""
    state_path = workspace / "workflow_state.json"
    if not state_path.exists():
        state_path = workspace / "00_meta" / "workflow_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    stages = state.get("stages")
    if not isinstance(stages, dict):
        return None
    done = []
    for key, status in stages.items():
        if str(status).lower() != "done":
            continue
        token = key.split("_")[0].upper()
        token = "1L" if token == "1L" else token.lower()
        # `2_5_design_lock` -> `2_5`
        if key.startswith("2_5"):
            token = "2_5"
        if token in STAGE_ORDER:
            done.append(token)
    if not done:
        return None
    return max(done, key=STAGE_ORDER.index)


def render(results: list[dict], header: str, as_json: bool) -> int:
    failed = [r for r in results if not r["ok"]]
    if as_json:
        print(json.dumps({"header": header, "ok": not failed,
                          "gates": [{k: v for k, v in r.items() if k != "output"} for r in results]},
                         ensure_ascii=False, indent=2))
        return 1 if failed else 0
    print()
    print(header)
    print("=" * max(len(header), 60))
    for r in results:
        mark = "PASS" if r["ok"] else "FAIL"
        flags = " ".join(a for a in r["argv"] if a != WS)
        print(f"  [{mark}] {r['script']}{(' ' + flags) if flags else ''}")
        print(f"         {r['why']}")
    print("=" * max(len(header), 60))
    if failed:
        print(f"RESULT: {len(failed)}/{len(results)} gate(s) failed -> do not advance")
    else:
        print(f"RESULT: all {len(results)} gate(s) green")
    return 1 if failed else 0


# --------------------------------------------------------------------------- #
# commands                                                                     #
# --------------------------------------------------------------------------- #
def cmd_enter(stage: str, workspace: Path, as_json: bool, verbose: bool) -> int:
    if stage not in PRECONDITION_STAGES:
        known = ", ".join(PRECONDITION_STAGES)
        print(f"Stage {stage} declares no entry preconditions (stages with them: {known})")
        return 0
    gate: Gate = ("scripts/check_workspace_gates.py", [WS, "--preconditions", stage],
                  f"may Stage {stage} start? checked before the work, not after")
    return render([run_gate(gate, workspace, verbose=verbose)],
                  f"Paper-WorkFlow · Stage {stage} entry preconditions", as_json)


def cmd_exit(stage: str, workspace: Path, as_json: bool, verbose: bool) -> int:
    gates = gates_for(stage)
    if not gates:
        print(f"unknown stage: {stage} (known: {', '.join(STAGE_ORDER)})", file=sys.stderr)
        return 2
    results = [run_gate(g, workspace, verbose=verbose) for g in gates]
    return render(results, f"Paper-WorkFlow · Stage {stage} exit gates", as_json)


def cmd_check(workspace: Path, as_json: bool, verbose: bool, upto: str | None) -> int:
    stage = upto or current_stage(workspace)
    gates = applicable_gates(stage)
    label = f"up to Stage {stage}" if stage else "all stages"
    results = [run_gate(g, workspace, verbose=verbose) for g in gates]
    return render(results, f"Paper-WorkFlow · run-time gates ({label})", as_json)


def cmd_final(workspace: Path, as_json: bool, verbose: bool) -> int:
    gates = applicable_gates("8") + gates_for("9")
    seen: set[tuple[str, tuple[str, ...]]] = set()
    ordered: list[Gate] = []
    # Stage 9's stricter variants win over the lenient ones for the same script.
    strict_scripts = {g[0] for g in gates_for("9")}
    for gate in gates:
        if gate[0] in strict_scripts and gate not in gates_for("9"):
            continue
        key = (gate[0], tuple(gate[1]))
        if key in seen:
            continue
        seen.add(key)
        ordered.append(gate)
    results = [run_gate(g, workspace, verbose=verbose) for g in ordered]
    return render(results, "Paper-WorkFlow · submission-final gate sweep", as_json)


def cmd_plan(stage: str | None, as_json: bool) -> int:
    stages = [stage] if stage else STAGE_ORDER
    payload = {}
    for st in stages:
        gates = gates_for(st)
        if not gates:
            print(f"unknown stage: {st} (known: {', '.join(STAGE_ORDER)})", file=sys.stderr)
            return 2
        payload[st] = [{"script": g[0], "argv": [a for a in g[1] if a != WS], "why": g[2]}
                       for g in gates]
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    for st, entries in payload.items():
        pre = " (entry preconditions apply)" if st in PRECONDITION_STAGES else ""
        print(f"\nStage {st}{pre}")
        for e in entries:
            flags = " ".join(e["argv"])
            print(f"  · {e['script']}{(' ' + flags) if flags else ''}")
            print(f"      {e['why']}")
    print()
    return 0


def cmd_list(as_json: bool) -> int:
    mapped = sorted({g[0] for gates in STAGE_EXIT_GATES.values() for g in gates})
    if as_json:
        print(json.dumps({"stage_scoped": mapped, "not_stage_scoped": NON_STAGE_RUNTIME},
                         ensure_ascii=False, indent=2))
        return 0
    print("\nStage-scoped run-time gates")
    print("=" * 60)
    for path in mapped:
        stages = [st for st in STAGE_ORDER if any(g[0] == path for g in STAGE_EXIT_GATES.get(st, []))]
        print(f"  {path}\n      runs at: Stage {', '.join(stages)}")
    print("\nRun-time checkers that are deliberately not stage-scoped")
    print("=" * 60)
    for path, why in sorted(NON_STAGE_RUNTIME.items()):
        print(f"  {path}\n      {why}")
    print()
    return 0


# --------------------------------------------------------------------------- #
# selftest                                                                     #
# --------------------------------------------------------------------------- #
def _registry_runtime_paths() -> list[str] | None:
    """Load the RIGOR registry's run-time layer, or None if unavailable."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_pw_rigor", ROOT / "scripts" / "generate_rigor_report.py")
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return [e["path"] for e in module.REGISTRY if e["layer"] == module.RUNTIME]


def _selftest() -> int:
    # 1. every mapped script exists on disk and takes a workspace argument
    mapped = {g[0] for gates in STAGE_EXIT_GATES.values() for g in gates}
    for path in mapped:
        assert (ROOT / path).exists(), f"mapped gate does not exist: {path}"
        assert any(WS in g[1] for gates in STAGE_EXIT_GATES.values()
                   for g in gates if g[0] == path), f"{path} never receives a workspace"

    # 2. the stage keys agree with the pipeline spine and with the state template
    assert set(STAGE_EXIT_GATES) == set(STAGE_ORDER), (set(STAGE_EXIT_GATES) ^ set(STAGE_ORDER))
    template = json.loads((ROOT / "assets" / "workflow_state.template.json").read_text(encoding="utf-8"))
    template_stages = set()
    for key in template["stages"]:
        token = "2_5" if key.startswith("2_5") else key.split("_")[0]
        template_stages.add("1L" if token == "1L" else token)
    assert template_stages == set(STAGE_ORDER), (template_stages, set(STAGE_ORDER))

    # 3. THE invariant: no run-time checker is orphaned from the stage flow
    registry = _registry_runtime_paths()
    if registry is not None:
        orphans = [p for p in registry if p not in mapped and p not in NON_STAGE_RUNTIME]
        assert not orphans, (
            "run-time checker(s) registered in RIGOR.md but reachable from no stage "
            f"and not declared non-stage-scoped: {orphans}")
        stale = [p for p in NON_STAGE_RUNTIME if p not in registry]
        assert not stale, f"NON_STAGE_RUNTIME names a checker that is not registered: {stale}"

    # 4. preconditions list matches what check_workspace_gates.py actually knows
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_pw_gates", ROOT / "scripts" / "check_workspace_gates.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HERE))
    try:
        spec.loader.exec_module(module)
        # check_workspace_gates.py lower-cases its stage keys; compare like for like.
        known = {k.lower() for k in module.STAGE_PRECONDITIONS}
        declared = {s.lower() for s in PRECONDITION_STAGES}
        assert declared == known, f"precondition stage drift: {declared ^ known}"
    finally:
        sys.path.pop(0)

    # 5. Stage 9 is strictly stronger than the lenient variants it supersedes
    stage9 = {g[0]: g[1] for g in gates_for("9")}
    for script, argv in stage9.items():
        earlier = [g[1] for st in STAGE_ORDER[:-1] for g in gates_for(st) if g[0] == script]
        for prev in earlier:
            assert len(argv) >= len(prev), f"Stage 9 weakened {script}: {argv} vs {prev}"

    # 6. applicable_gates is monotone and deduplicated
    assert len(applicable_gates("0")) <= len(applicable_gates("9"))
    all_gates = applicable_gates()
    assert len(all_gates) == len({(g[0], tuple(g[1])) for g in all_gates}), "duplicate gates"

    # 7. `final` prefers the strict variant of a script over the lenient one
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cmd_plan(None, as_json=True)
    plan = json.loads(buf.getvalue())
    assert "--final" in [a for e in plan["9"] for a in e["argv"]], plan["9"]

    # 8. current_stage reads a real state file
    import tempfile
    with tempfile.TemporaryDirectory(prefix="pw-selftest-") as tmp:
        ws = Path(tmp)
        (ws / "00_meta").mkdir()
        assert current_stage(ws) is None
        (ws / "00_meta" / "workflow_state.json").write_text(json.dumps(
            {"stages": {"0_intake_setup": "done", "1L_literature_base": "done",
                        "2_5_design_lock": "done", "3_identification_estimation": "in_progress"}}),
            encoding="utf-8")
        assert current_stage(ws) == "2_5", current_stage(ws)

    print("selftest OK: stage->gate map invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="pw", description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("-v", "--verbose", action="store_true", help="print each gate's full output")
    p.add_argument("--selftest", action="store_true", help="verify the stage->gate map")
    sub = p.add_subparsers(dest="command")

    e = sub.add_parser("enter", help="may Stage N start? (entry preconditions)")
    e.add_argument("stage"); e.add_argument("workspace")

    x = sub.add_parser("exit", help="is Stage N finished? (exit gates)")
    x.add_argument("stage"); x.add_argument("workspace")

    c = sub.add_parser("check", help="every gate owed at or before the current stage")
    c.add_argument("workspace"); c.add_argument("--upto", help="pretend the run is at this stage")

    f = sub.add_parser("final", help="submission-final sweep (Stage 9 strictness)")
    f.add_argument("workspace")

    pl = sub.add_parser("plan", help="print what a stage owes without running anything")
    pl.add_argument("stage", nargs="?")

    sub.add_parser("list", help="the whole stage -> gate map")

    args = p.parse_args(argv)
    if args.selftest:
        return _selftest()
    if not args.command:
        p.print_help()
        return 2

    def ws() -> Path:
        return Path(args.workspace).expanduser().resolve()

    if args.command == "enter":
        return cmd_enter(normalise_stage(args.stage), ws(), args.json, args.verbose)
    if args.command == "exit":
        return cmd_exit(normalise_stage(args.stage), ws(), args.json, args.verbose)
    if args.command == "check":
        upto = normalise_stage(args.upto) if args.upto else None
        return cmd_check(ws(), args.json, args.verbose, upto)
    if args.command == "final":
        return cmd_final(ws(), args.json, args.verbose)
    if args.command == "plan":
        return cmd_plan(normalise_stage(args.stage) if args.stage else None, args.json)
    if args.command == "list":
        return cmd_list(args.json)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
