---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - antitrust and speech law
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: ready
building_block: navigation
---

# Sub-plan 04: Antitrust and Speech Law

**Priority P1** · 2 document(s), 2,446 words · **10 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0237`, `doc_0256`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **10** |
| One building block per note | 10/10 |
| Under 1,800 source words per note | max **559** |
| Source coverage | **97.9%** |
| Term links per note | median **5**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `big_tech_antitrust_outlook.md` | `argument` | doc_0237 | 226 | `antitrust`, `cloud_computing`, `criminal_trial`, `hardware_device` |
| 2 | `first_amendment_editorial_judgment.md` | `argument` | doc_0256 | 171 | `first_amendment`, `content_moderation`, `editorial_judgment` |
| 3 | `google_antitrust_case.md` | `concept` | doc_0237 | 197 | `market_competition`, `antitrust`, `criminal_trial`, `default_search_engine`, `executive_order`, `valuation` |
| 4 | `google_apple_chrome_agreement.md` | `empirical_observation` | doc_0237 | 190 | `executive_order`, `criminal_trial`, `board_governance`, `total_addressable_market`, `valuation`, `hardware_device` |
| 5 | `google_default_hypocrisy_argument.md` | `argument` | doc_0237 | 223 | `antitrust`, `default_search_engine`, `litigation_hold` |
| 6 | `google_default_search_payments.md` | `empirical_observation` | doc_0237 | 245 | `valuation`, `total_addressable_market`, `market_competition`, `default_search_engine`, `executive_order`, `criminal_trial` |
| 7 | `google_deleted_chat_logs.md` | `empirical_observation` | doc_0237 | 125 | `litigation_hold`, `executive_order`, `bot_detection`, `criminal_trial`, `hardware_device` |
| 8 | `scotus_ruling_consequences.md` | `counter_argument` | doc_0256 | 559 | `executive_order`, `lobbying_political_donations`, `content_moderation`, `disinformation`, `first_amendment`, `bot_detection` |
| 9 | `scotus_social_media_cases.md` | `concept` | doc_0256 | 196 | `lobbying_political_donations`, `content_moderation`, `disinformation`, `executive_order`, `user_generated_content` |
| 10 | `texas_florida_moderation_laws.md` | `model` | doc_0256 | 285 | `bot_detection`, `first_amendment`, `criminal_trial`, `cloud_computing` |

BB distribution: `argument` 3, `empirical_observation` 3, `concept` 2, `counter_argument` 1, `model` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0237     1222     1206  98.7%  [0, 28]
doc_0256     1246     1211  97.2%  [0, 1]

total 2,468 words, 2,417 covered (97.9%)
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `Antitrust and Speech Law`
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

- This sub-plan owns `doc_0237, doc_0256`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)
