"""Figures for the network topic.
F-N1  fig_N1_core_network      core bipartite network (GC of nodes with degree >= 3), ForceAtlas2, fixed seed
F-N2  fig_N2_degree_fits       CCDF of distinct-partner degrees with power-law / lognormal fits (supplement)
F-N3  fig_N3_null_modularity   null-model Q histogram + annual Q vs null (optional)
Run after network_analysis.py.
"""
import random

import numpy as np
import pandas as pd
import networkx as nx
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import powerlaw
from fa2_modified import ForceAtlas2

from network_common import *

SEED = 42
OI = dict(orange="#E69F00", sky="#56B4E9", green="#009E73", yellow="#F0E442", blue="#0072B2",
          verm="#D55E00", pink="#CC79A7", black="#000000")
GREY = "#9A9A9A"
mpl.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"], "font.size": 8,
                     "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 7.5, "pdf.fonttype": 42})

MARKET_GROUP = {
    "health_information_systems": "Health information systems",
    "ERP_management_software": "ERP / management software",
    "custom_software_web_mobile": "Software development & licences",
    "software_licences": "Software development & licences",
    "network_datacentre_infrastructure": "Infrastructure, hardware & security",
    "computers_peripherals": "Infrastructure, hardware & security",
    "maintenance_support_services": "Infrastructure, hardware & security",
    "cybersecurity": "Infrastructure, hardware & security",
    "GIS_city_information": "GIS, smart city & surveillance",
    "smart_city_traffic_OT": "GIS, smart city & surveillance",
    "physical_security_surveillance": "GIS, smart city & surveillance",
}
MARKET_COL = {"Health information systems": OI["orange"], "ERP / management software": OI["sky"],
              "Software development & licences": OI["green"], "Infrastructure, hardware & security": OI["blue"],
              "GIS, smart city & surveillance": OI["verm"], "Other IT": GREY}
SECTOR_GROUP = {"Health": "Health", "Municipal/Local": "Municipal & provincial", "Provincial admin": "Municipal & provincial",
                "Education": "Education", "Infrastructure/Transport": "Infrastructure & transport"}
SECTOR_COL = {"Health": OI["orange"], "Municipal & provincial": OI["verm"], "Education": OI["pink"],
              "Infrastructure & transport": OI["yellow"], "Central gov. & other": "#555555"}


def save(fig, name):
    for ext in ["png", "pdf"]:
        fig.savefig(FIG / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig_core_network():
    d = load_master()
    m = sample(d)
    G = build_bipartite(m)
    nodes = pd.read_csv(RES / "nodes_main.csv")
    lab = {("F" if r.node_type == "firm" else "K", r.name): r.label for r in nodes.itertuples()}
    keep = [n for n in G if G.degree(n) >= 3]
    H = giant(G.subgraph(keep))
    order = sorted(H.nodes())
    H2 = nx.Graph()
    H2.add_nodes_from(order)
    H2.add_edges_from(sorted(H.edges(data=True), key=lambda e: (e[0], e[1])))
    rng = np.random.default_rng(SEED)
    random.seed(SEED)
    np.random.seed(SEED)
    pos0 = {n: tuple(rng.uniform(-1, 1, 2) * 100) for n in order}
    fa = ForceAtlas2(outboundAttractionDistribution=True, linLogMode=False, adjustSizes=False, edgeWeightInfluence=0.0,
                     jitterTolerance=1.0, barnesHutOptimize=True, barnesHutTheta=1.2, scalingRatio=2.0,
                     strongGravityMode=False, gravity=1.0, verbose=False)
    pos = fa.forceatlas2_networkx_layout(H2, pos=pos0, iterations=3000, weight_attr=None)
    pd.DataFrame([(n[0], n[1], *pos[n]) for n in order], columns=["mode", "name", "x", "y"]).to_csv(
        RES / "fig_N1_layout_positions.csv", index=False)

    F = [n for n in order if n[0] == "F"]
    K = [n for n in order if n[0] == "K"]
    fcol = [MARKET_COL[MARKET_GROUP.get(lab[n], "Other IT")] for n in F]
    kcol = [SECTOR_COL[SECTOR_GROUP.get(lab[n], "Central gov. & other")] for n in K]
    deg = dict(H2.degree())
    size = lambda n: 4 + 3.2 * deg[n] ** 0.85

    fig, ax = plt.subplots(figsize=(7, 6.2))
    segs = [(pos[u], pos[v]) for u, v in H2.edges()]
    from matplotlib.collections import LineCollection
    ax.add_collection(LineCollection(segs, colors="#B0B0B0", linewidths=0.25, alpha=0.45, zorder=1))
    ax.scatter([pos[n][0] for n in F], [pos[n][1] for n in F], s=[size(n) for n in F], c=fcol, marker="o",
               edgecolors="white", linewidths=0.3, zorder=3)
    ax.scatter([pos[n][0] for n in K], [pos[n][1] for n in K], s=[size(n) for n in K], c=kcol, marker="s",
               edgecolors="black", linewidths=0.35, zorder=2)
    # hub labels (<=8): top buyers and firms by degree in the plotted network
    hubs = sorted(K, key=lambda n: -deg[n])[:4] + sorted(F, key=lambda n: -deg[n])[:4]
    short = pd.read_csv(RES / "fig_N1_hub_labels.csv") if (RES / "fig_N1_hub_labels.csv").exists() else None
    labmap = dict(zip(short.name, short.short)) if short is not None else {}
    offs = dict(zip(short.name, zip(short.dx, short.dy))) if short is not None else {}
    hub_rows = []
    xs = np.array([pos[n][0] for n in order]); ys = np.array([pos[n][1] for n in order])
    x0, x1 = np.quantile(xs, [0.005, 0.995]); y0, y1 = np.quantile(ys, [0.005, 0.995])
    cx = np.median(xs)
    padx = 0.42 * (x1 - x0)
    sides = {"L": sorted([n for n in hubs if pos[n][0] < cx], key=lambda n: -pos[n][1]),
             "R": sorted([n for n in hubs if pos[n][0] >= cx], key=lambda n: -pos[n][1])}
    for side, lst in sides.items():
        ty = np.linspace(y1, y0, len(lst) + 2)[1:-1] if lst else []
        tx = x0 - 0.05 * (x1 - x0) if side == "L" else x1 + 0.05 * (x1 - x0)
        for n, yy in zip(lst, ty):
            txt = labmap.get(n[1], n[1][:28])
            ax.annotate(txt, pos[n], xytext=(tx, yy), textcoords="data", fontsize=7.5, zorder=5,
                        ha="right" if side == "L" else "left", va="center",
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#666666", lw=0.4, alpha=0.95),
                        arrowprops=dict(arrowstyle="-", lw=0.6, color="#222222", shrinkA=0, shrinkB=2))
            hub_rows.append(dict(mode=n[0], name=n[1], degree_in_plot=deg[n], short=txt))
    ax.set_xlim(x0 - padx, x1 + padx)
    ax.set_ylim(y0 - 0.03 * (y1 - y0), y1 + 0.03 * (y1 - y0))
    pd.DataFrame(hub_rows).to_csv(RES / "fig_N1_hubs_used.csv", index=False)
    ax.axis("off")
    h1 = [Line2D([], [], marker="o", ls="", mfc=c, mec="white", ms=6, label=k) for k, c in MARKET_COL.items()]
    h2 = [Line2D([], [], marker="s", ls="", mfc=c, mec="black", mew=0.4, ms=6, label=k) for k, c in SECTOR_COL.items()]
    l1 = fig.legend(handles=h1, title="Firms (circles): modal product market", loc="lower left",
                    bbox_to_anchor=(0.02, -0.07), frameon=False, ncol=2, title_fontsize=7.5, alignment="left")
    fig.legend(handles=h2, title="Buyers (squares): sector", loc="lower right", bbox_to_anchor=(0.99, -0.07),
               frameon=False, ncol=1, title_fontsize=7.5, alignment="left")
    save(fig, "fig_N1_core_network")
    return dict(nodes=H2.number_of_nodes(), firms=len(F), buyers=len(K), edges=H2.number_of_edges())


def fig_degree_fits():
    d = load_master()
    G = build_bipartite(sample(d))
    F, K = modes(G)
    fits = pd.read_csv(RES / "degree_powerlaw_fits.csv").set_index("mode")
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.9))
    for ax, (mode, nodes, col, lbl) in zip(axes, [("firm", F, OI["blue"], "Firms: distinct buyers"),
                                                  ("buyer", K, OI["verm"], "Buyers: distinct firms")]):
        deg = np.array([G.degree(n) for n in nodes])
        fit = powerlaw.Fit(deg, discrete=True, verbose=False)
        x = np.sort(np.unique(deg))
        ccdf = np.array([(deg >= v).mean() for v in x])
        ax.loglog(x, ccdf, "o", ms=3, mfc="none", mec=col, mew=0.8, label="Empirical CCDF")
        xmin = fit.power_law.xmin
        ptail = (deg >= xmin).mean()
        fit.power_law.plot_ccdf(ax=ax, color="#000000", ls="--", lw=1,
                                label=f"Power law, α={fit.power_law.alpha:.2f}, $x_{{min}}$={int(xmin)}")
        fit.lognormal.plot_ccdf(ax=ax, color=OI["green"], ls=":", lw=1.3, label="Lognormal")
        # plot_ccdf draws tail-normalised curves; rescale their y to whole-sample CCDF
        for ln in ax.get_lines()[1:]:
            ln.set_ydata(np.asarray(ln.get_ydata()) * ptail)
        r = fits.loc[mode]
        ax.text(0.03, 0.04, f"LR(PL vs LN) = {r.LR_vs_lognormal:.2f}, p = {r.p_vs_lognormal:.2f}\n"
                            f"GOF bootstrap p = {r.gof_p_bootstrap:.2f}", transform=ax.transAxes, fontsize=7)
        ax.set_xlabel(lbl + " (degree)")
        ax.set_ylabel("P(degree ≥ k)")
        ax.grid(True, which="major", color="#E5E5E5", lw=0.5)
        ax.legend(frameon=False, loc="upper right", fontsize=7)
    fig.tight_layout()
    save(fig, "fig_N2_degree_fits")


def fig_null():
    nul = pd.read_csv(RES / "null_main_curveball.csv")
    core = pd.read_csv(RES / "sensitivity_core.csv").iloc[0]
    ann = pd.read_csv(RES / "annual_modularity_vs_null.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.8), gridspec_kw=dict(width_ratios=[1, 1.35]))
    ax = axes[0]
    for k, c, lab in [("Q_full_binary", OI["blue"], "Whole network"), ("Q_gc_binary", OI["orange"], "Giant component")]:
        ax.hist(nul[k], bins=25, color=c, alpha=0.6, label=f"Null: {lab.lower()}")
        ax.axvline(core[k], color=c, lw=1.5, ls="-")
    ax.set_xlabel("Louvain modularity Q (binary)")
    ax.set_ylabel(f"Null graphs (n = {len(nul)})")
    ax.legend(frameon=False, loc="upper center", fontsize=7)
    ax.grid(True, color="#E5E5E5", lw=0.5)
    ax.text(0.98, 0.5, "vertical lines:\nobserved Q", transform=ax.transAxes, ha="right", fontsize=7)
    ax = axes[1]
    a = ann[ann.year <= 2025]
    ax.fill_between(a.year, a.null_mean - 1.96 * a.null_sd, a.null_mean + 1.96 * a.null_sd, color=OI["sky"], alpha=0.35,
                    lw=0, label="Null mean ± 1.96 SD")
    ax.plot(a.year, a.null_mean, color=OI["sky"], lw=1)
    ax.plot(a.year, a.Q_full_binary, "o-", color=OI["verm"], ms=3.5, lw=1.2, label="Observed Q")
    ax.set_xlabel("Tender year")
    ax.set_ylabel("Louvain modularity Q (binary)")
    ax.legend(frameon=False, loc="lower right", fontsize=7)
    ax.grid(True, color="#E5E5E5", lw=0.5)
    ax.set_xticks(range(2010, 2026, 3))
    fig.tight_layout()
    save(fig, "fig_N3_null_modularity")


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    print(fig_core_network())
    fig_degree_fits()
    fig_null()
