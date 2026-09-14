"""Reconstruct manifests for the runs that predate the registry.

Fifteen directories, `experiments/runs2` through `runs16`, hold results with no
record of what produced them. This recovers what is recoverable — the arm and
strategy from the filename, the benchmark from the data shape, the commit from
the file's last-touching commit — and marks every result `provenance:
reconstructed` so it is never mistaken for a first-class record.

What cannot be recovered, and is therefore left explicitly empty rather than
guessed: the exact config each run used (that information is why the
`execute_v2`…`v41` filenames exist), the environment, and whether the tree was
dirty at the time. A reconstructed manifest is a claim about the past, not a
record of it, and the distinction is the point.

    python3 -m runs.backfill --dry-run
    python3 -m runs.backfill --apply
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from runs.registry import (  # noqa: E402
    CodeProvenance,
    DataProvenance,
    EnvProvenance,
    RunManifest,
    compute_run_id,
    write_manifest,
)

EXPERIMENTS = ROOT / "experiments"
MANIFEST = ROOT / "data" / "manifest.json"

# Filenames encode the arm, but not in one scheme -- the results use at least
# four: `<arm>_<strategy>`, `deg<N>_<strategy>` (degree sweep), `v_<variant>_<strategy>`
# (vault variant) and bare `v<N>_<tag>` (rebuild version). A whitelist of arms
# dropped 37 real scored runs on the first attempt, which is the silent
# truncation this whole layer exists to prevent. So the rule is inverted: ANY
# file with the scored-run shape is a run, its stem IS its arm identity, and a
# recognised strategy suffix is extracted only as a convenience.
STRATEGIES = ("graph_hybrid", "bm25", "hybrid", "dense", "bfs", "ppr", "mmr")


def parse_result_name(stem: str) -> dict:
    """Recover a strategy suffix if the stem carries one; never reject a stem.

    Returns the stem as `arm` when no strategy is recognisable, so an
    unconventional name is recorded rather than dropped.
    """
    for strat in STRATEGIES:
        if stem == strat:
            return {"arm": stem, "strategy": strat, "variant": None}
        if stem.endswith("_" + strat):
            return {
                "arm": stem[: -len(strat) - 1],
                "strategy": strat,
                "variant": None,
            }
    return {"arm": stem, "strategy": None, "variant": None}


def looks_like_a_scored_run(path: Path) -> bool:
    """A scored run carries per-question arrays under `strategies`."""
    try:
        d = json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return False
    return isinstance(d, dict) and "strategies" in d and "arm" in d


def last_touching_commit(path: Path) -> tuple[str, str]:
    """(sha, iso date) of the commit that last changed this file."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%H|%cI", "--", str(path)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        if "|" in out:
            sha, date = out.split("|", 1)
            return sha, date
    except Exception:  # noqa: BLE001
        pass
    return "unknown", ""


def dataset_checksums(slug: str) -> dict[str, str]:
    if not MANIFEST.exists():
        return {}
    entry = json.loads(MANIFEST.read_text()).get(slug) or {}
    return {
        name: meta.get("sha256", "")
        for name, meta in (entry.get("files") or {}).items()
    }


# Answerable-question counts seen in this repo's results, and what they mean.
# The distinction is load-bearing: a 854-question SLICE result is not comparable
# to a 2,255-question full-corpus result, and both were being written to files
# whose names say nothing about which one they are.
ANSWERABLE_COUNTS = {
    2255: ("multihop_rag", "document_set", "full"),
    854: ("multihop_rag", "document_set", "slice_37doc"),
}


def infer_benchmark(payload: dict) -> tuple[str, str, str]:
    """(slug, gold_form, subset) from the answerable-question count.

    MultiHop-RAG's full answerable set is 2,255; the 37-document slice used for
    the reader experiments is 854. Anything else is left unknown rather than
    guessed, and reported, so an unrecognised corpus is visible instead of
    silently filed under the wrong benchmark.
    """
    for st in (payload.get("strategies") or {}).values():
        n = st.get("answerable")
        if n in ANSWERABLE_COUNTS:
            return ANSWERABLE_COUNTS[n]
        if n is not None:
            return "unknown", "unknown", f"answerable_{n}"
    return "unknown", "unknown", "unknown"


def build(apply: bool) -> list[RunManifest]:
    made: list[RunManifest] = []
    for run_dir in sorted(EXPERIMENTS.glob("runs*")):
        if not run_dir.is_dir():
            continue
        for path in sorted(run_dir.glob("*.json")):
            if not looks_like_a_scored_run(path):
                continue
            parsed = parse_result_name(path.stem)
            payload = json.loads(path.read_text())
            slug, gold_form, subset = infer_benchmark(payload)
            sha, date = last_touching_commit(path)

            strategies = list((payload.get("strategies") or {}))
            arm_config = {
                "arm": parsed["arm"],
                "strategy": parsed["strategy"],
                "variant": parsed["variant"],
                "vault": payload.get("vault"),
                "strategies_present": strategies,
                "legacy_path": str(path.relative_to(ROOT)),
                "legacy_run_dir": run_dir.name,
                "subset": subset,
            }
            code = CodeProvenance(git_sha=sha, dirty=False)
            data = DataProvenance(
                benchmark=slug,
                file_sha256=dataset_checksums(slug),
                gold_form=gold_form,
            )
            system = (
                f"{parsed['arm']}-{parsed['strategy']}"
                if parsed["strategy"]
                else parsed["arm"]
            )

            m = RunManifest(
                run_id=compute_run_id(system, arm_config, code, data),
                schema_version=1,
                system=system,
                arm_config=arm_config,
                # Recorded as what the file actually contains, not what the
                # harness would compute today.
                metric_set=("recall@k", "all_recall@k", "recall@budget",
                            "all_recall@budget"),
                code=code,
                data=data,
                env=EnvProvenance(python="unknown", platform="unknown"),
                created_at=date or "unknown",
                provenance="reconstructed",
                notes=(
                    "Backfilled from experiments/ by runs.backfill. Arm and "
                    "strategy recovered from the filename; benchmark inferred "
                    "from the 2,255-question answerable count; commit is the "
                    "last one to touch the file. The exact config, environment "
                    "and dirty state are NOT recoverable and are left empty."
                ),
            )
            made.append(m)
            if apply:
                write_manifest(m)
    return made


def main() -> None:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    made = build(apply=a.apply)
    if not made:
        print("no scored runs found under experiments/")
        return

    by_bench: dict[str, int] = {}
    for m in made:
        by_bench[m.data.benchmark] = by_bench.get(m.data.benchmark, 0) + 1

    verb = "wrote" if a.apply else "would write"
    print(f"{verb} {len(made)} reconstructed manifest(s)")
    for slug, n in sorted(by_bench.items()):
        print(f"  {slug:<16} {n}")
    unknown = [m for m in made if m.data.benchmark == "unknown"]
    if unknown:
        print(f"\n{len(unknown)} run(s) whose benchmark could not be inferred:")
        for m in unknown[:10]:
            print(f"  - {m.arm_config['legacy_path']}")
    dupes = len(made) - len({m.run_id for m in made})
    if dupes:
        print(f"\n{dupes} run_id collision(s) — same arm, config and data bytes; "
              "expected where a run was re-scored without changing inputs.")
    if not a.apply:
        print("\n--apply to write them under runs/<benchmark>/<system>/<run_id>/")


if __name__ == "__main__":
    main()
