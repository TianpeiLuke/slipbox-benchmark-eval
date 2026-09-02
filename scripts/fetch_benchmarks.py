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

# license is recorded because derived notes inherit it -- see LICENSE
SOURCES: dict[str, dict] = {
    # PRIMARY. Chosen because its document sizes land where our note-writing
    # pipeline actually operates, and because corpus and queries ship as
    # SEPARATE files -- quarantine is a matter of not reading one of them,
    # rather than of de-duplicating questions out of the corpus.
    "multihop_rag": {
        "name": "MultiHop-RAG (news, 609 docs / 2,556 queries)",
        "license": "ODC-BY-1.0",
        "homepage": "https://github.com/yixuantt/MultiHop-RAG",
        "paper": "Tang & Yang, 2024, arXiv:2401.15391",
        "files": {
            "corpus.json":
                "https://huggingface.co/datasets/yixuantt/MultiHopRAG/resolve/main/corpus.json",
            "MultiHopRAG.json":
                "https://huggingface.co/datasets/yixuantt/MultiHopRAG/resolve/main/MultiHopRAG.json",
        },
        "note": "corpus.json is the ONLY file an ingesting agent may read. "
                "MultiHopRAG.json holds the questions and their gold evidence.",
    },
    "musique": {
        "name": "MuSiQue (answerable)",
        "license": "CC BY 4.0",
        "homepage": "https://github.com/StonyBrookNLP/musique",
        "paper": "Trivedi et al., TACL 2022, arXiv:2108.00573",
        "files": {
            "musique_ans_v1.0_dev.jsonl":
                "https://huggingface.co/datasets/dgslibisey/MuSiQue/resolve/main/musique_ans_v1.0_dev.jsonl",
        },
    },
    "2wiki": {
        "name": "2WikiMultiHopQA",
        "license": "Apache-2.0",
        "homepage": "https://github.com/Alab-NII/2wikimultihop",
        "paper": "Ho et al., COLING 2020",
        "files": {
            "dev.parquet":
                "https://huggingface.co/datasets/xanhho/2WikiMultihopQA/resolve/main/dev.parquet",
        },
    },
    "hotpotqa": {
        "name": "HotpotQA (distractor dev)",
        "license": "CC BY-SA 4.0  (share-alike -- derived notes inherit this)",
        "homepage": "https://hotpotqa.github.io/",
        "paper": "Yang et al., EMNLP 2018, arXiv:1809.09600",
        "files": {
            "validation-00000-of-00001.parquet":
                "https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/distractor/validation-00000-of-00001.parquet",
        },
    },
    "narrativeqa": {
        "name": "NarrativeQA",
        "license": "Apache-2.0 (annotations); source texts have their own terms",
        "homepage": "https://github.com/google-deepmind/narrativeqa",
        "paper": "Kocisky et al., TACL 2018, arXiv:1712.07040",
        "files": {
            "test-00000-of-00008.parquet":
                "https://huggingface.co/datasets/deepmind/narrativeqa/resolve/main/data/test-00000-of-00008.parquet",
        },
        "note": "Full novel texts are NOT redistributed; fetch via the upstream script if needed.",
    },
}


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
    a = ap.parse_args()

    if a.list or (not a.slugs and not a.all):
        print(f"{'slug':<14}{'license':<42}{'name'}")
        for s, v in SOURCES.items():
            print(f"{s:<14}{v['license']:<42}{v['name']}")
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
