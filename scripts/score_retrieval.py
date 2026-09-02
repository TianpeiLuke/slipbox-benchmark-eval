#!/usr/bin/env python3
"""
Score a retrieval arm against benchmark gold evidence.

This script reads the QUESTIONS half of a benchmark. Nothing that ingests a
corpus may import or invoke it -- that separation is the blind-ingestion
guarantee, and it is the reason the corpus and the questions are prepared by
two different scripts that read two different files.

    python3 scripts/score_retrieval.py multihop_rag --arm notes  --vault vaults/multihop_rag
    python3 scripts/score_retrieval.py multihop_rag --arm chunks --chunk-db data/chunks/multihop_rag
    python3 scripts/score_retrieval.py multihop_rag --arm notes --vault vaults/multihop_rag \\
        --strategies bm25,hybrid,ppr --k 2,5,10 --budget 2048

Metrics
-------
Recall@k       fraction of a question's gold documents that appear in the top k
All-Recall@k   1 only if EVERY gold document appears in the top k, else 0

Both are reported because they answer different questions. A multi-hop question
is only answerable when all its evidence is present, so All-Recall is the metric
that tracks whether the retrieval could have supported an answer at all; Recall
shows partial progress and keeps a run interpretable when All-Recall is near
zero. Retrieval is scored at DOCUMENT level: a note is credited with the corpus
documents named in its own `source_docs` frontmatter, so a note that abstracts
several documents can satisfy several pieces of gold evidence at once -- which
is exactly the property under test and would be invisible to a chunk-level
metric.

null_query items carry no evidence and are excluded from recall; they are
counted separately, since scoring an unanswerable question by recall is
meaningless (nothing can be retrieved) and would silently inflate every arm.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

RAW = ROOT / "data" / "raw"
CORPUS = ROOT / "data" / "corpus"

QUESTIONS = {"multihop_rag": "MultiHopRAG.json"}


def load_gold(slug: str) -> tuple[list[dict], dict[str, str]]:
    """Questions with gold doc ids, plus the title -> doc_id map used to build them."""
    index = json.loads((CORPUS / slug / "index.json").read_text())
    by_title = {v["title"]: doc_id for doc_id, v in index.items()}

    raw = json.loads((RAW / slug / QUESTIONS[slug]).read_text())
    out, unmatched = [], 0
    for q in raw:
        gold, miss = set(), False
        for e in q.get("evidence_list", []):
            doc_id = by_title.get(e.get("title", ""))
            if doc_id is None:
                miss = True
            else:
                gold.add(doc_id)
        unmatched += miss
        out.append({"query": q["query"], "type": q.get("question_type", ""),
                    "gold": gold})
    if unmatched:
        print(f"WARNING: {unmatched} question(s) cite evidence with no matching "
              f"corpus document; their recall is unreachable by construction.")
    return out, by_title


def note_provenance(vault: Path) -> dict[str, set[str]]:
    """note_id -> the corpus documents it declares. This is what makes it scorable."""
    con = sqlite3.connect(vault / "notes.db")
    prov: dict[str, set[str]] = {}
    for nid, src in con.execute("SELECT note_id, source_doc FROM notes"):
        prov[nid] = {s.strip() for s in (src or "").split(",") if s.strip()}
    con.close()
    missing = [n for n, s in prov.items() if not s]
    if missing:
        print(f"WARNING: {len(missing)}/{len(prov)} notes declare no source_docs "
              f"and can never be credited. Run validate_notes.py --gate.")
    return prov


def score(questions: list[dict], resolve, ks: list[int], topk: int) -> dict:
    """resolve(query, k) -> ordered list of retrieval units mapped to doc-id sets."""
    stats = {k: {"recall": [], "all": []} for k in ks}
    by_type: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    answerable = 0

    for q in questions:
        if not q["gold"]:
            continue                      # null_query: nothing to retrieve
        answerable += 1
        ranked = resolve(q["query"], topk)
        for k in ks:
            seen: set[str] = set()
            for unit_docs in ranked[:k]:
                seen |= unit_docs
            hit = q["gold"] & seen
            r = len(hit) / len(q["gold"])
            stats[k]["recall"].append(r)
            stats[k]["all"].append(1.0 if hit == q["gold"] else 0.0)
            by_type[q["type"]][k].append(r)
    return {"stats": stats, "by_type": by_type, "answerable": answerable}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", choices=sorted(QUESTIONS))
    ap.add_argument("--arm", choices=["notes", "chunks"], required=True)
    ap.add_argument("--vault", help="notes arm: the corpus vault")
    ap.add_argument("--chunk-db", help="chunks arm: directory holding the chunk index")
    ap.add_argument("--strategies", default="bm25,hybrid,ppr")
    ap.add_argument("--k", default="2,5,10")
    ap.add_argument("--limit", type=int, default=0, help="score only the first N questions")
    ap.add_argument("--json", help="write results to this path")
    a = ap.parse_args()

    ks = sorted(int(x) for x in a.k.split(","))
    questions, _ = load_gold(a.slug)
    if a.limit:
        questions = questions[: a.limit]

    import retrieval as R

    if a.arm == "notes":
        vault = Path(a.vault or f"vaults/{a.slug}")
        if not (vault / "notes.db").exists():
            print(f"no database at {vault}/notes.db — run build_local_db.py first")
            sys.exit(2)
        prov = note_provenance(vault)
        unit_docs = lambda nid: prov.get(nid, set())          # noqa: E731
    else:
        cdir = Path(a.chunk_db or f"data/chunks/{a.slug}")
        if not (cdir / "notes.db").exists():
            print(f"no chunk index at {cdir}/notes.db — run build_chunk_baseline.py first")
            sys.exit(2)
        vault = cdir
        con = sqlite3.connect(cdir / "notes.db")
        cmap = {nid: {src} for nid, src in
                con.execute("SELECT note_id, source_doc FROM notes")}
        con.close()
        unit_docs = lambda nid: cmap.get(nid, set())          # noqa: E731

    results = {}
    for strat in a.strategies.split(","):
        strat = strat.strip()
        if strat not in R.STRATEGIES:
            print(f"unknown strategy {strat!r}; have {', '.join(R.STRATEGIES)}")
            sys.exit(2)

        def resolve(query: str, k: int, _s=strat):
            hits = R.STRATEGIES[_s](vault, query, k)
            return [unit_docs(nid) for nid, _ in hits]

        out = score(questions, resolve, ks, max(ks))
        results[strat] = out
        print(f"\n=== {a.arm} / {strat} — {out['answerable']} answerable questions ===")
        print(f"{'k':>4}  {'Recall@k':>9}  {'All-Recall@k':>13}")
        for k in ks:
            r = out["stats"][k]["recall"]
            al = out["stats"][k]["all"]
            print(f"{k:>4}  {sum(r)/len(r):>9.3f}  {sum(al)/len(al):>13.3f}")
        print("  by question type (Recall@%d):" % ks[-1])
        for t, d in sorted(out["by_type"].items()):
            v = d[ks[-1]]
            print(f"    {t:<20} {sum(v)/len(v):.3f}  (n={len(v)})")

    if a.json:
        Path(a.json).write_text(json.dumps(
            {s: {"stats": {k: {m: sum(v)/len(v) for m, v in d.items()}
                           for k, d in o["stats"].items()},
                 "answerable": o["answerable"]}
             for s, o in results.items()}, indent=2))
        print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
