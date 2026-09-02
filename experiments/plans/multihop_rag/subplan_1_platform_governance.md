---
tags:
  - plan
  - digestion
  - benchmark
keywords:
  - multihop rag subplan
  - platform governance notes
  - section coverage map
topics:
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-02
status: active
building_block: navigation
---

# Sub-plan 1: Platform Governance (8 documents)

Note table for the first batch of the MultiHop-RAG pilot slice. Shared decisions
— routing, format, gates, quarantine — are in the
[master plan](plan_digest_multihop_rag_slice.md) and are not repeated here.

**Documents**: doc_0009, doc_0010, doc_0030 (FTX trial) · doc_0024, doc_0025,
doc_0195 (EU/X) · doc_0106, doc_0335 (Meta) — 11,588 words, minimum 11 notes.

These eight were read in full before this table was written.

## Density Treatment

| Doc | Words | Rule triggered | Min notes |
|---|---|---|---|
| doc_0009 | 1,194 | ≤1200, 1 note likely | 1 |
| doc_0010 | 942 | ≤1200, 1 note likely | 1 |
| doc_0030 | 1,433 | 1200–1800, mixed BB → split | 2 |
| doc_0024 | 1,163 | ≤1200, 1 note likely | 1 |
| doc_0025 | 1,797 | 1200–1800, mixed BB → split | 2 |
| doc_0195 | 1,154 | ≤1200, 1 note likely | 1 |
| doc_0106 | 2,929 | 1800–3600, MUST split ≥2 | 2 |
| doc_0335 | 976 | ≤1200, 1 note likely | 1 |

## Planned Notes

| # | Note | BB | Source docs | Covers |
|---|---|---|---|---|
| 1 | `sbf_trial.md` | empirical_observation | doc_0009, doc_0010, doc_0030 | charges, schedule, jury, courtroom access, week-by-week testimony |
| 2 | `sam_bankman_fried.md` | concept | doc_0009, doc_0010, doc_0030 | who he is, roles, arrest, bail, plea, sentence exposure |
| 3 | `ftx.md` | concept | doc_0009, doc_0010, doc_0030 | the exchange, founding, peak valuation, investors, marketing, bankruptcy |
| 4 | `alameda_research.md` | concept | doc_0009, doc_0010 | the trading firm and its undisclosed relationship to FTX |
| 5 | `ftx_alameda_fund_flow.md` | model | doc_0009, doc_0010 | customer deposits → Alameda → deployment; the FTT collateral loop and the run |
| 6 | `sbf_trial_arguments.md` | argument | doc_0009, doc_0030 | prosecution vs defense; intent vs incompetence |
| 7 | `sbf_political_and_media_profile.md` | empirical_observation | doc_0030, doc_0010 | Lewis account, political access, the $5B Trump claim, celebrity deals |
| 8 | `digital_services_act.md` | concept | doc_0024, doc_0025, doc_0335 | DSA obligations, VLOP designation, Articles 36/66, penalties, crisis mechanism timing |
| 9 | `eu_enforcement_against_x.md` | empirical_observation | doc_0024, doc_0025 | Breton letter, formal RFI, deadlines, X's reply, parallel TikTok/Meta warnings |
| 10 | `x_moderation_capacity.md` | model | doc_0024, doc_0025 | layoffs, verification changes, Community Notes; why crisis load breaks it |
| 11 | `disinformation_on_x_israel_hamas.md` | empirical_observation | doc_0024, doc_0025 | the false-content examples, volume, casualty figures |
| 12 | `x_bot_countermeasures.md` | procedure | doc_0195 | $1 fee, payment/phone/ID verification, heuristics; the cost-imposition goal |
| 13 | `objections_to_x_bot_fee.md` | counter_argument | doc_0195 | Mullenweg on determined spammers; Vashistha on the digital divide |
| 14 | `meta_moderation_bias.md` | argument | doc_0106 | the bias-not-bug claim, with the 2021 report and EFF/7amleh findings as grounds |
| 15 | `meta_moderation_bias_mechanisms.md` | model | doc_0106 | dialect coverage, policy granularity, automation, regulatory gradient |
| 16 | `meta_response_to_suppression_claims.md` | counter_argument | doc_0106 | the Stories bug, the Live bug, and what the response does not address |
| 17 | `meta_crisis_response_measures.md` | procedure | doc_0335 | hostage policy, livestream priority, hashtag blocking, strike-free removals |

**17 planned against a floor of 11.** The floor is a minimum, not a target; the
excess comes from entity notes (2, 3, 4, 8) that serve several documents each
and from documents carrying two clearly distinct building blocks.

## Section Coverage Map

Articles in this corpus have no headings, so sections are the article's own
topic blocks, identified on reading.

```
doc_0009 SBF trial coverage (1,194w)
├── proceedings, schedule, jury, access ──── → note 1
├── Naftalis on taking the stand ─────────── → note 6
├── week 1/2/3 testimony ─────────────────── → note 1
├── fund flow described in testimony ─────── → note 5
└── opening statements (both sides) ──────── → note 6

doc_0010 How FTX got here (942w)
├── founding, funding, valuation ─────────── → note 3
├── marketing and celebrity deals ────────── → note 7
├── collapse: balance sheet, FTT, Binance ── → note 5
├── bankruptcy, Ray, Williams ────────────── → note 3
├── arrest, bail, plea, exposure ─────────── → note 2
├── cooperating witnesses ────────────────── → note 1
└── contagion: BlockFi, Genesis ──────────── → note 3

doc_0030 Lewis / $5B Trump claim (1,433w)
├── Going Infinite, 60 Minutes account ───── → note 7
├── political access, McConnell, Trump ───── → note 7
├── celebrity deals with figures ─────────── → note 7
├── reaction and criticism ───────────────── → note 6
└── intent vs incompetence framing ───────── → note 6

doc_0024 EU formal RFI (1,163w)      → notes 8, 9, 10
doc_0025 EU urgent warning (1,797w)  → notes 8, 9, 10, 11
doc_0195 X bot fee (1,154w)          → notes 12, 13
doc_0106 Meta bias (2,929w)          → notes 14, 15, 16
doc_0335 Meta crisis response (976w) → notes 8, 17
```

No source topic block is orphaned.

## Split Decisions

| Document | Split into | Rationale |
|---|---|---|
| doc_0030 (1,433w) | notes 6 + 7 | Mixed BB: the Lewis account is `empirical_observation`, the intent-vs-incompetence framing is `argument`, both well over 500 words |
| doc_0025 (1,797w) | notes 9 + 10 + 11 | Mixed BB across three types: enforcement events, capacity mechanism, observed content |
| doc_0106 (2,929w) | notes 14 + 15 + 16 | Exceeds 1,800 words, so a split is mandatory; the natural boundaries are claim / mechanism / rebuttal, which are three distinct building blocks |
| doc_0195 (1,154w) | notes 12 + 13 | Mixed BB: the measure is a `procedure`, the objections are a `counter_argument`. Under 1,200 words, but the BB rule takes precedence over the size rule |

## Cross-Reference Map

Entity notes are shared across documents; that sharing is what lets one note
satisfy several pieces of gold evidence.

| Note | Links out to |
|---|---|
| 1 `sbf_trial` | 2, 3, 5, 6 |
| 2 `sam_bankman_fried` | 1, 3, 4, 7 |
| 3 `ftx` | 2, 4, 5 |
| 4 `alameda_research` | 3, 5 |
| 5 `ftx_alameda_fund_flow` | 3, 4, 1 |
| 6 `sbf_trial_arguments` | 1, 2 |
| 7 `sbf_political_and_media_profile` | 2, 3 |
| 8 `digital_services_act` | 9, 10, 17 |
| 9 `eu_enforcement_against_x` | 8, 10, 11 |
| 10 `x_moderation_capacity` | 8, 9, 11 |
| 11 `disinformation_on_x_israel_hamas` | 9, 10 |
| 12 `x_bot_countermeasures` | 13, 10 |
| 13 `objections_to_x_bot_fee` | 12 |
| 14 `meta_moderation_bias` | 15, 16 |
| 15 `meta_moderation_bias_mechanisms` | 14, 8 |
| 16 `meta_response_to_suppression_claims` | 14 |
| 17 `meta_crisis_response_measures` | 8, 14 |

## Undigested Terms

Terms appearing across these documents that warrant glossary entries via
`capture-term-note`, which also bootstraps `vaults/multihop_rag/glossary.md`
since no glossary exists yet: FTT, VLOP, Community Notes, shadowbanning,
Chapter 11, Dangerous Organizations and Individuals policy.

## Related Notes

- [Master plan](plan_digest_multihop_rag_slice.md)
