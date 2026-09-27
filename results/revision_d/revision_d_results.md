# Revision D: state dependence vs heterogeneity (topic `revision_d`)

Code: `src/revision_d.py`. It imports `revision_c.py` for `setup`, `History`, `build`, the damped-Newton clogit and the `MAIN` specification, and `lockin_analysis.py` for the palette and the null-by-group output. It modifies no existing file. Run it with `python src/revision_d.py` (about 76 minutes). `python src/revision_d.py figs` redraws the figures only.

**Sample.** The sample is the revision-C choice data: 24-month pre-*t* market pool, all pool firms as alternatives, and winner in pool. That gives 3,013 contracts, 203,721 rows and 909 buyer clusters. It splits into 1,388 renewals and 1,625 new needs. SEs are buyer-clustered.

**Settings.**
- R = 100 replications per simulated world. The beta grid also uses R = 100 per point.
- σ calibration uses 20 replications per grid point. Each mixture-frontier point uses 50.
- The buyer-cluster bootstrap uses B = 200.
- Seeds are 42 + 500… (SD), 600… (bootstrap), 700… (grid/parametric/recompute), 800–900… (heterogeneity), 1000–1200… (mixture).

**Outputs** (in `results/revision_d/`):
- `D1_observed_clogit.csv`
- `D2a_beta_grid.csv`
- `D3_three_worlds.csv`
- `D3_het_sigma_calibration.csv`
- `D3b_mixture_frontier.csv`
- `D4_firm_controls_lags.csv`
- `D5_recency_count_control.csv`
- `D7_market_N3.csv`
- `D_simulations_all_reps.csv` (every replication)
- `revision_d_log.json`
- `run_stdout.txt`

**Figures:** `figures/F-D1_three_worlds.{png,pdf}` and `figures/F-L1b_incumbency_by_market_N3.{png,pdf}`.

## 0. Simulation engine and checks

**What is simulated.** Winners of the in-pool repeat-eligible contracts are re-drawn chronologically (day by day) from a conditional logit over the observed pre-*t* pool. All other contracts keep their observed winners: entrant winners, first contracts of a buyer–market, and, in subgroup runs, the other subgroup. `incumbent`, `future_supplier_only`, `inc_last`/`inc_earlier` and the prior-win count with the buyer–market are recomputed from the simulated history. The placebo, main and last-vs-earlier models are then re-estimated on each simulated dataset.

**Replay check.** Replaying the observed winners through the engine, with every covariate recomputed, reproduces all observed covariates exactly (max |diff| = 0) and the observed eligible incumbency of 0.452.

**Reproduction.** The overall pure-SD run reproduces the revision-C benchmark exactly: future-only OR 19.8 [16.1, 24.5].

**Simplifications.**
- The pools (choice sets) are the observed pre-*t* pools in every world.
- Entrant and first-contract winners are fixed.
- In the heterogeneity world, the random effect of a buyer–firm pair that won a fixed contract is drawn from its tilted posterior, N(σ, 1), because under the logit the winner's intercept is exponentially tilted. All other pairs get N(0, 1). Without this, fixed first-contract winners would carry no match advantage.

## 1. Pure state dependence by subgroup

Each subgroup uses its own fitted main model (β_inc: all 3.745, renewals 4.946, new needs 3.042) and simulates only that subgroup's contracts. The past/future ratio is OR_incumbent / OR_future-only from the placebo model.

| | all: observed | all: SD sim mean [95%] | renewals: observed | renewals: SD sim | new needs: observed | new needs: SD sim |
|---|---|---|---|---|---|---|
| contracts | 3,013 | | 1,388 | | 1,625 | |
| incumbent OR (placebo model) | 63.7 (53.9–75.3) | 56.6 [51.4, 62.7] | 258.1 (188.3–353.9) | 183.7 [148.2, 225.5] | 30.3 (25.1–36.7) | 24.4 [21.6, 27.5] |
| **future-only OR** | **54.4 (42.2–70.1)** | **19.8 [16.1, 24.5]** | **127.9 (82.9–197.2)** | **23.6 [14.1, 38.4]** | **39.9 (28.8–55.2)** | **7.2 [5.4, 9.5]** |
| **past/future ratio** | **1.17 (0.95–1.44)** | **2.88 [2.48, 3.37]** | **2.02 (1.43–2.85)** | **8.18 [5.29, 12.24]** | **0.76 (0.57–1.01)** | **3.44 [2.62, 4.22]** |
| incumbent OR (main model) | 42.3 | 42.3 [38.6, 45.7] | 140.7 | 143.9 [120.2, 175.0] | 21.0 | 21.1 [18.7, 23.4] |
| share of winners incumbent | 0.689 | 0.665 | 0.880 | 0.876 | 0.526 | 0.510 |
| share of winners future-only | 0.078 | 0.063 | 0.045 | 0.022 | 0.106 | 0.054 |

The observed-ratio CI shown is the Wald interval. The bootstrap CIs of the observed ratio (B = 200, buyer clusters) are:
- all: 0.97–1.40;
- renewals: 1.41–2.67;
- new needs: 0.55–0.99.

**Formal test.** The test compares the observed log past/future ratio with the simulated distribution: z = (obs − sim mean) / √(se_obs² + var_sim).

| sample | z (Wald se) | p | z (bootstrap se) | p | share of simulated ratios ≤ observed |
|---|---|---|---|---|---|
| all | −6.55 | 6e-11 | −6.81 | 1e-11 | 0 / 100 |
| renewals | −4.86 | 1e-6 | −4.91 | 9e-7 | 0 / 100 |
| new needs | −7.89 | 3e-15 | −7.71 | 1e-14 | 0 / 100 |

**Verdict.** Pure state dependence is rejected in every subgroup. It predicts a past tie two-and-a-half to eight times stronger than the future tie. Observed ratios are about 2 for renewals, about 1 overall, and below 1 for new needs.

## 2. Calibration and uncertainty (overall sample)

### (a) β_inc grid

The other coefficients are fixed at their fitted values.

| β_inc (OR) | share of winners incumbent | future-only OR [95%] | incumbent OR (placebo) | past/future | last/earlier | incumbency, all eligible |
|---|---|---|---|---|---|---|
| 2.745 (15.6), fitted − 1.0 | 0.510 | 10.0 [7.8, 12.3] | 19.9 | 2.02 | 1.01 | 0.340 |
| 3.245 (25.7), fitted − 0.5 | 0.590 | 14.3 [11.4, 17.9] | 33.6 | 2.36 | 0.99 | 0.389 |
| **3.745 (42.3), fitted** | 0.665 | 19.8 [16.1, 24.5] | 56.6 | 2.88 | 1.01 | 0.435 |
| 4.245 (69.8), fitted + 0.5 | 0.730 | 26.6 [20.2, 33.7] | 95.2 | 3.62 | 1.00 | 0.475 |
| 4.745 (115.0), fitted + 1.0 | 0.782 | 35.1 [27.8, 45.1] | 158.0 | 4.56 | 1.01 | 0.507 |

**Calibrated β_inc.** The β_inc that reproduces the observed share of incumbent winners (0.689) is **3.93 (OR 51)**, found by interpolation and re-run with R = 100. It gives:
- share 0.691;
- all-eligible incumbency 0.451 (observed 0.452);
- future-only OR **21.9 [17.9, 26.5]**;
- past/future ratio 3.19 [2.68, 3.65];
- last/earlier ratio 1.00.

Reaching the observed future-only OR of 54 would take β_inc well above +1.0. That would push the share of incumbent winners above 0.78 and the ratio above 4.5, both far from the data. **No β_inc reproduces the observed share and the observed future OR at the same time.**

### (b) Parametric uncertainty

Each replication draws β ~ N(β̂, V_cluster), R = 100. Result:
- future-only OR 19.8 [15.3, 25.8];
- past/future ratio 2.87 [2.49, 3.44];
- incumbent OR 56.5 [46.1, 69.3].

The interval widens only slightly, and the conclusion is unchanged.

### (c) Holding non-incumbent covariates fixed

Revision C held `inc_other_market`, same home province and the activity counts at their observed values. Here they are recomputed from the simulated history (every covariate, R = 100). Result:
- future-only OR 24.2 [20.0, 28.9], against 19.8 when held fixed;
- past/future ratio 2.48 [2.11, 2.96];
- incumbent OR (placebo) 59.5;
- last/earlier ratio 1.00.

The simplification biased the SD benchmark down by about 20%, because simulated winners also accumulate activity counts. The benchmark is still far below the observed 54, so the rejection stands (observed ratio 1.17 vs 2.48 [2.11, 2.96]).

## 3. Heterogeneity-only world and the three-world comparison

**Heterogeneity-only world:**
- β_inc = 0. The other coefficients are the fitted main-model values.
- A persistent buyer–firm intercept σ·u, with u ~ N(0, 1) (tilted for fixed-contract winners).
- σ is calibrated to the observed share of winners who are incumbents: **σ = 2.92** (all), **4.44** (renewals), **2.47** (new needs).

Implied incumbency over all repeat-eligible contracts:

| sample | observed | heterogeneity world | SD world |
|---|---|---|---|
| all | 0.452 | 0.457 | 0.435 |
| renewals | 0.720 | 0.721 | 0.717 |
| new needs | 0.305 | 0.305 | 0.294 |

The three worlds (simulations: mean [2.5–97.5%], R = 100; observed: 95% CI):

| sample | moment | observed | state dependence only | heterogeneity only |
|---|---|---|---|---|
| all | incumbent OR (main) | 42.3 (36.4–49.2) | 42.3 [38.6, 45.7] | 52.1 [45.3, 59.7] |
| all | incumbent OR (placebo) | 63.7 (53.9–75.3) | 56.6 [51.4, 62.7] | 72.9 [63.1, 86.2] |
| all | **future-only OR** | **54.4 (42.2–70.1)** | 19.8 [16.1, 24.5] | 40.5 [30.6, 51.5] |
| all | **past/future ratio** | **1.17 (0.95–1.44)** | 2.88 [2.48, 3.37] | 1.82 [1.45, 2.22] |
| all | **last/earlier ratio** | **1.75 (1.43–2.14)** | 1.01 [0.85, 1.17] | 2.29 [1.92, 2.60] |
| renewals | incumbent OR (placebo) | 258 (188–354) | 184 [148, 225] | 378 [257, 509] |
| renewals | **future-only OR** | **128 (83–197)** | 23.6 [14.1, 38.4] | 341 [207, 504] |
| renewals | **past/future ratio** | **2.02 (1.43–2.85)** | 8.18 [5.29, 12.24] | 1.14 [0.84, 1.51] |
| renewals | **last/earlier ratio** | **1.75 (1.34–2.29)** | 1.01 [0.83, 1.24] | 2.99 [2.33, 3.60] |
| new needs | incumbent OR (placebo) | 30.3 (25.1–36.7) | 24.4 [21.6, 27.5] | 29.6 [25.2, 34.2] |
| new needs | **future-only OR** | **39.9 (28.8–55.2)** | 7.2 [5.4, 9.5] | 21.7 [15.7, 28.3] |
| new needs | **past/future ratio** | **0.76 (0.57–1.01)** | 3.44 [2.62, 4.22] | 1.39 [1.04, 1.82] |
| new needs | **last/earlier ratio** | **1.60 (1.21–2.11)** | 1.00 [0.79, 1.22] | 1.63 [1.30, 2.02] |

Observed past/future ratio against the heterogeneity world:

| sample | z | p | direction |
|---|---|---|---|
| all | −2.89 | 0.004 | observed below the heterogeneity world |
| renewals | +2.47 | 0.014 | observed above |
| new needs | −2.82 | 0.005 | observed below |

**Key finding: heterogeneity alone does not give a recency ratio of about 1.** Persistent buyer–firm heterogeneity *also* makes the last supplier beat earlier suppliers: 2.3 overall, 3.0 for renewals, 1.6 for new needs. The reason is selection. A displaced earlier supplier has revealed a lower match value than the supplier that displaced it. The last-vs-earlier contrast is therefore **not diagnostic of state dependence**, and the revision-C reading of "last > earlier" as switching-cost evidence should be dropped. The SD world gives exactly 1.0, because the model has no recency term.

### 3b. Mixture frontier

Here β_inc is fixed on a grid and σ is recalibrated at each point to the same incumbent share (R = 50). This fills in between the two worlds.

| sample | β_inc (OR) | σ | future-only OR [95%] | past/future ratio [95%] | last/earlier ratio [95%] |
|---|---|---|---|---|---|
| all | 0 (1) | 2.93 | 42.0 [33.2, 53.6] | 1.82 [1.41, 2.20] | 2.31 [1.94, 2.76] |
| all | 1 (2.7) | 2.49 | 38.4 [31.7, 46.8] | 1.94 [1.60, 2.26] | 2.11 [1.73, 2.63] |
| all | 2 (7.4) | 2.01 | 37.7 [27.9, 46.5] | 1.98 [1.67, 2.40] | 1.90 [1.68, 2.23] |
| all | 3 (20) | 1.41 | 31.2 [25.9, 40.0] | 2.37 [1.94, 2.83] | 1.57 [1.37, 1.79] |
| renewals | 0 | 4.65 | 388 [262, 547] | 1.12 [0.81, 1.56] | 2.94 [2.36, 3.79] |
| renewals | 1 | 3.83 | 287 [198, 469] | 1.38 [1.08, 1.80] | 2.73 [2.25, 3.47] |
| **renewals** | **2 (7.4)** | 3.15 | 183 [132, 244] | **1.83 [1.32, 2.49]** | 2.35 [2.00, 2.89] |
| **renewals** | **3 (20)** | 2.52 | **125 [76, 178]** | 2.55 [1.92, 3.39] | **2.00 [1.69, 2.33]** |
| new needs | 0 | 2.48 | 22.3 [17.3, 29.1] | 1.36 [1.08, 1.72] | 1.65 [1.32, 2.10] |
| new needs | 1 | 2.05 | 17.9 [13.0, 24.0] | 1.70 [1.26, 2.13] | 1.48 [1.21, 1.82] |
| new needs | 2 | 1.47 | 12.2 [9.4, 15.2] | 2.33 [1.88, 3.12] | 1.24 [0.99, 1.63] |
| new needs | 3.04 (fitted) | 0.36 | 7.8 [6.3, 9.8] | 3.37 [2.62, 4.18] | 1.04 [0.90, 1.22] |

Rows at the fitted β for "all" and "renewals" were skipped by a rounding guard. They coincide with the SD world plus σ ≈ 0.

How each sample fits the frontier:
- **Renewals.** The observed moments are 128 / 2.02 / 1.75. They sit between β_inc = 2 and 3 with substantial σ. Both pure worlds are rejected: SD gives a ratio of 8.2, heterogeneity only gives 1.1. So renewals are consistent with a **mixture**: a state-dependence component on the order of OR 7–20, plus strong persistent match heterogeneity.
- **New needs.** The observed future-only OR (40) exceeds even the pure-heterogeneity world (22 [16, 28]). The observed ratio (0.76) is below it (1.39 [1.04, 1.82]). Every point with β_inc > 0 fits worse. **There is no evidence of state dependence in new needs.** The future tie is stronger than a time-invariant match effect implies, which suggests forward-looking or anticipatory relationships, for example multi-phase projects or pre-selection. It could also reflect model misspecification.
- **All.** The pooled sample inherits both patterns. Its ratio (1.17) lies below the whole frontier (≥ 1.82), so no single (β, σ) pair fits the pooled moments.

## 4. Firm-level vs dyadic heterogeneity; lags

The full pool is used, with the placebo model (MAIN + `future_supplier_only`). New controls are computed from the observed data:
- log(1 + the firm's wins in market *m* from **other** buyers *after t*);
- the same *before t*;
- log(1 + all the firm's future wins).

| model (all) | incumbent OR | **future-only OR** | control ORs |
|---|---|---|---|
| A baseline | 63.7 (53.9–75.3) | **54.4 (42.2–70.1)** | – |
| B + future wins in m, other buyers | 64.3 | **42.0 (32.3–54.5)** | 1.40 (1.31–1.49) |
| C + past wins in m, other buyers | 61.9 | 54.6 (42.3–70.4) | 0.87 (0.79–0.96) |
| **D + both** | 61.2 (51.8–72.3) | **41.5 (32.0–53.9)** | future 1.43, past 0.79 |
| E + both + all future wins | 63.8 | 38.8 (30.3–49.9) | all future 1.46 |
| F + future_other_market_only (same buyer) | 65.2 | 43.7 (33.4–57.2) | 6.0 (3.9–9.3) |
| G + both + future_other_market_only | 63.0 | 34.4 (26.3–45.0) | 5.4 |
| renewals, A → D | 258 → 231 | 128 → **96 (60–154)** | |
| new needs, A → D | 30.3 → 30.2 | 39.9 → **30.9 (22.3–42.8)** | |

The auditor's result (54.4 → 42.0) is reproduced. Firm-level future activity (growth or quality) accounts for about a quarter of the placebo. The **dyadic** future tie stays large: about 42 overall, 96 for renewals and 31 for new needs. Firm growth does not explain the placebo away.

**Caveat.** The simulated benchmarks hold these firm-level controls at their observed values. They should be compared with the baseline (A) ORs, not with D.

**Lag robustness.** The future tie is defined only by wins more than L days after *t*. A separate dummy flags future-only ties realised within (t, t + L], so the reference category stays clean.

| L (days) | winners future-only (share) | future-only OR (L) | + firm controls | near-future dummy OR |
|---|---|---|---|---|
| 0 | 0.078 | 54.4 (42.2–70.1) | 41.5 (32.0–53.9) | – |
| 30 | 0.076 | 56.1 (43.5–72.3) | 42.5 (32.8–55.1) | 20.8 (6.6–65.8) |
| 90 | 0.073 | 55.3 (42.6–71.8) | 41.6 (31.9–54.4) | 43.8 (19.5–98.7) |
| 180 | 0.068 | 52.7 (40.4–68.8) | 39.6 (30.1–52.0) | 68.3 (36.9–126.5) |
| 365 | 0.055 | 48.7 (37.0–63.9) | 35.5 (26.8–47.1) | 74.7 (49.1–113.8) |

By subgroup at L = 365:
- renewals: 108.7 (68.1–173.7), or 77.7 with firm controls;
- new needs: 36.8 (26.1–51.8), or 27.2 with firm controls.

The simulated benchmark at L = 365 (overall) is:
- SD world: 16.1 [12.9, 20.1];
- heterogeneity world: 38.1 [28.0, 49.9].

**The placebo is not driven by same-project or contemporaneous lots.** It survives excluding future ties realised within a year, falling only modestly (54 → 49).

## 5. Recency with the prior-win-count control

Last vs earlier supplier (full pool; ratio = OR_last / OR_earlier, cluster-robust Wald CI):

| sample | model | OR last | OR earlier | **ratio (95% CI)** | p | count-term OR |
|---|---|---|---|---|---|---|
| all | last vs earlier | 45.8 | 26.2 | 1.75 (1.43–2.14) | 5e-8 | – |
| **all** | **+ log(1 + prior wins with k in m)** | **27.5** | **16.3** | **1.69 (1.38–2.07)** | 6e-7 | 1.74 |
| renewals | + count | 79.9 | 48.8 | 1.64 (1.24–2.17) | 0.001 | 1.93 |
| new needs | + count | 25.4 | 15.9 | 1.60 (1.21–2.12) | 0.001 | 0.87 |

The ratio is 1.69 (1.38–2.07) with the count control. But section 3 shows that pure heterogeneity produces 2.3 (all), 3.0 (renewals) and 1.6 (new needs). **The recency ratio cannot discriminate between the two mechanisms, so it should not be offered as evidence of switching costs.**

## 6. Figure F-D1

`figures/F-D1_three_worlds.png/.pdf`, 7 × 2.5 in, Okabe–Ito palette. There are three panels:
- past-supplier OR (placebo model);
- future-supplier-only OR;
- last/earlier OR ratio.

Each panel has rows for all, renewals and new needs. Three markers per row show observed (95% CI), SD-only and heterogeneity-only (2.5–97.5% of replications). Axes are log scale. The figure was visually checked, with no overlaps.

Suggested caption: *"Observed moments of the supplier-choice model (black, 95% buyer-clustered CI) versus simulated worlds with pure state dependence (orange; fitted incumbent coefficient, no match effect) and pure buyer–firm heterogeneity (blue; incumbent coefficient 0, persistent normal buyer–firm intercept calibrated to the observed share of incumbent winners). Simulation intervals are the 2.5–97.5th percentiles of 100 replications."*

## 7. Figure F-L1b (incumbency by product market, N3 null)

`figures/F-L1b_incumbency_by_market_N3.png/.pdf` uses the same style as F_L1. The data are `results/lockin/null_by_group.csv`, variant `S8_cell_market_x_year_x_province`, dimension `market`, B = 1,000. The table is in `D7_market_N3.csv`.

Under N3:
- Every market except call-centre/helpdesk (n = 19, p = 0.03, observed at the upper null bound) exceeds its null (p = 0.001).
- Health information systems: 0.716 vs null 0.407 (×1.76).
- Maintenance/support: 0.536 vs 0.122 (×4.38).
- Custom software: 0.201 vs 0.056 (×3.61).
- ERP: 0.392 vs 0.111 (×3.53).

Physical security (×1.32), smart-city/OT (×1.26) and health IS (×1.76) have high province-conditioned nulls. So their raw incumbency is partly geography.

## Bottom line

| | all | renewals | new needs |
|---|---|---|---|
| Pure SD reproduces future-only OR / ratio? | No (20 vs 54; 2.9 vs 1.17) | No (24 vs 128; 8.2 vs 2.0) | No (7 vs 40; 3.4 vs 0.76) |
| Pure heterogeneity reproduces? | Close on the future OR (41 vs 54). Ratio too high (1.8 vs 1.17). | No: the future OR is too high (341 vs 128) and the ratio too low (1.1 vs 2.0) | Closer, but the future tie is observed even stronger (40 vs 22) |
| Best fit on the frontier | none (pooling of the two regimes) | **mixture: β_inc ≈ 2–3 (OR ≈ 7–20) + σ ≈ 2.5–3** | β_inc = 0; heterogeneity plus forward-looking ties |
| Recency (last/earlier) diagnostic? | No: heterogeneity alone produces 1.6–3.0 | | |
