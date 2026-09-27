"""Validate and combine the three isolated initialization sensitivity runs."""
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
SCENARIOS = ["legacy_all_fixed", "no_tilt", "pre_first_simulated"]
summaries, replications, calibrations, manifest = [], [], [], {}
for scenario in SCENARIOS:
    folder = ROOT / scenario
    reps = pd.read_csv(folder / f"replications_{scenario}.csv")
    assert len(reps) == 100 and set(reps.rep) == set(range(100))
    assert np.isfinite(reps.select_dtypes("number").to_numpy()).all()
    summary = pd.read_csv(folder / "summary.csv")
    assert (summary.reps == 100).all()
    provenance = json.loads((folder / "provenance.json").read_text())
    assert provenance["arguments"]["reps"] == 100
    assert provenance["arguments"]["cal_reps"] == 20
    assert provenance["covariates_recomputed"]
    summaries.append(summary)
    replications.append(reps)
    calibrations.append(pd.read_csv(folder / f"calibration_{scenario}.csv"))
    manifest[scenario] = {
        "provenance": str((folder / "provenance.json").relative_to(ROOT)),
        "files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in folder.iterdir() if p.suffix in (".csv", ".json")},
        "source_sha256": provenance["source_sha256"],
    }
    assert provenance["source_sha256"]["revision_e_initial_conditions.py"] == hashlib.sha256(
        (ROOT / "source_used_for_parallel_runs.py").read_bytes()).hexdigest()

summary = pd.concat(summaries, ignore_index=True)
summary.to_csv(ROOT / "summary.csv", index=False)
pd.concat(replications, ignore_index=True).to_csv(ROOT / "replications.csv", index=False)
pd.concat(calibrations, ignore_index=True).to_csv(ROOT / "calibrations.csv", index=False)
json.dump(manifest, open(ROOT / "aggregate_manifest.json", "w"), indent=2)

metrics = ["share_chosen_incumbent", "OR_future_only", "past_future_ratio", "last_earlier_ratio"]
lines = ["# Initial-condition sensitivity: completed results", "",
         "All scenarios set the explicit same-market incumbency coefficient to zero, retain other fitted coefficients, and recompute every history covariate. Observed alternative pools and 6,978 excluded awards remain fixed. The 3,013 modeled awards are simulated jointly, without freezing renewal/new-need subgroups separately.", "",
         "Each scenario uses 20 draws per calibration point and 100 independent evaluation draws. Seeds are shared across scenarios. Calibration targets the observed chosen-incumbent share, 0.689346. Intervals below are conditional simulation quantiles, not confidence intervals for structural parameters.", "",
         "| Initialization | Sigma | Calibration | Incumbent share | Future OR | Past/future ratio | Recency ratio |",
         "|---|---:|---|---:|---:|---:|---:|"]
for scenario in SCENARIOS:
    sub = summary[summary.scenario == scenario].set_index("metric")
    cells = [f"{sub.loc[m, 'mean']:.3f} [{sub.loc[m, 'p025']:.3f}, {sub.loc[m, 'p975']:.3f}]" for m in metrics]
    lines.append(f"| {scenario} | {sub.iloc[0].sigma:.5f} | {sub.iloc[0].calibration_status} | " + " | ".join(cells) + " |")
lines += ["", "The no-tilt scenario did not reach the calibration target at any tested sigma through 10. Its reported evaluation is explicitly the unmatched ceiling scenario; it is not a fitted alternative or an upper bound on what unrestricted heterogeneity can explain.", "",
          "The pre-first-simulated rule shifts only pairs with a fixed observed award strictly before that buyer's first modeled award. The legacy rule shifts pairs winning any fixed award, including later ones. Neither shifted-normal rule is the multinomial-logit posterior conditional on observed choices; the unconditional rule likewise assumes independence from the observed initial awards. These are initialization sensitivities, not identified mechanisms.", "",
          "The final driver performs fresh calibration by default; generated results used the preserved source snapshot source_used_for_parallel_runs.py. The legacy run resumed eight completed calibration points from a prior driver version; source_used_for_resumed_calibration.py matches that original provenance hash. Engine snapshots and per-scenario provenance preserve the exact generating versions. The cache fix changes reuse behavior, not simulation equations.", "",
          "Validation: 100 unique evaluation draws per scenario, finite numeric outputs, common calibration target, source snapshot hashes matched, and share-only calibration exactly matched the full assembled share for an identical random seed in a benchmark assertion."]
(ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(summary[summary.metric.isin(metrics)].to_string(index=False))
