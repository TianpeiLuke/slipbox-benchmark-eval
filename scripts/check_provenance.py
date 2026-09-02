#!/usr/bin/env python3
"""
Check that the vault's provenance matches the plan that produced it.

Provenance is what makes a note scorable: gold evidence in these benchmarks is
document-level, so a retrieved note is credited only through the documents named
in its own `source_docs`. Every other gate checks that source_docs EXISTS. None
checks that it is RIGHT.

That gap matters more than it sounds. A note whose source_docs names the wrong
document is not rejected anywhere: it validates, it indexes, it retrieves. It
simply scores against the wrong gold, and the arm looks worse than it is for a
reason no number points at.

    python3 scripts/check_provenance.py multihop_rag --vault vaults/multihop_rag
    python3 scripts/check_provenance.py multihop_rag --emit          # plan -> expected map

Checks
  MISSING     a planned note absent from the vault
  UNPLANNED   a vault note no plan accounts for
  MISMATCH    source_docs differs from the plan's block assignment
  EMPTY       a non-navigation note with no source_docs at all
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "experiments" / "plans"


def expected(slug: str) -> dict[str, set[str]]:
    """note -> the documents the PLAN says it draws on."""
    P = PLANS / slug
    out: dict[str, set[str]] = {}
    for f in sorted((P / "clusters").glob("c*.json")) if (P / "clusters").is_dir() else []:
        for s in json.loads(f.read_text())["subplans"]:
            for n in s["notes"]:
                out.setdefault(n["note"], set()).update(d for d, v in n["blocks"].items() if v)
    for f in sorted(P.glob("subplan_*_assignments.json")):
        for note, m in json.loads(f.read_text()).items():
            out.setdefault(note, set()).update(d for d, v in m.items() if v)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--vault")
    ap.add_argument("--emit", action="store_true")
    a = ap.parse_args()

    exp = expected(a.slug)
    if a.emit:
        out = PLANS / a.slug / "expected_provenance.json"
        out.write_text(json.dumps({k: sorted(v) for k, v in sorted(exp.items())}, indent=1))
        docs = {d for v in exp.values() for d in v}
        print(f"{len(exp)} notes -> {len(docs)} documents")
        print(f"multi-document notes: {sum(1 for v in exp.values() if len(v) > 1)}")
        print(f"wrote {out.relative_to(ROOT)}")
        return

    vault = Path(a.vault or f"vaults/{a.slug}")
    db = vault / "notes.db"
    if not db.exists():
        print(f"no database at {db} — nothing executed yet.")
        print(f"the plan expects {len(exp)} notes; run --emit to write the expected map.")
        sys.exit(2)

    con = sqlite3.connect(db)
    actual = {}
    navs = set()
    for nid, src, bb in con.execute("SELECT note_id, source_doc, building_block FROM notes"):
        actual[nid] = {s.strip() for s in (src or "").split(",") if s.strip()}
        if bb == "navigation":
            navs.add(nid)
    con.close()

    bad = []
    for note, docs in sorted(exp.items()):
        if note not in actual:
            bad.append(f"MISSING   {note}")
        elif actual[note] != docs:
            miss = docs - actual[note]
            extra = actual[note] - docs
            bad.append(f"MISMATCH  {note}: plan says {sorted(docs)}, vault says "
                       f"{sorted(actual[note])}"
                       + (f" [absent: {sorted(miss)}]" if miss else "")
                       + (f" [unexpected: {sorted(extra)}]" if extra else ""))
    for note in sorted(set(actual) - set(exp) - navs):
        bad.append(f"UNPLANNED {note}: in the vault, in no plan")
    for note in sorted(set(actual) - navs):
        if not actual[note]:
            bad.append(f"EMPTY     {note}: no source_docs — cannot be scored")

    print(f"planned notes {len(exp)}")
    print(f"vault notes   {len(actual)}  ({len(navs)} navigation, exempt)")
    if bad:
        print(f"\nFAIL — {len(bad)} provenance problem(s):")
        for b in bad[:40]:
            print("  " + b)
        if len(bad) > 40:
            print(f"  ... and {len(bad) - 40} more")
        sys.exit(1)
    print("\nPASS — every note's source_docs matches the plan that produced it")


if __name__ == "__main__":
    main()
