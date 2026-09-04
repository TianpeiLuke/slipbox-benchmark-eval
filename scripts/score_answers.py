#!/usr/bin/env python3
"""Score answer files from answer_from_contexts.py and compare arms pairwise.

Design notes, each of which corrects a specific defect in the earlier inline
scoring inside answer_eval.py:

REFUSAL is detected by what the answer LEADS with, not by substring. The old
test was `"insufficient" in answer`, which scored an answer that supplied the
right span and then hedged as a refusal -- that is how one run reported 0.690
over-refusal alongside 0.530 "contains".

NORMALISE maps punctuation to a space instead of deleting it. Deleting it turned
`Sam Bankman-Fried` into the single token `sambankmanfried`, so a model writing
the name with a space scored zero.

CONTAINMENT is contiguous token-subsequence, not character substring. Roughly a
quarter of gold answers are the two-character string `no`, which appears inside
`not`, `north` and `known`, so a character test scored almost any verbose answer
as correct.

GOLD CLASS is reported separately. About two thirds of the answerable questions
have a yes/no gold, and that stratum is near chance for a coin-flipping model
while the entity stratum is near ceiling. Pooling them hides both. Polarity
questions are scored by extracting the model's verdict rather than by string
equality, so a correct answer with a justification attached is not marked wrong.

BASELINES are printed in the same table, because neither stratum is interpretable
without them: `majority` always answers Yes, and a closed-book arm answers with
no context at all. An arm that fails to beat closed-book has not shown that
retrieval contributed anything.
"""
import argparse, json, re, string, sys
from collections import Counter
from pathlib import Path
import numpy as np

REFUSAL = "insufficient"
POLARITY = {"yes": "yes", "true": "yes", "no": "no", "false": "no"}


def normalise(s: str) -> str:
    s = s.lower().strip()
    s = "".join(" " if c in string.punctuation else c for c in s)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def gold_class(gold: str) -> str:
    return "polarity" if normalise(gold) in POLARITY else "entity"


def is_refusal(ans: str) -> bool:
    """Refusal when the answer LEADS with the refusal token, or is empty.

    The model was told to reply with exactly "INSUFFICIENT" and in practice
    complies but often appends an explanation, which is still a refusal. The
    opposite case is what a substring test gets wrong: "The context is
    insufficient, but the answer is Apple" supplies an answer.
    """
    n = normalise(ans)
    if not n:
        return True
    toks = n.split()
    if toks and toks[0] == "answer":
        toks = toks[1:]
    return bool(toks) and toks[0] == REFUSAL


def tok_contains(ans: str, gold: str) -> bool:
    g, a = normalise(gold).split(), normalise(ans).split()
    if not g:
        return False
    return any(a[i:i + len(g)] == g for i in range(len(a) - len(g) + 1))


def verdict(ans: str) -> str | None:
    """The yes/no the model actually committed to, from its leading token."""
    for line in ans.splitlines():
        n = normalise(line)
        if n:
            return POLARITY.get(n.split()[0])
    return None


def correct(ans: str, gold: str) -> float:
    """One binary outcome per question, appropriate to the gold's class."""
    if is_refusal(ans):
        return 0.0
    if gold_class(gold) == "polarity":
        return float(verdict(ans) == normalise(gold))
    return float(tok_contains(ans, gold))


def load(path: Path) -> dict:
    rows, errs = {}, 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("err"):
            errs += 1
            continue
        ans = r.get("answer", "")
        # Nulls carry the literal gold "Insufficient information." in the raw
        # benchmark; treat them as having no gold so content metrics stay off.
        gold = "" if r.get("null") else (r.get("gold") or "")
        rows[r["qid"]] = {
            "answer": ans, "gold": gold, "null": bool(r.get("null")),
            "units": r.get("units", 0), "refused": is_refusal(ans),
            "cls": gold_class(gold) if gold else "null",
            "correct": correct(ans, gold) if gold else 0.0,
        }
    return rows, errs


def boot(d: np.ndarray, rng, n=4000):
    if len(d) == 0:
        return 0.0, 0.0
    bs = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(n)])
    return float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", required=True, help="name=path.jsonl ...")
    ap.add_argument("--pairs", nargs="*", default=[], help="a:b paired comparisons")
    ap.add_argument("--json")
    a = ap.parse_args()

    arms, errors = {}, {}
    for spec in a.arms:
        name, _, p = spec.partition("=")
        arms[name], errors[name] = load(Path(p))

    # Majority-class baseline, no LLM call. The majority is computed PER STRATUM,
    # because the two strata have different modes and a single constant answer
    # would score zero on one of them and understate the floor. This matters here:
    # the coverage-fair subset is restricted to 37 documents, so the entity
    # stratum has very few distinct golds and its mode is a large share of it.
    any_arm = next(iter(arms.values()))
    modes = {}
    for cls in ("entity", "polarity"):
        golds = [v["gold"] for v in any_arm.values() if v["cls"] == cls and v["gold"]]
        modes[cls] = Counter(normalise(g) for g in golds).most_common(1)[0][0] if golds else ""
    arms["_majority"] = {q: {**v, "answer": modes.get(v["cls"], ""), "refused": False,
                             "correct": correct(modes.get(v["cls"], ""), v["gold"])
                             if v["gold"] else 0.0}
                         for q, v in any_arm.items()}
    errors["_majority"] = 0
    print(f"\nmajority baseline answers: " +
          ", ".join(f"{c}={modes[c]!r}" for c in modes))

    rng = np.random.default_rng(20260902)
    w = max(len(n) for n in arms)
    print(f"\n{'arm':<{w}}  {'n_ent':>6}{'entity':>8}  {'n_pol':>6}{'polarity':>9}"
          f"{'macro':>8}{'refuse':>8}{'abstain@null':>14}{'units':>7}{'err':>5}")
    summary = {}
    for n, rows in arms.items():
        ent = [r for r in rows.values() if r["cls"] == "entity"]
        pol = [r for r in rows.values() if r["cls"] == "polarity"]
        nul = [r for r in rows.values() if r["null"]]
        m = lambda v, f: sum(x[f] for x in v) / len(v) if v else float("nan")
        e_acc, p_acc = m(ent, "correct"), m(pol, "correct")
        macro = np.nanmean([e_acc, p_acc])
        ans_all = ent + pol
        summary[n] = {"n_entity": len(ent), "entity": e_acc, "n_polarity": len(pol),
                      "polarity": p_acc, "macro": float(macro),
                      "refused": m(ans_all, "refused"),
                      "abstain_null": m(nul, "refused"), "units": m(ans_all, "units"),
                      "n_failed": errors[n]}
        s = summary[n]
        print(f"{n:<{w}}  {len(ent):>6}{e_acc:>8.3f}  {len(pol):>6}{p_acc:>9.3f}"
              f"{macro:>8.3f}{s['refused']:>8.3f}{s['abstain_null']:>14.3f}"
              f"{s['units']:>7.1f}{errors[n]:>5}")

    comparisons = {}
    for pair in a.pairs:
        x, _, y = pair.partition(":")
        if x not in arms or y not in arms:
            print(f"\n!! unknown pair {pair}", file=sys.stderr); continue
        print(f"\n{y} - {x}")
        comparisons[pair] = {}
        for cls in ("entity", "polarity", "both"):
            shared = [q for q in arms[x] if q in arms[y] and not arms[x][q]["null"]
                      and (cls == "both" or arms[x][q]["cls"] == cls)]
            if not shared:
                continue
            d = np.array([arms[y][q]["correct"] - arms[x][q]["correct"] for q in shared])
            lo, hi = boot(d, rng)
            sig = "significant" if (lo > 0 or hi < 0) else "ns"
            print(f"   {cls:<9} n={len(shared):<5}{d.mean():+.3f}   [{lo:+.3f}, {hi:+.3f}]  {sig}")
            comparisons[pair][cls] = {"n": len(shared), "delta": float(d.mean()),
                                      "ci": [lo, hi], "significant": sig == "significant"}

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"arms": summary, "comparisons": comparisons}, indent=2))
    print()


if __name__ == "__main__":
    main()
