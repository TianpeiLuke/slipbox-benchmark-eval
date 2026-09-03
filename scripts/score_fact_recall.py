#!/usr/bin/env python3
"""
Score retrieval at the level of the gold FACT, not the gold document.

The main harness credits a note with the documents in its `source_docs`, which
is generous: this vault holds ~9.6 notes per document, so retrieving any one of
them scores the document even when the passage the question needs is in a
different note. That is fine for comparing arms and wrong for asking "could the
retrieved context actually answer this".

MultiHop-RAG carries the finer gold already -- each evidence entry names a
document AND the `fact` sentence the question depends on. This scores against
those sentences.

Presence is tested per SENTENCE of a retrieved unit, not per unit. Embedding a
whole note against a single fact fails by construction: a note condensing three
sentences resembles their conjunction and no one of them, which is why the
earlier whole-note semantic check scored 4.7% and was abandoned. Splitting the
unit and taking the best sentence gives a paraphrase a fair chance while still
demanding that some single span carry the fact.

    python3 scripts/score_fact_recall.py multihop_rag \
        --arms notes=vaults/multihop_rag chunks=data/chunks/multihop_rag \
        --theta 0.65 --sample 150
"""

from __future__ import annotations

import argparse, json, random, re, sqlite3, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from retrieval import hybrid  # noqa: E402

SENT = re.compile(r"(?<=[.!?])\s+")
NON_EVIDENCE = re.compile(r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)",
                          re.M | re.S)


def sentences(text: str) -> list[str]:
    text = NON_EVIDENCE.sub("", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    return [s.strip() for s in SENT.split(text) if len(s.strip().split()) >= 4]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--arms", nargs="+", required=True, help="name=path ...")
    ap.add_argument("--thetas", default="0.55,0.65,0.75",
                    help="evaluated in ONE pass; the calibration validates verbatim\n                         presence, not paraphrase, so sensitivity is reported not hidden")
    ap.add_argument("--sample", type=int, default=150)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--json")
    a = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    idx = json.loads((ROOT / "data/corpus" / a.slug / "index.json").read_text())
    by_title = {v["title"]: d for d, v in idx.items()}
    raw = json.loads((ROOT / "data/raw" / a.slug / "MultiHopRAG.json").read_text())

    random.seed(20260902)
    qs = [q for q in raw if q.get("evidence_list")]
    random.shuffle(qs)
    qs = qs[: a.sample]

    out = {}
    for spec in a.arms:
        name, _, vp = spec.partition("=")
        vault = Path(vp)
        con = sqlite3.connect(vault / "notes.db")
        body = {n: b for n, b in con.execute("SELECT note_id, body FROM notes")}
        srcs = {n: {d.strip() for d in (s or "").split(",") if d.strip()}
                for n, s in con.execute("SELECT note_id, source_doc FROM notes")}
        con.close()

        sent_cache: dict[str, np.ndarray] = {}

        def unit_emb(nid: str) -> np.ndarray:
            if nid not in sent_cache:
                ss = sentences(body.get(nid, ""))
                sent_cache[nid] = (model.encode(ss, normalize_embeddings=True,
                                                show_progress_bar=False)
                                   if ss else np.zeros((0, 384), dtype=np.float32))
            return sent_cache[nid]

        THETAS = [float(t) for t in a.thetas.split(",")]
        # sim[(qi, rank, fact)] computed once; thresholds applied afterwards, so
        # a sensitivity sweep costs no extra encoding
        per_q = []
        for q in qs:
            facts, golddocs = [], set()
            for e in q["evidence_list"]:
                d = by_title.get(e.get("title", ""))
                if d and e.get("fact"):
                    facts.append((e["fact"], d)); golddocs.add(d)
            if not facts:
                continue
            fe = model.encode([f for f, _ in facts], normalize_embeddings=True,
                              show_progress_bar=False)
            res = [n for n, _ in hybrid(vault, q["query"], a.k)]
            sims = np.zeros((len(res), len(facts)), dtype=np.float32)
            for r, nid in enumerate(res):
                ue = unit_emb(nid)
                if len(ue):
                    sims[r] = (ue @ fe.T).max(axis=0)
            dr = {}
            for r, nid in enumerate(res, 1):
                for d in srcs.get(nid, ()):
                    if d in golddocs: dr.setdefault(d, r)
            per_q.append((sims, golddocs, dr, len(facts)))

        import statistics as st
        arm = {}
        for th in THETAS:
            fr = {k: [] for k in (2, 5, 10)}; allfr = {k: [] for k in (2, 5, 10)}
            docr = {k: [] for k in (2, 5, 10)}
            first_rank, doc_first_rank, density, units_all = [], [], [], []
            for sims, golddocs, dr, nf in per_q:
                hit = sims >= th
                ranks = [int(np.argmax(hit[:, i])) + 1 if hit[:, i].any() else None
                         for i in range(nf)]
                for k in fr:
                    c = sum(1 for x in ranks if x is not None and x <= k)
                    fr[k].append(c / nf); allfr[k].append(1.0 if c == nf else 0.0)
                    dc = sum(1 for d in golddocs if dr.get(d, 99) <= k)
                    docr[k].append(dc / len(golddocs))
                first_rank += [x for x in ranks if x is not None]
                doc_first_rank += list(dr.values())
                density.append(hit.sum() / hit.shape[0] if hit.shape[0] else 0.0)
                if all(x is not None for x in ranks): units_all.append(max(ranks))
            arm[str(th)] = {
                "questions": len(fr[10]),
                "fact_recall": {k: sum(v)/len(v) for k, v in fr.items()},
                "all_fact_recall": {k: sum(v)/len(v) for k, v in allfr.items()},
                "doc_recall": {k: sum(v)/len(v) for k, v in docr.items()},
                "median_first_rank_fact": st.median(first_rank) if first_rank else None,
                "median_first_rank_doc": st.median(doc_first_rank) if doc_first_rank else None,
                "facts_per_unit": sum(density)/len(density) if density else 0,
                "share_all_facts_found": len(units_all)/len(fr[10]) if fr[10] else 0,
                "median_units_for_all_facts": st.median(units_all) if units_all else None,
            }
        out[name] = arm

    thetas = [float(t) for t in a.thetas.split(",")]
    w = max(len(n) for n in out)
    print(f"sample {len(qs)} questions   k={a.k}   arms: {', '.join(out)}\n")
    for th in thetas:
        t = str(th)
        print(f"--- theta = {th} " + "-" * 46)
        print(f"{'arm':<{w}}  " + "".join(f"  Fact@{k:<3}" for k in (2, 5, 10)) +
              "".join(f"  AllFact@{k:<3}" for k in (2, 5, 10)) +
              "   facts/unit  med.rank")
        for n, r in out.items():
            d = r[t]
            print(f"{n:<{w}}  " +
                  "".join(f"   {d['fact_recall'][k]:.3f}" for k in (2, 5, 10)) +
                  "".join(f"      {d['all_fact_recall'][k]:.3f}  " for k in (2, 5, 10)) +
                  f"    {d['facts_per_unit']:.3f}      {d['median_first_rank_fact']}")
        print()

    t = str(thetas[len(thetas) // 2])
    print(f"=== document credit vs fact credit, theta={t} ===")
    print(f"{'arm':<{w}}  doc-recall@10  fact-recall@10      gap   all facts found   median units for all")
    for n, r in out.items():
        d = r[t]
        g = d["doc_recall"][10] - d["fact_recall"][10]
        print(f"{n:<{w}}       {d['doc_recall'][10]:.3f}          {d['fact_recall'][10]:.3f}   "
              f"{g:+.3f}          {d['share_all_facts_found']:6.1%}              "
              f"{d['median_units_for_all_facts']}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
