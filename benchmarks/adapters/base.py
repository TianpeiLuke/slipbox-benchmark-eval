"""The adapter interface — what makes a benchmark runnable rather than merely downloaded.

One adapter per dataset, normalising it onto three iterators plus a gold lookup.
Everything downstream — the runner, the metrics, the report — sees only this
interface, so adding a benchmark is one record in the registry plus one adapter
here, instead of the three-to-five bespoke scripts it costs today.

Two decisions are worth stating because they are not obvious.

**Gold is returned at every granularity the dataset actually supports, not just
the one the old harness used.** MultiHop-RAG's upstream release carries a verbatim
`fact` string per evidence item; the harness in this repo kept only the document
id and threw the fact away, which is why an `evidence_recall` column came out NaN
and why all retrieval credit here is document-level. An adapter that exposes only
the coarse form makes that loss permanent, so `Gold` carries both and the caller
declares which it is scoring.

**Quarantine is enforced, not documented.** The first budget experiment in this
project was superseded outright because its questions had been generated from the
notes under test. `corpus()` is the only method a system under test may call, and
`assert_quarantine_respected` exists so a harness can prove it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Protocol, Sequence, runtime_checkable

from benchmarks.registry import BenchmarkSpec


@dataclass(frozen=True)
class Document:
    """One ingestible source document. This is all a system under test may see."""

    doc_id: str
    text: str
    title: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Query:
    query_id: str
    text: str
    stratum: str = ""
    """The subset this query belongs to. Reported separately, never pooled --
    pooling MultiHop-RAG's four types hides that null queries are where an
    abstaining system should win outright."""


@dataclass(frozen=True)
class Gold:
    """Ground truth at every granularity the dataset supports.

    `documents` is the coarse form every dataset has. `facts` and `answers` are
    populated when the release carries them; a scorer that wants fine-grained
    credit must check rather than assume.
    """

    query_id: str
    documents: frozenset[str] = frozenset()
    facts: tuple[str, ...] = ()
    answers: tuple[str, ...] = ()
    answerable: bool = True
    """False for a deliberately unanswerable query. Refusing one is CORRECT
    behaviour and is scored by metrics.selective.abstention_correctness."""

    def at(self, gold_form: str) -> frozenset[str] | tuple[str, ...]:
        """The gold for a declared granularity, or an error naming what is missing."""
        if gold_form in ("document_set", "passage"):
            return self.documents
        if gold_form == "span":
            if not self.facts:
                raise ValueError(
                    f"{self.query_id}: span-level gold requested but this "
                    "release carries no fact strings"
                )
            return self.facts
        if gold_form == "free_text":
            return self.answers
        raise ValueError(f"unsupported gold_form {gold_form!r}")


@runtime_checkable
class BenchmarkAdapter(Protocol):
    spec: BenchmarkSpec

    def corpus(self) -> Iterator[Document]:
        """The ONLY method a system under test may call."""

    def queries(self) -> Iterator[Query]: ...

    def gold(self, query_id: str) -> Gold: ...

    def files_read(self) -> Sequence[Path]:
        """Every file this adapter has opened, for the quarantine check."""


def assert_quarantine_respected(
    adapter: BenchmarkAdapter, files_read_by_system: Sequence[Path]
) -> None:
    """Raise if a system under test touched a quarantined file.

    Promotes the honour-system prose note on each spec into a check a harness can
    run. Question circularity is not a hypothetical failure here: it invalidated
    an entire experiment and 4,823 generated questions.
    """
    root = Path(adapter.spec_root) if hasattr(adapter, "spec_root") else None
    banned = set(adapter.spec.quarantine)
    if not banned:
        return
    offenders = [
        p for p in files_read_by_system
        if Path(p).name in banned and (root is None or root in Path(p).parents)
    ]
    if offenders:
        raise PermissionError(
            f"{adapter.spec.slug}: system under test read quarantined file(s) "
            f"{[Path(p).name for p in offenders]}. "
            f"{adapter.spec.note or 'Gold must not be visible at ingest time.'}"
        )
