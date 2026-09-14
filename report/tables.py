"""Cross-benchmark reporting, generated from the run registry.

`RESULTS.md` stays the human-facing artefact but becomes an output rather than a
hand-maintained file. Two rules are enforced here rather than remembered:

**Comparability is checked, not assumed.** `compare()` refuses a pair whose
`gold_form` or corpus subset differ. Comparing a document-level result against a
span-level one is the mistake that inflated a note arm about ten times more than
a chunk arm, and it is invisible once both are rendered as a column called
"recall". Same for a 854-question slice against the full 2,255.

**Reconstructed runs are marked in every table.** A backfilled manifest is a claim
about the past, not a record of it, and a reader must be able to see which is
which without opening the file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runs.registry import RunManifest, comparable, discover  # noqa: E402


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def load_metrics(m: RunManifest) -> dict:
    """Aggregate metrics for one run.

    Prefers a `metrics.json` written by the harness. Falls back to computing
    means from the legacy result file a reconstructed manifest points at, so the
    backfilled history is reportable without rewriting it.
    """
    from runs.registry import run_dir

    direct = run_dir(m) / "metrics.json"
    if direct.exists():
        return json.loads(direct.read_text())

    legacy = m.arm_config.get("legacy_path")
    if not legacy:
        return {}
    path = ROOT / legacy
    if not path.exists():
        return {}

    payload = json.loads(path.read_text())
    out: dict[str, float] = {}
    for strategy, block in (payload.get("strategies") or {}).items():
        for k, cell in (block.get("k") or {}).items():
            out[f"{strategy}/recall@k{k}"] = _mean(cell.get("recall", []))
            out[f"{strategy}/all_recall@k{k}"] = _mean(cell.get("all", []))
        for b, cell in (block.get("budget") or {}).items():
            out[f"{strategy}/recall@b{b}"] = _mean(cell.get("recall", []))
            out[f"{strategy}/all_recall@b{b}"] = _mean(cell.get("all", []))
    return out


def table(
    manifests: Iterable[RunManifest],
    metrics: Sequence[str],
) -> list[dict]:
    """One row per run, one column per requested metric."""
    rows = []
    for m in manifests:
        vals = load_metrics(m)
        row = {
            "benchmark": m.data.benchmark,
            "subset": m.arm_config.get("subset", "?"),
            "system": m.system,
            "gold_form": m.data.gold_form,
            "provenance": m.provenance,
            "run_id": m.run_id,
        }
        for name in metrics:
            row[name] = vals.get(name)
        rows.append(row)
    return rows


def render_markdown(rows: Sequence[Mapping], metrics: Sequence[str]) -> str:
    """A markdown table. Reconstructed rows carry a dagger."""
    head = ["system", "subset", *metrics]
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join(["---"] * len(head)) + "|"]
    for r in rows:
        mark = " †" if r.get("provenance") == "reconstructed" else ""
        cells = [f"`{r['system']}`{mark}", str(r.get("subset", "?"))]
        for name in metrics:
            v = r.get(name)
            cells.append("—" if v is None or v != v else f"{v:.3f}")
        out.append("| " + " | ".join(cells) + " |")
    if any(r.get("provenance") == "reconstructed" for r in rows):
        out.append("")
        out.append("† reconstructed from `experiments/` by `runs.backfill` — the "
                   "arm and benchmark were inferred, and the exact config, "
                   "environment and dirty state are not recoverable.")
    return "\n".join(out)


def compare(a: RunManifest, b: RunManifest, metrics: Sequence[str]) -> dict:
    """Paired comparison, refused when the two are not on one scale."""
    ok, why = comparable(a, b)
    if not ok:
        return {"comparable": False, "reason": why}
    va, vb = load_metrics(a), load_metrics(b)
    deltas = {}
    for name in metrics:
        x, y = va.get(name), vb.get(name)
        deltas[name] = None if x is None or y is None else y - x
    return {
        "comparable": True,
        "reason": why,
        "a": a.system,
        "b": b.system,
        "deltas": deltas,
        "caveat": (
            "Point deltas only. A single build cannot license an effect here: "
            "build-to-build variance from the stochastic writer alone was "
            "measured at ±0.047 pooled, so quote a paired bootstrap interval "
            "before claiming a difference."
        ),
    }


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="report from the run registry")
    ap.add_argument("--benchmark")
    ap.add_argument("--metrics", nargs="*", default=[
        "bm25/recall@b2048", "bm25/all_recall@b2048",
        "bm25/recall@k10", "bm25/all_recall@k10",
    ])
    ap.add_argument("--format", choices=("markdown", "json"), default="markdown")
    a = ap.parse_args()

    mans = discover()
    if a.benchmark:
        mans = [m for m in mans if m.data.benchmark == a.benchmark]
    if not mans:
        print("no runs found; try `python3 -m runs.backfill --apply`")
        return

    rows = table(mans, a.metrics)
    rows = [r for r in rows if any(r.get(k) is not None for k in a.metrics)]

    if a.format == "json":
        print(json.dumps(rows, indent=1))
        return

    by_subset: dict[str, list[dict]] = {}
    for r in rows:
        by_subset.setdefault(f"{r['benchmark']} · {r['subset']}", []).append(r)

    for key, group in sorted(by_subset.items()):
        print(f"\n### {key}\n")
        group.sort(key=lambda r: -(r.get(a.metrics[0]) or -1))
        print(render_markdown(group, a.metrics))
    print(f"\n{len(rows)} run(s) with at least one of the requested metrics; "
          f"{len(mans)} discovered.")


if __name__ == "__main__":
    main()
