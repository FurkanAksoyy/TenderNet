# -*- coding: utf-8 -*-
"""Figures F-R1 (AME plot, models A and B) and F-R2 (single-bid rates)."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from models_common import RES, FIG

FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"], "font.size": 8,
                     "axes.titlesize": 8, "axes.labelsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "legend.fontsize": 8, "axes.spines.top": False, "axes.spines.right": False})
BLUE, ORANGE, GREEN, BLACK = "#0072B2", "#E69F00", "#009E73", "#000000"


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- F-R1
ame = pd.read_csv(RES / "AME_A_B.csv")
A = ame[ame.model == "A1"]
rowsA = [("p_21b", "pre-7144", "21(b) vs open, pre-Law 7144"),
         ("p_21b", "post-7144", "21(b) vs open, post-Law 7144"),
         ("p_oth_neg", "all", "Other negotiated vs open"),
         ("post7144", "all", "Post-Law 7144 (within 2018 only)"),
         ("log_real_value", "all", "log real value"),
         ("log_prior_contracts", "all", "log prior contracts (buyer x market)"),
         ("log_prior_suppliers", "all", "log prior suppliers (buyer x market)"),
         ("years_since_first", "all", "Years since buyer's first contract")]
rowsB = [("p_21b", "First contract via 21(b) vs open"),
         ("p_oth_neg", "First contract via other negotiated"),
         ("log_real_value", "log real value of first contract"),
         ("log_firm_prior_contracts", "Firm size: log(1+prior contracts)"),
         ("log_firm_prior_markets", "Firm generalism: log(1+prior markets)"),
         ("log_buyer_prior_contracts", "Buyer experience: log(1+prior contracts)"),
         ("log_opp", "log later buyer-market contracts")]

fig, axes = plt.subplots(1, 2, figsize=(7, 3.6), gridspec_kw={"wspace": 1.25})
ax = axes[0]
for i, (t, sub, lab) in enumerate(rowsA):
    r = A[(A.term == t) & (A.subset == sub)].iloc[0]
    y = len(rowsA) - 1 - i
    ax.errorbar(r.ame * 100, y, xerr=[[(r.ame - r.lo) * 100], [(r.hi - r.ame) * 100]], fmt="o", color=BLUE,
                ms=4.5, capsize=2, lw=1.2)
ax.set_yticks(range(len(rowsA)))
ax.set_yticklabels([r[2] for r in rowsA][::-1])
ax.axvline(0, color=BLACK, lw=0.8)
ax.set_xlabel("AME on P(incumbent wins), percentage points")
ax.grid(axis="x", color="#dddddd", lw=0.5)
ax.text(-0.02, 1.03, "a  Model A: incumbency (N = 4,913)", transform=ax.transAxes, ha="right", fontweight="bold")

ax = axes[1]
specs = [("B_logit_full", "All firm covariates", BLUE, "o", 0.18),
         ("B_logit_size_generalism", "Size + generalism", ORANGE, "s", 0.0),
         ("B_logit_generalism_only", "Generalism only", GREEN, "^", -0.18)]
for m, lab, col, mk, off in specs:
    Bm = ame[ame.model == m]
    first = True
    for i, (t, _) in enumerate(rowsB):
        if t not in Bm.term.values:
            continue
        r = Bm[Bm.term == t].iloc[0]
        y = len(rowsB) - 1 - i + off
        ax.errorbar(r.ame * 100, y, xerr=[[(r.ame - r.lo) * 100], [(r.hi - r.ame) * 100]], fmt=mk, color=col,
                    ms=4, capsize=2, lw=1.1, label=lab if first else None)
        first = False
ax.set_yticks(range(len(rowsB)))
ax.set_yticklabels([r[1] for r in rowsB][::-1])
ax.axvline(0, color=BLACK, lw=0.8)
ax.set_xlabel("AME on P(dyad continues), percentage points")
ax.grid(axis="x", color="#dddddd", lw=0.5)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.35, -0.16), ncol=3, handletextpad=0.3,
          columnspacing=0.8)
ax.text(-0.02, 1.03, "b  Model B: dyad continuation (N = 3,427)", transform=ax.transAxes, ha="right",
        fontweight="bold")
save(fig, "F-R1_models_AME")

# ---------------------------------------------------------------- F-R2
D = pd.read_csv(RES / "D_single_bid_rates.csv")
groups = [("procedure", "open", "Open"), ("procedure", "21b", "21(b)"), ("procedure", "21f", "21(f)"),
          (None, None, None),
          ("incumbency", "incumbent winner", "Incumbent\nwinner"),
          ("incumbency", "non-incumbent winner", "Non-incumbent\nwinner"),
          ("incumbency", "buyer first in market (undefined)", "Buyer's first\nin market")]
fig, ax = plt.subplots(figsize=(7, 3.0))
xt, xl = [], []
for outc, lab, col, mk, off in [("single", "One bid submitted", BLUE, "o", -0.12),
                                ("single_valid", "One valid bid", ORANGE, "s", 0.12)]:
    first = True
    for x, (b, g, name) in enumerate(groups):
        if b is None:
            continue
        r = D[(D.outcome == outc) & (D.breakdown == b) & (D.group == g)].iloc[0]
        ax.errorbar(x + off, r.rate_w * 100, yerr=[[(r.rate_w - r.lo95) * 100], [(r.hi95 - r.rate_w) * 100]],
                    fmt=mk, color=col, ms=5, capsize=2.5, lw=1.2, label=lab if first else None)
        first = False
        if outc == "single":
            xt.append(x); xl.append(f"{name}\n(n = {int(r.n)})")
ax.axvline(3, color="#bbbbbb", lw=0.8, ls=":")
ax.set_xticks(xt); ax.set_xticklabels(xl)
ax.set_ylabel("Design-weighted share of tenders (%)")
ax.set_ylim(0, 100)
ax.grid(axis="y", color="#dddddd", lw=0.5)
ax.text(1, 97, "By procedure", ha="center", va="top")
ax.text(5, 97, "By winner's incumbency status", ha="center", va="top")
ax.legend(frameon=False, loc="lower left", ncol=2)
save(fig, "F-R2_single_bid")
print("figures written")
