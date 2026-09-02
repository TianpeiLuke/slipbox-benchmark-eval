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
    # frontmatter fields that only mean something in the source vault
    (r'^related_skill_headers:\n(?:  - .*\n)+', ""),
    (r'^access_control_group:.*\n', ""),
    (r'^note_second_category:.*\n', ""),
    (r'^pipeline_metadata:.*\n', ""),
]

# after porting, none of these may remain
FORBIDDEN = [
    r"/Users/", r"github_workspace", r"buyer_abuse", r"abuse_slipbox",
    r"amzn_", r"from config import", r"config\.py", r"SLIPBOX_PACKAGE_DIR",
    r"w\.amazon", r"quip", r"slipbot", r"athelas", r"tessellum", r"cursus",
    r"VAULT_PATH_STR", r"DB_PATH_STR",
    r"\$VAULT/\$VAULT", r"term_knowledge_building_blocks",
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
