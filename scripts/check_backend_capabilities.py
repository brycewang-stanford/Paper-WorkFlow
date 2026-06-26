#!/usr/bin/env python3
"""Validate backend runtime-capability reports for Paper-WorkFlow workspaces.

The analysis backend contract has two separate questions:

1. Which backend should produce the research artifacts?
2. Which runtimes and packages were actually available on this machine?

`00_meta/backend_capabilities.json` answers the second question without making
the fast gate depend on Stata, R, or StatsPAI being installed. The checker
validates the report shape and consistency; `--probe-backend` can emit a local
best-effort report for maintainers to paste into a workspace.

Usage:
    python3 scripts/check_backend_capabilities.py path/to/workspace
    python3 scripts/check_backend_capabilities.py --selftest
    python3 scripts/check_backend_capabilities.py --probe-backend python-statspai
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path


REPORT_REL = "00_meta/backend_capabilities.json"
ALLOWED_BACKENDS = {"python-statspai", "stata", "r"}
ALLOWED_SECONDARY = ALLOWED_BACKENDS | {"none", ""}
ALLOWED_REPORT_STATUS = {"pending", "available", "fallback", "blocked"}
ALLOWED_TOOL_STATUS = {"pending", "available", "unavailable", "blocked", "not_required", "not_checked"}
REQUIRED_TOOL_FIELDS = {"id", "label", "required_for", "probe", "status", "version", "path", "notes"}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _numbered_errors(errors: list[str]) -> str:
    return "; ".join(errors[:5])


def _tool(report: dict, tool_id: str) -> dict | None:
    tools = report.get("tools")
    if not isinstance(tools, list):
        return None
    for item in tools:
        if isinstance(item, dict) and item.get("id") == tool_id:
            return item
    return None


def _required_tools(report: dict, backend: str) -> list[dict]:
    tools = report.get("tools")
    if not isinstance(tools, list):
        return []
    out: list[dict] = []
    for item in tools:
        if not isinstance(item, dict):
            continue
        required_for = item.get("required_for")
        if isinstance(required_for, list) and backend in required_for:
            out.append(item)
    return out


def evaluate_report(report: dict) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if report.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    status = report.get("status")
    if status not in ALLOWED_REPORT_STATUS:
        errors.append("status must be pending, available, fallback, or blocked")
        status = "blocked"

    selected = report.get("selected_backend")
    if status == "pending":
        if selected not in ALLOWED_BACKENDS | {""}:
            errors.append("selected_backend must be blank or a known backend while pending")
    elif selected not in ALLOWED_BACKENDS:
        errors.append(f"selected_backend must be one of {sorted(ALLOWED_BACKENDS)}")
        selected = ""

    secondary = report.get("secondary_validation")
    if secondary not in ALLOWED_SECONDARY:
        errors.append("secondary_validation must be none, blank, or a known backend")
    if secondary in ALLOWED_BACKENDS and secondary == selected:
        errors.append("secondary_validation must differ from selected_backend")

    if status != "pending" and not str(report.get("probed_at", "")).strip():
        errors.append("probed_at must be filled when status is not pending")

    tools = report.get("tools")
    if not isinstance(tools, list) or not tools:
        errors.append("tools must be a non-empty list")
        tools = []

    seen: set[str] = set()
    unavailable_for_selected = 0
    for index, item in enumerate(tools):
        if not isinstance(item, dict):
            errors.append(f"tools[{index}] must be an object")
            continue
        missing = sorted(REQUIRED_TOOL_FIELDS - set(item))
        if missing:
            errors.append(f"tools[{index}] missing field(s): {', '.join(missing)}")
            continue
        tool_id = item.get("id")
        if not isinstance(tool_id, str) or not tool_id.strip():
            errors.append(f"tools[{index}].id must be a non-empty string")
            tool_id = f"<missing-{index}>"
        if tool_id in seen:
            errors.append(f"duplicate tool id: {tool_id}")
        seen.add(tool_id)

        for field in ("label", "probe", "status", "version", "path", "notes"):
            if not isinstance(item.get(field), str):
                errors.append(f"{tool_id}.{field} must be a string")
        tool_status = item.get("status")
        if tool_status not in ALLOWED_TOOL_STATUS:
            errors.append(f"{tool_id}.status must be one of {sorted(ALLOWED_TOOL_STATUS)}")

        required_for = item.get("required_for")
        if not isinstance(required_for, list) or any(backend not in ALLOWED_BACKENDS for backend in required_for):
            errors.append(f"{tool_id}.required_for must be a list of known backends")
        elif selected and selected in required_for and tool_status in {"unavailable", "blocked"}:
            unavailable_for_selected += 1

    for required_id in ("python", "statspai", "stata", "r"):
        if required_id not in seen:
            errors.append(f"tools missing required probe entry: {required_id}")

    missing_dependencies = report.get("missing_dependencies")
    if not isinstance(missing_dependencies, list) or any(
        not isinstance(item, str) or not item.strip() for item in missing_dependencies
    ):
        errors.append("missing_dependencies must be a list of non-empty strings")
        missing_dependencies = []

    fallback_backend = report.get("fallback_backend")
    if fallback_backend not in ALLOWED_BACKENDS | {""}:
        errors.append("fallback_backend must be blank or a known backend")
    if fallback_backend and fallback_backend == selected:
        errors.append("fallback_backend must differ from selected_backend")

    if status == "pending":
        if missing_dependencies:
            errors.append("status=pending but missing_dependencies is not empty")
        if fallback_backend:
            errors.append("status=pending but fallback_backend is filled")
    elif status == "available":
        required = _required_tools(report, selected)
        if not required:
            errors.append(f"no tool is marked required_for selected backend {selected!r}")
        for item in required:
            if item.get("status") != "available":
                errors.append(f"status=available but required tool {item.get('id')} is {item.get('status')!r}")
        if missing_dependencies:
            errors.append("status=available but missing_dependencies is not empty")
        if fallback_backend:
            errors.append("status=available but fallback_backend is filled")
    elif status == "fallback":
        if not missing_dependencies:
            errors.append("status=fallback requires at least one missing dependency")
        if not fallback_backend:
            errors.append("status=fallback requires fallback_backend")
        if selected and unavailable_for_selected < 1:
            errors.append("status=fallback requires at least one unavailable/blocked selected-backend tool")
    elif status == "blocked":
        if not missing_dependencies:
            errors.append("status=blocked requires at least one missing dependency")
        if selected and unavailable_for_selected < 1:
            errors.append("status=blocked requires at least one unavailable/blocked selected-backend tool")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "status": status,
        "selected_backend": selected,
        "missing_dependency_count": len(missing_dependencies),
        "tool_count": len(tools),
    }


def evaluate_workspace(workspace: Path) -> dict:
    path = workspace / REPORT_REL
    if not path.exists():
        return {
            "ok": False,
            "errors": [f"missing {REPORT_REL}"],
            "warnings": [],
            "status": "missing",
            "selected_backend": "",
            "missing_dependency_count": 0,
            "tool_count": 0,
            "path": REPORT_REL,
        }
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "errors": [f"{REPORT_REL} is not valid JSON: {exc}"],
            "warnings": [],
            "status": "invalid",
            "selected_backend": "",
            "missing_dependency_count": 0,
            "tool_count": 0,
            "path": REPORT_REL,
        }
    result = evaluate_report(report)
    result["path"] = REPORT_REL
    return result


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow backend capability report",
        f"  path: {result.get('path', REPORT_REL)}",
        f"  status: {result['status']}",
        f"  selected backend: {result.get('selected_backend') or '(unset)'}",
        f"  tools: {result['tool_count']}",
        f"  missing dependencies: {result['missing_dependency_count']}",
    ]
    for warning in result["warnings"]:
        lines.append(f"  WARN: {warning}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  BACKEND CAPABILITIES OK" if result["ok"] else "  BACKEND CAPABILITIES FAILED")
    return "\n".join(lines)


def _base_report() -> dict:
    return {
        "schema_version": 1,
        "status": "pending",
        "selected_backend": "",
        "secondary_validation": "none",
        "probed_at": "",
        "tools": [
            {
                "id": "python",
                "label": "Python runtime",
                "required_for": ["python-statspai"],
                "probe": "python3 --version",
                "status": "pending",
                "version": "",
                "path": "",
                "notes": "",
            },
            {
                "id": "statspai",
                "label": "StatsPAI MCP or package",
                "required_for": ["python-statspai"],
                "probe": "python -c 'import statspai'",
                "status": "pending",
                "version": "",
                "path": "",
                "notes": "",
            },
            {
                "id": "stata",
                "label": "Stata executable",
                "required_for": ["stata"],
                "probe": "stata-mp -q",
                "status": "pending",
                "version": "",
                "path": "",
                "notes": "",
            },
            {
                "id": "r",
                "label": "R runtime",
                "required_for": ["r"],
                "probe": "R --version",
                "status": "pending",
                "version": "",
                "path": "",
                "notes": "",
            },
        ],
        "missing_dependencies": [],
        "fallback_backend": "",
        "notes": "",
    }


def _available_report(backend: str = "python-statspai") -> dict:
    report = _base_report()
    report["status"] = "available"
    report["selected_backend"] = backend
    report["probed_at"] = "2026-06-25 12:00"
    for item in report["tools"]:
        if backend in item["required_for"]:
            item["status"] = "available"
            item["version"] = "fixture"
            item["path"] = f"/usr/bin/{item['id']}"
        else:
            item["status"] = "not_required"
    return report


def _fallback_report() -> dict:
    report = _available_report("python-statspai")
    report["status"] = "fallback"
    report["fallback_backend"] = "r"
    report["secondary_validation"] = "r"
    report["missing_dependencies"] = ["statspai unavailable"]
    _tool(report, "statspai")["status"] = "unavailable"
    _tool(report, "statspai")["path"] = ""
    _tool(report, "r")["status"] = "available"
    _tool(report, "r")["version"] = "fixture"
    _tool(report, "r")["path"] = "/usr/bin/R"
    return report


def _blocked_report() -> dict:
    report = _available_report("stata")
    report["status"] = "blocked"
    report["missing_dependencies"] = ["stata executable unavailable"]
    _tool(report, "stata")["status"] = "blocked"
    _tool(report, "stata")["path"] = ""
    return report


def probe_report(selected_backend: str) -> dict:
    if selected_backend not in ALLOWED_BACKENDS:
        fail(f"unknown backend for probe: {selected_backend}")
    report = _base_report()
    report["selected_backend"] = selected_backend
    report["probed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    missing: list[str] = []

    python_tool = _tool(report, "python")
    python_tool["status"] = "available"
    python_tool["version"] = sys.version.split()[0]
    python_tool["path"] = sys.executable

    statspai_tool = _tool(report, "statspai")
    try:
        import statspai  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on local env
        statspai_tool["status"] = "unavailable"
        statspai_tool["notes"] = exc.__class__.__name__
    else:  # pragma: no cover - depends on local env
        statspai_tool["status"] = "available"
        statspai_tool["version"] = str(getattr(statspai, "__version__", "installed"))

    stata_tool = _tool(report, "stata")
    stata_path = next((shutil.which(cmd) for cmd in ("stata-mp", "stata-se", "stata") if shutil.which(cmd)), None)
    if stata_path:
        stata_tool["status"] = "available"
        stata_tool["path"] = stata_path
    else:
        stata_tool["status"] = "unavailable"

    r_tool = _tool(report, "r")
    r_path = shutil.which("R")
    if r_path:
        r_tool["status"] = "available"
        r_tool["path"] = r_path
    else:
        r_tool["status"] = "unavailable"

    for item in _required_tools(report, selected_backend):
        if item["status"] != "available":
            missing.append(f"{item['id']} unavailable")

    report["missing_dependencies"] = missing
    report["status"] = "available" if not missing else "blocked"
    if selected_backend == "python-statspai" and missing and r_tool["status"] == "available":
        report["status"] = "fallback"
        report["fallback_backend"] = "r"
    return report


def _selftest() -> int:
    assert evaluate_report(_base_report())["ok"], "pending template must pass"
    assert evaluate_report(_available_report())["ok"], "available selected backend must pass"
    assert evaluate_report(_fallback_report())["ok"], "fallback report with missing dependency must pass"
    assert evaluate_report(_blocked_report())["ok"], "blocked report with missing dependency must pass"

    bad = _available_report()
    _tool(bad, "python")["status"] = "unavailable"
    assert not evaluate_report(bad)["ok"], "available report with missing required runtime must fail"

    bad = _fallback_report()
    bad["missing_dependencies"] = []
    assert not evaluate_report(bad)["ok"], "fallback report without missing dependency must fail"

    bad = _blocked_report()
    _tool(bad, "stata")["status"] = "pending"
    assert not evaluate_report(bad)["ok"], "blocked report without blocked selected tool must fail"

    probe = probe_report("python-statspai")
    assert probe["selected_backend"] == "python-statspai"
    assert evaluate_report(probe)["ok"], "local probe output must satisfy report schema"

    print("selftest OK: backend capability report invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", nargs="?", help="Paper-WorkFlow run workspace to validate")
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable validation result")
    parser.add_argument(
        "--probe-backend",
        choices=sorted(ALLOWED_BACKENDS),
        help="emit a best-effort local capability report for the selected backend",
    )
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.probe_backend:
        print(json.dumps(probe_report(args.probe_backend), indent=2))
        return 0

    if not args.workspace:
        parser.error("workspace is required unless --selftest or --probe-backend is used")

    result = evaluate_workspace(Path(args.workspace))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
