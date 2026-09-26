# TenderNet v3 — Regression models (topic `models`)

Code: `src/models_common.py`, `models_features.py`, `models_analysis.py`, `models_figures.py`, `models_report.py`
(run in that order from `src`). Seed 42; no permutations or bootstraps are used (all inference is analytic, sandwich or delta method).
Sample: v3 main sample (`in_scope_main`, 9,991 contracts, 2,890 buyers = `kurum_il_split`, 2,814 firms = `firma_v3`, 14 product markets).
Real values are 2025 TRY (annual-average CPI; 2026 = mean of the eight linked 2026 monthly values available, Jan–Aug).
"Strictly earlier" means a strictly earlier tender date (`tarih_v3`), so same-day contracts never count as each other's history.

This design replaces the old dyad NB model, which had four problems: an offset running from the first contract to the end of the data, α fixed at 1, "depth" that was really firm degree, and suppression between collinear firm covariates.

## Bottom line (plain language)

1. **Is incumbency associated with 21(b)?** Yes, but only after 2018 and only in health IT.
   - Before 25 May 2018, a 21(b) contract was no more likely than an open tender to go to the buyer's previous supplier in that market (AME −3.8 pp, 95% CI −12.4 to +4.9).
   - After that date it was clearly more likely: +13.5 pp (7.2 to 19.9). The change between the two periods is +17.3 pp (7.2 to 27.5). The interaction OR is 2.42 (1.43 to 4.09), p < 0.001, with two-way clustered SEs.
   - The pattern holds in every sample and definition check:
     - IT only: OR 2.43
     - main + gray: OR 1.87
     - recorded `kurum` as the buyer: OR 2.00
     - original firm names: OR 1.76
     - linear trend instead of year FE: OR 2.22
     - dropping 2020: OR 2.15
   - **It disappears in two tests:**
     - **Without health buyers:** OR 0.86, p = 0.78. Outside health there are only 84 A-sample 21(b) contracts. Almost all 21(b) use in the A sample is hospital information systems (HBYS) bought by health-sector buyers. The health-only interaction is OR 2.64 (p < 0.001).
     - **Within a buyer:** the LPM with buyer FE gives a 21(b)×post coefficient of +7.3 pp (−3.7 to +18.2), p = 0.20. Much of the association therefore comes from differences between buyers, meaning which buyers use 21(b) after 2018, not from the same buyer switching. The LPM without buyer FE gives +11.9 pp (p = 0.009).
2. **Did Law 7144 change it?** The data cannot tell. The 21(b) incumbency premium rises around 2017–2018, but the break is not specific to 7144:
   - Dating the break at KHK 694 (25 Aug 2017, the dissolution of the Public Hospitals Authority) fits slightly better: log-likelihood −2801.1 vs −2802.5, interaction OR 2.55.
   - A placebo break at May 2016 is also significant (OR 2.10, p = 0.009).
   - A May 2020 break is weaker (OR 1.57, p = 0.083).
   - Within 2018, the post-7144 main effect is null (OR 1.08, p = 0.77). With a linear trend it is also null (OR 1.13, p = 0.41).
   - The 7144 text is about *works*, not IT (see law_notes).
   - The defensible statement: *from about 2017–18, 21(b) contracts in health IT went increasingly to incumbents, which coincides with the MoH reorganisation (KHK 694) and Law 7144. We cannot attribute this to 7144.*
3. **Firm size and specialization.**
   - At dyad formation, larger firms are more likely to win again from the same buyer in the same market. Size is measured as prior contracts with *other* buyers. In the size-only model: OR 1.23 per log unit, AME +3.9 pp per log unit.
   - More general firms are also more likely to win again. Generalism is measured as the number of prior distinct markets. In the generalism-only model: OR 1.47, AME +7.2 pp.
   - The two measures are highly collinear: r = 0.86 between size and generalism, and r = 0.99 between size and buyer breadth; VIFs are 63 and 61 in the full model. With both entered, neither is significant: size OR 1.13 (p = 0.20), generalism OR 1.20 (p = 0.29).
   - In the full model, buyer breadth turns *negative* (OR 0.69, p = 0.16 in the logit; NB2 IRR 0.76, p = 0.045). That is a collinearity artefact, not a substantive effect.
   - **Firm-level experience predicts continuation, but these data cannot separate size from generalism. We find no evidence that specialists (low generalism) are more locked in.**
   - Buyer experience at t0 lowers the chance that the dyad continues (OR 0.76 per log unit). The buyer's first contract in a market is the one most likely to be repeated.
4. **Procedure at dyad formation.** A dyad whose first contract was a 21(b) negotiated procedure is much more likely to recur:
   - logit OR 1.85 (1.37 to 2.50), AME +12.1 pp
   - NB2 IRR 1.61 (1.39 to 1.87)
   - Other negotiated procedures: OR 1.26 (p = 0.025)
5. **21(b) share by dyad status.** By count, 21(b) is 2.6 times as common among repeat contracts (20.1%) as among first contracts (7.7%). The difference is +12.4 pp:
   - buyer-clustered SE 1.6 pp; two-way (buyer, firm) SE 3.1 pp; p < 0.001
   - with year, market and sector FE: +4.8 pp (p < 0.001)
   - **within buyer: +1.2 pp (p = 0.16)**

   **By value there is no difference:** 6.3% vs 7.1% (7.9% without the single largest contract). The value-weighted difference is −0.8 pp (p = 0.61). Repeat 21(b) contracts are many but small.
6. **Single bidding** (bid-count sample, 393 main-sample tenders with bid data, 2012–2026; **no data for 2010–2011**, which hold 673 main-sample contracts):
   - Design-weighted single-bid rate: 44.2% (39.1 to 49.4); single *valid* bid: 55.8%.
   - By procedure: 21(b) 75.0% (59.8 to 85.8) vs open 40.8% (+34 pp, p < 0.001); 21(f) 40.0%, no different from open.
   - By incumbency: incumbent winners 71.2% (60.7 to 79.8) vs non-incumbent winners 32.4% (24.1 to 42.1), a difference of +38.7 pp (25.5 to 52.0). Adjusted for procedure and year, OR = 4.44 (2.39 to 8.25).
   - Trend: +5% odds per year (unweighted OR 1.050/yr, p = 0.042; design-weighted 1.044/yr, p = 0.11). Single valid bid: OR 1.06/yr, p = 0.013 and 0.035.
   - Only 50 21(b) tenders are in the sample, so the procedure-level CIs are wide.

## A. Contract-level incumbency model (primary)

**Unit:** every contract c of buyer k in product market m that has at least one contract of k in m on a strictly earlier date.
- N = 4,913 of 9,991. The other 5,078 are buyer-market first contracts, or ties on the first date.

**Outcome:** the winner had won from k in m before (strictly earlier). The mean is 0.452.

**Covariates:**
- procedure: 21(b); other negotiated = 21(a), (c), (d), (e), (f); reference = open plus 17 restricted
- log real value
- log number of distinct prior suppliers of k in m
- log number of prior contracts of k in m
- years since k's first contract in m
- post-7144 (date ≥ 2018-05-25) and 21(b)×post

**Fixed effects:** product market, year (2010 pooled into 2011 because 2010 has only one A-observation), buyer sector.

**Estimation:** logit with Cameron–Gelbach–Miller two-way clustered SEs by buyer (1,126) and winning firm (1,437); V = V_buyer + V_firm − V_buyer∩firm. No eigenvalue clipping was needed in the main model. AMEs use the delta method with the two-way V; 21(b) AMEs are computed separately for pre- and post-7144 observations.

**History terms:**
- More prior contracts raise the incumbent-win probability (OR 4.36 per log unit). This is partly mechanical: there are more chances that the winner has won before.
- More distinct prior suppliers lower it (OR 0.40). A buyer that has rotated suppliers keeps rotating.
- Each additional year since the buyer's first contract lowers it by 2.4 pp. Old relationships decay.
- The two log counts correlate at r = 0.78 (VIF about 3), which is acceptable.

**Identification caveat:** with year FE, the post-7144 main effect is identified only by the difference between Jan–May 2018 and Jun–Dec 2018. Model A2 (linear trend) gives the across-year version. The interaction is identified across all years.

**Within-buyer LPM (A3):**
- The history effects change sign or size: prior suppliers +0.26, prior contracts +0.04 (n.s.). Within a buyer, both counts grow with time, so this is expected (Nickell-type dynamics). The buyer-FE LPM is therefore only a check on 21(b)×post.
- 21(b)×post = +7.3 pp, not significant.

## B. Dyad continuation model (secondary)

**Unit:** dyad (f, k, m) at its first contract (t0). There are 7,761 dyads in total.
- 4,334 dyads (55.8%) have **no** later contract by buyer k in market m, so they had no opportunity to continue. They are excluded, since they are uninformative about continuation. The old model's offset (time to end of data) treated them as zero-exposure-adjusted zeros.
- Estimation N = 3,427. 34.6% have at least one later contract. Later contracts: mean 0.65, variance 1.82, max 13.

**Exposure:** opportunities = number of contracts by k in m strictly after t0, entered as log(opportunities).
- The offset restriction (coefficient = 1) is rejected: PPML 0.902 (SE 0.042), p = 0.020; NB2 0.884 (SE 0.042), p = 0.006.
- So log(opportunities) is kept as a free covariate. An offset would overstate the dependence on opportunities.

**Covariates (all strictly before t0, no look-ahead):**
- first-contract procedure
- log real value of the first contract
- **firm size** = log(1 + prior contracts with buyers other than k, all markets)
- **firm generalism** = log(1 + number of distinct markets the firm had won in)
- **firm buyer breadth** = log(1 + distinct prior buyers other than k)
- **buyer experience** = log(1 + buyer's prior contracts, all markets)
- FE: product market and first-contract year (2025–26 pooled into 2024)

**Estimation and dispersion:**
- Two-way clustered SEs by firm (1,475) and buyer (1,126).
- Overdispersion is present: NB2 α = 0.459 (SE 0.115); LR(α = 0) = 152.5, p ≈ 2e−35; Cameron–Trivedi t = 7.94. It is moderate, with Pearson dispersion 1.28. PPML and NB2 point estimates agree closely.
- Specs: the full model, then size + generalism (drops buyer breadth, which is collinear with size at r = 0.99), generalism only, and size only. The "suppression" in the old model came from entering collinear firm measures together, as the full spec shows (buyer breadth flips negative). It is not a real opposite-sign effect.

## C. Procedure facts
- **Definitions:** a contract is **repeat** if its winner had won from the same buyer in the same product market on a strictly earlier date (the same definition as A); otherwise it is **first**.
- **Inference:** a count-share difference from an LPM of is21b on repeat, clustered by buyer, by dyad and two-way. The naive χ² (280.8, p ≈ 5e−63) is shown only for contrast; it overstates precision about twofold relative to two-way clustering.
- **Value measure:** real 2025 TRY. The largest contract (MHRS call centre, IKN 2025/1250982, 7.54 bn 2025 TRY) is an *open* first contract; results are shown with and without it.
- **Over time:** the repeat-contract 21(b) share rose from 14.7% before 7144 to 22.8% after, while the first-contract share was flat (8.1% → 7.3%).

## D. Single bidding
- **Source:** `data/bid_counts_sample.csv` (released copy of the bid-count sample). It holds 680 tenders drawn 40 per year (seed 42) from all completed EKAP results in cp1, including non-IT.
- **Join:** 414 are in the v3 main sample; 393 of them have bid counts.
- **Weighting:** tenders are drawn at random within year, so the main-sample subsample is random within year. The design weight is (main contracts in year) / (sampled main tenders with bid data in year), ranging from 3.0 (2026) to 43.1 (2012).
- **Years with no bid data:** 2010 (3 drawn, 0 with data) and 2011 (18 drawn, 0 with data), which hold 673 of the 9,991 contracts. **Estimates cover 2012–2026 only.**
- **Standard errors:** stratified (by year) linearization, with replacement and no FPC, so they are slightly conservative. CIs are formed on the logit scale.
- **Outcomes:**
  - single = total bids (`toplam_teklif`) = 1
  - single valid = valid bids (`gecerli_teklif`) = 1
- **Incumbency** uses A's definition; 185 sampled tenders are buyer-first-in-market, where incumbency is undefined.
- **Downloaders (`indiren_sayisi`):**
  - 85 tenders report 0 downloaders, all from 2012–2019, and all of them have ≥1 bid. So 0 means *not recorded*, and these tenders are excluded from the gap analysis, which uses 308 tenders.
  - On average 4.0 firms downloaded the documents vs 1.9 valid bids, a gap of 2.1 (1.8 to 2.4).
  - The gap is larger in open tenders (2.6) than negotiated ones (0.9).
  - 44.6% of tenders had ≥2 downloaders but only one valid bid (52.4% of open tenders).

## E. Figures
- `figures/F-R1_models_AME.png/.pdf` (7 in wide):
  - (a) Model A AMEs, with 21(b) split pre/post-7144.
  - (b) Model B logit AMEs for the full, size + generalism and generalism-only specs.
  - 95% CIs from two-way clustered V.
- `figures/F-R2_single_bid.png/.pdf` (7 in): design-weighted single-bid and single-valid-bid rates, by procedure (open / 21(b) / 21(f)) and by winner incumbency status, with 95% CIs and n.

## Machine-readable outputs (`results/models/`)
- **Model A:**
  - A1_logit_incumbency.csv
  - A_robustness.csv
  - A5_lpm_buyerFE.csv
  - A5b_lpm_noBuyerFE.csv
- **Model B:** B_{logit,ppml,nb2}_{full,size_generalism,generalism_only,size_only}.csv
- **Marginal effects (A and B):** AME_A_B.csv
- **21(b) shares:**
  - C_21b_share_by_status.csv
  - C_21b_share_by_status_period.csv
  - C_21b_share_by_year.csv
  - C_inference.csv
- **Single bidding:**
  - D_sample_coverage_by_year.csv
  - D_single_bid_rates.csv
  - D_single_bid_differences.csv
  - D_trend_test.csv
  - D_downloader_gap.csv
  - D_single_bid_by_year.csv
  - D_bid_sample_joined.csv
- **Analysis data:**
  - contracts_with_history.csv (per contract history features)
  - dyads_t0.csv (dyad table, uses `firm_id`)
- **Run log:** models_run_log.txt

## Full regression tables
### Table A1. Incumbent win, logit (contract level)

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | -0.1861 | 0.2217 | 0.830 [0.538, 1.282] | 0.401 |
| Other negotiated 21(a,c,d,e,f) (vs open) | -0.1372 | 0.1121 | 0.872 [0.700, 1.086] | 0.221 |
| post-Law 7144 (date >= 2018-05-25) | 0.0788 | 0.2726 | 1.082 [0.634, 1.846] | 0.773 |
| 21(b) x post-7144 | 0.8837*** | 0.2675 | 2.420 [1.432, 4.088] | <0.001 |
| log real value (2025 TRY) | -0.0273 | 0.0363 | 0.973 [0.906, 1.045] | 0.451 |
| log # distinct prior suppliers of buyer in market | -0.9102*** | 0.1486 | 0.402 [0.301, 0.538] | <0.001 |
| log # prior contracts of buyer in market | 1.4724*** | 0.1170 | 4.359 [3.466, 5.484] | <0.001 |
| years since buyer's first contract in market | -0.1215*** | 0.0178 | 0.886 [0.855, 0.917] | <0.001 |
| constant | -0.6951 | 0.8035 | 0.499 [0.103, 2.410] | 0.387 |
| Fixed effects | product market (13), year (2011–2026; 2010 pooled into 2011), buyer sector (10) | | | |
| N contracts | 4,913 | | | |
| Mean of outcome | 0.452 | | | |
| Clusters | buyer 1,126; winner 1,437; intersection 3,129 (CGM two-way) | | | |
| McFadden pseudo-R² | 0.1716 | | | |
| Log-likelihood | -2802.54 | | | |

SE: two-way clustered (buyer, winning firm), Cameron–Gelbach–Miller, small-sample factor G/(G−1)·(N−1)/(N−K). *** p<0.001, ** p<0.01, * p<0.05.

### Table A1-AME. Average marginal effects (delta method, two-way clustered V)

| model | Variable | subset | AME (pp) | SE (pp) | 95% CI (pp) | p |
|---|---|---|---:|---:|---:|---:|
| A1 | 21(b) negotiated (vs open) | all | 6.91 | 2.76 | [1.51, 12.32] | 0.012 |
| A1 | Other negotiated 21(a,c,d,e,f) (vs open) | all | -2.71 | 2.20 | [-7.02, 1.61] | 0.219 |
| A1 | post-Law 7144 (date >= 2018-05-25) | all | 3.37 | 5.32 | [-7.05, 13.80] | 0.526 |
| A1 | log real value (2025 TRY) | all | -0.53 | 0.70 | [-1.91, 0.84] | 0.449 |
| A1 | log # distinct prior suppliers of buyer in market | all | -17.68 | 2.74 | [-23.05, -12.31] | <0.001 |
| A1 | log # prior contracts of buyer in market | all | 28.60 | 1.99 | [24.70, 32.50] | <0.001 |
| A1 | years since buyer's first contract in market | all | -2.36 | 0.34 | [-3.03, -1.69] | <0.001 |
| A1 | 21(b) negotiated (vs open) | pre-7144 | -3.77 | 4.42 | [-12.44, 4.89] | 0.394 |
| A1 | 21(b) negotiated (vs open) | post-7144 | 13.53 | 3.24 | [7.19, 19.88] | <0.001 |
| A1 | 21(b) negotiated (vs open) | post minus pre | 17.30 | 5.18 | [7.15, 27.45] | <0.001 |

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
| A1_main | 4,913 | 1,126 | 1,437 | 0.172 | 0.83 [0.401] | 1.08 [0.773] | 2.42 [<0.001] | 0.40 [<0.001] | 4.36 [<0.001] |
| A2_trend_noYearFE | 4,913 | 1,126 | 1,437 | 0.167 | 0.85 [0.456] | 1.13 [0.407] | 2.22 [0.003] | 0.41 [<0.001] | 4.32 [<0.001] |
| A3_21f_separate | 4,913 | 1,126 | 1,437 | 0.172 | 0.84 [0.436] | 1.11 [0.703] | 2.38 [0.001] | 0.40 [<0.001] | 4.36 [<0.001] |
| A4_no_history_counts | 4,913 | 1,126 | 1,437 | 0.110 | 0.85 [0.473] | 1.14 [0.623] | 2.90 [<0.001] | — | — |
| R_excl_health_buyers | 3,411 | 637 | 1,249 | 0.116 | 0.55 [0.178] | 1.13 [0.674] | 0.86 [0.781] | 0.40 [<0.001] | 4.93 [<0.001] |
| R_health_buyers_only | 1,502 | 489 | 243 | 0.196 | 1.15 [0.591] | 0.76 [0.669] | 2.64 [<0.001] | 0.45 [0.008] | 2.70 [<0.001] |
| R_break_KHK694_2017-08-25 | 4,913 | 1,126 | 1,437 | 0.172 | 0.78 [0.263] | 1.29 [0.241] | 2.55 [<0.001] | 0.40 [<0.001] | 4.37 [<0.001] |
| R_placebo_break_2016-05-25 | 4,913 | 1,126 | 1,437 | 0.171 | 0.81 [0.421] | 1.04 [0.881] | 2.10 [0.009] | 0.40 [<0.001] | 4.39 [<0.001] |
| R_placebo_break_2020-05-25 | 4,913 | 1,126 | 1,437 | 0.170 | 1.14 [0.403] | 1.35 [0.226] | 1.57 [0.083] | 0.40 [<0.001] | 4.39 [<0.001] |
| R_excl_2020 | 4,503 | 1,110 | 1,373 | 0.160 | 0.87 [0.517] | 1.11 [0.698] | 2.15 [0.004] | 0.40 [<0.001] | 4.21 [<0.001] |
| R_it_only | 4,908 | 1,125 | 1,436 | 0.172 | 0.83 [0.394] | 1.08 [0.774] | 2.43 [<0.001] | 0.40 [<0.001] | 4.37 [<0.001] |
| R_broad | 5,623 | 1,298 | 1,769 | 0.161 | 1.10 [0.610] | 1.01 [0.962] | 1.87 [0.012] | 0.38 [<0.001] | 4.39 [<0.001] |
| R_buyer_kurum | 5,147 | 1,046 | 1,483 | 0.193 | 0.90 [0.626] | 1.28 [0.282] | 2.00 [0.006] | 0.32 [<0.001] | 4.28 [<0.001] |
| R_firm_original | 4,913 | 1,126 | 1,604 | 0.148 | 1.11 [0.609] | 1.05 [0.865] | 1.76 [0.026] | 0.57 [<0.001] | 3.62 [<0.001] |

A2 = linear time trend instead of year FE (post-7144 main effect then identified across years); A3 = 21(f) separated from other negotiated (A3's 21(f) OR 0.90, p=0.51; 21(f)×post in table CSV); A4 = drops prior-supplier/prior-contract counts; R_* = sample/definition sensitivity; R_break_* = alternative break dates (KHK 694 date 2017-08-25; placebos 2016-05-25 and 2020-05-25). Log-likelihoods (same N=4,913): A1 −2802.54; KHK-694 break −2801.10; placebo 2016 −2806.05; placebo 2020 −2807.77.

### Table A3. Linear probability model with buyer fixed effects (within-buyer)

| Variable | Coef. | SE | 95% CI | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.0131 | 0.0520 | [-0.0888, 0.1149] | 0.801 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.0089 | 0.0256 | [-0.0413, 0.0592] | 0.728 |
| post-Law 7144 (date >= 2018-05-25) | 0.0144 | 0.0503 | [-0.0842, 0.1130] | 0.775 |
| 21(b) x post-7144 | 0.0725 | 0.0560 | [-0.0373, 0.1824] | 0.196 |
| log real value (2025 TRY) | 0.0142 | 0.0080 | [-0.0014, 0.0298] | 0.075 |
| log # distinct prior suppliers of buyer in market | 0.2569*** | 0.0389 | [0.1807, 0.3332] | <0.001 |
| log # prior contracts of buyer in market | 0.0400 | 0.0284 | [-0.0156, 0.0957] | 0.159 |
| years since buyer's first contract in market | -0.0377*** | 0.0067 | [-0.0508, -0.0247] | <0.001 |

FE: buyer (absorbed; 1,126 buyers; sector FE collinear with buyer FE), product market, year. N=4,913; within-R²=0.1016; two-way clustered SE (buyer 1,126, winner 1,437). 450 contracts of buyers with a single A-observation contribute no within variation.

Same LPM without buyer FE (sector FE instead), for comparison:

| Variable | Coef. | SE | 95% CI | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | -0.0250 | 0.0454 | [-0.1140, 0.0640] | 0.582 |
| Other negotiated 21(a,c,d,e,f) (vs open) | -0.0271 | 0.0231 | [-0.0724, 0.0181] | 0.240 |
| post-Law 7144 (date >= 2018-05-25) | 0.0295 | 0.0547 | [-0.0776, 0.1367] | 0.589 |
| 21(b) x post-7144 | 0.1188** | 0.0454 | [0.0299, 0.2078] | 0.009 |
| log real value (2025 TRY) | -0.0036 | 0.0074 | [-0.0181, 0.0109] | 0.627 |
| log # distinct prior suppliers of buyer in market | -0.1547*** | 0.0255 | [-0.2047, -0.1046] | <0.001 |
| log # prior contracts of buyer in market | 0.2699*** | 0.0212 | [0.2282, 0.3115] | <0.001 |
| years since buyer's first contract in market | -0.0231*** | 0.0034 | [-0.0297, -0.0165] | <0.001 |
| constant | 0.3075 | 0.1663 | [-0.0184, 0.6333] | 0.064 |

### Table B-logit-full. Logit: any later contract (binary) — spec `full`

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.6141*** | 0.1533 | 1.848 [1.368, 2.495] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.2292* | 0.1021 | 1.258 [1.029, 1.536] | 0.025 |
| log real value (2025 TRY) | 0.0219 | 0.0368 | 1.022 [0.951, 1.098] | 0.552 |
| firm size: log(1+ prior contracts, other buyers) | 0.4577 | 0.2502 | 1.580 [0.968, 2.581] | 0.067 |
| firm generalism: log(1+ prior distinct markets) | 0.1799 | 0.1678 | 1.197 [0.861, 1.663] | 0.284 |
| firm buyer breadth: log(1+ prior distinct buyers, other buyers) | -0.3751 | 0.2642 | 0.687 [0.409, 1.153] | 0.156 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2688*** | 0.0513 | 0.764 [0.691, 0.845] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.6373*** | 0.0603 | 1.891 [1.681, 2.129] | <0.001 |
| constant | -2.1557** | 0.6974 | 0.116 [0.030, 0.454] | 0.002 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1358 | | | |
| Log-likelihood | -1909.15 | | | |

### Table B-logit-size_generalism. Logit: any later contract (binary) — spec `size_generalism`

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.6263*** | 0.1528 | 1.871 [1.387, 2.524] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.2320* | 0.1017 | 1.261 [1.033, 1.539] | 0.023 |
| log real value (2025 TRY) | 0.0224 | 0.0368 | 1.023 [0.951, 1.099] | 0.544 |
| firm size: log(1+ prior contracts, other buyers) | 0.1218 | 0.0953 | 1.129 [0.937, 1.361] | 0.201 |
| firm generalism: log(1+ prior distinct markets) | 0.1810 | 0.1723 | 1.198 [0.855, 1.680] | 0.293 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2706*** | 0.0510 | 0.763 [0.690, 0.843] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.6434*** | 0.0603 | 1.903 [1.691, 2.142] | <0.001 |
| constant | -2.1684** | 0.6980 | 0.114 [0.029, 0.449] | 0.002 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1352 | | | |
| Log-likelihood | -1910.47 | | | |

### Table B-logit-generalism_only. Logit: any later contract (binary) — spec `generalism_only`

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.6306*** | 0.1544 | 1.879 [1.388, 2.543] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.2282* | 0.1019 | 1.256 [1.029, 1.534] | 0.025 |
| log real value (2025 TRY) | 0.0227 | 0.0370 | 1.023 [0.951, 1.100] | 0.541 |
| firm generalism: log(1+ prior distinct markets) | 0.3826*** | 0.0673 | 1.466 [1.285, 1.673] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2845*** | 0.0498 | 0.752 [0.682, 0.830] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.6464*** | 0.0601 | 1.909 [1.697, 2.147] | <0.001 |
| constant | -2.2176** | 0.6940 | 0.109 [0.028, 0.424] | 0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1344 | | | |
| Log-likelihood | -1912.21 | | | |

### Table B-logit-size_only. Logit: any later contract (binary) — spec `size_only`

| Variable | Coef. | SE | OR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.6184*** | 0.1524 | 1.856 [1.377, 2.502] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.2258* | 0.1018 | 1.253 [1.027, 1.530] | 0.027 |
| log real value (2025 TRY) | 0.0244 | 0.0370 | 1.025 [0.953, 1.102] | 0.509 |
| firm size: log(1+ prior contracts, other buyers) | 0.2056*** | 0.0379 | 1.228 [1.140, 1.323] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2623*** | 0.0492 | 0.769 [0.699, 0.847] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.6405*** | 0.0592 | 1.898 [1.690, 2.131] | <0.001 |
| constant | -2.1658** | 0.6960 | 0.115 [0.029, 0.449] | 0.002 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1347 | | | |
| Log-likelihood | -1911.54 | | | |

### Table B-ppml-full. Poisson PML: number of later contracts — spec `full`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4887*** | 0.0735 | 1.630 [1.411, 1.883] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1845* | 0.0788 | 1.203 [1.031, 1.403] | 0.019 |
| log real value (2025 TRY) | 0.0051 | 0.0221 | 1.005 [0.963, 1.050] | 0.817 |
| firm size: log(1+ prior contracts, other buyers) | 0.2872* | 0.1220 | 1.333 [1.049, 1.693] | 0.019 |
| firm generalism: log(1+ prior distinct markets) | 0.1649 | 0.1051 | 1.179 [0.960, 1.449] | 0.117 |
| firm buyer breadth: log(1+ prior distinct buyers, other buyers) | -0.2261 | 0.1284 | 0.798 [0.620, 1.026] | 0.078 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2830*** | 0.0345 | 0.754 [0.704, 0.806] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.9020*** | 0.0420 | 2.465 [2.270, 2.676] | <0.001 |
| constant | -1.7935*** | 0.4848 | 0.166 [0.064, 0.430] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.2579 | | | |
| Log-likelihood | -3253.09 | | | |

### Table B-ppml-size_generalism. Poisson PML: number of later contracts — spec `size_generalism`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4969*** | 0.0739 | 1.644 [1.422, 1.900] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1865* | 0.0790 | 1.205 [1.032, 1.407] | 0.018 |
| log real value (2025 TRY) | 0.0054 | 0.0221 | 1.005 [0.963, 1.050] | 0.807 |
| firm size: log(1+ prior contracts, other buyers) | 0.0872 | 0.0581 | 1.091 [0.974, 1.223] | 0.133 |
| firm generalism: log(1+ prior distinct markets) | 0.1594 | 0.1087 | 1.173 [0.948, 1.451] | 0.142 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2852*** | 0.0344 | 0.752 [0.703, 0.804] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.9084*** | 0.0422 | 2.480 [2.284, 2.694] | <0.001 |
| constant | -1.8084*** | 0.4864 | 0.164 [0.063, 0.425] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.2575 | | | |
| Log-likelihood | -3254.99 | | | |

### Table B-ppml-generalism_only. Poisson PML: number of later contracts — spec `generalism_only`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.5080*** | 0.0820 | 1.662 [1.415, 1.952] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1814* | 0.0791 | 1.199 [1.027, 1.400] | 0.022 |
| log real value (2025 TRY) | 0.0061 | 0.0222 | 1.006 [0.963, 1.051] | 0.784 |
| firm generalism: log(1+ prior distinct markets) | 0.2970*** | 0.0506 | 1.346 [1.219, 1.486] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2978*** | 0.0341 | 0.742 [0.695, 0.794] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.9121*** | 0.0423 | 2.490 [2.291, 2.705] | <0.001 |
| constant | -1.8555*** | 0.4852 | 0.156 [0.060, 0.405] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.2566 | | | |
| Log-likelihood | -3258.55 | | | |

### Table B-ppml-size_only. Poisson PML: number of later contracts — spec `size_only`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4828*** | 0.0709 | 1.621 [1.410, 1.862] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1813* | 0.0792 | 1.199 [1.026, 1.400] | 0.022 |
| log real value (2025 TRY) | 0.0074 | 0.0221 | 1.007 [0.965, 1.052] | 0.738 |
| firm size: log(1+ prior contracts, other buyers) | 0.1587*** | 0.0271 | 1.172 [1.111, 1.236] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2777*** | 0.0337 | 0.758 [0.709, 0.809] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.9069*** | 0.0421 | 2.477 [2.280, 2.690] | <0.001 |
| constant | -1.8079*** | 0.4890 | 0.164 [0.063, 0.428] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.2567 | | | |
| Log-likelihood | -3258.40 | | | |

### Table B-nb2-full. NB2 (α estimated): number of later contracts — spec `full`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4758*** | 0.0755 | 1.609 [1.388, 1.866] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1739* | 0.0796 | 1.190 [1.018, 1.391] | 0.029 |
| log real value (2025 TRY) | 0.0092 | 0.0231 | 1.009 [0.965, 1.056] | 0.691 |
| firm size: log(1+ prior contracts, other buyers) | 0.3096* | 0.1236 | 1.363 [1.070, 1.736] | 0.012 |
| firm generalism: log(1+ prior distinct markets) | 0.1789 | 0.1000 | 1.196 [0.983, 1.455] | 0.074 |
| firm buyer breadth: log(1+ prior distinct buyers, other buyers) | -0.2704* | 0.1347 | 0.763 [0.586, 0.994] | 0.045 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2641*** | 0.0356 | 0.768 [0.716, 0.823] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.8838*** | 0.0422 | 2.420 [2.228, 2.629] | <0.001 |
| alpha | 0.4592*** | 0.1154 | 1.583 [1.262, 1.984] | <0.001 |
| constant | -1.8852*** | 0.4785 | 0.152 [0.059, 0.388] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1457 | | | |
| Log-likelihood | -3176.85 | | | |

### Table B-nb2-size_generalism. NB2 (α estimated): number of later contracts — spec `size_generalism`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4850*** | 0.0756 | 1.624 [1.400, 1.884] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1758* | 0.0794 | 1.192 [1.020, 1.393] | 0.027 |
| log real value (2025 TRY) | 0.0095 | 0.0232 | 1.010 [0.965, 1.057] | 0.681 |
| firm size: log(1+ prior contracts, other buyers) | 0.0703 | 0.0563 | 1.073 [0.961, 1.198] | 0.212 |
| firm generalism: log(1+ prior distinct markets) | 0.1745 | 0.1035 | 1.191 [0.972, 1.458] | 0.092 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2652*** | 0.0354 | 0.767 [0.716, 0.822] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.8898*** | 0.0421 | 2.435 [2.242, 2.644] | <0.001 |
| alpha | 0.4619*** | 0.1165 | 1.587 [1.263, 1.994] | <0.001 |
| constant | -1.8962*** | 0.4799 | 0.150 [0.059, 0.385] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1453 | | | |
| Log-likelihood | -3178.48 | | | |

### Table B-nb2-generalism_only. NB2 (α estimated): number of later contracts — spec `generalism_only`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4910*** | 0.0799 | 1.634 [1.397, 1.911] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1702* | 0.0793 | 1.186 [1.015, 1.385] | 0.032 |
| log real value (2025 TRY) | 0.0097 | 0.0233 | 1.010 [0.965, 1.057] | 0.679 |
| firm generalism: log(1+ prior distinct markets) | 0.2873*** | 0.0482 | 1.333 [1.213, 1.465] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2749*** | 0.0352 | 0.760 [0.709, 0.814] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.8930*** | 0.0421 | 2.442 [2.249, 2.652] | <0.001 |
| alpha | 0.4677*** | 0.1161 | 1.596 [1.271, 2.004] | <0.001 |
| constant | -1.9335*** | 0.4773 | 0.145 [0.057, 0.369] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1449 | | | |
| Log-likelihood | -3179.92 | | | |

### Table B-nb2-size_only. NB2 (α estimated): number of later contracts — spec `size_only`

| Variable | Coef. | SE | IRR [95% CI] | p |
|---|---:|---:|---:|---:|
| 21(b) negotiated (vs open) | 0.4739*** | 0.0729 | 1.606 [1.392, 1.853] | <0.001 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 0.1721* | 0.0796 | 1.188 [1.016, 1.388] | 0.031 |
| log real value (2025 TRY) | 0.0122 | 0.0232 | 1.012 [0.967, 1.059] | 0.599 |
| firm size: log(1+ prior contracts, other buyers) | 0.1488*** | 0.0264 | 1.160 [1.102, 1.222] | <0.001 |
| buyer experience: log(1+ buyer's prior contracts, all markets) | -0.2561*** | 0.0346 | 0.774 [0.723, 0.828] | <0.001 |
| log # later buyer-market contracts (opportunities) | 0.8875*** | 0.0416 | 2.429 [2.239, 2.635] | <0.001 |
| alpha | 0.4655*** | 0.1163 | 1.593 [1.268, 2.001] | <0.001 |
| constant | -1.8939*** | 0.4800 | 0.150 [0.059, 0.386] | <0.001 |
| Fixed effects | product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024) | | | |
| N dyads | 3,427 | | | |
| Clusters | firm 1,475; buyer 1,126; intersection 3,192 | | | |
| McFadden pseudo-R² | 0.1446 | | | |
| Log-likelihood | -3180.97 | | | |

For NB2, the row `alpha` is α itself (Var = μ + αμ²); its 'IRR' column is meaningless and can be ignored.

### Table B-AME. Logit AMEs (percentage points)

| model | Variable | subset | AME (pp) | SE (pp) | 95% CI (pp) | p |
|---|---|---|---:|---:|---:|---:|
| B_logit_full | 21(b) negotiated (vs open) | all | 12.13 | 3.18 | [5.91, 18.36] | <0.001 |
| B_logit_full | Other negotiated 21(a,c,d,e,f) (vs open) | all | 4.35 | 1.94 | [0.54, 8.16] | 0.025 |
| B_logit_full | log real value (2025 TRY) | all | 0.41 | 0.69 | [-0.94, 1.76] | 0.552 |
| B_logit_full | firm size: log(1+ prior contracts, other buyers) | all | 8.58 | 4.67 | [-0.56, 17.73] | 0.066 |
| B_logit_full | firm generalism: log(1+ prior distinct markets) | all | 3.37 | 3.14 | [-2.78, 9.53] | 0.283 |
| B_logit_full | firm buyer breadth: log(1+ prior distinct buyers, other buyers) | all | -7.04 | 4.93 | [-16.69, 2.62] | 0.153 |
| B_logit_full | buyer experience: log(1+ buyer's prior contracts, all markets) | all | -5.04 | 0.94 | [-6.89, -3.20] | <0.001 |
| B_logit_full | log # later buyer-market contracts (opportunities) | all | 11.95 | 1.09 | [9.82, 14.09] | <0.001 |
| B_logit_size_generalism | 21(b) negotiated (vs open) | all | 12.39 | 3.17 | [6.18, 18.61] | <0.001 |
| B_logit_size_generalism | Other negotiated 21(a,c,d,e,f) (vs open) | all | 4.40 | 1.94 | [0.60, 8.20] | 0.023 |
| B_logit_size_generalism | log real value (2025 TRY) | all | 0.42 | 0.69 | [-0.94, 1.78] | 0.544 |
| B_logit_size_generalism | firm size: log(1+ prior contracts, other buyers) | all | 2.29 | 1.79 | [-1.23, 5.80] | 0.202 |
| B_logit_size_generalism | firm generalism: log(1+ prior distinct markets) | all | 3.40 | 3.23 | [-2.93, 9.72] | 0.292 |
| B_logit_size_generalism | buyer experience: log(1+ buyer's prior contracts, all markets) | all | -5.08 | 0.94 | [-6.92, -3.24] | <0.001 |
| B_logit_size_generalism | log # later buyer-market contracts (opportunities) | all | 12.08 | 1.09 | [9.95, 14.21] | <0.001 |
| B_logit_generalism_only | 21(b) negotiated (vs open) | all | 12.50 | 3.21 | [6.22, 18.79] | <0.001 |
| B_logit_generalism_only | Other negotiated 21(a,c,d,e,f) (vs open) | all | 4.34 | 1.94 | [0.53, 8.15] | 0.026 |
| B_logit_generalism_only | log real value (2025 TRY) | all | 0.43 | 0.70 | [-0.94, 1.79] | 0.541 |
| B_logit_generalism_only | firm generalism: log(1+ prior distinct markets) | all | 7.19 | 1.25 | [4.74, 9.64] | <0.001 |
| B_logit_generalism_only | buyer experience: log(1+ buyer's prior contracts, all markets) | all | -5.35 | 0.91 | [-7.14, -3.56] | <0.001 |
| B_logit_generalism_only | log # later buyer-market contracts (opportunities) | all | 12.15 | 1.08 | [10.03, 14.27] | <0.001 |
| B_logit_size_only | 21(b) negotiated (vs open) | all | 12.25 | 3.17 | [6.04, 18.45] | <0.001 |
| B_logit_size_only | Other negotiated 21(a,c,d,e,f) (vs open) | all | 4.29 | 1.94 | [0.48, 8.09] | 0.027 |
| B_logit_size_only | log real value (2025 TRY) | all | 0.46 | 0.70 | [-0.90, 1.82] | 0.509 |
| B_logit_size_only | firm size: log(1+ prior contracts, other buyers) | all | 3.86 | 0.71 | [2.47, 5.25] | <0.001 |
| B_logit_size_only | buyer experience: log(1+ buyer's prior contracts, all markets) | all | -4.93 | 0.91 | [-6.70, -3.15] | <0.001 |
| B_logit_size_only | log # later buyer-market contracts (opportunities) | all | 12.03 | 1.07 | [9.93, 14.13] | <0.001 |

(model column: rows are in order full, size_generalism, generalism_only, size_only; see AME_A_B.csv.)

### Table B-VIF and correlations (estimation sample)

| Variable | VIF |
|---|---:|
| 21(b) negotiated (vs open) | 1.16 |
| Other negotiated 21(a,c,d,e,f) (vs open) | 1.18 |
| log real value (2025 TRY) | 1.14 |
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
- LR test α=0 (boundary, p halved): LR = 152.49, p = 2.5e-35.
- Cameron–Trivedi auxiliary regression (NB2 form): α̂ = 0.276, t = 7.94, p = 2.8e-15.
- Pearson dispersion of PPML = 1.276.
- Offset restriction (ppml): coefficient on log(opportunities) = 0.902 (SE 0.042); H0 = 1: z = -2.33, p = 0.020.
- Offset restriction (nb2): coefficient on log(opportunities) = 0.884 (SE 0.042); H0 = 1: z = -2.75, p = 0.006.

### Table C. Share of 21(b) by dyad status

| scope | status | n | n 21(b) | share 21(b), count | value (bn 2025 TRY) | 21(b) value (bn) | share 21(b), value |
|---|---|---:|---:|---:|---:|---:|---:|
| all contracts | first | 7,769 | 601 | 0.077 | 69.89 | 4.95 | 0.071 |
| all contracts | repeat | 2,222 | 447 | 0.201 | 19.37 | 1.22 | 0.063 |
| buyer has prior history in market (A sample) | first | 2,691 | 171 | 0.064 | 27.12 | 2.69 | 0.099 |
| buyer has prior history in market (A sample) | repeat | 2,222 | 447 | 0.201 | 19.37 | 1.22 | 0.063 |
| all, excl. largest contract | first | 7,768 | 601 | 0.077 | 62.35 | 4.95 | 0.079 |
| all, excl. largest contract | repeat | 2,222 | 447 | 0.201 | 19.37 | 1.22 | 0.063 |

| test | estimate | SE | p | N | clusters |
|---|---:|---:|---:|---:|---|
| naive chi2 (count), all | 280.7775 |  | 5.08e-63 | 9,991 |  |
| LPM diff repeat-first, count, all, cluster=buyer | 0.1238 | 0.0161 | 1.28e-14 | 9,991 | 2890 |
| LPM diff repeat-first, count, all, cluster=dyad | 0.1238 | 0.0144 | 6.29e-18 | 9,991 | 7761 |
| LPM diff repeat-first, count, all, two-way buyer+firm | 0.1238 | 0.0308 | 5.71e-05 | 9,991 | (2890, 2814, 7219) |
| LPM diff repeat-first, value-weighted, all, cluster=buyer | -0.0079 | 0.0154 | 6.07e-01 | 9,991 | 2890 |
| LPM diff repeat-first, value-weighted, all, cluster=dyad | -0.0079 | 0.0155 | 6.09e-01 | 9,991 | 7761 |
| LPM diff repeat-first, value-weighted, all, two-way buyer+firm | -0.0079 | 0.0170 | 6.42e-01 | 9,991 | (2890, 2814, 7219) |
| LPM diff repeat-first, count, A sample, cluster=buyer | 0.1376 | 0.0162 | 2.02e-17 | 4,913 | 1126 |
| LPM diff repeat-first, count, A sample, cluster=dyad | 0.1376 | 0.0151 | 6.04e-20 | 4,913 | 3365 |
| LPM diff repeat-first, count, A sample, two-way buyer+firm | 0.1376 | 0.0328 | 2.68e-05 | 4,913 | (1126, 1437, 3129) |
| LPM diff repeat-first, value-weighted, A sample, cluster=buyer | -0.0365 | 0.0263 | 1.65e-01 | 4,913 | 1126 |
| LPM diff repeat-first, value-weighted, A sample, cluster=dyad | -0.0365 | 0.0264 | 1.67e-01 | 4,913 | 3365 |
| LPM diff repeat-first, value-weighted, A sample, two-way buyer+firm | -0.0365 | 0.0268 | 1.74e-01 | 4,913 | (1126, 1437, 3129) |
| LPM diff repeat-first, count, all excl. largest, cluster=buyer | 0.1238 | 0.0161 | 1.28e-14 | 9,990 | 2890 |
| LPM diff repeat-first, count, all excl. largest, cluster=dyad | 0.1238 | 0.0144 | 6.33e-18 | 9,990 | 7760 |
| LPM diff repeat-first, count, all excl. largest, two-way buyer+firm | 0.1238 | 0.0308 | 5.72e-05 | 9,990 | (2890, 2813, 7218) |
| LPM diff repeat-first, value-weighted, all excl. largest, cluster=buyer | -0.0165 | 0.0143 | 2.48e-01 | 9,990 | 2890 |
| LPM diff repeat-first, value-weighted, all excl. largest, cluster=dyad | -0.0165 | 0.0145 | 2.55e-01 | 9,990 | 7760 |
| LPM diff repeat-first, value-weighted, all excl. largest, two-way buyer+firm | -0.0165 | 0.0159 | 3.01e-01 | 9,990 | (2890, 2813, 7218) |
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