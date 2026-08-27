#!/usr/bin/env python3
"""AI-use disclosure & authorship-integrity gate for a Paper-WorkFlow run.

Why this exists
---------------
This pipeline is an AI orchestrator: Stage 5 drafts with an LLM, Stage 6 polishes
with an LLM, and Stage 7 exists specifically to remove the *stylistic fingerprint*
of the LLM. Every major publisher (ICMJE, COPE, Elsevier, Springer Nature, Wiley,
SAGE, T&F, the AEA, and the 中文期刊 / 学位论文 side) now requires substantive
generative-AI assistance to be declared, requires that no AI system is an author,
and holds the human authors fully accountable for every word, number and citation.

The load-bearing invariant, and the reason this checker is a hard gate rather
than a paragraph of advice:

    Stage 7 removes the AI *accent*. It must never remove the AI *disclosure*.

A pipeline that automates de-AIGC without forcing a disclosure row has automated
the exact behaviour those policies are written to prevent. B4 below makes that
mechanical.

It reads `00_meta/ai_use_disclosure.md` (instantiated from
templates/ai_use_disclosure.md) plus, when present, `workflow_state.json`
(which stages are done), `00_meta/citation_integrity_log.md` (were AI-suggested
references ever resolved), and the manuscript author line. It is schema-tolerant:
a run that has not drafted anything yet is INFO, not failure.

Usage:
    python3 check_ai_disclosure.py <workspace>            # human report
    python3 check_ai_disclosure.py <workspace> --final    # Stage 9 strictness
    python3 check_ai_disclosure.py <workspace> --json     # machine readable
    python3 check_ai_disclosure.py --selftest             # verify this checker

Exit code is non-zero iff a blocking finding (B1-B8) is present.
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

REL_DISCLOSURE = "00_meta/ai_use_disclosure.md"
REL_STATE = "workflow_state.json"
REL_CITATION_LOG = "00_meta/citation_integrity_log.md"
MANUSCRIPT_CANDIDATES = (
    "07_dehumanize/main.tex",
    "06_polish/main.tex",
    "05_draft/main.tex",
)

PLACEHOLDER_RE = re.compile(r"<[^>\n]{0,120}>|\bTODO\b|\bTBD\b|（待填）|待填")

KNOWN_POLICY_FAMILIES = {
    "elsevier", "springer-nature", "wiley-sage-tf", "aea-econ", "cn-journal", "other",
}
VALID_CATEGORIES = {
    "literature", "code", "analysis", "text", "translation", "figure", "data",
}
# Categories whose output becomes a published number, citation, or artifact that
# nobody can sanity-check by reading. These may not be `unverified`.
MUST_VERIFY_CATEGORIES = {"code", "analysis", "data", "literature"}
VERIFICATION_TOKENS = {
    "rerun", "recomputed", "source-checked", "read-and-edited", "spot-checked",
    "unverified",
}
VALID_STAGES = {"0", "1", "1L", "2", "2.5", "3", "4", "5", "6", "7", "8", "9"}

# An AI system can never be an author. These tokens in an author line are the
# mechanical form of that violation.
AI_TOOL_TOKENS = (
    "chatgpt", "gpt-4", "gpt-5", "gpt4", "openai", "claude", "anthropic",
    "gemini", "bard", "llama", "copilot", "deepseek", "qwen", "kimi",
    "文心一言", "通义千问", "豆包", "人工智能助手",
)
# `Accountable` must be a person, not the orchestrator that produced the output.
NON_HUMAN_ACCOUNTABLE_RE = re.compile(
    r"^(?:the\s+)?(?:agent|sub-?agent|orchestrator|assistant|model|bot|ai|llm)\b"
    r"|agent[-_ ]?\d+|主代理|子代理|模型|智能体",
    re.IGNORECASE,
)

# Value-creation language in a `data` / `figure` row. Plotting a figure *from*
# results is fine; inventing the values is fabrication. Two tiers: words that are
# never innocent, and words that are innocent only when a source is named.
HARD_FABRICATION_RE = re.compile(
    r"fabricat|hallucinat|made[-\s]?up|虚构|编造|伪造|凭空",
    re.IGNORECASE,
)
SOFT_FABRICATION_RE = re.compile(
    r"(?:invent|generat|creat|fill(?:ed|ing)?\s+in|impute|synthes)\w*\s+"
    r"(?:[\w'’-]+\s+){0,3}"
    r"(?:data|datapoints?|values?|observations?|samples?|numbers?|coefficients?"
    r"|estimates?|results?|standard\s+errors?|series)"
    r"|补(?:全|齐|上).{0,6}(?:数据|观测|数值)",
    re.IGNORECASE,
)
# Evidence that a data/figure row is derivative rather than creative.
DERIVATIVE_RE = re.compile(
    r"\bfrom\b|\bbased on\b|\bplot|\brender|\bformat|\bexport|\bredraw|\blabel"
    r"|根据|依据|由.*绘制|绘制|导出|排版",
    re.IGNORECASE,
)

# Which words in the rendered statement count as covering a disclosed category.
CATEGORY_STATEMENT_MARKERS = {
    "text": ("draft", "wrote", "writing", "written", "copy-edit", "copyedit", "edit",
             "manuscript", "prose", "text", "撰写", "起草", "润色", "文字"),
    "code": ("code", "script", "program", "software", "代码", "脚本", "程序"),
    "analysis": ("analys", "analyz", "estimat", "regression", "statistical",
                 "分析", "估计", "回归"),
    "literature": ("literature", "reference", "bibliograph", "search", "screen",
                   "文献", "参考文献", "检索"),
    "translation": ("translat", "翻译", "译"),
    "figure": ("figure", "chart", "plot", "graph", "exhibit", "图", "图表"),
    "data": ("data", "dataset", "数据"),
}


# --------------------------------------------------------------------------- #
# parsing                                                                      #
# --------------------------------------------------------------------------- #
def _is_placeholder(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return True
    return bool(PLACEHOLDER_RE.search(v))


def split_sections(text: str) -> dict[str, str]:
    """Map each `## Heading` to its body text."""
    sections: dict[str, str] = {}
    current = "_preamble"
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*\S)\s*$", line)
        if m:
            sections[current] = "\n".join(buf)
            current = m.group(1).strip()
            buf = []
        else:
            buf.append(line)
    sections[current] = "\n".join(buf)
    return sections


def find_section(sections: dict[str, str], needle: str) -> str | None:
    for head, body in sections.items():
        if needle.lower() in head.lower():
            return body
    return None


def parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in body.splitlines():
        m = re.match(r"^-\s+([A-Za-z0-9_]+):\s*(.*?)\s*(?:<!--.*-->)?\s*$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def _table_rows(body: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= set("-: "):
            continue
        rows.append(cells)
    return rows


LEDGER_HEADER = ("stage", "category", "tool", "used for", "human verification",
                 "accountable", "disclose")


def parse_ledger(body: str) -> list[dict[str, str]]:
    """Return the ledger rows as dicts, skipping the header row."""
    rows = _table_rows(body)
    out: list[dict[str, str]] = []
    for cells in rows:
        low = [c.lower() for c in cells]
        if len(low) >= 3 and low[0] == "stage" and low[1] == "category":
            continue  # header
        if len(cells) < 7:
            continue
        out.append({
            "stage": cells[0],
            "category": cells[1].lower(),
            "tool": cells[2],
            "used_for": cells[3],
            "verification": cells[4],
            "accountable": cells[5],
            "disclose": cells[6].lower(),
        })
    return out


def _verification_token(value: str) -> str:
    v = (value or "").strip().lower()
    for tok in ("source-checked", "read-and-edited", "spot-checked", "recomputed",
                "unverified", "rerun"):
        if v.startswith(tok):
            return tok
    return v


# --------------------------------------------------------------------------- #
# validation                                                                   #
# --------------------------------------------------------------------------- #
def validate(
    text: str,
    *,
    final: bool = False,
    stage7_done: bool = False,
    drafting_stages_done: bool = False,
    unresolved_citations: int = 0,
    author_line: str = "",
) -> list[tuple[str, str]]:
    """Pure validation. Returns (level, message); FAIL is a blocking finding."""
    out: list[tuple[str, str]] = []
    sections = split_sections(text)

    # --- venue policy ------------------------------------------------------ #
    policy_body = find_section(sections, "Venue Policy")
    policy: dict[str, str] = {}
    if policy_body is None:
        out.append((FAIL, "B6 missing required section: ## 1. Venue Policy"))
    else:
        policy = parse_fields(policy_body)
        family = (policy.get("policy_family") or "").strip().lower()
        if _is_placeholder(family) or family not in KNOWN_POLICY_FAMILIES:
            level = FAIL if final else WARN
            out.append((level, f"B6 policy_family is unset or unknown: {family or '(empty)'} "
                               f"(expected one of {', '.join(sorted(KNOWN_POLICY_FAMILIES))})"))
        elif family == "other" and _is_placeholder(policy.get("policy_source", "")):
            out.append((FAIL, "B6 policy_family=other requires a policy_source URL or citation"))
        if final and _is_placeholder(policy.get("statement_placement", "")):
            out.append((FAIL, "B6 statement_placement is unfilled — the venue needs to know where "
                              "the declaration goes"))
        ai_author = (policy.get("ai_as_author") or "").strip().lower()
        if ai_author not in {"no", "n", "false", "否"}:
            out.append((FAIL, f"B1 ai_as_author must be 'no' (found: {ai_author or '(empty)'}); "
                              "an AI system can never be an author"))

    if author_line:
        hits = [t for t in AI_TOOL_TOKENS if t in author_line.lower()]
        if hits:
            out.append((FAIL, f"B1 manuscript author line names an AI system: {', '.join(hits)}"))

    # --- ledger ------------------------------------------------------------ #
    ledger_body = find_section(sections, "AI-Use Ledger")
    rows: list[dict[str, str]] = []
    if ledger_body is None:
        out.append((FAIL, "B6 missing required section: ## 2. AI-Use Ledger"))
    else:
        rows = parse_ledger(ledger_body)
        rows = [r for r in rows if not all(_is_placeholder(v) for v in r.values())]

    real_rows = [r for r in rows if not _is_placeholder(r["used_for"])]
    if not real_rows:
        if drafting_stages_done or stage7_done:
            out.append((WARN, "the ledger has no filled rows, but the drafting stages are done — "
                              "an AI pipeline that recorded no AI use is a bookkeeping failure"))
        else:
            out.append((INFO, "ledger is still empty (no drafting stage finished yet)"))

    disclosed_categories: set[str] = set()
    unverified_rows = 0
    for i, row in enumerate(real_rows, 1):
        tag = f"row {i} (stage {row['stage']}, {row['category']})"
        if row["stage"] not in VALID_STAGES and not _is_placeholder(row["stage"]):
            out.append((WARN, f"{tag}: '{row['stage']}' is not a pipeline stage "
                              f"({', '.join(sorted(VALID_STAGES))})"))
        if row["category"] not in VALID_CATEGORIES:
            out.append((WARN, f"{tag}: unknown category "
                              f"(expected {', '.join(sorted(VALID_CATEGORIES))})"))
        if _is_placeholder(row["tool"]) or not re.search(r"\d", row["tool"]):
            out.append((WARN, f"{tag}: tool/model needs a version or date, not just a vendor name "
                              f"({row['tool'] or '(empty)'})"))

        token = _verification_token(row["verification"])
        if token not in VERIFICATION_TOKENS:
            out.append((WARN, f"{tag}: verification '{row['verification']}' is not one of "
                              f"{', '.join(sorted(VERIFICATION_TOKENS))}"))
        if token == "unverified":
            unverified_rows += 1
            if row["category"] in MUST_VERIFY_CATEGORIES:
                out.append((FAIL, f"B3 {tag}: category '{row['category']}' is marked unverified — "
                                  "AI output that becomes a number, a citation or a dataset must be "
                                  "re-run, recomputed or source-checked by a human"))
        if token == "spot-checked" and not re.search(r"\d", row["verification"]):
            out.append((WARN, f"{tag}: spot-checked must state the sampling rate"))

        if row["category"] in {"data", "figure"}:
            used = row["used_for"]
            derivative = bool(DERIVATIVE_RE.search(used))
            if HARD_FABRICATION_RE.search(used) or (
                    SOFT_FABRICATION_RE.search(used) and not derivative):
                out.append((FAIL, f"B2 {tag}: '{used}' describes creating values "
                                  "rather than deriving them — that is fabrication, not assistance. "
                                  "If it was derived, name the source it was derived from."))
            elif not derivative:
                out.append((WARN, f"{tag}: a '{row['category']}' row should say what it was derived "
                                  "from (results file, cleaned data), so a referee can tell "
                                  "derivation from creation"))

        if row["disclose"].startswith("y"):
            disclosed_categories.add(row["category"])
            if final:
                who = row["accountable"]
                if _is_placeholder(who):
                    out.append((FAIL, f"B8 {tag}: no accountable human named"))
                elif NON_HUMAN_ACCOUNTABLE_RE.search(who):
                    out.append((FAIL, f"B8 {tag}: accountable='{who}' is an agent, not a person — "
                                      "an orchestrator cannot verify its own output"))

    # --- B4: the de-AIGC stage must disclose itself ------------------------- #
    if stage7_done:
        if any(r["stage"].strip() == "7" for r in real_rows):
            out.append((OKAY, "B4 the de-AIGC stage (Stage 7) discloses itself in the ledger"))
        else:
            out.append((FAIL, "B4 Stage 7 (de-AIGC) is done but has no ledger row — the stage whose "
                              "purpose is to remove the AI accent must not also remove the AI "
                              "disclosure"))

    # --- B7: AI-assisted literature with unresolved citations --------------- #
    if unresolved_citations > 0 and any(r["category"] == "literature" for r in real_rows):
        out.append((FAIL, f"B7 {unresolved_citations} citation(s) unresolved in "
                          f"{REL_CITATION_LOG} while the ledger records AI-assisted literature "
                          "work — AI-suggested references must resolve to real sources"))

    # --- statement ---------------------------------------------------------- #
    stmt_body = find_section(sections, "Rendered Statement")
    if stmt_body is None:
        out.append((FAIL, "B6 missing required section: ## 4. Rendered Statement"))
    else:
        stmt = "\n".join(l.lstrip("> ").strip() for l in stmt_body.splitlines()).strip()
        if _is_placeholder(stmt) or len(stmt) < 40:
            level = FAIL if final else INFO
            out.append((level, "B6 the rendered statement is still a placeholder — a template "
                               "cannot ship as a declaration"))
        else:
            low = stmt.lower()
            for cat in sorted(disclosed_categories):
                markers = CATEGORY_STATEMENT_MARKERS.get(cat, ())
                if markers and not any(m in low for m in markers):
                    out.append((FAIL, f"B5 category '{cat}' is disclosed in the ledger but does not "
                                      "appear in the rendered statement"))
            for cat, markers in CATEGORY_STATEMENT_MARKERS.items():
                if cat in disclosed_categories or cat in {"text", "data"}:
                    continue  # 'text'/'data' words are too common to test in reverse
                if any(m in low for m in markers[:2]):
                    out.append((WARN, f"the statement mentions '{cat}' but no ledger row discloses "
                                      "it (over-disclosure is not misconduct, but the two should agree)"))
            if final and not re.search(
                    r"responsib|accountab|reviewed and edited|承担|负责|审阅", stmt, re.IGNORECASE):
                out.append((FAIL, "B6 the statement must say the authors reviewed the output and "
                                  "take responsibility for the publication"))

    if not any(lvl == FAIL for lvl, _ in out):
        out.append((OKAY, f"AI-use disclosure complete: {len(real_rows)} ledger row(s), "
                          f"{len(disclosed_categories)} disclosed categor(ies), "
                          f"{unverified_rows} unverified"))
    return out


# --------------------------------------------------------------------------- #
# workspace mode                                                               #
# --------------------------------------------------------------------------- #
def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _unresolved_citations(workspace: Path) -> int:
    """Count unresolved-citation verdicts in the citation log.

    Table-aware on purpose: the log's own taxonomy table *defines* the verdict
    vocabulary, so a naive grep counts the legend as findings and blocks a clean
    run. Any table whose header names a definition column is skipped whole.
    """
    log = workspace / REL_CITATION_LOG
    if not log.exists():
        return 0
    text = log.read_text(encoding="utf-8", errors="replace")
    count = 0
    in_legend = False
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            in_legend = False  # a blank line or prose ends the current table
            continue
        cells = [c.strip().lower() for c in s.strip("|").split("|")]
        joined = " | ".join(cells)
        if joined and set(joined) <= set("-: |"):
            continue  # separator row keeps the current table's context
        header_like = {"verdict", "meaning", "status", "level", "gate consequence",
                       "definition", "含义", "说明"}
        if len(cells) >= 2 and cells[0] in {"verdict", "status", "level", "结论", "判定"}:
            in_legend = any(c in header_like for c in cells[1:])
            continue
        if in_legend:
            continue
        if PLACEHOLDER_RE.search(joined):
            continue  # an unfilled template row is not a finding
        # Hard-unresolved verdicts only. `to-verify` is an in-progress marker owned
        # by check_citation_integrity.py --final; this gate does not double-own it.
        if re.search(r"(?:^|[^a-z_])(retrieval_failed|unresolved|not_found"
                     r"|doi_unresolved|flagged|hallucinated)(?:[^a-z_]|$)", joined):
            count += 1
    return count


def _author_line(workspace: Path) -> str:
    for rel in MANUSCRIPT_CANDIDATES:
        p = workspace / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\\author\s*\{([^}]*)\}", text, re.DOTALL)
        if m:
            return m.group(1)
    return ""


def run(workspace: Path, *, final: bool = False) -> list[tuple[str, str]]:
    state = _read_json(workspace / REL_STATE)
    stages = state.get("stages", {}) if isinstance(state.get("stages"), dict) else {}
    stage7_done = str(stages.get("7_language_dehumanize", "")).lower() == "done"
    drafting_done = any(
        str(stages.get(k, "")).lower() == "done"
        for k in ("5_draft", "6_polish", "7_language_dehumanize")
    )

    doc = workspace / REL_DISCLOSURE
    if not doc.exists():
        if stage7_done or final:
            return [(FAIL, f"B4 no {REL_DISCLOSURE} on disk, but the pipeline has already "
                           "rewritten the manuscript for style — the AI-use ledger is missing "
                           "exactly where it is load-bearing")]
        if drafting_done:
            return [(WARN, f"no {REL_DISCLOSURE} yet, but a drafting stage is already done — "
                           "instantiate templates/ai_use_disclosure.md now, not at Stage 9")]
        return [(INFO, f"no {REL_DISCLOSURE} yet and no drafting stage finished — nothing to check")]

    return validate(
        doc.read_text(encoding="utf-8", errors="replace"),
        final=final,
        stage7_done=stage7_done,
        drafting_stages_done=drafting_done,
        unresolved_citations=_unresolved_citations(workspace),
        author_line=_author_line(workspace),
    )


def render(findings: list[tuple[str, str]], final: bool) -> str:
    mode = "final" if final else "per-stage"
    lines = ["", f"Paper-WorkFlow AI-use disclosure gate ({mode})", "=" * 68]
    for lvl, msg in findings:
        lines.append(f"[{lvl:<4}] {msg}")
    lines.append("=" * 68)
    fails = [m for lvl, m in findings if lvl == FAIL]
    lines.append(
        f"RESULT: {len(fails)} blocking finding(s) -> ai_disclosure.status=not_pass"
        if fails else "RESULT: AI-use disclosure verified -> ai_disclosure.status=pass")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# selftest                                                                     #
# --------------------------------------------------------------------------- #
GOOD = """# AI-Use Disclosure & Authorship Integrity

## 1. Venue Policy
- policy_family: elsevier
- policy_source:
- target_venue: Journal of Development Economics
- statement_placement: titled section before the reference list
- ai_as_author: no
- authors_take_responsibility: yes

## 2. AI-Use Ledger
| Stage | Category | Tool / model | Used for | Human verification | Accountable | Disclose |
|---|---|---|---|---|---|---|
| 1L | literature | Claude Opus 4.6 (2026-02) | screened 412 candidate papers into the corpus | source-checked | Wang Lei | yes |
| 3 | code | Claude Opus 4.6 (2026-02) | wrote the Callaway-Sant'Anna estimation script | rerun | Wang Lei | yes |
| 4 | figure | Claude Opus 4.6 (2026-02) | plotted the event-study figure from main_results.json | recomputed | Wang Lei | yes |
| 5 | text | Claude Opus 4.6 (2026-02) | drafted Sections 1-6 | read-and-edited | Wang Lei | yes |
| 7 | text | Claude Opus 4.6 (2026-02) | rewrote Sections 1-6 for readability | read-and-edited | Wang Lei | yes |

## 3. Prohibited-Use Screen
| # | Check | Verdict |
|---|---|---|
| B1 | No AI system appears as an author | pass |

## 4. Rendered Statement
> During the preparation of this work the authors used Claude Opus 4.6 (2026-02)
> to draft and copy-edit the manuscript, to screen the literature, to generate the
> estimation code, and to plot the exhibits. All estimation code was re-executed by
> the authors and every cited reference was checked against the original source.
> The authors reviewed and edited the content and take full responsibility for the
> content of the publication.

## 5. Deferred / Not Disclosed
| Stage | What | Why it is trivial |
|---|---|---|

## 6. State Sync
"""


def _selftest() -> int:
    def fails(text, **kw):
        return [m for lvl, m in validate(text, **kw) if lvl == FAIL]

    # 1. the golden document passes in both modes, including with Stage 7 done
    assert not fails(GOOD), fails(GOOD)
    assert not fails(GOOD, final=True, stage7_done=True), fails(GOOD, final=True, stage7_done=True)

    # 2. B1 — AI as author, both via the field and via the manuscript author line
    bad = GOOD.replace("- ai_as_author: no", "- ai_as_author: yes")
    assert any("B1" in m for m in fails(bad)), fails(bad)
    assert any("B1" in m for m in fails(GOOD, author_line="Wang Lei and ChatGPT")), "author line B1"
    assert not fails(GOOD, author_line="Wang Lei and Zhang Wei")

    # 3. B2 — a data row that generates values rather than deriving them
    fab = GOOD.replace(
        "| 4 | figure | Claude Opus 4.6 (2026-02) | plotted the event-study figure from main_results.json | recomputed | Wang Lei | yes |",
        "| 4 | data | Claude Opus 4.6 (2026-02) | generated the missing 2019 observations | spot-checked (10%) | Wang Lei | yes |")
    assert any("B2" in m for m in fails(fab)), fails(fab)
    # plotting *from* a results file is derivation, not fabrication
    assert not any("B2" in m for m in fails(GOOD))

    # 4. B3 — unverified code is blocking; unverified prose is not
    unver = GOOD.replace("| wrote the Callaway-Sant'Anna estimation script | rerun |",
                         "| wrote the Callaway-Sant'Anna estimation script | unverified |")
    assert any("B3" in m for m in fails(unver)), fails(unver)
    unver_text = GOOD.replace("| drafted Sections 1-6 | read-and-edited |",
                              "| drafted Sections 1-6 | unverified |")
    assert not any("B3" in m for m in fails(unver_text)), fails(unver_text)

    # 5. B4 — the de-AIGC stage must disclose itself. This is the point of the gate.
    no7 = "\n".join(l for l in GOOD.splitlines() if not l.startswith("| 7 |"))
    assert not fails(no7, stage7_done=False), "no stage-7 row is fine before stage 7 runs"
    assert any("B4" in m for m in fails(no7, stage7_done=True)), fails(no7, stage7_done=True)

    # 6. B5 — a disclosed category missing from the statement blocks. The
    #    statement here never mentions translation, so disclosing one must fail.
    mism = GOOD.replace(
        "| 5 | text |",
        "| 5 | translation | Claude Opus 4.6 (2026-02) | translated the abstract into English "
        "| read-and-edited | Wang Lei | yes |\n| 5 | text |")
    assert any("B5" in m and "translation" in m for m in fails(mism)), fails(mism)
    #    ...and the reverse (statement claims a category no row discloses) is a WARN, not a FAIL
    over = GOOD.replace("and to plot the exhibits.", "to plot the exhibits, and to translate the abstract.")
    assert not [m for m in fails(over) if "B5" in m], fails(over)
    assert any(l == WARN and "translation" in m for l, m in validate(over)), validate(over)

    # 7. B6 — placeholders and unknown policy families cannot ship at --final
    tmpl = GOOD.replace("- policy_family: elsevier", "- policy_family: <elsevier | cn-journal>")
    assert any("B6" in m for m in fails(tmpl, final=True)), fails(tmpl, final=True)
    assert not fails(tmpl), "an unset policy family is only a warning before --final"
    stub = re.sub(r"## 4\. Rendered Statement\n.*?\n## 5\.",
                  "## 4. Rendered Statement\n> <rendered statement>\n\n## 5.",
                  GOOD, flags=re.DOTALL)
    assert any("B6" in m for m in fails(stub, final=True)), fails(stub, final=True)
    noresp = re.sub(r"The authors reviewed and edited the content and take full responsibility for the\n> content of the publication\.",
                    "Thank you.", GOOD)
    assert any("B6" in m and "responsibility" in m for m in fails(noresp, final=True)), fails(noresp, final=True)

    # 8. B7 — AI-assisted literature work with unresolved citations
    assert any("B7" in m for m in fails(GOOD, unresolved_citations=3)), "B7"
    assert not fails(GOOD, unresolved_citations=0)

    # 9. B8 — an agent cannot be the accountable party at --final
    agent = GOOD.replace("| screened 412 candidate papers into the corpus | source-checked | Wang Lei |",
                         "| screened 412 candidate papers into the corpus | source-checked | agent-7 |")
    assert any("B8" in m for m in fails(agent, final=True)), fails(agent, final=True)
    assert not any("B8" in m for m in fails(agent)), "B8 is a --final rule"

    # 10. missing sections are structural failures
    for head in ("## 1. Venue Policy", "## 2. AI-Use Ledger", "## 4. Rendered Statement"):
        broken = GOOD.replace(head, head.replace("##", "###"))
        assert fails(broken), f"removing {head} must fail"

    # 11. an empty ledger warns once drafting is done, but never silently passes
    empty = re.sub(r"\| 1L \|.*?\n\| 7 \|[^\n]*\n", "", GOOD, flags=re.DOTALL)
    lv = validate(empty, drafting_stages_done=True)
    assert any(l == WARN and "bookkeeping" in m for l, m in lv), lv

    # 12. workspace mode
    with tempfile.TemporaryDirectory(prefix="aidisc-selftest-") as tmp:
        ws = Path(tmp)
        (ws / "00_meta").mkdir(parents=True)
        # empty run -> INFO only
        assert not [m for lvl, m in run(ws) if lvl == FAIL], run(ws)
        # stage 7 done but no disclosure file at all -> blocking
        (ws / REL_STATE).write_text(
            json.dumps({"stages": {"7_language_dehumanize": "done"}}), encoding="utf-8")
        assert any("B4" in m for lvl, m in run(ws) if lvl == FAIL), run(ws)
        # add the good ledger -> passes
        (ws / REL_DISCLOSURE).write_text(GOOD, encoding="utf-8")
        assert not [m for lvl, m in run(ws) if lvl == FAIL], run(ws)
        # an AI in the author line of the shipped manuscript -> blocking
        (ws / "07_dehumanize").mkdir()
        (ws / "07_dehumanize" / "main.tex").write_text(
            "\\author{Wang Lei \\and ChatGPT}\n", encoding="utf-8")
        assert any("B1" in m for lvl, m in run(ws) if lvl == FAIL), run(ws)
        (ws / "07_dehumanize" / "main.tex").write_text("\\author{Wang Lei}\n", encoding="utf-8")
        assert not [m for lvl, m in run(ws) if lvl == FAIL], run(ws)
        # unresolved citations in the log -> B7 (legend rows must not count)
        (ws / REL_CITATION_LOG).write_text(
            "| Verdict | Meaning |\n|---|---|\n| retrieval_failed | source exists but unchecked |\n",
            encoding="utf-8")
        assert _unresolved_citations(ws) == 0, "legend rows must not be counted as findings"
        (ws / REL_CITATION_LOG).write_text(
            "| Verdict | Meaning |\n|---|---|\n| retrieval_failed | source exists but unchecked |\n"
            "\n| ID | Cite | Status |\n|---|---|---|\n| C1 | smith2020 | retrieval_failed |\n",
            encoding="utf-8")
        assert _unresolved_citations(ws) == 1, _unresolved_citations(ws)
        assert any("B7" in m for lvl, m in run(ws) if lvl == FAIL), run(ws)

    # 13. the *shipped* citation-integrity template must not read as unresolved.
    #     A freshly instantiated log is all placeholders and legends; if this gate
    #     counted those it would block every clean run at Stage 1L.
    cit_tpl = Path(__file__).resolve().parent.parent / "templates" / "citation_integrity_log.md"
    if cit_tpl.exists():
        with tempfile.TemporaryDirectory(prefix="aidisc-cit-") as tmp:
            ws = Path(tmp)
            (ws / "00_meta").mkdir(parents=True)
            (ws / REL_CITATION_LOG).write_text(cit_tpl.read_text(encoding="utf-8"),
                                               encoding="utf-8")
            n = _unresolved_citations(ws)
            assert n == 0, f"fresh citation log reads as {n} unresolved citation(s)"

    # 14. the shipped template must be parseable by this checker (structure contract)
    tpl = Path(__file__).resolve().parent.parent / "templates" / "ai_use_disclosure.md"
    if tpl.exists():
        body = tpl.read_text(encoding="utf-8")
        secs = split_sections(body)
        for needle in ("Venue Policy", "AI-Use Ledger", "Rendered Statement"):
            assert find_section(secs, needle) is not None, f"template lost section {needle}"
        ledger = parse_ledger(find_section(secs, "AI-Use Ledger") or "")
        assert len(ledger) >= 4, f"template ledger rows: {len(ledger)}"
        assert {r["category"] for r in ledger} <= VALID_CATEGORIES, ledger
        assert any(r["stage"].strip() == "7" for r in ledger), "template must model the Stage 7 row"

    print("selftest OK: AI-use disclosure invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("workspace", nargs="?", help="path to the paper_workspace/<run> directory")
    p.add_argument("--final", action="store_true", help="Stage 9 strictness (no placeholders, named humans)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p.add_argument("--selftest", action="store_true", help="verify this checker on synthetic inputs")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.workspace:
        p.error("workspace path is required (or pass --selftest)")

    findings = run(Path(args.workspace).expanduser().resolve(), final=args.final)
    fails = [m for lvl, m in findings if lvl == FAIL]
    if args.json:
        print(json.dumps({"ok": not fails, "mode": "final" if args.final else "per-stage",
                          "findings": [{"level": l, "detail": m} for l, m in findings]},
                         ensure_ascii=False, indent=2))
    else:
        print(render(findings, args.final))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
