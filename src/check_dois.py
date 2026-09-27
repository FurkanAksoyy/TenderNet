"""List references cited in the manuscript that have no DOI in refs.bib."""
import re
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "paper"
bib = (P / "refs.bib").read_text(encoding="utf-8")
aux = (P / "tendernet_jibe.aux").read_text(encoding="utf-8")
cited = set()
for m in re.finditer(r"\\citation\{([^}]*)\}", aux):
    cited |= {k.strip() for k in m.group(1).split(",")}
ents = {}
for e in re.split(r"(?=^@)", bib, flags=re.M):
    m = re.match(r"@(\w+)\{([^,]+),", e.strip())
    if m:
        ents[m.group(2).strip()] = (m.group(1).lower(), bool(re.search(r"\bdoi\s*=", e, re.I)), e.strip()[:160].replace("\n", " "))
nodoi = sorted(k for k in cited if k in ents and not ents[k][1])
print(len(cited), "cited;", len(nodoi), "without DOI:")
for k in nodoi:
    print(" ", k, "|", ents[k][2])
