# What a run saves, and why each piece exists

Every run writes one directory:

```
runs/<benchmark>/<system>/<run_id>/
  manifest.json       ~2 KB    committed    provenance
  metrics.json        ~1 KB    committed    aggregate numbers
  per_question.json  ~100 KB   committed    per-item scores
  predictions.jsonl    ~3 MB   gitignored   what was retrieved
  log.txt              varies  gitignored   stdout/stderr
```

`run_id` is a content hash of the provenance block, not a timestamp — so the same
code, config and data always land in the same directory, and a changed input always
lands in a new one. That is why arms no longer need version suffixes in filenames
(`execute_v2` … `execute_v41` existed because there was nowhere else to record which
config a run used).

## The four files

### `manifest.json` — who made this number

Answers "can I trust and reproduce this?" without opening anything else.

- **code**: git sha **and a dirty flag**. A result from a dirty tree is not
  reproducible, and recording that is the difference between a result and an
  anecdote.
- **data**: benchmark slug, per-file SHA-256 from the fetch manifest, and
  `gold_form` — the credit granularity actually scored.
- **env**: python, platform, and `nondeterministic_components`. Not a footnote: the
  sentence encoder in this stack returns different vectors for the same sentence
  encoded alone versus in a batch, and the result moves with thread count. If
  something like that sat in the decision path, the run is not replayable and the
  manifest says so.
- **arm_config**: everything that distinguishes this arm, including `subset` and
  `gold_form_scored`.
- **provenance**: `first_class` (written by the harness) or `reconstructed`
  (backfilled from git history — a claim about the past, not a record of it).

### `metrics.json` — the aggregate numbers

Means only: `recall@k2/5/10`, `all_recall@…`, `mrr`, `hits`, `map`,
`recall@b2048/4096/8192`, per-stratum recall, and the abstention block
(`abstain_precision/recall/f1`, `correct_abstentions`, …).

**This file cannot support a comparison on its own.** A mean has no variance, so any
claim built only on `metrics.json` is a point difference with no interval — which on
this corpus is not evidence, because build-to-build variance from the stochastic
writer alone is ±0.047 pooled.

### `per_question.json` — the file that makes a run reanalysable

```json
{"qids": ["mhr-00000", ...], "scores": {"recall@b2048": [1.0, 0.667, ...], ...}}
```

One float per question per metric, aligned with `qids`.

**Committed deliberately, and it was nearly lost.** The first version of the harness
wrote only aggregates. That would have made the project's own headline correction
impossible to find: the discovery that the note layer *ties* chunking rather than
losing to it came from a paired bootstrap over per-item series, and those series only
existed because the legacy result files happened to keep them. A design that mandates
paired intervals while discarding the data needed to compute them is self-defeating,
so this file is first-class.

It is also what makes runs *re-scorable*. A new metric can be computed over an old
run's per-question series without re-executing the arm.

Cost: ~100 KB per run, ~5 MB across all 53 backfilled runs. Cheap for what it buys.

Read it through the bootstrap module rather than by hand:

```python
from metrics.bootstrap import compare_runs
from runs.registry import discover

runs = {m.system: m for m in discover()}
print(compare_runs(runs["notes-bm25"], runs["chunks-bm25"],
                   metrics=["recall@b2048"]))
```

It refuses the comparison outright if `gold_form` or `subset` differ, or if the two
runs scored different question sets — a paired test needs the same items aligned, and
silently zipping mismatched sets is how a wrong interval gets published.

### `predictions.jsonl` — what was actually retrieved

One line per query: `query_id`, `stratum`, `answerable`, and the ranked `units`.

**Gitignored**, at ~3 MB per run. This is the file for failure analysis — *why* a
query scored what it did, which unit was returned instead of the right one. It is
regenerable by re-running the arm at the manifest's pinned inputs, which is the
trade being made: reproducible rather than archived.

## What is deliberately not saved

- **The built index or vault.** Large, and reconstructable from the corpus plus the
  manifest's config. If an arm's index is not reconstructable, that is a defect in
  the arm, not a gap here.
- **Retrieved passage text.** `predictions.jsonl` keeps unit ids; the text is a join
  away through the corpus.
- **Generated answers.** There is no answer stage in the runner yet. When one lands
  it gets its own file (`answers.jsonl`) rather than being folded into metrics,
  because generated text needs its own review path.

## Commit policy

Committed: `manifest.json`, `metrics.json`, `per_question.json`. Together these make
a run **citable, comparable and reanalysable** off-machine, at roughly 100 KB each.

Gitignored: `predictions.jsonl`, `log.txt`, and `data/metrics.db` (a derived index,
rebuilt with `python3 -m metrics.store --rebuild`).

The line is drawn at reanalysis. Anything needed to recompute a number or an interval
is committed; anything needed only to debug a single query is regenerable.

The current full-vault Tessellum BM25 run is recorded under
`runs/multihop_rag/tessellum-bm25-full-vault/e1456c4b4da70303/`. It scores all
2,556 questions against the prepared 5,093-note vault using the document-set
provenance map. The vault itself remains an external input, so the manifest pins
its path and the benchmark file hashes; reproducing the run still requires the
Tessellum checkout and prepared vault.

The result is intentionally a lexical arm. It does not establish that the full
Tessellum semantic layer or DKS improves retrieval: dense/hybrid retrieval,
graph expansion, span-level provenance, and answer generation need independent
arms and paired comparisons.
