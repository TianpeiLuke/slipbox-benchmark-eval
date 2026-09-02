---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - week in review roundup
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: ready
building_block: navigation
---

# Sub-plan 12: Week in Review Roundup

**Priority P3** · 1 document(s), 1,179 words · **12 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0011`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **12** |
| One building block per note | 12/12 |
| Under 1,800 source words per note | max **192** |
| Source coverage | **doc_0043** |
| Term links per note | median **3**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `acurable_respiratory_wearables.md` | `empirical_observation` | doc_0011 | 63 | `wearable_device`, `hardware_device` |
| 2 | `breathe_battery_software.md` | `empirical_observation` | doc_0011 | 40 | `battery_technology` |
| 3 | `flexport_leadership_turmoil.md` | `empirical_observation` | doc_0011 | 78 | `valuation`, `board_governance`, `executive_order` |
| 4 | `gmail_bulk_sender_rules.md` | `procedure` | doc_0011 | 62 | `bot_detection` |
| 5 | `going_infinite_lewis_account.md` | `empirical_observation` | doc_0011 | 77 | `criminal_trial`, `acquisition`, `lobbying_political_donations` |
| 6 | `google_pixel_8_launch.md` | `empirical_observation` | doc_0011, doc_0043 | 192 | `hardware_device`, `livestreaming`, `product_launch` |
| 7 | `induced_ai_workflow_automation.md` | `empirical_observation` | doc_0011 | 56 | — |
| 8 | `ironnet_shutdown.md` | `empirical_observation` | doc_0011 | 76 | `initial_public_offering`, `layoffs` |
| 9 | `linkedin_ai_tools.md` | `empirical_observation` | doc_0011 | 56 | `market_competition`, `product_launch`, `lobbying_political_donations` |
| 10 | `sbf_trial_arguments.md` | `argument` | doc_0011 | 61 | `criminal_trial`, `fraud`, `executive_order` |
| 11 | `tiktok_ad_free_tier.md` | `empirical_observation` | doc_0011, doc_0043 | 98 | `subscription_model`, `executive_order`, `board_governance`, `market_competition` |
| 12 | `x_post_volume_discrepancy.md` | `counter_argument` | doc_0011 | 67 | `user_generated_content`, `executive_order`, `board_governance` |

BB distribution: `empirical_observation` 9, `procedure` 1, `argument` 1, `counter_argument` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0011     1195      822  68.8%  [0, 1, 2, 3, 4, 15, 16, 17, 19, 20, 21, 24]

total 1,195 words, 822 covered (68.8%)
cross-references: 2 block(s) from 1 document(s) owned elsewhere (doc_0043) — notes reused rather than duplicated
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `Week in Review Roundup`
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

- This sub-plan owns `doc_0011`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)
