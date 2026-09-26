"""Create blind coding sheets for human validation by the two authors.

Outputs (in human_coding/): one Excel workbook per coder with two sheets
  - markets:  300 tender titles (same random sample as the AI-assisted check), empty label column
  - renewals: 60 title pairs (same sample as the AI-assisted check), empty label column
No rule-based or AI labels are included, so the coding is blind.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "human_coding"
OUT.mkdir(exist_ok=True)

MARKETS = ["health_information_systems", "ERP_management_software", "custom_software_web_mobile",
           "software_licences", "network_datacentre_infrastructure", "computers_peripherals",
           "maintenance_support_services", "physical_security_surveillance", "GIS_city_information",
           "cybersecurity", "smart_city_traffic_OT", "education_technology", "call_centre_helpdesk", "other_IT"]

cv = pd.read_csv(ROOT / "data" / "audit" / "classifier_validation.csv")
title_col = next(c for c in cv.columns if "title" in c.lower() or "ihale_adi" in c.lower())
markets = cv[["IKN", title_col]].rename(columns={title_col: "tender_title"}).copy()
markets["your_label"] = ""
markets["ambiguous_(y/n)"] = ""
markets["note"] = ""

rp = pd.read_csv(ROOT / "results" / "revision_a" / "A_renewal_validation_sample.csv")
keep = ["pair_id"] + [c for c in rp.columns if any(k in c.lower() for k in ["title", "days"])]
renew = rp[keep].copy()
renew["same_recurring_need_(same/different/unclear)"] = ""
renew["note"] = ""

instructions = pd.DataFrame({"instructions": [
    "Code independently; do not discuss with the other coder until both are done.",
    "Sheet 'markets': choose ONE label per title from the list in sheet 'labels'. Mark ambiguous=y if two labels fit equally.",
    "Sheet 'renewals': decide whether the later tender renews the SAME recurring service/product as the earlier one.",
    "Return the file as <coder>_coded.xlsx; agreement (Cohen's kappa) will be computed against the other coder and the rules.",
]})
labels = pd.DataFrame({"allowed_market_labels": MARKETS})

for coder in ["FurkanAksoy", "ArdaSimsek"]:
    with pd.ExcelWriter(OUT / f"coding_sheet_{coder}.xlsx") as xw:
        instructions.to_excel(xw, sheet_name="instructions", index=False)
        markets.to_excel(xw, sheet_name="markets", index=False)
        renew.to_excel(xw, sheet_name="renewals", index=False)
        labels.to_excel(xw, sheet_name="labels", index=False)
print("markets:", len(markets), "renewal pairs:", len(renew), "->", OUT)
print("renewal columns:", keep)
