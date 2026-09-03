---
tags:
  - resource
  - technology
  - procedure
keywords:
  - how keep labs says it safeguards patient data
  - encryption at rest
  - data privacy
  - hipaa
  - medication
  - enterprise
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: procedure
source_docs: [doc_0230]
---

# How Keep Labs Says It Safeguards Patient Data

Keep Labs describes a layered, end-to-end security procedure for the patient data behind its enterprise offering: regulatory compliance first, then encryption of data in transit and at rest, then access controls, then continuous testing and review — with an external layer at the end. The statement TechCrunch asked for and reprinted in full reads: "Protecting user privacy and ensuring data security are paramount for KEEP. We adhere to stringent data protection regulations such as HIPAA in the U.S. and PIPEDA in Canada to safeguard customer information. All data transmitted through KEEP is encrypted both in transit and at rest, utilizing robust encryption algorithms. Our platform employs multi-factor authentication, regular security audits, and penetration testing to protect against unauthorized access. Furthermore, we conduct ongoing staff training and adhere to a strict privacy policy to ensure that all members of our team are vigilant and adhere to the highest standards of data protection and software development including RBAC. This comprehensive, multi-layered approach to security ensures that patient information remains confidential and secure at all times."

The specific mechanisms Wilkins added fill in each layer. Encryption keys are generated on the fly within the company's production environment and securely stored, with no individual having direct access to the keys. Data is transmitted using TLS 1.3 encryption, while data at rest is secured with AES-256 encryption. User passwords undergo hashing with PBKDF2 utilizing SHA256. On the software side, the company uses automated tools such as Scan Hawk and Synk to test its security and provide code vulnerability assessments; code is subject to peer reviews; and the company uses the Coalition Cybersecurity and Stendard to provide a final layer of external review.

The precondition that makes this procedure necessary is the enterprise data business it supports. With Wandzura leading the company and with gobs of customer feedback, Keep Labs started exploring an enterprise offering focused on medication adherence along with harm reduction. It became part of the McKesson Digital Health Network in Canada to provide real-time data about whether patients are taking their medication, and it has a partnership with Savvy Cooperative to give away free Keep devices to patients who are living with chronic conditions — partnerships that provide a feedback loop of front-line patients interacting with their devices. What the enterprise partners receive is deliberately not individual-level: "Let's make it super easy to deploy to individuals who need support," Wilkins said. "And we provide de-identified aggregate data to understand how many patients in the population are adhering [to their medications] and how many need intervention so they can understand patient behaviors at home. We charge a nominal subscription fee for that."

The same customer-contact habit runs alongside the enterprise program: the company has an active beta program with 150 users, and Wilkins calls the top 10 users weekly to better understand their usage, which is how he discovered people are now using their Keep for other critical items like keys, passports and cash — additional use cases he believes show users trust the device. One scope condition should stay attached to all of the above: these are the company's own descriptions of its practices, given to TechCrunch on 4 October 2023, and the reporter's assessment is that it's worth applauding Keep Labs' security and privacy measures because the statement shows a company proud of its efforts and comfortable making them public — an endorsement of disclosure, not an independent audit.

## Related Notes


- [Apple Blocks Beeper Mini's iMessage Access](apple_blocks_beeper_mini_imessage_access.md): shares the data-privacy and encryption themes, from a different source document.
- [CSAM Proposal Opposition](csam_proposal_opposition.md): shares the data-privacy and encryption themes, from a different source document.
- [Engadget's VPN Testing Methodology](engadget_vpn_testing_methodology.md): shares the data-privacy and encryption themes, from a different source document.
- [The Online Safety Act's Accredited Technology And Encryption](online_safety_act_accredited_technology_and_encryption.md): shares the data-privacy and encryption themes, from a different source document.
- [What A VPN Is And What It Does Not Hide](what_a_vpn_is_and_what_it_does_not_hide.md): shares the data-privacy, encryption-at-rest and multi-factor-authentication themes, from a different source document.
- [Keep Labs' Repositioning From Cannabis To Medicine](keep_labs_cannabis_repositioning.md): same source document (doc_0230)
- [The Keep, A Lockable Smart Storage Container For Medicine](keep_labs_device.md): same source document (doc_0230)
- [Keep Labs' Enterprise Turn And The Pharmacist Co-Lead](keep_labs_enterprise_partnerships.md): same source document (doc_0230)
- [Keep Labs' Funding And Second-Gen Roadmap](keep_labs_funding_and_roadmap.md): same source document (doc_0230)
- [Keep Labs' COVID Pivot And Leadership Change](keep_labs_pivot_and_leadership.md): same source document (doc_0230)
- [Encryption at Rest](term_encryption_at_rest.md): uses the concept encryption at rest
- [Data Privacy](term_data_privacy.md): uses the concept data privacy
- [HIPAA](term_hipaa.md): uses the concept hipaa
- [Harm Reduction](term_harm_reduction.md): uses the concept harm reduction
- [Medication Adherence](term_medication_adherence.md): uses the concept medication adherence
- [Multi-Factor Authentication (MFA)](term_multi_factor_authentication.md): uses the concept multi factor authentication

## Source

- doc_0230: TechCrunch, 2023-10-04
