#!/usr/bin/env python3
"""
Partition a corpus into planning clusters: the deterministic half of planning.

Which documents belong together is a structural question -- category, publisher,
time -- and answerable without reading anything. Doing it in a script keeps it
reproducible and keeps agents for the part that genuinely needs reading: which
blocks become which note, and what building block each carries.

    python3 scripts/partition_corpus.py multihop_rag --exclude <planned>.txt --target 20

Clusters group by category, then publisher, then month, so a cluster holds
documents that plausibly cross-reference each other. That matters beyond
tidiness: entity notes are shared WITHIN a cluster, so a cluster that mixes
unrelated beats produces no shared entities and loses the multi-document notes
multi-hop questions depend on.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--exclude", help="file of doc ids already planned")
    ap.add_argument("--target", type=int, default=20, help="documents per cluster")
    ap.add_argument("--out")
    a = ap.parse_args()

    idx = json.loads((CORPUS / a.slug / "index.json").read_text())
    raw = json.loads((ROOT / "data" / "raw" / a.slug / "corpus.json").read_text())
    cat = {f"doc_{i:04d}": d.get("category", "uncategorised") for i, d in enumerate(raw)}

    skip = set()
    if a.exclude and Path(a.exclude).exists():
        skip = set(Path(a.exclude).read_text().split())

    buckets: dict[tuple, list[str]] = defaultdict(list)
    for doc, meta in idx.items():
        if doc in skip:
            continue
        buckets[(cat[doc], meta["publisher"], (meta["date"] or "")[:7])].append(doc)

    # pack buckets into clusters, never splitting a bucket across two clusters
    # unless it alone exceeds the target
    clusters: list[dict] = []
    for (c, pub, month), docs in sorted(buckets.items(), key=lambda kv: (kv[0][0], -len(kv[1]))):
        docs.sort()
        while docs:
            chunk, docs = docs[: a.target], docs[a.target:]
            placed = False
            for cl in clusters:
                if cl["category"] == c and len(cl["docs"]) + len(chunk) <= a.target:
                    cl["docs"] += chunk
                    cl["publishers"].add(pub)
                    placed = True
                    break
            if not placed:
                clusters.append({"category": c, "publishers": {pub}, "docs": chunk})

    out = []
    for i, cl in enumerate(sorted(clusters, key=lambda c: (c["category"], c["docs"][0])), 1):
        w = sum(idx[d]["words"] for d in cl["docs"])
        out.append({"id": f"c{i:02d}", "category": cl["category"],
                    "publishers": sorted(cl["publishers"]), "docs": cl["docs"],
                    "words": w, "est_notes": round(len(cl["docs"]) * 5.28)})

    print(f"{'cluster':<9}{'cat':<14}{'docs':>5}{'words':>9}{'est notes':>10}  publishers")
    for c in out:
        print(f"{c['id']:<9}{c['category']:<14}{len(c['docs']):>5}{c['words']:>9,}"
              f"{c['est_notes']:>10}  {', '.join(c['publishers'][:3])}")
    print(f"\n{len(out)} clusters, {sum(len(c['docs']) for c in out)} documents, "
          f"{sum(c['words'] for c in out):,} words, ~{sum(c['est_notes'] for c in out):,} notes")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1))
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
