"""Approximate word count of the manuscript body (JIBE limit: 12,000 incl. references, tables, figures)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tex = (ROOT / "paper" / (sys.argv[1] if len(sys.argv) > 1 else "tendernet_jibe.tex")).read_text(encoding="utf-8")
tex = re.sub(r"(?<!\\)%.*", "", tex)
start, end = tex.index(r"\abstract{"), tex.index(r"\bibliography{")
body = tex[start:end]
text = re.sub(r"\\[a-zA-Z]+\*?", " ", body)
text = re.sub(r"[{}$\\&]", " ", text)
print("words (abstract to references, incl. tables/captions):", len(text.split()))
