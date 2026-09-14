"""Selective prediction — separating "wrong" from "declined to answer".

This family did not exist in the repo, and its absence is the single largest
reporting gap. The measured behaviour of the system under test is a conditional
accuracy of 0.98-0.99 *whenever it answers*, with refusal reaching 0.835. Pooled
accuracy describes neither of those facts: it reads as catastrophic failure when
the real finding is near-perfect precision at very low coverage.

Any metric that pools refusals with errors is the wrong instrument here.

Three requirements enforced by this module, each from a specific prior mistake:

**A constant-predictor floor beside every arm.** A prior run scored 0.145 macro
while the zero-model per-stratum modal baseline scored 0.542 -- the arm lost to a
constant by nearly 40 points, and no aggregate in the repo surfaced it. The floor
is a computed column here, not something a reader must remember to check.

**Per-stratum reporting, never pooled.** A stratum the model declines 87.6% of
the time is a refusal readout, not an accuracy measurement, and pooling hides it.

**Risk-coverage rather than a single operating point.** A system can be made to
look better or worse purely by moving its refusal threshold, so reporting one
point is reporting a choice.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class SelectiveScore:
    """One arm's behaviour, decomposed so refusal and error stay separate."""

    n: int
    answered: int
    refused: int
    refusal_rate: float
    coverage: float
    conditional_accuracy: float
    """Accuracy among ANSWERED items only. The 0.98-0.99 number."""
    pooled_accuracy: float
    """Accuracy over all items, refusals scored 0. Reported for comparability
    with benchmarks that demand it, never as the headline."""
    constant_floor: float
    """Best achievable by a zero-model predictor that always answers."""
    clears_floor: bool


def score_selective(
    correct: Sequence[float],
    refused: Sequence[bool],
    gold: Sequence[str] | None = None,
) -> SelectiveScore:
    """Decompose an arm into coverage and conditional accuracy.

    `correct[i]` is the item's score in [0, 1]; it is ignored where
    `refused[i]`. `gold` enables the constant-predictor floor: the score a
    model-free predictor gets by always emitting the modal gold value.
    """
    if len(correct) != len(refused):
        raise ValueError("correct and refused must be the same length")
    n = len(correct)
    if n == 0:
        return SelectiveScore(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, False)

    answered_idx = [i for i in range(n) if not refused[i]]
    n_ans = len(answered_idx)
    n_ref = n - n_ans

    cond = sum(correct[i] for i in answered_idx) / n_ans if n_ans else 0.0
    pooled = sum(correct[i] for i in answered_idx) / n

    floor = 0.0
    if gold is not None:
        if len(gold) != n:
            raise ValueError("gold must be the same length as correct")
        counts: dict[str, int] = defaultdict(int)
        for g in gold:
            counts[g] += 1
        floor = max(counts.values()) / n if counts else 0.0

    return SelectiveScore(
        n=n,
        answered=n_ans,
        refused=n_ref,
        refusal_rate=n_ref / n,
        coverage=n_ans / n,
        conditional_accuracy=cond,
        pooled_accuracy=pooled,
        constant_floor=floor,
        clears_floor=pooled > floor,
    )


def score_by_stratum(
    correct: Sequence[float],
    refused: Sequence[bool],
    stratum: Sequence[str],
    gold: Sequence[str] | None = None,
) -> dict[str, SelectiveScore]:
    """Per-stratum decomposition. Use this, not the pooled version.

    A stratum whose refusal rate is near 1.0 is measuring willingness, not
    ability, and that is invisible once strata are pooled.
    """
    if not (len(correct) == len(refused) == len(stratum)):
        raise ValueError("correct, refused and stratum must be the same length")
    buckets: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(stratum):
        buckets[s].append(i)
    out: dict[str, SelectiveScore] = {}
    for s, idx in buckets.items():
        out[s] = score_selective(
            [correct[i] for i in idx],
            [refused[i] for i in idx],
            [gold[i] for i in idx] if gold is not None else None,
        )
    return out


def risk_coverage(
    correct: Sequence[float], confidence: Sequence[float]
) -> list[tuple[float, float]]:
    """The risk-coverage curve: (coverage, risk) sorted by descending confidence.

    Reporting a single operating point reports a threshold choice. This sweeps
    it. Risk is 1 - accuracy over the covered prefix.
    """
    if len(correct) != len(confidence):
        raise ValueError("correct and confidence must be the same length")
    order = sorted(range(len(correct)), key=lambda i: -confidence[i])
    curve: list[tuple[float, float]] = []
    running = 0.0
    for j, i in enumerate(order, start=1):
        running += correct[i]
        curve.append((j / len(order), 1.0 - running / j))
    return curve


def aurc(correct: Sequence[float], confidence: Sequence[float]) -> float:
    """Area under the risk-coverage curve. Lower is better.

    The threshold-free summary of selective performance. Quote this alongside
    the curve, not instead of it.
    """
    curve = risk_coverage(correct, confidence)
    if not curve:
        return 0.0
    return sum(risk for _, risk in curve) / len(curve)


def abstention_correctness(
    refused: Sequence[bool], answerable: Sequence[bool]
) -> Mapping[str, float]:
    """Was each refusal the RIGHT call?

    On a benchmark with unanswerable questions -- MultiHop-RAG ships 301 -- a
    refusal is correct behaviour, not a failure. This is the metric on which an
    abstaining system should win outright: the strongest published graph baseline
    scores 13.95 on that subset.
    """
    if len(refused) != len(answerable):
        raise ValueError("refused and answerable must be the same length")
    tp = sum(1 for r, a in zip(refused, answerable) if r and not a)
    fp = sum(1 for r, a in zip(refused, answerable) if r and a)
    fn = sum(1 for r, a in zip(refused, answerable) if not r and not a)
    tn = sum(1 for r, a in zip(refused, answerable) if not r and a)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    return {
        "abstain_precision": prec,
        "abstain_recall": rec,
        "abstain_f1": (2 * prec * rec / (prec + rec)) if prec + rec else 0.0,
        "correct_abstentions": float(tp),
        "wrongly_refused_answerable": float(fp),
        "answered_unanswerable": float(fn),
        "correctly_attempted": float(tn),
    }
