---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - meta moderation
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: completed
building_block: navigation
---

# Sub-plan 03: Meta Moderation

**Priority P1** · 2 document(s), 3,905 words · **10 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0106`, `doc_0335`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **10** |
| One building block per note | 10/10 |
| Under 1,800 source words per note | max **911** |
| Source coverage | **doc_0024** |
| Term links per note | median **8**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `eu_warnings_to_other_platforms.md` | `empirical_observation` | doc_0024, doc_0335 | 123 | `disinformation`, `digital_services_act`, `bot_detection`, `regulatory_investigation` |
| 2 | `instagram_palestine_suppression.md` | `empirical_observation` | doc_0106 | 911 | `user_generated_content`, `accessibility_localisation`, `shadowbanning`, `terms_of_service`, `recommendation_algorithm`, `livestreaming` |
| 3 | `meta_2021_conflict_moderation.md` | `empirical_observation` | doc_0106 | 250 | `dangerous_organizations_policy`, `product_launch`, `user_generated_content`, `recommendation_algorithm`, `accessibility_localisation` |
| 4 | `meta_arabic_mistranslation.md` | `empirical_observation` | doc_0106 | 247 | `machine_translation`, `accessibility_localisation`, `executive_order`, `hardware_device` |
| 5 | `meta_bias_mechanisms.md` | `model` | doc_0106 | 445 | `accessibility_localisation`, `digital_services_act`, `content_moderation`, `dangerous_organizations_policy`, `executive_order`, `hardware_device` |
| 6 | `meta_crisis_response_measures.md` | `procedure` | doc_0335 | 591 | `livestreaming`, `executive_order`, `hashtag_blocking`, `recommendation_algorithm`, `accessibility_localisation`, `content_moderation` |
| 7 | `meta_enforcement_volume.md` | `empirical_observation` | doc_0335 | 70 | `accessibility_localisation`, `dangerous_organizations_policy` |
| 8 | `meta_moderation_bias.md` | `argument` | doc_0106 | 388 | `accessibility_localisation`, `user_generated_content`, `shadowbanning`, `executive_order`, `bot_detection`, `board_governance` |
| 9 | `meta_response_to_suppression_claims.md` | `counter_argument` | doc_0106 | 496 | `user_generated_content`, `executive_order`, `recommendation_algorithm`, `shadowbanning`, `dangerous_organizations_policy`, `livestreaming` |
| 10 | `shadowban_workarounds.md` | `procedure` | doc_0106 | 156 | `user_generated_content`, `shadowbanning`, `creator_economy`, `bot_detection`, `recommendation_algorithm` |

BB distribution: `empirical_observation` 5, `procedure` 2, `model` 1, `argument` 1, `counter_argument` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0106     2943     2893  98.3%  [0, 15, 16, 21, 40, 50, 63]
doc_0335      985      736  74.7%  [0, 15, 16, 17, 18, 19, 22]

total 3,928 words, 3,629 covered (92.4%)
cross-references: 1 block(s) from 1 document(s) owned elsewhere (doc_0024) — notes reused rather than duplicated
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `Meta Moderation`
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

- This sub-plan owns `doc_0106, doc_0335`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)

## Execution Record

All **10** planned notes exist in `vaults/multihop_rag/`. Verified by name against the vault, not by an agent's report of what it wrote.
