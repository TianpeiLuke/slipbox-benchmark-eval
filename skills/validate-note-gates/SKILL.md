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

Or invoke `/slipbox-check-note-format`. Fix every **error** before proceeding (common false positive: a scheme-less URL like `(host.amazon.com/...)` in a markdown link is flagged LINK-001 — prefix `https://`). **Do not run the DB update until all new notes pass G1 with 0 errors.**

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
VALIDATION GATES: PASS  (G1 format ✓ | G2 broken ✓ | G3 ghost ✓)
```

or, if any gate fails after remediation attempts:

```
VALIDATION GATES: FAIL  (G1 ✓ | G2 ✓ | G3 ✗ — <N> ghost ref(s) in <note>)
```

On FAIL, do not declare the parent note-authoring task done — surface the failing gate and the offending note(s).

## Important Constraints <!-- :: section_id = important_constraints :: -->

1. **All three gates are mandatory** — a note-authoring task is not complete until G1, G2, and G3 all pass for every new note.
2. **Ordering is fixed** — G1 before the DB update (format is file-level); G2/G3 after (they read rebuilt tables).
3. **Scope to the new notes** — vault-wide pre-existing broken/ghost debt is not this gate's responsibility; only the calling skill's notes must be clean to pass.
4. **Single source of truth** — capture/digest skills invoke this skill rather than re-implementing the sequence; edit the gate here, once.
5. **Explicit verdict required** — always emit the `VALIDATION GATES: PASS/FAIL` line so the caller can self-check.

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog — full vault skill index, organized by C.O.D.E. stage; this skill's row in the catalog has a back-link to this canonical body
