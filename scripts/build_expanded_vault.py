#!/usr/bin/env python3
"""
Append anticipated questions to a vault's indexed text and re-embed.

The questions go into the INDEX, not the note files. A reader gets the note as
written; a retriever additionally sees the questions the note answers, which is
where the questioner's vocabulary enters a corpus written in the author's.

Scaffolding is stripped at the same time, since runs6 measured that as a gain on
its own and leaving it in would confound the two changes.

    python3 scripts/build_expanded_vault.py --vault vaults/multihop_rag \
        --expansions expansions/notes.jsonl --out vaults/v_expanded
"""
from __future__ import annotations
import argparse, json, re, shutil, sqlite3
from pathlib import Path
import numpy as np

NON = re.compile(r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)", re.M | re.S)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--expansions", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-scaffolding", action="store_true")
    a = ap.parse_args()

    src, dst = Path(a.vault), Path(a.out)
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(src / "notes.db", dst / "notes.db")

    exp = {}
    for line in Path(a.expansions).read_text().splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        exp[r["id"]] = r["questions"]

    con = sqlite3.connect(dst / "notes.db")
    rows = con.execute("SELECT note_id, title, keywords, topics, body FROM notes").fetchall()
    con.execute("DELETE FROM notes_fts")
    texts, ids, n_exp = [], [], 0
    for nid, title, kw, tp, body in rows:
        ev = body if a.keep_scaffolding else NON.sub("", body)
        qs = exp.get(nid, [])
        n_exp += bool(qs)
        # questions lead: they carry the questioner's vocabulary, and a lexical
        # index rewards the terms a query actually uses
        text = ("\n".join(qs) + "\n\n" + ev) if qs else ev
        con.execute("INSERT INTO notes_fts VALUES (?,?,?)",
                    (nid, title, f"{kw or ''} {tp or ''} {text}"))
        ids.append(nid); texts.append(text)
    con.commit(); con.close()

    meta = json.loads((src / "embedding_ids.json").read_text())
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(meta["model"])
    E = m.encode(texts, normalize_embeddings=True, batch_size=128, show_progress_bar=False)
    np.save(dst / "embeddings.npy", E.astype(np.float32))
    (dst / "embedding_ids.json").write_text(
        json.dumps({"model": meta["model"], "dim": int(E.shape[1]), "ids": ids}))
    print(f"{dst}: {n_exp:,}/{len(rows):,} notes expanded, embeddings {E.shape}, "
          f"scaffolding {'kept' if a.keep_scaffolding else 'stripped'}")


if __name__ == "__main__":
    main()
