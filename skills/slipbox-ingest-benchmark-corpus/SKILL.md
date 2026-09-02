---
tags:
  - resource
  - skill
  - procedure
  - capture
  - benchmark
  - evaluation
keywords:
  - ingest benchmark corpus
  - slipbox-ingest-benchmark-corpus
  - blind ingestion
  - circularity guard
  - isolated experiment vault
  - provenance map
  - source adapter
  - in-vault skill canonical
topics:
  - Skill Procedures
  - Vault Tools
  - Evaluation Infrastructure
language: markdown
date of note: 2026-09-01
status: active
building_block: procedure
pipeline_metadata: none
---

# Procedure: slipbox-ingest-benchmark-corpus (Canonical Body)

This is the **single canonical body** for the `slipbox-ingest-benchmark-corpus` skill. The thin headers under `.claude/skills/slipbox-ingest-benchmark-corpus/SKILL.md` and `.kiro/skills/slipbox-ingest-benchmark-corpus/SKILL.md` point an invoking agent here at runtime; the in-vault note is the only place to edit the procedure.

## Skill description <!-- :: section_id = skill_description :: -->

Convert a **public QA-benchmark document corpus** into the digestion-pipeline input contract, digest it into a typed-note knowledge graph inside an **isolated experiment vault**, and emit the provenance artifacts an unbiased retrieval evaluation requires. This is the source-adapter pre-stage (C.O.D.E. *Capture*) for benchmark corpora, and it is the sibling of `slipbox-ingest-book` — same handoff contract, different source genre and one additional, non-negotiable constraint.

**Why this skill exists.** A benchmark whose questions were generated FROM the notes under test is circular: any measurement of "typed notes versus raw documents" is then decided by construction. Ingesting a public benchmark whose questions were authored independently is the only way to test that claim honestly. See docs/BACKGROUND.md.

**The one rule that makes the result valid.** The ingesting agent must **never read the benchmark's questions, gold answers, or gold passage labels.** Ingestion sees the *document corpus only*. Any leakage of the question set into note-writing recreates the circularity this skill exists to remove and silently invalidates every number downstream. This rule is enforced procedurally in Step 0 and re-checked in Step 6.

## Setup <!-- :: section_id = setup :: -->

```bash
SCRIPTS_DIR="./scripts"
BENCH_ROOT="./experiments/benchmarks/<benchmark_slug>"     # corpus + questions, kept SEPARATE
EXP_VAULT="./experiments/vaults/<benchmark_slug>"           # isolated vault, NOT the production vault
```

**Never point this skill at the production vault.** The experiment vault is a fresh directory with its own database and its own index; the production vault is neither read from nor written to during ingestion.

## Resources <!-- :: section_id = resources :: -->

- **Downstream pipeline**: `/slipbox-plan-digestion` then `/slipbox-augment-digestion-plan` then `/slipbox-review-digestion-plan` then `/slipbox-execute-digestion-plan` — used unchanged
- **Sibling adapter**: skill_slipbox_ingest_book — the same input contract, for PDFs
- **Validator**: `scripts/validate_notes.py` — frontmatter, structure, broken links, ghosts, and the vault-escape check (`--fix` repairs, `--gate` blocks a commit)
- **Indexers**: `scripts/build_local_db.py` (FTS5 + link graph), `scripts/build_embeddings.py` (dense half)
- **Retrieval**: `scripts/retrieval.py` — bm25, dense, hybrid, bfs, ppr
- **Corpus layout**: `<BENCH_ROOT>/corpus/` (documents), `<BENCH_ROOT>/questions/` (**quarantined**), `<BENCH_ROOT>/manifest.json`
- **Experiment note**: Context-Budget Renormalization

## Step 0: Pre-flight and the circularity quarantine <!-- :: section_id = step_0_pre_flight :: -->

1. Confirm the benchmark ships a **fixed, ingestible document corpus** — not a live-web or closed-index benchmark. If it does not, stop; this skill does not apply.
2. Download the benchmark and **immediately separate questions from corpus**: documents under `<BENCH_ROOT>/corpus/`, everything question-shaped (questions, answers, gold passage ids, supporting-fact labels) under `<BENCH_ROOT>/questions/`.
3. **Declare the quarantine.** For the remainder of ingestion, `<BENCH_ROOT>/questions/` is off limits — do not read it, do not grep it, do not pass its paths to a sub-agent. State this constraint verbatim in every sub-agent contract you dispatch.
4. Record the corpus baseline before touching it: document count, word-count distribution (median, p10, p90, min, max, **coefficient of variation**), and frontmatter presence. These become the *before* half of the renormalization measurement.
5. Create the isolated vault and confirm it is empty and separate from production.

## Step 1: Probe the corpus (agent decision input) <!-- :: section_id = step_1_probe :: -->

Read a **sample of documents, never the whole corpus**, and decide the questions the digestion planner needs answered: what genre is this (encyclopedic paragraphs, narrative prose, technical documentation, transcripts)? What is the natural atomic unit — a paragraph, a section, an entity? Which **building-block types** does the content map onto, and is the mapping honest rather than forced? Corpora of encyclopedic facts are mostly `concept` and `empirical_observation`; procedural corpora carry `procedure`; narrative corpora may fit none of our types cleanly, **and that is a finding to report rather than a problem to paper over**.

Record the genre assessment explicitly. Our digestion pipeline was tuned on technical documentation; a genre mismatch is the leading risk to external validity and must be stated in the experiment note, not discovered later.

## Step 2: Pilot one document (mandatory — pilot before full) <!-- :: section_id = step_2_pilot :: -->

Digest **one** document end to end through the full four-phase pipeline. Then inspect the output against three questions before proceeding:

- **Fidelity**: does every substantive claim in the source appear in some note? Read both and check by hand; do not delegate this.
- **Fan-out and expansion**: how many notes per document, and what is the word ratio? Our measured baseline on technical documentation is 0.7 to 2.7 notes per document at 1.15x words. A ratio far below 1.0 means the pipeline is compressing this genre, which changes what the experiment measures and must be reported.
- **Type honesty**: are the assigned building-block types the ones a careful reader would assign, or did the pipeline default everything to one type?

If any check fails, fix the plan and re-pilot. **Fan-out multiplies the cost of a wrong method by the corpus size**, so a bad pilot caught here costs one document and caught later costs the whole run.

## Step 3: Full ingestion <!-- :: section_id = step_3_full_ingestion :: -->

Run the four-phase pipeline over the corpus in batches, committing per batch. Two constraints carry over from the digestion runbook: cap agent fan-out at roughly 30 spawned agents per run, and give every sub-agent **absolute paths** — sub-agents inherit the session working directory, not the target directory, and a relative path silently produces a skipped file.

Dedup discipline is intrinsic and must not be skipped: a benchmark corpus frequently repeats the same entity across documents, and un-deduplicated notes would inflate the note count without adding knowledge, which would flatter our arm in the retrieval comparison.

## Step 4: Build the knowledge graph <!-- :: section_id = step_4_build_graph :: -->

Typed notes alone are not the treatment; the graph is. Three things must exist before the vault is usable as an arm:

1. **Typed links** — cross-references between notes, resolved and indexed. Verify with a link-count query, not by inspection; the link extractor only indexes the standard markdown link form, so a non-indexed format yields notes that look linked and are not.
2. **Folgezettel trails** — a benchmark corpus has no natural argumentative trail, so do not invent one. Use the corpus's own structure (document, section, entity) as the hierarchy and record that this is a *structural* rather than *dialectic* trail. Verify the prefix-derivable property.
3. **The index** — full database build plus the retrieval indexes, in the isolated vault.

## Step 5: Emit the provenance map <!-- :: section_id = step_5_provenance :: -->

Write `<EXP_VAULT>/provenance.json` mapping each source document to the notes derived from it, and each note back to its source spans. **Without this the evaluation cannot score the note arm at all**, because the benchmark's gold labels reference source documents while retrieval returns notes. Include per-document fan-out and word ratio so the renormalization measurement is reproducible from the artifact.

## Step 6: Verify the contract and the quarantine <!-- :: section_id = step_6_verify :: -->

Before declaring the corpus ready: format validators pass with zero errors; frontmatter is complete; the prefix-derivable property holds; the link and note counts are recorded; and the *after* half of the renormalization measurement is computed and compared against the Step 0 baseline — length coefficient of variation, expansion ratio, fan-out.

Then re-verify the quarantine: confirm no question file was read during ingestion, and state that explicitly in the experiment record. **If the quarantine was broken at any point, the corpus is contaminated and must be re-ingested from scratch.** A contaminated corpus that is used anyway produces numbers that look valid and are not, which is worse than no experiment.

## Error Handling <!-- :: section_id = error_handling :: -->

| Error | Cause | Recovery |
|-------|-------|----------|
| No ingestible corpus | Live-web or closed-index benchmark | Skill does not apply; choose a different benchmark |
| Fan-out below 1.0 with large word loss | Pipeline is compressing this genre | Stop; report the genre mismatch; do not proceed as though it were renormalization |
| Types all default to one value | Genre does not fit the building-block ontology | Report as a finding; consider a corpus-specific type mapping, declared in advance |
| Zero indexed links | Non-indexed link format used | Fix the link format and re-index; verify by query, never by reading |
| Quarantine breach | Question file read during ingestion | Discard the vault and re-ingest from scratch |
| Sub-agent skipped files | Relative paths given to sub-agents | Re-run with absolute paths; verify by file count, never by agent self-report |

## Checklist <!-- :: section_id = checklist :: -->

- [ ] Corpus and questions physically separated; quarantine declared in every sub-agent contract
- [ ] Step 0 baseline recorded (count, length distribution, coefficient of variation)
- [ ] Genre assessed and type mapping justified
- [ ] One document piloted and inspected by hand before full ingestion
- [ ] Full ingestion complete, committed per batch, absolute paths throughout
- [ ] Typed links verified by query; trails verified prefix-derivable; index built
- [ ] `provenance.json` written with per-document fan-out and word ratio
- [ ] Validators pass with zero errors
- [ ] Renormalization measurement computed and compared against baseline
- [ ] Quarantine re-verified and the verification stated in the experiment record
- [ ] Production vault confirmed untouched

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog — full vault skill index, organized by C.O.D.E. stage; this skill's row in the catalog has a back-link to this canonical body
