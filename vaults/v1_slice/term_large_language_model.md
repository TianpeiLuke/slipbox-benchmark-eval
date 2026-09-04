---
tags:
  - resource
  - business
  - technology
  - concept
keywords:
  - large language model llm
  - llms
  - chatgpt
  - openai
  - proprietary
  - gpt-3
topics:
  - Business
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0027, doc_0054, doc_0099, doc_0161, doc_0048]
---

# Large Language Model (LLM)

## Definition

A large language model (LLM) is a neural network trained to learn from enormous amounts of digital text — Wikipedia articles, digital books, message boards — so that it can generate text on its own.

## Context

The corpus traces the term to OpenAI's GPT-3, described as the neural network Dario Amodei's team built by analysing "countless Wikipedia articles, digital books and message boards" so it "could generate text on its own," released in the summer of 2020; it also "had the unfortunate habit of making things up." ChatGPT itself runs on GPT, the LLM lineage OpenAI had developed since 2016, iterating from GPT-1 (2018) to GPT-3 (June 2020) before GPT-3.5 powered ChatGPT's November 2022 launch. In the venture-capital view of the AI market, LLMs sit at the base "foundation model" layer of a broader stack — models, pre-training solutions, fine-tuning tools, middle-layer tooling, and end-market applications — with providers such as OpenAI's GPT-4, Google's Bard, and Anthropic's Claude expected to consolidate into an oligopolistic structure resembling the cloud-provider market. OpenAI's GPT-X models are repeatedly described as proprietary LLMs that other companies build businesses on top of, a dependency that became visible when the November 2023 OpenAI board upheaval led customers to contact rival LLM providers (Anthropic, Google, Cohere) out of concern for continuity.

## Key Characteristics

- **Trained on enormous text corpora** — LLMs learn by analysing vast amounts of digital text (Wikipedia, books, message boards) rather than following hand-written rules.
- **Generative** — once trained, an LLM can generate text on its own in response to a prompt.
- **Prone to fabrication and privacy leakage** — GPT-3 had "the unfortunate habit of making things up," and a Google DeepMind-led test found that prompting ChatGPT to repeat a word endlessly caused OpenAI's LLM to surface private, identifiable information (email addresses and similar) from its training data; a separate Microsoft-affiliated study found GPT-4 more easily "jailbroken" into unsafe outputs than other LLMs.
- **Costly to run and usage-priced** — LLM economics are dominated by compute cost (OpenAI was reported to spend roughly $700,000/day on compute), which is why LLM providers commonly bill by token/usage rather than flat SaaS pricing.
- **Anchors a layered AI stack** — LLMs form the "foundation model" layer beneath middle-layer tooling (fine-tuning, prompt engineering, model orchestration, observability) and top-layer applications that startups build against.
- **Split between proprietary and open approaches** — OpenAI's GPT-X models are proprietary LLMs, contrasted in the corpus with Meta's Llama family and other efforts pushing more "open" LLM development, a split that intensified after a leaked internal Google memo argued neither OpenAI nor Google had a durable "moat" against open-source LLMs.

## Related Notes

- [GPT Model Lineage and ChatGPT Launch](gpt_model_lineage_and_chatgpt_launch.md): the specific LLM lineage (GPT-1 through GPT-3.5/GPT-4) that ChatGPT is built on.
- [Prediction Limits of Monolithic LLMs](prediction_limits_of_monolithic_llms.md): documents the fabrication, bias, and reliability limits inherent to single, large-scale LLMs.
- [ChatGPT FAQ: Basics and Definitions](chatgpt_faq_basics_and_definitions.md): explains ChatGPT as a chatbot application built on top of an underlying LLM.
- [Google's "No Moat" Memo and Open-Source AI](google_no_moat_memo_open_source_ai.md): the leaked memo arguing proprietary LLMs from OpenAI and Google lack a durable advantage over open-source alternatives.
- [Enterprise Generative AI Adoption Caution](enterprise_generative_ai_adoption_caution.md): describes enterprises' cautious, slow adoption of LLM-based generative AI tools.
- [AI Pricing Models](ai_pricing_models.md): the token/usage-based pricing schemes that LLM providers like OpenAI commonly use.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [AI Startup Defensibility](ai_startup_defensibility.md)
- [Amazon's Offline Guardrail Pipeline For Alexa Kids Generative AI](alexa_kids_llm_guardrails.md)
- [Alexa Kids Data Handling And The Echo Pop Kids Launch](alexa_kids_privacy_and_hardware.md)
- [Anthropic's Fair Use Defense For AI Training](anthropic_fair_use_defense_for_ai_training.md)
- [Anthropic's Founding By Former OpenAI Researchers](anthropic_founding_by_openai_researchers.md)
- [ChatGPT Competitors And Alternatives](chatgpt_competitors_and_alternatives.md)
- [ChatGPT Security Incidents And Malicious Use](chatgpt_security_incidents_and_malicious_use.md)
- [ChatGPT Third-Party Integrations And Ecosystem](chatgpt_third_party_integrations_and_ecosystem.md)
- [China Versus Overseas: The Dual-Market Strategy](china_versus_overseas_dual_market_strategy.md)
- [Deft, The E-Commerce Search Startup](deft_ecommerce_search_startup.md)
- [French AI Startups' State Backing And Compliance Edge](french_ai_startups_state_backing_and_compliance_edge.md)
- [Independent Research And Reviews Of ChatGPT's Flaws](independent_research_and_reviews_of_chatgpt_flaws.md)
- [Llama's Open Source Licensing Limits](llama_open_source_licensing_limits.md)
- [The Four Layers Of The GenAI Tech Stack](llm_stack_layers.md)
- [Mistral AI, The French LLM Startup](mistral_ai_french_llm_startup.md)
- [The OpenAI Crisis As A Case Against Centralized AI Control](openai_crisis_risk_of_centralized_ai_control.md)
- [OpenAI's Nonprofit-To-For-Profit Structure](openai_nonprofit_to_for_profit_structure.md)
- [OpenAI's Q4 2023 Product Launches](openai_q4_2023_product_launches.md)
- [Startups' Over-Reliance On OpenAI's Proprietary Models](startup_over_reliance_on_openai_proprietary_models.md)
- [Tidalflow Exits Stealth With Gradient Ventures Backing](tidalflow_llm_integration.md)
- [UMG's USCO Filing Rejecting Fair Use For AI Training](umg_usco_filing_rejects_fair_use.md)
- [Valor VC's Applied AI Thesis](valor_applied_ai_thesis.md)

## Source

- doc_0027: The Age, 2023-12-09 — origin of GPT-3 as a large language model trained on Wikipedia, books, and message boards, and its tendency to fabricate content.
- doc_0054: TechCrunch, 2023-11-21 — OpenAI's proprietary GPT-X LLMs and startups' reliance on them; the "no moat" memo on proprietary vs. open-source LLMs.
- doc_0099: Engadget, 2023-11-30 — GPT as the LLM underlying ChatGPT, and its development timeline from GPT-1 to GPT-3.5.
- doc_0161: TechCrunch, 2023-10-13 — the layered AI/LLM tech stack, foundation model providers, and LLM usage-based pricing economics.
- doc_0048: TechCrunch, 2023-09-28 — privacy leakage and jailbreak/trustworthiness research findings about OpenAI's LLMs, including GPT-4.
