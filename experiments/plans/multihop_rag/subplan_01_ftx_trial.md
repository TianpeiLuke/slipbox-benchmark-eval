---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - ftx trial and collapse
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: completed
building_block: navigation
---

# Sub-plan 01: FTX Trial and Collapse

**Priority P1** · 3 document(s), 3,569 words · **14 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0009`, `doc_0010`, `doc_0030`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **14** |
| One building block per note | 14/14 |
| Under 1,800 source words per note | max **471** |
| Source coverage | **73.0%** |
| Term links per note | median **4**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `alameda_research.md` | `concept` | doc_0010 | 60 | `ftt_token`, `valuation` |
| 2 | `crypto_contagion_after_ftx.md` | `empirical_observation` | doc_0010, doc_0030 | 126 | `chapter_11`, `executive_order`, `board_governance`, `market_competition` |
| 3 | `ftx.md` | `concept` | doc_0010, doc_0030 | 94 | `valuation`, `venture_capital`, `criminal_trial`, `lobbying_political_donations` |
| 4 | `ftx_bankruptcy_and_leadership.md` | `empirical_observation` | doc_0010 | 76 | `fraud` |
| 5 | `ftx_collapse_mechanism.md` | `model` | doc_0010, doc_0030 | 209 | `valuation`, `ftt_token`, `board_governance`, `chapter_11`, `bank_run`, `executive_order` |
| 6 | `ftx_cooperating_witnesses.md` | `empirical_observation` | doc_0010 | 80 | `plea_agreement`, `board_governance`, `executive_order`, `bot_detection`, `criminal_trial`, `fine_penalty` |
| 7 | `ftx_marketing_and_influence.md` | `empirical_observation` | doc_0010, doc_0030 | 375 | `lobbying_political_donations`, `celebrity_endorsement`, `criminal_trial`, `valuation`, `recommendation_algorithm`, `market_competition` |
| 8 | `reaction_to_lewis_portrayal.md` | `counter_argument` | doc_0030 | 327 | `executive_order`, `market_competition` |
| 9 | `sam_bankman_fried.md` | `concept` | doc_0010, doc_0030 | 254 | `fraud`, `plea_agreement`, `valuation`, `executive_order`, `criminal_trial`, `bail` |
| 10 | `sbf_arrest_and_bail.md` | `empirical_observation` | doc_0010 | 72 | `bail`, `executive_order`, `board_governance` |
| 11 | `sbf_defense_counsel.md` | `empirical_observation` | doc_0010 | 61 | `criminal_trial` |
| 12 | `sbf_taking_the_stand.md` | `argument` | doc_0009 | 104 | `criminal_trial`, `fraud` |
| 13 | `sbf_trial_proceedings.md` | `empirical_observation` | doc_0009, doc_0030 | 326 | `criminal_trial`, `fraud`, `board_governance`, `executive_order`, `bot_detection`, `plea_agreement` |
| 14 | `sbf_trial_testimony.md` | `empirical_observation` | doc_0009 | 471 | `criminal_trial`, `valuation`, `board_governance`, `executive_order`, `line_of_credit`, `class_action` |

BB distribution: `empirical_observation` 8, `concept` 3, `model` 1, `counter_argument` 1, `argument` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0009     1205      789  65.5%  [6, 7, 8, 11, 20, 21, 22, 23, 24, 26, 30]
doc_0010      956      901  94.2%  [0, 26]
doc_0030     1447      945  65.3%  [0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 20, 30]

total 3,608 words, 2,635 covered (73.0%)
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `FTX Trial and Collapse`
- **Rows**: one per note, giving the note title, its building block, and the
  question it answers
- **Back-link**: every note links to the entry point, so no note is an island

The entry point itself is created once, by the master plan, not per sub-plan.


## Pacing Rules

- One phase at a time; validate every GATE before starting the next
- **Re-read the source block before writing each note** — never write from memory
- Each note under 400 lines; if a note passes 350 while writing, stop and split
- Quotations verbatim — never reformat or improve a quotation
- After each phase: verify GATEs, then commit and push
- **BB atomicity**: if a note starts mixing building blocks, split it
- No rush. A wrong note costs more than a slow one, because fan-out multiplies it

## Per-Phase GATEs

| Phase | Contents | GATE |
|---|---|---|
| 1 | Entity and hub notes first | G1 format, G5 provenance |
| 2 | Remaining content notes | G1, G5, G8 ceiling |
| 3 | Term notes and glossary registration | G1, G5, glossary entry per term |
| 4 | Cross-reference pass, 3+ per note | G2 links, G3 ghosts, G9 links |
| 5 | Inlinks from existing notes | G2, G3, zero orphans |
| 6 | Entry point | G1, G4 index, zero unresolved |

Gate commands are in the [master plan](plan_digest_multihop_rag_slice.md).

## Related Notes Mapping

Per-note link targets are **not enumerated here**, and that is deliberate. The
upstream skill asks for a hand-built table of at least eight term links per
note, which assumes a mature vault. This corpus vault starts empty, so such a
table written now would be a guess at what the vault will later contain — and a
planned link to a note that never gets written becomes a ghost reference the
gates then reject. Links are instead resolved **at execution time, against the
vault as it then exists**:

```bash
python3 scripts/retrieval.py vaults/multihop_rag \
    --query "<the note's opening claim>" --strategy hybrid --k 8
```

Floor: **three or more outbound links per note**, each stating how the notes
relate, plus one link from the batch entry point. Keep only links carrying a
real relation — `bfs` and `ppr` traverse every edge given, so a spurious edge
degrades the arm under test as surely as a missing one.

## Inlink Mapping

Every note needs at least one inbound link, and inlinks are **executed and
verified**, not merely planned:

```bash
python3 scripts/build_local_db.py vaults/multihop_rag --stats
```

The orphan count must be zero. An orphan is retrievable by name and unreachable
by traversal, so it is invisible to the graph arm — which is the arm the
experiment exists to measure.

## Follow-ups

- This sub-plan owns `doc_0009, doc_0010, doc_0030`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)

## Execution Record

All **14** planned notes exist in `vaults/multihop_rag/`. Verified by name against the vault, not by an agent's report of what it wrote.
