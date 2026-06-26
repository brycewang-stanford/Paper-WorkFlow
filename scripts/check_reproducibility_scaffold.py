#!/usr/bin/env python3
"""Exercise the replication-package scaffold.

`templates/run_all.sh` and `templates/check_outputs.py` are meant to work as a
pair: the master script captures the environment, rebuilds outputs, and, when an
expected manifest exists, calls the output checker so the paper numbers are
machine-verified. Syntax checks alone do not prove that contract.

This checker copies the real templates into a temporary package and verifies:

- no manifest -> run_all succeeds but logs that output integrity is unverified;
- matching manifest + actual values -> run_all succeeds and check_outputs passes;
- corrupted actual values -> run_all fails through the output-integrity branch.

It does not run project-specific empirical code; it only validates the reusable
replication scaffold shipped by this skill.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _copy_scaffold(workspace: Path) -> None:
    (workspace / "templates").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "templates" / "run_all.sh", workspace / "run_all.sh")
    shutil.copy2(ROOT / "templates" / "check_outputs.py", workspace / "templates" / "check_outputs.py")
    (workspace / "run_all.sh").chmod(0o755)


def _run(workspace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "run_all.sh"],
        cwd=workspace,
        text=True,
        capture_output=True,
        timeout=120,
    )


def _latest_log(workspace: Path) -> str:
    logs = sorted((workspace / "logs").glob("run_all_*.log"))
    if not logs:
        fail("run_all.sh did not create a logs/run_all_*.log file")
    return logs[-1].read_text(encoding="utf-8")


def _write_manifest(workspace: Path, actual_att: float = 0.123) -> None:
    expected = workspace / "04_results" / "expected"
    expected.mkdir(parents=True, exist_ok=True)
    (expected / "actual.json").write_text(
        json.dumps({"table2": {"att": actual_att, "se": 0.045, "n": 5000}}, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "tolerance": {"mode": "relative", "rtol": 1e-9},
        "values": {
            "table2.att": {
                "expected": 0.123,
                "actual_path": "04_results/expected/actual.json",
                "key": "table2.att",
            },
            "table2.se": {
                "expected": 0.045,
                "actual_path": "04_results/expected/actual.json",
                "key": "table2.se",
            },
            "table2.n": {
                "expected": 5000,
                "actual_path": "04_results/expected/actual.json",
                "key": "table2.n",
            },
        },
    }
    (expected / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def check_scaffold(workspace: Path) -> None:
    _copy_scaffold(workspace)

    no_manifest = _run(workspace)
    if no_manifest.returncode != 0:
        fail(f"run_all.sh failed without a manifest:\n{no_manifest.stdout}\n{no_manifest.stderr}")
    if not (workspace / "00_meta" / "env_capture.txt").exists():
        fail("run_all.sh did not create 00_meta/env_capture.txt")
    if "output integrity not verified" not in _latest_log(workspace):
        fail("run_all.sh without manifest did not log the required integrity warning")

    _write_manifest(workspace, actual_att=0.123)
    matching = _run(workspace)
    if matching.returncode != 0:
        fail(f"run_all.sh failed with a matching manifest:\n{matching.stdout}\n{matching.stderr}")
    if "OK: 3 expected values reproduced" not in matching.stdout:
        fail("run_all.sh did not surface check_outputs.py success for the matching manifest")

    _write_manifest(workspace, actual_att=0.999)
    corrupted = _run(workspace)
    if corrupted.returncode == 0:
        fail("run_all.sh passed even though the manifest actual values were corrupted")
    if "OUTPUT CHECK FAILED" not in _latest_log(workspace):
        fail("run_all.sh did not log OUTPUT CHECK FAILED after check_outputs.py failed")


def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="paper-workflow-repro-selftest-") as tmp:
        check_scaffold(Path(tmp) / "package")
    print("selftest OK: reproducibility scaffold catches manifest success and failure paths")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run the scaffold selftest")
    parser.add_argument("--keep", action="store_true", help="keep and print the temporary package path")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    if args.keep:
        tmp = Path(tempfile.mkdtemp(prefix="paper-workflow-repro-"))
        workspace = tmp / "package"
        check_scaffold(workspace)
        print(workspace)
        return 0

    with tempfile.TemporaryDirectory(prefix="paper-workflow-repro-") as tmp:
        check_scaffold(Path(tmp) / "package")
    print("OK: reproducibility scaffold passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
