#!/usr/bin/env python3
"""Build a 2WikiMultiHopQA corpus in this repo's passage format.

2Wiki is the benchmark where HippoRAG reports its largest margin over BM25
(R@5 89.5 vs 61.9), so it is the sharpest available check on whether an
implementation reproduces the method's advantage. Its hop is an ENTITY BRIDGE
between Wikipedia articles, which is what an entity KG plus PPR is built for --
unlike MultiHop-RAG, whose hop is bibliographic.

Following the paper's setup: take N questions from the validation split and
build the corpus from all their candidate passages, supporting and distractor
alike, deduplicated by title. Document-level credit is by title, matching
supporting_facts.
"""
import argparse, json, sqlite3, random
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="data/raw/2wiki/dev.parquet")
    ap.add_argument("--out", required=True)
    ap.add_argument("--questions", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260902)
    a = ap.parse_args()

    df = pd.read_parquet(ROOT / a.parquet)
    rows = df.to_dict("records")
    random.seed(a.seed); random.shuffle(rows)
    rows = rows[: a.questions]

    passages: dict[str, str] = {}
    qs = []
    for r in rows:
        ctx = json.loads(r["context"]) if isinstance(r["context"], str) else r["context"]
        for entry in ctx:
            title, sents = entry[0], entry[1]
            body = " ".join(sents)
            if title not in passages:
                passages[title] = body
        sf = json.loads(r["supporting_facts"]) if isinstance(r["supporting_facts"], str) \
            else r["supporting_facts"]
        gold = sorted({s[0] for s in sf})
        qs.append({"query": r["question"], "answer": r["answer"],
                   "gold_titles": gold, "type": r["type"]})

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    db = out / "notes.db"
    if db.exists():
        db.unlink()
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE notes (note_id TEXT PRIMARY KEY, note_name TEXT, title TEXT,
                            building_block TEXT, body TEXT, words INTEGER,
                            source_doc TEXT);
        CREATE VIRTUAL TABLE notes_fts
            USING fts5(note_id UNINDEXED, title, body, tokenize='porter unicode61');
        CREATE TABLE note_links (src TEXT, dst TEXT);
    """)
    recs = []
    for i, (title, body) in enumerate(sorted(passages.items())):
        # source_doc IS the title: 2Wiki credits supporting passages by title
        recs.append((f"p_{i:06d}", title, title, "empirical_observation",
                     body, len(body.split()), title))
    con.executemany("INSERT INTO notes VALUES (?,?,?,?,?,?,?)", recs)
    con.executemany("INSERT INTO notes_fts(note_id, title, body) VALUES (?,?,?)",
                    [(r[0], r[2], r[4]) for r in recs])
    con.commit(); con.close()

    (out / "questions.json").write_text(json.dumps(qs, indent=2))
    ntypes = {}
    for q in qs:
        ntypes[q["type"]] = ntypes.get(q["type"], 0) + 1
    print(f"{len(qs)} questions, {len(recs)} passages -> {out}")
    print(f"  question types: {ntypes}")
    print(f"  mean gold titles/question: "
          f"{sum(len(q['gold_titles']) for q in qs)/len(qs):.2f}")


if __name__ == "__main__":
    main()
