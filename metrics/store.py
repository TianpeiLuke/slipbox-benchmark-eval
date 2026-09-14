"""Centralized metric storage — a queryable index over every run.

Files on disk plus git remain the source of truth: one `manifest.json` and one
`metrics.json` per run, both committed. This is a **derived index** over them,
rebuilt from scratch on demand, so it can be deleted at any time without losing
anything. That is the same read/write split the vault itself uses, and for the
same reason: a projection that can be regenerated cannot drift into being a
second source of truth.

It exists because scanning 53-plus JSON trees to answer "which arms have a
budget-matched number on this benchmark, and how do they rank" is the kind of
question a report asks constantly and a filesystem answers badly.

The one rule the schema enforces rather than documents: `gold_form` and `subset`
travel with every metric row, so a query cannot silently average a document-level
number against a span-level one, or a 854-question slice against the full 2,255.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runs.registry import RunManifest, discover, run_dir  # noqa: E402

DEFAULT_DB = ROOT / "data" / "metrics.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id       TEXT PRIMARY KEY,
    benchmark    TEXT NOT NULL,
    subset       TEXT NOT NULL,
    system       TEXT NOT NULL,
    gold_form    TEXT NOT NULL,
    provenance   TEXT NOT NULL,   -- first_class | reconstructed
    git_sha      TEXT,
    dirty        INTEGER,
    created_at   TEXT,
    nondeterministic TEXT,        -- comma-joined; empty means replayable
    arm_config   TEXT             -- JSON
);

CREATE TABLE IF NOT EXISTS metrics (
    run_id     TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    metric     TEXT NOT NULL,
    value      REAL,
    -- Denormalised so a query cannot forget them. Averaging across differing
    -- gold_form or subset is the credit error this schema exists to block.
    benchmark  TEXT NOT NULL,
    subset     TEXT NOT NULL,
    gold_form  TEXT NOT NULL,
    system     TEXT NOT NULL,
    PRIMARY KEY (run_id, metric)
);

CREATE INDEX IF NOT EXISTS metrics_lookup
    ON metrics (benchmark, subset, gold_form, metric);
CREATE INDEX IF NOT EXISTS metrics_by_system ON metrics (system, metric);
"""


def connect(db: Path | None = None) -> sqlite3.Connection:
    con = sqlite3.connect(db or DEFAULT_DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def _load_metrics_for(m: RunManifest) -> dict[str, float]:
    """Prefer the harness-written metrics.json; fall back to legacy results."""
    direct = run_dir(m) / "metrics.json"
    if direct.exists():
        return {
            k: v for k, v in json.loads(direct.read_text()).items()
            if isinstance(v, (int, float))
        }
    legacy = m.arm_config.get("legacy_path")
    if not legacy or not (ROOT / legacy).exists():
        return {}
    payload = json.loads((ROOT / legacy).read_text())
    out: dict[str, float] = {}
    for strategy, block in (payload.get("strategies") or {}).items():
        for k, cell in (block.get("k") or {}).items():
            for name, key in (("recall", "recall"), ("all_recall", "all")):
                xs = cell.get(key) or []
                if xs:
                    out[f"{strategy}/{name}@k{k}"] = sum(xs) / len(xs)
        for b, cell in (block.get("budget") or {}).items():
            for name, key in (("recall", "recall"), ("all_recall", "all")):
                xs = cell.get(key) or []
                if xs:
                    out[f"{strategy}/{name}@b{b}"] = sum(xs) / len(xs)
    return out


def rebuild(db: Path | None = None, manifests: Iterable[RunManifest] | None = None) -> dict:
    """Rebuild the index from scratch. Idempotent and cheap.

    Deliberately destructive on its own tables: a derived index that is patched
    rather than rebuilt is how a projection drifts from its source.
    """
    con = connect(db)
    con.execute("DELETE FROM metrics")
    con.execute("DELETE FROM runs")
    mans = list(manifests) if manifests is not None else discover()
    n_metrics = 0
    for m in mans:
        subset = str(m.arm_config.get("subset", "unknown"))
        con.execute(
            "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                m.run_id, m.data.benchmark, subset, m.system, m.data.gold_form,
                m.provenance, m.code.git_sha, int(m.code.dirty), m.created_at,
                ",".join(m.env.nondeterministic_components),
                json.dumps(m.arm_config, sort_keys=True, default=str),
            ),
        )
        for metric, value in _load_metrics_for(m).items():
            con.execute(
                "INSERT OR REPLACE INTO metrics VALUES (?,?,?,?,?,?,?)",
                (m.run_id, metric, float(value), m.data.benchmark, subset,
                 m.data.gold_form, m.system),
            )
            n_metrics += 1
    con.commit()
    return {"runs": len(mans), "metrics": n_metrics, "db": str(db or DEFAULT_DB)}


# ── Queries the report and dashboard use ──────────────────────────────────────


def leaderboard(
    con: sqlite3.Connection, benchmark: str, metric: str,
    subset: str = "full", gold_form: str | None = None,
) -> list[sqlite3.Row]:
    """Systems ranked on one metric, within one comparable cell.

    benchmark + subset + gold_form together define the cell. Ranking across any
    of them would be the mistake the schema denormalises those columns to prevent.
    """
    sql = ("SELECT system, value, run_id FROM metrics "
           "WHERE benchmark=? AND subset=? AND metric=?")
    args: list = [benchmark, subset, metric]
    if gold_form:
        sql += " AND gold_form=?"
        args.append(gold_form)
    sql += " ORDER BY value DESC"
    return list(con.execute(sql, args))


def cells(con: sqlite3.Connection) -> list[sqlite3.Row]:
    """Every comparable cell present, with how many runs and metrics it holds."""
    return list(con.execute(
        "SELECT benchmark, subset, gold_form, COUNT(DISTINCT run_id) AS runs, "
        "COUNT(*) AS metrics FROM metrics "
        "GROUP BY benchmark, subset, gold_form ORDER BY benchmark, subset"
    ))


def metric_names(con: sqlite3.Connection, benchmark: str | None = None) -> list[str]:
    sql = "SELECT DISTINCT metric FROM metrics"
    args: list = []
    if benchmark:
        sql += " WHERE benchmark=?"
        args.append(benchmark)
    return [r["metric"] for r in con.execute(sql + " ORDER BY metric", args)]


def coverage_gaps(con: sqlite3.Connection) -> list[sqlite3.Row]:
    """Registered benchmarks with no runs at all.

    A report that only shows what was measured makes the unmeasured invisible.
    """
    from benchmarks.registry import REGISTRY

    have = {r["benchmark"] for r in con.execute("SELECT DISTINCT benchmark FROM runs")}
    return [{"benchmark": s, "runs": 0} for s in REGISTRY if s not in have]


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="metric store")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--cells", action="store_true")
    ap.add_argument("--leaderboard", nargs=2, metavar=("BENCHMARK", "METRIC"))
    ap.add_argument("--subset", default="full")
    a = ap.parse_args()

    if a.rebuild:
        print(json.dumps(rebuild(), indent=1))
        return
    con = connect()
    if a.cells:
        for r in cells(con):
            print(f"{r['benchmark']:<16}{r['subset']:<14}{r['gold_form']:<16}"
                  f"{r['runs']:>4} runs  {r['metrics']:>5} metrics")
        for g in coverage_gaps(con):
            print(f"{g['benchmark']:<16}{'—':<14}{'—':<16}   0 runs  (never measured)")
        return
    if a.leaderboard:
        bench, metric = a.leaderboard
        for i, r in enumerate(leaderboard(con, bench, metric, a.subset), 1):
            print(f"{i:>3}. {r['system']:<28} {r['value']:.4f}  {r['run_id']}")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
