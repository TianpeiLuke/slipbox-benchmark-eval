---
tags:
  - resource
  - business
  - technology
  - concept
keywords:
  - cloud computing
  - compute
  - flops
  - multi-cloud
  - spending
  - incumbents
topics:
  - Business
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0027, doc_0054, doc_0161, doc_0525, doc_0564]
enriched: web
external_refs: [https://www.nist.gov/publications/nist-definition-cloud-computing]
---

# Cloud Computing

## Definition

Cloud computing, in the corpus, is the named vendor-run industry that Microsoft's OpenAI deal plugged into — when the deal closed in 2019, Microsoft "had a new way to build AI into its vast cloud computing service" — and that later commentary treats as the historical template for AI-market dynamics like vendor lock-in, market consolidation, and billing norms.

## Context

In the corpus, cloud computing shows up mainly as the historical precedent and infrastructural backbone for the current AI boom, rather than as a subject in its own right.

Commentators reach for the cloud computing industry to explain both OpenAI's near-collapse and the shape of the AI market that followed it: the industry became renowned for locking companies into "centralized, vortex-like silos," which is offered as the reason so many startups panicked and contacted OpenAI's rivals when OpenAI itself looked like it might disintegrate.

The same precedent is used to forecast how the AI market layers will settle: the foundation-model layer is expected to "settle into an oligopolistic structure like the cloud provider market," and, separately, incumbents in cloud computing (like those in the earlier internet buildout) are said to have kept innovating "until innovation becomes stagnant" — a pattern predicted to repeat for AI incumbents.

Cloud computing also appears as a budget line competing with AI spending — total AI spending has overtaken cloud computing spending even though cloud computing "remains critical" — and as a unit-economics contrast: AI compute is normally metered in raw processing terms (FLOPs) or dollars per day, a different and less mature billing metric than most cloud computing's established consumption pricing.

## Key Characteristics

- **Centralized, provider-hosted delivery** — cloud computing is a vendor's service that a customer builds on top of, illustrated by Microsoft's use of its "cloud computing service" as the integration point for OpenAI's models.
- **Lock-in and the multi-cloud response** — the cloud computing industry is described as having locked customers into single-vendor "silos," which pushed companies toward multi-cloud and hybrid strategies — a dynamic the corpus draws on directly to explain AI startups' current over-reliance on OpenAI.
- **Tendency toward an oligopolistic market structure** — cloud computing is used as the reference case for a market that consolidated around a few large "cloud provider" incumbents, the same structure forecast for the foundation-model layer of the AI stack.
- **Incumbent-innovate-then-stagnate pattern** — cloud computing (alongside the internet) is cited as a precedent where incumbents keep innovating only until the market matures and stagnates, opening room for new entrants.
- **Compute as a metered, regulable resource** — "compute" (processing capacity, measured in floating point operations or FLOPs) is treated as a quantifiable input separate from "cloud computing" as an industry, and it is significant enough that the EU AI Act sets its high-risk regulatory threshold for general-purpose AI models directly on cumulative training compute (10^25 FLOPs).
- **Distinct billing norms from AI compute** — cloud computing has settled consumption-pricing conventions, whereas AI compute costs (e.g., OpenAI's roughly $700,000/day compute spend) are tracked and priced differently, "a very different metric than most cloud computing."

## Background (external)

More broadly (outside this corpus), cloud computing is a model for enabling ubiquitous, convenient, on-demand network access to a shared pool of configurable computing resources — such as networks, servers, storage, applications, and services — that can be rapidly provisioned and released with minimal management effort (NIST, "NIST Definition of Cloud Computing", accessed 2026-09-02, https://www.nist.gov/publications/nist-definition-cloud-computing).

## Related Notes

- [AI Market Spending Forecasts Reported In October 2023](ai_market_spending_forecasts.md): reports the figure that total AI spending has already overtaken cloud computing spending even though cloud computing remains critical.
- [Startups' Over-Reliance On OpenAI's Proprietary Models](startup_over_reliance_on_openai_proprietary_models.md): draws its central analogy directly from the cloud computing industry's history of vendor lock-in and the multi-cloud/hybrid response it provoked.
- [The Four Layers Of The GenAI Tech Stack](llm_stack_layers.md): predicts the foundation-model layer will settle into an oligopolistic structure "like the cloud provider market," borrowing cloud computing's market structure as the forecasting template.
- [AI Startup Defensibility](ai_startup_defensibility.md): cites the internet and cloud computing as prior cases where incumbents kept innovating only until the market matured and stagnated, to argue startups still have room to disrupt the AI layer.
- [Pricing Models For AI Products](ai_pricing_models.md): contrasts AI's usage-based, per-token compute costs (e.g. OpenAI's ~$700,000/day compute spend) with the more settled billing conventions of traditional cloud computing.
- [EU AI Act Two-Tier Rules For General Purpose AI](eu_ai_act_two_tier_rules_for_general_purpose_ai.md): sets its high-risk regulatory tier for general-purpose AI models using a compute threshold (10^25 FLOPs), treating compute as the measurable resource the law regulates.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [France And Mistral's Opposition To The GPAI Rules](france_and_mistral_opposition_to_gpai_rules.md)
- [MacBook Pro Design, Ports And The Space Black Finish](macbook_pro_design_ports_and_space_black_finish.md)
- [Musk's Founding Of OpenAI And His Departure](musk_openai_founding_and_departure.md)
- [Prediction: The Limits Of Monolithic LLMs](prediction_limits_of_monolithic_llms.md)
- [Valor VC's Applied AI Thesis](valor_applied_ai_thesis.md)

## Source

- doc_0027: The Age, 2023-12-09 — Microsoft's 2019 OpenAI investment gave it "a new way to build AI into its vast cloud computing service."
- doc_0054: TechCrunch, 2023-11-21 — cloud computing's history of vendor lock-in ("centralized, vortex-like silos") is cited as precedent for AI startups' over-reliance on OpenAI, and for the multi-cloud/hybrid shift that followed.
- doc_0161: TechCrunch, 2023-10-13 — cloud computing cited as precedent for incumbent-innovate-then-stagnate market dynamics, as the model for an oligopolistic "cloud provider market," as a budget line AI spending has now surpassed, and as a billing-metric contrast with AI compute pricing.
- doc_0525: TechCrunch, 2023-12-11 — explains that the EU AI Act's general-purpose-AI threshold is defined by cumulative training compute measured in FLOPs, set at 10^25.
- doc_0564: TechCrunch, 2023-12-09 — confirms the same compute-based FLOPs threshold (10^25) as the trigger for "high-impact" GPAI obligations under the EU AI Act.
