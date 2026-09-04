---
tags:
  - resource
  - skill
  - procedure
  - organize
  - vault-maintenance
keywords:
  - check note format
  - slipbox-check-note-format
  - in-vault skill canonical
topics:
  - Skill Procedures
  - Vault Tools
language: markdown
date of note: 2026-04-28
status: active
building_block: procedure
---

# Procedure: slipbox-check-note-format (Canonical Body)

> **Ported skill.** Adapted from an upstream vault canonical for use in this
> repository. All paths are local: notes live under `vaults/$CORPUS`, the database
> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill
> never reads or writes any vault outside this repo.

This is the **single canonical body** for the `slipbox-check-note-format` skill (FZ 12a). The thin headers under `.claude/skills/slipbox-check-note-format/SKILL.md` and `.kiro/skills/slipbox-check-note-format/SKILL.md` point an invoking agent here for the procedural content; only the format-specific frontmatter + ecosystem-required headers live in those thin shims.

## Skill description <!-- :: section_id = skill_description :: -->

Check if vault notes follow required format standards. Runs automated structural validation (YAML frontmatter, H1/H2 sections, internal links) via check_note_format.py, then adds semantic analysis for single-note checks. Supports single note, type filter, and full vault modes. Optional --fix mode auto-corrects simple issues.

## Setup <!-- :: section_id = setup :: -->

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```

## Resources <!-- :: section_id = resources :: -->

- **Hard-line script**: `python3 scripts/validate_notes.py "$VAULT"`
- **Comprehensive script**: `python3 scripts/validate_notes.py "$VAULT"`
- **Database**: `$DB` (resolved from config)
- **Vault root**: `$VAULT` (resolved from config)
- **YAML standard**: `slipbox/2_design/yaml_frontmatter_standard.md`
- **Note type designs**: `slipbox/2_design/note_type_*.md`

**Database schema**:
```
notes: note_id (PK, vault-relative path), note_name (filename stem), title, building_block, body, words, source_doc
       note_status, note_creation_date, file_path, tags (JSON), keywords (JSON), topics (JSON)

note_links: source_note_id -> target_note_id, link_context, link_type
```

## Validation Rules Reference <!-- :: section_id = validation_rules_reference :: -->

### Error Rules (required for database indexing) <!-- :: section_id = error_rules_required_for_database_indexing :: -->

| Rule | Check |
|------|-------|
| YAML-001 | YAML frontmatter must exist |
| YAML-010 | tags field must be present |

### Warning Rules (recommended) <!-- :: section_id = warning_rules_recommended :: -->

| Rule | Check |
|------|-------|
| YAML-011-015 | tags type, count, P.A.R.A. convention, lowercase, string type (no integers) |
| YAML-020-022 | keywords presence, type, count |
| YAML-030-032 | topics presence, type, count |
| YAML-040 | language field recommended |
| YAML-050-051 | date of note presence and YYYY-MM-DD format |
| YAML-060-061 | status presence and valid value |
| YAML-062-063 | building_block presence and valid value (concept, model, procedure, empirical_observation, argument, hypothesis, counter_argument, navigation) |
| YAML-070-081 | Type-specific fields for lit notes and paper sections |
| YAML-090 | book_title or source_url for digest notes |
| YAML-100 | No wiki links `[[...]]` in YAML fields |
| YAML-101 | No markdown links `[...](...)` in YAML fields |
| LINK-001 | Internal links must have .md extension |
| LINK-002 | Internal links should use relative paths |
| LINK-003 | Link target file should exist on disk |
| LINK-006 | Note should have at least one internal link (no orphans) |

### Info Rules (informational) <!-- :: section_id = info_rules_informational :: -->

H1-001/002 (heading count and prefix), H2-001/002 (required and unrecognized sections), PROSE-001 (mid-paragraph hard-wrapped prose — a prose line ending mid-sentence immediately followed by another prose line; a single newline renders as a space, so keep each paragraph on one logical source line), LINK-004 (Related Terms links), LINK-005 (paper back-links).

## When to Use <!-- :: section_id = when_to_use :: -->

- **After capture/digest skills** — verify output of `/slipbox-capture-term-note`, `/slipbox-capture-model-note`, `/slipbox-digest-paper`, etc.
- **Weekly vault health check** — run `--all --summary` to catch drift across the vault
- **Before git push** — spot-check recently modified notes
- **When a user asks** "does this note follow the format?" or "check my note format"
- **After batch changes** — e.g., after building_block backfill, tag renames, or decomposition campaigns

## When NOT to Use <!-- :: section_id = when_not_to_use :: -->

- For broken link repair — use `/slipbox-fix-broken-links`
- For atomicity/size analysis — use `/slipbox-detect-atomicity-drift`
- For content quality or semantic relevance — use `/slipbox-analyze-term-relevance`
- For ghost note resolution — use `/slipbox-resolve-ghost-term-matches`

## Step 1: Parse Arguments and Select Mode <!-- :: section_id = step_1_parse_arguments_and_select_mode :: -->

Parse `$ARGUMENTS` to determine invocation mode:

| Input Pattern | Mode | Action |
|---------------|------|--------|
| `<note_name>` | Single-note | Deep check with semantic analysis |
| `--type <subcategory>` | Type filter | Batch check all notes of one type |
| `--all` | Full vault | Vault-wide health report |
| `--fix` | Fix mode | Auto-correct simple issues (combine with any above) |
| No arguments | Help | Show usage instructions |

## Step 2: Run Hard-Line YAML Check First <!-- :: section_id = step_2_run_hard_line_yaml_check_first :: -->

Always run the strict YAML validator first. This catches MUST-FIX issues (missing `---`, missing required fields, links in YAML, non-string tags):

```bash
# Single file
python3 scripts/validate_notes.py "$VAULT"

# Full vault (summary)
python3 scripts/validate_notes.py "$VAULT"

# Specific directory
python3 scripts/validate_notes.py "$VAULT"
```

If hard-line errors exist, fix them BEFORE proceeding to Step 3.

## Step 3: Run Comprehensive Format Check <!-- :: section_id = step_3_run_comprehensive_format_check :: -->

Run the full format checker for structural validation (YAML warnings, H1/H2, links):

```bash
# Single note
python3 scripts/validate_notes.py "$VAULT"

# Type filter
python3 scripts/validate_notes.py "$VAULT"

# Full vault summary
python3 scripts/validate_notes.py "$VAULT"

# Full vault with JSON details
python3 scripts/validate_notes.py "$VAULT"

# Filter by severity
python3 scripts/validate_notes.py "$VAULT"
```

Parse the JSON output and present results in a structured table.

## Step 4: Semantic Analysis (single-note mode only) <!-- :: section_id = step_4_semantic_analysis_single_note_mode_only :: -->

For single-note checks, go beyond structural validation:

### 4a. Related Terms Quality <!-- :: section_id = 4a_related_terms_quality :: -->

Read the note's Related Terms section. For each linked term:
- Verify the term note exists and is not a stub
- Check if the linked term is semantically relevant to the note's content

### 4b. Missing Link Detection <!-- :: section_id = 4b_missing_link_detection :: -->

Query the database for term notes whose names match keywords in the note's content but are not currently linked:

```bash
sqlite3 "$DB" "
SELECT note_name, note_id FROM notes
WHERE note_name LIKE 'term\_%' ESCAPE '\'
  AND note_name NOT IN (
    SELECT REPLACE(target_note_id, '.md', '')
    FROM note_links WHERE source_note_id = '<current_note_id>'
  )
ORDER BY note_name;
"
```

Search the note content for matches against these term names. Report potential missing links. This also helps address LINK-006 (orphan notes).

### 4c. YAML Field Quality <!-- :: section_id = 4c_yaml_field_quality :: -->

Assess whether:
- keywords actually appear in or relate to the note content
- topics accurately categorize the note
- tags follow the P.A.R.A. convention (first tag = category type)

## Step 5: Fix Mode (--fix) <!-- :: section_id = step_5_fix_mode_fix :: -->

When `--fix` is specified, auto-correct issues with confirmation before applying.

### Hard-Line Fixes (from check_yaml_frontmatter.py) <!-- :: section_id = hard_line_fixes_from_check_yaml_frontmatter_py :: -->

| Issue | Auto-Fix |
|-------|----------|
| Missing opening `---` | Prepend `---\n` to file |
| Missing `date of note` | Add `date of note: YYYY-MM-DD` (today) |
| Missing `status` | Add `status: active` |
| Missing `building_block` | Identify from content: concept (definitions), procedure (how-tos/SOPs), model (system descriptions), empirical_observation (data/experiments), argument (claims with evidence), hypothesis (testable predictions), counter_argument (critiques), navigation (entry points/indexes) |
| Missing `keywords` | Add `keywords:\n  - <note_name>` (itemized list with note name as first keyword) |
| Missing `topics` | Add `topics:\n  - <inferred_topic>` (itemized list with inferred topic) |
| Tags not strings (integers) | Wrap in quotes: `2026` → `"2026"` |
| Wiki links in YAML | Remove `[[` and `]]` wrappers, keep path |

### Soft Fixes (from check_note_format.py) <!-- :: section_id = soft_fixes_from_check_note_format_py :: -->

| Issue | Auto-Fix |
|-------|----------|
| YAML-040: Missing language | Add `language: markdown` |
| YAML-015: Tags not lowercase | Convert to lowercase with underscores |
| LINK-001: Missing .md extension | Append .md to internal link targets |

### Fix Process <!-- :: section_id = fix_process :: -->
1. Run hard-line check first → collect fixable issues
2. Show summary table of proposed changes
3. Wait for user confirmation
4. Apply fixes with Edit tool
5. Re-run both validators to verify

Do NOT auto-fix: missing tags (human judgment), H2 issues (structural), LINK-003 (use /slipbox-fix-broken-links), LINK-006 (use /slipbox-add-inlinks).

## Step 6: Report Results <!-- :: section_id = step_6_report_results :: -->

### Single-note format <!-- :: section_id = single_note_format :: -->

Present a structured report with:
- Type, category, and status header
- Structural validation table (severity, rule ID, message)
- Result summary (error/warning/info counts)
- Semantic analysis findings (Related Terms quality, potential missing links, YAML quality)
- Specific recommendations

### Batch/vault format <!-- :: section_id = batch_vault_format :: -->

Present the summary table from the script output, then highlight:
- Note types with highest warning counts
- Most common issues across the vault
- Orphan notes (LINK-006) by type with suggested remediation
- Specific notes needing attention

## Cross-References <!-- :: section_id = cross_references :: -->

- `/slipbox-detect-atomicity-drift` — complementary (size vs format)
- `/slipbox-check-broken-links` — overlaps on LINK-003 (but this skill has broader scope)
- `/slipbox-fix-broken-links` — run after this skill to fix LINK-003 path issues
- `/slipbox-analyze-term-relevance` — deeper link analysis for Step 3b
- `/slipbox-capture-term-note` — run after to verify output; also for orphan term stubs
- `/slipbox-digest-paper` — run after to verify output

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

## Error Handling <!-- :: section_id = error_handling :: -->

| Error | Cause | Recovery |
|-------|-------|----------|
| Script not found | check_note_format.py missing | Verify scripts/ directory and run from repo root |
| Note not found | Invalid name or path | Script lists fuzzy matches; try with full relative path |
| YAML parse failure | Malformed frontmatter | Reported as YAML-002 error; manual fix required |
| Database unavailable | DB not built or path wrong | Run `/slipbox-run-full-database-rebuild` first |
| Fix mode conflict | Edit fails on ambiguous string | Use more specific old_string context for Edit tool |

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog — full vault skill index, organized by C.O.D.E. stage; this skill's row in the catalog has a back-link to this canonical body
