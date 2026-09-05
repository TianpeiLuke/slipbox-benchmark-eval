#!/usr/bin/env python3
"""Score retrieval strategies on CHAIN COMPLETENESS, the thing refusal tracks.

The refusal diagnosis showed the model abstains as a function of how much of a
question's supporting chain is present -- 0.65 refusal with none of it, 0.25
with some, 0.08 with all -- and that answer presence barely moves between
strategies. So the quantity worth optimising is the share of questions whose
chain arrives COMPLETE, and this scores that directly without spending a single
LLM call.

Probes are derived from question text only; the gold evidence facts are used to
SCORE, never to steer.
"""
import argparse, json, random, sqlite3, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval as R                                             # noqa: E402
from answer_eval import build_context                             # noqa: E402
from score_retrieval import unit_tokens                           # noqa: E402
from score_answers import gold_class, tok_contains, normalise     # noqa: E402
from refusal_diagnosis import frac_facts_present                  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--strategies", nargs="+", required=True)
    ap.add_argument("--questions", required=True)
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--budget", type=int, default=2048)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--condition", default="tokens", choices=["tokens", "slots"])
    ap.add_argument("--json")
    a = ap.parse_args()

    raw = json.loads((ROOT / "data/raw/multihop_rag/MultiHopRAG.json").read_text())
    pin = set(json.loads(Path(a.questions).read_text()))
    qs = [q for q in raw if q.get("evidence_list") and q.get("answer")
          and q["query"] in pin]
    random.seed(20260902); random.shuffle(qs); qs = qs[: a.sample]
    ev = {q["query"]: [e.get("fact", "") for e in q["evidence_list"] if e.get("fact")]
          for q in qs}

    vault = Path(a.vault)
    con = sqlite3.connect(vault / "notes.db")
    bodies = dict(con.execute("SELECT note_id, body FROM notes"))
    srcs = {n: {x.strip() for x in (s or "").split(",") if x.strip()}
            for n, s in con.execute("SELECT note_id, source_doc FROM notes")}
    con.close()
    toks = unit_tokens(vault / "notes.db", evidence_only=True)

    idx = json.loads((ROOT / "data/corpus/multihop_rag/index.json").read_text())
    by_title = {v["title"]: d for d, v in idx.items()}

    print(f"\n{Path(a.vault).name}   n={len(qs)}   {a.condition} budget={a.budget}\n")
    print(f"{'strategy':<10}{'chain COMPLETE':>16}{'mean chain':>12}{'answer present':>16}"
          f"{'doc recall':>12}{'units':>7}{'ent only':>10}")
    out = {}
    for name in a.strategies:
        comp, chains, present, docr, units, ent_comp = [], [], [], [], [], []
        for q in qs:
            ctx, n = build_context(vault, bodies, toks, q["query"],
                                   a.condition, a.k, a.budget, name)
            fr = frac_facts_present(ctx, ev.get(q["query"], []))
            if np.isnan(fr):
                continue
            gold = {by_title.get(e.get("title", "")) for e in q["evidence_list"]}
            gold = {g for g in gold if g}
            # documents represented in the assembled context
            got = set()
            for nid, b in bodies.items():
                if b and b[:60] and b[:60] in ctx:
                    got |= srcs.get(nid, set())
            chains.append(fr); comp.append(float(fr >= 0.999)); units.append(n)
            present.append(float(tok_contains(ctx, q.get("answer") or "")))
            docr.append(len(got & gold) / len(gold) if gold else np.nan)
            if gold_class(q.get("answer") or "") == "entity":
                ent_comp.append(float(fr >= 0.999))
        m = lambda v: float(np.nanmean(v)) if v else float("nan")
        out[name] = {"chain_complete": m(comp), "mean_chain": m(chains),
                     "answer_present": m(present), "doc_recall": m(docr),
                     "units": m(units), "chain_complete_entity": m(ent_comp),
                     "n": len(comp)}
        r = out[name]
        print(f"{name:<10}{r['chain_complete']:>16.3f}{r['mean_chain']:>12.3f}"
              f"{r['answer_present']:>16.3f}{r['doc_recall']:>12.3f}"
              f"{r['units']:>7.1f}{r['chain_complete_entity']:>10.3f}")

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, indent=2))
    print()


if __name__ == "__main__":
    main()
