#!/usr/bin/env python3
"""
Derive each planned note's related NOTES, with the reason each one is related.

Term links alone do not connect the graph. Most links a reader follows go note
to note, and those are what `bfs` and `ppr` traverse. This derives them from
evidence the plan already holds, and records WHY each pair is related, so the
executing agent writes a relation rather than a bare link.

    python3 scripts/build_note_links.py multihop_rag --plans experiments/plans/multihop_rag

CROSS-DOCUMENT EDGES RANK FIRST, and that ordering is the whole point.

This vault answers multi-hop questions whose gold evidence spans 2.6 distinct
documents on average. An edge between two notes from the SAME article is nearly
free to the retriever: they share vocabulary, so a lexical hit on one already
surfaces the other. The edge that earns its keep is the one that BRIDGES
documents, because that is the hop a multi-hop question actually requires and
the one no amount of lexical similarity provides.

Ranking within-document edges first -- the obvious ordering, since they are the
tightest relation -- fills the graph with edges that connect notes a retriever
has already reached together, and starves it of the hops it needs.

  shared terms, different document   the bridge. Both notes discuss the same
                                     concept, evidenced by their own source text,
                                     and they come from different articles.
  same sub-plan, different document  the planner grouped them while reading, and
                                     they still cross an article boundary.
  same source document               parts of one story. Kept, capped, and ranked
                                     last, because it is coherence rather than reach.

A link with no reason is a link nobody can check. The reason ships with the
mapping so it reaches the note, because "how they relate" is the part that makes
a Related Notes section worth reading -- and the part an agent otherwise invents.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANS = ROOT / "experiments" / "plans"
CORPUS = ROOT / "data" / "corpus"

# A curated term list cannot cover 609 documents across six categories, so notes
# whose subject nobody thought to add as a term end up with no bridge at all.
# Named entities supply the rest: two notes naming the same person, club, company
# or product are about the same thing, and that is a fact about their source text
# rather than a guess. Entities appearing almost everywhere are useless as bridges
# (they connect everything to everything), so the very common ones are dropped.
ENTITY = re.compile(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,3})\b")
ENTITY_STOP = {"The", "This", "That", "These", "But", "And", "For", "With", "When",
               "What", "Where", "How", "Why", "There", "Here", "After", "Before",
               "According", "While", "Some", "Many", "Most", "Last", "Next", "New"}
MAX_ENTITY_DOCS = 40      # above this an entity is background, not a bridge


WORD = re.compile(r"[a-z][a-z0-9\-']{2,}")
STOPW = set("""the and for that with this from have has had was were been are you your
their they them its it's will would could should about into over under after before
more most some such than then there here when what which who whom while also just only
said says say new one two three first last year years time says told according but not
all any can may might must our out per pic via etc""".split())


def bow(text: str) -> Counter:
    return Counter(w for w in WORD.findall(text.lower()) if w not in STOPW and len(w) > 3)


def note_entities(text: str) -> set[str]:
    out = set()
    for m in ENTITY.findall(text):
        if m.split()[0] in ENTITY_STOP:
            continue
        out.add(m)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--plans", required=True)
    ap.add_argument("--floor", type=int, default=3)
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--keep-single-term", action="store_true",
                    help="keep edges justified by ONE shared term (default: drop them)")
    ap.add_argument("--min-sim", type=float, default=0.10,
                    help="cosine floor for a content-relevance edge; below this the two "
                         "notes share vocabulary rather than a subject")
    ap.add_argument("--cross-max", type=int, default=5,
                    help="how many cross-document edges to take before filling with "
                         "same-document ones. These are the multi-hop edges.")
    ap.add_argument("--out")
    a = ap.parse_args()

    P = Path(a.plans)
    docs_of: dict[str, set[str]] = {}
    sub_of: dict[str, str] = {}
    title_of: dict[str, str] = {}
    for f in sorted((P / "clusters").glob("c*.json")) if (P / "clusters").is_dir() else []:
        for s in json.loads(f.read_text())["subplans"]:
            for n in s["notes"]:
                docs_of[n["note"]] = {d for d, v in n["blocks"].items() if v}
                sub_of[n["note"]] = f"{f.stem}:{s['slug']}"
                title_of[n["note"]] = s["title"]
    for f in sorted(P.glob("subplan_*_assignments.json")):
        for note, m in json.loads(f.read_text()).items():
            docs_of.setdefault(note, {d for d, v in m.items() if v})
            sub_of.setdefault(note, f.stem)
            title_of.setdefault(note, f.stem)

    terms = {}
    tlp = P / "term_links.json"
    if tlp.exists():
        terms = json.loads(tlp.read_text())

    # entity index, built from each note's OWN assigned source text
    blocks_of: dict[str, dict[str, list[int]]] = {}
    for f in sorted((P / "clusters").glob("c*.json")) if (P / "clusters").is_dir() else []:
        for s_ in json.loads(f.read_text())["subplans"]:
            for n in s_["notes"]:
                blocks_of[n["note"]] = n["blocks"]
    for f in sorted(P.glob("subplan_*_assignments.json")):
        for note, m in json.loads(f.read_text()).items():
            blocks_of.setdefault(note, m)
    cache: dict[str, list[str]] = {}
    ents_of: dict[str, set[str]] = {}
    note_text: dict[str, str] = {}
    for n, bl in blocks_of.items():
        txt = []
        for d, ids in bl.items():
            if d not in cache:
                cache[d] = [b.strip() for b in
                            (CORPUS / a.slug / f"{d}.txt").read_text().split("\n\n") if b.strip()]
            txt += [cache[d][i] for i in ids if i < len(cache[d])]
        note_text[n] = "\n".join(txt)
        ents_of[n] = note_entities(note_text[n])
    ent_docs: Counter = Counter()
    for n, es in ents_of.items():
        for e in es:
            ent_docs[e] += 1
    by_ent: dict[str, list[str]] = defaultdict(list)
    for n, es in ents_of.items():
        for e in es:
            if ent_docs[e] <= MAX_ENTITY_DOCS:
                by_ent[e].append(n)

    # Content relevance: tf-idf cosine over each note's OWN assigned source text.
    # Shared terms and shared entities are exact-match signals and miss two notes
    # that discuss the same thing in different words. This catches those, and it
    # is still evidence from the plan -- the text compared is the text the plan
    # assigned, not a search of the whole corpus.
    tf = {n: bow(t) for n, t in note_text.items()}
    df: Counter = Counter()
    for c in tf.values():
        df.update(c.keys())
    N = max(1, len(tf))
    vec: dict[str, dict[str, float]] = {}
    for n, c in tf.items():
        v = {w: (1 + math.log(f)) * math.log(N / (1 + df[w]))
             for w, f in c.items() if 1 < df[w] < N * 0.30}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vec[n] = {w: x / norm for w, x in sorted(v.items(), key=lambda kv: -kv[1])[:60]}
    postings: dict[str, list[str]] = defaultdict(list)
    for n, v in vec.items():
        for w in list(v)[:25]:
            postings[w].append(n)

    def similar(n: str, exclude_docs: set[str], k: int = 12):
        """Top content-similar notes from OTHER documents, with their score."""
        acc: dict[str, float] = defaultdict(float)
        for w, x in vec[n].items():
            plist = postings.get(w, ())
            if len(plist) > 400:      # a term this common carries no signal
                continue
            for o in plist:
                if o != n and not (docs_of[o] & exclude_docs):
                    acc[o] += x * vec[o].get(w, 0.0)
        return sorted(acc.items(), key=lambda kv: -kv[1])[:k]

    by_doc: dict[str, list[str]] = defaultdict(list)
    by_sub: dict[str, list[str]] = defaultdict(list)
    by_term: dict[str, list[str]] = defaultdict(list)
    for n, ds in docs_of.items():
        for d in ds:
            by_doc[d].append(n)
        by_sub[sub_of[n]].append(n)
        for t in terms.get(n, []):
            by_term[t].append(n)

    out: dict[str, list[dict]] = {}
    for n in docs_of:
        mine = docs_of[n]
        scored: dict[str, tuple[int, str]] = {}

        # Bridges, ranked by how reliably the signal means "same subject".
        # A single shared term is the weakest: terms are polysemous across
        # domains, and one shared term linked an FTX trial note to a football
        # recap because both matched a form of "criminal_trial". Content overlap
        # and shared entities do not fail that way, so they rank above it.
        shared: dict[str, list[str]] = defaultdict(list)
        for t in terms.get(n, []):
            for o in by_term[t]:
                if o != n and not (docs_of[o] & mine):
                    shared[o].append(t)

        # 3 — the other bridge: same named entity, different article
        ent_shared: dict[str, list[str]] = defaultdict(list)
        for e in ents_of.get(n, ()):
            for o in by_ent.get(e, ()):
                if o != n and o not in scored and not (docs_of[o] & mine):
                    ent_shared[o].append(e)
        for o, es in ent_shared.items():
            scored[o] = (3, f"both discuss {', '.join(sorted(es)[:2])}; "
                            f"different source document")

        # 3 — content relevance across documents: same subject, different words
        for o, sc in similar(n, mine):
            if o not in scored and sc >= a.min_sim:
                top = [w for w in vec[n] if w in vec[o]][:3]
                scored[o] = (3, f"content overlap {sc:.2f}"
                                + (f" on {', '.join(top)}" if top else "")
                                + "; different source document")

        # 3c — two or more shared terms: co-occurrence makes coincidence unlikely
        for o, ts in shared.items():
            if len(ts) >= 2 and o not in scored:
                scored[o] = (3, f"shares {', '.join(sorted(ts)[:3])}; "
                                f"different source document")

        # A single shared term is DROPPED, not merely down-ranked. Two execution
        # agents independently reported these as noise, and inspection agreed: one
        # shared term linked an FTX trial note to a football recap. Across the plan
        # they were 22.9% of all edges. An edge bfs and ppr will traverse has to
        # mean something; a coincidental token match does not, and a weak edge is
        # not free -- it moves probability mass onto an unrelated note.
        if a.keep_single_term:
            for o, ts in shared.items():
                if o not in scored:
                    scored[o] = (1, f"shares {ts[0]}; different source document")

        # 2 — grouped by the planner, still crossing an article boundary
        for o in by_sub[sub_of[n]]:
            if o != n and o not in scored and not (docs_of[o] & mine):
                scored[o] = (2, f"same sub-plan ({title_of[n]}), different source document")

        # 1 — same article: coherence, not reach
        for d in mine:
            for o in by_doc[d]:
                if o != n and o not in scored:
                    scored[o] = (1, f"same source document ({d})")

        ranked = sorted(scored.items(), key=lambda kv: (-kv[1][0], kv[0]))
        cross = [x for x in ranked if x[1][0] >= 2 and "different source" in x[1][1]][: a.cross_max]
        rest = [x for x in ranked if x[1][0] < 2][: max(0, a.max - len(cross))]
        chosen = cross + rest
        out[n] = [{"note": o, "why": why} for o, (_, why) in chosen]

    cross_n = sum(1 for v in out.values() for l in v if "different source document" in l["why"])
    tot_n = sum(len(v) for v in out.values())
    counts = sorted(len(v) for v in out.values())
    nocross = sum(1 for v in out.values()
                  if not any("different source document" in l["why"] for l in v))
    short = sum(1 for v in out.values() if len(v) < a.floor)
    print(f"notes              {len(out)}")
    print(f"links per note     min {counts[0]}, median {counts[len(counts)//2]}, max {counts[-1]}")
    print(f"at or above {a.floor}      {len(out) - short}")
    print(f"below the floor    {short}")
    print(f"total edges        {tot_n:,}")
    print(f"CROSS-document     {cross_n:,}  ({100*cross_n/tot_n:.1f}%) — the multi-hop edges")
    print(f"notes with none    {nocross}  (their sources share no concept with any other note)")
    if short:
        print(f"\n{short} note(s) below the floor are NOT padded: a note whose plan gives it "
              f"no genuine neighbour is peripheral, and an invented edge would mislead "
              f"the graph arms rather than help them.")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1))
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
