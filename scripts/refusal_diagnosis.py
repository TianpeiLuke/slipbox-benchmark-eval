#!/usr/bin/env python3
"""Explain WHEN the model refuses, given the context it actually received.

Refusal is the dominant channel in the answer-quality results: per-source
capping raises accuracy entirely by refusing less, not by answering better
(conditional accuracy is ~99% in every arm). That makes the question "when does
it refuse?" the one worth answering, and it decides how much headroom is left.

Two levels are separated because they give different answers:

  answer presence -- is the gold answer string in the assembled context?
  chain presence  -- what fraction of the question's gold evidence facts are in
                     the context, judged by content-word overlap?

Answer presence turns out NOT to be the thing that moves refusal: capping leaves
it essentially unchanged (484 vs 484 questions on one vault) while cutting
refusals substantially. Chain completeness does move it, monotonically.

No LLM calls and no torch: this reads contexts and answers already on disk.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_answers import gold_class, is_refusal, tok_contains, normalise  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def frac_facts_present(ctx: str, facts: list[str], thr: float = 0.6) -> float:
    """Fraction of gold evidence facts whose content words mostly appear in ctx.

    Content words only (>3 chars) and a 0.6 threshold, because a note paraphrases
    rather than quotes: requiring exact sentences would score a correct
    paraphrase as absent, which is the failure mode fact-level cosine scoring has.
    """
    cw = set(normalise(ctx).split())
    hits = []
    for f in facts:
        ft = [t for t in normalise(f).split() if len(t) > 3]
        if ft:
            hits.append(sum(t in cw for t in ft) / len(ft) >= thr)
    return float(np.mean(hits)) if hits else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", required=True,
                    help="name=ctx.jsonl:ans.jsonl ...")
    ap.add_argument("--stratum", default="entity", choices=["entity", "polarity", "both"])
    ap.add_argument("--json")
    a = ap.parse_args()

    raw = json.loads((ROOT / "data/raw/multihop_rag/MultiHopRAG.json").read_text())
    ev = {q["query"]: [e.get("fact", "") for e in q.get("evidence_list", []) if e.get("fact")]
          for q in raw if q.get("evidence_list")}

    out = {}
    w = max(len(s.partition("=")[0]) for s in a.arms)
    print(f"\n{'arm':<{w}}{'P(ref|absent)':>15}{'P(ref|present)':>16}"
          f"{'chain none':>12}{'some':>8}{'all':>7}{'n(all)':>8}")
    for spec in a.arms:
        name, _, paths = spec.partition("=")
        cp, _, an = paths.partition(":")
        ctx = {json.loads(l)["qid"]: json.loads(l)
               for l in Path(cp).read_text().splitlines() if l.strip()}
        ans = {json.loads(l)["qid"]: json.loads(l)
               for l in Path(an).read_text().splitlines() if l.strip()}
        absent, present, buckets = [], [], {"none": [], "some": [], "all": []}
        for q, c in ctx.items():
            if c["null"] or not c.get("gold"):
                continue
            if a.stratum != "both" and gold_class(c["gold"]) != a.stratum:
                continue
            if q not in ans or ans[q].get("err"):
                continue
            ref = is_refusal(ans[q]["answer"])
            if not tok_contains(c["context"], c["gold"]):
                absent.append(ref); continue
            present.append(ref)
            fr = frac_facts_present(c["context"], ev.get(q, []))
            if np.isnan(fr):
                continue
            buckets["all" if fr >= 0.999 else ("some" if fr > 0 else "none")].append(ref)
        m = lambda v: float(np.mean(v)) if v else float("nan")
        out[name] = {"p_refuse_answer_absent": m(absent), "n_absent": len(absent),
                     "p_refuse_answer_present": m(present), "n_present": len(present),
                     "chain": {k: {"n": len(v), "p_refuse": m(v)} for k, v in buckets.items()}}
        print(f"{name:<{w}}{m(absent):>15.3f}{m(present):>16.3f}"
              f"{m(buckets['none']):>12.3f}{m(buckets['some']):>8.3f}"
              f"{m(buckets['all']):>7.3f}{len(buckets['all']):>8}")

    print("\nHeadroom: refusals on questions whose answer was already in context")
    print(f"{'arm':<{w}}{'present':>9}{'refused':>9}{'wasted':>9}")
    for name, r in out.items():
        n, p = r["n_present"], r["p_refuse_answer_present"]
        print(f"{name:<{w}}{n:>9}{round(n * p):>9}{p:>9.1%}")

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, indent=2))
    print()


if __name__ == "__main__":
    main()
