"""MultiHop-RAG adapter.

Proves the interface against the one benchmark this repo has a real result on.

The notable thing it fixes: the upstream release carries a verbatim `fact` string
for every evidence item, and the existing harness discarded it, keeping only the
source document. That is why `evidence_recall` came out NaN and why every
retrieval number here is document-level — which is the credit granularity measured
to inflate a note arm about ten times more than a chunk arm. This adapter exposes
both, so a scorer can ask for span-level credit and get it.

The upstream corpus has no stable id field, while evidence items carry URLs. The
adapter assigns deterministic `doc_0000`-style ids in corpus order and uses the
same URL→id map for corpus documents and gold. This matches the `source_docs`
contract used by the prepared note vaults and prevents a retrieval arm from
returning one identifier space while gold is scored in another.
"""

from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Iterator, Sequence

from benchmarks.adapters.base import Document, Gold, Query
from benchmarks.registry import REGISTRY

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "multihop_rag"

# Upstream calls them `*_query`; the registry's strata drop the suffix.
_STRATUM = {
    "inference_query": "inference",
    "comparison_query": "comparison",
    "temporal_query": "temporal",
    "null_query": "null",
}


class MultiHopRagAdapter:
    spec = REGISTRY["multihop_rag"]
    spec_root = RAW

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else RAW
        self._read: list[Path] = []

    @cached_property
    def _corpus_records(self) -> list[dict]:
        path = self.root / "corpus.json"
        self._read.append(path)
        return json.loads(path.read_text())

    @cached_property
    def _url_to_doc_id(self) -> dict[str, str]:
        return {
            rec["url"]: f"doc_{i:04d}"
            for i, rec in enumerate(self._corpus_records)
        }

    # ── Corpus: the only thing a system under test may see ────────────────────

    def corpus(self) -> Iterator[Document]:
        for rec in self._corpus_records:
            yield Document(
                doc_id=self._url_to_doc_id[rec["url"]],
                text=rec["body"],
                title=rec.get("title", ""),
                metadata={
                    k: rec.get(k)
                    for k in ("author", "source", "published_at", "category")
                },
            )

    # ── Queries and gold: quarantined from ingestion ──────────────────────────

    @cached_property
    def _questions(self) -> list[dict]:
        path = self.root / "MultiHopRAG.json"
        self._read.append(path)
        return json.loads(path.read_text())

    def queries(self) -> Iterator[Query]:
        for i, rec in enumerate(self._questions):
            yield Query(
                query_id=f"mhr-{i:05d}",
                text=rec["query"],
                stratum=_STRATUM.get(rec["question_type"], rec["question_type"]),
            )

    @cached_property
    def _gold(self) -> dict[str, Gold]:
        out: dict[str, Gold] = {}
        for i, rec in enumerate(self._questions):
            qid = f"mhr-{i:05d}"
            evidence = rec.get("evidence_list") or []
            out[qid] = Gold(
                query_id=qid,
                documents=frozenset(
                    self._url_to_doc_id[e["url"]]
                    for e in evidence
                    if e.get("url") in self._url_to_doc_id
                ),
                # The field the old harness threw away.
                facts=tuple(e["fact"] for e in evidence if e.get("fact")),
                answers=(rec["answer"],) if rec.get("answer") else (),
                # 301 null queries carry no evidence. Refusing them is correct.
                answerable=bool(evidence),
            )
        return out

    def gold(self, query_id: str) -> Gold:
        return self._gold[query_id]

    def files_read(self) -> Sequence[Path]:
        return tuple(self._read)

    # ── Convenience the runner uses ───────────────────────────────────────────

    def stratum_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for q in self.queries():
            counts[q.stratum] = counts.get(q.stratum, 0) + 1
        return counts

    def answerable_count(self) -> int:
        return sum(1 for g in self._gold.values() if g.answerable)
