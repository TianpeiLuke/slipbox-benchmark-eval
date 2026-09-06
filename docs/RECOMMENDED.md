# What Works — the settings that survived measurement

Every row here was measured in this repo and every row that did not survive is
listed too, because knowing what to stop doing is most of the value. Nothing is
adopted on argument; the last column says what settled it.

## Build side

| Setting | Effect | Status | Settled by |
|---|---|---|---|
| Strip scaffolding (`## Related Notes`, `Source`, `References`) from indexed and encoded text | **+0.072 All-Recall@2048**, free | **adopt, now default** | index-side fixes |
| Split notes to one thought per note ("thought-atomic") | loses at every unit count at a small budget | **do not adopt** | v2 rebuild pilot |
| doc2query / question expansion | near-null | drop | index-side fixes |
| Contextualised chunks (Anthropic-style prefix) | falsifier failed | drop | index-side fixes |

**The atomicity caveat that matters.** Atoms lose at a 2,048-token budget and
nearly catch up at 16,384 (chain completeness 0.890 against coarse 0.970, doc
recall 0.983 against 0.980). Fine-grained units are not worse in general; they
are worse when starved. Do not conclude against them from small-budget runs.

## Retrieval side

| Strategy | Effect | Status |
|---|---|---|
| `perdoc1` — at most one unit per source document | +0.052 / +0.056 on a 37-doc slice; **does not replicate on the full 609-doc corpus** (-0.021 ns on notes, +0.029 ns on chunks) | **adopt only for small haystacks** |
| `logical` — strip named sources, rank on the predicate, quota per named source | chain completeness 0.190 -> 0.220 | keep, corpus-specific |
| `hybrid` — BM25 + dense via RRF | the baseline everything is measured against | keep as default |
| `mmr` — semantic-novelty diversity | moved document counts, moved recall by nothing | do not use for this |
| `chain` / `chain1` — decompose into entity anchors | **halves chain completeness** | **do not use** |
| `gapfill` — re-query on uncovered question terms | a wash | not worth the cost |
| `bfs` / `ppr` over derived edges | negative on this corpus | do not use here |

**Why entity decomposition fails, since it looks reasonable.** A multi-hop
question asks about a *relation*; probing "Apple" and "Google" separately returns
units about each entity and discards the relation, which is the question. The
whole-query embedding already encodes the conjunction. A question may be
decomposed, but not along a seam that dissolves what it asks. Only the SOURCE
axis proved safe.

## Notes against chunks, full corpus, matched haystack

The head-to-head both systems were built for, 609 documents each, 600 answerable
questions plus 100 nulls, all fixes applied.

| arm | entity | polarity | macro |
|---|---|---|---|
| notes hybrid | 0.624 | 0.165 | 0.394 |
| notes capped | 0.603 | 0.170 | 0.387 |
| chunks hybrid | 0.698 | 0.106 | 0.402 |
| chunks capped | **0.727** | 0.084 | 0.406 |
| closed book | 0.000 | 0.000 | 0.000 |
| majority | 0.302 | 0.578 | 0.440 |

**Overall it is a tie** -- pooled across strata the notes-minus-chunks difference
is +0.005 and +0.002, neither significant. Underneath the tie the two systems
are good at opposite things, both significantly: notes lose on entity extraction
(-0.074, -0.124) and win on the yes/no comparison and temporal questions
(+0.059, +0.087).

That is the honest state of the claim. An optimised note layer **matches**
chunking on this benchmark; it does not beat it. Where it is ahead is the
question type that needs several sources reconciled, which is what a note layer
is for, and where it is behind is verbatim span extraction, which is what
chunks preserve and summarisation discards.

**Capping does not generalise.** Its gain was measured on a 37-document slice and
does not survive on the full corpus in either system. A cap that forces breadth
helps when the haystack is small enough that breadth is cheap; with 609
documents the units it displaces cost more than the diversity buys.

## The lever that beats every strategy

| Budget | coarse notes | atomic notes |
|---|---|---|
| 2,048 | 0.220 | 0.095 |
| 8,192 | 0.835 | 0.515 |
| 16,384 | **0.970** | **0.890** |

Chain completeness. The best strategy moved it by 0.03; eight times the budget
moved it by 0.75. Since refusal collapses to 4-8% once the chain is complete and
the model is right ~99% of the time when it answers, **spend context before
spending cleverness.**

## Measurement discipline — the part that changed conclusions most

1. **Pin questions to a coverage-fair set.** The vaults did not cover the same
   corpus (178 source documents against 37), so cross-vault results were
   confounded with coverage. Use `--questions`, and match the haystack.
2. **Stratify by gold class.** Two thirds of answerable questions are yes/no,
   the model declines 87.6% of them, and every arm scores below a constant
   "Yes". Pooling that with the entity stratum hides both.
3. **Always print baselines.** A closed-book arm and a per-stratum majority arm,
   in the same table. An arm that cannot beat closed-book has shown nothing.
4. **`temperature=0`.** Otherwise arm differences of 0.01-0.03 are sampled noise.
5. **Persist failed calls.** They used to be dropped, so a degraded run looked
   like a smaller clean one.
6. **Scale the candidate pool with the budget.** A fixed pool is not neutral
   between unit sizes: 40 atoms carry a quarter the text of 40 coarse notes, and
   the atom arm saturated on the harness rather than on its own limits.
7. **Report fact-level alongside document-level, and when they disagree resolve
   it downstream.** Capping was adopted on document recall, withdrawn on fact
   recall, and vindicated on answer accuracy. Two of those three verdicts were
   reached by argument, and both were wrong.

## Known-good command

```bash
python3 scripts/dump_contexts.py multihop_rag --vault vaults/<v> \
    --strategy perdoc1 --condition tokens --budget 2048 \
    --questions experiments/runs9/fair_questions.json --sample 854 --nulls 100 \
    --out ctx.jsonl
python3 scripts/answer_from_contexts.py ctx.jsonl \
    --backend anthropic --model claude-haiku-4-5-20251001 --out ans.jsonl
python3 scripts/score_answers.py --arms a=ans.jsonl --pairs ...
```

`tests/test_known_good.py` pins the invariants above so they cannot regress
silently.
