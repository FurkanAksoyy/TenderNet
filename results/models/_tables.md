### Table A1. Incumbent win, logit (contract level)

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | -0.1869 | 0.2217 | 0.830 [0.537, 1.281] | 0.399 |
| Other negotiated 21(a,c,d,e,f) (vs open) | -0.1379 | 0.1122 | 0.871 [0.699, 1.085] | 0.219 |
| post-Law 7144 (date >= 2018-05-25) | 0.0788 | 0.2726 | 1.082 [0.634, 1.846] | 0.773 |
| 21(b) x post-7144 | 0.8841*** | 0.2676 | 2.421 [1.433, 4.090] | <0.001 |
| log real value (2025 TRY) | -0.0279 | 0.0365 | 0.972 [0.905, 1.045] | 0.444 |
| log # distinct prior suppliers of buyer in market | -0.9098*** | 0.1484 | 0.403 [0.301, 0.538] | <0.001 |
| log # prior contracts of buyer in market | 1.4723*** | 0.1170 | 4.359 [3.466, 5.483] | <0.001 |
| years since buyer's first contract in market | -0.1215*** | 0.0178 | 0.886 [0.855, 0.917] | <0.001 |
| constant | -0.6862 | 0.8072 | 0.503 [0.103, 2.450] | 0.395 |
| Fixed effects | product market (13), year (2011–2026; 2010 pooled into 2011), buyer sector (10) | | | |
| N contracts | 4,913 | | | |
| Mean of outcome | 0.452 | | | |
| Clusters | buyer 1,126; winner 1,437; intersection 3,129 (CGM two-way) | | | |
| McFadden pseudo-R² | 0.1716 | | | |
| Log-likelihood | -2802.53 | | | |

SE: two-way clustered (buyer, winning firm), Cameron–Gelbach–Miller, small-sample factor G/(G−1)·(N−1)/(N−K). *** p<0.001, ** p<0.01, * p<0.05.

### Table A1-AME. Average marginal effects (delta method, two-way clustered V)

| model | Variable | subset | AME (pp) | SE (pp) | 95% CI (pp) | p |
|---|---|---|---:|---:|---:|---:|
| A1 | 21(b) negotiated (vs open) | all | 6.90 | 2.76 | [1.50, 12.31] | 0.012 |
| A1 | Other negotiated 21(a,c,d,e,f) (vs open) | all | -2.72 | 2.21 | [-7.04, 1.60] | 0.217 |
| A1 | post-Law 7144 (date >= 2018-05-25) | all | 3.37 | 5.32 | [-7.05, 13.80] | 0.526 |
| A1 | log real value (2025 TRY) | all | -0.54 | 0.71 | [-1.93, 0.84] | 0.442 |
| A1 | log # distinct prior suppliers of buyer in market | all | -17.67 | 2.74 | [-23.04, -12.31] | <0.001 |
| A1 | log # prior contracts of buyer in market | all | 28.60 | 1.99 | [24.70, 32.50] | <0.001 |
| A1 | years since buyer's first contract in market | all | -2.36 | 0.34 | [-3.03, -1.69] | <0.001 |
| A1 | 21(b) negotiated (vs open) | pre-7144 | -3.79 | 4.42 | [-12.45, 4.88] | 0.392 |
| A1 | 21(b) negotiated (vs open) | post-7144 | 13.52 | 3.24 | [7.18, 19.87] | <0.001 |
| A1 | 21(b) negotiated (vs open) | post minus pre | 17.31 | 5.18 | [7.16, 27.46] | <0.001 |

### Table A1-pred. Mean predicted P(incumbent wins) by procedure and period (model A1, observed covariates)

| procedure | pre-7144 | post-7144 |
|---|---:|---:|
| open | 0.399 | 0.485 |
| 21b | 0.361 | 0.620 |
| oth_neg | 0.371 | 0.459 |

Raw incumbent-win rates (A sample):

| period | procedure | rate | n |
|---|---|---:|---:|
| pre | 21b | 0.540 | 198 |
| pre | open | 0.383 | 1161 |
| pre | oth_neg | 0.338 | 520 |
| post | 21b | 0.810 | 420 |
| post | open | 0.476 | 1888 |
| post | oth_neg | 0.353 | 726 |

### Table A2. Robustness of model A (logit, same covariates/FE unless stated; two-way clustered SE)

| Model | N | G buyer | G firm | pseudo-R² | OR 21(b) [p] | OR post-7144 [p] | OR 21(b)×post [p] | OR log prior suppliers [p] | OR log prior contracts [p] |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A1_main | 4,913 | 1,126 | 1,437 | 0.172 | 0.83 [0.399] | 1.08 [0.773] | 2.42 [<0.001] | 0.40 [<0.001] | 4.36 [<0.001] |
| A2_trend_noYearFE | 4,913 | 1,126 | 1,437 | 0.167 | 0.85 [0.454] | 1.13 [0.409] | 2.22 [0.003] | 0.41 [<0.001] | 4.32 [<0.001] |
| A3_21f_separate | 4,913 | 1,126 | 1,437 | 0.172 | 0.84 [0.434] | 1.11 [0.703] | 2.38 [0.001] | 0.40 [<0.001] | 4.36 [<0.001] |
| A4_no_history_counts | 4,913 | 1,126 | 1,437 | 0.110 | 0.85 [0.473] | 1.14 [0.623] | 2.90 [<0.001] | — | — |
| R_excl_health_buyers | 3,411 | 637 | 1,249 | 0.116 | 0.55 [0.178] | 1.13 [0.673] | 0.86 [0.782] | 0.40 [<0.001] | 4.93 [<0.001] |
| R_health_buyers_only | 1,502 | 489 | 243 | 0.196 | 1.15 [0.591] | 0.76 [0.669] | 2.64 [<0.001] | 0.45 [0.008] | 2.70 [<0.001] |
| R_break_KHK694_2017-08-25 | 4,913 | 1,126 | 1,437 | 0.172 | 0.78 [0.261] | 1.29 [0.241] | 2.55 [<0.001] | 0.40 [<0.001] | 4.37 [<0.001] |
| R_placebo_break_2016-05-25 | 4,913 | 1,126 | 1,437 | 0.171 | 0.81 [0.420] | 1.04 [0.884] | 2.10 [0.009] | 0.40 [<0.001] | 4.39 [<0.001] |
| R_placebo_break_2020-05-25 | 4,913 | 1,126 | 1,437 | 0.170 | 1.13 [0.404] | 1.35 [0.225] | 1.57 [0.083] | 0.40 [<0.001] | 4.39 [<0.001] |
| R_excl_2020 | 4,503 | 1,110 | 1,373 | 0.160 | 0.87 [0.516] | 1.11 [0.698] | 2.15 [0.004] | 0.40 [<0.001] | 4.21 [<0.001] |
| R_it_only | 4,908 | 1,125 | 1,436 | 0.172 | 0.83 [0.393] | 1.08 [0.774] | 2.43 [<0.001] | 0.40 [<0.001] | 4.37 [<0.001] |
| R_broad | 5,623 | 1,298 | 1,769 | 0.161 | 1.10 [0.616] | 1.01 [0.962] | 1.87 [0.012] | 0.38 [<0.001] | 4.39 [<0.001] |
| R_buyer_kurum | 5,147 | 1,046 | 1,483 | 0.193 | 0.90 [0.627] | 1.28 [0.282] | 2.00 [0.006] | 0.32 [<0.001] | 4.28 [<0.001] |
| R_firm_original | 4,913 | 1,126 | 1,604 | 0.148 | 1.11 [0.611] | 1.05 [0.865] | 1.77 [0.026] | 0.57 [<0.001] | 3.62 [<0.001] |

A2 = linear time trend instead of year FE (post-7144 main effect then identified across years); A3 = 21(f) separated from other negotiated (A3's 21(f) OR 0.90, p=0.51; 21(f)×post in table CSV); A4 = drops prior-supplier/prior-contract counts; R_* = sample/definition sensitivity; R_break_* = alternative break dates (KHK 694 date 2017-08-25; placebos 2016-05-25 and 2020-05-25). Log-likelihoods (same N=4,913): A1 −2802.54; KHK-694 break −2801.10; placebo 2016 −2806.05; placebo 2020 −2807.77.

### Table A3. Linear probability model with buyer fixed effects (within-buyer)

| Variable | Coef. | SE | 95% CI | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.0137 | 0.0519 | [-0.0881, 0.1154] | 0.793 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.0097 | 0.0256 | [-0.0405, 0.0598] | 0.705 |
| post-Law 7144 (date >= 2018-05-25) | 0.0143 | 0.0503 | [-0.0843, 0.1130] | 0.776 |
| 21(b) x post-7144 | 0.0724 | 0.0561 | [-0.0375, 0.1824] | 0.197 |
| log real value (2025 TRY) | 0.0147 | 0.0080 | [-0.0009, 0.0304] | 0.065 |
| log # distinct prior suppliers of buyer in market | 0.2570*** | 0.0389 | [0.1807, 0.3333] | <0.001 |
| log # prior contracts of buyer in market | 0.0400 | 0.0284 | [-0.0157, 0.0957] | 0.159 |
| years since buyer's first contract in market | -0.0377*** | 0.0067 | [-0.0508, -0.0247] | <0.001 |

FE: buyer (absorbed; 1,126 buyers; sector FE collinear with buyer FE), product market, year. N=4,913; within-R²=0.1017; two-way clustered SE (buyer 1,126, winner 1,437). 450 contracts of buyers with a single A-observation contribute no within variation.

Same LPM without buyer FE (sector FE instead), for comparison:

| Variable | Coef. | SE | 95% CI | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | -0.0252 | 0.0454 | [-0.1142, 0.0638] | 0.580 |
| Other negotiated 21(a,c,d,e,f) (vs open) | -0.0273 | 0.0231 | [-0.0726, 0.0180] | 0.238 |
| post-Law 7144 (date >= 2018-05-25) | 0.0295 | 0.0547 | [-0.0776, 0.1367] | 0.589 |
| 21(b) x post-7144 | 0.1189** | 0.0454 | [0.0299, 0.2078] | 0.009 |
| log real value (2025 TRY) | -0.0038 | 0.0074 | [-0.0183, 0.0108] | 0.613 |
| log # distinct prior suppliers of buyer in market | -0.1546*** | 0.0255 | [-0.2047, -0.1046] | <0.001 |
| log # prior contracts of buyer in market | 0.2699*** | 0.0212 | [0.2282, 0.3115] | <0.001 |
| years since buyer's first contract in market | -0.0231*** | 0.0034 | [-0.0297, -0.0165] | <0.001 |
| constant | 0.3100 | 0.1670 | [-0.0174, 0.6374] | 0.063 |

### Table B-logit-full. Logit: any later contract (binary) — spec `full`

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.6135*** | 0.1533 | 1.847 [1.368, 2.494] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.2279* | 0.1021 | 1.256 [1.028, 1.534] | 0.026 |
| log real value (2025 TRY) | 0.0206 | 0.0368 | 1.021 [0.950, 1.097] | 0.576 |
| firm size: log(1+ prior contracts, other buyers) | 0.4576 | 0.2502 | 1.580 [0.968, 2.580] | 0.067 |
| firm generalism: log(1+ prior distinct markets) | 0.1802 | 0.1678 | 1.197 [0.862, 1.664] | 0.283 |
| firm buyer breadth: log(1+ prior distinct buyers, other buyers) | -0.3750 | 0.2641 | 0.687 [0.410, 1.153] | 0.156 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2688*** | 0.0513 | 0.764 [0.691, 0.845] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.6374*** | 0.0603 | 1.892 [1.681, 2.129] | <0.001 |
| constant | -2.1365** | 0.6976 | 0.118 [0.030, 0.463] | 0.002 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1358 | | | |
| Log-likelihood | -1909.18 | | | |

### Table B-logit-size_generalism. Logit: any later contract (binary) — spec `size_generalism`

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.6258*** | 0.1528 | 1.870 [1.386, 2.523] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.2307* | 0.1017 | 1.260 [1.032, 1.537] | 0.023 |
| log real value (2025 TRY) | 0.0211 | 0.0369 | 1.021 [0.950, 1.098] | 0.567 |
| firm size: log(1+ prior contracts, other buyers) | 0.1217 | 0.0953 | 1.129 [0.937, 1.361] | 0.201 |
| firm generalism: log(1+ prior distinct markets) | 0.1813 | 0.1723 | 1.199 [0.855, 1.680] | 0.293 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2706*** | 0.0511 | 0.763 [0.690, 0.843] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.6435*** | 0.0603 | 1.903 [1.691, 2.142] | <0.001 |
| constant | -2.1500** | 0.6981 | 0.116 [0.030, 0.458] | 0.002 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1352 | | | |
| Log-likelihood | -1910.49 | | | |

### Table B-logit-generalism_only. Logit: any later contract (binary) — spec `generalism_only`

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.6301*** | 0.1544 | 1.878 [1.387, 2.542] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.2270* | 0.1020 | 1.255 [1.028, 1.532] | 0.026 |
| log real value (2025 TRY) | 0.0215 | 0.0371 | 1.022 [0.950, 1.099] | 0.562 |
| firm generalism: log(1+ prior distinct markets) | 0.3828*** | 0.0673 | 1.466 [1.285, 1.673] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2844*** | 0.0498 | 0.752 [0.682, 0.830] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.6465*** | 0.0602 | 1.909 [1.697, 2.148] | <0.001 |
| constant | -2.2000** | 0.6940 | 0.111 [0.028, 0.432] | 0.002 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1344 | | | |
| Log-likelihood | -1912.24 | | | |

### Table B-logit-size_only. Logit: any later contract (binary) — spec `size_only`

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.6179*** | 0.1524 | 1.855 [1.376, 2.501] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.2245* | 0.1018 | 1.252 [1.025, 1.528] | 0.027 |
| log real value (2025 TRY) | 0.0232 | 0.0371 | 1.023 [0.952, 1.101] | 0.532 |
| firm size: log(1+ prior contracts, other buyers) | 0.2057*** | 0.0379 | 1.228 [1.140, 1.323] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2622*** | 0.0492 | 0.769 [0.699, 0.847] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.6406*** | 0.0593 | 1.898 [1.690, 2.131] | <0.001 |
| constant | -2.1470** | 0.6960 | 0.117 [0.030, 0.457] | 0.002 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1347 | | | |
| Log-likelihood | -1911.57 | | | |

### Table B-ppml-full. Poisson PML: number of later contracts — spec `full`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4885*** | 0.0736 | 1.630 [1.411, 1.883] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1843* | 0.0789 | 1.202 [1.030, 1.403] | 0.019 |
| log real value (2025 TRY) | 0.0049 | 0.0221 | 1.005 [0.962, 1.049] | 0.823 |
| firm size: log(1+ prior contracts, other buyers) | 0.2872* | 0.1219 | 1.333 [1.049, 1.692] | 0.019 |
| firm generalism: log(1+ prior distinct markets) | 0.1650 | 0.1051 | 1.179 [0.960, 1.449] | 0.117 |
| firm buyer breadth: log(1+ prior distinct buyers, other buyers) | -0.2261 | 0.1284 | 0.798 [0.620, 1.026] | 0.078 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2830*** | 0.0345 | 0.754 [0.704, 0.806] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.9020*** | 0.0420 | 2.465 [2.270, 2.676] | <0.001 |
| constant | -1.7908*** | 0.4840 | 0.167 [0.065, 0.431] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.2579 | | | |
| Log-likelihood | -3253.10 | | | |

### Table B-ppml-size_generalism. Poisson PML: number of later contracts — spec `size_generalism`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4969*** | 0.0739 | 1.644 [1.422, 1.900] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1864* | 0.0791 | 1.205 [1.032, 1.407] | 0.018 |
| log real value (2025 TRY) | 0.0053 | 0.0221 | 1.005 [0.963, 1.050] | 0.811 |
| firm size: log(1+ prior contracts, other buyers) | 0.0872 | 0.0581 | 1.091 [0.974, 1.223] | 0.133 |
| firm generalism: log(1+ prior distinct markets) | 0.1595 | 0.1087 | 1.173 [0.948, 1.451] | 0.142 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2852*** | 0.0344 | 0.752 [0.703, 0.804] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.9084*** | 0.0421 | 2.480 [2.284, 2.694] | <0.001 |
| constant | -1.8063*** | 0.4856 | 0.164 [0.063, 0.425] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.2575 | | | |
| Log-likelihood | -3254.99 | | | |

### Table B-ppml-generalism_only. Poisson PML: number of later contracts — spec `generalism_only`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.5079*** | 0.0821 | 1.662 [1.415, 1.952] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1813* | 0.0793 | 1.199 [1.026, 1.400] | 0.022 |
| log real value (2025 TRY) | 0.0060 | 0.0222 | 1.006 [0.963, 1.051] | 0.787 |
| firm generalism: log(1+ prior distinct markets) | 0.2970*** | 0.0506 | 1.346 [1.219, 1.486] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2978*** | 0.0341 | 0.742 [0.694, 0.794] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.9121*** | 0.0423 | 2.490 [2.291, 2.705] | <0.001 |
| constant | -1.8540*** | 0.4843 | 0.157 [0.061, 0.405] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.2566 | | | |
| Log-likelihood | -3258.56 | | | |

### Table B-ppml-size_only. Poisson PML: number of later contracts — spec `size_only`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4827*** | 0.0710 | 1.620 [1.410, 1.862] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1811* | 0.0793 | 1.199 [1.026, 1.400] | 0.022 |
| log real value (2025 TRY) | 0.0072 | 0.0221 | 1.007 [0.964, 1.052] | 0.744 |
| firm size: log(1+ prior contracts, other buyers) | 0.1587*** | 0.0271 | 1.172 [1.111, 1.236] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2777*** | 0.0337 | 0.758 [0.709, 0.809] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.9069*** | 0.0421 | 2.477 [2.280, 2.690] | <0.001 |
| constant | -1.8050*** | 0.4881 | 0.164 [0.063, 0.428] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.2567 | | | |
| Log-likelihood | -3258.40 | | | |

### Table B-nb2-full. NB2 (α estimated): number of later contracts — spec `full`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4755*** | 0.0756 | 1.609 [1.387, 1.866] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1734* | 0.0797 | 1.189 [1.017, 1.390] | 0.030 |
| log real value (2025 TRY) | 0.0087 | 0.0231 | 1.009 [0.964, 1.055] | 0.706 |
| firm size: log(1+ prior contracts, other buyers) | 0.3096* | 0.1236 | 1.363 [1.070, 1.736] | 0.012 |
| firm generalism: log(1+ prior distinct markets) | 0.1791 | 0.1000 | 1.196 [0.983, 1.455] | 0.073 |
| firm buyer breadth: log(1+ prior distinct buyers, other buyers) | -0.2704* | 0.1346 | 0.763 [0.586, 0.994] | 0.045 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2641*** | 0.0357 | 0.768 [0.716, 0.823] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.8838*** | 0.0422 | 2.420 [2.228, 2.629] | <0.001 |
| alpha | 0.4591*** | 0.1154 | 1.583 [1.262, 1.984] | <0.001 |
| constant | -1.8780*** | 0.4774 | 0.153 [0.060, 0.390] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1457 | | | |
| Log-likelihood | -3176.86 | | | |

### Table B-nb2-size_generalism. NB2 (α estimated): number of later contracts — spec `size_generalism`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4847*** | 0.0757 | 1.624 [1.400, 1.883] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1753* | 0.0794 | 1.192 [1.020, 1.392] | 0.027 |
| log real value (2025 TRY) | 0.0091 | 0.0232 | 1.009 [0.964, 1.056] | 0.695 |
| firm size: log(1+ prior contracts, other buyers) | 0.0703 | 0.0563 | 1.073 [0.961, 1.198] | 0.212 |
| firm generalism: log(1+ prior distinct markets) | 0.1746 | 0.1035 | 1.191 [0.972, 1.459] | 0.091 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2651*** | 0.0355 | 0.767 [0.716, 0.822] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.8898*** | 0.0421 | 2.435 [2.242, 2.644] | <0.001 |
| alpha | 0.4618*** | 0.1164 | 1.587 [1.263, 1.994] | <0.001 |
| constant | -1.8898*** | 0.4788 | 0.151 [0.059, 0.386] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1453 | | | |
| Log-likelihood | -3178.49 | | | |

### Table B-nb2-generalism_only. NB2 (α estimated): number of later contracts — spec `generalism_only`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4907*** | 0.0800 | 1.633 [1.396, 1.911] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1697* | 0.0794 | 1.185 [1.014, 1.384] | 0.033 |
| log real value (2025 TRY) | 0.0093 | 0.0233 | 1.009 [0.964, 1.056] | 0.691 |
| firm generalism: log(1+ prior distinct markets) | 0.2874*** | 0.0481 | 1.333 [1.213, 1.465] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2748*** | 0.0352 | 0.760 [0.709, 0.814] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.8930*** | 0.0421 | 2.443 [2.249, 2.652] | <0.001 |
| alpha | 0.4677*** | 0.1161 | 1.596 [1.271, 2.004] | <0.001 |
| constant | -1.9276*** | 0.4762 | 0.145 [0.057, 0.370] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1449 | | | |
| Log-likelihood | -3179.92 | | | |

### Table B-nb2-size_only. NB2 (α estimated): number of later contracts — spec `size_only`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4736*** | 0.0730 | 1.606 [1.392, 1.853] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1716* | 0.0796 | 1.187 [1.016, 1.388] | 0.031 |
| log real value (2025 TRY) | 0.0117 | 0.0232 | 1.012 [0.967, 1.059] | 0.614 |
| firm size: log(1+ prior contracts, other buyers) | 0.1489*** | 0.0264 | 1.161 [1.102, 1.222] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2561*** | 0.0346 | 0.774 [0.723, 0.828] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.8875*** | 0.0416 | 2.429 [2.239, 2.635] | <0.001 |
| alpha | 0.4654*** | 0.1163 | 1.593 [1.268, 2.001] | <0.001 |
| constant | -1.8865*** | 0.4787 | 0.152 [0.059, 0.387] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1446 | | | |
| Log-likelihood | -3180.98 | | | |

For NB2, the row `alpha` is α itself (Var = μ + αμ²); its 'IRR' column is meaningless and can be ignored.

### Table B-AME. Logit AMEs (percentage points)

| model | Variable | subset | AME (pp) | SE (pp) | 95% CI (pp) | p |
|---|---|---|---:|---:|---:|---:|
| B_logit_full | 21(b) negotiated (vs open) | all | 12.12 | 3.18 | [5.90, 18.35] | <0.001 |
| B_logit_full | Other negotiated 21(a,c,d,e,f) (vs open) | all | 4.32 | 1.95 | [0.51, 8.14] | 0.026 |
| B_logit_full | log real value (2025 TRY) | all | 0.39 | 0.69 | [-0.97, 1.74] | 0.576 |
| B_logit_full | firm size: log(1+ prior contracts, other buyers) | all | 8.58 | 4.67 | [-0.56, 17.73] | 0.066 |
| B_logit_full | firm generalism: log(1+ prior distinct markets) | all | 3.38 | 3.14 | [-2.78, 9.54] | 0.282 |
| B_logit_full | firm buyer breadth: log(1+ prior distinct buyers, other buyers) | all | -7.03 | 4.93 | [-16.69, 2.62] | 0.153 |
| B_logit_full | buyer experience: log(1+ buyer's prior contracts, all markets) | all | -5.04 | 0.94 | [-6.89, -3.19] | <0.001 |
| B_logit_full | log # later buyer-market contracts (opportunities) | all | 11.96 | 1.09 | [9.82, 14.09] | <0.001 |
| B_logit_size_generalism | 21(b) negotiated (vs open) | all | 12.39 | 3.17 | [6.17, 18.60] | <0.001 |
| B_logit_size_generalism | Other negotiated 21(a,c,d,e,f) (vs open) | all | 4.38 | 1.94 | [0.58, 8.18] | 0.024 |
| B_logit_size_generalism | log real value (2025 TRY) | all | 0.40 | 0.69 | [-0.96, 1.75] | 0.567 |
| B_logit_size_generalism | firm size: log(1+ prior contracts, other buyers) | all | 2.29 | 1.79 | [-1.23, 5.80] | 0.202 |
| B_logit_size_generalism | firm generalism: log(1+ prior distinct markets) | all | 3.40 | 3.23 | [-2.92, 9.73] | 0.292 |
| B_logit_size_generalism | buyer experience: log(1+ buyer's prior contracts, all markets) | all | -5.08 | 0.94 | [-6.92, -3.24] | <0.001 |
| B_logit_size_generalism | log # later buyer-market contracts (opportunities) | all | 12.08 | 1.09 | [9.95, 14.21] | <0.001 |
| B_logit_generalism_only | 21(b) negotiated (vs open) | all | 12.49 | 3.21 | [6.21, 18.78] | <0.001 |
| B_logit_generalism_only | Other negotiated 21(a,c,d,e,f) (vs open) | all | 4.32 | 1.94 | [0.51, 8.13] | 0.026 |
| B_logit_generalism_only | log real value (2025 TRY) | all | 0.40 | 0.70 | [-0.96, 1.77] | 0.562 |
| B_logit_generalism_only | firm generalism: log(1+ prior distinct markets) | all | 7.20 | 1.25 | [4.75, 9.65] | <0.001 |
| B_logit_generalism_only | buyer experience: log(1+ buyer's prior contracts, all markets) | all | -5.35 | 0.91 | [-7.14, -3.55] | <0.001 |
| B_logit_generalism_only | log # later buyer-market contracts (opportunities) | all | 12.15 | 1.08 | [10.03, 14.28] | <0.001 |
| B_logit_size_only | 21(b) negotiated (vs open) | all | 12.24 | 3.17 | [6.03, 18.44] | <0.001 |
| B_logit_size_only | Other negotiated 21(a,c,d,e,f) (vs open) | all | 4.26 | 1.94 | [0.46, 8.07] | 0.028 |
| B_logit_size_only | log real value (2025 TRY) | all | 0.44 | 0.70 | [-0.93, 1.80] | 0.532 |
| B_logit_size_only | firm size: log(1+ prior contracts, other buyers) | all | 3.86 | 0.71 | [2.47, 5.26] | <0.001 |
| B_logit_size_only | buyer experience: log(1+ buyer's prior contracts, all markets) | all | -4.93 | 0.91 | [-6.70, -3.15] | <0.001 |
| B_logit_size_only | log # later buyer-market contracts (opportunities) | all | 12.03 | 1.07 | [9.93, 14.13] | <0.001 |

(model column: rows are in order full, size_generalism, generalism_only, size_only; see AME_A_B.csv.)

### Table B-VIF and correlations (estimation sample)

| Variable | VIF |
|---|---:|
| 21(b) negotiated (vs open) | 1.16 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 1.18 |
| log real value (2025 TRY) | 1.15 |
| firm size: log(1+ prior contracts, other buyers) | 63.32 |
| firm generalism: log(1+ prior distinct markets) | 4.21 |
| firm buyer breadth: log(1+ prior distinct buyers, other buyers) | 60.54 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | 1.14 |
| log # later buyer-market contracts (opportunities) | 1.03 |

```
                           log_firm_prior_contracts  log_firm_prior_markets  log_firm_prior_buyers  log_buyer_prior_contracts  log_opp
log_firm_prior_contracts                      1.000                   0.858                  0.992                     -0.129   -0.018
log_firm_prior_markets                        0.858                   1.000                  0.851                      0.015    0.004
log_firm_prior_buyers                         0.992                   0.851                  1.000                     -0.139   -0.021
log_buyer_prior_contracts                    -0.129                   0.015                 -0.139                      1.000    0.155
log_opp                                      -0.018                   0.004                 -0.021                      0.155    1.000
```

### Overdispersion and offset tests (full spec)

- NB2 α = 0.459 (two-way SE 0.115).
- LR test α=0 (boundary, p halved): LR = 152.48, p = 2.5e-35.
- Cameron–Trivedi auxiliary regression (NB2 form): α̂ = 0.276, t = 7.94, p = 2.8e-15.
- Pearson dispersion of PPML = 1.276.
- Offset restriction (ppml): coefficient on log(opportunities) = 0.902 (SE 0.042); H0 = 1: z = -2.33, p = 0.020.
- Offset restriction (nb2): coefficient on log(opportunities) = 0.884 (SE 0.042); H0 = 1: z = -2.75, p = 0.006.

### Table C. Share of 21(b) by dyad status

| scope | status | n | n 21(b) | share 21(b), count | value (bn 2025 TRY) | 21(b) value (bn) | share 21(b), value |
|---|---|---:|---:|---:|---:|---:|---:|
| all contracts | first | 7,769 | 601 | 0.077 | 70.34 | 4.96 | 0.071 |
| all contracts | repeat | 2,222 | 447 | 0.201 | 19.40 | 1.22 | 0.063 |
| buyer has prior history in market (A sample) | first | 2,691 | 171 | 0.064 | 27.21 | 2.71 | 0.100 |
| buyer has prior history in market (A sample) | repeat | 2,222 | 447 | 0.201 | 19.40 | 1.22 | 0.063 |
| all, excl. largest contract | first | 7,768 | 601 | 0.077 | 62.80 | 4.96 | 0.079 |
| all, excl. largest contract | repeat | 2,222 | 447 | 0.201 | 19.40 | 1.22 | 0.063 |

| test | estimate | SE | p | N | clusters |
|---|---:|---:|---:|---:|---|
| naive chi2 (count), all | 280.7775 |  | 5.08e-63 | 9,991 |  |
| LPM diff repeat-first, count, all, cluster=buyer | 0.1238 | 0.0161 | 1.28e-14 | 9,991 | 2890 |
| LPM diff repeat-first, count, all, cluster=dyad | 0.1238 | 0.0144 | 6.29e-18 | 9,991 | 7761 |
| LPM diff repeat-first, count, all, two-way buyer+firm | 0.1238 | 0.0308 | 5.71e-05 | 9,991 | (2890, 2814, 7219) |
| LPM diff repeat-first, value-weighted, all, cluster=buyer | -0.0078 | 0.0153 | 6.11e-01 | 9,991 | 2890 |
| LPM diff repeat-first, value-weighted, all, cluster=dyad | -0.0078 | 0.0154 | 6.12e-01 | 9,991 | 7761 |
| LPM diff repeat-first, value-weighted, all, two-way buyer+firm | -0.0078 | 0.0170 | 6.46e-01 | 9,991 | (2890, 2814, 7219) |
| LPM diff repeat-first, count, A sample, cluster=buyer | 0.1376 | 0.0162 | 2.02e-17 | 4,913 | 1126 |
| LPM diff repeat-first, count, A sample, cluster=dyad | 0.1376 | 0.0151 | 6.04e-20 | 4,913 | 3365 |
| LPM diff repeat-first, count, A sample, two-way buyer+firm | 0.1376 | 0.0328 | 2.68e-05 | 4,913 | (1126, 1437, 3129) |
| LPM diff repeat-first, value-weighted, A sample, cluster=buyer | -0.0368 | 0.0262 | 1.60e-01 | 4,913 | 1126 |
| LPM diff repeat-first, value-weighted, A sample, cluster=dyad | -0.0368 | 0.0264 | 1.62e-01 | 4,913 | 3365 |
| LPM diff repeat-first, value-weighted, A sample, two-way buyer+firm | -0.0368 | 0.0268 | 1.69e-01 | 4,913 | (1126, 1437, 3129) |
| LPM diff repeat-first, count, all excl. largest, cluster=buyer | 0.1238 | 0.0161 | 1.28e-14 | 9,990 | 2890 |
| LPM diff repeat-first, count, all excl. largest, cluster=dyad | 0.1238 | 0.0144 | 6.33e-18 | 9,990 | 7760 |
| LPM diff repeat-first, count, all excl. largest, two-way buyer+firm | 0.1238 | 0.0308 | 5.72e-05 | 9,990 | (2890, 2813, 7218) |
| LPM diff repeat-first, value-weighted, all excl. largest, cluster=buyer | -0.0163 | 0.0142 | 2.52e-01 | 9,990 | 2890 |
| LPM diff repeat-first, value-weighted, all excl. largest, cluster=dyad | -0.0163 | 0.0144 | 2.58e-01 | 9,990 | 7760 |
| LPM diff repeat-first, value-weighted, all excl. largest, two-way buyer+firm | -0.0163 | 0.0159 | 3.05e-01 | 9,990 | (2890, 2813, 7218) |
| LPM diff, count, all, + year/market/sector FE, cluster=buyer | 0.0484 | 0.0095 | 3.20e-07 | 9,991 | 2890 |
| LPM diff, count, all, buyer FE + year FE, cluster=buyer | 0.0116 | 0.0082 | 1.58e-01 | 9,991 | 2890 |

By period (count shares):

| period | status | n | share 21(b) |
|---|---|---:|---:|
| pre-7144 | first | 4,202 | 0.081 |
| pre-7144 | repeat | 728 | 0.147 |
| post-7144 | first | 3,567 | 0.073 |
| post-7144 | repeat | 1,494 | 0.228 |

### Table D0. Bid-count sample coverage by year (main sample)

| year | contracts in main sample | sampled tenders in main | with bid counts | design weight |
|---|---:|---:|---:|---:|
| 2010 | 100 | 3 | 0 | — |
| 2011 | 573 | 18 | 0 | — |
| 2012 | 603 | 14 | 14 | 43.07 |
| 2013 | 713 | 22 | 22 | 32.41 |
| 2014 | 679 | 28 | 28 | 24.25 |
| 2015 | 681 | 18 | 18 | 37.83 |
| 2016 | 677 | 24 | 24 | 28.21 |
| 2017 | 692 | 22 | 22 | 31.45 |
| 2018 | 624 | 33 | 33 | 18.91 |
| 2019 | 545 | 24 | 24 | 22.71 |
| 2020 | 663 | 27 | 27 | 24.56 |
| 2021 | 730 | 32 | 32 | 22.81 |
| 2022 | 712 | 31 | 31 | 22.97 |
| 2023 | 622 | 32 | 32 | 19.44 |
| 2024 | 568 | 24 | 24 | 23.67 |
| 2025 | 700 | 26 | 26 | 26.92 |
| 2026 | 109 | 36 | 36 | 3.03 |

### Table D1. Design-weighted single-bid rates (95% CI, logit-transformed linearization CI)

| outcome | breakdown | group | rate | SE | 95% CI | n | events |
|---|---|---|---:|---:|---:|---:|---:|
| single | overall | all | 0.442 | 0.026 | [0.391, 0.494] | 393 | 183 |
| single | procedure | open | 0.408 | 0.035 | [0.342, 0.477] | 225 | 98 |
| single | procedure | 21b | 0.750 | 0.067 | [0.598, 0.858] | 50 | 39 |
| single | procedure | 21f | 0.400 | 0.048 | [0.310, 0.496] | 114 | 46 |
| single | procedure | oth_neg | 0.000 | 0.000 | — | 4 | 0 |
| single | incumbency | incumbent winner | 0.712 | 0.049 | [0.607, 0.798] | 95 | 67 |
| single | incumbency | non-incumbent winner | 0.324 | 0.046 | [0.241, 0.421] | 113 | 39 |
| single | incumbency | buyer first in market (undefined) | 0.383 | 0.038 | [0.312, 0.460] | 185 | 77 |
| single | procedure x incumbency | open | incumbent winner | 0.687 | 0.063 | [0.553, 0.796] | 58 | 38 |
| single | procedure x incumbency | open | non-incumbent winner | 0.366 | 0.061 | [0.256, 0.492] | 69 | 27 |
| single | procedure x incumbency | negotiated | incumbent winner | 0.749 | 0.079 | [0.566, 0.872] | 37 | 29 |
| single | procedure x incumbency | negotiated | non-incumbent winner | 0.259 | 0.068 | [0.148, 0.413] | 44 | 12 |
| single | period (tender date vs 2018-05-25) | pre-7144 | 0.386 | 0.042 | [0.307, 0.472] | 140 | 55 |
| single | period (tender date vs 2018-05-25) | post-7144 | 0.489 | 0.033 | [0.424, 0.553] | 253 | 128 |
| single_valid | overall | all | 0.558 | 0.027 | [0.505, 0.609] | 393 | 230 |
| single_valid | procedure | open | 0.559 | 0.035 | [0.490, 0.626] | 225 | 133 |
| single_valid | procedure | 21b | 0.816 | 0.060 | [0.669, 0.907] | 50 | 42 |
| single_valid | procedure | 21f | 0.469 | 0.049 | [0.375, 0.564] | 114 | 54 |
| single_valid | procedure | oth_neg | 0.185 | 0.174 | [0.023, 0.686] | 4 | 1 |
| single_valid | incumbency | incumbent winner | 0.767 | 0.046 | [0.664, 0.845] | 95 | 74 |
| single_valid | incumbency | non-incumbent winner | 0.484 | 0.049 | [0.390, 0.579] | 113 | 57 |
| single_valid | incumbency | buyer first in market (undefined) | 0.502 | 0.040 | [0.424, 0.579] | 185 | 99 |
| single_valid | procedure x incumbency | open | incumbent winner | 0.764 | 0.058 | [0.634, 0.858] | 58 | 44 |
| single_valid | procedure x incumbency | open | non-incumbent winner | 0.588 | 0.062 | [0.463, 0.703] | 69 | 42 |
| single_valid | procedure x incumbency | negotiated | incumbent winner | 0.771 | 0.077 | [0.587, 0.888] | 37 | 30 |
| single_valid | procedure x incumbency | negotiated | non-incumbent winner | 0.319 | 0.072 | [0.197, 0.474] | 44 | 15 |
| single_valid | period (tender date vs 2018-05-25) | pre-7144 | 0.491 | 0.043 | [0.407, 0.575] | 140 | 70 |
| single_valid | period (tender date vs 2018-05-25) | post-7144 | 0.615 | 0.033 | [0.549, 0.676] | 253 | 160 |

### Table D2. Contrasts (design-weighted differences, stratified linearization)

| outcome | contrast | diff | SE | 95% CI | p |
|---|---|---:|---:|---:|---:|
| single | incumbent - non-incumbent | 0.387 | 0.068 | [0.255, 0.520] | <0.001 |
| single | incumbent - non-incumbent | open | 0.322 | 0.088 | [0.149, 0.494] | <0.001 |
| single | incumbent - non-incumbent | negotiated | 0.489 | 0.105 | [0.283, 0.695] | <0.001 |
| single | 21b - open | 0.342 | 0.076 | [0.193, 0.491] | <0.001 |
| single | 21f - open | -0.008 | 0.059 | [-0.124, 0.108] | 0.894 |
| single | post - pre 7144 | 0.102 | 0.054 | [-0.003, 0.208] | 0.057 |
| single_valid | incumbent - non-incumbent | 0.283 | 0.068 | [0.149, 0.416] | <0.001 |
| single_valid | incumbent - non-incumbent | open | 0.176 | 0.085 | [0.009, 0.343] | 0.039 |
| single_valid | incumbent - non-incumbent | negotiated | 0.451 | 0.107 | [0.242, 0.661] | <0.001 |
| single_valid | 21b - open | 0.257 | 0.070 | [0.120, 0.394] | <0.001 |
| single_valid | 21f - open | -0.090 | 0.059 | [-0.207, 0.026] | 0.129 |
| single_valid | post - pre 7144 | 0.124 | 0.054 | [0.017, 0.231] | 0.023 |

Adjusted logit (defined-incumbency tenders only, n=208): single bid ~ incumbent + negotiated + year; buyer-clustered. OR(incumbent) = 4.44 [2.39, 8.25], p = <0.001; OR(negotiated) = 1.02, p = 0.954.

### Table D3. Trend test (logit of single bid on year, centred 2018)

| outcome | model | b(year) | SE | OR/year | p | N |
|---|---|---:|---:|---:|---:|---:|
| single | unweighted logit, HC1 | 0.0488 | 0.0240 | 1.050 | 0.042 | 393 |
| single | design-weighted logit, HC1 | 0.0429 | 0.0270 | 1.044 | 0.112 | 393 |
| single | unweighted logit + negotiated dummy, buyer-clustered | 0.0534 | 0.0250 | 1.055 | 0.032 | 393 |
| single_valid | unweighted logit, HC1 | 0.0616 | 0.0248 | 1.064 | 0.013 | 393 |
| single_valid | design-weighted logit, HC1 | 0.0588 | 0.0279 | 1.061 | 0.035 | 393 |
| single_valid | unweighted logit + negotiated dummy, buyer-clustered | 0.0616 | 0.0251 | 1.063 | 0.014 | 393 |

### Table D4. Document downloaders vs bids (tenders with downloaders > 0; design-weighted means)

| subset | variable | mean | SE | 95% CI | n |
|---|---|---:|---:|---:|---:|
| all (downloaders>0) | indiren_sayisi | 4.022 | 0.198 | [3.633, 4.410] | 308 |
| all (downloaders>0) | gecerli_teklif | 1.905 | 0.086 | [1.736, 2.073] | 308 |
| all (downloaders>0) | gap_valid | 2.117 | 0.167 | [1.790, 2.444] | 308 |
| all (downloaders>0) | gap_total | 1.730 | 0.153 | [1.431, 2.030] | 308 |
| all (downloaders>0) | valid_per_dl | 0.630 | 0.032 | [0.567, 0.693] | 308 |
| all (downloaders>0) | multi_dl_single_valid | 0.446 | 0.030 | [0.388, 0.505] | 308 |
| open | indiren_sayisi | 4.543 | 0.248 | [4.056, 5.030] | 221 |
| open | gecerli_teklif | 1.984 | 0.112 | [1.766, 2.203] | 221 |
| open | gap_valid | 2.559 | 0.205 | [2.157, 2.961] | 221 |
| open | gap_total | 2.051 | 0.189 | [1.680, 2.421] | 221 |
| open | valid_per_dl | 0.580 | 0.040 | [0.503, 0.658] | 221 |
| open | multi_dl_single_valid | 0.524 | 0.034 | [0.457, 0.591] | 221 |
| negotiated | indiren_sayisi | 2.572 | 0.182 | [2.216, 2.928] | 87 |
| negotiated | gecerli_teklif | 1.683 | 0.097 | [1.492, 1.874] | 87 |
| negotiated | gap_valid | 0.889 | 0.161 | [0.574, 1.204] | 87 |
| negotiated | gap_total | 0.839 | 0.159 | [0.528, 1.150] | 87 |
| negotiated | valid_per_dl | 0.767 | 0.037 | [0.694, 0.840] | 87 |
| negotiated | multi_dl_single_valid | 0.230 | 0.048 | [0.136, 0.323] | 87 |