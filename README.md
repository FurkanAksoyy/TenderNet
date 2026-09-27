# TenderNet v1.1.0 — reproducibility package

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22994070.svg)](https://doi.org/10.5281/zenodo.22994070)

**Status (27 September 2026):** v1.1.0 contains the revised manuscript, code, derived data and results. Both authors have approved the manuscript for submission; independent human classification validation remains outstanding and is disclosed. The exact release is https://github.com/FurkanAksoyy/TenderNet/releases/tag/v1.1.0. The DOI above is the version-spanning Zenodo concept DOI; cite the record explicitly labelled v1.1.0 for this revision. The previous v1.0.1 archive has the version-specific DOI 10.5281/zenodo.22997485.


Data and code for

> Aksoy, F. and Şimşek, A. (2026). **Dispersed awards, persistent ties: evidence from Türkiye's public IT
> procurement.** Manuscript prepared for submission to the *Journal of Industrial and Business Economics* (JIBE, Springer).

We study 9,991 awarded information-technology contracts published on Türkiye's e-procurement platform EKAP
(2010–2026), linking 2,814 firms to 2,890 public buyers. Count-based supplier HHIs are below the historical 1,000 reference in every title-based product
category. Buyers return to incumbent suppliers more often than the specified permutation benchmarks: 45.2% of
repeat-eligible contracts go to an incumbent, against 6.2% under a permutation null within product category and year
and 20.7% under a null that also fixes the province. About a third of these contracts (1,743 of 4,913) are classified by title similarity and timing as title-flagged recurring purchases (not verified legal renewals); they carry most of the excess (72.0% vs 28.8% under the province null), but other purchases still exceed their null (30.5% vs 16.3%). In a conditional-logit supplier-choice model among firms active in the
same title-based product category in the 24 months before each tender, prior supply to the buyer is associated
with winning (OR 42.3, 95% CI 36.4–49.2; 3,013 contracts). An outcome-derived future-tie diagnostic cautions against a causal
interpretation: these observational diagnostics do not identify state dependence, stable matching, or their
relative contributions. Incumbency associations are especially pronounced in health IT and under Article 21(b)
negotiated procedures. Changes around 2018 are descriptive policy-timing associations; bid-count associations
are not measures of harm or efficiency. Title categories are not antitrust relevant markets.


## Repository structure

```
run_all.py              runs the whole pipeline in order (see below)
requirements.txt        pinned Python packages (tested with Python 3.13.2, Windows 11)
data/                   release dataset + data dictionary (data/README.md) + CPI series; CC BY 4.0
  contracts_v3.csv        13,024 contracts (9,991 in the main sample), natural persons pseudonymized
  firm_name_map_v3.csv    firm-name canonicalization map (pseudonymized)
  bid_counts_sample.csv   year-stratified sample of tenders with bid counts
  bid_counts_cp2.csv      bid counts for 3,400 tenders (second scrape; no firm names)
  fx_rates_tcmb.csv       TCMB source URLs, hashes, buying/selling rates and tender-date conversion proxies
  fx_cache_tcmb/          cached official daily XML (offline reproduction)
  cpi_turkey*.csv         TÜİK CPI used to deflate to 2025 TRY
  ppi_turkey_yiufe.csv    TÜİK producer price index (deflator robustness)
  ekap_detail_sample.csv  estimated cost, contract value and bids for 144 sampled tenders (no names)
  audit/                  hand review of the top-150 contracts, rule samples, classifier validation, build log
    ai_coding/            blind inputs and labels of two separately run AI coders (markets, renewals)
docs/law_notes.md       notes on Law 4734 Art. 21, Law 7144 and KHK 694
docs/estimated_cost_collection.md   how the estimated-cost sample was collected
src/                    analysis scripts (read data/, write results/, figures/, paper/si_tables/)
  build/                  raw-data build scripts (private inputs) and runnable offline currency normalization
results/                machine-readable outputs (CSV/JSON) and written reports (*_results.md) per topic
figures/                all figures, PNG (300 dpi) and PDF
paper/                  LaTeX sources, bibliography, SI tables, figures and compiled PDFs
```

## How to run

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py --skip-slow    # ~11 min: skips revision_d (~76 min) and the network nulls (~30 min)
python run_all.py                # full run, about 2 hours
python run_all.py --only lockin  # a single step
python src/build/normalize_currency.py  # independently reproduce currency fields offline
python src/revision_e_currency.py       # unknown-currency sensitivity and corrected top-150 screen
python -m unittest discover -s src/build -p test_currency_values.py
```

`--skip-slow` also skips the 300-draw initialization sensitivity. It skips `revision_d.py` (simulated worlds: 100 replications per world plus calibration) and
`network_analysis.py` (200 curveball randomizations, 50 Louvain stability runs, annual and sensitivity nulls);
later steps and the headline check then use the committed `results/revision_d/` and `results/network/` files. Each step logs to
`results/logs/<step>.log`. The final step, `src/check_headlines.py`, compares regenerated results with manually transcribed manuscript checkpoints and fails outside stated tolerances. It does not parse the manuscript or validate every claim. All random procedures use fixed seeds (42 and seed lists documented in the
scripts), with numerical reproducibility checked to the tolerances in the headline checker; floating-point libraries and platform differences can affect last digits.

The authoritative step list is `run_all.py`. Revision-E steps add taxonomy/history, bounded horizons, currency exclusion, sampling provenance, numerical-fit auditing, and initialization sensitivity. `refresh_paper_assets.py` refreshes labels and copies current figures to the paper.

The original analysis order starts with offline `build/normalize_currency.py`, followed by `concentration_v3.py` → `lockin_analysis.py` → `models_analysis.py` → `models_report.py` →
`models_figures.py` → `revision_a.py` → `revision_b.py` → `revision_c.py` → `revision_d.py` (slow) → `price_analysis.py` → `coder_agreement.py` →
`network_analysis.py` (slow) → `network_projections.py` → `network_figures.py` →
`make_si_tables.py` → `check_headlines.py`. `results/network/fig_N1_hub_labels.csv` is a hand-made input (short
hub labels for the supplementary network figure), not an output.

Paper: `cd paper && pdflatex tendernet_jibe && bibtex tendernet_jibe && pdflatex tendernet_jibe && pdflatex tendernet_jibe`
(Springer Nature `sn-jnl` class and `sn-apacite.bst` included); the SI is `tendernet_si.tex` (pdflatex twice);
`title_page.tex` is the separate title page and `cover_letter_JIBE.md` the cover letter.
`paper/figures/` holds copies of the PDF figures in `figures/`. Helpers: `src/wordcount.py` (manuscript word
count), `src/abstract_count.py` (abstract word count), `src/merge_bib.py` (rebuilds `paper/refs.bib` from
`paper/bib_src/`).

Human validation is outstanding. The prospective protocol and a codebook draft are in `docs/human_validation_protocol.md` and `docs/human_coding_codebook_draft.md`; blank inputs are `data/audit/ai_coding/blind_*_input.csv`. Existing result-report prose may retain legacy terminology; the revised manuscript and explicit scenario documentation govern interpretation.

## Where each result comes from

| paper item | content | script | output |
|---|---|---|---|
| Table 1 | main-sample descriptives | `concentration_v3.py`, `lockin_analysis.py` | `results/concentration/concentration_results.md`, `results/lockin/lockin_log.json` |
| Table 2 | product markets (contracts, eligible contracts, firms, buyers, value, procedure shares) | `revision_b.py` | `results/revision_b/B5_descriptives.csv` |
| Table 3 | incumbency vs nulls N1–N4b, title-flagged recurring / other purchases | `lockin_analysis.py`, `revision_a.py`, `revision_c.py` | `results/lockin/null_overall.csv`, `results/revision_a/B_null_*.csv`, `results/revision_c/C3_N4prior_*.csv` |
| Table 4 | conditional logit of who wins (24-month pre-tender pools), outcome-derived future-tie diagnostic, last vs earlier supplier | `revision_c.py` | `results/revision_c/C1_C2_clogit_results.csv` |
| Figure 1 | supplier HHI by product market | `concentration_v3.py` | `figures/F-C1_concentration_by_market.*`, `results/concentration/supplier_hhi_by_market.csv` |
| Figure 2 | incumbency by product market vs null N3 | `revision_d.py` | `figures/F-L1b_incumbency_by_market_N3.*`, `results/revision_d/D7_market_N3.csv` |
| Figure 3 | incumbency by days since previous contract, title-flagged recurring vs other purchases | `revision_a.py` | `figures/F-A1_incumbency_by_gap_renewal.*`, `results/revision_a/A_fig_A1_data.csv` |
| SI simulation figure | observed choice-model moments vs conditional algorithmic scenarios | `revision_d.py` | `figures/F-D1_three_worlds.*`, `results/revision_d/D3_three_worlds.csv` |
| Figure 4 | single-bid rates | `models_analysis.py`, `models_figures.py` | `figures/F-R2_single_bid.*`, `results/models/D_single_bid_rates.csv` |
| text | 21(b) × post-2018 logit (OR 2.42) and variants | `models_analysis.py`, `revision_b.py` | `results/models/A1_logit_incumbency.csv`, `results/revision_b/B1_controls_clustering.csv` |
| text | single bids in the larger cp2 sample (OR 2.04) | `revision_a.py` | `results/revision_a/F_single_bid_logit.csv`, `F_single_bid_rates.csv` |
| text | buyer-level tests with Benjamini–Hochberg | `revision_a.py` | `results/revision_a/E_buyer_BH.csv` |
| Table 3 / text | nulls N4, N4b with prior modal award province | `revision_c.py` | `results/revision_c/C3_N4prior_overall.csv`, `C3_N4prior_by_renewal.csv` |
| text | single bids with renewal controls; 21(b) × post × health triple interaction | `revision_c.py` | `results/revision_c/C5_single_bid_*.csv`, `revision_c_log.json` |
| SI: scope classes | | `make_si_tables.py` | `paper/si_tables/scope.tex` |
| SI: buyer sectors | | `revision_b.py` | `results/revision_b/B5_descriptives.csv` |
| SI: concentration, within-year HHI, PPI deflator | | `concentration_v3.py`, `revision_b.py` → `make_si_tables.py` | `paper/si_tables/concentration.tex`, `within_year.tex`, `results/revision_b/B6_hhi_cpi_vs_ppi.csv` |
| SI: incumbency by market / sector / buyer type / procedure / year, sensitivity; figures incumbency by year and buyers' top-supplier share | | `lockin_analysis.py` → `make_si_tables.py` | `paper/si_tables/lockin_*.tex`, `sensitivity.tex`, `figures/F_L2_*`, `figures/F_L3_*` |
| SI: renewals, N4 nulls, lots/framework check, natural-person exclusion | | `revision_a.py` (+ `revision_a_titles.py`) | `results/revision_a/B_null_*.csv`, `A_renewal_*.csv`, `C_multilot_framework_titles.csv` |
| SI: supplier choice and state dependence (pool sizes, 12/24-month windows, subgroups, placebo, simulation) | | `revision_c.py` | `results/revision_c/C1_*.csv`, `C2_*.csv` |
| SI: named-product licences and maintenance (exclusivity flags) | | `revision_c.py` | `results/revision_c/C4_exclusivity_nulls.csv`, `C4_strict_flagged_titles.csv` |
| SI (superseded model, kept for transparency) | first choice model with sampled alternatives | `revision_a.py` | `results/revision_a/D_clogit_results.csv` |
| SI: contract-level model, event study (Fig. F-B1), Art. 21(f) limits, buyer size | | `revision_b.py` | `figures/F-B1_event_study_21b.*`, `results/revision_b/B1_*.csv` … `B4_*.csv` |
| SI: simulated worlds, calibration, mixture frontier, firm controls and lags, recency vs count | | `revision_d.py` | `results/revision_d/D*.csv`, `revision_d_results.md` |
| SI: estimated costs and discounts | | `price_analysis.py` | `results/price/price_results.md`, `price_sample_analysis.csv` |
| SI: AI agreement audit of title coding by two blind AI coders (markets, renewals) | | `coder_agreement.py` | `results/coder_agreement/coder_agreement_results.md` |
| SI: dyad continuation (logit, NB2) | | `models_analysis.py` → `make_si_tables.py` | `paper/si_tables/B_*.tex` |
| SI: single-bid rates | | `models_analysis.py` → `make_si_tables.py` | `paper/si_tables/single_bid.tex` |
| SI: network structure (core network figure, nulls, projections, brokerage) | | `network_analysis.py`, `network_projections.py`, `network_figures.py` | `figures/fig_N1_core_network.*`, `results/network/*` |

`F-C2`, `F-R1`, `F_L1`, `fig_N2` and `fig_N3` are produced for completeness and are not in the paper. Reports with every
number that could go in the paper: `results/*/*_results.md` (the `lockin`, `models` and `revision_a` reports were
written by hand from the outputs; the others are generated). `results/revision_a/A_renewal_validation_labels.csv`
contains earlier AI-assisted title-pair labels; it is not a completed independent human validation. `results/revision_a/D_choice_data.csv.gz` and
`results/revision_c/C1_choice_data_24m_poolall.csv.gz` are choice-model data with integer codes only (the latter
without firm codes). `src/make_human_coding_sheets.py` writes Excel sheets for human validation coding into
`human_coding/` (not tracked; needs `openpyxl`).

## Currency correction and source validity

The archived release treated 76 explicitly USD/EUR amounts as TRY. This revision preserves `bedel` and legacy `bedel_num`, adds parsed original amount and currency fields, and uses `bedel_try` in value-based analyses. Official TCMB tender-date buying/selling midpoint rates (per unit) give a valuation proxy; the latest available weekday within seven calendar days is used only when that day's XML is absent. Cached XML and SHA-256 checks allow offline reproduction. This is not a payment-rate reconstruction.

The main sample contains 54 USD and 13 EUR records; **845 main-sample currency labels are missing** and are explicitly assumed TRY (1,291 across all data). `bedel_currency_status` records that assumption; an explicit label denotes what the source string says, not independent source verification. The separate sensitivity removes those 845 observations from value summaries and model estimation while preserving their observed relationship histories. See `docs/currency_normalization.md` and `results/revision_e_currency/currency_results.md`.

The historical top-150 hand-review file remains an archived review ranked by the mixed-currency legacy numeric amount. The corrected nominal-TRY screen reports historical review membership separately from new reviews needed. It must not be described as newly hand-validated. Title classifications and named-product flags are proxies; automated coder agreement does not establish legal exclusivity or ground truth. See `docs/human_validation_protocol.md` for the pending independent validation design.

## Data provenance

The underlying records are award results of Turkish public tenders, published by the Public Procurement
Authority (Kamu İhale Kurumu, KİK) on EKAP (<https://ekapv2.kik.gov.tr>) under Public Procurement Law No. 4734.
We retrieved them with IT domain keywords (13,418 records with an identifiable winner), audited the IT scope by
contract value, canonicalized firm names, split pooled buyer labels by province and classified product markets
(details: `data/README.md`, `data/audit/`). Bid counts come from the published result announcements of a
year-stratified random sample of tenders (`bid_counts_sample.csv`) and from a second scrape of 3,400 tenders
(`bid_counts_cp2.csv`: IKN, year, search keyword, number of bids, and whether a winner was listed; winner and
bidder names of the raw scrape are dropped). CPI and PPI: TÜİK (sources in `data/cpi_turkey_SOURCES.txt`, `data/ppi_turkey_SOURCES.txt`).

`src/build/` contains the scripts that built the dataset (`build_master_v3.py`, `rules_v3.py`,
`manual_scope_overrides.csv`, `firm_merge_groups_v3.csv`) and the pseudonymization step (`make_release_data.py`).
Those raw-data reconstruction scripts cannot be run from this repository because they need the raw scrape, which we do not redistribute: the raw
records contain the names of natural persons (sole proprietors and individuals who won contracts). These records
are public on EKAP, but we do not re-publish personal names. The scripts are included so that every rule and
manual decision can be inspected.

## Privacy

In accordance with the Turkish Personal Data Protection Law (KVKK, No. 6698), supplier names that may identify
a natural person are replaced by stable pseudonyms (`PSEUDONYM_nnn`) in every firm-name column: 690 of 4,389 firms
(1,113 of 13,024 contracts), including all 536 winners flagged as natural persons and, conservatively, every name
without an explicit legal-entity form. The replacement is one-to-one, so all results are identical to those on
the internal data: every result table of the concentration, lock-in, model and revision steps is byte-identical
(apart from the rehashed `firm_id` column). The network step is seeded, but Louvain partitions and curveball
nulls depend on node order, and pseudonyms sort differently from the original names; its outputs therefore
differ from the internal run in the third decimal (e.g. weighted giant-component modularity 0.761 vs 0.762,
34–43 vs 36–43 communities across 50 Louvain runs). All network numbers in the main text are unchanged at
the reported precision. The committed `results/network/` files come from the released data. The simulated-worlds step (`revision_d.py`, ~77 min) was also re-run on the released data; its result tables are numerically identical to the internal run.
Legal-entity and public-buyer names are kept. Please do not attempt to re-identify pseudonymized suppliers.
Details: `data/README.md`.

## License

- Code: MIT License (`LICENSE`).
- Data in `data/`: CC BY 4.0 (`data/LICENSE`). The license covers the authors' derived compilation; the
  underlying facts are public records published by KİK under Law 4734. Please attribute KİK/EKAP as the source
  of the underlying records.

## Citation

The following citation identifies archived v1.0.1, not the unreleased working-tree revision (see `CITATION.cff`):

> Aksoy, F. and Şimşek, A. (2026). TenderNet v1.0.1: data and code for "Unconcentrated markets, persistent ties:
> incumbency in Türkiye's public IT procurement" (Version 1.0.1) [Software and data]. Zenodo.
> https://doi.org/10.5281/zenodo.22994070

Contact: Furkan Aksoy (corresponding author), Department of Software Engineering, Maltepe University, Istanbul,
ORCID [0009-0000-0228-8202](https://orcid.org/0009-0000-0228-8202). Arda Şimşek, ORCID
[0009-0000-7969-6351](https://orcid.org/0009-0000-7969-6351).
