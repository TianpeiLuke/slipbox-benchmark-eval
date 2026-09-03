---
building_block: navigation
---

# MultiHop-RAG Corpus — Root Entry Point

Root index for the typed-atomic-note vault derived from the MultiHop-RAG benchmark corpus (609 news documents, 49 publishers). Navigation only — every note is reachable from here through its category and cluster entry points.

## Quick Stats

- Source documents: 609 (1,063,319 words, 49 publishers)
- Content notes: 4925
- Building blocks:
  - empirical_observation: 2572
  - concept: 998
  - argument: 716
  - model: 233
  - counter_argument: 223
  - procedure: 152
  - hypothesis: 31
- Resolved link count: reported by `scripts/build_local_db.py --stats`.

## Category Entry Points

- [Business](entry_business.md): 630 notes across 5 clusters.
- [Entertainment](entry_entertainment.md): 990 notes across 6 clusters.
- [Health](entry_health.md): 93 notes across 1 clusters.
- [Science](entry_science.md): 168 notes across 2 clusters.
- [Sports](entry_sports.md): 1495 notes across 11 clusters.
- [Technology](entry_technology.md): 1549 notes across 9 clusters.

## Related Notes

- [Corpus Glossary](glossary.md): alphabetical index of the corpus term notes.

## References

- Corpus: MultiHop-RAG (Tang & Yang, 2024, arXiv:2401.15391), ODC-BY-1.0.
- Plan: `experiments/plans/multihop_rag/plan_corpus_master.md`.
