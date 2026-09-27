# -*- coding: utf-8 -*-
"""TenderNet v3 - topic `revision_d` (referee round D): state dependence vs heterogeneity.

Builds on revision_c.py (leak-free conditional logit, 24-month pre-tender pools, future-supplier
placebo, pure-state-dependence simulation).  Nothing in revision_c.py (or any other file) is modified.

1. Pure-state-dependence (SD) simulation separately for renewals and new needs; formal comparison of the
   observed past/future OR ratio with the simulated distribution (Wald + buyer-cluster bootstrap).
2. Calibration & uncertainty: beta_inc grid; parametric draws beta ~ N(beta_hat, V_cluster); SD simulation
   with ALL history covariates recomputed from the simulated history.
3. Heterogeneity-only world: beta_inc = 0 plus a persistent normal buyer-firm random intercept, sigma
   calibrated to the observed share of chosen incumbents.  Three-world comparison.
4. Firm-level vs dyadic heterogeneity: firm's future / past wins in the market from OTHER buyers; lags.
5. Recency with prior-win-count control (ratio + CI).
6. Figure F-D1 (three worlds).  7. Figure F-L1b (incumbency by market vs N3 null).

Run: python src/revision_d.py   (env REVD_R = replications, default 100; REVD_BOOT default 200)
"""
from pathlib import Path
import bisect
import json
import os
import pickle
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import revision_c as RC               # noqa: E402  (installs the robust clogit into revision_a)
import lockin_analysis as L          # noqa: E402

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "revision_d"
OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "figures"
R = int(os.environ.get("REVD_R", 100))
BOOT = int(os.environ.get("REVD_BOOT", 200))
CALR = int(os.environ.get("REVD_CAL", 20))
RMIX = int(os.environ.get("REVD_RMIX", 50))
SEED = 42
LOG = {}
MAIN = RC.MAIN
OTH = MAIN[1:]
OI = L.OI
T0 = time.time()


def log(k, v):
    LOG[k] = v
    print(f"[{time.time() - T0:7.0f}s]", k, v if not isinstance(v, (dict, list)) else json.dumps(v, default=str)[:700],
          flush=True)
    json.dump(LOG, open(OUT / "revision_d_log.json", "w", encoding="utf-8"), indent=2, default=str, ensure_ascii=False)


# =====================================================================  estimation helpers
class Prep:
    """Sorted design for repeated clogit fits (singleton choice sets dropped)."""

    def __init__(self, C, cols):
        C = C[C.groupby("contract").chosen.transform("size") > 1]
        C = C.sort_values(["contract", "chosen"], ascending=[True, False]).reset_index(drop=True)
        self.g = pd.factorize(C.contract)[0]
        self.X = C[cols].values.astype(float)
        self.y = C.chosen.values.astype(float)
        self.cl = pd.factorize(C.groupby(self.g).buyer.first().values)[0]
        self.cols = cols
        self.n_con = int(self.g.max() + 1)

    def fit(self, w=None, V=True, beta0=None):
        b, Hh, S, ll = RC.clogit_fit_robust(self.X, self.g, self.y, w=w, beta0=beta0)
        if not V:
            return b, None
        Hinv = np.linalg.inv(Hh)
        nc = self.cl.max() + 1
        Sc = np.vstack([np.bincount(self.cl, weights=S[:, q], minlength=nc) for q in range(S.shape[1])]).T
        return b, Hinv @ (Sc.T @ Sc) @ Hinv * nc / (nc - 1)


def or_row(b, V, cols, name):
    se = np.sqrt(np.diag(V))
    return pd.DataFrame(dict(model=name, variable=cols, coef=b, se=se, OR=np.exp(b), OR_lo=np.exp(b - 1.96 * se),
                             OR_hi=np.exp(b + 1.96 * se), p=2 * stats.norm.sf(np.abs(b / se))))


def contrast(b, V, i, j):
    d = b[i] - b[j]
    s = np.sqrt(V[i, i] + V[j, j] - 2 * V[i, j])
    return dict(log_ratio=float(d), se=float(s), ratio=float(np.exp(d)), lo=float(np.exp(d - 1.96 * s)),
                hi=float(np.exp(d + 1.96 * s)), p=float(2 * stats.norm.sf(abs(d / s))))


PLAC = MAIN + ["future_supplier_only"]
LE = ["inc_last", "inc_earlier"] + OTH


def moments(C, name, V=True):
    """Moments used to compare worlds: incumbent OR (main), incumbent & future-only OR (placebo model),
    last & earlier OR, ratios."""
    out, tabs = {}, []
    for key, cols in [("main", MAIN), ("plac", PLAC), ("le", LE)]:
        b, Vv = Prep(C, cols).fit(V=V)
        out[key] = (b, Vv)
        if V:
            tabs.append(or_row(b, Vv, cols, f"{name} | {key}"))
    bm_, bp, bl = out["main"][0], out["plac"][0], out["le"][0]
    ch = C[C.chosen == 1]
    m = dict(OR_incumbent_main=np.exp(bm_[0]), OR_incumbent_plac=np.exp(bp[0]), OR_future_only=np.exp(bp[-1]),
             past_future_ratio=np.exp(bp[0] - bp[-1]), OR_inc_last=np.exp(bl[0]), OR_inc_earlier=np.exp(bl[1]),
             last_earlier_ratio=np.exp(bl[0] - bl[1]), share_chosen_incumbent=ch.incumbent.mean(),
             share_chosen_future_only=ch.future_supplier_only.mean(), share_chosen_last=ch.inc_last.mean())
    if V:
        m["pf"] = contrast(bp, out["plac"][1], 0, len(PLAC) - 1)
        m["le"] = contrast(bl, out["le"][1], 0, 1)
        se_p = np.sqrt(np.diag(out["plac"][1])); se_m = np.sqrt(np.diag(out["main"][1]))
        m["ci"] = dict(OR_incumbent_main=(np.exp(bm_[0] - 1.96 * se_m[0]), np.exp(bm_[0] + 1.96 * se_m[0])),
                       OR_incumbent_plac=(np.exp(bp[0] - 1.96 * se_p[0]), np.exp(bp[0] + 1.96 * se_p[0])),
                       OR_future_only=(np.exp(bp[-1] - 1.96 * se_p[-1]), np.exp(bp[-1] + 1.96 * se_p[-1])),
                       past_future_ratio=(m["pf"]["lo"], m["pf"]["hi"]),
                       last_earlier_ratio=(m["le"]["lo"], m["le"]["hi"]))
        m["n_contracts"] = Prep(C, MAIN).n_con
        m["beta_main"] = out["main"][0].tolist()
        m["V_main"] = out["main"][1]
        m["tables"] = pd.concat(tabs, ignore_index=True)
    return m


def boot_ratio(C, B, seed):
    """Buyer-cluster bootstrap of log(OR_inc / OR_future) in the placebo model."""
    pr = Prep(C, PLAC)
    b0, _ = pr.fit(V=False)
    rng = np.random.default_rng(seed)
    nc = pr.cl.max() + 1
    out = []
    for _ in range(B):
        w = np.bincount(rng.integers(0, nc, nc), minlength=nc).astype(float)[pr.cl]
        b, _ = pr.fit(w=w, V=False, beta0=b0)
        out.append(b[0] - b[-1])
    return np.array(out)


# =====================================================================  simulation engine
class Sim:
    """Sequential re-draw of the winners of the in-pool repeat-eligible contracts of `C` (choice data, full
    24-month pre-t pool) in chronological order.  All other contracts keep their observed winners.
    Worlds: state dependence (beta_inc != 0, sigma = 0) or heterogeneity (beta_inc = 0, sigma > 0: persistent
    N(0, sigma^2) buyer-firm intercept; pairs that won a fixed (not re-drawn) contract get the
    heuristic tilted draw N(sigma, 1)*sigma. This is an outcome-conditioned scenario,
    NOT the multinomial-logit posterior given winning. Fixed winners can occur later
    in the panel; see revision_e_initial_conditions.py for initialization sensitivity.
    recompute=True recomputes every history covariate (not only `incumbent`) from the simulated history;
    otherwise non-incumbent covariates stay at their observed values (the revision-C simplification).
    The choice sets (pools) are held at the observed pre-t pools in all worlds."""

    def __init__(self, P, C, el_idx=None):
        self.P = P
        self.el_idx = np.flatnonzero(P["elig"]) if el_idx is None else el_idx
        C = C.sort_values(["contract", "chosen"], ascending=[True, False]).reset_index(drop=True)
        self.C = C
        self.con, self.firms = C.contract.values, C.firm.values
        self.bu = C.buyer.values
        self.Xo = C[OTH].values.astype(float)
        con = self.con
        st = np.r_[0, np.flatnonzero(con[1:] != con[:-1]) + 1, len(con)]
        self.sl = {int(con[a]): (int(a), int(b)) for a, b in zip(st[:-1], st[1:])}
        day = P["day"]
        n = len(day)
        self.order = np.lexsort((np.arange(n), day))
        # buyer-firm pairs for heterogeneity
        nf = int(P["nf"])
        rowkey = self.bu.astype(np.int64) * nf + self.firms
        fixed = np.array([i for i in range(n) if i not in self.sl])
        fixkey = P["buyer"][fixed].astype(np.int64) * nf + P["firm"][fixed]
        allkeys = np.unique(np.r_[rowkey, fixkey])
        self.rowpair = np.searchsorted(allkeys, rowkey)
        self.npair = len(allkeys)
        self.tilt = np.isin(allkeys, fixkey)

    # ---------------------------------------------------------------- one replication
    def run(self, beta, rng, sigma=0.0, recompute=False, replay=False, lags=(365,)):
        P = self.P
        day, bm, fobs = P["day"], P["bm"], P["firm"]
        buyer, mkt, sec, ilc = P["buyer"], P["mkt"], P["sec"], P["ilc"]
        firms, sl = self.firms, self.sl
        b_inc, b_oth = beta[0], np.asarray(beta[1:])
        if sigma > 0:
            u = rng.standard_normal(self.npair)
            u[self.tilt] += sigma
            eff = sigma * u[self.rowpair]
        else:
            eff = None
        Xr = self.Xo.copy() if recompute else self.Xo
        simf = fobs.copy()
        inc_state = {}                     # bm -> set of firms with a win before the current day
        hist = {}                          # bm -> list of (day, firm)
        if recompute:
            fcount, fsec, fmd, fkm_ = {}, {}, {}, {}
            hc, hf, fpos = {}, {}, {}
        pending, cur = [], None

        def flush():
            for q in pending:
                f, k = simf[q], bm[q]
                inc_state.setdefault(k, set()).add(f)
                hist.setdefault(k, []).append((day[q], f))
                if recompute:
                    fcount[f] = fcount.get(f, 0) + 1
                    fsec[(f, sec[q])] = fsec.get((f, sec[q]), 0) + 1
                    fmd.setdefault((f, mkt[q]), []).append(day[q])
                    fkm_.setdefault((f, buyer[q]), set()).add(mkt[q])
                    c_ = hc.setdefault(f, {}); fi = hf.setdefault(f, {})
                    c_[ilc[q]] = c_.get(ilc[q], 0) + 1
                    if ilc[q] not in fi:
                        fi[ilc[q]] = fpos.get(f, 0)
                    fpos[f] = fpos.get(f, 0) + 1
            pending.clear()

        for i in self.order:
            if day[i] != cur:
                flush()
                cur = day[i]
            if i in sl:
                a, b = sl[i]
                prior = inc_state.get(bm[i], set())
                fa = firms[a:b]
                inc = np.fromiter((f in prior for f in fa), bool, b - a)
                if recompute:
                    t, k, m, s, il = day[i], buyer[i], mkt[i], sec[i], ilc[i]
                    for q, f in zip(range(a, b), fa):
                        oth = fkm_.get((f, k), ())
                        Xr[q, 0] = int(any(mm != m for mm in oth))
                        c_ = hc.get(f)
                        if c_:
                            fi = hf[f]
                            h = min(c_, key=lambda z: (-c_[z], fi[z]))
                            Xr[q, 1] = int(h == il)
                        else:
                            Xr[q, 1] = 0
                        dd = fmd.get((f, m))
                        Xr[q, 2] = np.log1p(len(dd) - bisect.bisect_left(dd, t - 365)) if dd else 0.0
                        Xr[q, 3] = np.log1p(fcount.get(f, 0))
                        Xr[q, 4] = np.log1p(fsec.get((f, s), 0))
                if replay:
                    pick = 0                                  # chosen row is first in its slice
                else:
                    uu = Xr[a:b] @ b_oth + b_inc * inc
                    if eff is not None:
                        uu = uu + eff[a:b]
                    p = np.exp(uu - uu.max()); p /= p.sum()
                    pick = rng.choice(b - a, p=p)
                simf[i] = firms[a + pick]
            pending.append(i)
        flush()
        return self._assemble(simf, hist, Xr, lags)

    def _assemble(self, simf, hist, Xr, lags):
        P = self.P
        day, bm = P["day"], P["bm"]
        firms, n = self.firms, len(self.firms)
        inc_s = np.zeros(n); fut_s = np.zeros(n); last_s = np.zeros(n); npw = np.zeros(n)
        futL = {L_: np.zeros(n) for L_ in lags}; nearL = {L_: np.zeros(n) for L_ in lags}
        for c_, (a, b) in self.sl.items():
            h = hist[bm[c_]]; t = day[c_]
            cnt, lastd, ffirst = {}, None, {}
            for d_, f in h:
                if d_ < t:
                    cnt[f] = cnt.get(f, 0) + 1
                    lastd = d_ if lastd is None or d_ > lastd else lastd
                elif d_ > t:
                    ffirst[f] = min(ffirst.get(f, d_), d_)
            lset = {f for d_, f in h if d_ == lastd} if lastd is not None else set()
            for q in range(a, b):
                f = firms[q]
                c = cnt.get(f, 0)
                inc_s[q] = c > 0
                npw[q] = np.log1p(c)
                last_s[q] = f in lset
                if c == 0 and f in ffirst:
                    fut_s[q] = 1
                    for L_ in lags:
                        if ffirst[f] > t + L_:
                            futL[L_][q] = 1
                        else:
                            nearL[L_][q] = 1
        Cs = pd.DataFrame(Xr, columns=OTH)
        Cs["contract"] = self.con; Cs["buyer"] = self.bu
        Cs["chosen"] = (firms == simf[self.con]).astype(int)
        Cs["incumbent"] = inc_s
        Cs["future_supplier_only"] = fut_s
        Cs["inc_last"] = inc_s * last_s
        Cs["inc_earlier"] = inc_s * (1 - last_s)
        Cs["log_prior_wins_buyer_market"] = npw
        for L_ in lags:
            Cs[f"fut_gt{L_}"] = futL[L_]; Cs[f"fut_le{L_}"] = nearL[L_]
        # incumbency over ALL repeat-eligible contracts (fixed ones re-evaluated on the simulated history)
        el = self.el_idx
        inc_all = np.empty(len(el), bool)
        for z, i in enumerate(el):
            inc_all[z] = any(d_ < day[i] and f == simf[i] for d_, f in hist[bm[i]])
        return Cs, float(inc_all.mean())

    def replicate(self, beta, R_, seed, sigma=0.0, recompute=False, beta_draws=None, lagfit=False, tag=""):
        rng = np.random.default_rng(seed)
        rows = []
        for r in range(R_):
            b = beta_draws[r] if beta_draws is not None else beta
            Cs, inc_all = self.run(b, rng, sigma=sigma, recompute=recompute)
            m = moments(Cs, "sim", V=False)
            m = {k: float(v) for k, v in m.items()}
            m["incumbency_all_eligible"] = inc_all
            if lagfit:
                bb, _ = Prep(Cs, MAIN + ["fut_gt365", "fut_le365"]).fit(V=False)
                m["OR_future_gt365"] = float(np.exp(bb[-2]))
            m["sim"] = r
            rows.append(m)
            if r % 20 == 0:
                print(f"  [{time.time() - T0:7.0f}s] {tag} rep {r}: inc {m['OR_incumbent_plac']:.1f} fut "
                      f"{m['OR_future_only']:.1f} L/E {m['last_earlier_ratio']:.2f} share {m['share_chosen_incumbent']:.3f}",
                      flush=True)
        return pd.DataFrame(rows)


def calibrate_sigma(sim, beta, target, seed, tag):
    """Smallest sigma grid bracket around the target share of chosen incumbents; linear interpolation."""
    cal = []
    for z, sg in enumerate([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0]):
        S = sim.replicate(beta, CALR, seed + z, sigma=sg, tag=f"{tag} s={sg}")
        cal.append(dict(sigma=sg, share_mean=S.share_chosen_incumbent.mean(), OR_incumbent=S.OR_incumbent_main.mean(),
                        OR_future=S.OR_future_only.mean(), past_future=S.past_future_ratio.mean(),
                        last_earlier=S.last_earlier_ratio.mean()))
        if cal[-1]["share_mean"] > target:
            break
    cal = pd.DataFrame(cal)
    sh = cal.share_mean.values
    if sh[0] >= target:
        return 0.0, cal
    if sh[-1] < target:
        return float(cal.sigma.iloc[-1]), cal
    return float(np.interp(target, sh, cal.sigma.values)), cal


def summ(S, obs=None):
    cols = [c for c in S.columns if c != "sim"]
    d = {c: dict(mean=float(S[c].mean()), p2_5=float(S[c].quantile(.025)), p97_5=float(S[c].quantile(.975)))
         for c in cols}
    return d


def compare_ratio(obs_m, S, bootd=None):
    """Observed log(OR_inc/OR_fut) vs simulated distribution."""
    lo = obs_m["pf"]["log_ratio"]; se = obs_m["pf"]["se"]
    ls = np.log(S.past_future_ratio.values)
    out = dict(obs_ratio=float(np.exp(lo)), obs_ci_wald=(obs_m["pf"]["lo"], obs_m["pf"]["hi"]),
               sim_mean_ratio=float(np.exp(ls.mean())), sim_p2_5=float(np.exp(np.quantile(ls, .025))),
               sim_p97_5=float(np.exp(np.quantile(ls, .975))),
               share_sims_at_or_below_obs=float((ls <= lo).mean()))
    z = (lo - ls.mean()) / np.sqrt(se ** 2 + ls.var(ddof=1))
    out.update(z_wald=float(z), p_wald_two_sided=float(2 * stats.norm.sf(abs(z))))
    if bootd is not None:
        sb = bootd.std(ddof=1)
        z2 = (lo - ls.mean()) / np.sqrt(sb ** 2 + ls.var(ddof=1))
        out.update(boot_B=len(bootd), boot_ci=(float(np.exp(np.quantile(bootd, .025))), float(np.exp(np.quantile(bootd, .975)))),
                   boot_se_log=float(sb), z_boot=float(z2), p_boot_two_sided=float(2 * stats.norm.sf(abs(z2))),
                   share_boot_ge_sim_mean=float((bootd >= ls.mean()).mean()))
    return out


# =====================================================================  data
def data():
    P = RC.setup()
    H = RC.History(P)
    # Rebuild rather than reuse an unversioned pickle after data or definition changes.
    Call, _ = RC.build(H, window=730, n_alt=None)
    return P, H, Call


def extra_feats(P, H, C, lags=(0, 30, 90, 180, 365)):
    """Firm-level (non-dyadic) activity in the same market from OTHER buyers, and lagged placebo flags."""
    day, mkt, buyer = P["day"], P["mkt"], P["buyer"]
    n = len(C)
    fut_ob = np.zeros(n); past_ob = np.zeros(n); fut_any = np.zeros(n)
    fl = {L_: np.zeros(n) for L_ in lags}; nr = {L_: np.zeros(n) for L_ in lags}
    for q, (i, j) in enumerate(zip(C.contract.values, C.firm.values)):
        t, m, k = day[i], mkt[i], buyer[i]
        dm = H.fm.get((j, m), np.empty(0, int))
        dkm = H.fkm.get((j, k, m), np.empty(0, int))
        fd = H.fdays[j]
        fut_ob[q] = (len(dm) - np.searchsorted(dm, t, "right")) - (len(dkm) - np.searchsorted(dkm, t, "right"))
        past_ob[q] = np.searchsorted(dm, t, "left") - np.searchsorted(dkm, t, "left")
        fut_any[q] = len(fd) - np.searchsorted(fd, t, "right")
        if len(dkm) and np.searchsorted(dkm, t, "left") == 0 and dkm[-1] > t:
            for L_ in lags:
                first_future = dkm[np.searchsorted(dkm, t, "right")]
                if first_future > t + L_:
                    fl[L_][q] = 1
                else:
                    nr[L_][q] = 1
    C = C.copy()
    C["log_future_wins_market_other_buyers"] = np.log1p(fut_ob)
    C["log_past_wins_market_other_buyers"] = np.log1p(past_ob)
    C["log_future_wins_any"] = np.log1p(fut_any)
    for L_ in lags:
        C[f"fut_gt{L_}"] = fl[L_]; C[f"fut_le{L_}"] = nr[L_]
    return C


def refresh_placebo(P, H, Call):
    """Re-estimate observed firm controls and FIRST-future-win horizon checks."""
    Cx = extra_feats(P, H, Call)
    res4 = []
    specs = [("A baseline: main + future_only", PLAC),
             ("B + log future wins in m from other buyers", PLAC + ["log_future_wins_market_other_buyers"]),
             ("C + log past wins in m from other buyers", PLAC + ["log_past_wins_market_other_buyers"]),
             ("D + both", PLAC + ["log_future_wins_market_other_buyers", "log_past_wins_market_other_buyers"]),
             ("E + both + log future wins any market/buyer", PLAC + ["log_future_wins_market_other_buyers",
                                                                     "log_past_wins_market_other_buyers",
                                                                     "log_future_wins_any"]),
             ("F + future_other_market_only", PLAC + ["future_other_market_only"]),
             ("G + both + future_other_market_only", PLAC + ["log_future_wins_market_other_buyers",
                                                            "log_past_wins_market_other_buyers",
                                                            "future_other_market_only"])]
    for sub, C in [("all", Cx), ("renewals", Cx[Cx.renewal == "renewal"]), ("new needs", Cx[Cx.renewal == "new need"])]:
        for nm, cols in specs:
            if sub != "all" and nm[0] not in "AD":
                continue
            b, V = Prep(C, cols).fit()
            res4.append(or_row(b, V, cols, f"T4 {sub} | {nm}"))
        for L_ in (0, 30, 90, 180, 365):
            for ctrl, extra in [("", []), (" + firm controls", ["log_future_wins_market_other_buyers",
                                                                  "log_past_wins_market_other_buyers"])]:
                if sub != "all" and L_ not in (0, 365):
                    continue
                cols = MAIN + [f"fut_gt{L_}"] + ([f"fut_le{L_}"] if L_ > 0 else []) + extra
                b, V = Prep(C, cols).fit()
                res4.append(or_row(b, V, cols, f"T4 lag {sub} | future win > t+{L_}d{ctrl}"))
    R4 = pd.concat(res4, ignore_index=True)
    R4.to_csv(OUT / "D4_firm_controls_lags.csv", index=False)
    log("T4_summary", R4[R4.variable.isin(["incumbent", "future_supplier_only"] + [f"fut_gt{L_}" for L_ in (0, 30, 90, 180, 365)]
                                          + ["log_future_wins_market_other_buyers", "log_past_wins_market_other_buyers"])]
        [["model", "variable", "OR", "OR_lo", "OR_hi"]].to_dict("records"))
    lag_share = {L_: dict(chosen=float(Cx[Cx.chosen == 1][f"fut_gt{L_}"].mean()), alts=int(Cx[f"fut_gt{L_}"].sum()))
                 for L_ in (0, 30, 90, 180, 365)}
    log("T4_lag_counts", lag_share)



# =====================================================================  main
def main():
    P, H, Call = data()
    SUB = {"all": Call, "renewals": Call[Call.renewal == "renewal"], "new needs": Call[Call.renewal == "new need"]}
    ren = P["df"].renewal.values
    ELI = {"all": None, "renewals": np.flatnonzero(P["elig"] & (ren == "renewal")),
           "new needs": np.flatnonzero(P["elig"] & (ren == "new need"))}
    tabs = []
    # ---------------- observed moments (+ bootstrap of the past/future ratio)
    OBS, BOOTD = {}, {}
    for q, (nm, C) in enumerate(SUB.items()):
        m = moments(C, f"observed {nm}")
        tabs.append(m.pop("tables"))
        OBS[nm] = m
        BOOTD[nm] = boot_ratio(C, BOOT, SEED + 600 + q)
        log(f"obs_{nm}", {k: v for k, v in m.items() if k not in ("V_main",)})
    # ---------------- replay check of the recompute engine
    simall = Sim(P, Call)
    Cs, inc_all = simall.run(OBS["all"]["beta_main"], np.random.default_rng(0), recompute=True, replay=True)
    Cref = simall.C
    chk = {c: float(np.abs(Cs[c].values - Cref[c].values).max()) for c in OTH + ["incumbent", "future_supplier_only",
                                                                               "inc_last", "inc_earlier",
                                                                               "log_prior_wins_buyer_market"]}
    chk["incumbency_all_eligible_replay"] = inc_all
    log("replay_check_max_abs_diff", chk)

    SIMS = {}
    # ---------------- 1. SD simulation overall and by subgroup
    for q, (nm, C) in enumerate(SUB.items()):
        sim = simall if nm == "all" else Sim(P, C, ELI[nm])
        S = sim.replicate(np.array(OBS[nm]["beta_main"]), R, SEED + 500 + 10 * q, lagfit=(nm == "all"), tag=f"SD {nm}")
        S["world"] = "state dependence"; S["sample"] = nm; S["variant"] = "fitted beta, covariates held"
        SIMS[("SD", nm)] = S
        log(f"T1_SD_{nm}", summ(S.drop(columns=["world", "sample", "variant"])))
        log(f"T1_ratio_test_{nm}", compare_ratio(OBS[nm], S, BOOTD[nm]))

    # ---------------- 2a. beta_inc grid (overall)
    b0 = np.array(OBS["all"]["beta_main"])
    grid = []
    for q, dlt in enumerate([-1.0, -0.5, 0.5, 1.0]):
        b = b0.copy(); b[0] += dlt
        S = simall.replicate(b, R, SEED + 700 + q, tag=f"grid {dlt:+}")
        S["world"] = "state dependence"; S["sample"] = "all"; S["variant"] = f"beta_inc {dlt:+.1f}"
        SIMS[("grid", dlt)] = S
        grid.append((dlt, S))
    grid.append((0.0, SIMS[("SD", "all")]))
    grid.sort(key=lambda z: z[0])
    G = pd.DataFrame([dict(delta=d_, beta_inc=b0[0] + d_, OR_incumbent_generating=np.exp(b0[0] + d_),
                           **{f"{c}_{s}": v for c in ["share_chosen_incumbent", "OR_future_only", "OR_incumbent_plac",
                                                      "past_future_ratio", "last_earlier_ratio", "incumbency_all_eligible"]
                              for s, v in [("mean", S[c].mean()), ("p2_5", S[c].quantile(.025)),
                                           ("p97_5", S[c].quantile(.975))]}) for d_, S in grid])
    G.to_csv(OUT / "D2a_beta_grid.csv", index=False)
    obs_share = OBS["all"]["share_chosen_incumbent"]
    xs, ys = G.beta_inc.values, G.share_chosen_incumbent_mean.values
    b_star = float(np.interp(obs_share, ys, xs)) if ys.min() <= obs_share <= ys.max() else None
    log("T2a_grid", dict(obs_share=obs_share, beta_star_interp=b_star, grid=G.to_dict("records")))
    if b_star is not None:
        b = b0.copy(); b[0] = b_star
        S = simall.replicate(b, R, SEED + 710, tag="beta*")
        S["world"] = "state dependence"; S["sample"] = "all"; S["variant"] = "beta_inc calibrated to share 0.689"
        SIMS[("SD", "all", "calibrated")] = S
        log("T2a_calibrated_beta", dict(beta=b_star, OR=np.exp(b_star), **summ(S.drop(columns=["world", "sample", "variant"]))))

    # ---------------- 2b. parametric uncertainty
    rngp = np.random.default_rng(SEED + 720)
    draws = rngp.multivariate_normal(b0, OBS["all"]["V_main"], size=R)
    S = simall.replicate(b0, R, SEED + 721, beta_draws=draws, tag="param")
    S["world"] = "state dependence"; S["sample"] = "all"; S["variant"] = "beta ~ N(beta_hat, V_cluster)"
    SIMS[("param",)] = S
    log("T2b_parametric", summ(S.drop(columns=["world", "sample", "variant"])))

    # ---------------- 2c. all covariates recomputed from the simulated history
    S = simall.replicate(b0, R, SEED + 730, recompute=True, tag="recompute")
    S["world"] = "state dependence"; S["sample"] = "all"; S["variant"] = "all covariates recomputed"
    SIMS[("recompute",)] = S
    log("T2c_recompute", summ(S.drop(columns=["world", "sample", "variant"])))

    # ---------------- 3. heterogeneity-only world (beta_inc = 0), sigma calibrated
    HET = {}
    for q, (nm, C) in enumerate(SUB.items()):
        sim = simall if nm == "all" else Sim(P, C, ELI[nm])
        bh = np.array(OBS[nm]["beta_main"]); bh[0] = 0.0
        target = OBS[nm]["share_chosen_incumbent"]
        s_star, cal = calibrate_sigma(sim, bh, target, SEED + 800 + 50 * q, f"cal {nm}")
        cal.insert(0, "sample", nm)
        HET[nm] = cal
        S = sim.replicate(bh, R, SEED + 900 + q, sigma=s_star, lagfit=(nm == "all"), tag=f"HET {nm}")
        S["world"] = "heterogeneity"; S["sample"] = nm; S["variant"] = f"sigma={s_star:.3f}"
        SIMS[("HET", nm)] = S
        log(f"T3_HET_{nm}", dict(target_share=target, sigma_star=s_star, calibration=cal.to_dict("records"),
                                 **summ(S.drop(columns=["world", "sample", "variant"]))))
        log(f"T3_ratio_test_{nm}", compare_ratio(OBS[nm], S, BOOTD[nm]))
    pd.concat(HET.values()).to_csv(OUT / "D3_het_sigma_calibration.csv", index=False)

    # ---------------- 3b. mixture frontier: beta_inc fixed on a grid, sigma calibrated to the same share
    mix = []
    for q, (nm, C) in enumerate(SUB.items()):
        sim = simall if nm == "all" else Sim(P, C, ELI[nm])
        bfit = np.array(OBS[nm]["beta_main"])
        target = OBS[nm]["share_chosen_incumbent"]
        for z, bi in enumerate(sorted({0.0, 1.0, 2.0, 3.0, round(bfit[0], 3)})):
            if bi > bfit[0] + 1e-9:
                continue
            bb = bfit.copy(); bb[0] = bi
            s_star, _ = calibrate_sigma(sim, bb, target, SEED + 1000 + 50 * q + 5 * z, f"mixcal {nm} b={bi}")
            S = sim.replicate(bb, RMIX, SEED + 1200 + 50 * q + z, sigma=s_star, tag=f"MIX {nm} b={bi}")
            mix.append(dict(sample=nm, beta_inc=bi, OR_inc_generating=np.exp(bi), sigma_star=s_star, reps=RMIX,
                            **{f"{c}_{st}": getattr(S[c], fn)(*a) for c in
                               ["share_chosen_incumbent", "OR_incumbent_main", "OR_incumbent_plac", "OR_future_only",
                                "past_future_ratio", "last_earlier_ratio", "incumbency_all_eligible"]
                               for st, fn, a in [("mean", "mean", ()), ("p2_5", "quantile", (.025,)),
                                                 ("p97_5", "quantile", (.975,))]}))
            print(mix[-1], flush=True)
    MIX = pd.DataFrame(mix)
    MIX.to_csv(OUT / "D3b_mixture_frontier.csv", index=False)
    log("T3b_mixture", MIX.to_dict("records"))

    allsims = pd.concat(SIMS.values(), ignore_index=True)
    allsims.to_csv(OUT / "D_simulations_all_reps.csv", index=False)

    # ---------------- three-world table
    MOM = ["OR_incumbent_main", "OR_incumbent_plac", "OR_future_only", "past_future_ratio", "OR_inc_last",
           "OR_inc_earlier", "last_earlier_ratio", "share_chosen_incumbent", "share_chosen_future_only",
           "incumbency_all_eligible"]
    rows = []
    for nm in SUB:
        o = OBS[nm]
        for c in MOM:
            if c == "incumbency_all_eligible":
                ov = float(P["inc"][P["elig"]].mean()) if nm == "all" else float(
                    P["inc"][P["elig"] & (P["df"].renewal.values == ("renewal" if nm == "renewals" else "new need"))].mean())
                ci = (np.nan, np.nan)
            else:
                ov = float(o[c]); ci = o["ci"].get(c, (np.nan, np.nan))
            rows.append(dict(sample=nm, moment=c, world="observed", center=ov, lo=ci[0], hi=ci[1]))
            for w, key in [("state dependence", ("SD", nm)), ("heterogeneity", ("HET", nm))]:
                S = SIMS[key]
                rows.append(dict(sample=nm, moment=c, world=w, center=S[c].mean(), lo=S[c].quantile(.025),
                                 hi=S[c].quantile(.975)))
    W = pd.DataFrame(rows)
    W.to_csv(OUT / "D3_three_worlds.csv", index=False)

    # ---------------- 4. firm-level controls + lags ; 5. recency with count control
    refresh_placebo(P, H, Call)

    res5 = []
    for sub, C in SUB.items():
        for nm, cols in [("last vs earlier", LE), ("+ log prior wins with buyer-market", LE + ["log_prior_wins_buyer_market"])]:
            b, V = Prep(C, cols).fit()
            res5.append(dict(sample=sub, model=nm, OR_last=np.exp(b[0]), OR_earlier=np.exp(b[1]), **contrast(b, V, 0, 1),
                             OR_count=np.exp(b[-1]) if "prior wins" in nm else np.nan))
    R5 = pd.DataFrame(res5)
    R5.to_csv(OUT / "D5_recency_count_control.csv", index=False)
    log("T5_recency", R5.to_dict("records"))
    # recency in the simulated worlds with the count control too (SD + HET, overall) -> quick R=30 replay
    pd.concat(tabs, ignore_index=True).to_csv(OUT / "D1_observed_clogit.csv", index=False)

    # ---------------- figures
    fig_three_worlds(W)
    fig_market_n3()
    json.dump(LOG, open(OUT / "revision_d_log.json", "w", encoding="utf-8"), indent=2, default=str, ensure_ascii=False)
    (OUT / "_cache_choice_all.pkl").unlink(missing_ok=True)       # temporary (contains firm codes)
    print("done", time.time() - T0)


# =====================================================================  figures
def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def fig_three_worlds(W):
    panels = [("OR_incumbent_plac", "Past-supplier OR"), ("OR_future_only", "Future-supplier-only OR"),
              ("last_earlier_ratio", "Last / earlier supplier OR ratio")]
    samples = [("all", "All"), ("renewals", "Renewals"), ("new needs", "New needs")]
    worlds = [("observed", "Observed (95% CI)", OI[7], "o"),
              ("state dependence", "Simulated: state dependence only", OI[5], "s"),
              ("heterogeneity", "Simulated: heterogeneity only", OI[4], "D")]
    fig, axes = plt.subplots(1, 3, figsize=(7, 2.5), sharey=True)
    for ax, (mom, xl) in zip(axes, panels):
        for si, (s, _) in enumerate(samples):
            for wi, (w, lab, col, mk) in enumerate(worlds):
                r = W[(W["sample"] == s) & (W.moment == mom) & (W.world == w)].iloc[0]
                y = si + (1 - wi) * 0.24
                ax.plot([r.lo, r.hi], [y, y], color=col, lw=1.4, solid_capstyle="butt")
                ax.plot(r.center, y, mk, color=col, ms=4.2, mfc=col if w == "observed" else "white", mew=1.2,
                        label=lab if si == 0 else None)
        ax.set_xscale("log")
        lo_ = W[W.moment == mom].lo.min(); hi_ = W[W.moment == mom].hi.max()
        tk = [t for t in [0.8, 1, 1.5, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000] if lo_ / 1.3 <= t <= hi_ * 1.3]
        ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(tk))
        ax.xaxis.set_major_formatter(matplotlib.ticker.FixedFormatter([f"{t:g}" for t in tk]))
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_xlabel(xl + " (log scale)")
        if mom == "last_earlier_ratio":
            ax.axvline(1, color="#777777", lw=0.8, ls=":")
        ax.grid(axis="y", visible=False)
        ax.set_ylim(len(samples) - 0.55, -0.45)
    axes[0].set_yticks(range(len(samples))); axes[0].set_yticklabels([s[1] for s in samples])
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.07))
    fig.tight_layout()
    save(fig, "F-D1_three_worlds")


def fig_market_n3():
    grdf = pd.read_csv(ROOT / "results" / "lockin" / "null_by_group.csv")
    g = grdf[(grdf.variant == "S8_cell_market_x_year_x_province") & (grdf.dimension == "market")].copy()
    g = g.sort_values("obs")
    fig, ax = plt.subplots(figsize=(7, 4.0))
    y = np.arange(len(g))
    ax.hlines(y, g.null_lo, g.null_hi, color=OI[1], lw=5, alpha=0.8, label="Null 95% interval (N3)")
    ax.plot(g.null_mean, y, "|", color=OI[4], ms=9, mew=1.5, label="Null mean")
    ax.plot(g.obs, y, "o", color=OI[5], ms=5, label="Observed")
    labels = [f"{m.replace('_', ' ')} (n={ne:,})" for m, ne in zip(g.group, g.n_eligible)]
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlabel("Incumbency rate (share of repeat-eligible contracts won by an incumbent)")
    ax.set_xlim(0, max(g.obs.max(), g.null_hi.max()) * 1.08)
    ax.legend(loc="lower right", frameon=False)
    ax.grid(axis="y", visible=False)
    save(fig, "F-L1b_incumbency_by_market_N3")
    g[["group", "n_eligible", "obs", "null_mean", "null_lo", "null_hi", "ratio", "excess", "p_upper"]].to_csv(
        OUT / "D7_market_N3.csv", index=False)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "figs":
        fig_three_worlds(pd.read_csv(OUT / "D3_three_worlds.csv")); fig_market_n3()
    elif len(sys.argv) > 1 and sys.argv[1] == "lags":
        previous = json.loads((OUT / "revision_d_log.json").read_text(encoding="utf-8"))
        LOG.update(previous)
        refresh_placebo(*data())
    else:
        main()
