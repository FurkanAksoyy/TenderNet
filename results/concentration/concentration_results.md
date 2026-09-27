# TenderNet v3 - Market concentration (topic: `concentration`)

Script: `src/concentration_v3.py`. Sample: main (`in_scope_main`), N = 9,991 contracts, 2,814 firms (`firma_v3`), 2,890 buyers (`kurum_il_split`). Nominal TRY uses explicit contract currencies and cached TCMB tender-date midpoint FX proxies; unlabelled currencies are assumed TRY (see currency fields and data/fx_cache_tcmb/README.md). Real values in 2025 TRY using TÜİK CPI annual averages (2026 deflated with the mean of the 8 available linked 2026 monthly values = 4,013.6; 2025 = 3,183.2). Total real value = 89.74 bn 2025-TRY (nominal 33.30 bn). HHI on 0-10,000 scale; CR4 in %. Bootstrap: 1000 resamples of contracts within each market, seed 42, bias-shifted percentile 95% CIs (percentile interval minus the bootstrap bias, mean(boot)−estimate, clipped to [0, 10,000]; raw percentile bounds and bias are in the CSV). Winsorised variant caps each contract's real value at the main-sample 99th percentile (101.5 m 2025-TRY). LOO = leave-one-contract-out (all contracts, exact).

The MHRS Faz-16 call-centre contract (2025, 7.54 bn 2025-TRY) is 8.4% of main-sample real value and 94.3% of the call-centre market.

## Bottom line

- **Pooled procurement mix falls below the reference lines by every measure**: aggregate supplier HHI = 39 (count), 147 (real value), 91 (value without MHRS contract). This pooled number is mechanically diluted (section 4) and should not be read as evidence of competition.
- **Robustly concentrated product categories (HHI above threshold under count AND real value AND value-without-largest AND worst-case leave-one-out AND winsorised value):** none at >1,800; none at 1,000-1,800.
- All 14 product categories fall below 1,000 on at least one variant, and the failing variant is always the **count** HHI: the highest count HHI is 690 (Call centre / help-desk, n=74); no category reaches 1,000 by count (bias-shifted upper CI bounds: Call centre / help-desk 1,160).
- Markets that cross 1,000 on raw real-value HHI: Call centre / help-desk 8,893 → 1,639 without its largest contract (LOO min 1,639, winsorised 1,366; largest contract = 94.3% of market value); Education technology 1,062 → 752 without its largest contract (LOO min 752, winsorised 539; largest contract = 25.4% of market value); Smart city / traffic OT 2,448 → 813 without its largest contract (LOO min 813, winsorised 581; largest contract = 36.3% of market value). Smart city and education technology drop below 1,000 once one contract is removed: single-contract artefacts. The call-centre market stays ≥1,000 on every value variant but is tiny (74 contracts, 46 firms), its count HHI is below 1,000, and its value is 94% one contract (MHRS); it is best described as a few very large national call-centre contracts, not a concentrated market in the merger-guideline sense.
- **Health information systems is the only large market with persistent, non-artefactual concentration**, still below the 1,000 screen: count HHI 431 [405, 458], real-value HHI 831 [692, 985], value CR4 53.2%, LOO range 803-868 (no single contract matters), 2,189 contracts but only 205 firms (numbers-equivalent 12 equal-sized firms by value). Within a year its median count HHI is 671 and value HHI 1,091 (IQR 962-1,355). Its level depends on firm canonicalisation (original `firma`: count 250, value 593).
- **Within-year view (section 2)**: plug-in within-year HHIs are higher than the 15-year pooled values, but for counts most of the gap is the small-sample floor (10,000/n with n≈30-150 per market-year): the unbiased within-year count HHI medians are Health information systems 597, GIS / city information 369, Software licences 187 and <200 elsewhere, i.e. genuine temporal dilution is modest except in health IS (597 vs pooled 426). Median within-year value HHI is ≥1,000 in GIS / city information, Cybersecurity, Health information systems, Maintenance / support services, Network / data-centre infra., Physical security / surveillance; this value measure carries the same small-n upward bias (no simple correction exists for value shares), so it is an upper bound. Within-year category HHIs describe the distribution of recorded awards; they do not identify competitive conduct or economic market boundaries.
- Conclusion for the paper: **no product market is robustly concentrated under count AND value AND leave-one-out**. Any dependence story must therefore rest on relational/buyer-level measures (lock-in), not on market-level HHI.
- The 1,000 HHI line is a historical 1992 guideline reference; the 2023 US Merger Guidelines use >1,800 as the high-concentration threshold. These reference lines are descriptive here, not merger presumptions or conduct/harm thresholds, and our 'markets' are title-based product categories pooled over 15 years and all of Türkiye, not antitrust relevant markets. Treat the classification as descriptive.

## 1. Supplier-side concentration by product category (urun_pazari)

Table 1a. HHI with bootstrap 95% CIs.

| category | N | firms | HHI count [95% CI] | HHI count (unbiased) | CR4 count | HHI value [95% CI] | CR4 value | HHI value w/o largest [95% CI] | CR4 w/o largest | largest contract % of value |
|---|---|---|---|---|---|---|---|---|---|---|
| All categories pooled | 9,991 | 2,814 | 39 [36, 41] | 38 | 7.3 | 147 [40, 501] | 18.1 | 91 [47, 288] | 12.9 | 8.4 |
| ERP / management software | 1,515 | 599 | 84 [71, 97] | 77 | 12.9 | 131 [74, 218] | 15.6 | 119 [67, 198] | 14.0 | 2.5 |
| GIS / city information | 553 | 203 | 353 [273, 444] | 335 | 27.1 | 408 [228, 842] | 33.4 | 385 [244, 712] | 30.4 | 8.6 |
| Call centre / help-desk | 74 | 46 | 690 [363, 1,160] | 563 | 35.1 | 8,893 [3,517, 10,000] | 97.8 | 1,639 [0, 7,297] | 66.9 | 94.3 |
| Computers / peripherals | 696 | 467 | 40 [34, 47] | 26 | 6.8 | 169 [69, 357] | 18.0 | 145 [61, 304] | 15.8 | 4.7 |
| Custom software / web / mobile | 1,117 | 734 | 25 [22, 29] | 16 | 4.9 | 262 [41, 737] | 26.6 | 175 [12, 542] | 21.0 | 7.1 |
| Cybersecurity | 390 | 194 | 193 [143, 263] | 168 | 19.7 | 476 [193, 999] | 37.4 | 441 [174, 901] | 36.2 | 11.4 |
| Education technology | 205 | 128 | 225 [147, 346] | 177 | 19.5 | 1,062 [196, 2,936] | 53.8 | 752 [100, 2,115] | 46.2 | 25.4 |
| Health information systems | 2,189 | 205 | 431 [405, 458] | 426 | 31.0 | 831 [692, 985] | 53.2 | 868 [737, 1,022] | 54.6 | 2.6 |
| Maintenance / support services | 626 | 297 | 82 [69, 98] | 66 | 10.7 | 299 [194, 473] | 24.3 | 300 [205, 456] | 23.7 | 5.6 |
| Network / data-centre infra. | 748 | 390 | 72 [60, 87] | 59 | 10.7 | 280 [151, 523] | 27.6 | 233 [127, 412] | 23.6 | 5.6 |
| Other IT | 277 | 215 | 79 [58, 111] | 43 | 10.1 | 757 [0, 2,278] | 46.0 | 594 [40, 1,917] | 36.3 | 19.2 |
| Physical security / surveillance | 385 | 222 | 84 [69, 104] | 58 | 10.4 | 212 [123, 373] | 20.4 | 208 [124, 340] | 20.0 | 4.9 |
| Smart city / traffic OT | 169 | 106 | 171 [125, 234] | 113 | 17.2 | 2,448 [483, 5,712] | 67.5 | 813 [0, 4,070] | 49.0 | 36.3 |
| Software licences | 1,047 | 375 | 103 [89, 118] | 94 | 13.5 | 274 [189, 436] | 24.7 | 275 [201, 377] | 25.3 | 5.2 |

Unbiased count HHI = Σ c(c−1)/(n(n−1)), removing the 1/n floor that inflates plug-in HHI in small markets. Plug-in HHI is biased upward under contract resampling (duplicated contracts), so CIs are bias-shifted percentile intervals. For value HHI in small, heavy-tailed markets (call centre, smart city, education technology, other IT) the bootstrap distribution is dominated by whether the one or two giant contracts are drawn; those CIs are very wide and mean 'poorly identified', not a precise range.

Table 1b. Influence and classification.

| category | HHI value | LOO min | LOO max | max abs LOO change (value) | max abs LOO change (count) | HHI winsorised [95% CI] | class count | class value | class w/o largest | class LOO-min | class winsorised | **robust class (min of all)** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| All categories pooled | 147 | 91 | 149 | 56 | 0.0 | 87 [75, 99] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| ERP / management software | 131 | 119 | 132 | 11 | 0.6 | 96 [73, 128] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| GIS / city information | 408 | 363 | 424 | 45 | 4.3 | 347 [249, 512] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Call centre / help-desk | 8,893 | 1,639 | 9,150 | 7,254 | 42.9 | 1,366 [426, 2,864] | below1000 (<1000) | above1800 (>1800) | between1000and1800 (1000-1800) | between1000and1800 (1000-1800) | between1000and1800 (1000-1800) | **below1000 (<1000)** |
| Computers / peripherals | 169 | 145 | 172 | 24 | 0.5 | 155 [75, 296] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Custom software / web / mobile | 262 | 175 | 269 | 87 | 0.2 | 110 [64, 195] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Cybersecurity | 476 | 441 | 499 | 35 | 4.4 | 341 [198, 512] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Education technology | 1,062 | 752 | 1,172 | 310 | 9.1 | 539 [203, 1,003] | below1000 (<1000) | between1000and1800 (1000-1800) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Health information systems | 831 | 803 | 868 | 37 | 0.4 | 812 [705, 923] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Maintenance / support services | 299 | 277 | 308 | 22 | 0.9 | 295 [203, 450] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Network / data-centre infra. | 280 | 233 | 288 | 47 | 0.8 | 226 [147, 332] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Other IT | 757 | 594 | 819 | 163 | 3.0 | 294 [99, 702] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Physical security / surveillance | 212 | 197 | 217 | 15 | 1.1 | 210 [123, 351] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Smart city / traffic OT | 2,448 | 813 | 2,901 | 1,635 | 5.4 | 581 [246, 1,162] | below1000 (<1000) | above1800 (>1800) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |
| Software licences | 274 | 263 | 279 | 11 | 0.8 | 269 [198, 348] | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | below1000 (<1000) | **below1000 (<1000)** |

Numbers-equivalent (10,000/HHI): All categories pooled 259 (count) / 68 (value); ERP / management software 120 (count) / 77 (value); GIS / city information 28 (count) / 25 (value); Call centre / help-desk 14 (count) / 1 (value); Computers / peripherals 250 (count) / 59 (value); Custom software / web / mobile 394 (count) / 38 (value); Cybersecurity 52 (count) / 21 (value); Education technology 44 (count) / 9 (value); Health information systems 23 (count) / 12 (value); Maintenance / support services 122 (count) / 33 (value); Network / data-centre infra. 139 (count) / 36 (value); Other IT 126 (count) / 13 (value); Physical security / surveillance 119 (count) / 47 (value); Smart city / traffic OT 58 (count) / 4 (value); Software licences 97 (count) / 37 (value).

## 1b. Supplier-side concentration by buyer sector (sektor_v3)

| sector | N | firms | HHI count [95% CI] | CR4 count | HHI value [95% CI] | CR4 value | HHI value w/o largest [95% CI] | LOO min | HHI winsorised | robust class |
|---|---|---|---|---|---|---|---|---|---|---|
| Health | 2,950 | 554 | 270 [253, 289] | 23.6 | 939 [357, 2,500] | 52.4 | 604 [333, 1,667] | 604 | 580 | below1000 (<1000) |
| Municipal/Local | 2,688 | 1,084 | 49 [43, 55] | 9.3 | 155 [62, 365] | 18.9 | 131 [70, 255] | 131 | 102 | below1000 (<1000) |
| Other public | 1,295 | 646 | 39 [34, 44] | 6.1 | 189 [106, 322] | 20.4 | 178 [105, 275] | 176 | 169 | below1000 (<1000) |
| Education | 1,054 | 519 | 76 [64, 89] | 12.0 | 181 [127, 260] | 19.0 | 171 [122, 236] | 171 | 179 | below1000 (<1000) |
| Infrastructure/Transport | 644 | 337 | 68 [57, 81] | 9.2 | 261 [114, 564] | 23.0 | 244 [112, 489] | 244 | 189 | below1000 (<1000) |
| Agriculture/Environment | 395 | 231 | 85 [68, 107] | 10.9 | 517 [232, 1,055] | 38.7 | 485 [221, 995] | 457 | 382 | below1000 (<1000) |
| Social/Finance | 303 | 156 | 129 [105, 159] | 13.9 | 493 [248, 863] | 35.8 | 510 [267, 883] | 454 | 463 | below1000 (<1000) |
| Provincial admin | 223 | 125 | 142 [112, 179] | 13.9 | 425 [227, 761] | 33.3 | 416 [241, 683] | 401 | 425 | below1000 (<1000) |
| Security/Interior | 202 | 142 | 104 [81, 135] | 11.4 | 358 [156, 753] | 30.0 | 349 [168, 690] | 329 | 349 | below1000 (<1000) |
| Defence | 191 | 96 | 209 [156, 281] | 18.8 | 938 [455, 1,720] | 44.5 | 1,026 [532, 1,867] | 747 | 905 | below1000 (<1000) |
| Justice | 46 | 32 | 378 [251, 554] | 23.9 | 1,986 [198, 4,727] | 69.8 | 1,634 [364, 4,347] | 1,634 | 857 | below1000 (<1000) |

## 2. Within-year HHI (market-years with ≥30 contracts)

Within a single year the CPI deflator is constant, so real-value and nominal-value HHI are identical.

| category | years | HHI count median [IQR] | HHI count unbiased, median | HHI value median [IQR] | HHI value w/o largest, median | years value HHI >1,800 | years value-w/o-largest HHI ≥1,000 | years count HHI >1,800 |
|---|---|---|---|---|---|---|---|---|
| All categories pooled | 17 | 69 [62-83] | 55 | 256 [210-309] | 209 | 2 | 0/17 | 0 |
| Custom software / web / mobile | 15 | 176 [163-196] | 37 | 740 [559-1,100] | 601 | 2 | 2/15 | 0 |
| ERP / management software | 15 | 226 [202-246] | 119 | 688 [549-940] | 521 | 0 | 0/15 | 0 |
| Computers / peripherals | 15 | 265 [245-309] | 44 | 903 [790-1,240] | 762 | 3 | 3/15 | 0 |
| Network / data-centre infra. | 15 | 274 [241-294] | 68 | 1,038 [932-1,457] | 937 | 2 | 4/15 | 0 |
| Software licences | 15 | 325 [276-414] | 187 | 998 [807-1,379] | 868 | 1 | 5/15 | 0 |
| Maintenance / support services | 14 | 343 [288-359] | 91 | 1,721 [1,070-1,855] | 1,238 | 6 | 8/14 | 0 |
| Cybersecurity | 7 | 416 [362-555] | 156 | 1,666 [1,412-2,443] | 1,263 | 3 | 4/7 | 0 |
| Physical security / surveillance | 4 | 427 [406-453] | 108 | 1,098 [881-1,258] | 926 | 0 | 2/4 | 0 |
| GIS / city information | 12 | 650 [575-766] | 369 | 1,503 [1,170-1,946] | 1,206 | 5 | 9/12 | 0 |
| Health information systems | 16 | 671 [519-722] | 597 | 1,091 [962-1,355] | 1,081 | 0 | 9/16 | 0 |

Markets with no year reaching 30 contracts (not computed): Call centre / help-desk, Education technology, Other IT, Smart city / traffic OT.

## 3. Buyer-side (demand) concentration

Buyer = `kurum_il_split` (primary); last two columns use recorded `kurum`.

| category | N | buyers | HHI count | CR4 count | HHI value | CR4 value | HHI value w/o largest | HHI count (kurum) | HHI value (kurum) |
|---|---|---|---|---|---|---|---|---|---|
| All categories pooled | 9,991 | 2,890 | 14 | 3.1 | 109 | 12.8 | 44 | 34 | 175 |
| ERP / management software | 1,515 | 770 | 27 | 4.1 | 146 | 17.0 | 120 | 33 | 147 |
| GIS / city information | 553 | 320 | 62 | 8.9 | 330 | 30.0 | 240 | 62 | 330 |
| Call centre / help-desk | 74 | 55 | 263 | 21.6 | 8,897 | 98.1 | 2,781 | 263 | 8,897 |
| Computers / peripherals | 696 | 415 | 55 | 8.9 | 215 | 22.8 | 170 | 111 | 236 |
| Custom software / web / mobile | 1,117 | 625 | 32 | 4.8 | 205 | 22.6 | 179 | 32 | 205 |
| Cybersecurity | 390 | 229 | 97 | 12.1 | 425 | 33.8 | 374 | 102 | 427 |
| Education technology | 205 | 124 | 199 | 21.0 | 1,293 | 60.9 | 847 | 202 | 1,293 |
| Health information systems | 2,189 | 935 | 22 | 3.0 | 84 | 13.1 | 70 | 197 | 1,226 |
| Maintenance / support services | 626 | 251 | 84 | 9.1 | 348 | 30.7 | 327 | 84 | 348 |
| Network / data-centre infra. | 748 | 420 | 53 | 8.6 | 196 | 18.9 | 167 | 64 | 208 |
| Other IT | 277 | 165 | 104 | 10.1 | 853 | 51.5 | 741 | 109 | 853 |
| Physical security / surveillance | 385 | 203 | 113 | 14.0 | 319 | 27.1 | 308 | 115 | 319 |
| Smart city / traffic OT | 169 | 111 | 167 | 17.8 | 1,702 | 67.4 | 947 | 167 | 1,702 |
| Software licences | 1,047 | 445 | 53 | 6.6 | 252 | 23.9 | 218 | 54 | 252 |

## 4. Why pooled HHI is diluted: decomposition

Let market s have weight w_s (share of total count or value) and firm i have within-market share s_is. Firm i's pooled share is s_i = Σ_s w_s s_is, so

  H_agg = Σ_i (Σ_s w_s s_is)² = Σ_s w_s² H_s + Σ_i Σ_{s≠t} w_s w_t s_is s_it.

The first term is the within-market part; because Σ_s w_s² < 1 (≈ 1/number of equally sized markets), even a set of highly concentrated markets yields a small pooled HHI unless the same firms lead several markets (the cross term, which is ≥0 and nonzero only for multi-market firms). Pooling is therefore mechanically dilutive; this is a relevant-market issue, not an empirical finding.

| partition | sample | weight | H_agg observed | Σ w_s² H_s | cross terms | Σ w_s² (×10⁴) | Σ w_s H_s (weighted mean within) | median H_s | % firms multi-market | % weight held by multi-market firms |
|---|---|---|---|---|---|---|---|---|---|---|
| urun_pazari | main | count | 38.6 | 26.7 | 11.9 | 1,165 | 179 | 93 | 25.4 | 68.9 |
| urun_pazari | main | real value | 147.2 | 126.7 | 20.5 | 1,081 | 1,269 | 353 | 25.4 | 67.8 |
| urun_pazari | main excl. MHRS | real value | 91.4 | 66.9 | 24.5 | 1,194 | 529 | 353 | 25.5 | 74.0 |
| sektor_v3 | main | count | 38.6 | 29.3 | 9.3 | 1,954 | 128 | 104 | 21.3 | 60.0 |
| sektor_v3 | main | real value | 147.2 | 128.6 | 18.7 | 2,011 | 526 | 425 | 21.3 | 62.0 |
| sektor_v3 | main excl. MHRS | real value | 91.4 | 69.1 | 22.3 | 1,790 | 392 | 425 | 21.3 | 67.6 |

(check: Σ w_s² H_s + cross terms equals H_agg to floating-point precision in every row.)

## 6. Count vs value firm rankings

| sample | firms | Spearman ρ (count, real value) | ρ, firms with ≥2 contracts | top-20 overlap | top-20-by-count share of value % | top-20-by-value share of value % | top-20-by-count share of contracts % | top-20-by-value share of contracts % |
|---|---|---|---|---|---|---|---|---|
| main | 2,814 | 0.639 (p=7.9e-323) | 0.680 (n=1,100) | 11/20 | 25.3 | 39.6 | 22.6 | 15.7 |
| main excl. MHRS | 2,813 | 0.640 (p=9.9e-324) | 0.680 (n=1,100) | 11/20 | 27.6 | 35.1 | 22.6 | 15.7 |

Top-20 firms by real value with their count rank: `top20_firms_by_value.csv`.

## 7. Sensitivities (point estimates, no bootstrap)

**HHI_count**

| category | main (firma_v3, real) | firm = original firma | include gray (broad) | nominal TRY | IT only (excl. call centre/MHRS) |
|---|---|---|---|---|---|
| All categories pooled | 39 | 24 | 31 | 39 | 39 |
| ERP / management software | 84 | 54 | 60 | 84 | 84 |
| GIS / city information | 353 | 321 | 349 | 353 | 353 |
| Call centre / help-desk | 690 | 420 | 592 | 690 | 884 |
| Computers / peripherals | 40 | 36 | 38 | 40 | 40 |
| Custom software / web / mobile | 25 | 22 | 25 | 25 | 25 |
| Cybersecurity | 193 | 164 | 191 | 193 | 193 |
| Education technology | 225 | 220 | 195 | 225 | 225 |
| Health information systems | 431 | 250 | 427 | 431 | 431 |
| Maintenance / support services | 82 | 54 | 73 | 82 | 82 |
| Network / data-centre infra. | 72 | 52 | 67 | 72 | 72 |
| Other IT | 79 | 70 | 67 | 79 | 79 |
| Physical security / surveillance | 84 | 72 | 105 | 84 | 84 |
| Smart city / traffic OT | 171 | 162 | 118 | 171 | 171 |
| Software licences | 103 | 70 | 103 | 103 | 103 |

**HHI_value**

| category | main (firma_v3, real) | firm = original firma | include gray (broad) | nominal TRY | IT only (excl. call centre/MHRS) |
|---|---|---|---|---|---|
| All categories pooled | 147 | 125 | 104 | 600 | 92 |
| ERP / management software | 131 | 99 | 100 | 285 | 131 |
| GIS / city information | 408 | 350 | 401 | 509 | 408 |
| Call centre / help-desk | 8,893 | 8,893 | 8,513 | 9,634 | 802 |
| Computers / peripherals | 169 | 159 | 220 | 235 | 169 |
| Custom software / web / mobile | 262 | 257 | 259 | 477 | 262 |
| Cybersecurity | 476 | 455 | 475 | 956 | 476 |
| Education technology | 1,062 | 1,061 | 936 | 2,414 | 1,062 |
| Health information systems | 831 | 593 | 817 | 1,060 | 831 |
| Maintenance / support services | 299 | 201 | 272 | 589 | 299 |
| Network / data-centre infra. | 280 | 194 | 1,700 | 405 | 280 |
| Other IT | 757 | 757 | 608 | 505 | 757 |
| Physical security / surveillance | 212 | 192 | 184 | 307 | 212 |
| Smart city / traffic OT | 2,448 | 2,072 | 1,759 | 1,002 | 2,448 |
| Software licences | 274 | 215 | 274 | 487 | 274 |

**HHI_value_nomax**

| category | main (firma_v3, real) | firm = original firma | include gray (broad) | nominal TRY | IT only (excl. call centre/MHRS) |
|---|---|---|---|---|---|
| All categories pooled | 91 | 65 | 77 | 147 | 91 |
| ERP / management software | 119 | 98 | 91 | 222 | 119 |
| GIS / city information | 385 | 315 | 378 | 536 | 385 |
| Call centre / help-desk | 1,639 | 1,620 | 1,066 | 1,685 | 788 |
| Computers / peripherals | 145 | 134 | 164 | 236 | 145 |
| Custom software / web / mobile | 175 | 169 | 172 | 323 | 175 |
| Cybersecurity | 441 | 415 | 440 | 791 | 441 |
| Education technology | 752 | 750 | 660 | 1,889 | 752 |
| Health information systems | 868 | 618 | 853 | 978 | 868 |
| Maintenance / support services | 300 | 190 | 272 | 603 | 300 |
| Network / data-centre infra. | 233 | 172 | 495 | 347 | 233 |
| Other IT | 594 | 593 | 462 | 296 | 594 |
| Physical security / surveillance | 208 | 185 | 186 | 313 | 208 |
| Smart city / traffic OT | 813 | 664 | 726 | 420 | 813 |
| Software licences | 275 | 210 | 275 | 431 | 275 |

**LOO_value_min**

| category | main (firma_v3, real) | firm = original firma | include gray (broad) | nominal TRY | IT only (excl. call centre/MHRS) |
|---|---|---|---|---|---|
| All categories pooled | 91 | 65 | 77 | 147 | 89 |
| ERP / management software | 119 | 94 | 91 | 222 | 119 |
| GIS / city information | 363 | 315 | 357 | 451 | 363 |
| Call centre / help-desk | 1,639 | 1,620 | 1,066 | 1,685 | 787 |
| Computers / peripherals | 145 | 134 | 164 | 213 | 145 |
| Custom software / web / mobile | 175 | 169 | 172 | 323 | 175 |
| Cybersecurity | 441 | 415 | 440 | 791 | 441 |
| Education technology | 752 | 750 | 660 | 1,889 | 752 |
| Health information systems | 803 | 555 | 789 | 978 | 803 |
| Maintenance / support services | 277 | 190 | 252 | 548 | 277 |
| Network / data-centre infra. | 233 | 172 | 495 | 347 | 233 |
| Other IT | 594 | 593 | 462 | 296 | 594 |
| Physical security / surveillance | 197 | 175 | 179 | 275 | 197 |
| Smart city / traffic OT | 813 | 664 | 726 | 420 | 813 |
| Software licences | 263 | 203 | 263 | 431 | 263 |

Robust class under each sensitivity (min of count, value, value w/o largest, LOO-min, winsorised):

| category | main (firma_v3, real) | firm = original firma | include gray (broad) | nominal TRY | IT only (excl. call centre/MHRS) |
|---|---|---|---|---|---|
| All categories pooled | 39 (below1000) | 24 (below1000) | 31 (below1000) | 39 (below1000) | 39 (below1000) |
| ERP / management software | 84 (below1000) | 54 (below1000) | 60 (below1000) | 84 (below1000) | 84 (below1000) |
| GIS / city information | 347 (below1000) | 288 (below1000) | 349 (below1000) | 353 (below1000) | 347 (below1000) |
| Call centre / help-desk | 690 (below1000) | 420 (below1000) | 592 (below1000) | 690 (below1000) | 787 (below1000) |
| Computers / peripherals | 40 (below1000) | 36 (below1000) | 38 (below1000) | 40 (below1000) | 40 (below1000) |
| Custom software / web / mobile | 25 (below1000) | 22 (below1000) | 25 (below1000) | 25 (below1000) | 25 (below1000) |
| Cybersecurity | 193 (below1000) | 164 (below1000) | 191 (below1000) | 193 (below1000) | 193 (below1000) |
| Education technology | 225 (below1000) | 220 (below1000) | 195 (below1000) | 225 (below1000) | 225 (below1000) |
| Health information systems | 431 (below1000) | 250 (below1000) | 427 (below1000) | 431 (below1000) | 431 (below1000) |
| Maintenance / support services | 82 (below1000) | 54 (below1000) | 73 (below1000) | 82 (below1000) | 82 (below1000) |
| Network / data-centre infra. | 72 (below1000) | 52 (below1000) | 67 (below1000) | 72 (below1000) | 72 (below1000) |
| Other IT | 79 (below1000) | 70 (below1000) | 67 (below1000) | 79 (below1000) | 79 (below1000) |
| Physical security / surveillance | 84 (below1000) | 72 (below1000) | 105 (below1000) | 84 (below1000) | 84 (below1000) |
| Smart city / traffic OT | 171 (below1000) | 162 (below1000) | 118 (below1000) | 171 (below1000) | 171 (below1000) |
| Software licences | 103 (below1000) | 70 (below1000) | 103 (below1000) | 103 (below1000) | 103 (below1000) |

'IT only' drops all 10 call-centre contracts (incl. MHRS); the call-centre market then contains only the 64 IT-scope call-centre software/equipment contracts.

## Files

- `results/concentration/buyer_hhi_by_market.csv`
- `results/concentration/count_vs_value_rankings.csv`
- `results/concentration/hhi_decomposition.csv`
- `results/concentration/sensitivity_by_market.csv`
- `results/concentration/supplier_hhi_by_market.csv`
- `results/concentration/supplier_hhi_by_sector.csv`
- `results/concentration/top20_firms_by_value.csv`
- `results/concentration/within_year_hhi.csv`
- `results/concentration/within_year_hhi_summary.csv`
- `figures/F-C1_concentration_by_market.png/.pdf` - dot plot: count HHI, real-value HHI, value HHI without largest contract, bootstrap 95% CIs, thresholds 1,000/1,800 (log x).
- `figures/F-C2_within_year_hhi.png/.pdf` - within-year HHI by category (box + strip; count left, real value right).