#!/usr/bin/env python3
"""
Derive each planned note's term links from the source blocks it actually covers.

The digestion plan asks for a per-note table of relevant term notes. Written by
hand it is a guess; derived from the plan it is not, because the plan already
declares which source blocks each note carries and which terms will be captured.
A term is linked to a note when the term's surface forms appear in that note's
own source text -- so relevance is evidence from the corpus rather than a
recollection, which is exactly the distinction between a relevancy-ranked
mapping and a padded one.

    python3 scripts/build_term_links.py multihop_rag --plans experiments/plans/multihop_rag

Terms are ranked per note by occurrences in that note's blocks. `--floor` sets
the target link count; notes that cannot reach it are REPORTED rather than
padded, because a link to an unrelated term is not neutral: bfs and ppr traverse
every edge, so a false edge degrades the arm under test.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"


def compile_forms(forms: list[str]) -> re.Pattern:
    """One pattern per term, with the two properties a naive join gets wrong.

    WORD BOUNDARIES. Without them "bot" matches inside "both", "NFL" inside
    "influenza", and "trial" inside "clinical trial" -- so a canine-illness note
    acquires links to bot detection and criminal trials. Every such edge is
    fabricated, and bfs and ppr traverse every edge they are given.

    CASE. An acronym is case-SENSITIVE: "WHO" is an organisation, "who" is a
    pronoun. A lowercase phrase is not, because it may open a sentence.
    """
    parts = []
    for f in forms:
        esc = re.escape(f)
        # a form starting/ending with a word character needs a boundary there
        left = r"\b" if f[:1].isalnum() else ""
        right = r"\b" if f[-1:].isalnum() else ""
        if f.isupper() and len(f) <= 6 and f.isalpha():
            parts.append(f"(?-i:{left}{esc}{right})")   # acronym: exact case
        else:
            parts.append(f"{left}{esc}{right}")
    return re.compile("|".join(parts), re.I)


def blocks(slug: str, doc: str) -> list[str]:
    return [b.strip() for b in (CORPUS / slug / f"{doc}.txt").read_text().split("\n\n") if b.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--plans", required=True)
    ap.add_argument("--floor", type=int, default=8)
    ap.add_argument("--out")
    ap.add_argument("--verify", metavar="TERM_LINKS_JSON",
                    help="audit an existing mapping: every link must be backed by an "
                         "occurrence of the term in that note's own source blocks. Exits "
                         "non-zero on any unbacked link.")
    a = ap.parse_args()

    P = Path(a.plans)
    terms = json.loads((P / "terms.json").read_text())
    pats = {t: compile_forms(forms) for t, forms in terms.items()}

    cache: dict[str, list[str]] = {}
    mapping: dict[str, list] = {}
    term_use: dict[str, int] = defaultdict(int)

    def assignments():
        """Every planned note, from both plan shapes: the hand-built sub-plan
        assignment files and the agent-produced cluster plans."""
        for f in sorted(P.glob("*_assignments.json")):
            yield from json.loads(f.read_text()).items()
        for f in sorted((P / "clusters").glob("c*.json")) if (P / "clusters").is_dir() else []:
            for sub in json.loads(f.read_text())["subplans"]:
                for n in sub["notes"]:
                    yield n["note"], n["blocks"]

    for note, m in assignments():
        if True:
            text = []
            for d, ids in m.items():
                cache.setdefault(d, blocks(a.slug, d))
                text += [cache[d][i] for i in ids if i < len(cache[d])]
            body = "\n".join(text)
            hits = [(t, len(p.findall(body))) for t, p in pats.items()]
            hits = sorted([h for h in hits if h[1]], key=lambda x: -x[1])
            mapping[note] = hits
            for t, _ in hits:
                term_use[t] += 1

    if a.verify:
        # A link nothing in the source supports is a fabricated edge. It is not
        # inert: bfs and ppr traverse every edge given, so it moves probability
        # mass onto a note the evidence never connected, degrading the arm the
        # experiment exists to measure. Cheaper to block than to detect later in
        # a retrieval number that merely looks disappointing.
        claimed = json.loads(Path(a.verify).read_text())
        backed = {n: {t for t, _ in v} for n, v in mapping.items()}
        bad = []
        for note, ts in claimed.items():
            if note not in backed:
                bad.append((note, "<not in any assignment>"))
                continue
            bad += [(note, t) for t in ts if t not in backed[note]]
        total = sum(len(v) for v in claimed.values())
        print(f"links claimed   {total}")
        print(f"backed by source {total - len(bad)}")
        print(f"UNBACKED         {len(bad)}")
        for note, t in bad[:20]:
            print(f"  {note} -> {t}")
        if bad:
            print("\nA link the source does not support is a fabricated edge. Remove it, "
                  "or add the term's real surface form to terms.json if the match was "
                  "missed. Never keep it to reach a floor.")
            sys.exit(1)
        print("\nevery link is backed by an occurrence in that note's own source")
        return

    short = {n: len(v) for n, v in mapping.items() if len(v) < a.floor}
    print(f"notes            {len(mapping)}")
    print(f"terms            {len(terms)}")
    print(f"floor            {a.floor} term links per note")
    print(f"at or above      {len(mapping) - len(short)}")
    print(f"below the floor  {len(short)}")
    counts = sorted(len(v) for v in mapping.values())
    print(f"links per note   min {counts[0]}, median {counts[len(counts)//2]}, max {counts[-1]}")

    unused = [t for t in terms if not term_use[t]]
    if unused:
        print(f"\nterms no note references ({len(unused)}): {', '.join(sorted(unused))}")
        print("  Drop these or widen their surface forms -- a term note nothing links to "
              "is a graph island, which is the failure the term list exists to prevent.")
    if short:
        print(f"\nnotes below the floor, with their count:")
        for n, c in sorted(short.items(), key=lambda x: x[1])[:25]:
            print(f"  {c:>2}  {n}")
        print("  Do NOT pad these. Either the note is genuinely peripheral, or the term "
              "list is missing a concept the note depends on -- add the concept.")
    if a.out:
        Path(a.out).write_text(json.dumps(
            {n: [t for t, _ in v] for n, v in mapping.items()}, indent=1))
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
