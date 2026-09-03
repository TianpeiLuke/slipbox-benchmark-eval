#!/usr/bin/env python3
"""
Do the gold facts survive into the derived layer at all, and how densely?

This is the representation question, separated from the retrieval question. A
fact from document D must live in one of D's units or no retriever can find it,
so each fact is searched only against units derived from its own document --
cheap, and exactly the right denominator.

Two numbers matter:

  RETENTION  share of gold facts present in at least one unit from their
             document. Chunks are extracts, so theirs is a sanity ceiling near
             1.0; notes are rewrites, so theirs is the real question -- a fact
             a summary dropped is unreachable no matter how good retrieval is.

  DENSITY    among units carrying at least one fact, how many they carry. This
             is the "a summary gets you there faster" claim stated as a property
             of the corpus rather than of a ranking.

    python3 scripts/fact_retention.py multihop_rag \
        --arms notes=vaults/multihop_rag chunks=data/chunks/multihop_rag
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SENT = re.compile(r"(?<=[.!?])\s+")
NON_EVIDENCE = re.compile(r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)", re.M | re.S)


def sentences(text: str) -> list[str]:
    text = NON_EVIDENCE.sub("", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.M)
    return [s.strip() for s in SENT.split(text) if len(s.strip().split()) >= 4]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--arms", nargs="+", required=True)
    ap.add_argument("--thetas", default="0.55,0.65,0.75")
    ap.add_argument("--json")
    a = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    idx = json.loads((ROOT / "data/corpus" / a.slug / "index.json").read_text())
    by_title = {v["title"]: d for d, v in idx.items()}
    raw = json.loads((ROOT / "data/raw" / a.slug / "MultiHopRAG.json").read_text())

    facts: dict[str, set[str]] = defaultdict(set)     # doc -> distinct fact sentences
    for q in raw:
        for e in q.get("evidence_list", []):
            d = by_title.get(e.get("title", ""))
            if d and e.get("fact"):
                facts[d].add(e["fact"].strip())
    total = sum(len(v) for v in facts.values())
    print(f"{total:,} distinct gold facts across {len(facts):,} documents\n")

    thetas = [float(t) for t in a.thetas.split(",")]
    out = {}
    for spec in a.arms:
        name, _, vp = spec.partition("=")
        con = sqlite3.connect(Path(vp) / "notes.db")
        by_doc: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for nid, src, b in con.execute("SELECT note_id, source_doc, body FROM notes"):
            for d in {x.strip() for x in (src or "").split(",") if x.strip()}:
                by_doc[d].append((nid, b))
        con.close()

        # Encode every unit's sentences ONCE in a single batch. Encoding per
        # (document, unit) pair re-encoded shared units and issued ~20k tiny
        # calls, which is what killed the first attempt.
        nids, offs, allsents = [], [], []
        for nid, b in {n: b for d in by_doc for n, b in by_doc[d]}.items():
            ss = sentences(b)
            if not ss:
                continue
            nids.append(nid); offs.append((len(allsents), len(allsents) + len(ss)))
            allsents += ss
        print(f"  {name}: encoding {len(allsents):,} sentences from {len(nids):,} units")
        S = model.encode(allsents, normalize_embeddings=True, batch_size=256,
                         show_progress_bar=False)
        span = {n: offs[i] for i, n in enumerate(nids)}

        fl_all = sorted({f for fs in facts.values() for f in fs})
        F = model.encode(fl_all, normalize_embeddings=True, batch_size=256,
                         show_progress_bar=False)
        frow = {f: i for i, f in enumerate(fl_all)}

        best: dict[tuple[str, str], dict[str, float]] = {}
        for d, fs in facts.items():
            units = by_doc.get(d, [])
            if not units:
                continue
            fi = [frow[f] for f in sorted(fs)]
            fe = F[fi]
            for nid, _ in units:
                if nid not in span:
                    continue
                lo, hi = span[nid]
                sims = (S[lo:hi] @ fe.T).max(axis=0)
                for j, f in enumerate(sorted(fs)):
                    best.setdefault((d, f), {})[nid] = float(sims[j])

        arm = {}
        for th in thetas:
            kept = {k: [n for n, s in v.items() if s >= th] for k, v in best.items()}
            retained = sum(1 for v in kept.values() if v)
            per_unit: dict[str, int] = defaultdict(int)
            for v in kept.values():
                for n in v:
                    per_unit[n] += 1
            dens = list(per_unit.values())
            arm[str(th)] = {
                "retention": retained / len(best) if best else 0,
                "facts_covered": retained,
                "units_carrying_a_fact": len(per_unit),
                "mean_facts_per_carrying_unit": (sum(dens) / len(dens)) if dens else 0,
                "share_units_with_2plus": (sum(1 for x in dens if x >= 2) / len(dens)) if dens else 0,
            }
        out[name] = arm

    w = max(len(n) for n in out)
    for th in thetas:
        t = str(th)
        print(f"--- theta = {th} " + "-" * 40)
        print(f"{'arm':<{w}}  retention  units w/ a fact  facts per carrying unit  units w/ 2+ facts")
        for n, r in out.items():
            d = r[t]
            print(f"{n:<{w}}    {d['retention']:6.1%}         {d['units_carrying_a_fact']:6,}"
                  f"              {d['mean_facts_per_carrying_unit']:5.2f}             {d['share_units_with_2plus']:6.1%}")
        print()
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
