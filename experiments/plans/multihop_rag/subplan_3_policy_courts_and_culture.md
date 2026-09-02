---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - policy, courts and culture
  - section coverage map
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: active
building_block: navigation
---

# Sub-plan 3: Policy, Courts and Culture (8 documents)

Eight documents on platform policy, litigation, creator economics and the war's effect on two tech ecosystems. All are conventionally reported single-topic articles, which is why this batch reaches the highest coverage of the three.

Shared decisions — routing, format, gates, quarantine — live in the
[master plan](plan_digest_multihop_rag_slice.md) and are not repeated here.
Every document was read in full, segmented into paragraph blocks, and every
block assigned to a note or explicitly dropped.

## Constraints, checked by script

| Constraint | Result |
|---|---|
| One building block per note | 33/33, closed enum |
| Under 1,800 source words per note | max **652**, 0 over |
| Source coverage | **doc_0043** |

```
python3 scripts/plan_coverage.py multihop_rag \
    --check experiments/plans/multihop_rag/subplan_3_assignments.json \
    --own-docs doc_0267,doc_0272,doc_0278,doc_0367,doc_0401,doc_0448,doc_0456,doc_0457
```

## Planned Notes

| # | Note | BB | Source docs | Src words |
|---|---|---|---|---|
| 1 | `web_summit_cosgrave_controversy.md` | `empirical_observation` | doc_0267 | 445 |
| 2 | `israel_tech_industry_boycott.md` | `empirical_observation` | doc_0267 | 397 |
| 3 | `web_summit_business_impact.md` | `empirical_observation` | doc_0267 | 387 |
| 4 | `ai_day_of_action_campaign.md` | `empirical_observation` | doc_0043, doc_0272 | 242 |
| 5 | `creative_industries_ai_concerns.md` | `argument` | doc_0272 | 341 |
| 6 | `ai_copyright_and_training_disputes.md` | `counter_argument` | doc_0272 | 171 |
| 7 | `ftc_generative_ai_roundtable.md` | `empirical_observation` | doc_0272 | 227 |
| 8 | `ohanian_social_media_critique.md` | `argument` | doc_0278 | 402 |
| 9 | `reddit_moderation_history.md` | `empirical_observation` | doc_0278 | 232 |
| 10 | `platform_truth_arbitration.md` | `argument` | doc_0278 | 291 |
| 11 | `ohanian_techno_optimism.md` | `argument` | doc_0278 | 273 |
| 12 | `uber_assault_litigation.md` | `empirical_observation` | doc_0367 | 365 |
| 13 | `uber_safety_features.md` | `procedure` | doc_0367 | 311 |
| 14 | `in_car_camera_proposal.md` | `argument` | doc_0367 | 322 |
| 15 | `surveillance_privacy_tradeoff.md` | `counter_argument` | doc_0367 | 419 |
| 16 | `twitch_revenue_split_controversy.md` | `empirical_observation` | doc_0401 | 225 |
| 17 | `twitch_partner_plus_program.md` | `procedure` | doc_0401 | 387 |
| 18 | `twitch_advertising_strategy.md` | `model` | doc_0401 | 318 |
| 19 | `twitch_sponsorship_and_amazon.md` | `model` | doc_0401 | 319 |
| 20 | `twitch_competitive_pressure.md` | `argument` | doc_0401 | 352 |
| 21 | `israel_tech_sector_scale.md` | `empirical_observation` | doc_0448 | 335 |
| 22 | `israel_startup_funding_decline.md` | `empirical_observation` | doc_0448 | 289 |
| 23 | `israel_tech_workforce_mobilisation.md` | `empirical_observation` | doc_0448 | 340 |
| 24 | `israeli_founders_operating_at_war.md` | `empirical_observation` | doc_0448 | 528 |
| 25 | `starnews_mobile_platform.md` | `concept` | doc_0456 | 271 |
| 26 | `african_telco_distribution_model.md` | `model` | doc_0456 | 449 |
| 27 | `starnews_content_and_growth.md` | `empirical_observation` | doc_0456 | 252 |
| 28 | `starnews_funding_round.md` | `empirical_observation` | doc_0456 | 397 |
| 29 | `eu_csam_scanning_proposal.md` | `concept` | doc_0457 | 412 |
| 30 | `commission_microtargeted_ad_campaign.md` | `empirical_observation` | doc_0457 | 378 |
| 31 | `dsa_political_ad_restrictions.md` | `model` | doc_0457 | 419 |
| 32 | `johansson_parliament_hearing.md` | `empirical_observation` | doc_0457 | 635 |
| 33 | `csam_proposal_opposition.md` | `counter_argument` | doc_0457 | 652 |

BB distribution: `empirical_observation` 16, `argument` 6, `model` 4, `counter_argument` 3, `procedure` 2, `concept` 2

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0267     1242     1229  99.0%  [0]
doc_0272      920      911  99.0%  [0]
doc_0278     1211     1198  98.9%  [0]
doc_0367     1427     1417  99.3%  [0]
doc_0401     1615     1601  99.1%  [0]
doc_0448     1499     1492  99.5%  [0]
doc_0456     1382     1369  99.1%  [0]
doc_0457     2504     2496  99.7%  [0]

total 11,800 words, 11,713 covered (99.3%)
cross-references: 1 block(s) from 1 document(s) owned elsewhere (doc_0043) — notes reused rather than duplicated
notes over the 1800-word source ceiling: 0
```

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

- This sub-plan owns `doc_0267,doc_0272,doc_0278,doc_0367,doc_0401,doc_0448,doc_0456,doc_0457`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.
