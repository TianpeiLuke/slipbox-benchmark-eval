---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - platform governance debate
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: completed
building_block: navigation
---

# Sub-plan 09: Platform Governance Debate

**Priority P2** · 2 document(s), 2,427 words · **7 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0267`, `doc_0278`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **7** |
| One building block per note | 7/7 |
| Under 1,800 source words per note | max **445** |
| Source coverage | **98.9%** |
| Term links per note | median **4**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `israel_tech_industry_boycott.md` | `empirical_observation` | doc_0267 | 397 | `executive_order`, `board_governance`, `celebrity_endorsement`, `value_added_services`, `lobbying_political_donations` |
| 2 | `ohanian_social_media_critique.md` | `argument` | doc_0278 | 402 | `board_governance`, `executive_order`, `disinformation`, `creator_economy` |
| 3 | `ohanian_techno_optimism.md` | `argument` | doc_0278 | 273 | `executive_order`, `livestreaming`, `board_governance`, `fine_penalty` |
| 4 | `platform_truth_arbitration.md` | `argument` | doc_0278 | 291 | `executive_order`, `community_notes`, `board_governance` |
| 5 | `reddit_moderation_history.md` | `empirical_observation` | doc_0278 | 232 | `user_generated_content`, `executive_order`, `appeals_process`, `valuation` |
| 6 | `web_summit_business_impact.md` | `empirical_observation` | doc_0267 | 387 | `executive_order`, `value_added_services`, `recommendation_algorithm` |
| 7 | `web_summit_cosgrave_controversy.md` | `empirical_observation` | doc_0267 | 445 | `user_generated_content`, `dangerous_organizations_policy`, `executive_order`, `bot_detection`, `lobbying_political_donations` |

BB distribution: `empirical_observation` 4, `argument` 3

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0267     1242     1229  99.0%  [0]
doc_0278     1211     1198  98.9%  [0]

total 2,453 words, 2,427 covered (98.9%)
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `Platform Governance Debate`
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

- This sub-plan owns `doc_0267, doc_0278`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)

## Execution Record

All **7** planned notes exist in `vaults/multihop_rag/`. Verified by name against the vault, not by an agent's report of what it wrote.
