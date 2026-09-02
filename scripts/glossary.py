#!/usr/bin/env python3
"""
Create or update a corpus glossary. Bootstraps when none exists.

Upstream assumes a set of domain glossaries already exists and routes each new
term into the best-fitting one. A fresh benchmark corpus has no glossary at
all, so this script starts one on first use and only proposes splitting it
once it is large enough for domains to be visible in the data rather than
guessed in advance.

    python3 scripts/glossary.py vaults/musique --check "Alpha Protocol"
    python3 scripts/glossary.py vaults/musique --add "Alpha Protocol" \\
        --full-name "Alpha Routing Protocol" \\
        --description "..." --note alpha_protocol.md
    python3 scripts/glossary.py vaults/musique --stats

Entries are inserted alphabetically. Adding a term that already exists updates
it in place rather than duplicating it -- dedup is part of the operation, not
a separate step someone can forget.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

SPLIT_THRESHOLD = 150   # below this, one glossary is easier to search than many

HEADER = """---
tags:
  - entry_point
  - index
  - navigation
  - glossary
keywords:
  - glossary
  - terms
  - {corpus}
topics:
  - Corpus Reference
language: markdown
date of note: {today}
status: active
building_block: navigation
---

# Glossary — {corpus}

Terms extracted from the {corpus} corpus. Every entry links to its term note,
and every term note cites the corpus documents it was derived from.

This glossary was created by the first term capture and grows with the corpus.
It stays a single file until it exceeds {threshold} entries, at which point
splitting by domain becomes worthwhile — and by then the domains are visible
in the data instead of guessed in advance.

## Terms

"""

ENTRY = """### {term}
**Full Name**: {full_name}
**Description**: {description}
**Note**: [{term}]({note})
**Source**: {source}

"""


def path_for(vault: Path) -> Path:
    return vault / "glossary.md"


def load(vault: Path) -> str:
    p = path_for(vault)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return HEADER.format(corpus=vault.name, today=date.today().isoformat(),
                         threshold=SPLIT_THRESHOLD)


def entries(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"^### (.+?)$(.*?)(?=^### |\Z)", text, re.M | re.S):
        out[m.group(1).strip()] = m.group(0)
    return out


def write(vault: Path, text: str) -> None:
    path_for(vault).write_text(text, encoding="utf-8")


def add(vault: Path, term: str, full_name: str, description: str,
        note: str, source: str) -> str:
    text = load(vault)
    existing = entries(text)
    block = ENTRY.format(term=term, full_name=full_name or term,
                         description=description, note=note, source=source or "corpus")
    verb = "updated" if term in existing else "added"

    if term in existing:
        text = text.replace(existing[term], block)
    else:
        head, _, tail = text.partition("## Terms\n")
        blocks = entries(tail)
        blocks[term] = block
        body = "".join(blocks[k] for k in sorted(blocks, key=str.lower))
        text = head + "## Terms\n\n" + body
    write(vault, text)
    return verb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--check")
    ap.add_argument("--add")
    ap.add_argument("--full-name", default="")
    ap.add_argument("--description", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    vault = Path(a.vault)
    if not vault.is_dir():
        print(f"no such vault: {vault}")
        sys.exit(2)

    if a.check:
        found = entries(load(vault))
        hit = [t for t in found if t.lower() == a.check.lower()]
        near = [t for t in found
                if t.lower() != a.check.lower()
                and (a.check.lower() in t.lower() or t.lower() in a.check.lower())]
        if hit:
            print(f"EXISTS: {hit[0]} — update it, do not create a duplicate")
            sys.exit(1)
        if near:
            print(f"NEAR MATCH: {', '.join(near[:5])}")
            print("Resolve before creating: same concept under another name, or genuinely distinct?")
            sys.exit(1)
        print(f"NEW: {a.check!r} is not in the glossary")
        return

    if a.add:
        if not a.description:
            print("--description required")
            sys.exit(2)
        if not path_for(vault).exists():
            print(f"no glossary yet — bootstrapping {path_for(vault)}")
        verb = add(vault, a.add, a.full_name, a.description, a.note, a.source)
        n = len(entries(load(vault)))
        print(f"{verb}: {a.add}  ({n} entries)")
        if n > SPLIT_THRESHOLD:
            print(f"\n{n} entries exceeds {SPLIT_THRESHOLD}: consider splitting by "
                  f"domain. Cluster the existing terms first — split on domains "
                  f"visible in the corpus, never on a schema decided up front.")
        return

    if a.stats or True:
        p = path_for(vault)
        if not p.exists():
            print(f"no glossary at {p} — it is created by the first term capture")
            return
        found = entries(load(vault))
        print(f"glossary {p}\nentries  {len(found)}")
        missing = [t for t, b in found.items() if "**Note**: []" in b or "**Note**: \n" in b]
        if missing:
            print(f"entries with no term note: {len(missing)}")


if __name__ == "__main__":
    main()
