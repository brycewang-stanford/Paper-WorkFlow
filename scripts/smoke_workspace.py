#!/usr/bin/env python3
"""Build a minimal Paper-WorkFlow workspace and verify template contracts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_OUTPUTS = {
    "templates/entry_routing.md": "00_meta/entry_routing.md",
    "templates/stage_passport.md": "00_meta/stage_passport.md",
    "templates/handoff_card.md": "00_meta/handoff/S00-template.md",
    "templates/handoff_prompt.md": "00_meta/handoff_prompt.md",
    "templates/pipeline_status.md": "00_meta/pipeline_status.md",
    "templates/analysis_backend.md": "00_meta/analysis_backend.md",
    "templates/backend_parity.json": "00_meta/backend_parity.json",
    "templates/design_risk_ledger.md": "03_analysis/design_risk_ledger.md",
    "templates/sample_audit.md": "02_data/sample_audit.md",
    "templates/design_register.md": "03_analysis/design_register.md",
    "templates/method_gate.md": "03_analysis/method_gate.md",
    "templates/evidence_ledger.md": "00_meta/evidence_ledger.md",
    "templates/claim_integrity_audit.md": "00_meta/claim_integrity_audit.md",
    "templates/quality_scorecard.md": "00_meta/quality_scorecard.md",
    "templates/REPLICATION.md": "REPLICATION.md",
    "templates/FINAL_REPORT.md": "FINAL_REPORT.md",
    "templates/submission_checklist.md": "09_submission/submission_checklist.md",
    "templates/data_governance.md": "00_meta/data_governance.md",
    "templates/DAS.md": "09_submission/DAS.md",
    "templates/run_all.sh": "run_all.sh",
}

ARTIFACTS = {
    "entry_routing": "00_meta/entry_routing.md",
    "stage_passport": "00_meta/stage_passport.md",
    "handoff_template": "00_meta/handoff/S00-template.md",
    "handoff_prompt": "00_meta/handoff_prompt.md",
    "pipeline_status": "00_meta/pipeline_status.md",
    "analysis_backend": "00_meta/analysis_backend.md",
    "backend_parity_report": "00_meta/backend_parity.json",
    "design_risk_ledger": "03_analysis/design_risk_ledger.md",
    "sample_audit": "02_data/sample_audit.md",
    "design_register": "03_analysis/design_register.md",
    "method_gate": "03_analysis/method_gate.md",
    "evidence_ledger": "00_meta/evidence_ledger.md",
    "claim_integrity_audit": "00_meta/claim_integrity_audit.md",
    "quality_scorecard": "00_meta/quality_scorecard.md",
    "replication_readme": "REPLICATION.md",
    "final_report": "FINAL_REPORT.md",
    "submission_checklist": "09_submission/submission_checklist.md",
    "data_governance": "00_meta/data_governance.md",
    "data_availability_statement": "09_submission/DAS.md",
    "master_script": "run_all.sh",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def copy_template(src_rel: str, dst: Path) -> None:
    src = ROOT / src_rel
    if not src.exists():
        fail(f"missing template: {src_rel}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".sh":
        shutil.copy2(src, dst)
        dst.chmod(0o755)
        return
    text = src.read_text(encoding="utf-8")
    text = (
        text.replace("<short name>", "smoke_project")
        .replace("<YYYY-MM-DD HH:MM>", "2026-06-20 18:30")
        .replace("<journal>", "TBD-by-stage1")
    )
    dst.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def build_workspace(tmp_root: Path) -> Path:
    workspace = tmp_root / "paper_workspace" / "smoke_project_20260620-1830"
    subprocess.run(
        ["bash", str(ROOT / "assets" / "init_workspace.sh"), str(workspace)],
        check=True,
    )
    for src_rel, dst_rel in TEMPLATE_OUTPUTS.items():
        copy_template(src_rel, workspace / dst_rel)

    state_path = workspace / "00_meta" / "workflow_state.json"
    state = load_json(state_path)
    state["project"].update(
        {
            "short_name": "smoke_project",
            "created_at_beijing": "2026-06-20 18:30",
            "entry_stage": 0,
            "mode": "auto",
            "target_journal": "TBD-by-stage1",
            "language": "en",
        }
    )
    state["analysis_backend"].update(
        {
            "primary": "python-statspai",
            "secondary_validation": "none",
            "script_extension": ".py",
            "child_skill": "StatsPAI MCP / statspai package",
            "environment_status": "pending",
            "version_report": "00_meta/analysis_backend.md",
            "backend_parity_report": "00_meta/backend_parity.json",
        }
    )
    state["orchestration"].update(
        {
            "status": "active",
            "entry_routing": "00_meta/entry_routing.md",
            "stage_passport": "00_meta/stage_passport.md",
            "pipeline_status": "00_meta/pipeline_status.md",
            "handoff_dir": "00_meta/handoff",
            "latest_handoff": "00_meta/handoff/S00-template.md",
            "checkpoint_policy": "full-at-hard-gates",
            "reset_boundaries": [
                {
                    "stage": 0,
                    "boundary": "smoke",
                    "handoff": "00_meta/handoff/S00-template.md",
                    "status": "verified",
                }
            ],
            "fresh_evidence_required": True,
            "last_recovery_probe": "smoke fixture only; git/passport/current artifacts not probed",
            "self_review_gate": "pending",
            "ethics_gate": "pending",
            "revision_rounds_cap": 2,
        }
    )
    state["empirical_audit"].update(
        {
            "status": "pending",
            "sample_audit": "02_data/sample_audit.md",
            "estimand_alignment": "pending",
            "missingness_balance": "pending",
            "construct_validity": "pending",
            "blocking_issues": [],
            "last_audit": "smoke fixture only; no real data audited",
        }
    )
    state["stages"]["0_intake_setup"] = "done"
    state["method_gate"].update(
        {
            "status": "pending",
            "primary_design": "staggered_did",
            "primary_estimator": "Callaway-Santanna",
        }
    )
    state["evidence_governance"].update(
        {
            "status": "pending",
            "evidence_ledger": "00_meta/evidence_ledger.md",
            "design_gate_card": "03_analysis/method_gate.md#design-gate-card",
            "claim_strength": "pending",
            "open_discrepancies": [],
            "last_claim_audit": "smoke fixture only; no real claim audited",
        }
    )
    state["integrity_audit"].update(
        {
            "status": "pending",
            "claim_integrity_audit": "00_meta/claim_integrity_audit.md",
            "claim_locator_manifest": "00_meta/claim_integrity_audit.md#claim-locator-manifest",
            "audit_mode": "pre-review",
            "checked_claims": 0,
            "unsupported_claims": 0,
            "unverified_citations": 0,
            "blocking_findings": [],
            "last_audit": "smoke fixture only; no real claims audited",
        }
    )
    state["design_risk"].update(
        {
            "status": "pending",
            "risk_ledger": "03_analysis/design_risk_ledger.md",
            "threats_reviewed": ["smoke fixture only"],
            "blocking_threats": [],
            "external_validity": "pending",
            "specification_search": "pending",
            "spillover_interference": "pending",
            "selection_attrition": "pending",
            "last_review": "smoke fixture only; no real design risk reviewed",
        }
    )
    state["replication_pack"].update(
        {
            "status": "not_ready",
            "master_script": "run_all.sh",
            "archive_plan": "TBD trusted repository",
            "last_rebuild_check": "smoke fixture only; no empirical rebuild",
        }
    )
    state["artifacts"] = dict(ARTIFACTS)
    state["decisions"].append(
        {
            "stage": 0,
            "decision": "Smoke fixture instantiated orchestration, pipeline-status, integrity-audit, governance, gate, replication, and submission templates",
            "at": "2026-06-20 18:30",
        }
    )
    state["last_updated_beijing"] = "2026-06-20 18:30"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return workspace


def check_workspace(workspace: Path) -> None:
    state = load_json(workspace / "00_meta" / "workflow_state.json")
    if state.get("schema_version") != 10:
        fail("smoke state schema_version must remain 10")
    if state["project"]["mode"] != "auto":
        fail("smoke state project fields were not populated")
    if state["analysis_backend"]["primary"] != "python-statspai":
        fail("smoke state analysis backend was not populated")
    if state["orchestration"]["stage_passport"] != "00_meta/stage_passport.md":
        fail("smoke state orchestration passport was not populated")
    if state["orchestration"]["latest_handoff"] != "00_meta/handoff/S00-template.md":
        fail("smoke state latest handoff was not populated")
    if state["orchestration"]["pipeline_status"] != "00_meta/pipeline_status.md":
        fail("smoke state pipeline status was not populated")
    if not state["orchestration"]["reset_boundaries"]:
        fail("smoke state reset boundary list was not populated")
    if state["empirical_audit"]["sample_audit"] != "02_data/sample_audit.md":
        fail("smoke state empirical audit was not populated")
    if state["replication_pack"]["status"] != "not_ready":
        fail("smoke fixture must not pretend replication is ready")
    if state["evidence_governance"]["evidence_ledger"] != "00_meta/evidence_ledger.md":
        fail("smoke state evidence governance was not populated")
    if state["integrity_audit"]["claim_integrity_audit"] != "00_meta/claim_integrity_audit.md":
        fail("smoke state integrity audit was not populated")
    if state["design_risk"]["risk_ledger"] != "03_analysis/design_risk_ledger.md":
        fail("smoke state design risk was not populated")
    for name, rel in ARTIFACTS.items():
        path = workspace / rel
        if not path.exists():
            fail(f"artifact missing after template instantiation: {name} -> {rel}")
        if path.is_file() and path.stat().st_size == 0:
            fail(f"artifact is empty after template instantiation: {name} -> {rel}")
    gate = (workspace / "03_analysis" / "method_gate.md").read_text(encoding="utf-8")
    if "Decision: PASS / NOT PASS" not in gate:
        fail("method gate template lost its explicit decision placeholder")
    if "Design Gate Card" not in gate:
        fail("method gate template missing design gate card section")
    ledger = (workspace / "00_meta" / "evidence_ledger.md").read_text(encoding="utf-8")
    for marker in ["Claim Register", "Estimand-to-Claim Map", "Claim Strength Ladder", "Exhibit and Script Map"]:
        if marker not in ledger:
            fail(f"evidence ledger template missing marker: {marker}")
    governance = (workspace / "00_meta" / "data_governance.md").read_text(encoding="utf-8")
    for marker in ["Public replication package must not include", "IRB", "DUA"]:
        if marker not in governance:
            fail(f"data governance template missing marker: {marker}")
    backend = (workspace / "00_meta" / "analysis_backend.md").read_text(encoding="utf-8")
    for marker in ["Backend Choice", "Environment Check", "Output Contract"]:
        if marker not in backend:
            fail(f"analysis backend template missing marker: {marker}")
    backend_parity = load_json(workspace / "00_meta" / "backend_parity.json")
    if backend_parity.get("status") != "pending":
        fail("backend parity template must default to pending")
    routing = (workspace / "00_meta" / "entry_routing.md").read_text(encoding="utf-8")
    for marker in ["Entry Routing", "Route Examples", "Decision Points"]:
        if marker not in routing:
            fail(f"entry routing template missing marker: {marker}")
    pipeline_status = (workspace / "00_meta" / "pipeline_status.md").read_text(encoding="utf-8")
    for marker in ["Pipeline Status", "Stage Dashboard", "Checkpoint Policy", "Reset Boundary"]:
        if marker not in pipeline_status:
            fail(f"pipeline status template missing marker: {marker}")
    claim_integrity = (workspace / "00_meta" / "claim_integrity_audit.md").read_text(encoding="utf-8")
    for marker in ["Claim Integrity Audit", "Audit Scope", "Claim Locator Manifest", "Verdict Taxonomy"]:
        if marker not in claim_integrity:
            fail(f"claim integrity audit template missing marker: {marker}")
    passport = (workspace / "00_meta" / "stage_passport.md").read_text(encoding="utf-8")
    for marker in ["Stage Passport", "Fresh Evidence", "Revision Budget"]:
        if marker not in passport:
            fail(f"stage passport template missing marker: {marker}")
    handoff = (workspace / "00_meta" / "handoff" / "S00-template.md").read_text(encoding="utf-8")
    for marker in ["Handoff Card", "Current Stage", "Completed Artifacts", "Do Not"]:
        if marker not in handoff:
            fail(f"handoff template missing marker: {marker}")
    sample_audit = (workspace / "02_data" / "sample_audit.md").read_text(encoding="utf-8")
    for marker in ["Estimand Alignment", "Sample Construction Flow", "Missingness, Balance, and Overlap"]:
        if marker not in sample_audit:
            fail(f"sample audit template missing marker: {marker}")
    design_risk = (workspace / "03_analysis" / "design_risk_ledger.md").read_text(encoding="utf-8")
    for marker in ["Threat Register", "Claim Consequence", "External Validity and Transport", "Blocking Threats"]:
        if marker not in design_risk:
            fail(f"design risk ledger template missing marker: {marker}")
    run_all = workspace / "run_all.sh"
    subprocess.run(["bash", "-n", str(run_all)], check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true", help="keep the temporary workspace and print its path")
    parser.add_argument("--quiet", action="store_true", help="only print failures")
    args = parser.parse_args(argv)

    if args.keep:
        tmp_root = Path(tempfile.mkdtemp(prefix="paper-workflow-smoke-"))
        workspace = build_workspace(tmp_root)
        check_workspace(workspace)
        print(workspace)
        return 0

    with tempfile.TemporaryDirectory(prefix="paper-workflow-smoke-") as tmp:
        workspace = build_workspace(Path(tmp))
        check_workspace(workspace)
    if not args.quiet:
        print("OK: smoke workspace fixture passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
