# TenderNet v3 data — data dictionary

All files are UTF-8 CSV (with BOM; read with `encoding="utf-8-sig"`), comma-separated, `.` as decimal
separator, booleans written as `True`/`False`. Raw monetary fields retain their original currencies: **`bedel_num` is not a common-currency TRY measure**. The corrected `bedel_try` is nominal TRY (with explicit exchange-rate and missing-label assumptions); analysis scripts deflate it to 2025 TRY. This working dataset belongs to an unreleased revision of archived v1.0.1.


| file | rows | content |
|---|---|---|
| `contracts_v3.csv` | 13,024 | one row per awarded contract (tender IKN); the analysis file |
| `firm_name_map_v3.csv` | 4,788 | recorded name → v2 canonical → v3 canonical firm, merge type, flags (pseudonymized like the contracts) |
| `bid_counts_sample.csv` | 680 | year-stratified random sample of tenders (40 per year, seed 42) with bid counts from EKAP result announcements |
| `bid_counts_cp2.csv` | 3,400 | bid counts from a second EKAP scrape (keyword `yazılım`, mostly 2021+): IKN, year, search keyword, number of bids (`teklif_veren_sayisi`, 0 = not reported), `has_winner`; winner and bidder names removed |
| `ppi_turkey_yiufe.csv` | 18 | TÜİK domestic PPI (Yİ-ÜFE, 2003=100), monthly and annual averages 2009–2026 (deflator robustness only); source in `ppi_turkey_SOURCES.txt` |
| `cpi_turkey.csv` | 16 | TÜİK CPI (2003=100), annual averages 2010–2025, with World Bank cross-check |
| `cpi_turkey_2026_monthly.csv` | 8 | TÜİK CPI 2026 (2025=100) linked to 2003=100; 2026 uses the mean of available months |
| `cpi_turkey_SOURCES.txt` | – | exact sources and linking of the CPI series |
| `audit/top150_value_review.csv` | 150 | historical scope review of the top 150 by legacy mixed-currency numeric amount; preserved, not corrected nominal-TRY ranking |
| `audit/scope_rule_samples.csv` | – | 5 random contracts per scope rule, for audit |
| `audit/product_market_confusion_sample.csv` | – | 6 random contracts per product market, for audit |
| `audit/classifier_validation.csv`, `.md` | – | hand validation of the product-market title classifier (titles only) |
| `ekap_detail_sample.csv` | 144 | estimated cost, contract value, bids and OKAS codes from EKAP tender-detail pages for a random 75/75 sample of incumbent/other repeat-eligible contracts; values as displayed (Turkish number format); no names — see `docs/estimated_cost_collection.md` |
| `audit/ai_coding/` | – | blind inputs (`blind_*_input.csv`) and labels of two independent AI coders (`coderA_*`, `coderB_*`) for 300 product-market titles and 60 renewal pairs |
| `audit/build_log_v3.txt` | – | full log of the build (every count, merge and rule table), pseudonymized |

## Provenance

The underlying records are award results of Turkish public tenders published by the Public Procurement
Authority (Kamu İhale Kurumu, KİK) on its electronic platform EKAP (<https://ekapv2.kik.gov.tr>) under
Public Procurement Law No. 4734. We collected them with domain keywords (2010-10-05 to 2026-03-18) and
kept tenders concluded with an identifiable winner (13,418 records). 394 obvious non-IT records were
dropped by an earlier count-based cleaning step, leaving the 13,024 rows here. The date is the **tender
date**, not the contract signature date. The scripts that built this table from the raw scrape are in
`src/build/` (see the privacy section for why the raw scrape itself is not distributed).

## Privacy (KVKK, Law No. 6698) and pseudonymization

Winning suppliers include natural persons (sole proprietors and individuals). Their names are personal
data. EKAP publishes them, but we do not redistribute them. In every firm-name column (`firma`, `firma_v2`,
`firma_v3`, and the name columns of `firm_name_map_v3.csv` and `audit/`), a name is replaced by a stable
pseudonym `PSEUDONYM_nnn` when

1. the build heuristic flagged it as a natural person or a joint venture that includes a person
   (`is_natural_person`, `contains_natural_person`; 557 strings), **or**
2. the name, or any comma-separated member of a joint-venture name, carries no explicit legal-entity form
   (A.Ş., Ltd. Şti., Anonim/Limited Şirketi, cooperative, foundation, foreign company forms, ...).

Rule 2 is deliberately conservative. It also catches sole proprietorships whose trade names contain the
owner's name, person-only partnerships and a few company names truncated by EKAP before their legal form.
In total **701 distinct name strings** are pseudonymized, covering **690 of 4,389 firms** (`firma_v3`) and
**1,113 of 13,024 contracts** (670 of the 9,991 main-sample contracts). Names of legal entities and of
public buyers (`kurum`, `kurum_il_split`) are kept. Tender titles (`ihale_adi`) were checked and contain
none of the pseudonymized names.

The replacement is **one-to-one and shared by all name columns**: two contracts have the same pseudonym
if and only if they had the same name. All counts, shares, HHIs, incumbency indicators, regressions and
network statistics are therefore unchanged. Results that involve random draws over firms sorted by name
(permutation and network nulls) can differ in the last digit because pseudonyms sort differently from the
original names; see the top-level README for the verification. Pseudonym numbers are a seeded random
permutation and carry no alphabetical information. The mapping is not released. `firm_id` is
`"F" + sha1(firma_v3)[:8]` computed on the **released** `firma_v3` (a hash of a real personal name could be
reversed with a list of names).

## `contracts_v3.csv` columns

Original scrape columns (Turkish names, as on EKAP):

| column | type | description |
|---|---|---|
| `firma` | str | winning supplier as recorded (pseudonymized, see above) |
| `kurum` | str | contracting authority (buyer) as recorded |
| `sektor` | str | buyer sector, v1 keyword classification (Turkish; superseded by `sektor_v3`) |
| `IKN` | str | tender registration number (İhale Kayıt Numarası), `YYYY/nnnnnn`; unique key |
| `tarih` | date | tender date `YYYY-MM-DD` |
| `tarih_dt` | date | **corrupt** (month/day swapped, 63.5% missing) — do not use; kept for transparency |
| `yil` | int | tender year |
| `bedel` | str | contract amount as displayed on EKAP (`"2.500.000,00 TRY"`) |
| `bedel_num` | float | legacy parsed original amount; mixed currencies, retained unchanged; **do not use as TRY** |
| `ihale_usulu` | str | procedure as displayed (Açık, Pazarlık (MD 21 B), Belli İstekliler Arasında, ...) |
| `il` | str | province of the tender (81 provinces) |
| `ihale_durumu` | str | tender status at scraping time |
| `ihale_adi` | str | tender title (free text) |
| `hard_nonIT` | bool | v1 cleaning flag (all False here) |
| `gri_yonetim` | bool | v1 flag for ambiguous "yönetim sistemi" titles |

Currency columns added by the unreleased correction:

| column | type | description |
|---|---|---|
| `bedel_amount_original` | float | amount parsed from preserved `bedel`, before conversion |
| `bedel_currency` | str | `TRY`, `USD` or `EUR`; TRY includes explicitly flagged assumptions |
| `bedel_currency_status` | str | `explicit` means labelled in raw text; `unspecified_assumed_TRY` means no currency label, not verification |
| `bedel_fx_try_per_unit` | float | TCMB indicative buying/selling midpoint per unit for USD/EUR; 1 for TRY |
| `bedel_fx_date` | date | actual TCMB quotation date (blank for TRY) |
| `bedel_valuation_method` | str | explicit/assumed TRY, same-day FX proxy, or prior-business-day FX proxy |
| `bedel_try` | float | original amount times rate: nominal TRY valuation proxy; monetary analyses use this field |

There are 57 USD and 19 EUR rows (main sample: 54 USD, 13 EUR). Currency is unspecified for 1,291 rows (845 main), assumed TRY. The date is the tender date, not the payment date. `fx_rates_tcmb.csv` records 146 USD/EUR rate rows for 73 required dates, with URLs, payload SHA-256, buying/selling/unit and actual rate date. `fx_cache_tcmb/` supplies the 73 source XML files. Offline normalization verifies hashes and fails closed on unsupported explicit currencies or absent/invalid rates. The sole prior-day fallback is 2014-10-28 to 2014-10-27. See `docs/currency_normalization.md`.

`results/revision_e_currency/corrected_top150_value_screen.csv` ranks the released data by nominal TRY. `legacy_scope_review_recorded` indicates membership in the historical review; `new_scope_review_required` identifies the one newly entering record. `currency_independently_reverified=False` prevents treating parsing or archived review membership as an award-price verification. The separate `ai_assisted_official_scope_check` and source URL record an official tender-notice scope/identity check of the one entrant; it is not human validation. Existing manual scope labels are retained, not revalidated by this calculation.

Columns added by the v3 build:

| column | type | description |
|---|---|---|
| `ihale_turu` | str | EKAP tender type: Hizmet (services), Mal (goods), Yapım (works), Danışmanlık (consultancy) |
| `kaynak_keyword` | str | EKAP search keyword that retrieved the tender |
| `tarih_v3`, `yil_v3` | date, int | tender date and year (**use these**) |
| `usul_v3` | str | `open`, `restricted`, `negotiated_21a` … `negotiated_21f` (Law 4734 Art. 21 sub-paragraphs) |
| `usul_v3_group` | str | `open`, `restricted`, `negotiated` |
| `kurum_il_split` | str | buyer node used in the paper: `kurum + " \| " + il` for 36 generic labels pooled across provinces (e.g. MoH provincial health directorates), else `kurum` |
| `pooled_label` | bool | `kurum` is one of the pooled generic labels |
| `sektor_v3`, `sektor_v3_en` | str | corrected buyer sector (11 classes), Turkish / English |
| `sector_changed` | bool | `sektor_v3` differs from `sektor` |
| `scope_v3` | str | `IT`, `IT_service_callcentre`, `gray` (ambiguous), `nonIT` |
| `scope_reason` | str | rule that fired, or `manual_override(was X)` |
| `scope_manual_override`, `callcentre_flag`, `it_staffing_flag` | bool | flags |
| `in_scope_core` / `in_scope_main` / `in_scope_broad` | bool | IT only / IT + call centre (**main sample, 9,991 rows**) / + gray |
| `urun_pazari` | str | product market (below); `not_IT` for non-IT rows |
| `firma_v2` | str | v2 canonical firm name (pseudonymized) |
| `firma_v3` | str | v3 canonical firm name — **firm node used in the paper** (pseudonymized) |
| `firm_merge_v3` | str | how the v3 name was merged: `none`, `spelling`, `legal_form`, `successor` |
| `is_natural_person` | bool | heuristic: winner is a bare personal name |
| `contains_natural_person` | bool | winner is a person or a joint venture that includes one |
| `firm_id` | str | `F` + 8 hex characters; stable firm pseudonym (one per `firma_v3`) |
| `name_pseudonymized` | bool | `firma_v3` of this row was replaced by a pseudonym |

### Scope classes (`scope_v3`)

| class | contracts | nominal value (bn TRY) | share of value |
|---|---|---|---|
| IT | 9,981 | 25.65 | 56.5% |
| IT_service_callcentre | 10 | 7.62 | 16.8% |
| gray | 1,406 | 4.12 | 9.1% |
| nonIT | 1,627 | 8.04 | 17.7% |

Rules are applied from titles in a fixed order (IT-user staffing → call centre → works contracts →
strong IT word → non-IT lexicon → weak word only → no IT word); see `src/build/rules_v3.py`
(`classify_scope`). The 150 largest contracts were checked by hand; 7 rule outcomes were overridden
(`src/build/manual_scope_overrides.csv`).

### Product markets (`urun_pazari`, in-scope rows)

| market | contracts | nominal value (bn TRY) |
|---|---|---|
| health_information_systems | 2,200 | 7.42 |
| ERP_management_software | 1,951 | 3.40 |
| custom_software_web_mobile | 1,141 | 2.10 |
| software_licences | 1,048 | 2.36 |
| network_datacentre_infrastructure | 795 | 2.70 |
| computers_peripherals | 719 | 1.03 |
| maintenance_support_services | 683 | 2.23 |
| physical_security_surveillance | 604 | 0.90 |
| GIS_city_information | 562 | 0.98 |
| IT_staffing_data_entry | 453 | 1.80 |
| cybersecurity | 392 | 1.70 |
| smart_city_traffic_OT | 230 | 1.53 |
| education_technology | 225 | 1.23 |
| call_centre_helpdesk | 82 | 7.70 |
| other_IT | 312 | – |

(Counts are over all in-scope rows as in the build log; the first matching title rule wins.)

### Buyer sectors (`sektor_v3_en`)

Health, Municipal/Local, Other public, Education, Infrastructure/Transport, Agriculture/Environment,
Social/Finance, Provincial admin, Defence, Security/Interior, Justice.

## `bid_counts_sample.csv` columns

| column | type | description |
|---|---|---|
| `IKN` | str | tender number (joins `contracts_v3.IKN`) |
| `yil` | int | tender year |
| `il` | str | province |
| `ihale_adi` | str | tender title (as shown on the result page; may be truncated) |
| `usul` | str | procedure as displayed (may contain the HTML entity `&nbsp;`) |
| `toplam_teklif` | int | total number of bids received |
| `gecerli_teklif` | int | number of valid bids |
| `indiren_sayisi` | int | number of parties that downloaded the tender documents |

Missing counts mean the result announcement did not report them (no data for 2010–2011).

## Known limitations

- Scope and product market are classified from titles only; bundled tenders and generic
  "yönetim/otomasyon sistemi" titles are uncertain (about 500 gray rows are verified only by sampling).
- Values mix explicit currencies and missing labels in the raw source. Corrected `bedel_try` uses a tender-date FX proxy and assumes missing labels are TRY; the 845-record main-sample exclusion sensitivity is reported separately. The large MHRS call-centre contract motivates largest-contract exclusions.
- Firm canonicalization is heuristic plus hand review of the ~300 largest firms; successor merges
  assume brand continuity. Joint ventures are separate firms.
- The natural-person flags are heuristic; pseudonymization rule 2 is conservative, so some pseudonymized
  names are small legal entities whose names EKAP truncated.
- No direct procurement (Art. 22) is in the extract; procedure analyses cover tenders only.
- 2026 is partial (to March 2026).
- Keyword retrieval may miss IT tenders whose titles use none of the search keywords.
