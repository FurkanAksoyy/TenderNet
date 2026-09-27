"""Observed-history sensitivity with equal 730-day past/future observation windows.

This is an outcome-derived association diagnostic, not a causal negative control.
Retains original, strictly prior 24-month alternative pools and full history controls.
"""
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
import json
from pathlib import Path
import numpy as np
import pandas as pd
import revision_d as D

OUT = Path(__file__).resolve().parents[1] / "results" / "revision_e_horizons"


def window_flags(dates, current, horizon):
    """Exclude awards on the current date from both directions."""
    past = np.searchsorted(dates, current, "left") - np.searchsorted(dates, current-horizon, "left")
    future = np.searchsorted(dates, current+horizon, "right") - np.searchsorted(dates, current, "right")
    return int(past > 0), int(past == 0 and future > 0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert window_flags(np.array([0, 10, 20]), 10, 5) == (0, 0)
    assert window_flags(np.array([0, 10, 20]), 10, 10) == (1, 0)
    assert window_flags(np.array([10, 20]), 10, 10) == (0, 1)
    P, H, C = D.data()
    horizon = 730
    first, last = int(P["day"].min()), int(P["day"].max())
    days = P["day"][C.contract.to_numpy()]
    C = C[(days >= first+horizon) & (days <= last-horizon)].copy()
    flags = []
    for i, j in zip(C.contract, C.firm):
        dates = H.fkm.get((j, P["buyer"][i], P["mkt"][i]), np.empty(0, int))
        flags.append(window_flags(dates, int(P["day"][i]), horizon))
    C[["past_730", "future_730_only"]] = np.asarray(flags)
    tables, counts = [], []
    for label, sub in [("all", C), ("recurring", C[C.renewal == "renewal"]),
                       ("other", C[C.renewal == "new need"])]:
        cols = ["past_730", "future_730_only"] + D.OTH
        prep = D.Prep(sub, cols)
        beta, variance = prep.fit()
        tab = D.or_row(beta, variance, cols, label)
        tab["n_contracts"] = prep.n_con
        tables.append(tab)
        chosen = sub[sub.chosen == 1]
        counts.append(dict(sample=label, n_contracts=prep.n_con,
                           chosen_past=int(chosen.past_730.sum()),
                           chosen_future_only=int(chosen.future_730_only.sum()),
                           **D.contrast(beta, variance, 0, 1)))
    pd.concat(tables).to_csv(OUT / "symmetric_choice.csv", index=False)
    pd.DataFrame(counts).to_csv(OUT / "symmetric_contrasts.csv", index=False)
    audit = dict(horizon_days=horizon, original_modeled_contracts=3013,
                 bounded_contracts=int(C.contract.nunique()),
                 minimum_day=first, maximum_day=last,
                 note="Both windows exclude same-day awards, include the 730-day endpoints, and are wholly within the observed extract. A future-only pair has no award in the preceding 730 days; it may have older awards. Controls retain full observed history. Equal observation windows do not solve omitted pre-extract history, selection into recent-winner pools, or causal identification.")
    (OUT / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(pd.DataFrame(counts).to_string(index=False))
    print(pd.concat(tables).query("variable in ['past_730','future_730_only']").to_string(index=False))


if __name__ == "__main__":
    main()
