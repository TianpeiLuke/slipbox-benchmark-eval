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
# A token must start at a real word boundary, or "49ers" yields "ers" and
# "23andMe" yields "andme". Hyphenated compounds stay whole: "fine-tuning" is
# one word to a reader, so it is one token here.
WORD = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9][A-Za-z0-9\-']{2,}(?![A-Za-z0-9])")

# Related Notes and Source are scaffolding the pipeline wrote, not content the
# document asserts. Deriving keywords from them imports the ENTITIES OF
# NEIGHBOURING NOTES -- a betting-pick note acquires the names of five fighters
# it never mentions -- and those keywords retrieve the note for questions it
# cannot answer. Same sections score_retrieval.py excludes from token accounting.
SCAFFOLD = re.compile(r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)",
                      re.M | re.S)


def tokens(text: str) -> Counter:
    """Content tokens of a note, possessives normalised, stopwords dropped."""
    out: Counter = Counter()
    for w in WORD.findall(text):
        w = re.sub(r"'s$", "", w.lower()).strip("'-")
        if len(w) > 2 and w not in STOP and any(c.isalpha() for c in w):
            out[w] += 1
    return out


def derive_keywords(title, body, terms, df, N, want, with_title):
    """Title phrase (optional), linked term names, then discriminating own terms."""
    kws: list[str] = []
    if with_title:
        t = re.sub(r"[^A-Za-z0-9 ]", " ", title).strip().lower()
        # drop a leading article: "the digital services act" and "digital
        # services act" are the same keyword, and a question never opens with it
        t = re.sub(r"^(the|a|an)\s+", "", re.sub(r"\s+", " ", t))
        if t:
            kws.append(t)
    for t in terms[:3]:
        k = t.replace("_", " ")
        # a term already contained in the title phrase adds nothing
        if k not in kws and not any(k in x or x in k for x in kws):
            kws.append(k)
    scored = sorted(((w, c * math.log(N / (1 + df[w])))
                     for w, c in tokens(SCAFFOLD.sub("", body)).items()
                     if 1 < df[w] < N * 0.25), key=lambda x: -x[1])
    for w, _ in scored:
        if len(kws) >= want:
            break
        if w not in " ".join(kws):
            kws.append(w)
    return kws

STOP = set("""the and for that with this from have has had was were been are you your their
they them its it will would could should about into over under after before more most some
such than then there here when what which who whom while also just only said says say new
one two three first last year years time told according but not all any can may might must
our out per via etc other another each both many much very own same too how why where
because during through against between among within without across behind beyond
she her him his hers he who's dont doesnt isnt wasnt were being does did done get got
make made take taken come came goes going know known think thought see seen look looking""".split())

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
    # Every note's first keyword used to be its own title, lowercased -- one slot
    # in six spent on a string already indexed as the title column. Off by
    # default now; the flag exists to reproduce a vault built the old way.
    ap.add_argument("--title-keyword", action="store_true")
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
    # over EVIDENCE text only -- scaffolding words are near-universal, so
    # counting them distorts every other term's idf as well as leaking entities
    df: Counter = Counter()
    for _nid, title, body, _bb, _s in rows:
        df.update(tokens(f"{title} {SCAFFOLD.sub('', body)}").keys())
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

        kws = derive_keywords(title, body, tl.get(nid, []), df, N,
                              a.keywords, a.title_keyword)

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
