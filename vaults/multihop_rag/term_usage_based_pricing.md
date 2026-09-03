---
tags:
  - resource
  - technology
  - concept
keywords:
  - usage based pricing
  - usage-based
  - periodic
  - saas
  - consumption
  - mediterranean
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0161]
enriched: web
external_refs: ["https://en.wikipedia.org/wiki/Software_as_a_service"]
---

# Usage-Based Pricing

## Definition

In the corpus, usage-based pricing (also called consumption pricing) is the charging model that VCs discuss as the one whose "trajectory... has organically aligned with the needs of large language models," with OpenAI's per-token API pricing cited as the motivating example, in contrast to conventional periodic SaaS pricing.

## Context

In the corpus the term surfaces in a TechCrunch roundup of venture capitalists discussing how AI startups should charge for AI-powered tooling, prompted directly by "the OpenAI pricing schema based on tokens and usage."
Rick Grinnell of Glasswing Ventures frames usage-based pricing as the model whose "trajectory... has organically aligned with the needs of large language models," because prompt/output sizes and per-user resource consumption vary significantly from one request to the next.
Lisa Calhoun of Valor VC makes the mechanism concrete: companies like OpenAI charge largely "by the token," which she calls "a very different metric than most cloud computing," and notes cost monitoring may be a key aspect of tracking that metric.
The same discussion frames usage-based pricing as one leg of a three-way choice facing AI startups, alongside conventional periodic SaaS pricing and hybrid structures that blend the two.

## Key Characteristics

- **Cost tracks consumption, not time** — charges scale with resource use (e.g., tokens processed) rather than a fixed subscription period.
- **Aligned with LLM cost structure** — the model fits large language models well because compute cost per request varies with prompt/output size and per-user resource utilization; OpenAI itself reportedly spends upward of $700,000 per day on compute, making usage-based allocation a way to recover those variable costs.
- **Unpopular for budgeting** — tying all costs to volume is "generally unpopular with end users," who prefer the predictability of a fixed periodic fee.
- **Not universal across AI products** — applications that don't rely on an LLM as a backbone, and that make no direct token calls to a model provider, tend to gravitate toward conventional periodic SaaS pricing instead.
- **Persists via hybrid structures** — as LLM adoption widens, vendors are expected to combine tiered periodic payments and usage limits for smaller customers with uncapped usage-based tiers for larger enterprises, rather than replacing usage-based pricing outright.
- **Tied to data dependency** — because large language technology remains heavily dependent on continuous data inflow, the source article argues usage-based pricing is unlikely to disappear even as the market matures.

## Background (external)

Outside this corpus, usage-based pricing (also called pay-per-usage) is a general software/SaaS revenue model: charges are calculated from measured consumption — "the number of users, transactions, amount of storage space used, or other metrics" — rather than a flat recurring fee, and Wikipedia notes many buyers favor it because they see themselves as "relatively light users of the software," while it can create revenue uncertainty and added billing overhead for the seller. (Wikipedia, "Software as a service," accessed 2026-09-02: https://en.wikipedia.org/wiki/Software_as_a_service)

## Related Notes

- [Pricing Models For AI Products](ai_pricing_models.md): the broader three-way framework (usage-based, periodic SaaS, hybrid) in which usage-based pricing is one structure, drawn from the same source document.
- [ChatGPT Subscription Tiers And Pricing](chatgpt_subscription_tiers_and_pricing.md): shows the conventional periodic SaaS alternative — flat monthly tiers — that usage-based pricing is contrasted against in the corpus.
- [Bolt Mobility's Distance-Based Pricing](bolt_mobility_distance_based_pricing.md): a non-AI example of the same underlying idea — charging by measured usage (distance ridden) rather than a flat fee — applied in micromobility.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [Amot Investments' Portfolio And War Scenario Assessment](amot_investments_portfolio_and_war_scenario_assessment.md)
- [Apple M3 Chip Architecture And GPU Features](apple_m3_chip_architecture_and_gpu_features.md)
- [Bank of Israel Interest Rate Policy During the War](bank_of_israel_interest_rate_policy_during_the_war.md)
- [Cavefish Ketogenic Diet Behavioral Results](cavefish_ketogenic_diet_behavioral_results.md)
- [China Recovery Greenshoots and Commodity Price Outlook](china_recovery_greenshoots_and_commodity_price_outlook.md)
- [Digital Twins Deployed for Sustainability Goals](digital_twins_deployed_for_sustainability_goals.md)
- [Discord's Shop, Remix And Client Improvements](discord_shop_remix_and_client_improvements.md)
- [Global Policy Responses To Ultra-Processed Foods](global_policy_responses_to_ultra_processed_foods.md)
- [IMF Assessment of India and Global Growth Divergence](imf_assessment_of_india_and_global_growth_divergence.md)
- [India Nominal GDP Forecast to 2030](india_nominal_gdp_forecast_to_2030.md)
- [iPad 9th Generation Holiday Deal](ipad_9th_generation_holiday_deal.md)
- [Israeli Sectors Most Exposed to War Damage](israeli_sectors_most_exposed_to_war_damage.md)
- [The 2023 Luminate Study Of TikTok And Music](luminate_tiktok_music_study_2023.md)
- [The Mediterranean Lifestyle UK Biobank Mortality Study](mediterranean_lifestyle_uk_biobank_mortality_study.md)
- [The MEDLIFE Mediterranean Lifestyle Index](medlife_mediterranean_lifestyle_index.md)
- [NTPC's H1 FY24 Operating Performance](ntpc_h1_fy24_operating_performance.md)
- [Reliance Jio Telecom Growth Outlook](reliance_jio_telecom_growth_outlook.md)
- [Reliance Retail Ventures Store Expansion](reliance_retail_ventures_store_expansion.md)
- [Siesta Napping and Mortality Uncertainty](siesta_napping_and_mortality_uncertainty.md)
- [Why Spanish-Language Music Keeps Growing Globally](spanish_language_music_global_growth.md)
- [62% Of US TikTok Users Pay For Music Streaming](tiktok_users_music_streaming_subscription_rate.md)
- [Twitch as an Alternative Sports Viewing Platform](twitch_as_an_alternative_sports_viewing_platform.md)
- [The University Of Michigan Review Of Ultra-Processed Food Addiction](university_of_michigan_ultra_processed_food_addiction_review.md)
- [Valor VC's Applied AI Thesis](valor_applied_ai_thesis.md)
- [What Positive Thinking Is and Is Not](what_positive_thinking_is_and_is_not.md)

## Source

- doc_0161: TechCrunch, 2023-10-13 — VC roundup defining and discussing usage-based/consumption pricing for AI startups, including OpenAI's token-based pricing as the motivating case.
