#!/usr/bin/env python3
"""
Precompute the retrieved context for every question and write it to disk.

Retrieval needs torch and sentence-transformers, roughly a gigabyte resident.
Answering needs a subprocess and a few megabytes. Holding both in one process
means every answering run carries the retrieval footprint for its whole life,
and on a memory-pressured machine the OOM killer takes it -- which is what
repeatedly killed the slots run while a bare cline call was fine.

Splitting them makes the expensive half a single short pass whose output is a
plain JSONL, and the long half cheap enough to survive.

    python3 scripts/dump_contexts.py multihop_rag --vault vaults/multihop_rag \
        --condition slots --k 10 --out contexts/slots_notes.jsonl
"""
from __future__ import annotations
import argparse, json, random, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--vault", required=True)
    ap.add_argument("--strategy", default="hybrid")
    ap.add_argument("--condition", choices=["slots", "tokens"], default="tokens")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--budget", type=int, default=2048)
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("--nulls", type=int, default=50)
    ap.add_argument("--questions",
                    help="JSON list of question strings to pin. Required for any\ncross-vault comparison: the vaults do NOT cover the same documents (v1_slice\nspans 178 source docs, v2_pilot 37), so an unpinned sample asks one vault far\nmore questions it structurally cannot answer than the other.")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    from answer_eval import build_context
    from score_retrieval import unit_tokens

    raw = json.loads((ROOT / "data/raw" / a.slug / "MultiHopRAG.json").read_text())
    random.seed(20260902)          # identical split to answer_eval.py
    answerable = [q for q in raw if q.get("evidence_list") and q.get("answer")]
    nulls = [q for q in raw if not q.get("evidence_list")]
    random.shuffle(answerable); random.shuffle(nulls)
    if a.questions:
        pin = set(json.loads(Path(a.questions).read_text()))
        chosen = [q for q in answerable if q["query"] in pin]
        missing = len(pin) - len(chosen)
        if missing:
            print(f"  !! {missing} pinned question(s) not found in the corpus")
        qs = chosen[: a.sample] + nulls[: a.nulls]
        print(f"  pinned {len(chosen[: a.sample])} answerable + {len(nulls[: a.nulls])} null")
    else:
        qs = answerable[: a.sample] + nulls[: a.nulls]

    vault = Path(a.vault)
    con = sqlite3.connect(vault / "notes.db")
    bodies = {n: b for n, b in con.execute("SELECT note_id, body FROM notes")}
    con.close()
    toks = unit_tokens(vault / "notes.db", evidence_only=True)

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as fh:
        for i, q in enumerate(qs, 1):
            ctx, n = build_context(vault, bodies, toks, q["query"],
                                   a.condition, a.k, a.budget, a.strategy)
            fh.write(json.dumps({"qid": q["query"], "context": ctx, "units": n,
                                 "ctx_chars": len(ctx),
                                 "gold": q.get("answer") or "",
                                 "null": not q.get("evidence_list")}) + "\n")
            if i % 50 == 0:
                print(f"  {i}/{len(qs)}", flush=True)
    print(f"wrote {len(qs)} contexts -> {out}")


if __name__ == "__main__":
    main()
