---
tags:
  - resource
  - technology
  - empirical_observation
keywords:
  - ftx s fabricated backstop insurance fund
  - criminal trial
  - alameda
  - ftx's
  - privileges
  - alameda's
topics:
  - Technology
language: markdown
date of note: 2026-09-02
status: active
building_block: empirical_observation
source_docs: [doc_0305]
---

# FTX's Fabricated Backstop Insurance Fund

Gary Wang testified on October 6th, 2023 that FTX lied about how much money was in its backstop fund, and the court was shown the code that generated the fake number published on FTX's website: it took the daily trading volume on FTX, multiplied it by a random number, divided it by a billion, and added the result to the number already displayed on the site. That figure had nothing to do with the actual amount of money in the insurance fund.

The fund mattered because of what FTX advertised. In many crypto networks, if someone lost enough money the exchanges could stick other traders with the losses too; FTX touted its automated liquidation as the way to avoid this, so that one customer going bankrupt would not affect the others. In the process of liquidating, FTX would try to sell the collateral on the open market, and if it could not finish, backstop liquidity providers would step in — market makers, including Alameda, which could be compensated for the losses they took from the backstop fund. Wang also testified that when there was not enough money in the fund, money was moved there from Alameda's accounts in order to pay the insurance out.

The prosecution's framing was that this was not merely a matter of Alameda holding special, secret privileges: it claimed those privileges were used to obfuscate basic elements of FTX's operations, exposing the exchange's supposed selling points as a lie.

## Related Notes


- [Alameda Research](alameda_research.md): overlaps on Alameda, liquidity and collateral, from a different source document.
- [Alameda Research as Alleged Conduit for FTX Customer Funds](alameda_research_as_alleged_conduit_for_ftx_customer_funds.md): overlaps on the fund and what was lied about, from a different source document.
- [Alameda's Special Privileges in FTX's Code](alameda_special_privileges_in_ftx_code.md): overlaps on Wang and Alameda's privileges, from a different source document.
- [Gary Wang's Cross-Examination by Everdell](gary_wang_cross_examination_by_everdell.md): the defense's attempt to reframe the same liquidation testimony, from a different source document.
- [Alameda's $65 Billion Line of Credit at FTX](alameda_65_billion_line_of_credit_at_ftx.md): a companion privilege shown in the same database (doc_0305).
- [Alameda Absorbed FTX's Losses, Including MobileCoin](alameda_absorbed_ftx_losses_mobilecoin.md): the same pattern of Alameda picking up FTX's tab (doc_0305).
- [Alameda Research's Origins And Naming](alameda_research_origins_and_naming.md): same sub-plan (FTX and Alameda Research: Mechanics of the Entanglement), different source document
- [The Escalation Of Alameda's Negative Balance](alameda_negative_balance_escalation.md): same source document (doc_0305)
- [Code Evidence Outweighs Deleted Signal Messages](code_evidence_outweighs_deleted_signal_messages.md): same source document (doc_0305)
- [The FTT Token And The "Sam Coins"](ftt_token_and_sam_coins.md): same source document (doc_0305)
- [Criminal Trial](term_criminal_trial.md): uses the concept criminal trial

## Source

- doc_0305: The Verge, 2023-10-06
