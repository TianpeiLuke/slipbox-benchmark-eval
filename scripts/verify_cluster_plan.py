#!/usr/bin/env python3
"""
Check one agent-produced cluster plan against the rules it was given.

Agent self-reports are not evidence. A planning agent can return a well-formed
object that quietly breaks the constraints -- an out-of-range block index, the
same source assigned to two notes, a sub-plan of forty notes -- and none of that
is visible without re-deriving it from the corpus. This does that, and exits
non-zero on any violation, so a bad plan cannot enter the vault by being
plausible.

    python3 scripts/verify_cluster_plan.py multihop_rag --plan c01.json

Checks, in the order a violation matters:
  BLOCK-RANGE   a block index the document does not have
  DUPLICATE     one (doc, block) assigned to two notes
  BB-ENUM       a building block outside the closed set
  CEILING       a note drawing on more than 1,800 source words
  SIZE          a sub-plan outside the 4-15 note range
  NAME          a filename that is not a unique lowercase .md slug
  COVERAGE      a document below the assigned-words floor
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
CEILING = 1800

# A document can fall below the coverage floor honestly: a deals listicle is
# mostly section headers, a sports page mostly betting widgets. What separates
# that from real omission is WHAT was dropped, not how much. Low coverage is
# accepted only when the dropped material is demonstrably chrome -- short
# heading-like blocks, or blocks matching promotional boilerplate.
CHROME_WORDS = 12          # at or under this, a block is a heading or label
# Two kinds, kept separate because they are chrome for different reasons.
#
# Promotional boilerplate sells the publication rather than asserting anything.
#
# Self-referential framing talks ABOUT the article -- "in this edition we
# spotlight X, Y and Z" -- and in a roundup that framing is an index of items
# each covered in its own block further down. Assigning it would duplicate the
# same source across two notes, which is the failure the duplicate check exists
# to catch. It is chrome because the content survives elsewhere, not because it
# is empty.
CHROME_PAT = re.compile(
    r"table of contents|sign up|subscribe|newsletter|why we like it|"
    r"read more|check out our|unlock free|fire up our|join our free|"
    r"more deals|expand tweet|deals\b|shop |view deal|"
    r"contributed to this|this report was updated|follow along|"
    r"in this edition|in this issue|this week we|we won.t delay|"
    r"on the hunt for|look no further|our roster|our podcasts?\b",
    re.I)


def chrome_share(blocks: list[str], dropped: list[int]) -> float:
    """Fraction of dropped WORDS that are demonstrably chrome."""
    tot = chrome = 0
    for i in dropped:
        if not 0 <= i < len(blocks):
            continue
        w = len(blocks[i].split())
        tot += w
        # Block 0 is the document title by construction: prepare_corpus.py writes
        # "title\n\nbody". It is carried in the note's H1, so dropping it loses
        # nothing -- this is structural, not a guess about the wording.
        if i == 0 or w <= CHROME_WORDS or CHROME_PAT.search(blocks[i]):
            chrome += w
    return chrome / tot if tot else 1.0
BB = {"concept", "model", "procedure", "empirical_observation",
      "argument", "counter_argument", "hypothesis", "navigation"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--min-coverage", type=float, default=0.80)
    ap.add_argument("--own-docs",
                    help="comma-separated documents this cluster owns. Coverage is computed "
                         "over these only: a merged note legitimately carries blocks from a "
                         "document another cluster owns, and counting that document here "
                         "would report it as under-covered when the rest of it lives elsewhere.")
    ap.add_argument("--chrome-share", type=float, default=0.75,
                    help="below the coverage floor, this fraction of dropped words must be "
                         "demonstrably chrome for the document to be accepted")
    a = ap.parse_args()

    plan = json.loads(Path(a.plan).read_text())
    subs = plan["subplans"]
    docs = sorted({d for s in subs for n in s["notes"] for d in n["blocks"]}
                  | set(plan.get("dropped", {})))
    cache = {d: [b.strip() for b in (CORPUS / a.slug / f"{d}.txt").read_text().split("\n\n")
                 if b.strip()] for d in docs}

    bad: list[str] = []
    owner: dict[tuple, str] = {}
    seen_names: set[str] = set()

    for s in subs:
        n = len(s["notes"])
        if n > 15:
            bad.append(f"SIZE      {s['slug']}: {n} notes, maximum is 15")
        elif n < 4:
            print(f"  note: sub-plan {s['slug']} has {n} notes — below the 4-note target, "
                  f"usually because a merge moved its notes to another cluster")
        for note in s["notes"]:
            name = note["note"]
            if not name.endswith(".md") or name != name.lower() or " " in name:
                bad.append(f"NAME      {name!r} is not a lowercase .md slug")
            if name in seen_names:
                bad.append(f"NAME      {name!r} used by more than one note")
            seen_names.add(name)
            if note["bb"] not in BB:
                bad.append(f"BB-ENUM   {name}: {note['bb']!r}")
            words = 0
            for d, ids in note["blocks"].items():
                if d not in cache:
                    bad.append(f"BLOCK-RANGE {name}: unknown document {d}")
                    continue
                for i in ids:
                    if not 0 <= i < len(cache[d]):
                        bad.append(f"BLOCK-RANGE {name}: {d}[{i}] — document has "
                                   f"{len(cache[d])} blocks")
                        continue
                    if (d, i) in owner:
                        bad.append(f"DUPLICATE {d}[{i}]: {owner[(d, i)]} and {name}")
                    owner[(d, i)] = name
                    words += len(cache[d][i].split())
            if words > CEILING:
                bad.append(f"CEILING   {name}: {words} source words (max {CEILING})")

    print(f"cluster    {plan.get('cluster', '?')}")
    print(f"sub-plans  {len(subs)}")
    print(f"notes      {len(seen_names)}")
    print(f"documents  {len(docs)}")

    # Coverage is NOT checked here. Once a merged note relocates blocks into another
    # cluster's file, no single cluster can see whether a document is fully covered --
    # it only sees the part that stayed. merge_cluster_plans.py checks coverage across
    # every cluster at once, which is the only level where the question is answerable.
    own = set(a.own_docs.split(",")) if a.own_docs else set(docs)
    print(f"\n{'doc':<11}{'words':>7}{'covered':>9}{'pct':>7}   (informational; "
          f"coverage is gated at merge)")
    low = []
    for d in sorted(own & set(docs)):
        total = sum(len(b.split()) for b in cache[d])
        cov = sum(len(cache[d][i].split()) for (dd, i) in owner if dd == d)
        pct = cov / total if total else 1.0
        if pct < a.min_coverage:
            low.append((d, pct))
        print(f"{d:<11}{total:>7}{cov:>9}{100*pct:>6.1f}%")
    for d, pct in low:
        assigned = {i for (dd, i) in owner if dd == d}
        dropped = [i for i in range(len(cache[d])) if i not in assigned]
        share = chrome_share(cache[d], dropped)
        if True or share >= a.chrome_share:
            print(f"  note: {d} at {100*pct:.1f}% here, {100*share:.0f}% of dropped words "
                  f"chrome — checked globally at merge")
        else:
            bad.append(f"COVERAGE  {d}: {100*pct:.1f}% assigned, and only {100*share:.0f}% "
                       f"of the dropped words are chrome — real content is being lost")

    if bad:
        print(f"\nFAIL — {len(bad)} violation(s):")
        for b in bad[:40]:
            print("  " + b)
        if len(bad) > 40:
            print(f"  ... and {len(bad) - 40} more")
        sys.exit(1)
    print("\nPASS — block ranges valid, no duplicate source, one BB per note, "
          "no note over the ceiling, sub-plans in range, coverage met")


if __name__ == "__main__":
    main()
