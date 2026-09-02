---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag digestion plan
  - benchmark corpus ingestion
  - building block atomic notes
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: active
building_block: navigation
---

# Master Plan: Digest the MultiHop-RAG Pilot Slice

Master plan for digesting the 25-document pilot slice of the MultiHop-RAG corpus
into `vaults/multihop_rag/`. Sub-plans hold the per-note tables; this file holds
the decisions that apply across all of them.

## Source

- **Corpus**: MultiHop-RAG (Tang & Yang, 2024, arXiv:2401.15391), ODC-BY-1.0
- **Documents**: `data/corpus/multihop_rag/doc_*.txt`, prepared by `scripts/prepare_corpus.py`
- **Slice manifest**: `vaults/multihop_rag_handwritten/SLICE.txt` — 25 documents, all TechCrunch, October 2023
- **Selection rule**: densest publisher-and-month cluster, chosen from corpus structure alone by `scripts/select_slice.py`

**Quarantine.** `data/raw/multihop_rag/MultiHopRAG.json` holds the questions and
gold evidence. It is off limits for the whole of digestion: not read, not
grepped, not passed to any sub-agent. Every sub-agent contract must state this
verbatim. A breach contaminates the corpus and requires re-ingestion from
scratch, because notes written with sight of the questions would answer them by
construction and every downstream number would be invalid while still looking
valid.

## Step 1: Content Measurement (measured, not estimated)

25 documents, **35,895 words**. Per-document word counts and the density
treatment each one triggers are in the sub-plans. Distribution: median 1,229
words, min 911, max 2,929.

| Source page size | Treatment | Documents |
|---|---|---|
| ≤ 1200 words | 1 note likely | 10 |
| 1200–1800 words | 1 if single BB, split if mixed | 11 |
| 1800–3600 words | MUST split ≥2 | 4 |
| > 3600 words | MUST split ≥3 | 0 |

**Minimum 40 notes** by the density rule, a fan-out floor of **1.60 notes per
document**.

### Step 1e: Divide-and-Conquer

40 notes exceeds the 30-note threshold, so this is a master plan with sub-plans.
The master never duplicates the sub-plan note tables.

| Sub-plan | Documents | Words | Notes | Status |
|---|---|---|---|---|
| [Sub-plan 1 — Platform Governance](subplan_1_platform_governance.md) | 8 | 11,696 | 37 | **planned, verified** |
| [Sub-plan 2 — Startups, Funding and Product](subplan_2_startups_funding_and_product.md) | 9 | 12,695 | 64 | **planned, verified** |
| [Sub-plan 3 — Policy, Courts and Culture](subplan_3_policy_courts_and_culture.md) | 8 | 11,800 | 33 | **planned, verified** |

All 25 documents have been read, segmented into paragraph blocks, and assigned
block by block. **132 distinct notes** across the slice, two of which are
shared: a later sub-plan extends a note an earlier one owns rather than creating
a second note on the same subject.

Coverage is measured over the documents each sub-plan **owns**. A note extended
by another batch does not credit that batch with source it does not own, so
`--own-docs` separates the two.

## Step 2: Routing

| Decision | Value | Why |
|---|---|---|
| Target directory | `vaults/multihop_rag/` (flat) | The DB uses the vault-relative path as note id; flat makes id = filename and lets links be bare filenames. See `docs/BUILDING_BLOCKS.md` and the note contract in each skill. |
| Filename prefix | none | News entities carry no natural type prefix. `term_` is reserved for glossary term notes created by `capture-term-note`. |
| Dedup baseline | vault is empty | No existing notes, so no dedup conflicts on the first batch. Batches 2 and 3 MUST dedup against batch 1 output. |

**Note Format Definition** — derived from the note contract, not invented:

```
---
building_block: <one of the eight>
source_docs: [doc_XXXX, ...]
---

# <Title>

<claim-first body: the answer in the first paragraph, detail after>

## Related Notes
- [Other Note](other_note.md): how it relates

## Source
- doc_XXXX: <publisher, date>
```

`source_docs` is required (`FM-004`) and is what makes a note scorable: gold
labels are passage-level, so a note that cannot name its documents cannot be
credited when retrieved.

## Step 3: Decomposition

### 3a. Building-block classification for this genre

News reporting maps onto the ontology unevenly, and the plan records that rather
than forcing it:

| Content pattern in these documents | Building block | Expected frequency |
|---|---|---|
| Dated events, testimony, filings, figures, company statements | `empirical_observation` | dominant |
| Entities: companies, people, regulations, products | `concept` | common |
| Mechanisms, causal chains, structural relations | `model` | occasional |
| Claims argued with evidence; positions attributed to a party | `argument` | occasional |
| Rebuttals, criticism, company denials | `counter_argument` | occasional |
| Documented step sequences (platform policies, user workarounds) | `procedure` | rare |
| Testable predictions | `hypothesis` | **near zero — do not manufacture** |
| Indexes | `navigation` | generated, not found |

`hypothesis` is expected to be absent. A corpus that contains no hypotheses
should not yield hypothesis notes; its absence is a finding to report. Sub-plan
1 confirms this: 37 notes, zero hypotheses.

### 3f. Navigation notes are generated, not extracted

Each sub-plan produces two notes that come from no document: the corpus
`glossary.md` (created by the first `capture-term-note`) and a per-batch entry
point. Both take `building_block: navigation` and carry no `source_docs`, since
they index rather than assert — `FM-004` exempts them for that reason.

### 3g. Per-note source ceiling

No note may draw on more than 1,800 words of source. Verify with
`scripts/plan_coverage.py --check`, which sums assigned block words per note and
exits non-zero on a breach. Sub-plan 1's maximum is 911.

### 3b. Topical coherence governs; density constrains

The two rules are not peers, and their order matters.

**Topical coherence decides where a note ends.** One note covers one subject.
This is what makes a note answerable: a reader retrieving it gets the whole of
one thing rather than part of several.

**Density then constrains how large that note may be.** If a topically coherent
unit exceeds 1,800 source words, it splits again — at a sub-topic boundary,
never at an arbitrary word count.

Applying them in the other order produces the failure this corpus makes obvious.
A newsletter roundup runs 1,195 words, so the size rule alone says "one note" —
but that note would hold fifteen unrelated items, a $8B logistics shake-up
beside a phone camera review. It would answer no question well, and retrieval
would surface it for everything and satisfy nothing. Size is a budget, not a
boundary.

The reverse case is equally clear: `doc_0106` is a single coherent argument
about moderation bias, and coherence alone would keep it whole at 2,943 words.
Density forces the split, taken at building-block boundaries — claim, mechanism,
observation, rebuttal.

### 3c. Density thresholds

Applied per the skill: split above 1800 words, 400 lines, 6 code blocks, or 6
unrelated H2 topics; split when a note would mix building blocks with more than
500 words each.

News articles carry no headings in this corpus, so the H2-boundary split rule
has no anchor. Splits are taken at **topic boundaries within the article** —
each a distinct event, party, or mechanism — and every split is recorded with
its reason in the sub-plan's Split Decisions table.

## Step 4: Cross-References

Entities recur across documents, which is the property multi-hop questions are
built on. Two rules follow.

1. **One note per entity, extended across documents.** When a later document
   evidences an existing entity note, extend that note and add the document to
   its `source_docs` — never create a second note for the same entity. This is
   what lets one note satisfy several pieces of gold evidence at once.
2. **Links are bare filenames** resolved inside the vault, and every note needs
   **at least three**, found by searching on the note's own content
   (`scripts/retrieval.py --strategy hybrid`) rather than by recall. Keep only
   links carrying a real relation: `bfs` and `ppr` traverse every edge given, so
   a spurious link degrades the arm under test as surely as a missing one.
3. **Term links are derived, not hand-tabled.** `scripts/build_term_links.py`
   links a term to a note when the term's surface forms appear in that note's
   own source blocks, so relevance is corpus evidence rather than recollection.
   Measured floor is **3**, not the upstream 8: with 93 curated terms the median
   note reaches 4 evidence-backed term links, and forcing 8 would add 425 edges
   with nothing behind them — **40% of the graph fabricated**. Since `bfs` and
   `ppr` traverse every edge, that does not merely fail to help, it degrades the
   arm under test. Link density has an optimum, not a maximum.
4. **Terms may be enriched from the web**, in a separate `## Background
   (external)` section with `external_refs` in frontmatter. `source_docs` stays
   corpus-only, so the scorer counts corpus evidence and nothing else, and the
   enrichment can be ablated to test whether any advantage survives without it.

## Undigested Terms Plan

**93 terms**, curated from candidates mined by `scripts/mine_terms.py`
(ranked by document spread, since a term appearing across many documents becomes
a hub several notes link to, while one appearing forty times in a single article
is that article's subject rather than a shared concept).

Every term is referenced by at least one note. A term note nothing links to is a
graph island — retrievable by name, unreachable by traversal — which is the exact
failure the term list exists to prevent, so unreferenced candidates were dropped
rather than captured.

Captured by `capture-term-note` in **Phase 3**, before the Phase 4 linking pass.
That ordering is what keeps the derived term links from becoming ghost references.

Most-linked terms:

| Term | Notes linking to it |
|---|---|
| `term_executive_order` | 67 |
| `term_board_governance` | 34 |
| `term_market_competition` | 34 |
| `term_bot_detection` | 30 |
| `term_hardware_device` | 27 |
| `term_recommendation_algorithm` | 24 |
| `term_valuation` | 22 |
| `term_criminal_trial` | 19 |
| `term_lobbying_political_donations` | 18 |
| `term_user_generated_content` | 17 |
| `term_creator_economy` | 16 |
| `term_product_launch` | 16 |

Full mapping: `term_links.json`. Surface forms: `terms.json`.

## Step 5: Validation Gates

| Gate | Command | Blocking |
|---|---|---|
| G1 format | `python3 scripts/validate_notes.py vaults/multihop_rag --gate` | yes |
| G2 broken links | same run, rules `LN-001` / `LN-002` | yes |
| G3 ghosts | same run, rule `GH-001` | yes |
| G4 index | `python3 scripts/build_local_db.py vaults/multihop_rag --stats` | zero unresolved links |
| G5 provenance | every note has `source_docs` (`FM-004`) | yes |
| G6 quarantine | no read of `MultiHopRAG.json` during digestion | yes — breach means re-ingest |
| G7 coverage | `python3 scripts/plan_coverage.py <slug> --check <assignments>` — every block assigned or explicitly dropped | yes |
| G8 ceiling | same command: no note over 1,800 source words | yes |
| G9 links | every note has ≥3 `Related Notes` by content relevance | yes |
| G10 no duplicate source | `python3 scripts/plan_coverage.py <slug> --crossplan experiments/plans/<slug>/` — no source block assigned to two notes | yes |

## Related Notes

- [Sub-plan 1 — Platform Governance](subplan_1_platform_governance.md): 37 notes, 95.7% coverage
- [Sub-plan 2 — Startups, Funding and Product](subplan_2_startups_funding_and_product.md): 64 notes, 93.5% coverage
- [Sub-plan 3 — Policy, Courts and Culture](subplan_3_policy_courts_and_culture.md): 33 notes, 99.3% coverage

## References

- MultiHop-RAG: https://github.com/yixuantt/MultiHop-RAG
- Building blocks: `docs/BUILDING_BLOCKS.md`
- Control arm: `vaults/multihop_rag_handwritten/README.md`
