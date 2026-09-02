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
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
CEILING = 1800
BB = {"concept", "model", "procedure", "empirical_observation",
      "argument", "counter_argument", "hypothesis", "navigation"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--min-coverage", type=float, default=0.80)
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
        if not 4 <= n <= 15:
            bad.append(f"SIZE      {s['slug']}: {n} notes, rule is 4-15")
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

    print(f"\n{'doc':<11}{'words':>7}{'covered':>9}{'pct':>7}")
    low = []
    for d in docs:
        total = sum(len(b.split()) for b in cache[d])
        cov = sum(len(cache[d][i].split()) for (dd, i) in owner if dd == d)
        pct = cov / total if total else 1.0
        if pct < a.min_coverage:
            low.append((d, pct))
        print(f"{d:<11}{total:>7}{cov:>9}{100*pct:>6.1f}%")
    for d, pct in low:
        bad.append(f"COVERAGE  {d}: {100*pct:.1f}% assigned (floor {100*a.min_coverage:.0f}%)")

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
