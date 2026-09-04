#!/usr/bin/env python3
"""
Prefix every chunk with its article's title and date, then re-index.

FZ 8c5b11a13a5g1b5i3a proposed this as the falsifier for the note layer's slot
advantage: if self-sufficiency is what earns it, and self-sufficiency can be
bought on a chunk for a hundred tokens of title and date, then the advantage is
obtainable without writing notes at all.

It is the cheap mechanical form of what Anthropic call Contextual Retrieval,
which generates the prefix with a model. Doing it mechanically keeps the test
honest -- no LLM is involved, so nothing about the result can be attributed to a
second model's judgement.

    python3 scripts/build_contextualised_chunks.py --out data/chunks/ctx_multihop_rag
"""
from __future__ import annotations
import argparse, json, shutil, sqlite3, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="data/chunks/multihop_rag")
    ap.add_argument("--slug", default="multihop_rag")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    idx = json.loads((ROOT / "data/corpus" / a.slug / "index.json").read_text())
    src, dst = Path(a.src), Path(a.out)
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(src / "notes.db", dst / "notes.db")
    con = sqlite3.connect(dst / "notes.db")

    rows = con.execute("SELECT note_id, source_doc, body FROM notes").fetchall()
    n_ctx = 0
    for nid, doc, body in rows:
        meta = idx.get((doc or "").strip())
        if not meta:
            continue
        title = meta.get("title", "").strip()
        date = (meta.get("date") or meta.get("published_at") or "")[:10]
        pub = meta.get("publisher") or meta.get("source") or ""
        # the prefix a reader needs to interpret a window cut by offset: what
        # this is about, who reported it, and when
        prefix = f"{title}. {pub}, {date}.".strip()
        con.execute("UPDATE notes SET body=? WHERE note_id=?", (f"{prefix}\n\n{body}", nid))
        n_ctx += 1
    con.commit()

    # the chunk table carries fewer columns than the note table, so select by
    # name presence rather than assuming a shared schema
    cols = {d[0] for d in con.execute("SELECT * FROM notes LIMIT 0").description}
    extra = " || ' ' || ".join(f"COALESCE({c},'')" for c in ("keywords", "topics")
                               if c in cols)
    sel = f"SELECT note_id, title, {extra + ' || \' \' || ' if extra else ''}body FROM notes"
    con.execute("DELETE FROM notes_fts")
    for nid, title, text in con.execute(sel):
        con.execute("INSERT INTO notes_fts VALUES (?,?,?)", (nid, title, text))
    con.commit()
    bodies = con.execute("SELECT note_id, body FROM notes").fetchall()
    con.close()

    # bodies changed, so embeddings must be recomputed -- reusing the old ones
    # would measure the prefix on the lexical side only and silently understate it
    from sentence_transformers import SentenceTransformer
    meta_old = json.loads((src / "embedding_ids.json").read_text())
    model = SentenceTransformer(meta_old["model"])
    ids = [n for n, _ in bodies]
    E = model.encode([b for _, b in bodies], normalize_embeddings=True,
                     batch_size=128, show_progress_bar=False)
    np.save(dst / "embeddings.npy", E.astype(np.float32))
    (dst / "embedding_ids.json").write_text(
        json.dumps({"model": meta_old["model"], "dim": int(E.shape[1]), "ids": ids}))
    print(f"contextualised {n_ctx:,} of {len(rows):,} chunks -> {dst}")
    print(f"embeddings recomputed {E.shape}")


if __name__ == "__main__":
    main()
