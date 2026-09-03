#!/usr/bin/env python3
"""Materialise the evidence-backed term links (term_links.json) into the vault,
and build the corpus glossary.

term_links.json maps note -> [term_key] (a term links to a note when the term's
surface forms occur in that note's OWN source blocks -- corpus evidence, floor 3,
no fabricated edges). build_local_db.py builds the graph only from markdown links
and symmetrises them (the graph is undirected), so writing each edge ONCE, inside
the term note, produces the identical graph as editing every referencing content
note -- at a fraction of the blast radius. No content note is modified.

Reuse: a term whose canonical definition already exists as a content note (e.g.
digital_services_act) has no term_<key>.md; its edges are written into that
existing note instead, and the glossary points there.

Run AFTER term-note capture, BEFORE the final DB rebuild.
"""
from __future__ import annotations
import glob, json, os, re, sys

VAULT = "vaults/multihop_rag"
PLANS = "experiments/plans/multihop_rag"
TERMS = json.load(open(f"{PLANS}/terms.json"))
TERM_LINKS = json.load(open(f"{PLANS}/term_links.json"))     # note -> [term_key]
REUSE_FILE = f"{PLANS}/term_reuse.json"                       # committed: term_key -> canonical note it reuses

FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^# (.+)$", re.M)
SEC = "## Corpus References"

def safe(text):
    """Markdown link text must not contain [ or ] (nested brackets break the link
    parser; the film '[REC]' is the corpus case)."""
    return text.replace("[", "").replace("]", "").strip()

# reuse map: a term whose canonical definition already exists as a content note
# (dedup, e.g. digital_services_act) has no term_<key>.md; its edges + glossary
# entry point at that existing note instead.
REUSE = json.load(open(REUSE_FILE)) if os.path.exists(REUSE_FILE) else {}

def title_of(fn):
    p = os.path.join(VAULT, fn)
    if not os.path.exists(p): return None
    m = H1.search(open(p, encoding="utf-8", errors="replace").read())
    return m.group(1).strip() if m else fn[:-3]

def definition_of(fn):
    txt = open(os.path.join(VAULT, fn), encoding="utf-8", errors="replace").read()
    m = re.search(r"## Definition\s*\n(.*?)(?:\n## |\Z)", txt, re.S)
    if not m:  # fall back to first body paragraph
        h = H1.search(txt); body = txt[h.end():] if h else txt
        m2 = re.search(r"\n([^\n#].+)", body)
        blurb = m2.group(1) if m2 else ""
    else:
        blurb = m.group(1)
    blurb = re.sub(r"\s+", " ", blurb).strip()
    return (blurb[:300].rsplit(" ", 1)[0] + "…") if len(blurb) > 300 else blurb

def target_note(term_key):
    tf = f"term_{term_key}.md"
    if os.path.exists(os.path.join(VAULT, tf)): return tf
    if term_key in REUSE and os.path.exists(os.path.join(VAULT, REUSE[term_key])):
        return REUSE[term_key]
    return None

def existing_links(txt):
    return set(re.findall(r"\]\(([^)]+\.md)\)", txt))

def main():
    # invert: term_key -> [referencing content notes that exist]
    inv = {}
    for note, keys in TERM_LINKS.items():
        if not os.path.exists(os.path.join(VAULT, note)):
            continue
        for k in keys:
            inv.setdefault(k, set()).add(note)

    written = edges = skipped = 0
    missing = []
    glossary_rows = []
    for term_key in sorted(TERMS):
        tgt = target_note(term_key)
        refs = sorted(inv.get(term_key, []))
        if tgt is None:
            if refs:  # has edges but no note to hang them on
                missing.append(term_key)
            continue
        # glossary entry (skip only if the term note truly absent)
        gtitle = title_of(tgt) or term_key
        gdesc = definition_of(tgt)
        glossary_rows.append((gtitle, tgt, gdesc))

        if not refs:
            continue
        path = os.path.join(VAULT, tgt)
        txt = open(path, encoding="utf-8", errors="replace").read()
        # idempotent: strip any previously-materialised Corpus References block
        txt = re.sub(r"\n## Corpus References\n.*?(?=\n## |\Z)", "\n", txt, flags=re.S)
        have = existing_links(txt)
        new = [n for n in refs if n not in have and n != tgt]
        if not new:
            open(path, "w", encoding="utf-8").write(txt)
            continue
        rows = "\n".join(f"- [{safe(title_of(n))}]({n})" for n in new)
        block = (f"\n{SEC}\n\nCorpus notes whose source text references this term "
                 f"(evidence-backed, from `term_links.json`):\n\n{rows}\n")
        # insert before ## Source if present, else append
        idx = txt.find("\n## Source")
        txt = (txt[:idx] + block + txt[idx:]) if idx != -1 else (txt.rstrip() + "\n" + block)
        open(path, "w", encoding="utf-8").write(txt)
        written += 1; edges += len(new)

    # build glossary.md (navigation) — gives every term note an inbound link
    lines = ["---", "building_block: navigation", "---", "",
             "# MultiHop-RAG Corpus Glossary", "",
             f"Alphabetical index of {len(glossary_rows)} term notes derived from the "
             "corpus. Navigation only.", "", "## Terms", ""]
    for title, tgt, desc in sorted(glossary_rows, key=lambda r: r[0].lower()):
        lines.append(f"- [{safe(title)}]({tgt}): {desc}")
    lines += ["", "## Related Notes", "",
              "- [MultiHop-RAG Corpus](entry_multihop_rag.md): the corpus root index.", ""]
    open(os.path.join(VAULT, "glossary.md"), "w", encoding="utf-8").write("\n".join(lines))

    print(f"term notes updated with references: {written}")
    print(f"term->content edges written: {edges}")
    print(f"glossary entries: {len(glossary_rows)}")
    if missing:
        print(f"WARN: {len(missing)} terms have edges but no note on disk (not written / not reused): {missing}")

if __name__ == "__main__":
    main()
