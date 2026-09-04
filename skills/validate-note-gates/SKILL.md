---
tags:
  - resource
  - skill
  - procedure
  - organize
  - knowledge-management
  - quality
  - verification
keywords:
  - validate note gates
  - slipbox-validate-note-gates
  - note format check
  - broken links
  - ghost references
  - validation gate
  - in-vault skill canonical
topics:
  - Skill Procedures
  - Vault Tools
language: markdown
date of note: 2026-06-17
status: active
building_block: procedure
---

# Procedure: slipbox-validate-note-gates (Canonical Body)

> **Ported skill.** Adapted from an upstream vault canonical for use in this
> repository. All paths are local: notes live under `vaults/$CORPUS`, the database
> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill
> never reads or writes any vault outside this repo.

This is the **single canonical body** for the `slipbox-validate-note-gates` skill (FZ 12a). The thin headers under `.claude/skills/slipbox-validate-note-gates/SKILL.md` and `.kiro/skills/slipbox-validate-note-gates/SKILL.md` point an invoking agent here for the procedural content; only the format-specific frontmatter + ecosystem-required headers live in those thin shims.

## Skill description <!-- :: section_id = skill_description :: -->

The shared, required validation gate for every capture/digest skill. Runs three quality gates against newly created or modified notes — **G1 note format** (`check_note_format.py`), **G2 broken links** (`/slipbox-fix-broken-links`), and **G3 ghost references** (`/slipbox-fix-ghost-references`) — in the correct order around the incremental database update, then reports a single pass/fail verdict. This is the one source of truth for the format + broken-link + ghost-reference gate sequence so the 28+ capture/digest skills do not each re-implement it. Invoke as the final step of any note-authoring skill, before declaring the task done.

## Setup <!-- :: section_id = setup :: -->

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```


## Inputs <!-- :: section_id = inputs :: -->

The calling skill passes (or the agent already knows) the **list of note file paths it just created or modified** (`$NEW_NOTES`). G1 is scoped to those files; G2/G3 are vault-wide but only the calling skill's notes must be clean for the gate to pass.

## Why this ordering <!-- :: section_id = why_this_ordering :: -->

Format is a file-level check (no DB needed) and must pass **before** indexing. Broken-link and ghost-reference detection both read tables (`broken_links`, `ghost_notes`/`ghost_note_references`) that are rebuilt by the database update — so the DB update sits **between** G1 and G2/G3.

```
G1 format  →  DB update (rebuild link tables)  →  G2 broken links  →  G3 ghost references  →  verdict
```

## Steps <!-- :: section_id = steps :: -->

### GATE 1 — Note format <!-- :: section_id = gate_1_note_format :: -->

Run the format checker on each new/modified note (errors must be 0; warnings/info are best-effort):

```bash
python3 scripts/validate_notes.py "$VAULT"
```

Or invoke `/slipbox-check-note-format`. Fix every **error** before proceeding (common false positive: a scheme-less URL like `(example.com/...)` in a markdown link is flagged LINK-001 — prefix `https://`). **Do not run the DB update until all new notes pass G1 with 0 errors.**

### DB UPDATE — Rebuild link tables <!-- :: section_id = db_update_rebuild_link_tables :: -->

```bash
python3 scripts/build_local_db.py "$VAULT"
```

Note the `post-state` line — it reports `broken=<N>` and `ghosts=<N>`; record these baselines.

### GATE 2 — Broken links <!-- :: section_id = gate_2_broken_links :: -->

Confirm the new notes introduced no broken links (internal links to the wrong relative path of an existing file):

```bash
sqlite3 "$DB" "SELECT COUNT(*) FROM broken_links WHERE source_note_id LIKE '%<note_slug>%';"
```

If any new note shows broken links, run `/slipbox-fix-broken-links` (dry-run → confirm → apply), then re-run the DB update and re-check.

### GATE 3 — Ghost references <!-- :: section_id = gate_3_ghost_references :: -->

Confirm the new notes introduced no ghost references (links whose target file does not exist):

```bash
sqlite3 "$DB" "SELECT COUNT(*) FROM ghost_note_references WHERE source_note_id LIKE '%<note_slug>%';"
```

If any new note shows ghost references, run `/slipbox-fix-ghost-references` (detect → decide redirect/drop/defer → dry-run → apply), then re-run the DB update and re-check. Prevention: only link a target whose file already exists.

### FINAL — Pass/fail verdict <!-- :: section_id = final_pass_fail_verdict :: -->

Report a single explicit verdict. The gate **passes only if all three are true for every new note**:

| Gate | Pass criterion |
|------|----------------|
| G1 format | 0 errors from `check_note_format.py` on each new note |
| G2 broken links | 0 rows in `broken_links` sourced from any new note |
| G3 ghost references | 0 rows in `ghost_note_references` sourced from any new note |

Emit the verdict in this exact shape so the calling skill's self-check can confirm it:

```
VALIDATION GATES: PASS  (G1 format ✓ | G2 broken ✓ | G3 ghost ✓ | G4 facts ✓ | G4b weight ✓ | G5 self-suff ✓)
```

or, if any gate fails after remediation attempts:

```
VALIDATION GATES: FAIL  (G1 ✓ | G2 ✓ | G3 ✗ — <N> ghost ref(s) in <note> | G4 ✓ | G5 ✓)
```

On FAIL, do not declare the parent note-authoring task done — surface the failing gate and the offending note(s).

### GATE 4 — Fact preservation <!-- :: section_id = gate_4_fact_preservation :: -->

**Why.** Measured on the benchmark vault, 18.3% of gold facts were unrecoverable
from any note, against 0.9% for a plain chunker. A fact the writer dropped is
unreachable no matter how good retrieval is, and no other gate can see it — G1
checks format, G2 links, G3 ghosts. None of them reads the source.

**Check.** For each note, take the source blocks the plan's coverage map assigns
it. Every **date, quantity with a unit, proper name and figure** appearing in
those blocks must appear in the note, verbatim where it is a number or a name.
Paraphrase the prose; do not paraphrase the data.

Report any dropped item as `FP-001 <note>: <item> present in assigned source,
absent from note`. This is cheap because the coverage map already names which
blocks each note owns.

**Not a licence to pad.** If a block genuinely belongs to a different note, fix
the coverage map rather than copying the fact into both — a fact duplicated
across notes is how sibling notes come to disagree.

### GATE 4b — Weight <!-- :: section_id = gate_4b_weight :: -->

**Why.** The note layer's measured deficit against a chunker is information per
token, not thoughts per note: a pipeline-built note carries about the same
number of facts as a 100-word chunk and spends 190 words doing it. No format or
link gate can see this, because an over-weight note is perfectly well-formed.

**Check.** Body word count, excluding frontmatter and the Related Notes and
Source sections, against the ceiling for the note's building block:

| building block | ceiling |
|---|---|
| empirical_observation | 130 |
| concept | 160 |
| navigation | 170 |
| model, hypothesis, counter_argument | 190 |
| argument | 220 |
| procedure | 350 |

Report as `WT-001 <note>: <n> body words, ceiling <c> for <block>`. A breach is
not automatically a split — it is a prompt to check which of the two defects is
present, a second thought or a padded one.

**Report the distribution, not only the breaches.** Median body words per block
is the number that says whether the vault as a whole competes on density, and a
gate that only lists outliers hides a corpus that is uniformly 60% too heavy.

### GATE 5 — Self-sufficiency <!-- :: section_id = gate_5_self_sufficiency :: -->

**Why.** This is the one property the note layer measurably wins on: notes never
open with an unresolved reference where 7.5% of chunks do, and they carry a date
more than twice as often. It is also the property most at risk from the
atomicity rules, because the obvious way to make a note smaller is to delete the
context that lets it stand alone. Gate it so the improvement cannot destroy it.

**Check.** For each note:
- It must not open with a **dangling** reference — a bare pronoun or connective
  pointing outside the note: `he`, `she`, `they`, `it`, `its`, or `but`,
  `however`, `meanwhile`, `therefore`. Report as `SS-001`.
- **Self-reference is not dangling.** "This index covers…", "These notes
  record…", "This review of…" anchor the demonstrative to the note itself and
  are exactly how a navigation note should open. A checker that flags them will
  send correct notes back for rewriting — it flagged all seven navigation notes
  in the first pilot before being corrected.
- It must name its own subject: the note's title entities appear in the body.
  Report as `SS-002`.
- Where its assigned source carries a date, the note must carry one. Report as
  `SS-003`.

A note failing this is a fragment, not an atom. Atomicity without resolution is
the opposite failure and equally disqualifying.

## Important Constraints <!-- :: section_id = important_constraints :: -->

1. **All three gates are mandatory** — a note-authoring task is not complete until G1, G2, and G3 all pass for every new note.
2. **Ordering is fixed** — G1 before the DB update (format is file-level); G2/G3 after (they read rebuilt tables).
3. **Scope to the new notes** — vault-wide pre-existing broken/ghost debt is not this gate's responsibility; only the calling skill's notes must be clean to pass.
4. **Single source of truth** — capture/digest skills invoke this skill rather than re-implementing the sequence; edit the gate here, once.
5. **Explicit verdict required** — always emit the `VALIDATION GATES: PASS/FAIL` line so the caller can self-check.

## Where Notes Go, and What They Must Carry

**Every note this skill creates is written to `$VAULT/<slug>.md` — flat, one
directory, no subtree.** `scripts/build_local_db.py` indexes `$VAULT/**/*.md`
and uses the vault-relative path as the note id, so a flat layout makes the id
equal to the filename and lets links be bare filenames that always resolve.

The source vault's `resources/` / `areas/` / `projects/` tree is deliberately
**not** reproduced. That tree encodes a personal-vault organising scheme; here
it would only make a note's id depend on a routing decision, adding a free
parameter to the retrieval comparison for no benefit.

### Required frontmatter

```yaml
---
tags:                                # FM-010 — 2+, first is a P.A.R.A. type
  - resource                         #   archive | area | entry_point | project | resource
  - <domain tag>
keywords:                            # FM-020 — 3+, and see below
  - <term the note is about>
  - <term a question would use>
  - <acronym or variant spelling>
topics:                              # FM-030
  - <broad subject area>
language: markdown                   # FM-040
date of note: <YYYY-MM-DD>           # FM-040
status: active                       # FM-040
building_block: <one of the eight>   # FM-002 / FM-003 — closed enum
source_docs: [<corpus_doc_id>, ...]  # FM-004 — the corpus evidence, the scoring key
---
```

**`keywords` and `topics` are retrieval surface, not decoration.** Graph
traversal can be seeded by matching a query against
`note_name`, `keywords`, `topics` and `tags` — so a note with none of them is
invisible to that seeding, and a vault with none of them cannot run the strategy
at all. They are also a denser statement of what the note is about than its body:
a short question tends to use the vocabulary a keyword list is written in, while
a body buries that vocabulary among incidental words. Write keywords a
*questioner* would use, not a summary of the note.

`building_block` and `source_docs` are ERRORS if absent. The rest are WARNINGS:
their absence degrades retrieval without making a note unscorable, and gating on
them would block a vault that is merely incomplete rather than wrong.

`navigation` notes — glossaries, entry points, indexes — are **exempt from
`source_docs`**. They index rather than assert, so there is no document to trace
them to; their links are their provenance. Every other building block requires
it.

Both are **enforced**, not conventional. `building_block` is what the retrieval
arms stratify on. `source_docs` is what makes the note scorable at all: gold
labels in these benchmarks are passage-level, so a note that cannot name the
documents it came from cannot be credited when it is retrieved. A note without
it is invisible to the evaluation even when it is correct.

`tags`, `keywords`, `topics`, `status`, `language` and `date of note` may be
included and are preserved, but the database does not read them — do not spend
effort on them at the expense of the two fields above.

### One note, one topic — then one building block, then a size budget

**Thought-atomicity decides where a note ends.** One note carries one thought of
its building block's kind — one fact, definition, mechanism, outcome, claim,
objection, hypothesis or index scope — so that retrieving it returns one whole
thing rather than several partial ones.

**Topical coherence is not the boundary.** Several thoughts about one subject are
exactly what a coherence rule merges, and the merged note then holds many
thoughts while passing every size check. Split on the thought; stop when the
relation between the halves can no longer be stated in one line.

**Density then constrains size, it does not set boundaries.** Past 1,800 source
words a coherent unit splits again — at a sub-topic boundary, never at a word
count. Applying size first merges unrelated subjects that happen to be short,
producing a note that is retrieved for everything and answers nothing.

### Related Notes — derived from evidence, minimum three

Every note carries a `## Related Notes` section with **at least three** outbound
links, each naming **how** the notes relate, not merely that they do.

Two ways to find them, and both beat recall:

```bash
# already-written notes: search on this note's own content
python3 scripts/retrieval.py "$VAULT" --query "<the note's opening claim>"     --strategy hybrid --k 8

# planned term notes: derive from the source blocks this note carries
python3 scripts/build_term_links.py <slug> --plans experiments/plans/<slug> --floor 3
```

The second is what makes a per-note term table possible before the vault exists.
A term links to a note when the term's surface forms appear in **that note's own
source text**, so relevance is corpus evidence rather than recollection. That is
the whole difference between a relevancy-ranked mapping and a padded one.

**The floor is a floor, never a quota.** A spurious edge is not harmless: `bfs`
and `ppr` traverse every edge they are given, so a false link degrades the arm
under test as surely as a missing one. Link density has an **optimum, not a
maximum**. If a floor cannot be met from evidence, the answer is to widen the
term list or accept the note as peripheral — never to invent an edge. On this
corpus a floor of 8 would have fabricated 40% of the graph, which is why the
measured floor is 3.

A note with no inbound link is a graph island: retrievable by name, unreachable
by traversal. Since the graph IS the treatment being measured, an under-linked
vault removes the thing the experiment exists to test.

### Required structure

- **H1 first** — the first content line after the frontmatter (`ST-001`/`ST-002`).
  It becomes the note title in the database and in every retrieval result.
- **Links are bare filenames** — `[Other Note](other_note.md)`, resolved inside
  `$VAULT` only. A link that escapes the vault is reported as `LN-002`
  contamination, because it means the note was written against a different vault.

### Verify before considering the note written

```bash
python3 scripts/validate_notes.py "$VAULT" --gate
python3 scripts/build_local_db.py "$VAULT" --stats
```

The second must report **zero unresolved links**.

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

Full definitions and the benchmark-corpus caveats: `docs/BUILDING_BLOCKS.md`.

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog — full vault skill index, organized by C.O.D.E. stage; this skill's row in the catalog has a back-link to this canonical body
