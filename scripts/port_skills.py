#!/usr/bin/env python3
"""
Port skill canonicals from a source vault into this repo, rewriting every path
so they operate on a LOCAL corpus vault and never on the source vault.

The ported skills are committed; this script exists so the adaptation is
reproducible and auditable rather than a pile of hand edits.

    python3 scripts/port_skills.py /path/to/source/vault

What it rewrites
----------------
  config-resolved VAULT_PATH / DB_PATH  ->  $VAULT and $VAULT/notes.db
  update_notes_database.sh              ->  build_local_db.py <vault>
  build_unified_db.py                   ->  build_local_db.py
  search-notes skill invocations        ->  scripts/retrieval.py
  vault-internal wiki links             ->  plain text (no dangling paths)
  vault-only frontmatter fields         ->  removed

What it refuses to do
---------------------
Anything that would leave a path pointing at the source vault. After porting,
every ported skill is checked for residual absolute paths, config imports and
internal tokens; a hit fails the run rather than shipping quietly.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "skills"

# canonical stem -> ported filename
# Deliberately NOT ported:
#   capture-term-note  REWRITTEN by hand at skills/capture-term-note/ rather than
#                      ported: upstream researches internal wikis/docs (forbidden by
#                      the blind-ingestion rule) and routes into pre-existing domain
#                      glossaries (which a fresh corpus does not have).
#   search-notes       superseded by scripts/retrieval.py, which is self-contained
#                      and operates on this repo's own hybrid index.
SKILLS = {
    "skill_slipbox_plan_digestion": "plan-digestion",
    "skill_slipbox_augment_digestion_plan": "augment-digestion-plan",
    "skill_slipbox_review_digestion_plan": "review-digestion-plan",
    "skill_slipbox_execute_digestion_plan": "execute-digestion-plan",
    "skill_slipbox_validate_note_gates": "validate-note-gates",
    "skill_slipbox_check_note_format": "check-note-format",
    "skill_slipbox_check_broken_links": "check-broken-links",
    "skill_slipbox_fix_broken_links": "fix-broken-links",
    "skill_slipbox_fix_ghost_references": "fix-ghost-references",
}

SETUP_BLOCK = """```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```"""


# Injected into every skill that creates or validates notes. The port is the
# only place these are written, so a re-port cannot drift from the scripts.

BB_BLOCK = """## Knowledge Building Blocks (reference)

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
"""

NOTE_CONTRACT = """## Where Notes Go, and What They Must Carry

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

Both are **enforced**, not conventional. `building_block` is what the retrieval
arms stratify on. `source_docs` is what makes the note scorable at all: gold
labels in these benchmarks are passage-level, so a note that cannot name the
documents it came from cannot be credited when it is retrieved. A note without
it is invisible to the evaluation even when it is correct.

`tags`, `keywords`, `topics`, `status`, `language` and `date of note` may be
included and are preserved, but the database does not read them — do not spend
effort on them at the expense of the two fields above.

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
"""

# skills that create or validate notes; link-only skills get neither block
CONTRACT_SKILLS = {"plan-digestion", "augment-digestion-plan", "review-digestion-plan",
                   "execute-digestion-plan", "validate-note-gates", "check-note-format",
                   "fix-ghost-references"}

# (pattern, replacement) applied in order
REWRITES: list[tuple[str, str]] = [
    # kill config-based path resolution wholesale
    (r'SCRIPTS_DIR="?\./scripts"?\n', ""),
    (r'SCRIPTS_DIR=\$\(python3 -c [^\n]+\n', ""),
    (r'VAULT_PATH=\$\(python3 -c [^\n]+\n', ""),
    (r'DB_PATH=\$\(python3 -c [^\n]+\n', ""),
    (r'PACKAGE_DIR=\$\(python3 -c [^\n]+\n', ""),
    # variable references
    (r'\$\{?VAULT_PATH\}?', "$VAULT"),
    (r'\$\{?DB_PATH\}?', "$DB"),
    (r'\$\{?SCRIPTS_DIR\}?', "scripts"),
    # script substitutions -> local equivalents
    (r'bash scripts/update_notes_database\.sh[^\n]*',
     'python3 scripts/build_local_db.py "$VAULT"'),
    (r'python3 scripts/build_unified_db\.py[^\n]*',
     'python3 scripts/build_local_db.py "$VAULT"'),
    (r'python3 scripts/build_notes_database\.py[^\n]*',
     'python3 scripts/build_local_db.py "$VAULT"'),
    (r'scripts/check_note_format\.py', 'scripts/check_note_format.py'),
    (r'python3 scripts/ppr\.py[^\n]*',
     'python3 scripts/retrieval.py "$VAULT" --strategy ppr --query "..."'),
    (r'python3 scripts/(?:bm25|dense|best_first_bfs|ppr)_search\.py[^\n]*',
     'python3 scripts/retrieval.py "$VAULT" --query "..." --strategy hybrid'),
    # plans directory
    (r'\bplans/', 'experiments/plans/'),
    # vault-internal links -> plain text
    (r'\[([^\]]+)\]\((?:\.\./)*(?:resources|areas|projects|archives|0_entry_points)/[^)]+\)', r'\1'),
    (r'\[([^\]]+)\]\(skill_slipbox_[^)]+\)', r'\1'),
    # internal source-fetch tables -> local corpus files
    (r'^\| w\.amazon[^\n]*\n', ''),
    (r'^\| Quip document[^\n]*\n', ''),
    (r'^\| Internal platform docs[^\n]*\n', ''),
    (r'^\| Amazon wiki[^\n]*\n', ''),
    (r'\bReadInternalWebsites\b', 'local file read'),
    (r'w\.amazon\.com[^\s`|)]*', 'the corpus'),
    (r'quip-amazon\.com[^\s`|)]*', 'the corpus'),
    (r'\bQuip\b', 'corpus document'),
    (r'\bBuilderHub\b', 'corpus'),
    # residual db / script names
    (r'abuse_slipbox_unified\.db', '$DB'),
    (r'abuse_slipbox_notes\.db', '$DB'),
    (r'\babuse_slipbox\b', 'corpus vault'),
    (r'bash "?scripts/update_notes_database\.sh"?[^\n]*',
     'python3 scripts/build_local_db.py "$VAULT"'),
    (r'^> \*\*Note\*\*: `config\.py` requires[^\n]*\n', ''),
    (r'`config\.py`', 'the local paths above'),
    # routing tables -> the corpus vault
    (r'resources/documentation/[a-z_<>]+/', '$VAULT/'),
    (r'resources/term_dictionary/', '$VAULT/'),
    (r'\bAmazon buyer abuse prevention\b', 'the corpus domain'),
    (r'entry_buyer_abuse\w*', 'entry_<topic>'),
    (r'\bbuyer_abuse\w*', 'corpus'),
    (r'\bbuyer abuse\b', 'the corpus domain'),
    # every upstream validator/indexer maps onto the two local scripts
    (r'(?:python3\s+|bash\s+)?"?scripts/check_note_format\.py"?[^\n`]*', 'python3 scripts/validate_notes.py "$VAULT"'),
    (r'(?:python3\s+|bash\s+)?"?scripts/check_yaml_frontmatter\.py"?[^\n`]*', 'python3 scripts/validate_notes.py "$VAULT"'),
    (r'(?:python3\s+|bash\s+)?"?scripts/fix_broken_links\.py"?[^\n`]*', 'python3 scripts/validate_notes.py "$VAULT" --fix'),
    (r'(?:python3\s+|bash\s+)?"?scripts/fix_ghost_references\.py"?[^\n`]*', 'python3 scripts/validate_notes.py "$VAULT" --fix'),
    (r'(?:python3\s+|bash\s+)?"?scripts/fz_fix_numbering\.py"?[^\n`]*', 'python3 scripts/validate_notes.py "$VAULT"'),
    (r'(?:python3\s+|bash\s+)?"?scripts/digest_note_gate\.sh"?[^\n`]*', 'python3 scripts/validate_notes.py "$VAULT" --gate'),
    (r'(?:python3\s+|bash\s+)?"?scripts/(?:build_unified_db|build_notes_database)\.py"?[^\n`]*', 'python3 scripts/build_local_db.py "$VAULT"'),
    (r'(?:python3\s+|bash\s+)?"?scripts/update_notes_database\.sh"?[^\n`]*', 'python3 scripts/build_local_db.py "$VAULT"'),
    (r'(?:python3\s+|bash\s+)?"?scripts/(?:bm25|dense)_search\.py"?[^\n`]*', 'python3 scripts/retrieval.py "$VAULT" --query "..." --strategy hybrid'),
    (r'scripts/output/', 'experiments/output/'),
    # BB definitions live in this repo, not in a vault note that was never copied
    (r'`?\$VAULT/\$VAULT/term_knowledge_building_blocks\.md`?', '`docs/BUILDING_BLOCKS.md` (in this repo)'),
    (r'`?\$VAULT/term_knowledge_building_blocks\.md`?', '`docs/BUILDING_BLOCKS.md` (in this repo)'),
    # collapse doubling introduced when a path already carried $VAULT
    (r'(?:\$VAULT/)+(\$VAULT/)', r'\1'),
    # ---- flat corpus vault: the source vault's PARA subtree does not exist here
    (r'`?\$VAULT/resources/(?:documentation|analysis_thoughts|policy_sops|term_dictionary|skills)/[a-z_0-9]*`?',
     r'`$VAULT/`'),
    (r'`(?:resources/)?(?:documentation|analysis_thoughts|policy_sops|term_dictionary)/`', r'`$VAULT/`'),
    (r'`(?:areas|projects|0_entry_points|archives/deep_dive_analysis)/`', r'`$VAULT/`'),
    (r'\| `(sop|thought)_<entity>_<topic>\.md` \| `[^`]*` \|', r'| `\1_<entity>_<topic>.md` | `$VAULT/` (flat) |'),
    (r'parent stays in `[^`]*`', r'parent stays at `$VAULT/term_<name>.md`'),
    (r'`resources/documentation/[A-Za-z_<>/]*wiki_topic_overview\.md`?', r'$VAULT/topic_overview.md'),
    (r'resources/documentation/X/wiki_topic_overview\.md', r'topic_overview.md'),
    (r'"?projects/project_obsolete\.md"?', r'"obsolete_note.md"'),
    (r'`archives/deep_dive_analysis/YYYY-MM-DD_<topic>_execution\.md`',
     r'`experiments/plans/$CORPUS/YYYY-MM-DD_<topic>_execution.md`'),
    # SQL classifier for source-vault path prefixes: meaningless in a flat vault
    (r'(?s)  CASE\n    WHEN broken_path NOT LIKE.*?  END AS error_pattern,',
     "  CASE\n"
     "    WHEN instr(broken_path, '/') > 0\n"
     "    THEN 'has_directory_component'   -- this vault is flat; a slash is itself the bug\n"
     "    WHEN lower(broken_path) = lower(correct_note_id)\n"
     "    THEN 'case_mismatch'\n"
     "    ELSE 'other'\n"
     "  END AS error_pattern,"),
    # upstream ships this YAML template collapsed onto ONE line -- invalid as written
    (r'^language: markdown date of note: <YYYY-MM-DD> status: active.*related_wiki:.*---$',
     "language: markdown\n"
     "date of note: <YYYY-MM-DD>\n"
     "status: active\n"
     "building_block: concept       # MUST be concept for term notes\n"
     "source_docs: [<corpus_doc_id>, ...]   # REQUIRED — see the note contract below\n"
     "---"),
    (r' See `archives/deep_dive_analysis/[^`]*` and\s*`[^`]*`\.',
     r' (The campaign that measured this over-counting is recorded in the source '
     r'vault, not here.)'),
    # ---- generalise source types: the upstream names internal hosts as examples
    (r'\| `?docs\.hub\.amazon\.dev`? \(corpus\) \| `local file read` \| https://docs\.hub\.amazon\.dev/\.\.\. \|',
     r'| Corpus document | `Read` tool | `corpus/<doc_id>.txt` |'),
    (r'\| `?code\.amazon\.com`? \(docs package\) \| `local file read` \| https://code\.amazon\.com[^|]*\|',
     r'| Source repository | `Read` tool | a checked-out path |'),
    (r'\| External URL \| `WebFetch` \| https://docs\.aws\.amazon\.com/\.\.\. \|',
     r'| External URL | `WebFetch` | any public documentation URL |'),
    (r'\|[^|\n]*\(docs\.aws\.amazon\.com\)[^|\n]*\|', r'| External vendor docs |'),
    (r'\|[^|\n]*docs\.hub\.amazon\.dev[^|\n]*\|', r'| Corpus document |'),
    (r'\(docs\.hub\.amazon\.dev\)|docs\.hub\.amazon\.dev', r'the corpus'),
    (r'docs\.aws\.amazon\.com', r'vendor documentation'),
    (r'code\.amazon\.com', r'a source repository'),
    (r'\(host\.amazon\.com/\.\.\.\)', r'(example.com/...)'),
    (r'\bdocs\.hub\b', r'vendor docs'),
    (r'\bMidway\b', r'the authenticated fetch path'),
    (r'\bmidway-gated\b', r'auth-gated'),
    (r'restore the authenticated fetch path / re-run', r'restore auth / re-run'),
    # entry points live flat in this vault -- every remaining form
    (r'`0_entry_points/entry_([a-z_<>]+)\.md`', r'`$VAULT/entry_\1.md`'),
    (r'\$VAULT/resources/(?:term_dictionary|documentation|analysis_thoughts|policy_sops|skills)(?=["\s`])', r'$VAULT'),
    (r'\bterm_midway\b', r'term_example'),
    (r'(?i)buyer[-_ ]abuse', r'the source domain'),
    (r'\$VAULT/0_entry_points/\$\{BEST_FIT_GLOSSARY\}', r'$VAULT/glossary.md'),
    (r'\$VAULT/0_entry_points/<?entry_([a-z_<>]+)\.md>?', r'$VAULT/entry_\1.md'),
    (r'\$VAULT/0_entry_points/', r'$VAULT/'),
    (r"'%0_entry_points%'", r"'entry_%'"),
    (r'`0_entry_points`,', r'`$VAULT`,'),
    (r'`0_entry_points/entry_([a-z_]+)\.md`', r'`$VAULT/entry_\1.md`'),
    (r'`0_entry_points/`', r'`$VAULT/`'),
    # target-directory tables: this vault is flat
    (r'\| `resources/digest/` \|', r'| `$VAULT/` |'),
    (r'\*\*Routing heuristic\*\*.*$',
     r'**Routing**: this vault is flat — every note is written to `$VAULT/<slug>.md` '
     r'and the prefix carries the distinction that a directory would. Run '
     r'`python3 scripts/retrieval.py "$VAULT" --query "<topic>" --strategy hybrid` '
     r'to find where similar content already lives.'),
    (r'> \*\*Corollary\*\*: If a cohesive series will produce >15 notes.*$',
     r'> **Corollary**: A cohesive series shares a filename prefix rather than a '
     r'subfolder, so that a note id stays equal to its filename.'),
    (r'/slipbox-search-notes <topic>', r'scripts/retrieval.py'),
    # frontmatter fields that only mean something in the source vault
    (r'^related_skill_headers:\n(?:  - .*\n)+', ""),
    (r'^access_control_group:.*\n', ""),
    (r'^note_second_category:.*\n', ""),
    (r'^pipeline_metadata:.*\n', ""),
]

# after porting, none of these may remain
FORBIDDEN = [
    r"/Users/", r"github_workspace", r"buyer[-_ ]abuse", r"abuse_slipbox",
    r"amzn_", r"from config import", r"config\.py", r"SLIPBOX_PACKAGE_DIR",
    r"w\.amazon", r"quip", r"slipbot", r"athelas", r"tessellum", r"cursus",
    r"VAULT_PATH_STR", r"DB_PATH_STR",
    r"\$VAULT/\$VAULT", r"term_knowledge_building_blocks",
    r"resources/(?:documentation|analysis_thoughts|policy_sops|term_dictionary|skills)\\b",
    r"archives/deep_dive_analysis", r"language: markdown date of note:",
    r"amazon", r"\bmidway\b", r"isengard", r"\bbrazil\b", r"0_entry_points",
    r"resources/digest",
    r"(?<![a-z])scripts/(?!validate_notes|build_local_db|build_embeddings|retrieval|scrub_check|fetch_benchmarks|port_skills|selftest|output|$| )",
]


def port(text: str, name: str) -> str:
    for pat, rep in REWRITES:
        text = re.sub(pat, rep, text, flags=re.M)
    # inject the local setup block after the Setup heading, or after the H1
    if re.search(r'^## Setup', text, re.M):
        text = re.sub(r'(^## Setup[^\n]*\n\n?)(?:```bash\n.*?```\n)?',
                      r'\1' + SETUP_BLOCK + "\n", text, count=1, flags=re.M | re.S)
    else:
        text = re.sub(r'(^# .+\n)', r'\1\n## Setup\n\n' + SETUP_BLOCK + "\n",
                      text, count=1, flags=re.M)
    if name in CONTRACT_SKILLS:
        anchor = re.search(r'^## (Error Handling|Checklist|Related Entry Point)', text, re.M)
        blocks = NOTE_CONTRACT + "\n" + BB_BLOCK + "\n"
        text = (text[:anchor.start()] + blocks + text[anchor.start():]) if anchor \
            else text.rstrip() + "\n\n" + blocks
    banner = (
        f"\n> **Ported skill.** Adapted from an upstream vault canonical for use in this\n"
        f"> repository. All paths are local: notes live under `vaults/$CORPUS`, the database\n"
        f"> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill\n"
        f"> never reads or writes any vault outside this repo.\n"
    )
    return re.sub(r'(^# .+\n)', r'\1' + banner, text, count=1, flags=re.M)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    src = Path(sys.argv[1])
    if not src.is_dir():
        print(f"no such source vault: {src}")
        sys.exit(2)

    OUT.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    done = 0
    for stem, slug in SKILLS.items():
        f = src / "resources" / "skills" / f"{stem}.md"
        if not f.exists():
            print(f"  [miss] {stem}")
            continue
        ported = port(f.read_text(encoding="utf-8", errors="replace"), slug)
        for pat in FORBIDDEN:
            m = re.search(pat, ported, re.I)
            if m:
                failures.append(f"{slug}: residual {pat!r} -> {m.group(0)!r}")
        d = OUT / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(ported)
        print(f"  [ok  ] {slug:<26} {len(ported.splitlines()):>4} lines")
        done += 1

    print(f"\nported {done} skills -> {OUT.relative_to(ROOT)}")
    if failures:
        print(f"\nFAIL — {len(failures)} residual reference(s) to the source vault:")
        for x in failures[:40]:
            print("  " + x)
        sys.exit(1)
    print("clean — no residual source-vault paths, config imports or internal tokens")


if __name__ == "__main__":
    main()
