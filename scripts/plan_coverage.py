#!/usr/bin/env python3
"""
Account for a digestion plan's source coverage, per note and per document.

Two questions a plan has to answer with numbers rather than assertion: does any
single note draw on more source than the density rule allows, and how much of
the corpus does the plan actually carry into notes?

    python3 scripts/plan_coverage.py multihop_rag --segment doc_0009
    python3 scripts/plan_coverage.py multihop_rag --check assignments.json

--segment prints a document's paragraph blocks with word counts, which is the
input a planner needs to assign blocks to notes. --check takes the assignment
back as {note: {doc: [block indices]}} and reports per-note source words against
the 1800-word ceiling, plus per-document coverage and what was left unassigned.

Unassigned text is not automatically a defect: publisher chrome (newsletter
plugs, "read more" links, podcast promos) carries no claim and should be
dropped. But it has to be VISIBLE, because the same number hides genuine
omission, and a plan that cannot say what it dropped cannot be reviewed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
CEILING = 1800


def blocks(slug: str, doc: str) -> list[str]:
    text = (CORPUS / slug / f"{doc}.txt").read_text(encoding="utf-8")
    return [b.strip() for b in text.split("\n\n") if b.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--segment")
    ap.add_argument("--check")
    a = ap.parse_args()

    if a.segment:
        bs = blocks(a.slug, a.segment)
        total = sum(len(b.split()) for b in bs)
        print(f"{a.segment}: {len(bs)} blocks, {total:,} words\n")
        for i, b in enumerate(bs):
            print(f"[{i:>2}] {len(b.split()):>4}w  {b[:96]}")
        return

    if not a.check:
        ap.error("pass --segment or --check")

    asg = json.loads(Path(a.check).read_text())
    docs = sorted({d for m in asg.values() for d in m})
    cache = {d: blocks(a.slug, d) for d in docs}

    print(f"{'note':<44}{'src words':>10}  {'ceiling':>8}")
    over = 0
    for note, m in asg.items():
        w = sum(len(cache[d][i].split()) for d, ids in m.items() for i in ids)
        flag = "OVER" if w > CEILING else "ok"
        if w > CEILING:
            over += 1
        print(f"{note:<44}{w:>10}  {flag:>8}")

    print(f"\n{'doc':<10}{'words':>7}{'covered':>9}{'pct':>7}  unassigned blocks")
    tot = cov = 0
    for d in docs:
        used = {i for m in asg.values() for i in m.get(d, [])}
        dw = sum(len(b.split()) for b in cache[d])
        cw = sum(len(cache[d][i].split()) for i in used)
        tot += dw
        cov += cw
        missing = [i for i in range(len(cache[d])) if i not in used]
        print(f"{d:<10}{dw:>7}{cw:>9}{100*cw/dw:>6.1f}%  {missing}")
    print(f"\ntotal {tot:,} words, {cov:,} covered ({100*cov/tot:.1f}%)")
    print(f"notes over the {CEILING}-word source ceiling: {over}")
    if over:
        sys.exit(1)


if __name__ == "__main__":
    main()
