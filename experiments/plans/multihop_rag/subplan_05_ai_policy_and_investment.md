---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - ai policy and investment
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: completed
building_block: navigation
---

# Sub-plan 05: AI Policy and Investment

**Priority P2** · 2 document(s), 3,026 words · **8 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0098`, `doc_0161`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **8** |
| One building block per note | 8/8 |
| Under 1,800 source words per note | max **858** |
| Source coverage | **doc_0011** |
| Term links per note | median **8**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `ai_legislation_gap.md` | `argument` | doc_0098 | 231 | `executive_order` |
| 2 | `ai_market_spending_forecasts.md` | `empirical_observation` | doc_0161 | 237 | `valuation`, `cloud_computing`, `generative_ai`, `recommendation_algorithm`, `market_competition` |
| 3 | `ai_pricing_models.md` | `model` | doc_0161 | 261 | `usage_based_pricing`, `large_language_model`, `saas_pricing`, `payment_processor`, `bot_detection`, `cloud_computing` |
| 4 | `ai_startup_defensibility.md` | `argument` | doc_0011, doc_0161 | 858 | `market_competition`, `large_language_model`, `foundation_model`, `defensibility`, `llm_observability`, `proprietary_data` |
| 5 | `biden_ai_executive_order.md` | `empirical_observation` | doc_0098 | 288 | `executive_order` |
| 6 | `llm_stack_layers.md` | `model` | doc_0161 | 518 | `market_competition`, `large_language_model`, `fine_penalty`, `generative_ai`, `foundation_model`, `defensibility` |
| 7 | `reaction_to_biden_ai_order.md` | `counter_argument` | doc_0098 | 431 | `executive_order`, `red_teaming`, `bot_detection`, `value_added_services`, `criminal_trial`, `board_governance` |
| 8 | `valor_applied_ai_thesis.md` | `argument` | doc_0161 | 265 | `large_language_model`, `fine_penalty`, `market_competition`, `generative_ai`, `model_fine_tuning`, `llm_observability` |

BB distribution: `argument` 3, `empirical_observation` 2, `model` 2, `counter_argument` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0098      950      950 100.0%  []
doc_0161     2103     2089  99.3%  [0]

total 3,053 words, 3,039 covered (99.5%)
cross-references: 1 block(s) from 1 document(s) owned elsewhere (doc_0011) — notes reused rather than duplicated
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `AI Policy and Investment`
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

- This sub-plan owns `doc_0098, doc_0161`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)

## Execution Record

All **8** planned notes exist in `vaults/multihop_rag/`. Verified by name against the vault, not by an agent's report of what it wrote.
