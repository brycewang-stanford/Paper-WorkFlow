#!/usr/bin/env python3
"""Cross-reference / internal-contract linter for the Paper-WorkFlow skill.

The skill is a web of ~30 mutually referential files: SKILL.md points at
references and templates, references invoke checker scripts by command line,
the gate checkers hard-code workspace artifact paths, and `init_workspace.sh`
lays down the workspace skeleton those paths live in. `validate_skill.py`
already guards two slices of that web — markdown `[text](link)` targets resolve,
and required template/reference markers are present — but it does NOT guard the
slices most likely to rot silently when the prose is edited:

  - an inline ``python3 scripts/foo.py`` / ``bash assets/bar.sh`` command in the
    prose that names a skill-repo script which has since been renamed or moved
    (inline code is invisible to the markdown-link checker);
  - a backticked or bare ``references/foo.md`` / ``templates/bar.md`` path
    mention (not written as a markdown link) that points at a file that does
    not exist;
  - a workspace artifact path hard-coded as a default in a gate checker whose
    top-level directory is not even part of the skeleton ``init_workspace.sh``
    creates (so the checker would forever look in a place nothing populates);
  - a new ``scripts/check_*.py`` checker that was added but never wired into the
    master harness ``validate_skill.py`` (so it silently never runs in CI).

This linter makes those four invariants mechanical. It is read-only and static
(no workspace, no network); it parses the skill's own tracked files. Two agents
editing this tree in parallel is exactly the regime where this drift appears, so
the check is preventive, not corrective: it should normally pass.

Usage:
    python3 scripts/check_cross_references.py            # human report
    python3 scripts/check_cross_references.py --json     # machine readable
    python3 scripts/check_cross_references.py --selftest  # verify this checker
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FAIL = "FAIL"
WARN = "WARN"
OKAY = "OK"

# Directories whose contents are skill-repo files (a command/path naming one of
# these must resolve on disk). Anything else is treated as a runtime path inside
# a *generated* paper workspace and is intentionally not checked here.
REPO_TOP_DIRS = {"scripts", "evals", "templates", "assets", "references"}

# Bare top-level scripts that the prose may invoke by name.
REPO_TOP_FILES = {"validate_skill.py", "build_notebook.py", "build_pptx.py"}

# A path segment like "03_analysis" / "00_meta" marks a *workspace-runtime* path
# (a file inside a user's generated workspace, not a skill-repo file).
_WORKSPACE_SEG_RE = re.compile(r"^\d\d_")

# Generated workspace scripts the prose tells the *run* to execute; never repo files.
WORKSPACE_RUNTIME_FILES = {"run_all.sh"}

# Inline shell commands: `python3 <path>` or `bash <path>` ending in .py/.sh.
_CMD_RE = re.compile(r"(?:python3|bash)\s+([A-Za-z0-9_./\-]+\.(?:py|sh))")

# Bare/backticked skill-repo path mentions anywhere in prose.
_REPO_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_./-])"
    r"((?:scripts|evals|templates|assets|references)/[A-Za-z0-9_./\-]+"
    r"\.(?:py|sh|md|json|svg|png|tex|ipynb))"
)

# Workspace artifact paths hard-coded as string literals in the gate checkers.
_WS_ARTIFACT_RE = re.compile(r"['\"](\d\d_[A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)*\.(?:md|json))['\"]")

# Metavariable placeholder filename stems (e.g. `scripts/X.py`, `templates/Y.md`):
# docs legitimately use these to illustrate a pattern, not to name a real file.
_PLACEHOLDER_STEM_RE = re.compile(r"^[A-Z]$")


def _is_placeholder_path(path: str) -> bool:
    """A path that is obviously an illustrative metavariable, not a real file."""
    if any(ch in path for ch in "<>") or "..." in path or "…" in path:
        return True
    return bool(_PLACEHOLDER_STEM_RE.match(Path(path).stem))


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
        lines = ["", "Paper-WorkFlow cross-reference contract", "=" * 64]
        for lvl, chk, det in self.rows:
            lines.append(f"[{lvl:<4}] {chk:<{width}}  {det}")
        lines.append("=" * 64)
        if self.failures:
            lines.append(f"RESULT: {len(self.failures)} contract violation(s) -> internal references NOT consistent")
        else:
            lines.append("RESULT: internal references are mutually consistent")
        return "\n".join(lines)


def _strip_repo_prefix(path: str) -> str:
    """`skills/69-Paper-WorkFlow/scripts/x.py` (subagent-context absolute) -> `scripts/x.py`."""
    marker = "69-Paper-WorkFlow/"
    if marker in path:
        return path.split(marker, 1)[1]
    return path


def _is_repo_command_target(path: str) -> bool:
    head = path.split("/", 1)[0]
    if path in REPO_TOP_FILES:
        return True
    if head in REPO_TOP_DIRS:
        return True
    return False


def _is_workspace_runtime(path: str) -> bool:
    head = path.split("/", 1)[0]
    return bool(_WORKSPACE_SEG_RE.match(head)) or path in WORKSPACE_RUNTIME_FILES


def _md_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if ".git" in rel.parts or "paper_workspace" in rel.parts or "__pycache__" in rel.parts:
            continue
        out.append(p)
    return out


def _skeleton_dirs(init_script: Path) -> set[str]:
    """Parse the `mkdir -p "$workspace"/{a,b/c,...}` skeleton from init_workspace.sh,
    returning every declared dir plus all ancestor prefixes (and ".")."""
    text = init_script.read_text(encoding="utf-8")
    m = re.search(r'mkdir\s+-p\s+"\$workspace"/\{([^}]*)\}', text)
    dirs: set[str] = {"."}
    if not m:
        return dirs
    for entry in m.group(1).split(","):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("/")
        for i in range(1, len(parts) + 1):
            dirs.add("/".join(parts[:i]))
    return dirs


def check_tree(root: Path) -> Report:
    rep = Report()

    md_files = _md_files(root)

    # --- invariant 1: inline python3/bash commands name real repo scripts -----
    cmd_problems: list[str] = []
    cmd_checked = 0
    for path in md_files:
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        for m in _CMD_RE.finditer(text):
            target = _strip_repo_prefix(m.group(1))
            if _is_placeholder_path(target) or _is_workspace_runtime(target):
                continue
            if not _is_repo_command_target(target):
                continue
            cmd_checked += 1
            if not (root / target).exists():
                cmd_problems.append(f"{rel}: `{m.group(1)}` -> missing {target}")
    if cmd_problems:
        rep.add(FAIL, "inline_commands", f"{len(cmd_problems)} command(s) name a missing script:\n    "
                + "\n    ".join(cmd_problems))
    else:
        rep.add(OKAY, "inline_commands", f"{cmd_checked} inline repo command(s) resolve")

    # --- invariant 2: bare/backticked repo-path mentions resolve --------------
    path_problems: list[str] = []
    path_checked = 0
    for path in md_files:
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        seen: set[str] = set()
        for m in _REPO_PATH_RE.finditer(text):
            target = m.group(1)
            if target in seen:
                continue
            seen.add(target)
            if _is_placeholder_path(target):
                continue
            path_checked += 1
            if not (root / target).exists():
                path_problems.append(f"{rel}: `{target}` does not exist")
    if path_problems:
        rep.add(FAIL, "repo_path_mentions", f"{len(path_problems)} mention(s) of a missing repo file:\n    "
                + "\n    ".join(path_problems))
    else:
        rep.add(OKAY, "repo_path_mentions", f"{path_checked} repo-path mention(s) resolve")

    # --- invariant 3: checker workspace paths live in the init skeleton -------
    init_script = root / "assets" / "init_workspace.sh"
    if not init_script.exists():
        rep.add(FAIL, "skeleton", "assets/init_workspace.sh missing; cannot verify workspace paths")
    else:
        skeleton = _skeleton_dirs(init_script)
        checker_files = [
            root / "scripts" / "check_workspace_gates.py",
            root / "scripts" / "check_citation_integrity.py",
        ]
        ws_problems: list[str] = []
        ws_checked = 0
        for cf in checker_files:
            if not cf.exists():
                continue
            ctext = cf.read_text(encoding="utf-8")
            for m in _WS_ARTIFACT_RE.finditer(ctext):
                artifact = m.group(1)
                parent = str(Path(artifact).parent)
                ws_checked += 1
                if parent not in skeleton:
                    ws_problems.append(f"{cf.name}: '{artifact}' -> dir '{parent}' not in init skeleton")
        if ws_problems:
            rep.add(FAIL, "workspace_paths", f"{len(ws_problems)} checker path(s) outside the init skeleton:\n    "
                    + "\n    ".join(ws_problems))
        else:
            rep.add(OKAY, "workspace_paths", f"{ws_checked} checker workspace path(s) live in the init skeleton")

    # --- invariant 4: every checker is wired into the master harness ----------
    validate = root / "validate_skill.py"
    if not validate.exists():
        rep.add(FAIL, "harness_wiring", "validate_skill.py missing")
    else:
        vtext = validate.read_text(encoding="utf-8")
        # A checker cannot make its own wiring a precondition for passing (that
        # is a bootstrap paradox: a freshly added checker could never be shipped
        # green before it is wired). So self is a WARN, every *other* orphan is a
        # FAIL. Once this checker is wired, the WARN clears on its own.
        self_name = Path(__file__).name
        orphans: list[str] = []
        wired = 0
        self_unwired = False
        for checker in sorted((root / "scripts").glob("check_*.py")):
            name = checker.name
            if name in vtext:
                wired += 1
            elif name == self_name:
                self_unwired = True
            else:
                orphans.append(f"scripts/{name}")
        if orphans:
            rep.add(FAIL, "harness_wiring", f"{len(orphans)} checker(s) not referenced by validate_skill.py "
                    f"(would never run in CI): {', '.join(orphans)}")
        elif self_unwired:
            rep.add(WARN, "harness_wiring", f"all peer checkers wired; this linter (scripts/{self_name}) "
                    "is not yet wired into validate_skill.py")
        else:
            rep.add(OKAY, "harness_wiring", f"all {wired} scripts/check_*.py are wired into validate_skill.py")

    return rep


# --------------------------------------------------------------------------- #
# selftest                                                                     #
# --------------------------------------------------------------------------- #
def _selftest() -> int:
    """Build a synthetic skill tree with injected drift; assert each invariant fires,
    then a clean tree passes."""
    with tempfile.TemporaryDirectory(prefix="xref-selftest-") as tmp:
        root = Path(tmp)

        def write(rel: str, content: str) -> None:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

        # minimal but real skeleton: a checker, an init script, validate_skill.py
        write(
            "assets/init_workspace.sh",
            'mkdir -p "$workspace"/{00_meta/handoff,02_data/raw,03_analysis/results,logs}\n',
        )
        # a gate checker with one good path and one orphan path
        write(
            "scripts/check_workspace_gates.py",
            'A = "00_meta/stage_passport.md"\nB = "99_void/ghost.md"\n',
        )
        # validate_skill.py wires check_workspace_gates.py but NOT check_orphan.py
        write("validate_skill.py", "subprocess.run(['check_workspace_gates.py'])\n")
        write("scripts/check_orphan.py", "# a checker nobody wired\n")
        # SKILL.md with: a good command, a broken command, a good mention, a broken mention,
        # and a workspace-runtime command that must be IGNORED.
        write(
            "SKILL.md",
            "Run `python3 scripts/check_workspace_gates.py`.\n"
            "Run `python3 scripts/missing_checker.py`.\n"
            "See `references/real.md` and `templates/ghost.md`.\n"
            "The run executes `python3 03_analysis/estimate.py` and `bash run_all.sh`.\n"
            "Docs illustrate with `scripts/X.py`, `references/<name>.md`, `python3 templates/Y.py`.\n",
        )
        write("references/real.md", "real\n")

        rep = check_tree(root)
        hits = {chk for lvl, chk, _ in rep.rows if lvl == FAIL}
        for expected in ("inline_commands", "repo_path_mentions", "workspace_paths", "harness_wiring"):
            assert expected in hits, f"selftest: expected {expected} to FAIL; got {hits}"
        blob = rep.render()
        # the workspace-runtime command/path must NOT have been flagged
        assert "estimate.py" not in blob, "selftest: workspace-runtime command wrongly flagged"
        assert "run_all.sh" not in blob, "selftest: workspace-runtime script wrongly flagged"
        # metavariable placeholders must NOT have been flagged
        for ph in ("scripts/X.py", "<name>.md", "templates/Y.py"):
            assert ph not in blob, f"selftest: placeholder {ph} wrongly flagged"

        # --- now repair every injected fault; the clean tree must pass --------
        write("scripts/missing_checker.py", "# now exists\n")
        write("templates/ghost.md", "now real\n")
        write("scripts/check_workspace_gates.py", 'A = "00_meta/stage_passport.md"\nB = "03_analysis/results/main.json"\n')
        write(
            "validate_skill.py",
            "subprocess.run(['check_workspace_gates.py', 'check_orphan.py', "
            "'missing_checker.py'])\n",
        )
        rep2 = check_tree(root)
        assert not rep2.failures, f"selftest: repaired tree should pass, got {rep2.failures}"

    print("selftest OK: cross-reference contract invariants hold")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-reference / internal-contract linter for Paper-WorkFlow.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--selftest", action="store_true", help="verify this checker on a synthetic tree")
    args = parser.parse_args()

    if args.selftest:
        return _selftest()

    rep = check_tree(ROOT)
    if args.json:
        print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(rep.render())
    return 1 if rep.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
