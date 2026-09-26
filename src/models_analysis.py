# -*- coding: utf-8 -*-
"""TenderNet v3 — topic `models`.
A. contract-level incumbency logit (+ LPM with buyer FE)
B. dyad continuation (logit, PPML, NB2 with estimated alpha)
C. 21(b) share by dyad status with clustered inference
D. single bidding in the bid-count sample (design-weighted)
Writes CSVs + tables to results/models/ ; figures are made by models_figures.py
"""
import json
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

from models_common import (ROOT, RES, load, mle_twoway, twoway_vcov, oneway_vcov,
                           ols_scores, pstars, LAW7144)
from models_features import contract_history, dyad_table

warnings.filterwarnings("ignore")
np.random.seed(42)
RES.mkdir(parents=True, exist_ok=True)
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


def fe(df, col, prefix, drop_first=True):
    return pd.get_dummies(df[col].astype(str), prefix=prefix, drop_first=drop_first, dtype=float)


def expit(x):
    return 1 / (1 + np.exp(-x))


# ------------------------------------------------------------------ table helper
def coef_table(names, b, V, kind="logit"):
    se = np.sqrt(np.diag(V))
    z = b / se
    p = 2 * stats.norm.sf(np.abs(z))
    t = pd.DataFrame({"term": names, "coef": b, "se": se, "z": z, "p": p,
                      "lo": b - 1.96 * se, "hi": b + 1.96 * se})
    if kind in ("logit", "count"):
        t["exp"] = np.exp(t.coef)
        t["exp_lo"] = np.exp(t.lo)
        t["exp_hi"] = np.exp(t.hi)
    return t


def md_table(t, keep, label_map, exp_name=None):
    rows = []
    hdr = "| term | coef | SE | " + (f"{exp_name} [95% CI] | " if exp_name else "95% CI | ") + "p |"
    rows.append(hdr)
    rows.append("|---|---:|---:|---:|---:|")
    for _, r in t[t.term.isin(keep)].set_index("term").loc[keep].reset_index().iterrows():
        ci = (f"{r.exp:.3f} [{r.exp_lo:.3f}, {r.exp_hi:.3f}]" if exp_name
              else f"[{r.lo:.4f}, {r.hi:.4f}]")
        rows.append(f"| {label_map.get(r.term, r.term)} | {r.coef:.4f}{pstars(r.p)} | {r.se:.4f} | {ci} | "
                    f"{'<0.001' if r.p < 0.001 else f'{r.p:.3f}'} |")
    return "\n".join(rows)


# ------------------------------------------------------------------ AME (delta method)
def ame_logit(beta, V, X, cf, eps=1e-6):
    """cf(X) -> (X1, X0) counterfactual matrices or ('deriv', j). Returns AME, SE."""
    def f(b):
        r = cf(X)
        if isinstance(r[0], str):
            j = r[1]
            p = expit(X @ b)
            return np.mean(p * (1 - p) * b[j])
        X1, X0 = r
        return np.mean(expit(X1 @ b) - expit(X0 @ b))
    est = f(beta)
    g = np.array([(f(beta + eps * e) - f(beta - eps * e)) / (2 * eps) for e in np.eye(len(beta))])
    return est, float(np.sqrt(g @ V @ g))


def ame_diff(beta, V, fa, fb, eps=1e-6):
    fd = lambda b: fa(b) - fb(b)
    est = fd(beta)
    g = np.array([(fd(beta + eps * e) - fd(beta - eps * e)) / (2 * eps) for e in np.eye(len(beta))])
    return est, float(np.sqrt(g @ V @ g))


# ================================================================== load
d = load("main")
d = contract_history(d)
n_all = len(d)
log(f"main sample contracts: {n_all}; buyers {d.buyer.nunique()}; firms {d.firm.nunique()}; markets {d.market.nunique()}")
d.to_csv(RES / "contracts_with_history.csv", index=False, encoding="utf-8-sig",
         columns=["IKN", "date", "year", "firm_id", "buyer", "market", "usul_v3", "proc", "real_value",
                  "bm_prior_contracts", "bm_prior_suppliers", "bm_years_since_first", "incumbent_win",
                  "dyad_repeat", "post7144"])

LABELS = {
    "p_21b": "21(b) negotiated (vs open)", "p_oth_neg": "Other negotiated 21(a,c,d,e,f) (vs open)",
    "p_21f": "21(f) negotiated (vs open)", "p_oth_neg3": "Other negotiated 21(a,c,d,e)",
    "log_real_value": "log real value (2025 TRY)", "log_prior_suppliers": "log # distinct prior suppliers of buyer in market",
    "log_prior_contracts": "log # prior contracts of buyer in market", "years_since_first": "years since buyer's first contract in market",
    "post7144": "post-Law 7144 (date >= 2018-05-25)", "p21b_x_post": "21(b) x post-7144", "year_trend": "year (linear, centred 2018)",
    "p21f_x_post": "21(f) x post-7144",
    "const": "constant",
    "log_opp": "log # later buyer-market contracts (opportunities)",
    "log_firm_prior_contracts": "firm size: log(1+ prior contracts, other buyers)",
    "log_firm_prior_markets": "firm generalism: log(1+ prior distinct markets)",
    "log_firm_prior_buyers": "firm buyer breadth: log(1+ prior distinct buyers, other buyers)",
    "log_buyer_prior_contracts": "buyer experience: log(1+ buyer's prior contracts, all markets)",
    "lnalpha": "ln alpha (NB2)",
}

# ================================================================== A. incumbency
A = d[d.buyer_has_history == 1].copy()
log(f"\nA: contracts that are not buyer's first in market: {len(A)} "
    f"(excluded {n_all - len(A)} first-in-market contracts incl. same-date ties)")
A["log_prior_suppliers"] = np.log(A.bm_prior_suppliers)
A["log_prior_contracts"] = np.log(A.bm_prior_contracts)
A["years_since_first"] = A.bm_years_since_first
A["p_21b"] = (A.proc == "21b").astype(float)
A["p_oth_neg"] = (A.proc == "oth_neg").astype(float)
A["p21b_x_post"] = A.p_21b * A.post7144
A["yearfe"] = A.year.clip(lower=2011)  # 2010 (Oct-Dec) has very few history rows -> pooled with 2011
log("A year counts:", A.year.value_counts().sort_index().to_dict())
log(f"A incumbent-win rate: {A.incumbent_win.mean():.4f}")

CORE_A = ["p_21b", "p_oth_neg", "log_real_value", "log_prior_suppliers", "log_prior_contracts",
          "years_since_first", "post7144", "p21b_x_post"]


def build_A(df, core, year_fe=True, extra_fe=("market", "sektor_v3")):
    parts = [df[core].astype(float)]
    if year_fe:
        parts.append(fe(df, "yearfe", "yr"))
    for c in extra_fe:
        parts.append(fe(df, c, "fe_" + c[:3]))
    X = pd.concat(parts, axis=1)
    X = sm.add_constant(X, has_constant="add")
    X = X.loc[:, X.std() > 0].copy() if False else X
    return X


def fit_logit_2w(X, y, g1, g2, name):
    res = sm.Logit(y, X).fit(disp=0, maxiter=200, method="newton")
    V, G, nneg = mle_twoway(res, g1, g2)
    log(f"  [{name}] N={len(y)}, clusters={G}, clipped eig={nneg}, converged={res.mle_retvals['converged']}, "
        f"McFadden R2={res.prsquared:.4f}")
    return res, V, G


def run_A(df, core, name, year_fe=True, g2col="firm"):
    X = build_A(df, core, year_fe)
    y = df.incumbent_win.values
    res, V, G = fit_logit_2w(X.values, y, df.buyer.values, df[g2col].values, name)
    t = coef_table(list(X.columns), res.params, V, "logit")
    return res, V, G, X, t


resA, VA, GA, XA, tA = run_A(A, CORE_A, "A1 logit two-way (buyer, winner)")
tA.to_csv(RES / "A1_logit_incumbency.csv", index=False)
# one-way buyer clustered comparison
S = resA.model.score_obs(resA.params); Hinv = np.linalg.inv(-resA.model.hessian(resA.params))
Vb, _ = oneway_vcov(S, Hinv, A.buyer.values)
tAb = coef_table(list(XA.columns), resA.params, Vb, "logit")

# VIF (core covariates, with FE dummies as controls would inflate; report core-only)
Xc = sm.add_constant(A[CORE_A].astype(float))
vifA = pd.DataFrame({"term": CORE_A, "VIF": [variance_inflation_factor(Xc.values, i + 1) for i in range(len(CORE_A))]})
log("A VIF (core only):", vifA.round(2).to_dict("records"))
log("A corr(log prior suppliers, log prior contracts) =", round(A[["log_prior_suppliers", "log_prior_contracts"]].corr().iloc[0, 1], 3))

# AMEs for A1
Xv = XA.values.astype(float)
cols = list(XA.columns)
j = {c: cols.index(c) for c in cols}


def setcols(X, **kw):
    X = X.copy()
    for c, v in kw.items():
        X[:, j[c]] = v if not callable(v) else v(X)
    return X


def cf_21b(X):
    X1 = setcols(X, p_21b=1.0, p_oth_neg=0.0); X1[:, j["p21b_x_post"]] = X1[:, j["post7144"]]
    X0 = setcols(X, p_21b=0.0, p_oth_neg=0.0); X0[:, j["p21b_x_post"]] = 0.0
    return X1, X0


def cf_oth(X):
    X1 = setcols(X, p_21b=0.0, p_oth_neg=1.0, p21b_x_post=0.0)
    X0 = setcols(X, p_21b=0.0, p_oth_neg=0.0, p21b_x_post=0.0)
    return X1, X0


def cf_post(X):
    X1 = setcols(X, post7144=1.0); X1[:, j["p21b_x_post"]] = X1[:, j["p_21b"]]
    X0 = setcols(X, post7144=0.0, p21b_x_post=0.0)
    return X1, X0


def ames_A(res, V, X, df, tag):
    rows = []
    b = res.params
    specs = [("p_21b", cf_21b), ("p_oth_neg", cf_oth), ("post7144", cf_post)]
    for name, cf in specs:
        e, s = ame_logit(b, V, X, cf)
        rows.append((tag, name, "all", e, s))
    for c in ["log_real_value", "log_prior_suppliers", "log_prior_contracts", "years_since_first"]:
        e, s = ame_logit(b, V, X, lambda Z, c=c: ("deriv", j[c]))
        rows.append((tag, c, "all", e, s))
    pre = df.post7144.values == 0
    Xpre, Xpost = X[pre], X[~pre]

    def f21(Z):
        return lambda bb: np.mean(expit(cf_21b(Z)[0] @ bb) - expit(cf_21b(Z)[1] @ bb))
    for lab, Z in [("pre-7144", Xpre), ("post-7144", Xpost)]:
        e, s = ame_logit(b, V, Z, cf_21b)
        rows.append((tag, "p_21b", lab, e, s))
    e, s = ame_diff(b, V, f21(Xpost), f21(Xpre))
    rows.append((tag, "p_21b", "post minus pre", e, s))
    out = pd.DataFrame(rows, columns=["model", "term", "subset", "ame", "se"])
    out["lo"] = out.ame - 1.96 * out.se
    out["hi"] = out.ame + 1.96 * out.se
    out["p"] = 2 * stats.norm.sf(np.abs(out.ame / out.se))
    return out


ameA = ames_A(resA, VA, Xv, A, "A1")
log(ameA.round(4).to_string())

# predicted incumbent-win probabilities by procedure x period (for text)
predA = []
for lab, mask in [("pre", A.post7144.values == 0), ("post", A.post7144.values == 1)]:
    Z = Xv[mask]
    for pn, cf in [("open", lambda Z: setcols(Z, p_21b=0.0, p_oth_neg=0.0, p21b_x_post=0.0)),
                   ("21b", lambda Z: cf_21b(Z)[0]),
                   ("oth_neg", lambda Z: setcols(Z, p_21b=0.0, p_oth_neg=1.0, p21b_x_post=0.0))]:
        predA.append((lab, pn, float(np.mean(expit(cf(Z) @ resA.params)))))
predA = pd.DataFrame(predA, columns=["period", "procedure", "mean_pred_incumbent_win"])
raw_rates = A.groupby(["post7144", "proc"]).incumbent_win.agg(["mean", "size"]).reset_index()
log(predA.to_string()); log(raw_rates.to_string())

# ---- robustness variants of A
variants = {}
# A2: linear year trend instead of year FE (post main effect identified across years)
A["year_trend"] = (A.date - pd.Timestamp("2018-01-01")).dt.days / 365.25
r = run_A(A, CORE_A + ["year_trend"], "A2 linear trend, no year FE", year_fe=False)
variants["A2_trend_noYearFE"] = r
# A3: 21(f) separated
A["p_21f"] = (A.usul_v3 == "negotiated_21f").astype(float)
A["p_oth_neg3"] = ((A.proc == "oth_neg") & (A.usul_v3 != "negotiated_21f")).astype(float)
A["p21f_x_post"] = A.p_21f * A.post7144
core3 = ["p_21b", "p_21f", "p_oth_neg3", "log_real_value", "log_prior_suppliers", "log_prior_contracts",
         "years_since_first", "post7144", "p21b_x_post", "p21f_x_post"]
variants["A3_21f_separate"] = run_A(A, core3, "A3 21f separate")
# A4: without the prior-supplier / prior-contract counts (to check sensitivity to mechanical history terms)
variants["A4_no_history_counts"] = run_A(A, ["p_21b", "p_oth_neg", "log_real_value", "years_since_first",
                                              "post7144", "p21b_x_post"], "A4 no history counts")


def rerun_on(sample, firm_col="firma_v3", buyer_col="kurum_il_split", name=""):
    dd = contract_history(load(sample, firm_col, buyer_col))
    AA = dd[dd.buyer_has_history == 1].copy()
    AA["log_prior_suppliers"] = np.log(AA.bm_prior_suppliers)
    AA["log_prior_contracts"] = np.log(AA.bm_prior_contracts)
    AA["years_since_first"] = AA.bm_years_since_first
    AA["p_21b"] = (AA.proc == "21b").astype(float)
    AA["p_oth_neg"] = (AA.proc == "oth_neg").astype(float)
    AA["p21b_x_post"] = AA.p_21b * AA.post7144
    AA["yearfe"] = AA.year.clip(lower=2011)
    return run_A(AA, CORE_A, name)


AH = A[A.sektor_v3_en != "Health"].copy()
variants["R_excl_health_buyers"] = run_A(AH, CORE_A, "R excl. health-sector buyers")
variants["R_health_buyers_only"] = run_A(A[A.sektor_v3_en == "Health"].copy(), CORE_A, "R health-sector buyers only")
# placebo / alternative break: KHK 694 (2017-08-25) instead of Law 7144
AK = A.copy(); AK["post7144"] = (AK.date >= pd.Timestamp("2017-08-25")).astype(int); AK["p21b_x_post"] = AK.p_21b * AK.post7144
variants["R_break_KHK694_2017-08-25"] = run_A(AK, CORE_A, "R break at KHK 694 instead of 7144")
for yb in ["2016-05-25", "2020-05-25"]:
    AK = A.copy(); AK["post7144"] = (AK.date >= pd.Timestamp(yb)).astype(int); AK["p21b_x_post"] = AK.p_21b * AK.post7144
    variants[f"R_placebo_break_{yb}"] = run_A(AK, CORE_A, f"R placebo break {yb}")
AC = A[~A.year.isin([2020])].copy()
variants["R_excl_2020"] = run_A(AC, CORE_A, "R excl. 2020 (COVID emergency year)")
variants["R_it_only"] = rerun_on("it_only", name="R it_only (no call centre)")
variants["R_broad"] = rerun_on("broad", name="R main+gray")
variants["R_buyer_kurum"] = rerun_on("main", buyer_col="kurum", name="R buyer=recorded kurum")
variants["R_firm_original"] = rerun_on("main", firm_col="firma", name="R firm=original firma")

rob_rows = []
for k, (res, V, G, X, t) in variants.items():
    for term in ["p_21b", "p_oth_neg", "p_21f", "post7144", "p21b_x_post", "log_prior_suppliers",
                 "log_prior_contracts", "log_real_value", "years_since_first", "year_trend"]:
        if term in t.term.values:
            r = t[t.term == term].iloc[0]
            rob_rows.append((k, term, r.coef, r.se, r.exp, r.p, len(X), G[0], G[1], res.prsquared,
                             res.model.endog.mean(), res.llf))
for term in ["p_21b", "p_oth_neg", "post7144", "p21b_x_post", "log_prior_suppliers", "log_prior_contracts",
             "log_real_value", "years_since_first"]:
    r = tA[tA.term == term].iloc[0]
    rob_rows.insert(0, ("A1_main", term, r.coef, r.se, r.exp, r.p, len(XA), GA[0], GA[1], resA.prsquared,
                        A.incumbent_win.mean(), resA.llf))
robA = pd.DataFrame(rob_rows, columns=["model", "term", "coef", "se", "OR", "p", "N", "G_buyer", "G_firm",
                                       "pseudoR2", "mean_y", "loglik"])
robA.to_csv(RES / "A_robustness.csv", index=False)

# ---- A5: LPM with buyer FE (within-buyer), two-way clustered (buyer, winner)
def demean(M, g):
    M = pd.DataFrame(M)
    return (M - M.groupby(g).transform("mean")).values


XL = build_A(A, CORE_A, year_fe=True, extra_fe=("market",)).drop(columns="const")  # sector FE absorbed by buyer FE
gb = A.buyer.values
Xd = demean(XL.values, gb)
yd = demean(A.incumbent_win.values.reshape(-1, 1), gb).ravel()
keep = np.abs(Xd).sum(0) > 1e-10
Xd = Xd[:, keep]
lcols = list(XL.columns[keep])
bL = np.linalg.lstsq(Xd, yd, rcond=None)[0]
SL, HL = ols_scores(Xd, yd, bL)
n_buy = A.buyer.nunique()
VL, GL, nnegL = twoway_vcov(SL, HL, gb, A.firm.values, k=Xd.shape[1] + 0)  # FE nested in buyer cluster
tL = coef_table(lcols, bL, VL, "lpm")
single = A.groupby("buyer").buyer.transform("size") == 1
resid = yd - Xd @ bL
r2w = 1 - (resid ** 2).sum() / (yd ** 2).sum()
log(f"  [A5 LPM buyer FE] N={len(yd)} (singleton buyers contribute nothing: {int(single.sum())}), "
    f"buyers={n_buy}, clusters={GL}, within-R2={r2w:.4f}, clipped eig={nnegL}")
tL.to_csv(RES / "A5_lpm_buyerFE.csv", index=False)
# LPM without buyer FE for comparability
XL2 = build_A(A, CORE_A, year_fe=True)
bL2 = np.linalg.lstsq(XL2.values, A.incumbent_win.values, rcond=None)[0]
SL2, HL2 = ols_scores(XL2.values, A.incumbent_win.values.astype(float), bL2)
VL2, GL2, _ = twoway_vcov(SL2, HL2, gb, A.firm.values)
tL2 = coef_table(list(XL2.columns), bL2, VL2, "lpm")
tL2.to_csv(RES / "A5b_lpm_noBuyerFE.csv", index=False)

# ================================================================== B. dyad continuation
D = dyad_table(d)
nD = len(D)
D = D[D.market != "not_IT"]
log(f"\nB: dyads {nD}; with zero later buyer-market opportunities: {(D.opportunities == 0).sum()}")
D["no_opp"] = (D.opportunities == 0).astype(int)
Dm = D[D.opportunities > 0].copy()
log(f"B estimation dyads (opportunities>0): {len(Dm)}; later_any mean {Dm.later_any.mean():.4f}; "
    f"later_n mean {Dm.later_n.mean():.3f}, var {Dm.later_n.var():.3f}, max {Dm.later_n.max()}")
Dm["p_21b"] = (Dm.proc == "21b").astype(float)
Dm["p_oth_neg"] = (Dm.proc == "oth_neg").astype(float)
Dm["log_opp"] = np.log(Dm.opportunities)
Dm["log_firm_prior_contracts"] = np.log1p(Dm.firm_prior_contracts_exbuyer)
Dm["log_firm_prior_markets"] = np.log1p(Dm.firm_prior_markets)
Dm["log_firm_prior_buyers"] = np.log1p(Dm.firm_prior_buyers_exbuyer)
Dm["log_buyer_prior_contracts"] = np.log1p(Dm.buyer_prior_contracts)
Dm["yearfe"] = Dm.year.clip(upper=2024)  # 2025-26 dyads have few later opportunities -> pooled with 2024
log("B year counts:", Dm.year.value_counts().sort_index().to_dict())
CORE_B = ["p_21b", "p_oth_neg", "log_real_value", "log_firm_prior_contracts", "log_firm_prior_markets",
          "log_firm_prior_buyers", "log_buyer_prior_contracts", "log_opp"]
GEN_B = ["p_21b", "p_oth_neg", "log_real_value", "log_firm_prior_markets", "log_buyer_prior_contracts", "log_opp"]
SIZE_B = ["p_21b", "p_oth_neg", "log_real_value", "log_firm_prior_contracts", "log_buyer_prior_contracts", "log_opp"]
SG_B = ["p_21b", "p_oth_neg", "log_real_value", "log_firm_prior_contracts", "log_firm_prior_markets",
        "log_buyer_prior_contracts", "log_opp"]


def build_B(df, core):
    X = pd.concat([df[core].astype(float), fe(df, "yearfe", "yr"), fe(df, "market", "fe_mkt")], axis=1)
    return sm.add_constant(X, has_constant="add")


Xc = sm.add_constant(Dm[CORE_B].astype(float))
vifB = pd.DataFrame({"term": CORE_B, "VIF": [variance_inflation_factor(Xc.values, i + 1) for i in range(len(CORE_B))]})
corrB = Dm[["log_firm_prior_contracts", "log_firm_prior_markets", "log_firm_prior_buyers",
            "log_buyer_prior_contracts", "log_opp"]].corr()
log("B VIF:", vifB.round(2).to_dict("records"))
log("B corr:\n" + corrB.round(3).to_string())
g1B, g2B = Dm.firm.values, Dm.buyer.values
Bres = {}
for spec, core in [("full", CORE_B), ("size_generalism", SG_B), ("generalism_only", GEN_B), ("size_only", SIZE_B)]:
    X = build_B(Dm, core)
    # logit
    res, V, G = fit_logit_2w(X.values, Dm.later_any.values, g1B, g2B, f"B logit {spec}")
    Bres[("logit", spec)] = (res, V, G, X, coef_table(list(X.columns), res.params, V, "logit"))
    # Poisson PPML
    pm = sm.Poisson(Dm.later_n.values, X.values).fit(disp=0, maxiter=300, method="newton")
    Vp, Gp, nn = mle_twoway(pm, g1B, g2B)
    log(f"  [B PPML {spec}] N={len(X)}, clusters={Gp}, pseudoR2={pm.prsquared:.4f}, conv={pm.mle_retvals['converged']}")
    Bres[("ppml", spec)] = (pm, Vp, Gp, X, coef_table(list(X.columns), pm.params, Vp, "count"))
    # NB2 estimated alpha
    nb = sm.NegativeBinomial(Dm.later_n.values, X.values, loglike_method="nb2").fit(
        start_params=np.append(pm.params, 0.5), disp=0, maxiter=500, method="bfgs")
    nb = sm.NegativeBinomial(Dm.later_n.values, X.values, loglike_method="nb2").fit(
        start_params=nb.params, disp=0, maxiter=200, method="newton")
    Vn, Gn, nn = mle_twoway(nb, g1B, g2B)
    names = list(X.columns) + ["alpha"]
    tn = coef_table(names, nb.params, Vn, "count")
    log(f"  [B NB2 {spec}] N={len(X)}, alpha={nb.params[-1]:.4f} (SE {np.sqrt(Vn[-1, -1]):.4f}), "
        f"pseudoR2={nb.prsquared:.4f}, conv={nb.mle_retvals['converged']}, LL={nb.llf:.2f} vs Poisson LL={pm.llf:.2f}")
    Bres[("nb2", spec)] = (nb, Vn, Gn, X, tn)

# overdispersion tests (full spec)
pm = Bres[("ppml", "full")][0]
nb = Bres[("nb2", "full")][0]
mu = pm.predict()
yB = Dm.later_n.values
aux = ((yB - mu) ** 2 - yB) / mu
ct = sm.OLS(aux, mu).fit()
LR = 2 * (nb.llf - pm.llf)
p_LR = 0.5 * stats.chi2.sf(LR, 1)
pearson_disp = np.sum((yB - mu) ** 2 / mu) / (len(yB) - len(pm.params))
log(f"Overdispersion: Cameron-Trivedi alpha_hat={ct.params[0]:.4f}, t={ct.tvalues[0]:.2f}, p={ct.pvalues[0]:.2e}; "
    f"LR(alpha=0)={LR:.2f}, p(boundary)={p_LR:.2e}; Pearson dispersion={pearson_disp:.3f}")
overdisp = dict(ct_alpha=ct.params[0], ct_t=ct.tvalues[0], ct_p=ct.pvalues[0], LR=LR, LR_p=p_LR,
                pearson_dispersion=pearson_disp, nb2_alpha=nb.params[-1],
                nb2_alpha_se=float(np.sqrt(Bres[("nb2", "full")][1][-1, -1])))

# offset restriction test: coefficient on log_opp == 1
offs = []
for mod in ["ppml", "nb2"]:
    res, V, G, X, t = Bres[(mod, "full")]
    i = list(X.columns).index("log_opp")
    b, se = res.params[i], np.sqrt(V[i, i])
    zz = (b - 1) / se
    offs.append((mod, b, se, zz, 2 * stats.norm.sf(abs(zz))))
    log(f"Offset test {mod}: b(log_opp)={b:.4f} SE={se:.4f}; H0 b=1: z={zz:.2f}, p={2*stats.norm.sf(abs(zz)):.2e}")
offs = pd.DataFrame(offs, columns=["model", "b_log_opp", "se", "z_vs_1", "p"])

# offset model (for comparison) PPML with offset log(opp)
Xo = build_B(Dm, [c for c in CORE_B if c != "log_opp"])
po = sm.GLM(Dm.later_n.values, Xo.values, family=sm.families.Poisson(), offset=Dm.log_opp.values).fit()
Vo, Go, _ = mle_twoway(po, g1B, g2B) if hasattr(po.model, "score_obs") else (None, None, None)
tpo = coef_table(list(Xo.columns), po.params, Vo, "count")

# AMEs for B logit (full & generalism-only)
ameB = []
for spec in ["full", "size_generalism", "generalism_only", "size_only"]:
    res, V, G, X, t = Bres[("logit", spec)]
    cl = list(X.columns); Xv_ = X.values.astype(float)
    for c in [c for c in cl if c in LABELS and c != "const"]:
        if c.startswith("p_"):
            def cf(Z, c=c):
                Z1 = Z.copy(); Z0 = Z.copy()
                for cc in ("p_21b", "p_oth_neg"):
                    Z1[:, cl.index(cc)] = 0.0; Z0[:, cl.index(cc)] = 0.0
                Z1[:, cl.index(c)] = 1.0
                return Z1, Z0
        else:
            cf = lambda Z, c=c: ("deriv", cl.index(c))
        e, s = ame_logit(res.params, V, Xv_, cf)
        ameB.append((f"B_logit_{spec}", c, "all", e, s))
ameB = pd.DataFrame(ameB, columns=["model", "term", "subset", "ame", "se"])
ameB["lo"] = ameB.ame - 1.96 * ameB.se; ameB["hi"] = ameB.ame + 1.96 * ameB.se
ameB["p"] = 2 * stats.norm.sf(np.abs(ameB.ame / ameB.se))
log(ameB.round(4).to_string())
pd.concat([ameA, ameB]).to_csv(RES / "AME_A_B.csv", index=False)
for (mod, spec), (res, V, G, X, t) in Bres.items():
    t.to_csv(RES / f"B_{mod}_{spec}.csv", index=False)
D.drop(columns=[c for c in D.columns if c not in
                ["firm_id", "buyer", "market", "date", "year", "proc", "real_value", "later_n", "later_any",
                 "opportunities", "firm_prior_contracts_exbuyer", "firm_prior_markets",
                 "firm_prior_buyers_exbuyer", "buyer_prior_contracts"]]).to_csv(
    RES / "dyads_t0.csv", index=False, encoding="utf-8-sig")

# ================================================================== C. 21(b) share by dyad status
log("\nC: 21(b) share by dyad status")
d["dyad_status"] = np.where(d.dyad_repeat == 1, "repeat", "first")
largest = d.real_value.idxmax()
log(f"largest contract: IKN {d.loc[largest, 'IKN']}, usul {d.loc[largest, 'usul_v3']}, "
    f"status {d.loc[largest, 'dyad_status']}, real value {d.loc[largest, 'real_value']/1e9:.3f} bn 2025 TRY")
d["dyad_key"] = d.firm + "||" + d.buyer + "||" + d.market
crows = []
for scope, sub in [("all contracts", d), ("buyer has prior history in market (A sample)", d[d.buyer_has_history == 1]),
                   ("all, excl. largest contract", d.drop(index=largest))]:
    for st, g in sub.groupby("dyad_status"):
        crows.append((scope, st, len(g), int(g.is21b.sum()), g.is21b.mean(),
                      g.real_value.sum() / 1e9, g.real_value[g.is21b == 1].sum() / 1e9,
                      g.real_value[g.is21b == 1].sum() / g.real_value.sum()))
Ctab = pd.DataFrame(crows, columns=["scope", "status", "n", "n_21b", "share_21b_count", "value_bn_2025TRY",
                                    "value_21b_bn", "share_21b_value"])
log(Ctab.round(4).to_string())
Ctab.to_csv(RES / "C_21b_share_by_status.csv", index=False)

cinf = []
chi = stats.chi2_contingency(pd.crosstab(d.dyad_status, d.is21b))
cinf.append(("naive chi2 (count), all", chi[0], np.nan, chi[1], len(d), np.nan))
for scope, sub in [("all", d), ("A sample", d[d.buyer_has_history == 1]), ("all excl. largest", d.drop(index=largest))]:
    X = sm.add_constant(sub.dyad_repeat.astype(float).values)
    yv = sub.is21b.values.astype(float)
    for wlab, w in [("count", None), ("value-weighted", sub.real_value.values)]:
        if w is None:
            b = np.linalg.lstsq(X, yv, rcond=None)[0]; S, Hinv = ols_scores(X, yv, b)
        else:
            sw = np.sqrt(w / w.mean()); Xw = X * sw[:, None]; yw = yv * sw
            b = np.linalg.lstsq(Xw, yw, rcond=None)[0]; S, Hinv = ols_scores(Xw, yw, b)
        for clab, g in [("buyer", sub.buyer.values), ("dyad", sub.dyad_key.values)]:
            V, G = oneway_vcov(S, Hinv, g)
            se = np.sqrt(V[1, 1])
            cinf.append((f"LPM diff repeat-first, {wlab}, {scope}, cluster={clab}", b[1], se,
                         2 * stats.norm.sf(abs(b[1] / se)), len(sub), G))
        V2, G2, _ = twoway_vcov(S, Hinv, sub.buyer.values, sub.firm.values)
        se = np.sqrt(V2[1, 1])
        cinf.append((f"LPM diff repeat-first, {wlab}, {scope}, two-way buyer+firm", b[1], se,
                     2 * stats.norm.sf(abs(b[1] / se)), len(sub), str(G2)))
# adjusted: with year + market + sector FE, buyer clustered
X = pd.concat([d[["dyad_repeat"]].astype(float), fe(d, "year", "yr"), fe(d, "market", "m"), fe(d, "sektor_v3", "s")], axis=1)
X = sm.add_constant(X)
b = np.linalg.lstsq(X.values, d.is21b.values.astype(float), rcond=None)[0]
S, Hinv = ols_scores(X.values, d.is21b.values.astype(float), b)
V, G = oneway_vcov(S, Hinv, d.buyer.values)
cinf.append(("LPM diff, count, all, + year/market/sector FE, cluster=buyer", b[1], np.sqrt(V[1, 1]),
             2 * stats.norm.sf(abs(b[1] / np.sqrt(V[1, 1]))), len(d), G))
# within-buyer
Xw = demean(np.column_stack([d.dyad_repeat.values.astype(float), fe(d, "year", "yr").values]), d.buyer.values)
yw = demean(d.is21b.values.reshape(-1, 1).astype(float), d.buyer.values).ravel()
kk = np.abs(Xw).sum(0) > 1e-10
Xw = Xw[:, kk]
b = np.linalg.lstsq(Xw, yw, rcond=None)[0]
S, Hinv = ols_scores(Xw, yw, b)
V, G = oneway_vcov(S, Hinv, d.buyer.values)
cinf.append(("LPM diff, count, all, buyer FE + year FE, cluster=buyer", b[0], np.sqrt(V[0, 0]),
             2 * stats.norm.sf(abs(b[0] / np.sqrt(V[0, 0]))), len(d), G))
Cinf = pd.DataFrame(cinf, columns=["test", "estimate", "se", "p", "N", "clusters"])
log(Cinf.to_string())
Cinf.to_csv(RES / "C_inference.csv", index=False)
# by period
Cper = d.groupby(["post7144", "dyad_status"]).agg(n=("is21b", "size"), share_21b=("is21b", "mean")).reset_index()
Cper.to_csv(RES / "C_21b_share_by_status_period.csv", index=False)
log(Cper.to_string())
Cyr = d.groupby(["year"]).agg(n=("is21b", "size"), share_21b=("is21b", "mean"),
                                inc=("dyad_repeat", "mean")).reset_index()
Cyr.to_csv(RES / "C_21b_share_by_year.csv", index=False)

# ================================================================== D. single bidding
log("\nD: single bidding")
tk = pd.read_csv(ROOT / "data" / "bid_counts_sample.csv", encoding="utf-8-sig")
log(f"bid_counts_sample rows: {len(tk)}")
log(f"bid-count sample: {len(tk)} tenders drawn 40/yr (seed 42) from all completed EKAP results in cp1; "
    f"with bid data: {tk.toplam_teklif.notna().sum()}")
S_ = tk.merge(d[["IKN", "year", "post7144", "proc", "proc3", "usul_v3", "incumbent_win", "buyer_has_history", "firm", "buyer",
                 "real_value"]], on="IKN", how="inner")
log(f"in v3 main sample: {len(S_)}; with bid counts: {S_.toplam_teklif.notna().sum()}")
cover = pd.DataFrame({
    "pop_main": d.groupby("year").size(),
    "drawn_in_main": S_.groupby("year").size(),
    "with_bids": S_[S_.toplam_teklif.notna()].groupby("year").size()}).fillna(0).astype(int)
cover["weight"] = np.where(cover.with_bids > 0, cover.pop_main / cover.with_bids.replace(0, np.nan), np.nan)
log(cover.to_string())
cover.to_csv(RES / "D_sample_coverage_by_year.csv")
Sb = S_[S_.toplam_teklif.notna()].copy()
Sb["w"] = Sb.year.map(cover.weight)
Sb["single"] = (Sb.toplam_teklif == 1).astype(int)
Sb["single_valid"] = (Sb.gecerli_teklif == 1).astype(int)
Sb["inc_status"] = np.where(Sb.buyer_has_history == 0, "buyer first in market (undefined)",
                            np.where(Sb.incumbent_win == 1, "incumbent winner", "non-incumbent winner"))
yrs_nodata = sorted(set(d.year.unique()) - set(Sb.year.unique()))
log(f"years in main sample with no bid data: {yrs_nodata} (population contracts in those years: "
    f"{int(d[d.year.isin(yrs_nodata)].shape[0])})")


def wprop(df, y, dom=None):
    """Design-weighted (year-stratified) domain proportion with linearization SE (with-replacement)."""
    dom = np.ones(len(df), bool) if dom is None else dom
    w = df.w.values * dom
    yy = df[y].values.astype(float)
    W = w.sum()
    p = (w * yy).sum() / W
    z = w * (yy - p) / W
    var = 0.0
    for h, idx in df.groupby("year").indices.items():
        zh = z[idx]; nh = len(zh)
        if nh > 1:
            var += nh / (nh - 1) * ((zh - zh.mean()) ** 2).sum()
    se = np.sqrt(var)
    n = int(dom.sum())
    # logit-transformed CI (stays in [0,1])
    if 0 < p < 1:
        lp = np.log(p / (1 - p)); sl = se / (p * (1 - p))
        lo, hi = 1 / (1 + np.exp(-(lp - 1.96 * sl))), 1 / (1 + np.exp(-(lp + 1.96 * sl)))
    else:
        lo, hi = np.nan, np.nan
    return p, se, lo, hi, n, int((dom * df[y].values).sum())


drows = []
for y in ["single", "single_valid"]:
    drows.append((y, "overall", "all", *wprop(Sb, y)))
    for pr in ["open", "21b", "21f", "oth_neg"]:
        dom = (Sb.proc3 == pr).values
        if dom.sum():
            drows.append((y, "procedure", pr, *wprop(Sb, y, dom)))
    for st in ["incumbent winner", "non-incumbent winner", "buyer first in market (undefined)"]:
        drows.append((y, "incumbency", st, *wprop(Sb, y, (Sb.inc_status == st).values)))
    for pr in ["open", "negotiated"]:
        for st in ["incumbent winner", "non-incumbent winner"]:
            dom = ((Sb.proc == "open") == (pr == "open")).values & (Sb.inc_status == st).values
            drows.append((y, "procedure x incumbency", f"{pr} | {st}", *wprop(Sb, y, dom)))
    for per, lab in [(0, "pre-7144"), (1, "post-7144")]:
        dom = (Sb.post7144.values == per)
        drows.append((y, "period (tender date vs 2018-05-25)", lab, *wprop(Sb, y, dom)))
Dtab = pd.DataFrame(drows, columns=["outcome", "breakdown", "group", "rate_w", "se", "lo95", "hi95", "n", "n_events"])


def wdiff(df, y, d1, d2):
    """Design-weighted difference of two domain proportions, stratified linearization SE."""
    yy = df[y].values.astype(float); w = df.w.values
    W1 = (w * d1).sum(); W2 = (w * d2).sum()
    p1 = (w * d1 * yy).sum() / W1; p2 = (w * d2 * yy).sum() / W2
    z = w * d1 * (yy - p1) / W1 - w * d2 * (yy - p2) / W2
    var = 0.0
    for h, idx in df.groupby("year").indices.items():
        zh = z[idx]; nh = len(zh)
        if nh > 1:
            var += nh / (nh - 1) * ((zh - zh.mean()) ** 2).sum()
    se = np.sqrt(var)
    return p1 - p2, se, p1 - p2 - 1.96 * se, p1 - p2 + 1.96 * se, 2 * stats.norm.sf(abs((p1 - p2) / se))


diffs = []
for y in ["single", "single_valid"]:
    inc = (Sb.inc_status == "incumbent winner").values; non = (Sb.inc_status == "non-incumbent winner").values
    diffs.append((y, "incumbent - non-incumbent", *wdiff(Sb, y, inc, non)))
    for pr in ["open", "negotiated"]:
        m_ = ((Sb.proc == "open") == (pr == "open")).values
        diffs.append((y, f"incumbent - non-incumbent | {pr}", *wdiff(Sb, y, inc & m_, non & m_)))
    diffs.append((y, "21b - open", *wdiff(Sb, y, (Sb.proc3 == "21b").values, (Sb.proc3 == "open").values)))
    diffs.append((y, "21f - open", *wdiff(Sb, y, (Sb.proc3 == "21f").values, (Sb.proc3 == "open").values)))
    diffs.append((y, "post - pre 7144", *wdiff(Sb, y, (Sb.post7144 == 1).values, (Sb.post7144 == 0).values)))
Ddiff = pd.DataFrame(diffs, columns=["outcome", "contrast", "diff", "se", "lo95", "hi95", "p"])
log(Ddiff.round(4).to_string())
Ddiff.to_csv(RES / "D_single_bid_differences.csv", index=False)
# adjusted: logit single ~ incumbent + negotiated + year trend, buyer-clustered, among defined incumbency
Si = Sb[Sb.inc_status != "buyer first in market (undefined)"]
Xi = sm.add_constant(np.column_stack([(Si.inc_status == "incumbent winner").astype(float), (Si.proc != "open").astype(float),
                                      (Si.year - 2018).astype(float)]))
ri = sm.Logit(Si.single.values, Xi).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(Si.buyer)[0]})
log(f"single ~ incumbent + negotiated + year (n={len(Si)}, buyer-clustered): OR_inc={np.exp(ri.params[1]):.3f} "
    f"[{np.exp(ri.conf_int()[1,0]):.3f}, {np.exp(ri.conf_int()[1,1]):.3f}], p={ri.pvalues[1]:.4f}")
Dadj = dict(n=len(Si), OR_inc=np.exp(ri.params[1]), lo=np.exp(ri.conf_int()[1, 0]), hi=np.exp(ri.conf_int()[1, 1]),
            p=ri.pvalues[1], OR_neg=np.exp(ri.params[2]), p_neg=ri.pvalues[2])
log(Dtab.round(4).to_string())
Dtab.to_csv(RES / "D_single_bid_rates.csv", index=False)

# trend test (logit on year) — unweighted and design-weighted, robust SE
trend = []
for y in ["single", "single_valid"]:
    X = sm.add_constant((Sb.year - 2018).astype(float).values)
    r = sm.Logit(Sb[y].values, X).fit(disp=0, cov_type="HC1")
    trend.append((y, "unweighted logit, HC1", r.params[1], r.bse[1], np.exp(r.params[1]), r.pvalues[1], len(Sb)))
    ww = Sb.w.values / Sb.w.mean()
    r = sm.GLM(Sb[y].values, X, family=sm.families.Binomial(), var_weights=ww).fit(cov_type="HC1")
    trend.append((y, "design-weighted logit, HC1", r.params[1], r.bse[1], np.exp(r.params[1]), r.pvalues[1], len(Sb)))
    # with procedure control
    X2 = sm.add_constant(np.column_stack([(Sb.year - 2018).astype(float).values,
                                          (Sb.proc != "open").astype(float).values]))
    r = sm.Logit(Sb[y].values, X2).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(Sb.buyer)[0]})
    trend.append((y, "unweighted logit + negotiated dummy, buyer-clustered", r.params[1], r.bse[1],
                  np.exp(r.params[1]), r.pvalues[1], len(Sb)))
trend = pd.DataFrame(trend, columns=["outcome", "model", "b_year", "se", "OR_per_year", "p", "N"])
log(trend.to_string())
trend.to_csv(RES / "D_trend_test.csv", index=False)

# downloaders vs bids
Sd = Sb[Sb.indiren_sayisi.notna()].copy()
Sd["gap_valid"] = Sd.indiren_sayisi - Sd.gecerli_teklif
Sd["gap_total"] = Sd.indiren_sayisi - Sd.toplam_teklif
Sd["dl_zero"] = (Sd.indiren_sayisi == 0).astype(int)
log("downloaders==0 by year:", Sd.groupby("year").dl_zero.sum().to_dict())
Sd_pos = Sd[Sd.indiren_sayisi > 0].copy()
Sd_pos["multi_dl_single_valid"] = ((Sd_pos.indiren_sayisi >= 2) & (Sd_pos.gecerli_teklif == 1)).astype(int)
Sd_pos["valid_per_dl"] = Sd_pos.gecerli_teklif / Sd_pos.indiren_sayisi


def wmean(df, y, dom=None):
    dom = np.ones(len(df), bool) if dom is None else dom
    sub = df[dom]
    w = sub.w.values; yy = sub[y].values.astype(float); W = w.sum(); m = (w * yy).sum() / W
    z = w * (yy - m) / W; var = 0
    for h, idx in sub.groupby("year").indices.items():
        zh = z[idx]; nh = len(zh)
        if nh > 1: var += nh / (nh - 1) * ((zh - zh.mean()) ** 2).sum()
    se = np.sqrt(var)
    return m, se, m - 1.96 * se, m + 1.96 * se, len(sub)


gaprows = []
for lab, dom in [("all (downloaders>0)", None), ("open", (Sd_pos.proc == "open").values),
                 ("negotiated", (Sd_pos.proc != "open").values)]:
    for y in ["indiren_sayisi", "gecerli_teklif", "gap_valid", "gap_total", "valid_per_dl", "multi_dl_single_valid"]:
        gaprows.append((lab, y, *wmean(Sd_pos, y, dom)))
gaps = pd.DataFrame(gaprows, columns=["subset", "variable", "mean_w", "se", "lo95", "hi95", "n"])
log(gaps.round(3).to_string())
gaps.to_csv(RES / "D_downloader_gap.csv", index=False)
log(f"downloader counts: rows with indiren recorded {len(Sd)}, of which indiren==0: {int(Sd.dl_zero.sum())}")
Sb.drop(columns=["firm", "buyer"]).to_csv(RES / "D_bid_sample_joined.csv", index=False, encoding="utf-8-sig")
# single-bid by year (weights irrelevant within year)
yr_single = Sb.groupby("year").agg(n=("single", "size"), single=("single", "mean"),
                                   single_valid=("single_valid", "mean"))
yr_single.to_csv(RES / "D_single_bid_by_year.csv")
log(yr_single.round(3).to_string())

# ================================================================== save objects for report/figures
import pickle
with open(RES / "_model_objects.pkl", "wb") as fh:
    pickle.dump(dict(tA=tA, tAb=tAb, GA=GA, NA=len(A), prA=resA.prsquared, llA=resA.llf, meanA=A.incumbent_win.mean(),
                     vifA=vifA, ameA=ameA, predA=predA, raw_rates=raw_rates, robA=robA,
                     tL=tL, GL=GL, NL=len(yd), r2w=r2w, tL2=tL2,
                     Bt={k: (v[4], v[2], len(v[3]), v[0].prsquared, v[0].llf) for k, v in Bres.items()},
                     tpo=tpo, vifB=vifB, corrB=corrB, overdisp=overdisp, offs=offs, ameB=ameB,
                     nB=len(Dm), nD=len(D), meanB=Dm.later_any.mean(), Ctab=Ctab, Cinf=Cinf, Cper=Cper,
                     cover=cover, Dtab=Dtab, trend=trend, gaps=gaps, Ddiff=Ddiff, Dadj=Dadj, yrs_nodata=yrs_nodata,
                     variants={k: (v[4], v[2], len(v[3]), v[0].prsquared) for k, v in variants.items()},
                     LABELS=LABELS), fh)
(RES / "models_run_log.txt").write_text("\n".join(LOG), encoding="utf-8")
print("done")
