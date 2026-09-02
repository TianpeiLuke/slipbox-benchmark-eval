---
building_block: concept
source_docs: [doc_0540]
---

# Beeper Mini's Encryption And Audit Status

Beeper claims it does not have access to the contents of users' messages: a message sent from an Android phone using Beeper Mini is end-to-end encrypted to the recipient, encrypted on the device before it leaves the app.

Two features distinguish this from the alternative approach. Unlike the recently paused efforts by Sunbird, which had been trying to solve the same problem, messages are not sent in clear text. And encryption keys are stored exclusively on the user's phone within the Android filesystem, similar to other apps like Signal and WhatsApp; the app does not connect to any servers at Beeper itself, only to Apple servers, the way a "real" iMessage text would.

The boundary on those claims is verification. To be fully trusted, Beeper Mini will need to be audited by a third party — something it has not yet done. Beeper also uses certificate pinning, which makes network traffic analysis more difficult to perform in order to verify its claims. The company says its external audit is still "in progress" but that it has performed an internal audit, and it is publishing those results on its blog along with a detailed, more technical description of how Beeper Mini works.

## Related Notes

- [Apple Blocks Beeper Mini iMessage Access](apple_blocks_beeper_mini_imessage_access.md): also covers Beeper Mini, from a different source document.
- [Beeper Mini Service Restoration and Apple ID Workaround](beeper_mini_service_restoration_and_apple_id_workaround.md): also covers Beeper Mini, from a different source document.
- [Beeper Security Audit Challenge to Apple](beeper_security_audit_challenge_to_apple.md): also covers Beeper Mini, from a different source document.
- [Elizabeth Warren Criticism of Apple Blocking Beeper](elizabeth_warren_criticism_of_apple_blocking_beeper.md): substantial content overlap on beeper, android, imessage, from a different source document.
- [Inco Encrypted EVM FHE Network](inco_encrypted_evm_fhe_network.md): substantial content overlap on encrypted, encryption, performed, from a different source document.
- [Beeper Company Background and Founders](beeper_company_background_and_founders.md): drawn from the same source document, doc_0540.
- [Beeper Funding and Investors](beeper_funding_and_investors.md): drawn from the same source document, doc_0540.
- [Beeper Mini Hands on Test Results](beeper_mini_hands_on_test_results.md): drawn from the same source document, doc_0540.

## Source

- doc_0540: TechCrunch, 2023-12-05
