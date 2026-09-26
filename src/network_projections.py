"""Statistically validated projections (BiCM, Saracco et al. 2015/2017), disparity-filter backbone on
Newman-weighted projections, firm brokerage vs. size, and shared-vendor coupling among buyers.

BiCM probabilities are obtained with the `bicm` package (v3.4.0, fixed-point/Newton solver). The package's
built-in exact Poisson-binomial projection raises a KeyError on this graph, so V-motif p-values are computed
here directly: exact Poisson-binomial upper tail P(V_ij >= v_ij) (dynamic programming, vectorised over pairs),
with the Poisson approximation reported alongside. Benjamini-Hochberg FDR is applied with
m = N(N-1)/2 (all pairs of the layer; the convention of Saracco et al. and of the bicm package) and,
as a more liberal variant, with m = number of pairs sharing >= 1 neighbour.

Run: python src/network_projections.py
"""
import json
import time

import numpy as np
import pandas as pd
import networkx as nx
import scipy.sparse as sp
from scipy.stats import poisson, spearmanr, pearsonr, t as tdist
import statsmodels.api as sm
from bicm import BipartiteGraph

from network_common import *

SEED = 42
ALPHAS = [0.05, 0.01]
out = {}


# ------------------------------------------------------------------ BiCM
def biadjacency(G):
    F, K = modes(G)
    fi = {n: i for i, n in enumerate(F)}
    ki = {n: i for i, n in enumerate(K)}
    B = np.zeros((len(F), len(K)), dtype=np.uint8)
    for u, v in G.edges():
        f, k = (u, v) if u[0] == "F" else (v, u)
        B[fi[f], ki[k]] = 1
    return F, K, B


def solve_bicm(B):
    bg = BipartiteGraph(biadjacency=B)
    bg.solve_tool(verbose=False, print_error=False)
    P = bg.get_bicm_matrix()
    err_r = np.abs(P.sum(1) - B.sum(1)).max()
    err_c = np.abs(P.sum(0) - B.sum(0)).max()
    return P, float(err_r), float(err_c)


def pb_upper_tail(Q, v, batch=4000):
    """Exact Poisson-binomial P(V >= v) for each row of Q (pairs x opposite layer), v >= 1."""
    out = np.empty(len(v))
    for s in range(0, len(v), batch):
        q = Q[s:s + batch]
        vv = v[s:s + batch]
        S = int(vv.max())  # states 0..S-1 needed for P(V <= v-1)
        dist = np.zeros((len(q), S))
        dist[:, 0] = 1.0
        for k in range(q.shape[1]):
            p = q[:, k:k + 1]
            nd = dist * (1 - p)
            nd[:, 1:] += dist[:, :-1] * p
            dist = nd
        cdf = np.cumsum(dist, axis=1)
        below = cdf[np.arange(len(q)), vv - 1]
        out[s:s + batch] = np.clip(1.0 - below, 0.0, 1.0)
    return out


def vmotif_pvals(B, P, layer):
    """layer='rows' (firms) or 'cols' (buyers). Returns DataFrame i, j, V, mu, p_pb, p_pois."""
    if layer == "cols":
        B, P = B.T, P.T
    Bs = sp.csr_matrix(B.astype(np.int32))
    V = sp.triu(Bs @ Bs.T, k=1).tocoo()
    i, j, v = V.row, V.col, V.data.astype(int)
    pv_pb = np.empty(len(i))
    mu = np.empty(len(i))
    bs = 3000
    for s in range(0, len(i), bs):
        Q = P[i[s:s + bs]] * P[j[s:s + bs]]
        mu[s:s + bs] = Q.sum(1)
        pv_pb[s:s + bs] = pb_upper_tail(Q, v[s:s + bs])
    pv_pois = poisson.sf(v - 1, mu)
    return pd.DataFrame(dict(i=i, j=j, V=v, mu=mu, p_pb=pv_pb, p_pois=pv_pois))


def bh_reject(p, alpha, m):
    p = np.asarray(p)
    o = np.argsort(p)
    ranks = np.arange(1, len(p) + 1)
    ok = p[o] <= ranks * alpha / m
    rej = np.zeros(len(p), bool)
    if ok.any():
        r = np.where(ok)[0].max()
        rej[o[: r + 1]] = True
    return rej


# ------------------------------------------------------------------ Newman + disparity
def newman_projection(B, layer):
    """w_ij = sum_k 1/(d_k - 1) over shared neighbours k with d_k > 1 (Newman 2001)."""
    if layer == "cols":
        B = B.T
    d = B.sum(0).astype(float)
    inv = np.where(d > 1, 1.0 / np.maximum(d - 1, 1), 0.0)
    Bs = sp.csr_matrix(B.astype(float))
    W = (Bs @ sp.diags(inv) @ Bs.T).tolil()
    W.setdiag(0)
    W = sp.triu(W.tocsr(), k=1).tocoo()
    m = W.data > 0
    return pd.DataFrame(dict(i=W.row[m], j=W.col[m], w=W.data[m]))


def disparity(E, n, alpha):
    """Serrano et al. (2009) disparity filter; edge kept if significant for at least one endpoint.
    For a degree-1 endpoint alpha_ij = 1 (edge judged by the other endpoint)."""
    s = np.bincount(E.i, E.w, n) + np.bincount(E.j, E.w, n)
    k = np.bincount(E.i, minlength=n) + np.bincount(E.j, minlength=n)
    a_i = np.where(k[E.i] > 1, (1 - E.w / s[E.i]) ** (k[E.i] - 1), 1.0)
    a_j = np.where(k[E.j] > 1, (1 - E.w / s[E.j]) ** (k[E.j] - 1), 1.0)
    return np.minimum(a_i, a_j) < alpha


# ------------------------------------------------------------------ projection summaries
def to_graph(names, E, weight=None):
    H = nx.Graph()
    for a, b, *w in E:
        if weight is None:
            H.add_edge(names[a], names[b])
        else:
            H.add_edge(names[a], names[b], weight=w[0])
    return H


def summarize(H, layer_size, label):
    if H.number_of_nodes() == 0:
        return dict(projection=label, nodes=0, share_of_layer=0, edges=0, components=0, gc_nodes=0,
                    gc_share_of_layer=0, gc_share_of_projection=np.nan, Q=np.nan, n_comms=0, Q_weighted=np.nan,
                    density=np.nan, mean_degree=np.nan)
    cc = sorted(nx.connected_components(H), key=len, reverse=True)
    comms, Q = louvain(H, SEED, weight=None)
    r = dict(projection=label, nodes=H.number_of_nodes(), share_of_layer=H.number_of_nodes() / layer_size,
             edges=H.number_of_edges(), components=len(cc), gc_nodes=len(cc[0]),
             gc_share_of_layer=len(cc[0]) / layer_size, gc_share_of_projection=len(cc[0]) / H.number_of_nodes(),
             Q=Q if H.number_of_edges() else np.nan, n_comms=len(comms), density=nx.density(H),
             mean_degree=2 * H.number_of_edges() / H.number_of_nodes(), Q_weighted=np.nan)
    if nx.get_edge_attributes(H, "weight"):
        r["Q_weighted"] = louvain(H, SEED)[1]
    return r


def jaccard(E1, E2):
    a = set(map(tuple, E1)); b = set(map(tuple, E2))
    return len(a & b) / len(a | b) if a | b else np.nan, len(a & b)


def all_projections(G, tag):
    F, K, B = biadjacency(G)
    t0 = time.time()
    P, er, ec = solve_bicm(B)
    out[f"{tag}_bicm_max_degree_error"] = dict(rows=er, cols=ec)
    rows, graphs, pvals = [], {}, {}
    for layer, names in [("rows", F), ("cols", K)]:
        lname = "firm" if layer == "rows" else "buyer"
        n = len(names)
        m_all = n * (n - 1) / 2
        pv = vmotif_pvals(B, P, layer)
        pvals[lname] = pv
        out[f"{tag}_{lname}_pairs"] = dict(n_nodes=n, m_all=m_all, pairs_with_V=len(pv), min_p_pb=pv.p_pb.min(),
                                           min_p_pois=pv.p_pois.min(), n_p_pb_lt_1e6=int((pv.p_pb < 1e-6).sum()),
                                           n_p_pb_lt_1e4=int((pv.p_pb < 1e-4).sum()),
                                           bh_threshold_first_rank_all=0.05 / m_all,
                                           share_pairs_V1=float((pv.V == 1).mean()), max_V=int(pv.V.max()))
        # raw projection (any shared neighbour) and Newman weights
        NE = newman_projection(B, layer)
        Hraw = to_graph(names, NE[["i", "j", "w"]].itertuples(index=False), weight=True)
        rows.append(summarize(Hraw, n, f"{lname}_raw"))
        graphs[f"{lname}_raw"] = Hraw
        for a in ALPHAS:
            for mname, m in [("mall", m_all), ("mobs", len(pv))]:
                for pcol in ["p_pb", "p_pois"]:
                    rej = bh_reject(pv[pcol].values, a, m)
                    E = pv.loc[rej, ["i", "j"]].values
                    H = to_graph(names, E)
                    lab = f"{lname}_bicm_{pcol[2:]}_{mname}_fdr{a}"
                    r = summarize(H, n, lab)
                    r["validated_pairs"] = int(rej.sum())
                    rows.append(r)
                    graphs[lab] = H
            keep = disparity(NE, n, a)
            Hd = to_graph(names, NE.loc[keep, ["i", "j", "w"]].itertuples(index=False), weight=True)
            rd = summarize(Hd, n, f"{lname}_disparity_a{a}")
            # overlap with BiCM (exact PB, liberal m) validated set
            rej = bh_reject(pv.p_pb.values, a, len(pv))
            jac, inter = jaccard(NE.loc[keep, ["i", "j"]].values, pv.loc[rej, ["i", "j"]].values)
            rd.update(jaccard_vs_bicm_pb_mobs=jac, n_shared_edges_vs_bicm=inter)
            rows.append(rd)
            graphs[f"{lname}_disparity_a{a}"] = Hd
    out[f"{tag}_projection_seconds"] = time.time() - t0
    return pd.DataFrame(rows), graphs, pvals, (F, K, B, P)


# ------------------------------------------------------------------ brokerage
def participation(H, comms):
    cd = comm_dict(comms)
    pc = {}
    for n in H:
        k = H.degree(n)
        if k == 0:
            pc[n] = np.nan
            continue
        cnt = {}
        for nb in H[n]:
            cnt[cd[nb]] = cnt.get(cd[nb], 0) + 1
        pc[n] = 1 - sum((c / k) ** 2 for c in cnt.values())
    return pc


def partial_spearman(df, x, y, controls):
    R = df[[x, y] + controls].rank()
    Z = sm.add_constant(R[controls])
    rx = sm.OLS(R[x], Z).fit().resid
    ry = sm.OLS(R[y], Z).fit().resid
    r = pearsonr(rx, ry)[0]
    n = len(df)
    dfree = n - 2 - len(controls)
    tt = r * np.sqrt(dfree / (1 - r**2))
    p = 2 * tdist.sf(abs(tt), dfree)
    return r, p


def brokerage(H, m, label, rng, n_boot=1000):
    firms = [n for n in H]
    names = [n[1] for n in firms]
    bt = nx.betweenness_centrality(H, normalized=True)
    comms, _ = louvain(H, SEED, weight=None)
    pc = participation(H, comms)
    g = m.groupby("firma_v3")
    df = pd.DataFrame(dict(firm=names, betweenness=[bt[n] for n in firms], participation=[pc[n] for n in firms],
                           proj_degree=[H.degree(n) for n in firms]))
    df["n_markets"] = df.firm.map(g.urun_pazari.nunique())
    df["n_buyers"] = df.firm.map(g.kurum_il_split.nunique())
    df["n_contracts"] = df.firm.map(g.size())
    df["log_buyers"] = np.log(df.n_buyers)
    df["log_contracts"] = np.log(df.n_contracts)
    res = dict(projection=label, n_firms=len(df), share_btw_pos=float((df.betweenness > 0).mean()))
    ctrl = ["n_buyers", "n_contracts"]
    for y in ["betweenness", "participation"]:
        res[f"spearman_{y}_markets"] = spearmanr(df[y], df.n_markets)[0]
        res[f"spearman_{y}_buyers"] = spearmanr(df[y], df.n_buyers)[0]
        res[f"spearman_{y}_contracts"] = spearmanr(df[y], df.n_contracts)[0]
        r, p = partial_spearman(df, y, "n_markets", ctrl)
        res[f"partial_spearman_{y}_markets"] = r
        res[f"partial_spearman_{y}_markets_p"] = p
        bs = []
        for _ in range(n_boot):
            s = df.sample(len(df), replace=True, random_state=int(rng.integers(1e9)))
            bs.append(partial_spearman(s, y, "n_markets", ctrl)[0])
        res[f"partial_spearman_{y}_markets_ci"] = (np.quantile(bs, .025), np.quantile(bs, .975))
    # also: partial correlation of markets with projection degree
    res["spearman_markets_buyers"] = spearmanr(df.n_markets, df.n_buyers)[0]
    # regressions
    eps = df.betweenness[df.betweenness > 0].min() / 2 if (df.betweenness > 0).any() else 1e-9
    df["log_btw"] = np.log(df.betweenness + eps)
    X0 = sm.add_constant(df[["log_buyers", "log_contracts"]])
    X1 = sm.add_constant(df[["n_markets", "log_buyers", "log_contracts"]])
    m0 = sm.OLS(df.log_btw, X0).fit(cov_type="HC3")
    m1 = sm.OLS(df.log_btw, X1).fit(cov_type="HC3")
    res.update(ols_eps=eps, ols_n=int(m1.nobs), ols_r2_size=m0.rsquared, ols_r2_full=m1.rsquared,
               ols_b_markets=m1.params["n_markets"], ols_se_markets=m1.bse["n_markets"],
               ols_p_markets=m1.pvalues["n_markets"],
               ols_ci_markets=tuple(m1.conf_int().loc["n_markets"]),
               ols_b_logbuyers=m1.params["log_buyers"], ols_p_logbuyers=m1.pvalues["log_buyers"],
               ols_b_logcontracts=m1.params["log_contracts"], ols_p_logcontracts=m1.pvalues["log_contracts"])
    R = df[["betweenness", "n_markets", "n_buyers", "n_contracts"]].rank() / len(df)
    r0 = sm.OLS(R.betweenness, sm.add_constant(R[["n_buyers", "n_contracts"]])).fit(cov_type="HC3")
    r1 = sm.OLS(R.betweenness, sm.add_constant(R[["n_markets", "n_buyers", "n_contracts"]])).fit(cov_type="HC3")
    res.update(rank_r2_size=r0.rsquared, rank_r2_full=r1.rsquared, rank_b_markets=r1.params["n_markets"],
               rank_p_markets=r1.pvalues["n_markets"], rank_b_buyers=r1.params["n_buyers"],
               rank_b_contracts=r1.params["n_contracts"])
    # hurdle: any betweenness
    y = (df.betweenness > 0).astype(int)
    if 0 < y.mean() < 1:
        try:
            lg = sm.Logit(y, X1).fit(disp=0, cov_type="HC3")
            res.update(logit_b_markets=lg.params["n_markets"], logit_p_markets=lg.pvalues["n_markets"],
                       logit_b_logbuyers=lg.params["log_buyers"], logit_p_logbuyers=lg.pvalues["log_buyers"])
        except Exception as e:  # separation etc.
            res["logit_error"] = str(e)
    # top brokers
    df = df.sort_values("betweenness", ascending=False)
    res["top10"] = df.head(10)[["firm", "betweenness", "participation", "n_markets", "n_buyers", "n_contracts"]].to_dict("records")
    return res, df


# ------------------------------------------------------------------ buyer coupling
def buyer_coupling(H, m, buyer_col, label, top=10):
    if H.number_of_nodes() == 0:
        return dict(projection=label, empty=True), pd.DataFrame()
    gc = max(nx.connected_components(H), key=len)
    sec = m.groupby(buyer_col).sektor_v3_en.first()
    bdeg = m.groupby(buyer_col).firma_v3.nunique()
    nct = m.groupby(buyer_col).size()
    tb = sorted(H.degree(), key=lambda x: -x[1])[:top]
    rows = [dict(projection=label, rank=i + 1, buyer=n[1], sector=sec[n[1]], proj_degree=k,
                 share_of_projection_linked=k / (H.number_of_nodes() - 1),
                 share_of_gc_linked=(len(set(H[n]) & gc) / (len(gc) - 1)) if n in gc else 0.0,
                 in_gc=n in gc, bip_degree_firms=int(bdeg[n[1]]), contracts=int(nct[n[1]]))
            for i, (n, k) in enumerate(tb)]
    top1 = tb[0][0]
    # share of GC within distance 1 of the top-3 buyers jointly
    t3 = set()
    for n, _ in tb[:3]:
        t3 |= set(H[n]) | {n}
    summ = dict(projection=label, nodes=H.number_of_nodes(), gc_nodes=len(gc), top_buyer=top1[1],
                top_sector=sec[top1[1]], top_degree=tb[0][1],
                top_share_of_gc_linked=len(set(H[top1]) & gc) / (len(gc) - 1) if top1 in gc else 0.0,
                top3_share_of_gc_covered=len(t3 & gc) / len(gc),
                top_share_of_projection_linked=tb[0][1] / (H.number_of_nodes() - 1))
    return summ, pd.DataFrame(rows)


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    d = load_master()
    m = sample(d, "main")
    G = build_bipartite(m)
    summ, graphs, pvals, (F, K, B, P) = all_projections(G, "main")
    summ.to_csv(RES / "projections_summary.csv", index=False)
    for lname, names in [("firm", F), ("buyer", K)]:
        pv = pvals[lname].copy()
        pv["node_i"] = [names[i][1] for i in pv.i]
        pv["node_j"] = [names[j][1] for j in pv.j]
        pv.sort_values("p_pb").to_csv(RES / f"bicm_vmotif_pvalues_{lname}.csv", index=False)
    print("projections done", time.time() - t0)

    # ---------------- brokerage on each firm projection that is non-trivial
    brk, tops = [], []
    for lab in ["firm_bicm_pb_mall_fdr0.05", "firm_bicm_pb_mobs_fdr0.05", "firm_disparity_a0.05",
                "firm_disparity_a0.01", "firm_raw"]:
        H = graphs[lab]
        if H.number_of_nodes() < 30:
            brk.append(dict(projection=lab, n_firms=H.number_of_nodes(), note="too small for brokerage analysis"))
            continue
        r, df = brokerage(H, m, lab, rng)
        df.insert(0, "projection", lab)
        tops.append(df)
        brk.append(r)
        print("brokerage", lab, time.time() - t0)
    pd.DataFrame(brk).to_csv(RES / "brokerage_summary.csv", index=False)
    pd.concat(tops).to_csv(RES / "brokerage_firm_table.csv", index=False)
    out["brokerage"] = brk

    # ---------------- buyer coupling (province split) + recorded kurum sensitivity
    cs, ct = [], []
    for lab in ["buyer_raw", "buyer_bicm_pb_mall_fdr0.05", "buyer_bicm_pb_mobs_fdr0.05", "buyer_disparity_a0.05"]:
        s, t = buyer_coupling(graphs[lab], m, "kurum_il_split", "kurum_il_split:" + lab)
        cs.append(s); ct.append(t)
    Gk = build_bipartite(m, "firma_v3", "kurum")
    summ_k, graphs_k, _, _ = all_projections(Gk, "recorded_kurum")
    summ_k.to_csv(RES / "projections_summary_recorded_kurum.csv", index=False)
    for lab in ["buyer_raw", "buyer_bicm_pb_mall_fdr0.05", "buyer_bicm_pb_mobs_fdr0.05", "buyer_disparity_a0.05"]:
        s, t = buyer_coupling(graphs_k[lab], m, "kurum", "kurum:" + lab)
        cs.append(s); ct.append(t)
    pd.DataFrame(cs).to_csv(RES / "buyer_coupling_summary.csv", index=False)
    pd.concat(ct).to_csv(RES / "buyer_coupling_top_buyers.csv", index=False)

    # save validated / backbone edge lists for figures & reuse
    for lab in ["firm_bicm_pb_mobs_fdr0.05", "buyer_bicm_pb_mobs_fdr0.05", "firm_disparity_a0.05"]:
        H = graphs[lab]
        pd.DataFrame([(u[1], v[1], dd.get("weight", 1)) for u, v, dd in H.edges(data=True)],
                     columns=["u", "v", "w"]).to_csv(RES / f"edges_{lab}.csv", index=False)
    out["runtime_s"] = time.time() - t0
    with open(RES / "network_projections.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))


if __name__ == "__main__":
    main()
