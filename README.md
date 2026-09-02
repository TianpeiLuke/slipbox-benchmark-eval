# slipbox-benchmark-eval

Does converting a document corpus into **typed atomic notes with a link graph** retrieve better than chunking the raw documents — and if so, *why*?

This repo holds the corpus-ingestion skill, the fetch scripts, the derived note vaults, and the evaluation harness for answering that on **public benchmarks with externally authored questions**.

## Why this exists

A knowledge vault can be evaluated against questions generated *from its own notes*. That measurement is circular: the questions inherit the notes' vocabulary, so the notes win by construction and the number means nothing. Every claim here is therefore made against benchmarks whose questions were written by other people, from source corpora we ingest but never author.

The ingestion pipeline under test does something more specific than "summarisation". Measured on a paired corpus elsewhere, it **renormalises rather than compresses**: three source length distributions with coefficients of variation 0.89 / 1.39 / 1.06 mapped onto notes at 0.33 / 0.33 / 0.18, while the total word count *grew* 1.15x, with a fan-out of 0.7–2.7 notes per source document. So the question is not whether a shorter representation beats a longer one. It is whether a **uniformly shaped, atomised, linked** representation beats a heterogeneous one at equal token budget.

## Hypotheses

**H1 — budget interaction.** The note advantage over chunked raw documents is largest at *small* context budgets and shrinks as the budget grows, and is stronger on questions needing several sources.

**H2 — graph plus notes beats chunk RAG.** Hybrid lexical-plus-dense retrieval over typed atomic notes, expanded one hop over typed links, beats fixed-window, recursive and whole-document chunking at **matched token budget** — never matched *k*, since matching on *k* hands the win to whichever representation has larger units.

**H3 — mechanism.** Any small-budget advantage is tested for *cause*: an order-only ablation separates front-loading from mere brevity.

> **Status:** H3's first pass returned a **null**, and the null was informative — a bag-of-words recall metric is order-invariant by construction, so it cannot detect position effects at all. That test is being rebuilt with an order-sensitive measure. Recorded here rather than quietly dropped.

## Benchmarks

Chosen to match the evaluation protocol of HippoRAG and HippoRAG 2, so results can be reported against published baselines instead of standing alone.

| Dataset | Queries | Passages | Category | License |
|---|---|---|---|---|
| MuSiQue (answerable) | ~1,000 | 11,656 | compositional 2–4 hop | CC BY 4.0 |
| 2WikiMultiHopQA | ~1,000 | 6,119 | entity-centric multi-hop | Apache-2.0 |
| HotpotQA (distractor) | ~1,000 | 9,221 | 2-hop, *weaker signal* | CC BY-SA 4.0 |
| NarrativeQA | 293 | 4,111 | sense-making, 10 novels | Apache-2.0 (annotations) |

Published baselines to situate against: BM25, Contriever, GTR, ColBERTv2, NV-Embed-v2, **Propositionizer** (the closest existing analogue to atomic notes), RAPTOR, GraphRAG, LightRAG, HippoRAG, HippoRAG 2.

Metrics mirror those papers: **Recall@2 / Recall@5**, **All-Recall@k** (fraction of queries where *all* gold passages are retrieved — the multi-source metric), and token-F1 for the answer stage. All retrieval metrics are computable without an LLM judge.

## Layout

```
scripts/fetch_benchmarks.py   download corpora (never committed)
scripts/build_local_db.py     lexical half: FTS5 + link graph, per vault
scripts/build_embeddings.py   dense half: sentence embeddings, per vault
scripts/retrieval.py          bm25 / dense / hybrid / bfs / ppr
scripts/scrub_check.py        publication gate for derived notes
scripts/selftest.sh           end-to-end check on a tiny committed fixture
skills/                       the corpus-ingestion skill
tests/fixture_vault/          4-note fixture; no downloads needed
data/manifest.json            URLs, licenses, checksums (committed)
data/raw/                     corpora (gitignored)
vaults/<corpus>/              derived notes (committed) + indexes (rebuilt)
experiments/                  harness and results
```

## Retrieval

Five strategies over a vault's own hybrid index. Nothing reads outside the repo.

| Strategy | What it does |
|---|---|
| `bm25` | FTS5 over title and body — the lexical baseline |
| `dense` | cosine over sentence embeddings (all-MiniLM-L6-v2, 384-dim) |
| `hybrid` | reciprocal-rank fusion of the two |
| `bfs` | hybrid seeds, best-first expansion over resolved links, hop-discounted |
| `ppr` | hybrid seeds as the teleport set, personalised PageRank (α=0.85) |

`bfs` and `ppr` are the **graph-based arm**. They exist to test whether a typed
link graph reaches gold evidence that similarity alone misses — the central
claim of graph RAG, and why multi-hop benchmarks are the right venue.

**Traversal follows only links that resolve inside the vault.** An unresolved
link points outside and is never followed, which is what keeps a corpus's
retrieval isolated from anything else on disk.

```bash
./scripts/selftest.sh     # builds, indexes, retrieves, scrubs — no downloads
```

On the committed 4-note fixture the query *"where is Alpha Protocol deployed"*
is answered in `gamma.md`, which shares no terms with the query, while
`beta.md` is the bridge between them. `ppr` ranks the bridge node **first**
where `bm25` misses it entirely — an illustration of the mechanism under test,
not evidence for it. The evidence has to come from the benchmarks.

## Isolation

**Every corpus gets its own database, its own link graph and its own full-text
index, inside this repository.** No script here reads or writes anything
outside it.

That is a correctness condition rather than housekeeping. A digestion pipeline
resolves "Related Notes" and inlinks against whatever vault it runs in, so a
corpus ingested against some other vault would carry that vault's links
outward — contaminating both the published notes and the evaluation. The link
builder therefore resolves links **only** within the corpus vault and reports
any link that escapes it as a contamination signal:

```bash
python3 scripts/build_local_db.py vaults/musique --stats
# links  4821  (4821 resolved in-vault, 0 unresolved/external)
```

A non-zero external count must be inspected before the vault is used.

## Data policy

**No third-party benchmark data is redistributed here.** `scripts/fetch_benchmarks.py` downloads corpora into a gitignored directory and records URLs, sizes, licenses and SHA-256 checksums in `data/manifest.json`, so the fetch is reproducible without republishing anyone's dataset.

The **derived notes are committed**, because they are the artifact under study. They are transformations of the source corpora and inherit their licenses — notably HotpotQA's **CC BY-SA 4.0 share-alike**. See `LICENSE` and the per-corpus `vaults/<corpus>/LICENSE.txt`.

## The rule that makes the results valid

**The ingesting agent never sees the benchmark's questions, answers, or gold labels.** Ingestion reads the document corpus only. Any leakage recreates the circularity this repo exists to escape, and would invalidate every number downstream. The quarantine is enforced procedurally in the skill and re-verified before a corpus is declared ready.

`scripts/scrub_check.py` is the second gate: it refuses to publish notes containing internal tokens, links escaping the repo, or missing provenance. Run it before committing anything under `vaults/`.

## Quick start

```bash
python3 scripts/fetch_benchmarks.py --list
python3 scripts/fetch_benchmarks.py musique 2wiki
# ingest with the skill, into an isolated vault, questions quarantined
python3 scripts/scrub_check.py vaults/musique     # must PASS before commit
```

## Honest limitations

- The ingestion pipeline was tuned on **technical documentation**. Wikipedia paragraphs and novels are different genres, and a genre mismatch is the leading threat to external validity. It is assessed and reported per corpus rather than assumed away.
- Benchmark gold labels are **passage**-level; our arm returns **notes**. The document-to-note provenance map is what makes the arm scorable, and it is emitted at ingestion time.
- Ingestion is not free: expect roughly 1–3 notes and ~1.15x the words per source document. The derived layer has to earn that cost back in retrieval, and may not.
