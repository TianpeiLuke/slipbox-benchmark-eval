"""Pin the settings that measurement selected, so they cannot regress silently.

Each test corresponds to a row in docs/RECOMMENDED.md. These are invariants
about the harness, not about scores -- they are cheap and run without a vault.
"""
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import retrieval as R          # noqa: E402
import answer_eval             # noqa: E402
import score_answers as SA     # noqa: E402


def test_perdoc_cap_is_strict_by_default():
    """spill=True silently disables the cap for any caller asking a large k."""
    assert inspect.signature(R.perdoc).parameters["spill"].default is False


def test_perdoc_charges_every_source_document():
    """Keying on min(docs) under-counted exactly the multi-source notes the cap
    exists to control."""
    # Check the BODY, not the docstring -- the docstring names min(docs) to
    # explain what was fixed, and matching it made this test fail on correct code.
    src = inspect.getsource(R.perdoc)
    body = src.split('"""')[2] if src.count('"""') >= 2 else src
    assert "min(docs)" not in body, "perdoc must charge every declared document"
    assert "all(used[d] < cap for d in docs)" in body


def test_candidate_pool_scales_with_budget():
    """A fixed pool is not neutral between unit sizes: 40 atoms carry about a
    quarter the text of 40 coarse notes, so the atom arm saturated on the
    harness rather than on its own limits."""
    src = inspect.getsource(answer_eval.build_context)
    assert "max(k, 40)" not in src, "candidate pool must scale with the budget"
    assert "budget //" in src


def test_answers_decoded_deterministically():
    src = inspect.getsource(answer_eval.ask_anthropic)
    assert "temperature=0" in src


def test_refusal_is_leading_not_substring():
    """A substring test scored a hedged but correct answer as a refusal."""
    assert SA.is_refusal("INSUFFICIENT\n\nThe context does not contain it")
    assert not SA.is_refusal("The context is insufficient, but the answer is Apple")


def test_containment_is_token_not_character():
    """A quarter of gold answers are 'no', which lives inside 'not' and 'north'."""
    assert not SA.tok_contains("This is not known", "no")
    assert SA.tok_contains("No", "no")


def test_normalise_preserves_token_boundaries():
    """Deleting punctuation turned 'Sam Bankman-Fried' into one token."""
    assert SA.normalise("Sam Bankman-Fried") == "sam bankman fried"


def test_polarity_scored_by_verdict_not_string_equality():
    assert SA.correct("No, because the article predates it.", "no") == 1.0
    assert SA.correct("Yes", "no") == 0.0


def test_harmful_strategies_are_still_registered_but_documented():
    """chain/chain1 measured harmful; they stay available for reproduction, and
    RECOMMENDED.md must keep saying not to use them."""
    doc = (Path(__file__).resolve().parent.parent / "docs/RECOMMENDED.md").read_text()
    assert "do not use" in doc.lower()
    assert "chain" in doc and "perdoc1" in doc
