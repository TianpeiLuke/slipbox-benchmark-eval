#!/usr/bin/env python3
"""
Fill each note's curated frontmatter: tags, keywords, topics, language, status, date.

The split follows the agent/program boundary used everywhere else here. A
program can derive everything that is a FACT about the note -- its P.A.R.A.
class, the category of the documents it came from, the concepts it links to,
the terms that distinguish it from every other note. It cannot decide what a
reader would call the note, which is the part keywords exist for.

So this derives candidates from evidence and marks what it could not settle:

  tags      P.A.R.A. class from the building block, plus the corpus category
  topics    from the cluster the note's source documents belong to
  keywords  title terms + linked term notes + distinctive tf-idf terms from the
            note's own text, deduplicated and ordered by how discriminating
            they are
  language  markdown
  status    active
  date      the note's file mtime, as the honest record of when it was written

    python3 scripts/revise_frontmatter.py multihop_rag --vault vaults/multihop_rag
    python3 scripts/revise_frontmatter.py multihop_rag --vault ... --dry-run

Keywords derived this way are a floor, not a ceiling. They are the vocabulary
the note actually uses; a curator adds the vocabulary a QUESTIONER would use,
which is not always the same and is exactly what a script cannot know.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^# (.+)$", re.M)
WORD = re.compile(r"[A-Za-z][A-Za-z0-9\-']{2,}")

STOP = set("""the and for that with this from have has had was were been are you your their
they them its it will would could should about into over under after before more most some
such than then there here when what which who whom while also just only said says say new
one two three first last year years time told according but not all any can may might must
our out per via etc other another each both many much very own same too how why where
because during through against between among within without across behind beyond""".split())

PARA_FOR_BB = {"navigation": "entry_point"}   # everything else is a resource


def read_fm(text: str) -> tuple[dict, str]:
    m = FM.match(text)
    if not m:
        return {}, text
    out, key = {}, None
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "-", "\t")):
            k, _, v = line.partition(":")
            key = k.strip()
            out[key] = v.strip()
        elif key and re.match(r"^\s*-\s+", line):
            out.setdefault(f"_{key}", []).append(
                re.sub(r"^\s*-\s+", "", line).strip().strip("\"'"))
    return out, text[m.end():]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--vault")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keywords", type=int, default=6)
    a = ap.parse_args()

    V = Path(a.vault or f"vaults/{a.slug}")
    P = ROOT / "experiments" / "plans" / a.slug

    # category per source document, from the corpus itself
    raw = json.loads((ROOT / "data" / "raw" / a.slug / "corpus.json").read_text())
    cat = {f"doc_{i:04d}": d.get("category", "general") for i, d in enumerate(raw)}

    tl = json.loads((P / "term_links.json").read_text()) if (P / "term_links.json").exists() else {}

    con = sqlite3.connect(V / "notes.db")
    rows = con.execute(
        "SELECT note_id, title, body, building_block, source_doc FROM notes").fetchall()
    con.close()

    # document frequency over the whole vault, so keywords are DISCRIMINATING
    df: Counter = Counter()
    toks: dict[str, Counter] = {}
    for nid, title, body, _bb, _s in rows:
        c = Counter(w.lower() for w in WORD.findall(f"{title} {body}")
                    if w.lower() not in STOP)
        toks[nid] = c
        df.update(c.keys())
    N = len(rows)

    written = skipped = 0
    for nid, title, body, bb, src in rows:
        f = V / nid
        if not f.exists():
            continue
        text = f.read_text()
        fm, rest = read_fm(text)

        docs = [d.strip() for d in (src or "").split(",") if d.strip()]
        cats = sorted({cat.get(d, "general") for d in docs}) or ["general"]

        para = PARA_FOR_BB.get(bb, "resource")
        tags = [para] + cats + ([bb] if bb and bb != "navigation" else [])

        # keywords: title phrase, linked term names, then discriminating body terms
        kws: list[str] = []
        t_clean = re.sub(r"[^A-Za-z0-9 ]", " ", title).strip().lower()
        # drop a leading article: "the digital services act" and "digital services
        # act" are the same keyword, and a question never opens with the article
        t_clean = re.sub(r"^(the|a|an)\s+", "", re.sub(r"\s+", " ", t_clean))
        if t_clean:
            kws.append(t_clean)
        for t in tl.get(nid, [])[:3]:
            k = t.replace("_", " ")
            # a term already contained in the title phrase adds nothing
            if k not in kws and not any(k in x or x in k for x in kws):
                kws.append(k)
        scored = sorted(
            ((w, c * math.log(N / (1 + df[w]))) for w, c in toks[nid].items()
             if 1 < df[w] < N * 0.25),
            key=lambda x: -x[1])
        for w, _ in scored:
            if len(kws) >= a.keywords:
                break
            if w not in " ".join(kws):
                kws.append(w)

        topics = [c.replace("_", " ").title() for c in cats]

        head = ["---", "tags:"]
        head += [f"  - {t}" for t in dict.fromkeys(tags)]
        head += ["keywords:"] + [f"  - {k}" for k in kws]
        head += ["topics:"] + [f"  - {t}" for t in topics]
        head += ["language: markdown",
                 f"date of note: {date.fromtimestamp(f.stat().st_mtime).isoformat()}",
                 "status: active",
                 f"building_block: {bb}"]
        if docs:
            head.append(f"source_docs: [{', '.join(docs)}]")
        for extra in ("enriched", "external_refs"):
            if extra in fm and fm[extra]:
                head.append(f"{extra}: {fm[extra]}")
            elif f"_{extra}" in fm:
                head.append(f"{extra}:")
                head += [f"  - {v}" for v in fm[f"_{extra}"]]
        head.append("---")

        new = "\n".join(head) + "\n" + rest
        if new == text:
            skipped += 1
            continue
        if not a.dry_run:
            f.write_text(new)
        written += 1

    print(f"notes            {len(rows):,}")
    print(f"{'would rewrite' if a.dry_run else 'rewritten':<16} {written:,}")
    print(f"unchanged        {skipped:,}")
    print("\nKeywords here are the vocabulary the note USES, derived from its own text "
          "and its term links. What a questioner would call it is a separate judgement "
          "and is not claimed.")


if __name__ == "__main__":
    main()
