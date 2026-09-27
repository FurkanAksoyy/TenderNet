"""Merge the v2 bibliography with the verified new references into paper/refs.bib.

Old entries that duplicate a verified new entry (BibTeX keys are case-insensitive)
are dropped in favour of the new one.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "paper" / "bib_src" / "tendernet-refs.bib"   # bibliography of the earlier (v2) manuscript
NEW = ROOT / "paper" / "bib_src" / "refs_new.bib"
DROP_OLD = {"saracco2017", "domagalski2021", "morselli2013", "farrell2007"}


def entries(text):
    parts = re.split(r"(?=^@)", text, flags=re.M)
    return [p for p in parts if p.strip().startswith("@")]


def key(entry):
    return re.match(r"@\w+\{([^,]+),", entry).group(1).strip()


old = [e for e in entries(OLD.read_text(encoding="utf-8")) if key(e).lower() not in DROP_OLD]
new = entries(NEW.read_text(encoding="utf-8"))
for extra in ["refs_revision.bib", "refs_revision2.bib", "refs_revision3.bib"]:
    path = ROOT / "paper" / "bib_src" / extra
    if path.exists():
        known = {key(e).lower() for e in new}
        new += [e for e in entries(path.read_text(encoding="utf-8")) if key(e).lower() not in known]
seen = {key(e).lower() for e in new}
old = [e for e in old if key(e).lower() not in seen]
text = "".join(new) + "\n" + "".join(old)
# Corrections to entries inherited from the v2 bibliography (verified against publisher pages).
PATCHES = [
    (r"author={Als\c{a}\c{c}, \"Umit}", r"author={Alsa\c{c}, \"Umit}"),
    (r"editor={Shakya, Rajesh Kumar}, pages={126--150}, year={2017}, publisher={IGI Global}}",
     r"editor={Shakya, Rajesh Kumar}, pages={126--150}, year={2017}, publisher={IGI Global}," "\n"
     r"  doi={10.4018/978-1-5225-2203-4.ch006}}"),
    (r"journal={European Journal on Criminal Policy and Research}, volume={22}, pages={369--397}, year={2016}}",
     r"journal={European Journal on Criminal Policy and Research}, volume={22}, number={3}, pages={369--397}, year={2016}," "\n"
     r"  doi={10.1007/s10610-016-9308-z}}"),
]
for a, b in PATCHES:
    assert a in text, a
    text = text.replace(a, b)
out = ROOT / "paper" / "refs.bib"
out.write_text(text, encoding="utf-8")
print(len(new), "new +", len(old), "old ->", out)
