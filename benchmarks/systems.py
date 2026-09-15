"""Small, committed retrieval systems used by calibration runs."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from benchmarks.adapters.base import Document


class PooledBm25System:
    """A deterministic lexical baseline over an adapter's pooled documents.

    The calibration protocol scores passage ids directly, so each result covers
    exactly its own passage id. The SQLite database is a rebuildable temporary
    artifact; only the implementation and run manifest are part of provenance.
    """

    system_id = "bm25-pooled-passages-clean"

    def __init__(self, db_path: Path = Path("/tmp/2wiki-bm25-clean.db")) -> None:
        self.db_path = Path(db_path)
        self._words: dict[str, int] = {}

    def arm_config(self) -> Mapping[str, object]:
        return {
            "scorer": "bm25",
            "k1": 1.2,
            "b": 0.75,
            "unit": "pooled_passage",
            "protocol": "hipporag_pooled_corpus",
        }

    def ingest(self, corpus: Iterable[Document]) -> None:
        if self.db_path.exists():
            self.db_path.unlink()
        con = sqlite3.connect(self.db_path)
        con.execute(
            "CREATE VIRTUAL TABLE passages USING fts5(" 
            "doc_id UNINDEXED, body, tokenize='porter unicode61')"
        )
        for document in corpus:
            self._words[document.doc_id] = len(document.text.split())
            con.execute(
                "INSERT INTO passages VALUES (?, ?)",
                (document.doc_id, document.text),
            )
        con.commit()
        con.close()

    def retrieve(self, query: str, k: int) -> Sequence[tuple[str, set[str]]]:
        terms = [term for term in re.findall(r"[A-Za-z0-9]+", query) if len(term) > 2]
        if not terms:
            return []
        con = sqlite3.connect(self.db_path)
        rows = con.execute(
            "SELECT doc_id FROM passages WHERE passages MATCH ? "
            "ORDER BY bm25(passages) LIMIT ?",
            (" OR ".join(terms), k),
        ).fetchall()
        con.close()
        return [(doc_id, {doc_id}) for (doc_id,) in rows]

    def unit_words(self) -> Mapping[str, int]:
        return self._words
