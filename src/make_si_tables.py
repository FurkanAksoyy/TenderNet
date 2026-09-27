"""Generate LaTeX tables for the Supplementary Information directly from result CSVs.

Output: paper/si_tables/*.tex (included by paper/tendernet_si.tex).
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = ROOT / "paper" / "si_tables"
OUT.mkdir(parents=True, exist_ok=True)

MARKET_LABEL = {
    "health_information_systems": "Health information systems",
    "ERP_management_software": "ERP / management software",
    "custom_software_web_mobile": "Custom software / web / mobile",
    "software_licences": "Software licences",
    "network_datacentre_infrastructure": "Network / data-centre infrastructure",
    "computers_peripherals": "Computers / peripherals",
    "maintenance_support_services": "Maintenance / support services",
    "physical_security_surveillance": "Physical security / surveillance",
    "GIS_city_information": "GIS / city information",
    "cybersecurity": "Cybersecurity",
    "smart_city_traffic_OT": "Smart city / traffic",
    "education_technology": "Education technology",
    "call_centre_helpdesk": "Call centre / help desk",
    "other_IT": "Other IT",
    "ALL (aggregate)": "All categories pooled",
}


PROC_LABEL = {"negotiated_21b": "Article 21(b)", "negotiated_21c": "Article 21(c)", "negotiated_21f": "Article 21(f)",
              "negotiated_21a": "Article 21(a)", "negotiated_21d": "Article 21(d)", "negotiated_21e": "Article 21(e)",
              "open": "Open", "restricted": "Restricted"}


def tex(x):
    return str(x).replace("&", r"\&").replace("_", " ").replace("%", r"\%")


def lab(x):
    return MARKET_LABEL.get(x, PROC_LABEL.get(x, tex(x)))


def fmt(x, d=0):
    if pd.isna(x):
        return "--"
    return f"{x:,.{d}f}"


def write(name, body):
    (OUT / f"{name}.tex").write_text(body, encoding="utf-8")


# --- S: scope classes -------------------------------------------------------
m = pd.read_csv(ROOT / "data" / "contracts_v3.csv", low_memory=False)
g = m.groupby("scope_v3").agg(n=("scope_v3", "size"), v=("bedel_try", "sum"))
g["share_v"] = 100 * g["v"] / g["v"].sum()
order = ["IT", "IT_service_callcentre", "gray", "nonIT"]
names = {"IT": "IT", "IT_service_callcentre": "IT-enabled call-centre services",
         "gray": "Ambiguous (excluded from main sample)", "nonIT": "Not IT (removed)"}
rows = "\n".join(f"{names[k]} & {fmt(g.loc[k,'n'])} & {fmt(g.loc[k,'v']/1e9,2)} & {fmt(g.loc[k,'share_v'],1)}\\\\" for k in order)
write("scope", rf"""\begin{{tabular}}{{@{{}}lrrr@{{}}}}
\toprule
Scope class & Contracts & Nominal value (bn TRY) & Share of value (\%)\\
\midrule
{rows}
\midrule
Total & {fmt(g['n'].sum())} & {fmt(g['v'].sum()/1e9,2)} & 100.0\\
\botrule
\end{{tabular}}""")

# --- S: concentration by market ---------------------------------------------
c = pd.read_csv(RES / "concentration" / "supplier_hhi_by_market.csv")
c = c.sort_values("n_contracts", ascending=False)
agg = c[c["group"].str.startswith("ALL")]
c = pd.concat([c[~c["group"].str.startswith("ALL")], agg])
rows = []
for _, r in c.iterrows():
    rows.append(
        f"{lab(r['group'])} & {fmt(r['n_contracts'])} & {fmt(r['n_firms'])} & "
        f"{fmt(r['HHI_count'])} [{fmt(r['HHI_count_lo'])}, {fmt(r['HHI_count_hi'])}] & "
        f"{fmt(r['HHI_value'])} [{fmt(r['HHI_value_lo'])}, {fmt(r['HHI_value_hi'])}] & "
        f"{fmt(r['HHI_value_nomax'])} & {fmt(r['HHI_value_wins'])} & {fmt(r['CR4_value'],0)}\\\\")
write("concentration", r"""\begin{tabular}{@{}lrrrrrrr@{}}
\toprule
Product category & Contracts & Firms & HHI count [95\% CI] & HHI value [95\% CI] & Value, no max & Value, winsor. & CR4 value (\%)\\
\midrule
""" + "\n".join(rows) + r"""
\botrule
\end{tabular}""")

# --- S: within-year HHI summary ---------------------------------------------
w = pd.read_csv(RES / "concentration" / "within_year_hhi_summary.csv")
(OUT / "within_year_columns.txt").write_text(",".join(w.columns), encoding="utf-8")

# --- S: lock-in by market and by group ---------------------------------------
nb = pd.read_csv(RES / "lockin" / "null_by_group.csv")


def group_table(dim, label_fn=lab, sort_by="excess"):
    base = nb[(nb.variant == "main_N1") & (nb.dimension == dim)].set_index("group")
    n2 = nb[(nb.variant == "main_N2") & (nb.dimension == dim)].set_index("group")
    n3 = nb[(nb.variant == "S8_cell_market_x_year_x_province") & (nb.dimension == dim)].set_index("group")
    base = base.sort_values(sort_by, ascending=False) if sort_by else base
    out = []
    for gname, r in base.iterrows():
        out.append(
            f"{label_fn(gname)} & {fmt(r['n_eligible'])} & {fmt(r['obs'],3)} & "
            f"{fmt(r['null_mean'],3)} [{fmt(r['null_lo'],3)}, {fmt(r['null_hi'],3)}] & "
            f"{fmt(n2.loc[gname,'null_mean'],3) if gname in n2.index else '--'} & "
            f"{fmt(n3.loc[gname,'null_mean'],3) if gname in n3.index else '--'}\\\\")
    return "\n".join(out)


HEAD = r"""\begin{tabular}{@{}lrrrrr@{}}
\toprule
%s & Eligible & Observed & N1 null [95\%% interval] & N2 null & N3 null\\
\midrule
"""
TAIL = "\n\\botrule\n\\end{tabular}"
write("lockin_market", HEAD % "Product category" + group_table("market") + TAIL)
write("lockin_sector", HEAD % "Buyer sector" + group_table("sector") + TAIL)
write("lockin_buyertype", HEAD % "Buyer type" + group_table("buyer_type") + TAIL)
write("lockin_procedure", HEAD % "Procedure" + group_table("procedure_fine") + TAIL)
write("lockin_year", HEAD % "Year" + group_table("year", lambda x: str(int(float(x))), sort_by=None) + TAIL)

# --- S: sensitivities ---------------------------------------------------------
o = pd.read_csv(RES / "lockin" / "null_overall.csv")
o = o[o.statistic == "incumbency"]
vlabel = {
    "main_N1": "Main (N1: market $\\times$ year)",
    "main_N1w": "N1 with 3-year windows",
    "main_N2": "N2: market $\\times$ year $\\times$ sector",
    "S8_cell_market_x_year_x_province": "N3: market $\\times$ year $\\times$ province",
    "S1_buyer_kurum": "Buyer = recorded label",
    "S2_firm_original": "Firm = recorded name",
    "S3_excl_MHRS_callcentre": "Excluding call-centre contracts",
    "S4_incl_gray": "Including ambiguous scope",
    "S5_cell_sector_x_year": "Cells = buyer sector $\\times$ year",
    "S6_incumbency_buyer_level_any_market": "Incumbency at buyer level (any market)",
    "S7_excl_21f": "Excluding Article 21(f) contracts",
}
rows = "\n".join(
    f"{vlabel.get(r.variant, r.variant)} & {fmt(r.obs,3)} & {fmt(r.null_mean,3)} [{fmt(r.null_lo,3)}, {fmt(r.null_hi,3)}] & {fmt(r.ratio,1)}\\\\"
    for r in o.itertuples())
write("sensitivity", r"""\begin{tabular}{@{}lrrr@{}}
\toprule
Variant & Observed & Null mean [95\% interval] & Ratio\\
\midrule
""" + rows + TAIL)

# --- S: dyad continuation (model B) -------------------------------------------
TERM = {
    "p_21b": "First contract under 21(b) (vs open)",
    "p_oth_neg": "First contract other negotiated (vs open)",
    "log_real_value": "Log real value of first contract",
    "log_firm_prior_contracts": "Log firm prior contracts (other buyers)",
    "log_firm_prior_markets": "Log firm prior markets (generalism)",
    "log_firm_prior_buyers": "Log firm prior distinct buyers",
    "log_buyer_prior_contracts": "Log buyer prior contracts",
    "log_opp": "Log later opportunities of buyer in market",
}


def btab(fname, exp_label):
    b = pd.read_csv(RES / "models" / fname)
    b = b[b.term.isin(TERM)]
    return "\n".join(
        f"{TERM[r.term]} & {fmt(r.exp,2)} [{fmt(r.exp_lo,2)}, {fmt(r.exp_hi,2)}] & {'<0.001' if r.p < 0.001 else f'{r.p:.3f}'}\\\\" for r in b.itertuples())


for name, f, lbl in [("B_logit", "B_logit_full.csv", "OR"), ("B_nb2", "B_nb2_full.csv", "IRR"),
                     ("B_logit_gen", "B_logit_generalism_only.csv", "OR"), ("B_logit_size", "B_logit_size_only.csv", "OR")]:
    write(name, r"""\begin{tabular}{@{}lrr@{}}
\toprule
 & %s [95\%% CI] & $p$\\
\midrule
""" % lbl + btab(f, lbl) + TAIL)

# --- S: single bidding ---------------------------------------------------------
d = pd.read_csv(RES / "models" / "D_single_bid_rates.csv")
GLAB = {"all": "All tenders", "open": "Open", "21b": "Article 21(b)", "21f": "Article 21(f)", "oth_neg": "Other negotiated",
        "incumbent winner": "Winner is incumbent", "non-incumbent winner": "Winner not previous supplier in market",
        "buyer first in market (undefined)": "Buyer's first contract in market",
        "pre-7144": "Before 25 May 2018", "post-7144": "After 25 May 2018"}
rows = []
for r in d[(d.outcome == "single") & (d.breakdown.isin(["overall", "procedure", "incumbency", "period (tender date vs 2018-05-25)"]))].itertuples():
    v = d[(d.outcome == "single_valid") & (d.breakdown == r.breakdown) & (d.group == r.group)].iloc[0]
    ci = f"[{100*r.lo95:.0f}, {100*r.hi95:.0f}]" if pd.notna(r.lo95) else ""
    rows.append(f"{GLAB.get(r.group, tex(r.group))} & {r.n} & {100*r.rate_w:.1f} {ci} & {100*v.rate_w:.1f}\\\\")
write("single_bid", r"""\begin{tabular}{@{}lrrr@{}}
\toprule
Group & Tenders & Single bid, \% [95\% CI] & Single valid bid, \%\\
\midrule
""" + "\n".join(rows) + TAIL)

# --- S: within-year concentration ---------------------------------------------
w = w.sort_values("HHI_count_med", ascending=False)
rows = "\n".join(
    f"{lab(r.market)} & {int(r.n_years)} & {fmt(r.HHI_count_med)} & {fmt(r.HHI_count_unb_med)} & {fmt(r.HHI_value_med)} & {fmt(r.HHI_value_nomax_med)}\\\\"
    for r in w.itertuples())
write("within_year", r"""\begin{tabular}{@{}lrrrrr@{}}
\toprule
Product category & Years & Count HHI & Count HHI, bias-corr. & Value HHI & Value HHI, no max\\
\midrule
""" + rows + TAIL)
print("written to", OUT)
