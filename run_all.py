"""Run the full TenderNet v3 analysis pipeline in the correct order.

    python run_all.py               # everything (about 2 h on a laptop; revision_d ~76 min, network nulls ~30 min)
    python run_all.py --skip-slow   # skip slow steps (revision_d, network nulls); reuse their committed results
    python run_all.py --only lockin models   # run selected steps (see STEPS)

Inputs:  data/contracts_v3.csv, data/cpi_turkey*.csv, data/ppi_turkey_yiufe.csv,
         data/bid_counts_sample.csv, data/bid_counts_cp2.csv
Outputs: results/<topic>/, figures/, paper/si_tables/ ; per-step logs in results/logs/
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

# (step name, script in src/, slow?) -- order matters: later steps read earlier outputs.
# To add an analysis, drop the script into src/ and append (or insert) one tuple here;
# `--only <name>` then runs it alone and `--skip-slow` skips it if flagged slow.
STEPS = [
    ("currency", "build/normalize_currency.py", False), # offline TCMB FX normalization
    ("concentration", "concentration_v3.py", False),     # Table 1, Fig 1 (F-C1), SI Fig F-C2
    ("lockin", "lockin_analysis.py", False),             # Table 2, Figs F_L1-F_L3 (1,000 permutations)
    ("models", "models_analysis.py", False),             # Table 3, single-bid sample
    ("models_report", "models_report.py", False),        # results/models/models_results.md
    ("models_figures", "models_figures.py", False),      # F-R1, F-R2
    ("revision_a", "revision_a.py", False),              # renewals, N4 nulls, conditional logit, BH, cp2 single bid; F-A1 (~6 min)
    ("revision_b", "revision_b.py", False),              # 21(b) logit variants, event study F-B1, descriptives, PPI robustness
    ("revision_c", "revision_c.py", False),              # leakage-free choice model (24-month pools), future-supplier placebo + simulation, N4 nulls, exclusivity, single-bid renewal controls
    ("revision_d", "revision_d.py", True),               # legacy conditional simulation scenarios, F-D1, F-L1b (~76 min)
    ("taxonomy_history", "revision_e_robustness.py", False), # 1,000-draw taxonomy / observed-history stress tests
    ("bounded_horizons", "revision_e_horizons.py", False), # equal observed past/future windows
    ("currency_sensitivity", "revision_e_currency.py", False), # unspecified-currency exclusion
    ("sampling_provenance", "revision_e_sampling.py", False), # public aggregate reconstruction
    ("choice_numerics", "audit_choice_numerics.py", False), # saved/refit observed choice-model scores
    ("initial_conditions", "revision_e_initial_conditions.py", True), # 100 draws/scenario plus calibration
    ("price", "price_analysis.py", False),               # discounts in the 144-tender estimated-cost sample
    ("coder_agreement", "coder_agreement.py", False),    # agreement of blind AI coders with the rules and earlier labels
    ("network", "network_analysis.py", True),            # curveball nulls, Louvain stability (~30 min)
    ("network_projections", "network_projections.py", False),  # BiCM projections, brokerage (~3 min)
    ("network_figures", "network_figures.py", False),    # fig_N1_core_network
    ("bibliography", "merge_bib.py", False),             # deterministic source bibliography merge
    ("si_tables", "make_si_tables.py", False),           # paper/si_tables/*.tex
    ("paper_assets", "refresh_paper_assets.py", False),   # labels and current paper figure copies
    ("check", "check_headlines.py", False),              # compare headline numbers with the paper
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-slow", action="store_true",
                    help="skip slow steps (revision_d.py, network_analysis.py); later steps reuse their committed outputs")
    ap.add_argument("--only", nargs="+", choices=[s[0] for s in STEPS], help="run only these steps")
    a = ap.parse_args()

    logs = ROOT / "results" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8", PYTHONHASHSEED="0",
               OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t_all = time.time()
    for name, script, slow in STEPS:
        if a.only and name not in a.only:
            continue
        if slow and a.skip_slow:
            print(f"[skip] {name:20s} ({script}; slow step, using committed outputs)")
            continue
        t0 = time.time()
        print(f"[run ] {name:20s} {script} ...", flush=True)
        with open(logs / f"{name}.log", "w", encoding="utf-8") as fh:
            r = subprocess.run([sys.executable, "-B", script], cwd=SRC, env=env, stdout=fh, stderr=subprocess.STDOUT)
        dt = time.time() - t0
        if r.returncode != 0:
            print(f"[FAIL] {name} after {dt:.0f}s -- see results/logs/{name}.log")
            sys.exit(r.returncode)
        print(f"[ ok ] {name:20s} {dt:7.0f}s")
    print(f"done in {time.time() - t_all:.0f}s")


if __name__ == "__main__":
    main()
