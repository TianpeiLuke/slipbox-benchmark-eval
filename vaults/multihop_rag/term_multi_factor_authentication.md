---
tags:
  - resource
  - technology
  - concept
keywords:
  - multi factor authentication mfa
  - multi-factor
  - vpn
  - security
  - passwords
  - labs
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0229, doc_0230]
enriched: web
external_refs: [https://www.cisa.gov/MFA]
---

# Multi-Factor Authentication (MFA)

## Definition

In the corpus, multi-factor authentication (MFA) is never defined on its own — it appears only as one item in a longer list of security practices that a source recommends or claims to already follow, alongside things like passwords, encryption, and security audits.

## Context

Engadget's VPN guide tells readers that a VPN alone does not cover them: because VPNs do not protect against phishing, hacking, or other cyberthreats, users should also maintain complex passwords and multi-factor authentication as part of their broader security routine. Keep Labs, in a statement provided to TechCrunch, lists multi-factor authentication alongside encryption in transit and at rest, regular security audits, and penetration testing as part of the company's layered approach to protecting patient medication data under HIPAA and PIPEDA.

## Key Characteristics

- **One layer among several** — in both corpus mentions, MFA is named in the same breath as passwords, encryption, or audits, never presented as sufficient on its own.
- **Complements, not replaces, other tools** — Engadget frames it as something users need in addition to a VPN, since a VPN does not defend against phishing or credential theft.
- **Used as a compliance signal** — Keep Labs cites its use of MFA as evidence of adherence to data-protection regulations (HIPAA, PIPEDA) and "highest standards" of security, in a self-reported statement rather than an independent audit.

## Background (external)

CISA (Cybersecurity & Infrastructure Security Agency, part of the U.S. Department of Homeland Security) describes MFA as "a layered approach to securing your online accounts and the data they contain," requiring a user to present two or more authenticators — something they know (like a password), something they have (like a phone or authentication app), or something they are (like a fingerprint or face scan) — before access is granted.

Source: CISA, "More than a Password" (https://www.cisa.gov/MFA), publisher: Cybersecurity & Infrastructure Security Agency, accessed 2026-09-02.

## Related Notes

- [What A VPN Is, And What It Does Not Hide](what_a_vpn_is_and_what_it_does_not_hide.md): the Engadget piece that names MFA as one of the safeguards users still need because a VPN does not stop phishing or credential theft.
- [How Keep Labs Says It Safeguards Patient Data](keep_labs_security_posture.md): the TechCrunch piece where Keep Labs lists MFA as one layer of its self-described, unaudited security procedure for patient data.
- [Passkeys As The Default Google Sign-In Method](passkeys_default_signin.md): a related but distinct phishing-resistant sign-in mechanism, showing an alternative approach to the same authentication problem MFA addresses.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [The University Response Gap To Faculty Online Abuse](university_response_gap_to_faculty_online_abuse.md)

## Source

- doc_0229: Engadget, 2023-10-16 — recommends multi-factor authentication alongside strong passwords as a baseline security practice VPN users still need.
- doc_0230: TechCrunch, 2023-10-04 — Keep Labs' security statement lists multi-factor authentication as one layer of its patient-data protection procedure.
