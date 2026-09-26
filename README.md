# TenderNet v1.0.0 — reproducibility package

Data and code for

> Aksoy, F. and Şimşek, A. (2026). **Unconcentrated markets, persistent ties: incumbency in Türkiye's public IT
> procurement.** Manuscript prepared for submission to the *Journal of Industrial and Business Economics* (JIBE, Springer).

We study 9,991 awarded information-technology contracts published on Türkiye's e-procurement platform EKAP
(2010–2026), linking 2,814 firms to 2,890 public buyers. Count-based supplier HHIs are below 1,000 in every product
market, yet buyers return to incumbent suppliers far more often than market structure implies: 45.2% of
repeat-eligible contracts go to an incumbent, against 6.2% under a permutation null within product market and year
and 20.7% under a null that also fixes the province. About a third of these contracts (1,743 of 4,913) are annual
re-tenders of the same service; they carry most of the excess (72.0% vs 28.8% under the province null), but new
needs still exceed their null (30.5% vs 16.3%). In a conditional-logit supplier-choice model among firms active in the
market in the 24 months before each tender, prior supply to the buyer raises a firm's odds of winning about 40-fold
(OR 42.3, 95% CI 36.4–49.2; 3,013 contracts). A future-supplier placebo (OR 54.4 for firms that supply the buyer
only later, against 19.8 expected under pure state dependence) indicates that much of the persistence reflects
stable buyer–firm matching, with state dependence clearest in renewals. Incumbency is highest in health IT and under Article 21(b) negotiated procedures, where the
21(b)–open gap jumped by 37 percentage points in 2018 relative to 2013–17, and incumbent-won tenders attract single
bids more often (OR 2.04).

## Repository structure

```
run_all.py              runs the whole pipeline in order (see below)
requirements.txt        pinned Python packages (tested with Python 3.13.2, Windows 11)
data/                   release dataset + data dictionary (data/README.md) + CPI series; CC BY 4.0
  contracts_v3.csv        13,024 contracts (9,991 in the main sample), natural persons pseudonymized
  firm_name_map_v3.csv    firm-name canonicalization map (pseudonymized)
  bid_counts_sample.csv   year-stratified sample of tenders with bid counts
  bid_counts_cp2.csv      bid counts for 3,400 tenders (second scrape; no firm names)
  cpi_turkey*.csv         TÜİK CPI used to deflate to 2025 TRY
  ppi_turkey_yiufe.csv    TÜİK producer price index (deflator robustness)
  audit/                  hand review of the top-150 contracts, rule samples, classifier validation, build log
docs/law_notes.md       notes on Law 4734 Art. 21, Law 7144 and KHK 694
src/                    analysis scripts (read data/, write results/, figures/, paper/si_tables/)
  build/                  scripts that built the data from the raw scrape (not runnable here, see below)
results/                machine-readable outputs (CSV/JSON) and written reports (*_results.md) per topic
figures/                all figures, PNG (300 dpi) and PDF
paper/                  LaTeX sources, bibliography, SI tables, figures and compiled PDFs
```

## How to run

```bash
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py --skip-slow    # ~10 min: everything except the network null models
python run_all.py                # full run, ~40 min (network_analysis.py alone takes ~30 min)
python run_all.py --only lockin  # a single step
```

`--skip-slow` skips `network_analysis.py` (200 curveball randomizations, 50 Louvain stability runs, annual and
sensitivity nulls); the later network steps then reuse the committed `results/network/` files. Each step logs to
`results/logs/<step>.log`. The final step, `src/check_headlines.py`, compares the regenerated numbers with the
paper and fails if any differs. All random procedures use fixed seeds (42 and seed lists documented in the
scripts), so results are exactly reproducible.

Pipeline order: `concentration_v3.py` → `lockin_analysis.py` → `models_analysis.py` → `models_report.py` →
`models_figures.py` → `revision_a.py` → `revision_b.py` → `revision_c.py` → `network_analysis.py` (slow) → `network_projections.py` → `network_figures.py` →
`make_si_tables.py` → `check_headlines.py`. `results/network/fig_N1_hub_labels.csv` is a hand-made input (short
hub labels for Figure 6), not an output.

Paper: `cd paper && pdflatex tendernet_jibe && bibtex tendernet_jibe && pdflatex tendernet_jibe && pdflatex tendernet_jibe`
(Springer Nature `sn-jnl` class and `sn-apacite.bst` included); the SI is `tendernet_si.tex` (pdflatex twice);
`title_page.tex` is the separate title page and `cover_letter_JIBE.md` the cover letter.
`paper/figures/` holds copies of the PDF figures in `figures/`. Helpers: `src/wordcount.py` (manuscript word
count), `src/abstract_count.py` (abstract word count), `src/merge_bib.py` (rebuilds `paper/refs.bib` from
`paper/bib_src/`).

## Where each result comes from

| paper item | content | script | output |
|---|---|---|---|
| Table 1 | main-sample descriptives | `concentration_v3.py`, `lockin_analysis.py` | `results/concentration/concentration_results.md`, `results/lockin/lockin_log.json` |
| Table 2 | product markets (contracts, firms, buyers, value, procedure shares) | `revision_b.py` | `results/revision_b/B5_descriptives.csv` |
| Table 3 | incumbency vs nulls N1–N3, N4 (home province), renewals / new needs | `lockin_analysis.py`, `revision_a.py` | `results/lockin/null_overall.csv`, `results/revision_a/B_null_overall.csv`, `B_null_by_group.csv` |
| Table 4 | conditional logit of supplier choice (24-month pre-tender pools), future-supplier placebo, last vs earlier supplier | `revision_c.py` | `results/revision_c/C1_C2_clogit_results.csv`, `C2_placebo_simulation.csv` |
| Figure 1 | supplier HHI by product market | `concentration_v3.py` | `figures/F-C1_concentration_by_market.*`, `results/concentration/supplier_hhi_by_market.csv` |
| Figure 2 | incumbency by product market | `lockin_analysis.py` | `figures/F_L1_incumbency_by_market.*`, `results/lockin/null_by_group.csv` |
| Figure 3 | incumbency by days since previous contract, renewals vs new needs | `revision_a.py` | `figures/F-A1_incumbency_by_gap_renewal.*`, `results/revision_a/A_fig_A1_data.csv` |
| Figure 4 | event study: 21(b)–open incumbency gap by year | `revision_b.py` | `figures/F-B1_event_study_21b.*`, `results/revision_b/B2_event_study.csv` |
| Figure 5 | single-bid rates | `models_analysis.py`, `models_figures.py` | `figures/F-R2_single_bid.*`, `results/models/D_single_bid_rates.csv` |
| text | 21(b) × post-2018 logit (OR 2.42) and variants | `models_analysis.py`, `revision_b.py` | `results/models/A1_logit_incumbency.csv`, `results/revision_b/B1_controls_clustering.csv` |
| text | single bids in the larger cp2 sample (OR 2.04) | `revision_a.py` | `results/revision_a/F_single_bid_logit.csv`, `F_single_bid_rates.csv` |
| text | buyer-level tests with Benjamini–Hochberg | `revision_a.py` | `results/revision_a/E_buyer_BH.csv` |
| Table 3 / text | nulls N4, N4b with home province from prior wins | `revision_c.py` | `results/revision_c/C3_N4prior_overall.csv`, `C3_N4prior_by_renewal.csv` |
| text | single bids with renewal controls; 21(b) × post × health triple interaction | `revision_c.py` | `results/revision_c/C5_single_bid_*.csv`, `revision_c_log.json` |
| SI: scope classes | | `make_si_tables.py` | `paper/si_tables/scope.tex` |
| SI: buyer sectors | | `revision_b.py` | `results/revision_b/B5_descriptives.csv` |
| SI: concentration, within-year HHI, PPI deflator | | `concentration_v3.py`, `revision_b.py` → `make_si_tables.py` | `paper/si_tables/concentration.tex`, `within_year.tex`, `results/revision_b/B6_hhi_cpi_vs_ppi.csv` |
| SI: incumbency by market / sector / buyer type / procedure / year, sensitivity; figures incumbency by year and buyers' top-supplier share | | `lockin_analysis.py` → `make_si_tables.py` | `paper/si_tables/lockin_*.tex`, `sensitivity.tex`, `figures/F_L2_*`, `figures/F_L3_*` |
| SI: renewals, N4 nulls, lots/framework check, natural-person exclusion | | `revision_a.py` (+ `revision_a_titles.py`) | `results/revision_a/B_null_*.csv`, `A_renewal_*.csv`, `C_multilot_framework_titles.csv` |
| SI: supplier choice and state dependence (pool sizes, 12/24-month windows, subgroups, placebo, simulation) | | `revision_c.py` | `results/revision_c/C1_*.csv`, `C2_*.csv` |
| SI: named-product licences and maintenance (exclusivity flags) | | `revision_c.py` | `results/revision_c/C4_exclusivity_nulls.csv`, `C4_strict_flagged_titles.csv` |
| SI (superseded model, kept for transparency) | first choice model with sampled alternatives | `revision_a.py` | `results/revision_a/D_clogit_results.csv` |
| SI: contract-level model, event study, Art. 21(f) limits, buyer size | | `revision_b.py` | `results/revision_b/B1_*.csv` … `B4_*.csv` |
| SI: dyad continuation (logit, NB2) | | `models_analysis.py` → `make_si_tables.py` | `paper/si_tables/B_*.tex` |
| SI: single-bid rates | | `models_analysis.py` → `make_si_tables.py` | `paper/si_tables/single_bid.tex` |
| SI: network structure (core network figure, nulls, projections, brokerage) | | `network_analysis.py`, `network_projections.py`, `network_figures.py` | `figures/fig_N1_core_network.*`, `results/network/*` |

`F-C2`, `F-R1`, `fig_N2` and `fig_N3` are produced for completeness and are not in the paper. Reports with every
number that could go in the paper: `results/*/*_results.md` (the `lockin`, `models` and `revision_a` reports were
written by hand from the outputs; the others are generated). `results/revision_a/A_renewal_validation_labels.csv`
is the hand-coded validation of the renewal rule (titles only). `results/revision_a/D_choice_data.csv.gz` and
`results/revision_c/C1_choice_data_24m_poolall.csv.gz` are choice-model data with integer codes only (the latter
without firm codes). `src/make_human_coding_sheets.py` writes Excel sheets for human validation coding into
`human_coding/` (not tracked; needs `openpyxl`).

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
They cannot be run from this repository because they need the raw scrape, which we do not redistribute: the raw
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
the reported precision. The committed `results/network/` files come from the released data.
Legal-entity and public-buyer names are kept. Please do not attempt to re-identify pseudonymized suppliers.
Details: `data/README.md`.

## License

- Code: MIT License (`LICENSE`).
- Data in `data/`: CC BY 4.0 (`data/LICENSE`). The license covers the authors' derived compilation; the
  underlying facts are public records published by KİK under Law 4734. Please attribute KİK/EKAP as the source
  of the underlying records.

## Citation

Please cite the paper and this package (see `CITATION.cff`):

> Aksoy, F. and Şimşek, A. (2026). TenderNet v1.0.0: data and code for "Unconcentrated markets, persistent ties:
> incumbency in Türkiye's public IT procurement" (Version 1.0.0) [Software and data]. Zenodo.
> https://doi.org/10.5281/zenodo.XXXXXXX

Contact: Furkan Aksoy (corresponding author), Department of Software Engineering, Maltepe University, Istanbul,
ORCID [0009-0000-0228-8202](https://orcid.org/0009-0000-0228-8202). Arda Şimşek, ORCID
[0009-0000-7969-6351](https://orcid.org/0009-0000-7969-6351).
