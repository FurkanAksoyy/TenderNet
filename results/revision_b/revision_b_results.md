# TenderNet v3 — Referee round B (topic `revision_b`)

Code: `src/revision_b.py` (imports `models_common`, `models_features`, `concentration_v3`; none modified). Sample: main (`in_scope_main`), incumbency sample A = contracts with a strictly earlier contract of the same buyer (`kurum_il_split`) in the same product market: N = 4,913, 1,126 buyers, 1,437 firms, mean incumbent-win = 0.452. Seed 42; no resampling in this topic (all inference analytic).

## 1. 21(b) × post-7144: history controls and clustering

Logit, FE = year (2010 pooled into 2011), product market, buyer sector; also log real value and 'other negotiated'. History controls = log # prior contracts and log # distinct prior suppliers of the buyer in the market, years since the buyer's first contract in the market. AMEs = average difference in P(incumbent win) between 21(b) and open, delta method, evaluated on pre- / post-25-May-2018 contracts.

| specification | SE | OR 21(b)×post [95% CI] | p | AME pre (pp) | AME post (pp) | post − pre (pp) | p (post−pre) |
|---|---|---:|---:|---:|---:|---:|---:|
| S1 full history controls (= A1) | two-way (buyer, firm) | 2.42 [1.43, 4.09] | <0.001 | -3.8 [-12.4, 4.9] | 13.5 [7.2, 19.9] | 17.3 [7.2, 27.5] | <0.001 |
| S1 full history controls (= A1) | buyer only | 2.42 [1.57, 3.73] | <0.001 | -3.8 [-11.1, 3.5] | 13.5 [8.0, 19.0] | 17.3 [8.8, 25.8] | <0.001 |
| S2 no prior-count controls (keeps years since first) | two-way (buyer, firm) | 2.90 [1.64, 5.15] | <0.001 | -3.5 [-13.0, 5.9] | 19.5 [12.3, 26.7] | 23.0 [11.5, 34.5] | <0.001 |
| S2 no prior-count controls (keeps years since first) | buyer only | 2.90 [1.92, 4.39] | <0.001 | -3.5 [-10.5, 3.5] | 19.5 [13.4, 25.5] | 23.0 [14.4, 31.5] | <0.001 |
| S3 no buyer-history controls | two-way (buyer, firm) | 2.93 [1.65, 5.19] | <0.001 | -3.6 [-13.0, 5.9] | 19.6 [12.4, 26.8] | 23.2 [11.7, 34.6] | <0.001 |
| S3 no buyer-history controls | buyer only | 2.93 [1.94, 4.41] | <0.001 | -3.6 [-10.5, 3.4] | 19.6 [13.5, 25.7] | 23.2 [14.7, 31.6] | <0.001 |

Pseudo-R²: S1 0.172, S2 0.110, S3 0.110. Point estimates are identical across the two SE types; only the CIs change. Dropping all buyer-history controls moves the interaction OR from 2.42 to 2.93. Buyer-only clustering gives narrower CIs than two-way clustering (the firm dimension adds dependence), so the two-way results are the conservative ones. CSV: `B1_controls_clustering.csv`.

## 2. Event study: 21(b) − open incumbency difference by year

LPM on sample A: P(incumbent win) = Σ_t δ_t·21(b)·1[bin t] + Σ_t θ_t·other-negotiated·1[bin t] + log real value + history controls + year FE + product-market FE (+ buyer-sector FE in (a); + buyer FE in (c)). All 21(b)×bin terms are included and the 21(b) main effect is omitted, so δ_t is directly the conditional 21(b) − open difference in bin t (open + 17 restricted = reference; other negotiated procedures get their own bin-specific terms so they do not contaminate the year FE). Bins: 2010–12 pooled (only 8 21(b) contracts in 2010), each year 2013–2024, 2025–26 pooled. **Base choice.** The requested 2010–12 base turns out to be a poor reference: sample A in 2010–12 is the start of the observation window (left-censored buyer histories of at most ~2 years; 242 contracts, 24 21(b)), and its δ is imprecise and high. We therefore report differences both against 2010–12 and against the average of 2013–2017 (the five full pre-reform years), and use the latter as the primary base. SEs two-way clustered (buyer, winning firm). SEs two-way clustered (buyer, winning firm). Figure: `figures/F-B1_event_study_21b.png/.pdf` (with history controls).

### (a) all buyers

| bin | contracts | 21(b) | raw inc. 21(b) | raw inc. open | δ (pp) [95% CI] | δ − mean δ(2013–17) (pp) [95% CI] | δ − δ(2010–12) (pp) [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2010–12 | 242 | 24 | 0.58 | 0.28 | 16.0 [-4.2, 36.2] | 23.2 [2.7, 43.7] | base |
| 2013 | 234 | 40 | 0.55 | 0.40 | -7.6 [-26.6, 11.4] | -0.3 [-18.3, 17.6] | -23.5 [-51.7, 4.6] |
| 2014 | 295 | 27 | 0.44 | 0.43 | -18.3 [-40.9, 4.4] | -11.0 [-29.6, 7.6] | -34.2 [-61.1, -7.4] |
| 2015 | 310 | 34 | 0.62 | 0.38 | 2.8 [-16.4, 21.9] | 10.0 [-4.9, 24.9] | -13.2 [-38.7, 12.3] |
| 2016 | 320 | 31 | 0.48 | 0.45 | -15.2 [-32.1, 1.7] | -8.0 [-24.8, 8.9] | -31.2 [-58.2, -4.1] |
| 2017 | 363 | 32 | 0.50 | 0.37 | 2.1 [-13.1, 17.3] | 9.3 [-4.0, 22.7] | -13.9 [-37.4, 9.6] |
| 2018 | 345 | 54 | 0.83 | 0.36 | 30.1 [19.5, 40.7] | 37.3 [24.4, 50.2] | 14.1 [-7.5, 35.7] |
| 2019 | 307 | 49 | 0.82 | 0.51 | 2.0 [-11.3, 15.3] | 9.2 [-8.1, 26.6] | -14.0 [-38.9, 11.0] |
| 2020 | 410 | 85 | 0.84 | 0.44 | 14.8 [6.6, 23.1] | 22.1 [11.6, 32.5] | -1.2 [-22.2, 19.9] |
| 2021 | 462 | 73 | 0.74 | 0.41 | 4.5 [-8.6, 17.7] | 11.8 [-3.4, 27.0] | -11.4 [-34.6, 11.7] |
| 2022 | 463 | 53 | 0.91 | 0.50 | 5.8 [-2.6, 14.2] | 13.1 [1.6, 24.6] | -10.2 [-31.5, 11.2] |
| 2023 | 413 | 46 | 0.83 | 0.49 | 7.4 [-4.7, 19.4] | 14.6 [0.4, 28.9] | -8.6 [-30.9, 13.7] |
| 2024 | 350 | 19 | 0.79 | 0.59 | -8.9 [-24.6, 6.9] | -1.6 [-19.0, 15.7] | -24.8 [-49.5, -0.2] |
| 2025–26 | 399 | 51 | 0.71 | 0.43 | 10.9 [-2.2, 24.0] | 18.1 [4.7, 31.5] | -5.1 [-28.4, 18.2] |

Wald tests (two-way V): all bins equal: χ²(13)=63.1, p=<0.001; 2013–17 bins equal: χ²(4)=6.1, p=0.191; post bins (>=2019) equal: χ²(7)=12.4, p=0.088; mean post(>=2019) = mean 2013–17: χ²(1)=8.5, p=0.003 (difference 13.8 pp, SE 4.7); mean 2018 = mean 2013–17: χ²(1)=32.0, p=<0.001 (difference 37.3 pp, SE 6.6); mean 2010–12 = mean 2013–17: χ²(1)=4.9, p=0.026 (difference 23.2 pp, SE 10.5).

Parametric shapes for the 21(b) − open difference (same controls; ΔAIC relative to best; Gaussian AIC on RSS):

| model | ΔAIC | step (pp) [p] | trend (pp/yr) [p] |
|---|---:|---:|---:|
| trend + step 2017-08-25 | 0.0 | 25.2 [<0.001] | -1.8 [0.026] |
| step 2017-08-25 (KHK 694) | 1.7 | 13.4 [0.004] |  |
| step 2018-01-01 | 1.8 | 13.2 [0.004] |  |
| step 2017-01-01 | 2.1 | 13.8 [0.004] |  |
| trend + step 2018-05-25 | 3.4 | 20.9 [0.008] | -1.4 [0.123] |
| step 2018-05-25 (Law 7144) | 3.7 | 11.7 [0.011] |  |
| unrestricted year bins | 6.4 |  |  |
| step 2016-01-01 | 7.0 | 10.3 [0.070] |  |
| step 2015-01-01 | 7.1 | 11.5 [0.056] |  |
| linear trend | 9.4 |  | 0.8 [0.154] |
| constant | 9.5 |  |  |
| step 2020-01-01 | 10.4 | 4.2 [0.287] |  |
| step 2019-01-01 | 10.5 | 4.1 [0.329] |  |
| step 2014-01-01 | 11.0 | 4.5 [0.524] |  |
| step 2013-01-01 | 11.0 | -6.7 [0.515] |  |
| step 2021-01-01 | 11.3 | -1.6 [0.678] |  |
| step 2024-01-01 | 11.4 | -1.4 [0.779] |  |
| step 2022-01-01 | 11.5 | 0.2 [0.945] |  |
| step 2023-01-01 | 11.5 | -0.0 [0.997] |  |

### (b) health buyers

| bin | contracts | 21(b) | raw inc. 21(b) | raw inc. open | δ (pp) [95% CI] | δ − mean δ(2013–17) (pp) [95% CI] | δ − δ(2010–12) (pp) [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2010–12 | 71 | 16 | 0.69 | 0.38 | 28.0 [4.1, 51.8] | 28.1 [2.1, 54.1] | base |
| 2013 | 69 | 37 | 0.54 | 0.41 | 6.5 [-17.6, 30.6] | 6.6 [-15.4, 28.7] | -21.5 [-58.3, 15.4] |
| 2014 | 79 | 22 | 0.50 | 0.52 | -10.4 [-39.1, 18.3] | -10.3 [-34.3, 13.8] | -38.4 [-73.0, -3.7] |
| 2015 | 89 | 30 | 0.67 | 0.37 | 15.0 [-9.7, 39.6] | 15.1 [-4.4, 34.6] | -13.0 [-45.8, 19.8] |
| 2016 | 97 | 27 | 0.56 | 0.65 | -18.1 [-41.3, 5.0] | -18.0 [-39.4, 3.4] | -46.1 [-79.2, -13.0] |
| 2017 | 87 | 23 | 0.65 | 0.50 | 6.4 [-15.8, 28.5] | 6.5 [-13.7, 26.7] | -21.6 [-52.8, 9.6] |
| 2018 | 101 | 51 | 0.88 | 0.39 | 42.4 [22.8, 62.0] | 42.6 [23.4, 61.7] | 14.5 [-15.3, 44.3] |
| 2019 | 99 | 46 | 0.85 | 0.58 | 14.8 [-0.4, 30.1] | 15.0 [-5.2, 35.1] | -13.1 [-42.9, 16.6] |
| 2020 | 145 | 68 | 0.99 | 0.60 | 23.5 [12.3, 34.7] | 23.6 [9.2, 38.0] | -4.5 [-30.6, 21.6] |
| 2021 | 138 | 64 | 0.83 | 0.59 | 13.7 [-4.6, 32.1] | 13.9 [-6.7, 34.6] | -14.2 [-40.3, 11.9] |
| 2022 | 150 | 51 | 0.92 | 0.75 | 2.9 [-5.6, 11.5] | 3.1 [-10.1, 16.3] | -25.0 [-50.5, 0.5] |
| 2023 | 137 | 41 | 0.90 | 0.79 | -0.5 [-11.5, 10.5] | -0.3 [-14.3, 13.6] | -28.4 [-54.0, -2.9] |
| 2024 | 98 | 14 | 1.00 | 0.84 | 0.6 [-7.4, 8.6] | 0.8 [-13.1, 14.6] | -27.3 [-51.0, -3.7] |
| 2025–26 | 142 | 44 | 0.75 | 0.55 | 14.2 [-0.4, 28.7] | 14.3 [0.1, 28.6] | -13.8 [-39.9, 12.3] |

Wald tests (two-way V): all bins equal: χ²(13)=40.3, p=<0.001; 2013–17 bins equal: χ²(4)=6.0, p=0.200; post bins (>=2019) equal: χ²(7)=20.7, p=0.004; mean post(>=2019) = mean 2013–17: χ²(1)=4.3, p=0.038 (difference 12.3 pp, SE 5.9); mean 2018 = mean 2013–17: χ²(1)=19.0, p=<0.001 (difference 42.6 pp, SE 9.8); mean 2010–12 = mean 2013–17: χ²(1)=4.5, p=0.034 (difference 28.1 pp, SE 13.3).

Parametric shapes for the 21(b) − open difference (same controls; ΔAIC relative to best; Gaussian AIC on RSS):

| model | ΔAIC | step (pp) [p] | trend (pp/yr) [p] |
|---|---:|---:|---:|
| trend + step 2017-08-25 | 0.0 | 31.8 [<0.001] | -3.1 [0.001] |
| unrestricted year bins | 1.6 |  |  |
| trend + step 2018-05-25 | 3.7 | 25.7 [0.013] | -2.6 [0.018] |
| step 2017-01-01 | 5.5 | 12.5 [0.017] |  |
| step 2018-01-01 | 5.8 | 11.5 [0.031] |  |
| step 2017-08-25 (KHK 694) | 6.3 | 11.0 [0.049] |  |
| step 2018-05-25 (Law 7144) | 7.5 | 9.1 [0.099] |  |
| step 2022-01-01 | 8.2 | -8.4 [0.031] |  |
| step 2013-01-01 | 8.7 | -18.3 [0.119] |  |
| constant | 8.9 |  |  |
| step 2021-01-01 | 9.0 | -6.6 [0.100] |  |
| step 2023-01-01 | 9.4 | -6.9 [0.098] |  |
| step 2015-01-01 | 10.0 | 6.6 [0.332] |  |
| step 2016-01-01 | 10.2 | 5.0 [0.427] |  |
| step 2014-01-01 | 10.9 | -1.9 [0.812] |  |
| step 2020-01-01 | 10.9 | -0.9 [0.833] |  |
| step 2024-01-01 | 10.9 | -1.3 [0.793] |  |
| step 2019-01-01 | 10.9 | 0.6 [0.902] |  |
| linear trend | 10.9 |  | 0.1 [0.920] |

### (c) health buyers, buyer FE

| bin | contracts | 21(b) | raw inc. 21(b) | raw inc. open | δ (pp) [95% CI] | δ − mean δ(2013–17) (pp) [95% CI] | δ − δ(2010–12) (pp) [95% CI] |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2010–12 | 71 | 16 | 0.69 | 0.38 | 31.0 [1.8, 60.1] | 41.1 [9.1, 73.0] | base |
| 2013 | 69 | 37 | 0.54 | 0.41 | 5.7 [-21.4, 32.9] | 15.8 [-10.8, 42.4] | -25.2 [-63.7, 13.2] |
| 2014 | 79 | 22 | 0.50 | 0.52 | -20.6 [-50.6, 9.5] | -10.5 [-34.6, 13.7] | -51.5 [-91.6, -11.5] |
| 2015 | 89 | 30 | 0.67 | 0.37 | -8.2 [-39.3, 22.9] | 1.9 [-21.1, 24.9] | -39.1 [-78.3, 0.0] |
| 2016 | 97 | 27 | 0.56 | 0.65 | -22.2 [-50.5, 6.1] | -12.1 [-36.5, 12.3] | -53.2 [-95.3, -11.0] |
| 2017 | 87 | 23 | 0.65 | 0.50 | -5.3 [-29.7, 19.1] | 4.8 [-17.8, 27.4] | -36.2 [-76.6, 4.2] |
| 2018 | 101 | 51 | 0.88 | 0.39 | 17.7 [-3.5, 38.8] | 27.8 [2.7, 52.9] | -13.3 [-49.0, 22.4] |
| 2019 | 99 | 46 | 0.85 | 0.58 | 15.3 [-1.7, 32.2] | 25.4 [4.2, 46.5] | -15.7 [-49.4, 18.0] |
| 2020 | 145 | 68 | 0.99 | 0.60 | 19.2 [5.7, 32.6] | 29.3 [14.3, 44.3] | -11.8 [-44.0, 20.4] |
| 2021 | 138 | 64 | 0.83 | 0.59 | 14.3 [-1.5, 30.1] | 24.4 [4.7, 44.1] | -16.7 [-48.2, 14.9] |
| 2022 | 150 | 51 | 0.92 | 0.75 | 9.7 [-4.0, 23.3] | 19.8 [3.4, 36.1] | -21.3 [-53.0, 10.4] |
| 2023 | 137 | 41 | 0.90 | 0.79 | 6.6 [-8.5, 21.7] | 16.7 [-3.4, 36.8] | -24.3 [-57.2, 8.5] |
| 2024 | 98 | 14 | 1.00 | 0.84 | 4.6 [-5.9, 15.1] | 14.7 [-1.2, 30.6] | -26.3 [-57.3, 4.6] |
| 2025–26 | 142 | 44 | 0.75 | 0.55 | 10.9 [-8.5, 30.4] | 21.1 [0.1, 42.0] | -20.0 [-54.4, 14.4] |

Wald tests (two-way V): all bins equal: χ²(13)=21.4, p=0.065; 2013–17 bins equal: χ²(4)=2.5, p=0.649; post bins (>=2019) equal: χ²(7)=6.5, p=0.483; mean post(>=2019) = mean 2013–17: χ²(1)=11.3, p=<0.001 (difference 24.0 pp, SE 7.2); mean 2018 = mean 2013–17: χ²(1)=4.7, p=0.030 (difference 27.8 pp, SE 12.8); mean 2010–12 = mean 2013–17: χ²(1)=6.4, p=0.012 (difference 41.1 pp, SE 16.3).

Parametric shapes for the 21(b) − open difference (same controls; ΔAIC relative to best; Gaussian AIC on RSS):

| model | ΔAIC | step (pp) [p] | trend (pp/yr) [p] |
|---|---:|---:|---:|
| trend + step 2017-08-25 | 0.0 | 31.9 [0.002] | -2.2 [0.092] |
| step 2017-08-25 (KHK 694) | 2.2 | 18.3 [0.004] |  |
| step 2018-01-01 | 3.1 | 17.2 [0.010] |  |
| step 2017-01-01 | 3.5 | 17.9 [0.013] |  |
| step 2018-05-25 (Law 7144) | 6.8 | 13.5 [0.034] |  |
| trend + step 2018-05-25 | 7.8 | 19.5 [0.048] | -1.1 [0.368] |
| step 2019-01-01 | 9.0 | 10.9 [0.014] |  |
| unrestricted year bins | 9.4 |  |  |
| step 2013-01-01 | 10.6 | -22.7 [0.115] |  |
| step 2020-01-01 | 10.8 | 8.4 [0.052] |  |
| step 2016-01-01 | 11.5 | 10.0 [0.217] |  |
| linear trend | 12.1 |  | 1.0 [0.187] |
| constant | 12.3 |  |  |
| step 2014-01-01 | 13.1 | -9.2 [0.415] |  |
| step 2015-01-01 | 13.8 | 5.0 [0.588] |  |
| step 2021-01-01 | 14.1 | 2.2 [0.601] |  |
| step 2023-01-01 | 14.2 | -1.8 [0.741] |  |
| step 2024-01-01 | 14.3 | -0.8 [0.868] |  |
| step 2022-01-01 | 14.3 | -0.0 [1.000] |  |

### Timing inside 2017–2018 (raw incumbent-win rates, sample A, all buyers)

| window | 21(b) n | 21(b) incumbent-win | open n | open incumbent-win |
|---|---:|---:|---:|---:|
| 2013–2016 | 132 | 0.53 | 733 | 0.41 |
| 1 Jan–24 Aug 2017 | 24 | 0.50 | 117 | 0.32 |
| 25 Aug–31 Dec 2017 (after KHK 694) | 8 | 0.50 | 100 | 0.43 |
| 1 Jan–24 May 2018 | 10 | 0.70 | 56 | 0.29 |
| 25 May–31 Dec 2018 (after Law 7144) | 44 | 0.86 | 121 | 0.39 |
| 2019–2026 | 376 | 0.80 | 1767 | 0.48 |

Without history controls (log value only) the δ_t are in `B2_event_study.csv` (`controls = value only`); Wald tests for both in `B2_wald_tests.csv`, cell counts in `B2_event_counts.csv`, parametric fits in `B2_break_models.csv`.

### Verdict on the break (plain language)

- **There is a discrete jump, and it is in 2018.** Measured against the 2013–17 average, the 21(b) − open incumbency gap jumps in 2018:
  - all buyers: +37 pp (95% CI 24 to 50)
  - health buyers: +43 pp (23 to 62)

  No 2013–17 year differs from the 2013–17 mean (joint tests p = 0.19 and 0.20).
- **Part of the jump persists.** From 2019 on, the gap is on average above its 2013–17 level:
  - all buyers: +14 pp (p = 0.003)
  - health buyers: +12 pp (p = 0.038)

  This is not a clean level shift. 2019 and 2024 fall back near the pre-reform level, 2020 (COVID) is high, and among health buyers 2022–24 are near zero.
- **Best-fitting shape.** In all three samples the best-fitting parametric shape is a step at 25 Aug 2017 combined with a *declining* 21(b)-specific trend. The step is +25 to +32 pp and the trend −1.8 to −3.1 pp per year. By AIC:
  - a step at 25 May 2018 fits worse, by 3.4–3.7 points;
  - a pure linear trend fits worst, about as badly as a constant.
- **Within health buyers (buyer FE) the shift is clearest and most persistent.**
  - In 2013–17 the gap averages −10 pp.
  - It is positive in every bin from 2018 on (+5 to +19 pp).
  - The post-2019 mean is +24 pp above 2013–17 (95% CI 10 to 38, p < 0.001).
- **When: between late 2017 and mid-2018.** The data cannot separate KHK 694 (25 Aug 2017) from Law 7144 (25 May 2018) because too few repeat-eligible 21(b) contracts fall between the two dates:

  | window | repeat-eligible 21(b) contracts | raw incumbent-win rate |
  |---|---:|---:|
  | 2013–16 | – | 0.53 |
  | 25 Aug–31 Dec 2017 | 8 | 0.50 |
  | 1 Jan–24 May 2018 | 10 | 0.70 |
  | 25 May–31 Dec 2018 | – | 0.86 |
- **Base caveat.** The pooled 2010–12 bin also has a high gap: +16 pp for all buyers and +28 pp for health buyers, both significantly above 2013–17.
  - Measured against a 2010–12 base, no post-2018 year is significantly higher in any sample (last column of the tables above).
  - We do not use 2010–12 as the reference. It is the left-censored start of the window, with at most about two years of buyer history and only 24 21(b) contracts.
  - A reader who did use it would conclude that 2013–17 is an unusual trough, not that 2018 is an unusual peak.
  - The 2010–12 bin is a likely reason why the buyer-FE interaction in `models` (A5) was null (+7.3 pp, p = 0.20): its "pre" period includes 2010–12.
- **Without history controls** the pattern is the same (`B2_wald_tests.csv`). Post-2019 vs 2013–17 is:
  - all buyers: +22.5 pp
  - health buyers: +15.0 pp
  - health buyers with buyer FE: +25.2 pp

  All three have p ≤ 0.015.

## 3. Statutory text of Law 4734 Art. 21

**Source.** Consolidated text of Law 4734 on mevzuat.gov.tr (`https://www.mevzuat.gov.tr/MevzuatMetin/1.5.4734.pdf`, downloaded 2026-09-26), Art. 21 and its footnotes 30–31.
- Footnote 30 records the 2018 change: *"16/5/2018 tarihli ve 7144 sayılı Kanunun 11 inci maddesiyle bu bentte yer alan 'beklenmeyen veya' ibaresinden sonra gelmek üzere '…' ibaresi eklenmiştir."*
- The pre-2018 wording is therefore the current wording minus the inserted phrase. This matches the Resmî Gazete text of Law 7144, Art. 11 (RG 25.05.2018 / 30431), cited in `docs/law_notes.md`.
- The chapeau reads *"Aşağıda belirtilen hallerde pazarlık usulü ile ihale yapılabilir:"* ("The negotiated procedure may be used in the following cases:").
- All translations are ours, not official.

**21(b) before 25 May 2018** (wording set by Law 5812 of 2008, in force until Law 7144):
> b) Doğal afetler, salgın hastalıklar, can veya mal kaybı tehlikesi gibi ani ve beklenmeyen veya idare tarafından önceden öngörülemeyen olayların ortaya çıkması üzerine ihalenin ivedi olarak yapılmasının zorunlu olması.

*EN:* (b) Where the tender must be held urgently because of the occurrence of sudden and unexpected events, such as natural disasters, epidemics or a danger of loss of life or property, or of events the contracting authority could not foresee in advance.

**21(b) from 25 May 2018** (inserted text in bold):
> b) Doğal afetler, salgın hastalıklar, can veya mal kaybı tehlikesi gibi ani ve beklenmeyen veya **yapım tekniği açısından özellik arz eden veya yapı veya can ve mal güvenliğinin sağlanması açısından ivedilikle yapılması gerekliliği idarece belirlenen hallerde veyahut** idare tarafından önceden öngörülemeyen olayların ortaya çıkması üzerine ihalenin ivedi olarak yapılmasının zorunlu olması.

*EN:* (b) Where the tender must be held urgently because of the occurrence of sudden and unexpected events, such as natural disasters, epidemics or a danger of loss of life or property, **or in cases that have special features in terms of construction technique, or in which the contracting authority determines that the work must be carried out urgently to ensure structural safety or the safety of life and property, or** of events the contracting authority could not foresee in advance.

**The other grounds.** These were unchanged from 2010 to 2026, apart from the annual update of the 21(f) amount.
- **21(a)** *Açık ihale usulü veya belli istekliler arasında ihale usulü ile yapılan ihale sonucunda teklif çıkmaması.*
  EN: No tender was submitted in an open or restricted procedure.
- **21(c)** *Savunma ve güvenlikle ilgili özel durumların ortaya çıkması üzerine ihalenin ivedi olarak yapılmasının zorunlu olması.*
  EN: The tender must be held urgently because special defence- or security-related circumstances have arisen.
- **21(d)** *İhalenin, araştırma ve geliştirme sürecine ihtiyaç gösteren ve seri üretime konu olmayan nitelikte olması.*
  EN: The procurement requires a research-and-development process and is not subject to serial production.
- **21(e)** *İhale konusu mal veya hizmet alımları ile yapım işlerinin özgün nitelikte ve karmaşık olması nedeniyle teknik ve malî özelliklerinin gerekli olan netlikte belirlenememesi.*
  EN: The technical and financial characteristics of the goods, services or works cannot be specified with the necessary precision because they are original and complex.
- **21(f)** *(Ek: 30/7/2003-4964/14 md.) İdarelerin yaklaşık maliyeti ellimilyar Türk Lirasına kadar olan mamul mal, malzeme veya hizmet alımları.*
  EN: Purchases by contracting authorities of manufactured goods, materials or services whose estimated cost (*yaklaşık maliyet*) is up to fifty billion (old) Turkish lira.
  - This equals 50,000 TRY after the 2005 redenomination, before indexation.
  - Under Art. 67, KİK updates the amount every 1 February using the previous year's producer (wholesale) price index.
  - Footnote 31 points to KİK Communiqué 2025/1 (RG 24.01.2025 / 32792) for the current amount.
- **Second paragraph** (Law 5812, 2008): *"(b), (c) ve (f) bentlerinde belirtilen hallerde ilan yapılması zorunlu değildir. İlan yapılmayan hallerde en az üç istekli davet edilerek, yeterlik belgelerini ve fiyat tekliflerini birlikte vermeleri istenir."*
  EN: In cases (b), (c) and (f), publishing a notice is not compulsory. Where no notice is published, at least three tenderers are invited and asked to submit their qualification documents and price offers together.
- **Fourth paragraph:** cases (a), (d) and (e) instead follow a two-stage procedure, with technical offers first and price offers second.

**What 21(f) covers (confirmed).** 21(f) is not an urgency or exceptional-circumstance ground.
- **It is a value-based ground.** It applies to any purchase of goods or services (not works) whose estimated cost is below a monetary limit. That limit is written into Art. 21(f) itself, is indexed every year, and is separate from, and much lower than, the Art. 8 EU-style thresholds.
- Like 21(b), it lets the authority skip the public notice and invite at least three firms instead.
- **In our data**, all 2,957 main-sample 21(f) contracts are goods (*Mal*, 851) or services (*Hizmet*, 2,106); none are works. Their contract amounts sit just under the limit in force (table below).
- **Wording.** "Below-threshold" is accurate if phrased as "below the Art. 21(f) monetary limit".
- **The limit over time:**

  | from | 21(f) limit (TRY) |
  |---|---:|
  | 2014 | 157,923 |
  | Feb 2024 | 2,076,108 |
  | Feb 2026 | 3,406,508 |

### 21(f) in the data

Monetary limits for 21(f) (goods/services, TRY, valid 1 Feb–31 Jan) were read from KİK's annual comparison sheets (dosyalar.kik.gov.tr/yardim/dokumanlar/<year>_Esik_Degerler_Parasal_Limitler_Karsilastirma.pdf): 2014: 157,923, 2015: 167,966, 2016: 177,556, 2017: 195,205, 2018: 225,403, 2019: 301,228, 2020: 323,398, 2021: 404,732, 2022: 728,072, 2023: 1,439,543, 2024: 2,076,108, 2025: 2,668,214, 2026: 3,406,508. Sheets before 2014 were not available at that URL pattern.

Main-sample 21(f) contracts tendered from 1 Feb 2014: 2,381; contract amount ≤ the 21(f) limit in force: **99.96%** (1 above; contract amount can differ from the approximate cost that the limit applies to). For comparison, 36.1% of open and 57.8% of 21(b) contracts are below the same limit. EKAP tender type of 21(f) contracts: {'Hizmet': 2106, 'Mal': 851}.

| year | 21(f) contracts | share ≤ limit | median value / limit | 95th pct value / limit |
|---|---:|---:|---:|---:|
| 2014 | 224 | 100.0% | 0.78 | 0.98 |
| 2015 | 203 | 99.5% | 0.83 | 0.98 |
| 2016 | 228 | 100.0% | 0.82 | 0.98 |
| 2017 | 246 | 100.0% | 0.82 | 0.98 |
| 2018 | 221 | 100.0% | 0.80 | 0.98 |
| 2019 | 149 | 100.0% | 0.71 | 0.98 |
| 2020 | 213 | 100.0% | 0.82 | 0.99 |
| 2021 | 217 | 100.0% | 0.79 | 0.99 |
| 2022 | 209 | 100.0% | 0.83 | 0.98 |
| 2023 | 146 | 100.0% | 0.80 | 0.98 |
| 2024 | 164 | 100.0% | 0.90 | 0.99 |
| 2025 | 144 | 100.0% | 0.81 | 0.97 |
| 2026 | 17 | 100.0% | 0.83 | 0.98 |

## 4. Buyer size vs dependence: reconciliation

Contract-level excess incumbency by buyer-size tercile (from `lockin_results.md` §4e, N1 null): T1 (≤4 contracts) 0.450, T2 (5–13) 0.425, T3 (>13) 0.342. Buyer-level test (540 buyers with ≥5 contracts, top-supplier share, N1):

| measure | size | buyers | mean observed | mean null | mean excess | mean (p95 − null mean) | share exceeding p95 |
|---|---|---:|---:|---:|---:|---:|---:|
| hhi | 5–9 | 316 | 0.360 | 0.180 | 0.181 | 0.041 | 59.2% |
| hhi | 10–19 | 163 | 0.262 | 0.092 | 0.170 | 0.021 | 81.0% |
| hhi | >=20 | 61 | 0.101 | 0.038 | 0.063 | 0.007 | 98.4% |
| top | 5–9 | 316 | 0.436 | 0.200 | 0.236 | 0.098 | 50.0% |
| top | 10–19 | 163 | 0.351 | 0.122 | 0.229 | 0.070 | 63.2% |
| top | >=20 | 61 | 0.193 | 0.064 | 0.129 | 0.034 | 80.3% |

Spearman(size, excess top-supplier share) = -0.09 (p = 0.042); Spearman(size, exceeds-flag) = 0.21 (p = <0.001).

**Reconciliation.** The two results measure different things.
- **The tercile table measures size.** It gives the excess incumbency per contract, and that excess falls somewhat with buyer size.
- The buyer-level data agree. Among the 540 tested buyers, the mean excess top-supplier share also falls with size:

  | buyer size (contracts) | mean excess top-supplier share | p95 − null-mean margin |
  |---|---:|---:|
  | 5–9 | 0.24 | 0.10 |
  | 10–19 | 0.23 | 0.07 |
  | ≥ 20 | 0.13 | 0.03 |
- **The share exceeding the 95th null percentile measures detectability.** Detectability rises with size because the null distribution tightens as n grows, which the shrinking margin in the last column shows.
- As a result, a large buyer with a modest excess is flagged, while a small buyer with a large excess often is not.

**Suggested sentence:** *"Per contract, excess incumbency is somewhat lower among the largest buyers (0.34 vs 0.45 in the smallest tercile), but because their null distributions are much tighter, a larger share of large buyers is individually distinguishable from the null (80% of buyers with ≥ 20 contracts vs 50% of those with 5–9); the rising share reflects statistical power, not stronger dependence."*

## 5. Descriptive table (main sample)

Real value in bn 2025 TRY (CPI). Shares are % of contracts. The single largest contract (7.54 bn, call_centre_helpdesk, Health, open) is included. 'Open' = `usul_v3 == open` (the 17 restricted and 77 other negotiated 21(a,c,d,e) contracts make up the remainder). Firms = `firma_v3`, buyers = `kurum_il_split`; row counts of firms/buyers do not sum to the total because firms and buyers span groups. CSV: `B5_descriptives.csv` (also has % of value under 21(b)).

| group | contracts | firms | buyers | value (bn 2025 TRY) | % 21(b) | % 21(f) | % open |
|---|---:|---:|---:|---:|---:|---:|---:|
| product market: Health information systems | 2,189 | 205 | 935 | 19.48 | 34.7 | 9.4 | 56.0 |
| product market: ERP / management software | 1,515 | 599 | 770 | 11.14 | 4.5 | 47.1 | 47.5 |
| product market: Custom software / web / mobile | 1,117 | 734 | 625 | 7.04 | 2.9 | 43.2 | 53.6 |
| product market: Software licences | 1,047 | 375 | 445 | 7.68 | 1.8 | 23.4 | 74.8 |
| product market: Network / data-centre infra. | 748 | 390 | 420 | 7.43 | 5.9 | 25.0 | 68.2 |
| product market: Computers / peripherals | 696 | 467 | 415 | 2.85 | 3.9 | 27.7 | 68.1 |
| product market: Maintenance / support services | 626 | 297 | 251 | 8.23 | 3.5 | 33.2 | 62.3 |
| product market: GIS / city information | 553 | 203 | 320 | 4.75 | 2.2 | 41.4 | 54.8 |
| product market: Cybersecurity | 390 | 194 | 229 | 3.25 | 5.4 | 33.1 | 60.0 |
| product market: Physical security / surveillance | 385 | 222 | 203 | 2.29 | 1.8 | 23.1 | 63.6 |
| product market: Other IT | 277 | 215 | 165 | 1.82 | 5.4 | 27.8 | 66.1 |
| product market: Education technology | 205 | 128 | 124 | 1.87 | 5.4 | 50.2 | 44.4 |
| product market: Smart city / traffic OT | 169 | 106 | 111 | 3.44 | 4.1 | 34.3 | 60.9 |
| product market: Call centre / help-desk | 74 | 46 | 55 | 7.99 | 5.4 | 51.4 | 43.2 |
| buyer sector: Health | 2,950 | 554 | 1,098 | 30.93 | 28.5 | 9.4 | 61.8 |
| buyer sector: Municipal/Local | 2,688 | 1,084 | 667 | 19.93 | 2.2 | 44.1 | 53.4 |
| buyer sector: Other public | 1,295 | 646 | 351 | 10.88 | 2.5 | 41.1 | 54.7 |
| buyer sector: Education | 1,054 | 519 | 330 | 4.68 | 5.1 | 31.8 | 62.6 |
| buyer sector: Infrastructure/Transport | 644 | 337 | 123 | 7.72 | 2.8 | 39.8 | 57.0 |
| buyer sector: Agriculture/Environment | 395 | 231 | 98 | 4.29 | 2.3 | 31.4 | 63.5 |
| buyer sector: Social/Finance | 303 | 156 | 42 | 5.20 | 3.6 | 39.3 | 55.4 |
| buyer sector: Provincial admin | 223 | 125 | 74 | 0.99 | 1.3 | 25.1 | 62.8 |
| buyer sector: Security/Interior | 202 | 142 | 64 | 1.50 | 3.5 | 26.2 | 66.8 |
| buyer sector: Defence | 191 | 96 | 29 | 1.89 | 1.0 | 3.7 | 95.3 |
| buyer sector: Justice | 46 | 32 | 14 | 1.25 | 26.1 | 28.3 | 43.5 |
| total: All | 9,991 | 2,814 | 2,890 | 89.26 | 10.5 | 29.6 | 59.0 |

LaTeX rows (columns: group & contracts & firms & buyers & value & %21(b) & %21(f) & %open):

```latex
% --- by product market
Health information systems & 2,189 & 205 & 935 & 19.48 & 34.7 & 9.4 & 56.0 \\
ERP / management software & 1,515 & 599 & 770 & 11.14 & 4.5 & 47.1 & 47.5 \\
Custom software / web / mobile & 1,117 & 734 & 625 & 7.04 & 2.9 & 43.2 & 53.6 \\
Software licences & 1,047 & 375 & 445 & 7.68 & 1.8 & 23.4 & 74.8 \\
Network / data-centre infra. & 748 & 390 & 420 & 7.43 & 5.9 & 25.0 & 68.2 \\
Computers / peripherals & 696 & 467 & 415 & 2.85 & 3.9 & 27.7 & 68.1 \\
Maintenance / support services & 626 & 297 & 251 & 8.23 & 3.5 & 33.2 & 62.3 \\
GIS / city information & 553 & 203 & 320 & 4.75 & 2.2 & 41.4 & 54.8 \\
Cybersecurity & 390 & 194 & 229 & 3.25 & 5.4 & 33.1 & 60.0 \\
Physical security / surveillance & 385 & 222 & 203 & 2.29 & 1.8 & 23.1 & 63.6 \\
Other IT & 277 & 215 & 165 & 1.82 & 5.4 & 27.8 & 66.1 \\
Education technology & 205 & 128 & 124 & 1.87 & 5.4 & 50.2 & 44.4 \\
Smart city / traffic OT & 169 & 106 & 111 & 3.44 & 4.1 & 34.3 & 60.9 \\
Call centre / help-desk & 74 & 46 & 55 & 7.99 & 5.4 & 51.4 & 43.2 \\
\midrule
% --- by buyer sector
Health & 2,950 & 554 & 1,098 & 30.93 & 28.5 & 9.4 & 61.8 \\
Municipal/Local & 2,688 & 1,084 & 667 & 19.93 & 2.2 & 44.1 & 53.4 \\
Other public & 1,295 & 646 & 351 & 10.88 & 2.5 & 41.1 & 54.7 \\
Education & 1,054 & 519 & 330 & 4.68 & 5.1 & 31.8 & 62.6 \\
Infrastructure/Transport & 644 & 337 & 123 & 7.72 & 2.8 & 39.8 & 57.0 \\
Agriculture/Environment & 395 & 231 & 98 & 4.29 & 2.3 & 31.4 & 63.5 \\
Social/Finance & 303 & 156 & 42 & 5.20 & 3.6 & 39.3 & 55.4 \\
Provincial admin & 223 & 125 & 74 & 0.99 & 1.3 & 25.1 & 62.8 \\
Security/Interior & 202 & 142 & 64 & 1.50 & 3.5 & 26.2 & 66.8 \\
Defence & 191 & 96 & 29 & 1.89 & 1.0 & 3.7 & 95.3 \\
Justice & 46 & 32 & 14 & 1.25 & 26.1 & 28.3 & 43.5 \\
\midrule
All & 9,991 & 2,814 & 2,890 & 89.26 & 10.5 & 29.6 & 59.0 \\
```

## 6. Deflator robustness: PPI (Yİ-ÜFE) vs CPI

Yİ-ÜFE (TÜİK domestic PPI, 2003=100) monthly series 2009–Aug 2026 was obtained from a mirror of the TÜİK table (hakedis.org/endeksler/yi-ufe-yurtici-uretici-fiyat-endeksi), stored with its source in `results/revision_b/ppi_turkey_yiufe.csv`. Annual average = mean of months (2026 = Jan–Aug, same convention as CPI). Spot-checks against published TÜİK figures: Dec 2021 = 1022.25, Dec 2022 = 2021.19; the 2022 annual-average change is 128.5%. Factor to 2025 TRY: 2010 PPI 25.21× vs CPI 17.84×; 2020 PPI 8.72× vs CPI 6.78×.

Count-based HHI is unchanged by construction. Value-based HHI (main sample, `firma_v3`, supplier side):

| group | HHI value CPI | HHI value PPI | HHI value excl. largest CPI / PPI | winsorised CPI / PPI | class (value) CPI → PPI |
|---|---:|---:|---:|---:|---|
| All markets pooled | 149 | 126 | 92 / 87 | 87 / 84 | unconcentrated (<1000) |
| ERP / management software | 132 | 143 | 120 / 129 | 96 / 96 | unconcentrated (<1000) |
| GIS / city information | 408 | 435 | 385 / 408 | 347 / 350 | unconcentrated (<1000) |
| Call centre / help-desk | 8,908 | 8,917 | 1,685 / 1,354 | 1,391 / 1,280 | high (>1800) |
| Computers / peripherals | 170 | 188 | 146 / 174 | 155 / 160 | unconcentrated (<1000) |
| Custom software / web / mobile | 264 | 283 | 176 / 154 | 110 / 108 | unconcentrated (<1000) |
| Cybersecurity | 476 | 451 | 442 / 430 | 340 / 354 | unconcentrated (<1000) |
| Education technology | 1,062 | 977 | 752 / 694 | 537 / 503 | **moderate (1000-1800) → unconcentrated (<1000)** |
| Health information systems | 831 | 795 | 868 / 837 | 811 / 794 | unconcentrated (<1000) |
| Maintenance / support services | 301 | 266 | 303 / 271 | 296 / 270 | unconcentrated (<1000) |
| Network / data-centre infra. | 281 | 253 | 234 / 218 | 226 / 219 | unconcentrated (<1000) |
| Other IT | 767 | 801 | 603 / 683 | 296 / 293 | unconcentrated (<1000) |
| Physical security / surveillance | 212 | 218 | 208 / 208 | 210 / 208 | unconcentrated (<1000) |
| Smart city / traffic OT | 2,580 | 2,634 | 823 / 1,010 | 568 / 615 | high (>1800) |
| Software licences | 275 | 276 | 276 / 282 | 270 / 276 | unconcentrated (<1000) |

Largest absolute change across product markets: HHI value 85, excl. largest 332 points. Classification changes (2023 US Merger Guidelines bands; any of value / excl. largest / winsorised / min-LOO, markets and sectors): **7**: education_technology HHI_value 1062→977 (moderate (1000-1800) → unconcentrated (<1000)); Defence HHI_value 938→1014 (unconcentrated (<1000) → moderate (1000-1800)); smart_city_traffic_OT HHI_value_nomax 823→1010 (unconcentrated (<1000) → moderate (1000-1800)); Defence HHI_value_nomax 1026→802 (moderate (1000-1800) → unconcentrated (<1000)); Justice HHI_value_nomax 1634→1950 (moderate (1000-1800) → high (>1800)); smart_city_traffic_OT LOO_value_min 823→1010 (unconcentrated (<1000) → moderate (1000-1800)); Justice LOO_value_min 1634→1950 (moderate (1000-1800) → high (>1800)). Robust (minimum-across-variants) class changes: 0. CSV: `B6_hhi_cpi_vs_ppi.csv`, `B6_class_changes.csv`.
