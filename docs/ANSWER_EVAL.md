# Answer evaluation: does the retrieved context let a model answer?

This is H7, pre-registered in FZ 8c5b11a13a5g1b5e and unrun until now. Everything
before it scores **retrieval**. This scores **answering**.

## Why it is needed, specifically

The fact-level run (FZ 5h) left the central comparison unresolved, and not for
want of care. Scoring a note against a gold evidence sentence needs a similarity
threshold, and the verdict flips with it:

| θ | All-Fact@10 notes | All-Fact@10 chunks |
|---|---|---|
| 0.55 | **0.680** | 0.580 |
| 0.65 | **0.393** | 0.333 |
| 0.75 | 0.180 | **0.213** |

A loose threshold says a rephrasing still carries the fact and notes win; a strict
one says only near-verbatim counts and chunks win. No control can adjudicate,
because the calibration set (a fact against its own document) validates *verbatim*
detection and there is no labelled set of "this note correctly rephrases this
fact". The question "does the rephrasing still answer it" is not answerable by
string similarity at all — it is answerable by asking a model to answer.

The same run also showed that 18.3% of gold facts are not recoverable from any
note at θ=0.65, against 0.9% for chunks. If that loss is real the notes arm should
lose on answers; if it is an artefact of paraphrase detection, it should not. That
is a sharp, falsifiable prediction and this pipeline tests it.

## Metric

Gold answers in MultiHop-RAG are short factual strings — a name, a number, a date,
yes/no — so deterministic string metrics are appropriate and reproducible. An
LLM judge is deliberately avoided: it would add a second model's bias to a
comparison that is already about model behaviour, and it is not needed for spans
this short. (If F1 proves too brittle on entity variants, a judge is the fallback,
and that change must be declared before it is run.)

**On the 2,255 answerable questions**

| | definition |
|---|---|
| `EM` | exact match after lowercasing and stripping punctuation and articles |
| `F1` | SQuAD-style token overlap between answer and gold — **the primary metric**, because a model may name the same entity differently |
| `contains` | the normalised gold string appears in the answer; lenient, catches a right answer inside a verbose one |
| `over_refusal` | model replied INSUFFICIENT to a question that does have an answer |

**On the 301 null questions**

| | definition |
|---|---|
| `abstained_on_null` | model correctly declined |

The null queries matter more than their share suggests. They exist to test
hallucination, **no experiment in this series has ever used them**, and they
measure something recall cannot see: a system that confidently answers an
unanswerable question is worse than one that scores lower on retrieval. Reporting
`over_refusal` alongside is what stops abstention being gamed — a model that
refuses everything scores 1.0 on nulls and 0 on F1.

## Conditions

The series' central finding is that **what is scarce decides the winner** — notes
lead by +0.167 Recall@10 at matched slots and trail by −0.042 at 2,048 tokens. So
answering is measured under both, and a result that only holds in one must be
reported that way.

- `--condition slots --k 10` — top k units, whatever they cost
- `--condition tokens --budget 2048` — units in rank order until the budget fills,
  skipping any single unit that would overrun

Token counts are real (tiktoken `cl100k_base`) and **evidence-only**: Related
Notes and Source are stripped before counting and before the model sees them,
per the correction in FZ 5d1. Chunks have no such sections, so the rule cannot
flatter either arm.

## Pipeline

```
question -> hybrid retrieval over the arm's index
         -> assemble context in rank order under the condition
         -> prompt: context + question + "answer with the shortest span,
                    or reply exactly INSUFFICIENT"
         -> score EM / F1 / contains, or abstention for null queries
```

The prompt forbids explanation and demands the shortest answering span, because
F1 against a short gold string punishes verbosity and that would confound answer
quality with output style.

## Backends

| backend | requirement |
|---|---|
| `openai` | `OPENAI_API_KEY`; any chat model, default `gpt-5-nano` |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `cline` | the Cline CLI — see below |

### Cline CLI

```bash
npm i -g cline          # not currently installed on this machine
cline auth              # INTERACTIVE — pick provider, paste key. Cannot be scripted.
```

Once authenticated, the pipeline calls it headlessly:

```bash
cline --json --auto-approve true -m <model> "<prompt>"
```

`--json` emits newline-delimited JSON; the parser concatenates `text` fields and
skips `reasoning`, so a reasoning model's scratchpad does not leak into the
scored answer. Verify the model id with a one-off call before a full run — a
wrong `-m` silently falls back to the configured default and the run would be
mislabelled.

## Running it

```bash
# smoke test first, always
python3 scripts/answer_eval.py multihop_rag \
    --arms notes=vaults/multihop_rag chunks=data/chunks/multihop_rag \
    --backend openai --model gpt-5-nano \
    --condition tokens --budget 2048 --sample 10 --nulls 5

# full run, both conditions
for c in tokens slots; do
  python3 scripts/answer_eval.py multihop_rag \
      --arms notes=vaults/multihop_rag chunks=data/chunks/multihop_rag \
      --backend cline --model <qwen-model-id> \
      --condition $c --budget 2048 --k 10 --sample 400 --nulls 100 \
      --json experiments/runs5/answers_$c.json
done
```

## Cost and scale

Each question costs one call **per arm**, so a run is `2 x (sample + nulls)`
calls. The full 2,255 answerable plus 301 null questions is 5,112 calls per
condition — cheap on a small local model, not free on a hosted one. Start at
`--sample 200 --nulls 50` (500 calls), which is enough to see a difference of
about 0.06 in F1, and scale only if the interval straddles zero.

## Known limitations of this design

- **One model tells you about one model.** A cheap model may fail to use context
  a strong one would exploit, and that failure would look like a retrieval
  difference. Any headline claim should be replicated on a second model tier
  before it is trusted.
- **No bootstrap intervals yet.** The runner reports means; pairing by question
  id across arms and bootstrapping is the obvious next step, and the per-question
  records are kept so it can be added without re-running.
- **Retrieval is fixed to hybrid.** The graph arms are not tested here, on the
  grounds that FZ 5f already showed every graph arm is worse at retrieval.
- **Gold answers are read by the scorer.** This is the first part of the series to
  use the `answer` field. The vault was built blind to it and is frozen, so this
  cannot contaminate the notes — but no note-writing or tuning may follow from
  these results without rebuilding.
