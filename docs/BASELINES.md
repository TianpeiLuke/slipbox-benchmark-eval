# Published baselines reproduced in this repo

## HippoRAG (Gutierrez et al., NeurIPS 2024, arXiv:2405.14831)

A graph-based multi-hop retriever: an LLM builds a schemaless open KG over the
corpus, and retrieval is Personalized PageRank seeded at the query's entities.

**Run it**

```bash
# offline: LLM NER + OpenIE per passage, KG, synonym edges, membership matrix
python3 scripts/build_hipporag_index.py \
    --corpus data/chunks/multihop_rag --out experiments/runs11/hippo_slice \
    --restrict-docs experiments/runs11/slice_docs.json

# online: query NER -> node linking -> PPR -> passage scores
python3 scripts/score_hipporag.py \
    --corpus data/chunks/multihop_rag_slice \
    --hippo-index experiments/runs11/hippo_slice \
    --questions experiments/runs9/fair_questions.json \
    --strategies bm25 dense hybrid hipporag --ner llm
```

### Result on MultiHop-RAG (37-document slice, 996 passages, 300 questions)

| strategy | R@2 | R@5 | AR@2 | AR@5 |
|---|---|---|---|---|
| BM25 | **0.351** | **0.499** | **0.037** | **0.113** |
| hybrid | 0.320 | 0.484 | 0.020 | 0.107 |
| dense | 0.218 | 0.370 | 0.010 | 0.047 |
| HippoRAG (LLM NER) | 0.222 | 0.310 | 0.013 | 0.043 |
| HippoRAG (heuristic NER) | 0.200 | 0.312 | 0.007 | 0.040 |

Query NER runs through the cline CLI against `deepseek/deepseek-v4-flash`, which
needs no Anthropic key. All 300 calls succeeded, no fallbacks.

**HippoRAG loses to plain BM25 here. This is NOT a refutation of the paper**, and
the run should not be cited as one. It is a baseline implementation measured
under a degradation the paper does not have, on a corpus and question type it
was not evaluated for.

### Is the implementation broken? Four checks say no

This gap was challenged, correctly -- "the corpus is unfavourable" is the kind of
explanation that lets a bug hide. Four diagnostics:

**1. The graph is sound.** Every gold passage carries KG nodes (13.8 per passage;
1 of 996 passages is empty). Nothing is missing from the index.

**2. Entity linking is accurate.** Mean best-match cosine 0.947, with correct
targets (`TechCrunch` -> `techcrunch`, `Epic Games` -> `epic games`).

**3. Oracle seeding beats BM25.** Seeding PPR from nodes that actually occur in
the gold passages gives **R@5 0.536 against BM25's 0.499**. The KG, the
membership matrix, the specificity weighting, the PPR and the passage scoring
are all working -- given good seeds this implementation wins. The bottleneck is
entirely which nodes the query seeds.

**4. Better seeds do not close the gap, and the real LLM NER does not either.**
Four real query-NER bugs were found and fixed: "the" was stripped as a stopword
so `The Verge` became `Verge`; bare month names were emitted as entities;
possessives made `Google's` and `Google` distinct seeds; and dates were linked
by cosine, where MiniLM scores `October 26, 2023` against `october 6, 2023` at
0.967 -- close enough to seed the wrong day, now matched exactly or dropped. All
four fixes moved R@5 from 0.300 to 0.312.

**Then the paper's actual LLM query-NER was run**, via cline against DeepSeek,
closing the deviation that had been flagged as the one most likely to matter. It
lands at R@5 0.310 and R@2 0.222 -- indistinguishable from the heuristic on R@5,
slightly better on R@2. The LLM extracts better entities (it picks up lowercase
topical terms such as `cryptocurrency` that a capitalisation heuristic cannot
see) and it does not help, because the entities it adds are not the problem.

### Why it underperforms here: the seeds are hubs

The node passage-frequency distribution is extremely skewed: **median 1, p95 4,
max 378**. Almost every node is specific to one passage. But **47.9% of the
seeds a query produces land on nodes appearing in 20 or more passages.**

That is the whole story. HippoRAG assumes the query's named entities are
discriminative bridges between passages, which is what they are in Wikipedia
multi-hop. Here the named entities are *publishers and dates* -- `The Verge`,
`TechCrunch`, `October 26, 2023` -- which are bibliographic hubs shared by
hundreds of passages. PPR seeded at a hub diffuses mass across the corpus rather
than across a chain, and node specificity (1/|P_i|) down-weights exactly those
seeds toward zero, leaving the personalization vector with little signal.

So the method is being asked to traverse a bridge its graph does not encode. The
result is evidence about the corpus, not about HippoRAG.

### Evidence the implementation is behaving correctly

Hyperparameters respond as the paper predicts, which is the main check available
without reproducing their corpora:

| linking_top_k | R@5 | | damping | R@5 |
|---|---|---|---|---|
| **1** | **0.310** | | 0.1 | 0.269 |
| 3 | 0.310 | | 0.3 | 0.277 |
| 5 | 0.292 | | **0.5** | **0.292** |
| 10 | 0.269 | | 0.85 | 0.257 |

Damping 0.5 is the authors' default and wins. The KG's density also matches
theirs closely: 6,979 nodes over 996 passages (7.0 nodes/passage) against their
91,729 over 11,656 (7.9).

### Deviations remaining, worst first

1. **Encoder is all-MiniLM-L6-v2**, what the rest of this repo indexes with, not
   Contriever/ColBERTv2 (paper) or NV-Embed-v2 (current release). This degrades
   synonym-edge quality and query-node linking, and is now the largest open
   deviation.
2. **Extraction LLM is claude-haiku-4-5**, not GPT-3.5-turbo-1106.

**Closed:** query NER now uses a real LLM call (DeepSeek via cline), matching the
paper's design. It changed the result by roughly nothing.

### Why this corpus is unfavourable to the method, independent of the deviations

HippoRAG is evaluated on Wikipedia entity-bridge multi-hop (MuSiQue,
2WikiMultiHopQA), where the hop is an entity shared between passages — exactly
what an entity KG plus PPR is built to traverse. MultiHop-RAG's hop is not that.
Its questions ask whether two *named publishers* say consistent things about one
topic, on given dates; 98.9% of them name at least one of their own gold
publishers. The bridge is bibliographic, not entity-level, and a KG of noun
phrases has no edges along it.

That is the same conclusion the chain-retrieval work in this repo reached from
the other direction: on this benchmark the axis that matters is provenance, and
entity-anchored retrieval underperforms because it discards it. HippoRAG failing
here is consistent with that, and is evidence about the corpus rather than about
the method.

### To finish the reproduction

1. ~~Re-run with `--ner llm`.~~ Done: R@5 0.310, no material change.
2. Swap in a stronger encoder for node linking and synonymy -- now the largest
   remaining deviation.
3. Run it on MuSiQue or 2WikiMultiHopQA, where the paper's numbers exist, to
   check the implementation against a published figure rather than against our
   own baselines. This is the check that would settle the reproduction, and
   unrun designs for those benchmarks already sit in the vault.
