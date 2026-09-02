#!/usr/bin/env python3
"""
Propose glossary term candidates from a corpus, by frequency and spread.

The per-note term-link table the digestion plan needs is only as good as the
term list behind it, and a list invented from memory will not match what the
corpus actually leans on. This mines candidates from the text: acronyms,
capitalised multi-word names, and quoted product or programme names.

    python3 scripts/mine_terms.py multihop_rag --docs vaults/.../SLICE.txt --top 60

Ranking is by DOCUMENT SPREAD first, then frequency. A term appearing in many
documents is what makes a term note worth writing: it becomes a hub that several
notes link to, and hubs are what the graph arms traverse. A term appearing forty
times in one article is that article's subject, not a shared concept.

Output is a candidate list for a human or agent to curate. It is deliberately
not authoritative: frequency finds what is mentioned, not what needs defining.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"

ACRONYM = re.compile(r"\b([A-Z]{2,6})\b")
PROPER = re.compile(r"\b([A-Z][a-z]+(?:\s+(?:of|for|and|the)\s+)?(?:\s+[A-Z][a-z]+){1,3})\b")
QUOTED = re.compile(r"[“\"]([A-Z][^”\"]{2,40})[”\"]")

# Words that start sentences or head sections; not concepts.
STOP = {"The", "This", "That", "These", "Those", "But", "And", "For", "With",
        "When", "What", "Where", "How", "Why", "It", "In", "On", "At", "As",
        "TechCrunch", "TC", "I", "We", "They", "He", "She", "A", "An", "So",
        "US", "U", "S", "EU", "AI", "CEO", "CTO", "VC", "VCs", "PR", "Q", "X"}


def mine(slug: str, docs: list[str], top: int) -> list[tuple]:
    spread: dict[str, set] = defaultdict(set)
    freq: dict[str, int] = defaultdict(int)
    for d in docs:
        text = (CORPUS / slug / f"{d}.txt").read_text(encoding="utf-8")
        found = set()
        for m in ACRONYM.findall(text):
            if m not in STOP and len(m) >= 2:
                found.add(m)
                freq[m] += 1
        for m in PROPER.findall(text) + QUOTED.findall(text):
            m = m.strip()
            if m.split()[0] in STOP or len(m) < 5:
                continue
            found.add(m)
            freq[m] += 1
        for f in found:
            spread[f].add(d)
    rows = [(t, len(spread[t]), freq[t], sorted(spread[t])) for t in spread]
    rows.sort(key=lambda r: (-r[1], -r[2]))
    return rows[:top]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--docs", required=True, help="file listing doc ids, one per line")
    ap.add_argument("--top", type=int, default=60)
    ap.add_argument("--min-spread", type=int, default=2)
    a = ap.parse_args()

    docs = Path(a.docs).read_text().split()
    rows = [r for r in mine(a.slug, docs, a.top * 3) if r[1] >= a.min_spread][: a.top]
    print(f"{'term':<38}{'docs':>5}{'freq':>6}  appears in")
    for t, s, f, ds in rows:
        print(f"{t:<38}{s:>5}{f:>6}  {', '.join(x.replace('doc_', '') for x in ds[:8])}")
    print(f"\n{len(rows)} candidates with spread >= {a.min_spread}. Curate before capturing: "
          f"frequency finds what is mentioned, not what needs defining.")


if __name__ == "__main__":
    main()
