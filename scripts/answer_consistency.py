#!/usr/bin/env python3
"""
Does an arm give the same answer when it is given more of the same context?

A representation that supplies COHERENT context should answer stably as
retrieval depth grows -- the extra units add detail, not contradiction. One
that supplies fragments should flip, because each new fragment can change what
the assembled context appears to say. That is a property of the representation,
measurable without any gold label, and it is the closest thing to "consistent
context" that this harness can observe.

Flips are then split by whether they helped or hurt, because stability is only
a virtue if the answers were not stably wrong.

    python3 scripts/answer_consistency.py \
        --shallow experiments/runs5/qf_slots.notes.jsonl \
        --deep    experiments/runs5/qf_k30_notes.jsonl --label notes
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer_eval import normalise   # noqa: E402


def load(p):
    return {r["qid"]: r for r in
            (json.loads(l) for l in Path(p).read_text().splitlines() if l.strip())
            if "err" not in r}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shallow", required=True)
    ap.add_argument("--deep", required=True)
    ap.add_argument("--label", default="arm")
    a = ap.parse_args()

    S, D = load(a.shallow), load(a.deep)
    sh = [q for q in S if q in D]
    ans = [q for q in sh if not S[q]["null"]]
    nl = [q for q in sh if S[q]["null"]]

    same = sum(1 for q in ans if normalise(S[q]["answer"]) == normalise(D[q]["answer"]))
    to_ans = [q for q in ans if S[q]["refused"] and not D[q]["refused"]]
    to_ref = [q for q in ans if not S[q]["refused"] and D[q]["refused"]]
    changed = [q for q in ans
               if not S[q]["refused"] and not D[q]["refused"]
               and normalise(S[q]["answer"]) != normalise(D[q]["answer"])]
    gain = sum(1 for q in changed if D[q]["f1"] > S[q]["f1"])
    loss = sum(1 for q in changed if D[q]["f1"] < S[q]["f1"])

    n = len(ans)
    print(f"{a.label}: {n} answerable questions answered at both depths")
    print(f"  identical answer at k=10 and k=30      {same/n:6.1%}")
    print(f"  refused shallow -> answered deep       {len(to_ans)/n:6.1%}  ({len(to_ans)})")
    print(f"  answered shallow -> refused deep       {len(to_ref)/n:6.1%}  ({len(to_ref)})")
    print(f"  answered both, answer CHANGED          {len(changed)/n:6.1%}  ({len(changed)})")
    if changed:
        print(f"      of those, better {gain}  worse {loss}  equal {len(changed)-gain-loss}")
    print(f"  F1 shallow {sum(S[q]['f1'] for q in ans)/n:.3f} -> deep "
          f"{sum(D[q]['f1'] for q in ans)/n:.3f}")
    if nl:
        sa = sum(S[q]["refused"] for q in nl)/len(nl)
        da = sum(D[q]["refused"] for q in nl)/len(nl)
        print(f"  abstain@null {sa:.3f} -> {da:.3f}  (n={len(nl)})")


if __name__ == "__main__":
    main()
