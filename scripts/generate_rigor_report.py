#!/usr/bin/env python3
"""Generate RIGOR.md — the public gate-coverage report for Paper-WorkFlow.

Why this exists
---------------
The competitive analysis in RELATED-WORK.md found that our two direct peers
(K-Dense `scientific-agent-skills`, Orchestra `AI-Research-SKILLs`) have no
executable research-rigor gate: K-Dense ships only a *security* scanner, and
Orchestra's "ARA Seal" rigor layer is markdown the LLM self-grades. Our
differentiator is the opposite — every load-bearing invariant about a paper run,
and about this skill package itself, is enforced by a script with a built-in
selftest, so a violation produces a non-zero exit, not a softly-worded warning.

That advantage is invisible unless we make it legible. K-Dense earns trust with an
auto-generated SECURITY.md + a live CI badge. This tool is the analog they cannot
produce: it enumerates every rigor checker, runs each checker's own selftest to
*prove the rigor machinery is sound*, and writes the result to a public RIGOR.md.
The report is the credibility artifact; the exit code makes it CI-enforceable.

What it is NOT
--------------
It does not score a paper run (check_workspace_gates does that for a workspace) and
it does not score this skill's quality (score_skill does that). It answers one
question — "are all of this skill's rigor checkers themselves passing their
selftests right now?" — and renders the answer as a trust badge.

Usage
-----
    python3 scripts/generate_rigor_report.py            # run all selftests, write RIGOR.md
    python3 scripts/generate_rigor_report.py --check     # verify RIGOR.md is up to date (CI)
    python3 scripts/generate_rigor_report.py --json       # machine-readable result
    python3 scripts/generate_rigor_report.py --date 2026-06-23   # pin the date (deterministic)

Exit code is non-zero iff a checker fails its selftest, an expected checker is
missing, a checker exists but is not registered (drift), or --check finds RIGOR.md
stale. The committed report body is deterministic apart from one dated line, so
--check can diff a fresh run against the on-disk file.
"""

from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPORT_PATH = ROOT / "RIGOR.md"
DATE_MARKER = "_Generated "  # the single volatile line; excluded from --check diff

# Layers a checker belongs to.
RUNTIME = "Run-time gate (verifies a paper run)"
MAINT = "Maintenance gate (verifies this skill package)"

# Curated registry. Explicit beats auto-discovery here: it lets us state precisely
# what each checker enforces, and a registry/disk mismatch is itself a drift signal
# (see _drift below). `argv` is appended to `python3 <path>`; most selftest, smoke
# runs bare. Keep this ordered the way the report should read.
REGISTRY: list[dict] = [
    {
        "path": "scripts/check_workspace_gates.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Method Gate / Draft Quality Gate / replication pack / claim-integrity / "
            "design-risk: a gate marked `pass` must have its evidence on disk, and "
            "ordering holds (quality gate never looser than the method gate)."
        ),
    },
    {
        "path": "scripts/check_method_gate_card.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Method Gate design-card honesty: a passed Method Gate cannot have "
            "missing/failed design-card rows, hit hard flags, placeholder paths, "
            "or evidence claims stronger than the card permits."
        ),
    },
    {
        "path": "scripts/check_runtime_fallbacks.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Runtime fallback honesty: missing tools, networks, MCP services, or "
            "statistical backends must be recorded in state decisions, stage logs, "
            "and backend reports, and blocked or non-parity fallbacks cannot pass "
            "Method Gate or replication readiness."
        ),
    },
    {
        "path": "scripts/check_backend_capabilities.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Backend capability reports: Python/StatsPAI, Stata, R, and export "
            "stack availability must be recorded as structured status, missing "
            "dependencies, fallback backend, and probe timestamp before execution."
        ),
    },
    {
        "path": "scripts/check_backend_parity.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Backend parity fixtures and workspace reports: fallback or secondary "
            "Python/StatsPAI, Stata, and R result bundles must agree on sample hash, "
            "estimator family, clustering, fixed effects, coefficients, standard "
            "errors, and diagnostics before parity claims can pass."
        ),
    },
    {
        "path": "scripts/check_citation_integrity.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Citation existence + temporal integrity: DOI resolution, retraction "
            "screening, citation-laundering, and look-ahead / vintage / "
            "sample-vs-claim-period leakage."
        ),
    },
    {
        "path": "scripts/check_verification_log.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "The load-bearing methods-claim verification log exists and every "
            "claim it makes is backed by a recorded check."
        ),
    },
    {
        "path": "scripts/smoke_workspace.py",
        "argv": [],
        "layer": RUNTIME,
        "enforces": (
            "A minimal workspace initialises and every template contract holds "
            "(templates instantiate with the fields the gates later require)."
        ),
    },
    {
        "path": "scripts/check_demo_execution.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Bundled DiD demo execution: the notebook's code cells run in a "
            "temporary workspace, regenerate the table/figures, and preserve the "
            "core teaching estimates and staggered-adoption caution."
        ),
    },
    {
        "path": "scripts/check_preregistration.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Pre-registration lock: the primary specification is committed before "
            "estimation, and any main result not pre-registered is labelled "
            "exploratory (researcher-degrees-of-freedom guard)."
        ),
    },
    {
        "path": "scripts/check_review_scorecard.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "L2 review scorecard: all 7 dimensions scored, every finding carries a "
            "severity + verbatim evidence span + locator, a blocking finding caps its "
            "dimension <=4, and a declared PASS is consistent with the scores."
        ),
    },
    {
        "path": "evals/check_replication_accuracy.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Stage 3 output correctness: candidate estimates are scored against "
            "sourced gold coefficients on sign-correct, perfect-reproduction, and "
            "partial-or-better metrics; template cases cannot be scored as truth."
        ),
    },
    {
        "path": "evals/check_quality_judge.py",
        "argv": ["--selftest"],
        "layer": RUNTIME,
        "enforces": (
            "Reproducible LLM-as-judge bookkeeping: the Draft Quality Gate verdict "
            "is recomputed from dimension scores, red flags, integrity status, and "
            "frozen calibration anchors."
        ),
    },
    {
        "path": "scripts/check_gate_integration.py",
        "argv": [],  # its bare run IS the end-to-end selftest (real init + real templates)
        "layer": MAINT,
        "enforces": (
            "End-to-end: a real workspace init flowed through real templates is "
            "accepted by the gate checkers as a coherent whole."
        ),
    },
    {
        "path": "scripts/check_stage_scenario.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Stage 0-9 golden-path scenario: a completed workspace must have "
            "per-stage logs, handoffs, key artifacts, final handoff recovery, "
            "a green workspace-gate card with table-result reconciliation, and "
            "a filled final delivery report."
        ),
    },
    {
        "path": "scripts/check_stage_adversarial.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Adversarial Stage 0-9 scenarios: common corruptions of a completed "
            "workspace (missing artifacts, stale handoffs, broken reset coverage, "
            "unreconciled tables, non-final citations, and gate-order regressions) "
            "or unfilled final reports must be rejected."
        ),
    },
    {
        "path": "scripts/check_design_gate_contract.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Design-gate-card contract: every contracted empirical design family "
            "has required artifacts, hard-fail conditions, allowed claim levels, "
            "behavioral guardrails, and a matching Method Gate template label."
        ),
    },
    {
        "path": "scripts/check_method_specific_failures.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Method-specific failure fixtures: every contracted design family must "
            "have a failure fixture, and each fixture rejects missing or failed "
            "design-specific diagnostics before a Method Gate can pass."
        ),
    },
    {
        "path": "scripts/check_state_template_paths.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Workflow-state path contract: default artifact paths are safe "
            "workspace-relative paths whose parent directories exist in the init "
            "skeleton, and Stage 0 bootstrap artifacts exist after init."
        ),
    },
    {
        "path": "scripts/check_reproducibility_scaffold.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Replication scaffold: the run_all master script captures environment "
            "state, warns when no expected manifest exists, accepts matching "
            "outputs, and fails corrupted output manifests."
        ),
    },
    {
        "path": "scripts/check_final_report_contract.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Final-report contract: delivery handoffs must include validation "
            "commands, changed files/commits, failures and fixes, residual risks, "
            "and child/parent remote-parity status."
        ),
    },
    {
        "path": "scripts/check_cross_references.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Cross-reference contract: every internal link, named artifact, and "
            "script path referenced from SKILL.md and references actually resolves."
        ),
    },
    {
        "path": "scripts/check_bilingual_docs.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Bilingual README parity: the Chinese and English user surfaces expose "
            "the same reference docs, script inventory, validation commands, and "
            "load-bearing workflow artifacts."
        ),
    },
    {
        "path": "scripts/check_contract_matrix.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Contract matrix: each quality theme has named owner files, validators, "
            "and docs, and high-leverage repo artifacts are covered by at least one "
            "maintained invariant."
        ),
    },
    {
        "path": "scripts/check_rigor_registry.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "RIGOR registry completeness: every checker discovered under scripts/ "
            "or evals/ must be registered in this report, and registry drift is a "
            "blocking maintenance failure."
        ),
    },
    {
        "path": "scripts/check_monthly_worklog.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Long-horizon maintenance evidence: the month-long worklog records the "
            "goal window, baseline PASS evidence, week plan, packet-level validation, "
            "and anti-cheat guards that prevent premature closure."
        ),
    },
    {
        "path": "scripts/check_skillopt_packet.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "SkillOpt improvement packets: >=3 train + >=2 held-out rollouts, a "
            "bounded edit budget, and accept requires a score gain + regression pass."
        ),
    },
    {
        "path": "evals/check_complexity_budget.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Complexity ratchet: the always-loaded SKILL.md and the reference-file "
            "count cannot grow past the recorded ceiling without a justified bump."
        ),
    },
    {
        "path": "evals/score_skill.py",
        "argv": ["--selftest"],
        "layer": MAINT,
        "enforces": (
            "Held-out scoring-harness invariants for the SkillOpt selection gate "
            "(baseline vs candidate scored on the same rubric)."
        ),
    },
]


def _run_selftest(entry: dict, timeout: int = 180) -> dict:
    """Run one checker's selftest. Pure-ish: spawns a subprocess, returns a verdict."""
    path = ROOT / entry["path"]
    result = {
        "path": entry["path"],
        "layer": entry["layer"],
        "enforces": entry["enforces"],
        "optional": entry.get("optional", False),
    }
    if not path.exists():
        result["status"] = "PLANNED" if entry.get("optional") else "MISSING"
        result["detail"] = "not yet on disk" if entry.get("optional") else "expected checker absent"
        return result
    try:
        proc = subprocess.run(
            [sys.executable, str(path), *entry["argv"]],
            cwd=ROOT, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        result["status"] = "FAIL"
        result["detail"] = f"selftest exceeded {timeout}s"
        return result
    result["status"] = "PASS" if proc.returncode == 0 else "FAIL"
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        result["detail"] = tail[-1] if tail else f"exit {proc.returncode}"
    else:
        result["detail"] = "selftest OK"
    return result


def _drift() -> list[str]:
    """Checkers present on disk but not in the registry — keeps the report honest."""
    registered = {e["path"] for e in REGISTRY}
    found: set[str] = set()
    for sub in ("scripts", "evals"):
        for p in (ROOT / sub).glob("*.py"):
            name = p.name
            if name.startswith(("check_", "score_", "validate_")) and name != "__init__.py":
                found.add(f"{sub}/{name}")
    # validate_skill.py is the MASTER aggregator (it chains every leaf checker), and
    # generate_rigor_report.py is this generator — neither is a leaf gate in the table.
    found.discard("scripts/generate_rigor_report.py")
    found.discard("validate_skill.py")
    return sorted(found - registered)


def _report_ok(active_results: list[dict], drift: list[str]) -> bool:
    return all(r["status"] == "PASS" for r in active_results) and not drift


def evaluate(timeout: int = 180) -> dict:
    results = [_run_selftest(e, timeout=timeout) for e in REGISTRY]
    active = [r for r in results if r["status"] != "PLANNED"]
    passed = [r for r in active if r["status"] == "PASS"]
    drift = _drift()
    ok = _report_ok(active, drift)
    return {
        "ok": ok,
        "passed": len(passed),
        "active": len(active),
        "planned": [r for r in results if r["status"] == "PLANNED"],
        "results": results,
        "drift": drift,
    }


def render(ev: dict, date: str) -> str:
    runtime = [r for r in ev["results"] if r["layer"] == RUNTIME]
    maint = [r for r in ev["results"] if r["layer"] == MAINT]
    badge = "PASSING" if ev["ok"] else "FAILING"
    out: list[str] = []
    out.append("# RIGOR.md — gate-coverage report")
    out.append("")
    out.append(f"**Rigor checkers selftest: {badge} — {ev['passed']}/{ev['active']} green.**")
    out.append("")
    out.append(
        "Paper-WorkFlow's differentiator is that research rigor is *executable*, not "
        "advisory. Every load-bearing invariant — about a paper run, and about this "
        "skill package itself — is enforced by a script with a built-in selftest. This "
        "report runs each checker's selftest and records the verdict. A failure here is a "
        "non-zero exit, not a soft warning. Regenerate with "
        "`python3 scripts/generate_rigor_report.py`; verify freshness in CI with `--check`."
    )
    out.append("")
    out.append(
        "> Context: our two closest peers do not have this layer. K-Dense "
        "`scientific-agent-skills` ships only a *security* scanner; Orchestra "
        "`AI-Research-SKILLs` self-grades rigor in markdown. See "
        "[`RELATED-WORK.md`](RELATED-WORK.md) for the evidence."
    )
    out.append("")
    out.append(
        "The master gate `validate_skill.py` chains every leaf checker below (plus "
        "asset, template-contract, link, and notebook checks) into a single "
        "`python3 validate_skill.py` run maintainers must pass before shipping."
    )
    out.append("")

    def section(title: str, rows: list[dict]) -> None:
        out.append(f"## {title}")
        out.append("")
        out.append("| Checker | Result | Enforced invariant |")
        out.append("|---|:--:|---|")
        for r in rows:
            mark = {
                "PASS": "✅ pass", "FAIL": "❌ FAIL",
                "MISSING": "⛔ missing", "PLANNED": "🗓️ planned",
            }.get(r["status"], r["status"])
            note = "" if r["status"] in {"PASS"} else f" — _{r['detail']}_"
            out.append(f"| [`{r['path']}`]({r['path']}) | {mark}{note} | {r['enforces']} |")
        out.append("")

    section("Run-time gates — verify a paper run", runtime)
    section("Maintenance gates — verify this skill package", maint)

    if ev["drift"]:
        out.append("## Registry drift (blocking)")
        out.append("")
        out.append(
            "These checkers exist on disk but are not registered above. This is a "
            "blocking maintenance failure: register each in `generate_rigor_report.py` "
            "or remove the stray checker so the report stays complete:"
        )
        out.append("")
        for d in ev["drift"]:
            out.append(f"- `{d}`")
        out.append("")

    out.append("## How to reproduce")
    out.append("")
    out.append("```bash")
    out.append("python3 scripts/generate_rigor_report.py        # regenerate this file")
    out.append("python3 scripts/generate_rigor_report.py --check # CI: fail if stale")
    out.append("```")
    out.append("")
    out.append(f"{DATE_MARKER}{date} by `scripts/generate_rigor_report.py`. "
               "The body is deterministic apart from this line.")
    out.append("")
    return "\n".join(out)


def _body_for_check(text: str) -> str:
    """Body used for --check freshness: drops only the volatile date line."""
    out: list[str] = []
    for l in text.splitlines():
        if l.startswith(DATE_MARKER):
            continue
        out.append(l)
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--check", action="store_true",
                   help="verify the committed RIGOR.md matches a fresh run (ignoring the date line)")
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p.add_argument("--date", default=None, help="pin the generated-on date (default: today, Asia/Shanghai-agnostic)")
    p.add_argument("--timeout", type=int, default=180, help="per-checker selftest timeout (s)")
    args = p.parse_args(argv)

    ev = evaluate(timeout=args.timeout)
    date = args.date or datetime.date.today().isoformat()
    report = render(ev, date)

    if args.json:
        import json
        print(json.dumps({k: v for k, v in ev.items() if k != "results"} | {"results": ev["results"]},
                         ensure_ascii=False, indent=2))
        return 0 if ev["ok"] else 1

    if args.check:
        if not REPORT_PATH.exists():
            print("RIGOR.md missing; run without --check to generate it", file=sys.stderr)
            return 1
        on_disk = REPORT_PATH.read_text(encoding="utf-8")
        if _body_for_check(on_disk).rstrip() != _body_for_check(report).rstrip():
            print("RIGOR.md is STALE — regenerate with: python3 scripts/generate_rigor_report.py",
                  file=sys.stderr)
            return 1
        if not ev["ok"]:
            if ev["drift"]:
                print(
                    "RIGOR.md is current but registry drift is present: "
                    + ", ".join(ev["drift"]),
                    file=sys.stderr,
                )
            else:
                print("RIGOR.md is current but a checker selftest is FAILING", file=sys.stderr)
            return 1
        print(f"RIGOR.md is current and {ev['passed']}/{ev['active']} checkers pass their selftest")
        return 0

    REPORT_PATH.write_text(report, encoding="utf-8")
    status = "all green" if ev["ok"] else "FAILURES present"
    print(f"wrote {REPORT_PATH.name}: {ev['passed']}/{ev['active']} checkers pass their selftest ({status})")
    for r in ev["results"]:
        if r["status"] not in {"PASS", "PLANNED"}:
            print(f"  {r['status']}: {r['path']} — {r['detail']}")
    for d in ev["drift"]:
        print(f"  DRIFT: {d} present on disk but not registered")
    return 0 if ev["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
