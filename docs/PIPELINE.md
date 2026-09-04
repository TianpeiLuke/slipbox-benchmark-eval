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


## Retrieval strategy: cap results per source document (SUPERSEDED — do not adopt)

`perdoc`/`perdoc1` allow at most N units from any one source document. It was
adopted here on a large document-level gain and then **withdrawn as a default**:
the gain does not survive fact-level scoring. Both directions are significant on
400 questions (`scripts/paired_strategy.py`, seed 20260902, 4000 resamples):

| vault | level | hybrid | capped | delta | 95% CI |
|---|---|---|---|---|---|
| coarse notes | doc | 0.509 | 0.548 | **+0.039** | [+0.021, +0.058] |
| coarse notes | **fact** | 0.405 | 0.384 | **-0.021** | [-0.037, -0.005] |
| atomic notes | doc | 0.331 | 0.427 | **+0.096** | [+0.079, +0.114] |
| atomic notes | **fact** | 0.291 | 0.255 | **-0.037** | [-0.054, -0.021] |

**Why the sign flips.** Document credit is generous: retrieving *any one* unit
from a gold document scores full credit for that document, whether or not that
unit carries the needed fact. Capping maximises exactly that quantity -- it
spends its budget collecting one unit from as many gold documents as possible --
and the unit it settles for is more often the wrong one. The gap between document
credit and fact credit widens under capping from +0.102 to +0.144 on coarse notes
and from +0.041 to +0.159 on atoms.

This is Goodhart, and it was self-inflicted. Document recall was introduced as a
*proxy* for having the facts. Optimising the proxy directly is what decoupled it
from the target, and the more aggressively it was optimised the further the two
came apart.

**The reasoning that justified adopting it was wrong in a specific way.** "The
task needs multiple documents, so diversifying by document is ordinary system
design" is true and still insufficient: needing a document is necessary, not
sufficient -- you need the *right part* of it. Arguing from the task's structure
to a retrieval rule skipped the step of checking the rule against the thing the
metric stands for.

**What still holds.** Capping really does increase document coverage; that part
was never a metric artifact. The coarse-over-atoms ordering also survives at
fact level (0.405 vs 0.291), so it does not depend on the defective strategy.
Keep `perdoc` as a diagnostic for measuring provenance concentration -- not as a
retrieval default.

**Standing rule.** Report fact-level alongside document-level for any change that
touches *which* units are selected rather than how they are ranked. A widening
doc-to-fact gap is the signature of this failure.

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
