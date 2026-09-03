---
tags:
  - resource
  - technology
  - concept
keywords:
  - hipaa
  - health
  - pipeda
  - keep
  - labs
  - data
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: concept
source_docs: [doc_0230]
enriched: web
external_refs:
  - https://en.wikipedia.org/wiki/Health_Insurance_Portability_and_Accountability_Act (Wikipedia, accessed 2026-09-02)
---

# HIPAA

## Definition

HIPAA is the U.S. data protection regulation that a company handling patient health information cites as one of the "stringent data protection regulations" it adheres to in order to safeguard customer information, alongside Canada's PIPEDA.

## Context

In the corpus, HIPAA appears in Keep Labs' public statement about how it safeguards the patient data behind its medication-adherence enterprise offering: "We adhere to stringent data protection regulations such as HIPAA in the U.S. and PIPEDA in Canada to safeguard customer information." That statement frames HIPAA as the first, foundational layer of a security stack described in the same quote — ahead of encryption in transit and at rest, multi-factor authentication, and security audits and penetration testing, before the statement closes on ongoing staff training and a strict privacy policy. A separate paragraph attributes further remarks to Wilkins naming an additional external-review layer (Coalition Cybersecurity and Stendard) on top of that stack, distinct from the quoted statement itself. The regulation is invoked specifically because Keep Labs provides real-time and de-identified aggregate patient-adherence data to enterprise healthcare partners such as the McKesson Digital Health Network in Canada, which is the kind of health data flow that data-protection regulation like HIPAA is meant to govern.

## Key Characteristics

- **Named as a compliance baseline, not explained** — the corpus cites HIPAA as a regulation a health-data company adheres to but does not state what obligations it imposes.
- **Paired with a Canadian counterpart** — Keep Labs names HIPAA (U.S.) and PIPEDA (Canada) together as the two jurisdictions' data-protection regimes it follows, reflecting its cross-border footprint (U.S. consumers, Canadian enterprise partnership).
- **Positioned as the entry point of a layered security posture** — in Keep Labs' own account, regulatory adherence is stated first, before the technical controls (encryption, MFA, audits) that operationalize it.

## Background (external)

The corpus names HIPAA without defining it, so this section fills the gap from the web, quarantined from the scored sections above. HIPAA (the Health Insurance Portability and Accountability Act) is a U.S. federal law enacted in 1996 to improve health insurance portability and protect health data from fraud and theft (Wikipedia, accessed 2026-09-02). Its Title II establishes the Administrative Simplification standards, including the Privacy Rule and Security Rule that govern health data handling (Wikipedia, accessed 2026-09-02). Under the Privacy Rule, Protected Health Information (PHI) is defined as "any information that is held by a covered entity regarding health status, provision of health care, or health care payment that can be linked to any individual" (Wikipedia, accessed 2026-09-02).

## Related Notes

- [How Keep Labs Says It Safeguards Patient Data](keep_labs_security_posture.md): the note built around the exact statement in which Keep Labs names HIPAA as a compliance baseline.
- [Keep Labs' Enterprise Turn And The Pharmacist Co-Lead](keep_labs_enterprise_partnerships.md): describes the patient-adherence data business — the health-data flow to enterprise partners — that Keep Labs' HIPAA/PIPEDA compliance statement is meant to cover.
- [DICOM Medical Imaging Server Exposure](dicom_medical_imaging_server_exposure.md): shows the real-world stakes HIPAA-style regulation addresses, reporting that exposed medical-imaging servers spilled patients' protected health information onto the open web.

## Source

- doc_0230: TechCrunch, 2023-10-04 — Keep Labs' security statement naming HIPAA and PIPEDA as the data-protection regulations it adheres to for patient data.
