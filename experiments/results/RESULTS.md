# MultiHop-RAG Results Summary

*Summary of the scoring runs in `experiments/runs2/`–`runs5/`, produced 2026-09-03.
All retrieval metrics are computed without an LLM judge; the answer stage uses the
`answer_eval` pipeline. Recall@budget = mean per-query passage recall; All-Recall =
share of queries where **all** gold passages were retrieved (the multi-source metric).
2,255 answerable questions for retrieval; 200 for the answer stage.*

## Headline

**On MultiHop-RAG, at matched token budget, the typed-atomic-note + link-graph
representation does not beat chunk RAG — for retrieval or for answering — and the
graph arm actively hurts.** The notes representation wins only when the comparison
is matched on *k* (number of units), which is the invalid comparison the project
was explicitly built to avoid. This is a clean negative result for the central
hypothesis (H2), and it is the number the repo exists to produce.

## The methodological crux: k vs. token budget

Paired bootstrap, `notes_bm25` − `chunks_bm25`, 2,255 shared questions (`compare_runs.py`); `*` = 95% CI excludes zero.

| Matched on | metric | chunks | notes | delta |
|---|---|--:|--:|--:|
| **k=10** | All-Recall | 0.360 | 0.666 | **+0.306** * |
| **k=10** | Recall | 0.668 | 0.857 | **+0.189** * |
| **budget=2048** | Recall | 0.732 | 0.577 | **−0.155** * |
| **budget=2048** | All-Recall | 0.451 | 0.248 | **−0.203** * |
| **budget=8192** | Recall | 0.921 | 0.850 | **−0.070** * |

Notes are smaller units, so at a fixed *k* they pack more gold passages and win by a
wide margin. At a fixed **token budget** — the fair comparison — chunks win at every
budget, all CIs excluding zero. *Never report the matched-k number as the result.*

## Arm comparison — token-budget matched (`runs2`, Recall / All-Recall)

| Arm · strategy | @2048 | @4096 | @8192 |
|---|--:|--:|--:|
| **chunks · bm25** | **0.732 / 0.451** | **0.844 / 0.633** | **0.921 / 0.798** |
| chunks · hybrid | 0.691 / 0.381 | 0.812 / 0.561 | 0.902 / 0.754 |
| notes · bm25 | 0.577 / 0.248 | 0.708 / 0.415 | 0.850 / 0.649 |
| notes · hybrid | 0.592 / 0.249 | 0.716 / 0.416 | 0.851 / 0.641 |
| wholedoc · bm25 | 0.241 / 0.001 | 0.413 / 0.113 | 0.626 / 0.325 |
| wholedoc · hybrid | 0.219 / 0.001 | 0.375 / 0.089 | 0.576 / 0.263 |

Chunks > notes > whole-document at every budget. Under **evidence-only** token
accounting (`runs3 *_evid`, charging only evidence tokens, not scaffolding),
notes·hybrid closes to a tie — **0.728 / 0.442 vs chunks 0.732 / 0.451 @2048** — but
still does not surpass chunks.

## Does the graph add anything? No — it subtracts. (`runs3` full-budget @2048)

| notes strategy | Recall / All-Recall @2048 |
|---|--:|
| hybrid | **0.516 / 0.174** |
| bm25 | 0.512 / 0.186 |
| graph_hybrid | 0.478 / 0.141 |
| bfs | 0.444 / 0.126 |
| ppr | 0.397 / 0.086 |
| keyword | 0.220 / 0.048 |

Every graph strategy (`bfs`, `ppr`, `graph_hybrid`) **underperforms** plain lexical/
dense retrieval on the same notes. The typed link graph does not reach gold evidence
that similarity misses — it moves probability mass onto weakly-related notes.

### Degree sweep — link density hurts (`runs4` @2048, Recall / All-Recall)

| degree | graph_hybrid | bfs | ppr |
|---|--:|--:|--:|
| **deg0 (no links)** | **0.718 / 0.413** | 0.568 / 0.231 | **0.658 / 0.325** |
| deg2 | 0.695 / 0.389 | 0.657 / 0.325 | 0.606 / 0.265 |
| deg4 | 0.693 / 0.372 | 0.657 / 0.324 | 0.614 / 0.272 |
| deg8 | 0.666 / 0.327 | 0.656 / 0.323 | 0.602 / 0.263 |
| degall | 0.653 / 0.313 | 0.656 / 0.324 | 0.596 / 0.254 |

For `graph_hybrid` and `ppr`, retrieval is **best with zero links and degrades
monotonically as edges are added**. Empirical confirmation of the project's own
"a weak edge is not a free edge" — link density has an optimum at ~0 here, not a maximum.

## Where notes do win, narrowly: fact-level consolidation (`runs4/fact_recall.json`)

| arm · match threshold | fact_recall@5 | all_fact@5 | share-all-facts |
|---|--:|--:|--:|
| **notes · 0.55** | **0.769** | **0.540** | **0.68** |
| chunks · 0.55 | 0.751 | 0.460 | 0.58 |
| notes · 0.65 | 0.554 | 0.247 | 0.393 |
| chunks · 0.65 | 0.545 | 0.220 | 0.333 |
| notes · 0.75 | 0.373 | 0.080 | 0.213 |
| chunks · 0.75 | 0.377 | 0.120 | 0.213 |

At **loose** fact matching (0.55) notes edge out chunks on fact recall and on
retrieving *all* of a question's facts (0.68 vs 0.58) — the consolidation advantage
appears at fact granularity even though it loses at passage granularity. The edge
shrinks and reverses at strict thresholds.

### But notes lose facts in the transformation (`runs4/fact_retention.json`)

| arm | retention @0.55 | @0.65 | @0.75 |
|---|--:|--:|--:|
| chunks | 0.998 | 0.991 | 0.963 |
| notes | 0.931 | 0.817 | 0.595 |

Chunks preserve nearly all gold facts; notes drop a growing share as the match gets
strict — the renormalization cost the pipeline was warned would have to be earned back.

## Answer stage (`runs5`, token-budget matched, hybrid, 200 Q)

| metric | chunks | notes |
|---|--:|--:|
| F1 | **0.794** | 0.655 |
| Exact-match | **0.780** | 0.645 |
| contains-answer | **0.820** | 0.690 |
| over-refusal | 0.090 | 0.175 |
| mean units in context | 14.1 | **6.9** |

Chunks answer better at matched budget; notes over-refuse more but do it with ~half
the context units — more token-efficient per unit, but the evidence they carry is
weaker, netting lower answer quality. (A second, harder answer condition
`answers_tokens.json` sits near a tie at low F1 ≈ 0.31 for both.)

## Hypothesis verdicts

- **H1 (budget interaction)** — *partial, sign-flipped.* The chunks-over-notes gap is
  largest at the tightest budget (−0.155 @2048) and shrinks with budget (−0.070 @8192).
  The predicted *interaction shape* holds, but the direction is the opposite of the
  hoped-for notes advantage — there is no advantage to be largest.
- **H2 (graph + notes beats chunk RAG at matched budget)** — **not supported / refuted.**
  Chunks win at matched token budget; the graph arm underperforms lexical/dense on notes.
- **H3 (mechanism / order effect)** — *still open.* Needs the order-sensitive metric;
  the retrieval runs here do not test it.

## Caveats

- Single corpus (MultiHop-RAG news, 609 docs). The pipeline was tuned on technical
  documentation; genre mismatch is the leading external-validity threat and is not
  controlled here.
- Notes carry web enrichment on 88/126 term notes (`enriched: web`), but term notes
  are a glossary layer, not the content notes scored here; the retrieval arms score
  the content-note vault. Enrichment is ablatable if it needs isolating.
- "evid" vs "full" token accounting materially changes the notes gap (tie vs loss).
  Report both; the fair headline is full-budget, with evid as the best case for notes.

## Provenance

`runs2` arm comparison · `runs3` notes strategies × {evid,full} · `runs4` degree sweep
+ fact recall/retention · `runs5` answer eval. Regenerate the aggregates with
`experiments/results/summarize.py`; paired CIs with `scripts/compare_runs.py`.
