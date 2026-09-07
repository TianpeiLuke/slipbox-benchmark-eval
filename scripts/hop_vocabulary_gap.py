#!/usr/bin/env python3
"""Measure WHY a graph retriever wins on one multi-hop benchmark and loses on another.

Hypothesis: HippoRAG helps exactly when a required passage shares little
vocabulary with the question, because single-shot lexical/dense retrieval cannot
reach a passage it has no terms in common with, while a KG edge can. Where every
required passage already shares the question's vocabulary, the graph adds noise
instead of a bridge.

For each question this computes, per gold passage, the fraction of the question's
content words that appear in it, and reports the MINIMUM across gold passages --
the hardest hop, the one that decides All-Recall.
"""
import json, re, sqlite3, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
STOP = set("""a an the of in on at to for from by with and or but is are was were be been
who what when where why how did does do has have had this that these those than then it its
their there which while also more most other some such no not any all one two both each""".split())


def content(s: str) -> set:
    return {w for w in re.findall(r"[a-z][a-z0-9'-]{2,}", s.lower()) if w not in STOP}


def report(name: str, pairs: list[tuple[set, list[set]]]) -> None:
    mins, means = [], []
    for q, golds in pairs:
        if not q or not golds:
            continue
        cov = [len(q & g) / len(q) for g in golds]
        mins.append(min(cov)); means.append(float(np.mean(cov)))
    print(f"\n{name}   n={len(mins)} questions")
    print(f"  query-word coverage of the EASIEST gold passage : {np.mean([max(0,m) for m in means]):.3f}")
    print(f"  query-word coverage of the HARDEST gold passage : {np.mean(mins):.3f}")
    print(f"  questions with a gold passage under 20% coverage: "
          f"{np.mean([m < 0.20 for m in mins]):.1%}")
    print(f"  questions with a gold passage under 10% coverage: "
          f"{np.mean([m < 0.10 for m in mins]):.1%}")


# ---- 2WikiMultiHopQA -------------------------------------------------------
corpus = ROOT / "data/chunks/twowiki_200"
qs = json.loads((corpus / "questions.json").read_text())
con = sqlite3.connect(corpus / "notes.db")
body = {t: b for t, b in con.execute("SELECT source_doc, body FROM notes")}
con.close()
pairs = [(content(q["query"]),
          [content(body.get(t, "")) for t in q["gold_titles"] if t in body])
         for q in qs]
report("2WikiMultiHopQA  (entity bridge)", [(q, g) for q, g in pairs if g])

# ---- MultiHop-RAG ----------------------------------------------------------
idx = json.loads((ROOT / "data/corpus/multihop_rag/index.json").read_text())
by_title = {v["title"]: d for d, v in idx.items()}
raw = json.loads((ROOT / "data/raw/multihop_rag/MultiHopRAG.json").read_text())
pin = set(json.loads((ROOT / "experiments/runs9/fair_questions.json").read_text()))
con = sqlite3.connect(ROOT / "data/chunks/multihop_rag_slice/notes.db")
docbody: dict[str, list[str]] = {}
for sd, b in con.execute("SELECT source_doc, body FROM notes"):
    docbody.setdefault((sd or "").strip(), []).append(b)
con.close()
mh = []
for q in raw:
    if q["query"] not in pin or not q.get("evidence_list"):
        continue
    gold = {by_title.get(e.get("title", "")) for e in q["evidence_list"]}
    gs = [content(" ".join(docbody[g])) for g in gold if g in docbody]
    if gs:
        mh.append((content(q["query"]), gs))
report("MultiHop-RAG     (bibliographic bridge)", mh)
print()
