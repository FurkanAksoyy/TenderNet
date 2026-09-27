"""Compare regenerated results with manually transcribed manuscript checkpoints.

This does not parse the manuscript or validate every statement. PDF/source review
is required separately. Expected monetary values reflect the TCMB-normalized revision.

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
    rc = RES / "revision_c"
    k = pd.read_csv(rc / "C1_C2_clogit_results.csv").set_index(["model", "variable"])
    main_ = ("T1 24m pool=all: main", "incumbent")
    fut = "T2a 24m pool=all: main + future_supplier_only"
    lve = "T2b 24m pool=all: last vs earlier"
    sim = pd.read_csv(rc / "C2_placebo_simulation.csv").OR_future_only
    n4 = pd.read_csv(rc / "C3_N4prior_overall.csv").set_index("null")
    import re
    import statsmodels.formula.api as smf
    pr = pd.read_csv(RES / "price" / "price_sample_analysis.csv")
    ols = smf.ols("discount ~ incumbent_win", pr).fit(cov_type="HC1")
    ca = (RES / "coder_agreement" / "coder_agreement_results.md").read_text(encoding="utf-8")
    kappa = float(re.search(r"\| coderA \| coderB \| \d+ \| [0-9.]+ \| ([0-9.]+) \|", ca).group(1))  # first table = markets
    w = pd.read_csv(RES / "revision_d" / "D3_three_worlds.csv")
    w = w[(w["sample"] == "all") & (w.moment == "OR_future_only")].set_index("world")
    lag = pd.read_csv(RES / "revision_d" / "D4_firm_controls_lags.csv").set_index(["model", "variable"])
    horizon = pd.read_csv(RES / "revision_e_horizons" / "symmetric_contrasts.csv").set_index("sample")
    annual = pd.read_csv(RES / "concentration" / "within_year_hhi_summary.csv")
    init = pd.read_csv(RES / "revision_e_initial_conditions" / "summary.csv").set_index(["scenario", "metric"])
    rev = [
        ("Renewals among repeat-eligible contracts", 1743, g.loc[("N1", "renewal"), "n_eligible"], 0),
        ("Repeat-eligible contracts", 4913, g.loc[("N1", "renewal"), "n_eligible"] + g.loc[("N1", "new need"), "n_eligible"], 0),
        ("Incumbency, renewals, observed", 0.720, g.loc[("N3", "renewal"), "obs"], 0.0005),
        ("Incumbency, renewals, N3 null", 0.288, g.loc[("N3", "renewal"), "null_mean"], 0.0015),
        ("Incumbency, new needs, observed", 0.305, g.loc[("N3", "new need"), "obs"], 0.0005),
        ("Incumbency, new needs, N3 null", 0.163, g.loc[("N3", "new need"), "null_mean"], 0.0015),
        ("Incumbency null N3 (province) mean", 0.21, bo.loc[("main", "N3"), "null_mean"], 0.005),
        ("Event study 21(b)-open, 2018 vs 2013-17 (pp)", 37, e.loc["2018", "vs_1317_pp"], 0.5),
        ("cp2 single-bid logit, incumbent OR", 2.04, sb.OR, 0.005),
        ("Choice model (24m, all pre-t firms): incumbent OR", 42.3, k.loc[main_, "OR"], 0.05),
        ("  ... 95% CI lower", 36.4, k.loc[main_, "OR_lo"], 0.05),
        ("  ... 95% CI upper", 49.2, k.loc[main_, "OR_hi"], 0.05),
        ("  ... contracts", 3013, k.loc[main_, "n_contracts"], 0),
        ("Placebo: future-supplier-only OR", 54.4, k.loc[(fut, "future_supplier_only"), "OR"], 0.05),
        ("  ... 95% CI lower", 42.2, k.loc[(fut, "future_supplier_only"), "OR_lo"], 0.05),
        ("  ... 95% CI upper", 70.1, k.loc[(fut, "future_supplier_only"), "OR_hi"], 0.05),
        ("Placebo model: past-incumbent OR", 63.7, k.loc[(fut, "incumbent"), "OR"], 0.05),
        ("Simulated future-only OR, mean (100 sims)", 19.8, sim.mean(), 0.05),
        ("  ... 2.5th percentile", 16.1, sim.quantile(0.025), 0.05),
        ("  ... 97.5th percentile", 24.5, sim.quantile(0.975), 0.05),
        ("Last supplier OR", 45.8, k.loc[(lve, "inc_last"), "OR"], 0.05),
        ("Earlier supplier OR", 26.2, k.loc[(lve, "inc_earlier"), "OR"], 0.05),
        ("N4 null (home from prior wins) mean", 0.173, n4.loc["N4_home_prior", "null_mean"], 0.0015),
        ("N4b null (province x home from prior wins) mean", 0.264, n4.loc["N4b_prov_home_prior", "null_mean"], 0.0015),
        ("Price sample: mean discount, incumbent winner", 0.121, pr[pr.incumbent_win == 1].discount.mean(), 0.0005),
        ("Price sample: mean discount, other winner", 0.165, pr[pr.incumbent_win == 0].discount.mean(), 0.0005),
        ("Price sample: n", 143, len(pr), 0),
        ("Price sample: OLS incumbent coefficient", -0.044, ols.params["incumbent_win"], 0.0005),
        ("AI coders A vs B, product markets: kappa", 0.873, kappa, 0.0005),
        ("Three worlds: future-only OR, state dependence", 19.8, w.loc["state dependence", "center"], 0.05),
        ("Three worlds: future-only OR, heterogeneity", 40.5, w.loc["heterogeneity", "center"], 0.05),
        ("First future >365 days: OR", 46.6, lag.loc[("T4 lag all | future win > t+365d", "fut_gt365"), "OR"], 0.05),
        ("First future >365 days: firm-control OR", 33.6, lag.loc[("T4 lag all | future win > t+365d + firm controls", "fut_gt365"), "OR"], 0.05),
        ("Equal 730d windows: modeled contracts", 2508, horizon.loc["all", "n_contracts"], 0),
        ("Equal 730d windows: past/future ratio", 0.98, horizon.loc["all", "ratio"], 0.005),
        ("Equal 730d windows: recurring ratio", 1.68, horizon.loc["recurring", "ratio"], 0.005),
        ("Annual category median value HHI >1000", 6, ((annual.market != "ALL (aggregate)") & (annual.HHI_value_med > 1000)).sum(), 0),
        ("Initialization, all-fixed: past/future ratio", 1.60, init.loc[("legacy_all_fixed", "past_future_ratio"), "mean"], 0.005),
        ("Initialization, early-only: past/future ratio", 2.06, init.loc[("pre_first_simulated", "past_future_ratio"), "mean"], 0.005),
        ("Initialization, no shift: incumbent share", 0.348, init.loc[("no_tilt", "share_chosen_incumbent"), "mean"], 0.0005),
        ("Initialization, no shift: grid ceiling sigma", 10.0, init.loc[("no_tilt", "share_chosen_incumbent"), "sigma"], 0),
    ]
    return [
        # (label, paper value, reproduced value, absolute tolerance)
        ("Incumbency rate, observed", 0.452, o.loc[("main_N1", "incumbency"), "obs"], 0.0005),
        ("Incumbency rate, null N1 mean", 0.062, o.loc[("main_N1", "incumbency"), "null_mean"], 0.0015),
        ("Repeat dyads, observed", 1377, o.loc[("main_N1", "repeat_dyads"), "obs"], 0),
        ("Supplier HHI pooled, count", 38.6, m.loc["ALL (aggregate)", "HHI_count"], 0.05),
        ("Supplier HHI pooled, real value", 147.2, m.loc["ALL (aggregate)", "HHI_value"], 0.05),
        ("HHI health information systems, value", 831, m.loc["health_information_systems", "HHI_value"], 0.5),
        ("Logit OR 21(b) x post-2018", 2.42, a.loc["p21b_x_post", "exp"], 0.005),
        ("Single-bid rate, incumbent winner (bid sample)", 0.712, d.loc["incumbent winner", "rate_w"], 0.0005),
        ("Single-bid rate, non-incumbent winner (bid sample)", 0.324, d.loc["non-incumbent winner", "rate_w"], 0.0005),
    ] + rev


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
