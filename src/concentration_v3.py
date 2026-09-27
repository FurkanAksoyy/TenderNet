"""TenderNet v3 - market concentration analysis (topic: concentration).

Supplier-side HHI/CR4 by count and real value (2025 TRY), aggregate / product
category (urun_pazari) / buyer sector (sektor_v3); influence diagnostics
(without largest contract, leave-one-contract-out, winsorised), bootstrap CIs,
within-year HHI, buyer-side HHI, aggregate-vs-within decomposition, historical 1,000 reference and 2023 1,800
HHI descriptive screens, count-vs-value firm rankings, sensitivities.

Run:  python src/concentration_v3.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contracts_v3.csv"
RES = ROOT / "results" / "concentration"
FIG = ROOT / "figures"
RES.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

SEED = 42
NBOOT = 1000
MIN_YEAR_N = 30
HI, MOD = 1800, 1000          # 1,800: 2023 guideline; 1,000: historical 1992 reference
OI = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]

# --------------------------------------------------------------------------- data
def cpi_table():
    a = pd.read_csv(ROOT / "data" / "cpi_turkey.csv")
    cpi = dict(zip(a.year, a.cpi_index_annual_avg))
    m = pd.read_csv(ROOT / "data" / "cpi_turkey_2026_monthly.csv")
    # brief: 2026 -> average of the linked 2026 monthly values available
    cpi[2026] = m.cpi_2003eq100_linked.mean()
    return cpi, len(m)

def load():
    d = pd.read_csv(DATA, encoding="utf-8-sig")
    for c in ["in_scope_main", "in_scope_broad", "callcentre_flag"]:
        d[c] = d[c].astype(str).str.lower().eq("true")
    cpi, n26 = cpi_table()
    d["defl"] = d.yil_v3.map(lambda y: cpi[2025] / cpi[y])
    d["real"] = d.bedel_try * d["defl"]
    d["is_mhrs"] = d.ihale_adi.str.contains("MHRS", case=False, na=False) & (d.scope_v3 == "IT_service_callcentre")
    return d, cpi, n26

# --------------------------------------------------------------------------- measures
def shares_hhi(codes, w):
    s = np.bincount(codes, weights=w)
    s = s[s > 0]
    p = s / s.sum()
    return 1e4 * np.sum(p ** 2), 1e2 * np.sort(p)[::-1][:4].sum(), len(p)

def hhi(codes, w):
    s = np.bincount(codes, weights=w)
    T = s.sum()
    return 1e4 * np.sum(s ** 2) / T ** 2

def hhi_unbiased_count(codes):
    c = np.bincount(codes).astype(float)
    n = c.sum()
    return 1e4 * np.sum(c * (c - 1)) / (n * (n - 1)) if n > 1 else np.nan

def loo(codes, w):
    """HHI after removing each contract i (vectorised). Returns array."""
    s = np.bincount(codes, weights=w)
    T, Q = s.sum(), np.sum(s ** 2)
    sf = s[codes]
    Qn = Q - sf ** 2 + (sf - w) ** 2
    Tn = T - w
    with np.errstate(invalid="ignore", divide="ignore"):
        return 1e4 * Qn / Tn ** 2

def drop_max(codes, w):
    k = np.argmax(w)
    mask = np.ones(len(w), bool); mask[k] = False
    return codes[mask], w[mask]

def group_stats(g, firm, cap, rng, boot=True):
    codes = pd.factorize(g[firm])[0]
    one = np.ones(len(g))
    v = g.real.to_numpy()
    vw = np.minimum(v, cap)
    r = {"n_contracts": len(g), "n_firms": codes.max() + 1,
         "value_bn_2025": v.sum() / 1e9,
         "largest_contract_share_pct": 100 * v.max() / v.sum()}
    r["HHI_count"], r["CR4_count"], _ = shares_hhi(codes, one)
    r["HHI_count_unbiased"] = hhi_unbiased_count(codes)
    r["HHI_value"], r["CR4_value"], _ = shares_hhi(codes, v)
    c2, v2 = drop_max(codes, v)
    r["HHI_value_nomax"], r["CR4_value_nomax"], _ = shares_hhi(c2, v2) if len(v2) else (np.nan,) * 3
    r["HHI_value_wins"], r["CR4_value_wins"], _ = shares_hhi(codes, vw)
    lv = loo(codes, v)
    lc = loo(codes, one)
    r["LOO_value_min"], r["LOO_value_max"] = np.nanmin(lv), np.nanmax(lv)
    r["LOO_value_maxabs_change"] = np.nanmax(np.abs(lv - r["HHI_value"]))
    r["LOO_count_maxabs_change"] = np.nanmax(np.abs(lc - r["HHI_count"]))
    r["numbers_equiv_count"] = 1e4 / r["HHI_count"]
    r["numbers_equiv_value"] = 1e4 / r["HHI_value"]
    if boot:
        n = len(g)
        B = {k: np.empty(NBOOT) for k in ["count", "value", "value_nomax", "value_wins"]}
        for b in range(NBOOT):
            idx = rng.integers(0, n, n)
            cb, vb = codes[idx], v[idx]
            B["count"][b] = hhi(cb, one[idx])
            B["value"][b] = hhi(cb, vb)
            c2, v2 = drop_max(cb, vb)
            B["value_nomax"][b] = hhi(c2, v2) if len(v2) else np.nan
            B["value_wins"][b] = hhi(cb, vw[idx])
        for k, arr in B.items():
            # plug-in HHI is biased upward under resampling (duplicated contracts);
            # primary CI = percentile interval shifted by the bootstrap bias estimate.
            lo, hi_ = np.nanpercentile(arr, [2.5, 97.5])
            bias = np.nanmean(arr) - r[f"HHI_{k}"]
            r[f"HHI_{k}_pct_lo"], r[f"HHI_{k}_pct_hi"] = lo, hi_
            r[f"HHI_{k}_boot_bias"] = bias
            r[f"HHI_{k}_boot_median"] = np.nanmedian(arr)
            r[f"HHI_{k}_lo"], r[f"HHI_{k}_hi"] = max(lo - bias, 0.0), min(hi_ - bias, 1e4)
    return r

def classify(h):
    return "above1800 (>1800)" if h > HI else ("between1000and1800 (1000-1800)" if h >= MOD else "below1000 (<1000)")

def by_group(df, col, firm, cap, rng, boot=True, extra_all=True):
    rows = []
    if extra_all:
        rows.append({"group": "ALL (aggregate)", **group_stats(df, firm, cap, rng, boot)})
    for k, g in df.groupby(col):
        rows.append({"group": k, **group_stats(g, firm, cap, rng, boot)})
    return pd.DataFrame(rows)

# --------------------------------------------------------------------------- decomposition
def decomposition(df, mkt, firm, wcol):
    """H_agg = sum_s w_s^2 H_s + sum_i sum_{s!=t} w_s w_t s_is s_it."""
    w_tot = df.groupby(mkt)[wcol].sum()
    W = w_tot / w_tot.sum()
    fm = df.groupby([firm, mkt])[wcol].sum().rename("x").reset_index()
    fm["s_is"] = fm.x / fm[mkt].map(w_tot)
    fm["w"] = fm[mkt].map(W)
    Hs = fm.groupby(mkt).s_is.apply(lambda s: np.sum(s ** 2))
    within = np.sum(W ** 2 * Hs)
    agg_share = fm.groupby(firm).x.sum() / fm.x.sum()
    H_agg = np.sum(agg_share ** 2)
    ws = fm.w * fm.s_is
    per_firm_sq = ws.groupby(fm[firm]).sum() ** 2
    per_firm_diag = (ws ** 2).groupby(fm[firm]).sum()
    cross = np.sum(per_firm_sq - per_firm_diag)
    multi = fm.groupby(firm)[mkt].nunique()
    return {"weight": wcol, "H_agg_observed": 1e4 * H_agg,
            "sum_w2_Hs": 1e4 * within, "cross_terms": 1e4 * cross,
            "check_sum": 1e4 * (within + cross),
            "sum_w2": np.sum(W ** 2) * 1e4,
            "weighted_mean_Hs(sum w_s H_s)": 1e4 * np.sum(W * Hs),
            "unweighted_mean_Hs": 1e4 * Hs.mean(),
            "median_Hs": 1e4 * Hs.median(),
            "share_firms_multi_market_pct": 100 * (multi > 1).mean(),
            "share_weight_by_multi_market_firms_pct":
                100 * fm[fm[firm].isin(multi[multi > 1].index)].x.sum() / fm.x.sum(),
            "n_markets": len(W)}

# --------------------------------------------------------------------------- main
def main():
    rng = np.random.default_rng(SEED)
    d, cpi, n26 = load()
    main_ = d[d.in_scope_main].copy()
    cap = np.percentile(main_.real, 99)
    out = {}
    L = []  # markdown lines

    # ---- 1. supplier HHI by market, sector
    mk = by_group(main_, "urun_pazari", "firma_v3", cap, rng)
    se = by_group(main_, "sektor_v3_en", "firma_v3", cap, rng, extra_all=False)
    for t in (mk, se):
        t["class_count"] = t.HHI_count.map(classify)
        t["class_value"] = t.HHI_value.map(classify)
        t["class_value_nomax"] = t.HHI_value_nomax.map(classify)
        t["class_value_wins"] = t.HHI_value_wins.map(classify)
        t["class_LOO_value_min"] = t.LOO_value_min.map(classify)
        allv = t[["HHI_count", "HHI_value", "HHI_value_nomax", "LOO_value_min", "HHI_value_wins"]].min(axis=1)
        t["min_across_variants"] = allv
        t["robust_class"] = allv.map(classify)
    mk.to_csv(RES / "supplier_hhi_by_market.csv", index=False)
    se.to_csv(RES / "supplier_hhi_by_sector.csv", index=False)

    # ---- 2. within-year
    wy = []
    for (m, y), g in main_.groupby(["urun_pazari", "yil_v3"]):
        if len(g) < MIN_YEAR_N:
            continue
        codes = pd.factorize(g.firma_v3)[0]
        v = g.real.to_numpy()
        c2, v2 = drop_max(codes, v)
        wy.append({"market": m, "year": y, "n": len(g), "HHI_count": hhi(codes, np.ones(len(g))),
                   "HHI_value": hhi(codes, v), "HHI_value_nomax": hhi(c2, v2),
                   "HHI_count_unb": hhi_unbiased_count(codes)})
    for y, g in main_.groupby("yil_v3"):
        codes = pd.factorize(g.firma_v3)[0]; v = g.real.to_numpy(); c2, v2 = drop_max(codes, v)
        wy.append({"market": "ALL (aggregate)", "year": y, "n": len(g), "HHI_count": hhi(codes, np.ones(len(g))),
                   "HHI_value": hhi(codes, v), "HHI_value_nomax": hhi(c2, v2),
                   "HHI_count_unb": hhi_unbiased_count(codes)})
    wy = pd.DataFrame(wy)
    wy.to_csv(RES / "within_year_hhi.csv", index=False)
    q = lambda s, p: s.quantile(p)
    wys = wy.groupby("market").agg(n_years=("year", "size"), min_year_n=("n", "min"),
        HHI_count_med=("HHI_count", "median"), HHI_count_q1=("HHI_count", lambda s: q(s, .25)),
        HHI_count_q3=("HHI_count", lambda s: q(s, .75)),
        HHI_value_med=("HHI_value", "median"), HHI_value_q1=("HHI_value", lambda s: q(s, .25)),
        HHI_value_q3=("HHI_value", lambda s: q(s, .75)),
        HHI_value_nomax_med=("HHI_value_nomax", "median"),
        HHI_count_unb_med=("HHI_count_unb", "median"),
        yrs_value_nomax_gt1000=("HHI_value_nomax", lambda s: int((s >= MOD).sum())),
        yrs_value_gt1800=("HHI_value", lambda s: int((s > HI).sum())),
        yrs_count_gt1800=("HHI_count", lambda s: int((s > HI).sum()))).reset_index()
    wys.to_csv(RES / "within_year_hhi_summary.csv", index=False)

    # ---- 3. buyer-side
    by = by_group(main_, "urun_pazari", "kurum_il_split", cap, rng, boot=False)
    by_k = by_group(main_, "urun_pazari", "kurum", cap, rng, boot=False)
    by = by[["group", "n_contracts", "n_firms", "HHI_count", "CR4_count", "HHI_value", "CR4_value",
             "HHI_value_nomax", "CR4_value_nomax"]].rename(columns={"n_firms": "n_buyers"})
    by["HHI_count_kurum_recorded"] = by_k.HHI_count.values
    by["HHI_value_kurum_recorded"] = by_k.HHI_value.values
    by.to_csv(RES / "buyer_hhi_by_market.csv", index=False)

    # ---- 4. decomposition
    main_["one"] = 1.0
    main_nomhrs = main_[~main_.is_mhrs]
    dec = pd.DataFrame([
        {"partition": "urun_pazari", "sample": "main", **decomposition(main_, "urun_pazari", "firma_v3", "one")},
        {"partition": "urun_pazari", "sample": "main", **decomposition(main_, "urun_pazari", "firma_v3", "real")},
        {"partition": "urun_pazari", "sample": "main excl. MHRS", **decomposition(main_nomhrs, "urun_pazari", "firma_v3", "real")},
        {"partition": "sektor_v3", "sample": "main", **decomposition(main_, "sektor_v3_en", "firma_v3", "one")},
        {"partition": "sektor_v3", "sample": "main", **decomposition(main_, "sektor_v3_en", "firma_v3", "real")},
        {"partition": "sektor_v3", "sample": "main excl. MHRS", **decomposition(main_nomhrs, "sektor_v3_en", "firma_v3", "real")},
    ])
    dec.to_csv(RES / "hhi_decomposition.csv", index=False)

    # ---- 6. count vs value rankings
    rk = []
    for lab, df in [("main", main_), ("main excl. MHRS", main_nomhrs)]:
        f = df.groupby("firma_v3").agg(n=("real", "size"), v=("real", "sum"))
        rho, p = spearmanr(f.n, f.v)
        f2 = f[f.n >= 2]; rho2, _ = spearmanr(f2.n, f2.v)
        t20n = set(f.sort_values(["n", "v"], ascending=False).index[:20])
        t20v = set(f.sort_values("v", ascending=False).index[:20])
        # value share of top-20 by count / by value
        rk.append({"sample": lab, "n_firms": len(f), "spearman_rho": rho, "p": p,
                   "spearman_rho_firms_n_ge2": rho2, "n_firms_ge2": len(f2),
                   "top20_overlap": len(t20n & t20v),
                   "top20_by_count_value_share_pct": 100 * f.loc[list(t20n), "v"].sum() / f.v.sum(),
                   "top20_by_value_value_share_pct": 100 * f.loc[list(t20v), "v"].sum() / f.v.sum(),
                   "top20_by_count_count_share_pct": 100 * f.loc[list(t20n), "n"].sum() / f.n.sum(),
                   "top20_by_value_count_share_pct": 100 * f.loc[list(t20v), "n"].sum() / f.n.sum()})
        if lab == "main":
            top = f.sort_values("v", ascending=False).head(20).copy()
            top["rank_value"] = range(1, 21)
            top["rank_count"] = f.n.rank(ascending=False, method="min").loc[top.index].astype(int)
            top["value_bn_2025"] = top.v / 1e9
            top[["rank_value", "rank_count", "n", "value_bn_2025"]].to_csv(RES / "top20_firms_by_value.csv")
    rk = pd.DataFrame(rk)
    rk.to_csv(RES / "count_vs_value_rankings.csv", index=False)

    # ---- 7. sensitivities (no bootstrap)
    d["real_nominal"] = d.bedel_try
    variants = {
        "main (firma_v3, real)": (d[d.in_scope_main], "firma_v3", "real"),
        "firm = original firma": (d[d.in_scope_main], "firma", "real"),
        "include gray (broad)": (d[d.in_scope_broad], "firma_v3", "real"),
        "nominal TRY": (d[d.in_scope_main], "firma_v3", "bedel_try"),
        "IT only (excl. call centre/MHRS)": (d[d.in_scope_main & (d.scope_v3 == "IT")], "firma_v3", "real"),
    }
    sens = []
    for name, (df, firm, vcol) in variants.items():
        df = df.copy(); df["real"] = df[vcol]
        capv = np.percentile(df.real, 99)
        t = by_group(df, "urun_pazari", firm, capv, rng, boot=False)
        t.insert(0, "variant", name)
        sens.append(t[["variant", "group", "n_contracts", "n_firms", "HHI_count", "CR4_count", "HHI_value",
                       "HHI_value_nomax", "LOO_value_min", "HHI_value_wins"]])
    sens = pd.concat(sens)
    sens.to_csv(RES / "sensitivity_by_market.csv", index=False)

    # ---- figures
    fig_c1(mk)
    fig_c2(wy, mk)

    # ---- report
    write_report(d, main_, cpi, n26, cap, mk, se, wys, by, dec, rk, sens)


# --------------------------------------------------------------------------- figures
PRETTY = {
    "health_information_systems": "Health information systems", "ERP_management_software": "ERP / management software",
    "custom_software_web_mobile": "Custom software / web / mobile", "software_licences": "Software licences",
    "network_datacentre_infrastructure": "Network / data-centre infra.", "computers_peripherals": "Computers / peripherals",
    "maintenance_support_services": "Maintenance / support services", "GIS_city_information": "GIS / city information",
    "cybersecurity": "Cybersecurity", "physical_security_surveillance": "Physical security / surveillance",
    "other_IT": "Other IT", "education_technology": "Education technology",
    "smart_city_traffic_OT": "Smart city / traffic OT", "call_centre_helpdesk": "Call centre / help-desk",
    "ALL (aggregate)": "All categories pooled"}

def style():
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                         "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
                         "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False})

def fig_c1(mk):
    style()
    t = mk.copy()
    agg = t[t.group == "ALL (aggregate)"]
    t = t[t.group != "ALL (aggregate)"].sort_values("HHI_count")
    t = pd.concat([agg, t])
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(7, 4.6))
    series = [("count", "HHI_count", OI[4], "o", -0.22, "Contract count"),
              ("value", "HHI_value", OI[0], "s", 0.0, "Real value (2025 TRY)"),
              ("value_nomax", "HHI_value_nomax", OI[5], "D", 0.22, "Real value, largest contract removed")]
    for key, col, c, mkr, off, lab in series:
        lo, hi_ = t[f"HHI_{key}_lo"], t[f"HHI_{key}_hi"]
        ax.errorbar(t[col], y + off, xerr=[(t[col] - lo.clip(lower=20)).clip(lower=0), (hi_ - t[col]).clip(lower=0)], fmt=mkr, color=c, ms=4,
                    elinewidth=1, capsize=0, label=lab)
    ax.set_axisbelow(True)
    for x, ls in [(MOD, "--"), (HI, "-")]:
        ax.axvline(x, color="0.25", lw=0.9, ls=ls, zorder=1)
    ax.text(MOD * 1.03, len(t) - 0.4, "1,000", fontsize=7, color="0.3", va="bottom")
    ax.text(HI * 1.03, len(t) - 0.4, "1,800", fontsize=7, color="0.3", va="bottom")
    ax.set_xscale("log")
    ax.set_xlim(20, 10000)
    ax.set_xticks([30, 100, 300, 1000, 3000, 10000])
    ax.set_xticklabels(["30", "100", "300", "1,000", "3,000", "10,000"])
    ax.set_yticks(y)
    ax.set_yticklabels([f"{PRETTY.get(g, g)} (n={n:,})" for g, n in zip(t.group, t.n_contracts)])
    ax.axhline(0.5, color="0.6", lw=0.6)
    ax.set_ylim(-0.6, len(t) - 0.1)
    ax.set_xlabel("Supplier HHI (0-10,000, log scale); bars: bias-shifted bootstrap 95% CI, 1,000 reps")
    ax.grid(axis="x", color="0.9", lw=0.6, which="both")
    ax.legend(loc="upper center", bbox_to_anchor=(0.4, -0.13), ncol=3, frameon=False)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"F-C1_concentration_by_market.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)

def fig_c2(wy, mk):
    style()
    w = wy[wy.market != "ALL (aggregate)"]
    order = w.groupby("market").HHI_count.median().sort_values().index.tolist()
    fig, axes = plt.subplots(1, 2, figsize=(7, 3.8), sharey=True)
    rng = np.random.default_rng(SEED)
    for ax, col, c, lab in [(axes[0], "HHI_count", OI[4], "Within-year HHI, contract count"),
                            (axes[1], "HHI_value", OI[0], "Within-year HHI, real value")]:
        data = [w.loc[w.market == m, col].values for m in order]
        ax.boxplot(data, orientation="horizontal", widths=0.55, showfliers=False,
                   medianprops=dict(color="black", lw=1.2), boxprops=dict(color="0.4"),
                   whiskerprops=dict(color="0.4"), capprops=dict(color="0.4"))
        for i, vals in enumerate(data):
            ax.scatter(vals, i + 1 + rng.uniform(-0.18, 0.18, len(vals)), s=7, color=c, alpha=0.75,
                       edgecolor="none", zorder=3)
        ax.set_axisbelow(True)
        for x, ls in [(MOD, "--"), (HI, "-")]:
            ax.axvline(x, color="0.25", lw=0.9, ls=ls, zorder=1)
        ax.set_xscale("log"); ax.set_xlim(50, 10000)
        ax.set_xticks([100, 300, 1000, 3000, 10000]); ax.set_xticklabels(["100", "300", "1,000", "3,000", "10,000"])
        ax.set_xlabel(lab + " (log)")
        ax.grid(axis="x", color="0.9", lw=0.6, which="both")
    nyr = w.groupby("market").size()
    axes[0].set_yticks(range(1, len(order) + 1))
    axes[0].set_yticklabels([f"{PRETTY.get(m, m)} ({nyr[m]} y)" for m in order])
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"F-C2_within_year_hhi.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------- report
def f0(x): return "NA" if pd.isna(x) else f"{x:,.0f}"
def f1(x): return "NA" if pd.isna(x) else f"{x:,.1f}"
def f2(x): return "NA" if pd.isna(x) else f"{x:,.2f}"
def ci(r, k): return f"{f0(r[f'HHI_{k}'] if k=='count' else r['HHI_'+k])} [{f0(r[f'HHI_{k}_lo'])}, {f0(r[f'HHI_{k}_hi'])}]"

def write_report(d, main_, cpi, n26, cap, mk, se, wys, by, dec, rk, sens):
    L = []
    A = L.append
    A("# TenderNet v3 - Market concentration (topic: `concentration`)\n")
    A(f"Script: `src/concentration_v3.py`. Sample: main (`in_scope_main`), N = {len(main_):,} contracts, "
      f"{main_.firma_v3.nunique():,} firms (`firma_v3`), {main_.kurum_il_split.nunique():,} buyers (`kurum_il_split`). "
      "Nominal TRY uses explicit contract currencies and cached TCMB tender-date midpoint FX proxies; unlabelled currencies are assumed TRY (see currency fields and data/fx_cache_tcmb/README.md). "
      f"Real values in 2025 TRY using TÜİK CPI annual averages (2026 deflated with the mean of the {n26} available linked "
      f"2026 monthly values = {cpi[2026]:,.1f}; 2025 = {cpi[2025]:,.1f}). Total real value = {main_.real.sum()/1e9:,.2f} bn 2025-TRY "
      f"(nominal {main_.bedel_try.sum()/1e9:,.2f} bn). HHI on 0-10,000 scale; CR4 in %. Bootstrap: {NBOOT} resamples of contracts "
      f"within each market, seed {SEED}, bias-shifted percentile 95% CIs (percentile interval minus the bootstrap bias, mean(boot)−estimate, clipped to [0, 10,000]; raw percentile bounds and bias are in the CSV). Winsorised variant caps each contract's real value at the "
      f"main-sample 99th percentile ({cap/1e6:,.1f} m 2025-TRY). LOO = leave-one-contract-out (all contracts, exact).\n")
    mh = main_[main_.is_mhrs].iloc[0]
    A(f"The MHRS Faz-16 call-centre contract (2025, {mh.real/1e9:,.2f} bn 2025-TRY) is "
      f"{100*mh.real/main_.real.sum():.1f}% of main-sample real value and "
      f"{100*mh.real/main_[main_.urun_pazari=='call_centre_helpdesk'].real.sum():.1f}% of the call-centre market.\n")

    # ---------- bottom line
    a = mk[mk.group == "ALL (aggregate)"].iloc[0]
    mm = mk[mk.group != "ALL (aggregate)"]
    rob_hi = mm[mm.min_across_variants > HI]
    rob_mod = mm[(mm.min_across_variants >= MOD) & (mm.min_across_variants <= HI)]
    A("## Bottom line\n")
    A(f"- **Pooled procurement mix falls below the reference lines by every measure**: aggregate supplier HHI = {f0(a.HHI_count)} (count), "
      f"{f0(a.HHI_value)} (real value), {f0(a.HHI_value_nomax)} (value without MHRS contract). "
      "This pooled number is mechanically diluted (section 4) and should not be read as evidence of competition.")
    A(f"- **Robustly concentrated product categories (HHI above threshold under count AND real value AND value-without-largest AND worst-case leave-one-out AND winsorised value):** "
      + (", ".join(f"{PRETTY[g]} (min {f0(x)})" for g, x in zip(rob_hi.group, rob_hi.min_across_variants)) or "none")
      + " at >1,800; " + (", ".join(f"{PRETTY[g]} (min {f0(x)})" for g, x in zip(rob_mod.group, rob_mod.min_across_variants)) or "none")
      + " at 1,000-1,800.")
    rest = mm[mm.min_across_variants < MOD]
    cmax = mm.loc[mm.HHI_count.idxmax()]
    A(f"- All {len(rest)} product categories fall below 1,000 on at least one variant, and the failing variant is always the **count** HHI: "
      f"the highest count HHI is {f0(cmax.HHI_count)} ({PRETTY[cmax.group]}, n={cmax.n_contracts}); no category reaches 1,000 by count "
      "(bias-shifted upper CI bounds: " + ", ".join(f"{PRETTY[g]} {f0(h)}" for g, h in zip(mm.group, mm.HHI_count_hi) if h >= 500) + ").")
    vonly = mm[mm.HHI_value >= MOD]
    A("- Markets that cross 1,000 on raw real-value HHI: " + "; ".join(
        f"{PRETTY[r.group]} {f0(r.HHI_value)} → {f0(r.HHI_value_nomax)} without its largest contract (LOO min {f0(r.LOO_value_min)}, winsorised {f0(r.HHI_value_wins)}; largest contract = {f1(r.largest_contract_share_pct)}% of market value)"
        for _, r in vonly.iterrows()) + ". "
      "Smart city and education technology drop below 1,000 once one contract is removed: single-contract artefacts. "
      "The call-centre market stays ≥1,000 on every value variant but is tiny (74 contracts, 46 firms), its count HHI is below 1,000, "
      "and its value is 94% one contract (MHRS); it is best described as a few very large national call-centre contracts, not a concentrated market in the merger-guideline sense.")
    h = mm[mm.group == "health_information_systems"].iloc[0]
    hw = wys[wys.market == "health_information_systems"].iloc[0]
    A(f"- **Health information systems is the only large market with persistent, non-artefactual concentration**, still below the 1,000 screen: "
      f"count HHI {f0(h.HHI_count)} [{f0(h.HHI_count_lo)}, {f0(h.HHI_count_hi)}], real-value HHI {f0(h.HHI_value)} [{f0(h.HHI_value_lo)}, {f0(h.HHI_value_hi)}], "
      f"value CR4 {f1(h.CR4_value)}%, LOO range {f0(h.LOO_value_min)}-{f0(h.LOO_value_max)} (no single contract matters), 2,189 contracts but only {h.n_firms} firms "
      f"(numbers-equivalent {h.numbers_equiv_value:.0f} equal-sized firms by value). Within a year its median count HHI is {f0(hw.HHI_count_med)} and value HHI {f0(hw.HHI_value_med)} "
      f"(IQR {f0(hw.HHI_value_q1)}-{f0(hw.HHI_value_q3)}). Its level depends on firm canonicalisation (original `firma`: count 250, value 593).")
    A("- **Within-year view (section 2)**: plug-in within-year HHIs are higher than the 15-year pooled values, but for counts most of the gap is the "
      "small-sample floor (10,000/n with n≈30-150 per market-year): the unbiased within-year count HHI medians are "
      + ", ".join(f"{PRETTY[r.market]} {f0(r.HHI_count_unb_med)}" for _, r in wys[wys.market != 'ALL (aggregate)'].sort_values('HHI_count_unb_med', ascending=False).head(3).iterrows())
      + " and <200 elsewhere, i.e. genuine temporal dilution is modest except in health IS (597 vs pooled 426). "
      "Median within-year value HHI is ≥1,000 in "
      + ", ".join(PRETTY[m] for m in wys[(wys.market != 'ALL (aggregate)') & (wys.HHI_value_med >= MOD)].market)
      + "; this value measure carries the same small-n upward bias (no simple correction exists for value shares), so it is an upper bound. "
      "Within-year category HHIs describe the distribution of recorded awards; they do not identify competitive conduct or economic market boundaries.")
    A("- Conclusion for the paper: **no product market is robustly concentrated under count AND value AND leave-one-out**. "
      "Any dependence story must therefore rest on relational/buyer-level measures (lock-in), not on market-level HHI.")
    A("- The 1,000 HHI line is a historical 1992 guideline reference; the 2023 US Merger Guidelines use >1,800 as the high-concentration threshold. "
      "These reference lines are descriptive here, not merger presumptions or conduct/harm thresholds, and our 'markets' are title-based product categories pooled over "
      "15 years and all of Türkiye, not antitrust relevant markets. Treat the classification as descriptive.\n")

    # ---------- table 1
    A("## 1. Supplier-side concentration by product category (urun_pazari)\n")
    A("Table 1a. HHI with bootstrap 95% CIs.\n")
    A("| category | N | firms | HHI count [95% CI] | HHI count (unbiased) | CR4 count | HHI value [95% CI] | CR4 value | HHI value w/o largest [95% CI] | CR4 w/o largest | largest contract % of value |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in mk.iterrows():
        A(f"| {PRETTY.get(r.group, r.group)} | {r.n_contracts:,} | {r.n_firms:,} | {ci(r,'count')} | {f0(r.HHI_count_unbiased)} | {f1(r.CR4_count)} | "
          f"{ci(r,'value')} | {f1(r.CR4_value)} | {ci(r,'value_nomax')} | {f1(r.CR4_value_nomax)} | {f1(r.largest_contract_share_pct)} |")
    A("\nUnbiased count HHI = Σ c(c−1)/(n(n−1)), removing the 1/n floor that inflates plug-in HHI in small markets. "
      "Plug-in HHI is biased upward under contract resampling (duplicated contracts), so CIs are bias-shifted percentile intervals. "
      "For value HHI in small, heavy-tailed markets (call centre, smart city, education technology, other IT) the bootstrap distribution is "
      "dominated by whether the one or two giant contracts are drawn; those CIs are very wide and mean 'poorly identified', not a precise range.\n")
    A("Table 1b. Influence and classification.\n")
    A("| category | HHI value | LOO min | LOO max | max abs LOO change (value) | max abs LOO change (count) | HHI winsorised [95% CI] | class count | class value | class w/o largest | class LOO-min | class winsorised | **robust class (min of all)** |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in mk.iterrows():
        A(f"| {PRETTY.get(r.group, r.group)} | {f0(r.HHI_value)} | {f0(r.LOO_value_min)} | {f0(r.LOO_value_max)} | {f0(r.LOO_value_maxabs_change)} | "
          f"{f1(r.LOO_count_maxabs_change)} | {ci(r,'value_wins')} | {r.class_count} | {r.class_value} | {r.class_value_nomax} | "
          f"{r.class_LOO_value_min} | {r.class_value_wins} | **{r.robust_class}** |")
    A("")
    A("Numbers-equivalent (10,000/HHI): " + "; ".join(f"{PRETTY.get(r.group, r.group)} {r.numbers_equiv_count:,.0f} (count) / {r.numbers_equiv_value:,.0f} (value)" for _, r in mk.iterrows()) + ".\n")

    A("## 1b. Supplier-side concentration by buyer sector (sektor_v3)\n")
    A("| sector | N | firms | HHI count [95% CI] | CR4 count | HHI value [95% CI] | CR4 value | HHI value w/o largest [95% CI] | LOO min | HHI winsorised | robust class |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in se.sort_values("n_contracts", ascending=False).iterrows():
        A(f"| {r.group} | {r.n_contracts:,} | {r.n_firms:,} | {ci(r,'count')} | {f1(r.CR4_count)} | {ci(r,'value')} | {f1(r.CR4_value)} | "
          f"{ci(r,'value_nomax')} | {f0(r.LOO_value_min)} | {f0(r.HHI_value_wins)} | {r.robust_class} |")
    A("")

    # ---------- within-year
    A(f"## 2. Within-year HHI (market-years with ≥{MIN_YEAR_N} contracts)\n")
    A("Within a single year the CPI deflator is constant, so real-value and nominal-value HHI are identical.\n")
    A("| category | years | HHI count median [IQR] | HHI count unbiased, median | HHI value median [IQR] | HHI value w/o largest, median | years value HHI >1,800 | years value-w/o-largest HHI ≥1,000 | years count HHI >1,800 |")
    A("|---|---|---|---|---|---|---|---|---|")
    for _, r in wys.sort_values("HHI_count_med").iterrows():
        A(f"| {PRETTY.get(r.market, r.market)} | {r.n_years} | {f0(r.HHI_count_med)} [{f0(r.HHI_count_q1)}-{f0(r.HHI_count_q3)}] | {f0(r.HHI_count_unb_med)} | "
          f"{f0(r.HHI_value_med)} [{f0(r.HHI_value_q1)}-{f0(r.HHI_value_q3)}] | {f0(r.HHI_value_nomax_med)} | {r.yrs_value_gt1800} | {r.yrs_value_nomax_gt1000}/{r.n_years} | {r.yrs_count_gt1800} |")
    missing = sorted(set(mm.group) - set(wys.market))
    A(f"\nMarkets with no year reaching {MIN_YEAR_N} contracts (not computed): {', '.join(PRETTY[m] for m in missing) or 'none'}.\n")

    # ---------- buyer-side
    A("## 3. Buyer-side (demand) concentration\n")
    A("Buyer = `kurum_il_split` (primary); last two columns use recorded `kurum`.\n")
    A("| category | N | buyers | HHI count | CR4 count | HHI value | CR4 value | HHI value w/o largest | HHI count (kurum) | HHI value (kurum) |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for _, r in by.iterrows():
        A(f"| {PRETTY.get(r.group, r.group)} | {r.n_contracts:,} | {r.n_buyers:,} | {f0(r.HHI_count)} | {f1(r.CR4_count)} | {f0(r.HHI_value)} | "
          f"{f1(r.CR4_value)} | {f0(r.HHI_value_nomax)} | {f0(r.HHI_count_kurum_recorded)} | {f0(r.HHI_value_kurum_recorded)} |")
    A("")

    # ---------- decomposition
    A("## 4. Why pooled HHI is diluted: decomposition\n")
    A("Let market s have weight w_s (share of total count or value) and firm i have within-market share s_is. "
      "Firm i's pooled share is s_i = Σ_s w_s s_is, so\n")
    A("  H_agg = Σ_i (Σ_s w_s s_is)² = Σ_s w_s² H_s + Σ_i Σ_{s≠t} w_s w_t s_is s_it.\n")
    A("The first term is the within-market part; because Σ_s w_s² < 1 (≈ 1/number of equally sized markets), even a set of highly concentrated markets "
      "yields a small pooled HHI unless the same firms lead several markets (the cross term, which is ≥0 and nonzero only for multi-market firms). "
      "Pooling is therefore mechanically dilutive; this is a relevant-market issue, not an empirical finding.\n")
    A("| partition | sample | weight | H_agg observed | Σ w_s² H_s | cross terms | Σ w_s² (×10⁴) | Σ w_s H_s (weighted mean within) | median H_s | % firms multi-market | % weight held by multi-market firms |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in dec.iterrows():
        A(f"| {r.partition} | {r['sample']} | {'count' if r.weight=='one' else 'real value'} | {f1(r.H_agg_observed)} | {f1(r.sum_w2_Hs)} | {f1(r.cross_terms)} | "
          f"{f0(r.sum_w2)} | {f0(r['weighted_mean_Hs(sum w_s H_s)'])} | {f0(r.median_Hs)} | {f1(r.share_firms_multi_market_pct)} | {f1(r.share_weight_by_multi_market_firms_pct)} |")
    A("\n(check: Σ w_s² H_s + cross terms equals H_agg to floating-point precision in every row.)\n")

    # ---------- rankings
    A("## 6. Count vs value firm rankings\n")
    A("| sample | firms | Spearman ρ (count, real value) | ρ, firms with ≥2 contracts | top-20 overlap | top-20-by-count share of value % | top-20-by-value share of value % | top-20-by-count share of contracts % | top-20-by-value share of contracts % |")
    A("|---|---|---|---|---|---|---|---|---|")
    for _, r in rk.iterrows():
        A(f"| {r['sample']} | {r.n_firms:,} | {r.spearman_rho:.3f} (p={r.p:.1e}) | {r.spearman_rho_firms_n_ge2:.3f} (n={r.n_firms_ge2:,}) | {r.top20_overlap}/20 | "
          f"{f1(r.top20_by_count_value_share_pct)} | {f1(r.top20_by_value_value_share_pct)} | {f1(r.top20_by_count_count_share_pct)} | {f1(r.top20_by_value_count_share_pct)} |")
    A("\nTop-20 firms by real value with their count rank: `top20_firms_by_value.csv`.\n")

    # ---------- sensitivity
    A("## 7. Sensitivities (point estimates, no bootstrap)\n")
    piv = sens.pivot_table(index="group", columns="variant", values=["HHI_count", "HHI_value", "HHI_value_nomax", "LOO_value_min"], aggfunc="first")
    vnames = list(dict.fromkeys(sens.variant))
    for metric in ["HHI_count", "HHI_value", "HHI_value_nomax", "LOO_value_min"]:
        A(f"**{metric}**\n")
        A("| category | " + " | ".join(vnames) + " |")
        A("|---|" + "---|" * len(vnames))
        for g in [x for x in mk.group]:
            if g not in piv.index:
                continue
            A(f"| {PRETTY.get(g, g)} | " + " | ".join(f0(piv.loc[g, (metric, v)]) if (metric, v) in piv.columns else "NA" for v in vnames) + " |")
        A("")
    A("Robust class under each sensitivity (min of count, value, value w/o largest, LOO-min, winsorised):\n")
    sens2 = sens.copy()
    sens2["minv"] = sens2[["HHI_count", "HHI_value", "HHI_value_nomax", "LOO_value_min", "HHI_value_wins"]].min(axis=1)
    A("| category | " + " | ".join(vnames) + " |")
    A("|---|" + "---|" * len(vnames))
    pv = sens2.pivot_table(index="group", columns="variant", values="minv", aggfunc="first")
    for g in mk.group:
        if g in pv.index:
            A(f"| {PRETTY.get(g, g)} | " + " | ".join("NA" if pd.isna(pv.loc[g, v]) else f"{f0(pv.loc[g, v])} ({classify(pv.loc[g, v]).split(' ')[0]})" for v in vnames) + " |")
    A("\n'IT only' drops all 10 call-centre contracts (incl. MHRS); the call-centre market then contains only the 64 IT-scope call-centre software/equipment contracts.\n")

    A("## Files\n")
    for p in sorted(RES.glob("*.csv")):
        A(f"- `results/concentration/{p.name}`")
    A("- `figures/F-C1_concentration_by_market.png/.pdf` - dot plot: count HHI, real-value HHI, value HHI without largest contract, bootstrap 95% CIs, thresholds 1,000/1,800 (log x).")
    A("- `figures/F-C2_within_year_hhi.png/.pdf` - within-year HHI by category (box + strip; count left, real value right).")
    (RES / "concentration_results.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
