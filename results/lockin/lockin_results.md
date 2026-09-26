# Lock-in: excess repeat contracting (topic `lockin`)

Script: `src/lockin_analysis.py` (run `python src/lockin_analysis.py`, about 45 s).
Permutations: B = 1,000 per null model and per sensitivity. Seeds: `numpy.random.default_rng(42 + i)`. Main N1/N1w/N2 use i = 0/1/2. Sensitivities S1–S8 use i = 10–17.
Machine-readable outputs, all in this folder:
- `null_overall.csv`: every variant × statistic.
- `null_by_group.csv`: heterogeneity, all dimensions and variants.
- `null_contrasts.csv`: pre/post, 21(b) vs open, and the difference-in-differences.
- `observed_by_sector.csv`.
- `buyer_dependence.csv`: buyer index only, no names.
- `lockin_log.json`: descriptives and sample sizes.

Figures, in `figures/`, PNG 300 dpi and PDF:
- `F_L1_incumbency_by_market`
- `F_L2_incumbency_by_year`
- `F_L3_buyer_top_supplier_share`

## 1. Definitions (for Methods)

- **Sample.** The main sample is `in_scope_main == True`: 9,991 contracts, 2,890 buyers (`kurum_il_split`), 2,814 firms (`firma_v3`), 2010-10 to 2026-03.
- **Dyad.** A (buyer, firm) pair with at least one contract, pooled over product markets. Its weight *w* is the number of contracts.
- **Repeat dyad.** A dyad with *w* ≥ 2.
- **Share of contracts in repeat dyads.** Contracts whose dyad has *w* ≥ 2, divided by all contracts.
- **Incumbency rate.** For each contract *i*, let *k* be its buyer, *m* its product market (`urun_pazari`) and *t* its tender date (`tarih_v3`).
  - *i* is **repeat-eligible** if buyer *k* has at least one other contract in market *m* with a date strictly earlier than *t*.
  - *i* is **incumbent** if its winning firm had already won a contract from *k* in *m* on a date strictly earlier than *t*.
  - Incumbency rate = incumbent contracts / repeat-eligible contracts.
  - Same-date ties do not count as prior history. This affects 52 contracts in 24 same-date buyer–market groups. 18 of them are ineligible only because of the tie rule.
  - Eligibility depends only on buyer, market and date, so the eligible set is identical under every permutation.
- **Null models.** Within each cell, the winner labels are randomly permuted across contracts (a uniform random permutation, independent across cells). This keeps each contract's buyer, date, market, procedure and sector. It keeps each buyer's demand per cell and each firm's number of wins per cell, so firm entry and exit timing and market specialisation are preserved. Only who wins from whom is randomised.
  - **N1:** product market × calendar year (234 cells; N1w 84 cells; N2 1,424 cells).
  - **N1w:** product market × 3-year window (2010–12, 2013–15, …, 2022–24, 2025–26).
  - **N2:** product market × year × `sektor_v3`.
  - **N3 (sensitivity S8):** product market × year × province (`il`). This is a local-supplier control.
- **Reported statistics.** For each statistic:
  - observed value;
  - null mean;
  - 95% null interval (2.5th and 97.5th percentiles);
  - ratio = observed / null mean;
  - excess = observed − null mean;
  - z = (observed − null mean) / null SD;
  - one-sided empirical p = (1 + #{null ≥ observed}) / (B + 1). The minimum is 1/1001 = 0.001.
- **Heterogeneity.** Incumbency is computed on the full sample in every permutation and then averaged within subgroups of eligible contracts. The procedure, sector, date and buyer-size tags stay attached to the contract. Each subgroup is therefore compared with its own null.
  - Procedure groups: 21(b) = `negotiated_21b`; open = `open`; other = 21(a,c,d,e,f) + restricted. 21(f) accounts for 2,957 of the 3,051 "other" contracts.
  - Buyer-size terciles are contract-weighted terciles of the buyer's total contract count in the sample: T1 ≤ 4, T2 5–13, T3 > 13.
  - Law 7144: pre means tender date < 2018-05-25.
- **Contrasts.** For example, 21(b) − open and post − pre. The observed difference is compared with the permutation distribution of the same difference.
- **Buyer dependence.** Computed for the 540 buyers with ≥ 5 contracts, using counts.
  - Top-supplier share = max_f n_kf / n_k.
  - Supplier HHI = Σ_f (n_kf / n_k)².
  - Each buyer is compared with its own null distribution under N1 (and N2). "Exceeds" means the observed value is strictly above the buyer's 95th null percentile.
- **Buyer type.** An anonymous keyword class assigned from the buyer label (`buyer_type()` in the script). Buyers are never named.

## 2. Observed statistics (main sample)

| statistic | value |
|---|---|
| dyads | 7,219 |
| repeat dyads (w ≥ 2) | 1,377 (19.1% of dyads) |
| dyad weight distribution | w=1: 5,842; 2: 820; 3: 264; 4: 118; 5: 70; ≥6: 105; max 18 |
| share of contracts in repeat dyads | 41.5% |
| repeat-eligible contracts | 4,913 (49.2% of contracts) |
| incumbent contracts | 2,222 |
| **incumbency rate** | **45.2%** |

Observed values by buyer sector (`observed_by_sector.csv`):

| sector | contracts | share of contracts in repeat dyads | incumbency | eligible |
|---|---|---|---|---|
| Health | 2,950 | 53.6% | 66.7% | 1,502 |
| Municipal/Local | 2,688 | 37.0% | 36.2% | 1,271 |
| Other public | 1,295 | 36.5% | 39.5% | 583 |
| Education | 1,054 | 30.6% | 36.4% | 439 |
| Infrastructure/Transport | 644 | 38.7% | 32.2% | 342 |
| Agriculture/Environment | 395 | 39.2% | 34.8% | 210 |
| Social/Finance | 303 | 44.9% | 35.7% | 196 |
| Provincial admin | 223 | 30.9% | 37.4% | 115 |
| Security/Interior | 202 | 27.7% | 28.0% | 100 |
| Defence | 191 | 50.8% | 29.8% | 131 |
| Justice | 46 | 32.6% | 29.2% | 24 |

The sector values are computed within the sector subsample, so incumbency here uses only that sector's contracts. This is the same as the full-sample values because buyers do not change sector.

## 3. Null models: overall

All p = 0.001, which is the permutation minimum.

| null | statistic | observed | null mean [95% interval] | ratio | z |
|---|---|---|---|---|---|
| N1 (market × year) | repeat dyads | 1,377 | 326 [299, 353] | 4.22 | 76.4 |
| | share of contracts in repeat dyads | 0.415 | 0.071 [0.065, 0.076] | 5.89 | 118.9 |
| | dyads | 7,219 | 9,612 [9,582, 9,644] | 0.75 | −149 |
| | max w | 18 | 5.1 [4, 7] | 3.5 | 15.3 |
| | **incumbency** | **0.452** | **0.062 [0.056, 0.067]** | **7.34** | **138.2** |
| N1w (market × 3-year) | repeat dyads | 1,377 | 320 [294, 348] | 4.31 | 75.8 |
| | share in repeat dyads | 0.415 | 0.069 [0.064, 0.075] | 6.02 | 119.3 |
| | incumbency | 0.452 | 0.060 [0.055, 0.066] | 7.51 | 136.1 |
| N2 (market × year × sector) | repeat dyads | 1,377 | 547 [517, 577] | 2.52 | 53.1 |
| | share in repeat dyads | 0.415 | 0.127 [0.121, 0.133] | 3.27 | 88.1 |
| | incumbency | 0.452 | 0.110 [0.103, 0.116] | 4.13 | 98.6 |
| N3 (market × year × province; S8) | repeat dyads | 1,377 | 861 [834, 892] | 1.60 | 33.6 |
| | share in repeat dyads | 0.415 | 0.216 [0.210, 0.222] | 1.92 | 64.4 |
| | incumbency | 0.452 | 0.207 [0.201, 0.213] | 2.18 | 78.9 |

Excess incumbent contracts under N1 = 0.391 × 4,913 ≈ **1,919 contracts**. These are contracts won by an incumbent beyond what the market-period null predicts.

The 3-year window hardly changes N1. Conditioning on buyer sector (N2) or province (N3) raises the null baseline. The observed rate remains 4.1× and 2.2× its null.

## 4. Heterogeneity: excess incumbency (N1 unless stated)

### 4a. Product market

Figure F-L1. Rows are sorted by excess. The last three columns show the N2 and N3 nulls.

| market | eligible | observed | N1 null mean [95%] | excess | ratio | N2 null | N3 null |
|---|---|---|---|---|---|---|---|
| health_information_systems | 1,252 | 0.716 | 0.151 [0.136, 0.167] | 0.564 | 4.7 | 0.157 | 0.407 |
| maintenance_support_services | 375 | 0.536 | 0.029 [0.013, 0.045] | 0.507 | 18.8 | 0.139 | 0.122 |
| physical_security_surveillance | 182 | 0.418 | 0.030 [0.011, 0.055] | 0.388 | 14.0 | 0.097 | 0.317 |
| other_IT | 112 | 0.393 | 0.019 [0.000, 0.045] | 0.374 | 21.2 | 0.132 | 0.233 |
| ERP_management_software | 745 | 0.392 | 0.027 [0.016, 0.039] | 0.365 | 14.7 | 0.077 | 0.111 |
| network_datacentre_infrastructure | 328 | 0.384 | 0.023 [0.009, 0.040] | 0.361 | 16.8 | 0.106 | 0.121 |
| smart_city_traffic_OT | 58 | 0.397 | 0.041 [0.000, 0.103] | 0.355 | 9.6 | 0.104 | 0.314 |
| cybersecurity | 161 | 0.398 | 0.052 [0.019, 0.087] | 0.346 | 7.7 | 0.132 | 0.186 |
| computers_peripherals | 281 | 0.327 | 0.012 [0.000, 0.025] | 0.316 | 28.0 | 0.047 | 0.164 |
| software_licences | 602 | 0.334 | 0.039 [0.025, 0.055] | 0.295 | 8.5 | 0.105 | 0.139 |
| education_technology | 80 | 0.350 | 0.068 [0.025, 0.125] | 0.282 | 5.1 | 0.201 | 0.168 |
| call_centre_helpdesk | 19 | 0.316 | 0.062 [0.000, 0.158] | 0.254 | 5.1 | 0.222 (p=0.079) | 0.178 (p=0.030) |
| GIS_city_information | 230 | 0.326 | 0.088 [0.057, 0.122] | 0.238 | 3.7 | 0.117 | 0.146 |
| custom_software_web_mobile | 488 | 0.201 | 0.006 [0.000, 0.014] | 0.194 | 31.2 | 0.029 | 0.056 |

- Under N1, every market is above its null (p = 0.001).
- Under N2, every market except call_centre_helpdesk (n = 19, p = 0.079) is above its null.
- Health information systems has the highest observed incumbency and supplies 36.8% of all excess incumbent contracts (≈706 of ≈1,919). ERP supplies 14.2%, maintenance/support 9.9% and software licences 9.2%.
- The largest *ratios* are in low-baseline markets: custom software, computers and other IT.
- Under the province null (N3), health IS has the highest baseline (0.41), because its suppliers are geographically concentrated. The largest remaining ratios are maintenance/support (4.4×), custom software (3.6×), ERP (3.5×) and network/datacentre (3.2×).

### 4b. Buyer sector (N1; N2 in brackets)

| sector | eligible | observed | N1 null [95%] | excess (N1) | excess (N2) |
|---|---|---|---|---|---|
| Health | 1,502 | 0.667 | 0.129 [0.116, 0.142] | 0.539 | 0.524 |
| Other public | 583 | 0.395 | 0.030 [0.017, 0.045] | 0.365 | 0.320 |
| Education | 439 | 0.364 | 0.028 [0.014, 0.043] | 0.337 | 0.246 |
| Municipal/Local | 1,271 | 0.362 | 0.031 [0.023, 0.041] | 0.331 | 0.304 |
| Provincial admin | 115 | 0.374 | 0.046 [0.009, 0.087] | 0.328 | 0.266 |
| Social/Finance | 196 | 0.357 | 0.041 [0.015, 0.066] | 0.317 | 0.172 |
| Agriculture/Environment | 210 | 0.348 | 0.042 [0.019, 0.067] | 0.306 | 0.238 |
| Infrastructure/Transport | 342 | 0.322 | 0.029 [0.015, 0.047] | 0.293 | 0.224 |
| Defence | 131 | 0.298 | 0.039 [0.008, 0.076] | 0.259 | 0.079 (N2 null 0.219) |
| Security/Interior | 100 | 0.280 | 0.025 [0.000, 0.060] | 0.255 | 0.135 |
| Justice | 24 | 0.292 | 0.038 [0.000, 0.125] | 0.253 | 0.000 (N2 degenerate: one cell) |

Health accounts for 42.1% of the excess incumbent contracts. All sectors are significant under N1, and all except Justice are significant under N2.

### 4c. Buyer type (anonymous keyword classes)

| buyer type | eligible | observed | N1 null | excess N1 | N2 null | N3 null | ratio N3 |
|---|---|---|---|---|---|---|---|
| MoH hospital / dental centre | 617 | **0.831** | 0.177 | 0.654 | 0.181 | 0.386 | 2.16 |
| University hospital / medical faculty | 110 | 0.627 | 0.099 | 0.528 | 0.120 | 0.363 | 1.73 |
| MoH provincial directorate / hospital union | 695 | 0.563 | 0.098 | 0.464 | 0.113 | 0.391 | 1.44 |
| Other health body (central/agency) | 82 | 0.378 | 0.058 | 0.320 | 0.139 | 0.130 | 2.91 |
| Municipality / municipal company | 1,271 | 0.362 | 0.031 | 0.331 | 0.057 | 0.143 | 2.53 |
| University (non-health unit) | 401 | 0.362 | 0.025 | 0.336 | 0.113 | 0.164 | 2.21 |
| Central government / agency | 1,441 | 0.353 | 0.035 | 0.318 | 0.124 | 0.107 | 3.29 |
| Other | 296 | 0.351 | 0.031 | 0.321 | 0.086 | 0.183 | 1.92 |

### 4d. Procedure (each subgroup against its own null)

| procedure | contracts | eligible | observed | N1 null [95%] | excess N1 | ratio N1 | N2 null | N3 null |
|---|---|---|---|---|---|---|---|---|
| **21(b)** | 1,048 | 618 | **0.723** | 0.143 [0.120, 0.165] | 0.580 | 5.1 | 0.159 | 0.376 |
| open | 5,892 | 3,041 | 0.441 | 0.057 [0.051, 0.064] | 0.384 | 7.7 | 0.112 | 0.203 |
| other (mainly 21(f)) | 3,051 | 1,254 | 0.345 | 0.033 [0.024, 0.042] | 0.313 | 10.5 | 0.080 | 0.134 |
| of which 21(f) | 2,957 | 1,204 | 0.346 | 0.033 | 0.312 | 10.5 | 0.080 | – |
| 21(c) | 66 | 34 | 0.412 | 0.020 | 0.392 | – | 0.069 | – |

Contrast of 21(b) − open incumbency: observed 0.282, compared with a null difference of 0.086 [0.061, 0.110] under N1, p = 0.001. Under N2 the null difference is 0.047 [0.023, 0.073]. Under N3 it is 0.174 [0.146, 0.203], giving excess 0.108 and p = 0.001.

21(b) contracts therefore have a much higher incumbency rate than open contracts, even after accounting for the higher chance baseline in 21(b)'s markets.

A caution on reading this: open tenders still show large excess incumbency (0.44 vs 0.06 under N1). Most excess repeats occur under open procedures: 60.9% of excess incumbent contracts, against 18.7% under 21(b), because open procedures are far more numerous.

### 4e. Buyer size terciles (contract-weighted)

| tercile | eligible | observed | N1 null | excess | N2 null |
|---|---|---|---|---|---|
| T1 small (≤ 4 contracts) | 823 | 0.493 | 0.044 | 0.450 | 0.063 |
| T2 mid (5–13) | 1,829 | 0.500 | 0.076 | 0.425 | 0.110 |
| T3 large (> 13) | 2,261 | 0.398 | 0.057 | 0.342 | 0.126 |

Excess incumbency is somewhat lower for the largest buyers, but it is large in every tercile.

### 4f. Law 7144 (25 May 2018)

| period | eligible | observed | N1 null [95%] | excess | N2 null | N3 null |
|---|---|---|---|---|---|---|
| pre | 1,879 | 0.387 | 0.039 [0.031, 0.047] | 0.349 | 0.086 | 0.155 |
| post | 3,034 | 0.492 | 0.076 [0.068, 0.084] | 0.417 | 0.124 | 0.239 |

Contrasts from `null_contrasts.csv`:

| contrast | observed difference | N1 null difference [95%] | p N1 | N3 null difference | p N3 |
|---|---|---|---|---|---|
| post − pre (all) | 0.105 | 0.037 [0.026, 0.049] | 0.001 | 0.084 | 0.001 |
| post − pre (21(b)): 0.540 → 0.810 | 0.269 | 0.111 [0.064, 0.152] | 0.001 | 0.201 | 0.005 |
| post − pre (open): 0.385 → 0.476 | 0.091 | 0.033 [0.018, 0.047] | 0.001 | 0.086 | 0.325 |
| DiD (21(b) vs open) | 0.178 | 0.078 [0.030, 0.125] | 0.001 | 0.114 | 0.017 |

Incumbency rose after 25 May 2018, and it rose most among 21(b) contracts. After 2018, 81% of repeat-eligible 21(b) contracts went to an incumbent.

**Caveats.** This is a before/after comparison, not a causal design.
- Part of the rise is mechanical: later contracts have longer observed histories, because the data are left-censored at 2010. The permutation null absorbs this, and the null difference is positive for that reason.
- There is also a secular upward trend (Figure F-L2): the observed rate is about 0.35–0.41 in 2011–2017, 0.44 in 2018, and 0.45–0.56 in 2019–2025. No year shows a discrete break.
- Under the province null, the open-procedure rise disappears (p = 0.33). The 21(b) rise and the DiD remain (p = 0.005 and p = 0.017).

### 4g. By year (Figure F-L2)

Observed incumbency is 5 to 17 times its N1 null in every year with ≥ 20 eligible contracts (2011–2026). In every one of those years the observed rate lies far above the 97.5th null percentile. The yearly values are in `null_by_group.csv` (dimension `year`).

## 5. Buyer-level dependence (540 buyers with ≥ 5 contracts)

| measure | observed Q1 / median / Q3 | median of buyers' null means | buyers above their 95th null percentile |
|---|---|---|---|
| top-supplier share (N1) | 0.20 / 0.33 / 0.50 | 0.16 | **310 / 540 = 57.4%** |
| supplier HHI (N1) | 0.14 / 0.21 / 0.35 | 0.145 | **379 / 540 = 70.2%** |
| top-supplier share (N2) | same | 0.18 | 255 = 47.2% |
| supplier HHI (N2) | same | 0.15 | 328 = 60.7% |

- If buyers matched their null, about 5% would exceed the threshold. The discreteness of small-*n* buyers makes the test conservative.
- 139 buyers (25.7%) give ≥ 50% of their contracts to one firm, and 35 (6.5%) give all of them to one firm.
- Figure F-L3 shows the ECDF of observed vs null top-supplier shares.

By anonymous buyer type (N1, top-supplier share):

| buyer type | buyers | mean observed | mean null | exceeding the 95th null percentile (top share / HHI) |
|---|---|---|---|---|
| MoH hospital / dental centre | 57 | **0.81** (median 0.90) | 0.25 | **89.5% / 93.0%** |
| University hospital / medical faculty | 13 | 0.60 | 0.22 | 69.2% / 76.9% |
| Other health body | 8 | 0.41 | 0.14 | 62.5% / 75.0% |
| Other | 47 | 0.36 | 0.15 | 61.7% / 68.1% |
| Central government / agency | 142 | 0.28 | 0.13 | 54.9% / 71.1% |
| MoH provincial directorate / hospital union | 80 | 0.47 | 0.21 | 51.2% / 76.2% |
| University (non-health) | 67 | 0.31 | 0.15 | 50.7% / 62.7% |
| Municipality / municipal company | 126 | 0.27 | 0.13 | 50.0% / 58.7% |

- By size, the share of buyers exceeding the 95th null percentile rises with the number of contracts: 50.0% for 5–9 contracts, 63.2% for 10–19, and 80.3% for ≥ 20. This partly reflects greater statistical power.
- Individual MoH hospitals and oral/dental health centres are the most dependent buyer type. Many of these facilities source every IT contract in the sample from a single firm.

## 6. Sensitivities (incumbency; N1 cells unless stated)

| variant | contracts | eligible | observed | null mean [95%] | ratio | repeat-dyad share observed / null |
|---|---|---|---|---|---|---|
| main (N1) | 9,991 | 4,913 | 0.452 | 0.062 [0.056, 0.067] | 7.34 | 0.415 / 0.071 |
| S1 buyer = recorded `kurum` | 9,991 | – | 0.462 | 0.106 [0.100, 0.112] | 4.36 | 0.427 / 0.098 |
| S2 firm = original `firma` | 9,991 | – | 0.394 | 0.047 [0.042, 0.052] | 8.41 | 0.377 / 0.054 |
| S3 excluding MHRS/call-centre (`in_scope_core`) | 9,981 | – | 0.452 | 0.062 [0.056, 0.067] | 7.34 | 0.415 / 0.071 |
| S4 including gray (`in_scope_broad`) | 11,397 | – | 0.435 | 0.056 [0.051, 0.061] | 7.76 | 0.405 / 0.064 |
| S5 cells = sector × year (not market) | 9,991 | 4,913 | 0.452 | 0.047 [0.042, 0.052] | 9.69 | 0.415 / 0.093 |
| S6 incumbency at buyer level (any market) | 9,991 | – | 0.389 | 0.053 [0.049, 0.058] | 7.31 | 0.415 / 0.071 |
| S7 excluding 21(f) | 7,034 | – | 0.495 | 0.079 [0.071, 0.087] | 6.29 | 0.427 / 0.087 |
| S8 cells = market × year × province | 9,991 | 4,913 | 0.452 | 0.207 [0.201, 0.213] | 2.18 | 0.415 / 0.216 |

Sample sizes for each variant are in `lockin_log.json`. Every sensitivity has p = 0.001.

Notes on the sensitivities:
- S1: with recorded `kurum`, pooled generic MoH labels create artificially large dyads. The maximum dyad weight is 40, but that is not significant against its null (p = 0.068).
- S2: firm-name canonicalisation raises observed incumbency from 0.39 to 0.45. Unmerged name variants hide real repeats.

## 7. What holds and what does not

- **Holds.** Public IT buyers return to the same suppliers far more often than the market-period configuration null predicts.
  - Incumbency is 45% against a null of 6% (7.3×).
  - 41.5% of contracts sit in repeat dyads, against 7% under the null.
  - The result survives every buyer, firm, scope and cell definition tested.
  - It survives the strictest local-supplier null, market × year × province, at 2.2×.
- **Concentration.** Excess repeat contracting is concentrated in health: health information systems and MoH hospitals, dental centres and university hospitals. It is also high in maintenance/support services and in 21(b) negotiated procedures (72% incumbency; 81% after 2018).
- **Qualifications.**
  - Excess incumbency is **not** confined to 21(b) or to health. Every market, sector and procedure shows large excess under N1. Most excess repeats occur under open procedures.
  - Under the province null, the excess in health IS is much smaller (1.8×), because health-IS suppliers are regionally concentrated. The same holds for physical security and smart-city markets (about 1.3×).
  - The Law 7144 pattern is consistent with, but not proof of, a policy effect. There is a secular upward trend. The open-procedure increase disappears under the province null, while the 21(b)-specific increase survives (DiD p = 0.017).
- **Interpretation limits.**
  - The nulls condition on market, time, sector and province, but not on contract continuity. Some repeats are legitimate follow-on maintenance or licence renewals of an installed system, and that is itself the switching-cost mechanism of lock-in.
  - The data contain winners only, not bids. So "buyer returns to supplier" cannot be separated from "only the incumbent bids".
