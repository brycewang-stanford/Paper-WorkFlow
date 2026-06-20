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
    "templates/design_register.md": "03_analysis/design_register.md",
    "templates/method_gate.md": "03_analysis/method_gate.md",
    "templates/quality_scorecard.md": "00_meta/quality_scorecard.md",
    "templates/REPLICATION.md": "REPLICATION.md",
    "templates/FINAL_REPORT.md": "FINAL_REPORT.md",
    "templates/submission_checklist.md": "09_submission/submission_checklist.md",
    "templates/data_governance.md": "00_meta/data_governance.md",
    "templates/DAS.md": "09_submission/DAS.md",
    "templates/run_all.sh": "run_all.sh",
}

ARTIFACTS = {
    "design_register": "03_analysis/design_register.md",
    "method_gate": "03_analysis/method_gate.md",
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
    state["stages"]["0_intake_setup"] = "done"
    state["method_gate"].update(
        {
            "status": "pending",
            "primary_design": "staggered_did",
            "primary_estimator": "Callaway-Santanna",
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
            "decision": "Smoke fixture instantiated governance, gate, replication, and submission templates",
            "at": "2026-06-20 18:30",
        }
    )
    state["last_updated_beijing"] = "2026-06-20 18:30"
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return workspace


def check_workspace(workspace: Path) -> None:
    state = load_json(workspace / "00_meta" / "workflow_state.json")
    if state.get("schema_version") != 4:
        fail("smoke state schema_version must remain 4")
    if state["project"]["mode"] != "auto":
        fail("smoke state project fields were not populated")
    if state["replication_pack"]["status"] != "not_ready":
        fail("smoke fixture must not pretend replication is ready")
    for name, rel in ARTIFACTS.items():
        path = workspace / rel
        if not path.exists():
            fail(f"artifact missing after template instantiation: {name} -> {rel}")
        if path.is_file() and path.stat().st_size == 0:
            fail(f"artifact is empty after template instantiation: {name} -> {rel}")
    gate = (workspace / "03_analysis" / "method_gate.md").read_text(encoding="utf-8")
    if "Decision: PASS / NOT PASS" not in gate:
        fail("method gate template lost its explicit decision placeholder")
    governance = (workspace / "00_meta" / "data_governance.md").read_text(encoding="utf-8")
    for marker in ["Public replication package must not include", "IRB", "DUA"]:
        if marker not in governance:
            fail(f"data governance template missing marker: {marker}")
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
