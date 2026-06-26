#!/usr/bin/env python3
"""Validate that the public RIGOR registry covers every checker on disk.

`generate_rigor_report.py` is the public trust surface for this package. This
checker makes its registry coverage a normal validation invariant: every
`check_*`, `score_*`, or `validate_*` checker under `scripts/` or `evals/` must
be registered, every registry entry must point to a real file, and registry
drift must be treated as blocking rather than advisory.

Usage:
    python3 scripts/check_rigor_registry.py
    python3 scripts/check_rigor_registry.py --selftest
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_DIRS = ("scripts", "evals")
DISCOVERY_PREFIXES = ("check_", "score_", "validate_")
EXCLUDED_DISCOVERED_PATHS = {
    "scripts/generate_rigor_report.py",
    "validate_skill.py",
}
MIN_ENFORCES_CHARS = 40


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root))


def discover_checker_paths(root: Path) -> set[str]:
    discovered: set[str] = set()
    for folder in DISCOVERY_DIRS:
        base = root / folder
        if not base.exists():
            continue
        for path in base.glob("*.py"):
            if path.name == "__init__.py":
                continue
            if path.name.startswith(DISCOVERY_PREFIXES):
                discovered.add(_rel(path, root))
    return discovered - EXCLUDED_DISCOVERED_PATHS


def load_rigor_module(root: Path) -> ModuleType:
    module_path = root / "scripts" / "generate_rigor_report.py"
    if not module_path.exists():
        fail("scripts/generate_rigor_report.py is missing")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("paper_workflow_generate_rigor_report", module_path)
    if spec is None or spec.loader is None:
        fail("cannot import scripts/generate_rigor_report.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def evaluate_registry(root: Path, registry: list[dict], *, generator_drift: list[str] | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    discovered = discover_checker_paths(root)
    registered: list[str] = []

    for index, entry in enumerate(registry):
        if not isinstance(entry, dict):
            errors.append(f"registry entry {index} is not an object")
            continue
        raw_path = entry.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            errors.append(f"registry entry {index} missing non-empty path")
            continue
        registered.append(raw_path)
        if not (root / raw_path).is_file():
            errors.append(f"registered checker path does not exist: {raw_path}")

        argv = entry.get("argv")
        if not isinstance(argv, list):
            errors.append(f"{raw_path}: argv must be a list")

        enforces = entry.get("enforces")
        if not isinstance(enforces, str) or len(enforces.strip()) < MIN_ENFORCES_CHARS:
            errors.append(f"{raw_path}: enforces text is missing or too thin")

        layer = entry.get("layer")
        if not isinstance(layer, str) or not layer:
            errors.append(f"{raw_path}: layer is missing")

    duplicates = sorted({path for path in registered if registered.count(path) > 1})
    for path in duplicates:
        errors.append(f"duplicate registry entry: {path}")

    registered_set = set(registered)
    unregistered = sorted(discovered - registered_set)
    for path in unregistered:
        errors.append(f"checker exists on disk but is absent from RIGOR registry: {path}")

    if generator_drift is not None and sorted(generator_drift) != unregistered:
        errors.append(
            "generate_rigor_report._drift() disagrees with checker discovery: "
            f"generator={sorted(generator_drift)} expected={unregistered}"
        )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "registered_count": len(registered_set),
        "discovered_count": len(discovered),
        "unregistered": unregistered,
    }


def render(result: dict) -> str:
    lines = [
        "Paper-WorkFlow RIGOR registry",
        f"  registered entries: {result['registered_count']}",
        f"  discovered checkers: {result['discovered_count']}",
        f"  unregistered checkers: {len(result['unregistered'])}",
    ]
    for warning in result["warnings"]:
        lines.append(f"  WARN: {warning}")
    for error in result["errors"]:
        lines.append(f"  FAIL: {error}")
    lines.append("  RIGOR REGISTRY OK" if result["ok"] else "  RIGOR REGISTRY FAILED")
    return "\n".join(lines)


def _write(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="rigor-registry-selftest-") as tmp:
        root = Path(tmp)
        for rel in [
            "scripts/check_alpha.py",
            "scripts/check_rigor_registry.py",
            "scripts/smoke_workspace.py",
            "evals/check_beta.py",
            "evals/score_gamma.py",
        ]:
            _write(root / rel)

        good_registry = [
            {
                "path": "scripts/check_alpha.py",
                "argv": ["--selftest"],
                "layer": "maintenance",
                "enforces": "Alpha checker enforces a substantive invariant for testing.",
            },
            {
                "path": "scripts/check_rigor_registry.py",
                "argv": ["--selftest"],
                "layer": "maintenance",
                "enforces": "RIGOR registry coverage must not drift away from disk.",
            },
            {
                "path": "scripts/smoke_workspace.py",
                "argv": [],
                "layer": "runtime",
                "enforces": "Smoke workspace checker may be registered even when not auto-discovered.",
            },
            {
                "path": "evals/check_beta.py",
                "argv": ["--selftest"],
                "layer": "maintenance",
                "enforces": "Beta eval checker enforces a substantive invariant for testing.",
            },
            {
                "path": "evals/score_gamma.py",
                "argv": ["--selftest"],
                "layer": "maintenance",
                "enforces": "Scoring eval checker enforces a substantive invariant for testing.",
            },
        ]
        assert evaluate_registry(root, good_registry)["ok"], "complete registry must pass"

        missing = [entry for entry in good_registry if entry["path"] != "evals/score_gamma.py"]
        assert not evaluate_registry(root, missing)["ok"], "unregistered discovered checker must fail"

        duplicate = good_registry + [good_registry[0]]
        assert not evaluate_registry(root, duplicate)["ok"], "duplicate registry path must fail"

        bad_path = [dict(good_registry[0], path="scripts/missing.py"), *good_registry[1:]]
        assert not evaluate_registry(root, bad_path)["ok"], "missing registered file must fail"

        thin = [dict(good_registry[0], enforces="thin"), *good_registry[1:]]
        assert not evaluate_registry(root, thin)["ok"], "thin enforces text must fail"

    module = load_rigor_module(ROOT)
    report_ok = getattr(module, "_report_ok", None)
    assert callable(report_ok), "generate_rigor_report must expose _report_ok"
    assert report_ok([{"status": "PASS"}], []) is True, "green selftests without drift should pass"
    assert report_ok([{"status": "PASS"}], ["scripts/check_missing.py"]) is False, (
        "registry drift must be blocking"
    )

    print("selftest OK: RIGOR registry coverage invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run synthetic checker selftest")
    parser.add_argument("--json", action="store_true", help="emit machine-readable result")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    module = load_rigor_module(ROOT)
    registry = getattr(module, "REGISTRY", None)
    if not isinstance(registry, list):
        fail("generate_rigor_report.REGISTRY must be a list")
    drift = module._drift() if hasattr(module, "_drift") else None
    result = evaluate_registry(ROOT, registry, generator_drift=drift)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
