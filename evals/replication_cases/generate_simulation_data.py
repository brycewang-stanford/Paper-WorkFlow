#!/usr/bin/env python3
"""Deterministic DGP generators for the five China-scenario simulation cases.

Why this exists
---------------
The replication suite's integrity rule says a gold value is a *measured fact*,
never a guess. For the transcribed cases (Card-Krueger 1994, Card 1995, NSW)
the fact lives in a published table. For the five "Own simulation" cases the
fact is the data-generating process itself — which used to exist only as prose
in each case's `gold_source`. This script makes those DGPs executable, so every
simulation gold is mechanically recomputable:

  - the TRUE parameters are declared once in TRUTHS below;
  - `--verify` cross-checks TRUTHS against the shipped case JSONs (stdlib only,
    run by the validate_skill battery via `--selftest`);
  - `--case <id> --out <dir>` regenerates the actual panel (needs numpy/pandas
    from requirements-dev.txt), seed=42 as documented in each gold_source.

Estimation-dependent golds (`smd_max`, `rosenbaum_lower_bound` in the PSM-DID
case) are properties of the matching pipeline, not of the DGP alone; they are
listed in ESTIMATION_DEPENDENT and exempted from --verify.

Usage
-----
    python3 evals/replication_cases/generate_simulation_data.py --verify
    python3 evals/replication_cases/generate_simulation_data.py --truth --case spatial_sdm_simulation
    python3 evals/replication_cases/generate_simulation_data.py --case all --out /tmp/sim_data
    python3 evals/replication_cases/generate_simulation_data.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 42

# --------------------------------------------------------------------------- #
# The declared truths. These ARE the gold values (single source).             #
# --------------------------------------------------------------------------- #
TRUTHS: dict[str, dict] = {
    "digital_economy_pilot_simulation": {
        "coefficients": {"att": 0.08, "leads_avg": 0.0},
        "dgp": "50 cities, 4 adoption cohorts (2017/2019/2020/2021, 10 each) "
               "+ 10 never-treated; log-TFP outcome; TRUE_ATT=0.08 per treated "
               "period, no anticipation (leads average 0 by construction).",
    },
    "digital_transformation_psm_did_simulation": {
        "coefficients": {"att_psm_did": 0.05},
        "dgp": "1500 A-share firms, 2010-2022; treatment = report word-freq "
               "score above median (score depends on observed covariates); "
               "TRUE_ATT=0.05 on post-2016 outcomes.",
    },
    "regional_compete_threshold_simulation": {
        "coefficients": {"gamma_threshold": 11.0, "beta_low_regime": 0.10,
                         "beta_high_regime": 0.45},
        "dgp": "280 prefecture cities x 12 years (2010-2021); threshold var "
               "q = log per-capita GDP; TRUE_gamma=log(60000)~11.0.",
    },
    "spatial_sdm_simulation": {
        # indirect_effect is the analytic LeSage-Pace value implied by
        # (rho, beta, theta) and the row-standardized queen W on the 5x6 city
        # grid: total=(beta+theta)/(1-rho)=1.2857, direct=0.5333 -> indirect
        # =0.7524. Recomputed by --effects / --selftest when numpy is present.
        "coefficients": {"rho": 0.3, "beta_direct": 0.5, "theta_wx": 0.4,
                         "indirect_effect": 0.75},
        "dgp": "Y = rho W Y + X beta + W X theta + eps; 30 cities (5x6 queen "
               "grid, row-standardized) x 20 years.",
    },
    "threshold_panel_simulation": {
        "coefficients": {"gamma_threshold": 1.0, "beta_below": 0.5,
                         "beta_above": 1.5},
        "dgp": "Y_it = a_i + b1 X I(q<=gamma) + b2 X I(q>gamma) + eps; "
               "N=500, T=10 balanced.",
    },
}

# Golds that depend on the estimation pipeline (matching quality, bounds), not
# on the DGP constants alone — the generator cannot verify these.
ESTIMATION_DEPENDENT: dict[str, set[str]] = {
    "digital_transformation_psm_did_simulation": {"smd_max", "rosenbaum_lower_bound"},
}

SPATIAL_GRID = (5, 6)  # 30 cities
SPATIAL_ANALYTIC_TOL = 0.01  # |stored 0.75 - recomputed| must be within this


# --------------------------------------------------------------------------- #
# verification (stdlib only)                                                  #
# --------------------------------------------------------------------------- #
def verify_against_cases() -> list[str]:
    """Every DGP-derived gold in the case JSONs must equal TRUTHS. Returns problems."""
    problems: list[str] = []
    for case_id, truth in TRUTHS.items():
        path = HERE / f"{case_id}.json"
        if not path.exists():
            problems.append(f"{case_id}: case file missing: {path.name}")
            continue
        case = json.loads(path.read_text(encoding="utf-8"))
        exempt = ESTIMATION_DEPENDENT.get(case_id, set())
        declared = truth["coefficients"]
        for coeff in case["primary_coefficients"]:
            name = coeff["name"]
            if name in exempt:
                continue
            if name not in declared:
                problems.append(f"{case_id}: gold '{name}' has no declared DGP truth")
                continue
            if abs(float(coeff["value"]) - declared[name]) > 1e-9:
                problems.append(
                    f"{case_id}: gold {name}={coeff['value']} != DGP truth {declared[name]}"
                )
        for name in declared:
            if name not in {c["name"] for c in case["primary_coefficients"]}:
                problems.append(f"{case_id}: declared truth '{name}' missing from case golds")
        if "generate_simulation_data.py" not in case.get("gold_source", ""):
            problems.append(f"{case_id}: gold_source does not reference this generator")
    return problems


# --------------------------------------------------------------------------- #
# data generation (numpy/pandas; requirements-dev.txt)                        #
# --------------------------------------------------------------------------- #
def _queen_w():
    import numpy as np

    rows, cols = SPATIAL_GRID
    n = rows * cols
    W = np.zeros((n, n))
    for i in range(rows):
        for j in range(cols):
            a = i * cols + j
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == dj == 0:
                        continue
                    ni, nj = i + di, j + dj
                    if 0 <= ni < rows and 0 <= nj < cols:
                        W[a, ni * cols + nj] = 1.0
    return W / W.sum(axis=1, keepdims=True)


def spatial_analytic_effects() -> dict[str, float]:
    """LeSage-Pace average direct/indirect/total implied by the DGP constants."""
    import numpy as np

    t = TRUTHS["spatial_sdm_simulation"]["coefficients"]
    rho, beta, theta = t["rho"], t["beta_direct"], t["theta_wx"]
    W = _queen_w()
    n = W.shape[0]
    S = np.linalg.inv(np.eye(n) - rho * W) @ (beta * np.eye(n) + theta * W)
    direct = float(np.mean(np.diag(S)))
    total = float(S.sum() / n)
    return {"direct": round(direct, 4), "indirect": round(total - direct, 4),
            "total": round(total, 4)}


def _gen_digital_economy(rng):
    import numpy as np
    import pandas as pd

    att = TRUTHS["digital_economy_pilot_simulation"]["coefficients"]["att"]
    cities, years = 50, list(range(2014, 2024))
    cohorts = {**{c: 2017 for c in range(10)}, **{c: 2019 for c in range(10, 20)},
               **{c: 2020 for c in range(20, 30)}, **{c: 2021 for c in range(30, 40)}}
    rows = []
    fe_city = rng.normal(0, 0.3, cities)
    fe_year = {y: 0.02 * (y - 2014) + rng.normal(0, 0.02) for y in years}
    for c in range(cities):
        g = cohorts.get(c, 0)  # 0 = never treated
        for y in years:
            treated = int(g and y >= g)
            rows.append({"city": c, "year": y, "cohort": g,
                         "treat_post": treated,
                         "log_tfp": fe_city[c] + fe_year[y] + att * treated
                         + rng.normal(0, 0.05)})
    return pd.DataFrame(rows)


def _gen_psm_did(rng):
    import numpy as np
    import pandas as pd

    att = TRUTHS["digital_transformation_psm_did_simulation"]["coefficients"]["att_psm_did"]
    n = 1500
    x1, x2, x3 = rng.normal(size=n), rng.normal(size=n), rng.normal(size=n)
    score = 0.6 * x1 + 0.4 * x2 + rng.normal(0, 1, n)  # word-freq score
    treat = (score > np.median(score)).astype(int)
    y_pre = 0.5 * x1 + 0.3 * x2 + 0.2 * x3 + rng.normal(0, 0.3, n)
    y_post = y_pre + 0.1 + att * treat + rng.normal(0, 0.3, n)
    return pd.DataFrame({"firm": range(n), "x1": x1, "x2": x2, "x3": x3,
                         "wordfreq_score": score, "treat": treat,
                         "y_pre": y_pre, "y_post": y_post})


def _gen_regional_threshold(rng):
    import numpy as np
    import pandas as pd

    t = TRUTHS["regional_compete_threshold_simulation"]["coefficients"]
    n, T = 280, 12
    rows = []
    fe = rng.normal(0, 0.5, n)
    for i in range(n):
        base_gdp = rng.normal(11.0, 0.8)
        for yr in range(2010, 2010 + T):
            q = base_gdp + 0.03 * (yr - 2010) + rng.normal(0, 0.1)
            x = rng.normal(1, 0.5)
            beta = t["beta_low_regime"] if q <= t["gamma_threshold"] else t["beta_high_regime"]
            rows.append({"city": i, "year": yr, "log_gdp_pc": q, "transparency": x,
                         "fiscal_competition": fe[i] + beta * x + rng.normal(0, 0.2)})
    return pd.DataFrame(rows)


def _gen_spatial_sdm(rng):
    import numpy as np
    import pandas as pd

    t = TRUTHS["spatial_sdm_simulation"]["coefficients"]
    W = _queen_w()
    n = W.shape[0]
    A_inv = np.linalg.inv(np.eye(n) - t["rho"] * W)
    rows = []
    for yr in range(2004, 2024):
        x = rng.normal(size=n)
        eps = rng.normal(0, 0.2, n)
        y = A_inv @ (t["beta_direct"] * x + t["theta_wx"] * (W @ x) + eps)
        for i in range(n):
            rows.append({"city": i, "year": yr, "x": x[i], "y": y[i]})
    return pd.DataFrame(rows)


def _gen_threshold_panel(rng):
    import numpy as np
    import pandas as pd

    t = TRUTHS["threshold_panel_simulation"]["coefficients"]
    n, T = 500, 10
    fe = rng.normal(0, 1, n)
    rows = []
    for i in range(n):
        for yr in range(T):
            q = rng.normal(1.0, 0.6)
            x = rng.normal(1, 0.5)
            beta = t["beta_below"] if q <= t["gamma_threshold"] else t["beta_above"]
            rows.append({"unit": i, "t": yr, "q": q, "x": x,
                         "y": fe[i] + beta * x + rng.normal(0, 0.3)})
    return pd.DataFrame(rows)


GENERATORS = {
    "digital_economy_pilot_simulation": _gen_digital_economy,
    "digital_transformation_psm_did_simulation": _gen_psm_did,
    "regional_compete_threshold_simulation": _gen_regional_threshold,
    "spatial_sdm_simulation": _gen_spatial_sdm,
    "threshold_panel_simulation": _gen_threshold_panel,
}


def generate(case_id: str, out_dir: Path) -> Path:
    import numpy as np

    rng = np.random.default_rng(SEED)
    df = GENERATORS[case_id](rng)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{case_id}.csv"
    df.to_csv(out, index=False)
    return out


# --------------------------------------------------------------------------- #
# selftest                                                                    #
# --------------------------------------------------------------------------- #
def _selftest() -> int:
    problems = verify_against_cases()
    assert not problems, f"gold/truth drift: {problems}"
    assert set(GENERATORS) == set(TRUTHS), "every truth must have a generator"

    try:
        import numpy  # noqa: F401
        import pandas  # noqa: F401
    except ImportError:
        print("selftest OK: DGP truths match case golds "
              "(numpy/pandas absent; generation smoke-test skipped)")
        return 0

    import tempfile

    eff = spatial_analytic_effects()
    stored = TRUTHS["spatial_sdm_simulation"]["coefficients"]["indirect_effect"]
    assert abs(eff["indirect"] - stored) <= SPATIAL_ANALYTIC_TOL, (
        f"stored indirect_effect {stored} drifted from analytic {eff['indirect']}"
    )

    with tempfile.TemporaryDirectory(prefix="dgp-selftest-") as tmp:
        out = Path(tmp)
        expected_rows = {
            "digital_economy_pilot_simulation": 50 * 10,
            "digital_transformation_psm_did_simulation": 1500,
            "regional_compete_threshold_simulation": 280 * 12,
            "spatial_sdm_simulation": 30 * 20,
            "threshold_panel_simulation": 500 * 10,
        }
        for case_id, n_rows in expected_rows.items():
            path = generate(case_id, out)
            got = sum(1 for _ in path.open()) - 1
            assert got == n_rows, f"{case_id}: {got} rows, expected {n_rows}"
        # determinism: same seed -> identical bytes
        a = (out / "threshold_panel_simulation.csv").read_bytes()
        b = generate("threshold_panel_simulation", out / "again").read_bytes()
        assert a == b, "generation must be deterministic under the fixed seed"

    print("selftest OK: DGP truths match case golds; generation is deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--case", help="case id, or 'all'")
    p.add_argument("--out", help="output directory for generated CSVs")
    p.add_argument("--truth", action="store_true", help="print declared truths as JSON")
    p.add_argument("--effects", action="store_true",
                   help="recompute the SDM analytic direct/indirect effects (needs numpy)")
    p.add_argument("--verify", action="store_true",
                   help="cross-check TRUTHS against the shipped case JSONs")
    p.add_argument("--selftest", action="store_true", help="run built-in invariant tests")
    args = p.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.verify:
        problems = verify_against_cases()
        for prob in problems:
            print(f"PROBLEM: {prob}", file=sys.stderr)
        print("VERIFY OK" if not problems else "VERIFY FAILED")
        return 1 if problems else 0
    if args.effects:
        print(json.dumps(spatial_analytic_effects(), indent=2))
        return 0
    if args.truth:
        wanted = TRUTHS if not args.case or args.case == "all" else {args.case: TRUTHS[args.case]}
        print(json.dumps(wanted, ensure_ascii=False, indent=2))
        return 0
    if args.case:
        ids = list(GENERATORS) if args.case == "all" else [args.case]
        out_dir = Path(args.out) if args.out else HERE / "generated"
        for cid in ids:
            if cid not in GENERATORS:
                p.error(f"unknown case: {cid} (known: {', '.join(GENERATORS)})")
            print(f"wrote {generate(cid, out_dir)}")
        return 0
    p.error("need --case, --truth, --effects, --verify, or --selftest")


if __name__ == "__main__":
    raise SystemExit(main())
