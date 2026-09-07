#!/usr/bin/env python3
"""Score HippoRAG and baselines on 2WikiMultiHopQA against the paper's numbers.

2Wiki is where HippoRAG reports its largest published margin -- R@2 71.5 / R@5
89.5 with Contriever against BM25's 51.8 / 61.9 -- so it is the sharpest check
on whether an implementation reproduces the method's advantage. Its hop is an
entity bridge between Wikipedia articles, the structure the method is designed
for.

Credit is by passage TITLE, matching the benchmark's supporting_facts.
"""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval as R                      # noqa: E402
import hipporag_retrieval as HR            # noqa: E402

# Gutierrez et al., NeurIPS 2024, Table 2 (2Wiki column)
PUBLISHED = {
    "bm25":     {"R@2": 0.518, "R@5": 0.619},
    "hipporag": {"R@2": 0.715, "R@5": 0.895},
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--hippo-index", required=True)
    ap.add_argument("--strategies", nargs="+",
                    default=["bm25", "dense", "hybrid", "hipporag"])
    ap.add_argument("--ner", default="llm", choices=["llm", "heuristic"])
    ap.add_argument("--backend", default="cline")
    ap.add_argument("--model", default="deepseek/deepseek-v4-flash")
    ap.add_argument("--prewarm", type=int, default=10)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--json")
    a = ap.parse_args()

    corpus = Path(a.corpus)
    qs = json.loads((corpus / "questions.json").read_text())
    if a.sample:
        qs = qs[: a.sample]
    con = sqlite3.connect(corpus / "notes.db")
    src = {n: (s or "") for n, s in con.execute("SELECT note_id, source_doc FROM notes")}
    con.close()

    if "hipporag" in a.strategies and a.ner == "llm" and a.prewarm > 0:
        from concurrent.futures import ThreadPoolExecutor
        st = HR.load(Path(a.hippo_index))
        ask = HR.make_ask(a.backend)
        todo = [q["query"] for q in qs if q["query"] not in st["qcache"]]
        if todo:
            print(f"prewarming query NER: {len(todo)} calls via {a.backend}/{a.model}")
            with ThreadPoolExecutor(max_workers=a.prewarm) as ex:
                list(ex.map(lambda x: HR.query_entities(st, x, ask, a.model, "llm"), todo))
            if st.get("fellback"):
                print(f"  !! {st['fellback']}/{len(todo)} NER calls fell back to heuristic")

    print(f"\n2WikiMultiHopQA   n={len(qs)} questions   {len(src)} passages\n")
    print(f"{'strategy':<12}{'R@2':>8}{'R@5':>8}{'AR@2':>8}{'AR@5':>8}"
          f"{'  paper R@2':>12}{'  paper R@5':>12}")
    out = {}
    for name in a.strategies:
        r2, r5, a2, a5 = [], [], [], []
        for q in qs:
            gold = set(q["gold_titles"])
            if not gold:
                continue
            if name == "hipporag":
                res = HR.retrieve(Path(a.hippo_index), q["query"], 5, ner=a.ner,
                                  backend=a.backend, model=a.model)
            else:
                res = R.STRATEGIES[name](corpus, q["query"], 5)
            titles = [src.get(n, "") for n, _ in res]
            for k, rl, al in ((2, r2, a2), (5, r5, a5)):
                got = {t for t in titles[:k] if t in gold}
                rl.append(len(got) / len(gold))
                al.append(1.0 if got == gold else 0.0)
        m = lambda v: float(np.mean(v)) if v else float("nan")
        out[name] = {"R@2": m(r2), "R@5": m(r5), "AR@2": m(a2), "AR@5": m(a5),
                     "n": len(r2)}
        pub = PUBLISHED.get(name, {})
        ps2 = f"{pub['R@2']:.3f}" if pub else "-"
        ps5 = f"{pub['R@5']:.3f}" if pub else "-"
        o = out[name]
        print(f"{name:<12}{o['R@2']:>8.3f}{o['R@5']:>8.3f}{o['AR@2']:>8.3f}"
              f"{o['AR@5']:>8.3f}{ps2:>12}{ps5:>12}")

    if "hipporag" in out and "bm25" in out:
        d = out["hipporag"]["R@5"] - out["bm25"]["R@5"]
        pd_ = PUBLISHED["hipporag"]["R@5"] - PUBLISHED["bm25"]["R@5"]
        print(f"\nHippoRAG - BM25 at R@5:  ours {d:+.3f}   paper {pd_:+.3f}")
        print("The paper's advantage is large and positive. Reproducing its SIGN and "
              "rough size is the check;\nabsolute values differ because the corpus here "
              "is a subsample and the encoder is MiniLM.")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"ours": out, "published": PUBLISHED}, indent=2))
    print()


if __name__ == "__main__":
    main()
