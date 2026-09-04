---
tags:
  - resource
  - technology
  - concept
keywords:
  - model fine tuning
  - fine-tuning
  - gpt-3
  - api
  - gpt-4
  - turbo
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0048, doc_0161]
enriched: web
external_refs: [https://developers.openai.com/api/docs/guides/model-optimization]
---

# Model Fine-Tuning

## Definition

In the corpus, model fine-tuning is the OpenAI capability that lets companies using GPT-3.5 Turbo or GPT-4 through the API continue training the model on their own data so it better fits their use case. In the corpus's most concrete example, OpenAI's fine-tuning of GPT-3.5 Turbo lets companies using the model through the API make it better follow specific instructions — such as always responding in a given language, formatting responses consistently, or matching a brand's tone — and shorten text prompts to speed up API calls and cut costs.

## Context

The corpus documents fine-tuning as a capability OpenAI progressively opened to developers alongside its paid APIs. OpenAI first brought fine-tuning to GPT-3.5 Turbo, partnering with Scale AI so companies could fine-tune the model, at published costs of $0.008 per 1K tokens for training, $0.012 per 1K tokens for usage input, and $0.016 per 1K tokens for usage output. It later extended fine-tuning to GPT-4, though the GPT-4 program involves more oversight and guidance from OpenAI teams than the GPT-3.5 program, largely due to technical hurdles. Separately, in TechCrunch's October 2023 survey of AI investors, fine-tuning is named as one of the distinct layers of the emerging LLM stack — alongside models and pre-training solutions — that sits in the middle layer connecting foundation models to specialized applications, together with prompt engineering and model orchestration.

## Key Characteristics

- **Continues training an existing model on customer data** — fine-tuning takes a model the customer already accesses through the API (e.g., GPT-3.5 Turbo, GPT-4) and continues training it on data the customer supplies.
- **Improves instruction-following and output style** — it can make a model better follow specific instructions, consistently format responses, and match a desired tone or brand voice.
- **Reduces prompt length and cost** — because the desired behavior is trained into the model, fine-tuning lets customers shorten text prompts, which speeds up API calls and cuts per-call cost.
- **Priced separately from inference** — OpenAI charged distinct per-token rates for fine-tuning training versus using (input/output) the fine-tuned model.
- **Oversight scales with model capability** — OpenAI applied more oversight and guidance to the GPT-4 fine-tuning program than to the GPT-3.5 program, citing technical hurdles.
- **A distinct layer of the LLM stack** — investors surveyed by TechCrunch treat fine-tuning tools as their own layer of the GenAI tech stack, separate from foundation model providers and end-user applications.

## Background (external)

Outside the corpus, OpenAI's own documentation describes fine-tuning more generally as letting a developer "take an OpenAI base model, provide the kinds of inputs and outputs you expect" so the model is adapted to a specific task rather than replaced with a newly trained one (OpenAI, "Model optimization," accessed 2026-09-02, https://developers.openai.com/api/docs/guides/model-optimization).

## Related Notes

- [OpenAI Developer Platform And API Releases](openai_developer_platform_and_api_releases.md): describes OpenAI's rollout of fine-tuning to GPT-3.5 Turbo and GPT-4, including its pricing and the Scale AI partnership, from the same source document.
- [GPT Model Releases From GPT-3.5 To GPT-4](gpt_model_releases_from_gpt35_to_gpt4.md): notes that ChatGPT itself is a fine-tuned version of GPT-3.5, showing fine-tuning as the mechanism that turned a base model into a general-purpose chatbot.
- [The Four Layers Of The GenAI Tech Stack](llm_stack_layers.md): situates fine-tuning tools as one of the middle-layer capabilities of the LLM stack that investors expect specialized startups to build around.
- [Valor VC's Applied AI Thesis](valor_applied_ai_thesis.md): from the same investor survey, contrasts fine-tuning as a stack-layer specialization with Valor's "applied AI" posture of solving customer problems directly.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [AI Startup Defensibility](ai_startup_defensibility.md)

## Source

- doc_0048: TechCrunch, 2023-09-28 — describes OpenAI's GPT-3.5 Turbo and GPT-4 fine-tuning programs, their purpose, pricing, and oversight differences, and notes ChatGPT as a fine-tuned version of GPT-3.5.
- doc_0161: TechCrunch, 2023-10-13 — investor survey naming fine-tuning tools as a distinct layer of the emerging LLM stack, connecting foundation models to specialized applications.
