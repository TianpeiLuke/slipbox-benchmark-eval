#!/usr/bin/env python3
"""
Stamp each plan's status from the vault, not from anyone's recollection.

A status field is a claim that decays: it is written when a plan is authored and
nothing forces it to change when the plan is executed. This derives it instead —
a plan is `completed` when every note it plans exists in the vault, and `ready`
when some do not — so the field cannot drift from the thing it describes.

    python3 scripts/mark_plan_status.py multihop_rag --vault vaults/multihop_rag
    python3 scripts/mark_plan_status.py multihop_rag --vault ... --check

--check reports without writing, and exits non-zero if any status is wrong. Use
it as a gate; use the plain form to correct them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--vault")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    P = ROOT / "experiments" / "plans" / a.slug
    V = Path(a.vault or f"vaults/{a.slug}")
    disk = {p.name for p in V.glob("*.md")}

    rows: list[tuple[str, str, int, int]] = []   # name, status, done, total
    wrong = []

    # cluster plans carry their status inside the JSON
    for f in sorted((P / "clusters").glob("c*.json")):
        plan = json.loads(f.read_text())
        notes = [n["note"] for s in plan["subplans"] for n in s["notes"]]
        done = sum(1 for n in notes if n in disk)
        status = "completed" if done == len(notes) else "ready"
        rows.append((f.name, status, done, len(notes)))
        if plan.get("status") != status:
            wrong.append(f"{f.name}: {plan.get('status', 'no status')} -> {status}")
            if not a.check:
                plan["status"] = status
                plan["executed_notes"] = f"{done}/{len(notes)}"
                f.write_text(json.dumps(plan, indent=1))

    # sub-plan markdown carries it in frontmatter, and in the master's index table
    for f in sorted(P.glob("subplan_*.md")):
        af = P / f"{f.stem}_assignments.json"
        if not af.exists():
            continue
        notes = list(json.loads(af.read_text()))
        done = sum(1 for n in notes if n in disk)
        status = "completed" if done == len(notes) else "ready"
        rows.append((f.name, status, done, len(notes)))
        s = f.read_text()
        cur = re.search(r'^status: (\w+)$', s, re.M)
        if not cur or cur.group(1) != status:
            wrong.append(f"{f.name}: {cur.group(1) if cur else 'none'} -> {status}")
            if not a.check:
                f.write_text(re.sub(r'^status: \w+$', f'status: {status}', s, flags=re.M))

    # the pilot master's index table repeats each sub-plan's status; keep it in step
    pm = P / "plan_digest_multihop_rag_slice.md"
    if pm.exists():
        s = pm.read_text()
        new = re.sub(r'(\| \[\d+ [^\]]+\]\(subplan_[^)]+\.md\)[^|]*(?:\|[^|]*){4}\| )ready( \|)',
                     r'\1completed\2', s)
        if new != s:
            wrong.append(f"{pm.name}: index table rows still 'ready'")
            if not a.check:
                pm.write_text(new)

    done_n = sum(1 for _, st, _, _ in rows if st == "completed")
    print(f"plans           {len(rows)}")
    print(f"completed       {done_n}")
    print(f"not completed   {len(rows) - done_n}")
    for name, st, d, t in rows:
        if st != "completed":
            print(f"  {name}: {d}/{t} notes written")
    if wrong:
        verb = "would correct" if a.check else "corrected"
        print(f"\n{verb} {len(wrong)} stale status field(s):")
        for w in wrong[:20]:
            print("  " + w)
        if a.check:
            sys.exit(1)
    else:
        print("\nevery status matches the vault")


if __name__ == "__main__":
    main()
