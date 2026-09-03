#!/usr/bin/env python3
"""
Build the whole-document arm: each source document is one retrieval unit.

This is the baseline the first experiment omitted, and its absence made that
experiment's framing wrong. Chunking is NOT the raw alternative -- it is itself
a lossy size-reduction step that discards document structure and keeps arbitrary
spans. Comparing notes only against chunks tests summarisation against
segmentation and never against doing nothing at all.

    python3 scripts/build_wholedoc_baseline.py multihop_rag

The arithmetic is why this matters: a 2,048-token window holds 0.3 whole
documents, 3.2 notes, or 14.2 chunks. If notes cannot beat whole documents at
matched budget, the derived layer is not earning its construction cost against
the simplest possible baseline, and no amount of tuning against chunks repairs
that.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
OUT = ROOT / "data" / "wholedoc"

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS notes (
    note_id TEXT PRIMARY KEY, note_name TEXT, title TEXT, building_block TEXT,
    body TEXT, words INTEGER, source_doc TEXT);
CREATE TABLE IF NOT EXISTS note_links (
    source_note_id TEXT NOT NULL, target_note_id TEXT NOT NULL,
    link_text TEXT, resolved INTEGER NOT NULL DEFAULT 0,
    UNIQUE(source_note_id, target_note_id));
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
    USING fts5(note_id UNINDEXED, title, body, tokenize='porter unicode61');
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    a = ap.parse_args()

    cdir = CORPUS / a.slug
    if not (cdir / "index.json").exists():
        print(f"no corpus at {cdir} — run prepare_corpus.py first")
        sys.exit(2)
    index = json.loads((cdir / "index.json").read_text())

    out = OUT / a.slug
    out.mkdir(parents=True, exist_ok=True)
    db = out / "notes.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript(DDL)

    for doc, meta in index.items():
        text = (cdir / f"{doc}.txt").read_text(encoding="utf-8")
        con.execute("INSERT INTO notes VALUES (?,?,?,?,?,?,?)",
                    (doc, doc, meta["title"], "document", text,
                     len(text.split()), doc))
        con.execute("INSERT INTO notes_fts VALUES (?,?,?)",
                    (doc, meta["title"], text))
    con.commit()
    con.close()
    print(f"corpus   {a.slug}")
    print(f"units    {len(index)} whole documents")
    print(f"index    {db.relative_to(ROOT)}")
    print("\nNo links: whole documents carry no graph, so bfs and ppr fall back to "
          "their seeding here. That is the honest baseline, not a handicap to fix.")


if __name__ == "__main__":
    main()
