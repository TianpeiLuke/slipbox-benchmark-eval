---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - consumer ai and devices
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: completed
building_block: navigation
---

# Sub-plan 07: Consumer AI and Devices

**Priority P2** · 2 document(s), 2,821 words · **10 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0188`, `doc_0230`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **10** |
| One building block per note | 10/10 |
| Under 1,800 source words per note | max **457** |
| Source coverage | **99.5%** |
| Term links per note | median **5**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `alexa_kids_interaction_design.md` | `model` | doc_0188 | 322 | `generative_ai_guardrails` |
| 2 | `alexa_kids_llm_guardrails.md` | `procedure` | doc_0188 | 430 | `large_language_model`, `generative_ai`, `executive_order`, `ai_hallucination`, `bot_detection`, `generative_ai_guardrails` |
| 3 | `alexa_kids_privacy_and_hardware.md` | `empirical_observation` | doc_0188 | 339 | `hardware_device`, `large_language_model`, `bot_detection`, `product_launch`, `accessibility_localisation`, `data_privacy` |
| 4 | `explore_with_alexa.md` | `concept` | doc_0188 | 119 | `generative_ai`, `subscription_model`, `bot_detection`, `product_launch`, `hardware_device` |
| 5 | `keep_labs_cannabis_repositioning.md` | `empirical_observation` | doc_0230 | 235 | `market_competition`, `executive_order`, `hardware_device`, `harm_reduction`, `board_governance` |
| 6 | `keep_labs_device.md` | `concept` | doc_0230 | 206 | `bot_detection`, `hardware_device`, `product_launch`, `harm_reduction`, `medication_adherence` |
| 7 | `keep_labs_enterprise_partnerships.md` | `empirical_observation` | doc_0230 | 155 | `executive_order`, `medication_adherence` |
| 8 | `keep_labs_funding_and_roadmap.md` | `empirical_observation` | doc_0230 | 178 | `product_launch`, `venture_capital`, `executive_order`, `hardware_device`, `board_governance` |
| 9 | `keep_labs_pivot_and_leadership.md` | `empirical_observation` | doc_0230 | 386 | `executive_order`, `hardware_device`, `product_launch`, `market_competition`, `board_governance`, `lobbying_political_donations` |
| 10 | `keep_labs_security_posture.md` | `procedure` | doc_0230 | 457 | `encryption_at_rest`, `data_privacy`, `hardware_device`, `hipaa`, `executive_order`, `subscription_model` |

BB distribution: `empirical_observation` 5, `procedure` 2, `concept` 2, `model` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0188     1210     1210 100.0%  []
doc_0230     1630     1617  99.2%  [0, 31]

total 2,840 words, 2,827 covered (99.5%)
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `Consumer AI and Devices`
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

- This sub-plan owns `doc_0188, doc_0230`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)

## Execution Record

All **10** planned notes exist in `vaults/multihop_rag/`. Verified by name against the vault, not by an agent's report of what it wrote.
