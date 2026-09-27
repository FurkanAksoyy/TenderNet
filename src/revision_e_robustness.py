"""Prespecified category/coverage stress tests; run: python src/revision_e_robustness.py.

All permutations retain observed contracts, dates, buyers and within-cell supplier
win totals. Categories are classification stress tests, not established markets.
"""
import os
for _var in ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_var] = "1"

from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from lockin_analysis import prepare, incumbent, permute_within, summarize, cells

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "revision_e_robustness"
B, SEED = 1000, 20260927
MERGE = {"ERP_management_software", "custom_software_web_mobile",
         "maintenance_support_services", "other_IT"}


def run_one(label, data, category_free=False, start_year=None):
    p = prepare(data, inc_market_col=None if category_free else "urun_pazari")
    df = p["df"]
    if category_free:
        cell = pd.factorize(df["yil_v3"].astype(str) + "|" + df["il"].fillna("NA").astype(str))[0]
        held = "year x buyer province; no category restriction"
    else:
        cell = cells(df, "N3")
        held = "variant category x year x buyer province"
    evaluation = np.ones(len(df), dtype=bool)
    if start_year is not None:
        evaluation &= df["date"].dt.year.to_numpy() >= start_year
    eligible = p["elig"] & evaluation
    observed_flags = incumbent(p, p["firm"])
    observed = observed_flags[eligible].mean()
    # Reset the fixed seed for each variant; variants are not independent studies.
    rng = np.random.default_rng(SEED)
    draws = np.empty(B)
    for j in range(B):
        shuffled = permute_within(p["firm"], cell, rng)
        draws[j] = incumbent(p, shuffled)[eligible].mean()
    sizes = np.bincount(cell)
    unique_firms = pd.DataFrame({"cell": cell, "firm": p["firm"]}).groupby("cell")["firm"].nunique()
    can_change = unique_firms.reindex(cell).to_numpy() > 1
    answer = dict(variant=label, history_contracts=len(df), evaluation_contracts=int(evaluation.sum()),
                  eligible=int(eligible.sum()), incumbent_wins=int(observed_flags[eligible].sum()),
                  **{k: float(v) for k, v in summarize(observed, draws, B).items()},
                  cells=len(sizes), singleton_contract_share=float((sizes[cell] == 1).mean()),
                  movable_contract_share=float(can_change.mean()),
                  movable_eligible_share=float(can_change[eligible].mean()),
                  earliest_history=str(df.date.min().date()), latest_history=str(df.date.max().date()),
                  evaluate_from_year=start_year, held_fixed_cells=held,
                  history_retained=True, permutations=B, seed=SEED)
    pd.DataFrame({"replication": np.arange(1, B + 1), "null_incumbency": draws}).to_csv(OUT / f"{label}_draws.csv", index=False)
    print(f"{label}: eligible={answer['eligible']}, observed={observed:.4f}, null={draws.mean():.4f}, ratio={answer['ratio']:.3f}", flush=True)
    return answer


def class_audit(master):
    """Report available AI agreement; never treat agreement as human accuracy."""
    folder = ROOT / "data" / "audit" / "ai_coding"
    needed = [folder / name for name in ("blind_markets_input.csv", "coderA_markets.csv", "coderB_markets.csv")]
    if not all(path.exists() for path in needed):
        return {"available": False, "reason": "Required AI audit files missing; no labels imputed."}
    sample, a, b = (pd.read_csv(path, dtype=str) for path in needed)
    if any(table.IKN.duplicated().any() for table in (sample, a, b)):
        raise ValueError("Duplicate audit IDs")
    rules = master[["IKN", "urun_pazari"]].copy()
    if rules.IKN.duplicated().any():
        raise ValueError("Master tender IDs are not unique")
    joined = sample[["IKN"]].merge(rules, on="IKN", how="left", validate="one_to_one")
    joined = joined.merge(a[["IKN", "label"]].rename(columns={"label": "coderA"}), on="IKN", how="left", validate="one_to_one")
    joined = joined.merge(b[["IKN", "label"]].rename(columns={"label": "coderB"}), on="IKN", how="left", validate="one_to_one")
    ok = joined[["coderA", "coderB", "urun_pazari"]].notna().all(axis=1)
    common = ok & joined.coderA.eq(joined.coderB)
    joined["AI_common_label"] = joined.coderA.where(common)
    joined.to_csv(OUT / "AI_agreement_audit_records.csv", index=False)
    rows = []
    labels = sorted(set(joined.urun_pazari.dropna()) | set(joined.coderA.dropna()) | set(joined.coderB.dropna()))
    for label in labels:
        rules_here = joined.urun_pazari.eq(label)
        reference = common & joined.coderA.eq(label)
        predicted = common & rules_here
        tp = int((reference & rules_here).sum())
        rows.append(dict(category=label, rule_n_all=int(rules_here.sum()),
                         rule_n_with_complete_AI=int((rules_here & ok).sum()),
                         rule_n_AI_disagreement=int((rules_here & ok & ~common).sum()),
                         AI_common_n=int(reference.sum()), rule_n_common_subset=int(predicted.sum()),
                         matches=tp, precision_vs_AI_common=tp / predicted.sum() if predicted.sum() else np.nan,
                         recall_vs_AI_common=tp / reference.sum() if reference.sum() else np.nan))
    pd.DataFrame(rows).to_csv(OUT / "AI_common_class_stats.csv", index=False)
    for coder in ("coderA", "coderB"):
        pd.crosstab(joined.loc[ok, "urun_pazari"], joined.loc[ok, coder], dropna=False).to_csv(OUT / f"rule_vs_{coder}_confusion.csv")
    return dict(available=True, sample_n=len(joined), complete_n=int(ok.sum()), common_n=int(common.sum()),
                disagreement_n=int((ok & ~common).sum()),
                rule_agreement_coderA=float(joined.loc[ok, "urun_pazari"].eq(joined.loc[ok, "coderA"]).mean()),
                rule_agreement_coderB=float(joined.loc[ok, "urun_pazari"].eq(joined.loc[ok, "coderB"]).mean()),
                rule_agreement_AI_common=float(joined.loc[common, "urun_pazari"].eq(joined.loc[common, "coderA"]).mean()),
                interpretation="AI agreement audit, not human accuracy; consensus conditions on easier/agreed cases.")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / "data" / "contracts_v3.csv"
    data = pd.read_csv(source, encoding="utf-8-sig", low_memory=False)
    data["date"] = pd.to_datetime(data.tarih_v3, errors="raise")
    main_data = data.loc[data.in_scope_main.astype(str).str.lower().eq("true")].copy()
    if main_data.empty or main_data[["kurum_il_split", "firma_v3", "urun_pazari", "date", "yil_v3"]].isna().any().any():
        raise ValueError("Missing required analysis identifiers or empty main sample")
    if not MERGE.issubset(set(main_data.urun_pazari)):
        raise ValueError("Expected merge categories absent")
    coarse = main_data.copy()
    coarse.loc[coarse.urun_pazari.isin(MERGE), "urun_pazari"] = "software_services"
    # Fixed list, declared before computing any stress-test outcome.
    variants = [("baseline", main_data, False, None),
                ("merged_software_services", coarse, False, None),
                ("category_free_buyer", main_data, True, None),
                ("health_only", main_data.loc[main_data.urun_pazari.eq("health_information_systems")], False, None),
                ("evaluate_2013_onward", main_data, False, 2013),
                ("evaluate_2015_onward", main_data, False, 2015),
                ("exclude_other_IT", main_data.loc[~main_data.urun_pazari.eq("other_IT")], False, None)]
    rows = [run_one(*variant) for variant in variants]
    pd.DataFrame(rows).to_csv(OUT / "robustness_summary.csv", index=False)
    audit = class_audit(data)
    with (OUT / "AI_agreement_summary.json").open("w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)
    # Hash only analysis columns: currency revisions have no bearing on these results.
    columns = ["IKN", "tarih_v3", "yil_v3", "kurum_il_split", "firma_v3", "urun_pazari", "il", "in_scope_main"]
    digest = hashlib.sha256(data[columns].to_csv(index=False).encode()).hexdigest()
    metadata = dict(permutations=B, seed=SEED, analysis_columns=columns,
                    analysis_columns_sha256=digest, variants=[v[0] for v in variants],
                    BLAS_threads=1, source="data/contracts_v3.csv")
    (OUT / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    lines = ["# Classification and observed-history stress tests", "",
             "Prespecified variants; 1,000 within-cell permutations per variant; fixed seed 20260927. "
             "Incumbency requires a strictly earlier tender date. Calendar-year demand, buyer identities, dates, "
             "and supplier win totals within each reported cell remain fixed. Null intervals are permutation percentiles, not confidence intervals for the observed rate.", "",
             "| Variant | History N | Evaluation N | Eligible | Observed | Null mean [2.5%,97.5%] | Ratio | Upper-tail p |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['variant']} | {r['history_contracts']} | {r['evaluation_contracts']} | {r['eligible']} | {r['obs']:.4f} | {r['null_mean']:.4f} [{r['null_lo']:.4f}, {r['null_hi']:.4f}] | {r['ratio']:.3f} | {r['p_upper']:.6f} |")
    lines += ["", "All variants use category x year x buyer-province cells, except category-free buyer incumbency, which uses year x buyer province. "
              "The merged variant changes both the history category and the null category. It merges ERP, custom software, maintenance and other IT into software_services solely as a taxonomic stress test; it does not establish an economic relevant market.", "",
              "Later evaluation windows retain all pre-window observed history in both observed and permuted records. "
              "Health-only and no-other-IT variants restrict the sample before computing histories. All null draws and cell-mobility diagnostics are saved. "
              "Movable means a cell contains at least two distinct supplier labels; it does not guarantee a given record moves in each draw.", "",
              "The keyword-defined extract does not measure national IT procurement coverage or identify omitted titles. "
              "2010 and 2026 are partial years (October 2010–March 2026 in the present extract). Later outcome windows cannot recover pre-2010 history or correct changes in keyword capture. "
              "No variant establishes switching costs, corruption, or causal effects. Permutation p=(1+exceedances)/(1001); resolution is 1/1001. "
              "These correlated sensitivity checks are not independent replications.", "", "## Available AI agreement audit", "", json.dumps(audit, indent=2), "",
              "Class-level rule denominators, AI-consensus denominators, disagreements, and pairwise confusion matrices accompany this report. "
              "Two model labels are not human truth, and consensus-only agreement can overstate performance on difficult titles."]
    (OUT / "robustness_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
