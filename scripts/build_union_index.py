#!/usr/bin/env python3
"""
Build a union index over two arms: the retriever sees both representations.

This is the residual connection from ResNet, transposed. A CNN does not replace
its input with the filtered version; it carries both forward, because a filter
that is right on average is wrong somewhere and the raw signal is the only thing
that can recover those cases. A knowledge system that indexes ONLY its notes has
no such path -- whatever the summariser dropped is unreachable, which is exactly
the 18.3% fact loss measured in FZ 5h.

Indexing notes and their source spans together costs nothing at write time and
lets the ranker choose per query. If the union beats both arms, the loss was
recoverable and the note layer should never have been a replacement.

    python3 scripts/build_union_index.py --out vaults/v_union \
        --arms notes=vaults/multihop_rag chunks=data/chunks/multihop_rag
"""
from __future__ import annotations
import argparse, json, shutil, sqlite3, sys
from pathlib import Path
import numpy as np


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    dst = Path(a.out); dst.mkdir(parents=True, exist_ok=True)
    first = Path(a.arms[0].partition("=")[2])
    shutil.copy(first / "notes.db", dst / "notes.db")
    con = sqlite3.connect(dst / "notes.db")
    con.execute("DELETE FROM notes"); con.execute("DELETE FROM notes_fts")
    try:
        con.execute("DELETE FROM note_links")
    except sqlite3.OperationalError:
        pass
    con.commit()

    embs, ids, dim, model = [], [], None, None
    # the two arms' tables need not share a schema -- the chunk index carries
    # fewer columns than the note index -- so insert BY NAME and let the
    # missing ones default rather than assuming positional agreement
    target = [d[0] for d in con.execute("SELECT * FROM notes LIMIT 0").description]
    for spec in a.arms:
        name, _, vp = spec.partition("=")
        v = Path(vp)
        src = sqlite3.connect(v / "notes.db")
        cols = [d[0] for d in src.execute("SELECT * FROM notes LIMIT 0").description]
        rows = [dict(zip(cols, r)) for r in src.execute("SELECT * FROM notes")]
        src.close()
        pref = f"{name}::"
        shared = [c for c in target if c in cols]
        for r in rows:
            r["note_id"] = pref + r["note_id"]
        con.executemany(
            f"INSERT INTO notes ({','.join(shared)}) VALUES ({','.join('?' * len(shared))})",
            [tuple(r[c] for c in shared) for r in rows])
        con.executemany("INSERT INTO notes_fts VALUES (?,?,?)",
                        [(r["note_id"], r.get("title") or "",
                          f"{r.get('keywords') or ''} {r.get('topics') or ''} {r.get('body') or ''}")
                         for r in rows])

        meta = json.loads((v / "embedding_ids.json").read_text())
        E = np.load(v / "embeddings.npy")
        dim = dim or meta["dim"]; model = model or meta["model"]
        assert meta["dim"] == dim and meta["model"] == model, "arms use different encoders"
        assert len(meta["ids"]) == E.shape[0], f"{name}: id/embedding mismatch"
        embs.append(E); ids += [pref + x for x in meta["ids"]]
        print(f"  {name}: {len(rows):,} units, {len(shared)}/{len(target)} columns carried")

    con.commit()
    U = np.vstack(embs)
    assert U.shape[0] == len(ids)
    np.save(dst / "embeddings.npy", U)
    (dst / "embedding_ids.json").write_text(
        json.dumps({"model": model, "dim": dim, "ids": ids}))
    n = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    con.close()
    print(f"union {dst}: {n:,} units, embeddings {U.shape}")


if __name__ == "__main__":
    main()
