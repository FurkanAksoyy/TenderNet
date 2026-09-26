# -*- coding: utf-8 -*-
"""Feature construction for the `models` topic (no look-ahead: only strictly earlier dates)."""
import numpy as np
import pandas as pd


def contract_history(d):
    """Per contract: history of buyer k in market m strictly before the contract date."""
    d = d.copy()
    out = {c: np.full(len(d), np.nan) for c in
           ["bm_prior_contracts", "bm_prior_suppliers", "bm_years_since_first", "incumbent_win"]}
    for (k, m), g in d.groupby(["buyer", "market"], sort=False):
        g = g.sort_values(["date", "IKN"])
        dates = g.date.values
        firms = g.firm.values
        first = dates[0]
        for pos, idx in enumerate(g.index):
            prior = dates < dates[pos]
            n = int(prior.sum())
            out["bm_prior_contracts"][idx] = n
            if n:
                pf = set(firms[prior])
                out["bm_prior_suppliers"][idx] = len(pf)
                out["bm_years_since_first"][idx] = (dates[pos] - first) / np.timedelta64(1, "D") / 365.25
                out["incumbent_win"][idx] = float(firms[pos] in pf)
            else:
                out["bm_prior_suppliers"][idx] = 0
    for c, v in out.items():
        d[c] = v
    # repeat contract of the dyad (f,k,m): firm had won from k in m on a strictly earlier date
    d["dyad_repeat"] = d.incumbent_win.fillna(0).astype(int)
    d["buyer_has_history"] = (d.bm_prior_contracts > 0).astype(int)
    return d


def dyad_table(d):
    """One row per dyad (f,k,m) at its first contract, with t0 covariates and later outcomes."""
    d = d.sort_values(["date", "IKN"]).reset_index(drop=True)
    first = d.groupby(["firm", "buyer", "market"], sort=False).head(1).copy()
    # later contracts within dyad (strictly after t0)
    t0 = first.set_index(["firm", "buyer", "market"]).date
    dd = d.join(t0.rename("t0"), on=["firm", "buyer", "market"])
    later = dd[dd.date > dd.t0].groupby(["firm", "buyer", "market"]).size()
    first = first.join(later.rename("later_n"), on=["firm", "buyer", "market"])
    first["later_n"] = first.later_n.fillna(0).astype(int)
    first["later_any"] = (first.later_n > 0).astype(int)
    # opportunities: contracts by buyer k in market m strictly after t0
    bm = {key: g.date.values for key, g in d.groupby(["buyer", "market"])}
    first["opportunities"] = [int((bm[(k, m)] > t).sum()) for k, m, t in
                              zip(first.buyer, first.market, first.date)]
    # firm history strictly before t0
    fg = {f: g for f, g in d.groupby("firm")}
    bg = {b: g.date.values for b, g in d.groupby("buyer")}
    pc, pm, pb, pck = [], [], [], []
    for f, k, t in zip(first.firm, first.buyer, first.date):
        g = fg[f]
        pr = g[g.date < t]
        pr_ex = pr[pr.buyer != k]
        pc.append(len(pr_ex))
        pm.append(pr.market.nunique())
        pb.append(pr_ex.buyer.nunique())
        pck.append(int((bg[k] < t).sum()))
    first["firm_prior_contracts_exbuyer"] = pc
    first["firm_prior_markets"] = pm
    first["firm_prior_buyers_exbuyer"] = pb
    first["buyer_prior_contracts"] = pck
    return first.reset_index(drop=True)
