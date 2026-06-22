# SkillOpt Improvement Packet

Use this packet before accepting a non-trivial update to `Paper-WorkFlow` itself.
Fill every placeholder, then run:

```bash
python3 scripts/check_skillopt_packet.py path/to/SKILLOPT_PACKET.md
```

## Candidate

- Target skill files: <SKILL.md / references/... / templates/... / scripts/...>
- Source SkillOpt snapshot: <repo URL + commit SHA or local path>
- Change scope: <one sentence>
- Edit budget L: <integer, recommended 1-4>
- Protected areas: <files or sections not to touch>

## Rollout Split

### Train rollouts

- [ ] train-001 | status=<success|failure> | score=<0.00> | evidence=<path-or-link> | note=<one-line>
- [ ] train-002 | status=<success|failure> | score=<0.00> | evidence=<path-or-link> | note=<one-line>
- [ ] train-003 | status=<success|failure> | score=<0.00> | evidence=<path-or-link> | note=<one-line>

### Held-out selection rollouts

- [ ] select-001 | status=<success|failure> | score=<0.00> | evidence=<path-or-link> | note=<one-line>
- [ ] select-002 | status=<success|failure> | score=<0.00> | evidence=<path-or-link> | note=<one-line>

## Reflection

### Failure patterns

- <common failure pattern and why it is general>

### Success patterns

- <common success pattern worth preserving>

## Proposed Bounded Patch

- [ ] edit_1 | op=<append|insert_after|replace|delete> | target=<exact file/heading/text> | rationale=<why this generalizes>

## Gate Decision

- Baseline selection score: <0.00>
- Candidate selection score: <0.00>
- Gate decision: <accept|reject>
- Regression check: <pass|fail>
- Selection rubric: <short description of scoring dimensions>

## Adoption Record

- Accepted files: <paths, or none if rejected>
- Rejected edit memory: <what not to retry, if rejected>
- Validation commands: <commands and pass/fail result>
- Follow-up: <remaining risks or next packet idea>

