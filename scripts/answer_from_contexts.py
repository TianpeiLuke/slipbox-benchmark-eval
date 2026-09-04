#!/usr/bin/env python3
"""
Answer from precomputed contexts. No torch, no embeddings, a few MB resident.

Pairs with dump_contexts.py. Checkpoints every answer, so a kill costs one call.

    python3 scripts/answer_from_contexts.py contexts/slots_chunks.jsonl \
        --backend cline --model qwen/qwen3.8-flash --out experiments/runs5/qf_slots.chunks.jsonl
"""
from __future__ import annotations
import argparse, json, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer_eval import BACKENDS, SYSTEM, USER, REFUSAL, normalise, f1   # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("contexts")
    ap.add_argument("--backend", default="cline")
    ap.add_argument("--model", default="qwen/qwen3.8-flash")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = [json.loads(l) for l in Path(a.contexts).read_text().splitlines() if l.strip()]
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    done = {}
    if out.exists():
        for l in out.read_text().splitlines():
            try:
                r = json.loads(l)
            except json.JSONDecodeError:
                continue
            if "qid" in r and not r.get("err"):
                done[r["qid"]] = r
    todo = [r for r in rows if r["qid"] not in done]
    print(f"{len(rows)} contexts, {len(done)} already answered, {len(todo)} to do")

    ask = BACKENDS[a.backend]
    lock = threading.Lock()

    def one(r):
        u = USER.format(context=r["context"], question=r["qid"])
        try:
            ans = ask(SYSTEM, u, a.model)
        except Exception as e:
            # Record the failure instead of returning early. Returning here
            # skipped the append below, so a failed call vanished from the
            # artifact entirely and a degraded run looked like a smaller clean
            # one. err rows are excluded from `done` so a re-run retries them.
            rec = {"qid": r["qid"], "err": str(e)[:200]}
            with lock:
                with out.open("a") as fh:
                    fh.write(json.dumps(rec) + "\n")
            return rec
        gold = r["gold"]
        rec = {"qid": r["qid"], "answer": ans, "gold": gold, "null": r["null"],
               "units": r["units"], "refused": REFUSAL.lower() in ans.lower(),
               "em": float(normalise(ans) == normalise(gold)) if gold else 0.0,
               "f1": f1(ans, gold) if gold else 0.0,
               "contains": float(bool(gold) and normalise(gold) in normalise(ans))}
        with lock:
            with out.open("a") as fh:
                fh.write(json.dumps(rec) + "\n")
        return rec

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        res = list(ex.map(one, todo))
    errs = [r for r in res if "err" in r]
    if errs:
        print(f"{len(errs)}/{len(res)} failed, e.g. {errs[0]['err']}")
    total = len(done) + len(res) - len(errs)
    print(f"answered {total}/{len(rows)}")


if __name__ == "__main__":
    main()
