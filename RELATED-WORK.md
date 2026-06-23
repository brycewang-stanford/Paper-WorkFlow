# Related Work & Positioning — Paper-WorkFlow vs. the field

> **一段话定位（中文）**：GitHub 上的「全流程自动化科研」明星项目（Sakana AI Scientist、
> K-Dense `scientific-agent-skills`、Orchestra `AI-Research-SKILLs` 等）几乎都在卷「能不能自动
> 写出一篇像样的论文」。本项目卷的是另一件事——**写出来的东西能不能信**。我们是一个面向
> 经管 / 社科**实证**研究的 meta-orchestrator，核心壁垒是一整套**可执行的、确定性的严谨性闸门**
> （方法识别闸门、引用存在性 + 时序完整性、claim 忠实度、可复现性），而这一层正是两个最直接的
> 竞品（K-Dense、Orchestra）共同缺失的。本文用证据把这条护城河讲清楚，并列出向它们借鉴、补齐
> 自身短板的路线图。

This document maps Paper-WorkFlow against the most-starred "automated research" projects on
GitHub, states our differentiation thesis with evidence, and records what we deliberately borrow.
It is a living strategy artifact, refreshed as the field moves.

Star counts are live values pulled from the GitHub API on **2026-06-23**; they will drift.

---

## 1. The landscape (and which projects are actually our peers)

| Category | Representative projects | Stars | Relationship to us |
|---|---|---|---|
| **Full-pipeline "AI Scientist"** (idea→experiment→paper, standalone apps) | [SakanaAI/AI-Scientist](https://github.com/SakanaAI/AI-Scientist) · [-v2](https://github.com/SakanaAI/AI-Scientist-v2) · [aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw) · [microsoft/RD-Agent](https://github.com/microsoft/RD-Agent) | 14.1k / 6.7k / 13.6k / 13.6k | **Different form factor.** Self-contained apps, ML-domain, weak on verifiable rigor. Inspiration for orchestration, not direct competitors. |
| **Deep research / report generation** (no experiments) | [stanford-oval/storm](https://github.com/stanford-oval/storm) · [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | 29.3k / 27.9k | Adjacent — long-form cited reports, not empirical paper pipelines. |
| **Scientific RAG / QA** | [Future-House/paper-qa](https://github.com/Future-House/paper-qa) | 8.8k | Best-in-class citation grounding; a component, not a pipeline. Worth studying for citation mechanics. |
| **★ Agent-Skills libraries** (same form factor as us) | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) · [Orchestra-Research/AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs) | 29.1k / 10.0k | **Our true peers.** Same "skills make any agent a researcher" model. Analyzed in depth below. |

**Key framing:** the AI-Scientist apps are a *different product shape* (a packaged binary you run). We are
a **skill package** that upgrades any host agent (Claude Code / Codex / Cursor). On that axis our direct
competitors are K-Dense and Orchestra. So the rest of this document focuses on those two.

---

## 2. The two direct peers, dissected

Both were cloned and read in full (147 and 98 skills respectively). Evidence-backed findings:

### 2.1 K-Dense — `scientific-agent-skills` (29.1k★, v2.50.0)

- **Shape:** 147 skills, 1469 files, **flat catalog** (`skills/<name>/`); grouping is README prose by
  *domain*, not by *research lifecycle*. No orchestrator — the host agent self-sequences.
- **Domain:** biology / chemistry / medicine / drug-discovery. The "100+ databases" claim is mostly **one**
  `database-lookup` skill fronting 78 per-DB Markdown reference files.
- **Anatomy:** `SKILL.md` (median 400 / max 1596 lines) + `references/` (135/147) + `scripts/` (70/147).
  Multi-host frontmatter with single-line-JSON `metadata`, host-gating (openclaw/hermes), and
  **cross-references baked into the `description`** to route among overlapping skills.
- **Rigor layer — the critical finding:** **there is none.** The only automated enforcement in the entire
  repo is a **security scanner** (Cisco AI-Defense, `--fail-on HIGH`, gates merges on prompt-injection /
  malware). There is no correctness gate, no eval harness, no reproducibility check. Rigor-adjacent skills
  (a CONSORT/STROBE/PRISMA `peer-review` checklist, a `scholar-evaluation` rubric that averages
  *human-supplied* scores, a `retrieval-contract.md`) are **advisory prose, never enforced.** Their one real
  citation script (`validate_citations.py`, CrossRef DOI check) is **opt-in, single-skill, not a gate.**
- **Econometrics depth:** **near zero.** No DiD / IV / RDD / synthetic-control / event-study / panel-FE skill
  exists; `grep` across all 147 skills surfaces only a generic `statistical-analysis`.

### 2.2 Orchestra — `AI-Research-SKILLs` (10.0k★, v1.7.2)

- **Shape:** 98 skills across 23 numbered categories; hybrid org (lifecycle skills at the bookends,
  one-tool-per-skill wrappers in the middle). **Has a real orchestrator** (`0-autoresearch-skill`,
  two-loop, designed to run autonomously via `/loop` or cron — "the human is asleep; never stop").
- **Domain:** ML / AI-engineering (model architecture, fine-tuning, RL, inference serving, evals).
- **Anatomy:** `SKILL.md` (avg 404 / max 982 lines) + `references/` + LaTeX `templates/` for ML venues.
  **Almost no executable code in skills.** Frontmatter: name / description-with-"Use when" / version /
  author / tags / pip-dependencies.
- **Rigor layer — has one, but it is 100% LLM-prose self-grading:** the "ARA Seal" —
  `ara-compiler` (Level-1 *structural* checklist) + `ara-rigor-reviewer` (Level-2 *semantic* review scoring
  6 dimensions 1–5 with anchors, severity findings, verbatim evidence spans, Strong-Accept→Reject grade) +
  provenance tags + git-as-pre-registration. **It is well-designed as a rubric — but nothing is executable.**
  The only real script in the repo counts files (`check-inventory.sh`). No statistical/causal-identification
  validity, no citation-integrity/retraction gate, no reproducibility re-run, no CI that tests skill content.

### 2.3 What both peers share (and therefore what is open)

1. **No executable, deterministic rigor gate.** K-Dense has only security; Orchestra's gates are markdown
   the LLM self-grades. Neither can *mechanically prove* a claimed gate is backed by evidence.
2. **No econometric / causal-identification layer.** The entire DiD/IV/RDD/SC/event-study vertical — with
   assumption audits, inference discipline, and design-risk ledgers — is unoccupied.
3. **No citation-integrity / retraction / temporal-leakage gate.** At best a one-off CrossRef DOI check.
4. **No enforced reproducibility.** Reproducibility is a stated value, never a re-run-and-compare gate.

---

## 3. Coverage matrix — where we lead, where we lag

`✅` strong / enforced · `🟡` partial / advisory · `❌` absent.  Evidence in §2 and in our own `scripts/`, `references/`.

| # | Capability / rigor dimension | **Paper-WorkFlow** | K-Dense | Orchestra |
|---|---|:--:|:--:|:--:|
| 1 | End-to-end lifecycle **orchestrator** (gated, resumable) | ✅ 10-stage + breakpoints | ❌ flat catalog | ✅ two-loop |
| 2 | **Econometrics / causal-identification** depth (DiD/IV/RDD/SC) | ✅ core vertical | ❌ none | ❌ none (ML) |
| 3 | **Executable** deterministic gates (not prose self-grade) | ✅ `check_workspace_gates.py` + 6 checkers | ❌ security only | 🟡 prose "ARA Seal" |
| 4 | **Method / identification gate** (design register, min-evidence pack) | ✅ hard gate, ordering-enforced | ❌ | 🟡 prose rubric |
| 5 | **Citation integrity** (existence + retraction + temporal/look-ahead) | ✅ `check_citation_integrity.py --final` | 🟡 opt-in DOI | ❌ advice only |
| 6 | **Claim fidelity** audit (number / quote / claim↔evidence) | ✅ `claim_integrity_audit` gated | ❌ | 🟡 prose entailment |
| 7 | **Reproducibility** enforcement (DAS, `run_all`, env capture, rebuild check) | ✅ replication-pack gate | ❌ value only | ❌ described, not run |
| 8 | **Pre-registration / researcher-DOF** guarding | 🟡 `design-transparency.md` (prose) | ❌ | 🟡 git-lock + prose |
| 9 | Structured **quality rubric / review** (severity, accept/reject) | ✅ 7-dim gate | 🟡 ScholarEval averaging | ✅ 6-dim ARA review |
| 10 | **Self-maintenance discipline** (eval harness, complexity ratchet, SkillOpt) | ✅ `score_skill` + ratchet + packet | 🟡 security CI | 🟡 inventory count |
| 11 | **Multi-host distribution / install** polish | 🟡 in-repo, no installer | ✅ `npx`/`gh skill install --pin` | ✅ `npx` + marketplace |
| 12 | **Public transparency / credibility** artifact (badge) | 🟡 worklogs, no badge | ✅ auto `SECURITY.md` + CI badge | 🟡 line/ref-count signals |
| 13 | Raw **breadth** (skill / DB count) | 🟡 1 orchestrator + 67-skill toolkit | ✅ 147 + 78 DBs | ✅ 98 |

**Reading the matrix:** we **dominate the entire rigor block (rows 1–10)** — the half of the table that
determines whether produced research is *trustworthy*. We **lag on the merchandising block (rows 11–13)** —
distribution, a public credibility badge, and raw breadth. That asymmetry is the roadmap: **don't chase their
breadth; make our rigor advantage loud, verifiable, and easy to adopt.**

---

## 4. Differentiation thesis

> **They optimize "can an agent produce a paper?" We optimize "can you trust the paper it produced?"**

The field has largely solved *generation* and almost entirely ignored *verification*. An AI-written paper that
cites a retracted study, leaks future information into a backtest, lets the estimation sample silently drift, or
states a causal claim its design can't support is *worse* than no paper — it manufactures false confidence at
scale. Our wager is that as AI-generated research floods journals and preprint servers, **the scarce, defensible
asset is enforced credibility, not faster drafting.** Every competitor's rigor layer is either absent (K-Dense)
or self-graded prose (Orchestra). Ours is **executable**: a checker exits non-zero and the gate does not pass.
That is a category they do not currently play in.

Three structural commitments encode the thesis:

1. **Rigor is executable, not advisory.** Every load-bearing claim about a run is checked by a script with a
   selftest, not by an LLM reading a checklist. Prose can be gamed; `exit 1` cannot.
2. **Identification before prose.** The Method Gate blocks the pipeline *before* writing if the design's
   minimum-evidence pack is incomplete or a blocking threat is unresolved. You cannot write your way out of a
   methods hole.
3. **Rigor-first, human-in-the-loop.** We reject the "never stop, the human is asleep" autonomy stance. Hard
   decision points (identification strategy, submission) are gated for a human in the default mode — because
   the failure modes of autonomous empirical research are silent and expensive.

---

## 5. What we borrow (credit where due)

Honest competitive analysis means stealing the good ideas. Concrete, attributed borrowings — each adapted to
our executable-rigor stance rather than copied as prose:

| From | Idea | Our adaptation |
|---|---|---|
| K-Dense | `retrieval-contract.md` — a data-retrieval completeness protocol | An **identification/estimation contract** that is **script-checked** against the design branch's required-evidence pack, not just narrated. |
| K-Dense | Auto-generated `SECURITY.md` + CI badge as a trust signal | A generated **`RIGOR.md`** gate-coverage report — our credibility badge, proving every gate passes its selftest. (A category they *can't* produce; they have no rigor gates.) |
| K-Dense | Description-level cross-reference routing; `gh skill install --pin <sha>` reproducible installs | Tighten our routing prose; evaluate a pinned-install path for the toolkit. |
| Orchestra | The 6-dimension review rubric (scoring anchors, severity findings, **verbatim evidence span**, accept/reject grade) | Fold severity + mandatory verbatim-evidence into our 7-dim quality rubric and claim-integrity audit. |
| Orchestra | Two-tier split: L1 *structural* validation + L2 *semantic* review | We already have L1 as a **real runnable validator** (`check_workspace_gates.py`) — their weakest spot. Make the L1/L2 split explicit and named. |
| Orchestra | Provenance tags (`user` / `ai-suggested` / `ai-executed`) + git pre-registration + confirmatory-vs-exploratory labeling | A **pre-registration template + checker**: lock the primary spec before estimation; any main result not pre-registered must be labeled exploratory. |

---

## 6. Roadmap — turning the moat into a product (the "month" of work)

Sequenced so each phase ships a verifiable artifact, respects the complexity ratchet (new load-bearing logic
goes into `scripts/` + `templates/`, never bloats the always-loaded `SKILL.md`), and is independently testable.

- **Phase 1 — Make the moat legible & credible.** This `RELATED-WORK.md`; a `scripts/generate_rigor_report.py`
  that runs every checker and emits a public **`RIGOR.md`** gate-coverage report (our `SECURITY.md` analog).
- **Phase 2 — Pre-registration & provenance layer.** `templates/preregistration.md` + `scripts/check_preregistration.py`
  enforcing spec-lock-before-estimation and confirmatory/exploratory labeling; wired into the Method Gate.
- **Phase 3 — Two-tier review formalization.** Name the L1 (executable) / L2 (semantic) split; add severity
  findings + mandatory verbatim-evidence spans to the quality rubric and claim-integrity templates.
- **Phase 4 — Deepen citation integrity past both peers.** Extend `check_citation_integrity.py` toward
  quote-vs-source faithfulness and citation-laundering depth; formalize the identification/estimation contract.
- **Phase 5 — Consolidate, validate, eval, complexity-budget check, worklogs, commit.**

Progress is tracked in `worklogs/` and gated by `validate_skill.py` + `evals/`.

---

*Maintained as part of the Paper-WorkFlow skill. Findings in §2 are reproducible: clone the two peer repos and
re-run the analysis. Star counts are point-in-time. Corrections welcome — accuracy is the whole point.*
