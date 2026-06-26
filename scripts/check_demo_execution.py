#!/usr/bin/env python3
"""Execute the bundled DiD demo notebook in a temporary workspace.

`validate_skill.py` already checks that `did_demo.ipynb` has the expected cells
and markers. This checker goes one step further: it executes the notebook's code
cells from the committed JSON, away from the repo, and verifies the generated
assets plus the key teaching claims.

The checker intentionally does not require `jupyter-nbconvert`, `nbformat`, or
`nbclient`; it uses the notebook JSON directly so the example can be verified in
the lightweight local environment used by this repo's gates.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import warnings
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "did_demo.ipynb"


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def _close(value: float, target: float, tol: float) -> bool:
    return abs(float(value) - target) <= tol


def _execute_notebook(tmp_dir: Path) -> tuple[dict, str]:
    os.environ.setdefault("MPLBACKEND", "Agg")
    try:
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"did_demo.ipynb is not valid JSON: {exc}")

    namespace: dict = {"__name__": "__main__"}
    stdout = io.StringIO()
    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_dir)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="FigureCanvasAgg is non-interactive")
            with contextlib.redirect_stdout(stdout):
                for index, cell in enumerate(notebook.get("cells", [])):
                    if cell.get("cell_type") != "code":
                        continue
                    source = "".join(cell.get("source", []))
                    if source.strip():
                        exec(compile(source, f"did_demo.ipynb cell {index}", "exec"), namespace)
    finally:
        os.chdir(old_cwd)
    return namespace, stdout.getvalue()


def check_demo() -> None:
    with tempfile.TemporaryDirectory(prefix="paper-workflow-did-demo-") as tmp:
        tmp_dir = Path(tmp)
        namespace, output = _execute_notebook(tmp_dir)
        assets = tmp_dir / "assets"

        expected_assets = {
            "fig_raw_trends.png": 30_000,
            "fig_event_study.png": 30_000,
            "did_table.tex": 120,
        }
        for name, min_bytes in expected_assets.items():
            path = assets / name
            if not path.exists():
                fail(f"did_demo.ipynb did not generate assets/{name}")
            if path.stat().st_size < min_bytes:
                fail(f"assets/{name} is unexpectedly small: {path.stat().st_size} bytes")

        table = (assets / "did_table.tex").read_text(encoding="utf-8")
        for marker in ["Treat$\\times$Post", "1.953***", "$N$ & 2400 & 2400"]:
            if marker not in table:
                fail(f"did_table.tex missing expected marker: {marker}")

        true_att = namespace.get("TRUE_ATT")
        did_2x2 = namespace.get("did_2x2")
        twfe = namespace.get("twfe")
        ftest = namespace.get("ftest")
        twfe_stag = namespace.get("twfe_stag")
        true_avg = namespace.get("true_avg")
        if true_att != 2.0:
            fail("did_demo.ipynb did not preserve TRUE_ATT = 2.0")
        if did_2x2 is None or not _close(did_2x2, 1.953, 0.01):
            fail(f"2x2 DiD estimate drifted: {did_2x2}")
        if twfe is None or not _close(twfe.params["treat_post"], 1.953, 0.01):
            fail("TWFE estimate drifted away from the documented demo value")
        if ftest is None or float(ftest.pvalue) <= 0.10:
            fail("pre-trend joint test no longer supports the intended teaching example")
        if twfe_stag is None or true_avg is None:
            fail("staggered-adoption section did not produce comparison objects")
        if float(twfe_stag.params["d_it"] - true_avg) >= -0.5:
            fail("staggered-adoption TWFE bias example is no longer visible")
        if "TWFE 明显偏离真值" not in output:
            fail("notebook output lost the staggered-adoption caution text")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="execute the real notebook fixture")
    args = parser.parse_args(argv)

    check_demo()
    if args.selftest:
        print("selftest OK: DiD demo notebook executes and preserves teaching invariants")
    else:
        print("OK: DiD demo notebook executes and generated assets are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
