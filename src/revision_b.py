# -*- coding: utf-8 -*-
"""TenderNet v3 — topic `revision_b` (referee round B).

1. 21(b) x post-7144 incumbency logit with / without buyer-history controls,
   two-way (buyer, firm) vs buyer-only clustering; ORs and AMEs.
2. Event study: 21(b)-open incumbency difference by year (LPM; all buyers,
   health buyers, health buyers with buyer FE) + break / trend comparison.  Figure F-B1.
3. 21(f) monetary limits vs contract values (legal text itself is in the md).
4. Buyer size vs dependence reconciliation (from lockin outputs).
5. Descriptive table by product market and buyer sector (CSV + LaTeX rows).
6. PPI (Yi-UFE) deflator robustness of value-based HHI by product market.

Run from anywhere:  python src/revision_b.py
Requires models_common.py / models_features.py / concentration_v3.py (imported, not modified).
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from models_common import ROOT, load, mle_twoway, twoway_vcov, oneway_vcov, ols_scores  # noqa: E402
from models_features import contract_history  # noqa: E402
import concentration_v3 as C3  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

warnings.filterwarnings("ignore")
np.random.seed(42)
RES = ROOT / "results" / "revision_b"
FIG = ROOT / "figures"
RES.mkdir(parents=True, exist_ok=True)
OI = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7", "#000000"]
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


def expit(x):
    return 1 / (1 + np.exp(-x))


def fe(df, col, prefix):
    return pd.get_dummies(df[col].astype(str), prefix=prefix, drop_first=True, dtype=float)


def fmt_p(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


# ============================================================ data (A sample as in models_analysis)
d = contract_history(load("main"))
A = d[d.buyer_has_history == 1].copy().reset_index(drop=True)
A["log_prior_suppliers"] = np.log(A.bm_prior_suppliers)
A["log_prior_contracts"] = np.log(A.bm_prior_contracts)
A["years_since_first"] = A.bm_years_since_first
A["p_21b"] = (A.proc == "21b").astype(float)
A["p_oth_neg"] = (A.proc == "oth_neg").astype(float)
A["p21b_x_post"] = A.p_21b * A.post7144
A["yearfe"] = A.year.clip(lower=2011)
A["health"] = (A.sektor_v3_en == "Health").astype(int)
log(f"A sample N={len(A)}, buyers={A.buyer.nunique()}, firms={A.firm.nunique()}, mean y={A.incumbent_win.mean():.4f}")

HIST = ["log_prior_suppliers", "log_prior_contracts", "years_since_first"]
BASE = ["p_21b", "p_oth_neg", "log_real_value", "post7144", "p21b_x_post"]


def design(df, core, fes=("yearfe", "market", "sektor_v3")):
    parts = [df[core].astype(float)] + [fe(df, c, "fe_" + c) for c in fes]
    return sm.add_constant(pd.concat(parts, axis=1), has_constant="add")


# ============================================================ 1. controls x clustering
def ame_fn(X, cols, which):
    j = {c: i for i, c in enumerate(cols)}

    def cf(Z):
        Z1, Z0 = Z.copy(), Z.copy()
        Z1[:, j["p_21b"]] = 1; Z1[:, j["p_oth_neg"]] = 0; Z1[:, j["p21b_x_post"]] = Z1[:, j["post7144"]]
        Z0[:, j["p_21b"]] = 0; Z0[:, j["p_oth_neg"]] = 0; Z0[:, j["p21b_x_post"]] = 0
        return Z1, Z0
    post = X[:, j["post7144"]] == 1
    subs = {"all": X, "pre": X[~post], "post": X[post]}

    def f(b, Z):
        Z1, Z0 = cf(Z)
        return np.mean(expit(Z1 @ b) - expit(Z0 @ b))
    if which == "post-pre":
        return lambda b: f(b, subs["post"]) - f(b, subs["pre"])
    return lambda b: f(b, subs[which])


def delta(fun, b, V, eps=1e-6):
    est = fun(b)
    g = np.array([(fun(b + eps * e) - fun(b - eps * e)) / (2 * eps) for e in np.eye(len(b))])
    return est, float(np.sqrt(max(g @ V @ g, 0)))


rows1 = []
specs1 = [("S1 full history controls (= A1)", BASE[:3] + HIST + BASE[3:]),
          ("S2 no prior-count controls (keeps years since first)", BASE[:3] + ["years_since_first"] + BASE[3:]),
          ("S3 no buyer-history controls", BASE)]
for sname, core in specs1:
    X = design(A, core)
    cols = list(X.columns)
    res = sm.Logit(A.incumbent_win.values, X.values).fit(disp=0, maxiter=200, method="newton")
    S = np.asarray(res.model.score_obs(res.params))
    Hinv = np.linalg.inv(-res.model.hessian(res.params))
    V2, G2, nneg = twoway_vcov(S, Hinv, A.buyer.values, A.firm.values)
    V1, G1 = oneway_vcov(S, Hinv, A.buyer.values)
    for vname, V in [("two-way (buyer, firm)", V2), ("buyer only", V1)]:
        k = cols.index("p21b_x_post")
        b, se = res.params[k], np.sqrt(V[k, k])
        r = dict(spec=sname, se_type=vname, N=len(A), pseudoR2=res.prsquared, loglik=res.llf,
                 int_coef=b, int_se=se, int_OR=np.exp(b), int_OR_lo=np.exp(b - 1.96 * se),
                 int_OR_hi=np.exp(b + 1.96 * se), int_p=2 * stats.norm.sf(abs(b / se)))
        for w in ["pre", "post", "post-pre"]:
            e, s = delta(ame_fn(X.values, cols, w), res.params, V)
            r[f"AME21b_{w}_pp"] = 100 * e
            r[f"AME21b_{w}_lo"] = 100 * (e - 1.96 * s)
            r[f"AME21b_{w}_hi"] = 100 * (e + 1.96 * s)
            r[f"AME21b_{w}_p"] = 2 * stats.norm.sf(abs(e / s))
        rows1.append(r)
    log(f"[1] {sname}: OR={np.exp(res.params[cols.index('p21b_x_post')]):.3f}, clusters two-way={G2}, buyer={G1}, clipped={nneg}")
T1 = pd.DataFrame(rows1)
T1.to_csv(RES / "B1_controls_clustering.csv", index=False)

# ============================================================ 2. event study
BINS = [(2010, 2012, "2010–12")] + [(y, y, str(y)) for y in range(2013, 2025)] + [(2025, 2026, "2025–26")]
A["ybin"] = ""
for lo, hi, lab in BINS:
    A.loc[A.year.between(lo, hi), "ybin"] = lab
BLABS = [b[2] for b in BINS]
BMID = {lab: (lo + hi) / 2 for lo, hi, lab in BINS}
for lab in BLABS:
    A[f"b21_{lab}"] = A.p_21b * (A.ybin == lab)
    A[f"oth_{lab}"] = A.p_oth_neg * (A.ybin == lab)
EV = [f"b21_{l}" for l in BLABS]
OTH = [f"oth_{l}" for l in BLABS]
PRE1317 = [f"b21_{y}" for y in range(2013, 2018)]
CTRL = ["log_real_value"] + HIST


def demean(M, g):
    M = pd.DataFrame(M)
    return (M - M.groupby(g).transform("mean")).values


def lpm(df, core, fes, buyer_fe=False):
    """OLS LPM with two-way (buyer, firm) clustered V. Returns b, V, cols, rss, n, k."""
    X = design(df, core, fes)
    y = df.incumbent_win.values.astype(float)
    if buyer_fe:
        X = X.drop(columns="const")
        Xv = demean(X.values, df.buyer.values)
        y = demean(y.reshape(-1, 1), df.buyer.values).ravel()
        keep = np.abs(Xv).sum(0) > 1e-10
        Xv, cols = Xv[:, keep], list(X.columns[keep])
    else:
        Xv, cols = X.values.astype(float), list(X.columns)
    # drop exactly collinear columns (e.g. empty bins)
    q, r = np.linalg.qr(Xv)
    ok = np.abs(np.diag(r)) > 1e-8
    Xv, cols = Xv[:, ok], [c for c, o in zip(cols, ok) if o]
    b = np.linalg.lstsq(Xv, y, rcond=None)[0]
    S, H = ols_scores(Xv, y, b)
    V, G, _ = twoway_vcov(S, H, df.buyer.values, df.firm.values)
    rss = float(((y - Xv @ b) ** 2).sum())
    k = Xv.shape[1] + (df.buyer.nunique() if buyer_fe else 0)
    return b, V, cols, rss, len(y), k


def wald(b, V, cols, R_rows):
    """R_rows: list of dicts {col: weight}."""
    R = np.array([[rw.get(c, 0.0) for c in cols] for rw in R_rows])
    Rb, RVR = R @ b, R @ V @ R.T
    W = float(Rb @ np.linalg.pinv(RVR) @ Rb)
    df_ = np.linalg.matrix_rank(RVR)
    return W, df_, stats.chi2.sf(W, df_)


samples = {"(a) all buyers": (A, ("yearfe", "market", "sektor_v3"), False),
           "(b) health buyers": (A[A.health == 1].copy(), ("yearfe", "market"), False),
           "(c) health buyers, buyer FE": (A[A.health == 1].copy(), ("yearfe", "market"), True)}
ev_rows, brk_rows, cnt_rows, wald_rows = [], [], [], []
for sname, (df, fes, bfe) in samples.items():
    for lab in BLABS:
        m = df.ybin == lab
        cnt_rows.append(dict(sample=sname, bin=lab, n=int(m.sum()), n_21b=int((m & (df.p_21b == 1)).sum()),
                             n_open=int((m & (df.proc == "open")).sum()),
                             raw_inc_21b=df.loc[m & (df.p_21b == 1), "incumbent_win"].mean(),
                             raw_inc_open=df.loc[m & (df.proc == "open"), "incumbent_win"].mean()))
    for ctl_name, ctl in [("with history controls", CTRL), ("value only (no history controls)", ["log_real_value"])]:
        b, V, cols, rss, n, k = lpm(df, EV + OTH + ctl, fes, bfe)
        est = {}
        for lab in BLABS:
            c = f"b21_{lab}"
            if c in cols:
                i = cols.index(c)
                est[lab] = (b[i], np.sqrt(V[i, i]))
        base = "b21_2010–12"
        for lab, (e, s) in est.items():
            # difference relative to the pooled 2010–12 base
            if lab != "2010–12" and base in cols:
                i, j0 = cols.index(f"b21_{lab}"), cols.index(base)
                dd = b[i] - b[j0]
                sd = np.sqrt(V[i, i] + V[j0, j0] - 2 * V[i, j0])
            else:
                dd, sd = 0.0, np.nan
            # difference relative to the 2013–17 average (post-left-censoring, pre-reform)
            rv = np.array([(1.0 if c == f"b21_{lab}" else 0.0) - (0.2 if c in PRE1317 else 0.0) for c in cols])
            d2, s2 = float(rv @ b), float(np.sqrt(rv @ V @ rv))
            ev_rows.append(dict(sample=sname, controls=ctl_name, bin=lab, year_mid=BMID[lab],
                                vs_1317_pp=100 * d2, vs_1317_lo=100 * (d2 - 1.96 * s2), vs_1317_hi=100 * (d2 + 1.96 * s2),
                                vs_1317_p=2 * stats.norm.sf(abs(d2 / s2)) if s2 > 1e-12 else np.nan,
                                diff_pp=100 * e, se_pp=100 * s, lo=100 * (e - 1.96 * s), hi=100 * (e + 1.96 * s),
                                p=2 * stats.norm.sf(abs(e / s)), vs_base_pp=100 * dd,
                                vs_base_lo=100 * (dd - 1.96 * sd), vs_base_hi=100 * (dd + 1.96 * sd),
                                vs_base_p=2 * stats.norm.sf(abs(dd / sd)) if sd == sd else np.nan))
        # Wald tests
        labs = [l for l in BLABS if f"b21_{l}" in cols]
        pre = [l for l in labs if l.isdigit() and 2013 <= int(l) <= 2017]
        post = [l for l in labs if l not in pre and l != "2018"]
        allR = [{f"b21_{l}": 1, f"b21_{labs[0]}": -1} for l in labs[1:]]
        preR = [{f"b21_{l}": 1, f"b21_{pre[0]}": -1} for l in pre[1:]]
        postR = [{f"b21_{l}": 1, f"b21_{post[0]}": -1} for l in post[1:]]
        meanR = [{**{f"b21_{l}": 1 / len(post) for l in post}, **{f"b21_{l}": -1 / len(pre) for l in pre}}]
        r18 = [{"b21_2018": 1, **{f"b21_{l}": -1 / len(pre) for l in pre}}]
        r1012 = [{"b21_2010–12": 1, **{f"b21_{l}": -1 / len(pre) for l in pre}}]
        for tname, R in [("all bins equal", allR), ("2013–17 bins equal", preR),
                         ("post bins (>=2019) equal", postR), ("mean post(>=2019) = mean 2013–17", meanR),
                         ("mean 2018 = mean 2013–17", r18), ("mean 2010–12 = mean 2013–17", r1012)]:
            W, dfw, p = wald(b, V, cols, R)
            extra = {}
            if tname.startswith("mean"):
                Rv = np.array([[R[0].get(c, 0.0) for c in cols]])
                extra = dict(estimate_pp=100 * float(Rv @ b), se_pp=100 * float(np.sqrt(Rv @ V @ Rv.T)))
            wald_rows.append(dict(sample=sname, controls=ctl_name, test=tname, W=W, df=dfw, p=p, **extra))
        log(f"[2] {sname} / {ctl_name}: N={n}, k={k}, 21b bins estimated={len(labs)}")

    # ---- parametric comparison (with history controls): constant / trend / steps
    df = df.copy()
    df["t18"] = (df.date - pd.Timestamp("2018-01-01")).dt.days / 365.25
    df["b21_t"] = df.p_21b * df.t18
    df["oth_t"] = df.p_oth_neg * df.t18
    cands = {"constant": []}
    cands["linear trend"] = ["b21_t"]
    breaks = {f"{y}-01-01": pd.Timestamp(f"{y}-01-01") for y in range(2013, 2025)}
    breaks["2017-08-25 (KHK 694)"] = pd.Timestamp("2017-08-25")
    breaks["2018-05-25 (Law 7144)"] = pd.Timestamp("2018-05-25")
    for bn, bd in breaks.items():
        df[f"step_{bn}"] = df.p_21b * (df.date >= bd)
        cands[f"step {bn}"] = [f"step_{bn}"]
    df["step_7144"] = df.p_21b * (df.date >= pd.Timestamp("2018-05-25"))
    cands["trend + step 2018-05-25"] = ["b21_t", "step_7144"]
    df["step_khk"] = df.p_21b * (df.date >= pd.Timestamp("2017-08-25"))
    cands["trend + step 2017-08-25"] = ["b21_t", "step_khk"]
    for cn, extra in cands.items():
        core = ["p_21b", "p_oth_neg", "oth_t"] + extra + CTRL
        b, V, cols, rss, n, k = lpm(df, core, fes, bfe)
        aic = n * np.log(rss / n) + 2 * k
        r = dict(sample=sname, model=cn, n=n, k=k, rss=rss, AIC=aic)
        for c in extra:
            i = cols.index(c)
            r[f"coef_{'trend' if c == 'b21_t' else 'step'}_pp"] = 100 * b[i]
            r[f"se_{'trend' if c == 'b21_t' else 'step'}_pp"] = 100 * np.sqrt(V[i, i])
            r[f"p_{'trend' if c == 'b21_t' else 'step'}"] = 2 * stats.norm.sf(abs(b[i] / np.sqrt(V[i, i])))
        brk_rows.append(r)
    # unrestricted (event-study) AIC for reference
    b, V, cols, rss, n, k = lpm(df, EV + ["p_oth_neg", "oth_t"] + CTRL, fes, bfe)
    brk_rows.append(dict(sample=sname, model="unrestricted year bins", n=n, k=k, rss=rss,
                         AIC=n * np.log(rss / n) + 2 * k))

EVT = pd.DataFrame(ev_rows); EVT.to_csv(RES / "B2_event_study.csv", index=False)
BRK = pd.DataFrame(brk_rows)
BRK["dAIC_vs_best"] = BRK.AIC - BRK.groupby("sample").AIC.transform("min")
BRK.to_csv(RES / "B2_break_models.csv", index=False)
CNT = pd.DataFrame(cnt_rows); CNT.to_csv(RES / "B2_event_counts.csv", index=False)
WLD = pd.DataFrame(wald_rows); WLD.to_csv(RES / "B2_wald_tests.csv", index=False)


# ---- figure F-B1
def fig_b1():
    C3.style()
    plt.rcParams.update({"font.size": 8})
    fig, axes = plt.subplots(1, 3, figsize=(7, 2.9), sharey=True)
    E = EVT[EVT.controls == "with history controls"]
    cols_ = [OI[4], OI[5], OI[2]]
    for ax, (sname, c) in zip(axes, zip(samples, cols_)):
        e = E[E["sample"] == sname].sort_values("year_mid")
        x = e.year_mid.values
        ax.axhline(0, color="0.3", lw=0.8)
        for xd, ls in [(2017 + 237 / 365, ":"), (2018 + 144 / 365, "--")]:
            ax.axvline(xd, color="0.4", lw=0.8, ls=ls)
        pm_ = e[e.bin.isin([str(y) for y in range(2013, 2018)])].diff_pp.mean()
        ax.hlines(pm_, 2012.5, 2017.5, color="0.35", lw=1.2, ls="-", zorder=1)
        ax.fill_between(x, e.lo, e.hi, color=c, alpha=0.18, lw=0)
        ax.errorbar(x, e.diff_pp, yerr=[e.diff_pp - e.lo, e.hi - e.diff_pp], fmt="o-", color=c, ms=3.2,
                    lw=1, elinewidth=0.9, capsize=0)
        ax.set_xticks([2011, 2014, 2017, 2020, 2023, 2025.5])
        ax.set_xticklabels(["10–12", "14", "17", "20", "23", "25–26"], rotation=0)
        ax.set_ylim(-58, 80)
        ax.set_xlim(2010, 2026.5)
        ax.grid(True, color="0.9", lw=0.5)
        ax.set_axisbelow(True)
        ax.text(0.03, 0.97, sname, transform=ax.transAxes, va="top", ha="left", fontsize=8)
        ax.set_xlabel("Tender year (20xx)")
    axes[0].set_ylabel("21(b) − open, P(incumbent wins)\n(percentage points, 95% CI)")
    axes[2].text(2017 + 237 / 365 - 0.2, 0.03, "KHK 694", transform=axes[2].get_xaxis_transform(),
                 rotation=90, ha="right", va="bottom", fontsize=7, color="0.3")
    axes[2].text(2018 + 144 / 365 + 0.25, 0.03, "Law 7144", transform=axes[2].get_xaxis_transform(),
                 rotation=90, ha="left", va="bottom", fontsize=7, color="0.3")
    fig.tight_layout(w_pad=0.6)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"F-B1_event_study_21b.{ext}", dpi=300)
    plt.close(fig)


fig_b1()

# ============================================================ 3. 21(f) limits vs values
LIM21F = [("2014-02-01", 157923), ("2015-02-01", 167966), ("2016-02-01", 177556), ("2017-02-01", 195205),
          ("2018-02-01", 225403), ("2019-02-01", 301228), ("2020-02-01", 323398), ("2021-02-01", 404732),
          ("2022-02-01", 728072), ("2023-02-01", 1439543), ("2024-02-01", 2076108), ("2025-02-01", 2668214),
          ("2026-02-01", 3406508)]
lim = pd.DataFrame(LIM21F, columns=["from", "limit_TRY"]); lim["from"] = pd.to_datetime(lim["from"])
f = d[d.usul_v3 == "negotiated_21f"].copy()
f = f[f.date >= lim["from"].min()].sort_values("date")
f = pd.merge_asof(f, lim.sort_values("from"), left_on="date", right_on="from")
f["le_limit"] = f.bedel_num <= f.limit_TRY
f["ratio"] = f.bedel_num / f.limit_TRY
L21F = f.groupby(f.date.dt.year).agg(n=("le_limit", "size"), share_le_limit=("le_limit", "mean"),
                                     median_ratio=("ratio", "median"), p95_ratio=("ratio", lambda s: s.quantile(.95)),
                                     max_ratio=("ratio", "max")).reset_index().rename(columns={"date": "year"})
L21F.to_csv(RES / "B3_21f_limit_check.csv", index=False)
tot21f = dict(n=len(f), share=f.le_limit.mean(), n_over=int((~f.le_limit).sum()))
# comparison: other procedures below the same limit
o = d[(d.date >= lim["from"].min())].sort_values("date")
o = pd.merge_asof(o, lim.sort_values("from"), left_on="date", right_on="from")
share_open_le = (o[o.usul_v3 == "open"].bedel_num <= o[o.usul_v3 == "open"].limit_TRY).mean()
share_21b_le = (o[o.usul_v3 == "negotiated_21b"].bedel_num <= o[o.usul_v3 == "negotiated_21b"].limit_TRY).mean()
ftype = d[d.usul_v3 == "negotiated_21f"].ihale_turu.value_counts().to_dict()
log(f"[3] 21f (from Feb 2014): n={tot21f['n']}, <= limit {tot21f['share']:.3f}; open <= limit {share_open_le:.3f}; 21b {share_21b_le:.3f}; types {ftype}")

# ============================================================ 4. buyer size vs dependence
bd = pd.read_csv(ROOT / "results" / "lockin" / "buyer_dependence.csv")
bd = bd[(bd["null"] == "N1")]
bd["size_bin"] = pd.cut(bd.n_contracts, [4, 9, 19, 10 ** 6], labels=["5–9", "10–19", ">=20"])
bd["excess"] = bd.obs - bd.null_mean
bd["thr_margin"] = bd.null_p95 - bd.null_mean
B4 = bd.groupby(["measure", "size_bin"]).agg(buyers=("obs", "size"), mean_obs=("obs", "mean"),
                                             mean_null=("null_mean", "mean"), mean_excess=("excess", "mean"),
                                             median_excess=("excess", "median"),
                                             mean_p95_minus_nullmean=("thr_margin", "mean"),
                                             share_exceed=("exceeds_p95", "mean")).reset_index()
B4.to_csv(RES / "B4_buyer_size_dependence.csv", index=False)
# correlation of size with excess among buyers (top share)
bt = bd[bd.measure == "top"]
rho_ex, p_ex = stats.spearmanr(bt.n_contracts, bt.excess)
rho_ex_ex, p_ex_ex = stats.spearmanr(bt.n_contracts, bt.exceeds_p95)
log(f"[4] spearman(size, excess top share)={rho_ex:.3f} p={p_ex:.3g}; with exceed flag {rho_ex_ex:.3f}")

# ============================================================ 5. descriptive table
m = load("main")
m["is21b"] = m.usul_v3 == "negotiated_21b"
m["is21f"] = m.usul_v3 == "negotiated_21f"
m["isopen"] = m.usul_v3 == "open"


def desc(g):
    return pd.Series(dict(contracts=len(g), firms=g.firma_v3.nunique(), buyers=g.kurum_il_split.nunique(),
                          value_bn_2025=g.real_value.sum() / 1e9,
                          pct_21b=100 * g.is21b.mean(), pct_21f=100 * g.is21f.mean(), pct_open=100 * g.isopen.mean(),
                          pct_value_21b=100 * g.loc[g.is21b, "real_value"].sum() / g.real_value.sum()))


PM = m.groupby("urun_pazari").apply(desc).sort_values("contracts", ascending=False).reset_index()
PM.insert(0, "dimension", "product market"); PM = PM.rename(columns={"urun_pazari": "group"})
SE = m.groupby("sektor_v3_en").apply(desc).sort_values("contracts", ascending=False).reset_index()
SE.insert(0, "dimension", "buyer sector"); SE = SE.rename(columns={"sektor_v3_en": "group"})
TOT = desc(m).to_frame().T; TOT.insert(0, "group", "All"); TOT.insert(0, "dimension", "total")
DES = pd.concat([PM, SE, TOT], ignore_index=True)
for c in ["contracts", "firms", "buyers"]:
    DES[c] = DES[c].astype(int)
DES.to_csv(RES / "B5_descriptives.csv", index=False)
mx = m.loc[m.real_value.idxmax()]
largest = dict(value_bn=mx.real_value / 1e9, market=mx.urun_pazari, sector=mx.sektor_v3_en, usul=mx.usul_v3)
PRETTY = dict(C3.PRETTY)


def latex_rows(t):
    out = []
    for _, r in t.iterrows():
        name = PRETTY.get(r.group, r.group).replace("&", r"\&").replace("/", "/")
        out.append(f"{name} & {int(r.contracts):,} & {int(r.firms):,} & {int(r.buyers):,} & {r.value_bn_2025:.2f} & "
                   f"{r.pct_21b:.1f} & {r.pct_21f:.1f} & {r.pct_open:.1f} \\\\")
    return "\n".join(out)


# ============================================================ 6. PPI deflator robustness
ppi = pd.read_csv(ROOT / "data" / "ppi_turkey_yiufe.csv")
PPI = dict(zip(ppi.year, ppi.ppi_annual_avg))
dd6, cpi, _ = C3.load()
main6 = dd6[dd6.in_scope_main].copy()
main6["real_cpi"] = main6.real
main6["real_ppi"] = main6.bedel_num * main6.yil_v3.map(lambda y: PPI[2025] / PPI[y])
rng = np.random.default_rng(42)
out6 = []
for defl in ["cpi", "ppi"]:
    t = main6.copy(); t["real"] = t[f"real_{defl}"]
    cap = np.percentile(t.real, 99)
    for dim in ["urun_pazari", "sektor_v3_en"]:
        g = C3.by_group(t, dim, "firma_v3", cap, rng, boot=False, extra_all=(dim == "urun_pazari"))
        g.insert(0, "dimension", dim); g.insert(0, "deflator", defl)
        out6.append(g)
H6 = pd.concat(out6, ignore_index=True)
keep6 = ["deflator", "dimension", "group", "n_contracts", "value_bn_2025", "HHI_count", "HHI_value",
         "HHI_value_nomax", "HHI_value_wins", "LOO_value_min", "CR4_value"]
H6 = H6[keep6]
W6 = H6[H6.deflator == "cpi"].merge(H6[H6.deflator == "ppi"], on=["dimension", "group"], suffixes=("_cpi", "_ppi"))
changes = []
for v in ["HHI_value", "HHI_value_nomax", "HHI_value_wins", "LOO_value_min"]:
    W6[f"class_{v}_cpi"] = W6[f"{v}_cpi"].map(C3.classify)
    W6[f"class_{v}_ppi"] = W6[f"{v}_ppi"].map(C3.classify)
    W6[f"d_{v}"] = W6[f"{v}_ppi"] - W6[f"{v}_cpi"]
    ch = W6[W6[f"class_{v}_cpi"] != W6[f"class_{v}_ppi"]]
    for _, r in ch.iterrows():
        changes.append(dict(measure=v, dimension=r.dimension, group=r.group, cpi=r[f"{v}_cpi"], ppi=r[f"{v}_ppi"],
                            class_cpi=r[f"class_{v}_cpi"], class_ppi=r[f"class_{v}_ppi"]))
mincols = ["HHI_count_cpi", "HHI_value", "HHI_value_nomax", "LOO_value_min", "HHI_value_wins"]
W6["robust_class_cpi"] = W6[["HHI_count_cpi"] + [f"{c}_cpi" for c in mincols[1:]]].min(1).map(C3.classify)
W6["robust_class_ppi"] = W6[["HHI_count_ppi"] + [f"{c}_ppi" for c in mincols[1:]]].min(1).map(C3.classify)
CH6 = pd.DataFrame(changes)
W6.to_csv(RES / "B6_hhi_cpi_vs_ppi.csv", index=False)
CH6.to_csv(RES / "B6_class_changes.csv", index=False)
n_robust_change = int((W6.robust_class_cpi != W6.robust_class_ppi).sum())
log(f"[6] class changes: {len(CH6)}; robust class changes {n_robust_change}")

# ============================================================ fixed text (written after inspecting the output)
BREAK_VERDICT = """### Verdict on the break (plain language)

- **There is a discrete jump, and it is in 2018.** Measured against the 2013–17 average, the 21(b) − open incumbency gap jumps in 2018:
  - all buyers: +37 pp (95% CI 24 to 50)
  - health buyers: +43 pp (23 to 62)

  No 2013–17 year differs from the 2013–17 mean (joint tests p = 0.19 and 0.20).
- **Part of the jump persists.** From 2019 on, the gap is on average above its 2013–17 level:
  - all buyers: +14 pp (p = 0.003)
  - health buyers: +12 pp (p = 0.038)

  This is not a clean level shift. 2019 and 2024 fall back near the pre-reform level, 2020 (COVID) is high, and among health buyers 2022–24 are near zero.
- **Best-fitting shape.** In all three samples the best-fitting parametric shape is a step at 25 Aug 2017 combined with a *declining* 21(b)-specific trend. The step is +25 to +32 pp and the trend −1.8 to −3.1 pp per year. By AIC:
  - a step at 25 May 2018 fits worse, by 3.4–3.7 points;
  - a pure linear trend fits worst, about as badly as a constant.
- **Within health buyers (buyer FE) the shift is clearest and most persistent.**
  - In 2013–17 the gap averages −10 pp.
  - It is positive in every bin from 2018 on (+5 to +19 pp).
  - The post-2019 mean is +24 pp above 2013–17 (95% CI 10 to 38, p < 0.001).
- **When: between late 2017 and mid-2018.** The data cannot separate KHK 694 (25 Aug 2017) from Law 7144 (25 May 2018) because too few repeat-eligible 21(b) contracts fall between the two dates:

  | window | repeat-eligible 21(b) contracts | raw incumbent-win rate |
  |---|---:|---:|
  | 2013–16 | – | 0.53 |
  | 25 Aug–31 Dec 2017 | 8 | 0.50 |
  | 1 Jan–24 May 2018 | 10 | 0.70 |
  | 25 May–31 Dec 2018 | – | 0.86 |
- **Base caveat.** The pooled 2010–12 bin also has a high gap: +16 pp for all buyers and +28 pp for health buyers, both significantly above 2013–17.
  - Measured against a 2010–12 base, no post-2018 year is significantly higher in any sample (last column of the tables above).
  - We do not use 2010–12 as the reference. It is the left-censored start of the window, with at most about two years of buyer history and only 24 21(b) contracts.
  - A reader who did use it would conclude that 2013–17 is an unusual trough, not that 2018 is an unusual peak.
  - The 2010–12 bin is a likely reason why the buyer-FE interaction in `models` (A5) was null (+7.3 pp, p = 0.20): its "pre" period includes 2010–12.
- **Without history controls** the pattern is the same (`B2_wald_tests.csv`). Post-2019 vs 2013–17 is:
  - all buyers: +22.5 pp
  - health buyers: +15.0 pp
  - health buyers with buyer FE: +25.2 pp

  All three have p ≤ 0.015.
"""

LEGAL = """**Source.** Consolidated text of Law 4734 on mevzuat.gov.tr (`https://www.mevzuat.gov.tr/MevzuatMetin/1.5.4734.pdf`, downloaded 2026-09-26), Art. 21 and its footnotes 30–31.
- Footnote 30 records the 2018 change: *"16/5/2018 tarihli ve 7144 sayılı Kanunun 11 inci maddesiyle bu bentte yer alan 'beklenmeyen veya' ibaresinden sonra gelmek üzere '…' ibaresi eklenmiştir."*
- The pre-2018 wording is therefore the current wording minus the inserted phrase. This matches the Resmî Gazete text of Law 7144, Art. 11 (RG 25.05.2018 / 30431), cited in `docs/law_notes.md`.
- The chapeau reads *"Aşağıda belirtilen hallerde pazarlık usulü ile ihale yapılabilir:"* ("The negotiated procedure may be used in the following cases:").
- All translations are ours, not official.

**21(b) before 25 May 2018** (wording set by Law 5812 of 2008, in force until Law 7144):
> b) Doğal afetler, salgın hastalıklar, can veya mal kaybı tehlikesi gibi ani ve beklenmeyen veya idare tarafından önceden öngörülemeyen olayların ortaya çıkması üzerine ihalenin ivedi olarak yapılmasının zorunlu olması.

*EN:* (b) Where the tender must be held urgently because of the occurrence of sudden and unexpected events, such as natural disasters, epidemics or a danger of loss of life or property, or of events the contracting authority could not foresee in advance.

**21(b) from 25 May 2018** (inserted text in bold):
> b) Doğal afetler, salgın hastalıklar, can veya mal kaybı tehlikesi gibi ani ve beklenmeyen veya **yapım tekniği açısından özellik arz eden veya yapı veya can ve mal güvenliğinin sağlanması açısından ivedilikle yapılması gerekliliği idarece belirlenen hallerde veyahut** idare tarafından önceden öngörülemeyen olayların ortaya çıkması üzerine ihalenin ivedi olarak yapılmasının zorunlu olması.

*EN:* (b) Where the tender must be held urgently because of the occurrence of sudden and unexpected events, such as natural disasters, epidemics or a danger of loss of life or property, **or in cases that have special features in terms of construction technique, or in which the contracting authority determines that the work must be carried out urgently to ensure structural safety or the safety of life and property, or** of events the contracting authority could not foresee in advance.

**The other grounds.** These were unchanged from 2010 to 2026, apart from the annual update of the 21(f) amount.
- **21(a)** *Açık ihale usulü veya belli istekliler arasında ihale usulü ile yapılan ihale sonucunda teklif çıkmaması.*
  EN: No tender was submitted in an open or restricted procedure.
- **21(c)** *Savunma ve güvenlikle ilgili özel durumların ortaya çıkması üzerine ihalenin ivedi olarak yapılmasının zorunlu olması.*
  EN: The tender must be held urgently because special defence- or security-related circumstances have arisen.
- **21(d)** *İhalenin, araştırma ve geliştirme sürecine ihtiyaç gösteren ve seri üretime konu olmayan nitelikte olması.*
  EN: The procurement requires a research-and-development process and is not subject to serial production.
- **21(e)** *İhale konusu mal veya hizmet alımları ile yapım işlerinin özgün nitelikte ve karmaşık olması nedeniyle teknik ve malî özelliklerinin gerekli olan netlikte belirlenememesi.*
  EN: The technical and financial characteristics of the goods, services or works cannot be specified with the necessary precision because they are original and complex.
- **21(f)** *(Ek: 30/7/2003-4964/14 md.) İdarelerin yaklaşık maliyeti ellimilyar Türk Lirasına kadar olan mamul mal, malzeme veya hizmet alımları.*
  EN: Purchases by contracting authorities of manufactured goods, materials or services whose estimated cost (*yaklaşık maliyet*) is up to fifty billion (old) Turkish lira.
  - This equals 50,000 TRY after the 2005 redenomination, before indexation.
  - Under Art. 67, KİK updates the amount every 1 February using the previous year's producer (wholesale) price index.
  - Footnote 31 points to KİK Communiqué 2025/1 (RG 24.01.2025 / 32792) for the current amount.
- **Second paragraph** (Law 5812, 2008): *"(b), (c) ve (f) bentlerinde belirtilen hallerde ilan yapılması zorunlu değildir. İlan yapılmayan hallerde en az üç istekli davet edilerek, yeterlik belgelerini ve fiyat tekliflerini birlikte vermeleri istenir."*
  EN: In cases (b), (c) and (f), publishing a notice is not compulsory. Where no notice is published, at least three tenderers are invited and asked to submit their qualification documents and price offers together.
- **Fourth paragraph:** cases (a), (d) and (e) instead follow a two-stage procedure, with technical offers first and price offers second.

**What 21(f) covers (confirmed).** 21(f) is not an urgency or exceptional-circumstance ground.
- **It is a value-based ground.** It applies to any purchase of goods or services (not works) whose estimated cost is below a monetary limit. That limit is written into Art. 21(f) itself, is indexed every year, and is separate from, and much lower than, the Art. 8 EU-style thresholds.
- Like 21(b), it lets the authority skip the public notice and invite at least three firms instead.
- **In our data**, all 2,957 main-sample 21(f) contracts are goods (*Mal*, 851) or services (*Hizmet*, 2,106); none are works. Their contract amounts sit just under the limit in force (table below).
- **Wording.** "Below-threshold" is accurate if phrased as "below the Art. 21(f) monetary limit".
- **The limit over time:**

  | from | 21(f) limit (TRY) |
  |---|---:|
  | 2014 | 157,923 |
  | Feb 2024 | 2,076,108 |
  | Feb 2026 | 3,406,508 |
"""

SIZE_TEXT = """**Reconciliation.** The two results measure different things.
- **The tercile table measures size.** It gives the excess incumbency per contract, and that excess falls somewhat with buyer size.
- The buyer-level data agree. Among the 540 tested buyers, the mean excess top-supplier share also falls with size:

  | buyer size (contracts) | mean excess top-supplier share | p95 − null-mean margin |
  |---|---:|---:|
  | 5–9 | 0.24 | 0.10 |
  | 10–19 | 0.23 | 0.07 |
  | ≥ 20 | 0.13 | 0.03 |
- **The share exceeding the 95th null percentile measures detectability.** Detectability rises with size because the null distribution tightens as n grows, which the shrinking margin in the last column shows.
- As a result, a large buyer with a modest excess is flagged, while a small buyer with a large excess often is not.

**Suggested sentence:** *"Per contract, excess incumbency is somewhat lower among the largest buyers (0.34 vs 0.45 in the smallest tercile), but because their null distributions are much tighter, a larger share of large buyers is individually distinguishable from the null (80% of buyers with ≥ 20 contracts vs 50% of those with 5–9); the rising share reflects statistical power, not stronger dependence."*
"""

# ============================================================ report
L = []
P = L.append
P("# TenderNet v3 — Referee round B (topic `revision_b`)\n")
P("Code: `src/revision_b.py` (imports `models_common`, `models_features`, `concentration_v3`; none modified). "
  "Sample: main (`in_scope_main`), incumbency sample A = contracts with a strictly earlier contract of the same buyer "
  f"(`kurum_il_split`) in the same product market: N = {len(A):,}, {A.buyer.nunique():,} buyers, {A.firm.nunique():,} firms, "
  f"mean incumbent-win = {A.incumbent_win.mean():.3f}. Seed 42; no resampling in this topic (all inference analytic).\n")

# ---- 1
P("## 1. 21(b) × post-7144: history controls and clustering\n")
P("Logit, FE = year (2010 pooled into 2011), product market, buyer sector; also log real value and 'other negotiated'. "
  "History controls = log # prior contracts and log # distinct prior suppliers of the buyer in the market, years since the buyer's first contract in the market. "
  "AMEs = average difference in P(incumbent win) between 21(b) and open, delta method, evaluated on pre- / post-25-May-2018 contracts.\n")
P("| specification | SE | OR 21(b)×post [95% CI] | p | AME pre (pp) | AME post (pp) | post − pre (pp) | p (post−pre) |")
P("|---|---|---:|---:|---:|---:|---:|---:|")
for _, r in T1.iterrows():
    P(f"| {r.spec} | {r.se_type} | {r.int_OR:.2f} [{r.int_OR_lo:.2f}, {r.int_OR_hi:.2f}] | {fmt_p(r.int_p)} | "
      f"{r['AME21b_pre_pp']:.1f} [{r['AME21b_pre_lo']:.1f}, {r['AME21b_pre_hi']:.1f}] | "
      f"{r['AME21b_post_pp']:.1f} [{r['AME21b_post_lo']:.1f}, {r['AME21b_post_hi']:.1f}] | "
      f"{r['AME21b_post-pre_pp']:.1f} [{r['AME21b_post-pre_lo']:.1f}, {r['AME21b_post-pre_hi']:.1f}] | {fmt_p(r['AME21b_post-pre_p'])} |")
P("")
s1 = T1[(T1.spec.str.startswith("S1")) & (T1.se_type.str.startswith("two"))].iloc[0]
s3 = T1[(T1.spec.str.startswith("S3")) & (T1.se_type.str.startswith("two"))].iloc[0]
P(f"Pseudo-R²: S1 {T1.pseudoR2.iloc[0]:.3f}, S2 {T1.pseudoR2.iloc[2]:.3f}, S3 {T1.pseudoR2.iloc[4]:.3f}. "
  "Point estimates are identical across the two SE types; only the CIs change. "
  f"Dropping all buyer-history controls moves the interaction OR from {s1.int_OR:.2f} to {s3.int_OR:.2f}. "
  "Buyer-only clustering gives narrower CIs than two-way clustering (the firm dimension adds dependence), so the two-way results are the conservative ones. CSV: `B1_controls_clustering.csv`.\n")

# ---- 2
P("## 2. Event study: 21(b) − open incumbency difference by year\n")
P("LPM on sample A: P(incumbent win) = Σ_t δ_t·21(b)·1[bin t] + Σ_t θ_t·other-negotiated·1[bin t] + log real value + history controls + year FE + product-market FE (+ buyer-sector FE in (a); + buyer FE in (c)). "
  "All 21(b)×bin terms are included and the 21(b) main effect is omitted, so δ_t is directly the conditional 21(b) − open difference in bin t (open + 17 restricted = reference; other negotiated procedures get their own bin-specific terms so they do not contaminate the year FE). "
  "Bins: 2010–12 pooled (only 8 21(b) contracts in 2010), each year 2013–2024, 2025–26 pooled. "
  "**Base choice.** The requested 2010–12 base turns out to be a poor reference: sample A in 2010–12 is the start of the observation window (left-censored buyer histories of at most ~2 years; 242 contracts, 24 21(b)), and its δ is imprecise and high. "
  "We therefore report differences both against 2010–12 and against the average of 2013–2017 (the five full pre-reform years), and use the latter as the primary base. "
  "SEs two-way clustered (buyer, winning firm). SEs two-way clustered (buyer, winning firm). Figure: `figures/F-B1_event_study_21b.png/.pdf` (with history controls).\n")
for sname in samples:
    e = EVT[(EVT["sample"] == sname) & (EVT.controls == "with history controls")]
    c = CNT[CNT["sample"] == sname]
    P(f"### {sname}\n")
    P("| bin | contracts | 21(b) | raw inc. 21(b) | raw inc. open | δ (pp) [95% CI] | δ − mean δ(2013–17) (pp) [95% CI] | δ − δ(2010–12) (pp) [95% CI] |")
    P("|---|---:|---:|---:|---:|---:|---:|---:|")
    for _, r in e.iterrows():
        cc = c[c.bin == r.bin].iloc[0]
        vb = "base" if r.bin == "2010–12" else f"{r.vs_base_pp:.1f} [{r.vs_base_lo:.1f}, {r.vs_base_hi:.1f}]"
        P(f"| {r.bin} | {cc.n} | {cc.n_21b} | {cc.raw_inc_21b:.2f} | {cc.raw_inc_open:.2f} | "
          f"{r.diff_pp:.1f} [{r.lo:.1f}, {r.hi:.1f}] | {r.vs_1317_pp:.1f} [{r.vs_1317_lo:.1f}, {r.vs_1317_hi:.1f}] | {vb} |")
    P("")
    w = WLD[(WLD["sample"] == sname) & (WLD.controls == "with history controls")]
    P("Wald tests (two-way V): " + "; ".join(
        f"{r.test}: χ²({r.df})={r.W:.1f}, p={fmt_p(r.p)}" + (f" (difference {r.estimate_pp:.1f} pp, SE {r.se_pp:.1f})" if r.test.startswith("mean") else "")
        for _, r in w.iterrows()) + ".\n")
    bk = BRK[BRK["sample"] == sname].sort_values("AIC")
    P("Parametric shapes for the 21(b) − open difference (same controls; ΔAIC relative to best; Gaussian AIC on RSS):\n")
    P("| model | ΔAIC | step (pp) [p] | trend (pp/yr) [p] |")
    P("|---|---:|---:|---:|")
    for _, r in bk.iterrows():
        st = f"{r.coef_step_pp:.1f} [{fmt_p(r.p_step)}]" if pd.notna(r.get("coef_step_pp")) else ""
        tr = f"{r.coef_trend_pp:.1f} [{fmt_p(r.p_trend)}]" if pd.notna(r.get("coef_trend_pp")) else ""
        P(f"| {r.model} | {r.dAIC_vs_best:.1f} | {st} | {tr} |")
    P("")
P("### Timing inside 2017–2018 (raw incumbent-win rates, sample A, all buyers)\n")
P("| window | 21(b) n | 21(b) incumbent-win | open n | open incumbent-win |")
P("|---|---:|---:|---:|---:|")
for wl, lo_, hi_ in [("2013–2016", "2013-01-01", "2017-01-01"), ("1 Jan–24 Aug 2017", "2017-01-01", "2017-08-25"),
                     ("25 Aug–31 Dec 2017 (after KHK 694)", "2017-08-25", "2018-01-01"),
                     ("1 Jan–24 May 2018", "2018-01-01", "2018-05-25"), ("25 May–31 Dec 2018 (after Law 7144)", "2018-05-25", "2019-01-01"),
                     ("2019–2026", "2019-01-01", "2027-01-01")]:
    w_ = A[(A.date >= lo_) & (A.date < hi_)]
    a_, o_ = w_[w_.p_21b == 1], w_[w_.proc == "open"]
    P(f"| {wl} | {len(a_)} | {a_.incumbent_win.mean():.2f} | {len(o_)} | {o_.incumbent_win.mean():.2f} |")
P("")
P("Without history controls (log value only) the δ_t are in `B2_event_study.csv` (`controls = value only`); Wald tests for both in `B2_wald_tests.csv`, cell counts in `B2_event_counts.csv`, parametric fits in `B2_break_models.csv`.\n")
P(BREAK_VERDICT)

# ---- 3
P("## 3. Statutory text of Law 4734 Art. 21\n")
P(LEGAL)
P("### 21(f) in the data\n")
P(f"Monetary limits for 21(f) (goods/services, TRY, valid 1 Feb–31 Jan) were read from KİK's annual comparison sheets (dosyalar.kik.gov.tr/yardim/dokumanlar/<year>_Esik_Degerler_Parasal_Limitler_Karsilastirma.pdf): "
  + ", ".join(f"{a[:4]}: {b:,}" for a, b in LIM21F) + ". Sheets before 2014 were not available at that URL pattern.\n")
P(f"Main-sample 21(f) contracts tendered from 1 Feb 2014: {tot21f['n']:,}; contract amount ≤ the 21(f) limit in force: **{100 * tot21f['share']:.2f}%** "
  f"({tot21f['n_over']} above; contract amount can differ from the approximate cost that the limit applies to). For comparison, {100 * share_open_le:.1f}% of open and {100 * share_21b_le:.1f}% of 21(b) contracts are below the same limit. "
  f"EKAP tender type of 21(f) contracts: {ftype}.\n")
P("| year | 21(f) contracts | share ≤ limit | median value / limit | 95th pct value / limit |")
P("|---|---:|---:|---:|---:|")
for _, r in L21F.iterrows():
    P(f"| {int(r.year)} | {int(r.n)} | {100 * r.share_le_limit:.1f}% | {r.median_ratio:.2f} | {r.p95_ratio:.2f} |")
P("")

# ---- 4
P("## 4. Buyer size vs dependence: reconciliation\n")
P("Contract-level excess incumbency by buyer-size tercile (from `lockin_results.md` §4e, N1 null): T1 (≤4 contracts) 0.450, T2 (5–13) 0.425, T3 (>13) 0.342. "
  "Buyer-level test (540 buyers with ≥5 contracts, top-supplier share, N1):\n")
P("| measure | size | buyers | mean observed | mean null | mean excess | mean (p95 − null mean) | share exceeding p95 |")
P("|---|---|---:|---:|---:|---:|---:|---:|")
for _, r in B4.iterrows():
    P(f"| {r.measure} | {r.size_bin} | {r.buyers} | {r.mean_obs:.3f} | {r.mean_null:.3f} | {r.mean_excess:.3f} | {r.mean_p95_minus_nullmean:.3f} | {100 * r.share_exceed:.1f}% |")
P("")
P(f"Spearman(size, excess top-supplier share) = {rho_ex:.2f} (p = {fmt_p(p_ex)}); Spearman(size, exceeds-flag) = {rho_ex_ex:.2f} (p = {fmt_p(p_ex_ex)}).\n")
P(SIZE_TEXT)

# ---- 5
P("## 5. Descriptive table (main sample)\n")
P(f"Real value in bn 2025 TRY (CPI). Shares are % of contracts. The single largest contract ({largest['value_bn']:.2f} bn, {largest['market']}, {largest['sector']}, {largest['usul']}) is included. "
  "'Open' = `usul_v3 == open` (the 17 restricted and 77 other negotiated 21(a,c,d,e) contracts make up the remainder). Firms = `firma_v3`, buyers = `kurum_il_split`; row counts of firms/buyers do not sum to the total because firms and buyers span groups. CSV: `B5_descriptives.csv` (also has % of value under 21(b)).\n")
P("| group | contracts | firms | buyers | value (bn 2025 TRY) | % 21(b) | % 21(f) | % open |")
P("|---|---:|---:|---:|---:|---:|---:|---:|")
for _, r in DES.iterrows():
    P(f"| {r.dimension}: {PRETTY.get(r.group, r.group)} | {r.contracts:,} | {r.firms:,} | {r.buyers:,} | {r.value_bn_2025:.2f} | {r.pct_21b:.1f} | {r.pct_21f:.1f} | {r.pct_open:.1f} |")
P("\nLaTeX rows (columns: group & contracts & firms & buyers & value & %21(b) & %21(f) & %open):\n")
P("```latex\n% --- by product market\n" + latex_rows(PM) + "\n\\midrule\n% --- by buyer sector\n" + latex_rows(SE)
  + "\n\\midrule\n" + latex_rows(TOT) + "\n```\n")

# ---- 6
P("## 6. Deflator robustness: PPI (Yİ-ÜFE) vs CPI\n")
P("Yİ-ÜFE (TÜİK domestic PPI, 2003=100) monthly series 2009–Aug 2026 was obtained from a mirror of the TÜİK table (hakedis.org/endeksler/yi-ufe-yurtici-uretici-fiyat-endeksi), stored with its source in `results/revision_b/ppi_turkey_yiufe.csv`. "
  "Annual average = mean of months (2026 = Jan–Aug, same convention as CPI). Spot-checks against published TÜİK figures: Dec 2021 = 1022.25, Dec 2022 = 2021.19; the 2022 annual-average change is "
  f"{100 * (PPI[2022] / PPI[2021] - 1):.1f}%. Factor to 2025 TRY: 2010 PPI {PPI[2025] / PPI[2010]:.2f}× vs CPI {cpi[2025] / cpi[2010]:.2f}×; 2020 PPI {PPI[2025] / PPI[2020]:.2f}× vs CPI {cpi[2025] / cpi[2020]:.2f}×.\n")
P("Count-based HHI is unchanged by construction. Value-based HHI (main sample, `firma_v3`, supplier side):\n")
P("| group | HHI value CPI | HHI value PPI | HHI value excl. largest CPI / PPI | winsorised CPI / PPI | class (value) CPI → PPI |")
P("|---|---:|---:|---:|---:|---|")
for _, r in W6[W6.dimension == "urun_pazari"].iterrows():
    cl = r.class_HHI_value_cpi if r.class_HHI_value_cpi == r.class_HHI_value_ppi else f"**{r.class_HHI_value_cpi} → {r.class_HHI_value_ppi}**"
    P(f"| {PRETTY.get(r.group, r.group)} | {r.HHI_value_cpi:,.0f} | {r.HHI_value_ppi:,.0f} | {r.HHI_value_nomax_cpi:,.0f} / {r.HHI_value_nomax_ppi:,.0f} | {r.HHI_value_wins_cpi:,.0f} / {r.HHI_value_wins_ppi:,.0f} | {cl} |")
P("")
dmax = W6[W6.dimension == "urun_pazari"][["d_HHI_value", "d_HHI_value_nomax"]].abs().max()
P(f"Largest absolute change across product markets: HHI value {dmax.d_HHI_value:.0f}, excl. largest {dmax.d_HHI_value_nomax:.0f} points. "
  f"Classification changes (2023 US Merger Guidelines bands; any of value / excl. largest / winsorised / min-LOO, markets and sectors): **{len(CH6)}**"
  + (": " + "; ".join(f"{r.group} {r.measure} {r.cpi:.0f}→{r.ppi:.0f} ({r.class_cpi} → {r.class_ppi})" for _, r in CH6.iterrows()) if len(CH6) else "")
  + f". Robust (minimum-across-variants) class changes: {n_robust_change}. CSV: `B6_hhi_cpi_vs_ppi.csv`, `B6_class_changes.csv`.\n")

(RES / "revision_b_results.md").write_text("\n".join(L), encoding="utf-8")
(RES / "run_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("done")
