---
tags:
  - resource
  - technology
  - concept
keywords:
  - csam scanning
  - proposal
  - safety
  - accredited
  - detection
  - encryption
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0026, doc_0457, doc_0498, doc_0505]
---

# CSAM Scanning

## Definition

CSAM scanning is the practice of using detection technology — hash matching, or broader content-scanning systems — to find child sexual abuse material (CSAM) on a platform so it can be removed and, where required, reported.
CSAM itself is treated across the corpus as a category of illegal content, alongside terrorism content and fraud, that platforms and regulators single out from ordinary "harmful" content because hosting or transmitting it is against the law.

## Context

The corpus shows CSAM scanning arising in three distinct regulatory and platform contexts.
In the EU, the European Commission's home affairs commissioner Ylva Johansson is spearheading a CSAM-scanning proposal that would require in-scope platforms to deploy prevention measures first and, only if those are insufficient, detection measures after a court decision; she notes that companies today already scan non-encrypted communications for CSAM under a temporary ePrivacy derogation, and that her proposal is meant to be "technology neutral" rather than naming a specific vendor's tool.
In the UK, Ofcom's first Online Safety Act guidelines recommend that platforms use "hash matching" to detect and remove CSAM, and reserve a separate "accredited technology" power that could require services — including encrypted messaging apps — to scan for CSAM, which critics say would require breaking end-to-end encryption.
At the platform level, Discord's scrutiny over CSAM followed an NBC News investigation that identified 35 cases over six years of adults allegedly using the platform to kidnap, groom, or sexually assault minors, plus 165 cases of prosecutions for sharing CSAM or using Discord to extort sexual images from young users; Discord responded by banning teen dating servers, banning sharing of AI-generated CSAM, and rolling out Teen Safety Assist content filters, rather than describing a scanning system of its own.
Mozilla's planned fediverse instance separately lists CSAM as illegal content its trust-and-safety policies will act against, alongside hate speech and harassment.

## Key Characteristics

- **Detection technique, not one product** — the corpus describes hash matching as the recommended baseline technique (per Ofcom), while the EU proposal is explicitly framed as "technology neutral," naming no specific vendor's scanning tool.
- **Ordered obligation, not a first resort** — in the EU proposal, platforms must attempt prevention before detection/scanning is permitted, and only after a court decision.
- **Encryption tension** — both the EU proposal and the UK's "accredited technology" power are described as potentially requiring scanning of end-to-end encrypted messages, which critics argue is incompatible with maintaining that encryption.
- **Legal basis already exists for some scanning** — Johansson notes companies currently scan non-encrypted content for CSAM under an ePrivacy derogation, which her proposal would replace.
- **Distinct from policy/moderation responses** — Discord's post-scrutiny response (bans, content filters, Teen Safety Assist) is a moderation and policy response to CSAM risk rather than a scanning system per se, illustrating that "addressing CSAM" and "CSAM scanning" are not synonymous.

## Related Notes

- [The EU CSAM Scanning Proposal](eu_csam_scanning_proposal.md): the specific EU legislative proposal that would mandate CSAM scanning/detection obligations on in-scope platforms.
- [Johansson's Rebuttals To The Case Against The CSAM Scanning Proposal](csam_proposal_opposition.md): the commissioner's defense of the proposal's scanning/detection design against mass-surveillance and vendor-capture criticisms.
- [Online Safety Act Accredited Technology And Encryption](online_safety_act_accredited_technology_and_encryption.md): the parallel UK power to require "accredited technology" for CSAM detection, and its tension with end-to-end encryption.
- [Discord's CSAM Scrutiny After NBC News Report](discord_csam_scrutiny_after_nbc_news_report.md): a platform-level case of CSAM exploitation risk that prompted policy and moderation changes rather than a described scanning system.
- [The UK's First Online Safety Act Guidelines From Ofcom](uk_online_safety_act_ofcom_first_guidelines.md): the broader Ofcom guidance package in which hash-matching-based CSAM detection is one recommended practice among several illegal-harms duties.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [The Commission's Defence Of Political Ad Targeting And The Channels MEPs Say It Bypassed](dsa_political_ad_restrictions.md)
- [Fotiadis Testimony And Johansson's Lobbying Contacts At The LIBE Hearing](johansson_parliament_hearing.md)
- [Mozilla.social's Trust And Safety Moderation Stance](mozilla_social_trust_and_safety_moderation_stance.md)
- [Ofcom's Recommended Practices And Enforcement For Illegal Harms](ofcom_illegal_harms_codes_of_practice.md)
- [Technology Neutrality: How The Online Safety Act Covers AI Content](online_safety_act_technology_neutral_treatment_of_ai.md)

## Source

- doc_0026: TechCrunch, 2023-11-03 — Mozilla's fediverse instance content policy names CSAM as illegal content it will act against.
- doc_0457: TechCrunch, 2023-10-25 — Details the EU's CSAM-scanning proposal, its prevention-before-detection ordering, and existing non-encrypted-content scanning under ePrivacy.
- doc_0498: The Verge, 2023-11-09 — Ofcom's Online Safety Act guidelines recommend hash matching to detect CSAM and describe the "accredited technology" power to detect CSAM in encrypted messaging.
- doc_0505: Engadget, 2023-10-19 — Discord's response to CSAM/exploitation scrutiny, including bans on sharing CSAM and AI-generated CSAM.
