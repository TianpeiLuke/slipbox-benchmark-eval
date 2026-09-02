#!/usr/bin/env python3
"""
Validate notes in a corpus vault: frontmatter, structure, links, ghosts.

One script replaces the four the upstream skills call separately
(check_note_format, check_yaml_frontmatter, fix_broken_links,
fix_ghost_references), because they all need the same parse and the same
vault-local link resolution.

    python3 scripts/validate_notes.py vaults/musique
    python3 scripts/validate_notes.py vaults/musique --fix
    python3 scripts/validate_notes.py vaults/musique --gate

Checks
------
  FM-001  missing or malformed YAML frontmatter
  FM-002  required field absent (building_block)
  FM-003  building_block outside the closed enum
  ST-001  no H1
  ST-002  H1 not the first content line
  LN-001  link target does not exist in this vault        (broken)
  LN-002  link escapes the vault                          (contamination)
  GH-001  link target exists nowhere and is never defined (ghost)

--fix repairs LN-001 where a unique case-insensitive basename match exists,
and reports everything it declines to guess at. --gate exits non-zero on any
ERROR, for use before a commit.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^# (.+)$", re.M)
LINK = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)\)")

CLOSED_BB = {"concept", "model", "procedure", "empirical_observation",
             "argument", "counter_argument", "hypothesis", "navigation"}

ERROR, WARN = "ERROR", "WARN"


def parse_fm(text: str) -> dict | None:
    m = FM.match(text)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "-", "\t")):
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def validate(vault: Path, fix: bool) -> list[tuple[str, str, str, str]]:
    notes = sorted(p for p in vault.rglob("*.md") if p.name != "README.md")
    by_name: dict[str, list[Path]] = defaultdict(list)
    existing = set()
    for p in notes:
        existing.add(str(p.relative_to(vault)))
        by_name[p.name.lower()].append(p)

    issues: list[tuple[str, str, str, str]] = []
    for p in notes:
        rel = str(p.relative_to(vault))
        raw = p.read_text(encoding="utf-8", errors="replace")
        fm = parse_fm(raw)
        body = FM.sub("", raw)

        if fm is None:
            issues.append((ERROR, "FM-001", rel, "missing or malformed frontmatter"))
        else:
            bb = fm.get("building_block")
            if not bb:
                issues.append((ERROR, "FM-002", rel, "no building_block"))
            elif bb not in CLOSED_BB:
                issues.append((ERROR, "FM-003", rel, f"building_block {bb!r} not in closed enum"))

        h1 = H1.search(body)
        if not h1:
            issues.append((ERROR, "ST-001", rel, "no H1 heading"))
        else:
            before = body[: h1.start()].strip()
            if before:
                issues.append((WARN, "ST-002", rel, "content precedes the H1"))

        changed = False
        for text_, target in LINK.findall(body):
            if target.startswith(("http://", "https://")):
                continue
            resolved = (p.parent / target).resolve()
            try:
                tid = str(resolved.relative_to(vault.resolve()))
            except ValueError:
                issues.append((ERROR, "LN-002", rel, f"link escapes vault: {target}"))
                continue
            if tid in existing:
                continue
            cands = by_name.get(Path(target).name.lower(), [])
            if len(cands) == 1 and fix:
                new = str(Path(cands[0]).relative_to(p.parent)) if p.parent != cands[0].parent \
                    else cands[0].name
                raw = raw.replace(f"]({target})", f"]({new})")
                changed = True
                issues.append((WARN, "LN-001", rel, f"repaired {target} -> {new}"))
            elif cands:
                issues.append((ERROR, "LN-001", rel, f"broken link {target} ({len(cands)} candidates)"))
            else:
                issues.append((ERROR, "GH-001", rel, f"ghost target {target} exists nowhere"))
        if changed:
            p.write_text(raw, encoding="utf-8")

    return issues


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--gate", action="store_true")
    a = ap.parse_args()

    vault = Path(a.vault)
    if not vault.is_dir():
        print(f"no such vault: {vault}")
        sys.exit(2)

    issues = validate(vault, a.fix)
    n = len(list(vault.rglob("*.md")))
    errs = [i for i in issues if i[0] == ERROR]
    warns = [i for i in issues if i[0] == WARN]

    by_code: dict[str, int] = defaultdict(int)
    for sev, code, _, _ in issues:
        by_code[code] += 1

    print(f"vault {vault} — {n} notes")
    for sev, code, rel, msg in issues[:80]:
        print(f"  {sev:<5} {code}  {rel}: {msg}")
    if len(issues) > 80:
        print(f"  ... and {len(issues) - 80} more")
    print(f"\n{len(errs)} error(s), {len(warns)} warning(s)")
    if by_code:
        print("by code: " + "  ".join(f"{k}={v}" for k, v in sorted(by_code.items())))
    if any(c == "LN-002" for _, c, _, _ in issues):
        print("\nLN-002 present: a link escapes this vault. That is a contamination "
              "signal — the note was written against a different vault. Investigate "
              "before using this corpus.")
    if a.gate and errs:
        sys.exit(1)


if __name__ == "__main__":
    main()
