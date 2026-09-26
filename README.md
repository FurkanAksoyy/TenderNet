# TenderNet v1.0.0 — reproducibility package

Data and code for

> Aksoy, F. and Şimşek, A. (2026). **Unconcentrated markets, captive buyers: incumbency in Türkiye's public IT
> procurement.** Manuscript prepared for submission to the *Journal of Industrial and Business Economics* (JIBE, Springer).

We study 9,991 awarded information-technology contracts published on Türkiye's e-procurement platform EKAP
(2010–2026), linking 2,814 firms to 2,890 public buyers. No product market is robustly concentrated (pooled
supplier HHI 39 by count, 149 by real value), yet buyers return to incumbent suppliers far more often than chance:
45.2% of repeat-eligible contracts go to an incumbent, against 6.2% under a permutation null that preserves each
buyer's demand and each firm's wins within product market and year. Incumbency is strongest in health IT and in
Article 21(b) negotiated procedures (odds ratio of the 21(b) × post-2018 interaction 2.42), and incumbent-won
tenders attract a single bid 71% of the time, against 32% for new suppliers.

## Repository structure

```
run_all.py              runs the whole pipeline in order (see below)
requirements.txt        pinned Python packages (tested with Python 3.13.2, Windows 11)
data/                   release dataset + data dictionary (data/README.md) + CPI series; CC BY 4.0
  contracts_v3.csv        13,024 contracts (9,991 in the main sample), natural persons pseudonymized
  firm_name_map_v3.csv    firm-name canonicalization map (pseudonymized)
  bid_counts_sample.csv   year-stratified sample of tenders with bid counts
  cpi_turkey*.csv         TÜİK CPI used to deflate to 2025 TRY
  audit/                  hand review of the top-150 contracts, rule samples, build log
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
python run_all.py --skip-slow    # ~3 min: everything except the network null models
python run_all.py                # full run, ~35 min (network_analysis.py alone takes ~30 min)
python run_all.py --only lockin  # a single step
```

`--skip-slow` skips `network_analysis.py` (200 curveball randomizations, 50 Louvain stability runs, annual and
sensitivity nulls); the later network steps then reuse the committed `results/network/` files. Each step logs to
`results/logs/<step>.log`. The final step, `src/check_headlines.py`, compares the regenerated numbers with the
paper and fails if any differs. All random procedures use fixed seeds (42 and seed lists documented in the
scripts), so results are exactly reproducible.

Pipeline order: `concentration_v3.py` → `lockin_analysis.py` → `models_analysis.py` → `models_report.py` →
`models_figures.py` → `network_analysis.py` (slow) → `network_projections.py` → `network_figures.py` →
`make_si_tables.py` → `check_headlines.py`. `results/network/fig_N1_hub_labels.csv` is a hand-made input (short
hub labels for Figure 6), not an output.

Paper: `cd paper && pdflatex tendernet_jibe && bibtex tendernet_jibe && pdflatex tendernet_jibe && pdflatex tendernet_jibe`
(Springer Nature `sn-jnl` class and `sn-apacite.bst` included); the SI is `tendernet_si.tex` (pdflatex twice).
`paper/figures/` holds copies of the PDF figures in `figures/`. Helpers: `src/wordcount.py` (manuscript word
count), `src/merge_bib.py` (rebuilds `paper/refs.bib` from `paper/bib_src/`).

## Where each result comes from

| paper item | content | script | output |
|---|---|---|---|
| Table 1 | main-sample descriptives | `concentration_v3.py`, `lockin_analysis.py` | `results/concentration/concentration_results.md`, `results/lockin/lockin_log.json`, `results/lockin/null_overall.csv` |
| Table 2 | incumbency and repeat contracting vs nulls N1–N3 | `lockin_analysis.py` | `results/lockin/null_overall.csv` |
| Table 3 | logit of an incumbent win | `models_analysis.py` | `results/models/A1_logit_incumbency.csv` |
| Figure 1 | supplier HHI by product market | `concentration_v3.py` | `figures/F-C1_concentration_by_market.*`, `results/concentration/supplier_hhi_by_market.csv` |
| Figure 2 | incumbency by product market | `lockin_analysis.py` | `figures/F_L1_incumbency_by_market.*`, `results/lockin/null_by_group.csv` |
| Figure 3 | incumbency by year | `lockin_analysis.py` | `figures/F_L2_incumbency_by_year.*`, `results/lockin/null_by_group.csv` |
| Figure 4 | buyers' top-supplier share | `lockin_analysis.py` | `figures/F_L3_buyer_top_supplier_share.*`, `results/lockin/buyer_dependence.csv` |
| Figure 5 | single-bid rates | `models_analysis.py`, `models_figures.py` | `figures/F-R2_single_bid.*`, `results/models/D_single_bid_rates.csv` |
| Figure 6 | core buyer–supplier network | `network_analysis.py`, `network_figures.py` | `figures/fig_N1_core_network.*`, `results/network/nodes_main.csv` |
| – (extra) | within-year HHI; average marginal effects | `concentration_v3.py`; `models_figures.py` | `figures/F-C2_within_year_hhi.*`; `figures/F-R1_models_AME.*` |
| SI Table S1 (scope classes) | | `make_si_tables.py` | `paper/si_tables/scope.tex` |
| SI concentration, within-year HHI | | `concentration_v3.py` → `make_si_tables.py` | `paper/si_tables/concentration.tex`, `within_year.tex` |
| SI incumbency by market / sector / buyer type / procedure / year, sensitivity | | `lockin_analysis.py` → `make_si_tables.py` | `paper/si_tables/lockin_*.tex`, `sensitivity.tex` |
| SI dyad continuation (logit, NB2 and variants) | | `models_analysis.py` → `make_si_tables.py` | `paper/si_tables/B_*.tex` |
| SI single-bid rates | | `models_analysis.py` → `make_si_tables.py` | `paper/si_tables/single_bid.tex` |
| SI network nulls, projections, brokerage | | `network_analysis.py`, `network_projections.py` | `results/network/*.csv`, `network_projections.json` |

The manuscript has six figures; `F-C2` and `F-R1` are produced for completeness and are not in the paper.
Narrative reports with every number that could go in the paper: `results/*/*_results.md`.

## Data provenance

The underlying records are award results of Turkish public tenders, published by the Public Procurement
Authority (Kamu İhale Kurumu, KİK) on EKAP (<https://ekapv2.kik.gov.tr>) under Public Procurement Law No. 4734.
We retrieved them with IT domain keywords (13,418 records with an identifiable winner), audited the IT scope by
contract value, canonicalized firm names, split pooled buyer labels by province and classified product markets
(details: `data/README.md`, `data/audit/`). Bid counts come from the published result announcements of a
year-stratified random sample of tenders. CPI: TÜİK (sources in `data/cpi_turkey_SOURCES.txt`).

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
the internal data: every result table of the concentration, lock-in and model steps is byte-identical
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

> Aksoy, F. and Şimşek, A. (2026). TenderNet v1.0.0: data and code for "Unconcentrated markets, captive buyers:
> incumbency in Türkiye's public IT procurement" (Version 1.0.0) [Software and data]. Zenodo.
> https://doi.org/10.5281/zenodo.XXXXXXX

Contact: Furkan Aksoy (corresponding author), Department of Software Engineering, Maltepe University, Istanbul,
ORCID [0009-0000-0228-8202](https://orcid.org/0009-0000-0228-8202). Arda Şimşek, ORCID
[0009-0000-7969-6351](https://orcid.org/0009-0000-7969-6351).
