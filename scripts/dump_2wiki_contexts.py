#!/usr/bin/env python3
"""Assemble 2WikiMultiHopQA contexts from HippoRAG vs chunk retrieval, for answering.

Every HippoRAG number in this repo is retrieval-only. The whole benchmark arc
found retrieval proxies disagreeing with downstream answers on the SAME
intervention, so HippoRAG's +0.198 R@5 on 2Wiki is not yet a demonstrated
answer-quality advantage. This produces the contexts that let a reader settle
it: same questions, same token budget, one arm per retriever, in the jsonl
shape answer_from_contexts.py consumes.
"""
import argparse, json, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval as R                    # noqa: E402
import hipporag_retrieval as HR          # noqa: E402
from score_retrieval import unit_tokens  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default="data/chunks/twowiki_200")
    ap.add_argument("--hippo-index", default="experiments/runs12/hippo_2wiki")
    ap.add_argument("--strategy", required=True, help="hybrid | bm25 | hipporag")
    ap.add_argument("--budget", type=int, default=2048)
    ap.add_argument("--ner", default="llm")
    ap.add_argument("--backend", default="cline")
    ap.add_argument("--model", default="deepseek/deepseek-v4-flash")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    corpus = ROOT / a.corpus
    qs = json.loads((corpus / "questions.json").read_text())
    con = sqlite3.connect(corpus / "notes.db")
    body = dict(con.execute("SELECT note_id, body FROM notes"))
    con.close()
    toks = unit_tokens(corpus / "notes.db", evidence_only=True)
    pool = max(40, a.budget // 24)

    def ranked(q: str) -> list[str]:
        if a.strategy == "hipporag":
            hits = HR.retrieve(ROOT / a.hippo_index, q, pool, ner=a.ner,
                               backend=a.backend, model=a.model)
        else:
            hits = R.STRATEGIES[a.strategy](corpus, q, pool)
        return [n for n, _ in hits]

    out = ROOT / a.out; out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        for i, q in enumerate(qs, 1):
            used, picked = 0, []
            for nid in ranked(q["query"]):
                t = toks.get(nid, 0)
                if used + t > a.budget:
                    continue
                used += t; picked.append(nid)
            ctx = "\n\n---\n\n".join(body[n] for n in picked)
            fh.write(json.dumps({"qid": q["query"], "context": ctx, "units": len(picked),
                                 "ctx_chars": len(ctx), "gold": q["answer"],
                                 "null": False, "type": q.get("type")}) + "\n")
            if i % 50 == 0:
                print(f"  {i}/{len(qs)}", flush=True)
    print(f"wrote {len(qs)} contexts -> {out}")


if __name__ == "__main__":
    main()
