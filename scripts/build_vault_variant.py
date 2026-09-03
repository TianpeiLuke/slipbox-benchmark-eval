#!/usr/bin/env python3
"""
Build an index variant of a vault: same notes, different graph or different index.

Two vault-design questions need this. Is frontmatter earning its place in the
index? And how does retrieval change as note degree changes?

**The variants are built at the INDEX level, not by duplicating note files, and
that is a methodological choice rather than a shortcut.** Editing the markdown to
change link density would also change every note's token count, so a
density comparison would be confounded with unit size -- the arm with fewer links
would win partly for being cheaper, and nothing in the result would separate the
two. Holding the note text fixed and varying only the index isolates the variable.

    python3 scripts/build_vault_variant.py vaults/multihop_rag --out vaults/v_nolinks --max-degree 0
    python3 scripts/build_vault_variant.py vaults/multihop_rag --out vaults/v_deg4   --max-degree 4
    python3 scripts/build_vault_variant.py vaults/multihop_rag --out vaults/v_nofm   --index body

--max-degree keeps the first N outbound links per note in their written order,
which is the order the link builder ranked them in, so pruning removes the
weakest edges rather than a random sample.

--index body   rebuilds the FTS over body text only, dropping keywords and topics
--index meta   rebuilds it over keywords and topics only, dropping the body
--index both   the default, as the main vault is built

--keywords clean re-derives every note's keywords with the two defects the
               curation pilot found removed -- no title restatement, and no
               tokens taken from the Related Notes block -- then rebuilds the
               FTS. The note FILES are untouched, so this isolates the keyword
               text from every other difference between two vaults.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from revise_frontmatter import SCAFFOLD, derive_keywords, tokens   # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-degree", type=int, default=-1,
                    help="keep at most N outbound links per note (-1 keeps all)")
    ap.add_argument("--index", choices=["both", "body", "meta"], default="both")
    ap.add_argument("--keywords", choices=["keep", "clean"], default="keep")
    ap.add_argument("--term-links",
                    default="experiments/plans/multihop_rag/term_links.json")
    a = ap.parse_args()

    src, dst = Path(a.vault), Path(a.out)
    if not (src / "notes.db").exists():
        print(f"no database at {src}/notes.db")
        sys.exit(2)
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(src / "notes.db", dst / "notes.db")
    # the dense index is content-derived, so it is shared unchanged: a variant
    # that changed embeddings too would confound the graph question with a
    # different semantic space
    for f in ("embeddings.npy", "embedding_ids.json"):
        if (src / f).exists():
            shutil.copy(src / f, dst / f)

    con = sqlite3.connect(dst / "notes.db")

    if a.max_degree >= 0:
        keep, seen = [], {}
        for rid, s, t in con.execute(
                "SELECT rowid, source_note_id, target_note_id FROM note_links "
                "WHERE resolved=1 ORDER BY rowid"):
            seen.setdefault(s, 0)
            if seen[s] < a.max_degree:
                seen[s] += 1
                keep.append(rid)
        con.execute("DELETE FROM note_links WHERE rowid NOT IN (%s)"
                    % ",".join("?" * len(keep)) if keep else
                    "DELETE FROM note_links", keep or [])
        con.commit()

    if a.keywords == "clean":
        rows = con.execute("SELECT note_id, title, body FROM notes").fetchall()
        tl = json.loads(Path(a.term_links).read_text()) if a.term_links and \
            Path(a.term_links).exists() else {}
        df: Counter = Counter()
        for _nid, title, body in rows:
            df.update(tokens(f"{title} {SCAFFOLD.sub('', body)}").keys())
        for nid, title, body in rows:
            kws = derive_keywords(title, body, tl.get(nid, []), df, len(rows),
                                  6, with_title=False)
            con.execute("UPDATE notes SET keywords=? WHERE note_id=?",
                        (", ".join(kws), nid))
        con.commit()

    # always rebuilt when keywords changed, or the FTS would still hold the old
    # ones and the variant would differ from its own notes table
    if a.index != "both" or a.keywords == "clean":
        con.execute("DELETE FROM notes_fts")
        for nid, title, kw, tp, body in con.execute(
                "SELECT note_id, title, keywords, topics, body FROM notes"):
            text = ({"body": body, "meta": f"{kw} {tp}"}
                    .get(a.index, f"{kw} {tp} {body}"))
            con.execute("INSERT INTO notes_fts VALUES (?,?,?)", (nid, title, text))
        con.commit()

    n = con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    l = con.execute("SELECT COUNT(*) FROM note_links WHERE resolved=1").fetchone()[0]
    con.close()
    print(f"variant  {dst}")
    print(f"notes    {n:,}   links {l:,}   mean out-degree {l/n:.2f}")
    print(f"index    {a.index}   keywords {a.keywords}   max out-degree "
          f"{'unlimited' if a.max_degree < 0 else a.max_degree}")


if __name__ == "__main__":
    main()
