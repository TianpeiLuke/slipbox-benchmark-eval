# The v2 pipeline, end to end

Stages, what each produces, and how to resume. Every stage checkpoints, so a
kill costs one item rather than the run.

```
corpus + question file
   │
   ├─ select pilot slice ──────────► experiments/plans/pilot_v2_docs.json
   │
   ├─ plan_v2.py ─────────────────► experiments/plans/v2/plan.jsonl
   │     thought-atomic decomposition: one thought per note, per-block
   │     definition of what one thought is, target weight, split test
   │
   ├─ execute_v2.py ──────────────► vaults/v2_pilot/*.md
   │     one agent per note; brief carries one-thought, target weight,
   │     self-sufficiency, data-verbatim, no-padding
   │
   ├─ build_local_db.py --with-embeddings ──► notes.db + embeddings.npy
   │     scaffolding excluded from BOTH the FTS text and the encoded text
   │
   └─ score_retrieval.py / compare_runs.py ─► experiments/runs*/  vs frozen v1
```

## Resuming any stage

All three generative stages skip work already on disk. Re-run the identical
command; nothing is regenerated.

| stage | checkpoint | resume by |
|---|---|---|
| plan_v2 | one JSONL line per document | re-run, it reads `plan.jsonl` |
| execute_v2 | one `.md` per note | re-run, it stats each target path |
| gen_anticipated_questions | one JSONL line per unit | re-run, it reads the out file |

## Failure handling

All generative stages route through `llm_call.py`, which classifies a call as
**transport** (the model never ran — retry), **format** (ran, wrong shape —
retry or repair) or **content** (ran, produced nothing usable — record and move
on), and retries only what retrying can fix.

They report failures **by kind**, never as a total. `29 failed` sends you to
rewrite a prompt that was never the problem; `24 transport, 4 format, 1 content`
tells you to fix the retry.

`answer_eval.py` and `answer_from_contexts.py` carry their own equivalent retry,
written before `llm_call` existed. Consolidating them is worthwhile and has not
been done.


## Retrieval strategy: cap results per source document

`perdoc` (and `perdoc1`, the cap=1 form) takes units in rank order but allows at
most N from any one source document. **It is the largest single retrieval gain
measured in this repo** and it helps every vault, not only fine-grained ones:

| vault | plain hybrid | capped (1/doc) |
|---|---|---|
| coarse notes | 0.841 | **0.937** |
| atomic notes | 0.634 | **0.852** |

**Why it works.** Multi-hop questions require 2 to 4 distinct documents by
construction, 64.8% of them across publishers, so provenance is the axis the
questions vary on. Plain top-k ignores it: on an atom vault a top-10 returned
4.80 distinct documents against a coarse vault's 6.88, and on one query returned
ten units from a single article.

**Why MMR does not substitute.** MMR diversifies by semantic novelty and moved
document counts to 5.64 while gold recall did not change at all — the documents
it added were different without being needed. Diversity has an axis and it must
be the one the task varies on.

**This is not fitting the benchmark.** Using the gold labels to steer retrieval
would be; using the known structure of a multi-hop task is ordinary system
design. The metric counts documents because the task needs documents, not the
reverse. An earlier version of this repo declined to add the strategy on that
confusion and reached the wrong conclusion about atomic notes as a result.

**Every result in `runs` through `runs6` used plain retrieval** and is therefore
understated. Relative orderings within a run are probably safe since all arms
shared the defect; absolute numbers are not.

## Controls

- **v1 baseline** is frozen at tag `vault-v1-baseline`, with a checksummed
  working copy at `vaults/v1_baseline/`. Do not edit it; a control that drifts
  is not a control.
- **Score both arms on the same question set, pinned explicitly.** Pass
  `--questions experiments/plans/v2_scorable_questions.json` to both arms.
  **Do not use `--covered-only` for a comparison**: it computes its set PER
  VAULT, so a full vault and a slice get different question sets *and* different
  haystacks, and the smaller haystack retrieves better for a reason that has
  nothing to do with note quality. This was set up wrongly once in this repo —
  v1 at 609 documents and 5,093 notes against v2 at 37 documents and 728 —
  before being caught.
- **Match the haystack, not only the questions.** When one arm covers a subset of
  documents, build the other arm's matching slice (`vaults/v1_slice`) rather than
  scoring the full vault against it. Equal question sets over unequal corpora is
  still not a comparison.
- **Attribute bundled changes.** When a variant carries two interventions, build
  the intermediate arm before looking at the numbers. Comparing v1 to
  scaffolding-plus-expansion credits expansion with a gain scaffolding produced.
