"""Check that the regenerated results reproduce the headline numbers reported in the paper.

    python src/check_headlines.py      (exit code 1 if any value is outside its tolerance)
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"


def get():
    o = pd.read_csv(RES / "lockin" / "null_overall.csv").set_index(["variant", "statistic"])
    m = pd.read_csv(RES / "concentration" / "supplier_hhi_by_market.csv").set_index("group")
    a = pd.read_csv(RES / "models" / "A1_logit_incumbency.csv").set_index("term")
    d = pd.read_csv(RES / "models" / "D_single_bid_rates.csv")
    d = d[(d.outcome == "single") & (d.breakdown == "incumbency")].set_index("group")
    return [
        # (label, paper value, reproduced value, absolute tolerance)
        ("Incumbency rate, observed (Table 2)", 0.452, o.loc[("main_N1", "incumbency"), "obs"], 0.0005),
        ("Incumbency rate, null N1 mean (Table 2)", 0.062, o.loc[("main_N1", "incumbency"), "null_mean"], 0.0015),
        ("Repeat dyads, observed (Table 2)", 1377, o.loc[("main_N1", "repeat_dyads"), "obs"], 0),
        ("Supplier HHI pooled, count (Table 1)", 38.6, m.loc["ALL (aggregate)", "HHI_count"], 0.05),
        ("Supplier HHI pooled, real value (Table 1)", 148.6, m.loc["ALL (aggregate)", "HHI_value"], 0.05),
        ("HHI health information systems, value (Fig. 1)", 831, m.loc["health_information_systems", "HHI_value"], 0.5),
        ("Logit OR 21(b) x post-2018 (Table 3)", 2.42, a.loc["p21b_x_post", "exp"], 0.005),
        ("Single-bid rate, incumbent winner (Fig. 5)", 0.712, d.loc["incumbent winner", "rate_w"], 0.0005),
        ("Single-bid rate, non-incumbent winner (Fig. 5)", 0.324, d.loc["non-incumbent winner", "rate_w"], 0.0005),
    ]


def main():
    bad = 0
    print(f"{'quantity':52s} {'paper':>8s} {'reproduced':>12s}  status")
    for lab, paper, val, tol in get():
        ok = abs(float(val) - paper) <= tol
        bad += not ok
        print(f"{lab:52s} {paper:>8} {float(val):>12.4f}  {'OK' if ok else 'MISMATCH'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
