---
tags:
  - plan
  - digestion
  - benchmark
  - master
keywords:
  - multihop rag corpus plan
  - full corpus digestion
  - entry point hierarchy
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: ready
building_block: navigation
---

# Corpus Master Plan: MultiHop-RAG (all 609 documents)

Index hub for the whole corpus. Per-note detail lives in the cluster plans and
the pilot sub-plans; this file never duplicates a note table.

| | |
|---|---|
| Documents | **609** (1,063,319 words) |
| Notes | **4,925** |
| Sub-plans | **595** across 33 clusters + 13 pilot sub-plans |
| Term links | **16,394**, every one backed by source |
| Fan-out | 8.09 notes per document |

## Clusters

| Cluster | Category | Docs | Words | Sub-plans | Notes |
|---|---|---|---|---|---|
| [c01](clusters/c01.json) | business | 20 | 23,658 | 18 | 171 |
| [c02](clusters/c02.json) | business | 20 | 32,414 | 19 | 155 |
| [c03](clusters/c03.json) | business | 20 | 35,363 | 19 | 153 |
| [c04](clusters/c04.json) | business | 20 | 26,798 | 19 | 137 |
| [c05](clusters/c05.json) | business | 1 | 1,271 | 3 | 14 |
| [c06](clusters/c06.json) | entertainment | 20 | 27,609 | 17 | 150 |
| [c07](clusters/c07.json) | entertainment | 20 | 22,737 | 13 | 99 |
| [c08](clusters/c08.json) | entertainment | 20 | 56,607 | 34 | 288 |
| [c09](clusters/c09.json) | entertainment | 20 | 34,861 | 26 | 203 |
| [c10](clusters/c10.json) | entertainment | 14 | 27,736 | 18 | 118 |
| [c11](clusters/c11.json) | entertainment | 20 | 29,925 | 18 | 132 |
| [c12](clusters/c12.json) | health | 10 | 12,510 | 10 | 93 |
| [c13](clusters/c13.json) | science | 20 | 30,309 | 19 | 155 |
| [c14](clusters/c14.json) | science | 1 | 1,405 | 3 | 13 |
| [c15](clusters/c15.json) | sports | 20 | 40,737 | 15 | 113 |
| [c16](clusters/c16.json) | sports | 20 | 30,175 | 13 | 133 |
| [c17](clusters/c17.json) | sports | 20 | 40,619 | 14 | 118 |
| [c18](clusters/c18.json) | sports | 20 | 32,641 | 16 | 132 |
| [c19](clusters/c19.json) | sports | 20 | 30,849 | 21 | 212 |
| [c20](clusters/c20.json) | sports | 20 | 31,150 | 18 | 130 |
| [c21](clusters/c21.json) | sports | 11 | 15,332 | 12 | 76 |
| [c22](clusters/c22.json) | sports | 20 | 46,862 | 21 | 167 |
| [c23](clusters/c23.json) | sports | 20 | 30,916 | 18 | 134 |
| [c24](clusters/c24.json) | sports | 20 | 28,870 | 16 | 136 |
| [c25](clusters/c25.json) | sports | 20 | 41,088 | 19 | 144 |
| [c26](clusters/c26.json) | technology | 20 | 27,385 | 18 | 162 |
| [c27](clusters/c27.json) | technology | 20 | 22,489 | 21 | 145 |
| [c28](clusters/c28.json) | technology | 20 | 46,190 | 16 | 131 |
| [c29](clusters/c29.json) | technology | 20 | 48,510 | 23 | 205 |
| [c30](clusters/c30.json) | technology | 20 | 50,752 | 24 | 239 |
| [c31](clusters/c31.json) | technology | 7 | 17,365 | 10 | 81 |
| [c32](clusters/c32.json) | technology | 20 | 39,375 | 21 | 162 |
| [c33](clusters/c33.json) | technology | 20 | 42,916 | 30 | 292 |
| pilot | technology | 25 | 35,895 | 13 | 132 |

## Building Blocks Across the Corpus

| Building block | Notes | Share |
|---|---|---|
| `empirical_observation` | 2,502 | 52.2% |
| `concept` | 986 | 20.6% |
| `argument` | 696 | 14.5% |
| `model` | 222 | 4.6% |
| `counter_argument` | 212 | 4.4% |
| `procedure` | 144 | 3.0% |
| `hypothesis` | 31 | 0.6% |

`hypothesis` is **0.6%** and `navigation` is absent from the
extracted notes. Both are the predicted result and neither was manufactured: news
reporting rarely states a testable prediction, and navigation notes are generated
by the pipeline rather than found in a source. A corpus that yields no hypotheses
should not be made to yield them.

## Entry Point Hierarchy

4,925 notes cannot hang off one index. Three levels, each a `navigation`
note carrying no `source_docs` (they index rather than assert, so `FM-004`
exempts them):

| Level | Note | Contents |
|---|---|---|
| Root | `entry_multihop_rag.md` | Quick Stats, the six category entry points, References. No note rows. |
| Category | `entry_<category>.md` × 6 | One section per cluster in that category, linking cluster entry points |
| Cluster | `entry_<cluster_slug>.md` × 33 | One row per note: title, building block, the question it answers |

| Category | Docs | Sub-plans | Notes | Clusters |
|---|---|---|---|---|
| `entry_technology.md` | 172 | 176 | 1,549 | c26, c27, c28, c29, c30, c31, c32, c33, pilot |
| `entry_sports.md` | 211 | 183 | 1,495 | c15, c16, c17, c18, c19, c20, c21, c22, c23, c24, c25 |
| `entry_entertainment.md` | 114 | 126 | 990 | c06, c07, c08, c09, c10, c11 |
| `entry_business.md` | 81 | 78 | 630 | c01, c02, c03, c04, c05 |
| `entry_science.md` | 21 | 22 | 168 | c13, c14 |
| `entry_health.md` | 10 | 10 | 93 | c12 |

Written **bottom-up**: cluster entry points after their notes exist, category
entry points after their clusters, the root last. Every note links to its cluster
entry point, so no note is a graph island — an island is retrievable by name and
unreachable by traversal, which makes it invisible to the graph arm the
experiment measures.

## Gates

Every gate from the pilot master plan applies, plus three the corpus scale adds:

| Gate | Command |
|---|---|
| G12 cluster rules | `scripts/verify_cluster_plan.py <slug> --plan <cluster>.json --own-docs ...` |
| G13 cross-cluster | `scripts/merge_cluster_plans.py <slug> --clusters <dir>` — no filename collision, no low coverage, no orphan document |
| G14 provenance | `scripts/check_provenance.py <slug> --vault <vault>` — every note's `source_docs` matches the plan |

## Execution Order

P1 clusters first within each category, because entity notes are shared inside a
cluster and later clusters link to them. Commit per cluster. Cap agent fan-out
at roughly 30 per wave.

## Related Notes

- [Pilot slice master plan](plan_digest_multihop_rag_slice.md)
- [Merges declined, with reasons](merge_declined.md)
- [Building blocks](../../../docs/BUILDING_BLOCKS.md)
