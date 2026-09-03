---
building_block: concept
source_docs: [doc_0009, doc_0053, doc_0086, doc_0121, doc_0226, doc_0305]
enriched: web
external_refs:
  - https://en.wikipedia.org/wiki/Line_of_credit (Wikipedia, accessed 2026-09-02)
---

# Line Of Credit

## Definition

In the corpus, "line of credit" denotes the informal, undocumented facility FTX extended to its affiliated trading firm Alameda Research.

Caroline Ellison testified there was "no contract and no written terms," and that Alameda drew against it in increments of $100,000 to $10 million at a time to fund trading.

## Context

The corpus uses "line of credit" almost exclusively to describe the Alameda–FTX arrangement at the center of the SBF fraud trial. Gary Wang testified he set the facility up for Alameda and repeatedly raised its ceiling as the firm kept running against its limit — moving from "a few hundred million," to a billion, and eventually to an effectively unlimited figure that reached $65 billion. Caroline Ellison separately testified that Alameda used $14 billion drawn "as a line of credit" to repay debts to third-party lenders, on Bankman-Fried's instruction. Bankman-Fried, for his part, denied on the stand that he knew about the "effectively infinite" line of credit Alameda received from FTX, a denial The Verge's trial coverage called "peculiar," concluding that the CEO of a financial company simply didn't pay attention to finances.

## Key Characteristics

- **Draw-as-needed structure** — funds are accessed incrementally against a ceiling rather than disbursed as one loan, as when Ellison described draws of $100,000 to $10 million at a time.
- **No collateral, no contract** — Ellison testified the $65 billion facility "did not have to post collateral" and had "no contract and no written terms."
- **Escalating limit** — the ceiling was repeatedly raised over time as the borrower kept exceeding it, per Wang's account of the increases from a few hundred million to $65 billion.
- **Invisible to oversight** — the credit line "wasn't visible to FTX's auditors," per Ellison's testimony, despite its size.
- **Exclusivity** — Wang testified the facility was "unmatched by anyone else on FTX," making it a privilege specific to the affiliated firm rather than a standard customer product.

## Background (external)

The corpus illustrates the term through a single, irregular instance rather than defining it as a general banking product. Per Wikipedia, a line of credit is ordinarily a borrowing arrangement from a bank or financial institution that lets a customer access funds up to a set maximum whenever needed, is typically revolving so that repaid amounts can be redrawn without reapplying, and generally charges interest only on the amount actually withdrawn (Wikipedia, *Line of credit*, accessed 2026-09-02). The Alameda–FTX facility described in the corpus departs from that standard model in that it had no written agreement, no collateral requirement, and no independent oversight.

## Related Notes

- [Alameda's $65 Billion Line Of Credit At FTX](alameda_65_billion_line_of_credit_at_ftx.md): the specific instance of this facility, examined in full detail with its size, informality, and exclusivity.
- [Alameda's Special Privileges Written Into FTX's Code](alameda_special_privileges_in_ftx_code.md): the code-level mechanism (`allow_negative`) that let Alameda draw against the line without triggering liquidation.
- [The Escalation of Alameda's Negative Balance](alameda_negative_balance_escalation.md): the parallel, step-by-step growth of Alameda's negative balance that tracked the credit line's rising ceiling.
- [Alameda Research](alameda_research.md): the firm that held the credit line and whose trading activity it funded.
- [FTX Cooperating Witnesses](ftx_cooperating_witnesses.md): the insiders (Wang, Ellison, Singh) whose testimony is the corpus's primary source for how the credit line operated.




## Corpus References

Corpus notes whose source text references this term (evidence-backed, from `term_links.json`):

- [Allow_negative: Alameda's Exemption From FTX Liquidation](ftx_alameda_allow_negative_liquidation_exemption.md)
- [Testimony At The SBF Trial](sbf_trial_testimony.md)

## Source

- doc_0009: TechCrunch, 2023-10-06 — Ellison testified she took $14 billion from customers, using them as a line of credit on Bankman-Fried's instruction.
- doc_0053: The Verge, 2023-10-28 — Bankman-Fried denied knowing about the "effectively infinite" line of credit Alameda received from FTX.
- doc_0086: The Verge, 2023-10-10 — Ellison testified the $65 billion line of credit required no collateral, no contract, and was drawn in $100,000–$10 million increments for trading.
- doc_0121: The Verge, 2023-10-26 — Wang testified the line of credit started small and was repeatedly increased to $65 billion as Alameda hit its limits; it was not visible to auditors.
- doc_0226: CNBC, 2023-10-06 — Wang described the $65 billion line of credit as part of Alameda's special code-based privileges on FTX.
- doc_0305: The Verge, 2023-10-06 — Wang testified the "allow_negative" code enabled the enormous line of credit and let Alameda operate with a negative balance.
