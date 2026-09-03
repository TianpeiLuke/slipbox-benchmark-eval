---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - creator economy and platform safety
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: completed
building_block: navigation
---

# Sub-plan 08: Creator Economy and Platform Safety

**Priority P2** · 3 document(s), 3,929 words · **13 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0272`, `doc_0367`, `doc_0401`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **13** |
| One building block per note | 13/13 |
| Under 1,800 source words per note | max **419** |
| Source coverage | **doc_0043** |
| Term links per note | median **5**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `ai_copyright_and_training_disputes.md` | `counter_argument` | doc_0272 | 171 | `generative_ai`, `fraud`, `hardware_device` |
| 2 | `ai_day_of_action_campaign.md` | `empirical_observation` | doc_0043, doc_0272 | 242 | `lobbying_political_donations`, `product_launch` |
| 3 | `creative_industries_ai_concerns.md` | `argument` | doc_0272 | 341 | `product_launch`, `lobbying_political_donations` |
| 4 | `ftc_generative_ai_roundtable.md` | `empirical_observation` | doc_0272 | 227 | `generative_ai`, `creator_economy`, `generative_ai_guardrails`, `livestreaming` |
| 5 | `in_car_camera_proposal.md` | `argument` | doc_0367 | 322 | `executive_order`, `in_car_surveillance` |
| 6 | `surveillance_privacy_tradeoff.md` | `counter_argument` | doc_0367 | 419 | `criminal_trial`, `class_action`, `livestreaming`, `patent_litigation`, `valuation` |
| 7 | `twitch_advertising_strategy.md` | `model` | doc_0401 | 318 | `creator_economy`, `revenue_split`, `livestreaming`, `executive_order`, `subscription_model`, `product_launch` |
| 8 | `twitch_competitive_pressure.md` | `argument` | doc_0401 | 352 | `executive_order`, `bot_detection`, `board_governance`, `creator_economy`, `revenue_split`, `simulcasting` |
| 9 | `twitch_partner_plus_program.md` | `procedure` | doc_0401 | 387 | `creator_economy`, `livestreaming`, `executive_order`, `revenue_split`, `simulcasting`, `subscription_model` |
| 10 | `twitch_revenue_split_controversy.md` | `empirical_observation` | doc_0401 | 225 | `subscription_model`, `creator_economy`, `revenue_split`, `embedded_finance`, `value_added_services`, `product_launch` |
| 11 | `twitch_sponsorship_and_amazon.md` | `model` | doc_0401 | 319 | `creator_economy`, `celebrity_endorsement`, `bot_detection`, `recommendation_algorithm`, `market_competition` |
| 12 | `uber_assault_litigation.md` | `empirical_observation` | doc_0367 | 365 | `in_car_surveillance`, `hardware_device`, `multidistrict_litigation`, `bot_detection`, `livestreaming`, `product_launch` |
| 13 | `uber_safety_features.md` | `procedure` | doc_0367 | 311 | `hardware_device`, `executive_order`, `data_privacy` |

BB distribution: `empirical_observation` 4, `argument` 3, `counter_argument` 2, `model` 2, `procedure` 2

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0272      920      911  99.0%  [0]
doc_0367     1427     1417  99.3%  [0]
doc_0401     1615     1601  99.1%  [0]

total 3,962 words, 3,929 covered (99.2%)
cross-references: 1 block(s) from 1 document(s) owned elsewhere (doc_0043) — notes reused rather than duplicated
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `Creator Economy and Platform Safety`
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

- This sub-plan owns `doc_0272, doc_0367, doc_0401`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)

## Execution Record

All **13** planned notes exist in `vaults/multihop_rag/`. Verified by name against the vault, not by an agent's report of what it wrote.
