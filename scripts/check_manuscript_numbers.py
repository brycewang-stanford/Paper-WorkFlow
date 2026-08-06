#!/usr/bin/env python3
"""Manuscript <-> results numeric-anchor and drift gate for a Paper-WorkFlow run.

Why this exists
---------------
Two of the most damaging failure modes in an agent-run empirical paper are both
numeric, and neither was mechanically covered before this checker:

  1. **Unanchored numbers.** A coefficient, standard error, sample size or effect
     magnitude appears in the manuscript prose that exists nowhere in the analysis
     output. Whether it came from a hallucination, a stale draft, or a spec that
     was re-run and never propagated, the reader cannot tell -- and neither can
     the evidence ledger, which is prose a critic self-grades.

  2. **Rewrite drift.** Stage 7 (de-AIGC) rewrites every sentence in the paper.
     Its own red line, stated in references/stage-playbook.md, is that numbers,
     coefficients, standard errors, p-values and sample sizes are *never touched*.
     A single digit silently changed during a 200-paragraph rewrite is invisible
     to a human reviewer and fatal to the paper.

`check_workspace_gates.py --reconcile` checks the *opposite* direction of (1):
whether result numbers made it into the exhibits. It is advisory and it never
opens the manuscript. This checker closes the loop that actually protects the
reader: every number the manuscript asserts must trace back to analysis output,
and the rewrite stages must be numerically inert.

What counts as authoritative
----------------------------
The number index is built from analysis output the run actually produced:
``03_analysis/results/*.json`` (and nested dirs) plus the exported exhibits in
``04_results/*.{tex,md,csv}``. Anything in there is "anchored"; the manuscript may
assert it. Matching is precision-aware: a manuscript figure of ``0.123`` matches
an index value of ``0.12345`` because the manuscript displays three decimals.

What is deliberately not flagged
--------------------------------
Prose is full of numbers that are not empirical claims: years, section and table
cross-references, LaTeX lengths, conventional significance levels and critical
values. These are excluded structurally (see EXCLUDE_* below) rather than by
raising the pass threshold, so the check stays strict where it matters.

The one deliberate blind spot: a bare integer below 1000 with no thousands
separator ("column 3", "Panel 2", but also "N = 842") is treated as structural.
Cross-references vastly outnumber sub-1000 magnitudes in prose, and a checker
that cries wolf on every "Table 4" gets switched off. Sample sizes written with a
separator (12,345) and every decimal figure are checked.

An unanchored number that is nonetheless correct (a figure quoted from a cited
paper, an institutional constant) is waived *in the manuscript itself*:

    % pw-number-ok: 4.7 -- 2019 unemployment rate, quoted from Chen (2021) Table 2

That keeps the waiver next to the claim, versioned with the paper, and readable
by a referee -- the same discipline the runtime-fallback and design-risk ledgers
use for every other degradation in this skill.

Usage:
    python3 check_manuscript_numbers.py <workspace>            # human report
    python3 check_manuscript_numbers.py <workspace> --json     # machine readable
    python3 check_manuscript_numbers.py <workspace> --strict   # WARN tiers become FAIL
    python3 check_manuscript_numbers.py --selftest             # verify this checker

Exit code is non-zero iff a HARD violation is found: an unanchored numeric claim,
or numeric drift across a rewrite boundary that is contractually inert.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

FAIL = "FAIL"
WARN = "WARN"
INFO = "INFO"
OKAY = "OK"

# Manuscript chain, earliest to latest. Stage 6 copies Stage 5, Stage 7 rewrites
# Stage 6, Stage 9 typesets Stage 8's revision: consecutive pairs are comparable.
MANUSCRIPT_CHAIN = [
    ("05_draft", "05_draft/main.tex"),
    ("06_polish", "06_polish/main.tex"),
    ("07_dehumanize", "07_dehumanize/main.tex"),
    ("08_review", "08_review/main.tex"),
    ("09_submission", "09_submission/main.tex"),
]

# Boundaries whose contract is "language may change, numbers may not". Any numeric
# delta across one of these is a hard violation, in either direction.
INERT_BOUNDARIES = {("06_polish", "07_dehumanize"), ("05_draft", "07_dehumanize")}

RESULTS_DIR = "03_analysis/results"
EXHIBIT_DIR = "04_results"
EXHIBIT_SUFFIXES = (".tex", ".md", ".csv")

# Conventional statistical furniture: not empirical claims about this paper.
EXCLUDE_CONSTANTS = {
    0.01, 0.05, 0.10, 0.1,          # significance levels
    1.0, 2.0, 3.0, 5.0, 10.0, 100.0,  # ordinals / percent bases
    1.96, 2.576, 2.58, 1.645,       # normal critical values
    90.0, 95.0, 99.0,               # confidence levels
}
YEAR_MIN, YEAR_MAX = 1800, 2100

# LaTeX constructs whose numeric payload is structural, not empirical.
_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)
_WAIVER_RE = re.compile(r"(?<!\\)%\s*pw-number-ok:\s*(-?[\d.,]+)", re.MULTILINE)
_STRIP_PATTERNS = [
    re.compile(r"\\(?:cite|citep|citet|citeauthor|citeyear|ref|eqref|autoref|pageref|label|input|include|includegraphics|usepackage|documentclass|bibliography|bibliographystyle|hspace|vspace|setlength|geometry|color|definecolor)\s*(?:\[[^\]]*\])?\s*(?:\{[^{}]*\})*", re.DOTALL),
    re.compile(r"\\begin\{(?:tabular|tabularx|longtable|table|figure|thebibliography)\}.*?\\end\{(?:tabular|tabularx|longtable|table|figure|thebibliography)\}", re.DOTALL),
    re.compile(r"\d+(?:\.\d+)?\s*(?:pt|em|ex|cm|mm|in|bp|sp|\\textwidth|\\linewidth|\\columnwidth|\\textheight)"),
]
_PREAMBLE_RE = re.compile(r"^.*?\\begin\{document\}", re.DOTALL)

# A numeric token, optionally signed, with optional thousands separators.
_NUMBER_RE = re.compile(r"(?<![\w.])(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?)(?![\w])")


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, level: str, check: str, detail: str) -> None:
        self.rows.append((level, check, detail))

    @property
    def failures(self) -> list[tuple[str, str, str]]:
        return [r for r in self.rows if r[0] == FAIL]

    def to_dict(self) -> dict:
        return {
            "ok": not self.failures,
            "checks": [{"level": lvl, "check": chk, "detail": det} for lvl, chk, det in self.rows],
        }

    def render(self) -> str:
        width = max((len(c) for _, c, _ in self.rows), default=4)
        lines = ["", "Paper-WorkFlow manuscript number gate", "=" * 64]
        for lvl, chk, det in self.rows:
            lines.append(f"[{lvl:<4}] {chk:<{width}}  {det}")
        lines.append("=" * 64)
        if self.failures:
            lines.append(
                f"RESULT: {len(self.failures)} hard violation(s) -> manuscript numbers NOT verified"
            )
        else:
            lines.append("RESULT: every manuscript number traces to analysis output")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# extraction                                                                   #
# --------------------------------------------------------------------------- #
def _to_float(token: str) -> float | None:
    try:
        return float(token.replace(",", ""))
    except ValueError:
        return None


def _decimals(token: str) -> int:
    """Displayed decimal places, which sets the precision the claim commits to."""
    body = token.replace(",", "")
    return len(body.split(".", 1)[1]) if "." in body else 0


def _is_structural(token: str, value: float) -> bool:
    """True when a numeric token is prose furniture rather than an empirical claim."""
    if abs(value) in EXCLUDE_CONSTANTS:
        return True
    if _decimals(token) == 0:
        ivalue = int(abs(value))
        if YEAR_MIN <= ivalue <= YEAR_MAX:      # sample periods, publication years
            return True
        if "," not in token and ivalue < 1000:  # section/table refs, small counts
            return True
    return False


def strip_latex(text: str) -> str:
    """Remove preamble, comments and constructs whose numbers are structural."""
    m = _PREAMBLE_RE.search(text)
    if m:
        text = text[m.end():]
    text = _COMMENT_RE.sub("", text)
    for pat in _STRIP_PATTERNS:
        text = pat.sub(" ", text)
    return text


def extract_claims(text: str) -> list[tuple[str, float, int]]:
    """Numeric claims in manuscript prose as (token, value, decimals)."""
    body = strip_latex(text)
    out: list[tuple[str, float, int]] = []
    for m in _NUMBER_RE.finditer(body):
        token = m.group(1)
        value = _to_float(token)
        if value is None or _is_structural(token, value):
            continue
        out.append((token, value, _decimals(token)))
    return out


def extract_waivers(text: str) -> set[float]:
    """Values explicitly waived by a `% pw-number-ok: <n> -- reason` comment."""
    out: set[float] = set()
    for m in _WAIVER_RE.finditer(text):
        value = _to_float(m.group(1))
        if value is not None:
            out.add(abs(value))
    return out


def _walk_json(obj: object, out: list[float]) -> None:
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, str):
        for m in _NUMBER_RE.finditer(obj):
            v = _to_float(m.group(1))
            if v is not None:
                out.append(v)
    elif isinstance(obj, dict):
        for v in obj.values():
            _walk_json(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk_json(v, out)


def build_index(workspace: Path) -> tuple[set[float], list[str]]:
    """Authoritative numbers produced by the analysis, plus the sources scanned."""
    values: list[float] = []
    sources: list[str] = []

    results_dir = workspace / RESULTS_DIR
    if results_dir.is_dir():
        for path in sorted(results_dir.rglob("*.json")):
            try:
                _walk_json(json.loads(path.read_text(encoding="utf-8")), values)
            except (OSError, json.JSONDecodeError):
                continue
            sources.append(str(path.relative_to(workspace)))

    exhibit_dir = workspace / EXHIBIT_DIR
    if exhibit_dir.is_dir():
        for path in sorted(exhibit_dir.rglob("*")):
            if path.suffix.lower() not in EXHIBIT_SUFFIXES or not path.is_file():
                continue
            try:
                blob = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in _NUMBER_RE.finditer(blob):
                v = _to_float(m.group(1))
                if v is not None:
                    values.append(v)
            sources.append(str(path.relative_to(workspace)))

    return {abs(v) for v in values}, sources


def is_anchored(value: float, decimals: int, index: set[float]) -> bool:
    """A claim is anchored if some index value agrees at the precision displayed.

    The manuscript commits only to the digits it prints: `0.123` is satisfied by an
    index value of 0.12345, and `12,345` by 12345.0. Rounding both sides to the
    displayed precision makes the comparison symmetric and free of epsilon fudging.
    """
    target = abs(value)
    if target in index:
        return True
    scale = round(target, decimals)
    for candidate in index:
        if round(candidate, decimals) == scale:
            return True
    return False


# --------------------------------------------------------------------------- #
# checks                                                                       #
# --------------------------------------------------------------------------- #
def _present_manuscripts(workspace: Path) -> list[tuple[str, Path]]:
    return [(name, workspace / rel) for name, rel in MANUSCRIPT_CHAIN if (workspace / rel).is_file()]


def check_anchors(workspace: Path, index: set[float], rep: Report, strict: bool) -> None:
    stages = _present_manuscripts(workspace)
    if not stages:
        rep.add(INFO, "anchors", "no manuscript in the chain yet — nothing to anchor")
        return
    if not index:
        rep.add(
            FAIL if strict else WARN,
            "anchors:index",
            f"a manuscript exists but no analysis output found under {RESULTS_DIR}/ or "
            f"{EXHIBIT_DIR}/ — nothing can be anchored"
            + ("" if strict else " (advisory until --strict; Stage 9 runs strict)"),
        )
        return

    name, path = stages[-1]          # the live manuscript is the last one produced
    text = path.read_text(encoding="utf-8", errors="ignore")
    waived = extract_waivers(text)
    claims = extract_claims(text)
    unanchored: list[str] = []
    seen: set[float] = set()
    for token, value, decimals in claims:
        key = abs(value)
        if key in seen or key in waived:
            continue
        if not is_anchored(value, decimals, index):
            seen.add(key)
            unanchored.append(token)

    rel = str(path.relative_to(workspace))
    if not unanchored:
        rep.add(
            OKAY,
            "anchors",
            f"{rel}: all {len(claims)} numeric claim(s) trace to analysis output"
            + (f"; {len(waived)} waived in-text" if waived else ""),
        )
        return
    shown = ", ".join(unanchored[:8]) + (" …" if len(unanchored) > 8 else "")
    rep.add(
        FAIL,
        "anchors",
        f"{rel}: {len(unanchored)} number(s) asserted with no match in {RESULTS_DIR}/ or "
        f"{EXHIBIT_DIR}/: {shown} (fix the number, re-export the result, or waive it "
        f"in-text with `% pw-number-ok: <n> -- reason`)",
    )


def check_drift(workspace: Path, index: set[float], rep: Report) -> None:
    stages = _present_manuscripts(workspace)
    if len(stages) < 2:
        rep.add(INFO, "drift", "fewer than two manuscript versions — no boundary to compare")
        return

    for (prev_name, prev_path), (name, path) in zip(stages, stages[1:]):
        prev_vals = {abs(v) for _, v, _ in extract_claims(
            prev_path.read_text(encoding="utf-8", errors="ignore"))}
        text = path.read_text(encoding="utf-8", errors="ignore")
        waived = extract_waivers(text)
        cur_vals = {abs(v) for _, v, _ in extract_claims(text)}

        added = sorted(cur_vals - prev_vals - waived)
        removed = sorted(prev_vals - cur_vals)
        boundary = f"{prev_name} -> {name}"

        if (prev_name, name) in INERT_BOUNDARIES:
            # A waiver excuses a number from needing analysis output behind it. It
            # does not license *introducing* a number during a rewrite that is
            # contractually language-only, so waivers are not subtracted here.
            delta = sorted(cur_vals - prev_vals) + removed
            if delta:
                rep.add(
                    FAIL,
                    "drift:inert",
                    f"{boundary} must be numerically inert (language-only rewrite) but "
                    f"{len(added)} number(s) appeared and {len(removed)} disappeared: "
                    + ", ".join(f"{v:g}" for v in delta[:8])
                    + (" …" if len(delta) > 8 else ""),
                )
            else:
                rep.add(OKAY, "drift:inert", f"{boundary}: numerically inert ({len(cur_vals)} value(s) preserved)")
            continue

        unanchored_new = [v for v in added if not is_anchored(v, 3, index)] if index else []
        if unanchored_new:
            rep.add(
                FAIL,
                "drift:new",
                f"{boundary}: {len(unanchored_new)} number(s) appeared that no analysis "
                "output backs: " + ", ".join(f"{v:g}" for v in unanchored_new[:8]),
            )
        elif added:
            rep.add(INFO, "drift:new", f"{boundary}: {len(added)} new number(s), all anchored in results")
        else:
            rep.add(OKAY, "drift:new", f"{boundary}: no unbacked numbers introduced")
        if removed:
            rep.add(INFO, "drift:removed", f"{boundary}: {len(removed)} number(s) no longer cited (content cut)")


def run(workspace: Path, strict: bool = False) -> Report:
    rep = Report()
    if not workspace.is_dir():
        rep.add(FAIL, "workspace", f"workspace not found: {workspace}")
        return rep

    index, sources = build_index(workspace)
    if sources:
        rep.add(INFO, "index", f"{len(index)} distinct value(s) from {len(sources)} analysis artifact(s)")
    else:
        rep.add(INFO, "index", f"no analysis artifacts under {RESULTS_DIR}/ or {EXHIBIT_DIR}/")

    check_anchors(workspace, index, rep, strict)
    check_drift(workspace, index, rep)
    return rep


# --------------------------------------------------------------------------- #
# selftest                                                                     #
# --------------------------------------------------------------------------- #
_RESULTS = {
    "baseline": {"coef": 0.12345, "se": 0.0412, "n": 12345, "pvalue": 0.0031},
    "robust": {"coef": 0.118, "se": 0.045},
}

_DRAFT = r"""
\documentclass{article}
\begin{document}
\section{Results}
The treatment raises log wages by 0.123 (s.e. 0.041), significant at the 1\% level.
The estimation sample contains 12,345 firm-year observations over 2010--2020.
Dropping the largest province leaves the coefficient at 0.118.
See Table 3 and Figure 2 for details, and \cite{chen2021} for background.
\hspace{0.8\textwidth}
\end{document}
"""


def _selftest() -> int:
    # --- extraction discipline ------------------------------------------------
    claims = extract_claims(_DRAFT)
    vals = {round(v, 5) for _, v, _ in claims}
    assert 0.123 in vals and 0.041 in vals and 12345.0 in vals and 0.118 in vals, vals
    for excluded in (2010.0, 2020.0, 3.0, 2.0, 1.0, 0.8):
        assert excluded not in vals, f"structural number {excluded} leaked into claims: {vals}"

    # --- precision-aware anchoring -------------------------------------------
    idx = {0.12345, 0.0412, 12345.0, 0.118}
    assert is_anchored(0.123, 3, idx), "displayed precision must satisfy a longer index value"
    assert is_anchored(0.041, 3, idx)
    assert not is_anchored(0.999, 3, idx)

    with tempfile.TemporaryDirectory(prefix="mnum-selftest-") as tmp:
        root = Path(tmp)

        def make(ws: str, files: dict[str, str]) -> Path:
            base = root / ws
            for rel, content in files.items():
                p = base / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
            return base

        results_json = json.dumps(_RESULTS)

        # --- clean workspace: every number anchored ---------------------------
        good = make("good", {
            f"{RESULTS_DIR}/main_results.json": results_json,
            "05_draft/main.tex": _DRAFT,
        })
        rep = run(good)
        assert not rep.failures, f"clean workspace should pass: {rep.failures}"

        # --- a fabricated coefficient -----------------------------------------
        bad = make("bad", {
            f"{RESULTS_DIR}/main_results.json": results_json,
            "05_draft/main.tex": _DRAFT.replace("0.123 (s.e. 0.041)", "0.876 (s.e. 0.041)"),
        })
        hits = {chk for lvl, chk, _ in run(bad).rows if lvl == FAIL}
        assert "anchors" in hits, f"fabricated number must fail; got {hits}"

        # --- the same number, waived in-text ----------------------------------
        waived = make("waived", {
            f"{RESULTS_DIR}/main_results.json": results_json,
            "05_draft/main.tex": _DRAFT.replace(
                "\\section{Results}",
                "% pw-number-ok: 0.876 -- 2019 sector average, quoted from Chen (2021) Table 2\n\\section{Results}",
            ).replace("0.123 (s.e. 0.041)", "0.876 (s.e. 0.041)"),
        })
        assert not run(waived).failures, "an in-text waiver must clear the anchor failure"

        # --- Stage 7 rewrite that silently changes a digit --------------------
        drifted = make("drifted", {
            f"{RESULTS_DIR}/main_results.json": results_json,
            "06_polish/main.tex": _DRAFT,
            "07_dehumanize/main.tex": _DRAFT.replace("12,345 firm-year", "12,845 firm-year"),
        })
        rows = run(drifted).rows
        hits = {chk for lvl, chk, _ in rows if lvl == FAIL}
        assert "drift:inert" in hits, f"de-AIGC drift must fail; got {hits}"

        # --- a faithful Stage 7 rewrite (wording changes, numbers do not) -----
        faithful = make("faithful", {
            f"{RESULTS_DIR}/main_results.json": results_json,
            "06_polish/main.tex": _DRAFT,
            "07_dehumanize/main.tex": _DRAFT.replace(
                "The treatment raises log wages by", "Wages rise by"),
        })
        assert not run(faithful).failures, "language-only rewrite must pass the inert boundary"

        # --- a waiver must not launder drift across an inert boundary ---------
        laundered = make("laundered", {
            f"{RESULTS_DIR}/main_results.json": results_json,
            "06_polish/main.tex": _DRAFT,
            "07_dehumanize/main.tex": _DRAFT.replace(
                "\\section{Results}",
                "% pw-number-ok: 7.77 -- sector average\n\\section{Results}",
            ).replace("at 0.118.", "at 0.118, against a sector average of 7.77."),
        })
        hits = {chk for lvl, chk, _ in run(laundered).rows if lvl == FAIL}
        assert "drift:inert" in hits, (
            f"a waiver must not excuse introducing a number during a language-only rewrite; got {hits}")

        # --- Stage 8 revision may add numbers, but only backed ones -----------
        revised = make("revised", {
            f"{RESULTS_DIR}/main_results.json": results_json,
            "07_dehumanize/main.tex": _DRAFT,
            "08_review/main.tex": _DRAFT.replace(
                "\\end{document}", "A referee asked for the p-value: 0.0031.\n\\end{document}"),
        })
        assert not run(revised).failures, "a revision citing a real result value must pass"

        invented = make("invented", {
            f"{RESULTS_DIR}/main_results.json": results_json,
            "07_dehumanize/main.tex": _DRAFT,
            "08_review/main.tex": _DRAFT.replace(
                "\\end{document}", "Robustness to trimming gives 0.771.\n\\end{document}"),
        })
        hits = {chk for lvl, chk, _ in run(invented).rows if lvl == FAIL}
        assert "drift:new" in hits, f"an invented revision number must fail; got {hits}"

        # --- an unfinished run is not a violation -----------------------------
        early = make("early", {f"{RESULTS_DIR}/main_results.json": results_json})
        assert not run(early).failures, "a run with no manuscript yet must not fail"

        # --- a manuscript with no analysis output: advisory, hard under --strict
        no_results = make("no_results", {"05_draft/main.tex": _DRAFT})
        assert not run(no_results).failures, "missing analysis output is advisory by default"
        strict_hits = {chk for lvl, chk, _ in run(no_results, strict=True).rows if lvl == FAIL}
        assert "anchors:index" in strict_hits, f"--strict must harden the index check; got {strict_hits}"

        # --- missing workspace ------------------------------------------------
        assert run(root / "nope").failures, "missing workspace must fail"

    print("selftest OK: manuscript number gate invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("workspace", nargs="?", help="path to the paper_workspace/<run> directory")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p.add_argument("--strict", action="store_true", help="treat advisory tiers as hard failures")
    p.add_argument("--selftest", action="store_true", help="verify this checker on synthetic workspaces")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.workspace:
        p.error("workspace path is required (or pass --selftest)")

    rep = run(Path(args.workspace).expanduser().resolve(), strict=args.strict)
    if args.json:
        print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(rep.render())
    return 1 if rep.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
