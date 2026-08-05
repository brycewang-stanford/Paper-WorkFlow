#!/usr/bin/env python3
"""Verify that a paper workspace's exported tables really are three-line tables.

Why this exists
---------------
`scripts/make_three_line_tables.py` *writes* the 三线表 rule structure into a
.docx. This checker is the read-only counterpart: it re-derives, from the shipped
artifacts alone, whether the tables a reviewer will actually open conform to the
economics/management house style. Writer and verifier are deliberately separate
programs -- a gate that only checks "did our own writer run?" proves nothing
about a table the agent produced through Stata `putdocx`, R `flextable`, or a
hand edit in Word after the fact.

What conformance means here
---------------------------
    ══════  top rule       heavy, first row
    ──────  header rule    light, last header row
    ══════  bottom rule    heavy, last row
    no vertical rules anywhere; no interior horizontal rules except one light
    rule above a `Panel X` / `面板X` head; no cell shading.

The LaTeX side is checked too, because Stage 4 ships `.tex`, `.docx` and `.xlsx`
of the same table and a booktabs-free `.tex` would silently reintroduce the grid
at compile time: `\\toprule` / `\\midrule` / `\\bottomrule`, no `\\hline`, no `|`
in the column spec.

Borders must be *explicit*. A table that inherits its rules from a Word table
style (`Table Grid` and friends) is reported as unverifiable rather than
guessed at -- running the normaliser makes it deterministic.

Scope control
-------------
The gate reads `00_meta/workflow_state.json` -> `table_style`. When
`format` is anything other than `three-line` the project has opted out and the
checker passes with a recorded note; `--require` forces the check regardless.
Stage-4-and-later artifacts that do not exist yet are simply not findings.

Usage:
    python3 scripts/check_table_style.py <workspace>
    python3 scripts/check_table_style.py <workspace> --json
    python3 scripts/check_table_style.py <workspace> --require
    python3 scripts/check_table_style.py --selftest
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

FAIL = "FAIL"
WARN = "WARN"
OKAY = "OK"
SKIP = "SKIP"

# Border weights written by scripts/make_three_line_tables.py, in eighths of a
# point. The checker accepts a range rather than the exact values so a journal
# template with slightly different rule weights still passes.
HEAVY_MIN_EIGHTHS = 8   # >= 1.0pt reads as a heavy (top/bottom) rule
LIGHT_MAX_EIGHTHS = 8   # <= 1.0pt reads as a light (header/panel) rule

DRAWN = {"single", "double", "thick", "dashed", "dotted", "wave"}
BLANK = {"", "nil", "none"}

DOCX_GLOBS = (
    "04_results/*.docx",
    "05_draft/*.docx",
    "06_polish/*.docx",
    "07_dehumanize/*.docx",
    "08_review/*.docx",
    "09_submission/*.docx",
)
TEX_GLOBS = (
    "04_results/*.tex",
    "05_draft/*.tex",
    "09_submission/*.tex",
)

_PANEL_PREFIXES = (
    "panel ", "panel:", "part ", "面板", "组别", "第一部分", "第二部分",
    "第三部分", "第四部分", "a. ", "b. ", "c. ",
)

# Table style names known to paint a full grid. Explicit borders override them,
# so these only matter when a table ships no `w:tblBorders` of its own.
_GRID_STYLE_HINT = re.compile(r"grid|网格|table\s*grid", re.IGNORECASE)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def w(tag: str) -> str:
    return f"{{{W}}}{tag}"


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


class Report:
    """Ordered finding list; FAIL rows decide the exit code."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str]] = []

    def add(self, level: str, check: str, detail: str) -> None:
        self.rows.append((level, check, detail))

    @property
    def failures(self) -> list[tuple[str, str, str]]:
        return [row for row in self.rows if row[0] == FAIL]

    @property
    def warnings(self) -> list[tuple[str, str, str]]:
        return [row for row in self.rows if row[0] == WARN]

    def to_dict(self) -> dict:
        return {
            "ok": not self.failures,
            "failures": len(self.failures),
            "warnings": len(self.warnings),
            "checks": [
                {"level": level, "check": check, "detail": detail}
                for level, check, detail in self.rows
            ],
        }

    def render(self) -> str:
        width = max((len(check) for _, check, _ in self.rows), default=4)
        lines = ["", "Paper-WorkFlow table style (三线表) gate", "=" * 68]
        for level, check, detail in self.rows:
            lines.append(f"[{level:<4}] {check:<{width}}  {detail}")
        lines.append("=" * 68)
        if self.failures:
            lines.append(
                f"RESULT: {len(self.failures)} violation(s) -> tables are NOT three-line. "
                "Fix with: python3 scripts/make_three_line_tables.py --workspace <ws>"
            )
        else:
            lines.append("RESULT: exported tables conform to the three-line table contract")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# OOXML border model                                                           #
# --------------------------------------------------------------------------- #
def _child_elements(node: ET.Element, name: str, stop_at: str) -> list[ET.Element]:
    found: list[ET.Element] = []

    def walk(current: ET.Element) -> None:
        for kid in current:
            tag = localname(kid.tag)
            if tag == name:
                found.append(kid)
            elif tag != stop_at:
                walk(kid)

    walk(node)
    return found


def _border(node: ET.Element | None, edge: str) -> tuple[str, int] | None:
    """(val, size-in-eighths) for one edge, or None when the edge is unset."""
    if node is None:
        return None
    found = node.find(w(edge))
    if found is None:
        return None
    val = (found.get(w("val")) or "").strip().lower()
    try:
        size = int(found.get(w("sz")) or 0)
    except ValueError:
        size = 0
    return val, size


def _is_drawn(spec: tuple[str, int] | None) -> bool:
    return spec is not None and spec[0] in DRAWN and spec[1] > 0


def _cell_text(cell: ET.Element) -> str:
    return "".join(node.text or "" for node in cell.iter(w("t"))).strip()


def _is_panel_head(text: str) -> bool:
    lowered = text.strip().lower()
    return bool(lowered) and any(lowered.startswith(p) for p in _PANEL_PREFIXES)


def _effective(cell_spec: tuple[str, int] | None,
               table_spec: tuple[str, int] | None) -> tuple[str, int] | None:
    """Cell-level direct formatting wins; otherwise the table-level edge applies."""
    return cell_spec if cell_spec is not None else table_spec


def analyse_table(tbl: ET.Element, index: int, source: str) -> list[tuple[str, str, str]]:
    """Findings for one `w:tbl`. Pure: no I/O, so the selftest can drive it."""
    label = f"{source}#table{index + 1}"
    findings: list[tuple[str, str, str]] = []

    rows = _child_elements(tbl, "tr", stop_at="tbl")
    if not rows:
        return [(WARN, "docx:empty", f"{label}: table has no rows")]

    tblpr = tbl.find(w("tblPr"))
    tbl_borders = tblpr.find(w("tblBorders")) if tblpr is not None else None
    style = tblpr.find(w("tblStyle")) if tblpr is not None else None
    style_name = style.get(w("val")) if style is not None else ""

    if tbl_borders is None:
        cells_with_borders = any(
            cell.find(w("tcPr")) is not None
            and cell.find(w("tcPr")).find(w("tcBorders")) is not None
            for row in rows
            for cell in _child_elements(row, "tc", stop_at="tbl")
        )
        if not cells_with_borders:
            hint = f" (table style {style_name!r})" if style_name else ""
            level = FAIL if (not style_name or _GRID_STYLE_HINT.search(style_name)) else WARN
            findings.append((
                level, "docx:implicit-borders",
                f"{label}: rules are inherited from a table style{hint}, not written "
                f"explicitly -- unverifiable; run make_three_line_tables.py",
            ))
            return findings

    # Vertical rules are never part of a three-line table.
    for edge in ("left", "right", "insideV"):
        if _is_drawn(_border(tbl_borders, edge)):
            findings.append((
                FAIL, "docx:vertical-rule",
                f"{label}: table-level {edge} border is drawn; three-line tables have no vertical rules",
            ))
    if _is_drawn(_border(tbl_borders, "insideH")):
        findings.append((
            FAIL, "docx:interior-rule",
            f"{label}: table-level insideH border is drawn; interior horizontal rules are not allowed",
        ))

    last = len(rows) - 1
    header_rows = 0
    for row in rows:
        trpr = row.find(w("trPr"))
        if trpr is not None and trpr.find(w("tblHeader")) is not None:
            header_rows += 1
        else:
            break
    if header_rows == 0 or header_rows > last:
        header_rows = 1 if last >= 1 else 0

    top_seen = bottom_seen = header_seen = False
    for row_index, row in enumerate(rows):
        cells = _child_elements(row, "tc", stop_at="tbl")
        if not cells:
            continue
        panel = row_index > header_rows and _is_panel_head(_cell_text(cells[0]))
        for cell in cells:
            tcpr = cell.find(w("tcPr"))
            tc_borders = tcpr.find(w("tcBorders")) if tcpr is not None else None

            for edge in ("left", "right", "insideV"):
                if _is_drawn(_border(tc_borders, edge)):
                    findings.append((
                        FAIL, "docx:vertical-rule",
                        f"{label}: row {row_index + 1} has a {edge} cell border drawn",
                    ))
                    break

            top = _effective(_border(tc_borders, "top"), _border(tbl_borders, "top")
                             if row_index == 0 else None)
            bottom = _effective(_border(tc_borders, "bottom"), _border(tbl_borders, "bottom")
                                if row_index == last else None)

            if row_index == 0 and _is_drawn(top):
                top_seen = True
                if top[1] < HEAVY_MIN_EIGHTHS:
                    findings.append((
                        WARN, "docx:rule-weight",
                        f"{label}: top rule is {top[1] / 8:.2f}pt; econ journals print >= 1pt",
                    ))
            if row_index == last and _is_drawn(bottom):
                bottom_seen = True
                if bottom[1] < HEAVY_MIN_EIGHTHS:
                    findings.append((
                        WARN, "docx:rule-weight",
                        f"{label}: bottom rule is {bottom[1] / 8:.2f}pt; econ journals print >= 1pt",
                    ))
            if header_rows and row_index == header_rows - 1 and _is_drawn(bottom):
                header_seen = True
                if bottom[1] > LIGHT_MAX_EIGHTHS:
                    findings.append((
                        WARN, "docx:rule-weight",
                        f"{label}: header rule is {bottom[1] / 8:.2f}pt; it must read lighter "
                        "than the top and bottom rules",
                    ))

            # Interior rules: only a panel head may carry one.
            if 0 < row_index <= last and not panel and _is_drawn(_border(tc_borders, "top")) \
                    and row_index != 0:
                findings.append((
                    FAIL, "docx:interior-rule",
                    f"{label}: row {row_index + 1} draws a top rule but is not a Panel/面板 head",
                ))
            if row_index != last and not (header_rows and row_index == header_rows - 1) \
                    and _is_drawn(_border(tc_borders, "bottom")):
                findings.append((
                    FAIL, "docx:interior-rule",
                    f"{label}: row {row_index + 1} draws a bottom rule; only the header rule "
                    "and the closing rule are allowed",
                ))

            shading = tcpr.find(w("shd")) if tcpr is not None else None
            if shading is not None:
                fill = (shading.get(w("fill")) or "").upper()
                if fill not in {"", "AUTO", "FFFFFF"}:
                    findings.append((
                        WARN, "docx:shading",
                        f"{label}: row {row_index + 1} is shaded (fill {fill}); "
                        "econ journals print unshaded tables",
                    ))

    if not top_seen:
        findings.append((FAIL, "docx:missing-rule", f"{label}: no top rule on the first row"))
    if not bottom_seen:
        findings.append((FAIL, "docx:missing-rule", f"{label}: no bottom rule on the last row"))
    if header_rows and not header_seen:
        findings.append((
            FAIL, "docx:missing-rule",
            f"{label}: no header rule under row {header_rows} (the column-head rule)",
        ))

    # Collapse duplicates so a 40-cell row reports one finding, not forty.
    seen: set[tuple[str, str, str]] = set()
    unique = []
    for finding in findings:
        if finding not in seen:
            seen.add(finding)
            unique.append(finding)
    return unique


def analyse_docx(path: Path, root: Path) -> list[tuple[str, str, str]]:
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    try:
        with zipfile.ZipFile(path) as archive:
            if "word/document.xml" not in archive.namelist():
                return [(FAIL, "docx:container", f"{rel}: no word/document.xml")]
            payload = archive.read("word/document.xml")
    except (zipfile.BadZipFile, OSError) as exc:
        return [(FAIL, "docx:container", f"{rel}: unreadable .docx ({exc})")]
    try:
        document = ET.fromstring(payload)
    except ET.ParseError as exc:
        return [(FAIL, "docx:xml", f"{rel}: malformed document.xml ({exc})")]

    tables = list(document.iter(w("tbl")))
    if not tables:
        return [(OKAY, "docx:tables", f"{rel}: no tables")]
    findings: list[tuple[str, str, str]] = []
    for index, tbl in enumerate(tables):
        findings.extend(analyse_table(tbl, index, rel))
    if not any(level == FAIL for level, _, _ in findings):
        findings.append((OKAY, "docx:tables", f"{rel}: {len(tables)} table(s) conform"))
    return findings


# --------------------------------------------------------------------------- #
# LaTeX side                                                                   #
# --------------------------------------------------------------------------- #
_TEX_COMMENT_RE = re.compile(r"(?<!\\)%.*")
_TEX_ENV_RE = re.compile(
    r"\\begin\{(?P<env>tabular\*?|tabularx|tabulary|longtable|supertabular)\}"
    r"(?:\s*\[[^\]]*\])?(?:\s*\{[^{}]*\})?\s*\{(?P<spec>[^{}]*)\}"
    r"(?P<body>.*?)"
    r"\\end\{(?P=env)\}",
    re.DOTALL,
)


def analyse_tex(path: Path, root: Path) -> list[tuple[str, str, str]]:
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [(FAIL, "tex:read", f"{rel}: unreadable ({exc})")]
    text = _TEX_COMMENT_RE.sub("", text)

    findings: list[tuple[str, str, str]] = []
    environments = list(_TEX_ENV_RE.finditer(text))
    if not environments:
        return [(OKAY, "tex:tables", f"{rel}: no tabular environments")]

    for index, match in enumerate(environments):
        label = f"{rel}#tabular{index + 1}"
        spec = match.group("spec")
        body = match.group("body")
        if "|" in spec:
            findings.append((
                FAIL, "tex:vertical-rule",
                f"{label}: column spec {spec.strip()!r} contains '|'; three-line tables "
                "have no vertical rules",
            ))
        if "\\vline" in body:
            findings.append((FAIL, "tex:vertical-rule", f"{label}: uses \\vline"))
        if "\\hline" in body:
            findings.append((
                FAIL, "tex:hline",
                f"{label}: uses \\hline; use booktabs \\toprule/\\midrule/\\bottomrule",
            ))
        if "\\cline" in body:
            findings.append((
                FAIL, "tex:cline",
                f"{label}: uses \\cline; use booktabs \\cmidrule for a spanning rule",
            ))
        if "\\toprule" not in body:
            findings.append((FAIL, "tex:missing-rule", f"{label}: no \\toprule"))
        if "\\bottomrule" not in body:
            findings.append((FAIL, "tex:missing-rule", f"{label}: no \\bottomrule"))
        if "\\midrule" not in body:
            findings.append((
                WARN, "tex:missing-rule",
                f"{label}: no \\midrule; the column heads carry no header rule",
            ))
    if not any(level == FAIL for level, _, _ in findings):
        findings.append((OKAY, "tex:tables", f"{rel}: {len(environments)} tabular(s) conform"))
    return findings


# --------------------------------------------------------------------------- #
# workspace driver                                                             #
# --------------------------------------------------------------------------- #
def read_table_style(workspace: Path) -> dict:
    state_path = workspace / "00_meta" / "workflow_state.json"
    if not state_path.is_file():
        return {}
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    block = state.get("table_style")
    return block if isinstance(block, dict) else {}


def collect(workspace: Path, globs: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for pattern in globs:
        found.extend(sorted(workspace.glob(pattern)))
    return [path for path in found if not path.name.startswith("~$")]


def evaluate(workspace: Path, *, require: bool = False) -> Report:
    report = Report()
    style = read_table_style(workspace)
    fmt = str(style.get("format") or "").strip().lower()

    if not require and style and fmt and fmt != "three-line":
        report.add(SKIP, "scope", f"table_style.format={fmt!r} -- three-line gate not requested")
        return report
    if not require and not style:
        report.add(
            WARN, "scope",
            "workflow_state.json has no table_style block; checking anyway with the "
            "three-line default (set table_style.format at Stage 0 to make this explicit)",
        )

    docx_files = collect(workspace, DOCX_GLOBS)
    tex_files = collect(workspace, TEX_GLOBS)
    if not docx_files and not tex_files:
        report.add(SKIP, "artifacts", "no .docx or .tex table artifacts yet (pre-Stage 4)")
        return report

    for path in docx_files:
        for level, check, detail in analyse_docx(path, workspace):
            report.add(level, check, detail)
    for path in tex_files:
        for level, check, detail in analyse_tex(path, workspace):
            report.add(level, check, detail)
    return report


# --------------------------------------------------------------------------- #
# selftest fixtures                                                            #
# --------------------------------------------------------------------------- #
_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.document.main+xml"/></Types>'
)


def _tc(text: str, borders: str = "", shading: str = "") -> str:
    tcpr = f"<w:tcPr>{borders}{shading}</w:tcPr>"
    return f"<w:tc>{tcpr}<w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:tc>"


def _bd(**edges: str) -> str:
    parts = []
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        value = edges.get(edge)
        if value:
            val, size = value.split(":")
            parts.append(f'<w:{edge} w:val="{val}" w:sz="{size}" w:color="000000"/>')
        else:
            parts.append(f'<w:{edge} w:val="nil" w:sz="0" w:color="auto"/>')
    return "<w:tcBorders>" + "".join(parts) + "</w:tcBorders>"


def conforming_document() -> str:
    header = f'<w:tr><w:trPr><w:tblHeader/></w:trPr>{_tc("变量", _bd(top="single:12", bottom="single:6"))}{_tc("(1)", _bd(top="single:12", bottom="single:6"))}</w:tr>'
    body = f'<w:tr>{_tc("treat", _bd())}{_tc("0.12***", _bd())}</w:tr>'
    panel = f'<w:tr>{_tc("Panel B: 稳健性", _bd(top="single:6"))}{_tc("", _bd(top="single:6"))}</w:tr>'
    tail = f'<w:tr>{_tc("N", _bd(bottom="single:12"))}{_tc("12,000", _bd(bottom="single:12"))}</w:tr>'
    borders = ('<w:tblBorders><w:top w:val="single" w:sz="12"/><w:left w:val="nil"/>'
               '<w:bottom w:val="single" w:sz="12"/><w:right w:val="nil"/>'
               '<w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>')
    return (f'<w:document xmlns:w="{W}"><w:body><w:tbl><w:tblPr>{borders}</w:tblPr>'
            f'{header}{body}{panel}{tail}</w:tbl></w:body></w:document>')


def gridded_document() -> str:
    grid = ('<w:tblBorders><w:top w:val="single" w:sz="4"/><w:left w:val="single" w:sz="4"/>'
            '<w:bottom w:val="single" w:sz="4"/><w:right w:val="single" w:sz="4"/>'
            '<w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/>'
            '</w:tblBorders>')
    shading = '<w:shd w:val="clear" w:color="auto" w:fill="D9D9D9"/>'
    rows = (f'<w:tr>{_tc("变量", "", shading)}{_tc("(1)", "", shading)}</w:tr>'
            f'<w:tr>{_tc("treat")}{_tc("0.12***")}</w:tr>')
    return (f'<w:document xmlns:w="{W}"><w:body><w:tbl>'
            f'<w:tblPr><w:tblStyle w:val="TableGrid"/>{grid}</w:tblPr>{rows}'
            f'</w:tbl></w:body></w:document>')


def style_only_document() -> str:
    rows = f'<w:tr>{_tc("变量")}{_tc("(1)")}</w:tr><w:tr>{_tc("treat")}{_tc("0.12***")}</w:tr>'
    return (f'<w:document xmlns:w="{W}"><w:body><w:tbl>'
            f'<w:tblPr><w:tblStyle w:val="TableGrid"/></w:tblPr>{rows}'
            f'</w:tbl></w:body></w:document>')


def write_docx(path: Path, document_xml: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _TYPES)
        archive.writestr("word/document.xml", document_xml)


GOOD_TEX = r"""
\begin{tabular}{lcc}
\toprule
Variable & (1) & (2) \\
\midrule
treat & 0.12*** & 0.10** \\
\bottomrule
\end{tabular}
"""

BAD_TEX = r"""
\begin{tabular}{|l|c|c|}
\hline
Variable & (1) & (2) \\
\hline
treat & 0.12*** & 0.10** \\
\hline
\end{tabular}
"""


def _levels(report: Report, check_prefix: str) -> list[str]:
    return [level for level, check, _ in report.rows if check.startswith(check_prefix)]


def selftest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / "ws"
        (workspace / "00_meta").mkdir(parents=True)
        (workspace / "04_results").mkdir(parents=True)

        # 1. Nothing produced yet -> the gate is silent, not noisy.
        (workspace / "00_meta" / "workflow_state.json").write_text(
            json.dumps({"table_style": {"format": "three-line"}}), encoding="utf-8")
        empty = evaluate(workspace)
        assert empty.to_dict()["ok"], "a pre-Stage-4 workspace must pass"
        assert any(level == SKIP for level, _, _ in empty.rows)

        # 2. A conforming .docx + booktabs .tex pass.
        write_docx(workspace / "04_results" / "table2.docx", conforming_document())
        (workspace / "04_results" / "table2.tex").write_text(GOOD_TEX, encoding="utf-8")
        good = evaluate(workspace)
        assert good.to_dict()["ok"], f"conforming artifacts must pass: {good.render()}"

        # 3. A gridded, shaded .docx fails on vertical *and* interior rules.
        write_docx(workspace / "04_results" / "table3.docx", gridded_document())
        bad = evaluate(workspace)
        checks = {check for level, check, _ in bad.rows if level == FAIL}
        assert not bad.to_dict()["ok"], "a full-grid table must fail"
        assert "docx:vertical-rule" in checks, checks
        assert "docx:interior-rule" in checks, checks
        assert any(check == "docx:shading" for _, check, _ in bad.rows), "shading must be flagged"
        (workspace / "04_results" / "table3.docx").unlink()

        # 4. Style-inherited borders are unverifiable, not silently accepted.
        write_docx(workspace / "04_results" / "table4.docx", style_only_document())
        implicit = evaluate(workspace)
        assert not implicit.to_dict()["ok"], "style-only borders must not pass"
        assert "docx:implicit-borders" in {c for level, c, _ in implicit.rows if level == FAIL}
        (workspace / "04_results" / "table4.docx").unlink()

        # 5. LaTeX: \hline + | + missing booktabs rules all fire.
        (workspace / "04_results" / "table5.tex").write_text(BAD_TEX, encoding="utf-8")
        tex_bad = evaluate(workspace)
        tex_checks = {check for level, check, _ in tex_bad.rows if level == FAIL}
        assert {"tex:vertical-rule", "tex:hline", "tex:missing-rule"} <= tex_checks, tex_checks
        (workspace / "04_results" / "table5.tex").unlink()

        # 6. Opting out is honoured, and --require overrides the opt-out.
        (workspace / "00_meta" / "workflow_state.json").write_text(
            json.dumps({"table_style": {"format": "journal-template"}}), encoding="utf-8")
        write_docx(workspace / "04_results" / "table6.docx", gridded_document())
        opted_out = evaluate(workspace)
        assert opted_out.to_dict()["ok"], "an explicit opt-out must not fail the build"
        assert any(level == SKIP for level, _, _ in opted_out.rows)
        forced = evaluate(workspace, require=True)
        assert not forced.to_dict()["ok"], "--require must override the opt-out"

        # 7. A missing state file still gets checked, with a WARN about the gap.
        (workspace / "00_meta" / "workflow_state.json").unlink()
        (workspace / "04_results" / "table6.docx").unlink()
        no_state = evaluate(workspace)
        assert no_state.to_dict()["ok"], no_state.render()
        assert any(check == "scope" and level == WARN for level, check, _ in no_state.rows)

    # Pure-function guards on the LaTeX matcher (comments must not count).
    with tempfile.TemporaryDirectory() as tmp:
        commented = Path(tmp) / "t.tex"
        commented.write_text("% \\hline in a comment\n" + GOOD_TEX, encoding="utf-8")
        assert not [f for f in analyse_tex(commented, Path(tmp)) if f[0] == FAIL], \
            "a commented-out \\hline must not fail the gate"

    print("selftest OK: three-line table gate invariants hold")


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify exported .docx/.tex tables follow the three-line (三线表) contract.",
    )
    parser.add_argument("workspace", nargs="?", type=Path, help="paper workspace root")
    parser.add_argument("--require", action="store_true",
                        help="check even when workflow_state.json opts out")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--selftest", action="store_true", help="verify this checker, then exit")
    args = parser.parse_args(argv)

    if args.selftest:
        selftest()
        return 0
    if args.workspace is None:
        fail("workspace path is required (or pass --selftest)")
    if not args.workspace.is_dir():
        fail(f"workspace not found: {args.workspace}")

    report = evaluate(args.workspace, require=args.require)
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2) if args.json
          else report.render())
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
