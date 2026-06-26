#!/usr/bin/env python3
"""Validate the Stage 0-9 golden-path scenario contract.

This is a maintenance-level scenario test. Unit checkers prove individual gates;
this checker proves the workflow timeline can be represented as one coherent
workspace: every Stage 0-9 state is done, each stage has a log and handoff card,
key artifacts exist, the final handoff pointer is recoverable, the existing
workspace gate checker accepts the finished scenario, and the delivery packet
contains a filled FINAL_REPORT.

Usage:
    python3 scripts/check_stage_scenario.py
    python3 scripts/check_stage_scenario.py --selftest
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "evals" / "stage_scenario_contract.json"
STATE_TEMPLATE = ROOT / "assets" / "workflow_state.template.json"
GATE_CHECKER = ROOT / "scripts" / "check_workspace_gates.py"
FINAL_REPORT_CHECKER = ROOT / "scripts" / "check_final_report_contract.py"

TEMPLATE_OUTPUTS = {
    "templates/sample_audit.md": "02_data/sample_audit.md",
    "templates/design_register.md": "03_analysis/design_register.md",
    "templates/method_gate.md": "03_analysis/method_gate.md",
    "templates/design_risk_ledger.md": "03_analysis/design_risk_ledger.md",
    "templates/inference_report.md": "03_analysis/inference_report.md",
    "templates/evidence_ledger.md": "00_meta/evidence_ledger.md",
    "templates/claim_integrity_audit.md": "00_meta/claim_integrity_audit.md",
    "templates/quality_scorecard.md": "00_meta/quality_scorecard.md",
    "templates/REPLICATION.md": "REPLICATION.md",
    "templates/DAS.md": "09_submission/DAS.md",
    "templates/submission_checklist.md": "09_submission/submission_checklist.md",
    "templates/FINAL_REPORT.md": "FINAL_REPORT.md",
    "templates/run_all.sh": "run_all.sh",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def _clean_path(raw: str) -> Path:
    if not raw or raw.startswith("/") or ".." in Path(raw).parts:
        fail(f"invalid repo/workspace-relative path: {raw!r}")
    return Path(raw)


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
        .replace("<short name>", "scenario_project")
        .replace("<YYYY-MM-DD HH:MM>", "2026-06-25 22:00")
        .replace("<journal>", "AER-style target")
    )
    dst.write_text(text, encoding="utf-8")


def _expected_stage_keys() -> list[str]:
    data = _load_json(STATE_TEMPLATE)
    stages = data.get("stages")
    if not isinstance(stages, dict):
        fail("workflow_state.template.json missing stages object")
    return list(stages.keys())


def evaluate_contract(data: dict) -> dict:
    errors: list[str] = []
    stages = data.get("stages")
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("required_stage_count") != 10:
        errors.append("required_stage_count must be 10")
    if not isinstance(stages, list) or not stages:
        errors.append("stages must be a non-empty list")
        stages = []
    if len(stages) != data.get("required_stage_count"):
        errors.append("stage count does not match required_stage_count")

    expected_keys = _expected_stage_keys()
    seen_numbers: set[int] = set()
    seen_paths: set[str] = set()
    contract_keys: list[str] = []

    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            errors.append(f"stages[{index}] must be an object")
            continue
        number = stage.get("number")
        state_key = stage.get("state_key")
        if number != index:
            errors.append(f"stages[{index}].number must be {index}")
        if isinstance(number, int):
            if number in seen_numbers:
                errors.append(f"duplicate stage number: {number}")
            seen_numbers.add(number)
        if not isinstance(state_key, str) or not state_key:
            errors.append(f"stages[{index}] missing state_key")
        else:
            contract_keys.append(state_key)
            if index < len(expected_keys) and state_key != expected_keys[index]:
                errors.append(f"stage {index} state_key {state_key!r} != template key {expected_keys[index]!r}")

        for field in ("log", "handoff"):
            value = stage.get(field)
            if not isinstance(value, str):
                errors.append(f"stage {index} missing {field}")
                continue
            path = str(_clean_path(value))
            if path in seen_paths:
                errors.append(f"duplicate scenario path: {path}")
            seen_paths.add(path)

        artifacts = stage.get("required_artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"stage {index} required_artifacts must be a non-empty list")
        else:
            for artifact in artifacts:
                if not isinstance(artifact, str):
                    errors.append(f"stage {index} has non-string artifact path")
                    continue
                path = str(_clean_path(artifact))
                seen_paths.add(path)

    if contract_keys != expected_keys:
        errors.append("contract stage_key sequence must exactly match workflow_state.template.json")

    final_required = data.get("final_required_artifacts", [])
    if not isinstance(final_required, list) or not final_required:
        errors.append("final_required_artifacts must be a non-empty list")
    for value in final_required:
        if not isinstance(value, str):
            errors.append("final_required_artifacts contains non-string path")
            continue
        _clean_path(value)

    final_checks = data.get("final_delivery_checks", [])
    if not isinstance(final_checks, list) or not final_checks:
        errors.append("final_delivery_checks must be a non-empty list")
    else:
        required = {"check_workspace_gates --json --reconcile", "check_final_report_contract --filled"}
        missing = required - set(final_checks)
        if missing:
            errors.append("final_delivery_checks missing: " + ", ".join(sorted(missing)))
        for check in final_checks:
            if not isinstance(check, str) or not check.strip():
                errors.append("final_delivery_checks contains an empty/non-string check")

    return {
        "ok": not errors,
        "errors": errors,
        "stage_count": len(stages),
        "path_count": len(seen_paths),
    }


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_final_citation_log(workspace: Path) -> None:
    _write(
        workspace / "00_meta" / "citation_integrity_log.md",
        """## 1. Citation Verification
| Bibkey | Cited claim | Identifier | Metadata match | Version | Retraction/erratum | Status | Checked | Note |
|---|---|---|---|---|---|---|---|---|
| smith2020 | scenario evidence claim | 10.1/example | ok | published | clean | verified | 2026-06-25 | ok |

## 2. Temporal Integrity
| Risk | Source | Requirement met? | Conclusion | Consequence if risk |
|---|---|---|---|---|
| Feature look-ahead | Synthetic panel | yes | pass | na |
""",
    )


def _write_filled_final_report(workspace: Path) -> None:
    _write(
        workspace / "FINAL_REPORT.md",
        """# Final Report

Project: scenario_project
Completed at (Beijing): 2026-06-25 22:00
Workspace: paper_workspace/scenario_project_20260625-2200

## 1. Pipeline Summary

| Stage | Status | Key outputs | Red flags / fallback |
|---|---|---|---|
| 0. Intake & setup | pass | 00_meta/workflow_state.json, 00_meta/stage_passport.md | none |
| 1. Topic & design | pass | 01_proposal/proposal.md, 03_analysis/design_register.md | none |
| 2. Data | pass | 02_data/codebook.md, 02_data/sample_audit.md | none |
| 3. Identification & estimation | pass | 03_analysis/method_gate.md, 03_analysis/results/main_results.json | none |
| 4. Tables & figures | pass | 04_results/table_main.tex, 04_results/figure_event_study.md | none |
| 5. Draft | pass | 05_draft/main.tex, 05_draft/ref.bib | none |
| 6. Polish | pass | 06_polish/polish_log.md, 06_polish/changed_claims.md | none |
| 7. Language & de-AI | pass | 07_dehumanize/main.tex, 00_meta/quality_scorecard.md | none |
| 8. Review & revision | pass | 08_review/referee_report.md, 08_review/response_letter.md | none |
| 9. Submission | pass | 09_submission/submission_checklist.md, 09_submission/DAS.md | none |

## 2. Gate Results

- Orchestration route: recorded
- Stage passport: current
- Pipeline status: current
- Latest handoff: recorded
- Method gate: pass
- Analysis backend: python-statspai
- Sample / estimand audit: pass
- Design risk ledger: pass
- Draft quality gate: pass
- Replication pack: ready
- Data governance: clear
- Evidence ledger: complete
- Evidence governance: pass
- Claim integrity audit: pass
- Strongest allowed claim: qualified_causal

## 3. Deliverables

| Deliverable | Path | Ready? |
|---|---|---:|
| Proposal | 01_proposal/proposal.md | yes |
| Entry routing | 00_meta/entry_routing.md | yes |
| Stage passport | 00_meta/stage_passport.md | yes |
| Pipeline status | 00_meta/pipeline_status.md | yes |
| Latest handoff | 00_meta/handoff/S09-submission.md | yes |
| Analysis backend report | 00_meta/analysis_backend.md | yes |
| Backend parity report | 00_meta/backend_parity.json | yes |
| Clean data and codebook | 02_data/clean/analysis_sample.csv, 02_data/codebook.md | yes |
| Sample / estimand audit | 02_data/sample_audit.md | yes |
| Design risk ledger | 03_analysis/design_risk_ledger.md | yes |
| Main results | 03_analysis/results/main_results.json | yes |
| Evidence ledger | 00_meta/evidence_ledger.md | yes |
| Claim integrity audit | 00_meta/claim_integrity_audit.md | yes |
| Tables and figures | 04_results/ | yes |
| Manuscript | 07_dehumanize/main.tex | yes |
| Review response | 08_review/response_letter.md | yes |
| Submission package | 09_submission/ | yes |
| Replication README | REPLICATION.md | yes |

## 4. Reproduction Command

```bash
bash run_all.sh
```

Last rebuild check: scenario checker rebuilt final artifact map

## 5. Validation Evidence

Commands run:

| Command | Result | Evidence / notes |
|---|---|---|
| `python3 validate_skill.py` | PASS | scenario package validation gate |
| `python3 scripts/generate_rigor_report.py --check` | PASS | RIGOR freshness gate |
| `git diff --check` | PASS | whitespace and conflict-marker hygiene |
| `make catalog` | not in scope | parent catalog not touched by scenario fixture |
| `make validate` | not in scope | parent validation not touched by scenario fixture |
| `make check` | not in scope | parent end-to-end gate not touched by scenario fixture |

## 6. Change / Commit Ledger

| Commit / SHA | Files changed | Change summary |
|---|---|---|
| no commit | scenario fixture workspace files | generated Stage 0-9 delivery packet for validator coverage |

## 7. Failures and Fixes

| Failures encountered | Fix / outcome | Follow-up |
|---|---|---|
| none | scenario fixture remained green | none |

## 8. Remote / Parity Status

| Scope | Status | Evidence / notes |
|---|---|---|
| Child repo status | dirty | scenario fixture is temporary and not a repo commit |
| Parent repo status | not in scope | no parent catalog/gitlink change for fixture run |
| Remote / parity status | No push requested | no remote parity claim for fixture run |

## 9. Residual Risks

- Identification: scenario fixture only, not a real empirical claim
- Design risks / external validity: scenario fixture only
- Sample / estimand alignment: synthetic data only
- Robustness: fixture-level only
- Evidence-to-claim alignment: checked by scenario fixture
- Claim/citation/number integrity: checked by scenario fixture
- Citation: synthetic bibkey only
- Data access / IRB / DUA: no restricted data in fixture
- Journal formatting: not exercised by fixture
- Handoff / continuation: Stage 9 handoff recorded

## 10. Next Actions

1. Replace fixture values with real project evidence in an actual workspace.
2. Run the filled final report checker before delivery.
3. Record remote parity only after an actual push.
""",
    )


def _build_state(contract: dict) -> dict:
    state = _load_json(STATE_TEMPLATE)
    state["project"].update(
        {
            "short_name": "scenario_project",
            "created_at_beijing": "2026-06-25 22:00",
            "entry_stage": 0,
            "mode": "auto",
            "target_journal": "AER-style target",
            "language": "en",
        }
    )
    state["stages"] = {stage["state_key"]: "done" for stage in contract["stages"]}
    state["orchestration"].update(
        {
            "status": "complete",
            "latest_handoff": contract["stages"][-1]["handoff"],
            "reset_boundaries": [
                {
                    "stage": stage["number"],
                    "handoff": stage["handoff"],
                    "status": "verified",
                }
                for stage in contract["stages"]
            ],
            "last_recovery_probe": "scenario checker verified stage logs, handoffs, artifacts, and gates",
            "self_review_gate": "pass",
            "ethics_gate": "pass",
        }
    )
    state["analysis_backend"].update(
        {
            "primary": "python-statspai",
            "secondary_validation": "r/fixest spot-check",
            "script_extension": ".py",
            "child_skill": "StatsPAI MCP / statspai package",
            "environment_status": "ok",
        }
    )
    state["empirical_audit"].update(
        {
            "status": "pass",
            "estimand_alignment": "pass",
            "missingness_balance": "pass",
            "construct_validity": "pass",
            "blocking_issues": [],
            "last_audit": "scenario fixture",
        }
    )
    state["evidence_governance"].update(
        {
            "status": "pass",
            "claim_strength": "associational",
            "open_discrepancies": [],
            "last_claim_audit": "scenario fixture",
        }
    )
    state["integrity_audit"].update(
        {
            "status": "pass",
            "audit_mode": "final-check",
            "checked_claims": 9,
            "unsupported_claims": 0,
            "unverified_citations": 0,
            "blocking_findings": [],
            "last_audit": "scenario fixture",
        }
    )
    state["design_risk"].update(
        {
            "status": "pass",
            "threats_reviewed": ["parallel_trends", "external_validity", "specification_search"],
            "blocking_threats": [],
            "external_validity": "pass",
            "specification_search": "pass",
            "spillover_interference": "not_applicable",
            "selection_attrition": "pass",
            "last_review": "scenario fixture",
        }
    )
    state["method_gate"].update(
        {
            "status": "pass",
            "primary_design": "staggered_did",
            "primary_estimator": "Callaway-Santanna",
            "required_artifacts": [
                "02_data/sample_audit.md",
                "03_analysis/design_register.md",
                "03_analysis/method_gate.md",
                "03_analysis/results/main_results.json",
            ],
            "missing_artifacts": [],
            "last_audit": "scenario fixture",
        }
    )
    state["quality_gate"].update(
        {
            "draft_milestone": "post-dehumanize",
            "status": "pass",
            "rounds": 1,
            "last_total_score": 61,
            "last_dimension_scores": {
                "identification": 9,
                "robustness": 8,
                "writing": 9,
                "contribution": 9,
                "evidence": 9,
                "citations": 8,
                "reproducibility": 9,
            },
        }
    )
    state["replication_pack"].update(
        {
            "status": "ready",
            "master_script": "run_all.sh",
            "archive_plan": "public synthetic archive",
            "runtime_minutes": 1,
            "last_rebuild_check": "scenario checker rebuilt final artifact map",
        }
    )
    artifacts: dict[str, str] = {}
    for stage in contract["stages"]:
        artifacts[f"stage_{stage['number']}_log"] = stage["log"]
        artifacts[f"stage_{stage['number']}_handoff"] = stage["handoff"]
        for artifact in stage["required_artifacts"]:
            artifacts[artifact.replace("/", "__")] = artifact
    state["artifacts"] = artifacts
    state["decisions"] = [
        {
            "stage": stage["number"],
            "decision": f"Scenario fixture completed {stage['state_key']} with logged artifacts",
            "at": "2026-06-25 22:00",
        }
        for stage in contract["stages"]
    ]
    state["last_updated_beijing"] = "2026-06-25 22:00"
    return state


def build_workspace(tmp_root: Path, contract: dict) -> Path:
    workspace = tmp_root / "paper_workspace" / "scenario_project_20260625-2200"
    subprocess.run(["bash", str(ROOT / "assets" / "init_workspace.sh"), str(workspace)], check=True)

    for src_rel, dst_rel in TEMPLATE_OUTPUTS.items():
        _copy_template(src_rel, workspace / dst_rel)

    _write(workspace / "01_proposal" / "proposal.md", "# Proposal\nA bounded scenario proposal.\n")
    _write(workspace / "01_proposal" / "candidates" / "topic_card.md", "# Topic Card\nScenario topic.\n")
    _write(workspace / "02_data" / "codebook.md", "# Codebook\n`y`, `treat`, and `post` are defined.\n")
    _write(workspace / "02_data" / "clean" / "analysis_sample.csv", "id,year,y,treat,post\n1,2020,1.2,1,1\n")
    _write(workspace / "03_analysis" / "results" / "main_results.json", json.dumps({"att": 0.123, "se": 0.045}, indent=2) + "\n")
    _write(workspace / "04_results" / "table_main.tex", "\\begin{tabular}{lr}\nATT & 0.123 \\\\\nSE & 0.045 \\\\\n\\end{tabular}\n")
    _write(workspace / "04_results" / "figure_event_study.md", "# Event-study figure placeholder\nATT 0.123 with 95 percent CI.\n")
    _write(workspace / "05_draft" / "main.tex", "\\section{Introduction}\nScenario draft tied to ATT 0.123.\n")
    _write(workspace / "05_draft" / "ref.bib", "@article{smith2020,title={Scenario Evidence},year={2020}}\n")
    _write(workspace / "06_polish" / "polish_log.md", "# Polish Log\nClaims tightened.\n")
    _write(workspace / "06_polish" / "changed_claims.md", "# Changed Claims\nNo unsupported causal upgrade.\n")
    _write(workspace / "07_dehumanize" / "main.tex", "\\section{Introduction}\nFinal human-edited scenario draft.\n")
    _write(workspace / "08_review" / "referee_report.md", "# Referee Report\nNo blocking issue remains.\n")
    _write(workspace / "08_review" / "response_letter.md", "# Response Letter\nAll scenario comments addressed.\n")
    _write_final_citation_log(workspace)

    passport_lines = ["# Stage Passport", "", "| Stage | Status | Handoff | Key artifacts |", "|---|---|---|---|"]
    pipeline_lines = ["# Pipeline Status", "", "| Stage | State key | Status | Handoff |", "|---|---|---|---|"]
    for stage in contract["stages"]:
        artifact_blob = ", ".join(stage["required_artifacts"])
        _write(
            workspace / stage["log"],
            f"# Stage {stage['number']} Log\n\nState key: `{stage['state_key']}`.\n\nArtifacts:\n"
            + "".join(f"- `{artifact}`\n" for artifact in stage["required_artifacts"]),
        )
        _write(
            workspace / stage["handoff"],
            f"# Handoff Card\n\nCurrent Stage: {stage['number']}\n\nCompleted Artifacts:\n"
            + "".join(f"- `{artifact}`\n" for artifact in stage["required_artifacts"])
            + "\nDo Not: skip fresh evidence checks.\n",
        )
        passport_lines.append(f"| {stage['number']} | done | `{stage['handoff']}` | {artifact_blob} |")
        pipeline_lines.append(f"| {stage['number']} | `{stage['state_key']}` | done | `{stage['handoff']}` |")
    _write(workspace / "00_meta" / "stage_passport.md", "\n".join(passport_lines) + "\n")
    _write(workspace / "00_meta" / "pipeline_status.md", "\n".join(pipeline_lines) + "\n")

    state = _build_state(contract)
    _write(workspace / "00_meta" / "workflow_state.json", json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    _write_filled_final_report(workspace)
    return workspace


def _exists_nonempty(workspace: Path, rel: str) -> bool:
    path = workspace / rel
    return path.exists() and (path.is_dir() or path.stat().st_size > 0)


def evaluate_workspace(workspace: Path, contract: dict) -> dict:
    errors: list[str] = []
    state = _load_json(workspace / "00_meta" / "workflow_state.json")
    stages = contract["stages"]

    if state.get("stages") != {stage["state_key"]: "done" for stage in stages}:
        errors.append("workflow_state stages must be exactly Stage 0-9 done")
    if state.get("orchestration", {}).get("latest_handoff") != stages[-1]["handoff"]:
        errors.append("latest_handoff must point to the Stage 9 handoff")

    reset = state.get("orchestration", {}).get("reset_boundaries")
    if not isinstance(reset, list):
        errors.append("reset_boundaries must be a list")
        reset = []
    reset_stages = {item.get("stage") for item in reset if isinstance(item, dict)}
    if reset_stages != {stage["number"] for stage in stages}:
        errors.append("reset_boundaries must cover every stage 0-9")

    passport = (workspace / "00_meta" / "stage_passport.md").read_text(encoding="utf-8")
    pipeline = (workspace / "00_meta" / "pipeline_status.md").read_text(encoding="utf-8")
    for stage in stages:
        for rel in [stage["log"], stage["handoff"], *stage["required_artifacts"]]:
            if not _exists_nonempty(workspace, rel):
                errors.append(f"missing or empty stage {stage['number']} artifact: {rel}")
        log_text = (workspace / stage["log"]).read_text(encoding="utf-8") if (workspace / stage["log"]).exists() else ""
        handoff_text = (workspace / stage["handoff"]).read_text(encoding="utf-8") if (workspace / stage["handoff"]).exists() else ""
        for artifact in stage["required_artifacts"]:
            if artifact not in log_text:
                errors.append(f"stage {stage['number']} log does not mention artifact: {artifact}")
            if artifact not in handoff_text:
                errors.append(f"stage {stage['number']} handoff does not mention artifact: {artifact}")
        if stage["state_key"] not in pipeline:
            errors.append(f"pipeline_status missing state key: {stage['state_key']}")
        if stage["handoff"] not in passport:
            errors.append(f"stage_passport missing handoff: {stage['handoff']}")

    for rel in contract["final_required_artifacts"]:
        if not _exists_nonempty(workspace, rel):
            errors.append(f"missing final required artifact: {rel}")

    gate = subprocess.run(
        [sys.executable, str(GATE_CHECKER), str(workspace), "--json", "--reconcile"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    try:
        gate_data = json.loads(gate.stdout)
    except json.JSONDecodeError:
        errors.append(f"check_workspace_gates did not emit JSON: {gate.stdout} {gate.stderr}")
        gate_data = {"checks": []}
    failures = [check["check"] for check in gate_data.get("checks", []) if check.get("level") == "FAIL"]
    if gate.returncode != 0 or failures:
        errors.append("workspace gate checker failed: " + ", ".join(failures or [f"exit {gate.returncode}"]))
    ok_checks = {check["check"] for check in gate_data.get("checks", []) if check.get("level") == "OK"}
    for required in ("method_gate:evidence", "quality_gate:evidence", "replication_pack", "reconcile"):
        if required not in ok_checks:
            errors.append(f"workspace gate checker did not prove OK: {required}")

    final_report = subprocess.run(
        [sys.executable, str(FINAL_REPORT_CHECKER), str(workspace / "FINAL_REPORT.md"), "--filled"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    final_report_ok = final_report.returncode == 0
    if not final_report_ok:
        detail = (final_report.stdout or final_report.stderr).strip().splitlines()
        errors.append("filled FINAL_REPORT check failed: " + (detail[-1] if detail else f"exit {final_report.returncode}"))

    return {
        "ok": not errors,
        "errors": errors,
        "stage_count": len(stages),
        "artifact_count": sum(len(stage["required_artifacts"]) for stage in stages),
        "gate_ok_count": len(ok_checks),
        "delivery_check_count": 1 if final_report_ok else 0,
    }


def render(contract_result: dict, workspace_result: dict) -> str:
    lines = [
        "Paper-WorkFlow Stage 0-9 scenario",
        f"  stages: {workspace_result['stage_count']}",
        f"  stage artifacts: {workspace_result['artifact_count']}",
        f"  gate OK checks: {workspace_result['gate_ok_count']}",
        f"  delivery checks: {workspace_result['delivery_check_count']}",
    ]
    for error in contract_result["errors"]:
        lines.append(f"  FAIL: {error}")
    for error in workspace_result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  SCENARIO OK" if contract_result["ok"] and workspace_result["ok"] else "  SCENARIO FAILED")
    return "\n".join(lines)


def _selftest() -> int:
    contract = _load_json(CONTRACT_PATH)
    assert evaluate_contract(contract)["ok"], "live scenario contract must pass schema checks"

    broken = deepcopy(contract)
    broken["stages"][3]["state_key"] = "3_wrong"
    assert not evaluate_contract(broken)["ok"], "state-key drift must fail"

    with tempfile.TemporaryDirectory(prefix="stage-scenario-selftest-") as tmp:
        workspace = build_workspace(Path(tmp), contract)
        assert evaluate_workspace(workspace, contract)["ok"], "built scenario workspace must pass"

        first_artifact = contract["stages"][4]["required_artifacts"][0]
        saved = (workspace / first_artifact).read_text(encoding="utf-8")
        (workspace / first_artifact).unlink()
        assert not evaluate_workspace(workspace, contract)["ok"], "missing stage artifact must fail"
        _write(workspace / first_artifact, saved)

        state_path = workspace / "00_meta" / "workflow_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["orchestration"]["latest_handoff"] = "00_meta/handoff/S00-intake.md"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        assert not evaluate_workspace(workspace, contract)["ok"], "stale latest_handoff must fail"
        state["orchestration"]["latest_handoff"] = contract["stages"][-1]["handoff"]
        state_path.write_text(json.dumps(state), encoding="utf-8")

        log_path = workspace / contract["stages"][6]["log"]
        log_saved = log_path.read_text(encoding="utf-8")
        log_path.write_text("# Stage 6 Log\nArtifacts not recorded.\n", encoding="utf-8")
        assert not evaluate_workspace(workspace, contract)["ok"], "stage log missing artifacts must fail"
        log_path.write_text(log_saved, encoding="utf-8")

        report_path = workspace / "FINAL_REPORT.md"
        report_saved = report_path.read_text(encoding="utf-8")
        report_path.write_text(report_saved.replace("Project: scenario_project", "Project: <short name>", 1), encoding="utf-8")
        assert not evaluate_workspace(workspace, contract)["ok"], "unfilled final report must fail"
        report_path.write_text(report_saved, encoding="utf-8")

    print("selftest OK: Stage 0-9 scenario contract invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    contract = _load_json(CONTRACT_PATH)
    contract_result = evaluate_contract(contract)
    with tempfile.TemporaryDirectory(prefix="stage-scenario-") as tmp:
        workspace = build_workspace(Path(tmp), contract)
        workspace_result = evaluate_workspace(workspace, contract)

    result = {
        "ok": contract_result["ok"] and workspace_result["ok"],
        "contract": contract_result,
        "workspace": workspace_result,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(contract_result, workspace_result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
