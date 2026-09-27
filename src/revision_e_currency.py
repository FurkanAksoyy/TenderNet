"""Currency-assumption sensitivity and corrected nominal-value audit screen.

Runs independently from released data. Histories are built on all observed main
contracts before excluding rows from regression estimation; missing currencies
do not erase the evidence that an earlier buyer-supplier relationship existed.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from models_common import ROOT, load, ols_scores, twoway_vcov
from models_features import contract_history

OUT = ROOT / "results" / "revision_e_currency"


def hhi_table(data):
    rows = []
    for variant, d in [("main_assumed_TRY", data),
                       ("explicit_currency_only", data[data.bedel_currency_status == "explicit"])]:
        for market, g in [("ALL", d), *list(d.groupby("market"))]:
            totals = g.groupby("firm").real_value.sum()
            counts = g.groupby("firm").size()
            rows.append({"variant": variant, "market": market, "n": len(g), "n_firms": len(totals),
                         "nominal_TRY": g.bedel_try.sum(), "real_2025_TRY": g.real_value.sum(),
                         "HHI_value": 10000 * ((totals / totals.sum()) ** 2).sum(),
                         "HHI_count": 10000 * ((counts / counts.sum()) ** 2).sum()})
    return pd.DataFrame(rows)


def model_sensitivity(data):
    history = contract_history(data)
    eligible = history[history.buyer_has_history == 1].copy()
    eligible["log_prior_suppliers"] = np.log(eligible.bm_prior_suppliers)
    eligible["log_prior_contracts"] = np.log(eligible.bm_prior_contracts)
    eligible["years_since_first"] = eligible.bm_years_since_first
    eligible["p_21b"] = (eligible.proc == "21b").astype(float)
    eligible["p_oth_neg"] = (eligible.proc == "oth_neg").astype(float)
    eligible["p21b_x_post"] = eligible.p_21b * eligible.post7144
    eligible["yearfe"] = eligible.year.clip(lower=2011)
    core = ["p_21b", "p_oth_neg", "log_real_value", "log_prior_suppliers", "log_prior_contracts",
            "years_since_first", "post7144", "p21b_x_post"]
    rows = []
    for variant, d in [("main_assumed_TRY", eligible),
                       ("explicit_currency_only", eligible[eligible.bedel_currency_status == "explicit"])]:
        parts = [d[core].astype(float)]
        for col in ["yearfe", "market", "sektor_v3"]:
            parts.append(pd.get_dummies(d[col], prefix=col, drop_first=True, dtype=float))
        X = sm.add_constant(pd.concat(parts, axis=1), has_constant="add")
        fit = sm.OLS(d.incumbent_win, X).fit()
        scores, hinv = ols_scores(X.to_numpy(), d.incumbent_win.to_numpy(), fit.params.to_numpy())
        covariance, clusters, clipped = twoway_vcov(scores, hinv, d.buyer, d.firm)
        for term in core:
            idx = X.columns.get_loc(term)
            coef = fit.params[term]
            se = np.sqrt(covariance[idx, idx])
            rows.append({"variant": variant, "term": term, "n": len(d), "coef": coef, "se": se,
                         "ci_low": coef - 1.96 * se, "ci_high": coef + 1.96 * se,
                         "buyer_clusters": clusters[0], "firm_clusters": clusters[1],
                         "clipped_vcov_eigenvalues": clipped})
    return pd.DataFrame(rows)


def corrected_audit_screen():
    data = pd.read_csv(ROOT / "data/contracts_v3.csv", low_memory=False)
    legacy = pd.read_csv(ROOT / "data/audit/top150_value_review.csv")
    screen = data.sort_values(["bedel_try", "IKN"], ascending=[False, True]).head(150).copy()
    screen.insert(0, "corrected_nominal_TRY_rank", range(1, len(screen) + 1))
    screen["legacy_review_rank"] = screen.IKN.map(legacy.set_index("IKN")["rank"])
    screen["legacy_scope_review_recorded"] = screen.IKN.isin(legacy.IKN)
    screen["new_scope_review_required"] = ~screen.legacy_scope_review_recorded
    screen["currency_independently_reverified"] = False
    # Official DHMI tender notice, inspected in this revision: page 1 matches
    # IKN and eight de-icing vehicles; page 3 gives 01.09.2023. This corroborates
    # scope/identity only, not the award price or a human validation exercise.
    source_url = "https://www.dhmi.gov.tr/Lists/IhaleIlanlari/Attachments/1455/ihale%20ilan%C4%B1-de.%C4%B1c%C4%B1ng.pdf"
    screen["ai_assisted_official_scope_check"] = screen.IKN.eq("2023/670417")
    screen["ai_scope_source_url"] = np.where(screen.ai_assisted_official_scope_check, source_url, "")
    cols = ["corrected_nominal_TRY_rank", "legacy_review_rank", "IKN", "bedel", "bedel_num",
            "bedel_amount_original", "bedel_currency", "bedel_currency_status", "bedel_try",
            "bedel_fx_date", "bedel_valuation_method", "scope_v3", "scope_reason", "ihale_adi",
            "legacy_scope_review_recorded", "new_scope_review_required", "currency_independently_reverified",
            "ai_assisted_official_scope_check", "ai_scope_source_url"]
    return screen[cols]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = load("main")
    hhi = hhi_table(data)
    models = model_sensitivity(data)
    screen = corrected_audit_screen()
    hhi.to_csv(OUT / "currency_exclusion_hhi.csv", index=False)
    models.to_csv(OUT / "currency_exclusion_A1_LPM.csv", index=False)
    screen.to_csv(OUT / "corrected_top150_value_screen.csv", index=False, encoding="utf-8-sig")
    unknown = data[data.bedel_currency_status != "explicit"]
    metadata = {"main_n": len(data), "unknown_currency_excluded": len(unknown),
                "explicit_currency_n": len(data) - len(unknown),
                "unknown_real_value_share": unknown.real_value.sum() / data.real_value.sum(),
                "corrected_top150_new_scope_reviews_needed": int(screen.new_scope_review_required.sum()),
                "screen_is_new_manual_validation": False,
                "regression_history": "all main observations retained; exclusion affects estimation rows only",
                "regression_specification": "linear probability sensitivity with A1 controls; buyer and winning-firm two-way clustered covariance"}
    (OUT / "currency_sensitivity_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    lines = ["# Currency-assumption sensitivity", "",
             f"Main N={len(data):,}; exclusion removes {len(unknown):,} unspecified-currency records "
             f"({metadata['unknown_real_value_share']:.2%} of main real value), leaving {len(data)-len(unknown):,}.", "",
             "Explicit currencies are USD/EUR/TRY labels in the preserved source string; this is not independent source revalidation. "
             "Missing labels are assumed TRY in the primary specification. Exclusion changes sample composition and is a sensitivity, not an imputation or identified bound.", "",
             "## HHI point estimates", "", "| Market | Main value HHI | Explicit-currency value HHI |", "|---|---:|---:|"]
    for market in hhi.market.unique():
        r = hhi[hhi.market == market].set_index("variant")
        lines.append(f"| {market} | {r.loc['main_assumed_TRY', 'HHI_value']:.3f} | {r.loc['explicit_currency_only', 'HHI_value']:.3f} |")
    lines += ["", "## Contract-level incumbency sensitivity (linear probability model)", "",
              "Same controls and fixed effects as the primary A1 model; histories are constructed before exclusions. "
              "Linear probability coefficients use two-way buyer/winning-firm clustered 95% intervals. The explicit-currency-only A1 logit failed to converge with Newton (200 iterations), so we report comparable linear probability fits for both samples instead of unstable odds ratios. No choice-model or full-pipeline rerun is implied.", "",
              "| Sample | N | Term | Coefficient | 95% interval |", "|---|---:|---|---:|---|"]
    for r in models[models.term.isin(["log_real_value", "p21b_x_post"])].itertuples():
        lines.append(f"| {r.variant} | {r.n} | {r.term} | {r.coef:.4f} | {r.ci_low:.4f}–{r.ci_high:.4f} |")
    lines += ["", "## Corrected top-150 screen", "",
              f"Ranking uses nominal `bedel_try` across all 13,024 records. {metadata['corrected_top150_new_scope_reviews_needed']} "
              "records enter beyond the historical top-150 review. `legacy_scope_review_recorded` documents membership in the archived review; "
              "`new_scope_review_required` identifies entrants. No new hand review or independent currency verification is claimed. "
              "Historical `data/audit/top150_value_review.csv` remains unchanged and was ranked by the mixed-currency legacy numeric amount.", "",
              "The entrant IKN 2023/670417 has an AI-assisted official-source scope check: the "
              "[DHMI tender notice](https://www.dhmi.gov.tr/Lists/IhaleIlanlari/Attachments/1455/ihale%20ilan%C4%B1-de.%C4%B1c%C4%B1ng.pdf) "
              "identifies eight de-icing vehicles and the exact IKN on page 1, with tender date 01.09.2023 on page 3. "
              "This corroborates the existing non-IT scope label and tender identity. It is not new human validation; "
              "the EUR 2,631,200 award amount has not been independently verified against an official award-price source.", ""]
    (OUT / "currency_results.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
