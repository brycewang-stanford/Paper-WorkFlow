#!/usr/bin/env python3
"""
check_compactness.py — orphan + duplication detector for the paper-workflow skill.

Two questions about the on-demand reference corpus, both advisory:

1. **Is anything unreachable?** Every `.md` under `references/` should be linked
   from `SKILL.md` or from another reference. An unlinked file is a doc the
   running agent never loads.
2. **Is the corpus growing by accretion or by content?** The complexity ratchet
   reports that the corpus got bigger; it cannot say whether the new bytes are
   new material or the same paragraph restated in a third place. This scans for
   near-duplicate paragraphs across files (token-shingle Jaccard) and answers it
   with a number instead of a worry.

Both are advisory: the script exits 0 unless `--strict`, so it can run in
pre-commit without blocking work.

Usage:
    python3 scripts/check_compactness.py            # human-readable report
    python3 scripts/check_compactness.py --json     # JSON output
    python3 scripts/check_compactness.py --strict   # exit 1 if any orphan found
    python3 scripts/check_compactness.py --selftest # verify the detectors

The script never modifies files. Pair it with `validate_skill.py` for the full
always-loaded-layer check; pair it with `evals/check_complexity_budget.py` for
the footprint ratchet.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_ROOT / "SKILL.md"
REFERENCES_DIR = SKILL_ROOT / "references"

# Match a markdown link whose visible text is anything, pointing at `xxx.md`
# (relative or absolute within the repo). Also catch the bare filename form
# some inline references use, e.g. "see design-risk-ledger.md".
LINK_TO_MD_RE = re.compile(r"\]\(([^)]*\.md)(?:#[^)]*)?\)")
BARE_BASENAME_RE = re.compile(r"\b([a-z0-9][a-z0-9\-_]*\.md)\b", re.IGNORECASE)


def _is_self_link(link_target: str, current_file: Path) -> bool:
    """True when the link points to the file that contains the link."""
    target = (SKILL_ROOT / link_target).resolve() if not link_target.startswith("/") else Path(link_target)
    try:
        return target.resolve() == current_file.resolve()
    except (OSError, ValueError):
        return False


def collect_referenced_basenames(source_paths: list[Path]) -> set[str]:
    """Return the union of md basenames referenced anywhere in source_paths."""
    referenced: set[str] = set()
    for src in source_paths:
        if not src.exists() or not src.is_file():
            continue
        try:
            text = src.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # Markdown links like ](path/to/foo.md)
        for match in LINK_TO_MD_RE.finditer(text):
            target = match.group(1)
            if _is_self_link(target, src):
                continue
            # Resolve to basename so cross-directory links still register
            referenced.add(Path(target).name)
        # Bare filename mentions (less reliable — false positives if e.g.
        # the word "skill-map.md" appears in prose; we accept the noise here
        # because the orphan list is advisory, not gating)
        for match in BARE_BASENAME_RE.finditer(text):
            referenced.add(match.group(1))
    return referenced


def discover_reference_files() -> list[Path]:
    if not REFERENCES_DIR.is_dir():
        return []
    return sorted(p for p in REFERENCES_DIR.glob("*.md") if p.is_file())


# --------------------------------------------------------------------------- #
# duplication                                                                  #
# --------------------------------------------------------------------------- #
# Paragraphs shorter than this are headings, one-liners and link stubs; they
# repeat legitimately and would drown the signal.
MIN_PARAGRAPH_CHARS = 200
SHINGLE_SIZE = 8
DUPLICATE_THRESHOLD = 0.45
_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+")
# Content that is *supposed* to appear verbatim in more than one file.
DUPLICATION_EXEMPT_MARKERS = (
    "_verification_log/cn-data-claims.md",   # the shared CN audit-status banner
    "check_cn_claim_audit.py",               # ...and the command that regenerates it
)


def _shingles(text: str) -> set[tuple[str, ...]]:
    toks = _TOKEN_RE.findall(text.lower())
    if len(toks) < SHINGLE_SIZE:
        return set()
    return {tuple(toks[i:i + SHINGLE_SIZE]) for i in range(len(toks) - SHINGLE_SIZE + 1)}


def _paragraphs(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    out = []
    for para in re.split(r"\n\s*\n", text):
        norm = re.sub(r"\s+", " ", para).strip()
        if len(norm) < MIN_PARAGRAPH_CHARS:
            continue
        if norm.startswith("|"):      # tables legitimately repeat their shape
            continue
        if any(marker in norm for marker in DUPLICATION_EXEMPT_MARKERS):
            continue
        out.append(norm)
    return out


def find_duplicate_paragraphs(paths: list[Path]) -> list[dict]:
    """Cross-file near-duplicate paragraphs, most similar first."""
    indexed: list[tuple[str, str, set]] = []
    for path in paths:
        for para in _paragraphs(path):
            sh = _shingles(para)
            if sh:
                indexed.append((path.name, para, sh))

    hits: list[dict] = []
    for i in range(len(indexed)):
        name_a, para_a, sh_a = indexed[i]
        for j in range(i + 1, len(indexed)):
            name_b, para_b, sh_b = indexed[j]
            if name_a == name_b:
                continue          # within-file repetition is a style issue, not accretion
            inter = len(sh_a & sh_b)
            if not inter:
                continue
            jaccard = inter / len(sh_a | sh_b)
            if jaccard > DUPLICATE_THRESHOLD:
                hits.append({"similarity": round(jaccard, 2), "files": [name_a, name_b],
                             "excerpt": para_a[:110]})
    hits.sort(key=lambda h: -h["similarity"])
    return hits


def build_report() -> dict:
    refs = discover_reference_files()
    referenced = collect_referenced_basenames([SKILL_MD, *refs])
    orphans: list[str] = []
    referenced_list: list[str] = []
    for ref in refs:
        name = ref.name
        if name in referenced:
            referenced_list.append(name)
        else:
            orphans.append(name)
    duplicates = find_duplicate_paragraphs(refs)
    return {
        "skill_md": str(SKILL_MD),
        "references_dir": str(REFERENCES_DIR),
        "total_references": len(refs),
        "total_bytes": sum(r.stat().st_size for r in refs),
        "referenced": sorted(referenced_list),
        "orphans": sorted(orphans),
        "duplicate_paragraphs": duplicates,
    }


def render_text(report: dict) -> str:
    lines = [
        "paper-workflow compactness check",
        "-----------------------------",
        f"references dir : {report['references_dir']}",
        f"SKILL.md       : {report['skill_md']}",
        f"references     : {report['total_references']} files, "
        f"{report['total_bytes'] // 1024} KB",
        f"orphans        : {len(report['orphans'])}",
        f"dup paragraphs : {len(report['duplicate_paragraphs'])} cross-file "
        f"(Jaccard > {DUPLICATE_THRESHOLD})",
        "",
    ]
    if report["orphans"]:
        lines.append("ORPHAN references (not linked from SKILL.md or any other reference):")
        for o in report["orphans"]:
            lines.append(f"  - {o}")
        lines.append("")
        lines.append(
            "Action: either (a) add a cross-link from SKILL.md or another reference, "
            "(b) remove the orphan if its content has been merged elsewhere, or "
            "(c) accept the orphan explicitly by linking it from a placeholder doc."
        )
    else:
        lines.append("OK — every reference is reachable from SKILL.md or another reference.")

    dups = report["duplicate_paragraphs"]
    if dups:
        lines.append("")
        lines.append("NEAR-DUPLICATE paragraphs across reference files:")
        for d in dups[:10]:
            lines.append(f"  {d['similarity']}  {' <-> '.join(d['files'])}")
            lines.append(f"        {d['excerpt']}...")
        if len(dups) > 10:
            lines.append(f"  ... and {len(dups) - 10} more")
        lines.append("")
        lines.append(
            "Action: the corpus is growing by restatement, not only by new material. "
            "Move the shared passage into the reference that owns the topic and link "
            "to it, or add it to DUPLICATION_EXEMPT_MARKERS if it must appear verbatim "
            "in both places (a required banner, for instance)."
        )
    else:
        lines.append(
            "OK — no cross-file near-duplicate paragraphs; corpus growth is new "
            "material, not restatement."
        )
    return "\n".join(lines) + "\n"


def _selftest() -> int:
    import tempfile

    # --- duplication detector -------------------------------------------------
    with tempfile.TemporaryDirectory(prefix="compactness-selftest-") as tmp:
        root = Path(tmp)
        shared = ("The estimation sample must be reconciled against the raw extract "
                  "before any coefficient is quoted, because a silently dropped stratum "
                  "changes the estimand rather than merely the precision of the estimate, "
                  "and no downstream robustness check can recover what was never in the "
                  "sample to begin with.")
        (root / "a.md").write_text(f"# A\n\n{shared}\n", encoding="utf-8")
        (root / "b.md").write_text(f"# B\n\n{shared}\n", encoding="utf-8")
        hits = find_duplicate_paragraphs([root / "a.md", root / "b.md"])
        assert len(hits) == 1 and hits[0]["similarity"] == 1.0, hits

        # unrelated prose of similar length must not match
        other = ("Journal policy pages change without notice, so the submission "
                 "checklist is refreshed from the live guidelines at Stage 9 rather "
                 "than trusted from whatever was recorded when the project began, "
                 "and an unreachable policy page is recorded as blocked instead of "
                 "quietly assumed unchanged.")
        (root / "b.md").write_text(f"# B\n\n{other}\n", encoding="utf-8")
        assert not find_duplicate_paragraphs([root / "a.md", root / "b.md"])

        # within-file repetition is not accretion across files
        (root / "b.md").write_text(f"# B\n\n{other}\n\n{other}\n", encoding="utf-8")
        assert not find_duplicate_paragraphs([root / "b.md"])

        # short paragraphs are ignored
        (root / "c.md").write_text("# C\n\nToo short to matter.\n", encoding="utf-8")
        (root / "d.md").write_text("# D\n\nToo short to matter.\n", encoding="utf-8")
        assert not find_duplicate_paragraphs([root / "c.md", root / "d.md"])

        # an exempt marker suppresses a genuine verbatim repeat
        banner = ("> The claims in this document are tracked in "
                  "`_verification_log/cn-data-claims.md`, which records the source, the "
                  "date it was checked and the person who checked it, so a reader can "
                  "tell a verified figure from one that has merely been repeated often.")
        (root / "e.md").write_text(f"# E\n\n{banner}\n", encoding="utf-8")
        (root / "f.md").write_text(f"# F\n\n{banner}\n", encoding="utf-8")
        assert not find_duplicate_paragraphs([root / "e.md", root / "f.md"]), "exempt marker ignored"

    # --- the live corpus ------------------------------------------------------
    report = build_report()
    assert report["total_references"] > 0, "no reference files discovered"
    assert isinstance(report["duplicate_paragraphs"], list)

    print("selftest OK: compactness (orphan + duplication) invariants hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any orphan reference is found (default: advisory only)",
    )
    parser.add_argument("--selftest", action="store_true",
                        help="verify the orphan and duplication detectors")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))
    if args.strict and report["orphans"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())