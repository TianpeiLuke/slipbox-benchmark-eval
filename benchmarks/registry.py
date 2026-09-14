"""The benchmark registry — one typed record per dataset.

This generalises the `SOURCES` dict that lived in `scripts/fetch_benchmarks.py`.
That dict already did the important things right: keyed by slug, carrying licence
and paper, downloading to a gitignored tree, and writing a *committed* manifest of
URLs and checksums so a fetch is reproducible without redistributing data. The
fetcher still works exactly as before and imports from here.

What is added are the fields that make a dataset **usable** rather than merely
downloadable, each of which exists because of a specific mistake this project has
already made:

`gold_form`
    The granularity the ground truth is defined at. This is load-bearing, not
    documentation. Measured on this corpus, document-level credit inflated a
    note arm about ten times more than a chunk arm, so a scorer that does not
    know the gold granularity silently produces a flattering number. Recording
    it lets the reporting layer refuse to compare a `document_set` result
    against a `span` result.

`strata`
    Question subsets that must be reported separately. Pooling MultiHop-RAG's
    four query types hides that the null queries are where an abstaining system
    should win outright.

`published_baselines`
    Cited numbers *with their protocol*. A dataset with no baseline produces a
    free-floating number, and the prior-art audit found ten of this project's
    findings had already been published — several with much larger effects.

`quarantine`
    Which files an ingesting system may not read. Today this is an honour-system
    prose `note`; making it a list lets `check_quarantine` enforce it. The first
    budget experiment here was superseded entirely because its questions had been
    generated from the notes under test.

Adding a benchmark should be one record here plus one adapter. It currently costs
three to five new scripts, which is the thing this package exists to end.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

TaskKind = Literal[
    "retrieval",       # ranked list of unit ids
    "qa",              # generated answer text
    "classification",  # categorical or multi-label
    "af_solving",      # abstract-argumentation labelling (ICCMA)
    "memory",          # multi-session / continual
]

GoldForm = Literal[
    "document_set",     # a set of source document ids  <- inflates paraphrase units
    "passage",          # a specific passage id in the authors' segmentation
    "span",             # verbatim character span in a source document
    "label",            # a categorical value
    "free_text",        # reference answer string(s)
    "graph_labelling",  # per-argument in/out/undec
]


@dataclass(frozen=True)
class Baseline:
    """One published number, with enough protocol to make it comparable."""

    system: str
    metric: str
    value: str
    protocol: str
    citation: str


@dataclass(frozen=True)
class BenchmarkSpec:
    slug: str
    name: str
    license: str
    homepage: str
    paper: str
    files: Mapping[str, str]

    task_kind: TaskKind
    gold_form: GoldForm

    strata: tuple[str, ...] = ()
    published_baselines: tuple[Baseline, ...] = ()
    quarantine: tuple[str, ...] = ()
    note: str = ""

    def __post_init__(self) -> None:
        if not self.files:
            raise ValueError(f"{self.slug}: no files to fetch")
        for q in self.quarantine:
            if q not in self.files:
                raise ValueError(
                    f"{self.slug}: quarantined file {q!r} is not in files"
                )


# ── The registry ──────────────────────────────────────────────────────────────

REGISTRY: dict[str, BenchmarkSpec] = {}


def register(spec: BenchmarkSpec) -> BenchmarkSpec:
    if spec.slug in REGISTRY:
        raise ValueError(f"duplicate slug {spec.slug!r}")
    REGISTRY[spec.slug] = spec
    return spec


# PRIMARY. Chosen because its document sizes land where the note-writing pipeline
# actually operates, and because corpus and queries ship as SEPARATE files --
# quarantine is a matter of not reading one of them, rather than of de-duplicating
# questions out of the corpus.
register(BenchmarkSpec(
    slug="multihop_rag",
    name="MultiHop-RAG (news, 609 docs / 2,556 queries)",
    license="ODC-BY-1.0",
    homepage="https://github.com/yixuantt/MultiHop-RAG",
    paper="Tang & Yang, 2024, arXiv:2401.15391",
    files={
        "corpus.json":
            "https://huggingface.co/datasets/yixuantt/MultiHopRAG/resolve/main/corpus.json",
        "MultiHopRAG.json":
            "https://huggingface.co/datasets/yixuantt/MultiHopRAG/resolve/main/MultiHopRAG.json",
    },
    task_kind="retrieval",
    # The authors' gold names a source document AND the exact fact sentence, but
    # the widely-used harness keeps only the document set. Recorded as the weaker
    # of the two, because that is what a naive scorer will award.
    gold_form="document_set",
    strata=("inference", "comparison", "temporal", "null"),
    published_baselines=(
        Baseline("bge-large-en-v1.5, no reranker", "MRR@10", "0.4298",
                 "retrieval only, authors' chunk segmentation", "arXiv:2401.15391"),
        Baseline("bge-large-en-v1.5, no reranker", "Hits@10", "0.6718",
                 "retrieval only", "arXiv:2401.15391"),
        Baseline("GPT-4 + retrieved chunks", "accuracy", "0.56",
                 "generation stage", "arXiv:2401.15391"),
        Baseline("GPT-4 + ground-truth chunks", "accuracy", "0.89",
                 "generation ceiling", "arXiv:2401.15391"),
        Baseline("GraphRAG (Community-Global)", "accuracy", "13.95",
                 "NULL queries only, Llama-3.1-70B unified protocol",
                 "arXiv:2502.11371"),
    ),
    quarantine=("MultiHopRAG.json",),
    note="corpus.json is the ONLY file an ingesting agent may read. "
         "MultiHopRAG.json holds the questions and their gold evidence.",
))

register(BenchmarkSpec(
    slug="musique",
    name="MuSiQue (answerable)",
    license="CC BY 4.0",
    homepage="https://github.com/StonyBrookNLP/musique",
    paper="Trivedi et al., TACL 2022, arXiv:2108.00573",
    files={
        "musique_ans_v1.0_dev.jsonl":
            "https://huggingface.co/datasets/dgslibisey/MuSiQue/resolve/main/musique_ans_v1.0_dev.jsonl",
    },
    task_kind="retrieval",
    gold_form="passage",
    published_baselines=(
        Baseline("HippoRAG", "R@5", "see paper",
                 "1,000-query / 11,656-passage split", "arXiv:2405.14831"),
    ),
    note="Questions and paragraphs are in the SAME file; quarantine here means "
         "reading only the paragraph field, which the adapter must enforce.",
))

register(BenchmarkSpec(
    slug="2wiki",
    name="2WikiMultiHopQA",
    license="Apache-2.0",
    homepage="https://github.com/Alab-NII/2wikimultihop",
    paper="Ho et al., COLING 2020",
    files={
        "dev.parquet":
            "https://huggingface.co/datasets/xanhho/2WikiMultihopQA/resolve/main/dev.parquet",
    },
    task_kind="retrieval",
    gold_form="passage",
    published_baselines=(
        Baseline("HippoRAG", "R@5", "0.900",
                 "entity-bridge corpus; PPR over an extracted KG",
                 "arXiv:2405.14831"),
        Baseline("BM25", "R@5", "0.669",
                 "same subsample; stronger than the paper's own BM25",
                 "measured in this repo, runs5"),
    ),
    note="Entity-bridge structure: the hop entity is often NOT named in the "
         "query, which is where a graph pays. The opposite of MultiHop-RAG.",
))

register(BenchmarkSpec(
    slug="hotpotqa",
    name="HotpotQA (distractor dev)",
    license="CC BY-SA 4.0  (share-alike -- derived notes inherit this)",
    homepage="https://hotpotqa.github.io/",
    paper="Yang et al., EMNLP 2018, arXiv:1809.09600",
    files={
        "validation-00000-of-00001.parquet":
            "https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/distractor/validation-00000-of-00001.parquet",
    },
    task_kind="retrieval",
    gold_form="passage",
    note="2-hop only, so a weaker signal than MuSiQue for multi-hop claims. "
         "Share-alike propagates to any derived note vault.",
))

register(BenchmarkSpec(
    slug="narrativeqa",
    name="NarrativeQA",
    license="Apache-2.0 (annotations); source texts have their own terms",
    homepage="https://github.com/google-deepmind/narrativeqa",
    paper="Kocisky et al., TACL 2018, arXiv:1712.07040",
    files={
        "test-00000-of-00008.parquet":
            "https://huggingface.co/datasets/deepmind/narrativeqa/resolve/main/data/test-00000-of-00008.parquet",
    },
    task_kind="qa",
    gold_form="free_text",
    note="Full novel texts are NOT redistributed; fetch via the upstream script "
         "if needed. Registered but never fetched -- see check_registry().",
))

# The one non-QA benchmark, registered deliberately: it proves the interface is
# not QA-shaped. Gold is a per-argument labelling, there are no questions, and
# the scorer is exact agreement rather than recall.
register(BenchmarkSpec(
    slug="iccma2023",
    name="ICCMA 2023 abstract-argumentation instances",
    license="see Zenodo record (competition instances)",
    homepage="https://iccma2023.github.io",
    paper="Jarvisalo, Lehtonen & Niskanen, Arg&App 2023, CEUR Vol-3472",
    files={
        # Zenodo 10.5281/zenodo.8348039. Verified against the record's file
        # listing: iccma2023_benchmarks.zip is 851.8 MB (the sibling
        # iccma2023_results.zip, 448.4 MB, holds the solver outputs and is only
        # needed to compare PAR-2 against the competing solvers).
        "iccma2023_benchmarks.zip":
            "https://zenodo.org/records/8348039/files/iccma2023_benchmarks.zip",
    },
    task_kind="af_solving",
    gold_form="graph_labelling",
    published_baselines=(
        Baseline("mu-toksia (glucose)", "PAR-2", "143.56",
                 "DC-CO track, 1200s timeout counted 2x", "zenodo.8348039"),
        Baseline("Crustabri", "PAR-2", "172.92", "DC-CO track", "zenodo.8348039"),
    ),
    note="NO grounded track since 2019 -- DS-CO and SE-CO are excluded from ICCMA "
         "precisely because they ARE grounded and considered poly-time trivial. "
         "Score grounded via that equivalence, or use the 2015/2017/2019 editions "
         "which had native GR tracks.",
))


# ── Integrity ─────────────────────────────────────────────────────────────────


def check_registry(manifest: Mapping[str, object]) -> list[str]:
    """Problems where the registry and a fetch manifest disagree.

    Exists because `data/manifest.json` recorded four of five registered
    datasets -- `narrativeqa` was never fetched, so the manifest silently
    under-reported the registry and nothing noticed. Returns human-readable
    lines; empty means consistent.
    """
    problems: list[str] = []
    for slug, spec in REGISTRY.items():
        if slug not in manifest:
            problems.append(
                f"{slug}: registered but absent from the manifest (never fetched)"
            )
            continue
        entry = manifest[slug]
        got = set((entry or {}).get("files", {})) if isinstance(entry, dict) else set()
        missing = set(spec.files) - got
        if missing:
            problems.append(
                f"{slug}: manifest missing file(s) {sorted(missing)}"
            )
    for slug in manifest:
        if slug not in REGISTRY:
            problems.append(f"{slug}: in the manifest but no longer registered")
    return problems


# Back-compat: the shape `scripts/fetch_benchmarks.py` consumed before the split.
# Kept so the fetcher and any ad-hoc caller keep working unchanged.
SOURCES: dict[str, dict] = {
    slug: {
        "name": s.name,
        "license": s.license,
        "homepage": s.homepage,
        "paper": s.paper,
        "files": dict(s.files),
        **({"note": s.note} if s.note else {}),
    }
    for slug, s in REGISTRY.items()
}
