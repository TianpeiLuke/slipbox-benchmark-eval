# Our findings against the published literature

Six parallel literature surveys (110 papers) plus an adversarial synthesis.
Verdict counts across 66 mappings:

| relation | n |
|---|---|
| confirms published work | 22 |
| extends published work | 17 |
| **already known, we rediscovered it** | **10** |
| contradicts published work | 10 |
| novel / not in the literature | 7 |

**Read section 4 first.** Most of what we found is already known, two of our
claims were refuted before we made them, and one "finding" had been run on this
exact corpus two years earlier with an order of magnitude larger effect.

Citations are as reported by the surveys. Where a claim rested on a single
surveyor's citation of a preprint no other survey saw, the synthesis flags it
inline as uncorroborated; re-verify those before relying on them.

---

# The Definitive Comparison

*Verification note: where a claim rests on a single surveyor's citation of a 2026 preprint that no other survey saw, I flag it inline as uncorroborated. Two surveys disagree on whether the Stronger Baselines (arXiv:2506.03989) budget table belongs to GPT-4o or GPT-4o-mini; the budget surveyor explicitly corrected an earlier mis-attribution and I follow that, noting the numbers are identical either way and the argument does not turn on it.*

---

## 1. Where we confirm published work (and so add little)

**F6 (budget dominates strategy) is a replication, not a discovery.** The shape is established in at least three independent places. Stronger Baselines scales budget 1.5K→30K for +17.5pp on inf-Bench En.MC while the best-versus-worst pipeline gap at any fixed budget is 4.5–7.0pp. RAGChecker's sweep moves claim recall 61.5→77.6 going k=5→20. Databricks publishes the recall curve directly, and it is close to superimposable on ours: FinanceBench recall@k runs 0.097 (2k) → 0.493 (8k); our atomic-notes chain completeness runs 0.095 (2K) → 0.515 (8K). We diverge at 16K (0.890 vs their 0.603), which is what a 609-article haystack should do against a 53,399-document one. Our contribution is a new corpus and a new unit type on a known curve.

Our 25:1 budget-to-strategy ratio is not a finding, it is a metric choice. Chain completeness is recall-shaped and close to monotone in budget by construction; the published 2.5:1 is measured on answer accuracy, where saturation and distraction eat the headroom. We should stop quoting the ratio.

**F8's MMR null was established three times before us, once by MMR's own authors.** Carbonell and Goldstein report no significant difference between λ=1, λ=0.7 and λ=0.3 on sentence precision, and scope their method to corpora with "a vast sea of potentially relevant documents, highly redundant with each other" — explicitly excluding the case where "relevant documents are few, or... very-high recall is necessary," which describes 2–4 gold documents out of 609 exactly. Santos, Macdonald and Ounis then tested novelty directly on 98 TREC Web topics and found a maximum improvement of +3%, never significant, even with ground-truth aspects. ARAGOG and the biomedical controlled study both report the same null on modern RAG. We added nothing to the null itself.

**F1's pooled tie is the expected outcome.** Nowhere in this literature does a summarised layer beat verbatim text at matched budget. Stronger Baselines runs the exact ablation — Vanilla RAG is RAPTOR minus the generated summaries — and verbatim wins at every budget from 1.5K to 40K. A tie is the friendliest result a note layer has been given; it is not a surprise and should not be framed as one.

**F1's type split direction is predicted by the benchmark's own baselines.** Multi-Meta-RAG reports per-type GPT-4 accuracy on this exact corpus of Inference 0.951, Comparison 0.382, Temporal 0.256. Entity-identification questions were already near ceiling and comparison/temporal were floor-bound; a note layer that trades verbatim surface strings for cross-document consolidation is trading in the direction the headroom already lay. (That paper's prose and its own Table 3 disagree on one GPT-4 number, 0.63 vs 0.606 — flagged by one surveyor, worth not leaning on.)

**F2's general phenomenon is the settled premise of the evaluation literature, not a result.** eRAG states it in the abstract and quantifies it: on HotpotQA with BM25, human document-level provenance labels correlate with downstream EM at Kendall tau 0.007. LongRAG states flatly that "end performance does not increase monotonically with the recall score." Lost in the Middle says reader accuracy saturates long before retriever recall does. Medrano et al. report it from production, with Hit@10 falling 0.51→0.48 while raw recall rose.

**F4's direction replicates ARM almost exactly.** ARM's "Perfect Recall" is operationally identical to our chain completeness, and adding decomposition to dense retrieval cut it 78.4→56.5 on BIRD and 43.1→32.7 on OTT-QA, with downstream accuracy following (17.5→13.9; EM 34.2→27.2). Our 0.190→0.073 is the same phenomenon, larger.

**F3's structural claim has one direct external replication.** Do Rosario et al. find accuracy-when-answering clustered at 97.0–98.0% across three commercial RAG systems while abstention spans a fiftyfold range, and state outright that "the largest observed difference among the RAG systems was abstention behavior rather than accuracy conditional on answering." This is a single 2026 preprint seen by one surveyor, on a single-hop benchmark; treat it as corroboration of shape, not of magnitude. The methodological corollary — decompose conditional on retrieval outcome rather than reporting marginal accuracy — is already formalized by the RAT paper across 27 configurations. We should cite that rather than present the decomposition as ours.

**F7's mechanism is named and solved in print.** Bennani and Moslonka adopt fill-to-budget specifically so there is "no fixed-K bias"; the Vectara paper observes the symptom without diagnosing it. (Both are single-survey citations; the Bennani paper in particular is an uncorroborated 2026 preprint, and our novelty claim on F7 is sensitive to whether it is real.)

---

## 2. Where we contradict published work

**F7's sign versus Dense X.** Dense X finds fine-grained propositions win *most* when starved (largest gain at 100–200 retrieved words); we find them lose most when starved. Three differences make this a regime split rather than a real disagreement, and all three favour our result *for our setting*: their entire budget range (100–500 words) sits below our 2,048-token floor; their questions are single-hop, so one proposition is a complete answer, while ours need 2–4 documents simultaneously, so an atom is a fragment of a chain and packing more atoms multiplies partial chains rather than completing them; and their propositions are decontextualised self-contained rewrites, which ours may not be. That third point is the one that could flip the verdict against us and it is *untested*, so we cannot yet claim to contradict Dense X. Until we run a decontextualisation control, the honest statement is that we measured a different regime.

Separately, our implied convergence claim is weaker than we thought. The granularity surveyor's own extracted numbers undercut Dense X's convergence: the downstream EM delta does *not* shrink monotonically with budget (SimCSE +2.4 at 100 tokens rising to +4.1 at 500). Convergence is a property of Dense X's Figure 4 recall curve, not of its QA results. And Stronger Baselines is a hard counterexample — the summary-unit penalty *grows* roughly fourfold from 1.5K to 30K. "Granularity differences converge with budget" should not be stated as a law anywhere in our write-up.

**F2's grain claim versus Samuel et al.** This is the sharpest cross-survey conflict and four of six surveys were on the wrong side of it. Three surveys treated our result — coarse document recall predicts the answer-level sign, fine sentence-similarity fact recall predicts it backwards — as confirming the literature. The evaluation survey found the closest published head-to-head, and it reports the *reverse* ordering on the same runs: nugget-grounded fact labels are the good predictors (topic-level Pearson 0.16–0.56) while document-relevance nDCG@20 is near zero and sometimes negative (0.1407, −0.0131, 0.0458, −0.0239 on NeuCLIR24).

**Samuel et al. are more likely right about grain; we are more likely right about our matcher.** Their nugget judge is validated at 69% precision / 90% recall; our fact-level recall is unvalidated sentence-embedding similarity. eRAG independently shows that the spread across *label definitions* (0.007 → 0.359 → 0.610 on one dataset) dwarfs the spread across metric formulas within a definition. Our fine/coarse contrast is a label-definition contrast, and one of the two labels has an unmeasured error rate. F2 must be restated as "an unvalidated similarity-based fact matcher inverted the sign," which is still worth reporting and is far more defensible.

**F3's calibration versus Sufficient Context.** Joren et al.'s central negative finding is that models hallucinate rather than abstain on insufficient context (abstention 50.0–73.1%, hallucination 15.4–40.4%); our answerer refuses 71–92%. This is not a contradiction of our measurement, it is a model-family difference sitting at the conservative extreme of their range — and in their own table Claude 3.5 Sonnet is the outlier that abstains most (11.1% with sufficient context) and hallucinates least (3.2%). Our answerer is claude-haiku-4-5. Every effect in F1–F8 flows through refusal, so every effect size is conditioned on the reader. **This is the largest external-validity exposure in the set.**

Worse, we cannot currently call our behaviour calibration at all. The AAAI paper measures *over-refusal* — with all-irrelevant retrieved documents, RALMs refuse questions they could have answered closed-book (over-refusal 0.355 at 0p10n, collapsing to 0.000 once one positive document appears). Without a closed-book arm we cannot distinguish "correctly declines without evidence" from "retrieval noise suppressed an answer it already knew."

And our ~99% conditional accuracy is out of line with this benchmark's own ceiling: MultiHop-RAG reports GPT-4 at 0.89 *with ground-truth evidence*. The two numbers are not strictly like-for-like (theirs may be unconditional), but a 10-point gap against a stronger model given perfect context is a grader-permissiveness signal, and F3 rests entirely on that number.

**F4 versus Ammann et al., on our own benchmark.** They get +4.4pp Hits@4 from decomposition alone on MultiHop-RAG and 0.464→0.635 MRR@10 with reranking. This is not a contradiction: they decompose into predicate-preserving sub-questions and rerank the merged pool against the *original* query, and their Hits@k counts a query as hit if at-least-one gold unit appears, where chain completeness requires all of it. A decomposition that scatters retrieval across entities can raise their metric while halving ours. Our claim must narrow to *predicate-stripped, union-merged decomposition without original-query reranking*.

But F4's stated mechanism is genuinely wrong. "The whole-query embedding already encodes the conjunction" is refuted by Weller et al.: the number of top-k document subsets a d-dimensional single-vector embedding can express is bounded by d, and on LIMIT — 50k documents, two relevant per query, trivially simple queries — state-of-the-art embedders fail to reach 20% recall@100 while BM25 comes close to perfect. **They are right and we are wrong.** The defensible restatement, fully consistent with our data: whole-query retrieval preserves the relation as a *scoring constraint* (a unit must match jointly); per-anchor retrieval removes the constraint. That survives Weller; our phrasing does not.

**F6's "strategy is near-irrelevant" versus IRCoT and HippoRAG.** Both move retrieval substantially at *fixed* budget — IRCoT by +3.5 to +22.6 points of fixed-budget optimal recall under a 15-paragraph cap, HippoRAG by AR@5 37.4→52.0 average at fixed k. Both are sequential or graph-joint. Our sweep covered only single-shot dense variants. **The literature is right and we over-claimed.** F6 must be narrowed to "within single-shot dense retrieval strategies, budget dominates," and that narrowing is a correction we should make ourselves rather than have made for us.

**F8's exact-zero versus two opposite published predictions.** Levy et al. show that at fixed token budget with gold always retained, *more* distinct documents costs 5–10% on MuSiQue and 10–20% on 2WikiMultiHopQA — so the predicted sign for "MMR raises distinct-document count" is negative, not zero. GeoRAG measures MMR at +2.4 average EM over truncation, so the predicted sign is positive. Our null is most likely a cancellation of a coverage gain against a fragmentation cost, not an absence of effect.

Here I also correct the diversity survey, which assumed our corpus sits at the low-redundancy end where MMR has no headroom. **News is the one genre where that assumption is least safe.** Wire copy, syndication and multi-outlet coverage of the same event make content-equivalence plausible, and 64.8% of our questions being cross-publisher means the gold evidence itself spans outlets covering overlapping ground. We never measured our corpus's redundancy rate, so the "no precondition" explanation for F8 is currently an assumption, not a finding.

**F1's temporal direction versus BEAR.** BEAR puts temporal questions on the *fine*-grained side ("localized or order-sensitive evidence"); we put them on the coarse side, pooled with yes/no comparison at +0.059. We cannot adjudicate: we pooled two types, BEAR splits them, and MultiHop-RAG defines them differently from BEAR's taxonomy. BEAR is also an uncorroborated single-survey 2026 preprint. Unpooling costs nothing and should be done before either claim is made.

---

## 3. What is genuinely novel or under-reported

**1. The corroboration gradient in F3 (refusal 0.65 → 0.25 → 0.08 with the fraction of the evidence chain present).** This is the strongest candidate in the set and the abstention survey returned an explicit negative search result for it. The nearest work builds exactly these levels and then does not report the curve: ESBT constructs C0 (unsupported) / C1 (partial, missing the bridge fact) / C2 (minimal sufficient) / C3 (sufficient plus redundancy) on 2,400 question families, but reports abstention *pooled* over C0+C1 and trains the transition rather than measuring it. The AAAI paper measures, but single-hop and binary — it finds a step function (0.000 → 0.355 → 0.000), because in single-hop one document saturates the requirement and there is no gradient to observe. Multi-hop is where the gradient can exist.

For this to be a contribution rather than an artifact, all of the following must hold: (a) the grader survives an audit against MultiHop-RAG's own gold-evidence ceiling — if 99% conditional accuracy is grader permissiveness, the whole finding dissolves; (b) the "no evidence" bin is stratified against the benchmark's 301 null queries (11.78%), which by construction have no gold evidence and therefore land in that bin necessarily — if nulls dominate it, the left endpoint is measuring the benchmark's designed unanswerables, not corroboration, and no surveyor raised this; (c) evidence presence is scored by exact gold-document membership, not by the similarity matcher that F2 shows can invert; (d) the gradient survives a non-Claude reader, or is reported as a policy curve for one model family; (e) it is reported per-level with bootstrap CIs and not confounded with budget or arm.

**2. F4 as the isolation of a fourth decomposition operation.** The decomposition survey's taxonomy is the most useful analytic contribution any surveyor made: every method that reports decomposition gains does at least one of predicate preservation (DecompRC's span-predicted sub-questions, Self-Ask's follow-ups, DecomP), sequential dependency (Least-to-Most's defining property, the ANS placeholder, IRCoT's CoT-sentence queries, MDR and Beam Retrieval's concatenated conditioning), or joint recombination (HippoRAG's single PPR run over a distribution where all anchors carry mass simultaneously, ARM's structure alignment). Naive entity-anchor splitting has none of the three, and no paper isolates and measures it. That gap is real.

The bar: **we have no control arm.** With only whole-query and entity-anchors measured, "predicate loss causes the collapse" is unsupported — splitting alone, or union-merging alone, could be the cause. HippoRAG already prices the union-merge half (their "Rq Nodes & Neighbors" arm is *worse* than nodes-only, 42.2 vs 50.7 R@2), which is evidence the merge matters. Until the predicate-preserving arm exists, this is a named hypothesis, not a result.

**3. F7's fixed-k bias magnitude and the conclusion flip.** The mechanism is known; what is not published is a measurement of how large the bias is and a demonstration that removing it *reverses a granularity verdict* on the same data. That matters because the two most systematic granularity evaluations available score at fixed rank cutoffs, and LongRAG's headline "+20 points answer recall" is a top-1 comparison in which the long unit carries roughly 46× more text. The bar: show the sign flip under both protocols on identical runs, and rule out that our atoms simply lack self-containment (the Dense X confound). Novelty shrinks to a magnitude measurement if the fill-to-budget preprint is real.

**4. F1's pooled null decomposing into two significant opposite subgroup effects at matched budget on a matched haystack.** Under-reported rather than novel — the direction is predictable from Multi-Meta-RAG's per-type table. The bar is statistical and it is not currently met: per-type CIs with a multiple-comparison correction over question types; base-rate correction for the yes/no slice, since Joren et al. show models answer 35–62% of insufficient-context instances correctly and name yes/no's 50% base rate as the main cause; and given F3, a demonstration that the +0.059 is not simply a lower abstention rate multiplied by a coin flip.

**5. Under-reported and nobody flagged it: the note layer has a lower recall ceiling than the chunk layer.** 5,093 notes against 14,589 chunks over the same documents is not only a granularity change, it is a lossy compression. A gold evidence span dropped during summarisation can never be retrieved at any budget. We have never measured what fraction of gold spans survive into the note layer, which means F1's tie and F6's coarse-note curve are both measured against an unknown ceiling. This is cheap and it bounds two findings.

**6. F8's corpus-size-conditional effect size is the weakest claim we have.** The diversity survey calls it novel; the evaluation survey calls it underpowered and points to Gabín et al.'s repeated-subset-sampling calibration. **The evaluation survey is right.** The parsimonious explanation for "significant on 37 documents, null on 609" is power, and the 37-document slice also confounds fewer questions with higher gold density. Both must be separated before this is stated as anything.

---

## 4. What we got wrong that the literature would have told us

**F5 is not a finding, and one paragraph of our own benchmark's paper would have said so.** MultiHop-RAG states: "In the construction of each query, we also include the source of the news article where the supporting evidence is associated with." Our 98.9% source-naming rate is a documented generation artifact. Worse, Multi-Meta-RAG (June 2024, ICTERI) ran exactly this intervention on exactly this corpus two years ago — metadata filter by the extracted publisher — and got Hits@4 0.6630→0.792 and GPT-4 accuracy 0.56→0.606, an order of magnitude more than our +0.03. And null queries carry *fictional* source metadata, so on the 301 nulls a source quota is a near-oracle refusal signal. F5 should be reported as a benchmark-construction result or dropped. Its collapse also widens the F6 gap: the 0.03 that budget beat by 25× was itself bought from an artifact.

**The F7 pool cap cost us a wrong conclusion, and fill-to-budget is standard advice in print.** Stronger Baselines explicitly recommends benchmarking "under matched token budgets"; Bennani and Moslonka name the bias. Granularity comparisons must equalise tokens, not units — that is not a subtle point and we shipped a conclusion without it.

**We designed the F4 arm without reading what "decomposition" means in this literature.** Had we read DecompRC, Self-Ask or DecomP first, the predicate-preserving control would have been in the design from day one, and F4 would today be a three-way result instead of a claim missing its control.

**We asserted a mechanism for F4 that was refuted at ICLR 2026.** Weller et al. is directly on point and would have stopped us writing "the whole-query embedding already encodes the conjunction."

**We ran MMR on a corpus its own authors scoped themselves out of.** Carbonell and Goldstein's sentence about "cases where relevant documents are few, or... very-high recall is necessary" describes 2–4 gold documents out of 609. The null was predictable from the 1998 paper.

**We claimed "strategy doesn't matter" having tested only one family of strategies.** IRCoT and HippoRAG both report large fixed-budget strategy gains; not including a sequential or graph-joint arm made F6 an overreach.

**We built an unvalidated fact matcher and treated its verdict as evidence about granularity.** eRAG's central result is that label definition dominates metric formula. Sentence-embedding similarity as a stand-in for "did we retrieve the fact" has an unmeasured error rate, and F2's most interesting claim is currently indistinguishable from that error.

**We piloted on a 37-document slice and generalised.** Hawking and Robertson establish that measurements do not transfer between a sample and its full collection; Gabín et al. supply the calibration procedure. This was foreseeable.

**We reported pooled accuracy in a system where abstention is the channel.** The RAT paper formalises the conditional decomposition, and Kalai et al. give the reason pooled grading structurally hides it. F1's "+0.005 ns" is exactly the blindness they describe.

---

## 5. Next experiments, ranked

**1. Grader audit plus penalty-aware rescoring of existing logs.** *Question:* is the ~99% accuracy-when-answering real, and does arm ordering survive a scoring rule that penalises guessing? *Design:* hand-audit ~150 answers graded correct against gold, stratified by question type and by whether the gold answer was in context; then rescore every arm as Q = P(correct) − k·P(wrong) with k=1..9 and report coverage-risk curves instead of pooled accuracy. *Changes belief:* if audited conditional accuracy lands near MultiHop-RAG's 0.89-with-gold ceiling, F3's headline is a grader artifact and everything downstream of it is rewritten. If arm ordering reorders under k=4, F1's tie and F2's answer-level verdicts are not the numbers we thought they were.

**2. Re-measure F2's fact-level recall with a validated matcher.** *Question:* is F2 about grain or about our matcher? *Design:* identical arms, identical budget; replace sentence similarity with (a) normalised gold-evidence-span membership and (b) an LLM nugget judge whose precision/recall you measure against ~100 human labels. Re-report the three verdicts. *Changes belief:* if the inversion disappears, F2 becomes "unvalidated similarity proxies invert signs" — cleaner and defensible. If it survives an exact matcher, we have a genuine contradiction with Samuel et al. worth writing up as such.

**3. Strip publisher names and re-run F5.** *Question:* is the source-quota gain retrieval or label-reading? *Design:* remove source names from the questions, re-run the quota arm, report chain completeness with and without, split by null and non-null. *Changes belief:* if the gain collapses, F5 is reported as a benchmark artifact and F6's strategy term shrinks toward zero.

**4. Re-cut the corroboration gradient properly.** *Question:* does the gradient survive a rigorous definition? *Design:* replace the three-bin summary with the ESBT levels (C0 / C1 missing-bridge / C2 minimal / C3 redundant), scored by gold-document membership; report refusal, unsupported-answer rate and conditional accuracy per level with bootstrap CIs; **stratify the C0 bin into benchmark nulls versus retrieval failures on answerable questions**; report per budget and per arm. *Changes belief:* if the left endpoint is carried by nulls, the gradient is measuring the benchmark's unanswerables and shrinks to a two-point result. If it holds on answerable questions alone, this is the paper.

**5. Add the predicate-preserving arm to F4.** *Question:* is the collapse caused by splitting or by predicate loss? *Design:* three-way at fixed budget and fixed metric — whole query / entity anchors (union-merged) / DecompRC-style sub-questions retaining the relation with an ANS placeholder. Optionally add a fourth arm changing only the merge (joint min/product scoring across anchors instead of union). *Changes belief:* if sub-questions recover most of the loss, F4 becomes "predicate-stripped decomposition hurts," which survives IRCoT and Self-Ask. If joint scoring alone recovers it, the mechanism is the merge, not the predicate, and HippoRAG already told us so.

**6. Score every granularity arm under both protocols.** *Question:* how large is the fixed-k bias and does it flip conclusions? *Design:* top-k at k ∈ {5,10,20,40} versus matched token budget, at 2K/8K/16K, all arms. Report bias magnitude and every sign flip. *Changes belief:* a measured flip on identical data turns an internal bug-fix into a methodological result about how granularity comparisons are run.

**7. Closed-book arm.** *Question:* is our absent-evidence refusal calibration or over-refusal? *Design:* same 2,556 questions, same model and prompt, no context; cross-tabulate refusals-under-absent-evidence against closed-book correctness. *Changes belief:* if the model answers a meaningful share correctly with no context at all, "refusal is calibrated to evidence" becomes "retrieval noise induces over-refusal," matching the AAAI result and inverting the story's polarity.

**8. Measure the note layer's recall ceiling, and add a decontextualisation control.** *Question:* how much gold can the note arms never retrieve, and are our atoms self-contained? *Design:* for every gold evidence span, check whether it survives into the coarse-note and atomic-note layers at all; separately, rewrite atomic notes to resolve pronouns and implicit referents (Dense X style) and re-run the 2K/8K/16K sweep. *Changes belief:* a low ceiling bounds F1 and F6 mechanically. If decontextualisation lifts the 2K point substantially, F7's starvation effect is a context-loss effect, fixable at index time, and our apparent contradiction with Dense X evaporates.

**9. Extend budget to 32K/64K and report answer accuracy and refusal alongside chain completeness.** *Question:* where is our inverted U, and does completeness convert into anything above 8K? *Design:* same arms, budgets 2K/8K/16K/32K/64K; report all three quantities per point. *Changes belief:* if refusal is at floor by 8K, the 0.835→0.970 completeness gain is worthless at the answer level and F6's practical claim collapses. If accuracy turns over near 32K as Databricks and OP-RAG predict, "budget dominates" is bounded by the reader's effective context, not general.

**10. Second answering model.** *Question:* is any of this a property of retrieval or of claude-haiku-4-5? *Design:* repeat F1/F2/F3 headline comparisons with a GPT-class model and one open-weights model at temperature 0, retrieval and contexts frozen; report conditional accuracy, refusal, and the corroboration gradient for each. *Changes belief:* Joren et al.'s table shows sufficient-context hallucination varying 3.2% to 14.3% across families. If the gradient does not survive, every finding is conditioned on the reader and must be labelled that way.

**11. Corpus redundancy plus a gold/non-gold split of MMR's extra documents.** *Question:* does MMR's precondition exist here, and were its extra documents gold? *Design:* shingling/fingerprint content-equivalence rate across the 609 articles, plus the fraction of gold evidence sentences with a near-duplicate elsewhere; then rescore existing MMR contexts on distinct documents, distinct *gold* documents, and answer-in-context. *Changes belief:* near-zero redundancy means F8 is "precondition absent," full stop. Non-trivial redundancy — plausible in news — means the null is a real puzzle and the cancellation hypothesis (Levy et al.) becomes the leading explanation.

**12. Power calibration before any haystack-size claim.** *Question:* is the 37-versus-609 flip power or density? *Design:* Gabín-style repeated subset sampling to find the smallest question count at which the sign is stable; only then run the haystack curve at 37/75/150/300/609 with gold held in every slice, plotting paired effect size against gold density with question count held fixed. *Changes belief:* if the sign is unstable below the full question set, the 37-document result is noise and the claim is withdrawn. If it is stable and effect size tracks 1/density, we have the one result in this set that nobody has published.
