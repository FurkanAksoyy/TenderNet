# -*- coding: utf-8 -*-
"""
build_master_v3.py -- builds the internal cleaned contract table (TenderNet v3).

NOT RUNNABLE FROM THE PUBLIC REPOSITORY. It needs the raw EKAP scrape, which is not
redistributed because the raw records contain the names of natural persons (sole
proprietors and individuals who won contracts). The records are public on EKAP
(https://ekapv2.kik.gov.tr) but we do not re-publish personal names (KVKK, Law 6698).
The script is included so that every cleaning rule is inspectable.

Inputs (place them under <repo>/raw/, which is git-ignored):
  raw/master_sozlesmeler_temiz.csv        13,024 contracts (v1 keyword-cleaned scrape)
  raw/clean_v2/firm_name_map.csv          v2 firm canonicalisation (4,788 names)
  raw/ekap_v3_cp1.json                    EKAP tender list (IKN -> date, type, procedure, keyword)
  src/build/manual_scope_overrides.csv    manual IT-scope decisions (top-150-by-value review)
  src/build/firm_merge_groups_v3.csv      manual firm merges on top of v2
Outputs (raw/internal/, contain names -- never commit):
  master_v3.csv, firm_name_map_v3.csv, corrected_top150_value_screen.csv, scope_rule_samples.csv,
  product_market_confusion_sample.csv, build_log_v3.txt
The public data/contracts_v3.csv is then made by src/build/make_release_data.py.
Run:  python src/build/build_master_v3.py
"""
import sys, io, json, re, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]           # repository root
# ------------------------------------------------------------------ EXTERNAL INPUT PATH (only constant to edit)
RAW = ROOT / "raw"                                   # non-public raw scrape (git-ignored)
# -------------------------------------------------------------------------------------------------------------
SRC, OUT = ROOT / "src" / "build", ROOT / "raw" / "internal"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT / "src"))
from currency_values import normalize_frame
from normalize_currency import verify_rates
import rules_v3 as R  # noqa: E402

LOG = open(OUT / "build_log_v3.txt", "w", encoding="utf-8")
def log(x=""):
    print(x); LOG.write(str(x) + "\n")
def hdr(x):
    log("\n" + "=" * 90); log(x); log("=" * 90)

df = pd.read_csv(RAW / "master_sozlesmeler_temiz.csv", encoding="utf-8-sig")
N0 = len(df)
orig_cols = list(df.columns)
cp1 = pd.DataFrame(json.load(open(RAW / "ekap_v3_cp1.json", encoding="utf-8"))["satirlar"])
assert cp1["IKN"].is_unique and df["IKN"].is_unique
cp1 = cp1.set_index("IKN")
df["ihale_turu"] = df["IKN"].map(cp1["ihale_turu"])
df["kaynak_keyword"] = df["IKN"].map(cp1["kaynak_keyword"])
hdr(f"INPUT: {N0:,} contracts, {df['firma'].nunique():,} firm names, {df['kurum'].nunique():,} buyer labels")

# ================================================================== 4. DATES
df["tarih_v3"] = pd.to_datetime(df["IKN"].map(cp1["ihale_tarihi"]), format="%Y-%m-%d", errors="coerce")
df["yil_v3"] = df["tarih_v3"].dt.year.astype("Int64")
bad_dt = pd.to_datetime(df["tarih_dt"], errors="coerce")
hdr("DATES")
log(f"tarih_v3 coverage: {df['tarih_v3'].notna().mean():.4%} | range {df['tarih_v3'].min().date()} -> {df['tarih_v3'].max().date()}")
log(f"tarih_v3 == original 'tarih' string: {(df['tarih_v3'].dt.strftime('%Y-%m-%d') == df['tarih']).mean():.4%}")
log(f"yil_v3 == original 'yil': {(df['yil_v3'] == df['yil']).mean():.4%}")
log(f"old tarih_dt: missing {bad_dt.isna().sum():,} ({bad_dt.isna().mean():.1%}); "
    f"wrong where present {(bad_dt.notna() & (bad_dt != df['tarih_v3'])).sum():,} "
    f"(dayfirst parsing swapped month/day on ISO strings)")
log("NOTE: ihale_tarihi = tender (auction) date from EKAP, not contract-signature date.")
df["tarih_v3"] = df["tarih_v3"].dt.strftime("%Y-%m-%d")

# Use the same cached, verified nominal TRY valuation as the public analysis.
fx_rates = pd.read_csv(ROOT / "data" / "fx_rates_tcmb.csv")
verify_rates(fx_rates)
df = normalize_frame(df, fx_rates)
log("Currency: nominal TRY proxy; unlabelled amounts assumed TRY. Raw bedel/bedel_num preserved.")

# ================================================================== 6. PROCEDURE
pr = df["ihale_usulu"].map(R.procedure_v3)
df["usul_v3"] = [a for a, b in pr]; df["usul_v3_group"] = [b for a, b in pr]
hdr("PROCEDURE (usul_v3)")
log(pd.crosstab(df["ihale_usulu"], df["usul_v3"]).to_string())
log("NOTE: no untyped 'Pazarlık' and no direct procurement (Md.22) exist in this EKAP tender-search extract "
    "(cp1 contains only Açık / Belli İstekliler / Pazarlık 21a-f); categories kept for schema stability.")

# ================================================================== 5. BUYERS: pooled labels
nil = df.groupby("kurum")["il"].nunique()
POOLED_PATTERNS = re.compile(r"^İl Sağlık Müdürlüğü SAĞLIK BAKANLIĞI|^Kamu Hastane Birliği SAĞLIK BAKANLIĞI|"
                             r"^Halk Sağlığı Müdürlüğü SAĞLIK BAKANLIĞI|^Aile ve Sosyal Hizmetler İl Müdürlüğü")
# single national entities whose offices happen to sit in 2 provinces are NOT pooled (checked by hand)
NOT_POOLED = re.compile(r"TEDAŞ GENEL|İHRACAT KREDİ|TOPLU KONUT İDARESİ|TED\.BLG|SAĞLIK ENSTİTÜLERİ BAŞKANLIĞI|"
                        r"BANKACILIK DÜZENLEME")
pooled_set = ({k for k in nil[nil >= 2].index if not NOT_POOLED.search(R.tr_upper(k))}
              | {k for k in nil.index if POOLED_PATTERNS.search(k)})
df["pooled_label"] = df["kurum"].isin(pooled_set)
df["kurum_il_split"] = np.where(df["pooled_label"], df["kurum"] + " | " + df["il"].astype(str), df["kurum"])
hdr("BUYERS (pooled labels = generic label spanning >=2 provinces, or known MoH/ASHB generic labels)")
log(f"pooled labels: {len(pooled_set)} | contracts under pooled labels: {df['pooled_label'].sum():,} "
    f"| buyer nodes: kurum {df['kurum'].nunique():,} -> kurum_il_split {df['kurum_il_split'].nunique():,}")
for k in sorted(pooled_set, key=lambda k: -int((df["kurum"] == k).sum()))[:12]:
    log(f"  {int((df['kurum'] == k).sum()):4d} contracts, {nil[k]:2d} provinces | {k}")

# ================================================================== 2a. SECTOR v3 (buyer type)
df["sektor_v3"] = df["kurum"].map(R.sector_v3)
df["sektor_v3_en"] = df["sektor_v3"].map(R.SECTOR_EN)
df["sector_changed"] = df["sektor"] != df["sektor_v3"]
hdr("BUYER SECTOR v3 -- fixes")
for f in R.FIXES_V3: log("  " + f)
log(f"\ncontracts whose sector changed: {df['sector_changed'].sum():,} ({df['sector_changed'].mean():.1%}); "
    f"buyer labels changed: {df.loc[df['sector_changed'], 'kurum'].nunique():,}")
log(pd.crosstab(df["sektor"], df["sektor_v3"], margins=True).to_string())
mv = (df[df["sector_changed"]].groupby(["sektor", "sektor_v3", "kurum"]).size().reset_index(name="n")
      .sort_values("n", ascending=False))
log("\nTop moved buyer labels:")
for _, r in mv.head(40).iterrows():
    log(f"  {r.n:4d}  {r.sektor:>17} -> {r.sektor_v3:<17} | {r.kurum[:95]}")

# ================================================================== 1. IT SCOPE
df["_T"] = df["ihale_adi"].map(R.tr_upper)
sc = [R.classify_scope(t, u) for t, u in zip(df["_T"], df["ihale_turu"])]
df["scope_v3"] = [a for a, b in sc]; df["scope_reason"] = [b for a, b in sc]
ov = pd.read_csv(SRC / "manual_scope_overrides.csv", encoding="utf-8")
ovm = dict(zip(ov["IKN"], ov["scope_v3"]))
df["scope_manual_override"] = df["IKN"].isin(ovm)
df.loc[df["scope_manual_override"], "scope_reason"] = "manual_override(was " + df["scope_v3"] + ")"
df.loc[df["scope_manual_override"], "scope_v3"] = df.loc[df["scope_manual_override"], "IKN"].map(ovm)
df["callcentre_flag"] = df["scope_v3"].eq("IT_service_callcentre")
df["it_staffing_flag"] = df["scope_reason"].eq("IT_user_staffing")
df["in_scope_core"] = df["scope_v3"].eq("IT")                                   # strict
df["in_scope_main"] = df["scope_v3"].isin(["IT", "IT_service_callcentre"])     # recommended default
df["in_scope_broad"] = df["scope_v3"].isin(["IT", "IT_service_callcentre", "gray"])

hdr("IT SCOPE v3 (scope_v3)")
tot_v = df["bedel_try"].sum()
g = df.groupby("scope_v3").agg(contracts=("IKN", "size"), value_TRY=("bedel_try", "sum"))
g["share_contracts"] = g["contracts"] / N0; g["share_value"] = g["value_TRY"] / tot_v
g["value_bnTRY"] = g["value_TRY"] / 1e9
log(g[["contracts", "share_contracts", "value_bnTRY", "share_value"]].to_string(float_format=lambda x: f"{x:,.3f}"))
log(f"TOTAL {N0:,} contracts, {tot_v/1e9:,.2f} bn TRY (nominal)")
log("\nBy rule reason:")
log(df.groupby(["scope_v3", "scope_reason"]).agg(n=("IKN", "size"), bnTRY=("bedel_try", lambda x: x.sum() / 1e9))
    .to_string(float_format=lambda x: f"{x:,.3f}"))
log("\nScope by original scraping keyword (shows EKAP substring noise: 'erp' hit YavERPaşa/sERPici, "
    "'teknik destek' hit facility staffing):")
log(pd.crosstab(df["kaynak_keyword"], df["scope_v3"], margins=True).to_string())
log(f"\nIhale türü 'Yapım' (works): {int((df['ihale_turu'] == 'Yapım').sum())} contracts -> "
    + str(df[df['ihale_turu'] == 'Yapım']['scope_v3'].value_counts().to_dict()))

top20 = df[df["scope_v3"] == "nonIT"].sort_values("bedel_try", ascending=False).head(20)
log("\nTOP-20 non-IT removals by value:")
for _, r in top20.iterrows():
    log(f"  {r.bedel_try/1e6:8.1f} mn | {r.firma[:34]:34} | {r.scope_reason[:28]:28} | {str(r.ihale_adi)[:95]}")

# Corrected top-150 screen: historical hand-review membership is provenance only.
# Newly entering records must not inherit an automatic hand-verification claim.
top150 = df.sort_values("bedel_try", ascending=False).head(150).copy()
top150["rank"] = range(1, 151)
top150["provisional_scope_label"] = top150["scope_v3"].map({"IT": "IT", "nonIT": "non-IT", "gray": "mixed",
                                                   "IT_service_callcentre": "IT-services (call centre)"})
legacy_review = pd.read_csv(ROOT / "data" / "audit" / "top150_value_review.csv")
top150["legacy_scope_review_recorded"] = top150.IKN.isin(legacy_review.IKN)
top150["new_scope_review_required"] = ~top150.legacy_scope_review_recorded
top150[["rank", "IKN", "bedel_num", "bedel_currency", "bedel_currency_status", "bedel_try", "firma", "kurum", "ihale_turu", "ihale_adi", "scope_v3", "scope_reason",
        "provisional_scope_label", "scope_manual_override", "legacy_scope_review_recorded", "new_scope_review_required"]].to_csv(
    OUT / "corrected_top150_value_screen.csv", index=False, encoding="utf-8-sig")
t150 = top150.groupby("provisional_scope_label").agg(n=("IKN", "size"), bn=("bedel_try", lambda x: x.sum() / 1e9))
log("\nTop-150 by corrected TRY proxy, provisional scope screen (see review flags):\n" + t150.to_string())

# random audit sample per rule reason (for manual spot checks)
samp = (df.groupby("scope_reason", group_keys=False)
        .apply(lambda x: x.sample(min(len(x), 5), random_state=42)))
samp[["scope_v3", "scope_reason", "IKN", "bedel_try", "ihale_turu", "kaynak_keyword", "ihale_adi"]].to_csv(
    OUT / "scope_rule_samples.csv", index=False, encoding="utf-8-sig")

# ================================================================== 2b. PRODUCT MARKET
df["urun_pazari"] = df["_T"].map(R.classify_product)
df.loc[df["scope_v3"] == "nonIT", "urun_pazari"] = "not_IT"
hdr("PRODUCT MARKET (urun_pazari; rule-based on ihale_adi; nonIT rows = 'not_IT')")
it = df[df["scope_v3"] != "nonIT"]
pm = it.groupby("urun_pazari").agg(contracts=("IKN", "size"), value_bn=("bedel_try", lambda x: x.sum() / 1e9))
pm["share_contracts"] = pm["contracts"] / len(it); pm["share_value"] = pm["value_bn"] * 1e9 / it["bedel_try"].sum()
log(pm.sort_values("contracts", ascending=False).to_string(float_format=lambda x: f"{x:,.3f}"))
cov = 1 - (it["urun_pazari"] == "other_IT").mean()
log(f"coverage (in-scope rows assigned to a specific market, not other_IT): {cov:.1%}")
log("\nProduct market x buyer sector (in-scope, contracts):")
log(pd.crosstab(it["urun_pazari"], it["sektor_v3"]).to_string())
conf = (it.groupby("urun_pazari", group_keys=False).apply(lambda x: x.sample(min(len(x), 6), random_state=7)))
conf[["urun_pazari", "sektor_v3", "IKN", "ihale_adi"]].to_csv(OUT / "product_market_confusion_sample.csv",
                                                              index=False, encoding="utf-8-sig")

# ================================================================== 3. FIRMS
v2 = pd.read_csv(RAW / "clean_v2" / "firm_name_map.csv", encoding="utf-8-sig")
v2map = dict(zip(v2["original"], v2["canonical"]))
missing = set(df["firma"]) - set(v2map)
assert not missing, f"{len(missing)} firm names missing from v2 map"
LEGAL_FORM = re.compile(r"ŞİRKETİ|ŞİRK\b|LTD|ŞTİ|A\.\s?Ş|\bAŞ\b|ANONİM|LİMİTED")
def is_jv(name):
    """v2 flagged every name containing a comma as a JV; v3 requires an explicit JV word or a comma-separated
    list with >= 2 legal-form tokens / person names (e.g. 'TEKOBEL TEKNOLOJİ HİZMETLERİ, İMALAT ...' is one firm)."""
    u = R.tr_upper(name)
    if re.search(r"ORTAKLI|ORTAK GİRİŞİM|KONSORS", u):
        return True
    parts = [p.strip() for p in re.split(r",|\+", u) if p.strip()]
    if len(parts) < 2:
        return False
    return sum(bool(LEGAL_FORM.search(p)) or R.is_natural_person(p) for p in parts) >= 2
v2["is_JV"] = v2["original"].map(is_jv)
canon_v2 = v2.groupby("canonical").agg(n=("n_contracts", "sum"), is_JV=("is_JV", "max")).reset_index()
yr = df.assign(c=df["firma"].map(v2map)).groupby("c")["yil_v3"].agg(["min", "max"])
canon_v2["y0"] = canon_v2["canonical"].map(yr["min"]); canon_v2["y1"] = canon_v2["canonical"].map(yr["max"])
canon_v2["U"] = canon_v2["canonical"].map(R.tr_upper)

groups = pd.read_csv(SRC / "firm_merge_groups_v3.csv", encoding="utf-8")
v3_of_v2, mtype_of_v2 = {}, {}
hdr("FIRM CANONICALISATION v3 (manual merges on top of v2)")
for _, gr in groups.iterrows():
    mem = canon_v2[(~canon_v2["is_JV"]) & canon_v2["U"].map(lambda u: bool(re.search(gr["prefix_regex"], u)))]
    assert len(mem) >= 2, f"group {gr.group_id} matched {len(mem)} names"
    mem = mem.sort_values(["n", "y1"], ascending=False)
    target = mem["canonical"].iloc[0]
    log(f"{gr.group_id} [{gr.merge_type}] -> {target[:70]}  (total {int(mem['n'].sum())})")
    for _, m in mem.iterrows():
        log(f"      {int(m.n):4d} {m.y0}-{m.y1} | {m.canonical[:95]}")
        assert m.canonical not in v3_of_v2, f"{m.canonical} in two groups"
        v3_of_v2[m.canonical] = target; mtype_of_v2[m.canonical] = gr["merge_type"]

df["firma_v2"] = df["firma"].map(v2map)
df["firma_v3"] = df["firma_v2"].map(lambda c: v3_of_v2.get(c, c))
df["firm_merge_v3"] = df["firma_v2"].map(lambda c: mtype_of_v2.get(c, "none"))

def fid(name):
    return "F" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]

def has_person(name):
    if R.is_natural_person(name):
        return True
    parts = re.split(r",|\s-\s|\+", re.sub(r"(?i)\s*(İş Ortaklığı|Ortak Girişimi|İŞ ORTAKLIĞI)\s*$", "", name))
    return len(parts) > 1 and any(R.is_natural_person(p.strip()) for p in parts)

firms = pd.DataFrame({"firma_v3": df["firma_v3"].unique()})
firms["is_natural_person"] = firms["firma_v3"].map(R.is_natural_person)
firms["contains_natural_person"] = firms["firma_v3"].map(has_person)
firms["firm_id"] = firms["firma_v3"].map(fid)
assert firms["firm_id"].is_unique, "firm_id hash collision"
firms["firma_release"] = np.where(firms["contains_natural_person"], firms["firm_id"], firms["firma_v3"])
df = df.merge(firms, on="firma_v3", how="left")

n_orig, n_v2, n_v3 = df["firma"].nunique(), df["firma_v2"].nunique(), df["firma_v3"].nunique()
log(f"\nfirm nodes: as recorded {n_orig:,} -> v2 {n_v2:,} -> v3 {n_v3:,} "
    f"(v3 merged {n_v2 - n_v3} further v2 firms in {len(groups)} groups; "
    f"{int(df['firm_merge_v3'].ne('none').sum()):,} contracts affected)")
log("merge types (contracts): " + str(df["firm_merge_v3"].value_counts().to_dict()))
top = df.groupby("firma_v3").size().sort_values(ascending=False)
log("\nTop-15 firms after v3 merge (contracts):")
for f, n in top.head(15).items():
    log(f"  {n:4d} | {f[:90]}")
np_f = firms[firms["is_natural_person"]]
log(f"\nNATURAL PERSONS (heuristic: 2-4 alphabetic tokens, no legal-form/business word): "
    f"{len(np_f):,} of {len(firms):,} firms ({len(np_f)/len(firms):.1%}); contracts {int(df['is_natural_person'].sum()):,} "
    f"({df['is_natural_person'].mean():.1%}); JVs/entities containing a person: "
    f"{int((firms['contains_natural_person'] & ~firms['is_natural_person']).sum())}")
log("  sample: " + "; ".join(np_f["firma_v3"].sample(min(15, len(np_f)), random_state=3)))

fm = (df.groupby(["firma", "firma_v2", "firma_v3", "firm_merge_v3", "firm_id", "is_natural_person",
                  "contains_natural_person", "firma_release"]).size().reset_index(name="n_contracts"))
fm["is_JV"] = fm["firma_v2"].map(dict(zip(canon_v2["canonical"], canon_v2["is_JV"])))
fm["merged_v2"] = fm["firma"] != fm["firma_v2"]
fm["merged_v3"] = fm["firma_v2"] != fm["firma_v3"]
fm.rename(columns={"firma": "original", "firma_v2": "canonical_v2"}).sort_values(
    ["firma_v3", "n_contracts"], ascending=[True, False]).to_csv(OUT / "firm_name_map_v3.csv", index=False,
                                                                 encoding="utf-8-sig")

# ================================================================== 7. WRITE
new_cols = ["ihale_turu", "kaynak_keyword", "tarih_v3", "yil_v3", "usul_v3", "usul_v3_group", "kurum_il_split",
            "pooled_label", "sektor_v3", "sektor_v3_en", "sector_changed", "scope_v3", "scope_reason",
            "scope_manual_override", "callcentre_flag", "it_staffing_flag", "in_scope_core", "in_scope_main",
            "in_scope_broad", "urun_pazari", "firma_v2", "firma_v3", "firm_merge_v3", "is_natural_person",
            "contains_natural_person", "firm_id", "firma_release"]
currency_cols = ["bedel_amount_original", "bedel_currency", "bedel_currency_status", "bedel_fx_try_per_unit",
                 "bedel_fx_date", "bedel_valuation_method", "bedel_try"]
out = df[orig_cols + new_cols + currency_cols]
assert len(out) == N0 and out["IKN"].is_unique
out.to_csv(OUT / "master_v3.csv", index=False, encoding="utf-8-sig")
hdr(f"WROTE master_v3.csv: {len(out):,} rows x {out.shape[1]} cols")

# headline network sizes under each scope
for lab, m in [("core IT", df["in_scope_core"]), ("main (IT+callcentre)", df["in_scope_main"]),
               ("broad (+gray)", df["in_scope_broad"])]:
    s = df[m]
    log(f"  {lab:22} contracts {len(s):6,} | value {s['bedel_try'].sum()/1e9:6.2f} bn | firms_v3 "
        f"{s['firma_v3'].nunique():5,} | buyers {s['kurum'].nunique():5,} (split {s['kurum_il_split'].nunique():5,})")
LOG.close()
