# Estimated-cost sample (`data/ekap_detail_sample.csv`)

Award lists on EKAP do not report the estimated cost (*yaklaşık maliyet*) of a tender. To study
discounts (1 − contract value / estimated cost) we collected tender-detail pages for a small random
sample. The analysis is `src/price_analysis.py`; results are in `results/price/`.

## Sampling

From the 4,913 repeat-eligible contracts of the main sample, 75 won by the buyer's incumbent supplier
and 75 won by other firms were drawn at random (seed 11). The list given to the collector contained only
tender numbers (IKN), so the collector did not see which group a tender belonged to.

## Collection

- An AI agent (Claude, Anthropic) opened each tender's public detail page on EKAP
  (<https://ekapv2.kik.gov.tr>) in the authors' ordinary browser session, one tender at a time.
- It worked slowly, about one tender every 40 seconds, and paused when the site slowed down.
- It did not use any automated scraping of hidden endpoints. It did not bypass, solve or interact with any
  access control or human-verification (CAPTCHA) widget.
- When EKAP showed a human-verification check, collection stopped. By then 144 of the 150 tenders had been
  recorded, and those 144 form the sample.
- No names were recorded: no firm, bidder, person or official names. The buyer is identified only through
  the IKN, which links to `data/contracts_v3.csv`.

## Fields recorded

| column | meaning |
|---|---|
| `IKN` | tender registration number |
| `status` | collection status (`ok` for all 144) |
| `ihale_usulu` | procedure as displayed |
| `okas_codes` | OKAS (CPV-based) product codes, `;`-separated (sometimes truncated on the page) |
| `sozlesme_bedeli` | contract value as displayed (Turkish number format) |
| `yaklasik_maliyet` | estimated cost as displayed |
| `para_birimi` | currency of the contract value |
| `en_yuksek_teklif`, `en_dusuk_teklif` | highest and lowest bid as displayed |
| `sozlesme_tarihi` | contract date (DD.MM.YYYY) |
| `n_dokuman_indiren` | number of parties that downloaded the tender documents |
| `n_teklif_veren`, `n_gecerli_teklif` | number of bids / valid bids, when shown |
| `n_contracts_listed` | number of contracts (lots) listed on the page |
| `note` | collector's notes (missing tabs, lots, currency) |

One contract is in US dollars, so 143 tenders have both values in lira. EKAP contract values match
the values in `data/contracts_v3.csv` within 1% for 99.3% of matched tenders.
