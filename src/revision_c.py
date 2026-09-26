# -*- coding: utf-8 -*-
"""TenderNet v3 - topic `revision_c` (referee round C).

1. Supplier-choice model with a leakage-free choice set: pool = firms with >=1 win in market m
   in the 24 (12) months strictly before t; entrant winners handled explicitly; pool sizes
   10 / 30 / all; subgroups; incumbents-in-pool diagnostics.
2. State dependence vs match heterogeneity: future-supplier-only placebo covariate and
   last-vs-earlier incumbent contrast inside the conditional logit.
3. N4 / N4b nulls with the winner's home province from wins strictly before t.
4. Exclusivity (licence / maintenance / support of named products) flags; incumbency + N1/N3
   nulls for the remaining contracts; 21(f) incumbency vs nulls.
5. Single bids: random sample (total / valid bids) and cp2 (valid bids) with renewal control.
6. 21(b) x post x health triple interaction (two-way clustered).

Reuses lockin_analysis.py, revision_a.py (clogit, null_run) and models_common/models_features;
none of them is modified.  Run: python src/revision_c.py  (env REVC_B = permutations).
"""
from pathlib import Path
import json
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lockin_analysis as L          # noqa: E402
import revision_a as RA              # noqa: E402
import revision_a_titles as T        # noqa: E402
from models_common import load as mload, twoway_vcov, oneway_vcov  # noqa: E402
from models_features import contract_history  # noqa: E402

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "revision_c"
OUT.mkdir(parents=True, exist_ok=True)
B = int(os.environ.get("REVC_B", 1000))
SEED = 42
LOG = {}


def clogit_fit_robust(X, g, y, w=None, beta0=None, maxit=200):
    """Same estimator as revision_a.clogit_fit but with a capped Newton step and a line search that
    never accepts a worsening step (the original can overshoot from beta=0 when an alternative-specific
    dummy is rare in large choice sets).  Installed into revision_a so RA.clogit uses it."""
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

    def derivs(p):
        xbar = np.vstack([np.bincount(g, weights=p * X[:, k], minlength=G) for k in range(K)]).T
        xch = np.vstack([np.bincount(g, weights=y * X[:, k], minlength=G) for k in range(K)]).T
        S = xch - xbar
        Xc = X - xbar[g]
        H = (Xc * (p * w[g])[:, None]).T @ Xc
        return S, H

    ll, p = evaluate(beta)
    for it in range(maxit):
        S, H = derivs(p)
        grad = (w[:, None] * S).sum(0)
        step = np.linalg.solve(H + 1e-8 * np.eye(K), grad)
        mx = np.max(np.abs(step))
        if mx > 2.0:
            step *= 2.0 / mx
        t, moved = 1.0, False
        while t >= 1e-8:
            ll_new, p_new = evaluate(beta + t * step)
            if np.isfinite(ll_new) and ll_new >= ll - 1e-12:
                moved = True
                break
            t /= 2
        if not moved:
            break
        beta = beta + t * step
        done = abs(ll_new - ll) < 1e-10 and np.max(np.abs(t * step)) < 1e-8
        ll, p = ll_new, p_new
        if done:
            break
    S, H = derivs(p)
    return beta, H, S, ll


RA.clogit_fit = clogit_fit_robust


def log(k, v):
    LOG[k] = v
    print(k, v if not isinstance(v, (dict, list)) else json.dumps(v, default=str)[:600], flush=True)


# =====================================================================  data
def setup():
    d = L.load()
    main_df = d[d["in_scope_main"] == True].copy()
    P = L.prepare(main_df)
    df = P["df"]
    fl = pd.read_csv(RA.OUT / "A_renewal_flags.csv", usecols=["IKN", "renewal"])
    df["renewal"] = df.IKN.map(fl.set_index("IKN").renewal).values
    assert (df.renewal.notna()).all()
    df["proc"] = L.proc3(df.usul_v3.values)
    P["inc"] = L.incumbent(P, P["firm"])
    P["ilc"] = pd.factorize(df["il"])[0]
    P["sec"] = pd.factorize(df["sektor_v3"])[0]
    return P


class History:
    """Look-up structures for strictly-before-t firm / buyer histories."""

    def __init__(self, P):
        df = P["df"]
        self.P = P
        firm, day, mkt, buyer, ilc, sec = P["firm"], P["day"], P["mkt"], P["buyer"], P["ilc"], P["sec"]
        n = len(day)
        order = np.lexsort((np.arange(n), day))          # chronological
        self.fdays, self.home_after = {}, {}
        tmp = {}
        for i in order:
            tmp.setdefault(firm[i], []).append(i)
        for j, idx in tmp.items():
            idx = np.array(idx)
            self.fdays[j] = day[idx]
            # home province after each prefix: most wins, ties -> earliest first win
            cnt, first, h = {}, {}, [-1]
            for pos, c in enumerate(ilc[idx]):
                cnt[c] = cnt.get(c, 0) + 1
                first.setdefault(c, pos)
                h.append(min(cnt, key=lambda q: (-cnt[q], first[q])))
            self.home_after[j] = np.array(h)
        self.fm, self.fs = {}, {}
        for key, g in pd.Series(day).groupby([firm, mkt]):
            self.fm[key] = np.sort(g.values)
        for key, g in pd.Series(day).groupby([firm, sec]):
            self.fs[key] = np.sort(g.values)
        # firm x buyer x market days
        self.fkm = {}
        for key, g in pd.Series(day).groupby([firm, buyer, mkt]):
            self.fkm[key] = np.sort(g.values)
        # firm x buyer -> {market: (first, last)}
        self.fk = {}
        for (j, k, m), dd in self.fkm.items():
            self.fk.setdefault((j, k), {})[m] = (dd[0], dd[-1])
        # buyer x market chronological (day, firm)
        self.km = {}
        for key, g in pd.DataFrame(dict(d=day, f=firm)).groupby([buyer, mkt]):
            g = g.sort_values("d")
            self.km[key] = (g.d.values, g.f.values)
        # market chronological (day, firm)
        self.mk = {}
        for m, g in pd.DataFrame(dict(d=day, f=firm)).groupby(mkt):
            g = g.sort_values("d")
            self.mk[m] = (g.d.values, g.f.values)
        # all markets chronological
        o = np.argsort(day, kind="stable")
        self.all_d, self.all_f = day[o], firm[o]

    def pool(self, m, t, window):
        if m is None:
            d_, f_ = self.all_d, self.all_f
        else:
            d_, f_ = self.mk[m]
        a, b = np.searchsorted(d_, t - window, "left"), np.searchsorted(d_, t, "left")
        return np.unique(f_[a:b])

    def buyer_state(self, k, m, t):
        """incumbent set, last-supplier set (winners on the latest date < t)."""
        d_, f_ = self.km[(k, m)]
        n = np.searchsorted(d_, t, "left")
        if n == 0:
            return set(), set()
        inc = set(f_[:n].tolist())
        last = set(f_[:n][d_[:n] == d_[n - 1]].tolist())
        return inc, last

    def feats(self, j, i, last):
        P = self.P
        t, k, m, s, il = P["day"][i], P["buyer"][i], P["mkt"][i], P["sec"][i], P["ilc"][i]
        fd = self.fdays[j]
        n = np.searchsorted(fd, t, "left")
        dm = self.fm.get((j, m), np.empty(0, int))
        nm12 = np.searchsorted(dm, t, "left") - np.searchsorted(dm, t - 365, "left")
        nm24 = np.searchsorted(dm, t, "left") - np.searchsorted(dm, t - 730, "left")
        ds = self.fs.get((j, s), np.empty(0, int))
        nsec = np.searchsorted(ds, t, "left")
        dkm = self.fkm.get((j, k, m), np.empty(0, int))
        nkm = np.searchsorted(dkm, t, "left")
        inc = int(nkm > 0)
        fut_only = int(nkm == 0 and len(dkm) > 0 and dkm[-1] > t)
        other = self.fk.get((j, k), {})
        inc_oth = int(any(fl[0] < t for mm, fl in other.items() if mm != m))
        ever_k_before = inc or inc_oth
        fut_oth_only = int((not ever_k_before) and any(fl[1] > t for mm, fl in other.items() if mm != m))
        h = self.home_after[j][n]
        is_last = int(inc and j in last)
        return (inc, is_last, int(inc and not is_last), fut_only, inc_oth, fut_oth_only,
                int(n > 0 and h == il), np.log1p(nm12), np.log1p(n), np.log1p(nsec), np.log1p(nkm),
                int(n == 0), int(nm24 == 0))


FEATS = ["incumbent", "inc_last", "inc_earlier", "future_supplier_only", "inc_other_market",
         "future_other_market_only", "same_home_prior", "log_wins_market_12m", "log_total_prior_wins",
         "log_prior_wins_same_sector", "log_prior_wins_buyer_market", "no_prior_wins", "new_to_market_24m"]
MAIN = ["incumbent", "inc_other_market", "same_home_prior", "log_wins_market_12m", "log_total_prior_wins",
        "log_prior_wins_same_sector"]


def build(H, window=730, n_alt=30, pool_kind="market", include_entrants=False, seed=SEED):
    """Choice data for repeat-eligible contracts.  Returns (C rows, per-contract diagnostics)."""
    P = H.P
    rng = np.random.default_rng(seed)
    firm, day, mkt, buyer = P["firm"], P["day"], P["mkt"], P["buyer"]
    rows, diag = [], []
    for i in np.flatnonzero(P["elig"]):
        t, m, k, w = day[i], mkt[i], buyer[i], firm[i]
        pool = H.pool(None if pool_kind == "broad" else m, t, window)
        in_pool = bool(np.isin(w, pool))
        inc_set, last = H.buyer_state(k, m, t)
        inc_arr = np.fromiter(inc_set, int) if inc_set else np.empty(0, int)
        diag.append((i, len(pool), in_pool, len(inc_set), int(np.isin(inc_arr, pool).sum()),
                     int(bool(last & set(pool.tolist()))), int(w in inc_set)))
        if not in_pool and not include_entrants:
            continue
        others = pool[pool != w]
        alts = others if (n_alt is None or len(others) <= n_alt) else rng.choice(others, n_alt, replace=False)
        for j, ch in [(w, 1)] + [(a, 0) for a in alts]:
            rows.append((i, j, ch, int(not in_pool and ch == 1)) + H.feats(j, i, last))
    C = pd.DataFrame(rows, columns=["contract", "firm", "chosen", "entrant"] + FEATS)
    df = P["df"]
    C["buyer"] = buyer[C.contract.values]
    C["renewal"] = df.renewal.values[C.contract.values]
    C["proc"] = df.proc.values[C.contract.values]
    C["year"] = df.yil_v3.values[C.contract.values].astype(int)
    D = pd.DataFrame(diag, columns=["contract", "pool_size", "winner_in_pool", "n_incumbents",
                                    "n_incumbents_in_pool", "last_supplier_in_pool", "winner_incumbent"])
    return C, D


def fit(C, cols, label):
    C = C[C.groupby("contract").chosen.transform("size") > 1]      # singleton sets carry no information
    r = RA.clogit(C, cols, label=label)
    return r


SIMR = int(os.environ.get("REVC_SIM", 100))


def placebo_sim(P, Call, beta, R):
    """Benchmark for the future-tie placebo under PURE state dependence.
    Winners of the in-pool repeat-eligible contracts are re-drawn sequentially (chronological order)
    from the fitted main model (pool = all pre-t active firms, 24 m), with `incumbent` recomputed from the
    simulated history of the buyer-market; all other covariates are held at their observed values and all
    other contracts (entrant winners, first contracts of a buyer-market) keep their observed winner.
    There is no match heterogeneity in this data-generating process beyond the observed covariates, so
    the future_supplier_only OR estimated on simulated data shows what state dependence alone produces
    (including the mechanical channel: the winner of t becomes the incumbent for later contracts)."""
    C = Call.sort_values(["contract", "chosen"], ascending=[True, False]).reset_index(drop=True)
    con, firms = C.contract.values, C.firm.values
    Xs = C[MAIN[1:]].values.astype(float) @ beta[1:]
    b_inc = beta[0]
    st = np.r_[0, np.flatnonzero(con[1:] != con[:-1]) + 1, len(con)]
    sl = {con[a]: (a, b) for a, b in zip(st[:-1], st[1:])}
    day, bm, fobs = P["day"], P["bm"], P["firm"]
    n = len(day)
    order = np.lexsort((np.arange(n), day))
    rng = np.random.default_rng(SEED + 500)
    rowcon_day = day[con]
    rowcon_bm = bm[con]
    out = []
    for r in range(R):
        simf = fobs.copy()
        hist = {}
        for i in order:
            key = bm[i]
            if i in sl:
                a, b = sl[i]
                prior = {f for d_, f in hist.get(key, ()) if d_ < day[i]}
                inc = np.fromiter((f in prior for f in firms[a:b]), bool, b - a)
                u = Xs[a:b] + b_inc * inc
                p = np.exp(u - u.max()); p /= p.sum()
                simf[i] = firms[a + rng.choice(b - a, p=p)]
            hist.setdefault(key, []).append((day[i], simf[i]))
        # recompute alternative-specific history covariates from the simulated winners
        inc_s = np.zeros(len(C)); fut_s = np.zeros(len(C)); last_s = np.zeros(len(C))
        for c_, (a, b) in sl.items():
            h = hist[bm[c_]]; t = day[c_]
            prior = [(d_, f) for d_, f in h if d_ < t]
            pset = {f for _, f in prior}
            fset = {f for d_, f in h if d_ > t}
            lastd = max((d_ for d_, _ in prior), default=None)
            lset = {f for d_, f in prior if d_ == lastd}
            for q in range(a, b):
                f = firms[q]
                inc_s[q] = f in pset
                fut_s[q] = (f not in pset) and (f in fset)
                last_s[q] = f in lset
        Cs = C[["contract", "buyer"] + MAIN[1:]].copy()
        Cs["chosen"] = (firms == simf[con]).astype(int)
        Cs["incumbent"] = inc_s
        Cs["future_supplier_only"] = fut_s
        Cs["inc_last"] = inc_s * last_s
        Cs["inc_earlier"] = inc_s * (1 - last_s)
        r1 = fit(Cs, MAIN + ["future_supplier_only"], "sim")
        r2 = fit(Cs, ["inc_last", "inc_earlier"] + MAIN[1:], "sim")
        o1 = dict(zip(r1.variable, r1.OR)); o2 = dict(zip(r2.variable, r2.OR))
        out.append(dict(sim=r, OR_incumbent=o1["incumbent"], OR_future_only=o1["future_supplier_only"],
                        OR_inc_last=o2["inc_last"], OR_inc_earlier=o2["inc_earlier"],
                        sim_incumbency_kept=float(Cs[Cs.chosen == 1].incumbent.mean()),
                        sim_chosen_future_only=float(Cs[Cs.chosen == 1].future_supplier_only.mean())))
        if r % 10 == 0:
            print("sim", r, out[-1], flush=True)
    S = pd.DataFrame(out)
    log("T2_placebo_sim_summary", {c: dict(mean=float(S[c].mean()), p2_5=float(S[c].quantile(.025)),
                                           p97_5=float(S[c].quantile(.975))) for c in S.columns if c != "sim"})
    return S


# =====================================================================  task 1 + 2
def choice_models(P):
    H = History(P)
    res, diags = [], {}
    specs = {}
    for win in (730, 365):
        for nalt, nm in [(10, "10"), (30, "30"), (None, "all")]:
            if win == 365 and nm != "30" and nm != "all":
                continue
            C, D = build(H, window=win, n_alt=nalt)
            specs[(win, nm)] = C
            diags[(win, nm)] = D
            print("built", win, nm, len(C), flush=True)
    D = diags[(730, "30")]
    D12 = diags[(365, "30")]
    el = P["df"].iloc[D.contract.values]

    def dsum(D):
        inc_c = D.n_incumbents > 0
        return dict(eligible=len(D), winner_in_pool=int(D.winner_in_pool.sum()),
                    entrant_share=float(1 - D.winner_in_pool.mean()),
                    entrant_share_among_incumbent_wins=float(1 - D[D.winner_incumbent == 1].winner_in_pool.mean()),
                    entrant_share_among_nonincumbent_wins=float(1 - D[D.winner_incumbent == 0].winner_in_pool.mean()),
                    incumbency_all=float(D.winner_incumbent.mean()),
                    incumbency_kept=float(D[D.winner_in_pool].winner_incumbent.mean()),
                    pool_size_median=float(D.pool_size.median()), pool_size_mean=float(D.pool_size.mean()),
                    pool_size_p10_p90=[float(x) for x in np.percentile(D.pool_size, [10, 90])],
                    share_contracts_any_incumbent_in_pool=float((D.n_incumbents_in_pool > 0).mean()),
                    share_incumbents_in_pool=float(D.n_incumbents_in_pool.sum() / D.n_incumbents.sum()),
                    share_contracts_last_supplier_in_pool=float(D.last_supplier_in_pool.mean()),
                    share_contracts_all_incumbents_in_pool=float((D.n_incumbents_in_pool == D.n_incumbents).mean()))
    log("pool_diag_24m", dsum(D))
    log("pool_diag_12m", dsum(D12))
    ent = pd.DataFrame(dict(renewal=el.renewal.values, proc=el.proc.values, in_pool=D.winner_in_pool.values))
    log("entrant_share_by_renewal", (1 - ent.groupby("renewal").in_pool.mean()).to_dict())
    log("entrant_share_by_proc", (1 - ent.groupby("proc").in_pool.mean()).to_dict())
    D.to_csv(OUT / "C1_pool_diagnostics_24m.csv", index=False)

    # ---- main models
    for (win, nm), C in specs.items():
        wl = f"{win // 365 * 12}m"
        res.append(fit(C, ["incumbent"], f"T1 {wl} pool={nm}: incumbent only"))
        res.append(fit(C, MAIN, f"T1 {wl} pool={nm}: main"))
    C30, Call = specs[(730, "30")], specs[(730, "all")]
    for lab, C in [("30", C30), ("all", Call)]:
        for sub, m_ in [("renewals", C.renewal == "renewal"), ("new needs", C.renewal == "new need"),
                        ("21(b)", C.proc == "21(b)"), ("open", C.proc == "open"),
                        ("other procedures", C.proc == "other")]:
            res.append(fit(C[m_], MAIN, f"T1 24m pool={lab}: main | {sub}"))
    # ---- (b) entrants added regardless
    Ce, De = build(H, window=730, n_alt=30, include_entrants=True)
    res.append(fit(Ce, MAIN, "T1b 24m pool=30 + entrant winners (no entrant flag)"))
    for sub, m_ in [("renewals", Ce.renewal == "renewal"), ("new needs", Ce.renewal == "new need")]:
        res.append(fit(Ce[m_], MAIN, f"T1b 24m pool=30 + entrant winners | {sub}"))
    log("T1b_entrant_flag", dict(rows_entrant=int(Ce.entrant.sum()),
                                  entrant_flag_chosen_share=float(Ce[Ce.entrant == 1].chosen.mean()),
                                  note="entrant==1 only for chosen rows -> perfect separation; not estimable"))
    # ---- (c) broad pool: firms with any win in any market in 24 m; new-to-market flag is defined for all
    Cb, Db = build(H, window=730, n_alt=30, pool_kind="broad")
    log("broad_pool_diag", dict(entrant_share=float(1 - Db.winner_in_pool.mean()),
                                pool_size_median=float(Db.pool_size.median())))
    res.append(fit(Cb, MAIN + ["new_to_market_24m"], "T1c broad 24m pool=30 (any market) + new-to-market"))

    # ---- task 2: future placebo, last vs earlier
    cut = pd.Timestamp("2023-12-31")
    early = set(np.flatnonzero((P["df"].date <= cut).values))
    for lab, C in [("30", C30), ("all", Call)]:
        res.append(fit(C, MAIN + ["future_supplier_only"], f"T2a 24m pool={lab}: main + future_supplier_only"))
        Ce_ = C[C.contract.isin(early)]
        res.append(fit(Ce_, MAIN + ["future_supplier_only"],
                       f"T2a 24m pool={lab}: main + future_supplier_only | t <= 2023-12-31"))
        res.append(fit(C, MAIN + ["future_supplier_only", "future_other_market_only"],
                       f"T2a 24m pool={lab}: + future_other_market_only"))
        M2 = ["inc_last", "inc_earlier"] + MAIN[1:]
        res.append(fit(C, M2, f"T2b 24m pool={lab}: last vs earlier"))
        res.append(fit(C, M2 + ["log_prior_wins_buyer_market"], f"T2b 24m pool={lab}: last vs earlier + log prior wins with buyer-market"))
        res.append(fit(C, M2 + ["future_supplier_only"], f"T2ab 24m pool={lab}: last vs earlier + future_only"))
        for sub, m_ in [("renewals", C.renewal == "renewal"), ("new needs", C.renewal == "new need")]:
            res.append(fit(C[m_], M2, f"T2b 24m pool={lab}: last vs earlier | {sub}"))
            res.append(fit(C[m_], MAIN + ["future_supplier_only"], f"T2a 24m pool={lab}: main + future_only | {sub}"))
    # Wald test last = earlier (pool all)
    Cs = Call[Call.groupby("contract").chosen.transform("size") > 1].sort_values(
        ["contract", "chosen"], ascending=[True, False]).reset_index(drop=True)
    M2 = ["inc_last", "inc_earlier"] + MAIN[1:]
    g = pd.factorize(Cs.contract)[0]
    beta, Hh, S, _ = RA.clogit_fit(Cs[M2].values.astype(float), g, Cs.chosen.values.astype(float))
    Hinv = np.linalg.inv(Hh)
    cl = pd.factorize(Cs.groupby(g).buyer.first().values)[0]
    nc = cl.max() + 1
    Sc = np.vstack([np.bincount(cl, weights=S[:, q], minlength=nc) for q in range(S.shape[1])]).T
    V = Hinv @ (Sc.T @ Sc) @ Hinv * nc / (nc - 1)
    dlt = beta[0] - beta[1]; sd = np.sqrt(V[0, 0] + V[1, 1] - 2 * V[0, 1])
    log("T2b_last_minus_earlier_poolall", dict(diff=dlt, ratio_OR=np.exp(dlt), lo=np.exp(dlt - 1.96 * sd),
                                                hi=np.exp(dlt + 1.96 * sd), p=2 * stats.norm.sf(abs(dlt / sd))))
    # descriptives for task 2
    ch = Call[Call.chosen == 1]
    al = Call[Call.chosen == 0]
    log("T2_descr_poolall", dict(
        chosen_share_incumbent=float(ch.incumbent.mean()), chosen_share_future_only=float(ch.future_supplier_only.mean()),
        alt_share_incumbent=float(al.incumbent.mean()), alt_share_future_only=float(al.future_supplier_only.mean()),
        chosen_share_inc_last=float(ch.inc_last.mean()), chosen_share_inc_earlier=float(ch.inc_earlier.mean()),
        alt_share_inc_last=float(al.inc_last.mean()), alt_share_inc_earlier=float(al.inc_earlier.mean()),
        contracts_with_earlier_incumbent_alt=int(Call.groupby("contract").inc_earlier.max().sum())))
    # P(win | status) in the full pool (descriptive per referee wording)
    st = np.where(Call.inc_last == 1, "incumbent: last", np.where(Call.inc_earlier == 1, "incumbent: earlier (not last)",
                  np.where(Call.future_supplier_only == 1, "future supplier only", "other pool firm")))
    tb = Call.assign(status=st).groupby("status").agg(alternatives=("chosen", "size"), wins=("chosen", "sum"))
    tb["P_win_per_alternative"] = tb.wins / tb.alternatives
    tb.to_csv(OUT / "C2_win_rate_by_status_poolall.csv")
    log("T2_win_rate_by_status", tb.to_dict())
    Call.drop(columns=["firm"]).to_csv(OUT / "C1_choice_data_24m_poolall.csv.gz", index=False, compression="gzip")
    # ---- simulation benchmark for the placebo under pure state dependence
    main_all = [r for r in res if r.model.iloc[0] == "T1 24m pool=all: main"][0]
    sim = placebo_sim(P, Call, main_all.coef.values, R=SIMR)
    sim.to_csv(OUT / "C2_placebo_simulation.csv", index=False)
    out = pd.concat(res, ignore_index=True)
    out.to_csv(OUT / "C1_C2_clogit_results.csv", index=False)
    return out, H


# =====================================================================  task 3
def n4_prior(P, H):
    df = P["df"]
    n = len(df)
    home = np.empty(n, dtype=object)
    for i in range(n):
        j = P["firm"][i]
        k = np.searchsorted(H.fdays[j], P["day"][i], "left")
        h = H.home_after[j][k]
        home[i] = "none (no prior win)" if h < 0 else str(h)
    y = df.yil_v3.astype(int).astype(str)
    il = pd.Series(P["ilc"]).astype(str)
    dims = {"renewal": RA.codes(df.renewal)}
    cells = {"N1": L.cells(df, "N1"), "N3": L.cells(df, "N3"),
             "N4_home_prior": pd.factorize(df.urun_pazari.astype(str) + "|" + y + "|" + home)[0],
             "N4b_prov_home_prior": pd.factorize(df.urun_pazari.astype(str) + "|" + y + "|" + il + "|" + home)[0]}
    ovs, grs = [], []
    el = P["elig"]
    log("N4prior_home", dict(share_no_prior_win_all=float((home == "none (no prior win)").mean()),
                             share_no_prior_win_eligible=float((home[el] == "none (no prior win)").mean()),
                             share_eligible_home_eq_buyer_prov=float((home[el] == il.values[el]).mean())))
    for q, (nm, c) in enumerate(cells.items()):
        ov, gr = RA.null_run(P, c.astype(np.int64), B, SEED + 300 + q, dims)
        nd = pd.Series(P["firm"]).groupby(c).nunique()
        ov["eligible_in_single_winner_cells"] = float((nd.reindex(c).values == 1)[el].mean())
        ovs.append(dict(null=nm, **ov)); gr.insert(0, "null", nm); grs.append(gr)
        print(nm, ov["obs"], ov["null_mean"], flush=True)
    ov = pd.DataFrame(ovs); gr = pd.concat(grs, ignore_index=True)
    ov.to_csv(OUT / "C3_N4prior_overall.csv", index=False)
    gr.to_csv(OUT / "C3_N4prior_by_renewal.csv", index=False)
    return ov, gr


# =====================================================================  task 4
GENERIC_RX = r"lisans|licen|bakim|destek|guncelle|yenile|abonelik|subscription|surum yukselt|upgrade"
BRAND_RX = (r"oracle|microsoft|\bmsdn\b|windows|office 365|\bsql server|\bsap\b|netcad|autodesk|autocad|\besri\b|arcgis|"
            r"adobe|vmware|veeam|kaspersky|\beset\b|symantec|mcafee|trend ?micro|sophos|fortinet|fortigate|cisco|"
            r"citrix|red ?hat|\bibm\b|check ?point|palo alto|\blogo\b|netsis|\bmikro\b|\bspss\b|matlab|solidworks|"
            r"\bhbys\b|\blbys\b|\bybbys\b|\bkbs\b|\bebys\b|probel|enlil|\bmedula\b|\bpacs\b|\bdys\b|kent rehberi|"
            r"\bkeos\b|\bebelediye\b|e-belediye|\buyap\b|imzager|kurumsal lisans|oem|\bzimbra\b|splunk|dell|lenovo")


def fold(s):
    return re.sub(r"[^a-z0-9 ]+", " ", T.tr_lower(s).translate(T.FOLD))


def exclusivity(P):
    df = P["df"]
    t = df.ihale_adi.fillna("").map(fold)
    gen = t.str.contains(GENERIC_RX).values
    brand = t.str.contains(BRAND_RX).values
    strict = gen & brand            # licence/maintenance/support/update of a named or proprietary product
    broad = gen                     # any licence/maintenance/support/update/renewal wording
    df["excl_strict"] = strict
    df["excl_broad"] = broad
    el = P["elig"]
    inc = P["inc"]

    def lab(flag):
        return np.where(el, np.where(flag, "flagged", "remaining") + " / " + df.renewal.values, "not eligible")
    dims = {"excl_strict_x_renewal": RA.codes(lab(strict)), "excl_broad_x_renewal": RA.codes(lab(broad)),
            "excl_strict": RA.codes(np.where(strict, "flagged", "remaining")),
            "excl_broad": RA.codes(np.where(broad, "flagged", "remaining")),
            "procedure_fine": RA.codes(df.usul_v3.astype(str)),
            "procedure_fine_x_renewal": RA.codes(df.usul_v3.astype(str) + " / " + df.renewal)}
    desc = {}
    for nm, f in [("strict", strict), ("broad", broad)]:
        desc[nm] = dict(eligible_flagged=int((f & el).sum()), share_eligible=float(f[el].mean()),
                        share_renewals_flagged=float(f[el & (df.renewal == "renewal").values].mean()),
                        share_newneeds_flagged=float(f[el & (df.renewal == "new need").values].mean()),
                        inc_flagged=float(inc[el & f].mean()), inc_remaining=float(inc[el & ~f].mean()))
    log("T4_exclusivity_desc", desc)
    ovs, grs = [], []
    for q, nm in enumerate(["N1", "N3"]):
        ov, gr = RA.null_run(P, L.cells(df, nm), B, SEED + 400 + q, dims)
        ovs.append(dict(null=nm, **ov)); gr.insert(0, "null", nm); grs.append(gr)
    gr = pd.concat(grs, ignore_index=True)
    gr.to_csv(OUT / "C4_exclusivity_nulls.csv", index=False)
    # examples of flagged titles (strict), for the reader
    ex = df.loc[el & strict, ["IKN", "yil_v3", "urun_pazari", "renewal", "ihale_adi"]]
    ex.to_csv(OUT / "C4_strict_flagged_titles.csv", index=False, encoding="utf-8-sig")
    top = pd.Series([w for s in t[el & strict] for w in set(re.findall(BRAND_RX, s))]).value_counts().head(15)
    log("T4_brand_hits_top", top.to_dict())
    return gr


# =====================================================================  task 5
def cl_logit(formula, data, groups, name):
    m = smf.logit(formula, data).fit(disp=0, maxiter=200, cov_type="cluster",
                                     cov_kwds=dict(groups=pd.factorize(groups)[0]))
    rows = []
    for v in m.params.index:
        if v.startswith("C(yr)") or v == "Intercept":
            continue
        b, s = m.params[v], m.bse[v]
        rows.append(dict(model=name, variable=v, OR=np.exp(b), OR_lo=np.exp(b - 1.96 * s), OR_hi=np.exp(b + 1.96 * s),
                         p=m.pvalues[v], n=int(m.nobs), clusters=int(pd.Series(groups).nunique()),
                         events=int(data[formula.split("~")[0].strip()].sum())))
    return rows


def single_bids(P):
    df = P["df"]
    buyer = df.set_index("IKN").kurum_il_split
    ren = df.set_index("IKN").renewal
    rows, rates = [], []
    # random sample
    D = pd.read_csv(ROOT / "results" / "models" / "D_bid_sample_joined.csv", encoding="utf-8-sig")
    D = D[D.inc_status != "buyer first in market (undefined)"].copy()
    D["buyer"] = D.IKN.map(buyer); D["renewal"] = D.IKN.map(ren)
    assert D.buyer.notna().all() and D.renewal.isin(["renewal", "new need"]).all()
    D["incumbent"] = (D.inc_status == "incumbent winner").astype(int)
    D["renewal_i"] = (D.renewal == "renewal").astype(int)
    D["proc"] = pd.Categorical(np.where(D.proc3 == "21b", "21(b)", np.where(D.proc3 == "open", "open", "other")),
                               ["open", "21(b)", "other"])
    D["yc"] = D.year - 2018
    D["yr"] = D.year.astype(str)
    D["single_total"] = D.single; D["single_valid"] = D.single_valid
    log("T5_random_sample", dict(n=len(D), clusters=int(D.buyer.nunique()),
                                  renewals=int(D.renewal_i.sum()), incumbents=int(D.incumbent.sum()),
                                  valid_missing=int(D.gecerli_teklif.isna().sum())))
    for y in ["single_total", "single_valid"]:
        Dy = D[D[y.replace("single_total", "toplam_teklif").replace("single_valid", "gecerli_teklif")].notna()]
        for nm, f in [("R0 incumbent + procedure + year (linear)", f"{y} ~ incumbent + C(proc) + yc"),
                      ("R1 + renewal", f"{y} ~ incumbent + renewal_i + C(proc) + yc"),
                      ("R2 + renewal, negotiated dummy", f"{y} ~ incumbent + renewal_i + I(proc != 'open') + yc")]:
            try:
                rows += cl_logit(f, Dy, Dy.buyer.values, f"random sample | {y} | {nm}")
            except Exception as ex:
                rows.append(dict(model=f"random sample | {y} | {nm}", variable="FAILED", p=str(ex)[:80]))
        for (r_, i_), s in Dy.groupby(["renewal", "inc_status"]):
            rates.append(dict(sample="random", outcome=y, renewal=r_, inc_status=i_, n=len(s), rate=s[y].mean()))
        for r_, s in Dy.groupby("renewal"):
            rates.append(dict(sample="random", outcome=y, renewal=r_, inc_status="all", n=len(s), rate=s[y].mean()))
    # cp2 (valid bids only)
    J = pd.read_csv(ROOT / "results" / "revision_a" / "F_single_bid_cp2_joined.csv")
    J = J[J.inc_status != "buyer first in market (undefined)"].copy()
    J["buyer"] = J.IKN.map(buyer)
    J["incumbent"] = (J.inc_status == "incumbent winner").astype(int)
    J["renewal_i"] = (J.renewal == "renewal").astype(int)
    J["proc"] = pd.Categorical(L.proc3(J.usul_v3.values), ["open", "21(b)", "other"])
    J["yr"] = J.yil_v3.astype(str)
    for nm, f in [("C0 incumbent + procedure + year FE", "single ~ incumbent + C(proc) + C(yr)"),
                  ("C1 + renewal", "single ~ incumbent + renewal_i + C(proc) + C(yr)"),
                  ("C2 + renewal + incumbent x renewal", "single ~ incumbent * renewal_i + C(proc) + C(yr)")]:
        rows += cl_logit(f, J, J.buyer.values, f"cp2 | single_valid | {nm}")
    for (r_, i_), s in J.groupby(["renewal", "inc_status"]):
        rates.append(dict(sample="cp2", outcome="single_valid", renewal=r_, inc_status=i_, n=len(s), rate=s.single.mean()))
    for r_, s in J.groupby("renewal"):
        rates.append(dict(sample="cp2", outcome="single_valid", renewal=r_, inc_status="all", n=len(s), rate=s.single.mean()))
    log("T5_cp2_corr", dict(n=len(J), P_renewal_given_inc=float(J[J.incumbent == 1].renewal_i.mean()),
                            P_renewal_given_noninc=float(J[J.incumbent == 0].renewal_i.mean()),
                            corr_inc_renewal=float(np.corrcoef(J.incumbent, J.renewal_i)[0, 1])))
    log("T5_random_corr", dict(P_renewal_given_inc=float(D[D.incumbent == 1].renewal_i.mean()),
                               P_renewal_given_noninc=float(D[D.incumbent == 0].renewal_i.mean())))
    R = pd.DataFrame(rows); R.to_csv(OUT / "C5_single_bid_logits.csv", index=False)
    Rt = pd.DataFrame(rates); Rt.to_csv(OUT / "C5_single_bid_rates.csv", index=False)
    return R, Rt


# =====================================================================  task 6
def triple():
    d = contract_history(mload("main"))
    A = d[d.buyer_has_history == 1].copy().reset_index(drop=True)
    A["log_prior_suppliers"] = np.log(A.bm_prior_suppliers)
    A["log_prior_contracts"] = np.log(A.bm_prior_contracts)
    A["years_since_first"] = A.bm_years_since_first
    A["p_21b"] = (A.proc == "21b").astype(float)
    A["p_oth_neg"] = (A.proc == "oth_neg").astype(float)
    A["health"] = (A.sektor_v3_en == "Health").astype(float)
    A["p21b_x_post"] = A.p_21b * A.post7144
    A["p21b_x_health"] = A.p_21b * A.health
    A["post_x_health"] = A.post7144 * A.health
    A["oth_x_health"] = A.p_oth_neg * A.health
    A["p21b_x_post_x_health"] = A.p_21b * A.post7144 * A.health
    A["yearfe"] = A.year.clip(lower=2011)
    core = ["p_21b", "p_oth_neg", "log_real_value", "log_prior_suppliers", "log_prior_contracts", "years_since_first",
            "post7144", "p21b_x_post", "p21b_x_health", "post_x_health", "oth_x_health", "p21b_x_post_x_health"]
    fes = [pd.get_dummies(A[c].astype(str), prefix=c, drop_first=True, dtype=float) for c in ["yearfe", "market", "sektor_v3"]]
    X = sm.add_constant(pd.concat([A[core].astype(float)] + fes, axis=1), has_constant="add")
    cols = list(X.columns)
    out = {}
    res = sm.Logit(A.incumbent_win.values, X.values).fit(disp=0, maxiter=200, method="newton")
    S = np.asarray(res.model.score_obs(res.params)); Hinv = np.linalg.inv(-res.model.hessian(res.params))
    V2, G2, _ = twoway_vcov(S, Hinv, A.buyer.values, A.firm.values)
    V1, _ = oneway_vcov(S, Hinv, A.buyer.values)
    b = res.params
    ix = {c: cols.index(c) for c in core}

    def lin(w, V):
        r = np.zeros(len(b))
        for c, v in w.items():
            r[ix[c]] = v
        e = r @ b; s = np.sqrt(r @ V @ r)
        return dict(coef=e, OR=np.exp(e), lo=np.exp(e - 1.96 * s), hi=np.exp(e + 1.96 * s), p=2 * stats.norm.sf(abs(e / s)))
    for vn, V in [("two-way", V2), ("buyer", V1)]:
        out[f"logit_{vn}"] = dict(
            triple=lin({"p21b_x_post_x_health": 1}, V),
            int_nonhealth=lin({"p21b_x_post": 1}, V),
            int_health=lin({"p21b_x_post": 1, "p21b_x_post_x_health": 1}, V))
    # AME DiD via delta method (two-way V)
    Xv = X.values.astype(float)
    post = A.post7144.values == 1; hl = A.health.values == 1

    def ame(bb, mask):
        Z1, Z0 = Xv[mask].copy(), Xv[mask].copy()
        for Z, v in [(Z1, 1.0), (Z0, 0.0)]:
            Z[:, ix["p_21b"]] = v; Z[:, ix["p_oth_neg"]] = 0; Z[:, ix["oth_x_health"]] = 0
            Z[:, ix["p21b_x_post"]] = v * Z[:, ix["post7144"]]
            Z[:, ix["p21b_x_health"]] = v * A.health.values[mask]
            Z[:, ix["p21b_x_post_x_health"]] = v * Z[:, ix["post7144"]] * A.health.values[mask]
        return np.mean(1 / (1 + np.exp(-Z1 @ bb)) - 1 / (1 + np.exp(-Z0 @ bb)))

    funs = {"health: post-pre change in 21(b)-open AME": lambda bb: ame(bb, post & hl) - ame(bb, ~post & hl),
            "non-health: post-pre change in 21(b)-open AME": lambda bb: ame(bb, post & ~hl) - ame(bb, ~post & ~hl)}
    funs["difference health - non-health"] = lambda bb: funs["health: post-pre change in 21(b)-open AME"](bb) - \
        funs["non-health: post-pre change in 21(b)-open AME"](bb)
    for k, f in funs.items():
        e = f(b); g = np.array([(f(b + 1e-6 * u) - f(b - 1e-6 * u)) / 2e-6 for u in np.eye(len(b))])
        s = np.sqrt(g @ V2 @ g)
        out[f"AME_pp {k}"] = dict(pp=100 * e, lo=100 * (e - 1.96 * s), hi=100 * (e + 1.96 * s), p=2 * stats.norm.sf(abs(e / s)))
    # LPM version
    y = A.incumbent_win.values.astype(float)
    q, r = np.linalg.qr(Xv); ok = np.abs(np.diag(r)) > 1e-8
    Xl = Xv[:, ok]; cl_ = [c for c, o in zip(cols, ok) if o]
    bl = np.linalg.lstsq(Xl, y, rcond=None)[0]
    e_ = y - Xl @ bl
    Vl, _, _ = twoway_vcov(Xl * e_[:, None], np.linalg.inv(Xl.T @ Xl), A.buyer.values, A.firm.values)
    k3 = cl_.index("p21b_x_post_x_health")
    out["LPM_triple_pp"] = dict(pp=100 * bl[k3], lo=100 * (bl[k3] - 1.96 * np.sqrt(Vl[k3, k3])),
                                hi=100 * (bl[k3] + 1.96 * np.sqrt(Vl[k3, k3])),
                                p=2 * stats.norm.sf(abs(bl[k3] / np.sqrt(Vl[k3, k3]))))
    out["N"] = len(A); out["health_n"] = int(A.health.sum())
    out["cells"] = A.groupby(["health", "post7144", "proc"]).incumbent_win.agg(["size", "mean"]).reset_index().to_dict("records")
    log("T6_triple", out)
    return out


# =====================================================================  main
def main():
    P = setup()
    log("sample", dict(contracts=len(P["df"]), eligible=int(P["elig"].sum()),
                       incumbency=float(P["inc"][P["elig"]].mean())))
    cres, H = choice_models(P)
    n4 = n4_prior(P, H)
    ex = exclusivity(P)
    sb = single_bids(P)
    tr = triple()
    json.dump(LOG, open(OUT / "revision_c_log.json", "w", encoding="utf-8"), indent=2, default=str, ensure_ascii=False)


if __name__ == "__main__":
    main()
