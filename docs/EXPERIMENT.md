# Experiment design: do typed atomic notes retrieve better than chunks?

The pre-registered design for the run this repo exists to perform. **It has not
been run.** Everything else here — 5,093 notes, both index halves, five
retrieval arms, a measured chunk baseline — exists to make it possible.

> **Supersedes** the vault note *Context-Budget Renormalization*
> (`archives/experiments/experiment_context_budget_renormalization.md`), whose
> hypotheses and pass conditions carry over intact. What does not carry over is
> its subject: that design scored against 4,823 questions generated **from the
> notes under test**. This one scores against 2,556 questions written by other
> people, which is the difference between measuring a vault and measuring
> yourself. See §6 for the full list of what changed and why.

---

## 1. The question

Does converting a document corpus into typed atomic notes with a link graph
retrieve better than chunking the raw documents — and if so, **because of what**?

"Better" is not obvious to define here, so it is defined operationally in §4.
The mechanism question is the harder half, and §2 is arranged so the three
hypotheses can fail independently.

## 2. Hypotheses

**H1 — budget interaction.** Notes retrieve gold evidence more completely than
chunks at matched token budget, and the advantage **decreases monotonically in
budget**, largest at 512–2,048 tokens. It is stronger on questions needing
several documents, because atomic units let an assembler pack several distinct
gold items where a chunk spends the budget on one.

**H2 — the graph adds reach.** Graph-expanded retrieval over notes (`bfs`,
`ppr`) beats plain note retrieval (`bm25`, `hybrid`) specifically on
multi-document questions — the case where a second gold document is reachable
by a link but not by the query terms.

**H3 — redistribution, not brevity.** Any small-budget advantage exists because
notes front-load. Isolated by truncating every retrieved unit to its first T
tokens before assembly: if notes front-load and articles bury their
conclusions, note recall degrades far more slowly in T.

**The separation is the design.** H1 could hold merely because notes are shorter
— a packing effect. H3 discriminates: truncation removes tail content only, so
an arm whose answer sits early is advantaged by construction. If notes win H1
but degrade under truncation as fast as chunks do, the advantage is packing
rather than position, and the front-loading claim must be withdrawn.

## 3. Arms

| Arm | What a retrieval unit is | Command |
|---|---|---|
| `notes` × {bm25, dense, hybrid} | one typed note | `score_retrieval.py --arm notes --strategies …` |
| `notes` × {bfs, ppr} | a note, plus graph expansion | same, `--seed hybrid` |
| `chunks` × {bm25, dense, hybrid} | a fixed window of source text | `--arm chunks` |
| `handwritten` | a note written by hand to the same contract | `--vault vaults/multihop_rag_handwritten` |

The fourth arm is the one that makes the result interpretable. Notes-vs-chunks
answers "does the format help". Notes-vs-handwritten holds the **format fixed
and varies only the method**, separating *the format helps* from *the pipeline
produces the format well*. Without it, a win is ambiguous between the two.

Chunks carry their document title, deliberately. Withholding it would handicap
the baseline on exactly the entity terms these questions turn on, and a win over
a crippled opponent is not a result.

## 4. Metrics

**Recall@k** — the fraction of a question's gold documents in the top k.
**All-Recall@k** — 1 only if *every* gold document is there, else 0.

Both, because they answer different questions. A multi-hop question is
answerable only when all its evidence is present, so All-Recall tracks whether
retrieval could have supported an answer at all; Recall shows partial progress
and keeps a run readable when All-Recall is near zero. The measured baseline
already shows the gap: **Recall@10 0.699 against All-Recall@10 0.419**.

Credit is assigned at **document level**, through each note's own `source_docs`.
A note abstracting several documents can therefore satisfy several pieces of
gold evidence at once — the property under test, and one a chunk-level metric
cannot see.

The 301 `null_query` items carry no evidence and are **excluded** from recall
rather than scored as zero, which would depress every arm identically and
flatter none.

## 5. Two rules that decide whether the comparison means anything

**Match on token budget, never on k.** Matching *k* hands the win to whichever
representation has larger units: 5 chunks of 200 words is not 5 notes of 328.
Every comparison assembles until a token budget is exhausted.

**Sweep the chunk size.** It is a free parameter that moves the baseline
substantially — `--sweep` spans 14,177 chunks at 100 words to 1,772 at 800. A
single setting proves nothing; report the best chunk configuration, not a
convenient one.

The budget range is chosen from the corpus rather than assumed: **100%** of
documents exceed 512 and 1,024 tokens, **36.9%** still exceed 2,048, and the
pressure is gone by 8,192. A comparison run only at a large budget cannot show
a slope, and H1 is a claim about a slope.

## 6. Pre-registered pass conditions

Written before the run, so the result cannot be read backwards into whichever
hypothesis it happens to fit.

| | Passes if |
|---|---|
| **H1** | the note-minus-chunk Recall gap at 512 tokens exceeds the gap at 8,192, 95% paired-bootstrap interval excluding zero; and the multi-document gap exceeds the single-document gap |
| **H2** | the best graph arm beats the best plain note arm on multi-document questions, interval excluding zero; equal performance **falsifies** H2 — the graph is not free, and an arm that adds nothing should be reported as adding nothing |
| **H3** | note recall at T=100 retains ≥80% of its untruncated value while chunk recall retains <50% |

Report paired bootstrap intervals over questions, and test H1's interaction
directly — fit recall against log-budget per arm and compare **slopes** — rather
than eyeballing two curves.

## 7. Known threats to validity

**H3 has no valid metric yet.** Its first pass returned a null, and the null was
uninformative: bag-of-words recall is **order-invariant by construction**, so it
cannot detect a position effect at all. H3 cannot be run until an order-sensitive
measure exists. Recorded here rather than quietly dropped.

**The comparison is not content-matched.** Notes carry ~1.15× the words of their
sources and were written by a different process, so a win could reflect better
*content* rather than better *form*. The handwritten arm bounds this partially;
the full control is reformatting raw text into note shape while discarding
nothing.

**Publisher chrome is a third route to winning.** Across 49 publishers, notes
drop newsletter promotion, section headers and bylines that chunks retain. That
is neither packing nor position, and the current design does not separate it.
A chrome-stripped chunk arm is the missing control.

**Recall is answerability, not an answer.** It measures whether gold reached the
window, not whether a model then answered correctly. Deliberate — it isolates
retrieval from generation — but a win here is necessary, not sufficient.

**16 questions cite evidence with no matching corpus document**, so their recall
is unreachable by construction. The scorer reports this rather than absorbing it.

## 8. How to run

```bash
python3 scripts/build_local_db.py       vaults/multihop_rag --with-embeddings
python3 scripts/build_chunk_baseline.py multihop_rag --words 200 --overlap 50

python3 scripts/score_retrieval.py multihop_rag --arm chunks \
        --strategies bm25,hybrid --k 2,5,10 --json experiments/runs/chunks.json
python3 scripts/score_retrieval.py multihop_rag --arm notes --vault vaults/multihop_rag \
        --strategies bm25,hybrid,bfs,ppr --k 2,5,10 --json experiments/runs/notes.json
python3 scripts/score_retrieval.py multihop_rag --arm notes \
        --vault vaults/multihop_rag_handwritten \
        --strategies bm25,hybrid --k 2,5,10 --covered-only
```

`--covered-only` is required for the handwritten arm and forbidden for the
others: that vault holds 25 documents, and scoring it against questions whose
evidence it never contained measures how much corpus is present, not how well it
retrieves.

## 9. What changed from the superseded design

| Then | Now | Why |
|---|---|---|
| 4,823 questions generated from the notes | 2,556 written independently | the old set was circular: questions inherited the notes' vocabulary, so the notes won by construction |
| gold = note ids, chunks scored by token overlap | gold = documents, both arms scored identically | an overlap threshold is a judgement call that silently sets the result |
| one internal vault | MultiHop-RAG, 609 documents | document sizes land where the pipeline operates; corpus and questions ship as separate files, so quarantine is enforceable |
| `raw_fixed` / `raw_recursive` / `raw_whole` | one chunk arm, size swept | the three differed by a parameter better swept than named |
| lexical-only chunk arm | chunks get dense and hybrid too | the old note "understates a well-tuned RAG baseline" — it did, and that is fixed |
| — | handwritten control arm | separates the format from the pipeline that produces it |

## References

- [BACKGROUND.md](BACKGROUND.md) — the renormalization measurement that motivates this
- [HANDOFF.md](HANDOFF.md) — repo state and how to continue
- Superseded: `archives/experiments/experiment_context_budget_renormalization.md` in the source vault
