---
building_block: concept
source_docs: [doc_0160, doc_0161, doc_0243]
---

# SaaS Pricing

## Definition

SaaS pricing is "conventional periodic" pricing for software-as-a-service products: customers pay recurring, predictable fees rather than being charged per unit of usage. The corpus frames it as one pole of a spectrum against usage-based (consumption) pricing, distinguished by whether the underlying cost driver is a fixed subscription versus variable resource consumption.

## Context

The corpus raises SaaS pricing directly in a TechCrunch piece interviewing six VCs about how AI startups should charge for AI-powered tooling. Within that piece, Rick Grinnell, founder and managing partner at Glasswing Ventures, was asked whether the recent slowdown in growth of consumption- or usage-based-priced tech products would push startups building modern AI tools toward more traditional SaaS pricing, a question prompted by OpenAI's own token- and usage-based pricing schema. Grinnell's answer ties the choice of pricing model to whether a large language model sits in the product's backbone: usage-based pricing has "organically aligned" with LLM-backed products because prompt and output sizes, and per-user resource utilization, vary significantly, and OpenAI itself is said to rack up upward of $700,000 per day on compute, so those operating costs need to be allocated effectively. Applications that do not rely on an LLM as a backbone, and that make no direct token calls to a model provider, can instead offer "conventional periodic SaaS pricing," and infrastructure or value-added layers for AI are described as likely to gravitate toward that strategy. Grinnell also describes a possible hybrid structure once LLM adoption becomes widespread — tiered periodic payments with usage limits for SMBs alongside uncapped usage-based tiers for larger enterprises — suggesting SaaS pricing is not necessarily displaced by usage-based pricing but can be combined with it. Separately, the corpus shows SaaS pricing already embedded in enterprise generative-AI cost discussions: TechCrunch reported that generative AI features carry "a higher cost ... in a SaaS product" as one of two ways enterprises pay for the technology, the other being paying per call to a large language model API when building software internally. The corpus also links the SaaS business model, of which SaaS pricing is the monetization mechanism, to recurring revenue: SaaS-growth consultant Georgiana Laudi's agency, Forget the Funnel, is built around helping SaaS businesses pursue "a customer-led approach for driving predictable, recurring revenue," consistent with SaaS pricing's periodic, subscription character.

## Key Characteristics

- **Periodic, not per-unit** — SaaS pricing charges customers on a recurring cadence rather than metering usage, in contrast to consumption/usage-based pricing.
- **Backbone-dependent choice** — whether a product relies on direct LLM token calls is presented as the deciding factor in whether usage-based or conventional SaaS pricing fits; products without an LLM backbone, or without direct token calls to a model provider, can use SaaS pricing.
- **Predictability as the buyer draw** — the corpus attributes SaaS pricing's appeal to end users' preference for budgetable, predictable costs over volume-tied billing.
- **Combinable with usage-based pricing** — a hybrid model (tiered periodic payments plus usage caps for SMBs, uncapped usage tiers for larger enterprises) is presented as a likely path once LLM adoption is widespread, rather than SaaS pricing and usage-based pricing being mutually exclusive.
- **Cost pass-through vector** — enterprises absorb generative-AI feature costs specifically as a higher price within their existing SaaS subscription, showing SaaS pricing as a channel through which vendor cost increases reach the customer.
- **Tied to recurring-revenue business models** — SaaS pricing is the monetization layer of a broader "predictable, recurring revenue" growth model that SaaS businesses are advised to pursue.

## Related Notes

- [Pricing Models For AI Products](ai_pricing_models.md): sets out the fuller three-way framework — usage-based, conventional SaaS, and hybrid — of which SaaS pricing is one structure, drawn from the same source document.
- [Enterprise Caution On Generative AI Adoption](enterprise_generative_ai_adoption_caution.md): documents the same passage where generative-AI features raise costs specifically inside SaaS product pricing, drawn from the same source document.
- [Georgiana Laudi Recommends "Loved"](georgiana_laudi_recommends_loved_product_marketing.md): connects SaaS pricing's recurring-revenue character to the broader SaaS growth and marketing practice Laudi advises on.
- [Ford Shuts Down VIIZR, Its Field Service SaaS](ford_viizr_field_service_saas_shutdown.md): a concrete example of a subscription SaaS product from the corpus, illustrating the business model that SaaS pricing monetizes.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [The Outlook For US-China VC Dealmaking](outlook_for_us_china_vc_dealmaking.md)
- [The Investor Thesis For Rainforest](rainforest_investor_thesis.md)

## Source

- doc_0160: TechCrunch, 2023-12-15 — generative AI features carry a higher cost within SaaS product pricing versus paying per call to an LLM API.
- doc_0161: TechCrunch, 2023-10-13 — VCs contrast usage-based/consumption pricing with "conventional periodic SaaS pricing" and describe a hybrid structure combining both.
- doc_0243: TechCrunch, 2023-12-01 — Georgiana Laudi's SaaS growth work centers on driving "predictable, recurring revenue," the business logic underlying SaaS pricing.
