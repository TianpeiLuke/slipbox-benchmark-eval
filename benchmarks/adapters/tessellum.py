"""Run the current Tessellum lexical retrieval path as a benchmark arm.

This adapter deliberately treats a prepared Tessellum vault as the system under
test. It never opens the benchmark question file: ``ingest`` builds an index from
the supplied vault only, and ``retrieve`` calls Tessellum's public ``bm25_search``
entrypoint. Source-document coverage is read from each note's own
``source_docs`` frontmatter so the common runner can score document-level gold
without changing the Tessellum index schema.

The adapter is intentionally lexical first. Dense and hybrid variants should be
separate arm classes so their model, index, and token budgets are recorded in the
run manifest rather than hidden behind one mutable flag.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from benchmarks.adapters.base import Document

_FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_SOURCE_LIST = re.compile(r"^\s*-\s*[\"']?([^\"'\n]+?)[\"']?\s*$")
_FTS_TOKEN = re.compile(r"[A-Za-z0-9_]+")


def _source_docs(path: Path) -> frozenset[str]:
    """Read the note's declared source document ids without indexing scaffolding."""
    text = path.read_text(encoding="utf-8", errors="replace")
    match = _FRONTMATTER.match(text)
    if not match:
        return frozenset()
    lines = match.group(1).splitlines()
    values: list[str] = []
    collecting = False
    for line in lines:
        if line.startswith("source_docs:"):
            collecting = True
            inline = line.split(":", 1)[1].strip()
            if inline.startswith("[") and inline.endswith("]"):
                values.extend(
                    item.strip().strip("\"'")
                    for item in inline[1:-1].split(",")
                    if item.strip()
                )
            continue
        if collecting:
            item = _SOURCE_LIST.match(line)
            if item:
                values.append(item.group(1).strip())
            elif line and not line.startswith((" ", "\t")):
                break
    return frozenset(v for v in values if v)


def _fts_query(query: str) -> str:
    """Turn benchmark prose into safe Tessellum FTS5 terms.

    The public Tessellum primitive intentionally exposes raw FTS5 syntax for
    expert callers. A benchmark query is ordinary prose and may contain `?`,
    quotes, parentheses, or hyphens, so the adapter must normalize it before
    dispatching instead of turning punctuation into a run failure.
    """
    # BM25 is a candidate generator: OR preserves recall, while the FTS ranker
    # still orders documents by how many/high-value terms they contain. An
    # implicit AND makes ordinary multi-hop questions return no candidates.
    return " OR ".join(f'"{token}"' for token in _FTS_TOKEN.findall(query))


class TessellumBm25System:
    """Benchmark arm backed by a checkout of Tessellum and one prepared vault."""

    def __init__(
        self,
        vault: Path,
        *,
        db_path: Path,
        tessellum_root: Path | None = None,
        system_id: str | None = None,
    ) -> None:
        self.vault = Path(vault).resolve()
        self.db_path = Path(db_path).resolve()
        self.tessellum_root = Path(
            tessellum_root
            or os.environ.get("TESSELLUM_ROOT", "")
        ).resolve() if (tessellum_root or os.environ.get("TESSELLUM_ROOT")) else None
        self.system_id = system_id or f"tessellum-bm25:{self.vault.name}"
        self._source_by_note: dict[str, frozenset[str]] = {}
        self._words_by_note: dict[str, int] = {}
        self._read: set[Path] = set()
        self._bm25_search = None

    def _load_tessellum(self):
        if self._bm25_search is not None:
            return self._bm25_search
        if self.tessellum_root is not None:
            src = str(self.tessellum_root / "src")
            if src not in sys.path:
                sys.path.insert(0, src)
        try:
            from tessellum.retrieval.bm25 import bm25_search
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Tessellum is unavailable; pass tessellum_root or set "
                "TESSELLUM_ROOT to a Tessellum checkout"
            ) from exc
        self._bm25_search = bm25_search
        return bm25_search

    def arm_config(self) -> Mapping[str, object]:
        return {
            "strategy": "bm25",
            "vault": str(self.vault),
            "indexer": "tessellum.indexer.build",
            "retriever": "tessellum.retrieval.bm25_search",
        }

    def ingest(self, corpus: Iterable[Document]) -> None:
        """Build the Tessellum index from the prepared vault only.

        The benchmark corpus iterator is intentionally not consumed: the vault is
        the transformed artifact being measured, and reading the corpus here would
        make provenance/quarantine ambiguous. The runner still supplies the
        iterator to satisfy the common system protocol.
        """
        if not self.vault.is_dir():
            raise FileNotFoundError(f"Tessellum vault not found: {self.vault}")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            self.db_path.unlink()
        if self.tessellum_root is not None:
            src = str(self.tessellum_root / "src")
            if src not in sys.path:
                sys.path.insert(0, src)
        try:
            from tessellum.indexer.build import build
        except ImportError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "Tessellum is unavailable; pass tessellum_root or set "
                "TESSELLUM_ROOT to a Tessellum checkout"
            ) from exc
        build(self.vault, self.db_path, force=True, with_dense=False)
        self._read.add(self.db_path)
        for path in sorted(self.vault.rglob("*.md")):
            rel = str(path.relative_to(self.vault))
            self._source_by_note[rel] = _source_docs(path)
            self._words_by_note[rel] = len(path.read_text(
                encoding="utf-8", errors="replace"
            ).split())
            self._read.add(path)

    def retrieve(self, query: str, k: int) -> Sequence[tuple[str, set[str]]]:
        safe_query = _fts_query(query)
        if not safe_query:
            return []
        hits = self._load_tessellum()(
            self.db_path, safe_query, k=k, snippet_length=None
        )
        return [
            (hit.note_id, set(self._source_by_note.get(hit.note_id, ())))
            for hit in hits
        ]

    def unit_words(self) -> Mapping[str, int]:
        return self._words_by_note

    def files_read(self) -> Sequence[Path]:
        return tuple(sorted(self._read))
