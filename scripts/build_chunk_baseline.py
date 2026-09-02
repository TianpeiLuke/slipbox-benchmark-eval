#!/usr/bin/env python3
"""
Build the chunk-RAG baseline arm: fixed-size passages over the raw documents.

This is the arm the slipbox notes are compared against, so it has to be a fair
opponent rather than a strawman. It uses the SAME database schema, the SAME
retrieval code and the SAME scorer as the notes arm; the only difference is what
a retrieval unit is -- a fixed window of the source text instead of a written
note. Chunks carry no links, so graph strategies degenerate to their lexical
seed on this arm, which is the honest result and not a bug to paper over.

    python3 scripts/build_chunk_baseline.py multihop_rag
    python3 scripts/build_chunk_baseline.py multihop_rag --words 200 --overlap 50

Defaults follow common RAG practice (~200 words, 25% overlap). Chunk size is a
free parameter that materially moves the baseline, so --sweep reports several
sizes and the scorer should be run against more than one before any comparison
is called.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
OUT = ROOT / "data" / "chunks"

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS notes (
    note_id        TEXT PRIMARY KEY,
    note_name      TEXT,
    title          TEXT,
    building_block TEXT,
    body           TEXT,
    words          INTEGER,
    source_doc     TEXT
);
CREATE TABLE IF NOT EXISTS note_links (
    source_note_id TEXT NOT NULL,
    target_note_id TEXT NOT NULL,
    link_text      TEXT,
    resolved       INTEGER NOT NULL DEFAULT 0,
    UNIQUE(source_note_id, target_note_id)
);
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
    USING fts5(note_id UNINDEXED, title, body, tokenize='porter unicode61');
"""


def chunk(text: str, size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []
    step = max(1, size - overlap)
    return [" ".join(words[i:i + size]) for i in range(0, len(words), step)
            if words[i:i + size]]


def build(slug: str, size: int, overlap: int) -> tuple[int, int]:
    cdir = CORPUS / slug
    if not (cdir / "index.json").exists():
        print(f"no corpus at {cdir} — run: python3 scripts/prepare_corpus.py {slug}")
        sys.exit(2)
    index = json.loads((cdir / "index.json").read_text())

    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    db = out / "notes.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript(DDL)

    n = 0
    for doc_id, meta in index.items():
        text = (cdir / f"{doc_id}.txt").read_text(encoding="utf-8")
        for j, piece in enumerate(chunk(text, size, overlap)):
            cid = f"{doc_id}#{j:03d}"
            # The document title is carried on every chunk. Dropping it would
            # handicap the baseline on exactly the entity terms these questions
            # turn on, and the comparison has to be against a fair opponent.
            con.execute("INSERT INTO notes VALUES (?,?,?,?,?,?,?)",
                        (cid, cid, meta["title"], "chunk", piece,
                         len(piece.split()), doc_id))
            con.execute("INSERT INTO notes_fts VALUES (?,?,?)",
                        (cid, meta["title"], piece))
            n += 1
    con.commit()
    con.close()
    return len(index), n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--words", type=int, default=200)
    ap.add_argument("--overlap", type=int, default=50)
    ap.add_argument("--sweep", action="store_true",
                    help="report chunk counts across common sizes and exit")
    a = ap.parse_args()

    if a.sweep:
        index = json.loads((CORPUS / a.slug / "index.json").read_text())
        total = sum(v["words"] for v in index.values())
        print(f"{'size':>6} {'overlap':>8} {'chunks':>9}")
        for size in (100, 200, 400, 800):
            ov = size // 4
            print(f"{size:>6} {ov:>8} {int(total / max(1, size - ov)):>9,}")
        return

    docs, n = build(a.slug, a.words, a.overlap)
    print(f"corpus   {a.slug}")
    print(f"docs     {docs}")
    print(f"chunks   {n:,}  ({a.words} words, {a.overlap} overlap)")
    print(f"index    {(OUT / a.slug / 'notes.db').relative_to(ROOT)}")
    print("\nChunks carry no links: bfs and ppr fall back to their lexical seed here.")


if __name__ == "__main__":
    main()
