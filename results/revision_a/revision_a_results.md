# Revision A: referee analyses (topic `revision_a`)

Code: `src/revision_a.py` (driver) and `src/revision_a_titles.py` (title normalisation). Both use relative paths. Run with `python src/revision_a.py` (about 5 min).

The script reuses the definitions and permutation engine in `lockin_analysis.py`:
- repeat-eligible;
- incumbent;
- strictly-earlier history, where same-date ties are not history;
- winners permuted within cells.

Settings:
- Permutations: B = 1,000 per null.
- Buyer bootstrap: 500 resamples.
- Seeds: `default_rng(42 + offset)`. Nulls use offsets 100–104 (main) and 200–212 (subsamples). The choice-set sampling and bootstrap use seed 42.

Main sample: `in_scope_main`, 9,991 contracts, of which 4,913 are repeat-eligible. Observed incumbency is 0.452 (2,222 contracts).

Outputs (this folder):
- `A_renewal_flags.csv`
- `A_renewal_validation_sample.csv` / `A_renewal_validation_labels.csv`
- `A_fig_A1_data.csv`
- `B_null_overall.csv`
- `B_null_by_group.csv`: every null × grouping
- `C_multilot_framework_titles.csv`
- `D_choice_data.csv.gz`: firm codes only, no names
- `D_clogit_results.csv`
- `E_buyer_BH.csv`
- `F_single_bid_*.csv`
- `revision_a_log.json`

Figure: `figures/F-A1_incumbency_by_gap_renewal.png/.pdf`.

All permutation p-values reported below are 0.001 (the minimum, 1/1001) unless stated otherwise.

---

## 1. Renewals vs new needs

### Definitions

**Title normalisation** (`norm_tokens`):
1. Turkish-aware lower-casing (I→ı, İ→i).
2. Fold diacritics (ç ğ ı ö ş ü → c g i o s u).
3. Keep only alphanumerics.
4. Drop every token containing a digit (years, durations, counts).
5. Drop tokens shorter than 3 characters.
6. Drop month names, number words, roman numerals, and a list of about 110 generic procurement or administrative words. Examples: *hizmet(i), alım(ı), iş(i), temini, yılı, yıllık, aylık, süreli, adet, kalem, kısım, grup, ihtiyacı, müdürlüğü, belediyesi, hastanesi, teknik, genel*.
7. Stem the remaining tokens to their first 5 characters (the standard F5 stemmer for Turkish).

Title similarity is the Jaccard index of the two stemmed token sets.

**Renewal (primary).** A repeat-eligible contract *i* (buyer *k*, market *m*, date *t*) is a renewal if buyer *k* has a contract in market *m* whose tender date lies 183–548 days (6–18 months) before *t* and whose title similarity is ≥ 0.50. Every other repeat-eligible contract is a **new need**.

Renewal status depends only on buyer, market, date and title. It does not depend on the winner, so it is fixed under every permutation, and each subgroup is compared with its own null.

**Threshold validation.** I drew 60 best-match pairs at random (seed 42), 15 in each similarity band: [0.35, 0.45), [0.45, 0.55), [0.55, 0.70), [0.70, 1]. I read every pair and coded it from the titles alone (`A_renewal_validation_labels.csv`; coded by the analysis agent, not by a human).

| band | same recurring need | different need | ambiguous |
|---|---|---|---|
| [0.35, 0.45) | 7 | 8 | 0 |
| [0.45, 0.55) | 12 | 3 | 0 |
| [0.55, 0.70) | 14 | 0 | 1 |
| [0.70, 1.00] | 14 | 0 | 1 |
| **sim ≥ 0.50 (42 pairs)** | **38 (90%)** | 2 | 2 |
| sim < 0.50 (18 pairs) | 9 (50%) | 9 | 0 |

- **Precision above the threshold is about 90–95%.** The typical false positive is YBBYS vs HBYS, where the modules differ but the stems overlap.
- **Recall is imperfect.** About half of the pairs just below 0.50 are also the same need, often with reworded titles. So the new-need group contains some renewals. This biases the renewal/new-need contrast *towards zero*.
- Thresholds of 0.40 and 0.67 are reported as sensitivities below.

### Counts

Of the 4,913 repeat-eligible contracts:
- **1,743 (35.5%) are renewals** and 3,170 are new needs.
- Threshold 0.40: 1,861 renewals (37.9%).
- Threshold 0.67: 1,455 (29.6%).
- Broad window (similar title 0–18 months earlier): 2,120 (43.2%).
- 0–24 months: 2,292 (46.7%).

Median days since the buyer's previous contract in the same market (any title): 356.

### Incumbency by renewal status

Observed rate, with the null mean for each null (B = 1,000):

| group | n | observed | N1 | N2 | N3 | N4 (home) | N4b (prov × home) | ratio N1 / N3 / N4b |
|---|---|---|---|---|---|---|---|---|
| renewal | 1,743 | **0.720** | 0.092 | 0.166 | 0.288 | 0.263 | 0.343 | 7.8 / 2.5 / 2.1 |
| new need | 3,170 | **0.305** | 0.045 | 0.078 | 0.163 | 0.142 | 0.186 | 6.8 / 1.9 / 1.6 |

N3 95% null intervals: renewal [0.275, 0.302]; new need [0.155, 0.171].

Excess incumbent contracts (observed − null, × n):

| group | N1 | N2 | N3 | N4b |
|---|---|---|---|---|
| renewal | 1,095 | 965 | 752 | 658 |
| new need | 825 | 719 | 450 | 376 |

New needs account for 43% of the N1 excess and 37% of the N3 excess.

**Finer split.** The four categories (A–D) are mutually exclusive:

| category | n | observed | N1 | N3 |
|---|---|---|---|---|
| A: similar title 6–18 months earlier (renewal) | 1,743 | 0.720 | 0.092 | 0.288 |
| B: similar title only < 6 months earlier | 377 | 0.578 | 0.073 | 0.312 |
| C: similar title only > 18 months earlier | 676 | 0.518 | 0.062 | 0.264 |
| **D: no similar-title prior at all** | **2,117** | **0.188** | 0.034 | 0.104 |

- Group D is the cleanest "new need" group. Its incumbency is 0.188 against an N3 null of 0.104 (1.8×) and an N1 null of 0.034 (5.5×).

**Sensitivities of the renewal definition** (observed renewal / new need, with N3 null means in brackets):

| definition | renewal | new need |
|---|---|---|
| threshold 0.40 | 0.709 [0.286] | 0.296 [0.159] |
| threshold 0.67 | 0.744 [0.302] | 0.329 [0.168] |
| window 0–18 months | 0.695 [0.293] | 0.268 [0.143] |
| window 0–24 months | 0.684 [0.290] | 0.250 [0.135] |

**By procedure** (observed [N1 null; N3 null]):

| procedure | renewal | new need |
|---|---|---|
| 21(b) | **0.900** [0.198; 0.427] (n = 291) | 0.566 [0.093; 0.331] (n = 327) |
| open | 0.669 [0.077; 0.267] (n = 1,128) | 0.307 [0.045; 0.165] (n = 1,913) |
| other (mainly 21(f)) | 0.735 [0.049; 0.237] (n = 324) | 0.210 [0.026; 0.099] (n = 930) |

**By product market**, for the 8 markets with ≥ 200 eligible contracts (observed [N1; N3 null means]). All 16 cells have N3 p ≤ 0.002.

| market | renewal: n | renewal: observed [N1; N3] | new need: n | new need: observed [N1; N3] |
|---|---|---|---|---|
| health_information_systems | 519 | 0.869 [0.209; 0.452] | 733 | 0.607 [0.110; 0.375] |
| ERP_management_software | 201 | 0.821 [0.034; 0.227] | 544 | 0.233 [0.024; 0.069] |
| software_licences | 241 | 0.593 [0.048; 0.212] | 361 | 0.161 [0.034; 0.091] |
| custom_software_web_mobile | 79 | 0.544 [0.010; 0.152] | 409 | 0.134 [0.006; 0.038] |
| maintenance_support_services | 192 | 0.776 [0.036; 0.138] | 183 | 0.284 [0.021; 0.107] |
| network_datacentre_infrastructure | 112 | 0.670 [0.035; 0.184] | 216 | 0.236 [0.016; 0.090] |
| computers_peripherals | 110 | 0.436 [0.014; 0.194] | 171 | 0.257 [0.010; 0.146] |
| GIS_city_information | 58 | 0.828 [0.135; 0.274] | 172 | 0.157 [0.071; 0.104] |

By buyer sector (`B_null_by_group.csv`, dimension `sector_x_renewal`):
- Health new needs still show 0.550 incumbency against an N3 null of 0.333.
- Municipal new needs show 0.220 against 0.100.

### Figure F-A1

`F-A1_incumbency_by_gap_renewal`, 7 in wide.
- **Top panel:** observed incumbency with 95% normal CIs, plus the N3 null mean, for renewals and new needs, by days since the buyer's previous contract in the market (any title). Bins with n < 15 are omitted.
- **Bottom panel:** contract counts per bin.

What it shows:
- Renewals: 0.60–0.81 incumbency at every gap, about 2.5–3× the N3 null.
- New needs: 0.19–0.38, roughly flat in the gap, and consistently above their N3 null (0.10–0.22).
- Renewals are, by construction, absent beyond 548 days.

**Verdict.** Re-tendering of the same service is a large part of incumbency:
- 35% of eligible contracts are renewals;
- they have 72% incumbency;
- they supply 57–64% of the excess, depending on the null.

It is not the whole story. New needs, including contracts with no similar-title predecessor at all, still go to incumbents 1.6–1.9× more often than the province-conditioned nulls predict, and 5.5–6.8× more often than the market × year null predicts.

---

## 2. Stronger nulls and the supplier-choice model

### 2a. Nulls preserving firm geography

- **Firm home province:** the buyer province (`il`) where the firm won the most main-sample contracts, with ties broken by the earliest win. 67.0% of contracts have buyer province = winner's home province.
- **N4 (home):** winners are permuted within market × year × winner's home province. The buyer's province is not constrained: contracts with buyer province ≠ firm home stay in the permutation.
- **N4b (prov × home):** market × year × buyer province × winner's home province.

Share of eligible contracts that sit in cells with a single distinct winner, where the permutation cannot move the winner:

| null | cells | eligible contracts in single-winner cells |
|---|---|---|
| N3 | 3,705 | 16.8% |
| N4 | 2,522 | 14.1% |
| N4b | 4,814 | 31.3% |

N4b is therefore very conservative.

| null | cells | null mean [95%] | ratio | z | excess contracts |
|---|---|---|---|---|---|
| N1 market × year | 234 | 0.062 [0.056, 0.067] | 7.35 | 141 | 1,920 |
| N2 + sector | 1,424 | 0.110 [0.102, 0.117] | 4.13 | 96 | **1,683** |
| N3 + buyer province | 3,705 | 0.208 [0.202, 0.214] | 2.18 | 81 | **1,203** |
| **N4 + firm home province** | 2,522 | 0.185 [0.178, 0.191] | **2.44** | 81 | 1,313 |
| **N4b + buyer province + firm home** | 4,814 | 0.242 [0.237, 0.247] | **1.87** | 76 | 1,034 |

**Verdict.** Preserving firm geography does not remove the excess. Even N4b leaves 1.87× (about 1,030 excess incumbent contracts, 21% of eligible contracts).

### 2b. Conditional logit supplier-choice model

**Choice set.** For each of the 4,913 repeat-eligible contracts, the set contains the actual winner plus a uniform random sample of 30 other firms. These firms won at least one main-sample contract in the same product market in the tender year or the year before.
- Mean set size: 30.5.
- 423 sets are smaller than 31 because the market pool was small.
- Rows: 149,670.
- Uniform sampling of non-chosen alternatives gives consistent conditional-logit estimates (McFadden 1978).

**Covariates of alternative *j* for contract *i*.** All histories use contracts strictly before the tender date of *i*.
- `inc_same_market`: *j* previously won from buyer *k* in market *m*.
- `inc_other_market`: *j* previously won from *k* in another market.
- `same_home_province`: *j*'s home province = the buyer's province (whole-sample home, as the referee specified).
- log(1 + *j*'s wins in *m* in the previous 365 days).
- log(1 + *j*'s total prior wins).
- log(1 + *j*'s prior wins from buyers of the same `sektor_v3`).

**Estimation.** Own Newton–Raphson maximum likelihood with line search. Point estimates match statsmodels `ConditionalLogit` to 3 decimals.
- Standard errors are cluster-robust by buyer (1,126 clusters; sandwich of summed contract scores, G/(G−1) correction).
- A pairs bootstrap by buyer (500 resamples) is reported for the main models.

**Leakage in the referee's home definition.** Whole-sample home includes contract *i* itself. The winner's home is partly defined by this win, which inflates `same_home_province` (OR 15) and absorbs part of the incumbency effect. I therefore also report:
- a *leave-contract-out* home;
- a *prior-wins-only* home (leakage-free). It adds a `no_prior_wins` dummy, because firms with no history have no home.

The prior-wins-only model is my preferred specification.

**Odds ratio for `inc_same_market`** (95% CI, buyer-clustered; bootstrap in brackets):

| model | contracts | OR incumbent |
|---|---|---|
| incumbent only | 4,913 | 50.9 (44.8–57.8) |
| full, referee spec (whole-sample home) | 4,913 | **15.2** (12.9–17.8) [boot 12.8–18.1] |
| full, leave-contract-out home | 4,913 | 20.4 (17.7–23.6) |
| **full, prior-wins-only home (preferred)** | 4,913 | **23.8** (20.6–27.5) [boot 20.7–27.9] |
| full without any home variable | 4,913 | 29.8 (26.0–34.1) |
| referee spec: renewals only | 1,743 | 32.7 (26.1–40.9) |
| referee spec: new needs only | 3,170 | **8.8** (7.2–10.6) |
| referee spec: 21(b) only | 618 | 52.5 (37.9–72.7) |
| referee spec: open only | 3,041 | 12.8 (10.7–15.3) |
| referee spec: other procedures (mainly 21(f)) | 1,254 | 10.5 (7.6–14.4) |
| preferred spec: renewals | 1,743 | 56.7 (44.7–72.0) |
| preferred spec: new needs | 3,170 | **13.9** (11.7–16.6) |
| preferred spec: 21(b) | 618 | 68.0 (50.5–91.7) |
| preferred spec: open | 3,041 | 19.5 (16.5–23.0) |

**Pooled interaction model** (referee spec). Incumbent main effect OR 7.5 (6.1–9.2). Interactions with incumbency:
- renewal: ×3.73 (2.86–4.88);
- 21(b): ×4.58 (3.19–6.56);
- other procedures: ×0.76 (0.55–1.05).

**Other covariates in the preferred model:**

| covariate | OR (95% CI) |
|---|---|
| incumbent in another market of the same buyer | 4.34 (3.27–5.77) |
| same home province (prior wins) | 3.17 (2.81–3.58) |
| log prior wins with same-sector buyers | 1.91 (1.75–2.08) |
| log wins in the market in the previous 12 months | 0.94 (0.86–1.03) |
| log total prior wins | 0.89 (0.82–0.96) |
| no prior wins | 11.4 (9.8–13.2) |

The no-prior-wins OR reflects frequent entrant winners relative to the sampled active firms.

**Verdict.** Conditional on firm geography, market activity, overall size and sector specialisation, a firm that has already won from the buyer in the same market has 15–24 times the odds of winning the next contract. The range depends on the home definition. The effect holds:
- for new needs (OR 8.8–13.9);
- under open procedures (12.8–19.5);
- and most strongly for 21(b) and renewals.

These are associations conditional on observables. They do not identify buyer favouritism versus switching costs or bidder self-selection. We observe winners, not bidders.

---

## 3. Lots and framework agreements

- **One row per IKN.** The data have exactly one row per IKN: 9,991 unique IKNs in 9,991 rows (13,024 in 13,024 in the full table). For multi-lot (*kısmi teklif*) tenders, only one winner is recorded per IKN: the scraper takes the first "Yüklenicisi" match. Other lot winners are missing.
- **Multi-lot titles.** A title regex (`KISIM`, `KISMİ TEKLİF`, `KISMİ İHALE`, `GRUP`, `LOT <n>`) flags **116 contracts**, 63 of them repeat-eligible. The list is in `C_multilot_framework_titles.csv`, spread over 12 markets.
  - Incumbency among them is 0.238, against 0.054 under N1 and 0.159 under N3 (p = 0.026).
- **Framework agreements.** No title contains "çerçeve anlaşma" or "çerçeve sözleşme": **0 framework agreements**. The word "çerçeve" appears in 7 titles, all meaning "within the framework of".
- **Excluding the 116 multi-lot contracts** (history recomputed):

| null | eligible | observed | null mean | ratio | excess contracts |
|---|---|---|---|---|---|
| N1 | 4,839 | 0.455 | 0.062 | 7.35 | 1,902 |
| N2 | 4,839 | 0.455 | 0.109 | 4.16 | 1,672 |
| N3 | 4,839 | 0.455 | 0.209 | 2.18 | 1,192 |

**Verdict.** Lots and framework agreements are negligible and do not affect the result.

---

## 4. Robustness: excluding natural persons and excess counts

- **Excluding natural-person winners.** 180 eligible contracts have a winner flagged `is_natural_person` or `contains_natural_person`. Removing them (history recomputed):

| null | contracts | eligible | observed | null mean [95%] | ratio | excess contracts |
|---|---|---|---|---|---|---|
| N1 | 9,509 | 4,665 | 0.464 | 0.066 [0.060, 0.072] | 7.07 | 1,859 |
| N2 | 9,509 | 4,665 | 0.464 | 0.116 [0.109, 0.123] | 4.01 | 1,625 |
| N3 | 9,509 | 4,665 | 0.464 | 0.214 [0.208, 0.220] | 2.17 | 1,166 |

  Natural-person winners themselves show 0.317 incumbency (N1 null 0.025).
- **Excess incumbent contracts on the main sample:**
  - N2: **1,683** (0.343 × 4,913);
  - N3: **1,203** (0.245 × 4,913);
  - N4: 1,313;
  - N4b: 1,034;
  - for comparison, N1: 1,920.

---

## 5. Buyer-level tests with multiple-testing correction

Setup:
- 540 buyers with at least 5 contracts.
- Per-buyer one-sided permutation p-values from `results/lockin/buyer_dependence.csv`: p = (1 + #null ≥ obs)/(B + 1), B = 1,000.
- Benjamini–Hochberg (BH) correction at q = 0.05 across the 540 buyers, separately for each measure and null.

| null | measure | above own 95th null pct (uncorrected) | **BH rejections at 5%** | Bonferroni |
|---|---|---|---|---|
| N1 | top-supplier share | 310 (57.4%) | **273 (50.6%)** | 0 |
| N1 | supplier HHI | 379 (70.2%) | **357 (66.1%)** | 0 |
| N2 | top-supplier share | 255 (47.2%) | **212 (39.3%)** | 0 |
| N2 | supplier HHI | 328 (60.7%) | **289 (53.5%)** | 0 |

- Bonferroni rejects none: the smallest attainable p (1/1001) exceeds 0.05/540, so it cannot reject with B = 1,000. BH is the appropriate correction here.
- **By buyer type**, BH share for N1 top-supplier share:

| buyer type | BH share |
|---|---|
| MoH hospitals / dental centres | 87.7% (50/57) |
| University hospitals | 61.5% |
| Central government | 49.3% |
| MoH provincial directorates | 46.3% |
| Municipalities | 44.4% |
| Universities (non-health) | 35.8% |

- The full table is `E_buyer_BH.csv`.

**Verdict.** After FDR control, half (top share) to two-thirds (HHI) of the buyers still exceed their N1 null, and 39–54% exceed their N2 null.

---

## 6. Single-bid expansion (cp2)

### What cp2 is

The cp2 scrape (released as `data/bid_counts_cp2.csv` without firm names) has 3,400 records with unique IKNs. It is the stage-2 checkpoint of `ekap_v3.py` (`asama2`), and it was built as follows:
- Stage 1 queried EKAP keyword by keyword, sorted by tender date descending, and deduplicated IKNs in keyword order.
- Stage 2 fetched the notices of the "completed" tenders (status contains *sonuç* or *sözleşme*) in stage-1 order.
- **The run stopped after 3,400 of 16,741 completed tenders.** All 3,400 therefore come from the **first keyword, "yazılım"**: 3,400 of that keyword's 4,254 completed tenders, running from 2026 back to 2013.

`teklif_veren_sayisi` comes from the regex "Geçerli Teklif Sayısı". It is the number of **valid bids**, not total bids:
- It equals `gecerli_teklif` in `teklif_ornek.csv` for 59/59 overlapping tenders, and `toplam_teklif` for only 85%.
- It is parsed only when the winner regex succeeded. That happened only for the new-format result notices of **2021–2026** (1,219 records).
- 0 means "not parsed" and is treated as missing.

**Selection.** The subsample is main-sample tenders from 2021 to March 2026 whose title (or IKN) contains "yazılım" (software).
- 1,194 joined main-sample tenders have a bid count.
- These are 94% of the 1,266 main-sample 2021+ tenders first retrieved by "yazılım", and 34.7% of all 3,441 main-sample 2021+ tenders.
- The subsample is near-complete within that frame. The frame is not random: it contains only software-titled tenders, only post-2021, and none of the hardware, network or call-centre titles retrieved by other keywords.
- Outcome: single valid bid (= 1). Unweighted, with Wilson CIs.

### Single-bid rates

| group | n | single-valid-bid rate [95% CI] |
|---|---|---|
| all | 1,194 | 0.580 [0.551, 0.607] |
| **incumbent winner** | 243 | **0.667** [0.605, 0.723] |
| **non-incumbent winner** | 438 | **0.493** [0.447, 0.540] |
| buyer first in market (undefined) | 513 | 0.612 |
| open | 726 | 0.653 [0.618, 0.687] |
| 21(b) | 57 | 0.737 [0.610, 0.834] |
| 21(f) | 408 | 0.429 [0.382, 0.477] |
| renewal (eligible) | 192 | 0.542 |
| new need (eligible) | 489 | 0.560 |
| renewal, incumbent / non-incumbent | 134 / 58 | 0.649 / **0.293** |
| new need, incumbent / non-incumbent | 109 / 380 | 0.688 / 0.524 |
| open, incumbent / non-incumbent | 154 / 271 | 0.740 / 0.554 |
| 21(b), incumbent / non-incumbent | 16 / 15 | 0.938 / 0.733 |

### Buyer-clustered logit

Sample: 681 eligible tenders, 263 buyer clusters.

| model | OR incumbent (95% CI) | p |
|---|---|---|
| single ~ incumbent + procedure + year FE + market FE | **2.04** (1.40–2.96) | < 0.001 |
| … + renewal | 2.65 (1.78–3.94) | < 0.001 |
| … (renewal term in the model above) | renewal OR 0.53 (0.33–0.84) | – |
| procedure + year FE only (as in models D) | 1.99 (1.37–2.89) | < 0.001 |

In the first model, 21(b) vs open has OR 2.57 (0.83–7.95).

**Comparison with the year-stratified random sample** (`results/models`, 2012–2026, 393 tenders):
- Total-bid single rate: 0.712 vs 0.324 (OR 4.44).
- The comparable *valid*-bid measure there: 0.767 vs 0.484.

**Verdict.** The association replicates in a sample three times larger: incumbent winners face a lone valid bid more often (0.67 vs 0.49). But it is weaker than in the random sample: OR about 2.0 against 4.4, and a 17 pp gap against 39 pp.

Reasons for the difference:
- The outcome here is valid bids, not total bids. Single valid bids are more common for everyone, which compresses the gap.
- The frame is software-titled tenders from 2021 onwards only.
- Open tenders in this frame have a high single-valid-bid rate (0.65).

Renewals won by a newcomer rarely have a single bid (0.29): switching happens where there is competition.

---

## 7. Summary of what holds and what does not

**Holds:**
- Excess incumbency survives separating renewals from new needs.
  - New needs: 0.305 vs N3 0.163.
  - No-similar-title contracts: 0.188 vs N3 0.104.
- It survives firm-geography nulls: N4 2.44×, N4b 1.87×.
- It survives excluding lots and natural persons.
- It survives buyer-level FDR control.
- It survives a supplier-choice model with firm covariates: incumbent OR 15–24, and 9–14 for new needs.

**Qualified:**
- About 35% of repeat-eligible contracts are annual-type renewals. They carry 57–64% of the excess, so the paper should present much of the incumbency as re-tendering of ongoing services, where switching costs are expected.
- The referee's whole-sample home-province variable is contaminated by the outcome. Use the prior-wins definition.
- The cp2 single-bid subsample is a non-random software/2021+ frame, and its incumbency–single-bid gradient (OR about 2) is about half that of the random sample.
- None of this separates favouritism from switching costs, because we observe winners, not bids.
