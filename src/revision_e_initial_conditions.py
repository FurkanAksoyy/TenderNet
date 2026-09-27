"""Initialization sensitivity for descriptive simulated choice diagnostics.

Uses revision_d's sequential engine without editing it. This is not structural
estimation. All scenarios retain observed alternative pools and fixed awards;
all history covariates are recomputed. The shifted scenarios are deliberately
ad hoc initialization assumptions, not posterior random-effect distributions.

Run: python src/revision_e_initial_conditions.py --reps 100 --cal-reps 20
"""
import os
for _name in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd
import revision_d as D

OUT = Path(__file__).resolve().parents[1] / "results" / "revision_e_initial_conditions"
SCENARIOS = ("legacy_all_fixed", "no_tilt", "pre_first_simulated")
SEED = 9272026


class SensitivitySim(D.Sim):
    share_only = False

    def _assemble(self, simf, hist, Xr, lags):
        if not self.share_only:
            return super()._assemble(simf, hist, Xr, lags)
        P = self.P
        hits = [any(d < P["day"][i] and f == simf[i] for d, f in hist[P["bm"][i]])
                for i in self.sl]
        return float(np.mean(hits)), None


def initialization_masks(sim):
    """Use the identical pair ordering as D.Sim; early means strictly earlier.

    The history window ends separately for each buyer at its first modeled
    award, across markets. Other fixed outcomes never enter the early mask.
    """
    P = sim.P
    nf = int(P["nf"])
    rows = sim.bu.astype(np.int64) * nf + sim.firms
    fixed = np.array([i for i in range(len(P["day"])) if i not in sim.sl])
    fixed_keys = P["buyer"][fixed].astype(np.int64) * nf + P["firm"][fixed]
    keys = np.unique(np.r_[rows, fixed_keys])
    start = {}
    for i in sim.sl:
        k, t = int(P["buyer"][i]), int(P["day"][i])
        start[k] = min(start.get(k, t), t)
    early = np.array([P["day"][i] < start.get(int(P["buyer"][i]), -np.inf) for i in fixed])
    masks = dict(legacy_all_fixed=np.isin(keys, fixed_keys),
                 no_tilt=np.zeros(len(keys), dtype=bool),
                 pre_first_simulated=np.isin(keys, fixed_keys[early]))
    assert np.array_equal(masks["legacy_all_fixed"], sim.tilt)
    assert np.all(~masks["pre_first_simulated"] | masks["legacy_all_fixed"])
    chosen = sim.C.chosen.to_numpy() == 1
    audit = dict(total_contracts=len(P["day"]), simulated_contracts=len(sim.sl),
                 fixed_contracts=len(fixed), fixed_before_buyer_start=int(early.sum()),
                 pair_count=len(keys), candidate_rows=len(rows),
                 note="Pooled simulations: no opposite-subgroup contracts are frozen separately. Observed alternative pools and all excluded awards remain fixed.")
    for name, mask in masks.items():
        rowmask = mask[sim.rowpair]
        audit[name] = dict(tilted_pairs=int(mask.sum()), candidate_row_share=float(rowmask.mean()),
                           observed_winner_row_share=float(rowmask[chosen].mean()))
    audit["legacy_only_after_start_pairs"] = int((masks["legacy_all_fixed"] & ~masks["pre_first_simulated"]).sum())
    return masks, audit


def calibrate(sim, beta, target, reps, scenario):
    """Share-only common-random-number calibration; never hide non-attainment."""
    # Always calibrate afresh. A matching target/repetition count cannot certify
    # unchanged data, fitted coefficients, code, or random seeds.
    records = []

    def evaluate(sigma):
        shares = []
        for r in range(reps):
            sim.share_only = True
            share, _ = sim.run(beta, np.random.default_rng(SEED + r), sigma=sigma, recompute=True)
            shares.append(share)
            sim.share_only = False
        mean = float(np.mean(shares))
        records.append(dict(scenario=scenario, sigma=sigma, target=target, share_mean=mean,
                            share_sd=float(np.std(shares, ddof=1)) if reps > 1 else None,
                            reps=reps))
        print(f"{scenario} calibration sigma={sigma:.4f} share={mean:.4f} target={target:.4f}", flush=True)
        pd.DataFrame(records).to_csv(OUT / f"calibration_{scenario}.csv", index=False)
        return mean

    prev_sigma, prev_share = 0.0, evaluate(0.0)
    if prev_share >= target:
        return 0.0, "target_at_or_below_zero_sigma", records
    for sigma in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0):
        share = evaluate(sigma)
        if share >= target:
            lo, hi = prev_sigma, sigma
            for _ in range(4):
                mid = (lo + hi) / 2
                midshare = evaluate(mid)
                if midshare < target:
                    lo = mid
                else:
                    hi = mid
            final = (lo + hi) / 2
            final_share = evaluate(final)
            return final, ("matched_within_0.01" if abs(final_share - target) <= 0.01 else "bracketed_not_within_0.01"), records
        prev_sigma, prev_share = sigma, share
    # Results at the ceiling are explicitly an unmatched scenario, not a fit.
    return 10.0, "target_not_attained_by_sigma_10", records


def main():
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--reps", type=int, default=100)
    parser.add_argument("--cal-reps", type=int, default=20)
    parser.add_argument("--scenarios", nargs="+", choices=SCENARIOS, default=list(SCENARIOS))
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if args.reps < 1 or args.cal_reps < 1:
        parser.error("--reps and --cal-reps must be positive")
    OUT = args.output
    OUT.mkdir(parents=True, exist_ok=True)
    began = time.monotonic()
    P, _, C = D.data()
    sim = SensitivitySim(P, C)
    masks, audit = initialization_masks(sim)
    json.dump(audit, open(OUT / "conditioning_audit.json", "w", encoding="utf-8"), indent=2)
    bfit, _ = D.Prep(C, D.MAIN).fit(V=False)
    target = float(C.loc[C.chosen == 1, "incumbent"].mean())
    beta = bfit.copy()
    beta[0] = 0.0
    observed = D.moments(C, "observed", V=False)
    if args.benchmark:
        start = time.monotonic()
        trial, inc = sim.run(beta, np.random.default_rng(SEED), sigma=3.0, recompute=True)
        gen_seconds = time.monotonic() - start
        D.moments(trial, "benchmark", V=False)
        full_seconds = time.monotonic()-start
        sim.share_only = True
        start_share = time.monotonic()
        share, _ = sim.run(beta, np.random.default_rng(SEED), sigma=3.0, recompute=True)
        assert share == float(trial.loc[trial.chosen == 1, "incumbent"].mean())
        print(json.dumps(dict(build_seconds=start-began, simulation_seconds=gen_seconds,
                              simulation_plus_fits_seconds=full_seconds,
                              share_only_seconds=time.monotonic()-start_share, inc_all=inc)), flush=True)
        return
    provenance = dict(arguments=vars(args), seed=SEED, target_share=target,
                      fitted_coefficients=bfit.tolist(), generating_coefficients=beta.tolist(),
                      covariates_recomputed=True, observed_pools_fixed=True,
                      note="No tilt or shifted normal initialization is an assumption, not a posterior correction. Conditional replication quantiles are not parameter confidence intervals.",
                      source_sha256={f: hashlib.sha256((Path(__file__).parent/f).read_bytes()).hexdigest()
                                     for f in ("revision_c.py", "revision_d.py", Path(__file__).name)})
    json.dump(provenance, open(OUT / "provenance.json", "w", encoding="utf-8"), indent=2, default=str)
    json.dump(observed, open(OUT / "observed.json", "w", encoding="utf-8"), indent=2)
    summary = []
    for scenario in args.scenarios:
        sim.tilt = masks[scenario]
        sigma, status, _ = calibrate(sim, beta, target, args.cal_reps, scenario)
        rows = []
        for r in range(args.reps):
            Cs, inc_all = sim.run(beta, np.random.default_rng(SEED + 10000 + r), sigma=sigma, recompute=True)
            m = D.moments(Cs, "sensitivity", V=False)
            rows.append(dict(scenario=scenario, sigma=sigma, calibration_status=status,
                             rep=r, incumbency_all_eligible=inc_all, **m))
            pd.DataFrame(rows).to_csv(OUT / f"replications_{scenario}.csv", index=False)
            if r % 10 == 0:
                print(f"{scenario} replication {r+1}/{args.reps}; elapsed {time.monotonic()-began:.1f}s", flush=True)
        frame = pd.DataFrame(rows)
        for metric in list(observed) + ["incumbency_all_eligible"]:
            values = frame[metric]
            summary.append(dict(scenario=scenario, sigma=sigma, calibration_status=status,
                                metric=metric, observed=observed.get(metric), mean=float(values.mean()),
                                p025=float(values.quantile(.025)), p975=float(values.quantile(.975)), reps=len(frame)))
        pd.DataFrame(summary).to_csv(OUT / "summary.csv", index=False)
    print(f"Finished in {time.monotonic()-began:.1f}s", flush=True)


if __name__ == "__main__":
    main()
