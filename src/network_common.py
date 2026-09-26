"""Shared helpers for the bipartite firm-buyer network analysis (topic: network).

Graph conventions
-----------------
* Firm nodes are tuples ('F', name), buyer nodes ('K', name); attribute
  bipartite=0 for firms, 1 for buyers.
* Edge weight = number of contracts between the firm and the buyer.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "contracts_v3.csv"
RES = ROOT / "results" / "network"
FIG = ROOT / "figures"


def load_master():
    d = pd.read_csv(DATA, encoding="utf-8-sig", low_memory=False)
    for c in ["in_scope_main", "in_scope_core", "in_scope_broad", "callcentre_flag"]:
        d[c] = d[c].astype(str).str.lower().eq("true")
    return d


def sample(d, name="main"):
    if name == "main":
        return d[d.in_scope_main].copy()
    if name == "it_only":  # robustness (a): main minus MHRS call-centre contracts
        return d[d.in_scope_main & (d.scope_v3 == "IT")].copy()
    if name == "broad":  # robustness (b): main + gray
        return d[d.in_scope_broad].copy()
    raise ValueError(name)


def build_bipartite(df, firm_col="firma_v3", buyer_col="kurum_il_split"):
    e = df.groupby([firm_col, buyer_col]).size().reset_index(name="w")
    G = nx.Graph()
    firms = sorted(e[firm_col].unique())
    buyers = sorted(e[buyer_col].unique())
    G.add_nodes_from([("F", f) for f in firms], bipartite=0)
    G.add_nodes_from([("K", k) for k in buyers], bipartite=1)
    G.add_weighted_edges_from(
        (("F", f), ("K", k), int(w)) for f, k, w in e[[firm_col, buyer_col, "w"]].itertuples(index=False)
    )
    return G


def modes(G):
    F = [n for n in G if n[0] == "F"]
    K = [n for n in G if n[0] == "K"]
    return F, K


def giant(G):
    cc = max(nx.connected_components(G), key=len)
    return G.subgraph(cc).copy()


def assert_bipartite(G, deg_ref=None):
    """Every edge must join a firm and a buyer; optional degree check."""
    for u, v in G.edges():
        if u[0] == v[0]:
            raise AssertionError(f"non-bipartite edge {u}-{v}")
    if deg_ref is not None:
        for n, k in deg_ref.items():
            if G.degree(n) != k:
                raise AssertionError(f"degree changed for {n}")
    return True


# ---------------------------------------------------------------- nulls
def curveball(G, rng, trades_per_row=20):
    """Curveball (Strona et al. 2014; Carstens 2015) on the binary bipartite graph.
    Preserves every firm degree and every buyer degree exactly. Returns
    (null graph, edge-overlap with the observed graph)."""
    F, K = modes(G)
    kidx = {k: i for i, k in enumerate(K)}
    rows = [set(kidx[nb] for nb in G[f]) for f in F]
    n = len(rows)
    n_trades = trades_per_row * n
    pairs = rng.integers(0, n, size=(n_trades, 2))
    for a, b in pairs:
        if a == b:
            continue
        A, B = rows[a], rows[b]
        a_only = A - B
        if not a_only:
            continue
        b_only = B - A
        if not b_only:
            continue
        shared = A & B
        pool = list(a_only | b_only)
        rng.shuffle(pool)
        na = len(a_only)
        rows[a] = shared | set(pool[:na])
        rows[b] = shared | set(pool[na:])
    H = nx.Graph()
    H.add_nodes_from(F, bipartite=0)
    H.add_nodes_from(K, bipartite=1)
    for f, r in zip(F, rows):
        H.add_edges_from((f, K[j]) for j in r)
    obs = set((f, k) for f in F for k in G[f])
    overlap = sum(1 for f in F for k in H[f] if (f, k) in obs) / len(obs)
    return H, overlap


def shuffle_weights(G, H, rng):
    """Assign the observed edge weights (contract counts) at random to the edges of H."""
    w = np.array([d["weight"] for _, _, d in G.edges(data=True)])
    rng.shuffle(w)
    H = H.copy()
    for (u, v), x in zip(H.edges(), w):
        H[u][v]["weight"] = int(x)
    return H


# ---------------------------------------------------------------- modularity
def louvain(G, seed, weight="weight"):
    comms = nx.community.louvain_communities(G, weight=weight, resolution=1.0, seed=seed)
    Q = nx.community.modularity(G, comms, weight=weight)
    return comms, Q


def comm_dict(comms):
    return {n: i for i, c in enumerate(comms) for n in c}


def barber_Q(G, part, weight="weight"):
    """Barber (2007) bipartite modularity of a node partition (dict node->label)."""
    m = 0.0
    e_in, kf, kb = {}, {}, {}
    for u, v, d in G.edges(data=True):
        w = d.get(weight, 1) if weight else 1
        m += w
        if part[u] == part[v]:
            e_in[part[u]] = e_in.get(part[u], 0) + w
    for n in G:
        s = G.degree(n, weight=weight) if weight else G.degree(n)
        tgt = kf if n[0] == "F" else kb
        tgt[part[n]] = tgt.get(part[n], 0) + s
    labs = set(part[n] for n in G)
    return sum(e_in.get(c, 0) / m - kf.get(c, 0) * kb.get(c, 0) / m**2 for c in labs)


def permuted_copy(G, rng):
    """Same graph with node and edge insertion order randomly permuted."""
    nodes = list(G.nodes(data=True))
    edges = list(G.edges(data=True))
    H = nx.Graph()
    for i in rng.permutation(len(nodes)):
        H.add_node(nodes[i][0], **nodes[i][1])
    for i in rng.permutation(len(edges)):
        u, v, d = edges[i]
        if rng.random() < 0.5:
            u, v = v, u
        H.add_edge(u, v, **d)
    return H


# ---------------------------------------------------------------- descriptives
def bip_assortativity(G):
    F, _ = modes(G)
    x, y = [], []
    for f in F:
        for k in G[f]:
            x.append(G.degree(f))
            y.append(G.degree(k))
    from scipy.stats import pearsonr, spearmanr

    return pearsonr(x, y)[0], spearmanr(x, y)[0]


def robins_alexander(G):
    """Robins-Alexander (2004) bipartite clustering = 4*C4 / L3."""
    return nx.bipartite.robins_alexander_clustering(G)


def latapy_means(G):
    c = nx.bipartite.latapy_clustering(G, mode="dot")
    F, K = modes(G)
    return float(np.mean([c[n] for n in F])), float(np.mean([c[n] for n in K])), float(np.mean(list(c.values())))


def modal_label(df, key, lab):
    """Modal label per key; ties broken alphabetically (deterministic)."""
    t = df.groupby([key, lab]).size().reset_index(name="n")
    t = t.sort_values([key, "n", lab], ascending=[True, False, True])
    return t.drop_duplicates(key).set_index(key)[lab]
