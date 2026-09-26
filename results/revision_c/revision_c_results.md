# Revision C: referee analyses (topic `revision_c`)

Code: `src/revision_c.py`. It imports `lockin_analysis.py`, `revision_a.py`, `revision_a_titles.py`, `models_common.py` and `models_features.py`, and modifies none of them. Run it with `python src/revision_c.py`, which takes about 12 minutes.

Settings:
- Permutations: B = 1,000 per null. Seeds are 42 + 300…303 (N4-prior) and 42 + 400…401 (exclusivity).
- Choice-set sampling uses seed 42. The placebo simulation uses seed 542 with R = 100.

Sample: main sample, 9,991 contracts. 4,913 are repeat-eligible, and their observed incumbency is 0.452. Buyer = `kurum_il_split`, firm = `firma_v3`, market = `urun_pazari`. Renewal flags are the revision-A flags (`A_renewal_flags.csv`): 1,743 renewals and 3,170 new needs.

**Estimator fix (numerical).** `revision_a.clogit_fit` can overshoot from β = 0 when a dummy is rare in a large choice set. It diverged for "renewals, full pool". `revision_c.py` therefore installs a damped Newton fit, with the step capped at 2 and no worsening steps accepted, in place of the original at run time. It gives identical estimates wherever the original converged.

Outputs:
- `C1_C2_clogit_results.csv`: every conditional-logit model.
- `C1_pool_diagnostics_24m.csv`
- `C1_choice_data_24m_poolall.csv.gz`: firm codes dropped.
- `C2_placebo_simulation.csv`
- `C2_win_rate_by_status_poolall.csv`
- `C3_N4prior_*.csv`
- `C4_exclusivity_nulls.csv`
- `C4_strict_flagged_titles.csv`
- `C5_single_bid_*.csv`
- `revision_c_log.json`

---

## 1. Choice-set bug: leakage-free supplier-choice model

### Definitions

**Contract.** Contract *i* has buyer *k*, market *m* and tender date *t*. Only repeat-eligible contracts are used.

**Pool.** The pool is all firms with at least one main-sample win in market *m* dated in [t − 730 d, t), strictly before *t*. The 12-month variant uses [t − 365 d, t). Pool membership therefore never depends on outcomes at or after *t*.

**Entrant.** An entrant is a winner that is not in its own pre-*t* pool.
- Main model (a): estimated only on contracts whose winner is in the pool. Under the MNL/IIA structure, conditioning on the chosen alternative lying in a predetermined set *C* gives consistent estimates for choice set *C*.
- Variant (b): adds the entrant winners as well.

**Pool size.** The non-chosen alternatives are 10 or 30 uniformly sampled pool firms (McFadden sampling), or the entire pool ("all").

**Covariates.** All are computed strictly before *t*:
- `incumbent`: the firm won from *k* in *m*.
- `inc_other_market`: the firm won from *k* in another market.
- `same_home_prior`: the firm's home province equals the buyer's province. Home is the province of most wins before *t*, with ties going to the earliest win. Every pool firm has prior wins, so home is always defined.
- log(1 + wins in *m* in the previous 365 d).
- log(1 + total prior wins).
- log(1 + prior wins with buyers of the same sector).

The `no_prior_wins` covariate is dropped. In model (a) it would be identically 0.

SEs are clustered by buyer (G/(G−1) sandwich).

### Pool diagnostics (4,913 eligible contracts)

| | 24-month pool | 12-month pool |
|---|---|---|
| winner in pre-t pool | 3,013 | 2,456 |
| **entrant share (contracts dropped)** | **38.7%** | 50.0% |
| entrant share among incumbent wins | 6.5% | 24.1% |
| entrant share among non-incumbent wins | 65.2% | 71.4% |
| incumbency in the kept sample | 0.689 | 0.687 |
| pool size: median (P10–P90) | 70 (33–124) | 40 (22–73) |
| contracts with ≥1 buyer incumbent in pool | 87.5% | 72.0% |
| buyer incumbents that are in the pool (pooled share) | 64.7% | 46.8% |
| contracts whose last supplier is in pool | 85.8% | 68.7% |
| contracts with all incumbents in pool | 60.0% | 43.3% |

Entrant share (24 months) by group:
- renewals 20.4%, new needs 48.7%;
- 21(b) 14.4%, open 38.3%, other procedures (mainly 21(f)) 51.6%.

About two-thirds of non-incumbent winners had no win in the market in the preceding 24 months. This is the population the old pool mis-handled. In the old pool, a firm with no history could enter the pool only through its *later* wins. The "no prior wins" OR of 11.4 in revision A was an artefact of this and is withdrawn.

### Incumbent odds ratio (95% CI, buyer-clustered)

24-month pool, winner in pool (3,013 contracts, 909 buyer clusters):

| alternatives | incumbent only | **main model** |
|---|---|---|
| 10 sampled | 113.6 (94.2–137.0) | **44.5 (36.3–54.5)** |
| 30 sampled | 117.7 (102.8–134.8) | **41.8 (35.8–48.8)** |
| all pre-t active firms | 125.2 (110.0–142.5) | **42.3 (36.4–49.2)** |

The 12-month pool (2,456 contracts) gives: 30 sampled 39.9 (33.8–47.2); all 39.8 (33.8–46.9).

Other covariates in the main model (24 months, 30 alternatives):

| covariate | OR (95% CI) |
|---|---|
| incumbent in another market of the same buyer | 2.67 (1.92–3.71) |
| same home province | 3.41 (2.88–4.04) |
| log wins in *m* in the last 12 months | 1.95 (1.74–2.19) |
| log total prior wins | 0.95 (0.85–1.06) |
| log same-sector prior wins | 1.76 (1.56–1.98) |

Subgroups (24-month pool, main model):

| subgroup | contracts | 30 alternatives | all pool |
|---|---|---|---|
| renewals | 1,388 | 118.8 (90.1–156.7) | 140.7 (107.0–185.1) |
| **new needs** | 1,625 | **22.2 (18.5–26.7)** | **21.0 (17.6–24.9)** |
| 21(b) | 529 | 101.3 (72.0–142.5) | 95.8 (69.4–132.3) |
| open | 1,877 | 31.8 (26.5–38.2) | 33.7 (28.1–40.5) |
| other (mainly 21(f)) | 607 | 50.3 (36.7–68.8) | 43.7 (32.3–59.1) |

### Entrant winners

**(b) Entrant winners included** (all 4,913 contracts; 30 alternatives from the pre-*t* pool plus the winner). Without an entrant flag, the incumbent OR is **21.5 (18.5–25.0)**:
- renewals: 48.1 (38.2–60.6);
- new needs: 13.0 (10.8–15.5).

An "entrant" flag cannot be estimated in this design. It equals 1 only for the chosen row (1,900 rows, all chosen), so it is perfectly separating, and its coefficient diverges. With the flag, the likelihood of every entrant contract becomes 1, and the other coefficients reduce to model (a). Variant (b) without the flag treats entrant winners as ordinary non-incumbent choices from a set they were not in. That biases the incumbent OR towards zero, so read it as a lower bound.

**(c) Broad pool.** The pool is all firms with any win in any market in the 24 months before *t*: median 617 firms, of which 30 are sampled. An entrant here is a winner with no win anywhere in 24 months, which is 25.4% of contracts. Because non-market firms are in the pool, a well-defined `new_to_market_24m` covariate can be added (no win in *m* in 24 months):
- incumbent OR 31.9 (25.1–40.4);
- new-to-market OR 0.23 (0.20–0.28);
- 3,665 contracts.

**Verdict.** Fixing the choice set does not weaken the incumbency effect.
- Conditional on geography, market activity, size and sector experience, the buyer's previous supplier in the market has about **42 times** the odds of winning (36–49). This holds across pool sizes 10/30/all and across 12- and 24-month windows.
- It is 21 (18–25) for new needs, about 32 under open procedures, and around 100–140 for renewals and 21(b).
- The price of the leakage-free design is that 39% of contracts (mostly new needs and 21(f)) are won by firms with no recent market history and must be dropped or handled as a bound. Including them gives OR ≈ 21.

---

## 2. State dependence vs match heterogeneity

### (a) Future-tie placebo

**Covariate.** `future_supplier_only` = 1 if the firm won from *k* in *m* at a date **after** *t* and never before *t*. It is entered alongside `incumbent` and the main covariates.

In the full 24-month pool:
- 7.8% of winners are future-only, against 0.35% of non-chosen alternatives.
- Incumbents are 68.9% of winners and 1.2% of alternatives.

Descriptive win rates per alternative in the full pool:

| status | P(win) |
|---|---|
| last supplier | 0.603 (2,814 alternatives) |
| earlier (not last) supplier | 0.221 (1,723) |
| future supplier only | 0.252 (931) |
| other pool firm | 0.0035 |

| model (24-month pool) | OR incumbent | **OR future-only** |
|---|---|---|
| 30 alternatives | 60.1 (50.5–71.5) | **51.3 (38.2–68.9)** |
| all pool | 63.7 (53.9–75.3) | **54.4 (42.2–70.1)** |
| all pool, t ≤ 2023-12-31 (less right-censoring) | 63.1 (52.3–76.0) | 52.4 (40.3–68.0) |
| all pool, renewals | 258.1 (188.3–353.9) | 127.9 (82.9–197.2) |
| all pool, new needs | 30.3 (25.1–36.7) | 39.9 (28.8–55.2) |
| 30 alternatives, + `future_other_market_only` | 62.1 | 42.2 (31.0–57.4); other-market future-only 7.0 (4.2–11.7) vs past `inc_other_market` 2.4 |

**Why the raw placebo is not decisive.** Winning *t* mechanically makes the winner the incumbent for later contracts. Under pure state dependence, therefore, "future supplier" status predicts winning *t* because of *t* itself. I benchmarked this by simulating pure state dependence, R = 100:
- Winners of the 3,013 in-pool contracts are re-drawn chronologically from the fitted main model (full pool), with `incumbent` recomputed from the simulated history.
- All other covariates stay at their observed values. Entrant and first contracts keep their observed winners.
- The placebo model is then re-estimated on each simulated dataset.

| | observed | pure-state-dependence simulation: mean [2.5–97.5%] |
|---|---|---|
| OR incumbent (placebo model) | 63.7 | 56.6 [51.4, 62.7] |
| **OR future-supplier-only** | **54.4** | **19.8 [16.1, 24.5]** |
| share of winners who are future-only | 7.8% | 6.3% [5.5, 6.8] |

**Interpretation.** State dependence alone produces a future-only OR of about 20. The observed OR is about 54, far outside the simulated range. So the future-tie placebo **fails for a pure switching-cost story**: firms that will supply the buyer later, but never had, win now much more often than pure state dependence implies.

This points to persistent buyer–firm match heterogeneity: unobserved fit, specialisation, relationships or pre-selection. The same shows up across markets, where the other-market future-only OR is 7.0 against 2.4 for the past tie.

It does not remove state dependence:
- The incumbent OR stays about 60 when the future-only term is added, above the future-only OR (54), and it is not diminished by the lead term.
- For new needs the two are similar (30 vs 40). For renewals the past tie dominates (258 vs 128).

A fair summary: **both mechanisms are present. Match heterogeneity is substantial, and state dependence is strongest in renewals.**

### (b) Last vs earlier supplier

**Definitions.**
- `inc_last`: the firm won the buyer's most recent contract(s) in *m* before *t* (all winners on the latest prior date).
- `inc_earlier`: an incumbent that is not the last supplier.

| model (24-month pool) | OR last | OR earlier (not last) | ratio last / earlier |
|---|---|---|---|
| 30 alternatives | 46.7 (40.0–54.6) | 24.7 (19.3–31.5) | 1.9 |
| **all pool** | **45.8 (39.6–52.9)** | **26.2 (20.7–33.1)** | **1.75 (1.43–2.14), p < 0.001** |
| all pool + log(1 + prior wins with *k* in *m*) | 27.5 (21.8–34.6) | 16.3 (12.0–22.1) | 1.7; count term OR 1.74 |
| all pool, renewals | 147.6 (113.6–191.8) | 84.4 (56.9–125.2) | 1.75 |
| all pool, new needs | 22.7 (19.2–26.9) | 14.2 (10.5–19.3) | 1.6 |
| all pool + future-only | 68.3 | 41.2 | 1.7; future-only 52.6 |
| pure-state-dependence simulation (any-incumbent model) | 42.3 [38.0, 46.3] | 42.2 [36.4, 47.8] | ≈ 1.0 |

**Interpretation.** The last supplier is favoured over earlier suppliers, by about 1.75× in odds, significantly. This holds within renewals and within new needs, and it survives controlling for the number of past wins with the buyer. That is the recency pattern switching costs predict.

But the contrast is modest. Earlier, displaced suppliers still have 14–26 times the odds of an unconnected firm. Switching costs tied to the current installed base alone would predict a much weaker advantage for displaced suppliers. **"Last ≫ earlier" does not hold. "Last > earlier, and earlier ≫ none" does**, which again points to a mix of switching costs and persistent match heterogeneity.

Caution: under heterogeneity, being the last supplier also correlates with win frequency, which is a proxy for match quality. The count control only partly addresses this.

---

## 3. N4/N4b with home province strictly from earlier wins

**Home province.** For each contract, the winner's home province is its most-won province among wins strictly before *t*, with ties going to the earliest win. Winners with no prior win get their own category, "none". That covers 28.2% of all contracts and 19.4% of eligible contracts. For eligible contracts, winner home = buyer province in 49.2% of cases.

**Cells:**
- N4: market × year × prior-home.
- N4b: market × year × buyer province × prior-home.

Share of eligible contracts in single-winner cells: N3 16.8%, N4 14.8%, N4b 38.5%.

| null | cells | null mean [95%] | ratio | z | excess contracts |
|---|---|---|---|---|---|
| N1 | 234 | 0.062 [0.056, 0.068] | 7.33 | 131 | 1,919 |
| N3 | 3,705 | 0.207 [0.201, 0.214] | 2.18 | 77 | 1,204 |
| **N4 prior-home** | 1,988 | 0.173 [0.167, 0.180] | **2.61** | 87 | 1,370 |
| **N4b prov × prior-home** | 5,521 | 0.264 [0.259, 0.270] | **1.71** | 68 | 923 |

By renewal status (observed; null mean [95%]):

| group | observed | N4 prior-home | N4b prior-home | N4b ratio | N4b excess |
|---|---|---|---|---|---|
| renewal (1,743) | 0.720 | 0.270 [0.256, 0.283] | 0.391 [0.380, 0.403] | 1.84 | 573 |
| new need (3,170) | 0.305 | 0.120 [0.113, 0.128] | 0.195 [0.189, 0.201] | 1.57 | 350 |

All p = 0.001 (the minimum).

**Verdict.** The leakage-free home definition slightly changes the numbers compared with revision A:
- N4: 2.61 now vs 2.44 before;
- N4b: 1.71 vs 1.87; N4b cells are finer and more degenerate.

It does not change the conclusion. Excess incumbency survives, including for new needs (1.57× under N4b).

---

## 4. Exclusivity (licence / maintenance / support of named products)

**Flags.** Titles are folded to lower-case ASCII.
- **Broad flag:** the title contains any of `lisans|licen|bakim|destek|guncelle|yenile|abonelik|subscription|surum yukselt|upgrade`.
- **Strict flag (proprietary product):** broad flag **and** a named or proprietary product or brand. Brands and products matched include Oracle, Microsoft/Windows/SQL Server, SAP, Netcad, Autodesk/AutoCAD, ESRI/ArcGIS, Adobe, VMware, Veeam, Kaspersky/ESET/Symantec/McAfee/Trend Micro/Sophos, Fortinet, Cisco, Citrix, Red Hat, IBM, Logo/Netsis/Mikro, SPSS, Matlab, the hospital and municipal systems HBYS/LBYS/YBBYS/KBS/EBYS/PACS/DYS/Medula/UYAP/e-Belediye/Kent Rehberi, and "kurumsal lisans". The full regex is in the code.
- Most frequent brand hits in strict-flagged titles: HBYS 134, Oracle 113, Microsoft 111, SAP 23, PACS 20, YBBYS 19, EBYS 17, KBS 17, IBM 15.
- Flagged titles are listed in `C4_strict_flagged_titles.csv`.

**Caveat.** `destek` also catches "karar destek sistemi" (decision support system), and `yenile` catches hardware replacement ("bilgisayar yenileme"). The broad flag is therefore an over-inclusive upper bound.

Of the 4,913 eligible contracts:

| flag | contracts flagged | share | % of renewals | % of new needs | incumbency: flagged vs remaining |
|---|---|---|---|---|---|
| strict (named product) | 514 | 10.5% | 13.9% | 8.6% | 0.486 vs 0.448 |
| broad (any wording) | 2,161 | 44.0% | 54.3% | 38.3% | 0.475 vs 0.434 |

Incumbency and nulls (observed; N1 / N3 null means; B = 1,000; all p = 0.001):

| group | n | observed | N1 null | N3 null | N3 ratio |
|---|---|---|---|---|---|
| strict-flagged renewals | 242 | 0.702 | 0.090 | 0.240 | 2.93 |
| strict-flagged new needs | 272 | 0.294 | 0.055 | 0.159 | 1.85 |
| **remaining renewals (strict)** | 1,501 | **0.723** | 0.093 | 0.296 [0.281, 0.311] | **2.44** |
| **remaining new needs (strict)** | 2,898 | **0.306** | 0.044 | 0.163 [0.155, 0.172] | **1.88** |
| remaining renewals (broad) | 797 | 0.724 | 0.127 | 0.350 [0.330, 0.371] | 2.07 |
| remaining new needs (broad) | 1,955 | 0.316 | 0.049 | 0.179 [0.169, 0.189] | 1.77 |

Note that "remaining" contracts keep their full history (flags are winner-independent groupings in the same permutation run).

**Verdict.** Title-identifiable exclusivity is not the driver:
- Named-product licence and maintenance contracts are only 10% of eligible contracts.
- Their incumbency is barely higher than the rest (0.49 vs 0.45).
- Excluding them, or even all 44% with any licence/maintenance/support/update wording, leaves renewals at 2.1–2.4× and new needs at 1.8–1.9× their N3 null.

---

## 5. Single bids with a renewal control

### Random sample

Source: `results/models/D_bid_sample_joined.csv`, year-stratified, 2012–2026. Repeat-eligible tenders: 208; 159 buyer clusters; 95 incumbent winners; 84 renewals. Logits are unweighted and buyer-clustered; year enters linearly (year − 2018); procedure is open / 21(b) / other.

| outcome | model | OR incumbent (95% CI) | OR renewal |
|---|---|---|---|
| total bids = 1 (106 events) | without renewal | 3.66 (1.92–7.00) | – |
| total bids = 1 | + renewal | **3.62 (1.84–7.13)** | 1.04 (0.54–1.98) |
| total bids = 1 | + renewal, negotiated dummy | 4.30 (2.23–8.31) | 1.10 |
| valid bids = 1 (131 events) | without renewal | 2.63 (1.29–5.36) | – |
| valid bids = 1 | + renewal | **2.95 (1.36–6.38)** | 0.72 (0.36–1.44) |
| valid bids = 1 | + renewal, negotiated dummy | 3.75 (1.77–7.94) | 0.78 |

Single-bid rates (random sample):

| outcome | renewal: incumbent | renewal: non-incumbent | new need: incumbent | new need: non-incumbent |
|---|---|---|---|---|
| total bids | 0.77 (n = 56) | **0.25** (28) | 0.62 (39) | 0.38 (85) |
| valid bids | 0.82 | **0.36** | 0.72 | 0.55 |

### cp2 sample (valid bids only)

Software-titled tenders, 2021 onwards: 681 eligible tenders, 263 clusters. Year FE and procedure are included.

| model | OR incumbent | OR renewal |
|---|---|---|
| without renewal | 1.99 (1.37–2.89) | – |
| + renewal | **2.68 (1.81–3.95)** | 0.52 (0.33–0.81) |
| + renewal + incumbent × renewal | 1.82 (1.17–2.82) among new needs | renewal 0.28 (0.15–0.53); interaction 3.13 (1.48–6.60) → within renewals the incumbent OR is about 5.7 |

cp2 single-valid-bid rates:

| | incumbent | non-incumbent |
|---|---|---|
| renewal | 0.649 (n = 134) | **0.293** (58) |
| new need | 0.688 (109) | 0.524 (380) |

**Why adding renewal raises the incumbent OR in cp2.** It is classic omitted-variable bias:
- Renewal is strongly positively related to incumbency: P(renewal) is 0.55 for incumbent winners and 0.13 for non-incumbent winners (r = 0.45).
- Conditional on the winner type, renewal is *negatively* related to single bidding (OR 0.52).
- Renewals won by a newcomer are the most contested tenders: 29% single bids against 52% for new needs won by newcomers. Switching happens where there is competition.

Leaving renewal out puts the low single-bid rate of contested renewals into the incumbent comparison and compresses the gap. Controlling for it restores the gap (1.99 → 2.68).

In the random sample the renewal effect on total bids is about zero (OR 1.04), so the incumbent OR does not move (3.66 → 3.62). For valid bids it rises modestly (2.63 → 2.95).

**Verdict.** Incumbent wins are associated with single bidding in both samples and for both outcomes:
- random sample: total OR about 3.6, valid OR about 3.0;
- cp2: valid OR about 2.7.

The renewal control does not explain it away.

---

## 6. 21(b) timing and 21(f)

### Triple interaction

Sample A: 4,913 eligible contracts, of which 1,502 are from health buyers. The model is the revision-B S1 logit:
- 21(b), other negotiated, log real value, the three buyer-history controls, post-7144, 21(b)×post;
- plus 21(b)×health, post×health, other-negotiated×health and **21(b)×post×health**;
- FE for year, market and buyer sector. The sector FE absorbs the health main effect.
- SEs are two-way clustered by buyer and firm.

| term | OR (95% CI) | p |
|---|---|---|
| **21(b)×post×health (triple)** | **2.74 (0.79–9.51)** | **0.11** (buyer-only clustering: 0.11) |
| implied 21(b)×post, non-health | 0.89 (0.31–2.56) | 0.83 |
| implied 21(b)×post, health | 2.44 (1.36–4.35) | 0.003 |

AME difference-in-differences (post − pre change in the 21(b) − open incumbency gap, delta method, two-way clustering):

| group | change (pp) | p |
|---|---|---|
| health | +11.8 (0.6 to 23.0) | 0.038 |
| non-health | −2.1 (−19.8 to 15.5) | 0.81 |
| **health − non-health** | **+13.9 (−7.6 to 35.5)** | **0.20** |

LPM triple interaction: +10.4 pp (−10.6 to 31.3), p = 0.33.

Raw cells (incumbency, 21(b) vs open):
- Health: pre 0.61 vs 0.48 (n = 163 / 285); post 0.88 vs 0.67 (371 / 579).
- Non-health: pre 0.23 vs 0.35 (35 / 876); post 0.24 vs 0.39 (49 / 1,309).

**Verdict.** The post-2018 rise in the 21(b) premium is significant for health buyers and absent for non-health buyers. But the **formal health vs non-health difference is not statistically significant** (triple OR 2.7, p = 0.11; AME DiD +14 pp, p = 0.20). Non-health 21(b) is thin (84 contracts), so the triple is imprecise. The paper should say "concentrated in health buyers" and not "significantly larger in health".

### 21(f)

Among the 1,204 repeat-eligible 21(f) contracts, incumbency is **0.346**, against null means of **0.033 (N1)** and **0.131 (N3)** (ratios 10.5 and 2.6; p = 0.001; B = 1,000):
- renewals: 0.737 vs N3 0.229;
- new needs: 0.209 vs N3 0.097.

Sentence for the paper: *"Under the below-threshold Art. 21(f) procedure, 34.6% of repeat-eligible contracts went to the incumbent, 2.6 times the province-conditioned null (13.1%) and 10.5 times the market–year null (3.3%)."*

---

## Summary

**Holds:**
- The corrected choice model gives an incumbent OR of about 42 (36–49), stable across pool sizes and windows. It is 21 for new needs and 21.5 with entrant winners included, which is a lower bound.
- Excess incumbency under leakage-free N4/N4b: 2.61× / 1.71×.
- Excess incumbency after removing named-product licence/maintenance contracts: N3 ratio 2.4 for renewals, 1.9 for new needs.
- Single bidding associated with incumbent wins, with a renewal control (OR 2.7–3.6).
- 21(f) excess incumbency.

**Changed or withdrawn:**
- The "no prior wins" OR of 11.4 was an artefact of the old pool and is withdrawn.
- 39% of eligible contracts (65% of non-incumbent wins) go to firms with no win in the market in the prior 24 months.

**Mechanism:**
- The future-tie placebo is large: OR 54, against about 20 under simulated pure state dependence. This indicates substantial persistent match heterogeneity.
- The last supplier beats earlier suppliers by only about 1.75×, and earlier suppliers keep OR about 26.
- Switching costs are consistent with the renewal and recency patterns, but they are not the whole story.

**Not significant:**
- The health vs non-health difference in the post-2018 21(b) premium (p = 0.11 logit; p = 0.20 AME).
