#!/usr/bin/env python3
"""Normalise every table inside a .docx to the economics/management three-line
table (三线表) house style.

Why this exists
---------------
Stage 4 emits tables through whichever backend the project chose -- StatsPAI
`.to_word()`, Stata `outreg2`/`putdocx`/`collect`, R `modelsummary`/`flextable`,
or a Markdown->Word conversion at Stage 9. Each of those writers has its own
default: full grids, banded shading, vertical rules, a "Table Grid" style. None
of them is the format economics and management journals actually print
(《经济研究》《管理世界》《中国工业经济》, AER/QJE/JPE and the Elsevier/Wiley
econ list all use the same booktabs-style three-line table).

Rather than teach every backend a different option, this normaliser runs once on
the finished .docx and makes the rule structure deterministic:

    ══════════════════════════   top rule      (1.5pt)
     header cells
    ──────────────────────────   header rule   (0.75pt)
     body cells
     ...
    ══════════════════════════   bottom rule   (1.5pt)

No vertical rules, no interior horizontal rules, no shading. Multi-panel tables
(``Panel A`` / ``面板A``) may carry one 0.75pt rule above each panel head -- the
single sanctioned exception, because both AER and 《管理世界》 print it.

It is deliberately dependency-free: it edits `word/document.xml` inside the
zip container with the standard library only, so it runs anywhere the rest of
the executable-gate battery runs (no python-docx, no pandoc, no Word).

Usage
-----
    # rewrite in place (a .bak copy is kept unless --no-backup)
    python3 scripts/make_three_line_tables.py 09_submission/main.docx

    # write elsewhere, Chinese journal typography (宋体小五 + Times New Roman)
    python3 scripts/make_three_line_tables.py 05_draft/main.docx \
        --output 09_submission/main.docx --preset cn-journal

    # whole workspace: 04_results/, 05_draft/, 06_polish/, 09_submission/
    python3 scripts/make_three_line_tables.py --workspace ./my-paper

    # see what would change without touching anything
    python3 scripts/make_three_line_tables.py main.docx --dry-run --json

Verification is a separate, read-only concern: `scripts/check_table_style.py`
is the gate that asserts the result conforms (and also covers the LaTeX side).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# Prefixes Word itself emits. Registering them keeps the serialised document
# byte-compatible with `mc:Ignorable="w14 w15 wp14"`-style attributes, which
# name prefixes rather than URIs and would dangle if ElementTree renamed them.
_NAMESPACES = {
    "w": W,
    "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
    "cx": "http://schemas.microsoft.com/office/drawing/2014/chartex",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "aink": "http://schemas.microsoft.com/office/drawing/2016/ink",
    "am3d": "http://schemas.microsoft.com/office/drawing/2017/model3d",
    "o": "urn:schemas-microsoft-com:office:office",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "v": "urn:schemas-microsoft-com:vml",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "w10": "urn:schemas-microsoft-com:office:word",
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16cex": "http://schemas.microsoft.com/office/word/2018/wordml/cex",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16sdtdh": "http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
    "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
    "wpi": "http://schemas.microsoft.com/office/word/2010/wordprocessingInk",
    "wne": "http://schemas.microsoft.com/office/word/2006/wordml",
    "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}

XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n'

# Border weights, in eighths of a point (the OOXML `w:sz` unit).
RULE_HEAVY_EIGHTHS = 12  # 1.5pt -- top and bottom rules
RULE_LIGHT_EIGHTHS = 6   # 0.75pt -- header rule and panel rules

# Schema element order. OOXML validates `w:tblPr` / `w:tcPr` / `w:trPr` as an
# ordered sequence, so a new child cannot simply be appended.
_TBLPR_ORDER = [
    "tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
    "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd",
    "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption",
    "tblDescription", "tblPrChange",
]
_TCPR_ORDER = [
    "cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd",
    "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark",
    "tcPrChange",
]
_TRPR_ORDER = [
    "cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter",
    "cantSplit", "trHeight", "tblHeader", "tblCellSpacing", "jc", "hidden",
    "ins", "del", "trPrChange",
]
_PPR_ORDER = [
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
    "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs",
    "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct",
    "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
    "suppressOverlap", "jc", "textDirection", "textAlignment", "textboxTightWrap",
    "outlineLvl", "divId", "cnfStyle", "rPr", "sectPr", "pPrChange",
]
_RPR_ORDER = [
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike",
    "dstrike", "outline", "shadow", "emboss", "imprint", "noProof",
    "snapToGrid", "vanish", "webHidden", "color", "spacing", "w", "kern",
    "position", "sz", "szCs", "highlight", "u", "effect", "bdr", "shd",
    "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout",
    "specVanish", "oMath",
]

# Panel heads that legitimately carry an interior rule. Kept deliberately tight:
# anything else in a first cell is body content, not a panel break.
_PANEL_PREFIXES = (
    "panel ", "panel:", "part ", "面板", "组别", "第一部分", "第二部分",
    "第三部分", "第四部分", "a. ", "b. ", "c. ",
)

PRESETS = {
    # Chinese economics / management journals: 宋体 for CJK, Times New Roman for
    # Latin and digits, 小五 (9pt). Matches《经济研究》《管理世界》house style.
    "cn-journal": {"ascii": "Times New Roman", "eastasia": "宋体", "size_pt": 9.0},
    # English-language econ journals (AER/QJE/JPE and the Elsevier econ list).
    "en-journal": {"ascii": "Times New Roman", "eastasia": "Times New Roman", "size_pt": 9.0},
    # Structure only: rules and alignment, fonts left exactly as the backend
    # wrote them. This is the default -- it never touches typography.
    "structure-only": {},
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def w(tag: str) -> str:
    return f"{{{W}}}{tag}"


def localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def register_namespaces() -> None:
    for prefix, uri in _NAMESPACES.items():
        ET.register_namespace(prefix, uri)


# --------------------------------------------------------------------------- #
# element helpers                                                              #
# --------------------------------------------------------------------------- #
def insert_ordered(parent: ET.Element, child: ET.Element, order: list[str]) -> None:
    """Insert `child` into `parent` at its schema-mandated position."""
    name = localname(child.tag)
    try:
        rank = order.index(name)
    except ValueError:
        parent.append(child)
        return
    for index, existing in enumerate(list(parent)):
        existing_name = localname(existing.tag)
        existing_rank = order.index(existing_name) if existing_name in order else len(order)
        if existing_rank > rank:
            parent.insert(index, child)
            return
    parent.append(child)


def ensure_child(parent: ET.Element, name: str, order: list[str]) -> ET.Element:
    found = parent.find(w(name))
    if found is None:
        found = ET.Element(w(name))
        insert_ordered(parent, found, order)
    return found


def ensure_props(node: ET.Element, name: str) -> ET.Element:
    """Return `node`'s properties element (`tblPr`/`tcPr`/`trPr`/`pPr`/`rPr`),
    creating it as the first child when absent -- properties always lead."""
    props = node.find(w(name))
    if props is None:
        props = ET.Element(w(name))
        node.insert(0, props)
    return props


def child_elements(node: ET.Element, name: str, stop_at: str) -> list[ET.Element]:
    """Depth-first descendants named `name` that belong to `node` itself.

    Descent stops at any nested `stop_at` element, so an outer table never
    claims the rows of a table nested inside one of its cells.
    """
    found: list[ET.Element] = []

    def walk(current: ET.Element) -> None:
        for kid in current:
            tag = localname(kid.tag)
            if tag == name:
                found.append(kid)
            elif tag == stop_at:
                continue
            else:
                walk(kid)

    walk(node)
    return found


def rows_of(tbl: ET.Element) -> list[ET.Element]:
    return child_elements(tbl, "tr", stop_at="tbl")


def cells_of(row: ET.Element) -> list[ET.Element]:
    return child_elements(row, "tc", stop_at="tbl")


def cell_text(cell: ET.Element) -> str:
    return "".join(node.text or "" for node in cell.iter(w("t"))).strip()


def _set_border(parent: ET.Element, edge: str, kind: str, size: int) -> None:
    """Write one border edge, replacing whatever was there."""
    for existing in parent.findall(w(edge)):
        parent.remove(existing)
    border = ET.SubElement(parent, w(edge))
    if kind == "none":
        border.set(w("val"), "nil")
        border.set(w("sz"), "0")
        border.set(w("space"), "0")
        border.set(w("color"), "auto")
    else:
        border.set(w("val"), "single")
        border.set(w("sz"), str(size))
        border.set(w("space"), "0")
        border.set(w("color"), "000000")


def _write_borders(parent: ET.Element, spec: dict[str, int | None], edges: list[str]) -> None:
    for edge in edges:
        size = spec.get(edge)
        if size is None:
            _set_border(parent, edge, "none", 0)
        else:
            _set_border(parent, edge, "single", size)


# --------------------------------------------------------------------------- #
# core transform                                                               #
# --------------------------------------------------------------------------- #
def is_panel_head(text: str) -> bool:
    lowered = text.strip().lower()
    if not lowered:
        return False
    return any(lowered.startswith(prefix) for prefix in _PANEL_PREFIXES)


def detect_header_rows(tbl: ET.Element, default: int) -> int:
    """Rows explicitly flagged `w:tblHeader` win; otherwise fall back."""
    rows = rows_of(tbl)
    flagged = 0
    for row in rows:
        trpr = row.find(w("trPr"))
        if trpr is not None and trpr.find(w("tblHeader")) is not None:
            flagged += 1
        else:
            break
    if flagged:
        return min(flagged, max(len(rows) - 1, 1))
    return min(default, max(len(rows) - 1, 1)) if len(rows) > 1 else 0


def normalise_table(
    tbl: ET.Element,
    *,
    header_rows: int,
    panel_rules: bool,
    align: bool,
    font: dict,
    repeat_header: bool,
) -> dict:
    rows = rows_of(tbl)
    if not rows:
        return {"rows": 0, "header_rows": 0, "panel_rules": 0, "cells": 0}

    n_header = detect_header_rows(tbl, header_rows)
    last_index = len(rows) - 1

    # Table-level rules. Direct formatting here overrides whatever the table
    # style (e.g. "Table Grid") would otherwise paint.
    tblpr = ensure_props(tbl, "tblPr")
    borders = ensure_child(tblpr, "tblBorders", _TBLPR_ORDER)
    _write_borders(
        borders,
        {"top": RULE_HEAVY_EIGHTHS, "bottom": RULE_HEAVY_EIGHTHS},
        ["top", "left", "bottom", "right", "insideH", "insideV"],
    )
    for shading in tblpr.findall(w("shd")):
        tblpr.remove(shading)

    panel_count = 0
    cell_count = 0
    for index, row in enumerate(rows):
        cells = cells_of(row)
        if not cells:
            continue
        first_text = cell_text(cells[0])
        is_panel = (
            panel_rules
            and index > n_header
            and index != 0
            and is_panel_head(first_text)
        )
        if is_panel:
            panel_count += 1

        top = RULE_HEAVY_EIGHTHS if index == 0 else (RULE_LIGHT_EIGHTHS if is_panel else None)
        bottom = None
        if index == last_index:
            bottom = RULE_HEAVY_EIGHTHS
        elif n_header and index == n_header - 1:
            bottom = RULE_LIGHT_EIGHTHS

        if repeat_header and index < n_header:
            trpr = ensure_props(row, "trPr")
            ensure_child(trpr, "tblHeader", _TRPR_ORDER)

        for column, cell in enumerate(cells):
            cell_count += 1
            tcpr = ensure_props(cell, "tcPr")
            tc_borders = ensure_child(tcpr, "tcBorders", _TCPR_ORDER)
            _write_borders(
                tc_borders,
                {"top": top, "bottom": bottom},
                ["top", "left", "bottom", "right", "insideH", "insideV"],
            )
            for shading in tcpr.findall(w("shd")):
                tcpr.remove(shading)
            if align:
                _align_cell(cell, column, is_stub=column == 0)
            if font:
                _restyle_cell(cell, font)

    return {
        "rows": len(rows),
        "header_rows": n_header,
        "panel_rules": panel_count,
        "cells": cell_count,
    }


def _align_cell(cell: ET.Element, column: int, *, is_stub: bool) -> None:
    """Stub column left, every other column centred -- the econ-table default."""
    justification = "left" if is_stub else "center"
    for para in child_elements(cell, "p", stop_at="tbl"):
        ppr = ensure_props(para, "pPr")
        jc = ensure_child(ppr, "jc", _PPR_ORDER)
        jc.set(w("val"), justification)


def _restyle_cell(cell: ET.Element, font: dict) -> None:
    half_points = str(int(round(font["size_pt"] * 2))) if font.get("size_pt") else None
    for run in child_elements(cell, "r", stop_at="tbl"):
        rpr = ensure_props(run, "rPr")
        if font.get("ascii") or font.get("eastasia"):
            fonts = ensure_child(rpr, "rFonts", _RPR_ORDER)
            if font.get("ascii"):
                fonts.set(w("ascii"), font["ascii"])
                fonts.set(w("hAnsi"), font["ascii"])
                fonts.set(w("cs"), font["ascii"])
            if font.get("eastasia"):
                fonts.set(w("eastAsia"), font["eastasia"])
        if half_points:
            for name in ("sz", "szCs"):
                node = ensure_child(rpr, name, _RPR_ORDER)
                node.set(w("val"), half_points)


# ElementTree drops namespace declarations it considers unused. That is fine for
# generic XML and wrong for OOXML, where `mc:Ignorable="w14 w15 wp14"` names
# *prefixes*: dropping a declaration leaves the attribute dangling and Word
# reports the document as corrupt. So the root element's original declarations
# are captured before parsing and re-injected afterwards.
_ROOT_TAG_RE = re.compile(r"""<(?!\?|!)[A-Za-z_][\w.:-]*(?:[^>"']|"[^"]*"|'[^']*')*>""")
_XMLNS_RE = re.compile(r"""xmlns:([A-Za-z_][\w.-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')""")


def _root_declarations(text: str) -> tuple[str, dict[str, str]]:
    match = _ROOT_TAG_RE.search(text)
    if not match:
        return "", {}
    tag = match.group(0)
    return tag, {m.group(1): (m.group(2) or m.group(3)) for m in _XMLNS_RE.finditer(tag)}


def restore_root_declarations(original: str, rendered: str) -> str:
    """Re-add xmlns:* declarations ElementTree pruned from the root element."""
    _, wanted = _root_declarations(original)
    if not wanted:
        return rendered
    match = _ROOT_TAG_RE.search(rendered)
    if not match:
        return rendered
    tag = match.group(0)
    present = set(_root_declarations(rendered)[1])
    missing = [f' xmlns:{prefix}="{uri}"' for prefix, uri in wanted.items()
               if prefix not in present]
    if not missing:
        return rendered
    closer = "/>" if tag.endswith("/>") else ">"
    patched = tag[: -len(closer)] + "".join(missing) + closer
    return rendered[: match.start()] + patched + rendered[match.end():]


def transform_document_xml(xml_bytes: bytes, **options) -> tuple[bytes, list[dict]]:
    register_namespaces()
    root = ET.fromstring(xml_bytes)
    stats = [normalise_table(tbl, **options) for tbl in root.iter(w("tbl"))]
    body = ET.tostring(root, encoding="unicode")
    body = restore_root_declarations(xml_bytes.decode("utf-8", "replace"), body)
    return XML_DECL.encode("utf-8") + body.encode("utf-8"), stats


# --------------------------------------------------------------------------- #
# docx container I/O                                                           #
# --------------------------------------------------------------------------- #
# Parts that can carry tables. Headers/footers are included because a running
# "continued" table header lives there in some journal templates.
_TABLE_PARTS = ("word/document.xml",)


def _table_parts(names: list[str]) -> list[str]:
    parts = [name for name in names if name in _TABLE_PARTS]
    parts += [
        name for name in names
        if name.startswith("word/") and (
            name.split("/")[-1].startswith("header") or name.split("/")[-1].startswith("footer")
        ) and name.endswith(".xml")
    ]
    return parts


def process_docx(source: Path, target: Path, *, dry_run: bool, **options) -> dict:
    if not source.is_file():
        fail(f"not a file: {source}")
    try:
        with zipfile.ZipFile(source) as archive:
            names = archive.namelist()
            if "word/document.xml" not in names:
                fail(f"{source} is not a Word document (no word/document.xml)")
            parts = _table_parts(names)
            payload = {name: archive.read(name) for name in names}
            infos = {info.filename: info for info in archive.infolist()}
    except zipfile.BadZipFile:
        fail(f"{source} is not a readable .docx container")

    all_stats: list[dict] = []
    for part in parts:
        try:
            new_bytes, stats = transform_document_xml(payload[part], **options)
        except ET.ParseError as exc:
            fail(f"{source}:{part} is not well-formed XML: {exc}")
        payload[part] = new_bytes
        all_stats.extend(stats)

    summary = {
        "source": str(source),
        "output": str(target),
        "tables": len(all_stats),
        "rows": sum(item["rows"] for item in all_stats),
        "cells": sum(item["cells"] for item in all_stats),
        "panel_rules": sum(item["panel_rules"] for item in all_stats),
        "dry_run": dry_run,
    }
    if dry_run:
        return summary

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", dir=str(target.parent)) as handle:
        staging = Path(handle.name)
    try:
        with zipfile.ZipFile(staging, "w", zipfile.ZIP_DEFLATED) as archive:
            for name in payload:
                info = zipfile.ZipInfo(name, date_time=infos[name].date_time)
                info.compress_type = infos[name].compress_type
                info.external_attr = infos[name].external_attr
                archive.writestr(info, payload[name])
        shutil.move(str(staging), str(target))
    finally:
        if staging.exists():
            staging.unlink()
    return summary


WORKSPACE_GLOBS = (
    "04_results/*.docx",
    "05_draft/*.docx",
    "06_polish/*.docx",
    "07_dehumanize/*.docx",
    "08_review/*.docx",
    "09_submission/*.docx",
)


def collect_workspace_docx(workspace: Path) -> list[Path]:
    found: list[Path] = []
    for pattern in WORKSPACE_GLOBS:
        found.extend(sorted(workspace.glob(pattern)))
    return [path for path in found if not path.name.startswith("~$")]


# --------------------------------------------------------------------------- #
# selftest                                                                     #
# --------------------------------------------------------------------------- #
_MINIMAL_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="word/document.xml"/></Relationships>'
)
_MINIMAL_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-'
    'officedocument.wordprocessingml.document.main+xml"/></Types>'
)


def build_fixture_document(rows: list[list[str]], *, grid: bool = True) -> str:
    """A gridded, shaded table -- what an unstyled backend export looks like."""

    def cell(text: str) -> str:
        shading = '<w:shd w:val="clear" w:color="auto" w:fill="D9D9D9"/>' if grid else ""
        return (
            f"<w:tc><w:tcPr><w:tcW w:w='2000' w:type='dxa'/>{shading}</w:tcPr>"
            f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:tc>"
        )

    body = "".join(f"<w:tr>{''.join(cell(text) for text in row)}</w:tr>" for row in rows)
    table_borders = (
        "<w:tblBorders>"
        "<w:top w:val='single' w:sz='4'/><w:left w:val='single' w:sz='4'/>"
        "<w:bottom w:val='single' w:sz='4'/><w:right w:val='single' w:sz='4'/>"
        "<w:insideH w:val='single' w:sz='4'/><w:insideV w:val='single' w:sz='4'/>"
        "</w:tblBorders>"
        if grid
        else ""
    )
    return (
        f'{XML_DECL}'
        f'<w:document xmlns:w="{W}" xmlns:w14="{_NAMESPACES["w14"]}" '
        f'xmlns:mc="{_NAMESPACES["mc"]}" mc:Ignorable="w14">'
        f"<w:body><w:tbl><w:tblPr><w:tblStyle w:val='TableGrid'/>{table_borders}"
        f"</w:tblPr>{body}</w:tbl></w:body></w:document>"
    ).replace("'", '"')


def write_fixture_docx(path: Path, document_xml: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _MINIMAL_TYPES)
        archive.writestr("_rels/.rels", _MINIMAL_RELS)
        archive.writestr("word/document.xml", document_xml)


def _edges(node: ET.Element) -> dict[str, str]:
    return {
        localname(edge.tag): (edge.get(w("val")) or "")
        for edge in node
    }


def selftest() -> None:
    register_namespaces()
    rows = [
        ["变量", "(1)", "(2)"],
        ["treat", "0.123***", "0.098**"],
        ["Panel B: 稳健性", "", ""],
        ["treat", "0.110***", "0.101**"],
        ["N", "12,000", "12,000"],
    ]
    xml = build_fixture_document(rows)

    out, stats = transform_document_xml(
        xml.encode("utf-8"),
        header_rows=1,
        panel_rules=True,
        align=True,
        font=PRESETS["cn-journal"],
        repeat_header=True,
    )
    assert len(stats) == 1, "one table expected"
    assert stats[0]["rows"] == 5 and stats[0]["header_rows"] == 1
    assert stats[0]["panel_rules"] == 1, "the Panel B row must earn a panel rule"

    root = ET.fromstring(out)
    tbl = next(root.iter(w("tbl")))
    tbl_borders = tbl.find(w("tblPr")).find(w("tblBorders"))
    edges = _edges(tbl_borders)
    assert edges["top"] == "single" and edges["bottom"] == "single", edges
    for edge in ("left", "right", "insideH", "insideV"):
        assert edges[edge] == "nil", f"{edge} must be suppressed, got {edges}"

    table_rows = rows_of(tbl)
    first = cells_of(table_rows[0])[0].find(w("tcPr")).find(w("tcBorders"))
    assert _edges(first)["top"] == "single", "top rule missing"
    assert first.find(w("top")).get(w("sz")) == str(RULE_HEAVY_EIGHTHS)
    assert first.find(w("bottom")).get(w("sz")) == str(RULE_LIGHT_EIGHTHS), "header rule weight"

    body_row = cells_of(table_rows[1])[0].find(w("tcPr")).find(w("tcBorders"))
    assert _edges(body_row)["bottom"] == "nil", "body rows must carry no rule"

    panel_row = cells_of(table_rows[2])[0].find(w("tcPr")).find(w("tcBorders"))
    assert panel_row.find(w("top")).get(w("sz")) == str(RULE_LIGHT_EIGHTHS), "panel rule weight"

    last_row = cells_of(table_rows[-1])[0].find(w("tcPr")).find(w("tcBorders"))
    assert last_row.find(w("bottom")).get(w("sz")) == str(RULE_HEAVY_EIGHTHS), "bottom rule weight"

    # Shading is stripped, header repeats, typography applied, stub stays left.
    assert not list(tbl.iter(w("shd"))), "cell shading must be removed"
    assert table_rows[0].find(w("trPr")).find(w("tblHeader")) is not None
    fonts = next(tbl.iter(w("rFonts")))
    assert fonts.get(w("eastAsia")) == "宋体" and fonts.get(w("ascii")) == "Times New Roman"
    assert next(tbl.iter(w("sz"))).get(w("val")) == "18", "9pt == 18 half-points"
    stub_jc = cells_of(table_rows[1])[0].find(w("p")).find(w("pPr")).find(w("jc"))
    assert stub_jc.get(w("val")) == "left"
    num_jc = cells_of(table_rows[1])[1].find(w("p")).find(w("pPr")).find(w("jc"))
    assert num_jc.get(w("val")) == "center"

    # Prefix preservation: mc:Ignorable="w14" must not dangle after a round trip.
    text = out.decode("utf-8")
    assert 'xmlns:w14=' in text and 'mc:Ignorable="w14"' in text, "namespace prefixes drifted"

    # Idempotence: running twice changes nothing further.
    twice, _ = transform_document_xml(
        out, header_rows=1, panel_rules=True, align=True,
        font=PRESETS["cn-journal"], repeat_header=True,
    )
    assert twice == out, "normalisation must be idempotent"

    # structure-only preset leaves typography untouched.
    plain, _ = transform_document_xml(
        xml.encode("utf-8"), header_rows=1, panel_rules=True, align=False,
        font={}, repeat_header=True,
    )
    plain_tbl = next(ET.fromstring(plain).iter(w("tbl")))
    assert not list(plain_tbl.iter(w("rFonts"))), "structure-only must not set fonts"
    assert not list(plain_tbl.iter(w("jc"))), "--no-align must not set alignment"

    # End-to-end through a real zip container.
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "09_submission" / "main.docx"
        write_fixture_docx(source, xml)
        summary = process_docx(
            source, source, dry_run=False, header_rows=1, panel_rules=True,
            align=True, font=PRESETS["en-journal"], repeat_header=True,
        )
        assert summary["tables"] == 1 and summary["cells"] == 15, summary
        with zipfile.ZipFile(source) as archive:
            assert "[Content_Types].xml" in archive.namelist(), "container parts must survive"
            round_trip = archive.read("word/document.xml")
        assert b"insideV" in round_trip

        workspace = Path(tmp)
        assert collect_workspace_docx(workspace) == [source]

    print("selftest OK: three-line table normaliser invariants hold")


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalise .docx tables to the econ/management three-line (三线表) style.",
    )
    parser.add_argument("docx", nargs="*", type=Path, help="one or more .docx files")
    parser.add_argument("--workspace", type=Path,
                        help="paper workspace; normalises every .docx under the stage dirs")
    parser.add_argument("--output", type=Path,
                        help="write here instead of in place (single input only)")
    parser.add_argument("--preset", choices=sorted(PRESETS), default="structure-only",
                        help="typography preset; default touches rules only")
    parser.add_argument("--header-rows", type=int, default=1,
                        help="header rows when the table does not flag them itself (default 1)")
    parser.add_argument("--no-panel-rules", action="store_true",
                        help="never draw the 0.75pt rule above a Panel/面板 row")
    parser.add_argument("--no-align", action="store_true",
                        help="leave paragraph alignment alone (default: stub left, rest centred)")
    parser.add_argument("--no-repeat-header", action="store_true",
                        help="do not mark header rows as repeating across pages")
    parser.add_argument("--no-backup", action="store_true",
                        help="skip the .bak copy taken before an in-place rewrite")
    parser.add_argument("--dry-run", action="store_true", help="report without writing")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--selftest", action="store_true", help="verify this tool, then exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.selftest:
        selftest()
        return 0

    targets = list(args.docx)
    if args.workspace:
        if not args.workspace.is_dir():
            fail(f"workspace not found: {args.workspace}")
        targets.extend(collect_workspace_docx(args.workspace))
    if not targets:
        fail("nothing to do: pass one or more .docx files, or --workspace <dir>")
    if args.output and len(targets) != 1:
        fail("--output takes exactly one input .docx")
    if args.header_rows < 0:
        fail("--header-rows must be >= 0")

    options = {
        "header_rows": args.header_rows,
        "panel_rules": not args.no_panel_rules,
        "align": not args.no_align,
        "font": dict(PRESETS[args.preset]),
        "repeat_header": not args.no_repeat_header,
    }

    summaries = []
    for source in targets:
        target = args.output or source
        if not args.dry_run and not args.no_backup and target == source:
            shutil.copy2(source, source.with_suffix(source.suffix + ".bak"))
        summaries.append(process_docx(source, target, dry_run=args.dry_run, **options))

    if args.json:
        print(json.dumps({"preset": args.preset, "files": summaries},
                         ensure_ascii=False, indent=2))
    else:
        verb = "would normalise" if args.dry_run else "normalised"
        print(f"Three-line table normaliser (preset={args.preset})")
        for item in summaries:
            print(f"  {verb} {item['tables']} table(s), {item['cells']} cell(s), "
                  f"{item['panel_rules']} panel rule(s)  ->  {item['output']}")
        print("  verify with: python3 scripts/check_table_style.py <workspace>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
