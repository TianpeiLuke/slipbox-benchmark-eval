"""Retrieval metrics — one implementation, so two arms are comparable.

Recall@k was implemented separately in `score_retrieval.py`, `score_hipporag.py`
and `score_2wiki.py`. Three implementations of one metric means two arms are not
guaranteed comparable, which is a silent correctness problem rather than a tidiness
one. These are the extracted definitions; the scorers import them.

The definitions themselves are unchanged from `score_retrieval.py`, and
`tests/test_metrics_parity.py` asserts they reproduce the committed
`summary_tables.json` exactly.

Two conventions carried over, both load-bearing:

**All-Recall@k is the multi-source metric.** A multi-hop question is only
answerable when *every* piece of its evidence is present, so All-Recall tracks
whether retrieval could have supported an answer at all. Recall shows partial
progress and keeps a run interpretable when All-Recall is near zero.

**Budget-matched is the fair cut; k-matched is not.** Matching on k hands the win
to whichever representation has larger units -- five chunks of 200 words is not
five notes of 328. On this corpus the same arms that lose by 0.155 Recall at a
2048-token budget *win* by 0.189 at k=10. Report the budget number; never lead
with the k number.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Iterable, Mapping, Sequence

# A resolver returns a ranked list of (unit_id, set of source doc ids it covers).
Ranked = Sequence[tuple[str, set[str]]]
Resolver = Callable[[str, int], Ranked]


def recall_at_k(ranked: Ranked, gold: set[str], k: int) -> float:
    """Fraction of a question's gold documents present in the top k units."""
    if not gold:
        raise ValueError("recall is undefined for a question with no gold")
    seen: set[str] = set()
    for _, unit_docs in ranked[:k]:
        seen |= unit_docs
    return len(gold & seen) / len(gold)


def all_recall_at_k(ranked: Ranked, gold: set[str], k: int) -> float:
    """1.0 only if EVERY gold document appears in the top k, else 0.0."""
    if not gold:
        raise ValueError("all-recall is undefined for a question with no gold")
    seen: set[str] = set()
    for _, unit_docs in ranked[:k]:
        seen |= unit_docs
    return 1.0 if gold & seen == gold else 0.0


def fill_to_budget(
    ranked: Ranked, budget: int, words: Mapping[str, int]
) -> set[str]:
    """Source docs covered by units assembled in rank order until the budget is spent.

    A unit that would overrun is SKIPPED and filling continues -- it is not a
    stopping condition. That is the behaviour the committed results were produced
    with, so it is preserved exactly.
    """
    seen: set[str] = set()
    spent = 0
    for uid, unit_docs in ranked:
        w = words.get(uid, 0)
        if spent + w > budget:
            continue
        spent += w
        seen |= unit_docs
    return seen


def recall_at_budget(
    ranked: Ranked, gold: set[str], budget: int, words: Mapping[str, int]
) -> tuple[float, float]:
    """(Recall, All-Recall) at a token budget. The fair cut between representations."""
    if not gold:
        raise ValueError("recall is undefined for a question with no gold")
    seen = fill_to_budget(ranked, budget, words)
    hit = gold & seen
    return len(hit) / len(gold), (1.0 if hit == gold else 0.0)


def mrr_at_k(ranked: Ranked, gold: set[str], k: int) -> float:
    """Reciprocal rank of the first unit covering any gold document."""
    for i, (_, unit_docs) in enumerate(ranked[:k], start=1):
        if unit_docs & gold:
            return 1.0 / i
    return 0.0


def hits_at_k(ranked: Ranked, gold: set[str], k: int) -> float:
    """1.0 if any gold document is covered in the top k. The upstream
    MultiHop-RAG convention, needed to compare against arXiv:2401.15391."""
    for _, unit_docs in ranked[:k]:
        if unit_docs & gold:
            return 1.0
    return 0.0


def map_at_k(ranked: Ranked, gold: set[str], k: int) -> float:
    """Mean average precision over the gold set, credited at first cover."""
    if not gold:
        raise ValueError("MAP is undefined for a question with no gold")
    covered: set[str] = set()
    precisions: list[float] = []
    for i, (_, unit_docs) in enumerate(ranked[:k], start=1):
        new = (unit_docs & gold) - covered
        if new:
            covered |= new
            precisions.append(len(covered) / i)
    return sum(precisions) / len(gold) if precisions else 0.0


def score_run(
    questions: Iterable[Mapping],
    resolve: Resolver,
    ks: Sequence[int],
    topk: int,
    budgets: Sequence[int] = (),
    words: Mapping[str, int] | None = None,
) -> dict:
    """Score one arm over a question set.

    Byte-compatible with `scripts/score_retrieval.py:score` -- same output keys,
    same skip rule for null queries, same budget fill. Questions with empty gold
    (null queries) are EXCLUDED from recall and counted separately: scoring an
    unanswerable question by recall is meaningless, and pooling it flatters or
    punishes an arm depending only on how often it returns nothing.
    """
    stats = {k: {"recall": [], "all": []} for k in ks}
    bstats = {b: {"recall": [], "all": []} for b in budgets}
    by_type: dict[str, dict[int, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    qids: list[str] = []
    answerable = 0

    for q in questions:
        gold = q["gold"]
        if not gold:
            continue
        answerable += 1
        qids.append(q["query"])
        ranked = resolve(q["query"], topk)

        for k in ks:
            r = recall_at_k(ranked, gold, k)
            stats[k]["recall"].append(r)
            stats[k]["all"].append(all_recall_at_k(ranked, gold, k))
            by_type[q["type"]][k].append(r)

        for b in budgets:
            r, a = recall_at_budget(ranked, gold, b, words or {})
            bstats[b]["recall"].append(r)
            bstats[b]["all"].append(a)

    return {
        "stats": stats,
        "by_type": by_type,
        "answerable": answerable,
        "budgets": bstats,
        "qids": qids,
    }
