"""Agreement between independent (blind) coders, the rule-based classifiers, and the earlier check.

Inputs (data/audit/ai_coding/): coderA_*.csv, coderB_*.csv (AI coders), optionally human_*.csv (same format).
Reference: rule-based product market (data/contracts_v3.csv urun_pazari) and rule-based renewal
flag (similarity >= 0.5, from results/revision_a/A_renewal_validation_sample.csv).
Output: results/coder_agreement/coder_agreement_results.md
"""
from itertools import combinations
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / "data" / "audit" / "ai_coding"
OUT = ROOT / "results" / "coder_agreement"
OUT.mkdir(parents=True, exist_ok=True)

master = pd.read_csv(ROOT / "data" / "contracts_v3.csv", usecols=["IKN", "urun_pazari"], low_memory=False)
rules_m = master.drop_duplicates("IKN").set_index("IKN")["urun_pazari"]
prev = pd.read_csv(ROOT / "data" / "audit" / "classifier_validation.csv").set_index("IKN")["your_label"]

pairs = pd.read_csv(ROOT / "results" / "revision_a" / "A_renewal_validation_sample.csv").set_index("pair_id")
rule_r = (pairs["sim"] >= 0.5).map({True: "same", False: "different"})
prev_r = pd.read_csv(ROOT / "results" / "revision_a" / "A_renewal_validation_labels.csv").set_index("pair_id")["hand_label"]

coders_m = {"rules": rules_m, "earlier_AI_check": prev}
coders_r = {"rule_sim>=0.5": rule_r, "earlier_AI_check": prev_r}
for f in sorted(AI.glob("*_markets.csv")):
    d = pd.read_csv(f).set_index("IKN")
    coders_m[f.stem.replace("_markets", "")] = d["label"]
for f in sorted(AI.glob("*_renewals.csv")):
    d = pd.read_csv(f).set_index("pair_id")
    coders_r[f.stem.replace("_renewals", "")] = d["decision"]

sample_m = pd.read_csv(AI / "blind_markets_input.csv")["IKN"]
sample_r = pd.read_csv(AI / "blind_renewals_input.csv")["pair_id"]
lines = ["# Coder agreement", "", "## Product markets (300 titles)", "", "| coder 1 | coder 2 | n | agreement | kappa |", "|---|---|---|---|---|"]
for a, b in combinations(coders_m, 2):
    x, y = coders_m[a].reindex(sample_m), coders_m[b].reindex(sample_m)
    ok = x.notna() & y.notna()
    lines.append(f"| {a} | {b} | {ok.sum()} | {(x[ok] == y[ok]).mean():.3f} | {cohen_kappa_score(x[ok], y[ok]):.3f} |")

# per-class precision/recall of the rules against the majority of independent AI coders
indep = [c for c in coders_m if c.startswith("coder")]
if len(indep) >= 2:
    df = pd.DataFrame({c: coders_m[c].reindex(sample_m).values for c in indep + ["rules"]}, index=sample_m)
    consensus = df[indep].apply(lambda r: r.iloc[0] if (r == r.iloc[0]).all() else None, axis=1)
    ok = consensus.notna()
    lines += ["", f"Titles where all independent coders agree: {ok.sum()} of {len(df)}; rules agree with that consensus on {(df.loc[ok, 'rules'] == consensus[ok]).mean():.3f}.", "",
              "| market | n (consensus) | rule precision | rule recall |", "|---|---|---|---|"]
    for mk in sorted(set(consensus[ok])):
        tp = ((df.loc[ok, "rules"] == mk) & (consensus[ok] == mk)).sum()
        pr = tp / max((df.loc[ok, "rules"] == mk).sum(), 1)
        rc = tp / max((consensus[ok] == mk).sum(), 1)
        lines.append(f"| {mk} | {(consensus[ok] == mk).sum()} | {pr:.2f} | {rc:.2f} |")

lines += ["", "## Renewal pairs (60)", "", "| coder 1 | coder 2 | n | agreement | kappa |", "|---|---|---|---|---|"]
for a, b in combinations(coders_r, 2):
    x = coders_r[a].reindex(sample_r).astype(str).str.lower().str.strip()
    y = coders_r[b].reindex(sample_r).astype(str).str.lower().str.strip()
    x = x.replace({"same recurring need": "same", "different need": "different", "ambiguous": "unclear"})
    y = y.replace({"same recurring need": "same", "different need": "different", "ambiguous": "unclear"})
    ok = (x != "nan") & (y != "nan")
    lines.append(f"| {a} | {b} | {ok.sum()} | {(x[ok] == y[ok]).mean():.3f} | {cohen_kappa_score(x[ok], y[ok]):.3f} |")

# precision of the similarity rule against each independent coder
lines += ["", "| coder | pairs flagged renewal by rule | of which coder says 'same' | pairs below threshold coder says 'same' |", "|---|---|---|---|"]
for c in [k for k in coders_r if k.startswith("coder") or k.startswith("human")]:
    y = coders_r[c].reindex(sample_r).astype(str).str.lower()
    r = rule_r.reindex(sample_r)
    lines.append(f"| {c} | {(r == 'same').sum()} | {((r == 'same') & (y == 'same')).sum()} | {((r == 'different') & (y == 'same')).sum()} of {(r == 'different').sum()} |")

(OUT / "coder_agreement_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
