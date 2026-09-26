"""TenderNet v3 - revision A (referee round 1): renewals, stronger nulls, supplier-choice
model, lots/framework check, natural-person robustness, BH buyer tests, single-bid expansion.

Builds on lockin_analysis.py (same definitions: repeat-eligible, incumbent, strictly-earlier
history; same-date ties are not history).
Run: python src/revision_a.py        (about 5-10 min; env REVA_B sets permutations)
Outputs: results/revision_a/*.csv, revision_a_log.json; figure F-A1 in figures.
The markdown report revision_a_results.md is written by hand from these outputs.
"""
from pathlib import Path
import json
import os
import re
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lockin_analysis as L          # noqa: E402
import revision_a_titles as T        # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "revision_a"
FIG = ROOT / "figures"
OUT.mkdir(parents=True, exist_ok=True)
CP2 = ROOT / "data" / "bid_counts_cp2.csv"          # released derivative of the cp2 scrape (no firm names)
ORNEK = ROOT / "data" / "bid_counts_sample.csv"

B = int(os.environ.get("REVA_B", 1000))
BOOT = int(os.environ.get("REVA_BOOT", 500))
SEED = 42
THRESH = 0.5                  # Jaccard threshold for "similar title" (validated by hand)
WIN = (183, 548)              # renewal window in days (6-18 months)
N_ALT = 30                    # sampled non-chosen alternatives in the choice model
OI = L.OI
BIG_MARKETS = ["health_information_systems", "ERP_management_software", "software_licences",
               "custom_software_web_mobile", "maintenance_support_services",
               "network_datacentre_infrastructure", "computers_peripherals", "GIS_city_information"]
LOG = {}


# =====================================================================  helpers
def codes(v):
    c, lab = pd.factorize(pd.Series(v).astype(str))
    return c.astype(np.int64), list(lab)


def tr_up(s):
    return pd.Series(s).astype(str).str.replace("i", "İ").str.replace("ı", "I").str.upper()


def home_province(df):
    """Firm home = province (buyer `il`) where the firm won most contracts in the whole main
    sample; ties -> province of the firm's earliest win among the tied provinces."""
    t = df.groupby(["firma_v3", "il"]).agg(n=("il", "size"), first=("date", "min")).reset_index()
    t = t.sort_values(["firma_v3", "n", "first"], ascending=[True, False, True])
    return t.drop_duplicates("firma_v3").set_index("firma_v3")["il"]


def null_run(P, cell, B, seed, dims):
    """Permute winners within `cell`; incumbency overall and by every grouping in `dims`
    (dims: name -> (codes, labels)).  Returns overall dict and group DataFrame."""
    rng = np.random.default_rng(seed)
    elig = P["elig"]
    inc0 = L.incumbent(P, P["firm"])
    obs = {k: L.group_rates(inc0, elig, c, len(lab))[0] for k, (c, lab) in dims.items()}
    obs_all = inc0[elig].mean()
    nul = {k: np.empty((B, len(lab))) for k, (c, lab) in dims.items()}
    nul_all = np.empty(B)
    for b in range(B):
        f = L.permute_within(P["firm"], cell, rng)
        inc = L.incumbent(P, f)
        nul_all[b] = inc[elig].mean()
        for k, (c, lab) in dims.items():
            nul[k][b] = L.group_rates(inc, elig, c, len(lab))[0]
    ne = int(elig.sum())
    ov = L.summarize(obs_all, nul_all, B)
    ov.update(n_eligible=ne, n_incumbent=int(inc0[elig].sum()),
              excess_contracts=(obs_all - ov["null_mean"]) * ne,
              n_cells=int(cell.max() + 1))
    rows = []
    for k, (c, lab) in dims.items():
        _, den = L.group_rates(inc0, elig, c, len(lab))
        for j, g in enumerate(lab):
            s = L.summarize(obs[k][j], nul[k][:, j], B)
            s.update(dimension=k, group=g, n_eligible=int(den[j]),
                     n_incumbent=int(round(obs[k][j] * den[j])) if den[j] else 0,
                     excess_contracts=(s["excess"] * den[j]) if den[j] else np.nan)
            rows.append(s)
    return ov, pd.DataFrame(rows)


# =====================================================================  1. renewals
def renewal_features(P):
    df = P["df"]
    tok = [T.norm_tokens(t) for t in df["ihale_adi"]]
    pm = T.prior_matches(df, tok, P["buyer"], P["mkt"], P["day"])
    n = len(df)
    sim_win = pd.Series(0.0, index=range(n))
    s = pm[(pm.gap >= WIN[0]) & (pm.gap <= WIN[1])].groupby("i").sim.max()
    sim_win.loc[s.index] = s.values
    sim_any = pd.Series(0.0, index=range(n))
    s = pm.groupby("i").sim.max()
    sim_any.loc[s.index] = s.values
    sim_short = pd.Series(0.0, index=range(n))
    s = pm[pm.gap < WIN[0]].groupby("i").sim.max(); sim_short.loc[s.index] = s.values
    sim_long = pd.Series(0.0, index=range(n))
    s = pm[pm.gap > WIN[1]].groupby("i").sim.max(); sim_long.loc[s.index] = s.values
    gap_prev = pm.groupby("i").gap.min()
    gp = np.full(n, np.nan); gp[gap_prev.index.values] = gap_prev.values
    F = pd.DataFrame(dict(sim_win=sim_win.values, sim_any=sim_any.values, sim_short=sim_short.values,
                          sim_long=sim_long.values, gap_prev=gp))
    F["elig"] = P["elig"]

    def lab(th):
        r = np.where(F.sim_win >= th, "renewal", "new need")
        return np.where(F.elig, r, "not eligible")
    F["renewal"] = lab(THRESH)
    F["renewal_t040"] = lab(0.40)
    F["renewal_t067"] = lab(0.67)
    # broad window: any similar-title prior within 0-548 days
    F["renewal_0_18m"] = np.where(~F.elig, "not eligible",
                                  np.where((F.sim_win >= THRESH) | (F.sim_short >= THRESH), "renewal", "new need"))
    F["renewal_0_24m"] = np.where(~F.elig, "not eligible", "new need")
    s24 = pm[(pm.gap <= 730) & (pm.sim >= THRESH)].i.unique()
    F.loc[F.index.isin(s24) & F.elig, "renewal_0_24m"] = "renewal"
    four = np.where(F.sim_win >= THRESH, "A renewal (similar title 6-18 m earlier)",
                    np.where(F.sim_short >= THRESH, "B similar title only < 6 m earlier",
                             np.where(F.sim_long >= THRESH, "C similar title only > 18 m earlier",
                                      "D no similar-title prior")))
    F["renewal4"] = np.where(F.elig, four, "not eligible")
    return F, pm, tok


def validation_sample(P, pm):
    """60 random best-match pairs (6-18 m window), stratified by similarity band."""
    df = P["df"]
    w = pm[(pm.gap >= WIN[0]) & (pm.gap <= WIN[1])].sort_values("sim").groupby("i").tail(1)
    w = w[P["elig"][w.i.values]]
    rng = np.random.default_rng(SEED)
    out = []
    for lo, hi in [(0.35, 0.45), (0.45, 0.55), (0.55, 0.70), (0.70, 1.01)]:
        s = w[(w.sim >= lo) & (w.sim < hi)]
        s = s.iloc[np.sort(rng.choice(len(s), 15, replace=False))]
        for r in s.itertuples():
            out.append(dict(band=f"[{lo:.2f},{min(hi,1):.2f})", sim=round(r.sim, 3), gap_days=r.gap,
                            market=df.urun_pazari[r.i], title_i=df.ihale_adi[r.i], title_prior=df.ihale_adi[r.j]))
    v = pd.DataFrame(out)
    v.insert(0, "pair_id", range(1, len(v) + 1))
    return v


def gap_bins(gp):
    edges = [0, 90, 183, 300, 430, 548, 730, 1095, 10 ** 6]
    labs = ["1-90", "91-183", "184-300", "301-430", "431-548", "549-730", "731-1095", ">1095"]
    b = pd.cut(gp, edges, labels=labs, right=True)
    return np.where(pd.isna(b), "none", b.astype(str)), labs


# =====================================================================  2b. choice model
def build_choice_data(P, F, home):
    df = P["df"]
    rng = np.random.default_rng(SEED)
    firm = P["firm"]; day = P["day"]; mkt = P["mkt"]; buyer = P["buyer"]
    yr = df["yil_v3"].astype(int).values
    sec = pd.factorize(df["sektor_v3"])[0]
    fname = pd.factorize(df["firma_v3"])[1]
    fhome = pd.Series(fname).map(home).values
    il = df["il"].values
    ilc, _ = pd.factorize(df["il"])
    nil = ilc.max() + 1
    firm_il = np.zeros((P["nf"], nil), dtype=np.int64)
    np.add.at(firm_il, (firm, ilc), 1)
    # per-firm history arrays sorted by day
    order = np.lexsort((day, firm))
    hist = {}
    fs = firm[order]
    starts = np.r_[0, np.flatnonzero(fs[1:] != fs[:-1]) + 1, len(fs)]
    for a, b_ in zip(starts[:-1], starts[1:]):
        idx = order[a:b_]
        hist[fs[a]] = (day[idx], mkt[idx], buyer[idx], sec[idx], ilc[idx])
    # active firms per market-year
    act = pd.DataFrame(dict(m=mkt, y=yr, f=firm)).drop_duplicates()
    active = act.groupby(["m", "y"]).f.apply(lambda s: np.array(sorted(s))).to_dict()
    rows = []
    elig_idx = np.flatnonzero(P["elig"])
    for i in elig_idx:
        m, y, t, k = mkt[i], yr[i], day[i], buyer[i]
        pool = np.union1d(active.get((m, y), np.array([], int)), active.get((m, y - 1), np.array([], int)))
        pool = pool[pool != firm[i]]
        alts = rng.choice(pool, min(N_ALT, len(pool)), replace=False) if len(pool) else np.array([], int)
        for j, ch in [(firm[i], 1)] + [(a, 0) for a in alts]:
            d_, m_, b_, s_, il_ = hist[j]
            n = np.searchsorted(d_, t, side="left")
            d_, m_, b_, s_, il_ = d_[:n], m_[:n], b_[:n], s_[:n], il_[:n]
            same_b = b_ == k
            # leakage-free home definitions: (a) leave contract i out, (b) prior wins only
            cnt = firm_il[j].copy()
            if ch == 1:
                cnt[ilc[i]] -= 1
            home_loo = int(cnt.max() > 0 and cnt.argmax() == ilc[i])
            home_prior = int(n > 0 and np.bincount(il_, minlength=nil).argmax() == ilc[i])
            rows.append((i, j, ch,
                         int(np.any(same_b & (m_ == m))),
                         int(np.any(same_b & (m_ != m))),
                         int(fhome[j] == il[i]),
                         np.log1p(np.sum((m_ == m) & (d_ >= t - 365))),
                         np.log1p(n),
                         np.log1p(np.sum(s_ == sec[i])), home_loo, home_prior, int(n == 0)))
    C = pd.DataFrame(rows, columns=["contract", "firm", "chosen", "inc_same_market", "inc_other_market",
                                    "same_home_province", "log_wins_market_12m", "log_total_prior_wins",
                                    "log_prior_wins_same_sector", "same_home_loo", "same_home_prior",
                                    "no_prior_wins"])
    C["buyer"] = buyer[C.contract.values]
    C["renewal"] = F["renewal"].values[C.contract.values]
    C["proc"] = L.proc3(df["usul_v3"].values)[C.contract.values]
    C["set_size"] = C.groupby("contract").firm.transform("size")
    return C


def clogit_fit(X, g, y, w=None, beta0=None, maxit=100):
    """Conditional logit (one chosen per group) by Newton-Raphson. g must be sorted codes 0..G-1.
    w: group weights (bootstrap). Returns beta, H (neg. Hessian), per-group scores."""
    G = g.max() + 1
    K = X.shape[1]
    w = np.ones(G) if w is None else w
    beta = np.zeros(K) if beta0 is None else beta0.copy()

    def evaluate(b):
        eta = X @ b
        mxg = np.full(G, -np.inf)
        np.maximum.at(mxg, g, eta)
        e = np.exp(eta - mxg[g])
        den = np.bincount(g, weights=e, minlength=G)
        p = e / den[g]
        ll = np.sum(w * (np.bincount(g, weights=eta * y, minlength=G) - (np.log(den) + mxg)))
        return ll, p

    ll, p = evaluate(beta)
    for it in range(maxit):
        xbar = np.vstack([np.bincount(g, weights=p * X[:, k], minlength=G) for k in range(K)]).T
        xch = np.vstack([np.bincount(g, weights=y * X[:, k], minlength=G) for k in range(K)]).T
        S = xch - xbar                                   # per-group score
        grad = (w[:, None] * S).sum(0)
        Xc = X - xbar[g]
        H = (Xc * (p * w[g])[:, None]).T @ Xc
        step = np.linalg.solve(H + 1e-10 * np.eye(K), grad)
        t = 1.0
        while True:                                      # backtracking line search
            ll_new, p_new = evaluate(beta + t * step)
            if ll_new >= ll - 1e-12 or t < 1e-6:
                break
            t /= 2
        beta = beta + t * step
        done = abs(ll_new - ll) < 1e-10 and np.max(np.abs(t * step)) < 1e-8
        ll, p = ll_new, p_new
        if done:
            break
    # recompute score and information at the optimum
    xbar = np.vstack([np.bincount(g, weights=p * X[:, k], minlength=G) for k in range(K)]).T
    xch = np.vstack([np.bincount(g, weights=y * X[:, k], minlength=G) for k in range(K)]).T
    S = xch - xbar
    Xc = X - xbar[g]
    H = (Xc * (p * w[g])[:, None]).T @ Xc
    return beta, H, S, ll


def clogit(C, cols, cluster="buyer", boot=0, seed=SEED, label=""):
    C = C.sort_values(["contract", "chosen"], ascending=[True, False]).reset_index(drop=True)
    g = pd.factorize(C["contract"])[0]
    X = C[cols].values.astype(float)
    y = C["chosen"].values.astype(float)
    beta, H, S, ll = clogit_fit(X, g, y)
    Hinv = np.linalg.inv(H)
    # cluster-robust by buyer: sum group scores within cluster
    cl = pd.factorize(C.groupby(g)[cluster].first().values)[0]
    nc = cl.max() + 1
    Sc = np.vstack([np.bincount(cl, weights=S[:, k], minlength=nc) for k in range(S.shape[1])]).T
    G_ = nc
    V = Hinv @ (Sc.T @ Sc) @ Hinv * G_ / (G_ - 1)
    se = np.sqrt(np.diag(V))
    se_naive = np.sqrt(np.diag(Hinv))
    out = pd.DataFrame(dict(model=label, variable=cols, coef=beta, se_cluster=se, se_model=se_naive,
                            OR=np.exp(beta), OR_lo=np.exp(beta - 1.96 * se), OR_hi=np.exp(beta + 1.96 * se)))
    from scipy.stats import norm
    out["p"] = 2 * norm.sf(np.abs(beta / se))
    if boot:
        rng = np.random.default_rng(seed)
        grp_cl = cl  # cluster of each group
        bs = []
        for _ in range(boot):
            draw = rng.integers(0, nc, nc)
            wcl = np.bincount(draw, minlength=nc).astype(float)
            wg = wcl[grp_cl]
            keep = wg > 0
            if keep.sum() < 50:
                continue
            b_, *_ = clogit_fit(X, g, y, w=wg, beta0=beta)
            bs.append(b_)
        bs = np.array(bs)
        out["OR_boot_lo"] = np.exp(np.percentile(bs, 2.5, axis=0))
        out["OR_boot_hi"] = np.exp(np.percentile(bs, 97.5, axis=0))
        out["n_boot"] = len(bs)
    out["n_contracts"] = g.max() + 1
    out["n_rows"] = len(C)
    out["n_buyer_clusters"] = nc
    out["loglik"] = ll
    return out


# =====================================================================  6. single bids
def single_bid(P, F):
    df = P["df"].copy()
    z = pd.read_csv(CP2, encoding="utf-8-sig")
    LOG["cp2"] = dict(records=len(z), unique_ikn=int(z.IKN.nunique()),
                      keyword=z.kaynak_keyword.value_counts().to_dict(),
                      with_winner=int(z.has_winner.sum()),
                      with_bidcount=int((z.teklif_veren_sayisi > 0).sum()),
                      bidcount_by_year=z[z.teklif_veren_sayisi > 0].yil.value_counts().sort_index().to_dict(),
                      year_all=z.yil.value_counts().sort_index().to_dict())
    inc = L.incumbent(P, P["firm"])
    df["incumbent"] = inc
    df["elig"] = P["elig"]
    df["renewal"] = F["renewal"].values
    df["proc"] = L.proc3(df["usul_v3"].values)
    df["proc_fine"] = df["usul_v3"]
    j = df.merge(z[["IKN", "teklif_veren_sayisi"]], on="IKN", how="inner")
    LOG["cp2"]["joined_main"] = len(j)
    # coverage: main-sample tenders 2021+ retrieved by keyword 'yazılım'
    base = df[(df.yil_v3 >= 2021)]
    LOG["cp2"]["main_2021plus"] = len(base)
    LOG["cp2"]["main_2021plus_kw_yazilim"] = int((base.kaynak_keyword == "yazılım").sum())
    j = j[j.teklif_veren_sayisi > 0].copy()
    LOG["cp2"]["joined_main_with_bidcount"] = len(j)
    LOG["cp2"]["joined_bid_by_keyword"] = j.kaynak_keyword.value_counts().to_dict()
    LOG["cp2"]["share_of_main_2021plus"] = len(j) / len(base)
    # validation against teklif_ornek (valid bids)
    o = pd.read_csv(ORNEK, encoding="utf-8-sig")
    v = o.merge(z[["IKN", "teklif_veren_sayisi"]], on="IKN")
    v = v[(v.teklif_veren_sayisi > 0) & v.gecerli_teklif.notna()]
    LOG["cp2"]["validation_vs_teklif_ornek"] = dict(n=len(v),
                                                    equal_valid=float((v.gecerli_teklif == v.teklif_veren_sayisi).mean()),
                                                    equal_total=float((v.toplam_teklif == v.teklif_veren_sayisi).mean()))
    j["single"] = (j.teklif_veren_sayisi == 1).astype(int)
    j["inc_status"] = np.where(~j.elig, "buyer first in market (undefined)",
                               np.where(j.incumbent, "incumbent winner", "non-incumbent winner"))
    rows = []

    def add(dim, grp, s):
        n = len(s); k = int(s.single.sum()); p = k / n if n else np.nan
        from statsmodels.stats.proportion import proportion_confint
        lo, hi = proportion_confint(k, n, method="wilson") if n else (np.nan, np.nan)
        rows.append(dict(dimension=dim, group=grp, n=n, single=k, rate=p, lo=lo, hi=hi,
                         mean_valid_bids=s.teklif_veren_sayisi.mean()))
    add("overall", "all", j)
    for g, s in j.groupby("inc_status"): add("incumbency", g, s)
    for g, s in j.groupby("proc_fine"): add("procedure", g, s)
    for g, s in j[j.elig].groupby("renewal"): add("renewal (eligible only)", g, s)
    for (a, b_), s in j[j.elig].groupby(["renewal", "inc_status"]): add("renewal x incumbency", f"{a} | {b_}", s)
    for (a, b_), s in j[j.elig].groupby(["proc", "inc_status"]): add("procedure x incumbency", f"{a} | {b_}", s)
    rates = pd.DataFrame(rows)
    # buyer-clustered logit on eligible tenders
    import statsmodels.formula.api as smf
    e = j[j.elig].copy()
    e["incumbent"] = e.incumbent.astype(int)
    e["proc"] = pd.Categorical(e.proc, ["open", "21(b)", "other"])
    e["renewal_i"] = (e.renewal == "renewal").astype(int)
    e["yr"] = e.yil_v3.astype(int).astype(str)
    e["mk"] = e.urun_pazari
    small = e.mk.value_counts(); e.loc[e.mk.isin(small[small < 15].index), "mk"] = "pooled_small"
    res = []
    for name, f in [("M1 single ~ incumbent + procedure + year FE + market FE",
                     "single ~ incumbent + C(proc) + C(yr) + C(mk)"),
                    ("M2 M1 + renewal", "single ~ incumbent + renewal_i + C(proc) + C(yr) + C(mk)"),
                    ("M0 single ~ incumbent + procedure + year FE (as in models D)",
                     "single ~ incumbent + C(proc) + C(yr)")]:
        grp = pd.factorize(e.kurum_il_split)[0]
        mdl = smf.logit(f, e).fit(disp=0, cov_type="cluster", cov_kwds=dict(groups=grp))
        for v_ in mdl.params.index:
            if v_.startswith("C(yr)") or v_.startswith("C(mk)") or v_ == "Intercept":
                continue
            b_, s_ = mdl.params[v_], mdl.bse[v_]
            res.append(dict(model=name, variable=v_, coef=b_, se_cluster=s_, OR=np.exp(b_),
                            OR_lo=np.exp(b_ - 1.96 * s_), OR_hi=np.exp(b_ + 1.96 * s_), p=mdl.pvalues[v_],
                            n=int(mdl.nobs), clusters=int(grp.max() + 1), pseudo_r2=mdl.prsquared))
    j[["IKN", "yil_v3", "urun_pazari", "usul_v3", "teklif_veren_sayisi", "single", "inc_status", "renewal"]].to_csv(
        OUT / "F_single_bid_cp2_joined.csv", index=False)
    return rates, pd.DataFrame(res)


# =====================================================================  figure
def fig_a1(gr):
    g = gr[gr.dimension == "gapbin_x_renewal"].copy()
    g[["bin", "ren"]] = g.group.str.split(" / ", expand=True)
    _, labs = gap_bins(np.array([1.0]))
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(7, 4.6), sharex=True,
                                  gridspec_kw=dict(height_ratios=[3, 1.2], hspace=0.08))
    x = np.arange(len(labs))
    for ren, col, off, mk in [("renewal", OI[5], -0.12, "o"), ("new need", OI[4], 0.12, "s")]:
        s = g[g.ren == ren].set_index("bin").reindex(labs)
        ok = s.n_eligible.fillna(0) >= 15
        n = s.n_eligible.values; p = s.obs.values
        lo = p - 1.96 * np.sqrt(p * (1 - p) / np.maximum(n, 1)); hi = p + 1.96 * np.sqrt(p * (1 - p) / np.maximum(n, 1))
        ax.errorbar(x[ok] + off, p[ok], yerr=[p[ok] - lo[ok], hi[ok] - p[ok]], fmt=mk + "-", color=col, ms=4,
                    lw=1.2, capsize=2, label=f"{ren.capitalize()}: observed")
        ax.plot(x[ok] + off, s.null_mean_N3.values[ok], mk, mfc="white", color=col, ms=4, ls=":", lw=1,
                label=f"{ren.capitalize()}: null N3 mean")
        ax2.bar(x + off, s.n_eligible.fillna(0).values, width=0.24, color=col, label=ren.capitalize())
    ax.set_ylabel("Incumbency rate")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, ncol=2, loc="upper right", fontsize=7)
    ax2.set_ylabel("Contracts")
    ax2.set_xticks(x); ax2.set_xticklabels(labs)
    ax2.set_xlabel("Days since the buyer's previous contract in the same product market")
    ax2.grid(axis="x", visible=False); ax.grid(axis="x", visible=False)
    fig.align_ylabels([ax, ax2])
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"F-A1_incumbency_by_gap_renewal.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


# =====================================================================  main
def main():
    d = L.load()
    main_df = d[d["in_scope_main"] == True].copy()
    P = L.prepare(main_df)
    df = P["df"]
    home = home_province(df)
    df["firm_home"] = df["firma_v3"].map(home)
    LOG["sample"] = dict(contracts=len(df), eligible=int(P["elig"].sum()),
                         unique_ikn=int(df.IKN.nunique()), rows_per_ikn_max=int(df.IKN.value_counts().max()))
    LOG["firm_home"] = dict(firms=int(home.size),
                            share_contracts_buyer_il_eq_home=float((df.il == df.firm_home).mean()))

    # ---------- 1. renewals
    F, pm, tok = renewal_features(P)
    validation_sample(P, pm).to_csv(OUT / "A_renewal_validation_sample.csv", index=False, encoding="utf-8-sig")
    F.assign(IKN=df.IKN.values, urun_pazari=df.urun_pazari.values).to_csv(OUT / "A_renewal_flags.csv", index=False)
    el = F.elig.values
    LOG["renewal_counts"] = {c: F.loc[el, c].value_counts().to_dict() for c in
                             ["renewal", "renewal_t040", "renewal_t067", "renewal_0_18m", "renewal_0_24m", "renewal4"]}
    LOG["gap_prev_eligible_median"] = float(np.nanmedian(F.gap_prev[el]))

    # ---------- flags for lots / framework
    tu = tr_up(df.ihale_adi)
    lot_pat = r"\bKISIM|KISMİ TEKLİF|KISMİ İHALE|\bGRUP\b|\bLOT\s*\d"
    fw_pat = r"ÇERÇEVE ANLAŞMA|CERCEVE ANLASMA|ÇERÇEVE SÖZLEŞME"
    df["multi_lot"] = tu.str.contains(lot_pat).values
    df["framework"] = tu.str.contains(fw_pat).values
    LOG["lots"] = dict(multi_lot=int(df.multi_lot.sum()), multi_lot_eligible=int((df.multi_lot & el).sum()),
                       framework=int(df.framework.sum()),
                       cerceve_word_any=int(tu.str.contains("ÇERÇEVE").sum()),
                       multi_lot_by_market=df[df.multi_lot].urun_pazari.value_counts().to_dict())
    df.loc[df.multi_lot | df.framework, ["IKN", "yil_v3", "urun_pazari", "ihale_adi"]].to_csv(
        OUT / "C_multilot_framework_titles.csv", index=False, encoding="utf-8-sig")

    # ---------- groupings (all winner-independent)
    gb, labs = gap_bins(F.gap_prev.values)
    dims = {
        "renewal": codes(F.renewal), "renewal_t040": codes(F.renewal_t040), "renewal_t067": codes(F.renewal_t067),
        "renewal_0_18m": codes(F.renewal_0_18m), "renewal_0_24m": codes(F.renewal_0_24m),
        "renewal4": codes(F.renewal4),
        "market_x_renewal": codes(df.urun_pazari.astype(str) + " / " + F.renewal),
        "procedure_x_renewal": codes(pd.Series(L.proc3(df.usul_v3.values)) + " / " + F.renewal),
        "sector_x_renewal": codes(df.sektor_v3_en.astype(str).values + " / " + F.renewal),
        "gapbin_x_renewal": codes(pd.Series(gb) + " / " + F.renewal),
        "multi_lot": codes(np.where(df.multi_lot, "multi-lot title", "single-lot title")),
        "natural_person": codes(np.where(df.is_natural_person | df.contains_natural_person,
                                         "natural-person winner", "company winner")),
    }
    # ---------- nulls on main sample
    y = df.yil_v3.astype(int).astype(str)
    cell_defs = {
        "N1": L.cells(df, "N1"), "N2": L.cells(df, "N2"), "N3": L.cells(df, "N3"),
        "N4_home": pd.factorize(df.urun_pazari.astype(str) + "|" + y + "|" + df.firm_home.astype(str))[0],
        "N4b_prov_home": pd.factorize(df.urun_pazari.astype(str) + "|" + y + "|" + df.il.astype(str) + "|" +
                                      df.firm_home.astype(str))[0],
    }
    ovs, grs = [], []
    for i, (nm, cell) in enumerate(cell_defs.items()):
        ov, gr = null_run(P, cell.astype(np.int64), B, SEED + 100 + i, dims)
        ov = dict(sample="main", null=nm, **ov); ovs.append(ov)
        gr.insert(0, "null", nm); grs.append(gr)
        print(nm, round(ov["obs"], 4), round(ov["null_mean"], 4), flush=True)
    # N4 degeneracy diagnostics: share of eligible contracts in cells with a single distinct winner
    for nm in ["N3", "N4_home", "N4b_prov_home"]:
        c = cell_defs[nm]
        nd = pd.Series(P["firm"]).groupby(c).nunique()
        LOG[f"{nm}_cells"] = dict(cells=int(c.max() + 1),
                                  eligible_in_single_winner_cells=float((nd.reindex(c).values == 1)[P["elig"]].mean()))
    # ---------- subsample robustness (lots excluded, natural persons excluded)
    subs = {
        "excl_multilot_framework": main_df[~(df.multi_lot | df.framework).values],
        "excl_natural_person": main_df[~(main_df.is_natural_person | main_df.contains_natural_person)],
    }
    for k, (nm, sub) in enumerate(subs.items()):
        Ps = L.prepare(sub)
        for i, kind in enumerate(["N1", "N2", "N3"]):
            ov, _ = null_run(Ps, L.cells(Ps["df"], kind), B, SEED + 200 + 10 * k + i, {})
            ovs.append(dict(sample=nm, null=kind, contracts=len(sub), **ov))
            print(nm, kind, round(ov["obs"], 4), round(ov["null_mean"], 4), flush=True)
    ovdf = pd.DataFrame(ovs)
    ovdf.to_csv(OUT / "B_null_overall.csv", index=False)
    grdf = pd.concat(grs, ignore_index=True)
    grdf.to_csv(OUT / "B_null_by_group.csv", index=False)

    # ---------- figure F-A1
    g = grdf[grdf.dimension == "gapbin_x_renewal"]
    fg = g[g.null == "N1"].copy()
    fg = fg.merge(g[g.null == "N3"][["group", "null_mean"]].rename(columns=dict(null_mean="null_mean_N3")), on="group")
    fg.to_csv(OUT / "A_fig_A1_data.csv", index=False)
    fig_a1(fg)

    # ---------- 5. BH on buyer-level tests
    bd = pd.read_csv(ROOT / "results" / "lockin" / "buyer_dependence.csv")
    from statsmodels.stats.multitest import multipletests
    bh = []
    for (nl, ms), s in bd.groupby(["null", "measure"]):
        rej, q, *_ = multipletests(s.p_upper.values, alpha=0.05, method="fdr_bh")
        bh.append(dict(null=nl, measure=ms, buyers=len(s), exceed_p95=int(s.exceeds_p95.sum()),
                       p_le_005=int((s.p_upper <= 0.05).sum()), bh_reject_5pct=int(rej.sum()),
                       bh_share=rej.mean(), min_p=s.p_upper.min(),
                       bonferroni_reject=int((s.p_upper <= 0.05 / len(s)).sum())))
        for bt, ss in s.assign(rej=rej).groupby("buyer_type"):
            bh.append(dict(null=nl, measure=ms, buyer_type=bt, buyers=len(ss), bh_reject_5pct=int(ss.rej.sum()),
                           bh_share=ss.rej.mean()))
    pd.DataFrame(bh).to_csv(OUT / "E_buyer_BH.csv", index=False)

    # ---------- 2b. choice model
    C = build_choice_data(P, F, home)
    C.to_csv(OUT / "D_choice_data.csv.gz", index=False, compression="gzip")
    LOG["choice"] = dict(contracts=int(C.contract.nunique()), rows=len(C),
                         mean_set=float(C.groupby("contract").size().mean()),
                         sets_lt_31=int((C.groupby("contract").size() < N_ALT + 1).sum()),
                         chosen_inc_rate=float(C[C.chosen == 1].inc_same_market.mean()),
                         alt_inc_rate=float(C[C.chosen == 0].inc_same_market.mean()),
                         means_by_chosen=C.groupby("chosen")[["inc_same_market", "inc_other_market", "same_home_province",
                                                              "log_wins_market_12m", "log_total_prior_wins",
                                                              "log_prior_wins_same_sector"]].mean().to_dict())
    full = ["inc_same_market", "inc_other_market", "same_home_province", "log_wins_market_12m",
            "log_total_prior_wins", "log_prior_wins_same_sector"]
    res = [clogit(C, ["inc_same_market"], label="M0 incumbent only"),
           clogit(C, full, boot=BOOT, label="M1 full (all repeat-eligible)")]
    for lab_, sub in [("M1 renewals", C[C.renewal == "renewal"]), ("M1 new needs", C[C.renewal == "new need"]),
                      ("M1 21(b)", C[C.proc == "21(b)"]), ("M1 open", C[C.proc == "open"]),
                      ("M1 other procedures", C[C.proc == "other"])]:
        res.append(clogit(sub, full, label=lab_))
    C2 = C.copy()
    C2["inc_x_renewal"] = C2.inc_same_market * (C2.renewal == "renewal")
    C2["inc_x_21b"] = C2.inc_same_market * (C2.proc == "21(b)")
    C2["inc_x_other_proc"] = C2.inc_same_market * (C2.proc == "other")
    res.append(clogit(C2, full + ["inc_x_renewal", "inc_x_21b", "inc_x_other_proc"], label="M2 interactions"))
    # home-province leakage checks: whole-sample home includes contract i itself
    base = [c for c in full if c != "same_home_province"]
    res.append(clogit(C, base, label="M1 without home province"))
    res.append(clogit(C, base + ["same_home_loo"], label="M1 home = leave-contract-out"))
    res.append(clogit(C, base + ["same_home_prior", "no_prior_wins"], boot=BOOT,
                      label="M1 home = prior wins only (leakage-free)"))
    for lab_, sub in [("M1-prior renewals", C[C.renewal == "renewal"]), ("M1-prior new needs", C[C.renewal == "new need"]),
                      ("M1-prior 21(b)", C[C.proc == "21(b)"]), ("M1-prior open", C[C.proc == "open"])]:
        res.append(clogit(sub, base + ["same_home_prior", "no_prior_wins"], label=lab_))
    cres = pd.concat(res, ignore_index=True)
    cres.to_csv(OUT / "D_clogit_results.csv", index=False)
    # statsmodels cross-check of the full model point estimates
    try:
        from statsmodels.discrete.conditional_models import ConditionalLogit
        Cs = C.sort_values("contract")
        cm = ConditionalLogit(Cs.chosen.values, Cs[full].values.astype(float), groups=Cs.contract.values).fit(disp=0)
        LOG["statsmodels_check_coef"] = dict(zip(full, map(float, cm.params)))
    except Exception as ex:  # pragma: no cover
        LOG["statsmodels_check_coef"] = str(ex)

    # ---------- 6. single bids
    rates, lres = single_bid(P, F)
    rates.to_csv(OUT / "F_single_bid_rates.csv", index=False)
    lres.to_csv(OUT / "F_single_bid_logit.csv", index=False)

    json.dump(LOG, open(OUT / "revision_a_log.json", "w", encoding="utf-8"), indent=2, default=str, ensure_ascii=False)


if __name__ == "__main__":
    main()
