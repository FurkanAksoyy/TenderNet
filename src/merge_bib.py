"""Merge the v2 bibliography with the verified new references into paper/refs.bib.

Old entries that duplicate a verified new entry (BibTeX keys are case-insensitive)
are dropped in favour of the new one.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "paper" / "bib_src" / "tendernet-refs.bib"   # bibliography of the earlier (v2) manuscript
NEW = ROOT / "paper" / "bib_src" / "refs_new.bib"          # verified new references
DROP_OLD = {"saracco2017", "domagalski2021", "morselli2013", "farrell2007"}


def entries(text):
    parts = re.split(r"(?=^@)", text, flags=re.M)
    return [p for p in parts if p.strip().startswith("@")]


def key(entry):
    return re.match(r"@\w+\{([^,]+),", entry).group(1).strip()


old = [e for e in entries(OLD.read_text(encoding="utf-8")) if key(e).lower() not in DROP_OLD]
new = entries(NEW.read_text(encoding="utf-8"))
seen = {key(e).lower() for e in new}
old = [e for e in old if key(e).lower() not in seen]
out = ROOT / "paper" / "refs.bib"
out.write_text("".join(new) + "\n" + "".join(old), encoding="utf-8")
print(len(new), "new +", len(old), "old ->", out)
