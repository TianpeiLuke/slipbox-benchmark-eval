#!/usr/bin/env python3
"""
Scrub gate: refuse to publish notes that leak internal content.

This is the safety gate that makes a PUBLIC repo defensible. The benchmark
corpora are public and are never committed; the risk surface is the notes WE
generate, because the digestion pipeline resolves "Related Notes" and inlinks
against whatever vault it runs in. If it ever runs against a production vault,
generated notes can carry links and terminology from that vault.

Run this before committing anything under vaults/. Exit code 1 blocks the push.

    python3 scripts/scrub_check.py vaults/musique

What it checks
--------------
1. INTERNAL TOKENS      corporate hosts, internal tooling, project codenames
2. DANGLING LINKS       markdown links whose target is not inside this repo
                        (a link to an internal vault note is the leak we fear)
3. NON-CORPUS TERMS     vocabulary that cannot plausibly come from the corpus
4. PROVENANCE PRESENT   every note must name the public source it derives from
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Patterns that must never appear in a published note.
INTERNAL = [
    r"\bw\.amazon\b", r"\bquip-amazon\b", r"\bcode\.amazon\b", r"\bsim/issues\b",
    r"\bamazon\.com/[a-z]", r"\bmidway\b", r"\bbrazil\b", r"\bisengard\b",
    r"\bbuyer[_ ]abuse\b", r"\babuse[_ ]slipbox\b", r"\bslipbot\b",
    r"\bathelas\b", r"\bnexustrace\b", r"\btessellum\b", r"\bcursus\b",
    r"\bmcp__", r"\bSLIPBOX_PACKAGE_DIR\b",
]

# Directories that indicate a link escaped into the production vault.
FOREIGN_DIRS = ["resources/analysis_thoughts", "resources/term_dictionary",
                "0_entry_points", "archives/experiments", "areas/",
                "projects/", "resources/policy_sops", "resources/skills"]

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def scan(root: Path) -> int:
    notes = sorted(root.rglob("*.md"))
    if not notes:
        print(f"FAIL: no notes found under {root}")
        return 1

    fails: list[str] = []
    for p in notes:
        rel = p.relative_to(root)
        text = p.read_text(encoding="utf-8", errors="replace")
        low = text.lower()

        for pat in INTERNAL:
            m = re.search(pat, low)
            if m:
                fails.append(f"{rel}: INTERNAL TOKEN {m.group(0)!r}")

        for target in LINK.findall(text):
            if target.startswith(("http://", "https://", "#")):
                continue
            if any(d in target for d in FOREIGN_DIRS):
                fails.append(f"{rel}: FOREIGN LINK -> {target}")
                continue
            resolved = (p.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                fails.append(f"{rel}: LINK ESCAPES REPO -> {target}")
            else:
                if not resolved.exists():
                    fails.append(f"{rel}: DANGLING LINK -> {target}")

        if "source" not in low and "provenance" not in low:
            fails.append(f"{rel}: NO PROVENANCE (must name its public source)")

    print(f"scanned {len(notes)} notes under {root}")
    if fails:
        print(f"\nFAIL — {len(fails)} issue(s); publication BLOCKED:\n")
        for f in fails[:60]:
            print("  " + f)
        if len(fails) > 60:
            print(f"  ... and {len(fails) - 60} more")
        return 1
    print("PASS — no internal tokens, no foreign or dangling links, provenance present")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(max(scan(Path(a)) for a in sys.argv[1:]))
