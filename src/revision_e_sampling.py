"""Sampling counts with no raw-person records in outputs.

Default: rebuild released-data counts and combine the committed private-source
aggregate snapshot. --private-root optionally verifies the original local files
and refreshes aggregate snapshots; private inputs are never copied into outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/revision_e_sampling"
sys.path.insert(0, str(ROOT / "src/collection"))
from ekap_v3_query_provenance import ARAMA_KELIMELERI


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    public = pd.read_csv(ROOT / "data/contracts_v3.csv", low_memory=False)
    assert public.IKN.is_unique
    main_data = public[public.in_scope_main]
    if args.private_root:
        base = args.private_root
        files = {"collector": "03_SCRAPER/ekap_v3.py", "cp1": "03_SCRAPER/ekap_v3_cp1.json",
                 "cp2_partial": "03_SCRAPER/ekap_v3_cp2.json", "winner_edges": "02_VERI/ekap_v8_kazandi_edge.csv",
                 "winner_master": "06_YENI_ANALIZ/master_sozlesmeler.csv",
                 "cleaned_master": "06_YENI_ANALIZ/master_sozlesmeler_temiz.csv"}
        cp1 = pd.DataFrame(json.loads((base / files["cp1"]).read_text(encoding="utf-8"))["satirlar"])
        raw = pd.read_csv(base / files["winner_master"], usecols=["IKN"])
        edges = pd.read_csv(base / files["winner_edges"], usecols=["IKN", "kaynak_tip"])
        clean = pd.read_csv(base / files["cleaned_master"], usecols=["IKN"])
        for d in (cp1, raw, edges, clean):
            assert d.IKN.is_unique
        assert set(edges.IKN) == set(raw.IKN)
        assert set(clean.IKN) == set(public.IKN)
        assert set(public.IKN) <= set(raw.IKN) <= set(cp1.IKN)
        assert public.kaynak_keyword.equals(public.IKN.map(cp1.set_index("IKN").kaynak_keyword))
        cp1["year"] = pd.to_datetime(cp1.ihale_tarihi).dt.year
        winner = cp1[cp1.IKN.isin(raw.IKN)]
        for col, filename in [("year", "upstream_counts_by_year.csv"), ("kaynak_keyword", "upstream_counts_by_keyword.csv")]:
            upstream = pd.concat([cp1.groupby(col).size().rename("checkpoint_unique_tenders"),
                                  winner.groupby(col).size().rename("winner_master_records")], axis=1).fillna(0).astype(int)
            upstream.to_csv(OUT / filename)
        metadata = {"source_files": [{"path": p, "sha256": hashlib.sha256((base/p).read_bytes()).hexdigest()} for p in files.values()],
                    "checkpoint_unique_n": len(cp1), "winner_n": len(raw), "cleaned_n": len(clean),
                    "public_n": len(public), "main_n": len(main_data),
                    "cp1_min_tender_date": cp1.ihale_tarihi.min(), "cp1_max_tender_date": cp1.ihale_tarihi.max(),
                    "source_code_keywords_n": len(ARAMA_KELIMELERI), "cp1_contributing_keywords_n": cp1.kaynak_keyword.nunique(),
                    "winner_source_type_counts": edges.kaynak_tip.value_counts().to_dict(),
                    "extraction_timestamp": None, "executed_query_start": None, "executed_query_end": None,
                    "query_status": "settings documented from current source; executed runtime settings unrecorded",
                    "membership_checks": "winner edges == winner master; public == cleaned; public subset winner subset cp1; all unique IKN; public keywords match cp1",
                    "private_rows_exported": False}
        (OUT / "sampling_provenance_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    for col, filename in [("yil_v3", "annual_sampling_counts.csv"), ("kaynak_keyword", "keyword_sampling_counts.csv")]:
        key = "year" if col == "yil_v3" else col
        upstream = pd.read_csv(OUT / ("upstream_counts_by_year.csv" if key == "year" else "upstream_counts_by_keyword.csv")).set_index(key)
        kept = public.groupby(col).size().rename("retained_release_records")
        main_counts = main_data.groupby(col).size().rename("main_IT_records")
        counts = pd.concat([upstream, kept, main_counts], axis=1)
        if key == "kaynak_keyword":
            counts = counts.reindex(ARAMA_KELIMELERI)
        else:
            counts = counts.reindex(range(2009, int(counts.index.max()) + 1))
        counts = counts.fillna(0).astype(int)
        counts.index.name = key
        counts["early_excluded"] = counts.winner_master_records - counts.retained_release_records
        counts["outside_main_after_cleaning"] = counts.retained_release_records - counts.main_IT_records
        assert counts.retained_release_records.sum() == len(public)
        assert counts.main_IT_records.sum() == len(main_data)
        assert (counts.early_excluded >= 0).all()
        counts.to_csv(OUT / filename, encoding="utf-8-sig")
    print(f"Sampling aggregates: public={len(public)}, main={len(main_data)}, configured keywords={len(ARAMA_KELIMELERI)}")


if __name__ == "__main__":
    main()
