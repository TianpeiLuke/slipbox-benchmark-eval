---
tags:
  - resource
  - technology
  - model
keywords:
  - beeper push notification service architecture
  - mini
  - apns
  - audit
  - imessage
  - android
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: model
source_docs: [doc_0540]
---

# Beeper Push Notification Service Architecture

Beeper Mini needs a persistent connection to Apple's push notification service (APNs) to be notified of new incoming messages in real time, and because Android cannot maintain that connection the way iOS does, Beeper built a new service — the Beeper Push Notification service, or BPNs — to hold it on the user's behalf.

The team explains the constraint: on an iPhone, an APNs connection is maintained by the operating system and connected at all times, whereas in Beeper Mini the connection can only be maintained when the app is running, since Android does not support APNs natively. BPNs works around that limitation by connecting to Apple's servers on the user's behalf when the app isn't running.

## Related Notes


- [Apple Blocks Beeper Mini iMessage Access](apple_blocks_beeper_mini_imessage_access.md): also covers Beeper Mini, from a different source document.
- [Beeper Mini Service Restoration and Apple ID Workaround](beeper_mini_service_restoration_and_apple_id_workaround.md): also covers Beeper Mini, from a different source document.
- [Beeper Security Audit Challenge to Apple](beeper_security_audit_challenge_to_apple.md): also covers Beeper Mini, from a different source document.
- [Elizabeth Warren Criticism of Apple Blocking Beeper](elizabeth_warren_criticism_of_apple_blocking_beeper.md): substantial content overlap on beeper, iphone, android, from a different source document.
- [Beeper Company Background and Founders](beeper_company_background_and_founders.md): drawn from the same source document, doc_0540.
- [Beeper Funding and Investors](beeper_funding_and_investors.md): drawn from the same source document, doc_0540.
- [Beeper Mini Encryption and Audit Status](beeper_mini_encryption_and_audit_status.md): drawn from the same source document, doc_0540.
- [Beeper Mini Hands on Test Results](beeper_mini_hands_on_test_results.md): drawn from the same source document, doc_0540.
- [Beeper Mini As An iMessage Client For Android](beeper_mini_imessage_client_for_android.md): same source document (doc_0540)
- [Beeper's Open Source Transparency Effort](beeper_open_source_transparency_effort.md): same source document (doc_0540)

## Source

- doc_0540: TechCrunch, 2023-12-05
