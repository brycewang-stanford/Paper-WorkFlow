#!/usr/bin/env python3
"""End-to-end gate integration test on REAL init + REAL templates.

The per-checker selftests exercise gate logic against synthetic stub workspaces
(``touch "x"`` files + hand-written state). `smoke_workspace.py` instantiates the
real templates and checks their markers — but never runs the gate checkers on the
result. So one contract is verified only by hand and never in CI:

    do the REAL `init_workspace.sh` skeleton and the REAL templates, when driven
    to a genuine PASS end-state, actually satisfy `check_workspace_gates.py` and
    `check_citation_integrity.py`? — and does corrupting that real workspace make
    the right checker go red?

This script closes that gap. It is the integration counterpart to the unit-level
selftests: same invariants, but on artifacts produced by the real init script and
the real template files, so drift between templates/init (which evolve) and the
checkers (which hard-code paths and keys) is caught automatically.

Usage:
    python3 scripts/check_gate_integration.py            # run the integration test
    python3 scripts/check_gate_integration.py --keep     # keep + print the workspace
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "scripts" / "check_workspace_gates.py"
CITES = ROOT / "scripts" / "check_citation_integrity.py"

# Stage-produced gate artifacts that ship a template (copied, with placeholder fill).
TEMPLATE_ARTIFACTS = {
    "templates/sample_audit.md": "02_data/sample_audit.md",
    "templates/design_register.md": "03_analysis/design_register.md",
    "templates/method_gate.md": "03_analysis/method_gate.md",
    "templates/quality_scorecard.md": "00_meta/quality_scorecard.md",
    "templates/REPLICATION.md": "REPLICATION.md",
    "templates/run_all.sh": "run_all.sh",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _copy_template(src_rel: str, dst: Path) -> None:
    src = ROOT / src_rel
    if not src.exists():
        fail(f"missing template: {src_rel}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".sh":
        shutil.copy2(src, dst)
        dst.chmod(0o755)
        return
    text = (
        src.read_text(encoding="utf-8")
        .replace("<short name>", "integ_project")
        .replace("<YYYY-MM-DD HH:MM>", "2026-06-23 12:00")
        .replace("<journal>", "TBD-by-stage1")
    )
    dst.write_text(text, encoding="utf-8")


def _passing_state() -> dict:
    """A state where every gate is legitimately PASS / ready, backed by files we write."""
    return {
        "schema_version": 10,
        "project": {"short_name": "integ_project", "mode": "auto"},
        "stages": {f"{i}_x": "done" for i in range(10)},
        "artifacts": {},
        "decisions": [],
        "orchestration": {
            "status": "active",
            "entry_routing": "00_meta/entry_routing.md",
            "stage_passport": "00_meta/stage_passport.md",
            "pipeline_status": "00_meta/pipeline_status.md",
            "handoff_dir": "00_meta/handoff",
            "latest_handoff": "00_meta/handoff/S09-ready.md",
            "checkpoint_policy": "full-at-hard-gates",
            "reset_boundaries": [],
            "fresh_evidence_required": True,
            "last_recovery_probe": "integration fixture",
            "self_review_gate": "pass",
            "ethics_gate": "pass",
            "revision_rounds_cap": 2,
        },
        "analysis_backend": {
            "primary": "python-statspai", "secondary_validation": "none",
            "script_extension": ".py", "child_skill": "statspai", "environment_status": "ok",
            "version_report": "00_meta/analysis_backend.md",
        },
        "empirical_audit": {"status": "pass", "sample_audit": "02_data/sample_audit.md",
                            "estimand_alignment": "pass", "missingness_balance": "pass",
                            "construct_validity": "pass", "blocking_issues": [], "last_audit": "integ"},
        "evidence_governance": {"status": "pass", "evidence_ledger": "00_meta/evidence_ledger.md",
                                "design_gate_card": "03_analysis/method_gate.md#design-gate-card",
                                "claim_strength": "associational", "open_discrepancies": [],
                                "last_claim_audit": "integ"},
        "integrity_audit": {"status": "pass", "claim_integrity_audit": "00_meta/claim_integrity_audit.md",
                            "claim_locator_manifest": "00_meta/claim_integrity_audit.md", "audit_mode": "final-check",
                            "checked_claims": 8, "unsupported_claims": 0, "unverified_citations": 0,
                            "blocking_findings": [], "last_audit": "integ"},
        "design_risk": {"status": "pass", "risk_ledger": "03_analysis/design_risk_ledger.md",
                        "threats_reviewed": ["parallel_trends", "external_validity"], "blocking_threats": [],
                        "external_validity": "pass", "specification_search": "pass",
                        "spillover_interference": "not_applicable", "selection_attrition": "pass",
                        "last_review": "integ"},
        "method_gate": {"status": "pass", "design_register": "03_analysis/design_register.md",
                        "method_gate_report": "03_analysis/method_gate.md", "missing_artifacts": [],
                        "primary_design": "staggered_did", "primary_estimator": "Callaway-Santanna"},
        "quality_gate": {"status": "pass", "scorecard": "00_meta/quality_scorecard.md"},
        "replication_pack": {"status": "ready", "readme": "REPLICATION.md", "master_script": "run_all.sh",
                             "data_availability_statement": "09_submission/DAS.md", "archive_plan": "Zenodo",
                             "runtime_minutes": 12, "last_rebuild_check": "rebuilt 2026-06-23"},
        "last_updated_beijing": "2026-06-23 12:00",
    }


def build_passing_workspace(tmp_root: Path) -> Path:
    workspace = tmp_root / "paper_workspace" / "integ_project_20260623-1200"
    subprocess.run(["bash", str(ROOT / "assets" / "init_workspace.sh"), str(workspace)], check=True)

    for src_rel, dst_rel in TEMPLATE_ARTIFACTS.items():
        _copy_template(src_rel, workspace / dst_rel)

    # synthesize the non-template artifacts a PASS requires
    (workspace / "03_analysis" / "results").mkdir(parents=True, exist_ok=True)
    (workspace / "03_analysis" / "results" / "main_results.json").write_text(
        json.dumps({"att": 0.123, "se": 0.045, "n": 5000}), encoding="utf-8")
    (workspace / "03_analysis" / "inference_report.md").write_text(
        "# Inference report\nClustering at state level; wild bootstrap for G=20.\n", encoding="utf-8")
    handoff = workspace / "00_meta" / "handoff" / "S09-ready.md"
    handoff.write_text("# Handoff Card\nCurrent Stage 9. Completed Artifacts. Do Not edit data.\n", encoding="utf-8")

    state_path = workspace / "00_meta" / "workflow_state.json"
    state_path.write_text(json.dumps(_passing_state(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return workspace


def _run_gates(workspace: Path) -> dict:
    proc = subprocess.run([sys.executable, str(GATES), str(workspace), "--json"],
                          capture_output=True, text=True)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        fail(f"check_workspace_gates --json did not return JSON:\n{proc.stdout}\n{proc.stderr}")
        raise  # unreachable


def _gate_failures(workspace: Path) -> list[str]:
    data = _run_gates(workspace)
    return [c["check"] for c in data.get("checks", []) if c["level"] == "FAIL"]


def run_integration(workspace: Path) -> None:
    # --- 1. fresh-init citation log passes the citation checker (non-final) ----
    fresh = workspace.parent / "fresh_init"
    subprocess.run(["bash", str(ROOT / "assets" / "init_workspace.sh"), str(fresh)], check=True)
    cite = subprocess.run([sys.executable, str(CITES), str(fresh)], capture_output=True, text=True)
    if cite.returncode != 0:
        fail(f"born-at-init citation_integrity_log.md does not pass check_citation_integrity:\n{cite.stdout}\n{cite.stderr}")

    # --- 2. real templates driven to PASS satisfy the gate checker -------------
    fails = _gate_failures(workspace)
    if fails:
        fail(f"PASS workspace built from real templates still has gate failures: {fails}")

    # --- 3. corrupting the real PASS workspace makes the right checker go red --
    state_path = workspace / "00_meta" / "workflow_state.json"

    # 3a: method gate marked pass but its report deleted -> method_gate:evidence
    saved = state_path.read_text(encoding="utf-8")
    report = workspace / "03_analysis" / "method_gate.md"
    report_text = report.read_text(encoding="utf-8")
    report.unlink()
    if "method_gate:evidence" not in _gate_failures(workspace):
        fail("deleting method_gate.md while method_gate=pass was NOT caught")
    report.write_text(report_text, encoding="utf-8")  # restore

    # 3b: quality gate pass while method gate not_pass -> quality_gate:ordering
    st = json.loads(saved)
    st["method_gate"]["status"] = "not_pass"
    state_path.write_text(json.dumps(st), encoding="utf-8")
    if "quality_gate:ordering" not in _gate_failures(workspace):
        fail("quality_gate=pass while method_gate=not_pass was NOT caught")

    # 3c: replication ready while integrity audit blocking -> replication + integrity flags
    st = json.loads(saved)
    st["integrity_audit"]["status"] = "pass"
    st["integrity_audit"]["blocking_findings"] = ["C3 unsupported"]
    state_path.write_text(json.dumps(st), encoding="utf-8")
    if "integrity_audit:blocking" not in _gate_failures(workspace):
        fail("integrity_audit=pass with a blocking finding was NOT caught")

    state_path.write_text(saved, encoding="utf-8")  # restore clean PASS
    if _gate_failures(workspace):
        fail("restoring the saved PASS state did not return the workspace to green")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true", help="keep + print the workspace path")
    args = parser.parse_args(argv)

    if args.keep:
        tmp_root = Path(tempfile.mkdtemp(prefix="paper-workflow-integ-"))
        ws = build_passing_workspace(tmp_root)
        run_integration(ws)
        print(ws)
        return 0

    with tempfile.TemporaryDirectory(prefix="paper-workflow-integ-") as tmp:
        ws = build_passing_workspace(Path(tmp))
        run_integration(ws)
    print("OK: gate integration test passed (real init + real templates satisfy the checkers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
