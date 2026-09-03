---
tags:
  - resource
  - technology
  - concept
keywords:
  - llm observability
  - monitoring
  - datadog's
  - monte
  - calhoun
  - barr
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0161, doc_0243]
---

# LLM Observability

## Definition

LLM observability, as the corpus uses the term, is tooling exemplified by Datadog's LLM observability tool that occupies the "middle layer" of the generative-AI stack, sitting between foundation-model providers and the specialized business applications built on top of them, with its value judged by whether it succeeds at monitoring AI performance bottlenecks.

## Context

In the corpus the term surfaces in TechCrunch's October 2023 investor survey on how AI startups can capture and defend market share: Rick Grinnell (Glasswing Ventures) and Lisa Calhoun (Valor VC) are both asked whether Datadog's release of an LLM observability tool — and similar output from incumbent tech powers — will curtail the market area available to startups. Grinnell places LLM observability squarely in the middle layer, "acting as a catalyst for specialized business applications to use foundational models," and names Datadog, New Relic, and Splunk as incumbents that have all produced LLM observability tools and are putting significant R&D dollars behind them. Calhoun frames the same tools more conditionally: they can only help drive acceptance of AI tools if they succeed in monitoring AI performance bottlenecks, which she calls largely unexplored territory still due for change and maturing. A second, adjacent term appears elsewhere in the corpus — Barr Moses, CEO of Monte Carlo, is described as running a "data observability" startup and co-authoring a book on building trustworthy data pipelines. Data observability concerns the reliability of data pipelines generally, whereas LLM observability is the AI-era specialization of that idea, aimed specifically at monitoring foundation-model-based applications.

## Key Characteristics

- **Middle-layer positioning** — LLM observability sits between foundation models and the specialized applications built on them, rather than being a foundation-model or end-application product itself.
- **Incumbent-led early market** — established monitoring vendors (Datadog, New Relic, Splunk) moved into LLM observability early and are investing heavily in it, which both VCs flag as a possible constraint on startup opportunity in the space.
- **Performance-bottleneck monitoring** — Calhoun frames the core unproven capability as monitoring AI performance bottlenecks, work she describes as still largely unexplored.
- **Cost/token monitoring as a likely component** — because LLM providers like OpenAI charge largely "by the token," a metric very different from typical cloud-computing billing, cost monitoring is flagged as a probable extension of LLM observability tooling.
- **Distinct from, but adjacent to, data observability** — data observability (e.g., Monte Carlo) addresses data-pipeline reliability broadly; LLM observability is the narrower, AI-stack-specific descendant of that same monitoring instinct.

## Related Notes

- [AI Startup Defensibility](ai_startup_defensibility.md): argues that LLM observability's incumbent-led middle layer is a weaker position for startups than the application layer, using the same Datadog/New Relic/Splunk evidence.
- [Valor Applied AI Thesis](valor_applied_ai_thesis.md): gives Lisa Calhoun's conditional take on whether LLM observability tools like Datadog's curtail startup opportunity, centered on unproven performance-bottleneck monitoring.
- [Barr Moses Recommends Dare To Lead](barr_moses_recommends_dare_to_lead.md): introduces the adjacent concept of data observability (Monte Carlo) that LLM observability specializes for the AI stack.

## Source

- doc_0161: TechCrunch, 2023-10-13 — Grinnell and Calhoun both discuss Datadog's LLM observability tool, its middle-layer position, and whether it curtails startup opportunity.
- doc_0243: TechCrunch, 2023-12-01 — introduces Barr Moses and Monte Carlo's data observability work, the adjacent concept referenced for contrast.
