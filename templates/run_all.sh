#!/usr/bin/env bash
set -euo pipefail

# Template master script (one-click rebuild contract).
# Replace each placeholder command with the project-specific cleaning, estimation,
# and exhibit-generation scripts. Acceptance test: delete all derived outputs, run
# this script, and rebuild every table/figure with numbers matching the paper.
# See references/reproducibility-pack.md §3 and references/computational-reproducibility.md.

# --- Run from the package root, use relative paths only ---
cd "$(dirname "$0")"
ANALYSIS_BACKEND="${ANALYSIS_BACKEND:-python-statspai}"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p logs 00_meta 04_results/expected
LOG="logs/run_all_${STAMP}.log"

# --- Determinism settings (computational-reproducibility.md §2): fixed threads,
#     hash seed, and locale so multi-threaded float reductions do not drift. ---
export PYTHONHASHSEED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export LC_ALL=C

log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
step_time() { local label="$1"; shift; local t0; t0=$(date +%s); "$@"; log "$label done in $(( $(date +%s) - t0 ))s"; }

log "master script start (backend=${ANALYSIS_BACKEND}, stamp=${STAMP})"

echo "Step 0/5: capture environment -> 00_meta/env_capture.txt"
{
  echo "# Environment captured ${STAMP}"
  uname -a || true
  echo "ANALYSIS_BACKEND=${ANALYSIS_BACKEND}"
  echo "PYTHONHASHSEED=${PYTHONHASHSEED} OMP_NUM_THREADS=${OMP_NUM_THREADS} LC_ALL=${LC_ALL}"
  case "${ANALYSIS_BACKEND}" in
    python-statspai) python3 --version; python3 -m pip freeze 2>/dev/null || true ;;
    r)               Rscript -e 'cat(R.version.string,"\n"); print(sessionInfo())' 2>/dev/null || true ;;
    stata)           echo "Record Stata flavor/version and ssc package versions manually (see repro_environment.md §3)" ;;
  esac
} > 00_meta/env_capture.txt 2>&1
log "environment captured"

echo "Step 1/5: environment check"
python3 --version
log "Analysis backend: ${ANALYSIS_BACKEND}"

echo "Step 2/5: build analysis data"
# step_time "clean" python3 02_data/clean.py
# step_time "clean" Rscript 02_data/clean.R
# step_time "clean" stata-mp -b do 02_data/clean.do

echo "Step 3/5: run analyses"
case "${ANALYSIS_BACKEND}" in
  python-statspai)
    : # step_time "estimate" python3 03_analysis/estimate.py
    ;;
  r)
    : # step_time "estimate" Rscript 03_analysis/estimate.R
    ;;
  stata)
    : # step_time "estimate" stata-mp -b do 03_analysis/estimate.do
    ;;
  *)
    echo "Unknown ANALYSIS_BACKEND: ${ANALYSIS_BACKEND}" >&2
    exit 2
    ;;
esac

echo "Step 4/5: build tables and figures"
# step_time "exhibits" python3 03_analysis/build_exhibits.py
# step_time "exhibits" Rscript 03_analysis/build_exhibits.R
# step_time "exhibits" stata-mp -b do 03_analysis/build_exhibits.do

echo "Step 5/5: verify outputs against expected manifest (numbers must match the paper)"
if [ -f 04_results/expected/manifest.json ]; then
  python3 templates/check_outputs.py --root . || { log "OUTPUT CHECK FAILED"; exit 1; }
else
  log "WARNING: no 04_results/expected/manifest.json — output integrity not verified (see computational-reproducibility.md §3)"
fi

log "master script done. Compare 04_results/ against REPLICATION.md Section 6."
echo "Done. Full log: ${LOG}"
