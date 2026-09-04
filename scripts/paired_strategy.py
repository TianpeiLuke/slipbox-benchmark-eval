#!/usr/bin/env python3
"""Paired hybrid-vs-capped comparison at BOTH doc level and fact level.

Same questions, same vault, same k -- the only thing that varies is the
retrieval strategy. Reports a paired bootstrap CI on the delta so a small
difference can be told apart from noise.

Exists because per-source capping was adopted on a document-level gain, and
document-level credit is generous: any one unit from a gold document scores
full credit for that document whether or not it carries the needed fact.
"""
import argparse, json, sys, re
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval as R
from sentence_transformers import SentenceTransformer

def sentences(t: str) -> list[str]:
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if len(s.strip()) > 25]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--a", default="hybrid")
    ap.add_argument("--b", default="perdoc1")
    ap.add_argument("--sample", type=int, default=400)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--theta", type=float, default=0.65)
    ap.add_argument("--boot", type=int, default=4000)
    ap.add_argument("--json")
    a = ap.parse_args()

    vault = ROOT / a.vault
    import random
    idx = json.loads((ROOT / "data/corpus/multihop_rag/index.json").read_text())
    by_title = {v["title"]: d for d, v in idx.items()}
    raw = json.loads((ROOT / "data/raw/multihop_rag/MultiHopRAG.json").read_text())
    random.seed(20260902)
    qs = [q for q in raw if q.get("evidence_list")]
    random.shuffle(qs)
    qs = qs[: a.sample]

    import sqlite3
    con = sqlite3.connect(vault / "notes.db")
    body = dict(con.execute("SELECT note_id, body FROM notes"))
    srcs = {n: {x.strip() for x in (s or "").split(",") if x.strip()}
            for n, s in con.execute("SELECT note_id, source_doc FROM notes")}
    con.close()
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    cache: dict[str, np.ndarray] = {}

    def emb(nid):
        if nid not in cache:
            ss = sentences(body.get(nid, ""))
            cache[nid] = (model.encode(ss, normalize_embeddings=True, show_progress_bar=False)
                          if ss else np.zeros((0, 384), dtype=np.float32))
        return cache[nid]

    rows = {a.a: {"doc": [], "fact": []}, a.b: {"doc": [], "fact": []}}
    for q in qs:
        facts, gold = [], set()
        for e in q["evidence_list"]:
            d = by_title.get(e.get("title", ""))
            if d and e.get("fact"):
                facts.append(e["fact"]); gold.add(d)
        if not facts:
            continue
        fe = model.encode(facts, normalize_embeddings=True, show_progress_bar=False)
        for name in (a.a, a.b):
            res = [n for n, _ in R.STRATEGIES[name](vault, q["query"], a.k)]
            got = set()
            for nid in res:
                got |= (srcs.get(nid, set()) & gold)
            sims = np.zeros((len(res), len(facts)), dtype=np.float32)
            for r, nid in enumerate(res):
                ue = emb(nid)
                if len(ue):
                    sims[r] = (ue @ fe.T).max(axis=0)
            hit = (sims >= a.theta).any(axis=0)
            rows[name]["doc"].append(len(got) / len(gold))
            rows[name]["fact"].append(float(hit.mean()))

    rng = np.random.default_rng(20260902)
    out = {"vault": a.vault, "k": a.k, "theta": a.theta, "n": len(rows[a.a]["doc"])}
    print(f"\n{a.vault}   n={out['n']}   k={a.k}   theta={a.theta}")
    print(f"{'level':<8}{a.a:>10}{a.b:>10}{'delta':>10}   95% CI            verdict")
    for lvl in ("doc", "fact"):
        x = np.array(rows[a.a][lvl]); y = np.array(rows[a.b][lvl])
        d = y - x
        bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(a.boot)])
        lo, hi = np.percentile(bs, [2.5, 97.5])
        sig = "significant" if (lo > 0 or hi < 0) else "not significant"
        print(f"{lvl:<8}{x.mean():>10.3f}{y.mean():>10.3f}{d.mean():>+10.3f}   "
              f"[{lo:+.3f}, {hi:+.3f}]  {sig}")
        out[lvl] = {"a": float(x.mean()), "b": float(y.mean()), "delta": float(d.mean()),
                    "ci": [float(lo), float(hi)], "significant": sig == "significant"}
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, indent=2))
    print()

if __name__ == "__main__":
    main()
