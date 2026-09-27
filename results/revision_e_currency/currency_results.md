# Currency-assumption sensitivity

Main N=9,991; exclusion removes 845 unspecified-currency records (5.27% of main real value), leaving 9,146.

Explicit currencies are USD/EUR/TRY labels in the preserved source string; this is not independent source revalidation. Missing labels are assumed TRY in the primary specification. Exclusion changes sample composition and is a sensitivity, not an imputation or identified bound.

## HHI point estimates

| Market | Main value HHI | Explicit-currency value HHI |
|---|---:|---:|
| ALL | 147.244 | 158.514 |
| ERP_management_software | 130.683 | 139.671 |
| GIS_city_information | 407.938 | 416.904 |
| call_centre_helpdesk | 8892.990 | 8922.208 |
| computers_peripherals | 169.164 | 181.965 |
| custom_software_web_mobile | 261.811 | 193.901 |
| cybersecurity | 475.736 | 489.020 |
| education_technology | 1062.062 | 1092.862 |
| health_information_systems | 831.069 | 872.608 |
| maintenance_support_services | 298.996 | 331.517 |
| network_datacentre_infrastructure | 280.410 | 299.123 |
| other_IT | 757.266 | 790.483 |
| physical_security_surveillance | 212.138 | 219.617 |
| smart_city_traffic_OT | 2447.789 | 2367.269 |
| software_licences | 273.597 | 289.944 |

## Contract-level incumbency sensitivity (linear probability model)

Same controls and fixed effects as the primary A1 model; histories are constructed before exclusions. Linear probability coefficients use two-way buyer/winning-firm clustered 95% intervals. The explicit-currency-only A1 logit failed to converge with Newton (200 iterations), so we report comparable linear probability fits for both samples instead of unstable odds ratios. No choice-model or full-pipeline rerun is implied.

| Sample | N | Term | Coefficient | 95% interval |
|---|---:|---|---:|---|
| main_assumed_TRY | 4913 | log_real_value | -0.0038 | -0.0183–0.0108 |
| main_assumed_TRY | 4913 | p21b_x_post | 0.1189 | 0.0299–0.2078 |
| explicit_currency_only | 4786 | log_real_value | -0.0050 | -0.0197–0.0098 |
| explicit_currency_only | 4786 | p21b_x_post | 0.1384 | 0.0508–0.2261 |

## Corrected top-150 screen

Ranking uses nominal `bedel_try` across all 13,024 records. 1 records enter beyond the historical top-150 review. `legacy_scope_review_recorded` documents membership in the archived review; `new_scope_review_required` identifies entrants. No new hand review or independent currency verification is claimed. Historical `data/audit/top150_value_review.csv` remains unchanged and was ranked by the mixed-currency legacy numeric amount.

The entrant IKN 2023/670417 has an AI-assisted official-source scope check: the [DHMI tender notice](https://www.dhmi.gov.tr/Lists/IhaleIlanlari/Attachments/1455/ihale%20ilan%C4%B1-de.%C4%B1c%C4%B1ng.pdf) identifies eight de-icing vehicles and the exact IKN on page 1, with tender date 01.09.2023 on page 3. This corroborates the existing non-IT scope label and tender identity. It is not new human validation; the EUR 2,631,200 award amount has not been independently verified against an official award-price source.
