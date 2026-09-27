# Currency valuation and sensitivity

This is an unreleased correction to archived TenderNet v1.0.1. The archive DOI
continues to identify the old release; it does not identify these local changes.

## Measurement

The preserved `bedel` strings contain 57 USD and 19 EUR values in the full 13,024
records. The archived `bedel_num` stripped those labels and treated the resulting
mixed-currency numbers as TRY. This field remains unchanged for auditability.
`bedel_amount_original` parses the raw number, `bedel_currency` supplies its label,
and `bedel_try` supplies the common-currency valuation used by monetary analyses.

The main sample has 9,991 records: 54 USD, 13 EUR and 9,924 labelled or assumed TRY.
There are 845 unlabelled main records (1,291 full data). Their status is
`unspecified_assumed_TRY`; they are not verified TRY. An `explicit` status means a
currency label occurs in the source string, not that a new EKAP verification was
performed. Unknown explicit currencies or malformed amounts fail closed.

For USD/EUR we use TCMB official indicative daily rates: the arithmetic midpoint
of ForexBuying and ForexSelling, divided by Unit, on the tender date. This is a
tender-date valuation proxy, not a reconstruction of payment dates or settlement
rates. If that weekday's XML returns HTTP 404, the algorithm searches backward at
most seven calendar days, skipping weekends. Other HTTP errors are propagated.
The only fallback in this dataset is 2014-10-28 to 2014-10-27.

The 73 daily XML files are cached in `data/fx_cache_tcmb/`. The adjacent
`data/fx_rates_tcmb.csv` lists exact source URLs, dates, quotations and payload
SHA-256 hashes. For example, [TCMB 4 November 2016](https://www.tcmb.gov.tr/kurlar/201611/04112016.xml)
quotes USD buying 3.1348 and selling 3.1405, giving midpoint 3.13765 TRY/USD.
Currency normalization precedes annual CPI/PPI deflation. No rounding to whole
lira is applied to converted amounts.

## Reproduction

From the repository root:

```bash
python src/build/normalize_currency.py
python -m unittest discover -s src/build -p test_currency_values.py
python src/revision_e_currency.py
```

Normalization is offline by default, verifies cached XML hashes and table rates,
and always recomputes from raw values, making repeated runs idempotent. `--fetch`
explicitly enables public TCMB retrieval. Five tests cover parsing, rate/unit/date
validation, bounded fallback, missing rates, idempotence, original amount equality
and sample counts. All 42 pre-existing data columns were compared with the archived
Git baseline and remain equal after CSV parsing. Full analysis regeneration is
coordinated through `run_all.py`; these commands alone do not rerun every model.

## Unknown-currency sensitivity

`src/revision_e_currency.py` independently writes pooled and category HHI results,
nominal and real totals, counts, and a contract-level linear probability
sensitivity to `results/revision_e_currency/`. The main sample's 845 unlabelled
records account for 5.27% of corrected real value. Their exclusion leaves 9,146
contracts and changes pooled value HHI from 147.244 to 158.514; health-IT value HHI
changes from 831.069 to 872.608. This exclusion changes sample composition and is
neither an identified bound nor an imputation of missing currencies.

The regression sensitivity uses the primary A1 controls and year/category/sector
fixed effects, with two-way buyer/winning-firm clustered covariance. It keeps all
observed contracts when constructing histories, then excludes unlabelled current
contracts from estimation. The explicit-only A1 logit failed to converge under
Newton at 200 iterations during this revision. Comparable linear probability
fits are therefore reported for both samples, without reporting unstable odds
ratios. The log-real-value coefficient changes from -0.0038 to -0.0050; the
21(b)-by-post interaction changes from 0.1189 to 0.1384 (N=4,913 and 4,786).
These are sensitivity associations, not causal effects.

## Historical audit versus corrected ranking

`data/audit/top150_value_review.csv` preserves the original hand-review record,
whose rank used the legacy mixed-currency numeric amount. The corrected screen
in `results/revision_e_currency/corrected_top150_value_screen.csv` ranks by nominal
TRY and records `legacy_scope_review_recorded`, `new_scope_review_required` and
`currency_independently_reverified`. These flags distinguish historical review
membership from an unperformed new hand review.

One record enters: IKN 2023/670417, eight de-icing-fluid spraying vehicles,
EUR 2,631,200 (TRY 76,209,550.56 proxy). Its existing scope classification is non-IT;
the screen does not create a new hand-validation label. An AI-assisted check of
the [official DHMI tender notice](https://www.dhmi.gov.tr/Lists/IhaleIlanlari/Attachments/1455/ihale%20ilan%C4%B1-de.%C4%B1c%C4%B1ng.pdf)
corroborates the exact IKN and eight vehicles on page 1 and tender date 01.09.2023
on page 3. `ai_assisted_official_scope_check` records that scope/identity check.
It is not new human validation and does not independently verify the award price
or currency against an official award-result source. Raw reconstruction also
uses corrected nominal TRY for value summaries and rankings, and release export
preserves the historical review separately from the corrected screen.
