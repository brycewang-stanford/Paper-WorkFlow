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
  - a Method Gate is marked ``pass`` while the design lock (pre-registration)
    was never taken, or was taken *after* the main results already existed.
  - a Draft Quality Gate is declared while the manuscript still asserts numbers
    no analysis output backs, or a numerically inert rewrite boundary drifted.

Beyond auditing a finished stage, the same contract answers the cheaper question
*may this stage start at all?* (``--preconditions <stage>``). Every failure the
gate card reports is a failure discovered after the work was done; a precondition
is the same fact checked before, which is where a rollback is affordable.

This script makes those invariants testable. It reads
``00_meta/workflow_state.json`` from a workspace and reports a gate card. It is
schema-tolerant: unknown keys are ignored and a missing optional block is a WARN,
not a crash, so it keeps working as the state schema evolves.

Usage:
    python3 check_workspace_gates.py <workspace_dir>          # human report
    python3 check_workspace_gates.py <workspace_dir> --json   # machine readable
    python3 check_workspace_gates.py <workspace_dir> --reconcile  # + number check
    python3 check_workspace_gates.py <ws> --preconditions 3   # may Stage 3 start?
    python3 check_workspace_gates.py --selftest               # verify this checker

Exit code is non-zero iff at least one HARD inconsistency is found (a gate claims
``pass``/``ready`` but its evidence is missing or its ordering is violated).
Gates still ``pending`` are reported as INFO, not failures — an unfinished run is
not an inconsistent one.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
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
    def __init__(self, title: str = "Paper-WorkFlow gate card",
                 fail_summary: str = "hard inconsistency(ies) -> gates NOT verified",
                 pass_summary: str = "no hard inconsistencies -> declared gates are backed by evidence") -> None:
        self.title = title
        self.fail_summary = fail_summary
        self.pass_summary = pass_summary
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
        lines = ["", self.title, "=" * 60]
        for lvl, chk, det in self.rows:
            lines.append(f"[{lvl:<4}] {chk:<{width}}  {det}")
        lines.append("=" * 60)
        if self.failures:
            lines.append(f"RESULT: {len(self.failures)} {self.fail_summary}")
        else:
            lines.append(f"RESULT: {self.pass_summary}")
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


# --------------------------------------------------------------------------- #
# scope tiers                                                                  #
# --------------------------------------------------------------------------- #
# What "finished" means depends on what is being produced. A two-day working
# paper and a top-field submission share the same pipeline, but not the same
# required gate set. Scope selects the set; it never relaxes verification of a
# gate the run explicitly claims to have passed.
SCOPE_REQUIRED_GATES = {
    "draft": ["method_gate"],
    "working-paper": ["method_gate", "design_risk", "quality_gate"],
    "submission": [
        "method_gate", "design_risk", "quality_gate",
        "integrity_audit", "manuscript_numbers", "ai_disclosure", "replication_pack",
    ],
}
DEFAULT_SCOPE = "submission"


# --------------------------------------------------------------------------- #
# stage preconditions                                                          #
# --------------------------------------------------------------------------- #
# (label, kind, target) where kind is "file" (must exist in the workspace) or
# "gate" (state block whose status must be pass/passed/locked/ready).
STAGE_PRECONDITIONS: dict[str, list[tuple[str, str, str]]] = {
    "1L": [
        ("entry routing recorded", "file", "00_meta/entry_routing.md"),
    ],
    "2": [
        ("proposal fixes the variables to collect", "file", "01_proposal/proposal.md"),
    ],
    "2_5": [
        ("proposal", "file", "01_proposal/proposal.md"),
        ("sample audit exists (data is in hand)", "file", "02_data/sample_audit.md"),
    ],
    "3": [
        ("design lock taken before any estimate", "gate", "design_lock"),
        ("pre-registration on disk", "file", "00_meta/preregistration.md"),
        ("sample audit", "file", "02_data/sample_audit.md"),
        ("design register drafted", "file", "03_analysis/design_register.md"),
    ],
    "4": [
        ("method gate passed", "gate", "method_gate"),
    ],
    "5": [
        ("method gate passed", "gate", "method_gate"),
        ("evidence ledger maps claims to results", "file", "00_meta/evidence_ledger.md"),
    ],
    "7": [
        ("a manuscript to rewrite", "file", "06_polish/main.tex"),
    ],
    "8": [
        ("draft quality gate passed", "gate", "quality_gate"),
    ],
    "9": [
        ("draft quality gate passed", "gate", "quality_gate"),
        ("claim integrity audit passed", "gate", "integrity_audit"),
        ("AI-use disclosure ledger on disk", "file", "00_meta/ai_use_disclosure.md"),
    ],
}

_READY_STATES = {"pass", "passed", "locked", "ready", "pass_with_notes"}


def check_preconditions(workspace: Path, state: dict, stage: str) -> Report:
    """Answer 'may this stage start?' before the work is done, not after."""
    rep = Report(
        f"Paper-WorkFlow stage preconditions -- Stage {stage}",
        fail_summary="unmet precondition(s) -> this stage must NOT start yet",
        pass_summary="preconditions met -> the stage may start",
    )
    key = str(stage).strip().lower().replace(".", "_").replace("-", "_")
    if key not in STAGE_PRECONDITIONS:
        known = ", ".join(sorted(STAGE_PRECONDITIONS))
        rep.add(INFO, f"stage:{stage}", f"no preconditions declared for this stage (known: {known})")
        return rep

    for label, kind, target in STAGE_PRECONDITIONS[key]:
        if kind == "file":
            if _exists(workspace, target):
                rep.add(OKAY, f"pre:{target}", label)
            else:
                rep.add(FAIL, f"pre:{target}", f"missing — {label}")
        else:
            block = state.get(target)
            status = _norm(block.get("status")) if isinstance(block, dict) else "absent"
            if status in _READY_STATES:
                rep.add(OKAY, f"pre:{target}", f"{label} (status={status})")
            else:
                rep.add(FAIL, f"pre:{target}", f"{target}.status={status} — {label}")

    if not rep.failures:
        rep.add(OKAY, f"stage:{stage}", "all preconditions met; the stage may start")
    return rep


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
    design_lock = state.get("design_lock", {}) if isinstance(state.get("design_lock"), dict) else {}
    numbers = state.get("manuscript_numbers", {}) if isinstance(state.get("manuscript_numbers"), dict) else {}
    ai_disc = state.get("ai_disclosure", {}) if isinstance(state.get("ai_disclosure"), dict) else {}
    project = state.get("project", {}) if isinstance(state.get("project"), dict) else {}
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
        # Rollback caps exist so an unattended run cannot loop forever on a gate it
        # will never pass. Exceeding one is not a crime -- it is a signal to stop
        # retrying and deliver with the shortfall documented.
        mg_cap = orchestration.get("method_gate_rounds_cap")
        mg_rounds = orchestration.get("method_gate_rounds")
        if isinstance(mg_cap, int) and isinstance(mg_rounds, int) and mg_rounds > mg_cap:
            rep.add(
                WARN,
                "orchestration:method_gate_cap",
                f"method_gate_rounds={mg_rounds} exceeds cap {mg_cap}; stop re-running "
                "Stage 1/2/3 and deliver with the shortfall recorded as a known gap",
            )
        q_rounds = quality.get("rounds")
        if isinstance(cap, int) and isinstance(q_rounds, int) and q_rounds > cap:
            rep.add(
                WARN,
                "orchestration:quality_cap",
                f"quality_gate.rounds={q_rounds} exceeds revision_rounds_cap {cap}",
            )
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

    # --- AI-use disclosure ---------------------------------------------------
    # The pipeline drafts, polishes and de-AIGCs with an LLM. Every venue policy
    # in references/ai-use-disclosure.md requires that to be declared, and the one
    # stage that could quietly erase the evidence is the same stage that removes
    # the stylistic fingerprint. So: Stage 7 done => a disclosure ledger exists,
    # and a declared pass has to be backed by the file it claims.
    ai_status = _norm(ai_disc.get("status"))
    ai_ready_for_delivery = ai_status in {"pass", "passed"}
    ai_file = _gate_artifact(ai_disc, "disclosure_file", "00_meta/ai_use_disclosure.md")
    if ai_status in {"pass", "passed", "pass_with_notes"}:
        if not _exists(workspace, ai_file):
            rep.add(FAIL, "ai_disclosure", f"status={ai_disc.get('status')} but missing {ai_file}")
        else:
            rep.add(OKAY, "ai_disclosure", f"{ai_disc.get('status')}, ledger present: {ai_file}")
        blocking = ai_disc.get("blocking_findings")
        if isinstance(blocking, list) and blocking:
            rep.add(FAIL, "ai_disclosure:blocking",
                    f"status={ai_disc.get('status')} but {len(blocking)} blocking finding(s) recorded")
        rows = ai_disc.get("ledger_rows")
        if isinstance(rows, int) and rows == 0:
            rep.add(FAIL, "ai_disclosure:empty",
                    "status=pass but ledger_rows=0 — an AI pipeline that recorded no AI use "
                    "has not disclosed, it has just not written anything down")
        if not str(ai_disc.get("policy_family") or "").strip():
            rep.add(WARN, "ai_disclosure:policy", "status=pass but policy_family is unset")
    elif "ai_disclosure" in state:
        rep.add(INFO, "ai_disclosure", f"status={ai_disc.get('status', 'absent')}")

    # The de-AIGC stage may not outrun its own disclosure.
    if _norm(stages.get("7_language_dehumanize")) == "done":
        if not _exists(workspace, ai_file):
            rep.add(FAIL, "ai_disclosure:stage7",
                    f"Stage 7 (de-AIGC) is done but {ai_file} does not exist — the stage that "
                    "removes the AI accent must not also remove the AI disclosure")
        elif ai_status in {"", "pending", "absent"}:
            rep.add(WARN, "ai_disclosure:stage7",
                    "Stage 7 is done but ai_disclosure.status is still pending — run "
                    "scripts/check_ai_disclosure.py and write the verdict back")

    # ethics_gate is the human-facing summary of this and the governance checks;
    # it cannot be greener than the mechanical gate underneath it.
    if _passed(orchestration.get("ethics_gate")) and "ai_disclosure" in state and not ai_ready_for_delivery:
        rep.add(FAIL, "orchestration:ethics_gate",
                f"ethics_gate=pass but ai_disclosure.status={ai_disc.get('status', 'absent')}")

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

    # --- design lock (pre-registration taken before estimation) --------------
    # A lock written after the results exist is not a lock; it is a transcript of
    # what was found. The one fact that makes it decidable is whether the primary
    # specification was fixed while the answer was still unknown.
    lock_status = _norm(design_lock.get("status"))
    if "design_lock" in state:
        prereg = _gate_artifact(design_lock, "preregistration", "00_meta/preregistration.md")
        results_exist = _exists(workspace, "03_analysis/results/main_results.json")
        if lock_status in {"locked", "pass", "passed"}:
            if not _exists(workspace, prereg):
                rep.add(FAIL, "design_lock", f"status={design_lock.get('status')} but missing {prereg}")
            elif design_lock.get("locked_before_estimation") is not True:
                rep.add(
                    FAIL,
                    "design_lock:timing",
                    "status=locked but locked_before_estimation is not true "
                    "(a lock taken after the results is not a lock)",
                )
            else:
                rep.add(OKAY, "design_lock", f"locked before estimation: {prereg}")
            if isinstance(design_lock.get("confirmatory_count"), int) and design_lock["confirmatory_count"] < 1:
                rep.add(WARN, "design_lock:hypotheses", "locked with zero confirmatory hypotheses registered")
        elif results_exist:
            rep.add(
                FAIL,
                "design_lock:timing",
                f"main results exist but design_lock.status={design_lock.get('status', 'absent')} "
                "(Stage 2.5 must lock the specification before Stage 3 estimates anything)",
            )
        else:
            rep.add(INFO, "design_lock", f"status={design_lock.get('status', 'absent')}")

    # --- manuscript numeric anchoring ---------------------------------------
    num_status = _norm(numbers.get("status"))
    if "manuscript_numbers" in state:
        unanchored = numbers.get("unanchored_claims")
        drift = numbers.get("inert_boundary_drift")
        problems = []
        if isinstance(unanchored, int) and unanchored > 0:
            problems.append(f"unanchored_claims={unanchored}")
        if isinstance(drift, int) and drift > 0:
            problems.append(f"inert_boundary_drift={drift}")
        if num_status in {"pass", "passed"}:
            if problems:
                rep.add(FAIL, "manuscript_numbers", "status=pass but " + "; ".join(problems))
            elif not str(numbers.get("checked_manuscript") or "").strip():
                rep.add(WARN, "manuscript_numbers", "status=pass but checked_manuscript is empty")
            else:
                rep.add(OKAY, "manuscript_numbers", f"pass, checked {numbers.get('checked_manuscript')}")
        else:
            rep.add(INFO, "manuscript_numbers", f"status={numbers.get('status', 'absent')}")

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
        if "design_lock" in state and lock_status not in {"locked", "pass", "passed"}:
            rep.add(
                FAIL,
                "method_gate:design_lock",
                f"status=pass but design_lock.status={design_lock.get('status', 'absent')} "
                "(the specification must have been locked before estimation; without it "
                "the robustness matrix cannot be distinguished from specification search)",
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
        if "manuscript_numbers" in state:
            unanchored = numbers.get("unanchored_claims")
            drift = numbers.get("inert_boundary_drift")
            if num_status not in {"pass", "passed"}:
                rep.add(
                    FAIL,
                    "quality_gate:numbers",
                    f"status=pass but manuscript_numbers.status={numbers.get('status', 'absent')} "
                    "(run scripts/check_manuscript_numbers.py: every figure in the draft must "
                    "trace to analysis output before the draft can be called submittable)",
                )
            elif (isinstance(unanchored, int) and unanchored > 0) or (isinstance(drift, int) and drift > 0):
                rep.add(
                    FAIL,
                    "quality_gate:numbers",
                    f"status=pass but unanchored_claims={unanchored}, inert_boundary_drift={drift}",
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
        if "ai_disclosure" in state and not ai_ready_for_delivery:
            problems.append(f"ai_disclosure.status={ai_disc.get('status', 'absent')} (must be pass for delivery)")
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

    # --- scope coverage ------------------------------------------------------
    # Which gates a finished run owes depends on what it set out to produce. This
    # row never loosens a claimed gate (those are verified above regardless); it
    # states the completion contract so "done" means the same thing twice.
    scope = _norm(project.get("scope")) or DEFAULT_SCOPE
    scope = scope.replace("_", "-")
    if scope not in SCOPE_REQUIRED_GATES:
        rep.add(WARN, "scope", f"unknown project.scope={project.get('scope')!r}; "
                               f"expected one of {', '.join(sorted(SCOPE_REQUIRED_GATES))}")
    else:
        required = SCOPE_REQUIRED_GATES[scope]
        outstanding = []
        for name in required:
            block = state.get(name)
            status = _norm(block.get("status")) if isinstance(block, dict) else "absent"
            if status not in _READY_STATES:
                outstanding.append(f"{name}={status}")
        if outstanding:
            rep.add(INFO, "scope", f"scope={scope}: {len(required) - len(outstanding)}/{len(required)} "
                                   f"required gate(s) satisfied; outstanding: {', '.join(outstanding)}")
        else:
            rep.add(OKAY, "scope", f"scope={scope}: all {len(required)} required gate(s) satisfied")

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


def run(workspace: Path, reconcile: bool, preconditions: str | None = None) -> Report:
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
    if preconditions is not None:
        return check_preconditions(workspace, state, preconditions)
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
            "00_meta/ai_use_disclosure.md",
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
            "ai_disclosure": {
                "status": "pass",
                "disclosure_file": "00_meta/ai_use_disclosure.md",
                "policy_family": "elsevier",
                "ledger_rows": 5,
                "disclosed_rows": 5,
                "unverified_rows": 0,
                "blocking_findings": [],
            },
            "replication_pack": {
                "status": "ready", "readme": "REPLICATION.md",
                "master_script": "run_all.sh", "last_rebuild_check": "rebuilt 2026-06-21",
            },
        })
        rep = run(good, reconcile=False)
        assert not rep.failures, f"good workspace should pass, got: {rep.failures}"

        # --- AI-use disclosure: the stage that hides the accent cannot hide the
        # --- disclosure, and no downstream gate may outrun it -----------------
        good_state = json.loads((good / "00_meta" / "workflow_state.json").read_text())

        def _ai_case(name: str, mutate) -> set[str]:
            ws = root / name
            shutil.copytree(good, ws)
            st = copy.deepcopy(good_state)
            mutate(ws, st)
            write_state(ws, st)
            return {chk for lvl, chk, _ in run(ws, reconcile=False).rows if lvl == FAIL}

        def _drop_ledger(ws, st):
            (ws / "00_meta" / "ai_use_disclosure.md").unlink()
            st["stages"]["7_language_dehumanize"] = "done"
            st["ai_disclosure"]["status"] = "pending"
        hit = _ai_case("ai_stage7_no_ledger", _drop_ledger)
        assert "ai_disclosure:stage7" in hit, hit

        def _pass_without_file(ws, st):
            (ws / "00_meta" / "ai_use_disclosure.md").unlink()
        assert "ai_disclosure" in _ai_case("ai_pass_no_file", _pass_without_file)

        def _pass_with_blocking(ws, st):
            st["ai_disclosure"]["blocking_findings"] = ["B4 stage 7 undisclosed"]
        assert "ai_disclosure:blocking" in _ai_case("ai_blocking", _pass_with_blocking)

        def _pass_empty_ledger(ws, st):
            st["ai_disclosure"]["ledger_rows"] = 0
        assert "ai_disclosure:empty" in _ai_case("ai_empty", _pass_empty_ledger)

        def _delivery_without_disclosure(ws, st):
            st["ai_disclosure"]["status"] = "not_pass"
        hit = _ai_case("ai_delivery", _delivery_without_disclosure)
        assert "replication_pack" in hit, hit

        def _ethics_ahead(ws, st):
            st["ai_disclosure"]["status"] = "not_pass"
            st["orchestration"]["ethics_gate"] = "pass"
        assert "orchestration:ethics_gate" in _ai_case("ai_ethics", _ethics_ahead)

        # a run that never declared the block at all is not penalised
        def _absent(ws, st):
            st.pop("ai_disclosure")
            st["replication_pack"]["status"] = "ready"
        assert not _ai_case("ai_absent", _absent), "absent ai_disclosure must stay backward-compatible"

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

        # --- bad workspace E: results estimated without a design lock --------
        bad_e = root / "bad_e"
        touch(bad_e, "03_analysis/results/main_results.json")
        write_state(bad_e, {
            "project": {}, "stages": {},
            "design_lock": {"status": "pending", "preregistration": "00_meta/preregistration.md"},
        })
        hit_e = {chk for lvl, chk, _ in run(bad_e, reconcile=False).rows if lvl == FAIL}
        assert "design_lock:timing" in hit_e, f"bad_e should flag design_lock:timing; got {hit_e}"

        # a lock claimed but back-dated after estimation is still a violation
        touch(bad_e, "00_meta/preregistration.md")
        write_state(bad_e, {
            "project": {}, "stages": {},
            "design_lock": {
                "status": "locked",
                "preregistration": "00_meta/preregistration.md",
                "locked_before_estimation": False,
            },
        })
        hit_e2 = {chk for lvl, chk, _ in run(bad_e, reconcile=False).rows if lvl == FAIL}
        assert "design_lock:timing" in hit_e2, f"back-dated lock must fail; got {hit_e2}"

        # --- bad workspace F: method gate passed without a design lock -------
        bad_f = root / "bad_f"
        for rel in ("02_data/sample_audit.md", "03_analysis/design_register.md",
                    "03_analysis/method_gate.md", "03_analysis/results/main_results.json"):
            touch(bad_f, rel)
        write_state(bad_f, {
            "project": {}, "stages": {},
            "empirical_audit": {"status": "pass", "sample_audit": "02_data/sample_audit.md"},
            "design_risk": {"status": "pass", "risk_ledger": "03_analysis/design_risk_ledger.md"},
            "design_lock": {"status": "pending"},
            "method_gate": {"status": "pass", "missing_artifacts": []},
        })
        hit_f = {chk for lvl, chk, _ in run(bad_f, reconcile=False).rows if lvl == FAIL}
        assert "method_gate:design_lock" in hit_f, f"bad_f should flag method_gate:design_lock; got {hit_f}"

        # --- bad workspace G: quality gate passed over unanchored numbers ----
        bad_g = root / "bad_g"
        touch(bad_g, "00_meta/quality_scorecard.md")
        write_citation_log(bad_g)
        write_state(bad_g, {
            "project": {}, "stages": {},
            "method_gate": {"status": "pass", "missing_artifacts": []},
            "manuscript_numbers": {
                "status": "pass",
                "checked_manuscript": "07_dehumanize/main.tex",
                "unanchored_claims": 3,
                "inert_boundary_drift": 1,
            },
            "quality_gate": {"status": "pass", "scorecard": "00_meta/quality_scorecard.md"},
        })
        hit_g = {chk for lvl, chk, _ in run(bad_g, reconcile=False).rows if lvl == FAIL}
        for expected in ("manuscript_numbers", "quality_gate:numbers"):
            assert expected in hit_g, f"bad_g should flag {expected}; got {hit_g}"

        # a quality gate declared before the number check ran at all
        write_state(bad_g, {
            "project": {}, "stages": {},
            "method_gate": {"status": "pass", "missing_artifacts": []},
            "manuscript_numbers": {"status": "pending"},
            "quality_gate": {"status": "pass", "scorecard": "00_meta/quality_scorecard.md"},
        })
        hit_g2 = {chk for lvl, chk, _ in run(bad_g, reconcile=False).rows if lvl == FAIL}
        assert "quality_gate:numbers" in hit_g2, f"unchecked numbers must block the gate; got {hit_g2}"

        # --- stage preconditions ---------------------------------------------
        pre = root / "pre"
        touch(pre, "01_proposal/proposal.md")
        touch(pre, "02_data/sample_audit.md")
        write_state(pre, {"project": {}, "stages": {}, "design_lock": {"status": "pending"}})
        # Stage 2.5 may start (proposal + data in hand)...
        assert not run(pre, reconcile=False, preconditions="2_5").failures, \
            "Stage 2.5 preconditions should be met"
        # ...but Stage 3 may not: nothing is locked and no design register exists.
        pre3 = {chk for lvl, chk, _ in run(pre, reconcile=False, preconditions="3").rows if lvl == FAIL}
        assert "pre:design_lock" in pre3 and "pre:00_meta/preregistration.md" in pre3, \
            f"Stage 3 must be blocked before the lock; got {pre3}"
        # once locked and registered, Stage 3 opens
        touch(pre, "00_meta/preregistration.md")
        touch(pre, "03_analysis/design_register.md")
        write_state(pre, {"project": {}, "stages": {},
                          "design_lock": {"status": "locked", "locked_before_estimation": True}})
        assert not run(pre, reconcile=False, preconditions="3").failures, \
            "Stage 3 preconditions should be met once the lock is taken"
        # an unknown stage is informational, never a failure
        assert not run(pre, reconcile=False, preconditions="42").failures

        # --- scope tiers ------------------------------------------------------
        scoped = root / "scoped"
        touch(scoped, "03_analysis/method_gate.md")
        write_citation_log(scoped)
        write_state(scoped, {
            "project": {"scope": "draft"}, "stages": {},
            "method_gate": {"status": "pass", "missing_artifacts": []},
        })
        rows = {chk: det for lvl, chk, det in run(scoped, reconcile=False).rows}
        assert "scope" in rows and "scope=draft" in rows["scope"], rows.get("scope")
        assert "all 1 required gate" in rows["scope"], f"draft scope needs only the method gate: {rows['scope']}"
        write_state(scoped, {
            "project": {"scope": "submission"}, "stages": {},
            "method_gate": {"status": "pass", "missing_artifacts": []},
        })
        rows = {chk: det for lvl, chk, det in run(scoped, reconcile=False).rows}
        assert "outstanding" in rows["scope"], f"submission scope must list outstanding gates: {rows['scope']}"

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
    parser.add_argument("--preconditions", metavar="STAGE",
                        help="check whether STAGE (e.g. 3, 2_5, 1L) may start, instead of auditing gates")
    parser.add_argument("--selftest", action="store_true", help="verify this checker on synthetic workspaces")
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    if not args.workspace:
        parser.error("workspace path is required (or pass --selftest)")

    rep = run(Path(args.workspace).expanduser().resolve(),
              reconcile=args.reconcile, preconditions=args.preconditions)
    if args.json:
        print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(rep.render())
    return 1 if rep.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
