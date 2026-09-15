"""Tests for the adapter, runner, metric store and dashboard.

The load-bearing ones are the guards: a benchmark stack whose comparability checks
do not fire is worse than none, because it lends authority to the exact comparison
it was built to prevent.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from benchmarks.adapters.base import Gold, assert_quarantine_respected  # noqa: E402
from benchmarks.registry import REGISTRY, check_registry  # noqa: E402
from metrics.store import connect, rebuild  # noqa: E402
from report.dashboard import build, family_of  # noqa: E402
from runs.registry import (  # noqa: E402
    CodeProvenance,
    DataProvenance,
    EnvProvenance,
    RunManifest,
    comparable,
    compute_run_id,
)

RAW = ROOT / "data" / "raw" / "multihop_rag"


# ── Registry ──────────────────────────────────────────────────────────────────


def test_every_spec_declares_a_gold_form_and_task_kind() -> None:
    """Both are required, because the report keys comparability off gold_form."""
    for slug, spec in REGISTRY.items():
        assert spec.gold_form, f"{slug} has no gold_form"
        assert spec.task_kind, f"{slug} has no task_kind"


def test_quarantined_file_must_exist_in_files() -> None:
    from benchmarks.registry import BenchmarkSpec

    with pytest.raises(ValueError, match="quarantined"):
        BenchmarkSpec(
            slug="x", name="x", license="x", homepage="x", paper="x",
            files={"a.json": "http://example/a"},
            task_kind="retrieval", gold_form="document_set",
            quarantine=("nonexistent.json",),
        )


def test_registry_check_reports_an_unfetched_dataset() -> None:
    """The check that found hotpotqa's silently-empty manifest entry."""
    problems = check_registry({"multihop_rag": {"files": {"corpus.json": {}}}})
    assert any("never fetched" in p for p in problems)
    assert any("missing file" in p for p in problems)


# ── Adapter ───────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not RAW.exists(), reason="multihop_rag not fetched")
def test_adapter_reproduces_the_documented_strata() -> None:
    """816 / 856 / 583 / 291 inference/comparison/temporal, 301 null, 2255 answerable."""
    from benchmarks.adapters.multihop_rag import MultiHopRagAdapter

    a = MultiHopRagAdapter()
    counts = a.stratum_counts()
    assert counts == {"inference": 816, "comparison": 856,
                      "temporal": 583, "null": 301}
    assert a.answerable_count() == 2255


@pytest.mark.skipif(not RAW.exists(), reason="multihop_rag not fetched")
def test_adapter_exposes_the_fact_strings_the_old_harness_discarded() -> None:
    """Span-level gold exists upstream; dropping it is why evidence_recall was NaN."""
    from benchmarks.adapters.multihop_rag import MultiHopRagAdapter

    a = MultiHopRagAdapter()
    answerable = [g for g in (a.gold(q.query_id) for q in a.queries()) if g.answerable]
    assert all(g.facts for g in answerable[:50]), "fact strings must survive"
    assert len(answerable[0].at("span")) == len(answerable[0].facts)


@pytest.mark.skipif(not RAW.exists(), reason="multihop_rag not fetched")
def test_adapter_uses_the_vault_document_id_namespace() -> None:
    """Corpus and gold must share the doc_#### ids used by source_docs."""
    from benchmarks.adapters.multihop_rag import MultiHopRagAdapter

    a = MultiHopRagAdapter()
    first = next(a.corpus())
    assert first.doc_id.startswith("doc_")
    evidence = next(g for g in (a.gold(q.query_id) for q in a.queries()) if g.answerable)
    assert all(doc_id.startswith("doc_") for doc_id in evidence.documents)


def test_span_gold_is_an_error_when_the_release_lacks_facts() -> None:
    g = Gold(query_id="q", documents=frozenset({"d1"}))
    assert g.at("document_set") == frozenset({"d1"})
    with pytest.raises(ValueError, match="no fact strings"):
        g.at("span")


def test_quarantine_check_fires_on_a_gold_file() -> None:
    class FakeAdapter:
        spec = REGISTRY["multihop_rag"]

    with pytest.raises(PermissionError, match="quarantined"):
        assert_quarantine_respected(
            FakeAdapter(), [Path("data/raw/multihop_rag/MultiHopRAG.json")]
        )


def test_quarantine_check_passes_on_the_corpus() -> None:
    class FakeAdapter:
        spec = REGISTRY["multihop_rag"]

    assert_quarantine_respected(
        FakeAdapter(), [Path("data/raw/multihop_rag/corpus.json")]
    )


# ── Run identity and comparability ────────────────────────────────────────────


def _man(**kw) -> RunManifest:
    base = dict(
        system="arm", arm_config={"subset": "full"}, metric_set=(),
        code=CodeProvenance(git_sha="abc", dirty=False),
        data=DataProvenance(benchmark="multihop_rag",
                            file_sha256={"corpus.json": "aa"},
                            gold_form="document_set"),
        env=EnvProvenance(python="3.12", platform="linux"),
        created_at="2026-09-14T00:00:00+00:00", schema_version=1,
    )
    base.update(kw)
    base["run_id"] = compute_run_id(
        base["system"], base["arm_config"], base["code"], base["data"]
    )
    return RunManifest(**base)


def test_run_id_is_stable_and_config_sensitive() -> None:
    """Same inputs collide on purpose; a config change must not."""
    a, b = _man(), _man()
    assert a.run_id == b.run_id
    c = _man(arm_config={"subset": "full", "k": 5})
    assert c.run_id != a.run_id


def test_comparability_refuses_differing_gold_form() -> None:
    """The 10x credit-inflation guard."""
    a = _man()
    b = _man(data=DataProvenance(benchmark="multihop_rag",
                                 file_sha256={"corpus.json": "aa"},
                                 gold_form="span"))
    ok, why = comparable(a, b)
    assert not ok and "gold_form" in why


def test_comparability_refuses_a_slice_against_the_full_corpus() -> None:
    a = _man()
    b = _man(arm_config={"subset": "slice_37doc"})
    ok, why = comparable(a, b)
    assert not ok and "subset" in why


def test_comparability_accepts_two_runs_in_one_cell() -> None:
    ok, why = comparable(_man(system="a"), _man(system="b"))
    assert ok, why


# ── Metric store ──────────────────────────────────────────────────────────────


def test_store_denormalises_the_guard_columns(tmp_path: Path) -> None:
    """gold_form and subset travel with every metric row, so a query cannot
    average across them by omission."""
    db = tmp_path / "m.db"
    rebuild(db=db, manifests=[])
    con = connect(db)
    cols = {r[1] for r in con.execute("PRAGMA table_info(metrics)")}
    assert {"gold_form", "subset", "benchmark", "system"} <= cols


def test_store_reports_registered_but_unmeasured_benchmarks(tmp_path: Path) -> None:
    """A report showing only what was measured makes the gap invisible."""
    from metrics.store import coverage_gaps

    db = tmp_path / "m.db"
    rebuild(db=db, manifests=[])
    gaps = {g["benchmark"] for g in coverage_gaps(connect(db))}
    assert gaps == set(REGISTRY), "with no runs, every benchmark is a gap"


# ── Dashboard ─────────────────────────────────────────────────────────────────


def test_families_are_four_and_never_cycled() -> None:
    """45 arms in one cell; hue encodes the family, identity comes from the label."""
    assert family_of("notes_bm25") == ("notes", 0)
    assert family_of("chunks-bm25") == ("chunks", 1)
    assert family_of("wholedoc-hybrid") == ("wholedoc", 2)
    assert family_of("deg4_ppr") == ("other", 7)
    assert family_of("union") == ("other", 7)
    slots = {family_of(s)[1] for s in
             ("notes_bm25", "chunks-bm25", "wholedoc-hybrid", "union")}
    assert len(slots) == 4


def test_dashboard_is_self_contained_and_carries_its_caveats(tmp_path: Path) -> None:
    db = tmp_path / "m.db"
    rebuild(db=db, manifests=[])
    h = build(connect(db))
    assert "http://" not in h and "https://" not in h
    assert "<script" not in h
    assert "±0.047" in h, "the noise-floor caveat must survive into the output"
    assert "never measured" in h, "coverage gaps must render"
