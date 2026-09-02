---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - startups weekly roundup
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: ready
building_block: navigation
---

# Sub-plan 13: Startups Weekly Roundup

**Priority P3** · 1 document(s), 1,201 words · **13 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0043`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **13** |
| One building block per note | 13/13 |
| Under 1,800 source words per note | max **167** |
| Source coverage | **75.2%** |
| Term links per note | median **1**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `adobe_generative_ai_tools.md` | `empirical_observation` | doc_0043 | 62 | `generative_ai` |
| 2 | `brave_software_layoffs.md` | `empirical_observation` | doc_0043 | 35 | `layoffs` |
| 3 | `consumer_ar_vr_hardware.md` | `empirical_observation` | doc_0043 | 44 | — |
| 4 | `creator_economy_sustainability.md` | `argument` | doc_0043 | 131 | `creator_economy`, `venture_capital` |
| 5 | `founder_event_attendance_debate.md` | `argument` | doc_0043 | 167 | `board_governance` |
| 6 | `mastodon_and_x_traffic_figures.md` | `empirical_observation` | doc_0043 | 61 | — |
| 7 | `openai_chip_and_nvidia_position.md` | `empirical_observation` | doc_0043 | 158 | `user_generated_content`, `bot_detection`, `market_competition` |
| 8 | `passkeys_default_signin.md` | `concept` | doc_0043 | 52 | `passkeys`, `hardware_device` |
| 9 | `pc_shipment_decline_2023.md` | `empirical_observation` | doc_0043 | 38 | `cloud_computing`, `hardware_device` |
| 10 | `reddit_api_third_party_apps.md` | `empirical_observation` | doc_0043 | 31 | `subscription_model` |
| 11 | `sonos_google_patent_reversal.md` | `empirical_observation` | doc_0043 | 42 | `patent_litigation` |
| 12 | `tidalflow_llm_integration.md` | `empirical_observation` | doc_0043 | 39 | `large_language_model` |
| 13 | `upi_commercial_sustainability.md` | `counter_argument` | doc_0043 | 46 | `acquisition`, `market_competition` |

BB distribution: `empirical_observation` 9, `argument` 2, `concept` 1, `counter_argument` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0043     1205      906  75.2%  [0, 1, 5, 6, 10, 13, 14, 17, 19, 24, 25, 26]

total 1,205 words, 906 covered (75.2%)
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `Startups Weekly Roundup`
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

- This sub-plan owns `doc_0043`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)
