# Initial-condition sensitivity: completed results

All scenarios set the explicit same-market incumbency coefficient to zero, retain other fitted coefficients, and recompute every history covariate. Observed alternative pools and 6,978 excluded awards remain fixed. The 3,013 modeled awards are simulated jointly, without freezing renewal/new-need subgroups separately.

Each scenario uses 20 draws per calibration point and 100 independent evaluation draws. Seeds are shared across scenarios. Calibration targets the observed chosen-incumbent share, 0.689346. Intervals below are conditional simulation quantiles, not confidence intervals for structural parameters.

| Initialization | Sigma | Calibration | Incumbent share | Future OR | Past/future ratio | Recency ratio |
|---|---:|---|---:|---:|---:|---:|
| legacy_all_fixed | 2.90625 | matched_within_0.01 | 0.694 [0.682, 0.707] | 43.043 [32.764, 54.557] | 1.595 [1.303, 2.017] | 2.445 [2.035, 3.164] |
| no_tilt | 10.00000 | target_not_attained_by_sigma_10 | 0.348 [0.334, 0.361] | 104.772 [89.904, 123.067] | 0.312 [0.271, 0.347] | 4.617 [3.941, 5.390] |
| pre_first_simulated | 3.40625 | matched_within_0.01 | 0.692 [0.680, 0.704] | 40.357 [30.758, 55.434] | 2.057 [1.584, 2.514] | 2.778 [2.356, 3.251] |

The no-tilt scenario did not reach the calibration target at any tested sigma through 10. Its reported evaluation is explicitly the unmatched ceiling scenario; it is not a fitted alternative or an upper bound on what unrestricted heterogeneity can explain.

The pre-first-simulated rule shifts only pairs with a fixed observed award strictly before that buyer's first modeled award. The legacy rule shifts pairs winning any fixed award, including later ones. Neither shifted-normal rule is the multinomial-logit posterior conditional on observed choices; the unconditional rule likewise assumes independence from the observed initial awards. These are initialization sensitivities, not identified mechanisms.

The final driver performs fresh calibration by default; generated results used the preserved source snapshot source_used_for_parallel_runs.py. The legacy run resumed eight completed calibration points from a prior driver version; source_used_for_resumed_calibration.py matches that original provenance hash. Engine snapshots and per-scenario provenance preserve the exact generating versions. The cache fix changes reuse behavior, not simulation equations.

Validation: 100 unique evaluation draws per scenario, finite numeric outputs, common calibration target, source snapshot hashes matched, and share-only calibration exactly matched the full assembled share for an identical random seed in a benchmark assertion.
