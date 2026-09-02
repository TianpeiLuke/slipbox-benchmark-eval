---
building_block: model
source_docs: [doc_0053, doc_0121, doc_0305]
---

# Allow_negative: Alameda's Exemption From FTX Liquidation

"Allow_negative" was a column in FTX's account database that exempted Alameda Research — and only Alameda — from the exchange's automated liquidation, letting Alameda hold a negative balance and withdraw money its accounts did not have. Gary Wang testified that it originated in a code commit dated July 31st, 2019 under Nishad Singh's username, titled "OTC trades and transfers to special accounts." Written in Python, it added two columns to the account database, the relevant one being "allow_negative," a toggle that when on let the account go negative; the feature was switched on the same day by a second set of code also carrying Singh's username, and Wang said he supervised.

The structure it modified was FTX's risk management. As Wang explained it, a futures exchange is the middleman that lets strangers bet with each other: it sits between the two ends of the bet, paying the winner and collecting from the loser, which is why it requires collateral, and under some circumstances it automatically sells that collateral to limit its losses. On FTX this liquidation process was automated and took about 30 seconds to find the accounts that needed to be liquidated to minimize FTX's losses. Normal customers — the defense objected to "normal" and was overruled — could be automatically liquidated, but not Alameda. Wang testified that Bankman-Fried "told me a few times to make sure that Alameda's account is never liquidated on FTX," and that "the code addition was the result of those conversations." Alongside the exemption, Alameda could place orders faster than other users and held an enormous line of credit, and the court saw evidence that users may have unwittingly deposited money into Alameda rather than FTX.

The relation holds only for Alameda: no other customer trading on FTX had allow_negative privileges, and the same day the toggle was switched on in July 2019, Bankman-Fried tweeted that Alameda "is a liquidity provider on FTX, but their account is just like everyone else's" — a tweet shown in court, and to The Verge's reporter evidence that the fraud at FTX started very early, just months after FTX was founded. Bankman-Fried offered a competing origin story from the stand: FTX's big selling point was its "risk engine," which in 2020 was "effectively sagging under the weight" of the exchange's rapid growth so that time to liquidation stretched to minutes, and at one point the engine got stuck in a catastrophic feedback loop that would have created losses in the "trillions of dollars," with Alameda teetering on the brink of a liquidation that "would have disastrous consequences" for FTX. "At the time, I wasn't entirely sure what was happening," he testified, saying that because of that experience he suggested an "alert" or "delay" to keep Alameda from being liquidated by a bug, that allow_negative was the eventual result of that conversation, and that he did not know about it until very recently. The dates do not fit: allow_negative was coded and switched on in 2019, and the code was displayed in court in front of Bankman-Fried and the jury.

## Related Notes

- [Adam Yedidia's Testimony and the $8 Billion Bug](adam_yedidia_testimony_and_the_eight_billion_bug.md): another criminal-trial account of the fraud, from a different source document.
- [Alameda Research](alameda_research.md): background on the trading firm the exemption was written for, from a different source document.
- [Alameda Research as Alleged Conduit for FTX Customer Funds](alameda_research_as_alleged_conduit_for_ftx_customer_funds.md): the same firm treated as the channel for customer money, from a different source document.
- [Alameda's Special Privileges in FTX's Code](alameda_special_privileges_in_ftx_code.md): the same code-level privileges attributed to Nishad Singh, from a different source document.
- [Caroline Ellison's Guilty Plea and First Day Testimony](caroline_ellison_guilty_plea_and_first_day_testimony.md): the Alameda CEO's account of the same arrangement, from a different source document.
- [Alameda's $65 Billion Line of Credit at FTX](alameda_65_billion_line_of_credit_at_ftx.md): the companion privilege granted in the same database (doc_0121).
- [Alameda Absorbed FTX's Losses, Including MobileCoin](alameda_absorbed_ftx_losses_mobilecoin.md): another way Alameda's books were used to shield FTX (doc_0121).

## Source

- doc_0053: The Verge, 2023-10-28
- doc_0121: The Verge, 2023-10-26
- doc_0305: The Verge, 2023-10-06
