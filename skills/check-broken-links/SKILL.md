---
tags:
  - resource
  - skill
  - procedure
  - organize
  - knowledge-management
keywords:
  - check broken links
  - slipbox-check-broken-links
  - in-vault skill canonical
topics:
  - Skill Procedures
  - Vault Tools
language: markdown
date of note: 2026-04-28
status: active
building_block: procedure
---

# Procedure: slipbox-check-broken-links (Canonical Body)

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

This is the **single canonical body** for the `slipbox-check-broken-links` skill (FZ 12a). The thin headers under `.claude/skills/slipbox-check-broken-links/SKILL.md` and `.kiro/skills/slipbox-check-broken-links/SKILL.md` point an invoking agent here for the procedural content; only the format-specific frontmatter + ecosystem-required headers live in those thin shims.

## Skill description <!-- :: section_id = skill_description :: -->

Check and report broken links in the vault. Queries the database for links with wrong relative paths, groups them by error pattern, source, and target. Read-only — does not modify any files. Use after a database rebuild or for periodic vault health checks.

## Resources <!-- :: section_id = resources :: -->

```bash

```

- **Database**: `$DB`

## Steps <!-- :: section_id = steps :: -->

### 1. Query broken link count <!-- :: section_id = 1_query_broken_link_count :: -->

```bash
sqlite3 $DB "SELECT COUNT(*) AS total_broken FROM broken_links;"
```

If 0, report "No broken links found" and stop.

### 2. Analyze by error pattern <!-- :: section_id = 2_analyze_by_error_pattern :: -->

```bash
sqlite3 -header -column $DB "
SELECT
  CASE
    WHEN instr(broken_path, '/') > 0
    THEN 'has_directory_component'   -- this vault is flat; a slash is itself the bug
    WHEN lower(broken_path) = lower(correct_note_id)
    THEN 'case_mismatch'
    ELSE 'other'
  END AS error_pattern,
  COUNT(*) AS link_count,
  COUNT(DISTINCT source_note_id) AS affected_files
FROM broken_links
GROUP BY error_pattern
ORDER BY link_count DESC;
"
```

### 3. Analyze by source and target <!-- :: section_id = 3_analyze_by_source_and_target :: -->

```bash
sqlite3 -header -column $DB "
SELECT source_note_id, COUNT(*) AS broken_count
FROM broken_links GROUP BY source_note_id
ORDER BY broken_count DESC LIMIT 20;
"

sqlite3 -header -column $DB "
SELECT bl.correct_note_id, n.note_name, COUNT(*) AS broken_ref_count
FROM broken_links bl JOIN notes n ON n.note_id = bl.correct_note_id
GROUP BY bl.correct_note_id ORDER BY broken_ref_count DESC LIMIT 15;
"
```

### 4. Show full details <!-- :: section_id = 4_show_full_details :: -->

```bash
sqlite3 -header -column $DB "
SELECT source_note_id AS source, broken_path AS broken,
       correct_note_id AS correct, link_text
FROM broken_links ORDER BY correct_note_id, source_note_id;
"
```

### 5. Present analysis <!-- :: section_id = 5_present_analysis :: -->

Present error pattern summary, most affected sources/targets, detailed breakdown by pattern, and suggest `/slipbox-fix-broken-links` to apply fixes.

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog — full vault skill index, organized by C.O.D.E. stage; this skill's row in the catalog has a back-link to this canonical body
