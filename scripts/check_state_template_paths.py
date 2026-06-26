#!/usr/bin/env python3
"""Validate workflow-state template paths against the init workspace skeleton.

`assets/workflow_state.template.json` is the resume contract for every generated
paper workspace. A path in that template can drift in two ways that ordinary
schema checks miss:

- the path points outside the workspace or into a directory the init skeleton
  never creates;
- a Stage 0 bootstrap artifact is listed in the state contract but the real
  `init_workspace.sh` run does not create it.

This checker keeps those contracts mechanical. It reads the state template,
parses the directory skeleton from `assets/init_workspace.sh`, runs the real init
script in a temp directory, and verifies that all path-like defaults are safe
workspace-relative paths whose parent directories exist. Stage-produced files
may be absent at setup time, but their parent directory must exist. Bootstrap
files must already exist immediately after init.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
STATE_TEMPLATE = ROOT / "assets" / "workflow_state.template.json"
INIT_SCRIPT = ROOT / "assets" / "init_workspace.sh"

PATH_VALUE_RE = re.compile(r"(^|/)[A-Za-z0-9_.-]+(?:\.(?:md|json|sh|do|py|R|qmd)|$)")
BOOTSTRAP_FILES = {
    "00_meta/workflow_state.json",
    "00_meta/intake.md",
    "00_meta/entry_routing.md",
    "00_meta/stage_passport.md",
    "00_meta/pipeline_status.md",
    "00_meta/handoff_prompt.md",
    "00_meta/analysis_backend.md",
    "00_meta/backend_parity.json",
    "00_meta/evidence_ledger.md",
    "00_meta/claim_integrity_audit.md",
    "00_meta/citation_integrity_log.md",
    "00_meta/data_governance.md",
    "00_meta/handoff/HANDOFF_TEMPLATE.md",
    "03_analysis/design_risk_ledger.md",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_state(path: Path = STATE_TEMPLATE) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def skeleton_dirs(init_script: Path = INIT_SCRIPT) -> set[str]:
    text = init_script.read_text(encoding="utf-8")
    match = re.search(r'mkdir\s+-p\s+"\$workspace"/\{([^}]*)\}', text)
    if not match:
        fail("init_workspace.sh does not contain the expected mkdir -p skeleton")
    dirs = {"."}
    for entry in match.group(1).split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("/")
        for index in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:index]))
    return dirs


def _walk_strings(value, prefix: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else key
            yield from _walk_strings(child, next_prefix)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_strings(child, f"{prefix}[{index}]")
    elif isinstance(value, str):
        yield prefix, value


def _looks_like_workspace_path(value: str) -> bool:
    if not value or " " in value or "://" in value:
        return False
    base = value.split("#", 1)[0]
    if not base or base.startswith(("/", "../", "./")):
        return False
    if "/" not in base and not base.endswith((".md", ".json", ".sh", ".do", ".py", ".R", ".qmd")):
        return False
    return bool(PATH_VALUE_RE.search(base))


def path_defaults(state: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for key, value in _walk_strings(state):
        if _looks_like_workspace_path(value):
            out.append((key, value.split("#", 1)[0]))
    return out


def evaluate(root: Path = ROOT) -> dict:
    state = load_state(root / "assets" / "workflow_state.template.json")
    dirs = skeleton_dirs(root / "assets" / "init_workspace.sh")
    errors: list[str] = []
    checked: list[tuple[str, str]] = []

    for key, rel in path_defaults(state):
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"{key}: unsafe workspace path: {rel}")
            continue
        parent = str(path.parent) if str(path.parent) != "." else "."
        if parent not in dirs:
            errors.append(f"{key}: parent directory is not in init skeleton: {parent} for {rel}")
            continue
        checked.append((key, rel))

    with tempfile.TemporaryDirectory(prefix="paper-workflow-state-paths-") as tmp:
        workspace = Path(tmp) / "workspace"
        subprocess.run(["bash", str(root / "assets" / "init_workspace.sh"), str(workspace)], check=True)
        for rel in sorted(BOOTSTRAP_FILES):
            target = workspace / rel
            if not target.exists():
                errors.append(f"bootstrap artifact missing after init: {rel}")
            elif target.is_file() and target.stat().st_size == 0:
                errors.append(f"bootstrap artifact is empty after init: {rel}")
        copied = json.loads((workspace / "00_meta" / "workflow_state.json").read_text(encoding="utf-8"))
        if copied != state:
            errors.append("init_workspace.sh did not copy workflow_state.template.json byte-for-meaningfully")

    return {
        "ok": not errors,
        "errors": errors,
        "checked_state_paths": checked,
        "bootstrap_files": sorted(BOOTSTRAP_FILES),
        "skeleton_dir_count": len(dirs),
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow state-template path contract",
        f"  state path defaults checked: {len(result['checked_state_paths'])}",
        f"  bootstrap files checked: {len(result['bootstrap_files'])}",
        f"  init skeleton dirs parsed: {result['skeleton_dir_count']}",
    ]
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  STATE PATHS OK" if result["ok"] else "  STATE PATHS FAILED")
    return "\n".join(lines)


def _selftest() -> int:
    good = {
        "orchestration": {"entry_routing": "00_meta/entry_routing.md"},
        "replication_pack": {"readme": "REPLICATION.md"},
    }
    found = dict(path_defaults(good))
    assert found["orchestration.entry_routing"] == "00_meta/entry_routing.md"
    assert found["replication_pack.readme"] == "REPLICATION.md"

    bad = {"x": "../escape.md", "y": "/absolute.md", "z": "https://example.com/a.md"}
    assert not path_defaults(bad), "unsafe or URL strings must not be treated as valid defaults"
    result = evaluate(ROOT)
    assert result["ok"], "live workflow-state path contract must pass"
    print("selftest OK: workflow-state path invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    result = evaluate(ROOT)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
