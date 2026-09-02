#!/usr/bin/env python3
"""
Choose a pilot slice of documents, using corpus structure only.

A pilot exists to validate the ingestion method before paying to fan it out, so
it must be small AND scorable. The tension is that "scorable" tempts you to pick
documents by looking at which questions they answer -- which is teaching to the
test, and would make the pilot's numbers meaningless.

So the slice is chosen from the CORPUS alone: the densest publisher-and-month
cluster, which is where multi-hop evidence naturally concentrates because
outlets covering one running story cross-reference the same events. Only after
the slice is fixed does --coverage report how many questions happen to be fully
covered by it. That number is an outcome of the choice, never an input to it.

    python3 scripts/select_slice.py multihop_rag --docs 25
    python3 scripts/select_slice.py multihop_rag --docs 25 --coverage
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"


def select(slug: str, n: int) -> list[str]:
    index = json.loads((CORPUS / slug / "index.json").read_text())
    buckets: dict[tuple[str, str], list[str]] = defaultdict(list)
    for doc_id, m in index.items():
        buckets[(m["publisher"], (m["date"] or "")[:7])].append(doc_id)
    # densest cluster first; extend with the next densest until we have n docs
    order = sorted(buckets.items(), key=lambda kv: -len(kv[1]))
    picked: list[str] = []
    for _, ids in order:
        picked.extend(sorted(ids))
        if len(picked) >= n:
            break
    return picked[:n]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--docs", type=int, default=25)
    ap.add_argument("--coverage", action="store_true",
                    help="report question coverage AFTER the slice is fixed")
    ap.add_argument("--out", help="write the slice manifest here")
    a = ap.parse_args()

    index = json.loads((CORPUS / a.slug / "index.json").read_text())
    picked = select(a.slug, a.docs)
    words = sum(index[d]["words"] for d in picked)
    pubs = Counter(index[d]["publisher"] for d in picked)

    print(f"slice    {len(picked)} documents, {words:,} words")
    print(f"publishers " + ", ".join(f"{k} ({v})" for k, v in pubs.most_common()))
    print(f"median words {sorted(index[d]['words'] for d in picked)[len(picked)//2]:,}")

    if a.coverage:
        # Reads the questions half ON PURPOSE -- this is the experimenter
        # measuring the slice, not an agent preparing to ingest it.
        raw = json.loads((ROOT / "data" / "raw" / a.slug / "MultiHopRAG.json").read_text())
        by_title = {v["title"]: d for d, v in index.items()}
        sel = set(picked)
        full = partial = 0
        types: Counter = Counter()
        for q in raw:
            gold = {by_title.get(e.get("title", "")) for e in q.get("evidence_list", [])}
            gold.discard(None)
            if not gold:
                continue
            if gold <= sel:
                full += 1
                types[q.get("question_type", "")] += 1
            elif gold & sel:
                partial += 1
        print(f"\nquestions fully covered by this slice: {full}")
        print(f"  by type: " + ", ".join(f"{k} {v}" for k, v in types.most_common()))
        print(f"questions partially covered (not scorable here): {partial}")
        if full < 20:
            print("\nFewer than 20 scorable questions: a pilot this small will not "
                  "separate the arms. Raise --docs.")

    if a.out:
        Path(a.out).write_text("\n".join(picked) + "\n")
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
