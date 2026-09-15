import json

import pyarrow as pa
import pyarrow.parquet as pq

from benchmarks.adapters.twowiki import TwoWikiAdapter


def _write_release(path):
    rows = [
        {
            "_id": "q0",
            "question": "Where does Alpha lead?",
            "type": "compositional",
            "context": json.dumps([
                ["Alpha", ["Alpha is a city.", "Alpha hosts Beta."]],
                ["Beta", ["Beta is a river."]],
            ]),
            "supporting_facts": json.dumps([["Alpha", 1], ["Beta", 0]]),
            "evidences": json.dumps([]),
            "answer": "Beta",
        },
        {
            "_id": "q1",
            "question": "What is shared?",
            "type": "comparison",
            "context": json.dumps([
                ["Alpha", ["Alpha is a city.", "Alpha hosts Beta."]],
                ["Gamma", ["Gamma is a lake."]],
            ]),
            "supporting_facts": json.dumps([["Gamma", 0]]),
            "evidences": json.dumps([]),
            "answer": "nothing",
        },
    ]
    pq.write_table(pa.Table.from_pylist(rows), path / "dev.parquet")


def test_twowiki_decodes_pools_and_preserves_fact_granularity(tmp_path):
    _write_release(tmp_path)
    adapter = TwoWikiAdapter(tmp_path, subsample=2)

    passages = list(adapter.corpus())
    assert [p.doc_id for p in passages] == ["Alpha", "Beta", "Gamma"]
    assert passages[0].text == "Alpha is a city. Alpha hosts Beta."
    assert adapter.gold("q0").documents == frozenset({"Alpha", "Beta"})
    assert adapter.gold("q0").facts == ("Alpha#1", "Beta#0")
    assert adapter.stratum_counts() == {"compositional": 1, "comparison": 1}
    assert adapter.answerable_count() == 2
    assert adapter.files_read() == (tmp_path / "dev.parquet",)


def test_twowiki_subsample_is_deterministic_and_zero_is_empty(tmp_path):
    _write_release(tmp_path)
    assert [q.query_id for q in TwoWikiAdapter(tmp_path, subsample=1).queries()] == ["q0"]
    assert list(TwoWikiAdapter(tmp_path, subsample=0).queries()) == []
    assert [q.query_id for q in TwoWikiAdapter(tmp_path, subsample=None).queries()] == ["q0", "q1"]
