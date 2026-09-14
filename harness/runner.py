"""The standardized experiment mechanism — one path from benchmark to stored metrics.

Before this, running an arm meant picking one of seventy-three scripts, and the
config that distinguished two runs lived in the filename (`execute_v2` …
`execute_v41`). There was no uniform way to say "run arm X on benchmark Y", and
nothing wrote a machine-readable metric record, so the report had to parse legacy
result files.

This closes that. One call, five stages, every stage recording what it did:

    fetch  ->  ingest  ->  retrieve  ->  score  ->  store

A system under test contributes a `System` implementation and nothing else. It
never sees the gold: `ingest` is handed the adapter's `corpus()` iterator only, and
`assert_quarantine_respected` proves it afterwards.

What this deliberately does NOT do: schedule, parallelise, or run remotely. The
bottleneck in this project is deciding what to measure, not compute.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmarks.adapters.base import (  # noqa: E402
    BenchmarkAdapter,
    Document,
    assert_quarantine_respected,
)
from metrics.retrieval import (  # noqa: E402
    all_recall_at_k,
    hits_at_k,
    map_at_k,
    mrr_at_k,
    recall_at_budget,
    recall_at_k,
)
from metrics.selective import abstention_correctness  # noqa: E402
from runs.registry import make_manifest, run_dir, write_manifest  # noqa: E402

DEFAULT_KS = (2, 5, 10)
DEFAULT_BUDGETS = (2048, 4096, 8192)


class System(Protocol):
    """What a system under test must provide. Three methods, no gold access."""

    system_id: str

    def arm_config(self) -> Mapping[str, Any]:
        """Everything that distinguishes this arm. Goes into the run_id hash, so
        two runs differing only here get different ids -- which is why the
        `execute_v2..v41` filename scheme is no longer needed."""

    def ingest(self, corpus: Iterable[Document]) -> None:
        """Build whatever index this arm needs. The ONLY data it is given."""

    def retrieve(self, query: str, k: int) -> Sequence[tuple[str, set[str]]]:
        """Ranked (unit_id, covered source doc ids). Ordered best first."""

    def unit_words(self) -> Mapping[str, int]:
        """Token/word cost per unit id, for budget-matched scoring.

        Required, not optional: matched-k is the comparison that hands the win to
        whichever arm has smaller units, and this repo has measured the same arms
        flipping from +0.306 at k=10 to -0.155 at a 2048-token budget.
        """


@dataclass
class RunResult:
    run_id: str
    manifest_path: Path
    metrics_path: Path
    metrics: dict
    per_question_path: Path | None = None


def _score_retrieval(
    adapter: BenchmarkAdapter,
    system: System,
    ks: Sequence[int],
    budgets: Sequence[int],
    gold_form: str,
    topk: int,
) -> tuple[dict, list[dict]]:
    """Score every query. Returns (aggregate metrics, per-query predictions)."""
    words = system.unit_words()
    per_k: dict[int, dict[str, list[float]]] = {
        k: {"recall": [], "all_recall": [], "mrr": [], "hits": [], "map": []}
        for k in ks
    }
    per_b: dict[int, dict[str, list[float]]] = {
        b: {"recall": [], "all_recall": []} for b in budgets
    }
    by_stratum: dict[str, dict[int, list[float]]] = {}
    # Per-question scores, aligned with `qids`. Committed, not derived: a paired
    # bootstrap needs the per-item series, and an aggregate mean cannot produce
    # one. The tie between the note and chunk arms was only findable because the
    # legacy files happened to keep these -- so keeping them is the difference
    # between a reanalysable run and a dead number.
    per_question: dict[str, list[float]] = {}
    qids: list[str] = []
    predictions: list[dict] = []
    refused: list[bool] = []
    answerable: list[bool] = []
    n_answerable = 0

    for q in adapter.queries():
        g = adapter.gold(q.query_id)
        ranked = list(system.retrieve(q.text, topk))

        predictions.append({
            "query_id": q.query_id,
            "stratum": q.stratum,
            "answerable": g.answerable,
            "units": [uid for uid, _ in ranked[: max(ks) if ks else topk]],
        })
        # A system that returns nothing has effectively declined.
        refused.append(not ranked)
        answerable.append(g.answerable)

        if not g.answerable:
            # Null queries are excluded from recall: scoring an unanswerable
            # question by recall is meaningless and lets an arm's score move
            # purely with how often it returns nothing. They are scored by
            # abstention instead.
            continue
        n_answerable += 1
        qids.append(q.query_id)
        gold = set(g.at(gold_form))

        for k in ks:
            r = recall_at_k(ranked, gold, k)
            per_k[k]["recall"].append(r)
            per_k[k]["all_recall"].append(all_recall_at_k(ranked, gold, k))
            per_k[k]["mrr"].append(mrr_at_k(ranked, gold, k))
            per_k[k]["hits"].append(hits_at_k(ranked, gold, k))
            per_k[k]["map"].append(map_at_k(ranked, gold, k))
            by_stratum.setdefault(q.stratum, {}).setdefault(k, []).append(r)
            per_question.setdefault(f"recall@k{k}", []).append(r)
            per_question.setdefault(f"all_recall@k{k}", []).append(
                per_k[k]["all_recall"][-1]
            )

        for b in budgets:
            r, a = recall_at_budget(ranked, gold, b, words)
            per_b[b]["recall"].append(r)
            per_b[b]["all_recall"].append(a)
            per_question.setdefault(f"recall@b{b}", []).append(r)
            per_question.setdefault(f"all_recall@b{b}", []).append(a)

    def mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else float("nan")

    flat: dict[str, float] = {}
    for k, cells in per_k.items():
        for name, xs in cells.items():
            flat[f"{name}@k{k}"] = mean(xs)
    for b, cells in per_b.items():
        for name, xs in cells.items():
            flat[f"{name}@b{b}"] = mean(xs)
    for stratum, kk in by_stratum.items():
        for k, xs in kk.items():
            flat[f"recall@k{k}/{stratum}"] = mean(xs)

    # Abstention is a first-class result, not a footnote: the 301 unanswerable
    # MultiHop-RAG queries are where an abstaining system should win outright
    # against a 13.95 published baseline.
    flat.update(abstention_correctness(refused, answerable))

    flat["n_answerable"] = float(n_answerable)
    flat["n_queries"] = float(len(predictions))
    return flat, predictions, {"qids": qids, "scores": per_question}


def run(
    adapter: BenchmarkAdapter,
    system: System,
    ks: Sequence[int] = DEFAULT_KS,
    budgets: Sequence[int] = DEFAULT_BUDGETS,
    topk: int = 50,
    gold_form: str | None = None,
    subset: str = "full",
    nondeterministic: Sequence[str] = (),
    notes: str = "",
    write_predictions: bool = True,
) -> RunResult:
    """Run one arm on one benchmark and store the result with its provenance.

    `gold_form` defaults to the spec's declared granularity. Overriding it to a
    finer one (e.g. `span` on MultiHop-RAG, which the upstream release supports
    and the old harness discarded) is the honest way to escape document-level
    credit inflation -- and it is recorded in the manifest so the report can
    refuse to compare the two.
    """
    spec = adapter.spec
    gf = gold_form or spec.gold_form

    # Stage 1-2: ingest. The system sees corpus() and nothing else.
    system.ingest(adapter.corpus())
    assert_quarantine_respected(adapter, getattr(system, "files_read", lambda: ())())

    # Stage 3-4: retrieve and score.
    flat, predictions, per_q = _score_retrieval(
        adapter, system, ks, budgets, gf, topk
    )

    # Stage 5: store, with provenance.
    checksums = _dataset_checksums(spec.slug)
    arm_config = {
        **dict(system.arm_config()),
        "subset": subset,
        "ks": list(ks),
        "budgets": list(budgets),
        "topk": topk,
        "gold_form_scored": gf,
    }
    m = make_manifest(
        system=system.system_id,
        benchmark=spec.slug,
        gold_form=gf,
        arm_config=arm_config,
        metric_set=tuple(sorted(flat)),
        file_sha256=checksums,
        nondeterministic=tuple(nondeterministic),
        notes=notes,
    )
    d = run_dir(m)
    d.mkdir(parents=True, exist_ok=True)
    manifest_path = write_manifest(m, base=d)

    metrics_path = d / "metrics.json"
    metrics_path.write_text(json.dumps(flat, indent=1, sort_keys=True) + "\n")

    # Per-question scores are COMMITTED. They are the only artefact from which a
    # paired interval can be recomputed, and the design mandates paired intervals,
    # so discarding them would make the requirement unmeetable. Cost is small: one
    # float per question per metric.
    per_question_path = d / "per_question.json"
    per_question_path.write_text(json.dumps(per_q, separators=(",", ":")) + "\n")

    if write_predictions:
        with (d / "predictions.jsonl").open("w") as f:
            for row in predictions:
                f.write(json.dumps(row) + "\n")

    return RunResult(m.run_id, manifest_path, metrics_path, flat,
                     per_question_path=per_question_path)


def _dataset_checksums(slug: str) -> dict[str, str]:
    p = ROOT / "data" / "manifest.json"
    if not p.exists():
        return {}
    entry = json.loads(p.read_text()).get(slug) or {}
    return {
        name: meta.get("sha256", "")
        for name, meta in (entry.get("files") or {}).items()
    }
