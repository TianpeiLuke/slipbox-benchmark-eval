---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - global tech ecosystems
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: ready
building_block: navigation
---

# Sub-plan 10: Global Tech Ecosystems

**Priority P3** · 2 document(s), 2,861 words · **8 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0448`, `doc_0456`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **8** |
| One building block per note | 8/8 |
| Under 1,800 source words per note | max **528** |
| Source coverage | **99.3%** |
| Term links per note | median **5**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `african_telco_distribution_model.md` | `model` | doc_0456 | 449 | `creator_economy`, `market_competition`, `subscription_model`, `acquisition`, `executive_order`, `telco_distribution` |
| 2 | `israel_startup_funding_decline.md` | `empirical_observation` | doc_0448 | 289 | `executive_order`, `reserve_mobilisation`, `judicial_reform`, `valuation`, `market_competition` |
| 3 | `israel_tech_sector_scale.md` | `empirical_observation` | doc_0448 | 335 | `executive_order`, `valuation`, `venture_capital`, `bot_detection`, `criminal_trial` |
| 4 | `israel_tech_workforce_mobilisation.md` | `empirical_observation` | doc_0448 | 340 | `executive_order`, `board_governance`, `venture_capital`, `reserve_mobilisation`, `layoffs` |
| 5 | `israeli_founders_operating_at_war.md` | `empirical_observation` | doc_0448 | 528 | `executive_order`, `reserve_mobilisation`, `board_governance`, `market_competition` |
| 6 | `starnews_content_and_growth.md` | `empirical_observation` | doc_0456 | 252 | `market_competition`, `creator_economy`, `executive_order`, `telco_distribution`, `recommendation_algorithm` |
| 7 | `starnews_funding_round.md` | `empirical_observation` | doc_0456 | 397 | `creator_economy`, `venture_capital`, `market_competition`, `valuation` |
| 8 | `starnews_mobile_platform.md` | `concept` | doc_0456 | 271 | `creator_economy`, `executive_order`, `telco_distribution`, `value_added_services`, `venture_capital`, `subscription_model` |

BB distribution: `empirical_observation` 6, `model` 1, `concept` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0448     1499     1492  99.5%  [0]
doc_0456     1382     1369  99.1%  [0]

total 2,881 words, 2,861 covered (99.3%)
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `Global Tech Ecosystems`
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

- This sub-plan owns `doc_0448, doc_0456`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)
