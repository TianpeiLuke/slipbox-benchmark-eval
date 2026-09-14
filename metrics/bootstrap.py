"""Paired bootstrap intervals — mandatory, not optional.

Build-to-build variance from the stochastic writer alone was measured at ±0.047
pooled on this corpus. A point difference smaller than that is not a result, so
every comparison reports an interval and a single build never licenses an effect.

This reads `per_question.json`, which is why the runner commits it: an aggregate
mean cannot produce a paired interval, and the one real correction this project
has made — that the note layer TIES chunking rather than losing to it — was only
findable because per-item series happened to survive in the legacy files.

Deterministic by construction: the resample seed is derived from the two run ids,
so the same pair always yields the same interval. A confidence interval that moves
when you re-run it is not evidence.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runs.registry import RunManifest, comparable, run_dir  # noqa: E402

DEFAULT_RESAMPLES = 4000
NOISE_FLOOR_POOLED = 0.047
"""Measured build-to-build variance, pooled. Reported beside every delta so a
gap inside it is not read as an effect."""


@dataclass(frozen=True)
class PairedDelta:
    metric: str
    n: int
    delta: float
    ci_low: float
    ci_high: float
    resamples: int
    significant: bool
    inside_noise_floor: bool
    """True when |delta| < the measured build-noise floor. A 'significant'
    result that is also inside the floor is significant against sampling noise
    and NOT against build noise -- both flags must be read together."""


def load_per_question(m: RunManifest) -> dict:
    p = run_dir(m) / "per_question.json"
    if not p.exists():
        raise FileNotFoundError(
            f"{m.run_id}: no per_question.json. A paired interval cannot be "
            "computed from aggregates; re-run the arm with the current harness."
        )
    return json.loads(p.read_text())


def _seed(a: str, b: str, metric: str) -> int:
    h = hashlib.sha256(f"{a}|{b}|{metric}".encode()).hexdigest()
    return int(h[:8], 16)


def paired_delta(
    arm: Sequence[float],
    ref: Sequence[float],
    metric: str,
    seed: int,
    resamples: int = DEFAULT_RESAMPLES,
    alpha: float = 0.05,
) -> PairedDelta:
    """Bootstrap the mean paired difference (arm − ref) over shared items."""
    if len(arm) != len(ref):
        raise ValueError(
            f"{metric}: arms have {len(arm)} and {len(ref)} items; a paired test "
            "requires the same question set in the same order"
        )
    n = len(arm)
    if n == 0:
        raise ValueError(f"{metric}: nothing to compare")

    diffs = [a - b for a, b in zip(arm, ref)]
    point = sum(diffs) / n

    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        total = 0.0
        for _ in range(n):
            total += diffs[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    lo = means[int((alpha / 2) * resamples)]
    hi = means[min(int((1 - alpha / 2) * resamples), resamples - 1)]

    return PairedDelta(
        metric=metric,
        n=n,
        delta=point,
        ci_low=lo,
        ci_high=hi,
        resamples=resamples,
        significant=(lo > 0 or hi < 0),
        inside_noise_floor=abs(point) < NOISE_FLOOR_POOLED,
    )


def compare_runs(
    arm: RunManifest,
    ref: RunManifest,
    metrics: Sequence[str] | None = None,
    resamples: int = DEFAULT_RESAMPLES,
) -> dict:
    """Paired comparison of two runs, refused when they are not on one scale."""
    ok, why = comparable(arm, ref)
    if not ok:
        return {"comparable": False, "reason": why}

    a_pq, r_pq = load_per_question(arm), load_per_question(ref)
    if a_pq["qids"] != r_pq["qids"]:
        return {
            "comparable": False,
            "reason": (
                "the two runs scored different question sets or orders "
                f"({len(a_pq['qids'])} vs {len(r_pq['qids'])} items); "
                "a paired test needs the same items aligned"
            ),
        }

    names = list(metrics) if metrics else sorted(
        set(a_pq["scores"]) & set(r_pq["scores"])
    )
    out = []
    for name in names:
        if name not in a_pq["scores"] or name not in r_pq["scores"]:
            continue
        out.append(paired_delta(
            a_pq["scores"][name], r_pq["scores"][name], name,
            seed=_seed(arm.run_id, ref.run_id, name), resamples=resamples,
        ))
    return {
        "comparable": True,
        "arm": arm.system,
        "ref": ref.system,
        "n_items": len(a_pq["qids"]),
        "noise_floor_pooled": NOISE_FLOOR_POOLED,
        "deltas": [d.__dict__ for d in out],
    }
