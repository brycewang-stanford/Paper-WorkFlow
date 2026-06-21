#!/usr/bin/env python3
"""Output-integrity harness for a replication package.

Compares regenerated results against a committed ground-truth manifest, within a
numerical tolerance, and (optionally) verifies file checksums. Run it as the last
step of the master script (run_all.sh) so "the numbers match the paper" becomes a
machine-checked claim instead of a hand-wave. Non-zero exit == replication failed.

Two checks:
  1. NUMERIC: every key number in expected/manifest.json is reproduced within
     tolerance (relative, or rounded-to-reported-digits).
  2. CHECKSUM (optional): released derived files match MANIFEST.sha256.

This is a TEMPLATE: adapt paths and the `load_actual` hook to your project. It has
no third-party dependencies (stdlib only).

Manifest format (04_results/expected/manifest.json):
{
  "tolerance": {"mode": "relative", "rtol": 1e-6},
  "values": {
    "table2.att":        {"expected": -0.0431, "actual_path": "04_results/expected/actual.json", "key": "table2.att"},
    "table2.se":         {"expected":  0.0118, "actual_path": "04_results/expected/actual.json", "key": "table2.se"},
    "table2.n":          {"expected":  15240,  "actual_path": "04_results/expected/actual.json", "key": "table2.n"}
  }
}

The estimation/exhibit scripts should write the regenerated numbers to
`actual_path` (e.g. 04_results/expected/actual.json) as a flat {key: number} map.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def rel_close(expected: float, actual: float, rtol: float) -> bool:
    if expected == 0:
        return abs(actual) <= rtol
    return abs(actual - expected) / abs(expected) <= rtol


def round_close(expected: float, actual: float, digits: int) -> bool:
    return round(float(expected), digits) == round(float(actual), digits)


def get_nested(data: dict, dotted_key: str):
    cur = data
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def check_numeric(root: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    tol = manifest.get("tolerance", {"mode": "relative", "rtol": 1e-6})
    mode = tol.get("mode", "relative")
    actual_cache: dict[str, dict] = {}
    for name, spec in manifest.get("values", {}).items():
        expected = spec["expected"]
        actual_path = spec.get("actual_path")
        key = spec.get("key", name)
        if actual_path is None:
            errors.append(f"{name}: manifest entry has no actual_path")
            continue
        ap = (root / actual_path).resolve()
        if actual_path not in actual_cache:
            if not ap.exists():
                errors.append(f"{name}: actual file missing: {actual_path} (run the analysis first)")
                continue
            actual_cache[actual_path] = json.loads(ap.read_text(encoding="utf-8"))
        actual = get_nested(actual_cache[actual_path], key)
        if actual is None:
            errors.append(f"{name}: key '{key}' not found in {actual_path}")
            continue
        if mode == "relative":
            ok = rel_close(float(expected), float(actual), float(tol.get("rtol", 1e-6)))
        elif mode == "rounded":
            ok = round_close(expected, actual, int(tol.get("digits", 3)))
        else:
            errors.append(f"{name}: unknown tolerance mode '{mode}'")
            continue
        if not ok:
            errors.append(f"{name}: expected {expected}, got {actual} (mode={mode}, tol={tol})")
    return errors


def check_checksums(root: Path, sha_file: Path) -> list[str]:
    """Verify files against a `sha256sum`-style manifest (lines: '<hash>  <path>')."""
    errors: list[str] = []
    if not sha_file.exists():
        return errors  # checksum manifest is optional
    for line in sha_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            want, rel = line.split(None, 1)
        except ValueError:
            errors.append(f"malformed checksum line: {line!r}")
            continue
        target = (sha_file.parent / rel.strip()).resolve()
        if not target.exists():
            errors.append(f"checksum target missing: {rel}")
            continue
        got = hashlib.sha256(target.read_bytes()).hexdigest()
        if got != want:
            errors.append(f"checksum mismatch: {rel}\n    want {want}\n    got  {got}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify regenerated outputs against the expected manifest.")
    parser.add_argument("--root", default=".", help="package root (default: cwd)")
    parser.add_argument("--manifest", default="04_results/expected/manifest.json")
    parser.add_argument("--checksums", default="04_results/MANIFEST.sha256")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = root / args.manifest
    if not manifest_path.exists():
        print(f"FAIL: manifest not found: {args.manifest}", file=sys.stderr)
        print("      Create it from the paper's reported numbers; see computational-reproducibility.md §3.", file=sys.stderr)
        return 2

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = check_numeric(root, manifest)
    errors += check_checksums(root, root / args.checksums)

    if errors:
        print("REPRODUCTION CHECK FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    n = len(manifest.get("values", {}))
    print(f"OK: {n} expected values reproduced within tolerance; checksums verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
