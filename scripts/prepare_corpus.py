#!/usr/bin/env python3
"""
Turn a fetched benchmark corpus into the plain documents an ingesting agent reads.

This script reads the CORPUS half of a benchmark and nothing else. The questions
and their gold evidence live in a separate file that this script never opens,
which is what makes blind ingestion checkable rather than merely promised: an
agent given only data/corpus/<slug>/ cannot have seen a question, because the
questions were never written there.

    python3 scripts/prepare_corpus.py multihop_rag
    python3 scripts/prepare_corpus.py multihop_rag --stats

Output (all gitignored -- derived from data we do not redistribute):
    data/corpus/<slug>/doc_0000.txt ...   one document per file, body text only
    data/corpus/<slug>/index.json         doc_id -> title, publisher, date, words

The index carries the title because that is the join key the scorer uses to map
a retrieved note back to the gold evidence it was derived from.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "corpus"

# slug -> (corpus filename, field names)
CORPORA = {
    "multihop_rag": ("corpus.json", {"title": "title", "body": "body",
                                     "source": "source", "date": "published_at"}),
}


def prepare(slug: str) -> dict:
    fname, F = CORPORA[slug]
    src = RAW / slug / fname
    if not src.exists():
        print(f"missing {src} — run: python3 scripts/fetch_benchmarks.py {slug}")
        sys.exit(2)

    docs = json.loads(src.read_text(encoding="utf-8"))
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("doc_*.txt"):
        old.unlink()

    index = {}
    for i, d in enumerate(docs):
        doc_id = f"doc_{i:04d}"
        body = (d.get(F["body"]) or "").strip()
        title = (d.get(F["title"]) or "").strip()
        # The title is written into the file because it is part of the document
        # a reader sees; the id is not, so a note cannot cite an id it never read.
        (out / f"{doc_id}.txt").write_text(f"{title}\n\n{body}\n", encoding="utf-8")
        index[doc_id] = {
            "title": title,
            "publisher": d.get(F["source"]) or "",
            "date": d.get(F["date"]) or "",
            "words": len(body.split()),
        }
    (out / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", choices=sorted(CORPORA))
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    index = prepare(a.slug)
    out = OUT / a.slug
    print(f"corpus   {a.slug}")
    print(f"wrote    {len(index)} documents -> {out.relative_to(ROOT)}/")
    print(f"index    {(out / 'index.json').relative_to(ROOT)}")

    if a.stats:
        w = [v["words"] for v in index.values()]
        print(f"\nwords    total {sum(w):,}  mean {statistics.mean(w):.0f}  "
              f"median {statistics.median(w):.0f}  max {max(w):,}")
        pubs = Counter(v["publisher"] for v in index.values())
        print(f"publishers {len(pubs)}  top: "
              + ", ".join(f"{k} ({n})" for k, n in pubs.most_common(4)))
        # Budget pressure is the point of the experiment: report how many
        # documents exceed each context window, since a corpus that fits
        # entirely inside the smallest budget cannot separate the arms.
        print("\ndocuments exceeding a context budget (approx 1.3 tokens/word):")
        for budget in (512, 1024, 2048, 4096, 8192):
            over = sum(1 for x in w if x * 1.3 > budget)
            print(f"  {budget:>5} tokens: {over:>4}/{len(w)}  ({100*over/len(w):5.1f}%)")


if __name__ == "__main__":
    main()
