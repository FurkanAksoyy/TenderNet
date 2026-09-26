"""TenderNet v3 - lock-in / excess repeat contracting analysis.

Research question: do Turkish public IT buyers return to the same suppliers more
often than chance, given each buyer's demand and each firm's market activity?

Definitions (see results/lockin/lockin_results.md for the full text):
  dyad            = (buyer, firm) pair with >=1 contract (all markets pooled)
  repeat dyad     = dyad with >=2 contracts
  incumbency rate = among contracts of buyer k in product market m that have at
                    least one earlier contract of k in m (strictly earlier
                    tender date), the share won by a firm that had already won
                    from k in m on a strictly earlier date.
Null models: winner labels permuted within cells
  N1  : product market x calendar year
  N1w : product market x 3-year window (2010-12, 13-15, ..., 25-26)
  N2  : product market x calendar year x buyer sector (sektor_v3)
Run: python src/lockin_analysis.py
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contracts_v3.csv"
OUT = ROOT / "results" / "lockin"
FIG = ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

B = int(__import__("os").environ.get("LOCKIN_B", 1000))
SEED = 42
LAW7144 = pd.Timestamp("2018-05-25")
OI = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "axes.grid": True, "grid.color": "#dddddd", "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
})


# ---------------------------------------------------------------- data prep
def load():
    d = pd.read_csv(DATA, encoding="utf-8-sig", low_memory=False)
    d["date"] = pd.to_datetime(d["tarih_v3"])
    return d


def proc3(u):
    return np.where(u == "negotiated_21b", "21(b)", np.where(u == "open", "open", "other"))


def prepare(df, buyer_col="kurum_il_split", firm_col="firma_v3",
            inc_market_col="urun_pazari"):
    df = df.copy().reset_index(drop=True)
    P = {}
    P["df"] = df
    P["buyer"] = pd.factorize(df[buyer_col])[0].astype(np.int64)
    P["firm"] = pd.factorize(df[firm_col])[0].astype(np.int64)
    P["nb"] = P["buyer"].max() + 1
    P["nf"] = P["firm"].max() + 1
    # market used in the incumbency definition (constant string -> buyer-level)
    if inc_market_col is None:
        P["mkt"] = np.zeros(len(df), dtype=np.int64)
    else:
        P["mkt"] = pd.factorize(df[inc_market_col])[0].astype(np.int64)
    P["day"] = (df["date"] - pd.Timestamp("2010-01-01")).dt.days.values.astype(np.int64)
    # eligibility: buyer-market has a strictly earlier contract
    bm = P["buyer"] * (P["mkt"].max() + 1) + P["mkt"]
    mind = pd.Series(P["day"]).groupby(bm).transform("min").values
    P["elig"] = P["day"] > mind
    P["bm"] = bm
    # buyer size (contracts of buyer in this sample)
    bsize = np.bincount(P["buyer"])[P["buyer"]]
    P["bsize"] = bsize
    return P


def cells(df, kind):
    y = df["yil_v3"].astype(int)
    if kind == "N1":
        key = df["urun_pazari"].astype(str) + "|" + y.astype(str)
    elif kind == "N1w":
        key = df["urun_pazari"].astype(str) + "|" + ((y - 2010) // 3).astype(str)
    elif kind == "N2":
        key = df["urun_pazari"].astype(str) + "|" + y.astype(str) + "|" + df["sektor_v3"].astype(str)
    elif kind == "N3":
        key = df["urun_pazari"].astype(str) + "|" + y.astype(str) + "|" + df["il"].fillna("NA").astype(str)
    elif kind == "SECT":
        key = df["sektor_v3"].astype(str) + "|" + y.astype(str)
    else:
        raise ValueError(kind)
    return pd.factorize(key)[0].astype(np.int64)


def tr_upper(x):
    return str(x).replace("i", "İ").replace("ı", "I").upper()


def buyer_type(label, sector):
    """Coarse, anonymous buyer type from the buyer label (keyword rules, first match wins)."""
    u = tr_upper(label)
    uni = any(k in u for k in ["ÜNİVERSİTE", "YÜKSEKÖĞRETİM", "FAKÜLTE"])
    health_kw = any(k in u for k in ["HASTANE", "DİŞ SAĞLIĞI", "SAĞLIK", "TIP ", "TIP FAK", "DİŞ HEKİM"])
    if any(k in u for k in ["İL SAĞLIK", "KAMU HASTANE BİRLİĞİ", "KAMU HASTANELER", "HALK SAĞLIĞI MÜD", "ASHB"]):
        return "MoH provincial directorate / hospital union"
    if uni and health_kw:
        return "University hospital / medical faculty"
    if uni:
        return "University (non-health unit)"
    if any(k in u for k in ["HASTANE", "DİŞ SAĞLIĞI", "SAĞLIK MERKEZ"]):
        return "MoH hospital / dental centre"
    if "BELEDİYE" in u or sector == "Municipal/Local":
        return "Municipality / municipal company"
    if sector == "Health":
        return "Other health body (central/agency)"
    if any(k in u for k in ["BAKANLIĞI", "GENEL MÜDÜRLÜĞÜ", "BAŞKANLIĞI", "KURUMU"]):
        return "Central government / agency"
    return "Other"


# ---------------------------------------------------------------- statistics
def incumbent(P, firm):
    key = P["bm"] * P["nf"] + firm
    day = P["day"]
    idx = np.lexsort((day, key))
    ks, ds = key[idx], day[idx]
    start = np.r_[True, ks[1:] != ks[:-1]]
    grp = np.cumsum(start) - 1
    mind = ds[start][grp]
    inc = np.empty(len(day), dtype=bool)
    inc[idx] = ds > mind
    return inc


def dyad_stats(P, firm, big_buyers=None):
    key = P["buyer"] * P["nf"] + firm
    u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    n_dyads = len(u)
    n_rep = int((cnt >= 2).sum())
    share_rep = float((cnt[inv] >= 2).mean())
    maxw = int(cnt.max())
    res = dict(dyads=n_dyads, repeat_dyads=n_rep, share_in_repeat=share_rep,
               repeat_dyad_share=n_rep / n_dyads, max_w=maxw)
    buyer_stats = None
    if big_buyers is not None:
        ub = u // P["nf"]
        top = np.zeros(P["nb"]); np.maximum.at(top, ub, cnt)
        ss = np.zeros(P["nb"]); np.add.at(ss, ub, cnt.astype(float) ** 2)
        n = np.bincount(P["buyer"], minlength=P["nb"]).astype(float)
        buyer_stats = (top[big_buyers] / n[big_buyers], ss[big_buyers] / n[big_buyers] ** 2)
    return res, buyer_stats


def group_rates(inc, elig, g, ng):
    num = np.bincount(g[elig], weights=inc[elig].astype(float), minlength=ng)
    den = np.bincount(g[elig], minlength=ng).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return num / den, den


def permute_within(firm, cell, rng):
    order = np.argsort(cell, kind="stable")
    perm = np.lexsort((rng.random(len(cell)), cell))
    out = np.empty_like(firm)
    out[order] = firm[perm]
    return out


def summarize(obs, null, B):
    null = np.asarray(null, dtype=float)
    ok = ~np.isnan(null)
    nl = null[ok]
    if len(nl) == 0 or np.isnan(obs):
        return dict(obs=obs, null_mean=np.nan, null_lo=np.nan, null_hi=np.nan,
                    ratio=np.nan, excess=np.nan, z=np.nan, p_upper=np.nan, p_lower=np.nan)
    m, s = nl.mean(), nl.std(ddof=1)
    return dict(obs=obs, null_mean=m, null_lo=np.percentile(nl, 2.5), null_hi=np.percentile(nl, 97.5),
                ratio=obs / m if m else np.nan, excess=obs - m, z=(obs - m) / s if s > 0 else np.nan,
                p_upper=(1 + (nl >= obs - 1e-12).sum()) / (len(nl) + 1),
                p_lower=(1 + (nl <= obs + 1e-12).sum()) / (len(nl) + 1))


# ---------------------------------------------------------------- groupings
def groupings(P):
    df = P["df"]
    G = {}
    G["market"] = df["urun_pazari"].astype(str).values
    G["sector"] = df["sektor_v3_en"].astype(str).values
    G["procedure"] = proc3(df["usul_v3"].values)
    G["procedure_fine"] = df["usul_v3"].astype(str).values
    q1, q2 = np.quantile(P["bsize"], [1 / 3, 2 / 3])
    G["buyer_size_tercile"] = np.where(P["bsize"] <= q1, f"T1 small (<= {int(q1)} contracts)",
                                       np.where(P["bsize"] <= q2, f"T2 mid ({int(q1)+1}-{int(q2)})",
                                                f"T3 large (> {int(q2)})"))
    G["law7144"] = np.where(df["date"] < LAW7144, "pre (< 2018-05-25)", "post (>= 2018-05-25)")
    G["year"] = df["yil_v3"].astype(int).astype(str).values
    G["buyer_type"] = np.array([buyer_type(l, sct) for l, sct in zip(df["kurum_il_split"], df["sektor_v3_en"])])
    G["law7144_x_procedure"] = np.char.add(np.char.add(G["law7144"].astype(str), " / "),
                                           G["procedure"].astype(str))
    out = {}
    for k, v in G.items():
        codes, labels = pd.factorize(pd.Series(v))
        out[k] = (codes.astype(np.int64), list(labels))
    return out


# ---------------------------------------------------------------- driver
def run_variant(P, cell, B, seed, with_groups=True, big_min=5):
    rng = np.random.default_rng(seed)
    firm = P["firm"]
    elig = P["elig"]
    big = None
    if big_min:
        nbc = np.bincount(P["buyer"], minlength=P["nb"])
        big = np.where(nbc >= big_min)[0]
    Gs = groupings(P) if with_groups else {}

    def one(f):
        inc = incumbent(P, f)
        ds, bs = dyad_stats(P, f, big)
        r = dict(ds)
        r["incumbency"] = inc[elig].mean()
        r["n_eligible"] = int(elig.sum())
        r["n_incumbent"] = int(inc[elig].sum())
        grs = {k: group_rates(inc, elig, c, len(l))[0] for k, (c, l) in Gs.items()}
        return r, grs, bs

    obs, obs_g, obs_b = one(firm)
    nulls = {k: [] for k in obs}
    null_g = {k: [] for k in Gs}
    null_top, null_hhi = [], []
    for _ in range(B):
        f = permute_within(firm, cell, rng)
        r, grs, bs = one(f)
        for k in r:
            nulls[k].append(r[k])
        for k in grs:
            null_g[k].append(grs[k])
        if bs is not None:
            null_top.append(bs[0]); null_hhi.append(bs[1])
    overall = {k: summarize(obs[k], nulls[k], B) for k in
               ["dyads", "repeat_dyads", "share_in_repeat", "repeat_dyad_share", "max_w", "incumbency"]}
    overall["_n_eligible"] = obs["n_eligible"]
    overall["_n_incumbent"] = obs["n_incumbent"]
    grp_rows = []
    for k, (c, labels) in Gs.items():
        _, den = group_rates(np.zeros(len(c), bool), elig, c, len(labels))
        ng_all = np.bincount(c, minlength=len(labels))
        arr = np.vstack(null_g[k])
        for j, lab in enumerate(labels):
            s = summarize(obs_g[k][j], arr[:, j], B)
            s.update(dimension=k, group=lab, n_contracts=int(ng_all[j]), n_eligible=int(den[j]))
            grp_rows.append(s)
    buyer = None
    if big is not None:
        buyer = dict(ids=big, obs_top=obs_b[0], obs_hhi=obs_b[1],
                     null_top=np.vstack(null_top), null_hhi=np.vstack(null_hhi))
    contrasts = []
    CON = [("law7144", "post (>= 2018-05-25)", "pre (< 2018-05-25)"),
           ("procedure", "21(b)", "open"),
           ("procedure", "21(b)", "other"),
           ("law7144_x_procedure", "post (>= 2018-05-25) / 21(b)", "pre (< 2018-05-25) / 21(b)"),
           ("law7144_x_procedure", "post (>= 2018-05-25) / open", "pre (< 2018-05-25) / open")]
    for dim, a, b in CON:
        if dim not in Gs:
            continue
        labels = Gs[dim][1]
        ia, ib = labels.index(a), labels.index(b)
        arr = np.vstack(null_g[dim])
        s = summarize(obs_g[dim][ia] - obs_g[dim][ib], arr[:, ia] - arr[:, ib], B)
        s.update(contrast=f"{dim}: [{a}] - [{b}]")
        contrasts.append(s)
    # difference-in-differences of excess: (post21b - pre21b) - (postopen - preopen)
    if "law7144_x_procedure" in Gs:
        labels = Gs["law7144_x_procedure"][1]
        arr = np.vstack(null_g["law7144_x_procedure"]); o = obs_g["law7144_x_procedure"]
        ix = {l: labels.index(l) for l in labels}
        f = lambda v: (v[ix["post (>= 2018-05-25) / 21(b)"]] - v[ix["pre (< 2018-05-25) / 21(b)"]]) -                       (v[ix["post (>= 2018-05-25) / open"]] - v[ix["pre (< 2018-05-25) / open"]])
        s = summarize(f(o), np.array([f(r) for r in arr]), B)
        s.update(contrast="DiD: (post-pre | 21(b)) - (post-pre | open)")
        contrasts.append(s)
    return overall, pd.DataFrame(grp_rows), buyer, nulls, pd.DataFrame(contrasts)


def overall_table(ov, label):
    rows = []
    for k, s in ov.items():
        if k.startswith("_"):
            continue
        r = dict(variant=label, statistic=k); r.update(s); rows.append(r)
    return rows


def main():
    d = load()
    main_df = d[d["in_scope_main"] == True].copy()
    log = {}

    # ---------------- 1. observed descriptives
    P = prepare(main_df)
    inc = incumbent(P, P["firm"])
    ds, _ = dyad_stats(P, P["firm"])
    desc = dict(contracts=len(main_df), buyers=int(P["nb"]), firms=int(P["nf"]), **ds,
                eligible=int(P["elig"].sum()), incumbent=int(inc[P["elig"]].sum()),
                incumbency=float(inc[P["elig"]].mean()))
    # dyad weight distribution
    key = P["buyer"] * P["nf"] + P["firm"]
    _, cnt = np.unique(key, return_counts=True)
    desc["dyad_w_dist"] = {str(w): int((cnt == w).sum()) for w in range(1, 6)}
    desc["dyad_w_ge6"] = int((cnt >= 6).sum())
    # same-date ties
    # contracts that share their tender date with another contract of the same buyer-market
    bmd = pd.Series(P["bm"] * 100000 + P["day"])
    tie = bmd.groupby(bmd).transform("size").values > 1
    desc["contracts_in_same_date_buyer_market_ties"] = int(tie.sum())
    desc["ineligible_first_date_ties"] = int((tie & ~P["elig"]).sum())
    log["descriptives"] = desc
    # observed by sector (descriptive)
    rows = []
    for sec, sub in main_df.groupby("sektor_v3_en"):
        Ps = prepare(sub)
        ii = incumbent(Ps, Ps["firm"]); dd, _ = dyad_stats(Ps, Ps["firm"])
        rows.append(dict(sector=sec, contracts=len(sub), buyers=int(Ps["nb"]), firms=int(Ps["nf"]),
                         dyads=dd["dyads"], repeat_dyads=dd["repeat_dyads"],
                         share_in_repeat=dd["share_in_repeat"], max_w=dd["max_w"],
                         eligible=int(Ps["elig"].sum()), incumbency=float(ii[Ps["elig"]].mean())))
    pd.DataFrame(rows).sort_values("contracts", ascending=False).to_csv(
        OUT / "observed_by_sector.csv", index=False)

    # ---------------- 2-4. null models on main sample
    all_overall, all_groups, all_con = [], [], []
    buyer_res = None
    null_store = {}
    for i, kind in enumerate(["N1", "N1w", "N2"]):
        cell = cells(P["df"], kind)
        ov, gr, buyer, nulls, con = run_variant(P, cell, B, SEED + i, big_min=5)
        con.insert(0, "variant", f"main_{kind}"); all_con.append(con)
        log[f"n_cells_{kind}"] = int(cell.max() + 1)
        all_overall += overall_table(ov, f"main_{kind}")
        gr.insert(0, "variant", f"main_{kind}")
        all_groups.append(gr)
        null_store[kind] = nulls
        if kind == "N1":
            buyer_res = buyer
        if kind == "N2":
            buyer_res_n2 = buyer
        print(kind, "done", ov["incumbency"])

    # ---------------- 5. sensitivities (N1 cells unless stated)
    sens = [
        ("S1_buyer_kurum", main_df, dict(buyer_col="kurum"), "N1"),
        ("S2_firm_original", main_df, dict(firm_col="firma"), "N1"),
        ("S3_excl_MHRS_callcentre", d[d["in_scope_core"] == True], {}, "N1"),
        ("S4_incl_gray", d[d["in_scope_broad"] == True], {}, "N1"),
        ("S5_cell_sector_x_year", main_df, {}, "SECT"),
        ("S6_incumbency_buyer_level_any_market", main_df, dict(inc_market_col=None), "N1"),
        ("S7_excl_21f", main_df[main_df["usul_v3"] != "negotiated_21f"], {}, "N1"),
        ("S8_cell_market_x_year_x_province", main_df, {}, "N3"),
    ]
    for j, (lab, sub, kw, kind) in enumerate(sens):
        Pj = prepare(sub, **kw)
        cell = cells(Pj["df"], kind)
        ov, gr, _, _, con = run_variant(Pj, cell, B, SEED + 10 + j, with_groups=(lab in ("S3_excl_MHRS_callcentre", "S8_cell_market_x_year_x_province")), big_min=0)
        all_overall += overall_table(ov, lab)
        if len(gr):
            gr.insert(0, "variant", lab); all_groups.append(gr)
            con.insert(0, "variant", lab); all_con.append(con)
        log[f"{lab}_n"] = dict(contracts=len(sub), buyers=int(Pj["nb"]), firms=int(Pj["nf"]),
                               eligible=int(Pj["elig"].sum()))
        print(lab, "done", ov["incumbency"])

    ovdf = pd.DataFrame(all_overall)
    ovdf.to_csv(OUT / "null_overall.csv", index=False)
    grdf = pd.concat(all_groups, ignore_index=True)
    grdf.to_csv(OUT / "null_by_group.csv", index=False)
    pd.concat(all_con, ignore_index=True).to_csv(OUT / "null_contrasts.csv", index=False)

    # ---------------- buyer-level dependence
    bl_rows = []
    df_ = P["df"]
    bsec = df_.groupby(P["buyer"])["sektor_v3_en"].agg(lambda s: s.value_counts().index[0])
    btype = df_.groupby(P["buyer"])["pooled_label"].first()
    bkind = pd.Series([buyer_type(l, sct) for l, sct in zip(df_["kurum_il_split"], df_["sektor_v3_en"])]).groupby(P["buyer"]).first()
    for tag, br in [("N1", buyer_res), ("N2", buyer_res_n2)]:
        ids = br["ids"]
        n = np.bincount(P["buyer"], minlength=P["nb"])[ids]
        for name in ["top", "hhi"]:
            o = br[f"obs_{name}"]; nl = br[f"null_{name}"]
            p95 = np.percentile(nl, 95, axis=0)
            pval = (1 + (nl >= o - 1e-12).sum(0)) / (nl.shape[0] + 1)
            bl_rows.append(pd.DataFrame(dict(null=tag, measure=name, buyer_idx=ids, n_contracts=n,
                                             sector=bsec.loc[ids].values, pooled=btype.loc[ids].values,
                                             buyer_type=bkind.loc[ids].values,
                                             obs=o, null_mean=nl.mean(0), null_p95=p95,
                                             exceeds_p95=o > p95 + 1e-12, p_upper=pval)))
    bl = pd.concat(bl_rows, ignore_index=True)
    bl.to_csv(OUT / "buyer_dependence.csv", index=False)  # buyer_idx only, no names

    # quick histogram data for F-L3 (N1, top share): pooled null sample
    np.save(OUT / "_null_top_N1_sample.npy", buyer_res["null_top"][:200])

    json.dump(log, open(OUT / "lockin_log.json", "w"), indent=2, default=str)
    return P, ovdf, grdf, bl, log


# ---------------------------------------------------------------- figures
def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_market(grdf):
    g = grdf[(grdf.variant == "main_N1") & (grdf.dimension == "market")].copy()
    g = g.sort_values("obs")
    fig, ax = plt.subplots(figsize=(7, 4.0))
    y = np.arange(len(g))
    ax.hlines(y, g.null_lo, g.null_hi, color=OI[1], lw=5, alpha=0.8, label="Null 95% interval (N1)")
    ax.plot(g.null_mean, y, "|", color=OI[4], ms=9, mew=1.5, label="Null mean")
    ax.plot(g.obs, y, "o", color=OI[5], ms=5, label="Observed")
    labels = [f"{m.replace('_', ' ')} (n={ne:,})" for m, ne in zip(g.group, g.n_eligible)]
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlabel("Incumbency rate (share of repeat-eligible contracts won by an incumbent)")
    ax.set_xlim(0, max(g.obs.max(), g.null_hi.max()) * 1.08)
    ax.legend(loc="lower right", frameon=False)
    ax.grid(axis="y", visible=False)
    save(fig, "F_L1_incumbency_by_market")


def fig_year(grdf):
    g = grdf[(grdf.variant == "main_N1") & (grdf.dimension == "year")].copy()
    g["yr"] = g.group.astype(int)
    g = g[g.n_eligible >= 20].sort_values("yr")
    fig, ax = plt.subplots(figsize=(7, 3.0))
    ax.fill_between(g.yr, g.null_lo, g.null_hi, color=OI[1], alpha=0.45, lw=0, label="Null 95% interval (N1)")
    ax.plot(g.yr, g.null_mean, "--", color=OI[4], lw=1, label="Null mean")
    ax.plot(g.yr, g.obs, "o-", color=OI[5], lw=1.3, ms=4, label="Observed")
    ax.axvline(2018.4, color="#555555", lw=0.8, ls=":")
    ax.text(2018.5, ax.get_ylim()[1] * 0.97 if False else 0.02, "Law 7144", fontsize=7, color="#555555",
            va="bottom", transform=ax.get_xaxis_transform())
    ax.set_xlabel("Tender year")
    ax.set_ylabel("Incumbency rate")
    ax.set_ylim(0, None)
    ax.set_xticks(g.yr)
    ax.tick_params(axis="x", rotation=0)
    ax.legend(loc="upper left", frameon=False, ncol=3)
    save(fig, "F_L2_incumbency_by_year")


def fig_buyer(bl):
    b = bl[(bl.null == "N1") & (bl.measure == "top")]
    nullsamp = np.load(OUT / "_null_top_N1_sample.npy").ravel()
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    for v, col, lab, ls in [(np.sort(nullsamp), OI[4], "Null (N1, 200 permutations pooled)", "--"),
                            (np.sort(b.obs.values), OI[5], "Observed", "-")]:
        ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=col, lw=1.4, ls=ls, label=lab)
    ax.set_xlim(0, 1.0); ax.set_ylim(0, 1.01)
    ax.set_xlabel("Top-supplier share of buyer's contracts")
    ax.set_ylabel("Cumulative share of buyers (≥5 contracts)")
    ax.legend(frameon=False, loc="lower right")
    save(fig, "F_L3_buyer_top_supplier_share")


if __name__ == "__main__":
    P, ovdf, grdf, bl, log = main()
    fig_market(grdf); fig_year(grdf); fig_buyer(bl)
    print(json.dumps(log["descriptives"], indent=1))
