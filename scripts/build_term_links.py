#!/usr/bin/env python3
"""
Derive each planned note's term links from the source blocks it actually covers.

The digestion plan asks for a per-note table of relevant term notes. Written by
hand it is a guess; derived from the plan it is not, because the plan already
declares which source blocks each note carries and which terms will be captured.
A term is linked to a note when the term's surface forms appear in that note's
own source text -- so relevance is evidence from the corpus rather than a
recollection, which is exactly the distinction between a relevancy-ranked
mapping and a padded one.

    python3 scripts/build_term_links.py multihop_rag --plans experiments/plans/multihop_rag

Terms are ranked per note by occurrences in that note's blocks. `--floor` sets
the target link count; notes that cannot reach it are REPORTED rather than
padded, because a link to an unrelated term is not neutral: bfs and ppr traverse
every edge, so a false edge degrades the arm under test.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "corpus"


# Compounds where the form's SENSE changes, so the term does not apply. This
# list is short because it is derived from the corpus rather than imagined: of
# the 143 hyphenated occurrences of any term form, these are the ones where the
# head noun is not the term. "fine-tuning" is not a monetary fine; "hard-
# charging" is not a battery. Everything else -- "COVID-19", "battery-swapping",
# "anti-disinformation", "pre-pandemic" -- IS the term, and a rule that treats
# every hyphen as a wall loses all of them to catch these two.
# An acronym only needs case-sensitivity when lowercasing it yields a real
# English word -- "WHO"/"who", "IT"/"it", "US"/"us". "COVID" lowercases to
# nothing else, so forcing exact case on it just loses "covid-related". Blanket
# case-sensitivity for anything all-caps was the wrong generalisation.
AMBIGUOUS_ACRONYMS = {
    "who", "it", "us", "can", "may", "all", "are", "was", "has", "but", "now",
    "new", "one", "two", "so", "no", "on", "in", "at", "by", "or", "and", "for",
    "the", "a", "an", "is", "be", "as", "if", "up", "out", "act", "aid", "ally",
    "bit", "cap", "cost", "fit", "gap", "hit", "ice", "id", "led", "lot", "map",
    "mass", "net", "pass", "pop", "post", "put", "ran", "run", "set", "sun",
    "tip", "top", "war", "way", "win",
}

EXCLUDED_COMPOUNDS = {
    "fine": ["fine-tuning", "fine-tune", "fine-tuned", "fine-tunes"],
    "charging": ["hard-charging"],
}


def compile_forms(forms: list[str]) -> re.Pattern:
    """One pattern per term, with the three properties a naive join gets wrong.

    WORD BOUNDARIES. Without them "bot" matches inside "both", "NFL" inside
    "influenza", and "trial" inside "clinical trial" -- so a canine-illness note
    acquires links to bot detection and criminal trials. Every such edge is
    fabricated, and bfs and ppr traverse every edge they are given.

    HYPHENS. A hyphen is a word boundary to \b, which is USUALLY right: the
    corpus writes "COVID-19" for the term whose form is "COVID", and
    "battery-swapping" for "battery". Walling off hyphens entirely was a
    correction that cost more than the error it fixed -- 19 correct COVID edges
    to remove 8 wrong "fine" ones. So hyphens stay permeable and the small set
    of sense-changing compounds is excluded by name.

    CASE. An acronym is case-SENSITIVE: "WHO" is an organisation, "who" is a
    pronoun. A lowercase phrase is not, because it may open a sentence.
    """
    parts = []
    for f in forms:
        esc = re.escape(f)
        # a form starting/ending with a word character needs a boundary there
        # A hyphen IS a word boundary, so \b alone lets "fine" match inside
        # "fine-tuning" and "battery" inside "battery-powered". A hyphenated
        # compound is one token to a reader and should be one to the matcher, so
        # the boundary also has to exclude an adjacent hyphen.
        left = r"(?<!\w)" if f[:1].isalnum() else ""
        right = r"(?!\w)" if f[-1:].isalnum() else ""
        bad = EXCLUDED_COMPOUNDS.get(f.lower(), [])
        # block the compound from either side: "fine" must not match in
        # "fine-tuning", and "charging" must not match in "hard-charging"
        for c in bad:
            head, _, tail = c.lower().partition("-")
            if head == f.lower():
                right = r"(?!-" + re.escape(tail) + r")" + right
            elif tail == f.lower():
                left = r"(?<!" + re.escape(head) + r"-)" + left
        if f.isupper() and f.isalpha() and f.lower() in AMBIGUOUS_ACRONYMS:
            parts.append(f"(?-i:{left}{esc}{right})")   # acronym: exact case
        else:
            parts.append(f"{left}{esc}{right}")
    return re.compile("|".join(parts), re.I)


def blocks(slug: str, doc: str) -> list[str]:
    return [b.strip() for b in (CORPUS / slug / f"{doc}.txt").read_text().split("\n\n") if b.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--plans", required=True)
    ap.add_argument("--floor", type=int, default=8)
    ap.add_argument("--out")
    ap.add_argument("--verify", metavar="TERM_LINKS_JSON",
                    help="audit an existing mapping: every link must be backed by an "
                         "occurrence of the term in that note's own source blocks. Exits "
                         "non-zero on any unbacked link.")
    a = ap.parse_args()

    P = Path(a.plans)
    terms = json.loads((P / "terms.json").read_text())
    pats = {t: compile_forms(forms) for t, forms in terms.items()}

    cache: dict[str, list[str]] = {}
    mapping: dict[str, list] = {}
    term_use: dict[str, int] = defaultdict(int)

    def assignments():
        """Every planned note, from both plan shapes: the hand-built sub-plan
        assignment files and the agent-produced cluster plans."""
        for f in sorted(P.glob("*_assignments.json")):
            yield from json.loads(f.read_text()).items()
        for f in sorted((P / "clusters").glob("c*.json")) if (P / "clusters").is_dir() else []:
            for sub in json.loads(f.read_text())["subplans"]:
                for n in sub["notes"]:
                    yield n["note"], n["blocks"]

    for note, m in assignments():
        if True:
            text = []
            for d, ids in m.items():
                cache.setdefault(d, blocks(a.slug, d))
                text += [cache[d][i] for i in ids if i < len(cache[d])]
            body = "\n".join(text)
            hits = [(t, len(p.findall(body))) for t, p in pats.items()]
            hits = sorted([h for h in hits if h[1]], key=lambda x: -x[1])
            mapping[note] = hits
            for t, _ in hits:
                term_use[t] += 1

    if a.verify:
        # A link nothing in the source supports is a fabricated edge. It is not
        # inert: bfs and ppr traverse every edge given, so it moves probability
        # mass onto a note the evidence never connected, degrading the arm the
        # experiment exists to measure. Cheaper to block than to detect later in
        # a retrieval number that merely looks disappointing.
        claimed = json.loads(Path(a.verify).read_text())
        backed = {n: {t for t, _ in v} for n, v in mapping.items()}
        bad = []
        for note, ts in claimed.items():
            if note not in backed:
                bad.append((note, "<not in any assignment>"))
                continue
            bad += [(note, t) for t in ts if t not in backed[note]]
        total = sum(len(v) for v in claimed.values())
        print(f"links claimed   {total}")
        print(f"backed by source {total - len(bad)}")
        print(f"UNBACKED         {len(bad)}")
        for note, t in bad[:20]:
            print(f"  {note} -> {t}")
        if bad:
            print("\nA link the source does not support is a fabricated edge. Remove it, "
                  "or add the term's real surface form to terms.json if the match was "
                  "missed. Never keep it to reach a floor.")
            sys.exit(1)
        print("\nevery link is backed by an occurrence in that note's own source")
        return

    short = {n: len(v) for n, v in mapping.items() if len(v) < a.floor}
    print(f"notes            {len(mapping)}")
    print(f"terms            {len(terms)}")
    print(f"floor            {a.floor} term links per note")
    print(f"at or above      {len(mapping) - len(short)}")
    print(f"below the floor  {len(short)}")
    counts = sorted(len(v) for v in mapping.values())
    print(f"links per note   min {counts[0]}, median {counts[len(counts)//2]}, max {counts[-1]}")

    unused = [t for t in terms if not term_use[t]]
    if unused:
        print(f"\nterms no note references ({len(unused)}): {', '.join(sorted(unused))}")
        print("  Drop these or widen their surface forms -- a term note nothing links to "
              "is a graph island, which is the failure the term list exists to prevent.")
    if short:
        print(f"\nnotes below the floor, with their count:")
        for n, c in sorted(short.items(), key=lambda x: x[1])[:25]:
            print(f"  {c:>2}  {n}")
        print("  Do NOT pad these. Either the note is genuinely peripheral, or the term "
              "list is missing a concept the note depends on -- add the concept.")
    if a.out:
        Path(a.out).write_text(json.dumps(
            {n: [t for t, _ in v] for n, v in mapping.items()}, indent=1))
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
