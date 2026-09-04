#!/usr/bin/env python3
"""
Add the dense half of the hybrid index to a corpus vault.

build_local_db.py builds the lexical half (FTS5) and the link graph. This adds
sentence embeddings so hybrid and graph retrieval can run. Embeddings live
beside the notes as a .npy plus an id list -- rebuildable, therefore gitignored.

    python3 scripts/build_embeddings.py vaults/musique
    python3 scripts/build_embeddings.py vaults/musique --model all-MiniLM-L6-v2

Model default matches the one used for the internal comparison so numbers are
comparable across repos: all-MiniLM-L6-v2 (384-dim). Encoding is done over the
note TITLE plus BODY, truncated per the model's window.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import re
import sys
from pathlib import Path

import numpy as np


NON_EVIDENCE = re.compile(
    r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)", re.M | re.S)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--model", default="all-MiniLM-L6-v2")
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--max-chars", type=int, default=4000)
    a = ap.parse_args()

    vault = Path(a.vault)
    db = vault / "notes.db"
    if not db.exists():
        print(f"no database at {db}; run build_local_db.py first")
        sys.exit(2)

    con = sqlite3.connect(db)
    rows = con.execute("SELECT note_id, title, body FROM notes ORDER BY note_id").fetchall()
    con.close()
    if not rows:
        print("no notes to encode")
        sys.exit(2)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("pip install sentence-transformers")
        sys.exit(2)

    print(f"encoding {len(rows)} notes with {a.model}")
    model = SentenceTransformer(a.model)
    # Scaffolding is excluded here for the same reason build_local_db excludes it
    # from the FTS: Related Notes and Source describe a note's NEIGHBOURS, so
    # embedding them pulls a note toward the topics of whatever it links to. Both
    # halves of hybrid retrieval must see the same text, or the arms disagree
    # about what the note is.
    texts = [f"{t}\n\n{NON_EVIDENCE.sub('', b)}"[: a.max_chars] for _, t, b in rows]
    emb = model.encode(texts, batch_size=a.batch, show_progress_bar=True,
                       convert_to_numpy=True, normalize_embeddings=True)

    np.save(vault / "embeddings.npy", emb.astype(np.float32))
    (vault / "embedding_ids.json").write_text(
        json.dumps({"model": a.model, "dim": int(emb.shape[1]),
                    "ids": [r[0] for r in rows]}, indent=1))
    print(f"wrote {emb.shape} -> {vault / 'embeddings.npy'}")


if __name__ == "__main__":
    main()
