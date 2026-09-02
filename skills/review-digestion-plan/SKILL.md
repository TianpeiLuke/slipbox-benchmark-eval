---
tags:
  - resource
  - skill
  - procedure
  - capture
  - planning
  - quality
  - review
keywords:
  - review digestion plan
  - slipbox-review-digestion-plan
  - in-vault skill canonical
  - 6 checkpoints
  - plan sign-off
  - ready not ready
topics:
  - Skill Procedures
  - Vault Tools
language: markdown
date of note: 2026-05-23
status: active
building_block: procedure
---

# Procedure: slipbox-review-digestion-plan (Canonical Body)

> **Ported skill.** Adapted from an upstream vault canonical for use in this
> repository. All paths are local: notes live under `vaults/$CORPUS`, the database
> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill
> never reads or writes any vault outside this repo.

This is the **single canonical body** for the `slipbox-review-digestion-plan` skill (FZ 12a).

## Skill description <!-- :: section_id = skill_description :: -->

Final review and sign-off for a digestion plan before execution begins. Runs **9 mandatory checkpoints** that verify: (1) Related Notes step exists, (2) ALL 8 GATEs per batch (G1-G6 + G8-Discoverability — G5 ghost-detect + G6 broken-link-fix added 2026-06-12, G8 inbound-link 2026-06-13), (3) entry point update specified, (4) plan size manageable, (5) note format aligned **and derived** from existing notes, (6) borderline density → promote split, (7) source word counts are measured (not under-estimated), (8) Undigested Terms Plan + Term-Note Authoring Requirements + **all-notes (term AND doc) dedup/collision audit**, (9) **Discoverability — inbound links executed (G8), no graph islands** (CP9 added 2026-06-13). Reports READY or NOT READY. Use AFTER `/slipbox-augment-digestion-plan` completes the plan augmentation.

## Setup <!-- :: section_id = setup :: -->

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```

## Resources <!-- :: section_id = resources :: -->

- **Plan to review**: `$PLANS/plan_digest_<topic>.md`
- **Format checker**: `python3 scripts/validate_notes.py "$VAULT"`
- **Target directory**: read existing notes in target dir to verify format alignment

---

## Step 1: Read the Plan <!-- :: section_id = step_1_read_plan :: -->

Read the plan file. Confirm it has `status: pending` (not already completed or in-progress).

---

## Step 2: Checkpoint 1 — Related Notes Step <!-- :: section_id = step_2_cp1 :: -->

**Check**: Does the plan include an explicit step to add `## Related Notes` references to every captured note?

**Look for**:
- A "Phase Xb: Add Related Notes" step with per-note mapping
- OR a cross-reference mapping table showing which terms/repos/snippets each note links to
- OR inline specification in the Planned Notes table

**Minimum requirement**:
- **Floor**: Each note must link to **≥8 relevancy-selected `$VAULT/` term notes** + ≥1 entry point back-link (raised ≥3 → ≥6 2026-06-13, ≥6 → ≥8 2026-06-21; terms chosen by content relevancy, not padding). Each term goes in the note's `## Related Notes` (reference) section as an indexed markdown link **with a term description AND its relevancy to this note** (`- Term — desc; relevance: …`); a bare link with no relevancy statement FAILs CP1. Other related notes (tools/repos/areas/siblings) are additional.
- **Target**: If `/slipbox-search-notes` returns many highly-relevant matches (PPR score >0.5 or direct keyword match), increase to ≥6-8 related notes per note. More cross-references = better graph connectivity and discoverability.
- **Guideline**: Notes on well-documented topics (e.g., MeshClaw, Builder MCP, OTF) should have 6-8 references. Notes on niche or new topics may only have 3-4.

**Result**: PASS / FAIL (if FAIL: "Missing Related Notes step — add per-note link mapping")

---

## Step 3: Checkpoint 2 — ALL 7 GATEs Per Batch <!-- :: section_id = step_3_cp2 :: -->

**Check**: Does every execution phase have a GATE table with ALL 7 gates? (G5 + G6 added 2026-06-12; older plans may only have G1-G4 → REVIEW MUST FAIL until augmented.)

**Count**:
- Number of execution phases in plan: N
- Number of GATE tables found: M
- Each table must contain ALL of:
  - **G1-Format** — skill-driven via `/slipbox-check-note-format` (incl. PROSE-001: no mid-paragraph hard-wrapped prose — blocking error)
  - **G2-Grounding** — content faithful to source
  - **G3-Density** — ≤400 lines / ≤1800 words / ≤6 code blocks
  - **G3-Coverage** — every source H2/H3 mapped
  - **G4-CrossRef** — links resolve + entry point + inlinks
  - **G5-Ghost** — every reference verified to exist; ghosts resolved via `/slipbox-fix-ghost-references` (redirect / drop / defer-to-capture)
  - **G6-Broken** — skill-driven via `/slipbox-check-broken-links` + `/slipbox-fix-broken-links`
  - **Consolidated gate** — the plan may run G1+G5+G6 together via `/slipbox-validate-note-gates` at batch close (single PASS/FAIL verdict); confirm the plan references it.

**Result**: PASS (M ≥ N and all 7 gates in each) / FAIL (missing gates — list which phases lack them and which gates).

> **Common failure pattern after 2026-06-12 spec update**: plans written before the spec change carry only G1-G4. The review skill MUST FAIL such plans with a recommendation to re-run `/slipbox-augment-digestion-plan`, which will append G5 + G6 per phase.

---

## Step 4: Checkpoint 3 — Entry Point Update Specified + Discovery <!-- :: section_id = step_4_cp3 :: -->

**Check**: Does the plan specify which entry point(s) to update? Are there ADDITIONAL entry points the plan should also update?

### 4a. Verify plan specifies at least one entry point

**Look for**:
- Specific filename (e.g., `entry_openclaw_meshclaw.md`)
- What section to add or modify
- Whether to create a NEW entry point (if >15 notes)

### 4b. Search for additional related entry points

Search the vault for ALL entry points that relate to the topic:

```bash
sqlite3 "$DB" \
  "SELECT note_id, note_name, file_path
   FROM notes
   WHERE note_location LIKE 'entry_%'
     AND (note_name LIKE '%<TOPIC_KEYWORD_1>%'
          OR note_name LIKE '%<TOPIC_KEYWORD_2>%'
          OR keywords LIKE '%<TOPIC_KEYWORD>%')
   ORDER BY static_ppr_score DESC LIMIT 10;"
```

Also run `/slipbox-search-notes <TOPIC> --type entry_point` or browse `$VAULT/` to find any entry points the keyword search may have missed.

### 4c. Decide if plan should update additional entry points

For each discovered entry point, ask: "Would a user browsing THIS entry point expect to find links to the new notes?"

If YES → add to the plan's "Entry Points to Update" section.

### 4d. Verify CREATE-vs-UPDATE decision matches size threshold (added 2026-06-12)

Per `/slipbox-plan-digestion` Step 4c + `/slipbox-augment-digestion-plan` Step 10.7, the entry-point decision is SIZE-DRIVEN:

| Total digest notes | Required action |
|---|---|
| <15 | UPDATE existing entry point(s) only |
| 15-30 (single plan) | CREATE dedicated `entry_<slug>.md` + UPDATE parent hub |
| >30 (master+sub-plans) | CREATE dedicated `entry_<slug>.md` REQUIRED + UPDATE parent hub |

Read the plan's `## Entry Point Decision` section AND the planned total notes count. Verify the stated action matches the threshold.

Common failures to flag:
- Plan says UPDATE only but total notes ≥15 → FAIL (insufficient — needs a dedicated entry point)
- Plan says CREATE but total notes <15 → FAIL (over-engineering — sparse entry point, route to UPDATE)
- Plan says CREATE but does not name the parent hub or back-link → FAIL (orphan entry point)
- Plan says CREATE but does not specify the new entry point's required body sections (Quick Stats, per-section table, Related Entry Points, References) → FAIL

**Result**: PASS (at least 1 entry point specified + size-decision matches threshold + parent hub identified if CREATE) / FAIL (specific gap listed)

---

## Step 5: Checkpoint 4 — Plan Size Manageable <!-- :: section_id = step_5_cp4 :: -->

**Check**: Is the planned note count ≤30? If >30, are sub-plans defined?

**Count**: Total planned notes from the plan table.

**If >30**: Plan SHOULD split into sub-plans. Each sub-plan ≤15-20 notes, independently executable, with cross-references documented.

**Result**: PASS (≤30 notes) / PASS with note (>30 but sub-plans defined) / FAIL (>30 with no split strategy)

---

## Step 6: Checkpoint 5 — Note Format Aligned <!-- :: section_id = step_6_cp5 :: -->

**Check**: Does the plan's Note Format Definition match existing notes in the target directory?

### 6a. Read the plan's YAML template

Extract the sample YAML from the "Note Format Definition" section.

### 6b. Read one existing note in the target directory

```bash
ls "$VAULT/<target_dir>/" | head -5
```

Read one existing note and compare its YAML frontmatter against the plan's template.

### 6c. Verify alignment

| Field | Plan Template | Existing Note | Match? |
|-------|--------------|---------------|--------|
| tags order | resource, documentation, ... | ? | ? |
| keywords | present | ? | ? |
| topics | present | ? | ? |
| language | markdown | ? | ? |
| date of note | YYYY-MM-DD | ? | ? |
| status | active | ? | ? |
| building_block | correct type | ? | ? |

### 6d. Check forbidden fields

Confirm plan lists these as FORBIDDEN: title, category, created, updated, source, parent, author, related_wiki, note_second_category

### 6e. Verify the format was DERIVED from existing notes, not invented (added 2026-06-13)

The plan's Note Format Definition must match an **actual** existing note in the target dir (per plan-digestion Step 2d). Open one existing target-dir note and confirm the plan's YAML field order + H2 conventions are copied from it. If the plan's format looks invented (e.g. `## Definition` / `## Related concepts` when the target dir uses `## Overview` / `## Related Notes`) → **FAIL**: the format was written from intuition, return to plan-digestion Step 2d.

**Result**: PASS / FAIL (if FAIL: list misaligned fields OR "format invented, not derived")

---

## Step 7: Checkpoint 6 — Density & BB Atomicity (Promote Splits) <!-- :: section_id = step_7_cp6 :: -->

**Check**: Are there borderline notes that should be proactively split?

### 7a. Scan all planned notes for borderline cases

A note is **borderline** if ANY of:
- Estimated >300 lines (under 400 but close)
- Estimated >5 code blocks (under 6 but close)
- Covers >5 H2 sections
- Source sections have mixed BB content (even if <500w each)

### 7b. For each borderline note, decide: SPLIT or KEEP

**Default is SPLIT** unless there's documented justification to keep:
- Sections are topically cohesive (single theme)
- Total estimated words <700
- No BB mixing whatsoever

### 7c. If splits needed, add to Split Decisions table

Update the plan's Split Decisions table with new entries.

**Result**: PASS (no borderline or all addressed) / FAIL (borderline cases unaddressed — list them with recommendation)

---

## Step 8: Checkpoint 7 — Source Word Counts Are Measured (Not Under-Estimated) <!-- :: section_id = step_8_cp7 :: -->

**Check**: Are the word counts in the plan's Source table based on actual page reads, or are they likely guessed from training knowledge?

### 8a. Spot-check 2-3 source pages

Pick 2-3 documents from the plan's Source table (preferably the densest — those mapped to the most notes). Re-segment them with `scripts/plan_coverage.py $CORPUS --segment <doc_id>` and confirm the block/word counts match the plan. The corpus is local; there is nothing to WebFetch.

### 8b. Compare measured vs plan estimates

| Page | Plan Estimate | Measured (actual) | Ratio | Verdict |
|------|--------------|-------------------|-------|---------|
| page_1 | ? | ? | measured/estimate | OK if 0.7-1.3 |
| page_2 | ? | ? | ? | ? |
| page_3 | ? | ? | ? | ? |

### 8c. Apply the 50% rule

- If ANY page's actual word count is **>1.5× the plan estimate** → **FAIL** — the plan under-estimated density and notes likely need further splitting.
- If ALL spot-checked pages are within 0.7-1.3× the estimate → PASS.

### 8d. If FAIL: identify which notes need re-splitting

For each under-estimated page:
1. Check which planned note(s) it maps to
2. Apply the source-page-level threshold from plan-digestion skill Step 3c:
   - 1800-3600w actual → MUST split into 2 notes
   - >3600w actual → MUST split into 3+ notes
3. Report: "Page X is {actual}w (plan said {estimate}w). Note Y must split into Y1 + Y2."

**Result**: PASS (spot-checked pages within ±30% of estimates) / FAIL (under-estimation detected — list pages and required splits)

> **Why this checkpoint exists**: Plans written by background agents or from training knowledge routinely under-estimate AWS documentation page sizes by 50-70%. This checkpoint catches the problem before execution begins, when fixes are cheap (update a plan table) rather than expensive (rewrite over-dense notes after the fact).

---

## Step 8.5: Checkpoint 8 — Undigested Terms Plan + Term-Note Authoring Requirements <!-- :: section_id = step_8_5_cp8 :: -->

**Check**: Does the augmented plan include the term-coverage sections that augment-digestion Step 10.5 was supposed to add?

> CP8 added 2026-06-12. Mirrors CP2's pattern: augment-digestion is supposed to add these sections; review verifies they actually landed. A plan that's been re-augmented after 2026-06-12 but lacks these sections → augmentation skipped a step.

### 8.5a Verify `## Undigested Terms Plan` section is present

```bash
grep -c '^## Undigested Terms Plan' "$PLAN_FILE"
```

- 0 occurrences → **FAIL** — augmentation must run Step 10.5; the plan-digestion Step 4e Undigested Terms Plan was not carried forward
- ≥1 occurrence → continue

### 8.5b Verify every row has a defined Capture Phase + best-fit glossary

Scan the table rows. Any row with `Capture Phase: TBD` or empty best-fit glossary → **FAIL**. List the offending rows.

### 8.5c Verify `## Term-Note Authoring Requirements` section is present

```bash
grep -c '^## Term-Note Authoring Requirements' "$PLAN_FILE"
```

The section MUST be present AND contain:
- YAML frontmatter spec (required fields including `building_block: concept` + `related_wiki`)
- Required H1 + H2 sections in order (Definition / Context / Key Characteristics / Performance optional / Related Terms 8-15 minimum / References external-only)
- Research scoped to corpus + vault (external enrichment only in a quarantined `## Background (external)` section, never scored; no internal Amazon systems)
- Cross-domain diversity matrix (6 connection types)
- Fleeting content guard
- Glossary entry format (4-5 sentence Description, no metrics)
- Acceptance failure conditions
- **Full-term-note mandate**: every undigested term ends as a FULL term note (≥8 related terms + ≥2 EXTERNAL web/wiki references — NOT digest-doc-only content); any Pattern-A pre-digest stub is a temporary link target that MUST be enriched before completion and carries `research_pending: true` until enriched. If the plan ships thin stubs as final OR lacks the ≥8-related-terms + external-references requirement → **FAIL**.

Spot-check the section content. If anything is missing → **FAIL**.

### 8.5d Verify plan invokes `/slipbox-capture-term-note` per term (not inline)

For each undigested term, the plan's execution phases must reference `/slipbox-capture-term-note <term>` — NOT inline-author within a digest note. Scan execution phase descriptions for the explicit invocation.

If any term's capture is inline (no `/slipbox-capture-term-note` reference) → **FAIL**.

### 8.5e Verify the multi-source research mandate is non-negotiable in plan language

The Term-Note Authoring Requirements section must use must-language (`MUST`, `required`, `mandate`) — NOT soft-language (`should`, `consider`, `optional`). Soft-language wording invites authors to skip steps and fall back to single-source (digest-doc-only) captures. If wording is soft → **FAIL**, return plan to augmentation with the specific language to fix.

### 8.5f Verify Term-Slug Specificity + Collision Audit was performed (Step 10.5f of augment-digestion)

> Added 2026-06-12. Mirrors the lesson from the Sub-Plan 0 (causal-handbook) review: augmentation's exact-slug existence check is necessary but insufficient. The plan must also document an explicit specificity audit (rename too-general slugs) and collision audit (synonym search against existing substantive vault notes, then REMOVE duplicates and redirect to existing).

For the Undigested Terms Plan section, verify EITHER:
- A `### Renamed (general → specific)` sub-table is present listing every renamed slug + the reason; OR
- A `### Removed (substantive vault notes already cover the concept — link instead of create)` sub-table is present; OR
- A Naming Notes column on the term table explicitly states `—` (audit performed, nothing flagged)

If NONE of those exist → augmentation did not perform Step 10.5f. **FAIL** — return to augmentation.

If sub-tables exist, spot-check 3 random rows:
- **Specificity spot-check**: for a renamed row, verify the reason names a concrete collision/ambiguity (not just "made clearer"). Empty or hand-wavy reasons → FAIL.
- **Collision spot-check**: for a removed row, verify the named existing note actually exists in the vault and has ≥30 lines + `status: active`:
  ```bash
  grep -E "term_[a-z_]+\.md" "$PLAN_FILE" | head -5  # pull a removed-row's existing-note ref
  ls -la "$VAULT/<existing_note>.md"
  wc -l "$VAULT/<existing_note>.md"
  ```
  Missing existing note OR <30 lines OR stub status → audit was sloppy → **FAIL**.

For renamed slugs: verify the new slug does NOT collide with any OTHER existing vault note (re-running existence check post-rename):
```bash
for new_slug in $(grep -oE 'renamed_to[: ]*`term_[a-z_]+`' "$PLAN_FILE" | grep -oE 'term_[a-z_]+'); do
  f="$VAULT/${new_slug}.md"
  [ -f "$f" ] && echo "POST-RENAME COLLISION: $new_slug"
done
```

Any POST-RENAME COLLISION → augmentation introduced a new duplicate while fixing an old one → **FAIL**.

**Result**: PASS (all sub-checks 8.5a-f pass) / FAIL (return to augmentation Step 10.5 with the specific gap)

---

## Step 8.6: Checkpoint 9 — Discoverability (Inbound Links) <!-- :: section_id = step_8_6_cp9 :: -->

> Added 2026-06-13. Mirrors the graph-island failure: a new note cluster can pass CP1-CP8 (well-formed,
> good outbound links, no ghosts) yet have **zero inbound links from outside the digest folder** — making
> it undiscoverable by graph traversal/PPR from existing knowledge.

**Check**: Does the plan's Inlink Mapping (augment Step 9) cover **every** new note with ≥1 inbound link
from an existing vault note OUTSIDE the digest folder, AND mark inlink-addition as an EXECUTED phase (not merely "recommended")?

- Inlink table missing, or covers only some notes, or inlinks are "recommended" not a gated execution
  phase → **FAIL**.
- Every new note has ≥1 planned outside-folder inbound link + G8-Discoverability is in the phase gate
  tables → **PASS**.

**Result**: PASS / FAIL (if FAIL: list notes with no planned inbound link)

---

## Step 9: Report Result <!-- :: section_id = step_9_report :: -->

```
PLAN REVIEW — FINAL SIGN-OFF

Plan: plan_digest_<topic>.md
Date: YYYY-MM-DD

□ CP1: Related Notes step ............................... [PASS/FAIL]
□ CP2: 8-GATE tables per batch (G1-G6,G8) ............... [PASS/FAIL]
□ CP3: Entry point update specified ..................... [PASS/FAIL]
□ CP4: Plan size manageable (≤30 or split) .............. [PASS/FAIL]
□ CP5: Note format aligned + DERIVED from existing ...... [PASS/FAIL]
□ CP6: Borderline density → split promoted .............. [PASS/FAIL]
□ CP7: Source word counts measured (not guessed) ........ [PASS/FAIL]
□ CP8: Undigested Terms Plan + Authoring Requirements ... [PASS/FAIL]
□ CP8f: Term-Slug + all-notes dedup/collision audit ..... [PASS/FAIL]
□ CP9: Discoverability — inbound links executed (G8) .... [PASS/FAIL]

RESULT: ___/9 pass → [READY FOR EXECUTION / NOT READY — return to augmentation]
```

If ALL 8 pass: Update plan status from `pending` to `ready`.

If any FAIL: Report which checkpoints failed and what needs to be fixed. Do NOT change plan status.

---

## Important Constraints <!-- :: section_id = important_constraints :: -->

1. **This is a READ-ONLY review** — do NOT modify the plan during review. Report findings only.
2. **Default for borderline is SPLIT** — the reviewer's job is to promote caution, not allow shortcuts.
3. **All 9 must pass** — partial passes don't count. A plan with 8/9 is NOT READY.
4. **Review is the final gate before execution** — once READY, execution can begin immediately.
5. **Record the review** — append a `## Review Sign-Off` section to the plan with date, result, and any notes.
6. **CP7 requires actual source reads** — the reviewer MUST re-segment 2-3 corpus documents (`scripts/plan_coverage.py $CORPUS --segment <doc_id>`) and confirm block/word counts against the plan. This cannot be done from memory. Flag any document whose counts do not match.

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
building_block: <one of the eight>   # FM-002 / FM-003 — closed enum
source_docs: [<corpus_doc_id>, ...]  # FM-004 — the corpus evidence for this note
---
```

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

**Topical coherence decides where a note ends.** One note covers one subject, so
that retrieving it returns the whole of one thing rather than part of several.
Within that subject, the note carries exactly one building block.

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

## Planning Accounting (this repo)

A plan asserts three things about every note. Here they are **checked by
script**, because two of them cannot be seen by reading the plan.

```bash
# per-note source ceiling + per-document coverage
python3 scripts/plan_coverage.py <slug> --check <assignments>.json --own-docs doc_a,doc_b

# no source block assigned to two notes, across ALL sub-plans at once
python3 scripts/plan_coverage.py <slug> --crossplan experiments/plans/<slug>/

# per-note term links, derived from each note's own source blocks
python3 scripts/build_term_links.py <slug> --plans experiments/plans/<slug> --floor 3

# audit an existing mapping: every link must be backed by source
python3 scripts/build_term_links.py <slug> --plans experiments/plans/<slug> \
    --verify experiments/plans/<slug>/term_links.json
```

**A link the source does not support is a fabricated edge, and it is not inert.**
`bfs` and `ppr` traverse every edge given, so it moves probability mass onto a
note the evidence never connected — degrading the arm the experiment exists to
measure, and showing up later only as a retrieval number that looks
disappointing for no visible reason. `--verify` blocks it at plan time instead.

**Assignments are block-level.** `--segment` splits a source into paragraph
blocks; the plan records which blocks each note carries, as JSON beside the
plan. That file is what makes the numbers reproducible instead of narrated.

**Coverage is measured over documents the plan OWNS.** A note extended by
another sub-plan brings that sub-plan's documents along; counting them here
would penalise a plan for correctly reusing a note instead of duplicating one.

**Duplicate source assignment is invisible to coverage.** A block counted twice
still looks covered, so summing can never find it — only the cross-plan check
can. It matters because two notes then carry the same claim, retrieval splits
between them, and the dedup rule that lets one note satisfy several pieces of
gold evidence is defeated.

**Dropped source must be listed, not just subtracted.** Publisher chrome —
titles already in the H1, section labels, newsletter promotion, contentless
reaction, bylines — carries no claim and should go. But the same subtraction
hides genuine omission, so enumerate what was dropped and inspect it. On this
corpus that review recovered a block that read as a routine correction notice
and in fact stated the opposite of its article's headline: a scope condition on
the central claim, which is precisely the class an unconditioned summariser
deletes.

## Error Handling <!-- :: section_id = error_handling :: -->

| Error | Cause | Recovery |
|-------|-------|----------|
| Plan file not found | Wrong path or not yet created | Run `/slipbox-plan-digestion` + `/slipbox-augment-digestion-plan` first |
| Plan has no Note Format Definition | Augmentation incomplete | Run `/slipbox-augment-digestion-plan` first |
| Target directory doesn't exist yet | New subfolder planned | Verify plan specifies directory creation; PASS CP5 if template is consistent with parent directory patterns |
| Plan already has status: ready/completed | Already reviewed | Report "Plan already reviewed" — skip |

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog
- [FZ 28d: Final Review & Sign-Off](../analysis_thoughts/thought_digestion_plan_final_review.md)
