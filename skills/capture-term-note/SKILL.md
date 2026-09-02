---
tags:
  - skill
  - procedure
  - capture
  - term
  - glossary
keywords:
  - capture term note
  - corpus-local research
  - glossary bootstrap
  - dedup before create
  - blind ingestion
topics:
  - Skill Procedures
language: markdown
date of note: 2026-09-01
status: active
building_block: procedure
---

# Capture a Term Note from the Corpus

> **Rewritten, not ported.** The upstream canonical researches each term against
> internal wikis and documents, which is unavailable here and forbidden by the
> blind-ingestion rule. This version researches **the corpus and the vault only**,
> and creates the glossary on first use instead of routing into a pre-existing one.

## Setup

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
GLOSSARY="$VAULT/glossary.md"   # created by the first capture
```

## Skill description

Create a `concept` note for a term that appears in the corpus, and register it
in the corpus glossary. Invoked by the digestion pipeline whenever a planned
note references a term that has no note yet — the Undigested Terms Plan — and
usable standalone.

**Two rules distinguish this from the upstream skill, and both are load-bearing.**

The term's meaning comes from **the corpus and existing vault notes only**. No
web search, no external lookup, no model recall dressed up as research. A note
that imports knowledge the corpus does not contain breaks the blind-ingestion
guarantee and silently invalidates the retrieval comparison, because the note
would then answer questions the source documents cannot.

And the glossary **does not exist yet**. Upstream routes a new term into one of
several established domain glossaries; here the first capture creates the
glossary, and it stays a single file until the corpus is large enough for
domains to be visible in the data rather than guessed in advance.

## Step 1: Dedup before create

```bash
python3 scripts/glossary.py "$VAULT" --check "<TERM>"
```

Exit code 1 means the term exists or a near match does. **Resolve before
writing anything**: update the existing note, or establish that the two are
genuinely distinct concepts and say so in both notes. Creating a second note
for the same concept is the failure this step exists to prevent, and it is
invisible afterwards — retrieval simply splits its evidence across two notes.

Also check the note store directly, since a term may have a note before it has
a glossary entry:

```bash
python3 scripts/retrieval.py "$VAULT" --query "<TERM>" --strategy hybrid --k 5
```

## Step 2: Gather evidence from the corpus

Collect every passage in the corpus that mentions the term, plus every existing
vault note that references it. **This set is the whole evidence base.** Record
the source document ids — they become the note's provenance and the glossary
entry's `Source`, and without them the note cannot be scored against
passage-level gold labels.

If the corpus says too little to write a real definition, **stop and record the
term as under-evidenced** rather than filling the gap from memory. An honest
absence is a finding about corpus coverage; a fabricated definition is
contamination that no downstream check will catch.

## Step 3: Write the term note

Path: `$VAULT/term_<normalized_name>.md`. Required frontmatter:

```yaml
---
building_block: concept
source_docs: [<doc_id>, ...]
---
```

Structure, claim-first so the definition sits where attention falls:

```markdown
# <Term Name>

## Definition
<What it is, in one or two sentences, entailed by the cited passages.>

## Context
<Where it appears in the corpus and what it relates to.>

## Key Characteristics
<Distinguishing properties, each traceable to a passage.>

## Related Terms
- [<Other Term>](term_<other>.md): <how they relate>

## Source
- <doc_id>: <short quote or locator>
```

**Every claim must be entailed by a cited passage.** `Related Terms` links only
to notes inside this vault — a link that escapes the vault is flagged as
contamination by the validator, because it means the note was written against a
different vault.

## Step 4: Create or update the glossary

```bash
python3 scripts/glossary.py "$VAULT" \
    --add "<Term Name>" \
    --full-name "<Expanded name, if the corpus gives one>" \
    --description "<2-4 sentences: what it is, how it works, what distinguishes it. No metrics.>" \
    --note "term_<normalized_name>.md" \
    --source "<doc_id>"
```

The script bootstraps the glossary if absent, inserts alphabetically, and
updates in place when the term already exists. It warns once the glossary
outgrows a single file; **cluster the existing terms before splitting**, so the
domains come from the corpus rather than from a schema decided up front.

## Step 5: Backlink

Add a link from each note that mentions the term to the new term note, inside
an existing `Related Terms` section rather than appended at the end. A term note
nothing links to is a graph island: retrievable by name, unreachable by
traversal, and therefore invisible to the graph arm being evaluated.

## Step 6: Validate

```bash
python3 scripts/validate_notes.py "$VAULT" --gate
python3 scripts/build_local_db.py "$VAULT" --stats
```

Both must pass before the term is considered captured. The link count in the
second command must show **zero unresolved** — any unresolved link points
outside this vault and is a contamination signal.

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `--check` exits 1 with EXISTS | Term already captured | Update that note; never create a second |
| `--check` exits 1 with NEAR MATCH | Similar term exists | Decide same-or-distinct explicitly; record the decision in both notes |
| Corpus evidence too thin | Term is mentioned but not explained | Record as under-evidenced; do NOT write from memory |
| Validator reports LN-002 | A link escapes the vault | The note was written against another vault; rewrite the link |
| Glossary exceeds the split threshold | Corpus outgrew one file | Cluster existing terms, then split on observed domains |

## Checklist

- [ ] Dedup checked against both glossary and note store
- [ ] Every claim entailed by a cited corpus passage; nothing from memory or the web
- [ ] `source_docs` frontmatter populated
- [ ] Glossary entry created or updated, alphabetical
- [ ] Backlinks added inside existing Related Terms sections
- [ ] Validator gate passes; zero unresolved links
