---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - eu enforcement against x
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: ready
building_block: navigation
---

# Sub-plan 02: EU Enforcement Against X

**Priority P1** · 3 document(s), 4,114 words · **11 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0024`, `doc_0025`, `doc_0195`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **11** |
| One building block per note | 11/11 |
| Under 1,800 source words per note | max **868** |
| Source coverage | **doc_0335** |
| Term links per note | median **6**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `digital_services_act.md` | `concept` | doc_0024, doc_0025, doc_0335 | 642 | `digital_services_act`, `very_large_online_platform`, `fine_penalty`, `disinformation`, `crisis_response_mechanism`, `recommendation_algorithm` |
| 2 | `disinformation_on_x_gaza.md` | `empirical_observation` | doc_0024, doc_0025 | 416 | `executive_order`, `user_generated_content`, `disinformation`, `recommendation_algorithm` |
| 3 | `eu_enforcement_against_x.md` | `empirical_observation` | doc_0024, doc_0025 | 868 | `digital_services_act`, `regulatory_investigation`, `disinformation`, `fine_penalty`, `crisis_response_mechanism`, `recommendation_algorithm` |
| 4 | `eu_warning_letter_to_x.md` | `empirical_observation` | doc_0024, doc_0025 | 336 | `disinformation`, `digital_services_act`, `content_moderation`, `executive_order`, `recommendation_algorithm`, `market_competition` |
| 5 | `musk_position_on_disinformation.md` | `counter_argument` | doc_0025 | 384 | `disinformation`, `digital_services_act`, `valuation`, `hardware_device`, `fine_penalty`, `recommendation_algorithm` |
| 6 | `objections_to_x_bot_fee.md` | `counter_argument` | doc_0195 | 263 | `bot_detection`, `digital_divide`, `battery_technology`, `executive_order`, `value_added_services` |
| 7 | `platform_transparency_after_x_private.md` | `argument` | doc_0024 | 49 | `regulatory_investigation` |
| 8 | `x_bot_countermeasures.md` | `procedure` | doc_0195 | 703 | `bot_detection`, `executive_order`, `identity_verification`, `livestreaming`, `payment_processor`, `creator_economy` |
| 9 | `x_competitive_position.md` | `empirical_observation` | doc_0195 | 169 | `market_competition`, `subscription_model`, `bot_detection`, `acquisition`, `open_source` |
| 10 | `x_moderation_capacity.md` | `model` | doc_0024, doc_0025 | 275 | `disinformation`, `community_notes`, `content_moderation`, `digital_services_act`, `executive_order`, `identity_verification` |
| 11 | `x_response_to_eu.md` | `empirical_observation` | doc_0024, doc_0025 | 122 | `digital_services_act`, `executive_order`, `board_governance`, `user_generated_content` |

BB distribution: `empirical_observation` 5, `counter_argument` 2, `concept` 1, `argument` 1, `procedure` 1, `model` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0024     1174     1074  91.5%  [0, 1, 19, 28]
doc_0025     1813     1797  99.1%  [0]
doc_0195     1173     1135  96.8%  [0, 1]

total 4,160 words, 4,006 covered (96.3%)
cross-references: 5 block(s) from 1 document(s) owned elsewhere (doc_0335) — notes reused rather than duplicated
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `EU Enforcement Against X`
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

- This sub-plan owns `doc_0024, doc_0025, doc_0195`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)
