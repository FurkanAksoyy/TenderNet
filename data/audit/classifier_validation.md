# Product-market classifier validation (urun_pazari)

**Important: the reference labels were produced by a model, not by a human expert.** Claude, an LLM, assigned them as an AI-assisted annotation. It read each Turkish tender title (`ihale_adi`) without seeing the rule label (`urun_pazari`) and chose one of the 14 markets. This check is therefore a model-versus-rule agreement check, not a gold-standard accuracy estimate. Before the results are reported as validation, a human coder, ideally one of the authors, should re-code at least the disagreements (69 rows).

## Design
- Population: `data/master_v3.csv`, rows with `in_scope_main == True` (n = 9,991).
- Sample: 300 contracts, `DataFrame.sample(300, random_state=7)`. The rule-label mix in the sample is close to the population: health 23.0% (population 21.9%), licences 13.3% (10.5%), ERP 12.0% (15.2%).
- The reference labels come from the title only; there is no access to buyer, value or `kaynak_keyword`. Coding conventions:
  - Maintenance of a *specific* product family goes to that family: HBYS maintenance → health, KGYS maintenance → physical security, network-device maintenance → network. Generic hardware or software maintenance and technical support go to `maintenance_support_services`.
  - EBYS, MIS, HR, library and dormitory systems go to ERP.
  - KGYS goes to physical security.
  - Security licences go to cybersecurity.
- File: `research/classifier_validation.csv`. Columns: sample_idx, IKN, title, your_label (the model reference), rule_label, agree, ambiguous_flag (flagged while labelling, before the rule labels were seen), disagreement_type (assigned after comparison).

## Headline results
| | n | Agreement | Cohen's κ |
|---|---|---|---|
| All 300 | 300 | **77.0%** | **0.741** |
| Excluding titles flagged ambiguous during labelling | 255 | 82.4% | 0.797 |

Breakdown of the 69 disagreements:
| Type | n | % of sample |
|---|---|---|
| Rule clearly wrong | 22 | 7.3% |
| Maintenance-vs-product convention (both labels defensible) | 16 | 5.3% |
| Genuinely ambiguous / multi-product boundary | 27 | 9.0% |
| Title is barely an IT product (a scope issue, not a market issue) | 4 | 1.3% |

If the convention and ambiguous cases count as acceptable, the rule is "defensible" for 91.3% of titles and clearly wrong for about 7%.

## Per-class precision and recall
The model labels are treated as the reference. Precision is the share of the rule's assignments to a class that the reference agrees with.

| Market | n (reference) | n (rule) | Precision | Recall | F1 |
|---|---|---|---|---|---|
| health_information_systems | 69 | 69 | 0.99 | 0.99 | 0.99 |
| software_licences | 37 | 40 | 0.85 | 0.92 | 0.88 |
| GIS_city_information | 20 | 17 | 1.00 | 0.85 | 0.92 |
| physical_security_surveillance | 14 | 14 | 0.86 | 0.86 | 0.86 |
| call_centre_helpdesk | 4 | 3 | 1.00 | 0.75 | 0.86 |
| network_datacentre_infrastructure | 19 | 27 | 0.67 | 0.95 | 0.78 |
| ERP_management_software | 25 | 36 | 0.64 | 0.92 | 0.75 |
| computers_peripherals | 24 | 22 | 0.77 | 0.71 | 0.74 |
| cybersecurity | 21 | 14 | 0.86 | 0.57 | 0.69 |
| education_technology | 10 | 8 | 0.62 | 0.50 | 0.56 |
| maintenance_support_services | 19 | 16 | 0.56 | 0.47 | 0.51 |
| custom_software_web_mobile | 24 | 29 | 0.41 | 0.50 | 0.45 |
| smart_city_traffic_OT | 4 | 1 | 1.00 | 0.25 | 0.40 |
| other_IT | 10 | 4 | 0.00 | 0.00 | 0.00 |

**Health IT, the market that carries the paper's main results, is almost perfectly classified.** Of the 69 contracts in each labelling, 68 overlap. The rule missed one health contract: a dental information system (idx 173) was put in ERP. The rule's one extra health label is a hospital-server maintenance contract (idx 49), which the reference put in maintenance.

## Main confusions (reference → rule)
1. **Generic maintenance → network or computers** (5 + 3 cases, e.g. "Sunucu bakım onarım", "Bilgisayar donanım ... bakım"). The rule sends maintenance of servers or PCs to the hardware market. This is a convention choice, not an error, but the maintenance market is under-populated as a result.
2. **Custom software ↔ maintenance** (5). Support and updates for bespoke apps or websites. A convention issue.
3. **Cybersecurity → custom software / licences / network** (4 + 3 + 1). Security products whose titles contain no "güvenlik duvarı / siber / antivirüs" keyword, for example data masking and encryption, e-mail filtering, SAST tools, and ICS penetration testing. These all fell to `custom_software` because of the word "yazılım". **Cybersecurity recall is only 0.57.**
4. **Custom software / other → ERP** (4 + 3). "Yönetim Sistemi" in a title triggers ERP even for websites with a CMS, web-GIS, a ship information system or an e-campus system. **ERP precision is 0.64.**
5. **other_IT is not usable as a class.** The rule's four other_IT assignments are all PCs or consumables (reference: computers). The reference's 10 residual titles (AV/videowall, generic "YAZILIM ALIMI", workshops) were spread over the substantive classes by the rule.

## Titles where the rule is clearly wrong (22)
| idx | Title (abridged) | Reference | Rule |
|---|---|---|---|
| 229 | İzmir BB resmi web sitesi, kent portalı, kiosk yazılımı | custom_software | computers_peripherals |
| 267 | Web tabanlı coğrafi yönetim bilgi sistemi yazılımı | GIS | ERP |
| 173 | 12 aylık diş hekimliği bilgi sistemi hizmet alımı | health | ERP |
| 298 | PLC otomasyon sistemi güncelleme ve bakım | smart_city_OT | ERP |
| 221 | Aktif ağ cihazları donanım, yazılım ve lisans | network | licences |
| 139 | Eğitim yönetim sistemi yazılım geliştirme + eğitim portalı | education | network |
| 144 | Web sitesi yazılımı, tasarım ve içerik yönetim sistemi | custom_software | ERP |
| 90 / 141 / 162 / 198 | Veri maskeleme-şifreleme; internet/e-posta filtreleme; güvenli uygulama geliştirme kontrol; EKS güvenlik testleri | cybersecurity | custom_software |
| 209 / 122 | İnternet güvenlik cihazı + 5651 kayıt; internet güvenlik donanımları | cybersecurity | licences / network |
| 89 | Göz biyometri kayıt üniteleri (nizamiye) | physical_security | licences |
| 62 | 3 kalem bilişim sistemi cihazı | computers | custom_software |
| 53 / 212 / 282 | Bilişim cihazları; bilgisayar ve donanım; kırtasiye ve bilişim sarf | computers | other_IT |
| 129 | Dijital konferans ve videowall sistemi | other_IT | custom_software |
| 168 | Hizmet masası yönetimi, uzaktan destek yazılımı | call_centre_helpdesk | custom_software |
| 201 | Gemi Bilgi Sistemi (GEBİS) malzemeleri | other_IT | ERP |
| 236 | Kurumsal eğitim yönetimi planlama sistemi ve OSCE yazılımı | education | custom_software |

## Genuinely ambiguous titles (examples)
- **Multi-product bundles**, where any single label is arbitrary:
  - 218: KGYS servers, storage, network security, virtualisation, DB and backup (physical security vs network).
  - 281: security licences, server warranty, virtualisation and antivirus licences.
  - 233: Microsoft plus antivirus licences.
  - 68: hardware maintenance plus network-security updates.
- **Library, dormitory and e-campus systems** (251, 258, 283, 154): ERP vs education technology.
- **Disaster information systems** (31, 43, 248): GIS vs custom software vs network.
- **Plate recognition** (207): physical security (KGYS-PTS) vs traffic OT.
- **Citizen-relations and complaint systems** (184, 226, 103): helpdesk vs ERP vs GIS.
- **Uninformative titles** (130 "YAZILIM ALIMI", 277 "Tümas Sistem Güncellemesi", 147 "EKS servis ve yazılım").

## Scope flags (not classifier errors)
Four sampled "main-scope" titles are barely IT products:
- 60: 143 items including construction, cleaning and stationery.
- 88: employing 3 forest engineers for a biodiversity project.
- 205: a blockchain workshop.
- 200: training for neighbourhood heads (muhtar) on an information system.

Consider re-checking the scope rules for multi-item "kalem" purchases and for event or staffing services.

## Implications for the paper
- The health IT results (HHI, incumbency) rest on a class with about 99% precision and recall in this check, so they are robust to classifier error.
- For market-level results in cybersecurity, custom software, maintenance, education and other_IT, report the moderate agreement (F1 0.45–0.69). Either merge `other_IT` or drop it as a stand-alone market in market-specific tables.
- Rule fixes that would remove most of the clear errors:
  - Add the cybersecurity keywords şifreleme/maskeleme, filtreleme, güvenlik cihazı, güvenlik testi, 5651 and SAST.
  - Give "web sitesi / portal / içerik yönetim" precedence over "yönetim sistemi".
  - Map "coğrafi" to GIS before ERP, and "diş hekimliği bilgi sistemi" to health.
  - Map "bilgisayar / bilişim cihaz / sarf" to computers rather than other_IT.
  - Map PLC/SCADA/EKS to OT.
- Suggested manuscript wording: "An AI-assisted re-annotation of a random sample of 300 titles (seed 7), blind to the rule labels, agreed with the rule in 77% of cases (Cohen's κ = 0.74; 82%, κ = 0.80, excluding inherently multi-product titles); agreement for health information systems was 99%." The model-generated nature of the reference labels should be disclosed.
