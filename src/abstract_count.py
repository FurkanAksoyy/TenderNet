"""Count words in the manuscript abstract (JIBE: 150-250 words)."""
import re
from pathlib import Path

tex = (Path(__file__).resolve().parents[1] / "paper" / "tendernet_jibe.tex").read_text(encoding="utf-8")
start = tex.index(r"\abstract{") + len(r"\abstract{")
end = tex.index(r"\keywords")
text = re.sub(r"\\[a-zA-Z]+|[{}$~]", " ", tex[start:end])
print("abstract words:", len(text.split()))
