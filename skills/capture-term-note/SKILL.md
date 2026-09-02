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

**Corpus evidence and external context are separated, never merged.** A term note
may be enriched from the web — a benchmark corpus mentions terms it never defines,
and a reader who cannot say what FTT or a VLOP *is* cannot use the note. But
external material is quarantined from the corpus material, because they play
different roles in the evaluation:

| | Comes from | Goes in | Counted by the scorer |
|---|---|---|---|
| Corpus evidence | the corpus, only | `## Definition`, `## Context`, `## Key Characteristics`, `source_docs` | yes |
| External context | web search | `## Background (external)`, `external_refs` | **no** |

`source_docs` lists **corpus documents only**. That is what keeps scoring honest:
gold labels are passage-level over the corpus, so a note is credited for the
corpus documents it carries and never for what it borrowed. Web search may still
change retrievability — more vocabulary means more lexical surface — so the
enrichment is recorded in frontmatter (`enriched: web`) and can be ablated:
re-run the comparison with external sections stripped to see whether any
advantage survives.

**Never let external material answer a question the corpus cannot.** If the web
says something the corpus does not, it belongs under `## Background (external)`
with its source named, never in the Definition. The question the experiment asks
is whether typed notes retrieve the corpus better — a note that smuggles in
outside answers is measuring something else.

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

## Step 2a: Gather evidence from the corpus (primary)

Collect every passage in the corpus that mentions the term, plus every existing
vault note that references it. **This set is the whole evidence base.** Record
the source document ids — they become the note's provenance and the glossary
entry's `Source`, and without them the note cannot be scored against
passage-level gold labels.

If the corpus says too little to write a real definition, proceed to Step 2b and
enrich — but record what the corpus itself supported, so corpus coverage stays
measurable. Never fill the gap from model recall: an unattributed definition is
contamination that no downstream check will catch, because nothing marks it as
having come from outside.

## Step 2b: Enrich from the web (secondary, optional)

Use `WebSearch` or `WebFetch` when the corpus mentions a term without defining
it — acronyms (FTT, VLOP, DSA), named regulations, technical mechanisms, or
organisations whose role the reader needs in order to follow the corpus.

Record for every external claim: the **URL**, the **publisher**, and the
**access date**. An unattributed external claim is indistinguishable from
fabrication once it is in the note.

Skip this step entirely when the corpus already defines the term. Enrichment is
for gaps, not for length.

## Step 3: Write the term note

Path: `$VAULT/term_<normalized_name>.md`. Required frontmatter:

```yaml
---
building_block: concept
source_docs: [<doc_id>, ...]        # CORPUS documents only — the scoring key
enriched: web                        # omit entirely when no external material
external_refs:                       # omit entirely when no external material
  - <url> (<publisher>, accessed <YYYY-MM-DD>)
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

## Background (external)
<Only if enriched. What the corpus does not supply, each claim attributed inline
to a source in `external_refs`. Omit this section entirely when the corpus was
sufficient.>

## Related Notes
- [<Other Note>](<other>.md): <how they relate>

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

## Step 5: Link by content relevance, not by memory

Two directions, and both are required.

**Outbound.** Find genuinely related notes by *searching on the note's content*,
not by recalling what you wrote earlier:

```bash
python3 scripts/retrieval.py "$VAULT" --query "<the note's Definition sentence>" \
    --strategy hybrid --k 8
```

Link the results that are actually related, with a clause saying **how** they
relate. Aim for **at least three** outbound links; a note with one is usually
under-connected rather than genuinely isolated. Discard results that merely share
vocabulary — a link that does not carry a real relation adds a false edge, and
the graph arms traverse every edge they are given.

**Inbound.** Add a link from each existing note that mentions the term, placed
inside that note's `Related Notes` section rather than appended at the end.

A note nothing links to is a graph island: retrievable by name, unreachable by
traversal, and therefore invisible to the graph arm being evaluated. Since the
graph *is* the treatment under test, an under-linked vault does not merely lose
recall — it removes the thing being measured.

## Step 6: Validate

```bash
python3 scripts/validate_notes.py "$VAULT" --gate
python3 scripts/build_local_db.py "$VAULT" --stats
```

Both must pass before the term is considered captured. The link count in the
second command must show **zero unresolved** — any unresolved link points
outside this vault and is a contamination signal.

## Knowledge Building Blocks (reference)

Every note carries exactly **one** `building_block:`. Closed enum — any other
value is rejected by `scripts/validate_notes.py` (rule `FM-003`):

| Type | Answers | Must retain |
|---|---|---|
| `concept` | *What is X?* | definition, discriminating features, boundary cases |
| `model` | *How does X relate to Y?* | structure, relations, the range over which they hold |
| `procedure` | *How do I do X?* | ordered steps, preconditions, where it does not apply |
| `empirical_observation` | *What happened?* | the event, its source, time anchor, conditions |
| `argument` | *Why believe P?* | claim, grounds, and the warrant joining them |
| `counter_argument` | *Why might that be wrong?* | which premise or inference it attacks |
| `hypothesis` | *Might P be true?* | the proposition and what would falsify it |
| `navigation` | *Where do I find things?* | index or routing only, no substantive claims |

The type is chosen **before** writing, because it is a retention contract: the
"must retain" column names the fields that have to survive. Scope conditions —
preconditions, authority, time anchors, applicability bounds — are the class an
unconditioned summariser reliably deletes, since they qualify claims rather than
being claims. Never mix two building blocks in one note.

Full definitions, the source-classification table, and the benchmark-corpus
caveats: `docs/BUILDING_BLOCKS.md`.

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
