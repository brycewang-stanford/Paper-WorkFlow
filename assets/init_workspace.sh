#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <workspace-dir>" >&2
  exit 2
fi

workspace=$1
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
template="$script_dir/workflow_state.template.json"

if [[ -e "$workspace" ]]; then
  echo "refusing to overwrite existing path: $workspace" >&2
  exit 1
fi

mkdir -p "$workspace"/{00_meta,01_proposal/candidates,02_data/raw,03_analysis/results,03_analysis/robustness,04_results,05_draft,06_polish,07_dehumanize,08_review,09_submission,logs,backups}
cp "$template" "$workspace/00_meta/workflow_state.json"
printf '# Paper workflow workspace\n\nCreated for staged empirical-paper orchestration.\n' > "$workspace/README.md"
cat > "$workspace/00_meta/intake.md" <<'EOF'
# Intake

- Short name:
- Created at Beijing:
- Entry stage:
- Mode: auto / stage-confirm / interactive
- Target journal:
- Language: en / zh / bilingual
- Source material:
- Notes:
EOF
