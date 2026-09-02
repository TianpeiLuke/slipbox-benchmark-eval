---
tags:
  - resource
  - skill
  - procedure
  - organize
  - knowledge-management
keywords:
  - fix ghost references
  - detect ghost references
  - slipbox-fix-ghost-references
  - in-vault skill canonical
topics:
  - Skill Procedures
  - Vault Tools
language: markdown
date of note: 2026-06-17
status: active
building_block: procedure
---

# Procedure: slipbox-fix-ghost-references (Canonical Body)

> **Ported skill.** Adapted from an upstream vault canonical for use in this
> repository. All paths are local: notes live under `vaults/$CORPUS`, the database
> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill
> never reads or writes any vault outside this repo.

This is the **single canonical body** for the `slipbox-fix-ghost-references` skill (FZ 12a). The thin headers under `.claude/skills/slipbox-fix-ghost-references/SKILL.md` and `.kiro/skills/slipbox-fix-ghost-references/SKILL.md` point an invoking agent here for the procedural content; only the format-specific frontmatter + ecosystem-required headers live in those thin shims.

## Skill description <!-- :: section_id = skill_description :: -->

Detect and fix ghost references across the whole vault. A ghost reference is a markdown link whose target file does not exist on disk (distinct from a broken link, which points to the wrong relative path of a file that DOES exist — use `/slipbox-fix-broken-links` for those). Runs `fix_ghost_references.py --detect` to report every ghost with ranked redirect candidates, the agent decides **redirect** (repoint to a real note) or **drop** (de-link, keep visible text) per ghost via two-sided verification, then applies the decisions and verifies with a database rebuild. Use when a database update reports `ghosts > 0` or for periodic vault health checks.

## Setup <!-- :: section_id = setup :: -->

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```


## Resources <!-- :: section_id = resources :: -->

- **Database**: `$DB`
- **Detect/fix script**: `python3 scripts/validate_notes.py "$VAULT" --fix`
- **Build script**: `python3 scripts/build_local_db.py "$VAULT"`

## Ghost vs Broken (disambiguation) <!-- :: section_id = ghost_vs_broken_disambiguation :: -->

| | Ghost reference | Broken link |
|---|---|---|
| **Target file** | Does **not** exist on disk | **Exists**, but the relative path is wrong |
| **DB table** | `ghost_notes` + `ghost_note_references` | `broken_links` |
| **Fix** | Redirect to a real note, or drop the link | Rewrite the relative path |
| **Skill** | `/slipbox-fix-ghost-references` (this skill) | `/slipbox-fix-broken-links` |

## Database Schema (quick reference) <!-- :: section_id = database_schema_quick_reference :: -->

- **`ghost_notes`**: one row per missing target — `ghost_note_id` (relative path), `ghost_note_name`, `ghost_note_location`, `ghost_note_category`, `referenced_by_count`.
- **`ghost_note_references`**: one row per source→ghost link — `ghost_note_id`, `source_note_id`, `link_text`, `link_context`.

## Steps <!-- :: section_id = steps :: -->

### 1. Detect ghosts <!-- :: section_id = 1_detect_ghosts :: -->

```bash
sqlite3 $DB "SELECT COUNT(*) AS total_ghosts FROM ghost_notes;"
```

If 0, report "No ghost references found" and stop. Otherwise generate the report (markdown for reading + JSON for programmatic use):

```bash
python3 scripts/validate_notes.py "$VAULT" --fix
```

The report lists each ghost, every source note that links to it (with `link_text` and `link_context`), and **ranked redirect candidates** (real notes whose filename/slug is similar — this surfaces obvious rename targets such as `term_bcce.md` → `term_bcce_buyer_code_of_conduct_enforcements.md`).

> ⚠️ **The script's filename-similarity candidates are a FIRST PASS only, never the decision.** Past resolution campaigns proved that naive string similarity over-counts redirect targets by ~13× (a 0.88 ratio match flagged 472 "renames" where component/canonical-aware matching found only ~36 real ones): short acronyms 1 char apart (`term_nr`≠`term_dnr`, `term_sota`≠`term_sopa`), career levels (`_i_`≠`_ii_`), versioned rulesets, and sibling models (`model_pda_xgboost`≠`model_ida_xgboost`) all score high but are **distinct concepts**. You MUST run the hybrid semantic search in Step 2 and confirm same-sense by reading the candidate — do not redirect on filename score alone. See `archives/deep_dive_analysis/2026-06-13_ghost_note_wrong_name_vs_missing_analysis.md` and `..._2026-06-15_ghost_note_triage_review.md`.

### 2. Hybrid candidate search + two-sided verification <!-- :: section_id = 2_hybrid_candidate_search_two_sided_verification :: -->

For each ghost (or, for large batches, **dispatch one agent per ~8 ghosts** — the proven fan-out from the 2026-06-15 triage campaign), find the closest same-topic note using a **hybrid strategy**, then verify both sides before deciding. The filename candidates from Step 1 seed this; they do not replace it.

**2a. Recover intended sense (source side).** Read the ghost's `link_text` + `link_context` for every referrer (they may differ across sources). This is *what the author meant* — the target you search for.

**2b. Hybrid search for a same-topic destination.** Run all three layers, scoped first to the ghost's own namespace, then to `term_dictionary/`:

```bash
# Layer 1 — filesystem / slug variants (exact, separator, acronym↔expansion, singular↔plural)
ls "$VAULT/<ghost_namespace>/" | grep -iE "<slug>|<acronym>|<expansion>"
# Layer 2 — lexical (BM25 over body text)
python3 scripts/retrieval.py "$VAULT" --query "..." --strategy hybrid
# Layer 3 — dense semantic (embedding nearest-neighbors; finds same concept under a different name)
python3 scripts/retrieval.py "$VAULT" --query "..." --strategy hybrid
```

Add `--subcategory <type>` (e.g. `terminology`, `team`) to focus the search. The dense layer is what catches a same-concept note named completely differently — the case filename similarity always misses.

**2c. Confirm same-sense (target side).** Read the top candidate note(s). Open the H1/Definition and confirm it is the **same concept** the referrer meant — not just a string or acronym neighbor. Reject same-acronym/sibling traps.

**2d. Adversarially verify** every REDIRECT (especially low-confidence) and every CAPTURE/defer, as the triage campaign did with a dedicated skeptic. Ask: *for a redirect* — is this a same-acronym or sibling-concept trap rather than the same note? *for a capture* — does a note already exist (→ redirect instead), or is this too-general/incidental (→ drop)? **Default to the safer verdict and never fabricate** (prefer DROP over a speculative CAPTURE).

Classify each ghost into one of three verdicts (observed distribution from 924 triaged ghosts: ~47% drop, ~36% redirect, ~15% capture — so **drop and redirect dominate; treat capture as the exception, not the default**):

| Verdict | When | Action |
|---------|------|--------|
| **redirect** | A real note is confirmed same-sense (rename, acronym↔full-name, variant spelling, moved file, or same concept under a different name found via dense search) | repoint every referrer to that `target_note_id` (Steps 3–5) |
| **drop** | Too general / malformed slug / wrong-namespace with no target / incidental / unsourced mention — no note represents it | de-link — strip the markdown link wrapper, keep the visible text |
| **defer → capture** | A genuine knowledge gap worth authoring (real dataset/table/team/model/concept referenced but never documented) | leave it; chain to the right capture skill; skip in the decisions file |

**Heuristics carried from the campaigns:**
- **Same-sense before redirect** — never redirect on a shared acronym or sibling name without reading the candidate (`term_seller_abuse`≠`term_reseller_abuse`).
- **Per-reference context** — an acronym-collision ghost (e.g. `term_bcce.md`) may redirect *different sources to different targets*; verify `link_context` per referrer.
- **Capture skews** to `data_sources`, `tables`/`staging_tables`, `teams`, `models` (real schemas/orgs/models); **drop skews** to `0_entry_points`, `areas`, `resources` (planned-but-unbuilt hubs, superseded sub-notes, one-off mentions).
- **Conflict-safe slugs + ghost-inbound-resolution** — if a ghost is deferred to capture, the new note's slug must match the inbound link (or the inbound links get redirected to the canonical slug) so the ghost actually resolves after authoring.

### 3. Write the decisions file <!-- :: section_id = 3_write_the_decisions_file :: -->

Record confirmed decisions as JSON (only `redirect`/`drop`; omit deferred ghosts):

```json
{
  "resolutions": [
    {"ghost_note_id": "$VAULT/term_bcce.md",
     "action": "redirect",
     "target_note_id": "$VAULT/term_bcce_buyer_code_of_conduct_enforcements.md"},
    {"ghost_note_id": "projects/project_obsolete.md", "action": "drop"}
  ]
}
```

Save to e.g. `experiments/output/ghost_decisions.json`.

### 4. Dry run <!-- :: section_id = 4_dry_run :: -->

```bash
python3 scripts/validate_notes.py "$VAULT" --fix
```

The script rewrites only links whose target does not resolve on disk (working links are never touched). Present the summary and ask the user for confirmation before applying.

### 5. Apply fixes <!-- :: section_id = 5_apply_fixes :: -->

```bash
python3 scripts/validate_notes.py "$VAULT" --fix
```

### 6. Rebuild database <!-- :: section_id = 6_rebuild_database :: -->

```bash
python3 scripts/build_local_db.py "$VAULT"
```

### 7. Verify <!-- :: section_id = 7_verify :: -->

```bash
sqlite3 $DB "SELECT COUNT(*) AS remaining_ghosts FROM ghost_note_references;"
```

Report ghosts redirected, ghosts dropped, ghosts deferred (with capture recommendations), files modified, and remaining ghost references (should be the deferred count only).

## Important Constraints <!-- :: section_id = important_constraints :: -->

0. **No ghosts → no edits (NO-OP).** If Step 1 reports `total_ghosts = 0`, STOP immediately — report "No ghost references found" and make **zero** file modifications. The skill must never touch a vault note when there is nothing to fix. (The script enforces this: `--detect` returns early on 0 ghosts and writes no note; `--apply` refuses an empty `resolutions` list; and `rewrite_source` only ever rewrites a link whose target does **not** resolve on disk — working links are never modified.)
1. **Never drop a link whose concept deserves a note** — defer and recommend a capture skill instead, so knowledge is not silently lost.
2. **Redirect requires an existing target** — the script skips any `redirect` whose `target_note_id` does not exist on disk.
3. **Per-reference context matters** — for acronym-collision ghosts, different source notes may redirect to different targets; verify `link_context` per reference, not once for the whole ghost.
4. **Always dry-run** (Step 4) and confirm before applying.
5. **Always rebuild** the database (Step 6) so the `ghost_notes`/`ghost_note_references` tables reflect the post-fix state.
6. **Drop preserves visible text** — de-linking removes the markdown link wrapper (the brackets and parentheses) but keeps the words the author wrote.

## Edge Cases <!-- :: section_id = edge_cases :: -->

### Source note links the ghost multiple times <!-- :: section_id = source_note_links_the_ghost_multiple_times :: -->

The script rewrites every matching, non-resolving occurrence in the source — all are redirected/dropped consistently.

### Ghost referenced by many source notes <!-- :: section_id = ghost_referenced_by_many_source_notes :: -->

A single resolution entry fans out to all referencing sources. If some sources mean a different target, split into multiple runs with per-source decisions (edit the references, or run apply once per target subset).

### The right fix is to create the note <!-- :: section_id = the_right_fix_is_to_create_the_note :: -->

Defer the ghost (omit from the decisions file) and chain to the relevant capture skill (`/slipbox-capture-term-note`, `/slipbox-capture-team-note`, etc.). The ghost resolves naturally once the real note exists and the DB is rebuilt.

### Overlap with ghost *term* matches <!-- :: section_id = overlap_with_ghost_term_matches :: -->

For ghosts confined to `term_dictionary/` that need deep acronym↔full-name reasoning, `/slipbox-resolve-ghost-term-matches` offers a term-specialized two-sided workflow. This skill is the general, all-directory detect+fix tool (redirect or drop) for ghosts of any note type.

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

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog — full vault skill index, organized by C.O.D.E. stage; this skill's row in the catalog has a back-link to this canonical body
