#!/usr/bin/env python3
"""
Stage 1 of the v2 pipeline: decompose a document into THOUGHT-ATOMIC notes.

Implements plan-digestion Step 3 as it now stands. The planner is told what one
thought is for each building block, what a note may weigh, and what padding
looks like -- the three things the v1 rules did not say and which produced notes
carrying one thought in 190 words.

    python3 scripts/plan_v2.py --docs experiments/plans/pilot_v2_docs.json \
        --out experiments/plans/v2/plan.jsonl
"""
from __future__ import annotations
import argparse, json, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from answer_eval import BACKENDS   # noqa: E402
from llm_call import call, Format   # noqa: E402

SYSTEM = """You decompose a source document into THOUGHT-ATOMIC notes for a knowledge vault.

TWO CONSTRAINTS, both required and orthogonal:
- one building_block per note (its KIND)
- one thought of that block's kind per note (HOW MANY)

What one thought is, by block:
  concept                one definition (term, genus and differentia, boundary)
  model                  one relation (entities, the relation, conditions it holds under)
  procedure              one OUTCOME (precondition, steps, verifiable postcondition) - NOT one step
  empirical_observation  one measurement (subject, metric, value, conditions, provenance)
  argument               one claim with its warrant and scope
  counter_argument       one objection, naming its target
  hypothesis             one testable proposition with its falsifier
  navigation             one index scope

SPLIT TEST: if a proposed note would answer two DIFFERENT questions, it is two notes.
STOPPING RULE: do not split when the relation between the halves cannot be stated in one line.

TARGET WEIGHT for the note body, in words:
  empirical_observation 40-90 | concept 50-110 | model/hypothesis/counter_argument 60-130
  argument 70-150 | procedure 80-250 | navigation 40-120

A note must be SELF-SUFFICIENT: it names its subject, carries the date, resolves every
reference. Do not buy brevity by deleting context.

Return STRICT JSON only:
{"notes":[{"slug":"snake_case_name","bb":"<block>","thought":"<the single thought, one sentence>",
"target_words":<int>,"covers":"<which part of the source>"}]}
No prose outside the JSON."""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", required=True)
    ap.add_argument("--slug", default="multihop_rag")
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", default="cline")
    ap.add_argument("--model", default="qwen/qwen3.8-flash")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--chars", type=int, default=6000)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    docs = json.loads(Path(a.docs).read_text())
    if a.limit:
        docs = docs[: a.limit]
    corpus = ROOT / "data/corpus" / a.slug
    idx = json.loads((corpus / "index.json").read_text())

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for l in out.read_text().splitlines():
            try: done.add(json.loads(l)["doc"])
            except Exception: pass
    todo = [d for d in docs if d not in done]
    print(f"{len(docs)} documents, {len(done)} planned, {len(todo)} to do")

    ask = BACKENDS[a.backend]; lock = threading.Lock()

    def one(doc):
        meta = idx.get(doc, {})
        text = (corpus / f"{doc}.txt").read_text()[: a.chars]
        user = (f"DOCUMENT {doc}\nTITLE: {meta.get('title','')}\n"
                f"PUBLISHER: {meta.get('publisher','')}  DATE: {(meta.get('date') or '')[:10]}\n\n"
                f"{text}\n\nDecompose into thought-atomic notes.")
        def parse(raw):
            m = re.search(r"\{.*\}", raw, re.S)
            if not m:
                raise Format("no json object")
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError as e:
                raise Format(f"bad json: {e}")

        obj, status = call(ask, SYSTEM, user, a.model, parse)
        if obj is None:
            return doc, 0, status
        notes = obj.get("notes") or []
        if not notes: return doc, 0, "empty"
        with lock, out.open("a") as fh:
            fh.write(json.dumps({"doc": doc, "title": meta.get("title",""),
                                 "date": (meta.get("date") or "")[:10],
                                 "publisher": meta.get("publisher",""),
                                 "notes": notes}) + "\n")
        return doc, len(notes), None

    ok = errs = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for doc, n, err in ex.map(one, todo):
            ok += n; errs += bool(err)
    print(f"planned {ok} notes across {len(todo)-errs} documents; {errs} failed")


if __name__ == "__main__":
    main()
