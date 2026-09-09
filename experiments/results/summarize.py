#!/usr/bin/env python3
"""Aggregate the scored retrieval runs (runs2-5) into the tables in RESULTS.md.

Each scored run is {arm, vault, answerable, strategies:{<strat>:{answerable, qids,
k:{K:{recall:[...]}}, budget:{B:{recall:[...]}}, by_type}}}. recall[] is per-query
passage recall over the answerable qids, so:
    Recall@X     = mean(recall)
    All-Recall@X = share(recall == 1.0)   # all gold passages retrieved
The token-BUDGET blocks are the fair comparison; matched-k hands the win to whichever
representation has smaller units (see compare_runs.py / HANDOFF). Writes
summary_tables.json beside this script.

    python3 experiments/results/summarize.py
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RUNS = ROOT / "experiments"
OUT = Path(__file__).resolve().parent / "summary_tables.json"


def agg(arr):
    n = len(arr)
    if not n:
        return None
    return {"recall": round(sum(arr) / n, 4),
            "all_recall": round(sum(1 for x in arr if x >= 0.9999) / n, 4),
            "n": n}


def run_metrics(path):
    d = json.load(open(path))
    out = {}
    for strat, s in d["strategies"].items():
        out[strat] = {
            "budget": {b: agg(blk["recall"]) for b, blk in s.get("budget", {}).items()},
            "k": {k: agg(blk["recall"]) for k, blk in s.get("k", {}).items()},
            "answerable": s.get("answerable"),
        }
    return out


def collect(rundir, files):
    res = {}
    for f in files:
        p = RUNS / rundir / f
        if p.exists():
            res[f[:-5]] = run_metrics(p)
    return res


def main():
    summary = {
        "arm_comparison_runs2": collect("runs2", [
            "chunks_bm25.json", "chunks_hybrid.json", "notes_bm25.json",
            "notes_hybrid.json", "wholedoc_bm25.json", "wholedoc_hybrid.json"]),
        "notes_strategies_runs3": collect("runs3", [
            "chunks_bm25_full.json", "notes_bm25_full.json", "notes_hybrid_full.json",
            "notes_bfs_full.json", "notes_ppr_full.json", "notes_graph_hybrid_full.json",
            "notes_keyword_full.json", "chunks_bm25_evid.json", "notes_bm25_evid.json",
            "notes_hybrid_evid.json", "notes_bfs_evid.json", "notes_ppr_evid.json",
            "notes_graph_hybrid_evid.json"]),
        "degree_sweep_runs4": collect("runs4", [
            f"{d}_{s}.json" for d in ("deg0", "deg2", "deg4", "deg8", "degall")
            for s in ("bfs", "graph_hybrid", "ppr")]),
        "fact_recall": json.load(open(RUNS / "runs4" / "fact_recall.json")),
        "fact_retention": json.load(open(RUNS / "runs4" / "fact_retention.json")),
        "answer_eval_qf_tokens": {a: {k: v for k, v in d.items() if isinstance(v, (int, float, str))}
                                  for a, d in json.load(open(RUNS / "runs5" / "qf_tokens.json")).items()},
        "answer_eval_answers_tokens": {a: {k: v for k, v in d.items() if isinstance(v, (int, float, str))}
                                       for a, d in json.load(open(RUNS / "runs5" / "answers_tokens.json")).items()},
    }
    OUT.write_text(json.dumps(summary, indent=1))
    print(f"wrote {OUT.relative_to(ROOT)}")
    # headline echo
    a = summary["arm_comparison_runs2"]
    for arm in ("chunks_bm25", "notes_bm25", "notes_hybrid"):
        b = a.get(arm, {})
        strat = "bm25" if "bm25" in arm else "hybrid"
        m = b.get(strat, {}).get("budget", {}).get("2048")
        if m:
            print(f"  {arm:16s} @2048  R={m['recall']:.3f}  All={m['all_recall']:.3f}")


if __name__ == "__main__":
    main()
