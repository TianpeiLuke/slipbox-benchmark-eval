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
    python3 scripts/build_local_db.py vaults/musique --with-embeddings   # lexical + dense

The index has three parts and they must be built from the SAME notes: FTS5 and
the link graph in notes.db, and the dense vectors beside it. --with-embeddings
builds all three in one pass so they cannot drift -- a dense index built from an
earlier vault silently answers with notes that no longer exist, and nothing
downstream reports it.

Vectors stay in a .npy rather than a BLOB column on purpose: dense search reads
every vector for every query, which a memory-mapped array does in one operation
and a per-row SQLite scan does not. They live in the same directory, are
gitignored together, and are rebuilt together.

Schema (deliberately minimal -- only what retrieval and scoring need):
    notes(note_id, note_name, title, building_block, body, words, source_doc)
               source_doc comes from the note's own `source_docs:` frontmatter
    note_links(source_note_id, target_note_id, link_text, resolved)
    broken_links / ghost_notes / ghost_note_references  -- link-repair diagnostics
    notes_fts  -- FTS5 over title + body
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
from difflib import SequenceMatcher
import sys
from pathlib import Path

FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^# (.+)$", re.M)
LINK = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)\)")

DDL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS notes (
    note_id        TEXT PRIMARY KEY,
    note_name      TEXT,          -- filename stem; what humans and skills call the note
    title          TEXT,
    building_block TEXT,
    body           TEXT,
    words          INTEGER,
    source_doc     TEXT
);
CREATE TABLE IF NOT EXISTS note_links (
    source_note_id TEXT NOT NULL,
    target_note_id TEXT NOT NULL,
    link_text      TEXT,          -- anchor text; how the source note NAMES the target
    resolved       INTEGER NOT NULL DEFAULT 0,
    UNIQUE(source_note_id, target_note_id)
);
CREATE INDEX IF NOT EXISTS idx_links_src ON note_links(source_note_id);
CREATE INDEX IF NOT EXISTS idx_links_tgt ON note_links(target_note_id);
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
    USING fts5(note_id UNINDEXED, title, body, tokenize='porter unicode61');

-- Link-repair diagnostics. The gate skills query these directly; they are
-- materialised at build time because ranking candidates needs a string-
-- similarity function SQLite does not provide.
--
-- A link whose target is missing is BROKEN if some existing note is a
-- plausible intended target, and a GHOST if nothing in the vault resembles it.
-- The distinction is what separates "fix the path" from "write the note or
-- drop the reference".
CREATE TABLE IF NOT EXISTS broken_links (
    source_note_id  TEXT NOT NULL,
    broken_path     TEXT NOT NULL,
    correct_note_id TEXT NOT NULL,
    link_text       TEXT,
    similarity      REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS ghost_notes (
    ghost_note_id   TEXT PRIMARY KEY,
    reference_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS ghost_note_references (
    ghost_note_id  TEXT NOT NULL,
    source_note_id TEXT NOT NULL,
    UNIQUE(ghost_note_id, source_note_id)
);
CREATE INDEX IF NOT EXISTS idx_broken_src ON broken_links(source_note_id);
"""

SIM_FLOOR = 0.75   # below this a candidate is noise, not a suggestion


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
            "INSERT OR REPLACE INTO notes VALUES (?,?,?,?,?,?,?)",
            (nid, p.stem, h1.group(1) if h1 else p.stem, fm.get("building_block", ""),
             body, len(body.split()), src or provenance.get(nid, "")),
        )
        con.execute("INSERT INTO notes_fts VALUES (?,?,?)",
                    (nid, h1.group(1) if h1 else p.stem, body))

    # links, resolved against THIS vault only
    for p in notes:
        nid = str(p.relative_to(vault))
        body = FM.sub("", p.read_text(encoding="utf-8", errors="replace"))
        for text_, target in LINK.findall(body):
            if target.startswith(("http://", "https://")):
                continue
            resolved_path = (p.parent / target).resolve()
            try:
                tid = str(resolved_path.relative_to(vault.resolve()))
            except ValueError:
                # link escapes this vault -- record unresolved, never follow it
                con.execute("INSERT OR IGNORE INTO note_links VALUES (?,?,?,0)",
                            (nid, target, text_))
                continue
            con.execute("INSERT OR IGNORE INTO note_links VALUES (?,?,?,?)",
                        (nid, tid, text_, 1 if tid in ids else 0))
    # ---- link-repair diagnostics -------------------------------------------
    # Candidates come from an exact basename match first (a moved note), then
    # from stem similarity. Filename similarity ALONE is not evidence: short
    # names one character apart are routinely distinct concepts, so these rows
    # are a first pass for a human or agent to confirm, never a decision.
    by_name: dict[str, list[str]] = {}
    for nid in ids:
        by_name.setdefault(Path(nid).name.lower(), []).append(nid)

    ghosts: dict[str, set[str]] = {}
    for src, tgt, ltext, resolved in con.execute(
            "SELECT source_note_id, target_note_id, link_text, resolved "
            "FROM note_links").fetchall():
        if resolved:
            continue
        base = Path(tgt).name.lower()
        cands = [(c, 1.0) for c in by_name.get(base, [])]
        if not cands:
            stem = Path(tgt).stem.lower()
            cands = [(nid, r) for nid in ids
                     if (r := SequenceMatcher(None, stem, Path(nid).stem.lower()).ratio())
                     >= SIM_FLOOR]
        if cands:
            for nid, r in sorted(cands, key=lambda x: -x[1])[:5]:
                con.execute("INSERT INTO broken_links VALUES (?,?,?,?,?)",
                            (src, tgt, nid, ltext, r))
        else:
            ghosts.setdefault(tgt, set()).add(src)

    for ghost, srcs in ghosts.items():
        con.execute("INSERT OR REPLACE INTO ghost_notes VALUES (?,?)", (ghost, len(srcs)))
        for src in srcs:
            con.execute("INSERT OR IGNORE INTO ghost_note_references VALUES (?,?)",
                        (ghost, src))

    con.commit()
    return con


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--with-embeddings", action="store_true",
                    help="also build the dense half, from the same notes, in one pass")
    ap.add_argument("--model", default="all-MiniLM-L6-v2")
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
        bl = con.execute("SELECT COUNT(DISTINCT source_note_id || broken_path) "
                         "FROM broken_links").fetchone()[0]
        gh = con.execute("SELECT COUNT(*) FROM ghost_notes").fetchone()[0]
        print(f"broken links (repair candidate exists): {bl}")
        print(f"ghost targets (nothing resembles them): {gh}")
    con.close()

    if a.with_embeddings:
        print()
        rc = subprocess.call([sys.executable,
                              str(Path(__file__).parent / "build_embeddings.py"),
                              str(vault), "--model", a.model])
        if rc != 0:
            print("dense index FAILED — notes.db is built, but hybrid, dense, bfs and "
                  "ppr cannot run until it succeeds.")
            sys.exit(rc)
        ids = json.loads((vault / "embedding_ids.json").read_text())["ids"]
        db_ids = {r[0] for r in sqlite3.connect(vault / "notes.db")
                  .execute("SELECT note_id FROM notes")}
        drift = set(ids) ^ db_ids
        if drift:
            print(f"\nMISMATCH: {len(drift)} note(s) differ between the dense index and "
                  f"notes.db. The two halves of the index disagree about what the vault "
                  f"contains; retrieval would answer with notes the database does not have.")
            sys.exit(1)
        print(f"\nindex complete: {len(db_ids)} notes in both halves, ids identical")


if __name__ == "__main__":
    main()
