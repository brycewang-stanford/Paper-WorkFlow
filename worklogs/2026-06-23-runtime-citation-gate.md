# 2026-06-23 Runtime Citation Gate

## Scope

Bounded weekly hardening pass in an isolated worktree because the shared `main`
worktree had unrelated concurrent edits in `scripts/check_cross_references.py`.
This pass does not touch that file and does not bump the workflow schema.

## Change

- `scripts/check_workspace_gates.py` now calls the existing
  `scripts/check_citation_integrity.py` validator.
- Draft Quality Gate `pass` now requires `00_meta/citation_integrity_log.md` to
  be pre-final clean.
- `replication_pack.status=ready` now requires the same log to pass the
  `--final` citation/temporal-integrity rules.
- `scripts/check_gate_integration.py` now builds a final-clean citation log in
  the real initialized workspace and proves that corrupting it blocks
  replication readiness.

## Schema Decision

No `schema_version` bump and no new top-level `citation_integrity` state block.
The prior citation-integrity pass deliberately kept this layer as artifact-state:
`00_meta/citation_integrity_log.md` plus the deterministic checker are the source
of truth. The runtime gate now enforces that existing contract instead of adding
parallel state that could drift.

## Validation

- `python3 scripts/check_workspace_gates.py --selftest` passed.
- `python3 scripts/check_gate_integration.py` passed.
- `python3 scripts/check_citation_integrity.py --selftest` passed.
- `python3 validate_skill.py` passed.
