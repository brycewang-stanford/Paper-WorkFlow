#!/usr/bin/env python3
"""Validate runtime-fallback honesty for a Paper-WorkFlow workspace.

`references/runtime-fallbacks.md` says missing tools, networks, MCP services, or
statistical backends must be disclosed rather than treated as verified success.
This checker enforces the decidable part of that rule:

- a fallback must be recorded in `workflow_state.json.decisions`,
  `00_meta/analysis_backend.md`, and a `logs/stage_<N>.md` runtime-fallback block;
- a blocked backend cannot coexist with a passing Method Gate or ready
  replication pack;
- artifact parity must be explicit before a fallback path can pass Method Gate.

Usage:
    python3 scripts/check_runtime_fallbacks.py <workspace_dir>
    python3 scripts/check_runtime_fallbacks.py <workspace_dir> --json
    python3 scripts/check_runtime_fallbacks.py --selftest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

import check_backend_parity


STATE_REL = "00_meta/workflow_state.json"
ANALYSIS_REL = "00_meta/analysis_backend.md"
BACKEND_PARITY_REL = "00_meta/backend_parity.json"
METHOD_REL = "03_analysis/method_gate.md"
REPLICATION_REL = "REPLICATION.md"
FALLBACK_BLOCK_RE = re.compile(r"^## Runtime fallback\b", re.IGNORECASE | re.MULTILINE)
FALLBACK_WORD_RE = re.compile(
    r"fallback|blocked|unavailable|not available|missing dependency|"
    r"缺失|不可用|退化|回退|阻断",
    re.IGNORECASE,
)
OK_PARITY_VALUES = {"yes", "equivalent", "passed", "pass", "same-artifacts", "same_artifacts"}
PASS_VALUES = {"pass", "passed"}
READY_VALUES = {"ready", "pass", "passed"}
FILLED_NEGATIVES = {
    "",
    "-",
    "no",
    "none",
    "n/a",
    "na",
    "pending",
    "not needed",
    "not used",
    "no / yes, describe",
    "yes / no",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _norm(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _load_state(workspace: Path) -> tuple[dict, list[str]]:
    path = workspace / STATE_REL
    if not path.exists():
        return {}, [f"missing {STATE_REL}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{STATE_REL} is not valid JSON: {exc}"]
    if not isinstance(data, dict):
        return {}, [f"{STATE_REL} must contain an object"]
    return data, []


def _line_value(text: str, label: str) -> str:
    pattern = re.compile(rf"^[ \t]*[-*]?[ \t]*{re.escape(label)}[ \t]*:[ \t]*(.*)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def _filled(value: str) -> bool:
    cleaned = value.strip().strip("`")
    if cleaned.startswith("<") and cleaned.endswith(">"):
        return False
    return cleaned.lower() not in FILLED_NEGATIVES


def _has_fallback_decision(state: dict) -> bool:
    decisions = state.get("decisions")
    if not isinstance(decisions, list):
        return False
    blob = json.dumps(decisions, ensure_ascii=False)
    return bool(FALLBACK_WORD_RE.search(blob))


def _log_files(workspace: Path) -> list[Path]:
    logs = workspace / "logs"
    if not logs.is_dir():
        return []
    return sorted(logs.glob("stage_*.md"))


def _log_has_fallback(workspace: Path) -> bool:
    return any(FALLBACK_BLOCK_RE.search(_read(path)) for path in _log_files(workspace))


def _has_fallback_signal(
    state: dict,
    analysis_text: str,
    method_text: str,
    replication_text: str,
    log_has_fallback: bool,
) -> tuple[bool, list[str]]:
    signals: list[str] = []
    analysis = state.get("analysis_backend", {}) if isinstance(state.get("analysis_backend"), dict) else {}
    environment_status = _norm(analysis.get("environment_status"))
    if environment_status in {"fallback", "blocked"}:
        signals.append(f"analysis_backend.environment_status={environment_status}")
    if _has_fallback_decision(state):
        signals.append("workflow_state.json.decisions mentions fallback")
    if log_has_fallback:
        signals.append("logs/stage_<N>.md has Runtime fallback block")

    for label, text in [
        ("analysis_backend.md Missing dependency", _line_value(analysis_text, "Missing dependency")),
        ("analysis_backend.md Fallback backend", _line_value(analysis_text, "Fallback backend")),
        ("analysis_backend.md Gate impact", _line_value(analysis_text, "Gate impact")),
        ("method_gate.md Runtime fallback used", _line_value(method_text, "Runtime fallback used")),
        ("REPLICATION.md Runtime fallback used", _line_value(replication_text, "Runtime fallback used")),
    ]:
        if _filled(text):
            signals.append(label)

    return bool(signals), signals


def evaluate_workspace(workspace: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    state, state_errors = _load_state(workspace)
    errors.extend(state_errors)
    if state_errors:
        return {
            "ok": False,
            "errors": errors,
            "warnings": warnings,
            "fallback_detected": False,
            "signals": [],
        }

    analysis = state.get("analysis_backend", {}) if isinstance(state.get("analysis_backend"), dict) else {}
    method = state.get("method_gate", {}) if isinstance(state.get("method_gate"), dict) else {}
    quality = state.get("quality_gate", {}) if isinstance(state.get("quality_gate"), dict) else {}
    replication = state.get("replication_pack", {}) if isinstance(state.get("replication_pack"), dict) else {}

    analysis_text = _read(workspace / ANALYSIS_REL)
    method_text = _read(workspace / METHOD_REL)
    replication_text = _read(workspace / REPLICATION_REL)
    log_has_fallback = _log_has_fallback(workspace)

    fallback_detected, signals = _has_fallback_signal(
        state,
        analysis_text,
        method_text,
        replication_text,
        log_has_fallback,
    )

    if not fallback_detected:
        return {
            "ok": True,
            "errors": errors,
            "warnings": warnings,
            "fallback_detected": False,
            "signals": [],
        }

    environment_status = _norm(analysis.get("environment_status"))
    method_status = _norm(method.get("status"))
    quality_status = _norm(quality.get("status"))
    replication_status = _norm(replication.get("status"))
    missing_dependency = _line_value(analysis_text, "Missing dependency")
    fallback_backend = _line_value(analysis_text, "Fallback backend")
    parity_value = _line_value(analysis_text, "Artifact parity checked")
    gate_impact = _line_value(analysis_text, "Gate impact")
    method_flag = _line_value(method_text, "Runtime fallback used")
    replication_fallback = _line_value(replication_text, "Runtime fallback used")
    parity_norm = _norm(parity_value)

    if environment_status not in {"fallback", "blocked"}:
        errors.append(
            "fallback evidence exists but analysis_backend.environment_status "
            f"is {analysis.get('environment_status', 'missing')!r}, not fallback/blocked"
        )

    if not analysis_text:
        errors.append(f"fallback detected but missing {ANALYSIS_REL}")
    else:
        for label, value in [
            ("Missing dependency", missing_dependency),
            ("Fallback backend", fallback_backend),
            ("Artifact parity checked", parity_value),
            ("Gate impact", gate_impact),
        ]:
            if not _filled(value):
                errors.append(f"{ANALYSIS_REL}: fallback field is not filled: {label}")

    if not _has_fallback_decision(state):
        errors.append("fallback detected but workflow_state.json.decisions has no fallback decision")

    if not log_has_fallback:
        errors.append("fallback detected but no logs/stage_<N>.md contains a Runtime fallback block")

    if method_status in {"pass", "passed", "not_pass", "fail", "failed"} and not _filled(method_flag):
        errors.append(f"{METHOD_REL}: Method Gate decision exists but Runtime fallback used is not filled")

    if environment_status == "blocked":
        if method_status in PASS_VALUES:
            errors.append("analysis backend is blocked but method_gate.status is pass")
        if quality_status in PASS_VALUES:
            errors.append("analysis backend is blocked but quality_gate.status is pass")
        if replication_status in READY_VALUES:
            errors.append("analysis backend is blocked but replication_pack.status is ready/pass")

    if parity_norm not in OK_PARITY_VALUES and method_status in PASS_VALUES:
        errors.append(
            "method_gate.status is pass but fallback artifact parity is not explicitly checked as yes/equivalent"
        )

    if parity_norm not in OK_PARITY_VALUES and replication_status in READY_VALUES:
        errors.append(
            "replication_pack.status is ready/pass but fallback artifact parity is not explicitly checked as yes/equivalent"
        )

    if parity_norm in OK_PARITY_VALUES and (method_status in PASS_VALUES or replication_status in READY_VALUES):
        parity_result = check_backend_parity.evaluate_workspace(workspace)
        if not parity_result["ok"]:
            errors.append(
                f"{BACKEND_PARITY_REL}: artifact parity is claimed but report is invalid: "
                + "; ".join(parity_result["errors"][:3])
            )
        elif parity_result["status"] != "pass":
            errors.append(
                f"{BACKEND_PARITY_REL}: artifact parity is claimed but report status is "
                f"{parity_result['status']!r}, not 'pass'"
            )

    if replication_status in READY_VALUES and not _filled(replication_fallback):
        errors.append(f"{REPLICATION_REL}: ready replication pack must disclose Runtime fallback used")

    if not _filled(method_flag) and method_status in {"pending", ""}:
        warnings.append("fallback detected before Method Gate; method_gate.md should record it before audit")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "fallback_detected": True,
        "signals": signals,
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow runtime fallback contract",
        f"  fallback detected: {'yes' if result['fallback_detected'] else 'no'}",
        f"  signals: {len(result['signals'])}",
    ]
    for signal in result["signals"]:
        lines.append(f"  signal: {signal}")
    for warning in result["warnings"]:
        lines.append(f"  WARN: {warning}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  RUNTIME FALLBACKS OK" if result["ok"] else "  RUNTIME FALLBACKS FAILED")
    return "\n".join(lines)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _state(*, environment_status: str = "pending", method_status: str = "pending", quality_status: str = "pending", replication_status: str = "pending", decision: bool = False) -> dict:
    decisions = []
    if decision:
        decisions.append(
            {
                "stage": 3,
                "decision": "StatsPAI MCP unavailable; used R/fixest fallback with identical artifacts",
                "at": "2026-06-25 12:00",
            }
        )
    return {
        "analysis_backend": {
            "environment_status": environment_status,
            "version_report": ANALYSIS_REL,
        },
        "method_gate": {
            "status": method_status,
            "method_gate_report": METHOD_REL,
        },
        "quality_gate": {
            "status": quality_status,
        },
        "replication_pack": {
            "status": replication_status,
            "readme": REPLICATION_REL,
        },
        "decisions": decisions,
    }


def _write_workspace(
    root: Path,
    *,
    environment_status: str = "pending",
    method_status: str = "pending",
    quality_status: str = "pending",
    replication_status: str = "pending",
    decision: bool = False,
    analysis: bool = False,
    log: bool = False,
    parity: str = "yes",
    method_flag: str | None = None,
    replication_flag: str | None = None,
) -> None:
    fallback_flag = environment_status in {"fallback", "blocked"}
    if method_flag is None:
        method_flag = "yes - StatsPAI MCP unavailable; R/fixest fallback used" if fallback_flag else "no"
    if replication_flag is None:
        replication_flag = "yes - fallback route documented with artifact parity" if fallback_flag else "no"
    _write(
        root / STATE_REL,
        json.dumps(
            _state(
                environment_status=environment_status,
                method_status=method_status,
                quality_status=quality_status,
                replication_status=replication_status,
                decision=decision,
            ),
            indent=2,
        ),
    )
    if analysis:
        _write(
            root / ANALYSIS_REL,
            f"""# Analysis Backend

## 4. Fallback

- Missing dependency: StatsPAI MCP unavailable
- Fallback backend: R/fixest with modelsummary
- Artifact parity checked: {parity}
- Gate impact: method evidence retained with equivalent artifacts
""",
        )
    _write(
        root / METHOD_REL,
        f"""# Method Gate

## 4. Hard Flags

- Runtime fallback used: {method_flag}

## 5. Decision

Decision: {method_status.upper() if method_status else "PENDING"}
""",
    )
    _write(
        root / REPLICATION_REL,
        f"""# Replication Package README

## 7. Known Limits

- Runtime fallback used: {replication_flag}
""",
    )
    if log:
        _write(
            root / "logs" / "stage_3.md",
            """# Stage 3 log

## Runtime fallback — 2026-06-25 12:00 Beijing

- Missing dependency: StatsPAI MCP unavailable
- Tried: MCP route
- Fallback used: R/fixest with equivalent artifacts
- Analysis backend before / after: python-statspai / r
- Output files affected: 03_analysis/results/main_results.json
- Research claim affected: no
- Gate impact: no downgrade after parity check
- Follow-up before submission: keep version report
""",
        )
    if fallback_flag:
        _write(
            root / BACKEND_PARITY_REL,
            json.dumps(check_backend_parity._good_report(), indent=2) + "\n",
        )
    else:
        _write(
            root / BACKEND_PARITY_REL,
            json.dumps(check_backend_parity._pending_report(), indent=2) + "\n",
        )


def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="runtime-fallback-selftest-") as tmp:
        root = Path(tmp)

        no_fallback = root / "no_fallback"
        _write_workspace(no_fallback)
        assert evaluate_workspace(no_fallback)["ok"], "workspace without fallback should pass"

        good = root / "good"
        _write_workspace(
            good,
            environment_status="fallback",
            method_status="pass",
            replication_status="ready",
            decision=True,
            analysis=True,
            log=True,
        )
        assert evaluate_workspace(good)["ok"], "complete fallback evidence should pass"

        missing_log = root / "missing_log"
        _write_workspace(
            missing_log,
            environment_status="fallback",
            method_status="pass",
            decision=True,
            analysis=True,
            log=False,
        )
        assert not evaluate_workspace(missing_log)["ok"], "fallback without stage log must fail"

        blocked_pass = root / "blocked_pass"
        _write_workspace(
            blocked_pass,
            environment_status="blocked",
            method_status="pass",
            decision=True,
            analysis=True,
            log=True,
        )
        assert not evaluate_workspace(blocked_pass)["ok"], "blocked backend with pass Method Gate must fail"

        no_parity = root / "no_parity"
        _write_workspace(
            no_parity,
            environment_status="fallback",
            method_status="pass",
            decision=True,
            analysis=True,
            log=True,
            parity="no",
        )
        assert not evaluate_workspace(no_parity)["ok"], "Method Gate pass without parity must fail"

        pending_report = root / "pending_report"
        _write_workspace(
            pending_report,
            environment_status="fallback",
            method_status="pass",
            decision=True,
            analysis=True,
            log=True,
        )
        _write(
            pending_report / BACKEND_PARITY_REL,
            json.dumps(check_backend_parity._pending_report(), indent=2) + "\n",
        )
        assert not evaluate_workspace(pending_report)["ok"], (
            "claimed parity with a pending backend_parity.json report must fail"
        )

        no_decision = root / "no_decision"
        _write_workspace(
            no_decision,
            environment_status="fallback",
            method_status="not_pass",
            decision=False,
            analysis=True,
            log=True,
        )
        assert not evaluate_workspace(no_decision)["ok"], "fallback without state decision must fail"

    print("selftest OK: runtime fallback honesty invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="?", help="Paper-WorkFlow run workspace")
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.workspace:
        parser.error("workspace is required unless --selftest is used")

    result = evaluate_workspace(Path(args.workspace))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
