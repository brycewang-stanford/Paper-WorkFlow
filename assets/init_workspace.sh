#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <workspace-dir>" >&2
  exit 2
fi

workspace=$1
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
template="$script_dir/workflow_state.template.json"
backend_template="$script_dir/../templates/analysis_backend.md"
ledger_template="$script_dir/../templates/evidence_ledger.md"
risk_template="$script_dir/../templates/design_risk_ledger.md"
routing_template="$script_dir/../templates/entry_routing.md"
passport_template="$script_dir/../templates/stage_passport.md"
handoff_template="$script_dir/../templates/handoff_card.md"
handoff_prompt_template="$script_dir/../templates/handoff_prompt.md"
pipeline_status_template="$script_dir/../templates/pipeline_status.md"
claim_integrity_template="$script_dir/../templates/claim_integrity_audit.md"

if [[ -e "$workspace" ]]; then
  echo "refusing to overwrite existing path: $workspace" >&2
  exit 1
fi

mkdir -p "$workspace"/{00_meta/handoff,01_proposal/candidates,02_data/raw,03_analysis/results,03_analysis/robustness,04_results,05_draft,06_polish,07_dehumanize,08_review,09_submission,logs,backups}
cp "$template" "$workspace/00_meta/workflow_state.json"
cp "$backend_template" "$workspace/00_meta/analysis_backend.md"
cp "$ledger_template" "$workspace/00_meta/evidence_ledger.md"
cp "$risk_template" "$workspace/03_analysis/design_risk_ledger.md"
cp "$routing_template" "$workspace/00_meta/entry_routing.md"
cp "$passport_template" "$workspace/00_meta/stage_passport.md"
cp "$handoff_template" "$workspace/00_meta/handoff/HANDOFF_TEMPLATE.md"
cp "$handoff_prompt_template" "$workspace/00_meta/handoff_prompt.md"
cp "$pipeline_status_template" "$workspace/00_meta/pipeline_status.md"
cp "$claim_integrity_template" "$workspace/00_meta/claim_integrity_audit.md"
printf '# Paper workflow workspace\n\nCreated for staged empirical-paper orchestration.\n' > "$workspace/README.md"
cat > "$workspace/00_meta/intake.md" <<'EOF'
# Intake

- Short name:
- Created at Beijing:
- Entry stage:
- Mode: auto / stage-confirm / interactive
- Target journal:
- Language: en / zh / bilingual
- Analysis backend: python-statspai / stata / r
- Source material:
- Entry routing file: 00_meta/entry_routing.md
- Stage passport: 00_meta/stage_passport.md
- Pipeline status: 00_meta/pipeline_status.md
- Handoff directory: 00_meta/handoff/
- Claim integrity audit: 00_meta/claim_integrity_audit.md
- Notes:
EOF
