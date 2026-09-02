---
tags:
  - resource
  - skill
  - procedure
  - capture
  - planning
  - documentation
  - quality
keywords:
  - augment digestion plan
  - slipbox-augment-digestion-plan
  - in-vault skill canonical
  - density re-assessment
  - section coverage map
  - split decisions
  - pacing rules
  - 4-GATE verification
topics:
  - Skill Procedures
  - Vault Tools
language: markdown
date of note: 2026-05-23
status: active
building_block: procedure
---

# Procedure: slipbox-augment-digestion-plan (Canonical Body)

> **Ported skill.** Adapted from an upstream vault canonical for use in this
> repository. All paths are local: notes live under `vaults/$CORPUS`, the database
> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill
> never reads or writes any vault outside this repo.

This is the **single canonical body** for the `slipbox-augment-digestion-plan` skill (FZ 12a).

## Skill description <!-- :: section_id = skill_description :: -->

After a draft digestion plan exists in `experiments/plans/`, this skill augments it with the **15 mandatory sections** (originally 11 per FZ 28c + Undigested Terms Plan + Term-Note Authoring Requirements + Entry Point Decision added 2026-06-12). Re-reads the source to verify density assumptions, adds section coverage maps, split decisions, validation scripts, pacing rules, inlink mapping, **validates the Undigested Terms Plan + per-term multi-source research requirements + entry-point CREATE-vs-UPDATE decision against the size threshold + term-slug specificity & collision audit (renames too-general slugs, removes duplicates of existing substantive vault notes)**, and runs a **28-item completeness checklist**. Critically: forces the agent to re-read the source and confirm no over-compression / omission / term-coverage gap / entry-point sizing mismatch / duplicate term capture before marking the plan ready. Use AFTER `/slipbox-plan-digestion` creates the initial draft.

## Setup <!-- :: section_id = setup :: -->

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```

## Resources <!-- :: section_id = resources :: -->

- **Plan to augment**: `$PLANS_PATH/plan_digest_<topic>.md` (must already exist)
- **FZ 28c reference**: `$VAULT/resources/analysis_thoughts/thought_digestion_plan_augmentation.md`
- **Best-plan examples**: `$PLANS_PATH/plan_digest_builder_mcp_user_guide.md`, `$PLANS_PATH/plan_digest_meshclaw_wiki.md`
- **Vault DB**: `$DB` for cross-reference search

---

## Step 0: Detect Plan Structure (Single vs Master+Sub-Plans) <!-- :: section_id = step_0_detect_structure :: -->

Before augmenting, determine which pattern the plan uses:

| Pattern | Detection | How to Augment |
|---------|-----------|----------------|
| **Single plan** | File has a Planned Notes table with specific filenames | Augment this file directly (Steps 1-12) |
| **Master plan** | File has a Sub-Plans Index Table with links to sub-plan files | Do NOT augment the master — it's an index hub. Instead, augment EACH sub-plan file independently (Steps 1-12 applied to each) |

**If master plan detected**: Read the Sub-Plans Index Table. For each sub-plan file listed, run Steps 1-12 on that sub-plan. The master plan itself only needs: (a) status updated as sub-plans are augmented, (b) shared sections verified (routing, format, cross-refs).

**Master-level augmentation checklist** (added 2026-06-13 — the 28-item checklist below is shaped for single/sub-plans; a master plan is verified against the shorter list of master-required sections from `/slipbox-plan-digestion` Step 6). Confirm the master has, and DB-verify where applicable:
- [ ] Objective, Routing (shared), **Format Definition (shared) — derived from existing target-dir notes, not invented** (Step 2d of plan-digestion)
- [ ] Sub-Plans Index Table + exhaustive page→sub-plan assignment (every source page assigned once)
- [ ] Execution Order, Validation Gates (shared, **all 8 incl. G8-Discoverability**), Pacing Rules (shared)
- [ ] **Cross-References (shared)** — existing vault notes to link, all DB-verified present
- [ ] **Entry Points to Update** — named parent hub + CREATE/UPDATE decision matching the size threshold
- [ ] **Undigested-Terms corpus-ownership inventory** — every term has an owner sub-plan (Pattern B) or existing-note link; 0 orphans
- [ ] Summary Statistics, Follow-up, Pipeline Status tracker
Report "Master passes N/8 shared-section checks. Missing: [list]."

---

## Step 1: Read the Existing Draft Plan <!-- :: section_id = step_1_read_draft :: -->

Read the plan file at `$PLANS_PATH/plan_digest_<topic>.md` (or the specific sub-plan file if augmenting within a master+sub-plan structure).

Identify which of the 11 mandatory sections are PRESENT and which are MISSING:

| # | Section | Check |
|---|---------|-------|
| 1 | Routing Decision validated | Applies `/slipbox-route-content` 3-criterion rule; context affinity considered |
| 2 | Section Coverage Map | ASCII tree mapping every H2/H3 → note |
| 3 | Split Decisions table | WHY each split was made |
| 4 | Note Format Definition | YAML template + body format + forbidden fields |
| 5 | Pacing Rules | One-phase-at-a-time + re-read + stop-and-split |
| 6 | Density Re-Assessment | Post-plan recheck paragraph |
| 7 | Validation Scripts (bash) | Format + density + cross-link scripts |
| 8 | Per-phase GATE tables | G1-G4 per execution phase |
| 9 | Prerequisite Deduplication Check | No repeated boilerplate across notes |
| 10 | Inlink step (existing → new) | Table mapping existing notes → new notes |
| 11 | Entry Point specifics | WHICH entry point, WHAT section, HOW MANY rows |
| 12 | Follow-up Recommendations | DB update, add-inlinks, sync, backlinks |
| 13 | **Undigested Terms Plan** (added 2026-06-12) | Table with term slug, best-fit glossary, capture phase, stub/full, source page |
| 14 | **Term-Note Authoring Requirements** (added 2026-06-12) | Format compliance + multi-source research mandates (internal wiki + SAGE + corpus document + external web) |
| 15 | **Entry Point Decision** (added 2026-06-12) | UPDATE vs CREATE per size threshold from `/slipbox-plan-digestion` Step 4c; if CREATE, names the new `entry_<slug>.md` + parent-hub back-link |

**If the plan's Routing Decision is missing or weak**: Apply the 3-criterion rule from `/slipbox-route-content` — check (a) source novelty, (b) operational tasks, (c) maintenance cadence. Verify context affinity (same source → same folder). Verify content TYPE > SOURCE. Update the plan's Routing Decision accordingly.

Report: "Plan has N/11 sections. Missing: [list]."

---

## Step 2: Re-Read the Source — Density Verification <!-- :: section_id = step_2_reread_source :: -->

> **CRITICAL**: This is the most important step. You MUST re-read the original source document(s) — do NOT work from memory or from the plan's summary. Failure to actually read pages is the #1 cause of under-estimated density and insufficient splits.

### 2a. Re-read every source page AND measure

Use the same tool used to read the source initially (local file read, Read, WebFetch). Read EVERY page listed in the plan's Source section.

**For each page, record ACTUAL measured values**:
- Word count (from the tool output, not from memory)
- Code block count
- H2/H3 heading count

**Compare measured values against the plan's estimates**. If any page's measured words are >50% higher than the plan's estimate, the plan has a density estimation failure and notes must be re-split.

> **Common failure pattern**: Plans written without actual page reads (e.g., from training knowledge or page titles only) routinely under-estimate by 50-70%. AWS documentation pages average 2000-5000 words — not 800-1500. If the plan's Source table shows most pages at <1500w, treat this as a red flag requiring verification.

**Sanity check**: Sum all measured page word counts. If total < plan's "Total words" estimate × 0.7, the plan was written correctly. If total > estimate × 1.5, the plan under-estimated and needs re-splitting.

### 2b. For each planned note, answer these questions:

| Question | If YES → action |
|----------|-----------------|
| Does this note combine >1800 words of source content? | SPLIT into 2 notes at H2/H3 boundary |
| Does this note have >6 code blocks from source? | SPLIT "overview" from "examples" |
| Does this note mix step-by-step commands WITH conceptual explanation (>500w each)? | SPLIT into concept note + procedure note |
| Is any source section OMITTED from the plan? | ADD the section to a planned note |
| Is any source section COMPRESSED (summarized instead of captured)? | EXPAND — create additional note or expand existing |
| Are there source warnings/callouts that would be lost? | MARK as must-preserve in plan |

### 2c. Write findings

Add a `## Density Re-Assessment After Plan Complete` section to the plan with:
- Per-page word counts (main page, leaf pages)
- Per-note estimated word count and line count
- Any notes that are borderline (>300 lines estimated)
- Decision: "No further splits needed" OR "Split note X into Xa + Xb because..."

### 2d. Surface NEWLY-Identified Undigested Terms (Re-Read Catches Misses)

The re-read often reveals terms the original plan-digestion Step 4e missed — concepts that appear in a chapter the planner skimmed, sub-sections the planner didn't enumerate, or method names introduced in a code block or figure caption that text-search regex skipped.

For each source page re-read in Step 2a, scan again for:
- Acronyms in figure captions / code comments / equation labels
- Method names introduced AFTER the first H2 (often glossed over in the initial pass)
- Terms in supplementary boxes / sidebars / footnotes

For every newly-found candidate, run the Step 4e.2 existence check (vault DB query). If still undigested, append the term to the plan's `## Undigested Terms Plan` table with a `Source Page` annotation marking it as "added at augmentation".

If ≥3 new terms surface, this is a **plan-digestion quality flag**: the original Step 4e may have been performed without the full source read. Note this in the Augmentation Report so the next run improves the upstream plan-digestion step.

---

## Step 3: Add Section Coverage Map <!-- :: section_id = step_3_coverage_map :: -->

If the plan lacks a Section Coverage Map, add one using this format:

```
Source Page (~Nw)
├── Section A (Mw, concept) ──── → Note 1 (filename)
├── Section B (Mw, procedure)
│   ├── Sub-section B1 (Mw) ──── → Note 2 (filename)
│   └── Sub-section B2 (Mw) ──── → Note 2
├── Section C (Mw, model) ────── → Note 3 (filename)
└── Section D (Mw) ──────────── → SKIP (reason)
```

Every source H2/H3 MUST appear. No orphans allowed.

---

## Step 4: Add Split Decisions Table <!-- :: section_id = step_4_split_decisions :: -->

If any notes were split beyond initial grouping (from Step 2 or from the original plan), document:

```markdown
## Split Decisions

| Original | Split Into | Rationale |
|----------|-----------|-----------|
| Note X (1250w) | Note Xa + Note Xb | BB mixing: concept + procedure |
| Note Y (3000w) | Note Ya + Note Yb | >1800w threshold exceeded |
```

---

## Step 5: Add Validation Scripts <!-- :: section_id = step_5_validation_scripts :: -->

Add bash scripts for automated checking:

**Script 1: Format + Density**
```bash
TARGET_DIR="$VAULT/<target_directory>"
PREFIX="<file_prefix>"

for f in "$TARGET_DIR"/${PREFIX}*.md; do
  python3 scripts/validate_notes.py "$VAULT"
  lines=$(wc -l < "$f")
  words=$(sed -n '/^---$/,/^---$/!p' "$f" | tail -n +2 | wc -w)
  code_blocks=$(grep -c '^\`\`\`' "$f")
  code_blocks=$((code_blocks / 2))
  if [ "$lines" -gt 400 ] || [ "$words" -gt 1800 ] || [ "$code_blocks" -gt 6 ]; then
    echo "DENSITY WARNING: $(basename $f) → SPLIT"
  fi
done
```

**Script 2: Cross-Link Validation**
```bash
for f in "$TARGET_DIR"/${PREFIX}*.md; do
  grep -oE '\]\([^)]+\.md[^)]*\)' "$f" | sed 's/.*(\([^#)]*\).*/\1/' | while read link; do
    resolved=$(cd "$(dirname "$f")" && realpath -q "$link" 2>/dev/null)
    [ -f "$resolved" ] || echo "BROKEN in $(basename $f): $link"
  done
done
```

**Script 3: Prerequisite Duplication** (if applicable)
```bash
for f in "$TARGET_DIR"/${PREFIX}*.md; do
  count=$(grep -c "<repeated_boilerplate_pattern>" "$f" 2>/dev/null || echo 0)
  [ "$count" -gt 0 ] && echo "BLOAT: $(basename $f) has repeated block"
done
```

**Script 4: Ghost Reference Detection (G5 Implementation)**

This script implements Gate G5. Every link in the new notes must resolve to a real vault note. Ghosts → redirect to verified alternatives per Step 4e.

```bash
# Verify every internal link target exists in the vault DB
for f in "$TARGET_DIR"/${PREFIX}*.md; do
  # Extract all markdown link targets ending in .md (not http(s) URLs)
  grep -oE '\]\(([^)]+\.md)[^)]*\)' "$f" | sed -E 's/.*\(([^)]+\.md).*/\1/' | while read raw_link; do
    # Strip anchor fragments and url params
    clean=$(echo "$raw_link" | sed -E 's/#.*$//; s/\?.*$//')
    # Resolve relative path to vault-root note_id form
    resolved=$(cd "$(dirname "$f")" && realpath -q -m "$clean" 2>/dev/null)
    if [ -z "$resolved" ]; then continue; fi
    # Convert absolute path to vault-relative note_id
    note_id=$(echo "$resolved" | sed "s|$VAULT/||")
    # Query vault DB for existence
    found=$(sqlite3 "$DB" "SELECT 1 FROM notes WHERE note_id=?" "$note_id")
    if [ -z "$found" ]; then
      echo "GHOST in $(basename $f): $raw_link  →  note_id=$note_id  NOT IN VAULT"
    fi
  done
done
```

Any GHOST output is a Gate G5 failure. The plan author must (a) redirect to a verified alternative (recorded in Plan Amendments per `/slipbox-execute-digestion-plan` Step 2), OR (b) create the missing target (term stub / placeholder note) BEFORE re-running. Do NOT execute the batch with ghosts present.

---

## Step 6: Add Pacing Rules <!-- :: section_id = step_6_pacing_rules :: -->

Add this section if missing:

```markdown
## Pacing Rules

- Do ONE phase at a time — validate all GATEs before proceeding
- Re-read source wiki page BEFORE writing each note — do NOT work from memory
- Each note ≤ 400 lines — if exceeding, split before writing
- **No rush** — quality over speed; re-read source if uncertain
- Code blocks MUST be verbatim — do NOT edit, reformat, or "improve"
- After each phase: verify ALL GATEs, then commit + push
- **BB atomicity rule**: If a note mixes procedure + concept/model, SPLIT
- **Density rule**: If during writing a note exceeds 350 lines, STOP and split
```

---

## Step 7: Add Per-Phase GATE Tables <!-- :: section_id = step_7_gate_tables :: -->

For each execution phase, add a validation gate table covering **all 7 gates** (G1-G6 as defined in `/slipbox-plan-digestion` Step 5). G5 and G6 are SKILL-DRIVEN and were added 2026-06-12 to close ghost-reference / broken-link gaps. G1 (format), G5 (ghost), and G6 (broken links) can be executed together at batch close via `/slipbox-validate-note-gates`, which runs all three around the incremental DB update and returns a single PASS/FAIL verdict.

```markdown
### Phase N Validation Gate — ALL must pass:

| Gate | Check | Pass Criteria | Tool |
|------|-------|---------------|------|
| G1-Format | YAML fields, line count, single BB, H1 present, **prose wrapping (PROSE-001 — no mid-paragraph hard-wrap)** | 0 errors | **/slipbox-check-note-format --path <note>** (skill) |
| G2-Grounding | Content faithful, code verbatim, no hallucination, source warnings preserved | Manual diff verified | Manual diff against source |
| G3-Density | Word count ≤ 1800, code blocks ≤ 6, lines ≤ 400 | All thresholds met | Validation script (`wc -w`, `grep -c '^\`\`\`'`, `wc -l`) |
| G3-Coverage | All source H2/H3 sections from coverage map present | 100% coverage | Checklist |
| G4-CrossRef | Internal links resolve, source URL present, entry-point updated | All present | Bash link-check script |
| **G5-Ghost** | Every reference (Related Notes, Inlinks) exists in vault — no ghosts | All references DB-verified | **`/slipbox-fix-ghost-references`** (skill) — `--detect` surfaces ghosts + ranked candidates; resolve each by redirect (to a verified same-sense note, recorded in Plan Amendments), drop, or defer→capture |
| **G6-Broken** | After batch lands, zero broken links touching new notes | 0 broken links from batch files | **/slipbox-check-broken-links** + **/slipbox-fix-broken-links** (skills) |
```

**Verify the plan's gate tables include G5 and G6**. A plan with only G1-G4 in its phase gate tables is incomplete — return to the plan author and add the missing gates BEFORE marking augmentation done. See Entry: COEs for the bulk-script ghost-link incidents that motivated adding G5/G6.

---

## Step 8: Build Per-Note Related Notes Mapping <!-- :: section_id = step_8_related_notes :: -->

For EACH planned note, search the vault to find related notes that should appear in its `## Related Notes` section. This mapping goes directly into the plan so the executing agent can copy it verbatim.

### 8a. Search for each planned note's related notes

For each planned note, run `/slipbox-search-notes <key_concepts_from_that_note>`. The search skill applies BM25, graph traversal, and PPR across ALL note types.

### 8b. Build the per-note reference table

Add a section to the plan:

```markdown
## Per-Note Related Notes Mapping

| Planned Note | Related Notes to Include in ## Related Notes |
|--------------|---------------------------------------------|
| wiki_topic_overview.md | [term_topic](path), [tool_topic](path), [repo_topic](path), [entry_topic](path) |
| wiki_topic_install.md | [howto_install_topic](path), [term_midway](path), [term_toolbox](path) |
| ... | ... |
```

### 8c. Minimum per note

Each planned note MUST have **≥8 `term_dictionary/` term notes**, selected by **content relevancy** to that note (the concepts the note actually uses — relevancy-ranked via `/slipbox-search-notes` BM25/dense/graph,
**NOT padded with unrelated terms**), PLUS other related vault notes (tools/repos/areas/howtos/siblings) and
**≥1 entry point back-link**. Augmentation must DB-verify every listed term note exists (G5). If fewer than
8 truly-relevant term notes exist for a niche note, broaden the search keywords / check adjacent concepts; only fall below 8 with an explicit per-note justification recorded in the mapping (do not pad with irrelevant terms). (raised ≥3 → ≥6 2026-06-13, ≥6 → ≥8 2026-06-21 — relevancy-selected term coverage drives graph retrieval quality; the causal-handbook sub-plans used ≥8.)

**Format in the note (reference section).** The ≥8 term notes are rendered in the digest note's
`## Related Notes` section as **indexed markdown links, each carrying a term description AND its relevancy to the digested note**:

```
- [Term Name](relative_path.md) — <one-line what-the-term-is>; relevance: <why it matters to THIS note>
```

The per-note mapping table (8b) records, for each planned note, the chosen term slugs **with their relevancy note**, so the executor copies the link + description + relevancy verbatim. A bare link with no relevancy statement is incomplete.

### 8d. Group by category in the mapping

For clarity, group related notes by type in the mapping:
- **Terms**: term notes referenced by the content
- **Tools/How-Tos**: tool or howto notes for the same system
- **Code Repos/Snippets**: implementation-level notes
- **Entry Points**: navigation hubs that should link to this note
- **Sibling Notes**: other notes in the same digestion (prev/next)

This mapping is used TWICE: once when writing the note (to populate `## Related Notes`), and once in Step 9 (to determine inlinks in the reverse direction).

---

## Step 9: Add Inlink Mapping (Existing → New) <!-- :: section_id = step_9_inlink_mapping :: -->

The REVERSE of Step 8: which EXISTING vault notes should get a new link pointing TO the new notes? This ensures new notes are discoverable via graph traversal from existing knowledge.

### 9a. From Step 8's mapping, identify reverse links

For each related note found in Step 8, ask: "Should this existing note link TO the new note?" The answer is YES if:
- The existing note documents the same system/tool/concept from a different angle
- The existing note is a code repo/snippet that implements what the new note documents
- The existing note is a term that the new note explains in more detail

### 9b. Build the inlink table

```markdown
## Inlinks (existing notes → new notes)

| Existing Note | Inlink to Add | Rationale |
|---------------|---------------|-----------|
| repo_X.md | [Wiki: Topic](wiki_topic.md) | Repo implements what wiki describes |
| snippet_Y.md | [Wiki: Feature](wiki_feature.md) | Snippet is code-level of wiki feature |
| term_Z.md | [Wiki: Z Deep Dive](wiki_z_detail.md) | Term links to detailed documentation |
| howto_W.md | [Wiki: W Reference](wiki_w.md) | How-to references wiki for context |
```

### 9c. This step becomes an execution phase

Add a post-creation phase to the execution plan: "Phase Xb: Add inlinks to N existing notes per this table." This phase runs AFTER all notes are created and pass GATEs.

### 9d. Inlinks are EXECUTED + VERIFIED, not just planned (G8-Discoverability; added 2026-06-13)

The inlink table is a *plan*; the gate is *execution*. The plan MUST require, and execution MUST verify, that **every new note ends up with ≥1 inbound link from an existing vault note OUTSIDE the digest folder** (DB in-degree ≥1). A cohesive new cluster routinely passes G1-G6 while being a **graph island** (0 inbound links → buried in PPR, unreachable by graph traversal from existing knowledge). Add **G8-Discoverability** to every phase gate table and a DB in-degree check to the execution/verification step. "Inlinks planned but not executed" is a G8 failure.

---

## Step 10: Add Follow-up Recommendations <!-- :: section_id = step_10_followup :: -->

```markdown
## Follow-up Recommendations

- After completing this plan, run `/slipbox-run-incremental-update` to index new notes
- Run `/slipbox-add-inlinks` to propagate backlinks from new notes
- Add backlinks to existing tool/term notes (per inlink table)
- Sync to secondary workspace and S3
- Consider creating a dedicated entry point if total note count exceeds threshold
```

---

## Step 10.5: Validate Undigested Terms Plan + Term-Note Authoring Requirements <!-- :: section_id = step_10_5_undigested_terms :: -->

> **Why this step exists**: the plan-digestion skill's Step 4e produces an Undigested Terms Plan. The augment step MUST verify that table is present, complete, and that each term-capture obligation specifies (a) multi-source research, not just the source doc, and (b) term-note format compliance per the capture-term-note skill canonical. Without this step, the plan ships with term-stub gaps that surface as ghost references at Gate G5.

### 10.5a Verify the Undigested Terms Plan section exists

```bash
grep -c '^## Undigested Terms Plan' "$PLAN_FILE"
```

- 0 occurrences → FAIL — return the plan to `/slipbox-plan-digestion` for Step 4e completion
- ≥1 occurrence → continue

### 10.5b Verify every row has a defined Capture Phase

Scan the Undigested Terms table; any row with `Capture Phase: TBD` (or empty) is a planning incompleteness. Either fill it now OR mark the term as "REJECTED — see notes" with explicit rationale.

### 10.5c Verify the best-fit glossary for every term

For each row, confirm:
```bash
ls "$VAULT/0_entry_points/${BEST_FIT_GLOSSARY}"   # must exist
```

If a row's best-fit glossary doesn't exist in `0_entry_points/`, EITHER (a) re-pick a glossary that does exist OR (b) plan to CREATE the new glossary as an explicit phase (this is a separate phase from the term capture; do not bundle).

### 10.5d Add the Term-Note Authoring Requirements section to the plan

For every undigested term, the plan must include explicit authoring requirements **lifted from `skill_slipbox_capture_term_note.md` canonical**. Augmentation does NOT redefine these — it ensures the plan invokes them. Append this section to the plan verbatim:

```markdown
## Term-Note Authoring Requirements (Per Undigested Term — Inherited from `/slipbox-capture-term-note` canonical)

Every term in the Undigested Terms Plan must be authored via **`/slipbox-capture-term-note <term>`** (interactive or via ENRICHER_INPUTS), NOT inline-authored within a digest note. The capture skill enforces the requirements below; augmentation verifies the plan respects them.

### YAML Frontmatter (Required Fields)

```yaml
--- tags:
  - resource
  - terminology
  - <domain_tag_1>          # e.g., machine_learning, causal_inference, econometrics
  - <domain_tag_2>          # narrower domain tag
keywords:
  - <ACRONYM>               # e.g., DML
  - <Full Name>             # e.g., Double Machine Learning
  - <variant_spellings>
topics:
  - <topic_1>
  - <topic_2>
language: markdown date of note: <YYYY-MM-DD> status: active                # or `stub` if Pattern B Phase-0 stub building_block: concept       # MUST be concept for term notes access_control_group: ["general"] related_wiki: <primary_wiki_url_or_null> ---
```

### Required H1 + H2 Sections (in order)

| Section | Required | Content |
|---|---|---|
| `# <ACRONYM> - <Full Name>` H1 | Yes | Exact `# ACRONYM - Full Name` pattern |
| `## Definition` | Yes | 1-2 paragraphs; what it is, what problem it solves, who uses it (buyer-abuse context where applicable) |
| `## Context` | Yes | Which teams / systems / programs / workflows use or reference this term |
| `## Key Characteristics` | Yes | Bullet list of distinctive properties; technical approach + deployment scale where applicable |
| `## Performance / Metrics` | Optional | Include ONLY if metrics found in research; omit entirely otherwise |
| `## Related Terms` | Yes | **8-15 vault term-note links minimum** (see Cross-Domain Diversity below) — INDEXED markdown link format: `**[Term Name](term_X.md)** — one-line description` |
| `## References` | Yes | EXTERNAL URLs ONLY (wiki, corpus document, papers, Wikipedia, books); NO `term_*.md` links here — those go in Related Terms above |

### Multi-Source Research (Load-Bearing — Avoids Doc-Trapped Scope)

> The source doc that triggered the capture is ONE viewpoint. Relying only on it gives a doc-narrow view that's blind to the term's broader meaning, related concepts, and cross-domain applications. Every capture MUST research across multiple sources.

For every undigested term, the plan MUST require the author to:

1. **`builder-mcp WIKI`** — try direct wiki URLs first (e.g. `https://the corpus`); then `InternalSearch` with `domain: WIKI` for the term + 1-2 strongest context keywords; read top 2-3 matching wiki pages
2. **corpus document** — `https://the corpus`; read top 1-2 promising results for design docs, project summaries, launch announcements
3. **`builder-mcp SAGE_HORDE`** — corporate search with `domain: SAGE_HORDE`, pageSize 3; record top results
4. **`builder-mcp BROADCAST`** — `domain: BROADCAST` for launch announcements; pageSize 3
5. **External sources** (≥2 of): Wikipedia, Pearl/Angrist textbook PDFs, official open-source documentation, top arXiv result on the method, original method paper. Even when the digest doc covers the term richly, an external source provides definition orthogonality
6. **Vault cross-reference**: `/slipbox-search-notes <term>` AND DB query for in-domain + cross-domain related term notes per the capture-term-note canonical Steps 3d + 3e

### Cross-Domain Diversity for Related Terms (8-15 links minimum)

Per capture-term-note canonical Step 3e, the Related Terms section MUST include cross-domain connections — NOT just same-domain siblings:

| Connection Type | Example | What to look for |
|---|---|---|
| **Foundation** | Normal distribution → linear regression, XGBoost | Stats foundations the method uses |
| **Application** | Concentration inequality → UCB bandits, LASSO theory | Applied terms that depend on this theoretical tool |
| **Analogy** | Epidemic SIR → information cascade | Structural parallels in other fields |
| **Contrast** | Pareto vs Normal, LASSO vs Ridge | Terms explicitly contrasted in the literature |
| **Successor/Predecessor** | BoW → Word2Vec → BERT, HMM → CRF → Transformer | Evolutionary chains |
| **Component** | Tokenization → BERT, Softmax → attention | Building blocks used elsewhere |

Target: ≥3 in-domain + ≥3 cross-domain = ≥8-15 total verified links.

### Math Notation Requirement (Constraint 11 of capture-term-note canonical — load-bearing)

The plan MUST require every mathematical formula, equation, symbol, or expression in the captured note body to use **MathJax delimiters**:

| Form | Syntax | Example |
|---|---|---|
| Inline math | `$...$` | `$\bar{X}_1 - \bar{X}_2$`, `$\mathbb{E}[Y(1)]$`, `$\alpha = 0.05$` |
| Display math | `$$...$$` on its own line | `$$t = \frac{\bar{X}_1 - \bar{X}_2}{s_p \sqrt{1/n_1 + 1/n_2}}$$` |

**Forbidden** in note body:
- Plain-text math: `X̄₁ - X̄₂`, `μ_diff`, ASCII fractions `(a)/(b)`
- Unicode-only subscripts/superscripts as standalone notation
- `**bold**` markdown for variable names where MathJax would render correctly
- Mixing notation systems within the same paragraph (e.g., `$\bar{X}_1$` then `X̄_2`)

Mathematical content is preserved **verbatim** from source — never paraphrase math. Only re-notate plain-text source equations or different-flavor LaTeX into MathJax form. Greek letters, vectors, integrals, expectations, distributions, summations, and probabilistic notation ALL go through MathJax.

Rationale: Obsidian + the slipbox UI render MathJax natively; plain-text math fragments degrade search (terms inside `$...$` are indexed via the math tokenizer), break copy-paste fidelity to source, and prevent rendered notes from matching their authoritative form.

### Fleeting Content Guard (Step 4b in capture-term-note canonical)

The plan MUST require capture to strip / genericize:
- Person aliases as POCs (`@jsmith` → "Contact: BAP ML team")
- Bare ETAs (`Q3 2025` → remove OR `launched 2025` if confirmed)
- Bare dollar amounts (`$128M savings` → `$128M savings (as of 2025)`)
- Bare team headcounts (`team of 15` → "small team")
- Reporting relationships (`reports to VP X` → "under BAP Science org")

### Glossary Entry Requirements (Step 5 of capture-term-note canonical)

After writing the term note, the capture skill updates the best-fit `acronym_glossary_*.md`:
- **4-5 sentence Description maximum** (hard limit from `prompt_term_note_create`)
- NO specific numbers, percentages, or dollar amounts
- Bold the single most important distinguishing fact
- Sentence 1: what it is + problem it solves
- Sentence 2: key technical approach / core mechanism
- Sentence 3-4: characteristics, use cases, distinguishing properties
- Sentence 5 (optional): status, team, deployment scope

### Pre-Flight Outcome Routing (from `/slipbox-capture-term-note` Step 2)

Every undigested-term capture obligation must respect the three-way pre-flight outcome:

| Existing vault state | Action | Recorded in plan |
|---|---|---|
| **No matching note** (DB returns nothing) | Proceed to create | `Capture Phase: <phase>`, `Stub or Full: full` |
| **Stub note exists** (`status: stub/placeholder/empty`, <30 lines, only TODO/TBD/single-sentence) | Fill in the stub — same path, overwrite stub content; ask user "Continue? [yes/no]" first | `Capture Phase: <phase>`, `Stub or Full: fill-stub` |
| **Substantive note exists** (status active, ≥30 lines, real content) | **STOP** — redirect to `/slipbox-update-feedback`, do NOT overwrite | `Capture Phase: REJECTED — already substantive`, with path |

The plan MUST scan for stub-vs-substantive distinction at Step 4e.2, not just existence. Pure existence checks miss the stub-fill-in case (which is common when an earlier digest left placeholder stubs).

### File Naming Normalization (Step 4 of capture-term-note canonical)

| Term | Filename |
|---|---|
| `DNR` | `term_dnr.md` |
| `BEARS` | `term_bears_buyer_enforcement_abuse_risk_score.md` |
| `Returnless Refunds` | `term_rr.md` (use canonical acronym, not `term_returnless_refunds`) |
| `k-Nearest Neighbors` | `term_knn.md` (use canonical acronym) |
| `Doubly Robust Estimator` | `term_doubly_robust.md` (drop common word "Estimator") |
| `Frisch-Waugh-Lovell` | `term_frisch_waugh_lovell.md` (hyphenated proper-noun chain → underscore-joined) |

Rule: prefer the canonical acronym when one exists; otherwise lowercase + spaces/hyphens → underscores + drop trivial trailing words (`Estimator`, `Method`, `Algorithm` are usually droppable).

### Depth-Scaled Related Terms Minimums

| Note depth | Minimum Related Terms |
|---|---|
| Simple (40-80 lines) | **8** links |
| Moderate (80-150 lines) | **10** links |
| Complex (150-250+ lines) | **12** links |

The plan must specify which depth tier each undigested term is expected to land in (based on its anticipated content density) and enforce the corresponding minimum. The Related Terms floor is **≥8 for ALL term notes** (every tier starts at 8); full term notes scale up with depth.

> **A Pattern-A Phase-0 stub is a TEMPORARY link target only — it MUST be enriched to a FULL term note before the plan is marked completed; do NOT ship a thin stub.** The plan MUST require every stub to be authored via `/slipbox-capture-term-note` into a full note (Definition + Context + Key Characteristics + **≥8** related terms + **≥2 EXTERNAL references** found via web/wiki research — not digest-doc-only content) and to carry `research_pending: true` in YAML until enriched. A plan that leaves any `research_pending: true` term note is NOT complete.

### Backlink Expansion Requirement (Step 6 of capture-term-note canonical — REVERSE direction)

Outward `## Related Terms` (8-12 minimum) is ONE direction. The capture skill also requires INWARD backlinks from existing vault notes:

1. **6a-6d Backlink existing non-term notes** that mention the term in plain text — `grep -rl` across `areas/`, `resources/`, `projects/`, `0_entry_points/` (excluding `term_dictionary/`); convert the first plain-text mention in each qualifying note to a markdown link. Target: 1-2 backlinks minimum; optional if no candidates exist.
2. **6e Expand inlinks from existing term notes** — query for in-domain + cross-domain term notes that lack a link to the new term but should have one; add the new term to their `## Related Terms` sections using the standard bold markdown link format. **Target: 5-10 inlinks (mix of in-domain + cross-domain).**

The plan must require both directions, not just outward Related Terms. Without backlinks, the new term sits at low in-degree and gets buried in PPR rankings.

### Section Structure + Ordering Enforcement (Steps 6f-6g of capture-term-note canonical)

| Position | Section | Content |
|---|---|---|
| Bottom-3 | `## Related Terms` | ALL vault-internal `.md` links (`term_*.md`, other notes). Bold markdown link + description per line. |
| Bottom-2 | `## References` | ONLY external URLs (wiki, corpus document, papers, docs.hub, Wikipedia). **NO `.md` links here.** |
| Bottom-1 (optional) | Footer block | `---` separator + `**Last Updated**:` + `**Status**:` lines |

Both rules are LOAD-BEARING:
- No external URLs inside `## Related Terms` (those belong in References)
- No `term_*.md` links below `## References` (those belong in Related Terms)
- Related Terms MUST come BEFORE References
- Footer block (if any) MUST be the LAST element

### >200-Line Atomicity Decomposition (Step 7 of capture-term-note canonical)

If the captured term note exceeds 200 lines, the capture skill DECOMPOSES it. The plan must require:

| Section Building Block | Child Note Type | Target Directory |
|---|---|---|
| Procedure (Steps, How-To, Workflow, Detection, Prevention, Enforcement) | `sop_<entity>_<topic>.md` | `resources/policy_sops/` |
| Model / Empirical Observation / Argument / Hypothesis / Counter-argument | `thought_<entity>_<topic>.md` | `resources/analysis_thoughts/` |
| KEEP in parent | Concept + Navigation (Definition, Description, Related Terms, References) | parent stays in `term_dictionary/` |

The decomposed parent gets a `## Key Highlights` summary + `## See Also` listing child notes. Children get `decomposed_from: <parent_path>` YAML field + `## Source` linking back. Verify: `parent_after_lines + sum(children_lines) ≥ parent_before_lines` (zero information loss).

### Exact Glossary Entry Template (Step 5 of capture-term-note canonical)

```markdown
### <ACRONYM> - <Full Name>
**Full Name**: <Full Name spelled out>
**Description**: <4-5 sentences MAXIMUM. Bold the single most important distinguishing fact. NO specific numbers/metrics/dollar amounts.>
**Documentation**: <Term Name>
**Wiki**: <primary_wiki_url>
**Related**: <Related Term 1>, [<Term 2>](#<anchor>)
```

4-5 sentence Description structure:
- Sentence 1: what it is + problem it solves
- Sentence 2: key technical approach / core mechanism
- Sentence 3-4: characteristics / use cases / distinguishing properties
- Sentence 5 (optional): status / team / deployment scope

### ENRICHER_INPUTS Non-Interactive Pattern (Step 1 of capture-term-note canonical)

For batch term capture (Pattern A Phase-0 stub creation OR interleaved batch dispatch from `/slipbox-execute-digestion-plan`), the plan should specify the non-interactive ENRICHER_INPUTS pattern:

```yaml
ENRICHER_INPUTS:
  key_terms: ["<TERM NAME>"]
  acronym: "<ACRONYM>"
  domain: "<context keywords for source search>"
  summary_snippets:
    - "<first definition from digest doc>"
    - "<key characteristic from digest doc>"
  references:
    - <digest_doc_url>

SOURCE CONTENT: <the relevant excerpt(s) from the digest doc — verbatim>
```

When ENRICHER_INPUTS + SOURCE CONTENT are provided, the capture skill skips interactive prompts (Step 1 interactive) AND may skip Steps 3a-3c (wiki / corpus document / supplementary search) IF the SOURCE CONTENT provides sufficient body. **It still REQUIRES Steps 3d (in-domain related terms) and 3e (cross-domain related terms)** — those use the vault DB and don't depend on external research. Multi-source research mandate still holds for full term notes (vs Phase-0 stubs).

### Research Dry-Fall Fallback (Constraint 7 of capture-term-note canonical)

If multi-source research returns NOTHING substantive (wiki empty, corpus document empty, SAGE empty, BROADCAST empty, no useful external sources found), the capture skill MUST ask the user for a direct URL OR pasted source. The plan must NOT plan to silently emit a stub with only the digest doc's content — that violates the doc-trapped-scope avoidance. Acceptable fallbacks:
- Pause for user input on direct URL
- Mark the term as `status: stub` with explicit `research_pending: true` YAML field and a TODO comment

### Acceptance — term-note authoring is NOT done if

- Only the digest doc is cited (single-source trapped scope) → **FAIL**
- `## Related Terms` lists fewer than the depth-scaled minimum (8/10/12 by note complexity) → **FAIL**
- Related Terms lacks cross-domain diversity (all same-tag siblings) → **FAIL**
- No inlink expansion from existing term notes (Step 6e — 5-10 target missed) → **FAIL**
- `## References` contains `term_*.md` links (those belong in Related Terms) → **FAIL**
- `## Related Terms` contains external URLs (those belong in References) → **FAIL**
- Section ordering violated (References before Related Terms, footer not last) → **FAIL**
- YAML uses any forbidden field (`title`, `category`, `created`, `updated`, `source`, `parent`, `author`, `note_second_category`) → **FAIL**
- `building_block` is not `concept` → **FAIL** (term notes are concepts; treat-as-procedure goes to how-to)
- Fleeting content present without temporal qualifier → **FAIL**
- Glossary Description exceeds 5 sentences or contains metrics → **FAIL**
- Glossary entry uses anything other than the exact `**Full Name** / **Description** / **Documentation** / **Wiki** / **Related**` template → **FAIL**
- Note exceeds 200 lines without Step-7 decomposition (Procedure→`sop_*`, Model/Argument→`thought_*`) → **FAIL**
- File naming uses non-canonical form (`term_returnless_refunds.md` when `term_rr.md` is canonical) → **FAIL**
- Substantive note exists at target path and was OVERWRITTEN instead of redirected to `/slipbox-update-feedback` → **FAIL** (data loss)
- Multi-source research dry but no fallback to user prompt was attempted → **FAIL**
- Any mathematical formula written in plain-text instead of MathJax (`X̄₁` instead of `$\bar{X}_1$`; `(a)/(b)` instead of `$\frac{a}{b}$`) → **FAIL** (per Constraint 11 of capture-term-note canonical)
```

### 10.5e Verify the plan invokes `/slipbox-capture-term-note` for each undigested term

Each capture obligation in the plan's execution phases must explicitly call `/slipbox-capture-term-note <term>` — NOT inline-author the term note. The capture skill bundles the multi-source research + format compliance; rolling-your-own per term scatters quality.

### 10.5f Term Slug Specificity + Collision Audit

> **Why this step exists**: Plan-digestion Step 4e's three-way pre-flight checks only the EXACT planned slug — it doesn't catch (a) substantive vault notes covering the same concept under a different name (e.g. `term_orthogonal_ml` duplicates the existing `term_double_machine_learning`), or (b) slugs that are so general they collide with broader concepts (e.g. `term_fixed_effects` collides with ANOVA/GLM/mixed-model "fixed effects", a different concept), or (c) slugs that collide with existing differently-scoped notes (e.g. CATE `term_meta_learner` vs few-shot `term_meta_learning`). Skipping this audit ships duplicate term notes + ambiguous-name notes that break PPR retrieval.

For each row in the Undigested Terms Plan, run BOTH a **specificity audit** and a **collision audit**.

#### Specificity audit — flag slugs that are too general

A slug is "too general" if any of these hold:

| Heuristic | Example fail | Fix |
|---|---|---|
| One-word common-English noun without domain qualifier | `term_randomization`, `term_fixed_effects` | Add domain prefix/suffix: `term_random_assignment`, `term_panel_fixed_effects` |
| Drops canonical authorial / framework attribution | `term_compliance_types` (Angrist-Imbens-Rubin called this `principal_strata`) | Use literature's standard name: `term_principal_strata` |
| Drops scope qualifier when scope-specific concept | `term_meta_learner` (causal CATE-specific, but ambiguous) | Add scope prefix: `term_cate_meta_learner` |
| Singular noun for a formal framework | `term_potential_outcome` | Use plural + "framework": `term_potential_outcomes_framework` |
| Generic ML/stats metric name re-used in a specific subfield | `term_cumulative_gain` (uplift-modeling-specific but bare "cumulative gain" exists in recsys/ranking) | Add subfield qualifier: `term_cumulative_gain_curve` |

For every too-general slug, RENAME it in the Undigested Terms Plan table AND add a Naming Notes column explaining the reason. Record the rename in a `### Renamed (general → specific)` sub-table inside the Undigested Terms Plan section.

#### Collision audit — verify no substantive vault note already covers the concept

> **Generalize beyond term slugs (added 2026-06-13).** Run this collision audit for **EVERY planned note
> in the Planned Notes table — documentation concept/procedure notes too, not only `term_*` slugs** — and
> search **both** `term_dictionary/` AND `resources/documentation/`. The most common real miss is a planned
> documentation concept note (e.g. `cc_mcp`, `cc_skill`) that duplicates an existing **term** note
> (`term_mcp`, `term_skills`) — the term-only check never catches it. Substantive same-concept match (term
> OR doc) → REMOVE from the plan; link or enrich the existing note instead. Confirm every DUP verdict with
> an independent skeptic pass before any delete/merge (adversarial dedup-verify).

The Step 4e.2 existence check used the EXACT slug only. Augmentation must run a broader synonym search:

```bash
# For each planned slug, query the vault for substantive notes covering the same concept
for slug in $(grep -oE '`term_[a-z_]+`' "$PLAN_FILE" | tr -d '`' | sort -u); do
  topic=${slug#term_}
  # Search by topic keywords (split slug on underscores) — find substantive matches under different names
  keywords=$(echo "$topic" | tr '_' ' ')
  # Query both filesystem (fuzzy) AND vault DB (semantic)
  echo "=== Synonym scan: $slug — looking for '$keywords' under different names ==="
  # 1. Filesystem: list terms whose name contains ANY keyword
  for kw in $(echo "$topic" | tr '_' ' '); do
    find "$VAULT/resources/term_dictionary" -name "term_*${kw}*.md" -type f 2>/dev/null
  done | sort -u
  # 2. DB query: BM25 search across term_dictionary for the topic
  sqlite3 "$DB" "SELECT note_id, line_count FROM notes WHERE note_id LIKE '$VAULT/term_%' AND title MATCH '$keywords' LIMIT 5" 2>/dev/null
done
```

For each existing substantive match (status:active, ≥30 lines, content not just stub TODO/TBD), the planned slug must be:
- **REMOVED** from the Undigested Terms Plan
- **Recorded** in a `### Removed (substantive vault notes already cover the concept — link instead of create)` sub-table with: original slug, existing note path, line count + status, action (which sub-plan(s) will link to existing instead)

> **Worked example (2026-06-12)**: Sub-Plan 0 of `plan_digest_causal_inference_handbook_master.md` originally listed `term_randomization` (Ch 2) and `term_orthogonal_ml` (Ch 22). The augment-time collision audit caught both — `term_randomized_controlled_trial.md` (171 lines, status:active) already covered "randomization"; `term_double_machine_learning.md` (171 lines, status:active) already covered "orthogonal ML / DML". Both removed, sub-plans 1/2/7 rerouted to link the existing notes. Five other slugs (`potential_outcome`, `compliance_types`, `fixed_effects`, `cumulative_gain`, `meta_learner`) flagged by specificity audit and renamed. Sub-Plan 0 went 29→27.

#### Re-run pre-flight after renames

Renaming a slug changes its existence check target. After all renames, re-run Step 4e.2 against the NEW slugs to confirm they're still NEW (not accidentally matching a different existing note).

### 10.5g Update plan status only when 10.5a-f all pass

If any sub-check fails, append a FAIL row to a `## Augmentation Failures` section in the plan and DO NOT advance the plan to `ready`. Re-run augmentation after the plan author addresses the gaps.

## Step 10.6: Documentation-Note Authoring Spec (for non-term notes) <!-- :: section_id = step_10_6_doc_note_spec :: -->

> Added 2026-06-13 (gap fix). Step 10.5d specifies Term-Note Authoring Requirements in depth, but the
> **bulk of most digests is `documentation/` concept/procedure notes**, which had no equivalent authoring
> spec — leaving their format to an un-derived "Note Format Definition" (the format-drift gap). Augmentation
> MUST verify the plan's Documentation-Note Authoring Spec is present and **derived from existing target-dir
> notes** (plan-digestion Step 2d), not invented.

For documentation concept/procedure notes the plan must require (copying the *actual* convention of the target directory, verified against ≥2 existing notes there):
- **YAML**: exact field order of existing notes (typically `tags → keywords → topics → language → date of note → status → building_block → source_url → access_control_group`); `language: markdown`; `access_control_group: ["general"]`; same forbidden-field list as term notes.
- **Body**: `# <Descriptive Title>` → `## Overview` opener (NOT `## Definition`) → source-mirrored H2/H3 (`## How It Works`, `## Key Points`, `## Steps`, …) → `## Related Notes` (reference section: **≥8 relevancy-selected term-note links** + other related notes, each `- Term Name — description; relevance: <why it matters to this note>`; terms/siblings then cross-folder) → optional `## References` (external URLs) → footer `**Source**` / `**Last Updated**` / `**Status**: Active` (plain bold, no heading).
- **One BB type per note**; density caps ≤400 lines / ≤1800 words / ≤6 code blocks.
- **Dedup-before-create** (Step 10.5f generalized) + **G8 inbound link** (Step 9d).

If the plan's Note Format Definition was clearly invented (doesn't match any existing target-dir note), FAIL — return to `/slipbox-plan-digestion` Step 2d.

## Step 10.7: Validate Entry-Point Decision (CREATE vs UPDATE) <!-- :: section_id = step_10_7_entry_point_decision :: -->

> Added 2026-06-12. Plan-digestion's Step 4c introduced a size-based rule: `<15` notes = UPDATE only, `15-30` notes = CREATE + update parent hub, `>30` notes = CREATE required. Augmentation verifies the plan respects the rule.

### 10.7a Read the plan's Note count

```bash
TOTAL_NOTES=$(grep -c '^| [0-9]' "$PLAN_FILE")   # rough — adjust to actual planned-notes table format
# For master+sub-plans, sum across all sub-plans (recorded in master plan's "Total estimated" line)
```

### 10.7b Read the plan's `## Entry Point Decision` section

If the section is **missing** → FAIL — return the plan to `/slipbox-plan-digestion` for Step 4c completion.

### 10.7c Verify the decision matches the size threshold

| Total notes | Required action | Plan must state |
|---|---|---|
| <15 | UPDATE only | Lists ≥1 existing entry point + WHICH section/rows to add |
| 15-30 | CREATE + parent-hub UPDATE | Names new `entry_<slug>.md` + identifies the parent hub to back-link |
| >30 | CREATE required | Same as 15-30, plus a per-section/per-sub-plan table structure for the new entry point |

If the plan's stated action does NOT match the size threshold → FAIL with the specific mismatch.

Common failures:
- Plan says "UPDATE existing entry_X" but the digest is 50 notes → user/agent must reconsider; 50-note digest needs its own entry point
- Plan says "CREATE new entry_Y" but the digest is only 6 notes → too sparse; route to UPDATE instead
- Plan names a new entry point but forgets the parent-hub back-link → ADD the parent-hub update step

### 10.7d For CREATE: verify the dedicated entry point spec

The plan's `## Entry Point Decision` for CREATE must include:
- New entry-point filename (`entry_<slug>.md`)
- Slug matches the master plan slug
- Required body sections (`## Quick Stats`, per-section/per-sub-plan link table, `## Related Entry Points`, `## References`)
- YAML: `building_block: navigation`
- Identified parent hub + back-link row content

### 10.7e For UPDATE: verify the existing entry point exists

```bash
# For each existing entry point named in the plan:
ls "$VAULT/0_entry_points/<entry_X.md>"
```

If the named entry point doesn't exist → FAIL — the plan author named a non-existent target. Either pick a real entry point OR convert to CREATE.

## Step 11: Run 19-Item Completeness Checklist <!-- :: section_id = step_11_checklist :: -->

Verify the augmented plan passes ALL items:

- [ ] Objective states source, page count, planned note count
- [ ] Routing Decision with location, rationale, existing notes
- [ ] Source with URL, page count, owner
- [ ] Content Strategy (prioritize, group, skip)
- [ ] Section Coverage Map (every H2/H3 → one note)
- [ ] Split Decisions table (if any splits made)
- [ ] Planned Notes table (filename, BB, ~words, description)
- [ ] Content Size Assessment
- [ ] Summary Statistics
- [ ] Building Block Distribution
- [ ] Cross-References per-note mapping
- [ ] Entry Points to update (specific section + rows)
- [ ] Inlinks to add (existing → new)
- [ ] Execution Phases with per-phase GATE tables
- [ ] Note Format Definition (YAML template + forbidden fields)
- [ ] Validation Scripts (bash — format, density, links)
- [ ] Pacing Rules
- [ ] Density Re-Assessment (source re-read confirmation)
- [ ] Follow-up Recommendations
- [ ] **Undigested Terms Plan section present** (Step 10.5a) — table of undigested terms surfaced from the source
- [ ] **Every undigested term has a defined Capture Phase** (Step 10.5b) — no `TBD` rows
- [ ] **Every undigested term has a verified best-fit glossary** (Step 10.5c)
- [ ] **Term-Note Authoring Requirements section present** (Step 10.5d) — format compliance + multi-source research mandates
- [ ] **Plan invokes `/slipbox-capture-term-note` for each undigested term** (Step 10.5e) — not inline authoring
- [ ] **Entry Point Decision section present** (Step 10.7b) — CREATE vs UPDATE + parent-hub back-link
- [ ] **Entry-Point Decision matches size threshold** (Step 10.7c) — `<15` UPDATE / `15-30` CREATE + hub / `>30` CREATE required
- [ ] **Term Slug Specificity audit performed** (Step 10.5f) — no too-general slugs; renames documented in plan with reasons
- [ ] **Term Slug Collision audit performed** (Step 10.5f) — synonym search against existing vault notes; substantive matches removed from plan and rerouted to link existing
- [ ] **Dedup audit generalized to ALL planned notes** (Step 10.5f, incl. documentation concept notes; search term_dictionary AND documentation/) — no doc-note duplicates an existing term note
- [ ] **G8-Discoverability gate present in every phase table + inlinks marked EXECUTED** (Step 9d) — every new note ends with DB in-degree ≥1 from outside the folder
- [ ] **Documentation-Note Authoring Spec present + derived from existing target-dir notes** (Step 10.6) — format not invented

Report: "Plan passes N/31 checklist items. Missing: [list]."

If all 31 pass → plan is ready for execution.

---

## Step 12: Final Confirmation <!-- :: section_id = step_12_confirm :: -->

Ask the user:

```
Plan augmentation complete. 24/24 checklist items pass.

Summary:
- [N] notes planned across [M] phases
- [X] sections added/updated during augmentation
- Density re-assessment: [no further splits / N additional splits applied]
- Inlinks mapped: [K] existing notes → new notes
- Undigested terms surfaced: [T_orig from plan-digestion + T_new added during augment re-read]
- Term-Note Authoring Requirements: present; multi-source research mandated (WIKI + corpus document + SAGE + BROADCAST + external)
- Ghost-reference detection script (G5): present
- Broken-link fix gate (G6): present

Ready to execute? Or review specific sections first?
```

---

## Important Constraints <!-- :: section_id = important_constraints :: -->

1. **MUST re-read source** — Step 2 is non-negotiable. Never trust the plan's word-count estimates without verifying against actual source content.
2. **Split is ALWAYS preferred over compression** — if in doubt, split. A 20-note plan is better than a 12-note plan with over-dense notes.
3. **Plan is the contract** — all changes go into the plan file first, then execution follows the plan.
4. **Verbatim code** — mark in the plan which source sections contain code that MUST be preserved character-for-character.
5. **No orphaned sections** — every source H2/H3 must appear in the coverage map. "Skip" with documented reason is acceptable; silent omission is not.

## Error Handling <!-- :: section_id = error_handling :: -->

| Error | Cause | Recovery |
|-------|-------|----------|
| Plan file not found | Wrong path or not yet created | Run `/slipbox-plan-digestion` first |
| Source URL no longer accessible | Page moved/deleted since plan was written | Ask user for updated URL; note in plan |
| Plan already has all 11 sections | Augmentation not needed | Report "Plan is already complete (19/19)" |
| Re-read reveals plan is fundamentally wrong | Source structure misunderstood | Recommend rewriting plan from scratch |

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog
- [FZ 28c: Plan Augmentation](../analysis_thoughts/thought_digestion_plan_augmentation.md) — the design note this skill implements
