#!/usr/bin/env python3
"""
Build a self-contained note database for one benchmark vault.

This repo does not depend on any private vault. Each corpus gets its OWN
SQLite database, its OWN link graph and its OWN full-text index, living beside
the notes under vaults/<corpus>/. Nothing here reads or writes anything
outside this repository.

That isolation is not tidiness -- it is the correctness condition. A digestion
pipeline resolves "Related Notes" and inlinks against whatever vault it runs
in, so a corpus ingested against some other vault would carry that vault's
links outward and contaminate both the notes and the evaluation.

    python3 scripts/build_local_db.py vaults/musique
    python3 scripts/build_local_db.py vaults/musique --stats

Schema (deliberately minimal -- only what retrieval and scoring need):
    notes(note_id, title, building_block, body, words, source_doc)
               source_doc comes from the note's own `source_docs:` frontmatter
    note_links(source_note_id, target_note_id, resolved)
    notes_fts  -- FTS5 over title + body
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^# (.+)$", re.M)
LINK = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)\)")

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS notes (
    note_id        TEXT PRIMARY KEY,
    title          TEXT,
    building_block TEXT,
    body           TEXT,
    words          INTEGER,
    source_doc     TEXT
);
CREATE TABLE IF NOT EXISTS note_links (
    source_note_id TEXT NOT NULL,
    target_note_id TEXT NOT NULL,
    resolved       INTEGER NOT NULL DEFAULT 0,
    UNIQUE(source_note_id, target_note_id)
);
CREATE INDEX IF NOT EXISTS idx_links_src ON note_links(source_note_id);
CREATE INDEX IF NOT EXISTS idx_links_tgt ON note_links(target_note_id);
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
    USING fts5(note_id UNINDEXED, title, body, tokenize='porter unicode61');
"""


def parse_frontmatter(text: str) -> dict:
    m = FM.match(text)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def build(vault: Path, provenance: dict[str, str]) -> sqlite3.Connection:
    db_path = vault / "notes.db"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript(DDL)

    notes = sorted(p for p in vault.rglob("*.md") if p.name != "README.md")
    ids = set()
    for p in notes:
        nid = str(p.relative_to(vault))
        ids.add(nid)
        raw = p.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(raw)
        body = FM.sub("", raw)
        h1 = H1.search(body)
        # provenance: frontmatter source_docs is authoritative; provenance.json is a fallback
        src = fm.get("source_docs", "").strip("[] ").replace('"', "").replace("'", "")
        con.execute(
            "INSERT OR REPLACE INTO notes VALUES (?,?,?,?,?,?)",
            (nid, h1.group(1) if h1 else p.stem, fm.get("building_block", ""),
             body, len(body.split()), src or provenance.get(nid, "")),
        )
        con.execute("INSERT INTO notes_fts VALUES (?,?,?)",
                    (nid, h1.group(1) if h1 else p.stem, body))

    # links, resolved against THIS vault only
    for p in notes:
        nid = str(p.relative_to(vault))
        body = FM.sub("", p.read_text(encoding="utf-8", errors="replace"))
        for _, target in LINK.findall(body):
            if target.startswith(("http://", "https://")):
                continue
            resolved_path = (p.parent / target).resolve()
            try:
                tid = str(resolved_path.relative_to(vault.resolve()))
            except ValueError:
                # link escapes this vault -- record unresolved, never follow it
                con.execute(
                    "INSERT OR IGNORE INTO note_links VALUES (?,?,0)", (nid, target))
                continue
            con.execute("INSERT OR IGNORE INTO note_links VALUES (?,?,?)",
                        (nid, tid, 1 if tid in ids else 0))
    con.commit()
    return con


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    vault = Path(a.vault)
    if not vault.is_dir():
        print(f"no such vault: {vault}")
        sys.exit(2)

    prov_file = vault / "provenance.json"
    prov = {}
    if prov_file.exists():
        raw = json.loads(prov_file.read_text())
        for doc, notes in raw.get("doc_to_notes", {}).items():
            for n in notes:
                prov[n] = doc

    con = build(vault, prov)
    n = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    tot = con.execute("SELECT COUNT(*) FROM note_links").fetchone()[0]
    res = con.execute("SELECT COUNT(*) FROM note_links WHERE resolved=1").fetchone()[0]
    esc = tot - res
    print(f"vault      {vault}")
    print(f"database   {vault / 'notes.db'}")
    print(f"notes      {n}")
    print(f"links      {tot}  ({res} resolved in-vault, {esc} unresolved/external)")
    if esc:
        print(f"  WARNING: {esc} link(s) do not resolve inside this vault.")
        print("  Any link pointing outside is a contamination signal -- inspect before use.")
    if a.stats and n:
        print("\nbuilding blocks:")
        for bb, c in con.execute(
                "SELECT building_block, COUNT(*) FROM notes GROUP BY 1 ORDER BY 2 DESC"):
            print(f"  {c:6d}  {bb or '(unset)'}")
        w = con.execute("SELECT AVG(words), MIN(words), MAX(words) FROM notes").fetchone()
        print(f"\nwords: mean {w[0]:.0f}  min {w[1]}  max {w[2]}")
        orphan = con.execute(
            "SELECT COUNT(*) FROM notes WHERE note_id NOT IN "
            "(SELECT target_note_id FROM note_links WHERE resolved=1)").fetchone()[0]
        print(f"orphans (no inbound resolved link): {orphan}")
    con.close()


if __name__ == "__main__":
    main()
