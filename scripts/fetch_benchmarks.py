#!/usr/bin/env python3
"""
Fetch public QA benchmark corpora. Nothing downloaded here is ever committed.

Datasets are chosen to match the evaluation protocol of HippoRAG and HippoRAG 2,
so our arm can be reported against their published baselines rather than
free-floating numbers:

  MuSiQue (answerable)   ~1,000 queries / 11,656 passages  compositional 2-4 hop
  2WikiMultiHopQA        ~1,000 queries /  6,119 passages  entity-centric multi-hop
  HotpotQA               ~1,000 queries /  9,221 passages  2-hop (weaker signal)
  NarrativeQA              293 queries /  4,111 passages   10 full novels

Metrics those papers report, which we mirror: Recall@2 / Recall@5, All-Recall@k
(fraction of queries where ALL gold passages are retrieved -- the multi-source
metric), and token-F1 for the answer stage.

Usage
-----
    python3 scripts/fetch_benchmarks.py --list
    python3 scripts/fetch_benchmarks.py musique 2wiki
    python3 scripts/fetch_benchmarks.py --all

Everything lands under data/raw/<slug>/ which is gitignored. A manifest with
URLs, licenses and checksums is written to data/manifest.json and IS committed,
so the fetch is reproducible without redistributing the data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "manifest.json"

# The registry moved to benchmarks/registry.py so a dataset is one typed record
# rather than a dict literal buried in a script. SOURCES is re-exported there for
# back-compat, so everything below is unchanged.
sys.path.insert(0, str(ROOT))
from benchmarks.registry import REGISTRY, SOURCES, check_registry  # noqa: E402


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(slug: str) -> dict:
    spec = SOURCES[slug]
    out = RAW / slug
    out.mkdir(parents=True, exist_ok=True)
    got = {}
    for fname, url in spec.get("files", {}).items():
        dest = out / fname
        if dest.exists():
            print(f"  [skip] {fname} already present")
        else:
            print(f"  [get ] {fname} <- {url}")
            try:
                urllib.request.urlretrieve(url, dest)
            except Exception as e:  # noqa: BLE001
                print(f"  [FAIL] {fname}: {e}")
                continue
        got[fname] = {"bytes": dest.stat().st_size, "sha256": sha256(dest)}
    if spec.get("note"):
        print(f"  [note] {spec['note']}")
    return {"name": spec["name"], "license": spec["license"],
            "homepage": spec["homepage"], "paper": spec["paper"], "files": got}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="report where the registry and the manifest disagree")
    a = ap.parse_args()

    if a.check:
        manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
        problems = check_registry(manifest)
        if not problems:
            print(f"registry and manifest agree ({len(SOURCES)} dataset(s))")
            return
        print(f"{len(problems)} inconsistency(ies):")
        for line in problems:
            print(f"  - {line}")
        sys.exit(1)

    if a.list or (not a.slugs and not a.all):
        print(f"{'slug':<14}{'task':<15}{'gold form':<17}{'name'}")
        for slug, spec in REGISTRY.items():
            print(f"{slug:<14}{spec.task_kind:<15}{spec.gold_form:<17}{spec.name}")
        print()
        print("gold form governs comparability: a document_set result must not be")
        print("compared against a span result -- document-level credit inflated a")
        print("note arm ~10x more than a chunk arm on this corpus.")
        print("\nNothing under data/raw/ is ever committed (see .gitignore).")
        print("Derived notes inherit their corpus license (see LICENSE).")
        return

    slugs = list(SOURCES) if a.all else a.slugs
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    for s in slugs:
        if s not in SOURCES:
            print(f"unknown slug {s!r}; use --list")
            sys.exit(2)
        print(f"\n=== {SOURCES[s]['name']} ({SOURCES[s]['license']}) ===")
        manifest[s] = fetch(s)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"\nmanifest -> {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
