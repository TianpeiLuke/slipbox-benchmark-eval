"""2WikiMultiHopQA adapter.

The benchmark that matters most for the graph claim, and the one MultiHop-RAG
cannot test. Its questions are compositional: the linking entity is usually **not
named in the question**, so answering requires traversing from one document to
another. MultiHop-RAG is the opposite — nearly every question names both of its
entities — which is why the graph arm's result there is uninformative rather than
negative.

**The protocol decision that makes the number comparable.** The release ships as a
*distractor* set: each question carries its own 10-paragraph context. Retrieving
over per-question context measures nothing, because the gold is already 2 of 10
candidates. HippoRAG's protocol instead **pools** all contexts across a
subsample into one shared corpus and retrieves over that, which is what makes
R@2/R@5 meaningful and what the published numbers are measured on. This adapter
pools, and records the resulting corpus size so a reader can check it against the
~6,119 passages the protocol expects at 1,000 questions.

**Gold granularity is `passage`, keyed by title.** `supporting_facts` names
`[title, sentence_index]` pairs; the title identifies the passage. Sentence indices
are carried into `facts` so a scorer can ask for finer credit than the passage —
the same escape from document-level credit inflation the MultiHop-RAG adapter
provides through its `fact` strings.

**Quarantine.** Questions, `supporting_facts`, `evidences` and `answer` all live in
the same file as the context. Quarantine here is therefore a property of the
adapter, not of file access: `corpus()` yields only titles and sentences, and never
touches the other four fields.
"""

from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Iterator, Sequence

from benchmarks.adapters.base import Document, Gold, Query
from benchmarks.registry import REGISTRY

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "2wiki"

DEFAULT_SUBSAMPLE = 1000
"""HippoRAG's protocol uses 1,000 questions. Matching it is what allows the
published R@2/R@5 to be quoted as the baseline rather than a free-floating number."""


class TwoWikiAdapter:
    spec = REGISTRY["2wiki"]
    spec_root = RAW

    def __init__(
        self,
        root: Path | None = None,
        subsample: int | None = DEFAULT_SUBSAMPLE,
    ) -> None:
        self.root = Path(root) if root else RAW
        self.subsample = subsample
        self._read: list[Path] = []

    @cached_property
    def _rows(self) -> list[dict]:
        import pyarrow.parquet as pq

        path = self.root / "dev.parquet"
        self._read.append(path)
        table = pq.read_table(path)
        rows = table.to_pylist()
        # `context`, `supporting_facts`, `evidences` arrive as JSON STRINGS in
        # this release, not as nested arrays. Decoding here keeps every consumer
        # below working on real structures.
        for row in rows:
            for field in ("context", "supporting_facts", "evidences"):
                value = row.get(field)
                if isinstance(value, str):
                    row[field] = json.loads(value)
        # Deterministic prefix rather than a random sample: a seeded sample would
        # have to be recorded to be reproducible, and the release order is fixed.
        return rows[: self.subsample] if self.subsample else rows

    # ── Corpus: pooled across the subsample, keyed by title ───────────────────

    @cached_property
    def _passages(self) -> dict[str, str]:
        pooled: dict[str, str] = {}
        for row in self._rows:
            for title, sentences in row["context"]:
                if title not in pooled:
                    pooled[title] = " ".join(sentences).strip()
        return pooled

    def corpus(self) -> Iterator[Document]:
        for title, text in self._passages.items():
            yield Document(doc_id=title, text=text, title=title)

    # ── Queries and gold ──────────────────────────────────────────────────────

    def queries(self) -> Iterator[Query]:
        for row in self._rows:
            yield Query(
                query_id=row["_id"],
                text=row["question"],
                # `type` is the released question class: compositional, inference,
                # comparison, bridge_comparison. Reported separately -- pooling
                # them hides that comparison questions name both entities and so
                # cannot reward traversal.
                stratum=row.get("type") or "unknown",
            )

    @cached_property
    def _gold(self) -> dict[str, Gold]:
        out: dict[str, Gold] = {}
        for row in self._rows:
            facts = row.get("supporting_facts") or []
            titles = {t for t, _ in facts}
            out[row["_id"]] = Gold(
                query_id=row["_id"],
                documents=frozenset(titles),
                # `title#sentence_index` -- finer than passage, so a scorer can
                # escape passage-level credit if it wants to.
                facts=tuple(f"{t}#{i}" for t, i in facts),
                answers=(row["answer"],) if row.get("answer") else (),
                answerable=bool(titles),
            )
        return out

    def gold(self, query_id: str) -> Gold:
        return self._gold[query_id]

    def files_read(self) -> Sequence[Path]:
        return tuple(self._read)

    # ── Reporting helpers ─────────────────────────────────────────────────────

    def corpus_size(self) -> int:
        return len(self._passages)

    def stratum_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for q in self.queries():
            counts[q.stratum] = counts.get(q.stratum, 0) + 1
        return counts

    def answerable_count(self) -> int:
        return sum(1 for g in self._gold.values() if g.answerable)
