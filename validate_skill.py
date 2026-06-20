#!/usr/bin/env python3
"""Local consistency checks for the Paper-WorkFlow skill."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent
EXPECTED_STAGE_KEYS = [
    "0_intake_setup",
    "1_topic_design",
    "2_data",
    "3_identification_estimation",
    "4_tables_figures",
    "5_draft",
    "6_polish",
    "7_language_dehumanize",
    "8_review_revision",
    "9_submission",
]
EXPECTED_WORKSPACE_DIRS = [
    "00_meta",
    "01_proposal/candidates",
    "02_data/raw",
    "03_analysis/results",
    "03_analysis/robustness",
    "04_results",
    "05_draft",
    "06_polish",
    "07_dehumanize",
    "08_review",
    "09_submission",
    "logs",
    "backups",
]
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")
REQUIRED_TEMPLATES = {
    "templates/design_register.md": ["Target estimand", "Bad-control screen", "Fallback Plan"],
    "templates/method_gate.md": ["Required Artifact Table", "Decision: PASS / NOT PASS", "Hard Flags"],
    "templates/quality_scorecard.md": ["Draft Quality Gate Scorecard", "Reproducibility and governance"],
    "templates/REPLICATION.md": ["Data Availability and Provenance", "Program to Output Map"],
    "templates/FINAL_REPORT.md": ["Gate Results", "Residual Risks"],
    "templates/submission_checklist.md": ["Journal Policy Refresh", "Final Gates"],
    "templates/data_governance.md": ["Data Classification", "Public replication package must not include", "IRB"],
    "templates/DAS.md": ["Restricted or Confidential Data", "Rights and Ethics"],
    "templates/run_all.sh": ["set -euo pipefail", "build tables and figures"],
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def tracked_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return [
            path.relative_to(ROOT)
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.relative_to(ROOT).parts
            and "paper_workspace" not in path.relative_to(ROOT).parts
        ]
    return [Path(line) for line in result.stdout.splitlines() if line.strip()]


def load_template() -> dict:
    template_path = ROOT / "assets" / "workflow_state.template.json"
    try:
        data = json.loads(template_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{template_path.relative_to(ROOT)} is not valid JSON: {exc}")
    if data.get("schema_version") != 4:
        fail("workflow_state.template.json schema_version must be 4")
    if list(data.get("stages", {}).keys()) != EXPECTED_STAGE_KEYS:
        fail("workflow_state.template.json stage keys do not match Stage 0-9 contract")
    for key in [
        "project",
        "method_gate",
        "quality_gate",
        "replication_pack",
        "artifacts",
        "decisions",
        "last_updated_beijing",
    ]:
        if key not in data:
            fail(f"workflow_state.template.json missing top-level key: {key}")
    gate = data["replication_pack"]
    for key in [
        "status",
        "readme",
        "master_script",
        "data_availability_statement",
        "archive_plan",
        "runtime_minutes",
        "last_rebuild_check",
    ]:
        if key not in gate:
            fail(f"replication_pack missing key: {key}")
    return data


def check_markdown_links(files: list[Path]) -> None:
    errors: list[str] = []
    for rel_path in files:
        if rel_path.suffix.lower() not in {".md"}:
            continue
        path = ROOT / rel_path
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                continue
            if " " in target and not target.startswith("<"):
                target = target.split(" ", 1)[0]
            target = target.strip("<>")
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT)
            except ValueError:
                errors.append(f"{rel_path}: link escapes skill dir: {match.group(1)}")
                continue
            if not candidate.exists():
                errors.append(f"{rel_path}: broken local link: {match.group(1)}")
    if errors:
        fail("broken markdown links:\n" + "\n".join(errors))


def check_assets() -> None:
    required = [
        "SKILL.md",
        "README.md",
        "README.en.md",
        "LICENSE",
        "did_demo.ipynb",
        "assets/did_table.tex",
        "assets/fig_event_study.png",
        "assets/fig_raw_trends.png",
        "assets/workflow.svg",
        "assets/init_workspace.sh",
        "assets/workflow_state.template.json",
        "references/stage-playbook.md",
        "references/skill-map.md",
        "references/research-grade-methods.md",
        "references/writing-craft.md",
        "references/reproducibility-pack.md",
        "references/peer-review-and-submission.md",
        "references/quality-rubric.md",
        "references/subagent-templates.md",
        "references/workspace-and-state.md",
        "references/threats-to-validity.md",
        "references/design-transparency.md",
        "references/literature-and-positioning.md",
        "references/worked-example.md",
        "references/data-governance.md",
        "references/runtime-fallbacks.md",
        "scripts/smoke_workspace.py",
    ]
    required.extend(REQUIRED_TEMPLATES)
    for rel in required:
        path = ROOT / rel
        if not path.exists():
            fail(f"required file missing: {rel}")
        if path.is_file() and path.stat().st_size == 0:
            fail(f"required file is empty: {rel}")
    if not os.access(ROOT / "assets" / "init_workspace.sh", os.X_OK):
        fail("assets/init_workspace.sh must be executable")


def check_template_contracts() -> None:
    for rel, markers in REQUIRED_TEMPLATES.items():
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                fail(f"{rel} missing required marker: {marker}")
    subprocess.run(["bash", "-n", str(ROOT / "templates" / "run_all.sh")], check=True)


def check_notebook() -> None:
    notebook_path = ROOT / "did_demo.ipynb"
    data = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = data.get("cells", [])
    if len(cells) < 20:
        fail("did_demo.ipynb should contain the full staged demo, not a tiny stub")
    if data.get("metadata", {}).get("kernelspec", {}).get("name") != "python3":
        fail("did_demo.ipynb kernelspec should be python3")
    source = "\n".join(
        "".join(cell.get("source", [])) if isinstance(cell.get("source", []), list) else cell.get("source", "")
        for cell in cells
    )
    for expected in ["TRUE_ATT", "fig_event_study.png", "did_table.tex", "Callaway", "Sun"]:
        if expected not in source:
            fail(f"did_demo.ipynb missing expected demo marker: {expected}")


def check_init_workspace(template: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="paper-workflow-check-") as tmp:
        workspace = Path(tmp) / "workspace with spaces"
        script = ROOT / "assets" / "init_workspace.sh"
        subprocess.run(["bash", str(script), str(workspace)], check=True)
        for rel in EXPECTED_WORKSPACE_DIRS:
            if not (workspace / rel).is_dir():
                fail(f"init_workspace.sh did not create directory: {rel}")
        state_path = workspace / "00_meta" / "workflow_state.json"
        if not state_path.exists():
            fail("init_workspace.sh did not copy workflow_state.json")
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state != template:
            fail("init_workspace.sh copied a workflow_state.json that differs from template")
        if not (workspace / "00_meta" / "intake.md").exists():
            fail("init_workspace.sh did not create 00_meta/intake.md")
        second = subprocess.run(["bash", str(script), str(workspace)], capture_output=True)
        if second.returncode == 0:
            fail("init_workspace.sh should refuse to overwrite an existing workspace")


def check_python_compile() -> None:
    files = [ROOT / "validate_skill.py", ROOT / "scripts" / "smoke_workspace.py"]
    for path in files:
        subprocess.run([sys.executable, "-m", "py_compile", str(path)], check=True)


def check_smoke_workspace() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "smoke_workspace.py"), "--quiet"], check=True)


def main() -> None:
    os.chdir(ROOT)
    template = load_template()
    files = tracked_files()
    check_assets()
    check_template_contracts()
    check_markdown_links(files)
    check_notebook()
    check_init_workspace(template)
    check_python_compile()
    check_smoke_workspace()
    print("OK: Paper-WorkFlow skill checks passed")


if __name__ == "__main__":
    main()
