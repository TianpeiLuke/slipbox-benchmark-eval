---
tags:
  - resource
  - technology
  - concept
keywords:
  - encryption at rest
  - in-transit
  - data
  - beeper
  - vpn
  - end-to-end
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0230, doc_0229, doc_0402, doc_0457, doc_0498]
enriched: web
external_refs: ["https://en.wikipedia.org/wiki/Data_at_rest"]
---

# Encryption at Rest

## Definition

In the corpus, encryption at rest names the protection Keep Labs applies to stored user data — "data at rest is secured with AES-256 encryption" — presented as the counterpart to its in-transit protection, TLS 1.3 (doc_0230).

The corpus does not otherwise define the term generically: every other encryption discussion it contains concerns data in motion rather than data sitting in storage (doc_0229, doc_0402, doc_0457, doc_0498).

## Context

The corpus's clearest definition-by-example comes from Keep Labs, a medication-storage startup: the company told TechCrunch that "data at rest is secured with AES-256 encryption" while "data is transmitted using TLS 1.3 encryption," explicitly naming encryption at rest as the counterpart to encryption in transit within its layered security stack (doc_0230). Elsewhere in the corpus, "encryption" more often refers to data in motion rather than data at rest: VPN services encrypt the network "tunnel" carrying a user's traffic to its next hop (doc_0229); Beeper Mini describes its iMessage relay as "local, end-to-end encryption" protecting messages as they are sent (doc_0402); and both the EU's CSAM-scanning proposal and the UK's Online Safety Act "accredited technology" provision are fought over precisely because they would require scanning — and by extension weakening — end-to-end encrypted messages in transit, not stored data (doc_0457, doc_0498). Encryption at rest is therefore the narrower, storage-specific slice of the broader "encryption" vocabulary that dominates the corpus's privacy and security coverage.

## Key Characteristics

- **Protects stored data, not data in motion** — Keep Labs frames it as one half of a pair with in-transit encryption, applied to data once it has landed in storage (doc_0230).
- **Concrete algorithm named in the corpus** — Keep Labs specifies AES-256 for data at rest, paired with TLS 1.3 for data in transit and PBKDF2/SHA256 for password hashing (doc_0230).
- **Depends on key management** — Keep Labs says its encryption keys are "generated on the fly within their production environment and securely stored," with "no individual" having direct access to them, which is what keeps the at-rest ciphertext meaningfully protected (doc_0230).
- **One layer among several** — the company presents encryption at rest as part of a multi-layered stack that also includes regulatory compliance (HIPAA, PIPEDA), multi-factor authentication, security audits, and penetration testing, rather than a standalone guarantee (doc_0230).
- **Contrasts with the corpus's other encryption debates** — the VPN, Beeper Mini, EU CSAM, and UK Online Safety Act discussions in the corpus all concern encrypting data while it moves between parties, a materially different threat model from protecting data already in storage (doc_0229, doc_0402, doc_0457, doc_0498).

## Background (external)

Outside this corpus, "data at rest" is generally defined as digital data stored physically on a device, explicitly excluding data "traversing a network or temporarily residing in computer memory," and encryption at rest is the practice of applying an algorithm (commonly AES) to that stored data to prevent its exposure if the storage is accessed or stolen without authorization (Wikipedia, "Data at rest," accessed 2026-09-02, https://en.wikipedia.org/wiki/Data_at_rest).

## Related Notes

- [How Keep Labs Says It Safeguards Patient Data](keep_labs_security_posture.md): the procedure note describing the layered security stack in which Keep Labs' encryption-at-rest claim (AES-256) sits alongside its in-transit (TLS 1.3) claim.
- [Beeper Mini's Encryption and Audit Status](beeper_mini_encryption_and_audit_status.md): describes Beeper Mini's end-to-end, in-transit encryption model, the corpus's clearest contrast case to encryption at rest.
- [The Online Safety Act's Accredited Technology And Encryption](online_safety_act_accredited_technology_and_encryption.md): covers the UK provision threatening end-to-end (in-transit) encrypted messaging, the regulatory counterpart debate to at-rest protections.
- [What A VPN Is And What It Does Not Hide](what_a_vpn_is_and_what_it_does_not_hide.md): explains VPN tunnel encryption, an in-transit mechanism that is often conflated with but distinct from encryption at rest.
- [CSAM Proposal Opposition](csam_proposal_opposition.md): covers the EU debate over scanning end-to-end encrypted communications, another in-transit encryption fight that helps delineate what encryption at rest is not.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [Apple Blocks Beeper Mini's iMessage Access](apple_blocks_beeper_mini_imessage_access.md)
- [Beeper Mini As An iMessage Client For Android](beeper_mini_imessage_client_for_android.md)
- [Beeper Mini's Service Restoration And Apple ID Workaround](beeper_mini_service_restoration_and_apple_id_workaround.md)
- [Engadget's VPN Testing Methodology](engadget_vpn_testing_methodology.md)
- [Inco, Encrypted Ethereum Virtual Machine](inco_encrypted_evm_fhe_network.md)
- [ProtonVPN, Best VPN Overall](protonvpn_best_overall_vpn.md)

## Source

- doc_0230: TechCrunch, 2023-10-04 — Keep Labs states data at rest is secured with AES-256 while data in transit uses TLS 1.3, with keys generated and stored securely.
- doc_0229: Engadget, 2023-10-16 — VPNs encrypt the network tunnel carrying traffic, an in-transit mechanism distinct from at-rest storage encryption.
- doc_0402: TechCrunch, 2023-12-11 — Beeper Mini describes local, end-to-end encryption protecting messages as they are sent, an in-transit contrast case.
- doc_0457: TechCrunch, 2023-10-25 — EU CSAM-scanning proposal debate centers on scanning end-to-end encrypted content in transit, not data at rest.
- doc_0498: The Verge, 2023-11-09 — UK Online Safety Act's accredited-technology provision is contested for its impact on end-to-end encrypted messaging in transit.
