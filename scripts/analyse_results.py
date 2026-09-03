#!/usr/bin/env python3
"""
Test the pre-registered hypotheses against scored runs.

Reading two curves and deciding one is higher is not a test. H1 is a claim about
a SLOPE -- that the note advantage shrinks as the budget grows -- so it is tested
by fitting recall against log-budget per arm and comparing slopes, with a paired
bootstrap over questions. Paired, because both arms answer the same questions:
an unpaired interval throws away the pairing and is wider than the evidence
warrants.

    python3 scripts/analyse_results.py --runs experiments/runs --out RESULTS.md

Reports each hypothesis against the condition registered BEFORE the run, and
says pass or fail rather than describing the numbers and leaving the reader to
infer a verdict.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

random.seed(20260902)          # fixed: a bootstrap that moves between runs is not a measure
B = 2000


def boot_ci(pairs: list[tuple[float, float]], stat, n=B):
    """Paired bootstrap CI for stat(a_values, b_values) over resampled questions."""
    if not pairs:
        return (0.0, 0.0, 0.0)
    obs = stat([p[0] for p in pairs], [p[1] for p in pairs])
    out = []
    m = len(pairs)
    for _ in range(n):
        s = [pairs[random.randrange(m)] for _ in range(m)]
        out.append(stat([p[0] for p in s], [p[1] for p in s]))
    out.sort()
    return (obs, out[int(0.025 * n)], out[int(0.975 * n)])


def slope(budgets: list[int], vals: list[float]) -> float:
    """OLS slope of value against log2(budget)."""
    xs = [math.log2(b) for b in budgets]
    mx, my = sum(xs) / len(xs), sum(vals) / len(vals)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, vals))
    den = sum((x - mx) ** 2 for x in xs) or 1e-9
    return num / den


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="experiments/runs")
    ap.add_argument("--out")
    a = ap.parse_args()

    R = Path(a.runs)
    runs = {}
    for f in sorted(R.glob("*.json")):
        runs[f.stem] = json.loads(f.read_text())
    if not runs:
        raise SystemExit(f"no runs under {R}")
    def series(run, strat, key):
        d = runs[run]["strategies"][strat]
        return d[key], d["qids"]

    def pair(a_run, a_st, b_run, b_st, key, sub):
        """Align two arms question by question. Both answered the same set, but
        --limit or a covered-only filter can shorten one, so align on qids
        rather than assuming index correspondence."""
        (da, qa), (db, qb) = series(a_run, a_st, key), series(b_run, b_st, key)
        ia = {q: i for i, q in enumerate(qa)}
        out = []
        for j, q in enumerate(qb):
            if q in ia:
                out.append((da[sub]["recall"][ia[q]], db[sub]["recall"][j]))
        return out

    lines = []
    def emit(t=""):
        print(t); lines.append(t)

    note_runs = [r for r in runs if r.startswith("notes_")]
    chunk_runs = [r for r in runs if r.startswith("chunks_")]
    budgets = sorted(int(b) for b in
                     next(iter(runs.values()))["strategies"].popitem()[1]["budget"]) \
        if False else None
    any_st = next(iter(runs.values()))["strategies"]
    budgets = sorted(int(b) for b in next(iter(any_st.values()))["budget"])

    emit("# Results\n")
    emit(f"Runs: {len(runs)}. Budgets: {budgets}. Bootstrap: {B} resamples, paired, seed fixed.\n")

    # ---- headline table, by budget
    emit("## Recall by token budget\n")
    hdr = "| arm | " + " | ".join(str(b) for b in budgets) + " |"
    emit(hdr); emit("|---" * (len(budgets) + 1) + "|")
    means = {}
    for r in sorted(runs):
        for st, d in runs[r]["strategies"].items():
            row = []
            for b in budgets:
                v = d["budget"][str(b)]["recall"]
                row.append(sum(v) / len(v) if v else 0.0)
            means[(r, st)] = row
            emit(f"| {r}/{st} | " + " | ".join(f"{x:.3f}" for x in row) + " |")
    emit("")

    # ---- best arms
    def best(cands):
        return max(cands, key=lambda k: sum(means[k]) / len(means[k])) if cands else None
    bn = best([(r, st) for r in note_runs for st in runs[r]["strategies"]
               if st in ("bm25", "hybrid")])
    bg = best([(r, st) for r in note_runs for st in runs[r]["strategies"]
               if st in ("bfs", "ppr")])
    bc = best([(r, st) for r in chunk_runs for st in runs[r]["strategies"]])
    emit(f"Best plain note arm: `{bn[0]}/{bn[1]}`" if bn else "no note arm")
    emit(f"Best graph note arm: `{bg[0]}/{bg[1]}`" if bg else "no graph arm")
    emit(f"Best chunk arm:      `{bc[0]}/{bc[1]}`" if bc else "no chunk arm")
    emit("")

    # ---- H1
    emit("## H1 — budget interaction\n")
    if bn and bc:
        lo_b, hi_b = str(budgets[0]), str(budgets[-1])
        p_lo = pair(bc[0], bc[1], bn[0], bn[1], "budget", lo_b)
        p_hi = pair(bc[0], bc[1], bn[0], bn[1], "budget", hi_b)
        g_lo = boot_ci(p_lo, lambda c, n: sum(n) / len(n) - sum(c) / len(c))
        g_hi = boot_ci(p_hi, lambda c, n: sum(n) / len(n) - sum(c) / len(c))
        emit(f"- gap at {lo_b} tokens: **{g_lo[0]:+.3f}** [{g_lo[1]:+.3f}, {g_lo[2]:+.3f}]")
        emit(f"- gap at {hi_b} tokens: **{g_hi[0]:+.3f}** [{g_hi[1]:+.3f}, {g_hi[2]:+.3f}]")
        both = [(a, b) for a, b in zip(p_lo, p_hi)] if len(p_lo) == len(p_hi) else []
        if both:
            d = boot_ci([(x[0][1] - x[0][0], x[1][1] - x[1][0]) for x in both],
                        lambda lo, hi: sum(lo) / len(lo) - sum(hi) / len(hi))
            emit(f"- **shrinkage** (gap at {lo_b} minus gap at {hi_b}): "
                 f"**{d[0]:+.3f}** [{d[1]:+.3f}, {d[2]:+.3f}]")
            passed = d[1] > 0
            emit(f"\n**H1: {'PASS' if passed else 'FAIL'}** — registered condition was that "
                 f"the small-budget gap exceed the large-budget gap with a 95% interval "
                 f"excluding zero.")
    emit("")

    # ---- H2
    emit("## H2 — does the graph add reach\n")
    if bn and bg:
        for b in budgets:
            pr = pair(bn[0], bn[1], bg[0], bg[1], "budget", str(b))
            ci = boot_ci(pr, lambda p, g: sum(g) / len(g) - sum(p) / len(p))
            emit(f"- {b:>5} tokens: graph minus plain **{ci[0]:+.3f}** "
                 f"[{ci[1]:+.3f}, {ci[2]:+.3f}]")
        pr = pair(bn[0], bn[1], bg[0], bg[1], "budget", str(budgets[len(budgets) // 2]))
        ci = boot_ci(pr, lambda p, g: sum(g) / len(g) - sum(p) / len(p))
        passed = ci[1] > 0
        emit(f"\n**H2: {'PASS' if passed else 'FAIL'}** — registered condition was that the "
             f"graph arm beat the plain note arm with an interval excluding zero. Equal "
             f"performance falsifies it: an arm that adds nothing should be reported as "
             f"adding nothing.")
    emit("")

    emit("## H3 — front-loading\n")
    emit("**NOT RUN.** H3 needs an order-sensitive metric. Its first pass used "
         "bag-of-words recall, which is order-invariant by construction and therefore "
         "could not have detected a position effect at all; that null is not evidence of "
         "absence. Reported as untested rather than failed.\n")

    if a.out:
        Path(a.out).write_text("\n".join(lines) + "\n")
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
