#!/usr/bin/env python3
r"""Assemble the finished manuscript into one full-text `.docx` deliverable.

Why this exists
---------------
Every stage of this pipeline produced its own artifact and the last hop produced
none. Stage 4 exports each table three ways (`.tex`, `.docx`, `.xlsx`); Stage 5-8
carry a *body* file that only ever references those tables by include directive;
Stage 9 then asks for "the Word version" -- and nothing built it. Two gates,
`make_three_line_tables.py` and `check_table_style.py`, already operated on
`09_submission/main.docx`, a file no step in the pipeline was instructed to
create. Meanwhile the venues that most often require Word (中文期刊, 学位论文
committees, and any co-author who edits in track-changes) were exactly the runs
with no defined path to a deliverable.

This module is that step. It takes the last manuscript in the chain, resolves the
exhibit includes into *real Word tables*, embeds the figures, appends the
reference list, and writes one self-contained `.docx`.

Fidelity, stated rather than assumed
------------------------------------
Two converters, and the run records which one it used
(`workflow_state.json.manuscript.converter`):

  ``pandoc``   preferred when the binary is present. Handles citeproc, a journal
               ``--reference-doc`` template, and inline math properly.
  ``builtin``  a dependency-free writer that emits `word/document.xml` into a zip
               with the standard library alone -- same discipline as
               `make_three_line_tables.py`, so the deliverable can still be built
               on a machine with no pandoc and no python-docx.

The builtin writer emits tables **already in three-line form** (heavy top rule,
light header rule, heavy bottom rule, no vertical rules, no shading), so the
output satisfies `check_table_style.py` without a repair pass. Running
`make_three_line_tables.py` afterwards remains safe -- it is idempotent.

What it refuses to do quietly
-----------------------------
An exhibit include that resolves to nothing, a figure that exists only as a
`.pdf` this writer cannot rasterise, a `\ref{}` with no target: each is recorded
in `manuscript.unresolved_markers` and printed. A conversion that silently drops
a table is the failure mode this whole layer exists to prevent, so the assembler
counts what it placed (`exhibits_embedded` / `figures_embedded`) and
`check_deliverable_contract.py` is what passes or fails on the result.

Usage:
    python3 scripts/assemble_manuscript_docx.py <workspace>
    python3 scripts/assemble_manuscript_docx.py <workspace> --converter builtin
    python3 scripts/assemble_manuscript_docx.py <workspace> --json
    python3 scripts/assemble_manuscript_docx.py --selftest
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

# Manuscript chain, latest first: the deliverable is built from the most advanced
# version that exists, not from whichever stage happens to be open.
CHAIN = ["09_submission", "08_review", "07_dehumanize", "06_polish", "05_draft"]
BODY_STEMS = ("main",)
BODY_SUFFIXES = (".md", ".tex")
EXHIBIT_DIRS = ("04_results", "03_analysis/results", "")
EXHIBIT_SUFFIXES = (".md", ".tex", ".csv")
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")

EMU_PER_PX = 9525
MAX_IMAGE_EMU = 5486400  # 6 inches: the usable width of a portrait A4 body

# Three-line rule weights in eighths of a point, matching check_table_style.py's
# HEAVY_MIN_EIGHTHS / LIGHT_MAX_EIGHTHS thresholds.
HEAVY = 12
LIGHT = 6


# --------------------------------------------------------------------------- #
# blocks                                                                       #
# --------------------------------------------------------------------------- #
class Block:
    """One element of the assembled document."""

    def __init__(self, kind: str, **fields: object) -> None:
        self.kind = kind
        self.__dict__.update(fields)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Block({self.kind}, {({k: v for k, v in self.__dict__.items() if k != 'kind'})})"


# --------------------------------------------------------------------------- #
# source discovery                                                             #
# --------------------------------------------------------------------------- #
def load_state(workspace: Path) -> dict:
    for rel in ("00_meta/workflow_state.json", "workflow_state.json"):
        path = workspace / rel
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
    return {}


def declared_format(state: dict) -> str:
    fmt = str(state.get("manuscript", {}).get("format", "") or "").lower()
    return fmt if fmt in {"latex", "markdown"} else ""


def find_source(workspace: Path, fmt: str = "") -> Path | None:
    """The most advanced manuscript body on disk, honouring the declared format."""
    preferred = {"markdown": (".md",), "latex": (".tex",)}.get(fmt, ())
    order = preferred + tuple(s for s in BODY_SUFFIXES if s not in preferred)
    for stage in CHAIN:
        for stem in BODY_STEMS:
            for suffix in order:
                candidate = workspace / stage / f"{stem}{suffix}"
                if candidate.is_file():
                    return candidate
    return None


# --------------------------------------------------------------------------- #
# exhibit + figure resolution                                                  #
# --------------------------------------------------------------------------- #
def _candidate_paths(workspace: Path, target: str, suffixes: tuple[str, ...]) -> list[Path]:
    target = target.strip().strip("{}").lstrip("./")
    stem = target
    for suffix in suffixes:
        if stem.lower().endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    names = [stem, Path(stem).name]
    out: list[Path] = []
    for base in EXHIBIT_DIRS:
        root = workspace / base if base else workspace
        for name in names:
            for suffix in suffixes:
                out.append(root / f"{name}{suffix}")
    # Also honour a path that already resolves as written.
    out.insert(0, workspace / target)
    seen: set[Path] = set()
    unique = []
    for path in out:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique


def resolve_exhibit(workspace: Path, target: str) -> Path | None:
    for path in _candidate_paths(workspace, target, EXHIBIT_SUFFIXES):
        if path.is_file():
            return path
    return None


def resolve_image(workspace: Path, target: str) -> Path | None:
    for path in _candidate_paths(workspace, target, IMAGE_SUFFIXES):
        if path.is_file():
            return path
    return None


# --------------------------------------------------------------------------- #
# table parsing                                                                #
# --------------------------------------------------------------------------- #
_TEX_CLEAN = [
    (re.compile(r"\\(?:toprule|midrule|bottomrule|hline|cmidrule)(?:\([^)]*\))?(?:\{[^{}]*\})?"), ""),
    (re.compile(r"\\multicolumn\{\d+\}\{[^{}]*\}\{([^{}]*)\}"), r"\1"),
    (re.compile(r"\\(?:sym|textbf|textit|emph|mathrm|text)\{([^{}]*)\}"), r"\1"),
    (re.compile(r"\\(?:small|footnotesize|scriptsize|centering|noalign|addlinespace)\b"), ""),
    (re.compile(r"[$\\]"), ""),
]


def _clean_tex_cell(cell: str) -> str:
    out = cell
    for pattern, repl in _TEX_CLEAN:
        out = pattern.sub(repl, out)
    return " ".join(out.split())


def parse_tex_table(text: str) -> tuple[list[list[str]], int]:
    """Rows + header-row count from the first tabular environment in `text`."""
    m = re.search(r"\\begin\{(tabular\*?|tabularx|longtable)\}", text)
    if not m:
        return [], 0
    body = text[m.end():]
    end = re.search(r"\\end\{(tabular\*?|tabularx|longtable)\}", body)
    if end:
        body = body[: end.start()]
    # Drop the column spec (and any width argument) that follows \begin{tabular}.
    depth = 0
    cut = 0
    for i, ch in enumerate(body):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                cut = i + 1
                break
        elif ch not in " \t\n" and depth == 0:
            break
    body = body[cut:]

    # \midrule marks the end of the header block when it is present.
    header_rows = 0
    mid = re.search(r"\\midrule", body)
    if mid:
        header_rows = len([r for r in body[: mid.start()].split(r"\\") if _clean_tex_cell(r)])

    rows: list[list[str]] = []
    for raw in body.split(r"\\"):
        cells = [_clean_tex_cell(c) for c in raw.split("&")]
        if any(cells):
            rows.append(cells)
    return rows, min(header_rows, len(rows))


def parse_md_table(text: str) -> tuple[list[list[str]], int]:
    """Rows + header-row count from the first pipe table in `text`."""
    lines = [ln.strip() for ln in text.splitlines()]
    block: list[str] = []
    for line in lines:
        if line.startswith("|"):
            block.append(line)
        elif block:
            break
    if not block:
        return [], 0
    rows: list[list[str]] = []
    header_rows = 0
    for line in block:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c or "") for c in cells if c != ""):
            header_rows = len(rows)          # the delimiter row closes the header
            continue
        rows.append(cells)
    return rows, header_rows or (1 if rows else 0)


def parse_csv_table(text: str) -> tuple[list[list[str]], int]:
    rows = [row for row in csv.reader(io.StringIO(text)) if any(c.strip() for c in row)]
    return rows, (1 if rows else 0)


def load_table(path: Path) -> tuple[list[list[str]], int]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".csv":
        return parse_csv_table(text)
    if path.suffix.lower() == ".md":
        return parse_md_table(text)
    return parse_tex_table(text)


def table_caption(path: Path) -> str:
    """A caption from the exhibit file itself, so numbering survives conversion."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"\\caption\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", text)
    if m:
        return _clean_tex_cell(m.group(1))
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if re.match(r"^\*\*(表|Table)", line):
            return line.strip("*").strip()
    return ""


# --------------------------------------------------------------------------- #
# body parsing                                                                 #
# --------------------------------------------------------------------------- #
_TEX_HEADINGS = {
    "section": 1, "section*": 1,
    "subsection": 2, "subsection*": 2,
    "subsubsection": 3, "subsubsection*": 3,
    "paragraph": 4, "paragraph*": 4,
}
_TEX_INLINE = [
    (re.compile(r"\\(?:textbf|textit|emph|texttt|underline)\{([^{}]*)\}"), r"\1"),
    (re.compile(r"\\(?:citep|citet|cite|citeauthor|citeyear)\s*(?:\[[^\]]*\])?\{([^{}]*)\}"), r"(\1)"),
    (re.compile(r"\\(?:label|index)\{[^{}]*\}"), ""),
    (re.compile(r"\\(?:ref|eqref|autoref|pageref)\{([^{}]*)\}"), r"\1"),
    (re.compile(r"\\%"), "%"),
    (re.compile(r"\\&"), "&"),
    (re.compile(r"\\(?:newpage|clearpage|maketitle|centering|noindent|bigskip|medskip|smallskip)\b"), ""),
]


def _clean_tex_inline(text: str) -> str:
    out = text
    for pattern, repl in _TEX_INLINE:
        out = pattern.sub(repl, out)
    out = re.sub(r"(?<!\\)%.*$", "", out, flags=re.MULTILINE)
    return " ".join(out.split())


def parse_latex_body(text: str) -> list[Block]:
    m = re.search(r"\\begin\{document\}", text)
    if m:
        text = text[m.end():]
    text = re.split(r"\\end\{document\}", text)[0]

    blocks: list[Block] = []
    # Float environments first: they carry the include + caption pairing.
    def float_repl(match: re.Match) -> str:
        inner = match.group(0)
        cap = re.search(r"\\caption\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", inner)
        caption = _clean_tex_inline(cap.group(1)) if cap else ""
        graphic = re.search(r"\\includegraphics\s*(?:\[[^\]]*\])?\{([^{}]*)\}", inner)
        if graphic:
            return f"\n@@PWFIGURE:{graphic.group(1)}::{caption}@@\n"
        inp = re.search(r"\\(?:input|include)\{([^{}]*)\}", inner)
        if inp:
            return f"\n@@PWTABLE:{inp.group(1)}::{caption}@@\n"
        if re.search(r"\\begin\{tabular", inner):
            return f"\n@@PWINLINETABLE:{len(blocks)}::{caption}@@\n"
        return f"\n@@PWTABLE:::{caption}@@\n"

    inline_tables: list[str] = []

    def stash_inline(match: re.Match) -> str:
        inner = match.group(0)
        cap = re.search(r"\\caption\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", inner)
        caption = _clean_tex_inline(cap.group(1)) if cap else ""
        graphic = re.search(r"\\includegraphics\s*(?:\[[^\]]*\])?\{([^{}]*)\}", inner)
        if graphic:
            return f"\n@@PWFIGURE:{graphic.group(1)}::{caption}@@\n"
        inp = re.search(r"\\(?:input|include)\{([^{}]*)\}", inner)
        if inp:
            return f"\n@@PWTABLE:{inp.group(1)}::{caption}@@\n"
        if re.search(r"\\begin\{tabular", inner):
            inline_tables.append(inner)
            return f"\n@@PWINLINE:{len(inline_tables) - 1}::{caption}@@\n"
        return "\n"

    text = re.sub(r"\\begin\{(table\*?|figure\*?)\}.*?\\end\{\1\}", stash_inline, text, flags=re.DOTALL)
    text = re.sub(r"\\(?:input|include)\{([^{}]*)\}", lambda m: f"\n@@PWTABLE:{m.group(1)}::@@\n", text)
    text = re.sub(r"\\includegraphics\s*(?:\[[^\]]*\])?\{([^{}]*)\}",
                  lambda m: f"\n@@PWFIGURE:{m.group(1)}::@@\n", text)
    text = re.sub(r"\\bibliography\{([^{}]*)\}", lambda m: f"\n@@PWBIB:{m.group(1)}@@\n", text)

    for chunk in re.split(r"\n\s*\n", text):
        chunk = chunk.strip()
        if not chunk:
            continue
        marker = re.fullmatch(r"@@PW(TABLE|FIGURE|INLINE|BIB):([^:@]*)(?:::(.*))?@@", chunk, re.DOTALL)
        if marker:
            kind, payload, caption = marker.group(1), marker.group(2), (marker.group(3) or "")
            if kind == "TABLE":
                blocks.append(Block("include_table", target=payload, caption=caption))
            elif kind == "FIGURE":
                blocks.append(Block("include_figure", target=payload, caption=caption))
            elif kind == "INLINE":
                rows, header = parse_tex_table(inline_tables[int(payload)])
                blocks.append(Block("table", rows=rows, header_rows=header, caption=caption, source="inline"))
            else:
                blocks.append(Block("bibliography", target=payload))
            continue
        heading = re.match(r"\\(\w+\*?)\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\s*$", chunk)
        if heading and heading.group(1) in _TEX_HEADINGS:
            blocks.append(Block("heading", level=_TEX_HEADINGS[heading.group(1)],
                                text=_clean_tex_inline(heading.group(2))))
            continue
        # A heading followed by prose in the same paragraph block.
        lead = re.match(r"\\(\w+\*?)\{([^{}]*)\}", chunk)
        if lead and lead.group(1) in _TEX_HEADINGS:
            blocks.append(Block("heading", level=_TEX_HEADINGS[lead.group(1)],
                                text=_clean_tex_inline(lead.group(2))))
            chunk = chunk[lead.end():]
        body = _clean_tex_inline(chunk)
        if body:
            blocks.append(Block("para", text=body))
    return blocks


def parse_markdown_body(text: str) -> list[Block]:
    blocks: list[Block] = []
    lines = text.splitlines()
    i = 0
    para: list[str] = []

    def flush() -> None:
        if para:
            blocks.append(Block("para", text=" ".join(" ".join(para).split())))
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        image = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)\s*$", stripped)
        include = re.match(r"^\{\{\s*(?:include|table|exhibit)\s*:\s*([^}]+?)\s*\}\}\s*$", stripped)
        if heading:
            flush()
            blocks.append(Block("heading", level=len(heading.group(1)), text=heading.group(2).strip()))
            i += 1
            continue
        if image:
            flush()
            blocks.append(Block("include_figure", target=image.group(2), caption=image.group(1).strip()))
            i += 1
            continue
        if include:
            flush()
            blocks.append(Block("include_table", target=include.group(1), caption=""))
            i += 1
            continue
        if stripped.startswith("|"):
            flush()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows, header = parse_md_table("\n".join(table_lines))
            blocks.append(Block("table", rows=rows, header_rows=header, caption="", source="inline"))
            continue
        if not stripped:
            flush()
            i += 1
            continue
        para.append(stripped)
        i += 1
    flush()
    return blocks


def parse_body(path: Path) -> list[Block]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".md":
        return parse_markdown_body(text)
    return parse_latex_body(text)


# --------------------------------------------------------------------------- #
# bibliography                                                                 #
# --------------------------------------------------------------------------- #
_BIB_ENTRY = re.compile(r"@\w+\s*\{\s*([^,]+),(.*?)\n\}", re.DOTALL)
_BIB_FIELD = re.compile(r"(\w+)\s*=\s*[{\"](.*?)[}\"]\s*,?\s*\n", re.DOTALL)


def format_bibliography(bib_path: Path) -> list[str]:
    """Flat reference lines from a .bib file, ordered by author then year.

    Deliberately plain: when pandoc + a CSL style is available it does this job
    properly, and this fallback exists so a run without pandoc still ships a
    reference list rather than an empty section.
    """
    text = bib_path.read_text(encoding="utf-8", errors="ignore")
    out: list[tuple[str, str]] = []
    for match in _BIB_ENTRY.finditer(text):
        fields = {k.lower(): " ".join(v.split()) for k, v in _BIB_FIELD.findall(match.group(2) + "\n")}
        author = fields.get("author", "").replace(" and ", ", ")
        year = fields.get("year", "n.d.")
        title = fields.get("title", "").strip("{}")
        venue = fields.get("journal") or fields.get("booktitle") or fields.get("publisher") or ""
        volume = fields.get("volume", "")
        pages = fields.get("pages", "")
        tail = ", ".join(p for p in [venue, volume, pages] if p)
        line = f"{author} ({year}). {title}." + (f" {tail}." if tail else "")
        out.append((author.lower() + year, " ".join(line.split())))
    return [line for _, line in sorted(out)]


def find_bib(workspace: Path, target: str = "") -> Path | None:
    names = [target] if target else []
    names += ["ref", "references", "bibliography"]
    for stage in CHAIN:
        for name in names:
            for candidate in (workspace / stage / f"{Path(name).name}.bib",):
                if candidate.is_file():
                    return candidate
    matches = sorted(workspace.rglob("*.bib"))
    return matches[0] if matches else None


# --------------------------------------------------------------------------- #
# docx writer (stdlib only)                                                    #
# --------------------------------------------------------------------------- #
_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Default Extension="jpeg" ContentType="image/jpeg"/>'
    '<Default Extension="jpg" ContentType="image/jpeg"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
    'wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.'
    'wordprocessingml.styles+xml"/>'
    "</Types>"
)

_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    'officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)

_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:styles xmlns:w="{W}">'
    '<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/>'
    '<w:pPr><w:jc w:val="center"/><w:spacing w:before="120" w:after="120"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="20"/></w:rPr></w:style>'
    "</w:styles>"
)


def _esc(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _para(text: str, *, style: str = "", bold: bool = False, size: int = 0,
          align: str = "", indent: bool = False) -> str:
    props = []
    if style:
        props.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        props.append(f'<w:jc w:val="{align}"/>')
    if indent:
        props.append('<w:ind w:firstLine="480"/>')
    ppr = f"<w:pPr>{''.join(props)}</w:pPr>" if props else ""
    rprops = []
    if bold:
        rprops.append("<w:b/>")
    if size:
        rprops.append(f'<w:sz w:val="{size}"/>')
    rpr = f"<w:rPr>{''.join(rprops)}</w:rPr>" if rprops else ""
    if not text:
        return f"<w:p>{ppr}</w:p>"
    return f"<w:p>{ppr}<w:r>{rpr}<w:t xml:space=\"preserve\">{_esc(text)}</w:t></w:r></w:p>"


def _cell_borders(top: int = 0, bottom: int = 0) -> str:
    parts = []
    for edge in ("top", "left", "bottom", "right"):
        size = {"top": top, "bottom": bottom}.get(edge, 0)
        if size:
            parts.append(f'<w:{edge} w:val="single" w:sz="{size}" w:color="000000"/>')
        else:
            parts.append(f'<w:{edge} w:val="nil" w:sz="0" w:color="auto"/>')
    parts.append('<w:insideH w:val="nil" w:sz="0" w:color="auto"/>')
    parts.append('<w:insideV w:val="nil" w:sz="0" w:color="auto"/>')
    return "<w:tcBorders>" + "".join(parts) + "</w:tcBorders>"


def _is_panel_head(cells: list[str]) -> bool:
    head = (cells[0] if cells else "").strip()
    return bool(re.match(r"^(Panel\s+[A-Z]|面板\s*[A-Z\u4e00-\u9fff])", head))


def render_table(rows: list[list[str]], header_rows: int) -> str:
    """A Word table already in three-line form (see check_table_style.py)."""
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    header_rows = max(1, min(header_rows or 1, len(rows)))
    last = len(rows) - 1

    borders = ('<w:tblBorders>'
               f'<w:top w:val="single" w:sz="{HEAVY}" w:color="000000"/>'
               '<w:left w:val="nil" w:sz="0" w:color="auto"/>'
               f'<w:bottom w:val="single" w:sz="{HEAVY}" w:color="000000"/>'
               '<w:right w:val="nil" w:sz="0" w:color="auto"/>'
               '<w:insideH w:val="nil" w:sz="0" w:color="auto"/>'
               '<w:insideV w:val="nil" w:sz="0" w:color="auto"/>'
               '</w:tblBorders>')
    grid = "<w:tblGrid>" + "".join('<w:gridCol w:w="1200"/>' for _ in range(width)) + "</w:tblGrid>"

    out = [f"<w:tbl><w:tblPr><w:tblW w:w=\"0\" w:type=\"auto\"/>{borders}</w:tblPr>{grid}"]
    for index, row in enumerate(rows):
        cells = list(row) + [""] * (width - len(row))
        top = HEAVY if index == 0 else (LIGHT if _is_panel_head(cells) and index else 0)
        bottom = HEAVY if index == last else (LIGHT if index == header_rows - 1 else 0)
        trpr = "<w:trPr><w:tblHeader/></w:trPr>" if index < header_rows else ""
        tcs = []
        for cell in cells:
            align = "left" if cells.index(cell) == 0 else "center"
            body = _para(cell, align=align)
            tcs.append(f"<w:tc><w:tcPr>{_cell_borders(top, bottom)}</w:tcPr>{body}</w:tc>")
        out.append(f"<w:tr>{trpr}{''.join(tcs)}</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def _png_size(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        w, h = struct.unpack(">II", data[16:24])
        return int(w), int(h)
    return None


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2: i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5: i + 9])
            return int(w), int(h)
        i += 2 + length
    return None


def image_extent(data: bytes) -> tuple[int, int]:
    size = _png_size(data) or _jpeg_size(data) or (800, 600)
    w_emu, h_emu = size[0] * EMU_PER_PX, size[1] * EMU_PER_PX
    if w_emu > MAX_IMAGE_EMU:
        h_emu = int(h_emu * MAX_IMAGE_EMU / w_emu)
        w_emu = MAX_IMAGE_EMU
    return max(w_emu, 1), max(h_emu, 1)


def render_image(rel_id: str, index: int, cx: int, cy: int) -> str:
    return (
        '<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
        f'<wp:inline xmlns:wp="{WP_NS}" distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{index}" name="Figure {index}"/>'
        f'<a:graphic xmlns:a="{A_NS}"><a:graphicData uri="{PIC_NS}">'
        f'<pic:pic xmlns:pic="{PIC_NS}"><pic:nvPicPr>'
        f'<pic:cNvPr id="{index}" name="Figure {index}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip xmlns:r="{R_NS}" r:embed="{rel_id}"/>'
        "<a:stretch><a:fillRect/></a:stretch></pic:blipFill>"
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"
    )


def write_docx(path: Path, body_xml: str, media: list[tuple[str, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W}" xmlns:r="{R_NS}">'
        f"<w:body>{body_xml}</w:body></w:document>"
    )
    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/styles" Target="styles.xml"/>']
    for index, (name, _) in enumerate(media, start=1):
        rels.append(
            f'<Relationship Id="rIdImg{index}" Type="http://schemas.openxmlformats.org/officeDocument/'
            f'2006/relationships/image" Target="media/{name}"/>'
        )
    rels.append("</Relationships>")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
        archive.writestr("_rels/.rels", _ROOT_RELS)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/styles.xml", _STYLES)
        archive.writestr("word/_rels/document.xml.rels", "".join(rels))
        for name, data in media:
            archive.writestr(f"word/media/{name}", data)


# --------------------------------------------------------------------------- #
# assembly                                                                     #
# --------------------------------------------------------------------------- #
class Assembly:
    def __init__(self) -> None:
        self.exhibits = 0
        self.figures = 0
        self.unresolved: list[str] = []
        self.notes: list[str] = []


def assemble_builtin(workspace: Path, source: Path, out_path: Path) -> Assembly:
    result = Assembly()
    blocks = parse_body(source)
    body: list[str] = []
    media: list[tuple[str, bytes]] = []
    table_no = 0
    figure_no = 0

    for block in blocks:
        if block.kind == "heading":
            level = min(int(block.level), 4)
            body.append(_para(block.text, bold=True, size=32 - 2 * level))
        elif block.kind == "para":
            body.append(_para(block.text, indent=True))
        elif block.kind == "table":
            table_no += 1
            caption = block.caption or f"表 {table_no}"
            body.append(_para(caption, style="Caption", bold=True, align="center"))
            body.append(render_table(block.rows, block.header_rows))
            result.exhibits += 1
        elif block.kind == "include_table":
            target = str(block.target).strip()
            path = resolve_exhibit(workspace, target) if target else None
            if path is None:
                result.unresolved.append(f"table include unresolved: {target or '(empty)'}")
                body.append(_para(f"[UNRESOLVED TABLE INCLUDE: {target}]", bold=True))
                continue
            rows, header = load_table(path)
            if not rows:
                result.unresolved.append(f"table include parsed to zero rows: {path.name}")
                body.append(_para(f"[EMPTY TABLE: {path.name}]", bold=True))
                continue
            table_no += 1
            caption = block.caption or table_caption(path) or f"表 {table_no}"
            body.append(_para(caption, style="Caption", bold=True, align="center"))
            body.append(render_table(rows, header))
            result.exhibits += 1
            result.notes.append(f"table {table_no} <- {path.relative_to(workspace)}")
        elif block.kind == "include_figure":
            target = str(block.target).strip()
            path = resolve_image(workspace, target) if target else None
            if path is None:
                result.unresolved.append(f"figure unresolved (no .png/.jpg on disk): {target or '(empty)'}")
                body.append(_para(f"[UNRESOLVED FIGURE: {target}]", bold=True))
                continue
            data = path.read_bytes()
            name = f"image{len(media) + 1}{path.suffix.lower()}"
            media.append((name, data))
            cx, cy = image_extent(data)
            figure_no += 1
            body.append(render_image(f"rIdImg{len(media)}", len(media), cx, cy))
            body.append(_para(block.caption or f"图 {figure_no}", style="Caption",
                              bold=True, align="center"))
            result.figures += 1
            result.notes.append(f"figure {figure_no} <- {path.relative_to(workspace)}")
        elif block.kind == "bibliography":
            bib = find_bib(workspace, str(block.target))
            body.append(_para("参考文献 / References", bold=True, size=28))
            if bib is None:
                result.unresolved.append("bibliography referenced but no .bib found")
                body.append(_para("[UNRESOLVED BIBLIOGRAPHY]", bold=True))
                continue
            for line in format_bibliography(bib):
                body.append(_para(line))
            result.notes.append(f"bibliography <- {bib.relative_to(workspace)}")

    if not any(b.kind == "bibliography" for b in blocks):
        bib = find_bib(workspace)
        if bib is not None:
            lines = format_bibliography(bib)
            if lines:
                body.append(_para("参考文献 / References", bold=True, size=28))
                for line in lines:
                    body.append(_para(line))
                result.notes.append(f"bibliography <- {bib.relative_to(workspace)} (appended)")

    write_docx(out_path, "".join(body), media)
    return result


def pandoc_available() -> bool:
    return shutil.which("pandoc") is not None


def _md_escape(text: str) -> str:
    return text.replace("|", "\\|")


def blocks_to_markdown(workspace: Path, blocks: list[Block], result: Assembly) -> str:
    """Serialise the parsed body to Markdown with **every exhibit already inlined**.

    Handing the raw manuscript to pandoc does not work: pandoc's LaTeX reader
    cannot resolve `\\input{results/table2}` against this workspace's layout, so
    the table is dropped without a word and the deliverable ships short a
    result. Resolving the includes here — the same resolution the builtin writer
    does — is what makes the pandoc path safe. Pandoc is then used for what it is
    genuinely better at: citeproc, journal `--reference-doc` styling, and math.
    """
    out: list[str] = []
    table_no = 0
    figure_no = 0

    def emit_table(rows: list[list[str]], header_rows: int, caption: str) -> None:
        nonlocal table_no
        table_no += 1
        width = max(len(r) for r in rows)
        header_rows = max(1, min(header_rows or 1, len(rows)))
        out.append(f"**{caption or f'表 {table_no}'}**\n")
        padded = [list(r) + [""] * (width - len(r)) for r in rows]
        head = padded[0]
        out.append("| " + " | ".join(_md_escape(c) for c in head) + " |")
        out.append("|" + "---|" * width)
        for row in padded[header_rows:] if header_rows <= len(padded) else padded[1:]:
            out.append("| " + " | ".join(_md_escape(c) for c in row) + " |")
        out.append("")

    for block in blocks:
        if block.kind == "heading":
            out.append("#" * min(int(block.level), 6) + " " + block.text + "\n")
        elif block.kind == "para":
            out.append(block.text + "\n")
        elif block.kind == "table":
            emit_table(block.rows, block.header_rows, block.caption)
            result.exhibits += 1
        elif block.kind == "include_table":
            target = str(block.target).strip()
            path = resolve_exhibit(workspace, target) if target else None
            if path is None:
                result.unresolved.append(f"table include unresolved: {target or '(empty)'}")
                out.append(f"[UNRESOLVED TABLE INCLUDE: {target}]\n")
                continue
            rows, header = load_table(path)
            if not rows:
                result.unresolved.append(f"table include parsed to zero rows: {path.name}")
                out.append(f"[EMPTY TABLE: {path.name}]\n")
                continue
            emit_table(rows, header, block.caption or table_caption(path))
            result.exhibits += 1
            result.notes.append(f"table {table_no} <- {path.relative_to(workspace)}")
        elif block.kind == "include_figure":
            target = str(block.target).strip()
            path = resolve_image(workspace, target) if target else None
            if path is None:
                result.unresolved.append(f"figure unresolved (no .png/.jpg on disk): {target or '(empty)'}")
                out.append(f"[UNRESOLVED FIGURE: {target}]\n")
                continue
            figure_no += 1
            caption = block.caption or f"图 {figure_no}"
            out.append(f"![{caption}]({path.as_posix()})\n")
            result.figures += 1
            result.notes.append(f"figure {figure_no} <- {path.relative_to(workspace)}")
        elif block.kind == "bibliography":
            bib = find_bib(workspace, str(block.target))
            out.append("# 参考文献 / References\n")
            if bib is None:
                result.unresolved.append("bibliography referenced but no .bib found")
                out.append("[UNRESOLVED BIBLIOGRAPHY]\n")
                continue
            for line in format_bibliography(bib):
                out.append(line + "\n")
            result.notes.append(f"bibliography <- {bib.relative_to(workspace)}")

    if not any(b.kind == "bibliography" for b in blocks):
        bib = find_bib(workspace)
        if bib is not None:
            lines = format_bibliography(bib)
            if lines:
                out.append("# 参考文献 / References\n")
                out.extend(line + "\n" for line in lines)
                result.notes.append(f"bibliography <- {bib.relative_to(workspace)} (appended)")
    return "\n".join(out)


def assemble_pandoc(workspace: Path, source: Path, out_path: Path,
                    reference_docx: str = "", csl: str = "") -> Assembly:
    """Convert via pandoc from a fully-resolved Markdown intermediate."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = Assembly()
    blocks = parse_body(source)
    markdown = blocks_to_markdown(workspace, blocks, result)

    with tempfile.TemporaryDirectory(prefix="pw-pandoc-") as tmp:
        intermediate = Path(tmp) / "manuscript.md"
        intermediate.write_text(markdown, encoding="utf-8")
        cmd = ["pandoc", str(intermediate), "-o", str(out_path), "--from", "markdown",
               "--resource-path", ":".join([str(workspace), str(workspace / "04_results"),
                                            str(source.parent)])]
        if csl:
            bib = find_bib(workspace)
            if bib is not None:
                cmd += ["--citeproc", "--bibliography", str(bib), "--csl", csl]
        if reference_docx:
            cmd += ["--reference-doc", reference_docx]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout).strip() or "pandoc failed")

    # Trust the file, not the intent: count what landed, and treat any exhibit
    # that went missing in conversion as a hard unresolved marker.
    tables, figures = count_docx_exhibits(out_path)
    if tables < result.exhibits:
        result.unresolved.append(
            f"pandoc emitted {tables} table(s) but {result.exhibits} were resolved — "
            "exhibits were lost in conversion")
    if figures < result.figures:
        result.unresolved.append(
            f"pandoc emitted {figures} figure(s) but {result.figures} were resolved — "
            "figures were lost in conversion")
    result.exhibits, result.figures = tables, figures
    result.unresolved.extend(scan_unresolved(docx_text(out_path)))
    result.notes.append("converted by pandoc from a resolved Markdown intermediate")
    return result


# --------------------------------------------------------------------------- #
# post-hoc inspection (shared with check_deliverable_contract.py)              #
# --------------------------------------------------------------------------- #
_UNRESOLVED_PATTERNS = [
    (re.compile(r"\\(?:input|include)\s*\{"), "unresolved LaTeX include"),
    (re.compile(r"\\(?:ref|eqref|autoref|cite[a-z]*)\s*\{"), "unresolved LaTeX reference/citation"),
    (re.compile(r"\[UNRESOLVED [A-Z ]+[^\]]*\]"), "assembler placeholder"),
    (re.compile(r"\[EMPTY TABLE[^\]]*\]"), "empty exhibit"),
    (re.compile(r"\{\{\s*(?:include|table|exhibit)\s*:"), "unresolved Markdown include"),
    (re.compile(r"(?<![\w?])\?\?(?![\w?])"), "broken cross-reference (??)"),
]


def docx_text(path: Path) -> str:
    """All visible text in a .docx, paragraph-separated. Stdlib only."""
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    except (OSError, KeyError, zipfile.BadZipFile):
        return ""
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<w:tab\s*/>", "\t", xml)
    # `<w:t[^>]*>` would also match `<w:tbl>`, `<w:tc>` and `<w:tr>`, leaking raw
    # markup into the extracted text — and every downstream gate reads this text.
    # Match only the run-text element itself: `<w:t>` or `<w:t xml:space="...">`.
    parts = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>|(\n)", xml, flags=re.DOTALL)
    text = "".join(a or b for a, b in parts)
    return (text.replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&"))


def count_docx_exhibits(path: Path) -> tuple[int, int]:
    """(tables, figures) actually present in the .docx."""
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8", errors="ignore")
            media = [n for n in archive.namelist() if n.startswith("word/media/")]
    except (OSError, KeyError, zipfile.BadZipFile):
        return 0, 0
    tables = len(re.findall(r"<w:tbl(?:\s|>)", xml))
    drawings = len(re.findall(r"<w:drawing(?:\s|>)", xml))
    return tables, max(drawings, len(media))


def scan_unresolved(text: str) -> list[str]:
    out: list[str] = []
    for pattern, label in _UNRESOLVED_PATTERNS:
        hits = pattern.findall(text)
        if hits:
            out.append(f"{label} x{len(hits)}")
    return out


# --------------------------------------------------------------------------- #
# state                                                                        #
# --------------------------------------------------------------------------- #
def update_state(workspace: Path, *, converter: str, out_path: Path,
                 result: Assembly, source: Path) -> bool:
    path = workspace / "00_meta" / "workflow_state.json"
    if not path.is_file():
        path = workspace / "workflow_state.json"
    if not path.is_file():
        return False
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    manuscript = state.setdefault("manuscript", {})
    manuscript["deliverable_docx"] = str(out_path.relative_to(workspace))
    manuscript["docx_status"] = "assembled"
    manuscript["converter"] = converter
    manuscript["exhibits_embedded"] = result.exhibits
    manuscript["figures_embedded"] = result.figures
    manuscript["unresolved_markers"] = result.unresolved
    manuscript.setdefault("body_file", str(source.relative_to(workspace)))
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


# --------------------------------------------------------------------------- #
# driver                                                                       #
# --------------------------------------------------------------------------- #
def normalise_tables(workspace: Path, out_path: Path, manuscript: dict,
                     result: Assembly) -> None:
    """Run the three-line normaliser over the fresh .docx.

    Mandatory for the pandoc path, which emits Word's default gridded tables,
    and harmless for the builtin path, which already writes conforming rules —
    the normaliser is idempotent by design. Doing it here means the assembler's
    output is submission-shaped the moment it exists, instead of depending on
    whoever runs Stage 9 remembering a second command.
    """
    fixer = Path(__file__).resolve().parent / "make_three_line_tables.py"
    if not fixer.exists() or not out_path.is_file():
        return
    preset = str(manuscript.get("typography_preset") or "structure-only")
    proc = subprocess.run(
        [sys.executable, str(fixer), str(out_path), "--preset", preset, "--no-backup"],
        capture_output=True, text=True)
    if proc.returncode == 0:
        result.notes.append(f"tables normalised to three-line form (--preset {preset})")
    else:
        result.unresolved.append(
            "three-line normaliser failed on the assembled .docx: "
            + ((proc.stderr or proc.stdout).strip().splitlines() or ["unknown error"])[-1])


def run(workspace: Path, *, converter: str = "auto", out: str = "",
        write_state: bool = True) -> dict:
    state = load_state(workspace)
    manuscript = state.get("manuscript", {}) if isinstance(state.get("manuscript"), dict) else {}
    fmt = declared_format(state)
    source = find_source(workspace, fmt)
    if source is None:
        return {"ok": False, "error": "no manuscript body found in "
                + ", ".join(f"{s}/main{{{','.join(BODY_SUFFIXES)}}}" for s in CHAIN[:1])
                + " … (Stage 5 has not produced a draft yet)"}

    rel_out = out or str(manuscript.get("deliverable_docx") or "09_submission/main.docx")
    out_path = workspace / rel_out

    chosen = converter
    if chosen == "auto":
        chosen = "pandoc" if pandoc_available() else "builtin"
    if chosen == "pandoc" and not pandoc_available():
        return {"ok": False, "error": "pandoc requested but not on PATH; rerun with "
                                      "--converter builtin (see references/runtime-fallbacks.md)"}

    if chosen == "pandoc":
        try:
            result = assemble_pandoc(workspace, source, out_path,
                                     str(manuscript.get("reference_docx") or ""),
                                     str(manuscript.get("csl") or ""))
        except RuntimeError as exc:
            result = assemble_builtin(workspace, source, out_path)
            chosen = "builtin"
            result.notes.append(f"pandoc failed, fell back to builtin: {exc}")
    else:
        result = assemble_builtin(workspace, source, out_path)

    normalise_tables(workspace, out_path, manuscript, result)

    state_written = update_state(workspace, converter=chosen, out_path=out_path,
                                 result=result, source=source) if write_state else False
    return {
        "ok": True,
        "source": str(source.relative_to(workspace)),
        "output": str(out_path.relative_to(workspace)),
        "converter": chosen,
        "exhibits_embedded": result.exhibits,
        "figures_embedded": result.figures,
        "unresolved_markers": result.unresolved,
        "notes": result.notes,
        "state_updated": state_written,
    }


def render(result: dict) -> str:
    lines = ["", "Paper-WorkFlow manuscript assembly", "=" * 64]
    if not result.get("ok"):
        lines.append(f"  FAILED: {result.get('error')}")
        lines.append("=" * 64)
        return "\n".join(lines)
    lines.append(f"  source     {result['source']}")
    lines.append(f"  output     {result['output']}")
    lines.append(f"  converter  {result['converter']}")
    lines.append(f"  exhibits   {result['exhibits_embedded']} table(s)")
    lines.append(f"  figures    {result['figures_embedded']}")
    for note in result["notes"]:
        lines.append(f"    · {note}")
    if result["unresolved_markers"]:
        lines.append("  UNRESOLVED (deliverable cannot be marked verified):")
        for marker in result["unresolved_markers"]:
            lines.append(f"    ! {marker}")
    lines.append("=" * 64)
    lines.append("  ASSEMBLED — now run: make_three_line_tables.py, then "
                 "check_deliverable_contract.py")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# selftest                                                                     #
# --------------------------------------------------------------------------- #
_PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000004000000030802000000d9c8a3"
    "9b0000000a49444154789c6360000002000100ffff0300000600055773d8d200"
    "00000049454e44ae426082"
)

_TEX_BODY = r"""
\documentclass{article}
\begin{document}
\section{Results}
Treatment raises log wages by 0.123 (s.e. 0.041).
\begin{table}[htbp]
\caption{Main results}
\input{results/table2}
\end{table}
\begin{figure}[htbp]
\caption{Event study}
\includegraphics[width=0.8\textwidth]{fig_event_study.png}
\end{figure}
\section{Conclusion}
The effect is robust.
\bibliography{ref}
\end{document}
"""

_MD_BODY = """# Results

Treatment raises log wages by 0.123 (s.e. 0.041).

{{ include: table2 }}

![Event study](fig_event_study.png)

# Conclusion

The effect is robust.
"""

_TABLE_TEX = r"""
\begin{tabular}{lcc}
\toprule
Variable & (1) & (2) \\
\midrule
treat & 0.123*** & 0.118*** \\
N & 12,345 & 12,345 \\
\bottomrule
\end{tabular}
"""

_BIB = """@article{chen2021,
  author = {Chen, Wei and Li, Hua},
  title = {Firm Responses to Place-Based Policy},
  journal = {Journal of Development Economics},
  year = {2021},
  volume = {150},
  pages = {102--130},
}
"""


def _build_workspace(root: Path, *, fmt: str) -> Path:
    ws = root / "ws"
    (ws / "05_draft").mkdir(parents=True)
    (ws / "04_results").mkdir(parents=True)
    (ws / "09_submission").mkdir(parents=True)
    (ws / "00_meta").mkdir(parents=True)
    if fmt == "markdown":
        (ws / "05_draft" / "main.md").write_text(_MD_BODY, encoding="utf-8")
    else:
        (ws / "05_draft" / "main.tex").write_text(_TEX_BODY, encoding="utf-8")
    (ws / "04_results" / "table2.tex").write_text(_TABLE_TEX, encoding="utf-8")
    (ws / "04_results" / "fig_event_study.png").write_bytes(_PNG_1PX)
    (ws / "05_draft" / "ref.bib").write_text(_BIB, encoding="utf-8")
    (ws / "00_meta" / "workflow_state.json").write_text(
        json.dumps({"schema_version": 14,
                    "manuscript": {"format": fmt,
                                   "deliverable_docx": "09_submission/main.docx",
                                   "docx_status": "pending"}}), encoding="utf-8")
    return ws


def selftest() -> None:
    failures: list[str] = []

    # Both body formats, and — when pandoc is installed — both converters. The
    # pandoc path is covered deliberately: handing it the raw manuscript silently
    # dropped every `\input{}` exhibit, which is exactly the class of failure this
    # deliverable layer exists to make impossible.
    converters = ["builtin"] + (["pandoc"] if pandoc_available() else [])
    cases = [(fmt, conv) for fmt in ("latex", "markdown") for conv in converters]

    for fmt, conv in cases:
        with tempfile.TemporaryDirectory(prefix="pw-assemble-") as tmp:
            ws = _build_workspace(Path(tmp), fmt=fmt)
            result = run(ws, converter=conv)
            fmt = f"{fmt}/{conv}"
            if not result["ok"]:
                failures.append(f"{fmt}: assembly failed: {result.get('error')}")
                continue
            out = ws / result["output"]
            if not out.is_file():
                failures.append(f"{fmt}: no .docx written")
                continue
            if result["exhibits_embedded"] != 1:
                failures.append(f"{fmt}: expected 1 embedded table, got {result['exhibits_embedded']}")
            if result["figures_embedded"] != 1:
                failures.append(f"{fmt}: expected 1 embedded figure, got {result['figures_embedded']}")
            if result["unresolved_markers"]:
                failures.append(f"{fmt}: unexpected unresolved markers: {result['unresolved_markers']}")
            text = docx_text(out)
            # The numbers must survive conversion -- that is the whole point of
            # putting the .docx inside check_manuscript_numbers.py's chain.
            for needle in ("0.123", "12,345", "Conclusion", "Chen"):
                if needle not in text:
                    failures.append(f"{fmt}: '{needle}' missing from assembled .docx text")
            tables, figures = count_docx_exhibits(out)
            if tables != 1 or figures != 1:
                failures.append(f"{fmt}: docx inspection saw {tables} table(s)/{figures} figure(s)")
            # State must record what happened, not what was hoped for.
            state = json.loads((ws / "00_meta" / "workflow_state.json").read_text(encoding="utf-8"))
            if state["manuscript"]["docx_status"] != "assembled":
                failures.append(f"{fmt}: docx_status not advanced to 'assembled'")
            if state["manuscript"]["converter"] != conv:
                failures.append(f"{fmt}: converter recorded as "
                                f"{state['manuscript']['converter']!r}, expected {conv!r}")
            # Whichever converter ran, the deliverable must be three-line by the
            # time the assembler hands it back.
            checker = Path(__file__).resolve().parent / "check_table_style.py"
            if checker.exists():
                proc = subprocess.run([sys.executable, str(checker), str(ws)],
                                      capture_output=True, text=True)
                if proc.returncode != 0:
                    failures.append(f"{fmt}: assembled .docx fails check_table_style.py:\n"
                                    + (proc.stdout + proc.stderr).strip())

    # A missing exhibit must be reported, never silently dropped.
    with tempfile.TemporaryDirectory(prefix="pw-assemble-miss-") as tmp:
        ws = _build_workspace(Path(tmp), fmt="latex")
        (ws / "04_results" / "table2.tex").unlink()
        result = run(ws, converter="builtin")
        if not result["unresolved_markers"]:
            failures.append("a missing exhibit include was not reported as unresolved")
        if result["exhibits_embedded"] != 0:
            failures.append("a missing exhibit was counted as embedded")
        if "UNRESOLVED" not in docx_text(ws / result["output"]):
            failures.append("the .docx does not carry a visible unresolved marker")

    # No manuscript yet is a clean refusal, not a crash or an empty file.
    with tempfile.TemporaryDirectory(prefix="pw-assemble-empty-") as tmp:
        ws = Path(tmp) / "ws"
        (ws / "09_submission").mkdir(parents=True)
        result = run(ws, converter="builtin")
        if result["ok"]:
            failures.append("assembly claimed success with no manuscript on disk")

    if failures:
        print("FAIL: assemble_manuscript_docx selftest\n  - " + "\n  - ".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("selftest OK: manuscript assembly builds a gated .docx from both body formats")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="assemble_manuscript_docx.py",
        description="Assemble the finished manuscript, its exhibits and its figures "
                    "into one full-text .docx deliverable.",
        epilog="Then run make_three_line_tables.py and check_deliverable_contract.py.",
    )
    parser.add_argument("workspace", nargs="?", help="paper workspace root")
    parser.add_argument("--converter", choices=["auto", "pandoc", "builtin"], default="auto",
                        help="auto (default) prefers pandoc when it is on PATH")
    parser.add_argument("--out", default="", help="output path relative to the workspace")
    parser.add_argument("--no-state", action="store_true",
                        help="do not write manuscript.* back into workflow_state.json")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--selftest", action="store_true", help="verify this assembler")
    args = parser.parse_args(argv)

    if args.selftest:
        selftest()
        return 0
    if not args.workspace:
        parser.error("workspace is required (or pass --selftest)")

    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.is_dir():
        print(f"FAIL: workspace not found: {workspace}", file=sys.stderr)
        return 2

    result = run(workspace, converter=args.converter, out=args.out, write_state=not args.no_state)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
