# Computational Environment Record

Project: <short name>
Captured (Beijing): <YYYY-MM-DD HH:MM>
Analysis backend: python-statspai / stata / r

Purpose: make the environment rebuildable, not just describable. Pick the highest
pinning level you can reach (see `references/computational-reproducibility.md` §1)
and record it in `workflow_state.json.replication_pack.env_level`.

## 1. Pinning Level Reached

- [ ] L0 — versions listed only (minimum, brittle)
- [ ] L1 — lockfile committed (DEFAULT requirement)
- [ ] L2 — container image / Code Ocean capsule (preferred for AEA / long-term archive)
- [ ] L3 — fully declarative (Nix / Binder)

Declared level: <L0 / L1 / L2 / L3>

## 2. Software and Hardware

- Operating system + version:
- CPU / cores / RAM:
- GPU (if ML used): model + CUDA/cuDNN version, or "none"
- BLAS implementation (Python): OpenBLAS / MKL / Accelerate
- Total wall-clock to run master script:
- Peak disk usage:

## 3. Backend Version and Lockfile

### python-statspai
- Python version: `python3 --version`
- Lockfile: `requirements.txt` (from `pip freeze`) or `environment.yml` (`conda env export`)
- Key packages + versions: statspai=<>, numpy=<>, pandas=<>, scipy=<>, ...

### stata
- `version` set in code: <e.g. version 18>
- Stata flavor + version: <SE/MP, 18.0>
- Community packages (record source + install date): reghdfe=<>, csdid=<>, ... (`which`, `net describe`, `ssc`)

### r
- R version + `RNGkind()`: <4.x; Mersenne-Twister, Rejection>
- Lockfile: `renv.lock`
- Key packages + versions: fixest=<>, did=<>, modelsummary=<>, ...

## 4. Controlled Randomness (seed registry)

| Step | File:line | RNG / seed | Notes |
|---|---|---|---|
| <bootstrap / cross-fit / placebo / simulation> | 03_analysis/<script>:<line> | seed=<value> |  |

## 5. Determinism Settings Applied

(see computational-reproducibility.md §2 — set these in the master script before running)

- [ ] `PYTHONHASHSEED=0`
- [ ] `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `VECLIB_MAXIMUM_THREADS=1`, `NUMEXPR_NUM_THREADS=1`
- [ ] `LC_ALL=C` (stable sort / number formatting)
- [ ] R: `RNGkind(sample.kind="Rejection")` set explicitly for cross-version `sample()`
- [ ] GPU determinism flags set, or "results reproducible within tolerance only" declared
- [ ] Stable sort + explicit tie-break keys on order-dependent operations

## 6. Rebuild Instructions

```bash
# L1 example (python)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash run_all.sh            # captures env, sets determinism, runs, checks outputs
```

Last clean-room rebuild check: <YYYY-MM-DD: deleted derived outputs, ran master script, check_outputs.py passed>
</content>
