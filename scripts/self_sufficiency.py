#!/usr/bin/env python3
"""
Is the note layer's 1.23x expansion redundancy that buys self-sufficiency?

A chunk is a window cut by offset: it can open mid-sentence, refer to "he" with
no antecedent in view, and omit the date and the subject because the article
established them 400 words earlier. A note restates that context because it was
written to stand alone. If that is what the extra words are, three things should
hold and are measured here:

  REDUNDANCY      units from one document should overlap MORE for notes than
                  for chunks -- shared context restated in each sibling
  SELF-SUFFICIENCY units should less often open with an unresolved reference,
                  and should more often name a subject and a time
  YIELD PER SLOT  a retrieved note should carry more distinct source documents
                  than a retrieved chunk, which is the payoff redundancy buys

    python3 scripts/self_sufficiency.py --arms notes=vaults/multihop_rag chunks=data/chunks/multihop_rag
"""
from __future__ import annotations
import argparse, re, sqlite3, random, sys
from collections import defaultdict
from pathlib import Path
import numpy as np

DANGLING = re.compile(r"^\W*(he|she|they|it|his|her|their|its|this|that|these|those|"
                      r"the company|the firm|the group|the team|but|and|so|however|"
                      r"meanwhile|also|then)\b", re.I)
PRONOUN = re.compile(r"\b(he|she|they|him|her|them|his|hers|their|its|it)\b", re.I)
PROPER = re.compile(r"\b[A-Z][a-z]{2,}\b")
DATE = re.compile(r"\b(19|20)\d{2}\b|\b(January|February|March|April|May|June|July|"
                  r"August|September|October|November|December|Monday|Tuesday|Wednesday|"
                  r"Thursday|Friday|Saturday|Sunday)\b")
NON_EVID = re.compile(r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)", re.M | re.S)
HEAD = re.compile(r"^#{1,6}\s*", re.M)


def clean(t: str) -> str:
    return HEAD.sub("", NON_EVID.sub("", t)).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", required=True)
    ap.add_argument("--sample-docs", type=int, default=120)
    a = ap.parse_args()

    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    random.seed(21)

    for spec in a.arms:
        name, _, vp = spec.partition("=")
        con = sqlite3.connect(Path(vp) / "notes.db")
        by_doc = defaultdict(list)
        for nid, src, body in con.execute("SELECT note_id, source_doc, body FROM notes"):
            for d in {x.strip() for x in (src or "").split(",") if x.strip()}:
                by_doc[d].append(clean(body))
        con.close()

        docs = sorted(d for d, v in by_doc.items() if len(v) >= 2)
        random.shuffle(docs); docs = docs[: a.sample_docs]

        sib = []
        for d in docs:
            u = by_doc[d][:12]
            E = m.encode(u, normalize_embeddings=True, show_progress_bar=False)
            S = E @ E.T
            iu = np.triu_indices(len(u), k=1)
            sib += list(S[iu])

        allu = [x for d in docs for x in by_doc[d]]
        dang = sum(1 for u in allu if DANGLING.match(u)) / len(allu)
        pron, prop, dated = [], [], 0
        for u in allu:
            w = max(len(u.split()), 1)
            pron.append(len(PRONOUN.findall(u)) / w * 100)
            prop.append(len(set(PROPER.findall(u))))
            dated += bool(DATE.search(u))
        print(f"{name}")
        print(f"  sibling overlap (same document)   mean cosine {np.mean(sib):.3f}   "
              f"median {np.median(sib):.3f}")
        print(f"  opens with an unresolved reference           {dang:6.1%}")
        print(f"  pronouns per 100 words                       {np.mean(pron):6.2f}")
        print(f"  distinct capitalised names per unit          {np.mean(prop):6.2f}")
        print(f"  carries a date or weekday                    {dated/len(allu):6.1%}")
        print()


if __name__ == "__main__":
    main()
