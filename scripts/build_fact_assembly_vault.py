#!/usr/bin/env python3
"""
Reassemble scattered evidence by linking atoms that came from the same place.

Splitting a document into thought-atomic notes measurably DESTROYS evidence:
facts carried per unit fell from 0.321 to 0.254 in the pilot, because a gold
evidence sentence and the context that makes it interpretable end up in
different notes. The atom is smaller than the fact.

The repair is a graph, but not the kind FZ 5f found harmful. Those edges were
topical and were traversed at MATCH time, pulling in whatever was associated.
These edges are provenance-bounded and used at ASSEMBLY time: after an atom
matches, its co-derived siblings are appended to restore what splitting broke.
The graph is not finding new material -- it is putting back material that was
one unit before the pipeline divided it.

Two atoms are siblings when they come from the same source document AND are
mutually similar enough to be about the same stretch of it. Provenance bounds
the candidates; similarity picks the adjacent ones.

    python3 scripts/build_fact_assembly_vault.py --atoms vaults/v2_pilot \
        --out vaults/v_assembled --siblings 2 --min-sim 0.35
"""
from __future__ import annotations
import argparse, json, re, shutil, sqlite3
from collections import defaultdict
from pathlib import Path
import numpy as np

NON = re.compile(r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)", re.M | re.S)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atoms", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--siblings", type=int, default=2,
                    help="how many co-derived neighbours to append")
    ap.add_argument("--min-sim", type=float, default=0.35,
                    help="similarity floor; below it two atoms are not about the "
                         "same stretch of source and appending one is padding")
    a = ap.parse_args()

    src = Path(a.atoms); dst = Path(a.out); dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(src / "notes.db", dst / "notes.db")
    con = sqlite3.connect(dst / "notes.db")
    rows = con.execute("SELECT note_id, title, body, source_doc FROM notes").fetchall()
    E = np.load(src / "embeddings.npy")
    ids = json.loads((src / "embedding_ids.json").read_text())["ids"]
    pos = {n: i for i, n in enumerate(ids)}

    bydoc = defaultdict(list)
    for nid, _t, _b, s in rows:
        for d in {x.strip() for x in (s or "").split(",") if x.strip()}:
            bydoc[d].append(nid)
    body = {nid: NON.sub("", b).strip() for nid, _t, b, _s in rows}

    con.execute("DELETE FROM notes_fts")
    texts, out_ids, linked, total_sibs = [], [], 0, 0
    for nid, title, b, s in rows:
        docs = {x.strip() for x in (s or "").split(",") if x.strip()}
        cands = [c for d in docs for c in bydoc[d] if c != nid and c in pos]
        sibs = []
        if nid in pos and cands:
            v = E[pos[nid]]
            scored = sorted(((float(E[pos[c]] @ v), c) for c in cands), reverse=True)
            sibs = [c for sim, c in scored[: a.siblings] if sim >= a.min_sim]
        if sibs:
            linked += 1; total_sibs += len(sibs)
        text = "\n\n".join([body[nid]] + [body[c] for c in sibs])
        con.execute("INSERT INTO notes_fts VALUES (?,?,?)", (nid, title, text))
        out_ids.append(nid); texts.append(text)
    con.commit(); con.close()

    from sentence_transformers import SentenceTransformer
    meta = json.loads((src / "embedding_ids.json").read_text())
    m = SentenceTransformer(meta["model"])
    Enew = m.encode(texts, normalize_embeddings=True, batch_size=128, show_progress_bar=False)
    np.save(dst / "embeddings.npy", Enew.astype(np.float32))
    (dst / "embedding_ids.json").write_text(
        json.dumps({"model": meta["model"], "dim": int(Enew.shape[1]), "ids": out_ids}))
    import statistics as st
    w = [len(t.split()) for t in texts]
    print(f"{dst}: {len(rows)} atoms, {linked} got siblings "
          f"({total_sibs/max(linked,1):.1f} each), {len(rows)-linked} stood alone")
    print(f"  unit words: median {st.median(w):.0f}  mean {st.mean(w):.0f}   "
          f"(v2 atom 108, v1 note 239)")


if __name__ == "__main__":
    main()
