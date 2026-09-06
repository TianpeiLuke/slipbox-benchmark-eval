#!/usr/bin/env python3
"""Score HippoRAG against lexical/dense/hybrid baselines on an identical corpus.

Reports the paper's own metrics -- Recall@2, Recall@5 and All-Recall@2/@5, where
All-Recall is the fraction of questions for which EVERY gold document was
retrieved -- so the numbers here are directly comparable to Table 2 of
arXiv:2405.14831.

Retrieval units are passages; credit is at the DOCUMENT level, matching both the
paper and the rest of this repo.
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval as R                      # noqa: E402
import hipporag_retrieval as HR            # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--hippo-index", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--strategies", nargs="+",
                    default=["bm25", "dense", "hybrid", "hipporag"])
    ap.add_argument("--ner", default="heuristic", choices=["llm", "heuristic"],
                    help="query-side NER. The paper uses an LLM call; heuristic is a\ndeterministic capitalised-span fallback and is expected to be weaker.")
    ap.add_argument("--backend", default="cline")
    ap.add_argument("--model", default="deepseek/deepseek-v4-flash")
    ap.add_argument("--prewarm", type=int, default=8,
                    help="threads used to fill the query-NER cache before scoring; "
                         "cline is slow per call and scoring is sequential")
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--json")
    a = ap.parse_args()

    corpus = Path(a.corpus)
    con = sqlite3.connect(corpus / "notes.db")
    src = {n: (s or "").strip() for n, s in
           con.execute("SELECT note_id, source_doc FROM notes")}
    con.close()

    idx = json.loads((ROOT / "data/corpus/multihop_rag/index.json").read_text())
    by_title = {v["title"]: d for d, v in idx.items()}
    raw = json.loads((ROOT / "data/raw/multihop_rag/MultiHopRAG.json").read_text())
    pin = set(json.loads(Path(a.questions).read_text()))
    qs = [q for q in raw if q.get("evidence_list") and q.get("answer")
          and q["query"] in pin]
    import random
    random.seed(20260902); random.shuffle(qs); qs = qs[: a.sample]
    print(f"\ncorpus {corpus.name}   n={len(qs)} questions\n")
    print(f"{'strategy':<12}{'R@2':>8}{'R@5':>8}{'AR@2':>8}{'AR@5':>8}{'empty':>8}")

    out = {}
    for name in a.strategies:
        r2, r5, a2, a5, empty = [], [], [], [], 0
        for q in qs:
            gold = {by_title.get(e.get("title", "")) for e in q["evidence_list"]}
            gold = {g for g in gold if g}
            if not gold:
                continue
            if name == "hipporag":
                res = HR.retrieve(Path(a.hippo_index), q["query"], 5, ner=a.ner,
                                  backend=a.backend, model=a.model)
            else:
                res = R.STRATEGIES[name](corpus, q["query"], 5)
            if not res:
                empty += 1
            docs = [src.get(n, "") for n, _ in res]
            for k, rl, al in ((2, r2, a2), (5, r5, a5)):
                got = {d for d in docs[:k] if d in gold}
                rl.append(len(got) / len(gold))
                al.append(1.0 if got == gold else 0.0)
        m = lambda v: float(np.mean(v)) if v else float("nan")
        out[name] = {"R@2": m(r2), "R@5": m(r5), "AR@2": m(a2), "AR@5": m(a5),
                     "empty": empty, "n": len(r2)}
        o = out[name]
        print(f"{name:<12}{o['R@2']:>8.3f}{o['R@5']:>8.3f}{o['AR@2']:>8.3f}"
              f"{o['AR@5']:>8.3f}{empty:>8}")

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, indent=2))
    print()


if __name__ == "__main__":
    main()
