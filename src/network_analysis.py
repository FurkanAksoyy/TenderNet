"""Bipartite firm-buyer network: descriptives, communities, nulls, validation, annual snapshots,
sensitivity. Projections/backbone/brokerage are in network_projections.py.

Run: python src/network_analysis.py
Outputs: results/network/*.csv, network_core.json
"""
import json
import time

import numpy as np
import pandas as pd
import networkx as nx
import powerlaw
from sklearn.metrics import normalized_mutual_info_score as NMI, adjusted_rand_score as ARI, \
    adjusted_mutual_info_score as AMI

from network_common import *

RES.mkdir(parents=True, exist_ok=True)
SEED = 42
N_NULL = 200            # main null reps
N_NULL_YEAR = 100       # per-year null reps
N_NULL_SENS = 100       # sensitivity null reps
N_STAB = 50             # stability runs
N_GOF = 500             # power-law GOF bootstrap reps
TRADES = 50             # curveball trades per firm row
out = {}


def descriptives(G):
    F, K = modes(G)
    E = G.number_of_edges()
    W = G.size(weight="weight")
    Gc = giant(G)
    Fc, Kc = modes(Gc)
    r_p, r_s = bip_assortativity(G)
    return dict(
        n_firms=len(F), n_buyers=len(K), n_edges=E, n_contracts=int(W),
        density=E / (len(F) * len(K)),
        n_components=nx.number_connected_components(G),
        gc_nodes=Gc.number_of_nodes(), gc_share_nodes=Gc.number_of_nodes() / G.number_of_nodes(),
        gc_firms=len(Fc), gc_buyers=len(Kc), gc_share_firms=len(Fc) / len(F), gc_share_buyers=len(Kc) / len(K),
        gc_edges=Gc.number_of_edges(), gc_share_contracts=Gc.size(weight="weight") / W,
        mean_deg_firm=np.mean([G.degree(n) for n in F]), mean_deg_buyer=np.mean([G.degree(n) for n in K]),
        max_deg_firm=max(G.degree(n) for n in F), max_deg_buyer=max(G.degree(n) for n in K),
        share_deg1_firm=np.mean([G.degree(n) == 1 for n in F]), share_deg1_buyer=np.mean([G.degree(n) == 1 for n in K]),
        share_deg1_all=np.mean([G.degree(n) == 1 for n in G]),
        mean_w=W / E, max_w=max(d["weight"] for *_, d in G.edges(data=True)),
        share_edges_w_gt1=np.mean([d["weight"] > 1 for *_, d in G.edges(data=True)]),
        assort_pearson=r_p, assort_spearman=r_s,
        nx_degree_assortativity=nx.degree_assortativity_coefficient(G),
        robins_alexander=robins_alexander(G),
    )


def gof_bootstrap(deg, fit, rng, reps):
    """Clauset-Shalizi-Newman semi-parametric bootstrap GOF p-value for the discrete power law."""
    deg = np.asarray(deg)
    xmin = fit.power_law.xmin
    body = deg[deg < xmin]
    n = len(deg)
    ntail = int((deg >= xmin).sum())
    D0 = fit.power_law.D
    alpha = fit.power_law.alpha
    ge = 0
    # discrete power-law sampler via inverse CDF over support xmin..xmax_big
    support = np.arange(xmin, 100000)
    from scipy.special import zeta
    pmf = support.astype(float) ** (-alpha) / zeta(alpha, xmin)
    cdf = np.cumsum(pmf)
    for _ in range(reps):
        nt = rng.binomial(n, ntail / n)
        tail = support[np.minimum(np.searchsorted(cdf, rng.random(nt) * cdf[-1]), len(support) - 1)]
        b = rng.choice(body, n - nt, replace=True) if len(body) and n - nt > 0 else np.array([], int)
        s = np.concatenate([b, tail])
        f = powerlaw.Fit(s, discrete=True, verbose=False)
        if f.power_law.D >= D0:
            ge += 1
    return ge / reps


def powerlaw_block(G, rng):
    F, K = modes(G)
    rows = []
    for mode, nodes in [("firm", F), ("buyer", K)]:
        deg = np.array([G.degree(n) for n in nodes])
        fit = powerlaw.Fit(deg, discrete=True, verbose=False)
        r = dict(mode=mode, n=len(deg), alpha=fit.power_law.alpha, alpha_se=fit.power_law.sigma,
                 xmin=fit.power_law.xmin, n_tail=int((deg >= fit.power_law.xmin).sum()), KS_D=fit.power_law.D)
        for alt in ["lognormal", "exponential", "truncated_power_law", "stretched_exponential"]:
            R, p = fit.distribution_compare("power_law", alt, normalized_ratio=True)
            r[f"LR_vs_{alt}"] = R
            r[f"p_vs_{alt}"] = p
        r["lognormal_mu"] = fit.lognormal.mu
        r["lognormal_sigma"] = fit.lognormal.sigma
        r["tpl_lambda"] = fit.truncated_power_law.parameter2
        r["gof_p_bootstrap"] = gof_bootstrap(deg, fit, rng, N_GOF)
        r["gof_reps"] = N_GOF
        # fixed xmin=1 fit for reference
        f1 = powerlaw.Fit(deg, discrete=True, xmin=1, verbose=False)
        r["alpha_xmin1"] = f1.power_law.alpha
        R1, p1 = f1.distribution_compare("power_law", "lognormal", normalized_ratio=True)
        r["LR_vs_lognormal_xmin1"], r["p_vs_lognormal_xmin1"] = R1, p1
        rows.append(r)
    return pd.DataFrame(rows)


def label_validation(Gc, part, m, buyer_col, firm_col, rng, nperm=500):
    sec = m.groupby(buyer_col).sektor_v3_en.first()
    mk = modal_label(m, firm_col, "urun_pazari")
    rows = []
    for mode, lab in [("buyer_sector", sec), ("firm_modal_market", mk)]:
        pref = "K" if mode.startswith("buyer") else "F"
        nodes = [n for n in Gc if n[0] == pref]
        c = np.array([part[n] for n in nodes])
        y = np.array([lab[n[1]] for n in nodes])
        nmi, ari, ami = NMI(y, c), ARI(y, c), AMI(y, c)
        perm = [NMI(rng.permutation(y), c) for _ in range(nperm)]
        # purity: share of nodes whose label equals their community's modal label
        t = pd.DataFrame(dict(c=c, y=y))
        pur = t.groupby("c").y.agg(lambda s: s.value_counts().iloc[0]).sum() / len(t)
        rows.append(dict(mode=mode, n_nodes=len(nodes), n_labels=len(set(y)), n_comms=len(set(c)),
                         NMI=nmi, AMI=ami, ARI=ari, NMI_perm_mean=np.mean(perm),
                         NMI_perm_95=np.quantile(perm, 0.95), purity=pur,
                         purity_baseline_largest_label=pd.Series(y).value_counts().iloc[0] / len(y)))
    return pd.DataFrame(rows)


def core_run(m, firm_col, buyer_col, rng, n_null, tag, full_detail=False):
    G = build_bipartite(m, firm_col, buyer_col)
    deg = dict(G.degree())
    desc = descriptives(G)
    Gc = giant(G)
    comms_w, Qw_gc = louvain(Gc, SEED)
    comms_b, Qb_gc = louvain(Gc, SEED, weight=None)
    part = comm_dict(comms_w)
    _, Qw_full = louvain(G, SEED)
    comms_bf, Qb_full = louvain(G, SEED, weight=None)
    res = dict(desc)
    res.update(Q_gc_weighted=Qw_gc, Q_gc_binary=Qb_gc, Q_full_weighted=Qw_full, Q_full_binary=Qb_full,
               barber_gc_weighted=barber_Q(Gc, part), barber_gc_binary=barber_Q(Gc, comm_dict(comms_b), None),
               n_comms_gc_weighted=len(comms_w), n_comms_gc_binary=len(comms_b))
    # --- null
    nulls = []
    t0 = time.time()
    for r in range(n_null):
        H, ov = curveball(G, rng, TRADES)
        assert_bipartite(H, deg)
        Hw = shuffle_weights(G, H, rng)
        Hc = giant(H)
        Hwc = Hw.subgraph(Hc.nodes()).copy()
        cb, qb = louvain(H, SEED + r + 1, weight=None)
        cbg, qbg = louvain(Hc, SEED + r + 1, weight=None)
        cwg, qwg = louvain(Hwc, SEED + r + 1)
        _, qwf = louvain(Hw, SEED + r + 1)
        row = dict(rep=r, overlap=ov, Q_full_binary=qb, Q_gc_binary=qbg, Q_gc_weighted=qwg, Q_full_weighted=qwf,
                   barber_gc_binary=barber_Q(Hc, comm_dict(cbg), None), barber_gc_weighted=barber_Q(Hwc, comm_dict(cwg)),
                   gc_share_nodes=Hc.number_of_nodes() / H.number_of_nodes(), n_comms_gc_binary=len(cbg))
        if full_detail:
            rp, rs = bip_assortativity(H)
            row.update(assort_pearson=rp, assort_spearman=rs, robins_alexander=robins_alexander(H))
            lf, lk, la = latapy_means(H)
            row.update(latapy_firm=lf, latapy_buyer=lk, latapy_all=la)
        nulls.append(row)
    nulls = pd.DataFrame(nulls)
    res["null_reps"] = n_null
    res["null_seconds"] = time.time() - t0
    res["null_mean_edge_overlap"] = nulls.overlap.mean()
    for k in ["Q_full_binary", "Q_gc_binary", "Q_gc_weighted", "Q_full_weighted", "barber_gc_binary",
              "barber_gc_weighted"]:
        mu, sd = nulls[k].mean(), nulls[k].std(ddof=1)
        res[f"null_{k}_mean"] = mu
        res[f"null_{k}_sd"] = sd
        res[f"null_{k}_q025"] = nulls[k].quantile(0.025)
        res[f"null_{k}_q975"] = nulls[k].quantile(0.975)
        res[f"z_{k}"] = (res[k] - mu) / sd
        res[f"p_emp_{k}"] = (1 + (nulls[k] >= res[k]).sum()) / (n_null + 1)
    res["null_gc_share_nodes_mean"] = nulls.gc_share_nodes.mean()
    val = label_validation(Gc, part, m, buyer_col, firm_col, rng, nperm=200)
    for _, v in val.iterrows():
        for k in ["NMI", "AMI", "ARI", "NMI_perm_mean", "purity"]:
            res[f"{v['mode']}_{k}"] = v[k]
    res["tag"] = tag
    return res, G, Gc, comms_w, nulls, val


def stability(Gc, rng):
    runs = []
    parts = []
    nodes = sorted(Gc.nodes())
    for r in range(N_STAB):
        H = permuted_copy(Gc, rng)
        seed = int(rng.integers(0, 2**31 - 1))
        c, Q = louvain(H, seed)
        pd_ = comm_dict(c)
        parts.append(np.array([pd_[n] for n in nodes]))
        sizes = sorted(map(len, c), reverse=True)
        runs.append(dict(run=r, seed=seed, Q=Q, n_comms=len(c), largest=sizes[0],
                         n_comms_ge10=sum(s >= 10 for s in sizes),
                         barber=barber_Q(H, pd_)))
    runs = pd.DataFrame(runs)
    nm, ar = [], []
    for i in range(N_STAB):
        for j in range(i + 1, N_STAB):
            nm.append(NMI(parts[i], parts[j]))
            ar.append(ARI(parts[i], parts[j]))
    return runs, np.array(nm), np.array(ar)


def annual(m, firm_col, buyer_col, rng):
    rows = []
    parts = {}
    for y in sorted(m.yil_v3.unique()):
        my = m[m.yil_v3 == y]
        G = build_bipartite(my, firm_col, buyer_col)
        deg = dict(G.degree())
        Gc = giant(G)
        c, Qb = louvain(G, SEED, weight=None)
        cw, Qw = louvain(G, SEED)
        cg, Qbg = louvain(Gc, SEED, weight=None)
        parts[y] = comm_dict(c)
        nb, nbg = [], []
        for r in range(N_NULL_YEAR):
            H, _ = curveball(G, rng, TRADES)
            assert_bipartite(H, deg)
            nb.append(louvain(H, SEED + r + 1, weight=None)[1])
            nbg.append(louvain(giant(H), SEED + r + 1, weight=None)[1])
        nb, nbg = np.array(nb), np.array(nbg)
        F, K = modes(G)
        rows.append(dict(year=int(y), contracts=len(my), firms=len(F), buyers=len(K), edges=G.number_of_edges(),
                         gc_share=Gc.number_of_nodes() / G.number_of_nodes(), n_components=nx.number_connected_components(G),
                         Q_full_binary=Qb, Q_full_weighted=Qw, n_comms=len(c),
                         null_mean=nb.mean(), null_sd=nb.std(ddof=1), null_q975=np.quantile(nb, 0.975),
                         z=(Qb - nb.mean()) / nb.std(ddof=1), p_emp=(1 + (nb >= Qb).sum()) / (len(nb) + 1),
                         Q_gc_binary=Qbg, null_gc_mean=nbg.mean(), null_gc_sd=nbg.std(ddof=1),
                         z_gc=(Qbg - nbg.mean()) / nbg.std(ddof=1), p_emp_gc=(1 + (nbg >= Qbg).sum()) / (len(nbg) + 1),
                         null_reps=N_NULL_YEAR))
    ann = pd.DataFrame(rows)
    cons = []
    years = sorted(parts)
    for a, b in zip(years[:-1], years[1:]):
        common = sorted(set(parts[a]) & set(parts[b]))
        if len(common) < 5:
            continue
        x = np.array([parts[a][n] for n in common])
        y = np.array([parts[b][n] for n in common])
        perm = [NMI(x, rng.permutation(y)) for _ in range(200)]
        cons.append(dict(year_a=int(a), year_b=int(b), n_persistent=len(common),
                         n_persistent_firms=sum(n[0] == "F" for n in common),
                         n_persistent_buyers=sum(n[0] == "K" for n in common),
                         NMI=NMI(x, y), AMI=AMI(x, y), ARI=ARI(x, y), NMI_perm_mean=np.mean(perm),
                         NMI_perm_q975=np.quantile(perm, 0.975)))
    return ann, pd.DataFrame(cons)


def community_table(Gc, comms, m, buyer_col, firm_col):
    sec = m.groupby(buyer_col).sektor_v3_en.first()
    mk = modal_label(m, firm_col, "urun_pazari")
    rows = []
    for i, c in enumerate(sorted(comms, key=len, reverse=True)):
        F = [n for n in c if n[0] == "F"]
        K = [n for n in c if n[0] == "K"]
        s = pd.Series([sec[n[1]] for n in K]).value_counts()
        p = pd.Series([mk[n[1]] for n in F]).value_counts()
        sub = Gc.subgraph(c)
        topK = sorted(K, key=lambda n: -Gc.degree(n))[:3]
        topF = sorted(F, key=lambda n: -Gc.degree(n))[:3]
        rows.append(dict(comm=i, size=len(c), firms=len(F), buyers=len(K), contracts=int(sub.size(weight="weight")),
                         top_sector=s.index[0] if len(s) else "", top_sector_share=s.iloc[0] / len(K) if len(K) else np.nan,
                         top_market=p.index[0] if len(p) else "", top_market_share=p.iloc[0] / len(F) if len(F) else np.nan,
                         top_buyers="; ".join(n[1] for n in topK), top_firms="; ".join(n[1] for n in topF)))
    return pd.DataFrame(rows)


def main():
    t0 = time.time()
    d = load_master()
    m = sample(d, "main")
    rng = np.random.default_rng(SEED)

    # ---------------- main network
    res, G, Gc, comms, nulls, val = core_run(m, "firma_v3", "kurum_il_split", rng, N_NULL, "main", full_detail=True)
    lf, lk, la = latapy_means(G)
    res.update(latapy_firm=lf, latapy_buyer=lk, latapy_all=la)
    for k in ["assort_pearson", "assort_spearman", "robins_alexander", "latapy_firm", "latapy_buyer", "latapy_all"]:
        res[f"null_{k}_mean"] = nulls[k].mean()
        res[f"null_{k}_q025"] = nulls[k].quantile(0.025)
        res[f"null_{k}_q975"] = nulls[k].quantile(0.975)
        res[f"z_{k}"] = (res[k] - nulls[k].mean()) / nulls[k].std(ddof=1)
    out["main"] = res
    nulls.to_csv(RES / "null_main_curveball.csv", index=False)
    val.to_csv(RES / "community_label_validation.csv", index=False)
    print("main done", time.time() - t0)

    # node table (for figures and projections)
    part = comm_dict(sorted(comms, key=len, reverse=True))
    sec = m.groupby("kurum_il_split").sektor_v3_en.first()
    mk = modal_label(m, "firma_v3", "urun_pazari")
    nmk = m.groupby("firma_v3").urun_pazari.nunique()
    nodes = pd.DataFrame([dict(node_type="firm" if n[0] == "F" else "buyer", name=n[1], degree=G.degree(n),
                               strength=G.degree(n, weight="weight"), in_gc=n in Gc, community=part.get(n, -1),
                               label=mk[n[1]] if n[0] == "F" else sec[n[1]],
                               n_markets=nmk[n[1]] if n[0] == "F" else np.nan) for n in G])
    nodes.to_csv(RES / "nodes_main.csv", index=False)
    community_table(Gc, comms, m, "kurum_il_split", "firma_v3").to_csv(RES / "communities_main_gc.csv", index=False)

    # power laws
    pl = powerlaw_block(G, rng)
    pl.to_csv(RES / "degree_powerlaw_fits.csv", index=False)
    print("powerlaw done", time.time() - t0)

    # stability
    runs, nm, ar = stability(Gc, rng)
    runs.to_csv(RES / "louvain_stability_runs.csv", index=False)
    out["stability"] = dict(runs=N_STAB, Q_min=runs.Q.min(), Q_max=runs.Q.max(), Q_mean=runs.Q.mean(), Q_sd=runs.Q.std(),
                            ncomm_min=int(runs.n_comms.min()), ncomm_max=int(runs.n_comms.max()),
                            ncomm_ge10_min=int(runs.n_comms_ge10.min()), ncomm_ge10_max=int(runs.n_comms_ge10.max()),
                            barber_min=runs.barber.min(), barber_max=runs.barber.max(),
                            NMI_mean=nm.mean(), NMI_min=nm.min(), NMI_max=nm.max(), NMI_q05=np.quantile(nm, .05),
                            ARI_mean=ar.mean(), ARI_min=ar.min(), ARI_max=ar.max(), n_pairs=len(nm))
    print("stability done", time.time() - t0)

    # annual
    ann, cons = annual(m, "firma_v3", "kurum_il_split", rng)
    ann.to_csv(RES / "annual_modularity_vs_null.csv", index=False)
    cons.to_csv(RES / "annual_partition_similarity.csv", index=False)
    print("annual done", time.time() - t0)

    # sensitivity
    sens = [res]
    for tag, samp, fc, bc in [("recorded_kurum", "main", "firma_v3", "kurum"),
                              ("original_firma", "main", "firma", "kurum_il_split"),
                              ("it_only", "it_only", "firma_v3", "kurum_il_split"),
                              ("main_plus_gray", "broad", "firma_v3", "kurum_il_split")]:
        r, *_ = core_run(sample(d, samp), fc, bc, np.random.default_rng(SEED), N_NULL_SENS, tag)
        sens.append(r)
        print("sens", tag, time.time() - t0)
    pd.DataFrame(sens).to_csv(RES / "sensitivity_core.csv", index=False)
    out["runtime_s"] = time.time() - t0
    with open(RES / "network_core.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()
