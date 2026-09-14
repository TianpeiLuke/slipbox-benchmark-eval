"""ICCMA abstract-argumentation adapter.

Registered deliberately as the NON-QA case: gold is a per-argument labelling, there
are no questions, and the scorer is exact agreement rather than recall. If the
adapter interface holds for this and for MultiHop-RAG together, it will hold for the
rest — that was the point of including it from the start.

It is also the cleanest test available for Tessellum: it scores
`tessellum.dks.dung.grounded_labelling` directly, with no LLM, no corpus to digest,
no credit-granularity ambiguity, and a competition-verified answer to compare
against. Correctness is the whole bar.

**Format.** ICCMA 2023 uses the `.af` form:

    p af <N>          # N arguments, numbered 1..N
    # <name>          # optional per-argument comment lines
    <a> <b>           # a attacks b

**The grounded-track caveat, which must not be papered over.** ICCMA has had no
grounded (GR) track since 2019 — `DS-CO` and `SE-CO` are excluded from the modern
competition precisely because they *are* grounded and considered polynomial-time
trivial. So this yields a correctness check, not a competitive ranking. Comparing
PAR-2 against the published solvers would be comparing a trivial semantics against
solvers built for hard ones.
"""

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Iterator

from benchmarks.registry import REGISTRY

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "iccma2023"
ARCHIVE = RAW / "iccma2023_benchmarks.zip"


@dataclass(frozen=True)
class AFInstance:
    """One abstract argumentation framework."""

    name: str
    n_args: int
    arguments: tuple[str, ...]
    attacks: tuple[tuple[str, str], ...]

    @property
    def density(self) -> float:
        return len(self.attacks) / max(self.n_args, 1)


def parse_af(text: str, name: str = "") -> AFInstance:
    """Parse the ICCMA `.af` format.

    Arguments are the integers 1..N from the `p af N` header. `#` lines are
    comments — the competition uses them for human-readable names, and they are
    NOT argument declarations, so treating them as such would silently double the
    argument count.
    """
    n = 0
    attacks: list[tuple[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("p af"):
            n = int(line.split()[2])
            continue
        parts = line.split()
        if len(parts) == 2:
            attacks.append((parts[0], parts[1]))
    return AFInstance(
        name=name,
        n_args=n,
        arguments=tuple(str(i) for i in range(1, n + 1)),
        attacks=tuple(attacks),
    )


class IccmaAdapter:
    """Reads instances straight out of the committed-checksum archive.

    Deliberately does not extract 813 MB to disk: `zipfile` random-access is fast
    enough and leaves the fetched artefact exactly as its checksum describes it.
    """

    spec = REGISTRY["iccma2023"]
    spec_root = RAW

    def __init__(self, archive: Path | None = None) -> None:
        self.archive = Path(archive) if archive else ARCHIVE

    @cached_property
    def _names(self) -> list[str]:
        with zipfile.ZipFile(self.archive) as z:
            return sorted(n for n in z.namelist() if n.endswith(".af"))

    def instance_names(self) -> list[str]:
        return list(self._names)

    def instances(self, limit: int | None = None, smallest_first: bool = False
                  ) -> Iterator[AFInstance]:
        with zipfile.ZipFile(self.archive) as z:
            names = self._names
            if smallest_first:
                names = sorted(names, key=lambda n: z.getinfo(n).file_size)
            for name in names[: limit or len(names)]:
                yield parse_af(z.read(name).decode(), name=Path(name).stem)

    # The interface, for uniformity with the QA adapters. There is no corpus to
    # ingest and no query text: each instance IS the input, and the gold is the
    # labelling a correct solver must produce.
    def corpus(self):
        return iter(())

    def queries(self):
        return iter(())

    def gold(self, query_id: str):
        raise NotImplementedError(
            "ICCMA gold is a per-argument labelling verified by the competition, "
            "not a per-query answer. Score with agreement.exact_labelling."
        )

    def files_read(self):
        return (self.archive,)
