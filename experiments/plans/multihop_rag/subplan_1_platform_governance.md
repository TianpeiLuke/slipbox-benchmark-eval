---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - platform governance notes
  - section coverage map
  - building block atomicity
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: active
building_block: navigation
---

# Sub-plan 1: Platform Governance (8 documents)

Note table for the first batch of the MultiHop-RAG pilot slice. Shared decisions
— routing, format, gates, quarantine — live in the
[master plan](plan_digest_multihop_rag_slice.md) and are not repeated here.

**Documents**: doc_0009, doc_0010, doc_0030 (FTX trial) · doc_0024, doc_0025,
doc_0195 (EU/X) · doc_0106, doc_0335 (Meta). All eight were read in full, then
segmented into paragraph blocks with `scripts/plan_coverage.py --segment`, and
every block was assigned to a note or explicitly dropped.

## Three constraints, checked by script rather than by eye

| Constraint | Method | Result |
|---|---|---|
| One building block per note | Each note carries exactly one `building_block`, from the closed enum | 37/37 |
| Under 1,800 source words per note | Sum of assigned block words per note | max **911**, 0 over |
| Cover the source without omitting much | Assigned blocks ÷ document words | **95.7%** |

`python3 scripts/plan_coverage.py multihop_rag --check <assignments>` reproduces
all three and exits non-zero if any note breaches the ceiling.

## Planned Notes

| # | Note | BB | Source docs | Source blocks | Src words |
|---|---|---|---|---|---|
| 1 | `sbf_trial_proceedings.md` | `empirical_observation` | doc_0009, doc_0030 | 0009:0,1,2,9,10,29; 0030:1,2 | 326 |
| 2 | `sbf_trial_testimony.md` | `empirical_observation` | doc_0009 | 0009:12,13,14,15,16,17,18,19,25,27,28 | 471 |
| 3 | `sbf_trial_arguments.md` | `argument` | doc_0009, doc_0030 | 0009:20,21,22,23; 0030:30 | 250 |
| 4 | `sbf_taking_the_stand.md` | `argument` | doc_0009 | 0009:3,4,5 | 104 |
| 5 | `sam_bankman_fried.md` | `concept` | doc_0010, doc_0030 | 0010:2,3,8,16,22; 0030:22 | 254 |
| 6 | `sbf_arrest_and_bail.md` | `empirical_observation` | doc_0010 | 0010:17,18 | 72 |
| 7 | `sbf_defense_counsel.md` | `empirical_observation` | doc_0010 | 0010:24,25 | 61 |
| 8 | `ftx.md` | `concept` | doc_0010, doc_0030 | 0010:1,4,5,6; 0030:15 | 125 |
| 9 | `alameda_research.md` | `concept` | doc_0010 | 0010:5,12 | 60 |
| 10 | `ftx_marketing_and_influence.md` | `empirical_observation` | doc_0010, doc_0030 | 0010:7; 0030:14,16,17,18,19 | 375 |
| 11 | `ftx_collapse_mechanism.md` | `model` | doc_0010, doc_0030 | 0010:9,10,11,13,14,15; 0030:21 | 209 |
| 12 | `ftx_bankruptcy_and_leadership.md` | `empirical_observation` | doc_0010 | 0010:19 | 76 |
| 13 | `ftx_cooperating_witnesses.md` | `empirical_observation` | doc_0010 | 0010:20,21 | 80 |
| 14 | `crypto_contagion_after_ftx.md` | `empirical_observation` | doc_0010, doc_0030 | 0010:23; 0030:23 | 126 |
| 15 | `going_infinite_lewis_account.md` | `empirical_observation` | doc_0030 | 0030:5,6,7,8,9,10,11,12,13 | 405 |
| 16 | `reaction_to_lewis_portrayal.md` | `counter_argument` | doc_0030 | 0030:3,4,24,25,26,27,28,29 | 327 |
| 17 | `digital_services_act.md` | `concept` | doc_0024, doc_0025, doc_0335 | 0024:3,4,12,13,14; 0025:3,12,13,20; 0335:15,16,17,18,19 | 642 |
| 18 | `eu_enforcement_against_x.md` | `empirical_observation` | doc_0024, doc_0025 | 0024:2,6,7,10,11,23,24,25,26,29; 0025:17,18,21,22,23,24,25,29,30,31 | 868 |
| 19 | `eu_warning_letter_to_x.md` | `empirical_observation` | doc_0024, doc_0025 | 0024:8,9; 0025:1,2,4,26,27 | 336 |
| 20 | `x_moderation_capacity.md` | `model` | doc_0024, doc_0025 | 0024:16,21,27; 0025:14,15,16 | 275 |
| 21 | `disinformation_on_x_gaza.md` | `empirical_observation` | doc_0024, doc_0025 | 0024:15,20,22; 0025:5,6,7,8,9,10,11 | 416 |
| 22 | `x_response_to_eu.md` | `empirical_observation` | doc_0024, doc_0025 | 0024:17,18; 0025:33 | 122 |
| 23 | `musk_position_on_disinformation.md` | `counter_argument` | doc_0025 | 0025:19,28,32,34,35,36,37,38 | 384 |
| 24 | `eu_warnings_to_other_platforms.md` | `empirical_observation` | doc_0024, doc_0335 | 0024:28; 0335:20,21 | 123 |
| 25 | `platform_transparency_after_x_private.md` | `argument` | doc_0024 | 0024:5 | 49 |
| 26 | `x_bot_countermeasures.md` | `procedure` | doc_0195 | 0195:2,3,4,5,8,9,10,11,12,13 | 703 |
| 27 | `objections_to_x_bot_fee.md` | `counter_argument` | doc_0195 | 0195:6,7,16,17,18 | 263 |
| 28 | `x_competitive_position.md` | `empirical_observation` | doc_0195 | 0195:14,15,19 | 169 |
| 29 | `meta_moderation_bias.md` | `argument` | doc_0106 | 0106:1,7,9,41,42,48,49 | 388 |
| 30 | `meta_bias_mechanisms.md` | `model` | doc_0106 | 0106:8,43,44,45,52,53,54 | 445 |
| 31 | `instagram_palestine_suppression.md` | `empirical_observation` | doc_0106 | 0106:2,3,4,6,12,13,14,19,20,22,23,27,28,29,30,31,32,34,35,37,38,39 | 911 |
| 32 | `meta_response_to_suppression_claims.md` | `counter_argument` | doc_0106 | 0106:5,10,11,17,18,24,25,26,33,36 | 496 |
| 33 | `meta_2021_conflict_moderation.md` | `empirical_observation` | doc_0106 | 0106:46,47,51,55 | 250 |
| 34 | `meta_arabic_mistranslation.md` | `empirical_observation` | doc_0106 | 0106:56,57,58,59 | 247 |
| 35 | `shadowban_workarounds.md` | `procedure` | doc_0106 | 0106:60,61,62 | 156 |
| 36 | `meta_crisis_response_measures.md` | `procedure` | doc_0335 | 0335:1,2,3,4,5,6,7,8,9,10,11,13,14 | 591 |
| 37 | `meta_enforcement_volume.md` | `empirical_observation` | doc_0335 | 0335:12 | 70 |

BB distribution: `empirical_observation` 19, `argument` 4, `concept` 4, `counter_argument` 4, `model` 3, `procedure` 3

Source words per note range from 49 to 911, well inside the ceiling. **14 of 37
notes draw on more than one document** — that is the property multi-hop
questions depend on, and the reason a note arm can satisfy several pieces of
gold evidence with a single retrieval where a chunk arm cannot.

`hypothesis` is absent, as the master plan predicted for news reporting. That
absence is reported, not filled.

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0009     1205      959  79.6%  [6, 7, 8, 11, 24, 26, 30]
doc_0010      956      901  94.2%  [0, 26]
doc_0024     1174     1122  95.6%  [0, 1, 19]
doc_0025     1813     1797  99.1%  [0]
doc_0030     1447     1430  98.8%  [0, 20]
doc_0106     2943     2893  98.3%  [0, 15, 16, 21, 40, 50, 63]
doc_0195     1173     1135  96.8%  [0, 1]
doc_0335      985      957  97.2%  [0, 22]

total 11,696 words, 11,194 covered (95.7%)
notes over the 1800-word source ceiling: 0
```

`doc_0009` is the outlier at 79.6%, and the reason is visible in what was
dropped: seven blocks of newsletter promotion, podcast plugs and "read our full
coverage" links. It is the most promotion-heavy article in the batch.

Everything dropped falls into five kinds, and each was inspected individually
rather than discarded by rule:

| Kind | Example | Why it is dropped |
|---|---|---|
| Article title | `doc_0106[0]` | Carried in the note's H1, so not lost |
| Section header | "A history of suppression" | A label with no claim of its own |
| Publisher promotion | "follow along in the Chain Reaction newsletter" | Names no fact about the world |
| Reaction with no content | "THEY TRY TO SILENCE US" | Sentiment without an assertion to retain |
| Byline / update notice | "Dominic-Madori Davis contributed" | Metadata about the article |

**One block was recovered after review.** `doc_0024[29]` reads as a routine
correction notice, but states that the EU had **not** opened an investigation —
contradicting that article's own headline. It is a scope condition on the
central claim, exactly the class an unconditioned summariser drops, so it is
assigned to `eu_enforcement_against_x.md`. Three reaction tweets carrying
specific shadowbanning claims were recovered on the same grounds.

## Split Decisions

| Document | Words | Split into | Rule that forced it |
|---|---|---|---|
| doc_0106 | 2,943 | 7 notes | >1,800 words: split mandatory. Boundaries taken at building block: claim / mechanism / observation / rebuttal / history / incident / workaround |
| doc_0025 | 1,813 | 8 notes | >1,800 words: split mandatory. Also mixed BB across regulation, enforcement, capacity and observed content |
| doc_0030 | 1,447 | 6 notes | Mixed BB, each well over 500 words: the Lewis account is `empirical_observation`, the criticism `counter_argument`, the intent framing `argument` |
| doc_0010 | 956 | 9 notes | Under the size threshold, but spans nine distinct entities and events; a single note would have mixed four building blocks |
| doc_0195 | 1,173 | 3 notes | Mixed BB: the measure is `procedure`, the objections `counter_argument`, the market position `empirical_observation` |
| doc_0024 | 1,174 | 6 notes | Mixed BB across regulation, enforcement events, platform capacity and observed content |
| doc_0009 | 1,205 | 4 notes | Mixed BB: proceedings and testimony are `empirical_observation`, both argument notes are `argument` |
| doc_0335 | 985 | 5 notes | Mixed BB: crisis measures are `procedure`, obligations and volume `empirical_observation` |

Articles here carry no headings, so the split-at-H2 rule has no anchor. Splits
are taken at **building-block boundaries**, which is the rule the H2 heuristic
was approximating.

## Navigation Notes (generated, not derived)

Two notes are produced by the pipeline rather than extracted from any document.
Both take `building_block: navigation` and carry no `source_docs` — they index
rather than assert, so there is nothing to trace them to, and `FM-004` exempts
them.

| Note | Produced by | Contents |
|---|---|---|
| `glossary.md` | `scripts/glossary.py`, via `capture-term-note` | One entry per captured term: full name, 2–4 sentence description, link to the term note, source document |
| `entry_platform_governance.md` | authored at the end of execution | Entry point for the batch: the three story clusters, each note listed under the question it answers, and the cross-cluster links |

The glossary does not exist yet and is **created by the first term capture**.
Ordering matters: the term note is written first, then registered, so the
glossary never links to a note that does not exist.

## Undigested Terms

Terms the corpus uses without defining. Each needs `capture-term-note`, which
may enrich from the web for background the corpus does not supply — kept in a
separate `## Background (external)` section with `external_refs`, and never in
`source_docs`, so the scorer counts only corpus evidence.

| Term | Corpus gives | Needs external context |
|---|---|---|
| FTT | Called "the token behind FTX"; its role in the collapse | What an exchange token is, and why holding your own is fragile |
| VLOP | Designation and obligations | The designation threshold and the full 19-platform list |
| Community Notes | Named as X's main disinformation response | How the crowdsourcing mechanism actually works |
| Chapter 11 | Used without definition | What the procedure is and what it does to creditors |
| Shadowbanning | Used throughout, defined only in passing | The term's origin and its contested definition |
| Dangerous Organizations and Individuals policy | Named, enforcement volumes given | What the policy covers |

## Cross-References

Every note needs **at least three** `Related Notes` links, found by content
search rather than recall:

```bash
python3 scripts/retrieval.py vaults/multihop_rag \
    --query "<the note's opening claim>" --strategy hybrid --k 8
```

Keep results carrying a real relation; discard those sharing only vocabulary. A
spurious edge is not harmless — `bfs` and `ppr` traverse every edge they are
given, so a false link degrades the arm under test.

Entity notes (`ftx`, `sam_bankman_fried`, `alameda_research`,
`digital_services_act`) are the hubs: each is extended as later documents
evidence it, and gains that document in its `source_docs`. **Never create a
second note for an entity that already has one** — the dedup rule is what lets a
single note satisfy several pieces of gold evidence.

## Execution Order

1. Content notes in document order, entity notes first within each cluster
2. `capture-term-note` for the six undigested terms; the first creates the glossary
3. Cross-reference pass: every note to at least three related notes by content search
4. `entry_platform_governance.md` last, once every note it indexes exists
5. Gates G1–G7 from the master plan

## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md): routing, format, gates, quarantine
- [Building blocks](../../../docs/BUILDING_BLOCKS.md): the closed enum and retention contracts
