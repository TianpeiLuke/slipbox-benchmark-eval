#!/usr/bin/env python3
"""
Paired comparison of two scored runs over the questions they share.

Any two vault variants answer the SAME questions, so the comparison must be
paired -- an unpaired interval discards that and is wider than the evidence
warrants. Questions are matched by qid, not by position: a variant that drops
an unanswerable question would otherwise silently shift every later pair.

    python3 scripts/compare_runs.py A.json B.json --strategy bm25

Prints B - A per metric with a 95% paired-bootstrap CI. A CI straddling zero
means the variant did not move retrieval, which for an ablation is the
informative answer, not a failed one.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

random.seed(20260902)
B = 4000


def paired_delta(a: list[float], b: list[float]) -> tuple[float, float, float]:
    d = [y - x for x, y in zip(a, b)]
    obs = sum(d) / len(d)
    m, out = len(d), []
    for _ in range(B):
        s = sum(d[random.randrange(m)] for _ in range(m))
        out.append(s / m)
    out.sort()
    return obs, out[int(0.025 * B)], out[int(0.975 * B)]


def load(path: Path, strategy: str):
    d = json.load(open(path))
    if strategy not in d["strategies"]:
        raise SystemExit(f"{path}: no strategy {strategy!r} (has {list(d['strategies'])})")
    return d["strategies"][strategy]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--label-a", default=None)
    ap.add_argument("--label-b", default=None)
    args = ap.parse_args()

    A, Bv = load(Path(args.a), args.strategy), load(Path(args.b), args.strategy)
    la = args.label_a or Path(args.a).stem
    lb = args.label_b or Path(args.b).stem

    ia = {q: i for i, q in enumerate(A["qids"])}
    shared = [(ia[q], j) for j, q in enumerate(Bv["qids"]) if q in ia]
    if not shared:
        raise SystemExit("no shared qids")
    print(f"{la}  ->  {lb}   [{args.strategy}]   {len(shared)} shared questions")
    if len(shared) != len(A["qids"]) or len(shared) != len(Bv["qids"]):
        print(f"  note: {len(A['qids'])} vs {len(Bv['qids'])} questions; compared on the intersection")

    rows = []
    for group in ("k", "budget"):
        for key in sorted(A.get(group, {}), key=lambda s: int(s)):
            if key not in Bv.get(group, {}):
                continue
            for metric in ("recall", "all"):
                va = [A[group][key][metric][i] for i, _ in shared]
                vb = [Bv[group][key][metric][j] for _, j in shared]
                obs, lo, hi = paired_delta(va, vb)
                rows.append((f"{group}={key}", metric,
                             sum(va) / len(va), sum(vb) / len(vb), obs, lo, hi))

    w = max(len(r[0]) for r in rows)
    print(f"\n{'unit':<{w}}  {'metric':<7} {la[:14]:>14} {lb[:14]:>14}   {'delta':>8}  95% CI")
    for unit, metric, ma, mb, obs, lo, hi in rows:
        sig = "" if lo <= 0 <= hi else "  *"
        print(f"{unit:<{w}}  {metric:<7} {ma:14.3f} {mb:14.3f}   {obs:+8.3f}  [{lo:+.3f},{hi:+.3f}]{sig}")
    print("\n* = CI excludes zero")


if __name__ == "__main__":
    main()
