#!/usr/bin/env python3
"""
Score a retrieval arm against benchmark gold evidence.

This script reads the QUESTIONS half of a benchmark. Nothing that ingests a
corpus may import or invoke it -- that separation is the blind-ingestion
guarantee, and it is the reason the corpus and the questions are prepared by
two different scripts that read two different files.

    python3 scripts/score_retrieval.py multihop_rag --arm notes  --vault vaults/multihop_rag
    python3 scripts/score_retrieval.py multihop_rag --arm chunks --chunk-db data/chunks/multihop_rag
    python3 scripts/score_retrieval.py multihop_rag --arm notes --vault vaults/multihop_rag \\
        --strategies bm25,hybrid,ppr --k 2,5,10 --budget 2048

Metrics
-------
Recall@k       fraction of a question's gold documents that appear in the top k
All-Recall@k   1 only if EVERY gold document appears in the top k, else 0

Both are reported because they answer different questions. A multi-hop question
is only answerable when all its evidence is present, so All-Recall is the metric
that tracks whether the retrieval could have supported an answer at all; Recall
shows partial progress and keeps a run interpretable when All-Recall is near
zero. Retrieval is scored at DOCUMENT level: a note is credited with the corpus
documents named in its own `source_docs` frontmatter, so a note that abstracts
several documents can satisfy several pieces of gold evidence at once -- which
is exactly the property under test and would be invisible to a chunk-level
metric.

null_query items carry no evidence and are excluded from recall; they are
counted separately, since scoring an unanswerable question by recall is
meaningless (nothing can be retrieved) and would silently inflate every arm.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

RAW = ROOT / "data" / "raw"
CORPUS = ROOT / "data" / "corpus"

QUESTIONS = {"multihop_rag": "MultiHopRAG.json"}


def load_gold(slug: str) -> tuple[list[dict], dict[str, str]]:
    """Questions with gold doc ids, plus the title -> doc_id map used to build them."""
    index = json.loads((CORPUS / slug / "index.json").read_text())
    by_title = {v["title"]: doc_id for doc_id, v in index.items()}

    raw = json.loads((RAW / slug / QUESTIONS[slug]).read_text())
    out, unmatched = [], 0
    for q in raw:
        gold, miss = set(), False
        for e in q.get("evidence_list", []):
            doc_id = by_title.get(e.get("title", ""))
            if doc_id is None:
                miss = True
            else:
                gold.add(doc_id)
        unmatched += miss
        out.append({"query": q["query"], "type": q.get("question_type", ""),
                    "gold": gold})
    if unmatched:
        print(f"WARNING: {unmatched} question(s) cite evidence with no matching "
              f"corpus document; their recall is unreachable by construction.")
    return out, by_title



def unit_tokens(db: Path) -> dict[str, int]:
    """Real token count per retrieval unit, from a tokenizer -- not words x k.

    A fixed words-to-tokens factor is not safe here because the factor DIFFERS
    BY ARM: measured on this corpus, notes run 1.67 tokens/word against 1.28 for
    raw chunks, because markdown headings, link brackets, table pipes and dense
    proper nouns all tokenize poorly. Charging both arms 1.30 undercharged notes
    by ~28%, so the note arm was assembling more real context than its budget
    allowed while appearing to spend the same.

    Budget means what fits in the window before the prompt goes in. That only
    holds if the count is the one the model would actually see.
    """
    con = sqlite3.connect(db)
    rows = con.execute("SELECT note_id, title, body FROM notes").fetchall()
    con.close()
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return {n: len(enc.encode(f"{t}\n\n{b}")) for n, t, b in rows}
    except ModuleNotFoundError:
        print("WARNING: tiktoken not installed — falling back to words x 1.3, which "
              "undercharges note-shaped text by roughly a quarter and biases the "
              "comparison toward the note arm. Install tiktoken for a valid run.")
        return {n: int(len(f"{t} {b}".split()) * 1.3) for n, t, b in rows}

def note_provenance(vault: Path) -> dict[str, set[str]]:
    """note_id -> the corpus documents it declares. This is what makes it scorable."""
    con = sqlite3.connect(vault / "notes.db")
    prov: dict[str, set[str]] = {}
    nav = set()
    for nid, src, bb in con.execute(
            "SELECT note_id, source_doc, building_block FROM notes"):
        prov[nid] = {s.strip() for s in (src or "").split(",") if s.strip()}
        if bb == "navigation":
            nav.add(nid)
    con.close()
    # navigation notes have no source_docs by design -- they index rather than
    # assert -- and retrieval already excludes them from results. Reporting them
    # as a problem would train a reader to ignore this warning.
    missing = [n for n, s in prov.items() if not s and n not in nav]
    if nav:
        print(f"note: {len(nav)} navigation notes carry no source_docs by design "
              f"and are excluded from retrieval results.")
    if missing:
        print(f"WARNING: {len(missing)}/{len(prov)} content notes declare no "
              f"source_docs and can never be credited. Run validate_notes.py --gate.")
    return prov


def score(questions: list[dict], resolve, ks: list[int], topk: int,
          budgets: list[int] | None = None, words=None) -> dict:
    """resolve(query, k) -> ordered list of (unit_id, doc-id set), ranked.

    Two ways to cut the ranked list, and they answer different questions.

    By k: the conventional report, comparable to published Recall@k numbers.

    By TOKEN BUDGET: assemble units in rank order until the budget is spent.
    This is the only fair cut between representations of different size --
    matching k gives the win to whichever arm has larger units, since 5 chunks
    of 200 words is not 5 notes of 328. H1 is a claim about how the gap moves
    with budget, so it cannot be tested on k at all.
    """
    stats = {k: {"recall": [], "all": []} for k in ks}
    bstats = {b: {"recall": [], "all": []} for b in (budgets or [])}
    qids: list[str] = []
    by_type: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    answerable = 0

    for q in questions:
        if not q["gold"]:
            continue                      # null_query: nothing to retrieve
        answerable += 1
        qids.append(q["query"])
        ranked = resolve(q["query"], topk)
        for k in ks:
            seen: set[str] = set()
            for _, unit_docs in ranked[:k]:
                seen |= unit_docs
            hit = q["gold"] & seen
            r = len(hit) / len(q["gold"])
            stats[k]["recall"].append(r)
            stats[k]["all"].append(1.0 if hit == q["gold"] else 0.0)
            by_type[q["type"]][k].append(r)

        for b in (budgets or []):
            seen, spent = set(), 0
            for uid, unit_docs in ranked:
                w = words.get(uid, 0) if words else 0
                if spent + w > b:
                    continue          # skip a unit that overruns; keep filling
                spent += w
                seen |= unit_docs
            hit = q["gold"] & seen
            bstats[b]["recall"].append(len(hit) / len(q["gold"]))
            bstats[b]["all"].append(1.0 if hit == q["gold"] else 0.0)

    return {"stats": stats, "by_type": by_type, "answerable": answerable,
            "budgets": bstats, "qids": qids}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", choices=sorted(QUESTIONS))
    ap.add_argument("--arm", choices=["notes", "chunks", "wholedoc"], required=True)
    ap.add_argument("--vault", help="notes arm: the corpus vault")
    ap.add_argument("--chunk-db", help="chunks arm: directory holding the chunk index")
    ap.add_argument("--strategies", default="bm25,hybrid,ppr")
    ap.add_argument("--k", default="2,5,10")
    ap.add_argument("--budgets", default="",
                    help="comma-separated TOKEN budgets, e.g. 512,1024,2048,4096,8192. "
                         "Assembles units in rank order until spent. This is the cut H1 "
                         "needs; k is not comparable across arms with different unit sizes.")
    ap.add_argument("--seed", default="hybrid", choices=["hybrid", "bm25"],
                    help="seed for the bfs and ppr arms")
    ap.add_argument("--limit", type=int, default=0, help="score only the first N questions")
    ap.add_argument("--covered-only", action="store_true",
                    help="score only questions whose gold documents were ALL ingested")
    ap.add_argument("--json", help="write results to this path")
    a = ap.parse_args()

    ks = sorted(int(x) for x in a.k.split(","))
    budgets = sorted(int(x) for x in a.budgets.split(",") if x.strip())
    CANDIDATE_CEILING = 400     # retrieving more per query costs time for no packing gain
    questions, _ = load_gold(a.slug)
    if a.limit:
        questions = questions[: a.limit]

    import retrieval as R

    if a.arm == "notes":
        vault = Path(a.vault or f"vaults/{a.slug}")
        if not (vault / "notes.db").exists():
            print(f"no database at {vault}/notes.db — run build_local_db.py first")
            sys.exit(2)
        prov = note_provenance(vault)
        unit_docs = lambda nid: prov.get(nid, set())          # noqa: E731
        words = unit_tokens(vault / "notes.db")
    else:
        cdir = Path(a.chunk_db or f"data/{'wholedoc' if a.arm == 'wholedoc' else 'chunks'}/{a.slug}")
        if not (cdir / "notes.db").exists():
            print(f"no chunk index at {cdir}/notes.db — run build_chunk_baseline.py first")
            sys.exit(2)
        vault = cdir
        con = sqlite3.connect(cdir / "notes.db")
        cmap = {nid: {src} for nid, src in
                con.execute("SELECT note_id, source_doc FROM notes")}
        con.close()
        words = unit_tokens(cdir / "notes.db")
        unit_docs = lambda nid: cmap.get(nid, set())          # noqa: E731

    if a.covered_only:
        # Scoring a partial ingestion against the whole question set measures
        # how much of the corpus is present, not how well the arm retrieves.
        # Both are real numbers; only one is the comparison being made.
        ingested = set()
        for docs in (prov.values() if a.arm == "notes" else cmap.values()):
            ingested |= docs
        before = len(questions)
        questions = [x for x in questions if x["gold"] and x["gold"] <= ingested]
        print(f"covered-only: {len(questions)}/{before} questions have all their "
              f"gold documents among the {len(ingested)} ingested")
        if not questions:
            print("\nNo question is fully covered by what has been ingested. "
                  "Scoring now would compare arms on evidence neither can reach; "
                  "ingest more documents first.")
            sys.exit(1)

    results = {}
    for strat in a.strategies.split(","):
        strat = strat.strip()
        if strat not in R.STRATEGIES:
            print(f"unknown strategy {strat!r}; have {', '.join(R.STRATEGIES)}")
            sys.exit(2)

        def resolve(query: str, k: int, _s=strat):
            hits = (R.STRATEGIES[_s](vault, query, k, seed="bm25")
                    if _s in ("bfs", "ppr") and a.seed == "bm25"
                    else R.STRATEGIES[_s](vault, query, k))
            return [(nid, unit_docs(nid)) for nid, _ in hits]

        # The candidate list must be long enough that the BUDGET binds, never the
        # cap. A fixed cap silently handicaps whichever arm has smaller units: at
        # 8,192 tokens a 126-token chunk arm can fit ~65 units, so a cap of 40 let
        # it assemble only ~5,050 tokens while the note arm spent its full budget.
        # That is an asymmetric handicap on the baseline, and it favours notes at
        # exactly the budget where the two were reported to converge.
        need = max(ks)
        if budgets and words:
            # Size from the 10th-percentile unit, not the minimum: a handful of
            # degenerate one-token units would otherwise demand thousands of
            # candidates per query for no gain in what actually gets packed.
            sizes = sorted(w for w in words.values() if w > 0)
            p10 = sizes[len(sizes) // 10] if sizes else 1
            need = min(CANDIDATE_CEILING, max(need, math.ceil(max(budgets) / p10) + 5))
            fits = max(budgets) / p10
            print(f"  (candidates/query {need}; p10 unit {p10} tokens, so the largest "
                  f"budget wants ~{fits:.0f} units"
                  + ("" if need >= fits else
                     f" — CAPPED at {CANDIDATE_CEILING}, the cap binds not the budget")
                  + ")")
        out = score(questions, resolve, ks, need, budgets, words)
        results[strat] = out
        print(f"\n=== {a.arm} / {strat} — {out['answerable']} answerable questions ===")
        print(f"{'k':>4}  {'Recall@k':>9}  {'All-Recall@k':>13}")
        for k in ks:
            r = out["stats"][k]["recall"]
            al = out["stats"][k]["all"]
            print(f"{k:>4}  {sum(r)/len(r):>9.3f}  {sum(al)/len(al):>13.3f}")
        if budgets:
            print(f"  {'budget':>7}  {'Recall':>9}  {'All-Recall':>11}")
            for b in budgets:
                r = out["budgets"][b]["recall"]; al = out["budgets"][b]["all"]
                print(f"  {b:>7}  {sum(r)/len(r):>9.3f}  {sum(al)/len(al):>11.3f}")
        print("  by question type (Recall@%d):" % ks[-1])
        for t, d in sorted(out["by_type"].items()):
            v = d[ks[-1]]
            print(f"    {t:<20} {sum(v)/len(v):.3f}  (n={len(v)})")

    if a.json:
        # Per-question vectors are kept, not just means. A paired bootstrap needs
        # the pairing: both arms answer the same questions, and discarding that
        # gives an interval wider than the evidence supports. qids fixes the order
        # so two runs can be aligned question by question.
        Path(a.json).write_text(json.dumps(
            {"arm": a.arm, "vault": str(vault), "answerable": None,
             "strategies": {
                 st: {"answerable": o["answerable"],
                      "qids": o["qids"],
                      "k": {str(k): {m: v for m, v in d.items()}
                            for k, d in o["stats"].items()},
                      "budget": {str(b): {m: v for m, v in d.items()}
                                 for b, d in o["budgets"].items()},
                      "by_type": {t: {str(k): v for k, v in d.items()}
                                  for t, d in o["by_type"].items()}}
                 for st, o in results.items()}}, indent=1))
        print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
