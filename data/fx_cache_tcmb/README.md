# TCMB daily XML cache

Public official source: `https://www.tcmb.gov.tr/kurlar/YYYYMM/DDMMYYYY.xml`.
Fetched 2026-09-27 for the 73 distinct tender dates of contracts explicitly
denominated in USD or EUR. The adjacent `fx_rates_tcmb.csv` records the exact
source URL, date and SHA-256 for each cached payload and each required currency.
It includes both USD and EUR for each required date.

The valuation uses `(ForexBuying + ForexSelling) / (2 * Unit)` on the tender
date, or the latest available weekday within seven calendar days when the
date's XML returns HTTP 404. The sole fallback is 2014-10-28 → 2014-10-27.
This is a nominal TRY valuation proxy, not a claimed payment exchange rate.

`python src/build/normalize_currency.py` verifies hashes and quotations and
rebuilds the enriched contract file offline. `--fetch` opts into retrieval.
The raw contract value string and legacy parsed amount are preserved.
