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
    ra = RES / "revision_a"
    g = pd.read_csv(ra / "B_null_by_group.csv")
    g = g[g.dimension == "renewal"].set_index(["null", "group"])
    c = pd.read_csv(ra / "D_clogit_results.csv")
    c = c[c.variable == "inc_same_market"].set_index("model")
    cm = "M1 home = prior wins only (leakage-free)"
    e = pd.read_csv(RES / "revision_b" / "B2_event_study.csv")
    e = e[(e["sample"] == "(a) all buyers") & (e.controls == "with history controls")].astype({"bin": str}).set_index("bin")
    sb = pd.read_csv(ra / "F_single_bid_logit.csv")
    sb = sb[sb.model.str.startswith("M1 ") & (sb.variable == "incumbent")].iloc[0]
    bo = pd.read_csv(ra / "B_null_overall.csv").set_index(["sample", "null"])
    rev = [
        ("Renewals among repeat-eligible contracts", 1743, g.loc[("N1", "renewal"), "n_eligible"], 0),
        ("Repeat-eligible contracts", 4913, g.loc[("N1", "renewal"), "n_eligible"] + g.loc[("N1", "new need"), "n_eligible"], 0),
        ("Incumbency, renewals, observed", 0.720, g.loc[("N3", "renewal"), "obs"], 0.0005),
        ("Incumbency, renewals, N3 null", 0.288, g.loc[("N3", "renewal"), "null_mean"], 0.0015),
        ("Incumbency, new needs, observed", 0.305, g.loc[("N3", "new need"), "obs"], 0.0005),
        ("Incumbency, new needs, N3 null", 0.163, g.loc[("N3", "new need"), "null_mean"], 0.0015),
        ("Incumbency null N3 (province) mean", 0.21, bo.loc[("main", "N3"), "null_mean"], 0.005),
        ("Cond. logit incumbent OR (home from prior wins)", 23.8, c.loc[cm, "OR"], 0.05),
        ("  ... 95% CI lower", 20.6, c.loc[cm, "OR_lo"], 0.05),
        ("  ... 95% CI upper", 27.5, c.loc[cm, "OR_hi"], 0.05),
        ("Event study 21(b)-open, 2018 vs 2013-17 (pp)", 37, e.loc["2018", "vs_1317_pp"], 0.5),
        ("cp2 single-bid logit, incumbent OR", 2.04, sb.OR, 0.005),
    ]
    return [
        # (label, paper value, reproduced value, absolute tolerance)
        ("Incumbency rate, observed", 0.452, o.loc[("main_N1", "incumbency"), "obs"], 0.0005),
        ("Incumbency rate, null N1 mean", 0.062, o.loc[("main_N1", "incumbency"), "null_mean"], 0.0015),
        ("Repeat dyads, observed", 1377, o.loc[("main_N1", "repeat_dyads"), "obs"], 0),
        ("Supplier HHI pooled, count", 38.6, m.loc["ALL (aggregate)", "HHI_count"], 0.05),
        ("Supplier HHI pooled, real value", 148.6, m.loc["ALL (aggregate)", "HHI_value"], 0.05),
        ("HHI health information systems, value", 831, m.loc["health_information_systems", "HHI_value"], 0.5),
        ("Logit OR 21(b) x post-2018", 2.42, a.loc["p21b_x_post", "exp"], 0.005),
        ("Single-bid rate, incumbent winner (bid sample)", 0.712, d.loc["incumbent winner", "rate_w"], 0.0005),
        ("Single-bid rate, non-incumbent winner (bid sample)", 0.324, d.loc["non-incumbent winner", "rate_w"], 0.0005),
    ] + rev


def main():
    bad = 0
    print(f"{'quantity':50s} {'paper':>8s} {'reproduced':>12s}  status")
    for lab, paper, val, tol in get():
        ok = abs(float(val) - paper) <= tol
        bad += not ok
        print(f"{lab:50s} {paper:>8} {float(val):>12.4f}  {'OK' if ok else 'MISMATCH'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
