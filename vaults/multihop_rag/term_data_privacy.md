---
tags:
  - resource
  - technology
  - concept
keywords:
  - data privacy
  - meta
  - consent
  - gdpr
  - meta's
  - pixel
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0107, doc_0164, doc_0189, doc_0304]
enriched: web
external_refs: ["https://gdpr.eu/what-is-gdpr/"]
---

# Data Privacy

## Definition

Data privacy, across the corpus, is the recurring dispute over whether companies may collect, track, or profile people's personal information without their knowledge or consent.

That dispute plays out as regulatory enforcement against platforms: GDPR action against Meta's consentless ad tracking (doc_0107), COPPA litigation over Meta's collection of data from children under 13 (doc_0304), a "mass breach of privacy" allegation against TikTok's pre-consent tracking pixel (doc_0189), and California's CPPA extending opt-out and access rights to AI-based profiling (doc_0164).

## Context

In the corpus, data privacy surfaces as the recurring fault line between platforms that monetize personal data and the regulators pushing back on non-consensual collection. Norway's Datatilsynet issued an emergency GDPR ban on Meta running "personalized ads" without consent, then referred the case to the EU's Board to make the ban permanent across the single market, because Meta kept running tracking ads despite the order and a rejected court challenge (doc_0107). California's CPPA is drafting rules that would give residents opt-out and access rights over "automated decisionmaking technology," explicitly modeled on GDPR and expected to draw pushback from adtech and AI firms like Meta and OpenAI (doc_0164). The Age's investigation found TikTok's tracking pixel scraping site visitors' names, emails, and phone numbers before users clicked "I consent," prompting an Australian senator to call it a "mass breach of privacy" and demand a regulatory probe (doc_0189). Meta separately faces a 42-state lawsuit alleging it violated COPPA — the US law restricting data collection from children under 13 and requiring parental consent — by knowingly letting millions of underage users onto Instagram and Facebook while collecting their personal information (doc_0304).

## Key Characteristics

- **Consent is the legal hinge** — GDPR, as applied against Meta in Norway, turns on whether a company has a valid legal basis (consent, not "legitimate interest" or "contractual necessity") before tracking or profiling users for ads (doc_0107).
- **Pre-consent collection is the specific harm alleged against TikTok** — its pixel captured form-field data "often before clicking 'I consent'," unlike Google's and Meta's pixels, which the same test showed firing only after consent (doc_0189).
- **Children are a protected, heavily litigated category** — COPPA restricts data collection from users under 13 and requires verifiable parental consent, and Meta's alleged evasion of that requirement (ignoring reports, not disabling accounts, avoiding "actual knowledge") is the specific violation named in the unredacted lawsuit (doc_0304).
- **Regulators are extending consent/access rights into AI** — California's CPPA is drafting opt-out and access rights over automated decisionmaking technology and AI-based profiling, explicitly borrowing from GDPR's model (doc_0164).
- **Enforcement can escalate beyond a single national regulator** — Norway's local DPA used an emergency GDPR mechanism to bypass the "one-stop-shop" rule and force an EU-wide decision on Meta, showing that a single country's action can become bloc-wide policy (doc_0107).

## Background (external)

Outside the corpus, the general legal concept the enforcement actions above are built on is the definition of "personal data" under GDPR.

GDPR.eu describes personal data as "any information that relates to an individual who can be directly or indirectly identified," a category spanning obvious identifiers like names and emails as well as location data and other online identifiers (GDPR.eu, "What Is GDPR, the EU's New Data Protection Law?", published by Proton AG with EU Horizon 2020 co-funding, accessed 2026-09-02: https://gdpr.eu/what-is-gdpr/).

## Related Notes

- [CCPA/CPPA Regulatory Lineage](ccpa_cppa_regulatory_lineage.md): traces the California law that the CPPA's opt-out and access rights build on.
- [Alexa Kids Privacy and Hardware](alexa_kids_privacy_and_hardware.md): a sibling case of children's data handling under scrutiny, parallel to the COPPA allegations against Meta.
- [23andMe Data Breach Scope](23andme_data_breach_scope.md): a different failure mode for the same concept — personal data exposed through a breach rather than through non-consensual tracking.
- [ASPI Analysis of TikTok Pixel Data Aggregation Risk](aspi_analysis_of_tiktok_pixel_data_aggregation_risk.md): expands on how the TikTok pixel's collected data can be aggregated and linked across sites, from the same investigation.
- [James Paterson Call for TikTok Privacy Investigation](james_paterson_call_for_tiktok_privacy_investigation.md): the regulatory response triggered directly by the TikTok pixel findings cited above.
- [Apple Privacy Stance versus Google Default Payments](apple_privacy_stance_versus_google_default_payments.md): a contrasting case where a platform invokes privacy as a defense rather than being accused of violating it.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [Civil Rights, Privacy And Consumer Protections In The AI Executive Order](ai_civil_rights_and_consumer_protections_in_the_eo.md)
- [Analysis Of Meta's Delay Tactics On The Consent Switch](analysis_of_meta_delay_tactics_on_consent_switch.md)
- [Apple Blocks Beeper Mini's iMessage Access](apple_blocks_beeper_mini_imessage_access.md)
- [Apple's iOS Security Fixes And Spyware Notifications](apple_ios_security_fixes_and_spyware_notifications.md)
- [Australian Advertiser Responses To The TikTok Pixel Findings](australian_advertiser_responses_to_tiktok_pixel_findings.md)
- [Beeper's Security Audit Challenge To Apple](beeper_security_audit_challenge_to_apple.md)
- [BEUC And 18 Member Groups File A CPC Complaint Against Meta](beuc_consumer_complaint_meta_pay_or_consent.md)
- [BEUC's Consumer-Law Case Against Meta's Pay-Or-Consent Model](beuc_consumer_law_objections_to_meta_model.md)
- [BEUC: The Choice And Its Implementation Cannot Be Separated](beuc_position_choice_versus_implementation.md)
- [Britney Spears And Sam Asghari: Marriage And Divorce](britney_spears_sam_asghari_marriage_and_divorce.md)
- [ChatGPT Legal And Privacy Controversies](chatgpt_legal_and_privacy_controversies.md)
- [ChatGPT's Mid-2023 Usage Decline](chatgpt_mid_2023_usage_decline.md)
- [ChatGPT Subscription Tiers And Pricing](chatgpt_subscription_tiers_and_pricing.md)
- [ChatGPT Use In Government And Courts](chatgpt_use_in_government_and_courts.md)
- [China's Data Laws And Government TikTok Device Bans](china_data_laws_and_government_tiktok_device_bans.md)
- [Chris Partridge's Firing And The Evidence-Destruction Allegation](chris_partridge_firing_and_evidence_destruction.md)
- [Civic Data's Warning To Remove The TikTok Pixel](civic_data_warning_to_remove_tiktok_pixel.md)
- [Collingwood Players Who Missed Out On The 2023 Premiership](collingwood_2023_premiership_players_who_missed_out.md)
- [The Commission's Microtargeted Ad Campaign For CSAM Scanning](commission_microtargeted_ad_campaign.md)
- [California's CPPA Publishes Draft ADMT Rules](cppa_draft_admt_regulations.md)
- [The CPPA Pre-Use Notice Requirement](cppa_pre_use_notice_requirement.md)
- [The CPPA's Risk-Based Approach Versus The EU AI Act](cppa_risk_based_approach_versus_eu_ai_act.md)
- [Critique Of Meta's App Store Parental Approval Proposal](critique_of_meta_app_store_parental_approval_proposal.md)
- [Johansson's Rebuttals To The Case Against The CSAM Scanning Proposal](csam_proposal_opposition.md)
- [Discogs' Stated Justification For The Fee Increase](discogs_stated_justification_for_fee_increase.md)
- [DMA And DSA Oversight Of Meta's Advertising Consent](dma_dsa_oversight_of_meta_advertising_consent.md)
- [DSA And DMA Oversight Of Meta's Ad Tracking](dsa_dma_oversight_of_meta_ad_tracking.md)
- [Eddy Cue's Testimony In US V. Google](eddy_cue_testimony_in_us_v_google.md)
- [Engadget's VPN Testing Methodology](engadget_vpn_testing_methodology.md)
- [The Commission's Earlier Requests For Information To X](eu_commission_prior_requests_for_information_to_x.md)
- [The EU CSAM Scanning Proposal](eu_csam_scanning_proposal.md)
- [Federation Alone Is Not A Product Advantage](federation_alone_is_not_a_product_advantage.md)
- [The Fediverse Definition And The Email Analogy](fediverse_definition_and_the_email_analogy.md)
- [Google's Denial That Ad Keyword Matching Affects Organic Results](google_denial_that_ad_keyword_matching_affects_organic_results.md)
- [Google's Generative AI Disinformation Measures](google_generative_ai_disinformation_measures.md)
- [Google Nest Hub Smart Display Deal](google_nest_hub_smart_display_deal.md)
- [Independent Research And Reviews Of ChatGPT's Flaws](independent_research_and_reviews_of_chatgpt_flaws.md)
- [Irish DPC's Assessment Of Meta's Consent Model](irish_dpc_assessment_of_meta_consent_model.md)
- [Italy's ChatGPT Ban Over GDPR](italy_chatgpt_ban_over_gdpr.md)
- [Kashmir Hill Recommends "The Listeners"](kashmir_hill_recommends_the_listeners_wiretapping_history.md)
- [How Keep Labs Says It Safeguards Patient Data](keep_labs_security_posture.md)
- [Kelley Coleman on Child-Centred Disability Disclosure](kelley_coleman_on_child_centred_disability_disclosure.md)
- [Kevin Federline's 2022 Comments And The Spears Camp's Rebuttal](kevin_federline_2022_comments_and_the_spears_camp_rebuttal.md)
- [Kick's Corporate Response To The Incident](kick_corporate_response_to_the_incident.md)
- [Meta's Ad-Free Subscription Pricing In The EU](meta_ad_free_subscription_eu_pricing.md)
- [Meta Crisis Response Measures](meta_crisis_response_measures.md)
- [Meta's Justification For The Subscription Choice](meta_justification_for_subscription_choice.md)
- [Meta's Legal Basis For Ad Tracking In The EU](meta_legal_basis_for_ad_tracking_in_eu.md)
- [The GDPR Track Running Alongside The Consumer Complaint](meta_pay_or_consent_gdpr_dimension.md)
- [Meta's EU Pay-Or-Consent Ad-Free Subscription](meta_pay_or_consent_subscription_model_eu.md)
- [Meta's Response To The Norwegian DPA Referral](meta_response_to_norwegian_dpa_referral.md)
- [Arturo Bejar's Critique Of Meta's Teen Safety Self-Regulation](meta_teen_safety_self_regulation_and_bejar_critique.md)
- [The 42-State Lawsuit Against Meta Over Harms To Young Users](multistate_lawsuit_against_meta_teen_harms.md)
- [NFL Figures React To The Swift-Kelce Romance](nfl_figures_react_to_the_swift_kelce_romance.md)
- [Norway's Ban On Meta's Consentless Tracking Ads](norway_ban_on_meta_consentless_tracking_ads.md)
- [noyb's "Pay Or Okay" Challenge](noyb_pay_or_okay_challenge.md)
- [The Accredited Technology Clause And The Encryption Objection](online_safety_act_accredited_technology_and_encryption.md)
- [OpenAI Denial Of Malfeasance In Altman Ouster](openai_denial_of_malfeasance_in_altman_ouster.md)
- ["Pay Or Okay": The Cookie Paywall Model Meta Borrowed](pay_or_okay_cookie_paywall_origins.md)
- [Prime Day 2023 Baby And Pet Gear Deals](prime_day_2023_baby_and_pet_gear_deals.md)
- [Prime Day 2023 iPhone Case And Accessory Deals](prime_day_2023_iphone_case_and_accessory_deals.md)
- [Prime Day Security Camera And Doorbell Deals, October 2023](prime_day_security_camera_and_doorbell_deals_october_2023.md)
- [Ray-Ban Meta: Design And Discreetness](ray_ban_meta_design_and_discreetness.md)
- [Ray-Ban Meta Smart Glasses: Verdict And Specs](ray_ban_meta_smart_glasses_verdict_and_specs.md)
- [Reaction To Biden's AI Order](reaction_to_biden_ai_order.md)
- [Regulatory Investigations Into OpenAI In 2023](regulatory_investigations_into_openai_2023.md)
- [Risks And Limitations Of Clinical AI](risks_and_limitations_of_clinical_ai.md)
- [Smart Glasses Privacy And Bystander Consent](smart_glasses_privacy_and_bystander_consent.md)
- [Theory: A Security Or Privacy Incident At OpenAI](theory_openai_security_or_privacy_incident.md)
- [TikTok's Denial And The OAIC's Monitoring Of The Pixel Claims](tiktok_denial_and_oaic_monitoring_of_pixel_claims.md)
- [TikTok Pixel Pre-Consent Data Collection Test](tiktok_pixel_pre_consent_data_collection_test.md)
- [Uber Assault Litigation](uber_assault_litigation.md)
- [Uber's Recording Features And Driver Screening](uber_safety_features.md)
- [What A VPN Is, And What It Does Not Hide](what_a_vpn_is_and_what_it_does_not_hide.md)
- [Whether A VPN Is Worth It](whether_a_vpn_is_worth_it.md)
- [WIRED Black Friday 2023 Screen Protector, Grip And Cable Deals](wired_black_friday_2023_screen_protector_grip_and_cable_deals.md)
- [Wired's Retracted Claim That Google Manipulates Search Queries](wired_retracted_claim_that_google_manipulates_search_queries.md)

## Source

- doc_0107: TechCrunch, 2023-09-28 — Norway's DPA emergency-banned Meta's consentless tracking ads under GDPR and referred the case to the EDPB for an EU-wide decision.
- doc_0164: TechCrunch, 2023-11-27 — California's CPPA drafts GDPR-inspired opt-out and access rights over AI-based automated decisionmaking and profiling.
- doc_0189: The Age, 2023-12-25 — TikTok's tracking pixel scraped site-visitor personal data before consent was given, prompting a "mass breach of privacy" allegation.
- doc_0304: TechCrunch, 2023-11-27 — Unredacted multi-state lawsuit alleges Meta knowingly collected personal data from millions of under-13 users in violation of COPPA.
