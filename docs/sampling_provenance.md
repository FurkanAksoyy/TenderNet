# Sampling and collection provenance

This retrospective reconstruction separates evidence in preserved files from
the collector configuration currently on disk. It neither reruns collection nor
asserts national procurement coverage. No raw-person records are redistributed.

## Evidence and unresolved dates

The preserved listing checkpoint `03_SCRAPER/ekap_v3_cp1.json` contains 20,171
distinct tender registration numbers (IKN). The winner edge file
`02_VERI/ekap_v8_kazandi_edge.csv` and `06_YENI_ANALIZ/master_sozlesmeler.csv` contain
the same 13,418 unique IKN, all present in that checkpoint. Every winner edge has
source type `html_regex`. The early cleaned master contains 13,024 IKN, exactly
matching the public release. The main IT sample has 9,991. These are checked
file-membership relationships, not national sampling fractions.

Listing-checkpoint tender dates span 2010-09-17 through 2026-04-03. Winner and
released/main samples span 2010-10-05 through 2026-03-18. Tender dates are not
extraction dates. Neither checkpoint records a capture timestamp, executed
start/end parameters, per-query totals, or a completed-query ledger. **The exact
extraction date and executed end date are unrecoverable from these files.**
Filesystem modification times are not treated as extraction timestamps.

The short saved `03_SCRAPER/ekap çıktısı.txt` concerns a v7 run with 2,424 tenders
and 1,805 winners, not the 13,418-winner chain. It cannot resolve this gap. The
surviving cp2 is partial (3,400 processed, 1,219 winner edges), not complete
winner-master provenance.

## Keyword evidence

The current `ekap_v3.py` assignment contains **48** keywords; its banner says 41
and is stale. The listing checkpoint has 31 contributing first-match keywords;
the public and main samples each have 26. All observed checkpoint keywords occur
in the configured list. Every public `kaynak_keyword` exactly matches the
checkpoint value by IKN. This consistency does not prove all 48 queries finished.
A zero first-match count may reflect overlap with earlier queries, no results,
or incomplete execution. The full ordered list and counts appear below.

## Settings in the current source

| Setting | Preserved source configuration |
|---|---|
| Endpoint | POST `/b_ihalearama/api/Ihale/GetListByParameters`, host `https://ekapv2.kik.gov.tr`, API version `v1` |
| Text query | `searchText=keyword`, `searchType=GirdigimGibi`, `ikNdeAra=True`, `ihaleAdindaAra=True` |
| Tender-date start | `2009-01-01T00:00:00` |
| Tender-date end | `datetime.today()` at runtime through `23:59:59`; historical value unrecorded |
| Law/type selectors | `yasaKapsami4734List=[1]`, `ihaleTuruIdList=[1,2,3,4]` |
| Other filters | Procedure/subprocedure, province, status, announcement/offer type and code lists empty; nullable flags `None` |
| Ordering | Descending tender date (`orderBy=ihaleTarihi`, `siralamaTipi=desc`) |
| Pagination | 50 records per page; at most 10,000 results per keyword |
| Nominal waits | Listing 1.0 second; detail 1.5 seconds |

These are current-source settings, not a recovered historical execution manifest.
The dynamic end date changes on each run. API errors produce no rows, and an
empty page terminates keyword pagination. A nonempty cp1 skips listing collection
wholesale on restart, including after an incomplete run. Cap hits, failed/empty
pages and query completion cannot be reconstructed from the saved checkpoint.
No claim of exhaustive search or absence of truncation is made.

## De-duplication and retention

Listing code maintains a global `ikn_set` across queries. It appends a nonempty
IKN only on first encounter and discards subsequent matches. `kaynak_keyword`
therefore records first retained query, not all matching queries. Keyword counts
are mutually exclusive attribution counts, not keyword-hit totals. All inspected
checkpoint/master/release IKN are unique.

The detail step prioritizes statuses containing Turkish result/contract terms and
extracts a winner from announcement fields/HTML; other listings receive empty
winner fields. The final raw award chain is the v8 winner-edge file, enriched
from cp1 by IKN in `06_YENI_ANALIZ/01_master_tablo_ve_HHI.py`. Extant v3 code and
partial cp2 do not establish the complete later v8 execution history. One row
per IKN is not a census of lots, every winning supplier, or every award under it.

Early cleaning (`06_YENI_ANALIZ/02_kapsam_temizlik_ve_robustness.py`) removes obvious
non-IT title matches only when strong IT terms are absent: 394 rows, leaving
13,024. Later public v3 scope rules/overrides retain 9,991 main IT observations.
The 6,753 listing-checkpoint IKN outside the winner master cannot all be labelled
failed retrievals or cancellations from the available artifacts.

## Reproduction and source excerpts

`python src/revision_e_sampling.py` reproduces public counts and joins committed
upstream aggregate snapshots. Holders of the original workspace can use
`--private-root PATH` to verify memberships and refresh upstream counts.
`results/revision_e_sampling/sampling_provenance_metadata.json` records origin
relative paths and SHA-256 hashes. Hashes identify artifacts, not collection
dates or completeness. No raw rows, titles, winners or buyer names are exported.

`src/collection/ekap_v3_query_provenance.py` contains relevant configuration,
list-query and de-duplication excerpts from the project collector with its origin
SHA-256. It contains no credentials or raw records. No collection runs on import;
live helpers are omitted and there is no main entry point. It documents methods,
not a claim that today's endpoint reproduces the historical snapshot. No network
requests were made during this reconstruction.

Annual counts use cp1 tender dates upstream and `yil_v3` in the released/main
data. They measure observed retention by tender year, not national recall. 2026
is partial. Full CSV tables are in `results/revision_e_sampling/`.


## Annual flow

| year | Listing checkpoint | Winner master | Early excluded | Public retained | Main IT |
|---|---:|---:|---:|---:|---:|
| 2009 | 0 | 0 | 0 | 0 | 0 |
| 2010 | 557 | 151 | 3 | 148 | 100 |
| 2011 | 1551 | 910 | 28 | 882 | 573 |
| 2012 | 1472 | 1004 | 39 | 965 | 603 |
| 2013 | 1572 | 1164 | 40 | 1124 | 713 |
| 2014 | 1443 | 1025 | 49 | 976 | 679 |
| 2015 | 1501 | 1037 | 46 | 991 | 681 |
| 2016 | 1360 | 927 | 36 | 891 | 677 |
| 2017 | 1522 | 925 | 29 | 896 | 692 |
| 2018 | 1122 | 745 | 17 | 728 | 624 |
| 2019 | 997 | 663 | 22 | 641 | 545 |
| 2020 | 1112 | 792 | 25 | 767 | 663 |
| 2021 | 1185 | 849 | 14 | 835 | 730 |
| 2022 | 1254 | 856 | 15 | 841 | 712 |
| 2023 | 1110 | 748 | 11 | 737 | 622 |
| 2024 | 1009 | 688 | 11 | 677 | 568 |
| 2025 | 1163 | 813 | 8 | 805 | 700 |
| 2026 | 241 | 121 | 1 | 120 | 109 |


## Complete configured keyword list and first-match counts

| kaynak_keyword | Listing checkpoint | Winner master | Early excluded | Public retained | Main IT |
|---|---:|---:|---:|---:|---:|
| yazılım | 5013 | 4196 | 0 | 4196 | 4045 |
| yazılım geliştirme | 0 | 0 | 0 | 0 | 0 |
| uygulama geliştirme | 50 | 42 | 1 | 41 | 41 |
| mobil uygulama | 120 | 95 | 0 | 95 | 94 |
| web uygulaması | 17 | 17 | 0 | 17 | 17 |
| web tabanlı | 229 | 192 | 0 | 192 | 190 |
| yazılım lisans | 0 | 0 | 0 | 0 | 0 |
| lisans alım | 190 | 14 | 0 | 14 | 14 |
| yazılım bakım | 0 | 0 | 0 | 0 | 0 |
| yazılım destek | 0 | 0 | 0 | 0 | 0 |
| yazılım güncelleme | 0 | 0 | 0 | 0 | 0 |
| bilgi sistemi | 1237 | 733 | 15 | 718 | 519 |
| yönetim sistemi | 3522 | 2865 | 7 | 2858 | 2259 |
| bilgi yönetim sistemi | 0 | 0 | 0 | 0 | 0 |
| otomasyon sistemi | 1060 | 864 | 288 | 576 | 147 |
| otomasyon yazılım | 0 | 0 | 0 | 0 | 0 |
| erp | 748 | 618 | 0 | 618 | 68 |
| kurumsal kaynak | 66 | 4 | 0 | 4 | 4 |
| muhasebe yazılım | 0 | 0 | 0 | 0 | 0 |
| veri tabanı | 255 | 208 | 0 | 208 | 207 |
| veritabanı | 142 | 124 | 0 | 124 | 124 |
| veri ambarı | 35 | 3 | 0 | 3 | 3 |
| veri analiz | 12 | 0 | 0 | 0 | 0 |
| raporlama sistemi | 38 | 2 | 0 | 2 | 2 |
| siber güvenlik | 95 | 81 | 0 | 81 | 80 |
| bilgi güvenlik | 0 | 0 | 0 | 0 | 0 |
| ağ yönetim | 17 | 0 | 0 | 0 | 0 |
| yapay zeka | 67 | 49 | 0 | 49 | 44 |
| makine öğrenimi | 0 | 0 | 0 | 0 | 0 |
| dijital dönüşüm | 20 | 18 | 0 | 18 | 18 |
| bulut bilişim | 1 | 1 | 0 | 1 | 1 |
| cloud | 26 | 0 | 0 | 0 | 0 |
| hbys | 896 | 684 | 0 | 684 | 623 |
| hasta bilgi | 20 | 18 | 0 | 18 | 1 |
| hastane bilgi sistemi | 0 | 0 | 0 | 0 | 0 |
| e-belediye | 12 | 10 | 0 | 10 | 10 |
| e-devlet | 9 | 7 | 0 | 7 | 7 |
| vatandaş portal | 0 | 0 | 0 | 0 | 0 |
| coğrafi bilgi sistemi | 0 | 0 | 0 | 0 | 0 |
| bilişim | 1539 | 1302 | 22 | 1280 | 1164 |
| bilgisayar yazılım | 0 | 0 | 0 | 0 | 0 |
| it hizmet | 896 | 0 | 0 | 0 | 0 |
| teknik destek | 1536 | 1247 | 61 | 1186 | 301 |
| portal yazılım | 0 | 0 | 0 | 0 | 0 |
| platform yazılım | 0 | 0 | 0 | 0 | 0 |
| entegrasyon yazılım | 0 | 0 | 0 | 0 | 0 |
| api | 2273 | 0 | 0 | 0 | 0 |
| bakım destek hizmet | 30 | 24 | 0 | 24 | 8 |
