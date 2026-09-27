# Price (discount) analysis — EKAP detail sample

Collected OK: 144; with estimated cost and contract value in TRY: 143; used (discount in [-0.5, 1]): 143.
Contract value on EKAP equals our recorded value (ratio within 1%): 0.993 of rows with comparable original amounts and currencies; missing currency labels are explicitly assumed TRY.

## Discount by incumbency

| group | n | mean discount | median | share with zero discount |
|---|---|---|---|---|
| incumbent winner | 73 | 0.121 | 0.089 | 0.082 |
| other winner | 70 | 0.165 | 0.112 | 0.043 |
| renewal: incumbent | 46 | 0.120 | 0.087 | 0.043 |
| renewal: other | 9 | 0.156 | 0.019 | 0.000 |
| new need: incumbent | 27 | 0.123 | 0.101 | 0.148 |
| new need: other | 61 | 0.166 | 0.132 | 0.049 |

## OLS: discount on incumbency (HC1 SEs)

- `discount ~ incumbent_win`: incumbent coefficient -0.044 (SE 0.027, p = 0.105), n = 143
- `discount ~ incumbent_win + renew + C(proc) + np.log(real_value) + year`: incumbent coefficient -0.060 (SE 0.038, p = 0.113), n = 143
- `discount ~ incumbent_win + renew + C(proc) + np.log(real_value) + year + C(market)`: incumbent coefficient -0.050 (SE 0.041, p = 0.220), n = 143

## Bids (detail pages)

| group | n with counts | mean valid bids | share single valid bid |
|---|---|---|---|
| incumbent winner | 33 | 1.79 | 0.485 |
| other winner | 35 | 1.34 | 0.657 |

## OKAS (CPV) division by rule-based product market (first listed code)

```
cpv2                               16  30  31  32  34  35  48  50  63  71  72  77  79  92
urun_pazari                                                                              
ERP_management_software             0   1   0   0   0   0   3   1   0   0  17   0   0   1
GIS_city_information                0   0   0   0   0   0   0   0   0   0   3   0   0   0
computers_peripherals               0   2   0   1   1   0   0   1   0   0   1   0   0   0
custom_software_web_mobile          1   0   0   0   0   0   4   0   0   0   7   0   0   0
cybersecurity                       0   0   0   0   0   0   0   0   0   0   2   0   0   1
health_information_systems          0   0   0   0   0   0   1   3   1   0  41   0   0   0
maintenance_support_services        0   0   0   0   0   0   0   5   0   2   7   0   0   0
network_datacentre_infrastructure   0   0   0   0   0   0   3   1   0   0   4   0   0   0
other_IT                            0   0   0   0   0   0   0   1   0   0   1   1   1   0
physical_security_surveillance      0   1   0   0   0   1   1   0   0   0   0   0   0   0
smart_city_traffic_OT               0   0   1   0   0   0   1   0   0   0   0   0   0   0
software_licences                   0   0   0   0   0   0   7   1   0   0  11   0   0   0
```
