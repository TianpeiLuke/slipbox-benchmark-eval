---
tags:
  - resource
  - skill
  - procedure
  - organize
  - knowledge-management
keywords:
  - fix broken links
  - slipbox-fix-broken-links
  - in-vault skill canonical
topics:
  - Skill Procedures
  - Vault Tools
language: markdown
date of note: 2026-04-28
status: active
building_block: procedure
---

# Procedure: slipbox-fix-broken-links (Canonical Body)

> **Ported skill.** Adapted from an upstream vault canonical for use in this
> repository. All paths are local: notes live under `vaults/$CORPUS`, the database
> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill
> never reads or writes any vault outside this repo.

## Setup

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```

This is the **single canonical body** for the `slipbox-fix-broken-links` skill (FZ 12a). The thin headers under `.claude/skills/slipbox-fix-broken-links/SKILL.md` and `.kiro/skills/slipbox-fix-broken-links/SKILL.md` point an invoking agent here for the procedural content; only the format-specific frontmatter + ecosystem-required headers live in those thin shims.

## Skill description <!-- :: section_id = skill_description :: -->

Fix broken links in the vault by correcting wrong relative paths. Runs /slipbox-check-broken-links first to show the analysis, then applies fixes using fix_broken_links.py and verifies with a database rebuild. Use when the user wants to fix (not just report) broken links.

## Resources <!-- :: section_id = resources :: -->

```bash

```

- **Database**: `$DB`
- **Fix script**: `python3 scripts/validate_notes.py "$VAULT" --fix`
- **Build script**: `python3 scripts/build_local_db.py "$VAULT"`

## Steps <!-- :: section_id = steps :: -->

### 1. Check broken links <!-- :: section_id = 1_check_broken_links :: -->

Run `/slipbox-check-broken-links` first to show the analysis report. If 0 broken links, stop.

### 2. Dry run <!-- :: section_id = 2_dry_run :: -->

```bash
python3 scripts/validate_notes.py "$VAULT" --fix
```

Present summary and ask user for confirmation before applying.

### 3. Apply fixes <!-- :: section_id = 3_apply_fixes :: -->

```bash
python3 scripts/validate_notes.py "$VAULT" --fix
```

### 4. Rebuild database <!-- :: section_id = 4_rebuild_database :: -->

```bash
python3 scripts/build_local_db.py "$VAULT"
```

### 5. Verify <!-- :: section_id = 5_verify :: -->

```bash
sqlite3 $DB "SELECT COUNT(*) AS remaining_broken FROM broken_links;"
```

Report links fixed, files modified, and remaining broken links (if any).

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog — full vault skill index, organized by C.O.D.E. stage; this skill's row in the catalog has a back-link to this canonical body
