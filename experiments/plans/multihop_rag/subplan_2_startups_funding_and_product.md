---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - startups, funding and product
  - section coverage map
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: active
building_block: navigation
---

# Sub-plan 2: Startups, Funding and Product (9 documents)

Nine documents spanning startup funding, AI investment, consumer product launches and two antitrust matters. Three of them (doc_0011, doc_0043, doc_0075) are **newsletter roundups** rather than reported articles, and they need a different treatment, described below.

Shared decisions — routing, format, gates, quarantine — live in the
[master plan](plan_digest_multihop_rag_slice.md) and are not repeated here.
Every document was read in full, segmented into paragraph blocks, and every
block assigned to a note or explicitly dropped.

## Constraints, checked by script

| Constraint | Result |
|---|---|
| One building block per note | 64/64, closed enum |
| Under 1,800 source words per note | max **858**, 0 over |
| Source coverage | **93.5%** |

```
python3 scripts/plan_coverage.py multihop_rag \
    --check experiments/plans/multihop_rag/subplan_2_assignments.json \
    --own-docs doc_0011,doc_0043,doc_0075,doc_0098,doc_0161,doc_0188,doc_0230,doc_0237,doc_0256
```

## Planned Notes

| # | Note | BB | Source docs | Src words |
|---|---|---|---|---|
| 1 | `induced_ai_workflow_automation.md` | `empirical_observation` | doc_0011 | 56 |
| 2 | `google_pixel_8_launch.md` | `empirical_observation` | doc_0011, doc_0043 | 192 |
| 3 | `flexport_leadership_turmoil.md` | `empirical_observation` | doc_0011 | 78 |
| 4 | `gmail_bulk_sender_rules.md` | `procedure` | doc_0011 | 62 |
| 5 | `tiktok_ad_free_tier.md` | `empirical_observation` | doc_0011, doc_0043 | 98 |
| 6 | `linkedin_ai_tools.md` | `empirical_observation` | doc_0011 | 56 |
| 7 | `x_post_volume_discrepancy.md` | `counter_argument` | doc_0011 | 67 |
| 8 | `ironnet_shutdown.md` | `empirical_observation` | doc_0011 | 76 |
| 9 | `breathe_battery_software.md` | `empirical_observation` | doc_0011 | 40 |
| 10 | `acurable_respiratory_wearables.md` | `empirical_observation` | doc_0011 | 63 |
| 11 | `founder_event_attendance_debate.md` | `argument` | doc_0043 | 167 |
| 12 | `openai_chip_and_nvidia_position.md` | `empirical_observation` | doc_0043 | 158 |
| 13 | `adobe_generative_ai_tools.md` | `empirical_observation` | doc_0043 | 62 |
| 14 | `tidalflow_llm_integration.md` | `empirical_observation` | doc_0043 | 39 |
| 15 | `consumer_ar_vr_hardware.md` | `empirical_observation` | doc_0043 | 44 |
| 16 | `sonos_google_patent_reversal.md` | `empirical_observation` | doc_0043 | 42 |
| 17 | `pc_shipment_decline_2023.md` | `empirical_observation` | doc_0043 | 38 |
| 18 | `reddit_api_third_party_apps.md` | `empirical_observation` | doc_0043 | 31 |
| 19 | `creator_economy_sustainability.md` | `argument` | doc_0043 | 131 |
| 20 | `mastodon_and_x_traffic_figures.md` | `empirical_observation` | doc_0043 | 61 |
| 21 | `passkeys_default_signin.md` | `concept` | doc_0043 | 52 |
| 22 | `upi_commercial_sustainability.md` | `counter_argument` | doc_0043 | 46 |
| 23 | `brave_software_layoffs.md` | `empirical_observation` | doc_0043 | 35 |
| 24 | `rainforest_embedded_payments.md` | `concept` | doc_0075 | 312 |
| 25 | `rainforest_investor_thesis.md` | `argument` | doc_0075 | 219 |
| 26 | `paypal_anti_steering_lawsuit.md` | `empirical_observation` | doc_0075 | 195 |
| 27 | `payment_gatekeeper_antitrust_view.md` | `argument` | doc_0075 | 167 |
| 28 | `bolt_sec_probe.md` | `empirical_observation` | doc_0075 | 219 |
| 29 | `synapse_layoffs.md` | `empirical_observation` | doc_0075 | 81 |
| 30 | `visa_generative_ai_fund.md` | `empirical_observation` | doc_0075 | 62 |
| 31 | `slice_bank_merger_india.md` | `empirical_observation` | doc_0075 | 101 |
| 32 | `cred_revenue_growth.md` | `empirical_observation` | doc_0075 | 74 |
| 33 | `fintech_startup_rankings_2023.md` | `empirical_observation` | doc_0075 | 47 |
| 34 | `fintech_funding_roundup_oct_2023.md` | `empirical_observation` | doc_0075 | 229 |
| 35 | `biden_ai_executive_order.md` | `empirical_observation` | doc_0098 | 288 |
| 36 | `ai_legislation_gap.md` | `argument` | doc_0098 | 231 |
| 37 | `reaction_to_biden_ai_order.md` | `counter_argument` | doc_0098 | 431 |
| 38 | `llm_stack_layers.md` | `model` | doc_0161 | 518 |
| 39 | `ai_startup_defensibility.md` | `argument` | doc_0011, doc_0161 | 858 |
| 40 | `ai_pricing_models.md` | `model` | doc_0161 | 261 |
| 41 | `ai_market_spending_forecasts.md` | `empirical_observation` | doc_0161 | 237 |
| 42 | `explore_with_alexa.md` | `concept` | doc_0188 | 119 |
| 43 | `alexa_kids_llm_guardrails.md` | `procedure` | doc_0188 | 430 |
| 44 | `alexa_kids_interaction_design.md` | `model` | doc_0188 | 322 |
| 45 | `alexa_kids_privacy_and_hardware.md` | `empirical_observation` | doc_0188 | 339 |
| 46 | `keep_labs_device.md` | `concept` | doc_0230 | 206 |
| 47 | `keep_labs_cannabis_repositioning.md` | `empirical_observation` | doc_0230 | 235 |
| 48 | `keep_labs_pivot_and_leadership.md` | `empirical_observation` | doc_0230 | 386 |
| 49 | `keep_labs_enterprise_partnerships.md` | `empirical_observation` | doc_0230 | 155 |
| 50 | `keep_labs_security_posture.md` | `procedure` | doc_0230 | 457 |
| 51 | `keep_labs_funding_and_roadmap.md` | `empirical_observation` | doc_0230 | 178 |
| 52 | `google_antitrust_case.md` | `concept` | doc_0237 | 197 |
| 53 | `google_default_search_payments.md` | `empirical_observation` | doc_0237 | 245 |
| 54 | `google_apple_chrome_agreement.md` | `empirical_observation` | doc_0237 | 190 |
| 55 | `google_deleted_chat_logs.md` | `empirical_observation` | doc_0237 | 125 |
| 56 | `google_default_hypocrisy_argument.md` | `argument` | doc_0237 | 223 |
| 57 | `big_tech_antitrust_outlook.md` | `argument` | doc_0237 | 226 |
| 58 | `scotus_social_media_cases.md` | `concept` | doc_0256 | 196 |
| 59 | `texas_florida_moderation_laws.md` | `model` | doc_0256 | 285 |
| 60 | `first_amendment_editorial_judgment.md` | `argument` | doc_0256 | 171 |
| 61 | `scotus_ruling_consequences.md` | `counter_argument` | doc_0256 | 559 |
| 62 | `sbf_trial_arguments.md` ⇗ | `argument` | doc_0011 | 61 |
| 63 | `valor_applied_ai_thesis.md` | `argument` | doc_0161 | 265 |
| 64 | `going_infinite_lewis_account.md` ⇗ | `empirical_observation` | doc_0011 | 77 |

BB distribution: `empirical_observation` 36, `argument` 11, `concept` 6, `counter_argument` 4, `model` 4, `procedure` 3

⇗ marks a note **owned by another sub-plan** that this batch extends with a further source document instead of creating a second note on the same subject. This is the dedup rule doing its job: one note gaining a document is what lets a single retrieval satisfy several pieces of gold evidence, where two near-duplicate notes would split the evidence and lose both.

- `sbf_trial_arguments.md` — extended here with doc_0011
- `going_infinite_lewis_account.md` — extended here with doc_0011

## Coverage Accounting

```
doc         words  covered    pct  unassigned blocks
doc_0011     1195      872  73.0%  [0, 1, 2, 3, 4, 15, 16, 17, 19, 20, 21]
doc_0043     1205     1010  83.8%  [0, 1, 5, 6, 10, 13, 14, 19, 25, 26]
doc_0075     1934     1706  88.2%  [0, 1, 12, 25, 30, 33, 42, 43, 50]
doc_0098      950      950 100.0%  []
doc_0161     2103     2089  99.3%  [0]
doc_0188     1210     1210 100.0%  []
doc_0230     1630     1617  99.2%  [0, 31]
doc_0237     1222     1206  98.7%  [0, 28]
doc_0256     1246     1211  97.2%  [0, 1]

total 12,695 words, 11,871 covered (93.5%)
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

- This sub-plan owns `doc_0011,doc_0043,doc_0075,doc_0098,doc_0161,doc_0188,doc_0230,doc_0237,doc_0256`. A later batch may extend a note here with a
  further document; that is expected, and must never produce a second note on
  the same subject.
- Record any building block that stayed empty. Absence is a finding about the
  corpus, not a gap to fill.
