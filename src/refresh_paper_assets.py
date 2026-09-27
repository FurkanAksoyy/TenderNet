"""Refresh descriptive simulation labels and copy current figure assets to the paper.

The legacy simulation data are preserved; display labels describe their conditional
specifications without claiming that they identify pure economic mechanisms.
"""
from pathlib import Path
import shutil
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"


def main():
    W = pd.read_csv(ROOT / "results/revision_d/D3_three_worlds.csv")
    panels = [("OR_incumbent_plac", "Past-supplier OR"),
              ("OR_future_only", "Future-supplier-only OR"),
              ("last_earlier_ratio", "Last / earlier supplier OR ratio")]
    samples = [("all", "All"), ("renewals", "Recurring"), ("new needs", "Other purchases")]
    scenarios = [("observed", "Observed (95% CI)", "#333333", "o"),
                 ("state dependence", "Incumbency-term scenario", "#D55E00", "s"),
                 ("heterogeneity", "Dyad-effect scenario", "#009E73", "D")]
    with plt.rc_context({"font.size": 8}):
        fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.6), sharey=True)
        for ax, (moment, label) in zip(axes, panels):
            for si, (sample, _) in enumerate(samples):
                for wi, (scenario, legend, color, marker) in enumerate(scenarios):
                    row = W[(W["sample"] == sample) & (W.moment == moment) & (W.world == scenario)].iloc[0]
                    y = si + (1-wi)*.24
                    ax.plot([row.lo, row.hi], [y,y], color=color, lw=1.4)
                    ax.plot(row.center, y, marker, color=color, ms=4.2,
                            mfc=color if scenario == "observed" else "white", mew=1.1,
                            label=legend if si == 0 else None)
            ax.set_xscale("log")
            sub = W[W.moment == moment]
            ticks = [v for v in [.8,1,1.5,2,3,5,10,20,50,100,200,500,1000]
                     if sub.lo.min()/1.3 <= v <= sub.hi.max()*1.3]
            ax.xaxis.set_major_locator(FixedLocator(ticks))
            ax.xaxis.set_major_formatter(FixedFormatter([f"{v:g}" for v in ticks]))
            ax.xaxis.set_minor_formatter(NullFormatter())
            ax.set_xlabel(label + " (log scale)")
            ax.set_ylim(2.45, -.45)
            if moment == "last_earlier_ratio":
                ax.axvline(1, color="#777777", lw=.8, ls=":")
        axes[0].set_yticks(range(3), [label for _, label in samples])
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False,
                   bbox_to_anchor=(.5,1.06))
        fig.tight_layout()
        for suffix in ("pdf", "png"):
            fig.savefig(FIG / f"F-D1_three_worlds.{suffix}", dpi=300, bbox_inches="tight")
        plt.close(fig)
    destination = ROOT / "paper/figures"
    destination.mkdir(exist_ok=True)
    for source in FIG.iterdir():
        if source.is_file() and source.suffix in (".pdf", ".png"):
            shutil.copy2(source, destination / source.name)
    print("Updated conditional-scenario labels and copied current figure assets.")


if __name__ == "__main__":
    main()
