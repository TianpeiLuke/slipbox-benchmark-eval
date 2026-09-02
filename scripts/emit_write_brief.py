#!/usr/bin/env python3
"""
Emit the writing brief for one cluster: every note, with its source text inline.

An executing agent should not have to rediscover what the plan already decided.
The plan fixed which blocks each note carries; this hands the agent exactly that
text, so it writes from source rather than from a search of its own -- which is
what keeps the note faithful and keeps `source_docs` correct by construction.

    python3 scripts/emit_write_brief.py multihop_rag --cluster c11 --out brief.md

Inlining the source also closes the quarantine at the narrowest point: an agent
given its blocks has no reason to open the corpus at large, and none at all to
go looking for the question file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"
PLANS = ROOT / "experiments" / "plans"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--cluster", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()

    P = PLANS / a.slug
    f = P / "clusters" / f"{a.cluster}.json"
    if not f.exists():
        f = P / f"subplan_{a.cluster}_assignments.json"
        if not f.exists():
            raise SystemExit(f"no plan for {a.cluster}")
        # The assignment file carries blocks but not building blocks; those live in
        # the sub-plan's own table. Emitting an empty bb here silently strips the
        # scoring key from the brief, and an agent copying it faithfully would
        # write 130 unusable notes.
        import re as _re
        md = P / f"subplan_{a.cluster}.md"
        bbmap = {}
        if md.exists():
            for m in _re.finditer(r"\|\s*\d+\s*\|\s*`([^`]+\.md)`[^|]*\|\s*`([a-z_]+)`", md.read_text()):
                bbmap[m.group(1)] = m.group(2)
        missing = [n for n in json.loads(f.read_text()) if n not in bbmap]
        if missing:
            raise SystemExit(f"no building_block for {len(missing)} note(s) in {md.name}: "
                             f"{missing[:3]} — refusing to emit a brief without the scoring key")
        plan = {"subplans": [{"slug": a.cluster, "title": a.cluster,
                              "notes": [{"note": n, "bb": bbmap[n], "blocks": m}
                                        for n, m in json.loads(f.read_text()).items()]}]}
    else:
        plan = json.loads(f.read_text())

    idx = json.loads((CORPUS / a.slug / "index.json").read_text())
    cache: dict[str, list[str]] = {}
    nl = {}
    nlp = P / "note_links.json"
    if nlp.exists():
        nl = json.loads(nlp.read_text())

    out = [f"# Writing brief — {a.cluster}", ""]
    n_notes = 0
    for s in plan["subplans"]:
        out.append(f"## Sub-plan: {s['title']}  (`{s['slug']}`)")
        out.append("")
        for note in s["notes"]:
            n_notes += 1
            docs = sorted(note["blocks"])
            out.append(f"### `{note['note']}`")
            out.append(f"- building_block: `{note['bb']}`")
            out.append(f"- source_docs: [{', '.join(docs)}]")
            rel = nl.get(note["note"], [])
            if rel:
                out.append("- **Related Notes to use** (already chosen by content relevance; "
                           "copy the reason into the note):")
                for r in rel:
                    out.append(f"    - `{r['note']}` — {r['why']}")
            out.append("")
            out.append("SOURCE (write only from this):")
            out.append("")
            for d in docs:
                cache.setdefault(d, [b.strip() for b in
                                     (CORPUS / a.slug / f"{d}.txt").read_text().split("\n\n")
                                     if b.strip()])
                meta = idx[d]
                out.append(f"> **{d}** — {meta['publisher']}, {meta['date'][:10]} — "
                           f"*{meta['title']}*")
                for i in note["blocks"][d]:
                    if i < len(cache[d]):
                        out.append(f">")
                        out.append("> " + cache[d][i].replace("\n", " "))
                out.append("")
    text = "\n".join(out)
    if a.out:
        Path(a.out).write_text(text)
        print(f"{n_notes} notes, {len(text):,} chars -> {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
