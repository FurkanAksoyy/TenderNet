"""Discount analysis on the EKAP detail sample (data/ekap_detail_sample.csv).

Discount = 1 - contract value / estimated cost (yaklaşık maliyet). Compares contracts won by the
buyer's incumbent supplier with other repeat-eligible contracts (the sample was drawn 75/75 from
the two groups, blind to the collector). Also checks EKAP contract values against our data, bid
counts, and the product-market classification against OKAS (CPV) codes.
Output: results/price/price_results.md
"""
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "price"
OUT.mkdir(parents=True, exist_ok=True)


def tr_num(x):
    if pd.isna(x) or str(x).strip() == "":
        return np.nan
    s = str(x).strip()
    # EKAP shows both Turkish (1.581.000,00) and English (1,581,000.00) formats:
    # the last separator is the decimal mark.
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if len(s.split(",")[-1]) == 2 else s.replace(",", "")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[-1]) == 3):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return np.nan


d = pd.read_csv(ROOT / "data" / "ekap_detail_sample.csv", dtype=str)
d = d[d["status"] == "ok"].copy()
for c in ["sozlesme_bedeli", "yaklasik_maliyet", "en_yuksek_teklif", "en_dusuk_teklif"]:
    d[c + "_n"] = d[c].map(tr_num)
for c in ["n_dokuman_indiren", "n_teklif_veren", "n_gecerli_teklif"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")

h = pd.read_csv(ROOT / "results" / "models" / "contracts_with_history.csv")
h["IKN"] = h["IKN"].astype(str)
ren = pd.read_csv(ROOT / "results" / "revision_a" / "A_renewal_flags.csv", usecols=["IKN", "renewal"])
m = pd.read_csv(ROOT / "data" / "contracts_v3.csv", usecols=["IKN", "bedel_num", "urun_pazari"], low_memory=False).drop_duplicates("IKN")
x = d.merge(h, on="IKN", how="left").merge(ren, on="IKN", how="left").merge(m, on="IKN", how="left")
x = x[x["para_birimi"].fillna("TRY").str.upper().isin(["TRY", "TL", ""])]
x["discount"] = 1 - x["sozlesme_bedeli_n"] / x["yaklasik_maliyet_n"]
x["value_match"] = (x["sozlesme_bedeli_n"] / x["bedel_num"]).round(3)
x["single_valid"] = (x["n_gecerli_teklif"] == 1).astype(float).where(x["n_gecerli_teklif"].notna())
x["renew"] = (x["renewal"] == "renewal").astype(int)
x["proc"] = np.where(x["usul_v3"].eq("negotiated_21b"), "21b", np.where(x["usul_v3"].eq("open"), "open", "other"))
v = x[x["discount"].notna() & x["discount"].between(-0.5, 1)].copy()

L = ["# Price (discount) analysis — EKAP detail sample", "",
     f"Collected OK: {len(d)}; with estimated cost and contract value in TRY: {x['discount'].notna().sum()}; "
     f"used (discount in [-0.5, 1]): {len(v)}.",
     f"Contract value on EKAP equals our recorded value (ratio within 1%): {((x['value_match'] - 1).abs() <= 0.01).mean():.3f} of matched rows.", ""]
L += ["## Discount by incumbency", "", "| group | n | mean discount | median | share with zero discount |", "|---|---|---|---|---|"]
for name, g in [("incumbent winner", v[v.incumbent_win == 1]), ("other winner", v[v.incumbent_win == 0])]:
    L.append(f"| {name} | {len(g)} | {g.discount.mean():.3f} | {g.discount.median():.3f} | {(g.discount.abs() < 0.005).mean():.3f} |")
for r_ in [1, 0]:
    for name, g in [("incumbent", v[(v.incumbent_win == 1) & (v.renew == r_)]), ("other", v[(v.incumbent_win == 0) & (v.renew == r_)])]:
        L.append(f"| {'renewal' if r_ else 'new need'}: {name} | {len(g)} | {g.discount.mean():.3f} | {g.discount.median():.3f} | {(g.discount.abs() < 0.005).mean():.3f} |")

L += ["", "## OLS: discount on incumbency (HC1 SEs)", ""]
for f in ["discount ~ incumbent_win", "discount ~ incumbent_win + renew + C(proc) + np.log(real_value) + year",
          "discount ~ incumbent_win + renew + C(proc) + np.log(real_value) + year + C(market)"]:
    try:
        r = smf.ols(f, data=v).fit(cov_type="HC1")
        b, se, p = r.params["incumbent_win"], r.bse["incumbent_win"], r.pvalues["incumbent_win"]
        L.append(f"- `{f}`: incumbent coefficient {b:+.3f} (SE {se:.3f}, p = {p:.3f}), n = {int(r.nobs)}")
    except Exception as e:  # noqa: BLE001
        L.append(f"- `{f}`: failed ({e})")

L += ["", "## Bids (detail pages)", "", "| group | n with counts | mean valid bids | share single valid bid |", "|---|---|---|---|"]
for name, g in [("incumbent winner", x[x.incumbent_win == 1]), ("other winner", x[x.incumbent_win == 0])]:
    gg = g[g.n_gecerli_teklif.notna()]
    L.append(f"| {name} | {len(gg)} | {gg.n_gecerli_teklif.mean():.2f} | {gg.single_valid.mean():.3f} |")

# OKAS (CPV) check of product-market classification: division (first 2 digits) of the first code
x["cpv2"] = x["okas_codes"].fillna("").str.split(";").str[0].str[:2]
L += ["", "## OKAS (CPV) division by rule-based product market (first listed code)", ""]
tab = pd.crosstab(x["urun_pazari"], x["cpv2"])
L.append("```\n" + tab.to_string() + "\n```")
(OUT / "price_results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
v.to_csv(OUT / "price_sample_analysis.csv", index=False)
print("\n".join(L))
