"""Independent terminal-score audit of saved and refitted observed choice models.

No bootstrap or simulations. Outputs diagnostic CSV/JSON; exits nonzero for a
material score, Newton correction, ill-conditioning or coefficient discrepancy.
"""
import os
for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"
import json
from pathlib import Path
import numpy as np
import pandas as pd
import revision_d as D
from revision_e_horizons import window_flags

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/revision_e_numerics"


def diagnostics(prep, beta):
    """Evaluate likelihood derivatives independently of the custom optimizer."""
    X, y, g, n = prep.X, prep.y, prep.g, prep.n_con
    eta = X @ beta
    starts = np.r_[0, np.flatnonzero(np.diff(g)) + 1]
    maxima = np.maximum.reduceat(eta, starts)
    unnormalized = np.exp(eta - maxima[g])
    den = np.add.reduceat(unnormalized, starts)
    probability = unnormalized / den[g]
    mean = np.add.reduceat(X * probability[:, None], starts, axis=0)
    score = X.T @ (y - probability)
    centered = X - mean[g]
    information = centered.T @ (centered * probability[:, None])
    eigen = np.linalg.eigvalsh(information)
    correction = np.linalg.solve(information, score)
    return dict(n_contracts=n, n_alternatives=len(y), parameters=X.shape[1],
                max_abs_score=float(np.max(np.abs(score))),
                max_abs_score_per_contract=float(np.max(np.abs(score)) / n),
                max_abs_newton_correction=float(np.max(np.abs(correction))),
                information_eigen_min=float(eigen.min()),
                information_eigen_max=float(eigen.max()),
                information_condition=float(eigen.max() / eigen.min()),
                log_likelihood=float(y @ eta - np.sum(np.log(den) + maxima)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    P, H, C = D.data()
    saved = pd.read_csv(ROOT / "results/revision_d/D1_observed_clogit.csv")
    rows = []

    def audit(data, cols, model, table, saved_model):
        prep = D.Prep(data, cols)
        old = table[table.model == saved_model].set_index("variable").loc[cols, "coef"].to_numpy()
        fitted, _ = prep.fit(V=False)
        discrepancy = float(np.max(np.abs(fitted - old)))
        for label, beta in (("saved", old), ("refit", fitted)):
            row = dict(model=model, estimate=label, max_abs_refit_difference=discrepancy,
                       **diagnostics(prep, beta))
            row["pass"] = bool(row["max_abs_score_per_contract"] < 1e-7
                               and row["max_abs_newton_correction"] < 1e-5
                               and 0 < row["information_condition"] < 1e10
                               and row["information_eigen_min"] > 0
                               and discrepancy < 1e-5)
            rows.append(row)
        print(model, "PASS" if all(r["pass"] for r in rows[-2:]) else "FAIL", flush=True)

    for sample, sub in (("all", C), ("renewals", C[C.renewal == "renewal"]),
                        ("new needs", C[C.renewal == "new need"])):
        for name, cols in (("main", D.MAIN), ("plac", D.PLAC), ("le", D.LE)):
            audit(sub, cols, f"observed {sample} | {name}", saved, f"observed {sample} | {name}")

    first, last = int(P["day"].min()), int(P["day"].max())
    days = P["day"][C.contract.to_numpy()]
    bounded = C[(days >= first + 730) & (days <= last - 730)].copy()
    flags = [window_flags(H.fkm.get((j, P["buyer"][i], P["mkt"][i]), np.empty(0, int)),
                          int(P["day"][i]), 730) for i, j in zip(bounded.contract, bounded.firm)]
    bounded[["past_730", "future_730_only"]] = np.asarray(flags)
    saved_window = pd.read_csv(ROOT / "results/revision_e_horizons/symmetric_choice.csv")
    for sample, sub in (("all", bounded), ("recurring", bounded[bounded.renewal == "renewal"]),
                        ("other", bounded[bounded.renewal == "new need"])):
        audit(sub, ["past_730", "future_730_only"] + D.OTH,
              f"symmetric 730d | {sample}", saved_window, sample)
    table = pd.DataFrame(rows)
    table.to_csv(OUT / "observed_choice_numerics.csv", index=False)
    summary = dict(fits=12, diagnostic_rows=len(table), all_pass=bool(table["pass"].all()),
                   maximum_score_per_contract=float(table.max_abs_score_per_contract.max()),
                   maximum_newton_correction=float(table.max_abs_newton_correction.max()),
                   maximum_information_condition=float(table.information_condition.max()),
                   maximum_refit_difference=float(table.max_abs_refit_difference.max()),
                   scope="Saved and refitted observed models only; no bootstrap or simulation-fit guarantee.")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not summary["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
