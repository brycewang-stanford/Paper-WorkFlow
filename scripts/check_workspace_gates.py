#!/usr/bin/env python3
"""Mechanical gate verifier for a Paper-WorkFlow run workspace.

The two hard gates (Method Gate, Draft Quality Gate) and the replication pack are
enforced at runtime by a critic subagent reading prose. Prose judgement cannot
*guarantee* the cheap, decidable invariants:

  - a gate is marked ``pass`` but its required evidence file does not exist on disk;
  - a gate is marked ``pass`` while an upstream gate it depends on is not passed
    (the orchestrator's rule "the quality gate may be stricter than the method
    gate but never looser");
  - the replication pack is ``ready`` with no master script or no rebuild check.
  - a Method Gate is marked ``pass`` while the design-risk ledger still has
    blocking threats or is not passed.
  - a stage is marked complete but the Stage 0 route / stage passport / latest
    handoff pointer is missing.
  - a Draft Quality Gate or ready replication pack is declared while the claim
    integrity audit is missing, stale, or blocking.
  - a Draft Quality Gate or ready replication pack is declared while the
    citation/temporal-integrity log is missing, malformed, or not final-clean.

This script makes those invariants testable. It reads
``00_meta/workflow_state.json`` from a workspace and reports a gate card. It is
schema-tolerant: unknown keys are ignored and a missing optional block is a WARN,
not a crash, so it keeps working as the state schema evolves.

Usage:
    python3 check_workspace_gates.py <workspace_dir>          # human report
    python3 check_workspace_gates.py <workspace_dir> --json   # machine readable
    python3 check_workspace_gates.py <workspace_dir> --reconcile  # + number check
    python3 check_workspace_gates.py --selftest               # verify this checker

Exit code is non-zero iff at least one HARD inconsistency is found (a gate claims
``pass``/``ready`` but its evidence is missing or its ordering is violated).
Gates still ``pending`` are reported as INFO, not failures — an unfinished run is
not an inconsistent one.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import check_citation_integrity

FAIL = "FAIL"   # hard inconsistency -> non-zero exit
WARN = "WARN"   # worth surfacing, does not fail the run
INFO = "INFO"   # informational (e.g. gate still pending)
OKAY = "OK"     # invariant satisfied


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []  # (level, check, detail)

    def add(self, level: str, check: str, detail: str) -> None:
        self.rows.append((level, check, detail))

    @property
    def failures(self) -> list[tuple[str, str, str]]:
        return [r for r in self.rows if r[0] == FAIL]

    def to_dict(self) -> dict:
        return {
            "ok": not self.failures,
            "checks": [
                {"level": lvl, "check": chk, "detail": det} for lvl, chk, det in self.rows
            ],
        }

    def render(self) -> str:
        width = max((len(c) for _, c, _ in self.rows), default=4)
        lines = ["", "Paper-WorkFlow gate card", "=" * 60]
        for lvl, chk, det in self.rows:
            lines.append(f"[{lvl:<4}] {chk:<{width}}  {det}")
        lines.append("=" * 60)
        if self.failures:
            lines.append(f"RESULT: {len(self.failures)} hard inconsistency(ies) -> gates NOT verified")
        else:
            lines.append("RESULT: no hard inconsistencies -> declared gates are backed by evidence")
        return "\n".join(lines)


def _norm(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _exists(workspace: Path, rel: str) -> bool:
    rel = (rel or "").strip()
    if not rel:
        return False
    # state files sometimes carry an anchor (path.md#section); strip it for the disk check
    rel = rel.split("#", 1)[0]
    return (workspace / rel).exists()


def _passed(status: object) -> bool:
    return _norm(status) in {"pass", "passed"}


def _gate_artifact(block: dict, key: str, default: str) -> str:
    val = block.get(key) if isinstance(block, dict) else None
    return val if isinstance(val, str) and val.strip() else default


def check_state(workspace: Path, state: dict, reconcile: bool) -> Report:
    rep = Report()

    # --- top-level shape (soft: schema may evolve) ---------------------------
    for key in ("project", "orchestration", "stages", "method_gate", "design_risk", "integrity_audit", "quality_gate", "replication_pack"):
        if key not in state:
            rep.add(WARN, f"schema:{key}", "missing top-level block (schema drift?)")

    orchestration = state.get("orchestration", {}) if isinstance(state.get("orchestration"), dict) else {}
    stages = state.get("stages", {}) if isinstance(state.get("stages"), dict) else {}
    empirical = state.get("empirical_audit", {}) if isinstance(state.get("empirical_audit"), dict) else {}
    evidence = state.get("evidence_governance", {}) if isinstance(state.get("evidence_governance"), dict) else {}
    integrity = state.get("integrity_audit", {}) if isinstance(state.get("integrity_audit"), dict) else {}
    design_risk = state.get("design_risk", {}) if isinstance(state.get("design_risk"), dict) else {}
    method = state.get("method_gate", {}) if isinstance(state.get("method_gate"), dict) else {}
    quality = state.get("quality_gate", {}) if isinstance(state.get("quality_gate"), dict) else {}
    replication = state.get("replication_pack", {}) if isinstance(state.get("replication_pack"), dict) else {}
    citation_errors = check_citation_integrity.validate_workspace(workspace, final=False)

    # --- orchestration and continuation ------------------------------------
    if "orchestration" in state:
        completed_stage = any(_norm(v) in {"done", "skipped"} for v in stages.values())
        routing = _gate_artifact(orchestration, "entry_routing", "00_meta/entry_routing.md")
        passport = _gate_artifact(orchestration, "stage_passport", "00_meta/stage_passport.md")
        pipeline_status = _gate_artifact(orchestration, "pipeline_status", "00_meta/pipeline_status.md")
        latest_handoff = str(orchestration.get("latest_handoff") or "").strip()
        if _exists(workspace, routing):
            rep.add(OKAY, "orchestration:routing", f"entry routing present: {routing}")
        else:
            rep.add(WARN, "orchestration:routing", f"missing {routing} (Stage 0 route not recorded)")
        if _exists(workspace, passport):
            rep.add(OKAY, "orchestration:passport", f"stage passport present: {passport}")
        elif completed_stage:
            rep.add(FAIL, "orchestration:passport", f"stage completed but missing {passport}")
        else:
            rep.add(WARN, "orchestration:passport", f"missing {passport}")
        if _exists(workspace, pipeline_status):
            rep.add(OKAY, "orchestration:pipeline_status", f"pipeline status present: {pipeline_status}")
        elif completed_stage:
            rep.add(WARN, "orchestration:pipeline_status", f"stage completed but missing {pipeline_status}")
        else:
            rep.add(INFO, "orchestration:pipeline_status", f"missing {pipeline_status}")
        if latest_handoff:
            if _exists(workspace, latest_handoff):
                rep.add(OKAY, "orchestration:handoff", f"latest handoff present: {latest_handoff}")
            else:
                rep.add(FAIL, "orchestration:handoff", f"latest_handoff set but missing {latest_handoff}")
        elif completed_stage:
            rep.add(WARN, "orchestration:handoff", "stage completed but latest_handoff is empty")
        if orchestration.get("fresh_evidence_required") is not True:
            rep.add(WARN, "orchestration:evidence", "fresh_evidence_required is not true")
        cap = orchestration.get("revision_rounds_cap")
        if isinstance(cap, int) and cap < 1:
            rep.add(WARN, "orchestration:revision_cap", f"revision_rounds_cap={cap}")
        reset_boundaries = orchestration.get("reset_boundaries")
        if reset_boundaries is not None and not isinstance(reset_boundaries, list):
            rep.add(WARN, "orchestration:reset_boundaries", "reset_boundaries is not a list")

    # --- empirical (sample/estimand) audit -----------------------------------
    if _passed(empirical.get("status")):
        sample_audit = _gate_artifact(empirical, "sample_audit", "02_data/sample_audit.md")
        if _exists(workspace, sample_audit):
            rep.add(OKAY, "empirical_audit", f"pass, sample audit present: {sample_audit}")
        else:
            rep.add(FAIL, "empirical_audit", f"status=pass but missing {sample_audit}")
    else:
        rep.add(INFO, "empirical_audit", f"status={empirical.get('status', 'absent')}")

    # --- evidence governance (claim ledger) ----------------------------------
    if _passed(evidence.get("status")):
        ledger = _gate_artifact(evidence, "evidence_ledger", "00_meta/evidence_ledger.md")
        if not _exists(workspace, ledger):
            rep.add(FAIL, "evidence_governance", f"status=pass but missing {ledger}")
        else:
            rep.add(OKAY, "evidence_governance", f"pass, evidence ledger present: {ledger}")
        open_disc = evidence.get("open_discrepancies")
        if isinstance(open_disc, list) and open_disc:
            rep.add(WARN, "evidence_governance:open", f"status=pass but {len(open_disc)} open discrepancy(ies) recorded")
    elif "evidence_governance" in state:
        rep.add(INFO, "evidence_governance", f"status={evidence.get('status', 'absent')}")

    # --- claim integrity audit ----------------------------------------------
    istatus = _norm(integrity.get("status"))
    integrity_ok_for_quality = istatus in {"pass", "passed", "pass_with_notes"}
    integrity_ready_for_delivery = istatus in {"pass", "passed"}
    if integrity_ok_for_quality:
        audit = _gate_artifact(integrity, "claim_integrity_audit", "00_meta/claim_integrity_audit.md")
        if not _exists(workspace, audit):
            rep.add(FAIL, "integrity_audit", f"status={integrity.get('status')} but missing {audit}")
        else:
            rep.add(OKAY, "integrity_audit", f"{integrity.get('status')}, audit present: {audit}")
        blocking = integrity.get("blocking_findings")
        if isinstance(blocking, list) and blocking:
            rep.add(FAIL, "integrity_audit:blocking", f"status={integrity.get('status')} but {len(blocking)} blocking finding(s) recorded")
        unsupported = integrity.get("unsupported_claims")
        if isinstance(unsupported, int) and unsupported > 0:
            rep.add(FAIL, "integrity_audit:unsupported", f"status={integrity.get('status')} but unsupported_claims={unsupported}")
        unverified = integrity.get("unverified_citations")
        if istatus == "pass" and isinstance(unverified, int) and unverified > 0:
            rep.add(WARN, "integrity_audit:unverified", f"status=pass but unverified_citations={unverified}")
        checked = integrity.get("checked_claims")
        if isinstance(checked, int) and checked == 0:
            rep.add(WARN, "integrity_audit:coverage", "status pass/pass_with_notes but checked_claims=0")
    elif "integrity_audit" in state:
        rep.add(INFO, "integrity_audit", f"status={integrity.get('status', 'absent')}")

    # --- citation existence + temporal integrity ----------------------------
    citation_log = check_citation_integrity.LOG_RELPATH
    if citation_errors:
        level = FAIL if _passed(quality.get("status")) else WARN
        rep.add(
            level,
            "citation_integrity",
            f"{citation_log} not pre-final clean: " + "; ".join(citation_errors[:3]),
        )
    else:
        rep.add(OKAY, "citation_integrity", f"pre-final log passes: {citation_log}")

    # --- design risk ledger -------------------------------------------------
    if _passed(design_risk.get("status")):
        ledger = _gate_artifact(design_risk, "risk_ledger", "03_analysis/design_risk_ledger.md")
        if not _exists(workspace, ledger):
            rep.add(FAIL, "design_risk", f"status=pass but missing {ledger}")
        else:
            rep.add(OKAY, "design_risk", f"pass, risk ledger present: {ledger}")
        blocking = design_risk.get("blocking_threats")
        if isinstance(blocking, list) and blocking:
            rep.add(FAIL, "design_risk:blocking", f"status=pass but {len(blocking)} blocking threat(s) recorded")
        reviewed = design_risk.get("threats_reviewed")
        if isinstance(reviewed, list) and not reviewed:
            rep.add(WARN, "design_risk:review", "status=pass but threats_reviewed is empty")
        for key in ("external_validity", "specification_search", "spillover_interference", "selection_attrition"):
            if _norm(design_risk.get(key)) in {"not_pass", "blocking", "fail", "failed"}:
                rep.add(FAIL, f"design_risk:{key}", f"status=pass but {key}={design_risk.get(key)}")
    elif "design_risk" in state:
        rep.add(INFO, "design_risk", f"status={design_risk.get('status', 'absent')}")

    # --- method gate ---------------------------------------------------------
    if _passed(method.get("status")):
        required = {
            "design_register": _gate_artifact(method, "design_register", "03_analysis/design_register.md"),
            "method_gate_report": _gate_artifact(method, "method_gate_report", "03_analysis/method_gate.md"),
            "sample_audit": _gate_artifact(empirical, "sample_audit", "02_data/sample_audit.md"),
            "main_results": "03_analysis/results/main_results.json",
        }
        missing = [f"{name}={path}" for name, path in required.items() if not _exists(workspace, path)]
        if missing:
            rep.add(FAIL, "method_gate:evidence", "status=pass but missing: " + "; ".join(missing))
        else:
            rep.add(OKAY, "method_gate:evidence", "pass, all required artifacts present")

        declared_missing = method.get("missing_artifacts")
        if isinstance(declared_missing, list) and declared_missing:
            rep.add(FAIL, "method_gate:self", f"status=pass but missing_artifacts not empty: {declared_missing}")

        # ordering: a passed method gate requires a passed sample/estimand audit
        if "empirical_audit" in state and not _passed(empirical.get("status")):
            rep.add(
                FAIL,
                "method_gate:ordering",
                f"status=pass but empirical_audit.status={empirical.get('status', 'absent')} "
                "(sample/estimand audit must pass first)",
            )
        if "design_risk" in state and not _passed(design_risk.get("status")):
            rep.add(
                FAIL,
                "method_gate:design_risk",
                f"status=pass but design_risk.status={design_risk.get('status', 'absent')} "
                "(design-risk ledger must pass before Method Gate can pass)",
            )

        # inference layer companion (soft, this skill introduces it as method-gate kin)
        if not _exists(workspace, "03_analysis/inference_report.md"):
            rep.add(WARN, "method_gate:inference", "no 03_analysis/inference_report.md "
                                                   "(clustering / few-cluster / multiple-testing rationale unrecorded)")
    else:
        rep.add(INFO, "method_gate", f"status={method.get('status', 'absent')}")

    # --- draft quality gate --------------------------------------------------
    if _passed(quality.get("status")):
        scorecard = _gate_artifact(quality, "scorecard", "00_meta/quality_scorecard.md")
        if not _exists(workspace, scorecard):
            rep.add(FAIL, "quality_gate:evidence", f"status=pass but missing {scorecard}")
        else:
            rep.add(OKAY, "quality_gate:evidence", f"pass, scorecard present: {scorecard}")
        # ordering: quality gate cannot be looser than the method gate
        if not _passed(method.get("status")):
            rep.add(
                FAIL,
                "quality_gate:ordering",
                f"status=pass but method_gate.status={method.get('status', 'absent')} "
                "(quality gate may be stricter than the method gate, never looser)",
            )
        if "integrity_audit" in state and not integrity_ok_for_quality:
            rep.add(
                FAIL,
                "quality_gate:integrity",
                f"status=pass but integrity_audit.status={integrity.get('status', 'absent')} "
                "(claim integrity audit must pass or pass_with_notes before Draft Quality Gate can pass)",
            )
        if citation_errors:
            rep.add(
                FAIL,
                "quality_gate:citation_integrity",
                f"status=pass but {citation_log} is not pre-final clean "
                "(citation existence and temporal integrity must be checked before Draft Quality Gate can pass)",
            )
    else:
        rep.add(INFO, "quality_gate", f"status={quality.get('status', 'absent')}")

    # --- replication pack ----------------------------------------------------
    rstatus = _norm(replication.get("status"))
    if rstatus == "ready":
        problems = []
        master = _gate_artifact(replication, "master_script", "")
        if not master:
            problems.append("master_script unset")
        elif not _exists(workspace, master):
            problems.append(f"master_script missing on disk ({master})")
        readme = _gate_artifact(replication, "readme", "REPLICATION.md")
        if not _exists(workspace, readme):
            problems.append(f"readme missing ({readme})")
        if not str(replication.get("last_rebuild_check") or "").strip():
            problems.append("last_rebuild_check empty")
        if "integrity_audit" in state and not integrity_ready_for_delivery:
            problems.append(f"integrity_audit.status={integrity.get('status', 'absent')} (must be pass for delivery)")
        citation_final_errors = check_citation_integrity.validate_workspace(workspace, final=True)
        if citation_final_errors:
            problems.append(
                f"{citation_log} not final-clean ({'; '.join(citation_final_errors[:3])})"
            )
        if problems:
            rep.add(FAIL, "replication_pack", "status=ready but " + "; ".join(problems))
        else:
            rep.add(OKAY, "replication_pack", f"ready, master script present: {master}")
    else:
        rep.add(INFO, "replication_pack", f"status={replication.get('status', 'absent')}")

    # --- optional numbers reconciliation (heuristic, advisory) ---------------
    if reconcile:
        _reconcile_numbers(workspace, rep)

    return rep


_NUM_RE = re.compile(r"-?\d+\.\d+")


def _collect_numbers(obj: object, out: list[float]) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, float):
        out.append(obj)
    elif isinstance(obj, str):
        for m in _NUM_RE.findall(obj):
            try:
                out.append(float(m))
            except ValueError:
                pass
    elif isinstance(obj, dict):
        for v in obj.values():
            _collect_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_numbers(v, out)


def _reconcile_numbers(workspace: Path, rep: Report) -> None:
    results = workspace / "03_analysis" / "results" / "main_results.json"
    if not results.exists():
        rep.add(INFO, "reconcile", "no main_results.json to reconcile")
        return
    exhibits = list((workspace / "04_results").glob("*.tex")) + list((workspace / "04_results").glob("*.md"))
    if not exhibits:
        rep.add(INFO, "reconcile", "no .tex/.md exhibits in 04_results to reconcile against")
        return
    try:
        data = json.loads(results.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.add(WARN, "reconcile", f"main_results.json not valid JSON: {exc}")
        return
    numbers: list[float] = []
    _collect_numbers(data, numbers)
    # keep coefficient-like values (a decimal point, magnitude not trivially tiny/huge)
    coefs = {round(n, 3) for n in numbers if 0.001 <= abs(n) < 1e6}
    if not coefs:
        rep.add(INFO, "reconcile", "no coefficient-like numbers found in main_results.json")
        return
    blob = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in exhibits)
    found = 0
    missing_samples: list[str] = []
    for c in coefs:
        variants = {f"{c:.3f}", f"{c:.2f}", f"{c:g}"}
        if any(v in blob for v in variants):
            found += 1
        elif len(missing_samples) < 5:
            missing_samples.append(f"{c:g}")
    total = len(coefs)
    if found == total:
        rep.add(OKAY, "reconcile", f"all {total} coefficient-like values appear in exhibits")
    else:
        rep.add(
            WARN,
            "reconcile",
            f"{found}/{total} result numbers found in exhibits; "
            f"not located (sample): {', '.join(missing_samples)} "
            "(heuristic — verify table↔results mapping in evidence ledger)",
        )


def run(workspace: Path, reconcile: bool) -> Report:
    state_path = workspace / "00_meta" / "workflow_state.json"
    rep = Report()
    if not state_path.exists():
        rep.add(FAIL, "workspace", f"no state file at {state_path}")
        return rep
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        rep.add(FAIL, "workspace", f"workflow_state.json is not valid JSON: {exc}")
        return rep
    return check_state(workspace, state, reconcile)


def _selftest() -> int:
    """Build synthetic workspaces and assert the checker's invariants hold."""
    with tempfile.TemporaryDirectory(prefix="gate-selftest-") as tmp:
        root = Path(tmp)

        def touch(ws: Path, rel: str) -> None:
            p = ws / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x", encoding="utf-8")

        def write_state(ws: Path, state: dict) -> None:
            (ws / "00_meta").mkdir(parents=True, exist_ok=True)
            (ws / "00_meta" / "workflow_state.json").write_text(json.dumps(state), encoding="utf-8")

        def write_citation_log(ws: Path, final_clean: bool = True) -> None:
            (ws / "00_meta").mkdir(parents=True, exist_ok=True)
            status = "verified" if final_clean else "to-verify"
            note = "ok" if final_clean else "needs DOI check"
            (ws / check_citation_integrity.LOG_RELPATH).write_text(
                f"""## 1. Citation Verification
| Bibkey | Cited claim | Identifier | Metadata match | Version | Retraction/erratum | Status | Checked | Note |
|---|---|---|---|---|---|---|---|---|
| smith2020 | baseline citation | 10.1/example | ok | published | clean | {status} | 2026-06-23 | {note} |

## 2. Temporal Integrity
| Risk | Source | Requirement met? | Conclusion | Consequence if risk |
|---|---|---|---|---|
| Feature look-ahead | Compustat | yes | pass | na |
""",
                encoding="utf-8",
            )

        # --- good workspace: every declared gate is backed by evidence -------
        good = root / "good"
        for rel in (
            "00_meta/entry_routing.md",
            "00_meta/stage_passport.md",
            "00_meta/pipeline_status.md",
            "00_meta/handoff/S01-ready.md",
            "02_data/sample_audit.md",
            "03_analysis/design_register.md",
            "03_analysis/method_gate.md",
            "03_analysis/results/main_results.json",
            "03_analysis/inference_report.md",
            "00_meta/quality_scorecard.md",
            "00_meta/evidence_ledger.md",
            "00_meta/claim_integrity_audit.md",
            "03_analysis/design_risk_ledger.md",
            "REPLICATION.md",
            "run_all.sh",
        ):
            touch(good, rel)
        write_citation_log(good)
        write_state(good, {
            "project": {}, "stages": {}, "artifacts": {}, "decisions": [],
            "orchestration": {
                "status": "active",
                "entry_routing": "00_meta/entry_routing.md",
                "stage_passport": "00_meta/stage_passport.md",
                "pipeline_status": "00_meta/pipeline_status.md",
                "handoff_dir": "00_meta/handoff",
                "latest_handoff": "00_meta/handoff/S01-ready.md",
                "fresh_evidence_required": True,
                "revision_rounds_cap": 2,
                "reset_boundaries": [],
            },
            "empirical_audit": {"status": "pass", "sample_audit": "02_data/sample_audit.md"},
            "evidence_governance": {"status": "pass", "evidence_ledger": "00_meta/evidence_ledger.md", "open_discrepancies": []},
            "integrity_audit": {
                "status": "pass",
                "claim_integrity_audit": "00_meta/claim_integrity_audit.md",
                "checked_claims": 12,
                "unsupported_claims": 0,
                "unverified_citations": 0,
                "blocking_findings": [],
            },
            "design_risk": {
                "status": "pass",
                "risk_ledger": "03_analysis/design_risk_ledger.md",
                "threats_reviewed": ["parallel_trends", "external_validity"],
                "blocking_threats": [],
                "external_validity": "pass",
                "specification_search": "pass",
                "spillover_interference": "not_applicable",
                "selection_attrition": "pass",
            },
            "method_gate": {
                "status": "pass",
                "design_register": "03_analysis/design_register.md",
                "method_gate_report": "03_analysis/method_gate.md",
                "missing_artifacts": [],
            },
            "quality_gate": {"status": "pass", "scorecard": "00_meta/quality_scorecard.md"},
            "replication_pack": {
                "status": "ready", "readme": "REPLICATION.md",
                "master_script": "run_all.sh", "last_rebuild_check": "rebuilt 2026-06-21",
            },
        })
        rep = run(good, reconcile=False)
        assert not rep.failures, f"good workspace should pass, got: {rep.failures}"

        # --- bad workspace A: method gate claims pass without evidence -------
        bad_a = root / "bad_a"
        write_state(bad_a, {
            "project": {}, "stages": {"0_intake_setup": "done"},
            "orchestration": {
                "entry_routing": "00_meta/entry_routing.md",
                "stage_passport": "00_meta/stage_passport.md",
                "pipeline_status": "00_meta/pipeline_status.md",
                "latest_handoff": "00_meta/handoff/S99-missing.md",
                "fresh_evidence_required": False,
                "revision_rounds_cap": 0,
                "reset_boundaries": "not-a-list",
            },
            "empirical_audit": {"status": "not_pass", "sample_audit": "02_data/sample_audit.md"},
            "evidence_governance": {"status": "pass", "evidence_ledger": "00_meta/evidence_ledger.md"},
            "design_risk": {"status": "pass", "risk_ledger": "03_analysis/design_risk_ledger.md", "blocking_threats": ["bad control"]},
            "method_gate": {"status": "pass", "missing_artifacts": ["main_results"]},
            "replication_pack": {"status": "ready", "master_script": "", "last_rebuild_check": ""},
        })
        hit_a = {chk for lvl, chk, det in run(bad_a, reconcile=False).rows if lvl == FAIL}
        expect_a = {
            "evidence_governance",    # status=pass but ledger missing on disk
            "method_gate:evidence",   # required artifacts missing
            "method_gate:self",       # missing_artifacts non-empty while pass
            "method_gate:ordering",   # empirical audit not passed
            "design_risk",            # status=pass but risk ledger missing on disk
            "design_risk:blocking",   # status=pass but blocking threat recorded
            "replication_pack",       # ready but no master script / rebuild check
            "orchestration:passport",  # completed stage but no passport
            "orchestration:handoff",   # latest handoff set but missing
        }
        assert expect_a <= hit_a, f"bad_a should flag {expect_a - hit_a}; got {hit_a}"

        # --- bad workspace B: quality gate looser than the method gate -------
        bad_b = root / "bad_b"
        touch(bad_b, "00_meta/quality_scorecard.md")
        write_state(bad_b, {
            "project": {}, "stages": {},
            "design_risk": {"status": "pending"},
            "integrity_audit": {"status": "not_pass"},
            "method_gate": {"status": "not_pass"},
            "quality_gate": {"status": "pass", "scorecard": "00_meta/quality_scorecard.md"},
        })
        hit_b = {chk for lvl, chk, det in run(bad_b, reconcile=False).rows if lvl == FAIL}
        assert "quality_gate:ordering" in hit_b, f"bad_b should flag quality_gate:ordering; got {hit_b}"
        assert "quality_gate:integrity" in hit_b, f"bad_b should flag quality_gate:integrity; got {hit_b}"
        assert "quality_gate:citation_integrity" in hit_b, (
            f"bad_b should flag quality_gate:citation_integrity; got {hit_b}"
        )

        # --- bad workspace C: method gate skips unresolved design risk -------
        bad_c = root / "bad_c"
        for rel in (
            "02_data/sample_audit.md",
            "03_analysis/design_register.md",
            "03_analysis/method_gate.md",
            "03_analysis/results/main_results.json",
        ):
            touch(bad_c, rel)
        write_state(bad_c, {
            "project": {}, "stages": {},
            "empirical_audit": {"status": "pass", "sample_audit": "02_data/sample_audit.md"},
            "design_risk": {"status": "not_pass", "risk_ledger": "03_analysis/design_risk_ledger.md"},
            "method_gate": {"status": "pass", "missing_artifacts": []},
        })
        hit_c = {chk for lvl, chk, det in run(bad_c, reconcile=False).rows if lvl == FAIL}
        assert "method_gate:design_risk" in hit_c, f"bad_c should flag method_gate:design_risk; got {hit_c}"

        # --- bad workspace D: integrity audit claims pass while blocking ----
        bad_d = root / "bad_d"
        touch(bad_d, "00_meta/claim_integrity_audit.md")
        touch(bad_d, "REPLICATION.md")
        touch(bad_d, "run_all.sh")
        write_state(bad_d, {
            "project": {}, "stages": {},
            "integrity_audit": {
                "status": "pass",
                "claim_integrity_audit": "00_meta/claim_integrity_audit.md",
                "checked_claims": 0,
                "unsupported_claims": 1,
                "unverified_citations": 2,
                "blocking_findings": ["C2 unsupported"],
            },
            "replication_pack": {
                "status": "ready",
                "readme": "REPLICATION.md",
                "master_script": "run_all.sh",
                "last_rebuild_check": "rebuilt",
            },
        })
        hit_d = {chk for lvl, chk, det in run(bad_d, reconcile=False).rows if lvl == FAIL}
        for expected in ("integrity_audit:blocking", "integrity_audit:unsupported"):
            assert expected in hit_d, f"bad_d should flag {expected}; got {hit_d}"

        # --- empty / missing state -------------------------------------------
        rep = run(root / "does_not_exist", reconcile=False)
        assert rep.failures, "missing workspace should fail"

    print("selftest OK: gate verifier invariants hold")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Mechanical gate verifier for a Paper-WorkFlow workspace.")
    parser.add_argument("workspace", nargs="?", help="path to the paper_workspace/<run> directory")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--reconcile", action="store_true", help="also heuristically check result numbers vs exhibits")
    parser.add_argument("--selftest", action="store_true", help="verify this checker on synthetic workspaces")
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    if not args.workspace:
        parser.error("workspace path is required (or pass --selftest)")

    rep = run(Path(args.workspace).expanduser().resolve(), reconcile=args.reconcile)
    if args.json:
        print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(rep.render())
    return 1 if rep.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
