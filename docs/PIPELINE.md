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
