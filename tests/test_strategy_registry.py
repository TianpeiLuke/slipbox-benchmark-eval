"""STRATEGIES is the single retrieval registry.

A strategy registered only as a dict lambda used to be invisible to callers that
resolved by getattr, which is how `perdoc1` silently failed for four of eight
experiment arms -- the run exited 0 with empty output files.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import retrieval as R


def test_every_strategy_is_callable():
    for name, fn in R.STRATEGIES.items():
        assert callable(fn), f"{name} is not callable"


def test_every_strategy_resolves_by_name_too():
    """Belt and braces: no dict-only entries, so either resolution path works."""
    for name, fn in R.STRATEGIES.items():
        assert getattr(R, name, None) is fn, (
            f"{name} is in STRATEGIES but getattr(retrieval, {name!r}) is not the "
            f"same object -- a caller resolving by attribute would miss it")


def test_answer_eval_resolves_through_the_registry():
    import answer_eval
    src = Path(answer_eval.__file__).read_text()
    assert "getattr(R, strategy)" not in src, (
        "answer_eval.build_context must resolve strategies through R.STRATEGIES")
