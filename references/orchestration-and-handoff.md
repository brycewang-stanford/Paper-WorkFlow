# Orchestration & Handoff — 编排、路由与断点交接

This reference translates the useful engineering patterns from full research
skill suites into Paper-WorkFlow's empirical-paper contract. It does not lower
the method gate; it makes stage routing and continuation auditable.

## Entry Routing

Stage 0 must write `00_meta/entry_routing.md` before executing a later stage.
The route decision records what the user brought, which stage is safe to enter,
which assumptions were inferred, and which decisions remain human-owned.

Use the route file to separate similar requests:

| Request shape | Route |
|---|---|
| "Continue / pick up / another agent stopped" | Recovery probe first, then the first incomplete stage |
| "Write or polish this paragraph" | Stage 5/6/7 only; do not start the full pipeline |
| "From idea/data to submission" | Full Stage 0-9 pipeline |
| "I already have results" | Stage 5 only after Method Gate evidence exists |
| "Submit this completed draft" | Stage 9 after citation, data-governance, and policy refresh |

## Stage Passport

`00_meta/stage_passport.md` is the human-readable stage ledger. It complements
`workflow_state.json`; it is not a replacement. Update both at each stage
boundary.

Each completed stage needs:

- input accepted from the previous stage;
- output artifact paths;
- gate result and evidence;
- revision rounds used;
- known limitations or open gaps.

If the passport and `workflow_state.json` disagree, treat that as a recovery
problem and refresh current evidence before proceeding.

## Pipeline Status Dashboard

`00_meta/pipeline_status.md` is the compact dashboard for humans and follow-on
agents. Update it at the same boundaries as the stage passport, but keep it
short: current status, key materials, latest checkpoint, open flags, and next
smallest action.

Use it when:

- the user asks for status;
- another agent may take over;
- a hard gate just passed or failed;
- a long session needs a reset boundary.

Do not treat the dashboard as proof. It is an index into current artifacts and
fresh evidence, not a substitute for `workflow_state.json` or gate reports.

## Fresh Evidence

Do not declare a stage done from memory. A current proof must exist in one of
these forms:

- command output with exit status;
- `scripts/check_workspace_gates.py` report;
- a gate report or scorecard written in the workspace;
- a file diff or generated artifact;
- an explicit user decision recorded in `workflow_state.json.decisions`.

Old handoff notes are pointers, not proof. On recovery, refresh `git status`,
`workflow_state.json`, the stage passport, and the current stage artifact.

## Handoff Card

Use `00_meta/handoff/` for handoff cards whenever a long run pauses, a stage
switches, context is getting thin, or another agent takes over. A card must say:

- current stage;
- completed artifacts and how they were verified;
- worktree state;
- next smallest action;
- blocking risks;
- files the next agent must read;
- explicit "Do Not" boundaries.

The latest card path should be written to
`workflow_state.json.orchestration.latest_handoff`. If that field is set, the
runtime checker verifies the file exists.

## Reset Boundaries

For long sessions, use the handoff card as the reset boundary. Append a compact
entry to `workflow_state.json.orchestration.reset_boundaries` with:

- completed stage;
- handoff card path;
- status snapshot (`verified`, `stale`, or `needs_probe`);
- next stage or pending decision;
- created time.

This is lighter than ARS's hash ledger, but preserves the same operational
discipline: a new session resumes from disk artifacts and a named boundary,
not from chat memory. If two agents are active, write a new boundary instead of
mutating an old one.

## Runtime Discipline

- `orchestration.fresh_evidence_required` stays `true`.
- `orchestration.revision_rounds_cap` defaults to `2`; do not reset it after a
  handoff.
- `orchestration.pipeline_status` points to `00_meta/pipeline_status.md`.
- `orchestration.checkpoint_policy` records the current confirmation policy
  (`full-at-hard-gates` by default).
- `orchestration.reset_boundaries` is append-only within a run.
- `orchestration.self_review_gate` and `orchestration.ethics_gate` record whether
  the current stage had a fresh self-review and research-integrity pass.
- Any fallback or unavailable probe goes into `logs/stage_<N>.md` and
  `workflow_state.json.decisions`.

## schema_version 12

Schema v12 keeps everything v11 shipped and closes four ordering holes: work that
was *documented* as happening at the right time but was never *required* to.

**① 两个前置阶段（`stages` 新增两行）.** `1L_literature_base` 与 `2_5_design_lock`
带父阶段数字前缀，Stage 0–9 主干不变，但它们各自守着一件必须发生在父阶段结束**之前**
的事：文献语料要在查新打分之前建好，主设定要在第一个估计值存在之前锁死。

- `literature_base`：`corpus` / `lit_matrix` / `screened_count` / `core_count` /
  `reused_by`（记录哪些环节复用了这份语料：`novelty` / `related_work` /
  `reference_verify`）。见 [`literature-and-positioning.md`](literature-and-positioning.md) §0。
- `design_lock`：`preregistration` / `locked_before_estimation` / `lock_commit` /
  `confirmatory_count` / `deviations`。`locked_before_estimation` 不为 `true` 而
  `03_analysis/results/main_results.json` 已存在 = 硬违规：**事后写的锁不是锁**。
  见 [`design-transparency.md`](design-transparency.md) §0。

**② `manuscript_numbers`（数字锚定）.** `unanchored_claims` / `inert_boundary_drift` /
`waived_claims` / `checked_manuscript`。由 `scripts/check_manuscript_numbers.py` 填，
质量门放行前必须为 `pass` 且两个计数为 0。见
[`integrity-and-claim-audit.md`](integrity-and-claim-audit.md) §4。

**③ `project.scope`（严格度档位）.** `draft` / `working-paper` / `submission`（缺省）。
它只决定「这次交付欠哪些闸门」，**不放松**任何已声明为 `pass` 的闸门的验证：

| scope | 必过闸门 | 典型用途 |
|---|---|---|
| `draft` | method_gate | 两天出一版内部讨论稿 |
| `working-paper` | + design_risk、quality_gate | 工作论文 / 组会 / 预印本 |
| `submission` | + integrity_audit、manuscript_numbers、replication_pack | 正式投稿（缺省） |

档位在 Phase 0 与交互档位一起问定；交互档位管**暂停频率**，scope 管**严格度**，两者正交。

**④ 回退上限（`orchestration`）.** `method_gate_rounds_cap`（缺省 2）与
`method_gate_rounds` 计数，配合既有的 `revision_rounds_cap`。超限时
`budget_exhausted_action`（缺省 `deliver-with-known-gaps`）生效：停止重跑，按已知短板
交付并标红，而不是让全自动档位无界重试。

**⑤ `replication_pack.environment_record` / `frozen_at_stage`.** 复现包不再是收尾
一次性构建：Stage 3 估计跑通即冻结环境记录与 master script 骨架，收尾只做**验证性重跑**。
见 [`computational-reproducibility.md`](computational-reproducibility.md) §0。

字段语义见 [`workspace-and-state.md`](workspace-and-state.md) §2。

## schema_version 11

Schema v11 keeps everything v10 shipped and adds one Stage-0 decision block,
`workflow_state.json.table_style`: the export format for every table the run
produces, defaulting to `three-line` (三线表). It is resolved once in the Phase 0
intake alongside the analysis backend, enforced at Stage 4 and again at the
Stage 9 Word export by `scripts/check_table_style.py`, and opted out of only by
changing `table_style.format` and recording the reason in `decisions`. Field
semantics live in [`workspace-and-state.md`](workspace-and-state.md) §2; the
format contract and the per-backend recipes live in
[`analysis-backends.md`](analysis-backends.md) §4.1.

Schema v10 kept the v9 `orchestration` block and added ARS-inspired checkpoint
and integrity surfaces:

- `00_meta/entry_routing.md`
- `00_meta/stage_passport.md`
- `00_meta/pipeline_status.md`
- `00_meta/handoff/`
- `00_meta/handoff_prompt.md`
- `00_meta/claim_integrity_audit.md`
- `workflow_state.json.integrity_audit`

These files are created by `assets/init_workspace.sh`, exercised by
`scripts/smoke_workspace.py`, and checked by `validate_skill.py`.

## Failure modes & recovery

This section is the recovery contract for the orchestrator. The full
descriptions — triggers, expected paths, and maintenance checks — live
in `evals/chaos/`. `scripts/check_chaos_coverage.py` enforces the
mapping between this prose and the scenario files; add a new
scenario file when you add a new entry here, and add a new entry here
when you add a new scenario file.

| Failure mode | Scenario | Recovery in one line |
|---|---|---|
| `Skill` tool reports "skill not found" | `evals/chaos/chaos_skill_not_found.md` | Read the child skill's `SKILL.md` inline; do not retry the `Skill` tool. |
| Subagent crashes or hangs before writing its summary | `evals/chaos/chaos_subagent_failure.md` | Check output files; retry at most once; write a handoff card on second failure. |
| Context budget exhausted mid-Stage-3 | `evals/chaos/chaos_context_overflow.md` | Discard heavy context; resume from the last `done` stage in `workflow_state.json`; re-dispatch subagents with the ≤10-line contract. |

> **Based on inference, refine on first real failure.** The recovery
> paths above are derived from the orchestrator's documented intent
> (SKILL.md, skill-map.md §0, this file). A real failure should be
> recorded as a one-paragraph addition to the matching scenario file
> in `evals/chaos/`, not as a one-off fix in code.
