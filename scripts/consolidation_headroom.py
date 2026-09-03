"""Is there headroom for a note that integrates ACROSS documents?

If a multi-hop question's gold documents are about the same event, one
cross-document note could answer it in a single unit -- collapsing multi-hop
retrieval to single-hop. If they are unrelated, no note boundary could have
helped and the null is about the task, not the pipeline.
"""
import json, random, sys
import numpy as np
from pathlib import Path
sys.path.insert(0, "scripts")

random.seed(5)
idx = json.loads(Path("data/corpus/multihop_rag/index.json").read_text())
by_title = {v["title"]: d for d, v in idx.items()}
raw = json.loads(Path("data/raw/multihop_rag/MultiHopRAG.json").read_text())
CORP = Path("data/corpus/multihop_rag")

from sentence_transformers import SentenceTransformer
m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

docs = sorted({d for q in raw for e in q.get("evidence_list", [])
               if (d := by_title.get(e.get("title", "")))})
texts = [(CORP / f"{d}.txt").read_text()[:3000] for d in docs]
E = m.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
pos = {d: i for i, d in enumerate(docs)}

within, across = [], []
for q in raw:
    g = sorted({d for e in q.get("evidence_list", []) if (d := by_title.get(e.get("title", "")))})
    if len(g) < 2:
        continue
    ix = [pos[d] for d in g if d in pos]
    for a in range(len(ix)):
        for b in range(a + 1, len(ix)):
            within.append(float(E[ix[a]] @ E[ix[b]]))
for _ in range(4000):
    a, b = random.randrange(len(docs)), random.randrange(len(docs))
    if a != b:
        across.append(float(E[a] @ E[b]))

import statistics as st
p = lambda v, q: sorted(v)[int(q * (len(v) - 1))]
print(f"gold-document pairs from the same question: {len(within):,}")
print(f"  similarity  median {st.median(within):.3f}   p25 {p(within,.25):.3f}   p75 {p(within,.75):.3f}")
print(f"random document pairs: {len(across):,}")
print(f"  similarity  median {st.median(across):.3f}   p75 {p(across,.75):.3f}   p95 {p(across,.95):.3f}")
for t in (0.5, 0.6, 0.7):
    w = sum(1 for x in within if x >= t) / len(within)
    a = sum(1 for x in across if x >= t) / len(across)
    print(f"  >= {t}: {w:6.1%} of same-question pairs vs {a:5.1%} of random pairs")
