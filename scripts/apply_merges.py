#!/usr/bin/env python3
"""
Apply note merges across cluster plans, from an explicit decision list.

Merging is the operation that turns two half-notes into one note carrying two
source documents -- which is exactly what a multi-hop question needs, since a
single retrieval then satisfies evidence from both. Splitting the same subject
across two notes loses both: neither carries the whole claim, and retrieval
divides between them.

But a wrong merge destroys evidence rather than duplicating it, so nothing here
is automatic except an EXACT filename collision, where two clusters already
chose the same name for the same subject and one would otherwise overwrite the
other at execution time.

    python3 scripts/apply_merges.py multihop_rag --clusters <dir> --decisions merges.json
    python3 scripts/apply_merges.py multihop_rag --clusters <dir> --auto-collisions

decisions.json is {"keep_this.md": ["drop_this.md", ...]}. The kept note absorbs
every source block of the dropped ones; the dropped names disappear.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load(d: Path) -> dict[str, dict]:
    return {f.stem: json.loads(f.read_text()) for f in sorted(d.glob("c*.json"))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--clusters", required=True)
    ap.add_argument("--decisions")
    ap.add_argument("--auto-collisions", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    D = Path(a.clusters)
    plans = load(D)

    merges: dict[str, list[str]] = {}
    if a.decisions:
        merges.update(json.loads(Path(a.decisions).read_text()))

    if a.auto_collisions:
        where: dict[str, list[str]] = defaultdict(list)
        for cid, p in plans.items():
            for s in p["subplans"]:
                for n in s["notes"]:
                    where[n["note"]].append(cid)
        for name, cids in where.items():
            if len(cids) > 1:
                # same name from two clusters: they already agreed on the subject,
                # so the merge target is the name itself
                merges.setdefault(name, [])

    if not merges:
        print("nothing to merge")
        return

    drop_to_keep = {d: k for k, ds in merges.items() for d in ds}
    absorbed: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    kept_bb: dict[str, str] = {}
    removed = 0

    for cid, p in plans.items():
        for s in p["subplans"]:
            out = []
            for n in s["notes"]:
                name = n["note"]
                target = drop_to_keep.get(name, name if name in merges else None)
                if target is None:
                    out.append(n)
                    continue
                for d, ids in n["blocks"].items():
                    absorbed[target][d].extend(ids)
                kept_bb.setdefault(target, n["bb"])
                if name != target:
                    removed += 1
            s["notes"] = out

    # place each merged note once, in the first cluster that had it
    placed: set[str] = set()
    for cid, p in sorted(plans.items()):
        for s in p["subplans"]:
            for target in list(absorbed):
                if target in placed:
                    continue
                if any(d in {dd for n in s["notes"] for dd in n["blocks"]}
                       for d in absorbed[target]) or True:
                    pass
        # fall through: append merged notes to the first sub-plan of their home cluster
    for target, blocks in absorbed.items():
        home = None
        for cid, p in sorted(plans.items()):
            for s in p["subplans"]:
                if any(d in blocks for n in s["notes"] for d in n["blocks"]):
                    home = s
                    break
            if home:
                break
        if home is None:
            home = sorted(plans.items())[0][1]["subplans"][0]
        entry = {"note": target, "bb": kept_bb[target],
                 "blocks": {d: sorted(set(v)) for d, v in blocks.items()}}
        if len(home["notes"]) >= 15:
            # Appending here would break the 4-15 rule the plan is held to, so the
            # merged notes get their own sub-plan rather than silently oversizing one.
            hp = next(p for p in plans.values() if home in p["subplans"])
            spill = next((s for s in hp["subplans"]
                          if s["slug"].endswith("_merged") and len(s["notes"]) < 15), None)
            if spill is None:
                spill = {"slug": f"{home['slug']}_merged",
                         "title": f"{home['title']} — merged cross-cluster notes",
                         "notes": []}
                hp["subplans"].append(spill)
            spill["notes"].append(entry)
        else:
            home["notes"].append(entry)
        placed.add(target)

    print(f"merged {len(absorbed)} note(s); {removed} duplicate name(s) removed")
    for t, b in sorted(absorbed.items()):
        print(f"  {t}  <- {len(b)} document(s): {', '.join(sorted(b))}")
    if a.dry_run:
        print("\ndry run — nothing written")
        return
    for cid, p in plans.items():
        p["subplans"] = [s for s in p["subplans"] if s["notes"]]
        (D / f"{cid}.json").write_text(json.dumps(p, indent=1))
    print(f"\nrewrote {len(plans)} cluster plans")


if __name__ == "__main__":
    main()
