---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - eu csam scanning proposal
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: completed
building_block: navigation
---

# Sub-plan 11: EU CSAM Scanning Proposal

**Priority P3** · 1 document(s), 2,496 words · **5 notes**

Shared decisions — routing, format, gates, entry points, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md). This sub-plan is independently
executable: nothing here waits on another sub-plan, and cross-references are
added after execution.

Documents: `doc_0457`

## Constraints

| Constraint | Result |
|---|---|
| Notes in the 4–15 range | **5** |
| One building block per note | 5/5 |
| Under 1,800 source words per note | max **652** |
| Source coverage | **99.7%** |
| Term links per note | median **6**, floor 3 |

## Planned Notes

| # | Note | BB | Source docs | Src words | Term links |
|---|---|---|---|---|---|
| 1 | `commission_microtargeted_ad_campaign.md` | `empirical_observation` | doc_0457 | 378 | `executive_order`, `microtargeting`, `lobbying_political_donations`, `digital_services_act`, `data_privacy`, `embedded_finance` |
| 2 | `csam_proposal_opposition.md` | `counter_argument` | doc_0457 | 652 | `csam_scanning`, `data_privacy`, `executive_order`, `encryption_at_rest`, `hardware_device`, `recommendation_algorithm` |
| 3 | `dsa_political_ad_restrictions.md` | `model` | doc_0457 | 419 | `lobbying_political_donations`, `microtargeting`, `csam_scanning` |
| 4 | `eu_csam_scanning_proposal.md` | `concept` | doc_0457 | 412 | `lobbying_political_donations`, `digital_services_act`, `csam_scanning`, `very_large_online_platform`, `microtargeting`, `data_privacy` |
| 5 | `johansson_parliament_hearing.md` | `empirical_observation` | doc_0457 | 635 | `csam_scanning`, `disinformation`, `regulatory_investigation` |

BB distribution: `empirical_observation` 2, `counter_argument` 1, `model` 1, `concept` 1

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0457     2504     2496  99.7%  [0]

total 2,504 words, 2,496 covered (99.7%)
notes over the 1800-word source ceiling: 0
```

## Entry Point Contribution

This sub-plan contributes one section to `entry_multihop_rag.md`, written after
its notes exist:

- **Section**: `EU CSAM Scanning Proposal`
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

- This sub-plan owns `doc_0457`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.


## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)

## Execution Record

All **5** planned notes exist in `vaults/multihop_rag/`. Verified by name against the vault, not by an agent's report of what it wrote.
