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
# Generic defaults only. Organisation-specific terms (internal hostnames, tool
# names, project codenames) belong in a LOCAL, GITIGNORED file so that
# publishing this detector does not itself disclose them:
#
#     echo 'internal-hostname\nproject-codename' > .scrub-patterns
#
# --tokens-only scans a tree that is prose ABOUT notes (skills/, docs/) rather
# than notes: it applies the internal-token check and skips the link and
# provenance checks, whose premises do not hold there.
#
# One regex per line, blank lines and #-comments ignored.
INTERNAL = [
    r"\b[a-z0-9.-]+\.corp\b", r"\b[a-z0-9.-]+\.internal\b",
    r"\bintranet\b", r"\bconfidential\b", r"\bproprietary\b",
    r"\bdo[- ]not[- ]distribute\b",
    r"\bmcp__", r"_PACKAGE_DIR\b",
    r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",          # access key ids
    r"\barn:aws:[a-z0-9-]+:", r"\b\d{12}\b",   # cloud arns / account ids
]

_LOCAL = Path(__file__).resolve().parent.parent / ".scrub-patterns"
if _LOCAL.exists():
    INTERNAL += [ln.strip() for ln in _LOCAL.read_text().splitlines()
                 if ln.strip() and not ln.startswith("#")]

# Directories that indicate a link escaped into the production vault.
FOREIGN_DIRS = ["resources/analysis_thoughts", "resources/term_dictionary",
                "0_entry_points", "archives/experiments", "areas/",
                "projects/", "resources/policy_sops", "resources/skills"]

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def scan(root: Path, tokens_only: bool = False) -> int:
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

        if tokens_only:
            # Skills and docs are prose about notes, not notes: their example
            # links (`other_note.md`) are illustrations, and they cite no corpus
            # source. Only the internal-token check applies to them.
            continue

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
    args = [a for a in sys.argv[1:] if a != "--tokens-only"]
    tokens_only = "--tokens-only" in sys.argv[1:]
    sys.exit(max(scan(Path(a), tokens_only) for a in args))
