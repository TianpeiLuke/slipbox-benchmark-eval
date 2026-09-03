---
tags:
  - resource
  - technology
  - concept
keywords:
  - foundation model
  - layer
  - models
  - stack
  - applications
  - reporting
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0161, doc_0313]
---

# Foundation Model

## Definition

A foundation model is a large AI model — trained by a small set of well-resourced providers — that sits at the base of the generative-AI stack and is adapted or built upon by other tools and applications, rather than being the end product itself.

## Context

In the corpus the term surfaces in two distinct settings: market structure and government regulation. In a TechCrunch survey of venture capitalists on the emerging LLM stack, Glasswing Ventures' Rick Grinnell divides the generative-AI landscape into four layers — foundation model providers, middle-tier companies, end-market/top-layer applications, and full-stack vertical companies — with foundation models sitting at the base layer that middle-layer tooling and top-layer applications are built on top of. He names Alphabet/Google's Bard, Microsoft/OpenAI's GPT-4, and Anthropic's Claude as examples of this foundational layer. Separately, in coverage of the Biden Administration's AI executive order, "foundation model" is the regulatory unit the order targets: it directs new reporting standards specifically for developers whose foundation models might affect national or economic security.

## Key Characteristics

- **Base-layer position** — foundation models sit beneath the middle tier (fine-tuning, prompt engineering, orchestration) and the application layer in the GenAI tech stack; other companies build and compete on top of them rather than replacing them.
- **Concentrated provider set** — the layer is dominated by a small number of large players (Alphabet/Google, Microsoft/OpenAI, Anthropic), whose advantages in data access, talent, and compute are expected to push this layer toward an oligopolistic structure akin to the cloud-provider market, tempered by open-source alternatives.
- **Reused across applications** — applications "blend" foundation models with in-house middle-layer tooling to build specialized, defensible products, rather than starting from scratch.
- **Trigger for regulatory reporting** — under the White House AI executive order, a company training any foundation model that poses a serious risk to national security, economic security, or public health/safety must notify the federal government when training the model and share red-team safety test results before public release.
- **High-capability threshold for regulation** — the EO's reporting duty is scoped to a computational threshold (10^26 petaflops) beyond the capacity of existing models at the time, so it targets only the next generation of the largest foundation models, not models currently on the market or built by small/independent developers.

## Related Notes

- [The Four Layers Of The GenAI Tech Stack](llm_stack_layers.md): lays out the layer model in which foundation model providers form the base layer.
- [Foundation Model Reporting And Red-Team Disclosure Under The EO](foundation_model_reporting_and_red_team_disclosure.md): the regulatory reporting procedure that specifically targets high-risk foundation models.
- [AI Startup Defensibility](ai_startup_defensibility.md): argues startups build defensibility by blending foundation models with proprietary data and middle-layer tooling rather than competing at the foundation-model layer itself.
- [The "General Purpose AI" Terminology Choice In The EU AI Act](general_purpose_ai_terminology_choice_in_eu_ai_act.md): shows a regulator (the EU) deliberately avoiding the industry term "foundation model" in favor of "general purpose AI model."

## Source

- doc_0161: TechCrunch, 2023-10-13 — describes foundation model providers as the base layer of the GenAI tech stack and names Bard, GPT-4, and Claude as examples.
- doc_0313: Engadget, 2023-10-30 — the AI executive order's reporting and red-team disclosure requirements for foundation models posing national-security risk.
