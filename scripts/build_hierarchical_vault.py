#!/usr/bin/env python3
"""
Small-to-big: index the atoms, return the parent.

Two published patterns bear on the v2 pilot, and it implemented neither.

  Dense X Retrieval indexes AND reads propositions, capped at a word budget --
  they win on "higher density of question-relevant information" per token. That
  regime is a TOKEN budget. The v2 pilot nearly tied there (-0.010, interval
  spanning zero) and lost heavily at matched SLOTS, which is the regime where
  density buys nothing and coverage per unit is everything.

  Auto-merging retrieval indexes small leaves and returns the PARENT when
  enough leaves point at it, to "consolidate potentially disparate, smaller
  contexts into a larger context".

This builds the second: the atom supplies the matching text, the parent supplies
the returned body. Precision of a small unit, coherence of a large one.

    python3 scripts/build_hierarchical_vault.py --atoms vaults/v2_pilot \
        --parents vaults/v1_slice --out vaults/v_hier
"""
from __future__ import annotations
import argparse, json, re, shutil, sqlite3
from collections import defaultdict
from pathlib import Path
import numpy as np

NON = re.compile(r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)", re.M | re.S)


def load(v: Path):
    con = sqlite3.connect(v / "notes.db")
    rows = con.execute("SELECT note_id, title, body, source_doc FROM notes").fetchall()
    con.close()
    E = np.load(v / "embeddings.npy")
    ids = json.loads((v / "embedding_ids.json").read_text())["ids"]
    return rows, {n: E[i] for i, n in enumerate(ids)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atoms", required=True)
    ap.add_argument("--parents", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    A, Ae = load(Path(a.atoms))
    P, Pe = load(Path(a.parents))
    pdoc = defaultdict(list)
    for nid, _t, _b, src in P:
        for d in {x.strip() for x in (src or "").split(",") if x.strip()}:
            pdoc[d].append(nid)

    # each atom is assigned to the parent it is most similar to, within the
    # document it came from -- provenance bounds the candidates, similarity picks
    assigned = defaultdict(list)
    orphan = 0
    for nid, _t, body, src in A:
        docs = {x.strip() for x in (src or "").split(",") if x.strip()}
        cands = [p for d in docs for p in pdoc.get(d, [])]
        if not cands or nid not in Ae:
            orphan += 1
            continue
        v = Ae[nid]
        best = max(cands, key=lambda p: float(Pe[p] @ v) if p in Pe else -1)
        assigned[best].append(NON.sub("", body).strip())

    dst = Path(a.out); dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(a.parents) / "notes.db", dst / "notes.db")
    con = sqlite3.connect(dst / "notes.db")
    con.execute("DELETE FROM notes_fts")

    texts, ids, matched = [], [], 0
    for nid, title, body, _src in P:
        atoms = assigned.get(nid, [])
        matched += bool(atoms)
        # the ATOMS are the matching surface; the PARENT body is what a reader gets
        match_text = "\n".join(atoms) if atoms else NON.sub("", body)
        con.execute("INSERT INTO notes_fts VALUES (?,?,?)", (nid, title, match_text))
        ids.append(nid); texts.append(match_text)
    con.commit(); con.close()

    from sentence_transformers import SentenceTransformer
    meta = json.loads((Path(a.parents) / "embedding_ids.json").read_text())
    m = SentenceTransformer(meta["model"])
    E = m.encode(texts, normalize_embeddings=True, batch_size=128, show_progress_bar=False)
    np.save(dst / "embeddings.npy", E.astype(np.float32))
    (dst / "embedding_ids.json").write_text(
        json.dumps({"model": meta["model"], "dim": int(E.shape[1]), "ids": ids}))
    print(f"{dst}: {len(P)} parents, {len(A)-orphan} atoms assigned "
          f"({orphan} orphaned), {matched} parents carry atom text")
    print(f"  mean atoms per parent: {sum(len(v) for v in assigned.values())/max(matched,1):.1f}")


if __name__ == "__main__":
    main()
