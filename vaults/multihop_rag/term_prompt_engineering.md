---
building_block: concept
source_docs: [doc_0161]
enriched: web
external_refs:
  - https://en.wikipedia.org/wiki/Prompt_engineering (Wikipedia, accessed 2026-09-02)
---

# Prompt Engineering

## Definition

Prompt engineering is one of the specialized capabilities that make up the "middle layer" of the generative AI/LLM tech stack — the layer that sits between foundation model providers and end-market applications and connects the foundational aspects of AI to the refined, specialized application layer.

## Context

The term appears in a TechCrunch survey of venture capitalists on how startups can capture and defend market share in the AI era, where Glasswing Ventures' Rick Grinnell lays out a four-layer view of the generative AI stack: foundation model providers, middle-tier companies, end-market/top-layer applications, and full-stack vertical companies. Prompt engineering is named as one of the "cutting-edge capabilities" of that middle tier, grouped alongside model fine-tuning and agile model orchestration, and it is this middle layer where Grinnell anticipates the rise of companies "akin to Databricks." Grinnell frames the middle layer as strategically weaker than the application layer: foundation-model providers are expanding into middle-layer tooling and established market leaders are entering the space too, which heightens commoditization risk for startups that build only prompt-engineering or orchestration tooling rather than full-stack, vertically integrated applications.

## Key Characteristics

- **Middle-layer capability** — grouped with model fine-tuning and model orchestration as one of the specialized tools that connect foundation models to application-layer software.
- **Commoditization exposure** — because foundation-model providers and incumbents are both moving into this layer, startups built purely around prompt engineering face heightened competitive risk relative to the application layer.
- **Grouped, not detailed** — the survey names prompt engineering alongside fine-tuning and orchestration as a middle-layer capability but does not describe what the practice itself involves.

## Background (external)

The corpus names prompt engineering as a middle-layer capability but does not explain what the practice itself consists of. Per Wikipedia, prompt engineering is the practice of structuring natural language inputs ("prompts") to guide a generative AI model toward a desired output, and the Oxford English Dictionary defines it as "the action or process of formulating and refining prompts for an artificial intelligence program" (Wikipedia, *Prompt engineering*, accessed 2026-09-02). The practice is described as highly sensitive to phrasing, example ordering, and formatting, and largely model-specific — a technique that helps one model can hurt another — with common techniques including few-shot (multi-shot) prompting, chain-of-thought prompting, self-consistency, tree-of-thought, role assignment, and retrieval-augmented generation (Wikipedia, *Prompt engineering*, accessed 2026-09-02).

## Related Notes

- [AI Startup Defensibility](ai_startup_defensibility.md): the argument note built from the same survey, which names prompt engineering as a middle-layer capability and situates it within the broader defensibility framework for AI startups.
- [ChatGPT FAQ: Basics And Definitions](chatgpt_faq_basics_and_definitions.md): defines the "prompt" that a user enters into a chatbot like ChatGPT — the object that prompt engineering is the practice of crafting.
- [Robust Intelligence's Jailbreak Of Gemini Pro](gemini_pro_jailbreak_by_robust_intelligence.md): shows adversarial prompt manipulation ("jailbreaks") of a generative model's guardrails, a related but distinct use of crafted prompts.

## Source

- doc_0161: TechCrunch, 2023-10-13 — names prompt engineering as one of the middle layer's cutting-edge capabilities, alongside model fine-tuning and agile model orchestration, in the generative AI tech stack.
