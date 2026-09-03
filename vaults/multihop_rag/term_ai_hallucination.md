---
tags:
  - resource
  - technology
  - concept
keywords:
  - ai hallucination
  - tendency
  - hallucinate
  - fabricated
  - chatgpt's
  - incident
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0099, doc_0188]
enriched: web
external_refs: [https://www.ibm.com/think/topics/ai-hallucinations]
---

# AI Hallucination

## Definition

AI hallucination, in the corpus, is the tendency of a generative AI system — a large language model — to produce fabricated content: ChatGPT's "tendency to hallucinate facts and figures," illustrated by a fabricated legal-citation incident, and Alexa's capacity, per Amazon, to "be led astray or 'hallucinate' answers."

## Context

In the corpus the term surfaces in two very different settings that share the same underlying risk.

The first is ChatGPT's real-world track record: its "tendency to hallucinate facts and figures" produced a documented incident in which a New York lawyer used the chatbot for "legal research" and was given "a number of entirely made-up, nonexistent cases to cite in his argument," which he then filed without independently verifying them.

The second is a product-design setting: Amazon, in building the "Explore with Alexa" conversational AI feature for children, explicitly names hallucination as one of the two core risks the product has to design around, noting that "generative AI can be led astray or 'hallucinate' answers, while kids could ask inappropriate questions."

Across both cases hallucination is treated not as an occasional glitch but as an inherent property of generative AI systems that any deployment — whether a general-purpose chatbot or a child-safety-scoped assistant — must account for.

## Key Characteristics

- **Fabrication, not error-correction failure** — the model does not merely get a fact wrong; it invents content (fake case citations, made-up figures) that did not exist.
- **Plausibility is the danger** — the fabricated case citations were credible enough that the lawyer who received them filed them "without bothering to independently validate any of them."
- **Treated as a known, recurring property of generative AI** — both docs frame hallucination with a definite article ("its tendency to hallucinate," "generative AI can be led astray or 'hallucinate'"), not as a one-off bug.
- **Drives downstream mitigation design** — in the Alexa Kids case, hallucination is named alongside kids asking inappropriate questions as one of the risks Amazon built guardrails around, generating content offline and running it through a human-and-AI review process rather than hooking kids up to an LLM at runtime.

## Background (external)

More broadly (outside this corpus), AI hallucinations are cases where an AI system generates outputs that seem believable but are actually incorrect, unrelated, or completely made up — such as fake facts, invented studies, or nonexistent sources presented as if true (IBM, "What Are AI Hallucinations?", accessed 2026-09-02, https://www.ibm.com/think/topics/ai-hallucinations).

## Related Notes

- [ChatGPT Hallucination Legal Filing Incident](chatgpt_hallucination_legal_filing_incident.md): the concrete real-world incident — a lawyer sanctioned for filing ChatGPT's fabricated case citations — that instantiates this concept.
- [Alexa Kids LLM Guardrails](alexa_kids_llm_guardrails.md): documents Amazon's offline-review pipeline built specifically to guard against hallucinated (and inappropriate) content reaching children.
- [ChatGPT's Hallucination And Bias Limitations](chatgpt_hallucination_and_bias_limitations.md): broadens the concept into ChatGPT's general failure modes, tracing hallucination to its next-word-prediction training method and to further consequences (Stack Overflow bans, defamation claims).

## Source

- doc_0099: Engadget, 2023-11-30 — describes ChatGPT's tendency to hallucinate facts and figures, illustrated by the fabricated legal-citation incident.
- doc_0188: TechCrunch, 2023-10-25 — names hallucination as a core risk of generative AI that Amazon designed "Explore with Alexa" guardrails around.
