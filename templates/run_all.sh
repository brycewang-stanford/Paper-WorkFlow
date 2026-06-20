#!/usr/bin/env bash
set -euo pipefail

# Template master script. Replace each placeholder command with the project
# specific cleaning, estimation, and exhibit-generation scripts.

echo "Step 1/4: environment check"
python3 --version

echo "Step 2/4: build analysis data"
# python3 02_data/clean.py
# Rscript 02_data/clean.R
# stata-mp -b do 02_data/clean.do

echo "Step 3/4: run analyses"
# python3 03_analysis/estimate.py
# Rscript 03_analysis/estimate.R
# stata-mp -b do 03_analysis/estimate.do

echo "Step 4/4: build tables and figures"
# python3 03_analysis/build_exhibits.py

echo "Done. Compare 04_results/ against REPLICATION.md Section 6."
