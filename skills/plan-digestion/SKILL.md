---
tags:
  - resource
  - skill
  - procedure
  - capture
  - planning
  - documentation
  - digestion
keywords:
  - plan digestion
  - slipbox-plan-digestion
  - in-vault skill canonical
  - building block atomic notes
  - content density
  - section coverage map
topics:
  - Skill Procedures
  - Vault Tools
language: markdown
date of note: 2026-05-23
status: active
building_block: procedure
---

# Procedure: slipbox-plan-digestion (Canonical Body)

> **Ported skill.** Adapted from an upstream vault canonical for use in this
> repository. All paths are local: notes live under `vaults/$CORPUS`, the database
> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill
> never reads or writes any vault outside this repo.

This is the **single canonical body** for the `slipbox-plan-digestion` skill (FZ 12a).

## Skill description <!-- :: section_id = skill_description :: -->

Read a documentation source (wiki site, corpus docs, corpus document doc, PDF, or any multi-section document) and generate a structured digestion plan that decomposes the content into BB-atomic notes. Each planned note corresponds to exactly one building block type. The plan controls content density (split if >400 lines, >1800 words, or >6 code blocks), maps every source section to a note, identifies cross-references, and defines validation gates. Outputs plan to `experiments/plans/`. Use when the user provides a documentation URL or source and wants to plan how to digest it into vault notes before execution.

## Setup <!-- :: section_id = setup :: -->

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```

## Resources <!-- :: section_id = resources :: -->

- **Plans directory**: `$PLANS_PATH` (project root `experiments/plans/`)
- **Existing plans**: Read 1-2 completed plans in `$PLANS_PATH` to calibrate format (e.g., `plan_digest_builder_mcp_user_guide.md`, `plan_digest_meshclaw_wiki.md`)
- **Building block definitions**: `$VAULT/$VAULT/term_knowledge_building_blocks.md`
- **Vault DB**: `$DB` for searching existing notes (avoid duplication)
- **Digest wiki site skill**: `$VAULT/resources/skills/skill_slipbox_digest_wiki_site.md` (reference for GATE definitions)

---

## Step 1: Identify Source and Read Content <!-- :: section_id = step_1_identify_source :: -->

### 1a. Determine source type

| Source Type | How to Read | Examples |
|-------------|-------------|---------|
| docs.hub.amazon.dev (corpus) | `local file read` | https://docs.hub.amazon.dev/... |
| code.amazon.com (docs package) | `local file read` | https://code.amazon.com/packages/.../blobs/mainline/--/... |
| External URL | `WebFetch` | https://docs.aws.amazon.com/... |
| Local file/PDF | `Read` tool | File path provided by user |

### 1b. Read the root page and all leaf pages

Read the source URL. Extract all linked sub-pages (child pages, leaf pages). Read each one.

### 1c. MEASURE content size per page (not estimate)

For each page, you MUST record **measured** word counts and section counts — not estimates from memory or training knowledge. The measurement comes from the actual tool output (WebFetch, local file read, or Read).

**Measurement protocol**:
1. After reading each page, count words in the tool output (or ask the fetch tool to report word count)
2. Count code blocks (``` pairs / 2)
3. List all H2/H3 headings

Record in a table:

```
| Page | URL | Measured Words | Code Blocks | H2/H3 Headings |
|------|-----|---------------|-------------|-----------------|
```

> **WARNING — Common failure mode**: Agents frequently UNDERESTIMATE page sizes by 50-70% when working from training knowledge instead of actual page reads. AWS documentation pages typically contain 2000-5000 words each (not 800-1500). If your estimates seem low (most pages <1500w), you likely did not actually read the page — go back and WebFetch it.

**Calibration check**: If total source content across all pages is <5000 words for a multi-page documentation site, your measurements are almost certainly wrong. A typical AWS service developer guide chapter has 15,000-50,000 words.

### 1d. Assess total content volume — decide if sub-plans needed

| Total Content | Treatment |
|---------------|-----------|
| ≤ 10,000 words (≤15 notes) | Single plan — proceed normally |
| 10,000–30,000 words (15-30 notes) | Single plan with phased execution |
| > 30,000 words (>30 notes) | **Divide-and-conquer** — master plan + sub-plans |

### 1e. Divide-and-Conquer Principle (>30 notes)

When the source is too large for a single plan, apply the **master plan + sub-plans** pattern:

**Master plan** (`plan_digest_<source>_master.md`) is a **pure index hub** — it does NOT contain per-note details. It defines:
1. Shared routing decision (location, prefix, 3-criterion rationale)
2. Shared format definition (YAML template, forbidden fields)
3. Shared cross-references (existing vault notes to link from ALL sub-plans)
4. Shared validation gates and pacing rules
5. Shared entry points to update
6. **Sub-plans index table** with: file link, topic, note count, priority, status
7. **Execution order** by priority grouping (P1 core → P2 operational → P3 specialized)

**Sub-plans** (`plan_digest_<source>_N_<topic>.md`) are **self-contained** — each one is independently augmentable and executable. Each sub-plan gets the full treatment (Steps 2-8) and full augmentation (19-item checklist):
- Its own section coverage map
- Its own planned notes table (the ONLY place note filenames/BBs are defined)
- Its own per-note related notes mapping
- Its own inlink table
- Its own execution phases with per-phase GATEs
- Its own density re-assessment
- Its own validation scripts

**Key rules**:
- The master plan NEVER duplicates note tables from sub-plans — if someone needs note details, they read the sub-plan file
- Each sub-plan can execute independently — no cross-sub-plan dependency for execution (only for cross-references added post-execution)
- Priority grouping determines order: P1 sub-plans create foundational concepts that P2/P3 reference
- Status tracking lives in the master plan's index table (pending → ready → in_progress → complete)

**Sub-plan splitting heuristic**: Split by major chapter/domain of the source. Each sub-plan should produce 4-10 notes. If a sub-plan would produce >15 notes, split it further.

**File naming convention**:
```
plan_digest_<source_slug>_master.md          ← index hub
plan_digest_<source_slug>_1_<topic>.md       ← sub-plan for chapter 1
plan_digest_<source_slug>_2_<topic>.md       ← sub-plan for chapter 2
...
```

Sub-plans can execute in parallel if they have no cross-dependencies.

---

## Step 2: Route — Decide Where Notes Go <!-- :: section_id = step_2_route :: -->

### 2a. Check existing notes (avoid duplication)

```bash
sqlite3 "$DB" \
  "SELECT note_id, note_name, file_path
   FROM notes
   WHERE (note_name LIKE '%<TOPIC>%' OR keywords LIKE '%<TOPIC>%')
     AND note_status = 'active'
   ORDER BY static_ppr_score DESC
   LIMIT 20;"
```

List existing notes that cover the same topic. The plan must NOT duplicate them — instead reference them.

### 2b. Determine target directory

Apply the routing principles from `/slipbox-route-content` (the authoritative routing skill):

1. **3-Criterion Rule**: Check (a) source novelty, (b) operational tasks, (c) maintenance cadence. 0-1 novel → route to existing folder. 2-3 novel → propose new subfolder.
2. **Context Affinity**: Notes from the same source stay close in folder hierarchy.
3. **Content TYPE > SOURCE**: Route by what the content IS, not where it came from.

Quick reference for common sources:

| Source Type | Content Style | Target Directory | Prefix Pattern |
|-------------|--------------|-----------------|----------------|
| corpus docs (docs.hub.amazon.dev) | Reference/guide | `$VAULT/` | `builderhub_<topic>_*.md` |
| User guide / onboarding guide (any platform) | Step-by-step tutorial sequence | `$VAULT/` | `tutorial_<topic>_*.md` |
| External (books, blogs, open-source docs) | Digest | `resources/digest/` | `digest_<topic>_*.md` |
| AWS service docs (docs.aws.amazon.com) | Reference/guide | `$VAULT/` | `aws_<service>_<topic>_*.md` |

**Routing heuristic**: Sequential user guide → `tutorials/`. Reference/inventory → platform subfolder. When in doubt, run `/slipbox-search-notes <topic>` to find where similar content already lives.

> **Corollary**: If a cohesive series will produce >15 notes, a dedicated subfolder is justified. Otherwise, use file prefixes within the existing folder.

### 2c. Document routing decision in plan

Write a **Routing Decision** section with: location, rationale, existing notes to NOT duplicate, and file prefix.

### 2d. Derive the Note Format Definition from existing target-dir notes (do NOT invent)

> Added 2026-06-13 (gap fix). Plans that invent a note format from intuition drift from the vault's
> conventions and fail review CP5 — catching it late instead of preventing it. Derive the format at PLAN
> time from the notes already in the target directory.

Read **≥2 existing notes** in the routed target directory (or, for a brand-new subfolder, the closest sibling folder). Extract and COPY into the plan's Note Format Definition:
- the **exact YAML field order** (run a quick survey if the dir is large — e.g.
  `grep -h '^[a-z].*:' <dir>/*.md | ...` to find the dominant order; verify with `check_yaml_frontmatter.py`),
- the **dominant H2 conventions** (e.g. `## Overview` opener, `## Related Notes` cross-link section, the
  `**Source**`/`**Last Updated**`/`**Status**` footer — whatever the existing notes actually use),
- the forbidden-field list.

The Note Format Definition must say "derived from `<example note>`", not be written from memory. This is the **Documentation-Note Authoring Spec** — the doc-note analog of the Term-Note Authoring Requirements that `/slipbox-augment-digestion-plan` adds for term notes.

---

## Step 3: Decompose into BB-Atomic Notes <!-- :: section_id = step_3_decompose :: -->

### 3a. Classify each source section by building block

| Content Pattern | Building Block |
|----------------|---------------|
| Definitions, terminology, "what is X" | concept |
| Step-by-step instructions, commands, setup | procedure |
| Architecture, system components, data flow, tables | model |
| Claims with evidence, design rationale, trade-offs | argument |
| Observed behavior, metrics, examples, demos | empirical_observation |
| Testable predictions, experimental design | hypothesis |
| Limitations, risks, critiques | counter_argument |
| Index/routing structures | navigation |

### 3b. Group adjacent sections with same BB into candidate notes

Adjacent sections with the same building block combine into one note. NEVER mix BBs in a single note.

### 3c. Apply density thresholds — split if exceeded

**First: check source page size** — if a source page exceeds 1800 words, it CANNOT map to a single note without splitting. Apply the page-level rule BEFORE grouping:

| Source Page Size | Treatment |
|-----------------|-----------|
| ≤ 1200 words | Likely fits 1 note |
| 1200–1800 words | Fits 1 note if single BB; split if mixed BB |
| 1800–3600 words | MUST split into 2 notes minimum |
| > 3600 words | MUST split into 3+ notes |

**Then: check per-note thresholds** after grouping:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Word count | > 1800 words | Split at nearest H2/H3 boundary |
| Line count | > 400 lines | Split |
| Code blocks | > 6 per note | Split "overview" from "examples" |
| H2 sections | > 6 unrelated topics | Split by topic cluster |
| Mixed BB | Both procedure AND concept (>500w each) | Split into separate notes |

### 3d. Write Section Coverage Map

For EVERY source section (H1/H2/H3), record which planned note it maps to. No section can be orphaned.

```
Source Page (~Nw)
├── Section A (Mw, concept) ──── → Note 1
├── Section B (Mw, procedure) ── → Note 2
│   ├── Sub-section B1 (Mw) ──── → Note 2
│   └── Sub-section B2 (Mw) ──── → Note 2
└── Section C (Mw, model) ────── → Note 3
```

### 3e. Document split decisions

If any note was split beyond initial grouping, write a **Split Decisions** table explaining WHY:

| Original | Split Into | Rationale |
|----------|-----------|-----------|
| Note X (too dense) | Note Xa + Note Xb | >1800w OR mixed BB OR >6 code blocks |

---

## Step 4: Plan Cross-References <!-- :: section_id = step_4_cross_references :: -->

### 4a. Search vault for related notes

Use `/slipbox-search-notes <KEYWORD>` for each of 5-8 keywords from the source content. The search skill applies BM25, graph traversal, and PPR scoring across ALL note types automatically.

Alternatively, for direct DB lookup:
```bash
sqlite3 "$DB" \
  "SELECT note_id, note_name, note_second_category, file_path
   FROM notes
   WHERE (note_name LIKE '%<KEYWORD>%' OR keywords LIKE '%<KEYWORD>%')
     AND note_status = 'active'
   ORDER BY static_ppr_score DESC
   LIMIT 20;"
```

### 4b. Build per-note reference mapping

For each planned note, use `/slipbox-search-notes` with key concepts from that note to discover related vault notes (any type — terms, tools, repos, snippets, areas, howtos, projects, etc.). List the top matches in a per-note reference mapping.

> **Minimum ≥8 term notes per planned note (added 2026-06-13; raised ≥6 → ≥8 on 2026-06-21).** Every planned note's reference mapping
> MUST include **≥8 `term_dictionary/` term notes**, selected by **content relevancy** to that note — the
> terms whose concepts the note actually uses, relevancy-ranked (BM25/dense/graph), **NOT padded with
> unrelated terms**. Other related notes (tools/repos/areas/howtos/siblings/entry points) are *additional*,
> not a substitute. If genuinely fewer than 8 relevant term notes exist for a niche note, broaden the
> search first; only fall below 8 with an explicit per-note justification in the mapping. (Augmentation
> Step 8 verifies this floor and DB-checks every term exists.)
>
> **Format in the note** — the ≥8 term notes appear in the digest note's reference section (`## Related
> Notes`) as **indexed markdown links, each with a term description AND its relevancy to THIS note**:
> `- [Term Name](relative_path.md) — <one-line what-the-term-is>; relevance: <why it matters to this note>`.
> Relevancy is the selection criterion AND must be stated per link (not just listed).

### 4c. Identify entry points — UPDATE vs CREATE (size-driven)

Two actions are possible: UPDATE an existing entry point, or CREATE a new dedicated one. The decision is driven by the digest's note count:

| Digest size | Entry-Point Action |
|---|---|
| **<15 notes** | UPDATE only — add 1-3 rows OR a new H2 section to the most relevant existing entry point(s). Do NOT create a new entry point — would be too sparse. |
| **15-30 notes (single plan)** | **CREATE a dedicated entry point** + update parent hub. The 15+ note series is cohesive enough to deserve its own navigation hub; readers expect to land on a clean index. |
| **>30 notes (master + sub-plans)** | **CREATE a dedicated entry point — REQUIRED.** The entry point mirrors the master plan's Sub-Plans Index, grouped by topic / sub-plan / chapter. It is the canonical navigation surface for the series. |

#### When CREATE: file naming + template

- **File**: `0_entry_points/entry_<source_slug>.md`
- **Slug**: same slug used in `plan_digest_<source_slug>_master.md` (e.g. `entry_aws_lambda.md`, `entry_causal_inference_handbook.md`, `entry_aws_bedrock_agentcore.md`)
- **YAML**: `building_block: navigation`, `tags: [entry_point, ...]`, `keywords: [<source name>, <key concepts>]`
- **Required body sections**:
  - H1 + 1-line description with source URL
  - `## Quick Stats` table (Total Notes / Source / Sections — e.g. `entry_aws_lambda.md` shows "71 of 71" notes, source URL, named sections)
  - Per-section / per-sub-plan table linking to each digest note grouped by topic (one row per note: # / link / BB / one-line description)
  - `## Related Entry Points` cross-linking to sibling entry points + parent hub
  - `## References` — source URL + the master plan file under `experiments/plans/`

#### When CREATE: mandatory back-link to the parent hub

After creating the dedicated entry point, ADD a row to the parent hub so the new entry is discoverable. The parent hub varies by source type:

| Source type | Parent hub to update |
|---|---|
| AWS service docs (docs.aws.amazon.com) | `0_entry_points/entry_aws_services_hub.md` |
| Internal wiki (the corpus) | `0_entry_points/entry_wiki_hub.md` (or equivalent index) |
| corpus (docs.hub.amazon.dev) | `0_entry_points/entry_builderhub.md` |
| External book / blog / open-source docs | `0_entry_points/entry_digest_index.md` (or equivalent) |

Without the parent-hub back-link, the new entry point is an orphan and won't be reached via normal navigation.

#### When UPDATE: which entry point(s)

Identify ≥1 existing entry point that naturally covers the topic. Spell out:
- The specific entry-point filename (e.g. `entry_<topic>.md`)
- WHICH section to extend (existing H2) OR a new section to add
- HOW MANY rows the update introduces

If 3+ candidate entry points cover overlapping ground, decide ONE primary + cross-link from the others.

### 4d. Plan inlinks (existing notes → new notes)

Which existing code repo/snippet/tool notes should get backlinks pointing TO the new notes?

---

## Step 4e: Identify Undigested Terms + Best-Fit Glossary <!-- :: section_id = step_4e_undigested_terms :: -->

> **Why this step exists**: every documentation source introduces concepts (acronyms, method names, statistical terms) the vault may or may not already have term notes for. If we only digest the source body and skip the term-coverage gap, the resulting notes link to ghost terms (lesson from the causal-inference handbook digest, 2026-06-12 — 25 missing causal-method terms surfaced AFTER the plan was already written). This step makes the gap explicit BEFORE the plan is finalized.

### 4e.1 Extract candidate terms from the source

Scan every source page for:
- **ALL CAPS acronyms** (e.g. `ATE`, `CATE`, `IPW`, `DML`, `RCT`, `RDD`, `OVB`)
- **Capitalized method/estimator names** (e.g. `Doubly Robust`, `Propensity Score`, `Frisch-Waugh-Lovell`, `Causal Forest`, `Meta-Learner`)
- **Statistical/ML concepts on first use** (e.g. `Confidence Interval`, `Standard Error`, `p-value`, `Cross-Validation`, `Regularization`)
- **Domain abbreviations** that appear early and recur (the source defines them once, then uses without re-definition)

### 4e.2 Check each candidate against existing vault terms (three-way pre-flight)

Per `/slipbox-capture-term-note` Step 2, the existence check is THREE-WAY, not binary. The plan must record the outcome explicitly:

For each candidate, query the term dictionary AND inspect the file for stub-vs-substantive content:

```bash
SLUG=$(echo "$TERM" | tr '[:upper:]' '[:lower:]' | tr -s ' -' '_' | tr -cd '[:alnum:]_')
NOTE_ID=$(sqlite3 "$DB" "SELECT note_id, note_status FROM notes WHERE note_id LIKE '$VAULT/term_${SLUG}%' LIMIT 1")
# Inspect the file if found
if [ -n "$NOTE_ID" ]; then
  LINES=$(wc -l < "$VAULT/<note_id>")
  # A note is a STUB if note_status in (stub, placeholder, empty) OR <30 lines OR only TODO/TBD/single-sentence
fi
```

| Existing vault state | Action | Plan annotation |
|---|---|---|
| **No matching note** | UNDIGESTED — append to Undigested Terms Plan with `Stub or Full: full` | Capture as full term note |
| **Stub note exists** (`status: stub/placeholder/empty`, <30 lines, only TODO/TBD/single-sentence) | UNDIGESTED — append with `Stub or Full: fill-stub`, record existing-stub path | Capture skill will overwrite with full content after user confirmation |
| **Substantive note exists** (status active, ≥30 lines, real content) | NOT undigested — add the path to Step 4b's per-note Related Notes mapping for every digest note that references the concept. Do NOT plan to capture again. | Existing note used as-is |

The stub-vs-substantive distinction is critical: planning to "create" when a stub exists silently overwrites it (potentially OK but should be user-confirmed), and planning to "create" when a substantive note exists CAUSES DATA LOSS unless redirected to `/slipbox-update-feedback`. The capture skill's Step 2 enforces redirect; the plan must mark substantive existing notes as "do not re-capture" up-front.

Also try canonical-acronym normalization variants before declaring undigested — e.g. for "Returnless Refunds" check `term_rr.md` BEFORE `term_returnless_refunds.md`, since the capture skill uses acronyms canonically (Step 4 file naming rule).

### 4e.3 For each undigested term, identify best-fit glossary

The vault organizes terms by **acronym glossary** notes that group terms by domain. List them:

```bash
ls "$VAULT/0_entry_points/" | grep '^acronym_glossary'
```

Pick the glossary whose existing entries are most topically aligned with the undigested term. If no existing glossary fits and the term cluster is large (>5 sibling terms from the same source), propose a NEW glossary as a separate plan phase.

### 4e.4 Plan the undigested-term capture phases (BEFORE or INTERLEAVED, never AFTER)

Two patterns — pick based on term count:

**Pattern A — Pre-digest stub creation** (when undigested terms ≤10):
- **Phase 0** (runs first): create stubs for every undigested term (`status: stub`, `research_pending: true`, ≤30 lines, definition + source-page citation) so digest notes have real link targets from the start
- **Phase 1-N**: digest the source, linking to the stubs; stubs get back-filled to full notes as the digest passes through their chapters

> **A Pattern-A stub is ONLY a temporary link target — it MUST be enriched to a FULL term note before the plan is marked completed.** Every term MUST end as a full `/slipbox-capture-term-note` note (Definition + Context + Key Characteristics + **≥8** related terms + **≥2 EXTERNAL references** found via web/wiki research), NOT shipped as a thin stub. A stub carries `research_pending: true` in YAML until it is enriched; the plan is NOT complete while any `research_pending: true` term note remains.

**Pattern B — Interleaved** (when undigested terms >10):
- Each sub-plan phase explicitly captures the terms it introduces, BEFORE writing the digest notes for that phase
- Term capture uses `/slipbox-capture-term-note` skill, NOT inline within a digest note

> **Corpus-wide term-ownership sweep (REQUIRED for master+sub-plans under Pattern B; added 2026-06-13).**
> Pattern B distributes term capture to each sub-plan and relies on per-sub-plan G5 to catch ghosts —
> which leaves a **cross-cutting term owned by *no* sub-plan** undetected until late. Before finalizing the
> master, sweep the WHOLE source for undigested terms and assign **every** term an OWNER sub-plan (the one
> that introduces / best-homes it). Record the ownership inventory in the master's Undigested Terms section.
> Any term with **no owner** gets a dedicated capture phase (or switch that cluster to Pattern A). A master
> that declares "Pattern B" without an ownership inventory is incomplete.

### 4e.5 Write the Undigested Terms Plan into the master plan

Append this section to the plan:

```markdown
## Undigested Terms Plan

| Term Slug | Best-Fit Glossary | Capture Phase | Stub or Full | Source Page | Notes |
|---|---|---|---|---|---|
| `term_propensity_score` | acronym_glossary_ml.md | Phase 0 (pre-digest) | full term note | Ch 11 | Distinct from existing `term_propensity_score_matching` (PSM is one IPW variant) |
| `term_synthetic_control` | acronym_glossary_ml.md | Sub-plan 5 interleaved | full term note | Ch 15 | — |
| `term_frisch_waugh_lovell` | acronym_glossary_ml.md | Sub-plan 7 interleaved | full term note | Ch 22 | New method-name term |
| ... | ... | ... | ... | ... | ... |
```

Every undigested term row must have a chosen Capture Phase. A row with `Capture Phase: TBD` is a planning incomplete-ness — go back to Step 4e.4 and decide.

### 4e.6 Discipline rules

- **Do NOT** plan to embed term definitions inline in digest notes "to save a stub" — that violates BB atomicity and prevents the term from being a real link target. Always create a term note even if it starts as a one-paragraph stub.
- **Do NOT** plan to capture undigested terms "after the digest is done" — by then the digest notes ship with ghost references, and Gate G5 fails.
- The `/slipbox-capture-term-note` skill is the canonical author tool for these — augment-digestion will verify the plan invokes it correctly and requires multi-source research (see augment skill Step 10.5).

### 4e.7 Term-Note Authoring Spec (Inherited from `/slipbox-capture-term-note` canonical)

The plan does NOT need to duplicate the full capture-term-note spec, but it MUST explicitly state that every undigested-term capture phase invokes `/slipbox-capture-term-note <term>` (not inline authoring) AND records in the plan that the skill's mandatory requirements are:

- **YAML frontmatter** (required): `tags`, `keywords`, `topics`, `language: markdown`, `date of note`, `status: active`, `building_block: concept`, `access_control_group: ["general"]`, `related_wiki` (primary wiki URL or null)
- **H1 pattern**: `# ACRONYM - Full Name`
- **Required H2 sections in order**: `## Definition` (1-2 paragraphs) → `## Context` (teams, systems, programs) → `## Key Characteristics` (bullet list) → `## Performance / Metrics` (OPTIONAL — only if metrics found) → `## Related Terms` (**8-15 links minimum**, mix of in-domain + cross-domain) → `## References` (external URLs ONLY, ≥1 internal wiki/corpus document URL)
- **Multi-source research domains** (load-bearing): `builder-mcp WIKI` (internal wiki at the corpus) + `corpus document` (the corpus) + `builder-mcp SAGE_HORDE` (corporate search) + `builder-mcp BROADCAST` (launch announcements) + ≥2 external sources (Wikipedia, textbooks, official open-source docs)
- **Cross-domain Related Terms** (the diversity requirement): per the capture-term-note canonical Step 3e, the Related Terms section MUST include cross-domain connections — Foundation, Application, Analogy, Contrast, Successor/Predecessor, Component
- **Fleeting content guard** (Step 4b in capture skill): no person aliases as POCs/owners (use team aliases), no bare dollar amounts without `(as of YYYY)`, no bare ETAs, no team headcounts without qualifiers
- **Glossary entry format** (Step 5 of capture skill): 4-5 sentence Description (hard limit), no metrics, bold the single most important distinguishing fact

The plan must NOT plan to bypass any of these by inline authoring or by reducing requirements. Augmentation (Step 10.5) verifies the plan respects them.

## Step 5: Define Validation Gates <!-- :: section_id = step_5_validation_gates :: -->

Write an **8-GATE** validation table per execution phase. Gates 5-7 are SKILL-DRIVEN and catch ghost references, broken links, and structural defects that no manual review reliably catches; G8 (added 2026-06-13) closes the discoverability/graph-island gap:

| Gate | Check | Pass Criteria | Tool |
|------|-------|---------------|------|
| **G1-Format** | YAML fields, line count, single BB, H1, Related Notes, **prose wrapping (PROSE-001)** | 0 errors — PROSE-001 (mid-paragraph hard-wrap) is now a **blocking error**, fails the batch via `digest_note_gate.sh` | **`/slipbox-check-note-format --path <note>`** (skill) — wraps `check_note_format.py`. Run per note + roll up batch report. Do NOT skip when a note "looks right" — programmatic check catches what eyes miss (unquoted backticks in keywords, hex-as-int, missing fields, **mid-paragraph hard-wrapped prose**). **Authoring rule (prevents PROSE-001): keep each paragraph on ONE logical source line — a single newline renders as a space, so do NOT hard-wrap prose at a column limit; break only at a paragraph end or a standalone list/reference item.** Subagent briefs that author notes MUST carry this rule. |
| **G2-Grounding** | Content faithful, code verbatim, no hallucination, source warnings preserved | Manual diff against source | Diff the snippet's source-line citations against the actual source page; don't hand-wave "verified" |
| **G3-Density** | ≤400 lines, ≤1800 words, ≤6 code blocks, ≤6 unrelated H2 per note | All thresholds met | Validation script in plan (Step 5 of augment skill) |
| **G3-Coverage** | All source H2/H3 sections present in coverage map, no compression | Section coverage map checklist | Per-note coverage table |
| **G4-CrossRef** | Internal links resolve, source URL present, entry-point row added, inlinks landed | All present | Bash link-check script |
| **G5-Ghost** | Every reference (Related Notes, Inlinks, entry-point links) exists in the vault — no ghosts | All references verified | **`/slipbox-fix-ghost-references`** (skill) — `--detect` surfaces every ghost + ranked redirect candidates, then resolve each by **redirect** (to a verified same-sense note, recorded in `## Plan Amendments`), **drop** (de-link), or **defer→capture**. NO ghost reference may survive into execution. Re-run after applying to confirm. |
| **G6-Broken** | After the batch lands, the vault has zero broken links touching the new notes | 0 broken links from any file in the batch | **`/slipbox-check-broken-links`** (skill, read-only) to surface, then **`/slipbox-fix-broken-links`** (skill) to repair path-depth bugs and stale references. Do NOT defer to "next DB rebuild will catch it" — broken-link cleanup is part of the batch, not a separate cycle. |
| **G8-Discoverability** (added 2026-06-13) | Every new note RECEIVES ≥1 inbound link from an existing vault note **outside** the digest folder — the Inlink Mapping (augment Step 9) is *executed*, not just planned | in-degree ≥1 per new note | **DB query** for inbound `note_links` from outside the batch folder. A new cluster can pass G1-G6 yet be an undiscoverable island (0 inbound); G8 prevents that. Reciprocal inlinks are part of the batch, added before the sub-plan is "done". |

### Gate 5 Implementation — Ghost-Reference Detection + Redirect

```bash
# For every reference in the per-note Related Notes mapping:
sqlite3 "$DB" "SELECT note_id FROM notes WHERE note_id = ?" "<candidate>"
#   row returned  → ✓ verified, keep
#   no rows       → ✗ GHOST — find a verified alternative

# Concrete pattern from a prior digest (causal_inference_handbook, 2026-06-12):
# term_machine_learning was a ghost → replaced with term_random_forest (verified existing,
# canonical predictive-ML method that contextually fits the same role)
```

Redirect strategy:
1. Search for a sibling note that covers the same concept (`/slipbox-search-notes <concept>`)
2. Prefer notes from the same building block + the same broader domain
3. If no replacement exists in the vault, EITHER (a) create the missing reference as a `status: stub` term/concept note BEFORE the digest batch runs, OR (b) drop the reference and pick a different verified note that's still relevant
4. Record every redirect in the plan's `## Plan Amendments` section so the audit trail survives

### Gate 6 Implementation — Skill-Driven Broken-Link Repair

```bash
# After the batch is committed (or before, on staged files):
/slipbox-check-broken-links                  # read-only — surface all broken links
# If any belong to files in the batch:
/slipbox-fix-broken-links                    # apply path-depth fix
/slipbox-run-incremental-update              # confirm 0 broken links via DB
```

Gate 6 catches the **recurring path-depth bug class** (`../resources/...` written from inside `resources/` — see Entry: COEs for prior incidents). The skill encapsulates the fix logic; do NOT roll your own regex pass.

### Gate Authoring Pattern for the Plan File

Include all 8 gates in EVERY execution phase's gate table — not just the first phase. Augmentation (`/slipbox-augment-digestion-plan`) verifies per-phase coverage; missing G5/G6/G8 in any phase is a checklist failure.

Include validation scripts (bash) in the plan for automated checking.

---

## Step 6: Write the Plan File <!-- :: section_id = step_6_write_plan :: -->

Create the plan at: `$PLANS_PATH/plan_digest_<TOPIC_SLUG>.md`

### Required Plan Sections

```markdown
---
title: <Source Type> Digestion Plan — <Source Name>
date: YYYY-MM-DD
status: pending
source_url: <ROOT_URL>
---

# Plan: Digest <Source Name> into <Target> Notes

## Objective
## Routing Decision
## Source
## Content Strategy
## Section Coverage Map
## Split Decisions
## Planned Notes (table with #, filename, BB, ~words, description)
## Content Size Assessment
## Summary Statistics
## Building Block Distribution
## Cross-References to Add
## Entry Point Decision (UPDATE existing or CREATE new — per Step 4c size threshold; if CREATE, name the new entry point + parent-hub back-link)
## Undigested Terms Plan (from Step 4e — term slug, best-fit glossary, capture phase, stub/full, source page)
## Execution Phases (with per-phase validation gates)
## Note Format Definition (YAML template + body format)
## Validation Scripts (bash)
## Pacing Rules
## Density Re-Assessment
## Follow-up Recommendations
```

### Plan File Naming

**Single plan** (≤30 notes): `plan_digest_<source_slug>.md`
- `plan_digest_meshclaw_wiki.md`
- `plan_digest_builder_mcp_user_guide.md`
- `plan_digest_cloud_desktop_user_guide.md`

**Master + sub-plans** (>30 notes, per Step 1e):
- `plan_digest_<source_slug>_master.md` — index hub only (no note tables)
- `plan_digest_<source_slug>_1_<topic>.md` — self-contained sub-plan
- `plan_digest_<source_slug>_2_<topic>.md`
- Example: `plan_digest_aws_lambda_master.md` + `plan_digest_aws_lambda_1_foundations.md` + ...

**Master plan required sections** (subset — index-only):
- Objective, Routing Decision (shared), Format Definition (shared), Sub-Plans Index Table, Execution Order, Entry Points, Cross-References (shared), Validation Gates (shared), Pacing Rules (shared), Summary Statistics, Follow-up Recommendations

**Sub-plan required sections** (full): same as single-plan (all sections from Required Plan Sections above)

---

## Step 7: Present Plan for Approval <!-- :: section_id = step_7_present_plan :: -->

Show the user:
1. Total pages read vs digestible vs excluded
2. Total notes planned (with BB distribution)
3. Density assessment — any over-threshold notes?
4. Key cross-references identified
5. Ask: "Ready to execute? Or modify the plan first?"

If user wants changes, update the plan and re-present.

---

## Step 8: Density Re-Assessment <!-- :: section_id = step_8_density_recheck :: -->

After writing the plan, re-read the source carefully and ask:
- Did we compress too much? Should any note be further split?
- Did we omit any source section?
- Is any note mixing BBs (step-by-step + conceptual explanation)?

If any issue found, update the plan before marking ready.

---

## Important Constraints <!-- :: section_id = important_constraints :: -->

1. **BB atomicity is non-negotiable** — each planned note gets exactly ONE building block type
2. **Density thresholds are hard limits** — plan splits BEFORE writing, not after
3. **Section coverage is complete** — every source section mapped to exactly one note
4. **No duplication of existing notes** — reference them, don't recreate
5. **Plan is the contract** — execution follows the plan; changes require plan update first
6. **Quality over speed** — re-read source if uncertain about density or BB classification
7. **Code blocks MUST be verbatim in plan** — note which source sections have code that must be preserved exactly
8. **Measured, not estimated** — word counts in the Source table MUST come from actual page reads (tool output), never from training knowledge or guesswork. A page not read is a page not measurable. If you cannot read it, mark as "unread — estimate only" and flag for verification during augmentation.

## Error Handling <!-- :: section_id = error_handling :: -->

| Error | Cause | Recovery |
|-------|-------|----------|
| Source returns 404/empty | URL invalid or page deleted | Ask user for correct URL |
| Too many pages (50+) | Very large wiki site | Split into multiple plans by domain; ask user which to prioritize |
| Can't determine BB for a section | Mixed content | Default to the dominant BB; add split decision if >500w of each |
| Existing note covers same content | Duplication risk | Document in plan as "do NOT duplicate"; link instead |
| User disagrees with routing | Subjective choice | Update routing decision per user feedback |
| Word counts seem too low (most pages <1500w) | Pages not actually read — estimated from training knowledge | Go back to Step 1b and WebFetch/Read every page. Record measured word counts. Re-apply Step 3c source-page-level thresholds. This is the #1 cause of under-splitting. |
| Plan delegated to background agent | Agent may skip page reads | Verify Source table word counts against actual page reads during augmentation (Step 2). Flag "unread" pages explicitly. |

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog
