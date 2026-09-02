#!/usr/bin/env python3
"""
Merge per-cluster plans into one corpus plan, and surface what only merging reveals.

Each cluster is planned by an agent that sees only its own documents. That is
what makes the fan-out affordable, and it is also its blind spot: two clusters
covering the same entity cannot know about each other. Three failures follow,
and none is visible inside a cluster.

    python3 scripts/merge_cluster_plans.py multihop_rag --clusters <dir>

  COLLISION   two clusters chose the same filename for different content.
              Left alone, one silently overwrites the other at execution time.
  SPLIT-ENTITY  two clusters wrote near-identical filenames for what is likely
              one entity. Two half-notes split the evidence, and a multi-hop
              question needing both retrieves neither well -- the exact failure
              the dedup rule exists to prevent.
  ORPHAN-DOC  a document no cluster claimed.

Nothing is merged automatically. Deciding that two notes are the same concept
requires reading both, and a wrong merge destroys evidence rather than
duplicating it; the script reports candidates and leaves the judgement.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
SIM = 0.86


def norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name[:-3].lower()).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--clusters", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()

    files = sorted(Path(a.clusters).glob("c*.json"))
    if not files:
        print(f"no cluster plans under {a.clusters}")
        sys.exit(2)

    owner: dict[str, list[str]] = defaultdict(list)
    notes: dict[str, dict] = {}
    claimed: set[str] = set()
    total_sub = 0
    for f in files:
        p = json.loads(f.read_text())
        cid = p.get("cluster", f.stem)
        total_sub += len(p["subplans"])
        for s in p["subplans"]:
            for n in s["notes"]:
                owner[n["note"]].append(cid)
                notes.setdefault(n["note"], {"bb": n["bb"], "cluster": cid, "blocks": {}})
                for d, ids in n["blocks"].items():
                    notes[n["note"]]["blocks"].setdefault(d, []).extend(ids)
                    claimed.add(d)

    idx = json.loads((CORPUS / a.slug / "index.json").read_text())
    print(f"clusters   {len(files)}")
    print(f"sub-plans  {total_sub}")
    print(f"notes      {len(notes)}")
    print(f"documents  {len(claimed)} claimed of {len(idx)} in corpus")

    issues = 0
    coll = {n: cs for n, cs in owner.items() if len(cs) > 1}
    if coll:
        issues += len(coll)
        print(f"\nCOLLISION — same filename from more than one cluster ({len(coll)}):")
        for n, cs in sorted(coll.items())[:20]:
            print(f"  {n}  <- {', '.join(cs)}")

    keys = sorted(notes)
    normed = {k: norm(k) for k in keys}
    near = []
    by_first = defaultdict(list)
    for k in keys:
        first = normed[k].split()[0] if normed[k] else ""
        by_first[first].append(k)
    for group in by_first.values():
        for i, x in enumerate(group):
            for y in group[i + 1:]:
                if notes[x]["cluster"] == notes[y]["cluster"]:
                    continue
                r = SequenceMatcher(None, normed[x], normed[y]).ratio()
                if r >= SIM:
                    near.append((round(r, 3), x, notes[x]["cluster"], y, notes[y]["cluster"]))
    near.sort(reverse=True)
    if near:
        print(f"\nSPLIT-ENTITY — near-identical names in different clusters ({len(near)}):")
        for r, x, cx, y, cy in near[:25]:
            print(f"  {r}  {x} ({cx})  ~  {y} ({cy})")
        print("  Read both before merging. A wrong merge destroys evidence; leaving a real "
              "duplicate splits it. Neither is automatic.")

    orphan = sorted(set(idx) - claimed)
    if orphan:
        print(f"\nORPHAN-DOC — claimed by no cluster ({len(orphan)}): {', '.join(orphan[:15])}")

    if a.out:
        Path(a.out).write_text(json.dumps(
            {n: {"bb": v["bb"], "cluster": v["cluster"],
                 "blocks": {d: sorted(set(ids)) for d, ids in v["blocks"].items()}}
             for n, v in notes.items()}, indent=1))
        print(f"\nwrote {a.out}")
    if coll:
        print("\nCollisions are blocking: a filename used twice means one note overwrites "
              "the other at execution time.")
        sys.exit(1)


if __name__ == "__main__":
    main()
