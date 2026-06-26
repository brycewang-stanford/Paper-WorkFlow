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
    "00_meta/handoff",
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
    "templates/analysis_backend.md": ["Backend Choice", "Environment Check", "Fallback"],
    "templates/entry_routing.md": ["Entry Routing", "Route Examples", "Decision Points", "Fallback"],
    "templates/stage_passport.md": ["Stage Passport", "Fresh Evidence", "Revision Budget", "Known Limitations"],
    "templates/handoff_card.md": ["Handoff Card", "Current Stage", "Completed Artifacts", "Do Not"],
    "templates/handoff_prompt.md": ["Handoff Prompt", "Fresh Reality Check", "Completion Criteria"],
    "templates/pipeline_status.md": ["Pipeline Status", "Stage Dashboard", "Checkpoint Policy", "Reset Boundary"],
    "templates/design_risk_ledger.md": ["Design Risk Ledger", "Threat Register", "Claim Consequence", "External Validity and Transport", "Blocking Threats"],
    "templates/design_register.md": ["Target estimand", "Claim Boundary", "Bad-control screen", "Fallback Plan"],
    "templates/method_gate.md": ["Required Artifact Table", "Design Gate Card", "Decision: PASS / NOT PASS", "Hard Flags"],
    "templates/sample_audit.md": ["Estimand Alignment", "Sample Construction Flow", "Inference-Level Check"],
    "templates/inference_report.md": ["Standard Errors and Clustering Decision", "Few-Cluster", "Multiple Hypothesis Testing"],
    "templates/quality_scorecard.md": [
        "Draft Quality Gate Scorecard",
        "L2 semantic",
        "Findings Register",
        "Verbatim evidence span",
        "blocking",
        "Review Grade",
        "Reproducibility and governance",
        "Evidence ledger claim strength",
    ],
    "templates/REPLICATION.md": ["Data Availability and Provenance", "Program to Output Map"],
    "templates/FINAL_REPORT.md": [
        "Gate Results",
        "Validation Evidence",
        "Change / Commit Ledger",
        "Failures and Fixes",
        "Remote / Parity Status",
        "Residual Risks",
    ],
    "templates/evidence_ledger.md": ["Claim Register", "Estimand-to-Claim Map", "Claim Strength Ladder", "Exhibit and Script Map"],
    "templates/claim_integrity_audit.md": ["Claim Integrity Audit", "Audit Scope", "Claim Locator Manifest", "Verdict Taxonomy", "Blocking findings"],
    "templates/preregistration.md": [
        "Pre-Registration & Analysis Plan",
        "Lock Status",
        "locked_before_estimation",
        "Confirmatory Hypotheses",
        "Primary Specification Lock",
        "Confirmatory vs Exploratory",
        "Deviations from Plan",
    ],
    "templates/submission_checklist.md": ["Journal Policy Refresh", "Final Gates"],
    "templates/data_governance.md": ["Data Classification", "Public replication package must not include", "IRB"],
    "templates/DAS.md": ["Restricted or Confidential Data", "Rights and Ethics"],
    "templates/run_all.sh": ["set -euo pipefail", "build tables and figures"],
    "templates/SKILLOPT_PACKET.md": [
        "SkillOpt Improvement Packet",
        "Train rollouts",
        "Held-out selection rollouts",
        "Gate Decision",
        "Adoption Record",
    ],
}
REQUIRED_JSON_TEMPLATES = [
    "templates/backend_capabilities.json",
    "templates/backend_parity.json",
]
REQUIRED_REFERENCES = {
    "references/design-risk-ledger.md": [
        "Design Risk Ledger",
        "blocking_threats",
        "specification_search",
        "spillover_interference",
        "Method Gate",
    ],
    "references/design-gate-cards.md": [
        "Claim strength ladder",
        "DiD / Event Study",
        "IV / 2SLS",
        "RDD / Kink",
        "Design Gate Card",
    ],
    "references/inference-and-uncertainty.md": [
        "Inference & Uncertainty Pack",
        "标准误与聚类层级",
        "多重检验",
        "弱工具稳健推断",
        "inference_report.md",
    ],
    "references/mechanism-and-channels.md": [
        "Mechanism & Channels Pack",
        "先分清三类",
        "反模式清单",
        "Gelbach",
        "sequential ignorability",
    ],
    "references/skillopt-improvement-loop.md": [
        "SkillOpt-style improvement loop",
        "rollout",
        "held-out selection",
        "bounded patch",
        "check_skillopt_packet.py",
    ],
    "references/orchestration-and-handoff.md": [
        "Orchestration & Handoff",
        "Entry Routing",
        "Stage Passport",
        "Fresh Evidence",
        "Handoff Card",
        "schema_version 10",
    ],
    "references/integrity-and-claim-audit.md": [
        "Integrity & Claim Audit",
        "Claim Locator Manifest",
        "Verdicts",
        "Sampling Discipline",
        "integrity_audit",
    ],
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
    if data.get("schema_version") != 10:
        fail("workflow_state.template.json schema_version must be 10")
    if list(data.get("stages", {}).keys()) != EXPECTED_STAGE_KEYS:
        fail("workflow_state.template.json stage keys do not match Stage 0-9 contract")
    for key in [
        "project",
        "orchestration",
        "analysis_backend",
        "empirical_audit",
        "method_gate",
        "evidence_governance",
        "integrity_audit",
        "design_risk",
        "quality_gate",
        "replication_pack",
        "artifacts",
        "decisions",
        "last_updated_beijing",
    ]:
        if key not in data:
            fail(f"workflow_state.template.json missing top-level key: {key}")
    orchestration = data["orchestration"]
    for key in [
        "status",
        "entry_routing",
        "stage_passport",
        "pipeline_status",
        "handoff_dir",
        "latest_handoff",
        "checkpoint_policy",
        "reset_boundaries",
        "fresh_evidence_required",
        "last_recovery_probe",
        "self_review_gate",
        "ethics_gate",
        "revision_rounds_cap",
    ]:
        if key not in orchestration:
            fail(f"orchestration missing key: {key}")
    if orchestration.get("fresh_evidence_required") is not True:
        fail("orchestration.fresh_evidence_required must default to true")
    if orchestration.get("revision_rounds_cap") != 2:
        fail("orchestration.revision_rounds_cap must default to 2")
    if not isinstance(orchestration.get("reset_boundaries"), list):
        fail("orchestration.reset_boundaries must default to an empty list")
    backend = data["analysis_backend"]
    for key in [
        "primary",
        "secondary_validation",
        "script_extension",
        "child_skill",
        "environment_status",
        "version_report",
        "capability_report",
        "backend_parity_report",
    ]:
        if key not in backend:
            fail(f"analysis_backend missing key: {key}")
    audit = data["empirical_audit"]
    for key in [
        "status",
        "sample_audit",
        "estimand_alignment",
        "missingness_balance",
        "construct_validity",
        "blocking_issues",
        "last_audit",
    ]:
        if key not in audit:
            fail(f"empirical_audit missing key: {key}")
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
    governance = data["evidence_governance"]
    for key in [
        "status",
        "evidence_ledger",
        "design_gate_card",
        "claim_strength",
        "open_discrepancies",
        "last_claim_audit",
    ]:
        if key not in governance:
            fail(f"evidence_governance missing key: {key}")
    integrity = data["integrity_audit"]
    for key in [
        "status",
        "claim_integrity_audit",
        "claim_locator_manifest",
        "audit_mode",
        "checked_claims",
        "unsupported_claims",
        "unverified_citations",
        "blocking_findings",
        "last_audit",
    ]:
        if key not in integrity:
            fail(f"integrity_audit missing key: {key}")
    design_risk = data["design_risk"]
    for key in [
        "status",
        "risk_ledger",
        "threats_reviewed",
        "blocking_threats",
        "external_validity",
        "specification_search",
        "spillover_interference",
        "selection_attrition",
        "last_review",
    ]:
        if key not in design_risk:
            fail(f"design_risk missing key: {key}")
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
        "_verification_log/README.md",
        "_verification_log/methods-claims.md",
        "references/stage-playbook.md",
        "references/skill-map.md",
        "references/research-grade-methods.md",
        "references/design-risk-ledger.md",
        "references/design-gate-cards.md",
        "references/empirical-audit.md",
        "references/statspai-analysis.md",
        "references/analysis-backends.md",
        "references/writing-craft.md",
        "references/reproducibility-pack.md",
        "references/peer-review-and-submission.md",
        "references/quality-rubric.md",
        "references/subagent-templates.md",
        "references/workspace-and-state.md",
        "references/threats-to-validity.md",
        "references/design-transparency.md",
        "references/orchestration-and-handoff.md",
        "references/integrity-and-claim-audit.md",
        "references/inference-and-uncertainty.md",
        "references/mechanism-and-channels.md",
        "references/literature-and-positioning.md",
        "references/worked-example.md",
        "references/skillopt-improvement-loop.md",
        "references/data-governance.md",
        "references/runtime-fallbacks.md",
        "scripts/smoke_workspace.py",
        "scripts/check_demo_execution.py",
        "scripts/check_backend_capabilities.py",
        "scripts/check_backend_parity.py",
        "scripts/check_stage_scenario.py",
        "scripts/check_stage_adversarial.py",
        "scripts/check_design_gate_contract.py",
        "scripts/check_method_specific_failures.py",
        "scripts/check_method_gate_card.py",
        "scripts/check_runtime_fallbacks.py",
        "scripts/check_workspace_gates.py",
        "scripts/check_state_template_paths.py",
        "scripts/check_contract_matrix.py",
        "scripts/check_bilingual_docs.py",
        "scripts/check_final_report_contract.py",
        "scripts/check_monthly_worklog.py",
        "scripts/check_rigor_registry.py",
        "scripts/check_reproducibility_scaffold.py",
        "scripts/check_skillopt_packet.py",
        "scripts/check_verification_log.py",
        "scripts/check_citation_integrity.py",
        "scripts/check_preregistration.py",
        "scripts/check_review_scorecard.py",
        "scripts/generate_rigor_report.py",
        "templates/backend_capabilities.json",
        "templates/backend_parity.json",
        "evals/stage_scenario_contract.json",
        "evals/stage_adversarial_cases.json",
        "evals/design_gate_contract.json",
        "evals/method_failure_cases.json",
        "evals/backend_parity_cases.json",
    ]
    required.extend(REQUIRED_TEMPLATES)
    required.extend(REQUIRED_JSON_TEMPLATES)
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
    for rel, markers in REQUIRED_REFERENCES.items():
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                fail(f"{rel} missing required marker: {marker}")
    for rel in REQUIRED_JSON_TEMPLATES:
        try:
            json.loads((ROOT / rel).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"{rel} is not valid JSON: {exc}")
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
        if not (workspace / "00_meta" / "entry_routing.md").exists():
            fail("init_workspace.sh did not create 00_meta/entry_routing.md")
        if not (workspace / "00_meta" / "stage_passport.md").exists():
            fail("init_workspace.sh did not create 00_meta/stage_passport.md")
        if not (workspace / "00_meta" / "handoff" / "HANDOFF_TEMPLATE.md").exists():
            fail("init_workspace.sh did not create 00_meta/handoff/HANDOFF_TEMPLATE.md")
        if not (workspace / "00_meta" / "handoff_prompt.md").exists():
            fail("init_workspace.sh did not create 00_meta/handoff_prompt.md")
        if not (workspace / "00_meta" / "pipeline_status.md").exists():
            fail("init_workspace.sh did not create 00_meta/pipeline_status.md")
        if not (workspace / "00_meta" / "analysis_backend.md").exists():
            fail("init_workspace.sh did not create 00_meta/analysis_backend.md")
        if not (workspace / "00_meta" / "backend_capabilities.json").exists():
            fail("init_workspace.sh did not create 00_meta/backend_capabilities.json")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_backend_capabilities.py"), str(workspace)],
            check=True,
        )
        if not (workspace / "00_meta" / "backend_parity.json").exists():
            fail("init_workspace.sh did not create 00_meta/backend_parity.json")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "check_backend_parity.py"), str(workspace)],
            check=True,
        )
        if not (workspace / "00_meta" / "evidence_ledger.md").exists():
            fail("init_workspace.sh did not create 00_meta/evidence_ledger.md")
        if not (workspace / "00_meta" / "data_governance.md").exists():
            fail("init_workspace.sh did not create 00_meta/data_governance.md")
        if not (workspace / "00_meta" / "claim_integrity_audit.md").exists():
            fail("init_workspace.sh did not create 00_meta/claim_integrity_audit.md")
        if not (workspace / "00_meta" / "citation_integrity_log.md").exists():
            fail("init_workspace.sh did not create 00_meta/citation_integrity_log.md")
        if not (workspace / "03_analysis" / "design_risk_ledger.md").exists():
            fail("init_workspace.sh did not create 03_analysis/design_risk_ledger.md")
        second = subprocess.run(["bash", str(script), str(workspace)], capture_output=True)
        if second.returncode == 0:
            fail("init_workspace.sh should refuse to overwrite an existing workspace")


def check_python_compile() -> None:
    files = [
        ROOT / "validate_skill.py",
        ROOT / "scripts" / "smoke_workspace.py",
        ROOT / "scripts" / "check_demo_execution.py",
        ROOT / "scripts" / "check_backend_capabilities.py",
        ROOT / "scripts" / "check_backend_parity.py",
        ROOT / "scripts" / "check_stage_scenario.py",
        ROOT / "scripts" / "check_stage_adversarial.py",
        ROOT / "scripts" / "check_design_gate_contract.py",
        ROOT / "scripts" / "check_method_specific_failures.py",
        ROOT / "scripts" / "check_method_gate_card.py",
        ROOT / "scripts" / "check_runtime_fallbacks.py",
        ROOT / "scripts" / "check_workspace_gates.py",
        ROOT / "scripts" / "check_state_template_paths.py",
        ROOT / "scripts" / "check_contract_matrix.py",
        ROOT / "scripts" / "check_bilingual_docs.py",
        ROOT / "scripts" / "check_final_report_contract.py",
        ROOT / "scripts" / "check_monthly_worklog.py",
        ROOT / "scripts" / "check_rigor_registry.py",
        ROOT / "scripts" / "check_reproducibility_scaffold.py",
        ROOT / "scripts" / "check_skillopt_packet.py",
        ROOT / "scripts" / "check_verification_log.py",
        ROOT / "scripts" / "check_citation_integrity.py",
        ROOT / "scripts" / "check_cross_references.py",
        ROOT / "scripts" / "check_gate_integration.py",
        ROOT / "scripts" / "check_preregistration.py",
        ROOT / "scripts" / "check_review_scorecard.py",
        ROOT / "scripts" / "generate_rigor_report.py",
        ROOT / "evals" / "score_skill.py",
        ROOT / "evals" / "check_complexity_budget.py",
        ROOT / "evals" / "check_replication_accuracy.py",
        ROOT / "evals" / "check_quality_judge.py",
    ]
    for path in files:
        subprocess.run([sys.executable, "-m", "py_compile", str(path)], check=True)


def check_gate_verifier() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_workspace_gates.py"), "--selftest"],
        check=True,
    )


def check_skillopt_packet_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_skillopt_packet.py"), "--selftest"],
        check=True,
    )


def check_contract_matrix_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_contract_matrix.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_contract_matrix.py")],
        check=True,
    )


def check_bilingual_docs_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_bilingual_docs.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_bilingual_docs.py")],
        check=True,
    )


def check_final_report_contract_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_final_report_contract.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_final_report_contract.py")],
        check=True,
    )


def check_monthly_worklog_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_monthly_worklog.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_monthly_worklog.py")],
        check=True,
    )


def check_rigor_registry_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_rigor_registry.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_rigor_registry.py")],
        check=True,
    )


def check_state_template_paths_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_state_template_paths.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_state_template_paths.py")],
        check=True,
    )


def check_reproducibility_scaffold_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_reproducibility_scaffold.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_reproducibility_scaffold.py")],
        check=True,
    )


def check_demo_execution_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_demo_execution.py"), "--selftest"],
        check=True,
    )


def check_backend_capabilities_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_backend_capabilities.py"), "--selftest"],
        check=True,
    )


def check_backend_parity_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_backend_parity.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_backend_parity.py")],
        check=True,
    )


def check_stage_scenario_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_stage_scenario.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_stage_scenario.py")],
        check=True,
    )


def check_stage_adversarial_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_stage_adversarial.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_stage_adversarial.py")],
        check=True,
    )


def check_design_gate_contract_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_design_gate_contract.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_design_gate_contract.py")],
        check=True,
    )


def check_method_specific_failures_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_method_specific_failures.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_method_specific_failures.py")],
        check=True,
    )


def check_method_gate_card_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_method_gate_card.py"), "--selftest"],
        check=True,
    )


def check_runtime_fallbacks_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_runtime_fallbacks.py"), "--selftest"],
        check=True,
    )


def check_verification_log() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_verification_log.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_verification_log.py")],
        check=True,
    )


def check_citation_integrity_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_citation_integrity.py"), "--selftest"],
        check=True,
    )


def check_preregistration_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_preregistration.py"), "--selftest"],
        check=True,
    )


def check_review_scorecard_checker() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_review_scorecard.py"), "--selftest"],
        check=True,
    )


def check_cross_references_linter() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_cross_references.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_cross_references.py")],
        check=True,
    )


def check_smoke_workspace() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "smoke_workspace.py"), "--quiet"], check=True)


def check_gate_integration() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "check_gate_integration.py")], check=True)


def check_maintenance_evals() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "evals" / "score_skill.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "evals" / "check_complexity_budget.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "evals" / "check_complexity_budget.py")],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "evals" / "check_replication_accuracy.py"), "--selftest"],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "evals" / "check_quality_judge.py"), "--selftest"],
        check=True,
    )


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
    check_demo_execution_checker()
    check_backend_capabilities_checker()
    check_backend_parity_checker()
    check_stage_scenario_checker()
    check_stage_adversarial_checker()
    check_design_gate_contract_checker()
    check_method_specific_failures_checker()
    check_method_gate_card_checker()
    check_runtime_fallbacks_checker()
    check_smoke_workspace()
    check_gate_integration()
    check_gate_verifier()
    check_state_template_paths_checker()
    check_contract_matrix_checker()
    check_bilingual_docs_checker()
    check_final_report_contract_checker()
    check_monthly_worklog_checker()
    check_rigor_registry_checker()
    check_reproducibility_scaffold_checker()
    check_skillopt_packet_checker()
    check_verification_log()
    check_citation_integrity_checker()
    check_preregistration_checker()
    check_review_scorecard_checker()
    check_cross_references_linter()
    check_maintenance_evals()
    print("OK: Paper-WorkFlow skill checks passed")


if __name__ == "__main__":
    main()
