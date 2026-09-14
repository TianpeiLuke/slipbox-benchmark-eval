"""The committed results are the regression test for the metrics extraction.

`metrics/retrieval.py` pulled Recall@k, All-Recall@k and the budget fill out of
`scripts/score_retrieval.py`, where three scorers each had their own copy. The
extraction is only safe if it reproduces what is already published, so these tests
recompute the headline table in `experiments/results/RESULTS.md` from the
per-question arrays committed under `experiments/runs2/` and assert the numbers
match.

If a test here fails, the extraction changed a definition. Do not update the
expected value -- find out which definition moved.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from metrics.retrieval import (  # noqa: E402
    all_recall_at_k,
    fill_to_budget,
    hits_at_k,
    mrr_at_k,
    recall_at_k,
)
from metrics.selective import (  # noqa: E402
    abstention_correctness,
    score_selective,
)

RUNS2 = ROOT / "experiments" / "runs2"


def _arm(slug: str, strategy: str) -> dict:
    path = RUNS2 / f"{slug}.json"
    if not path.exists():
        pytest.skip(f"{path.relative_to(ROOT)} not present")
    return json.loads(path.read_text())["strategies"][strategy]


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


# ── The published headline, recomputed ────────────────────────────────────────

# RESULTS.md, "Arm comparison -- token-budget matched (runs2, Recall / All-Recall)".
# Expected values are read off the committed summary table, to 3 dp.
PUBLISHED = [
    ("chunks_bm25", "bm25", "2048", 0.732, 0.451),
    ("chunks_bm25", "bm25", "4096", 0.844, 0.633),
    ("chunks_bm25", "bm25", "8192", 0.921, 0.798),
    ("chunks_hybrid", "hybrid", "2048", 0.691, 0.381),
    ("notes_bm25", "bm25", "2048", 0.577, 0.248),
    ("notes_bm25", "bm25", "8192", 0.850, 0.649),
    ("notes_hybrid", "hybrid", "2048", 0.592, 0.249),
]


@pytest.mark.parametrize("slug,strategy,budget,exp_recall,exp_all", PUBLISHED)
def test_published_budget_numbers_reproduce(
    slug: str, strategy: str, budget: str, exp_recall: float, exp_all: float
) -> None:
    """The per-question arrays average to the published table."""
    arm = _arm(slug, strategy)
    if budget not in arm["budget"]:
        pytest.skip(f"{slug}/{strategy} has no budget {budget}")
    cell = arm["budget"][budget]
    assert _mean(cell["recall"]) == pytest.approx(exp_recall, abs=5e-4)
    assert _mean(cell["all"]) == pytest.approx(exp_all, abs=5e-4)


def test_the_matched_k_inversion_is_real() -> None:
    """The central methodological finding, asserted as a test.

    Notes WIN at matched k and LOSE at matched token budget. If this ever stops
    holding, either the data moved or a definition did -- and the k number is the
    one the project must never report as its result.
    """
    chunks = _arm("chunks_bm25", "bm25")
    notes = _arm("notes_bm25", "bm25")

    k_gap = _mean(notes["k"]["10"]["all"]) - _mean(chunks["k"]["10"]["all"])
    b_gap = _mean(notes["budget"]["2048"]["recall"]) - _mean(
        chunks["budget"]["2048"]["recall"]
    )

    assert k_gap > 0.25, f"notes should win big at k=10, got {k_gap:+.3f}"
    assert b_gap < -0.10, f"notes should lose at budget=2048, got {b_gap:+.3f}"


def test_answerable_count_is_the_documented_set() -> None:
    """2,255 answerable questions; the 301 null queries are excluded from recall."""
    for slug, strategy in (("chunks_bm25", "bm25"), ("notes_bm25", "bm25")):
        arm = _arm(slug, strategy)
        assert arm["answerable"] == 2255
        assert len(arm["qids"]) == 2255


# ── Unit behaviour of the extracted definitions ───────────────────────────────


def test_recall_and_all_recall_disagree_on_partial_cover() -> None:
    ranked = [("u1", {"d1"}), ("u2", {"d3"})]
    gold = {"d1", "d2"}
    assert recall_at_k(ranked, gold, 2) == pytest.approx(0.5)
    assert all_recall_at_k(ranked, gold, 2) == 0.0


def test_all_recall_needs_every_gold_doc() -> None:
    ranked = [("u1", {"d1"}), ("u2", {"d2"})]
    assert all_recall_at_k(ranked, {"d1", "d2"}, 2) == 1.0
    assert all_recall_at_k(ranked, {"d1", "d2"}, 1) == 0.0


def test_budget_fill_skips_an_overrunning_unit_and_keeps_going() -> None:
    """The preserved quirk: an oversized unit is skipped, not a stop condition.

    This is the behaviour the committed results were produced with. Changing it
    would silently move every budget number.
    """
    ranked = [("big", {"d1"}), ("small", {"d2"})]
    words = {"big": 5000, "small": 10}
    assert fill_to_budget(ranked, 100, words) == {"d2"}


def test_empty_gold_is_an_error_not_a_zero() -> None:
    """Null queries must be excluded upstream, never scored as 0 recall.

    Scoring an unanswerable question by recall is meaningless, and returning 0
    would let an arm's score move purely with how often it returns nothing.
    """
    with pytest.raises(ValueError):
        recall_at_k([("u1", {"d1"})], set(), 1)
    with pytest.raises(ValueError):
        all_recall_at_k([("u1", {"d1"})], set(), 1)


def test_mrr_and_hits_agree_on_first_cover() -> None:
    ranked = [("u1", {"dx"}), ("u2", {"d1"})]
    gold = {"d1"}
    assert mrr_at_k(ranked, gold, 5) == pytest.approx(0.5)
    assert hits_at_k(ranked, gold, 5) == 1.0
    assert hits_at_k(ranked, gold, 1) == 0.0


# ── Selective prediction ──────────────────────────────────────────────────────


def test_refusal_and_error_are_separated() -> None:
    """The shape of the measured behaviour: near-perfect when it speaks, rarely speaks."""
    correct = [1.0, 1.0, 0.0, 0.0, 0.0]
    refused = [False, False, True, True, True]
    s = score_selective(correct, refused)
    assert s.conditional_accuracy == pytest.approx(1.0)
    assert s.pooled_accuracy == pytest.approx(0.4)
    assert s.refusal_rate == pytest.approx(0.6)
    assert s.coverage == pytest.approx(0.4)


def test_constant_floor_catches_an_arm_losing_to_a_zero_model_baseline() -> None:
    """A prior run scored 0.145 against a 0.542 modal baseline and nothing noticed."""
    gold = ["yes"] * 8 + ["no"] * 2
    correct = [1.0] + [0.0] * 9
    refused = [False] + [True] * 9
    s = score_selective(correct, refused, gold=gold)
    assert s.constant_floor == pytest.approx(0.8)
    assert s.pooled_accuracy == pytest.approx(0.1)
    assert s.clears_floor is False


def test_abstaining_on_unanswerable_is_scored_as_correct() -> None:
    """MultiHop-RAG ships 301 unanswerable queries; refusing them is the right call."""
    refused = [True, True, False, False]
    answerable = [False, True, False, True]
    m = abstention_correctness(refused, answerable)
    assert m["correct_abstentions"] == 1.0
    assert m["wrongly_refused_answerable"] == 1.0
    assert m["answered_unanswerable"] == 1.0
    assert m["correctly_attempted"] == 1.0
    assert m["abstain_precision"] == pytest.approx(0.5)


# ── What the registry surfaced that the hand-written summary did not ──────────


def _paired_delta(arm_path: str, ref_path: str, budget: str = "2048") -> float:
    """Mean paired difference in Recall@budget, arm minus reference."""
    def cell(rel: str) -> list[float]:
        p = ROOT / "experiments" / f"{rel}.json"
        if not p.exists():
            pytest.skip(f"{rel} not present")
        d = json.loads(p.read_text())
        return d["strategies"]["bm25"]["budget"][budget]["recall"]

    arm, ref = cell(arm_path), cell(ref_path)
    assert len(arm) == len(ref), "arms must be scored on the same question set"
    return sum(a - b for a, b in zip(arm, ref)) / len(arm)


def test_the_headline_loss_is_against_the_ORIGINAL_note_vault() -> None:
    """RESULTS.md's -0.155 is real, and it is specific to the runs2 vault."""
    assert _paired_delta("runs2/notes_bm25", "runs2/chunks_bm25") < -0.10


@pytest.mark.parametrize("arm", ["runs6/notes_noscaffold", "runs6/notes_expanded"])
def test_improved_note_vaults_are_NOT_a_loss_against_chunks(arm: str) -> None:
    """The correction the run registry surfaced.

    Putting runs2 and runs6 in one table -- which no hand-written summary had
    done -- shows the headline "chunks win at every budget" is true of the
    ORIGINAL note vault and not of the improved variants. After the
    scaffolding-exclusion fix, notes reach 0.736-0.742 against chunks' 0.732:
    a tie, not a 0.155 loss. Paired bootstrap over the 2,255 shared questions
    puts both deltas' CIs across zero, so the honest claim is
    indistinguishable, in BOTH directions -- these arms do not beat chunks
    either.
    """
    delta = _paired_delta(arm, "runs2/chunks_bm25")
    assert delta > -0.02, f"{arm} should not be a large loss, got {delta:+.4f}"
    assert delta < 0.05, (
        f"{arm} should not be claimed as a win either, got {delta:+.4f}; "
        "the measured CI crosses zero"
    )
