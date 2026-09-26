# -*- coding: utf-8 -*-
"""Create the public release dataset data/contracts_v3.csv from the internal master_v3.csv.

Privacy (KVKK, Law 6698): supplier names that may identify a natural person are replaced by
stable pseudonyms. A supplier string is pseudonymized when
  (a) the build heuristic flagged it (is_natural_person / contains_natural_person), OR
  (b) it -- or, for joint ventures, any of its comma-separated members -- carries no explicit
      legal-entity form (A.S., Ltd., Sti., cooperative, foundation, foreign company forms, ...).
Rule (b) is deliberately conservative: sole proprietorships (whose trade names contain the
owner's name), person-only partnerships and a few truncated company names are pseudonymized too.

The mapping string -> pseudonym is one-to-one and shared by all firm-name columns
(firma, firma_v2, firma_v3), so every analysis gives the same results as on the internal file
(up to Monte-Carlo ordering effects, see data/README.md). The mapping itself is NOT released.

Requires the internal file (not distributed); run from the repository root:
    python src/build/make_release_data.py --master PATH/TO/master_v3.csv --name-map PATH/TO/firm_name_map_v3.csv
"""
import argparse
import hashlib
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
NAME_COLS = ["firma", "firma_v2", "firma_v3"]

LEGAL = re.compile("|".join([
    r"\bA\s?\.\s?Ş", r"\bAŞ\b",r"ANON[İI]M", r"L[İI]M[İI]TED", r"L[İI]M[İI]TET", r"\bLTD", r"\bLT\b",
    r"\bLT\.", r"ŞT[İI]", r"\bŞT\b", r"Ş[İI]RKET", r"Ş[İI]RK\b", r"Ş[İI]RT\b", r"KOOP", r"\bKOP\b", r"\bS\.\s?S\.",
    r"VAKF", r"VAKIF", r"DERNEĞ", r"SEND[İI]KA", r"[İI]KT[İI]SAD[İI] [İI]ŞLETME", r"ÜN[İI]VERS[İI]TE",
    r"MÜDÜRLÜĞÜ", r"BAŞKANLIĞI", r"BAKANLIĞI", r"BELED[İI]YES[İI]", r"KURUMU\b",
    r"\bGMBH", r"\bINC\b", r"\bLLC\b", r"\bS\.?P\.?A\b", r"\bSA\.?$", r"\bS\.A\.?", r"\bPLC\b", r"\bB\.?V\.?$", r"\bAG$",
    r"CORP", r"COMPANY", r"\bKG$", r"\bSRL\b", r"\bL\.?\s?Ş\b", r"[.\s]L\.?$", r"\bLDT\b",
]), flags=re.I)
JV_SUFFIX = re.compile(r"\s*(İş Ortaklığı|İŞ ORTAKLIĞI|Ortak Girişimi|ORTAK GİRİŞİMİ|Konsorsiyumu?|KONSORSİYUMU?)\.?\s*$")


def tr_upper(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def lacks_legal_form(name):
    base = JV_SUFFIX.sub("", str(name)).strip()
    parts = [p.strip() for p in base.split(",") if p.strip()] or [base]
    return any(not LEGAL.search(tr_upper(p)) for p in parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True, help="internal master_v3.csv (contains names)")
    ap.add_argument("--name-map", required=True, help="internal firm_name_map_v3.csv")
    ap.add_argument("--audit-dir", default=None,
                    help="folder with the internal audit files (top150_value_review.csv, scope_rule_samples.csv, "
                         "product_market_confusion_sample.csv, build_log_v3.txt); default: folder of --master")
    ap.add_argument("--seed", type=int, default=20260926)
    a = ap.parse_args()

    d = pd.read_csv(a.master, encoding="utf-8-sig", low_memory=False)
    fm = pd.read_csv(a.name_map, encoding="utf-8-sig")

    flagged = d.is_natural_person.astype(bool) | d.contains_natural_person.astype(bool)
    names = pd.unique(pd.concat([d[c] for c in NAME_COLS] + [fm.original, fm.canonical_v2, fm.firma_v3]).dropna())
    s_flag = set(pd.concat([d.loc[flagged, c] for c in NAME_COLS]))
    s_flag |= set(pd.concat([fm.loc[fm.is_natural_person | fm.contains_natural_person, c]
                             for c in ["original", "canonical_v2", "firma_v3"]]))
    to_pseudo = sorted({n for n in names if n in s_flag or lacks_legal_form(n)})

    # pseudonym numbers are a seeded random permutation -> they carry no alphabetical information
    rng = np.random.default_rng(a.seed)
    nums = rng.permutation(len(to_pseudo)) + 1
    width = len(str(len(to_pseudo)))
    mapping = {n: f"PSEUDONYM_{k:0{width}d}" for n, k in zip(to_pseudo, nums)}
    assert len(set(mapping.values())) == len(mapping)
    assert not set(mapping.values()) & set(names)

    out = d.copy()
    for c in NAME_COLS:
        out[c] = out[c].map(lambda x: mapping.get(x, x))
    out["name_pseudonymized"] = d.firma_v3.isin(mapping.keys())
    # firm_id was sha1(firma_v3); a hash of a personal name can be reversed with a name list, so rehash
    out["firm_id"] = "F" + out.firma_v3.map(lambda s: hashlib.sha1(s.encode("utf-8")).hexdigest()[:8])
    out = out.drop(columns=["firma_release"])

    # checks: 1:1 relabelling per column
    for c in NAME_COLS:
        assert d[c].nunique() == out[c].nunique(), c
        assert (pd.factorize(d[c])[0] == pd.factorize(out[c])[0]).all(), c
    assert out.firm_id.nunique() == out.firma_v3.nunique()

    (ROOT / "data").mkdir(exist_ok=True)
    out.to_csv(ROOT / "data" / "contracts_v3.csv", index=False, encoding="utf-8-sig")

    fm2 = fm.copy()
    for c in ["original", "canonical_v2", "firma_v3"]:
        fm2[c] = fm2[c].map(lambda x: mapping.get(x, x))
    fm2["firm_id"] = "F" + fm2.firma_v3.map(lambda s: hashlib.sha1(s.encode("utf-8")).hexdigest()[:8])
    fm2["name_pseudonymized"] = fm.firma_v3.isin(mapping.keys())
    fm2 = fm2.drop(columns=["firma_release"])
    fm2.to_csv(ROOT / "data" / "firm_name_map_v3.csv", index=False, encoding="utf-8-sig")

    # audit files: same pseudonyms; the build log is plain text, so names are replaced longest-first
    adir = Path(a.audit_dir) if a.audit_dir else Path(a.master).parent
    aout = ROOT / "data" / "audit"
    aout.mkdir(parents=True, exist_ok=True)
    t = pd.read_csv(adir / "top150_value_review.csv", encoding="utf-8-sig")
    t["firma"] = t.firma.map(lambda x: mapping.get(x, x))
    t.to_csv(aout / "top150_value_review.csv", index=False, encoding="utf-8-sig")
    for f in ["scope_rule_samples.csv", "product_market_confusion_sample.csv"]:
        x = pd.read_csv(adir / f, encoding="utf-8-sig")
        assert not {"firma", "firma_v2", "firma_v3"} & set(x.columns)
        x.to_csv(aout / f, index=False, encoding="utf-8-sig")
    log = (adir / "build_log_v3.txt").read_text(encoding="utf-8").splitlines()
    log = [ln for ln in log if not ln.strip().startswith("sample:")]      # the list of example person names
    txt = "\n".join(log) + "\n"
    for k in sorted(mapping, key=len, reverse=True):
        txt = txt.replace(k, mapping[k])
    (aout / "build_log_v3.txt").write_text(txt, encoding="utf-8")

    n_rows = int(out.name_pseudonymized.sum())
    print(f"distinct strings pseudonymized: {len(mapping):,} (flagged by heuristic: {len(s_flag):,}); "
          f"firma_v3 firms pseudonymized: {out.loc[out.name_pseudonymized, 'firma_v3'].nunique():,} of "
          f"{out.firma_v3.nunique():,}; contracts: {n_rows:,} of {len(out):,}; "
          f"in main sample: {int((out.name_pseudonymized & out.in_scope_main).sum()):,} of {int(out.in_scope_main.sum()):,}")


if __name__ == "__main__":
    main()
