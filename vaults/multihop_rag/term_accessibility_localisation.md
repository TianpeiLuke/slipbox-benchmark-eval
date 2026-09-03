---
building_block: concept
source_docs: [doc_0106, doc_0188, doc_0335]
---

# Accessibility Localisation

Accessibility localisation is the work of adapting a digital product or platform's language coverage — dialects, translation, and rollout scope — to serve users outside the default language, and the gap that opens when that work is incomplete. In the corpus it shows up in two forms: a company's own roadmap for extending a feature beyond one language, and the moderation failures that surface when a platform's language resources are thin relative to the languages and dialects it actually serves.

## Context

Amazon's "Explore with Alexa" generative-AI feature for kids launched on 25 October 2023 available in English only, with internationalization described as "further down the road" — an explicit statement that localisation is a staged rollout, not a launch-day requirement. On the other end of the spectrum, TechCrunch's 19 October 2023 reporting on Meta describes localisation as an unmet obligation rather than a future roadmap item: Meta "struggles to navigate the cultural and linguistic nuances of Arabic, a language with over 25 dialects, and has been criticized for neglecting to adequately diversify its language resources," and a third-party report commissioned by Meta after the May 2021 conflict found Arabic content flagged as violating at higher rates than Hebrew content, attributing the gap partly to Hebrew being a "more standardized language" and to reviewers lacking competence in less common Arabic dialects like Palestinian Arabic. Meta's response to the October 2023 Israel-Hamas war — a special operations center staffed with Hebrew and Arabic speakers that removed or flagged over 795,000 pieces of content in those two languages in three days — is itself evidence of how much moderation capacity a platform must mobilize once it takes multilingual coverage seriously.

## Key Characteristics

- **Staged rollout vs. structural gap** — a company can frame incomplete localisation as a temporary phase (Amazon's "English only… internationalization further down the road") or it can be a longstanding structural deficit that draws external criticism (Meta's under-resourced Arabic-language moderation).
- **Dialect granularity matters** — Arabic's 25+ dialects mean that broad-language coverage is not the same as coverage of a specific dialect (e.g., Palestinian Arabic), and a platform can claim "Arabic support" while still failing specific dialect communities.
- **Localisation gaps have asymmetric enforcement effects** — Meta's own commissioned report found Arabic content flagged as violating at higher rates than Hebrew content for the same underlying conduct, tying uneven language resourcing directly to uneven moderation outcomes.
- **Crisis response can expand localisation capacity rapidly** — Meta stood up a dedicated Hebrew/Arabic special operations center and processed hundreds of thousands of pieces of content in those languages within days once the Israel-Hamas war escalated, showing localisation investment is elastic to urgency, not fixed.

## Related Notes

- [Meta Bias Mechanisms](meta_bias_mechanisms.md): describes the thin-Arabic-language-resources layer as one of several interacting mechanisms behind Meta's disproportionate content suppression, from the same source document.
- [Meta Moderation Bias](meta_moderation_bias.md): the broader argument that Meta's language-resourcing gap is part of a pattern of bias rather than an isolated bug, from the same source document.
- [Meta Enforcement Volume](meta_enforcement_volume.md): the concrete Hebrew/Arabic enforcement figures produced once Meta mobilized dedicated language-capable moderation staff, from a different source document.
- [Alexa Kids Data Handling And The Echo Pop Kids Launch](alexa_kids_privacy_and_hardware.md): the English-only launch and internationalization roadmap for "Explore with Alexa," the product-side localisation example in this note, from a different source document.
- [Meta Arabic Mistranslation](meta_arabic_mistranslation.md): a specific incident where an automated Arabic translation feature itself produced an offensive mistranslation, illustrating how localisation tooling failures compound moderation-resourcing gaps, from the same source document as the Meta bias evidence.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [Eylon Levy's Aliyah And IDF Service](eylon_levy_aliyah_and_idf_service.md)
- [Gerudo Town's Gender Segregation in Breath of the Wild](gerudo_town_gender_segregation_in_breath_of_the_wild.md)
- [Instagram Palestine Suppression](instagram_palestine_suppression.md)
- [Meta's Moderation During An Earlier Hamas-Israel Conflict](meta_2021_conflict_moderation.md)
- [Meta Crisis Response Measures](meta_crisis_response_measures.md)
- [Meta Response To Suppression Claims](meta_response_to_suppression_claims.md)
- [Mohamed Al Fayed and the Dodi-Diana Kiss Photo](mohamed_al_fayed_and_the_dodi_diana_kiss_photo.md)
- [Travel And Language Learning Gift Cards](travel_and_language_learning_gift_cards.md)

## Source

- doc_0106: TechCrunch, 2023-10-19 — Meta's thin Arabic-language resources, dialect diversity gap, and the 2021 third-party report finding Arabic content flagged at higher rates than Hebrew.
- doc_0188: TechCrunch, 2023-10-25 — Amazon's "Explore with Alexa" launching English only, with internationalization "further down the road."
- doc_0335: TechCrunch, 2023-10-13 — Meta's special operations center staffed with Hebrew and Arabic speakers, and the resulting Hebrew/Arabic enforcement volume.
