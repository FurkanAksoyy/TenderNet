# -*- coding: utf-8 -*-
"""Builds the regression tables (markdown) for results/models/models_results.md."""
import pickle
import numpy as np
import pandas as pd
from models_common import RES, pstars

O = pickle.load(open(RES / "_model_objects.pkl", "rb"))
L = O["LABELS"]


def fp(p):
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def tab(t, terms, expname=None, extra_rows=()):
    t = t.set_index("term")
    out = ["| Variable | Coef. | SE | " + (f"{expname} [95% CI] | " if expname else "95% CI | ") + "p |",
           "|---|---:|---:|---:|---:|"]
    for k in terms:
        if k not in t.index:
            continue
        r = t.loc[k]
        ci = f"{r.exp:.3f} [{r.exp_lo:.3f}, {r.exp_hi:.3f}]" if expname else f"[{r.lo:.4f}, {r.hi:.4f}]"
        out.append(f"| {L.get(k, k)} | {r.coef:.4f}{pstars(r.p)} | {r.se:.4f} | {ci} | {fp(r.p)} |")
    for row in extra_rows:
        out.append(f"| {row[0]} | {row[1]} | | | |")
    return "\n".join(out)


def ame_tab(a):
    out = ["| model | Variable | subset | AME (pp) | SE (pp) | 95% CI (pp) | p |", "|---|---|---|---:|---:|---:|---:|"]
    for _, r in a.iterrows():
        out.append(f"| {r.model} | {L.get(r.term, r.term)} | {r.subset} | {100*r.ame:.2f} | {100*r.se:.2f} | "
                   f"[{100*r.lo:.2f}, {100*r.hi:.2f}] | {fp(r.p)} |")
    return "\n".join(out)


parts = []
CA = ["p_21b", "p_oth_neg", "post7144", "p21b_x_post", "log_real_value", "log_prior_suppliers",
      "log_prior_contracts", "years_since_first", "const"]
GA = O["GA"]
parts.append("### Table A1. Incumbent win, logit (contract level)\n")
parts.append(tab(O["tA"], CA, "OR", [
    ("Fixed effects", "product market (13), year (2011–2026; 2010 pooled into 2011), buyer sector (10)"),
    ("N contracts", f"{O['NA']:,}"), ("Mean of outcome", f"{O['meanA']:.3f}"),
    ("Clusters", f"buyer {GA[0]:,}; winner {GA[1]:,}; intersection {GA[2]:,} (CGM two-way)"),
    ("McFadden pseudo-R²", f"{O['prA']:.4f}"), ("Log-likelihood", f"{O['llA']:.2f}")]))
parts.append("\nSE: two-way clustered (buyer, winning firm), Cameron–Gelbach–Miller, small-sample factor G/(G−1)·(N−1)/(N−K). "
             "*** p<0.001, ** p<0.01, * p<0.05.\n")
parts.append("### Table A1-AME. Average marginal effects (delta method, two-way clustered V)\n")
parts.append(ame_tab(O["ameA"]))
parts.append("\n### Table A1-pred. Mean predicted P(incumbent wins) by procedure and period (model A1, observed covariates)\n")
pa = O["predA"].pivot(index="procedure", columns="period", values="mean_pred_incumbent_win")
parts.append("| procedure | pre-7144 | post-7144 |\n|---|---:|---:|")
for p_ in ["open", "21b", "oth_neg"]:
    parts.append(f"| {p_} | {pa.loc[p_, 'pre']:.3f} | {pa.loc[p_, 'post']:.3f} |")
parts.append("\nRaw incumbent-win rates (A sample):\n\n| period | procedure | rate | n |\n|---|---|---:|---:|")
for _, r in O["raw_rates"].iterrows():
    parts.append(f"| {'post' if r.post7144 else 'pre'} | {r.proc} | {r['mean']:.3f} | {int(r['size'])} |")

parts.append("\n### Table A2. Robustness of model A (logit, same covariates/FE unless stated; two-way clustered SE)\n")
rb = pd.read_csv(RES / "A_robustness.csv")
parts.append("| Model | N | G buyer | G firm | pseudo-R² | OR 21(b) [p] | OR post-7144 [p] | OR 21(b)×post [p] | OR log prior suppliers [p] | OR log prior contracts [p] |")
parts.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for m, g in rb.groupby("model", sort=False):
    g = g.set_index("term")
    f = lambda k: f"{g.loc[k,'OR']:.2f} [{fp(g.loc[k,'p'])}]" if k in g.index else "—"
    r0 = g.iloc[0]
    parts.append(f"| {m} | {int(r0.N):,} | {int(r0.G_buyer):,} | {int(r0.G_firm):,} | {r0.pseudoR2:.3f} | {f('p_21b')} | "
                 f"{f('post7144')} | {f('p21b_x_post')} | {f('log_prior_suppliers')} | {f('log_prior_contracts')} |")
parts.append("\nA2 = linear time trend instead of year FE (post-7144 main effect then identified across years); "
             "A3 = 21(f) separated from other negotiated (A3's 21(f) OR 0.90, p=0.51; 21(f)×post in table CSV); "
             "A4 = drops prior-supplier/prior-contract counts; R_* = sample/definition sensitivity; "
             "R_break_* = alternative break dates (KHK 694 date 2017-08-25; placebos 2016-05-25 and 2020-05-25). "
             "Log-likelihoods (same N=4,913): A1 −2802.54; KHK-694 break −2801.10; placebo 2016 −2806.05; placebo 2020 −2807.77.\n")

parts.append("### Table A3. Linear probability model with buyer fixed effects (within-buyer)\n")
parts.append(tab(O["tL"], CA))
parts.append(f"\nFE: buyer (absorbed; {O['GL'][0]:,} buyers; sector FE collinear with buyer FE), product market, year. "
             f"N={O['NL']:,}; within-R²={O['r2w']:.4f}; two-way clustered SE (buyer {O['GL'][0]:,}, winner {O['GL'][1]:,}). "
             "450 contracts of buyers with a single A-observation contribute no within variation.\n")
parts.append("Same LPM without buyer FE (sector FE instead), for comparison:\n")
parts.append(tab(O["tL2"], CA))

CB = ["p_21b", "p_oth_neg", "log_real_value", "log_firm_prior_contracts", "log_firm_prior_markets",
      "log_firm_prior_buyers", "log_buyer_prior_contracts", "log_opp", "alpha", "const"]
Bt = O["Bt"]
for mod, nm, ex in [("logit", "Logit: any later contract (binary)", "OR"),
                    ("ppml", "Poisson PML: number of later contracts", "IRR"),
                    ("nb2", "NB2 (α estimated): number of later contracts", "IRR")]:
    for spec in ["full", "size_generalism", "generalism_only", "size_only"]:
        t, G, N, pr2, ll = Bt[(mod, spec)]
        parts.append(f"\n### Table B-{mod}-{spec}. {nm} — spec `{spec}`\n")
        extra = [("Fixed effects", "product market (13), first-contract year (2010–2024; 2025–26 pooled into 2024)"),
                 ("N dyads", f"{N:,}"), ("Clusters", f"firm {G[0]:,}; buyer {G[1]:,}; intersection {G[2]:,}"),
                 ("McFadden pseudo-R²", f"{pr2:.4f}"), ("Log-likelihood", f"{ll:.2f}")]
        parts.append(tab(t, CB, ex, extra))
parts.append("\nFor NB2, the row `alpha` is α itself (Var = μ + αμ²); its 'IRR' column is meaningless and can be ignored.\n")
parts.append("### Table B-AME. Logit AMEs (percentage points)\n")
parts.append(ame_tab(O["ameB"]))
ameB = O["ameB"]
parts.append("\n(model column: rows are in order full, size_generalism, generalism_only, size_only; see AME_A_B.csv.)\n")
parts.append("### Table B-VIF and correlations (estimation sample)\n")
parts.append("| Variable | VIF |\n|---|---:|")
for _, r in O["vifB"].iterrows():
    parts.append(f"| {L.get(r.term, r.term)} | {r.VIF:.2f} |")
parts.append("\n```\n" + O["corrB"].round(3).to_string() + "\n```\n")
od = O["overdisp"]
parts.append("### Overdispersion and offset tests (full spec)\n")
parts.append(f"- NB2 α = {od['nb2_alpha']:.3f} (two-way SE {od['nb2_alpha_se']:.3f}).\n"
             f"- LR test α=0 (boundary, p halved): LR = {od['LR']:.2f}, p = {od['LR_p']:.1e}.\n"
             f"- Cameron–Trivedi auxiliary regression (NB2 form): α̂ = {od['ct_alpha']:.3f}, t = {od['ct_t']:.2f}, p = {od['ct_p']:.1e}.\n"
             f"- Pearson dispersion of PPML = {od['pearson_dispersion']:.3f}.")
for _, r in O["offs"].iterrows():
    parts.append(f"- Offset restriction ({r.model}): coefficient on log(opportunities) = {r.b_log_opp:.3f} (SE {r.se:.3f}); "
                 f"H0 = 1: z = {r.z_vs_1:.2f}, p = {r.p:.3f}.")
parts.append("")
parts.append("### Table C. Share of 21(b) by dyad status\n")
parts.append("| scope | status | n | n 21(b) | share 21(b), count | value (bn 2025 TRY) | 21(b) value (bn) | share 21(b), value |")
parts.append("|---|---|---:|---:|---:|---:|---:|---:|")
for _, r in O["Ctab"].iterrows():
    parts.append(f"| {r.scope} | {r.status} | {r.n:,} | {r.n_21b:,} | {r.share_21b_count:.3f} | {r.value_bn_2025TRY:.2f} | "
                 f"{r.value_21b_bn:.2f} | {r.share_21b_value:.3f} |")
parts.append("\n| test | estimate | SE | p | N | clusters |\n|---|---:|---:|---:|---:|---|")
for _, r in O["Cinf"].iterrows():
    se = "" if pd.isna(r.se) else f"{r.se:.4f}"
    parts.append(f"| {r.test} | {r.estimate:.4f} | {se} | {r.p:.2e} | {r.N:,} | {r.clusters if not (isinstance(r.clusters, float) and np.isnan(r.clusters)) else ''} |")
parts.append("\nBy period (count shares):\n\n| period | status | n | share 21(b) |\n|---|---|---:|---:|")
for _, r in O["Cper"].iterrows():
    parts.append(f"| {'post' if r.post7144 else 'pre'}-7144 | {r.dyad_status} | {r.n:,} | {r.share_21b:.3f} |")

parts.append("\n### Table D0. Bid-count sample coverage by year (main sample)\n")
cv = O["cover"]
parts.append("| year | contracts in main sample | sampled tenders in main | with bid counts | design weight |\n|---|---:|---:|---:|---:|")
for y, r in cv.iterrows():
    w = "—" if pd.isna(r.weight) else f"{r.weight:.2f}"
    parts.append(f"| {y} | {int(r.pop_main):,} | {int(r.drawn_in_main)} | {int(r.with_bids)} | {w} |")
parts.append("\n### Table D1. Design-weighted single-bid rates (95% CI, logit-transformed linearization CI)\n")
parts.append("| outcome | breakdown | group | rate | SE | 95% CI | n | events |\n|---|---|---|---:|---:|---:|---:|---:|")
for _, r in O["Dtab"].iterrows():
    ci = "—" if pd.isna(r.lo95) else f"[{r.lo95:.3f}, {r.hi95:.3f}]"
    parts.append(f"| {r.outcome} | {r.breakdown} | {r.group} | {r.rate_w:.3f} | {r.se:.3f} | {ci} | {r.n} | {r.n_events} |")
parts.append("\n### Table D2. Contrasts (design-weighted differences, stratified linearization)\n")
parts.append("| outcome | contrast | diff | SE | 95% CI | p |\n|---|---|---:|---:|---:|---:|")
for _, r in O["Ddiff"].iterrows():
    parts.append(f"| {r.outcome} | {r.contrast} | {r['diff']:.3f} | {r.se:.3f} | [{r.lo95:.3f}, {r.hi95:.3f}] | {fp(r.p)} |")
da = O["Dadj"]
parts.append(f"\nAdjusted logit (defined-incumbency tenders only, n={da['n']}): single bid ~ incumbent + negotiated + year; "
             f"buyer-clustered. OR(incumbent) = {da['OR_inc']:.2f} [{da['lo']:.2f}, {da['hi']:.2f}], p = {fp(da['p'])}; "
             f"OR(negotiated) = {da['OR_neg']:.2f}, p = {fp(da['p_neg'])}.\n")
parts.append("### Table D3. Trend test (logit of single bid on year, centred 2018)\n")
parts.append("| outcome | model | b(year) | SE | OR/year | p | N |\n|---|---|---:|---:|---:|---:|---:|")
for _, r in O["trend"].iterrows():
    parts.append(f"| {r.outcome} | {r.model} | {r.b_year:.4f} | {r.se:.4f} | {r.OR_per_year:.3f} | {fp(r.p)} | {r.N} |")
parts.append("\n### Table D4. Document downloaders vs bids (tenders with downloaders > 0; design-weighted means)\n")
parts.append("| subset | variable | mean | SE | 95% CI | n |\n|---|---|---:|---:|---:|---:|")
for _, r in O["gaps"].iterrows():
    parts.append(f"| {r.subset} | {r.variable} | {r.mean_w:.3f} | {r.se:.3f} | [{r.lo95:.3f}, {r.hi95:.3f}] | {r.n} |")
(RES / "_tables.md").write_text("\n".join(parts), encoding="utf-8")
print("tables written")
