#!/usr/bin/env python3
"""
End-to-end answer accuracy: does retrieved context let a model answer the question?

This is H7, unrun since FZ 8c5b11a13a5g1b5e. Every result before it scores
RETRIEVAL, and [FZ 5h] showed why that is not enough: the notes arm's advantage
at matched slots is largely document-level credit, and whether a REPHRASED fact
still answers a question cannot be settled by any similarity threshold. Only
generation can settle it.

Two conditions, because the whole series turns on which resource is scarce:

  --condition slots    top k units, however many tokens that costs
  --condition tokens   units in rank order until a token budget is full

Metrics
-------
Answerable questions (2,255):
  EM          exact match after normalising case, articles and punctuation
  F1          SQuAD-style token overlap -- the primary metric, since gold
              answers are short factual strings and a model may phrase the same
              entity differently
  contains    the gold string appears in the answer; lenient, catches a correct
              answer buried in a verbose one
  refused     model said INSUFFICIENT on a question that does have an answer
              (over-abstention -- reported so abstention cannot be gamed)

Null questions (301):
  abstained   model correctly declined. These 301 exist to test hallucination
              and no experiment in this series has ever used them. A system that
              answers them confidently is worse than one that scores lower on
              recall, and nothing before this could see that.

Backends
--------
  openai      OPENAI_API_KEY, any chat model (default gpt-5-nano)
  anthropic   ANTHROPIC_API_KEY
  cline       the Cline CLI: `cline --json -m MODEL --auto-approve true PROMPT`,
              parsed from newline-delimited JSON. Requires `npm i -g cline` and
              an interactive `cline auth` first -- neither can be done headless.

    python3 scripts/answer_eval.py multihop_rag \
        --arms notes=vaults/multihop_rag chunks=data/chunks/multihop_rag \
        --backend openai --model gpt-5-nano --condition tokens --budget 2048 \
        --sample 200 --json experiments/runs5/answers.json
"""

from __future__ import annotations

import argparse, json, os, re, string, subprocess, sys, random, threading, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval as R                             # noqa: E402
from score_retrieval import strip_scaffolding      # noqa: E402

REFUSAL = "INSUFFICIENT"

# FIXED across every arm, condition and run. The only thing that varies between
# the two arms is the retrieved context, so any difference in answer quality is
# attributable to the retrieval representation and not to prompting.
SYSTEM = (
    "You are a question-answering system. Answer strictly from the context you "
    "are given, never from prior knowledge.\n"
    "- Reply with the shortest span that answers the question: a name, a number, "
    "a date, or yes/no.\n"
    "- Do not explain, do not restate the question, do not cite the context.\n"
    f"- If the context does not contain the answer, reply with exactly: {REFUSAL}\n"
    "- Never call a tool. Reply with the answer text only."
)

USER = """Context:
{context}

Question: {question}
Answer:"""


# ---------------------------------------------------------------- scoring

def normalise(s: str) -> str:
    s = s.lower().strip()
    s = "".join(c for c in s if c not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def f1(pred: str, gold: str) -> float:
    p, g = normalise(pred).split(), normalise(gold).split()
    if not p or not g:
        return float(p == g)
    common = Counter(p) & Counter(g)
    n = sum(common.values())
    if not n:
        return 0.0
    prec, rec = n / len(p), n / len(g)
    return 2 * prec * rec / (prec + rec)


# ---------------------------------------------------------------- backends

def ask_openai(system: str, user: str, model: str) -> str:
    from openai import OpenAI
    r = OpenAI().chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}])
    return (r.choices[0].message.content or "").strip()


def ask_anthropic(system: str, user: str, model: str) -> str:
    import anthropic
    r = anthropic.Anthropic().messages.create(
        model=model, max_tokens=64, system=system,
        messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in r.content if b.type == "text").strip()


_CLINE_SANDBOX = Path(os.environ.get("CLINE_SANDBOX", "/tmp/cline_qa_sandbox"))


def ask_cline(system: str, user: str, model: str) -> str:
    """Cline CLI, one shot, no tools, isolated state.

    cline is an agent, not a completion endpoint, so three things are forced:
    --cwd points at an empty sandbox so a stray tool call cannot touch the repo,
    --auto-approve false stops it acting on one, and -s replaces its coding
    system prompt with ours. It still bills ~7,000 tokens of tool schemas per
    call regardless -- constant across arms, so the comparison holds, but it is
    the reason a run is not cheap.

    The answer is the `text` field of the final run_result line; the streamed
    reasoning lines are ignored so a reasoning model's scratchpad is never
    scored.
    """
    _CLINE_SANDBOX.mkdir(parents=True, exist_ok=True)
    # NO --data-dir. Credentials live in the default ~/.cline/data, and pointing
    # --data-dir at a fresh path creates empty state whose every call returns
    # "Unauthorized" -- which is what silently hung the first two runs. The
    # sandbox is enforced by --cwd instead, which is what actually bounds file
    # access; state is shared across workers and cline keys sessions per run.
    cmd = ["cline", "-P", os.environ.get("CLINE_PROVIDER", "cline"),
           "--cwd", str(_CLINE_SANDBOX),
           "--auto-approve", "false", "-t", "120", "--json", "-s", system]
    if model:
        cmd += ["-m", model]
    cmd.append(user)
    # An OAuth token can expire mid-run, and cline refreshes it on a later call.
    # Without a retry a five-minute expiry silently deletes hundreds of
    # questions from the sample, because failed calls are excluded from the
    # metrics -- so a degraded run would look like a smaller clean one.
    last = ""
    for attempt in range(4):
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired:
            # A wedged cline hub daemon makes calls hang indefinitely. A long
            # per-call timeout turns that into a run that never finishes rather
            # than one that fails, so keep it short and let the retry decide.
            last = "timeout"; time.sleep(2 * (attempt + 1)); continue
        joined = out.stdout
        if "Unauthorized" in joined or "rate limit" in joined.lower() or \
                (out.returncode != 0 and not joined.strip()):
            last = "unauthorized/transient"
            time.sleep(3 * (attempt + 1))
            continue
        break
    else:
        raise RuntimeError(f"cline failed after 4 attempts ({last})")
    text, cost = None, 0.0
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("type") == "run_result":
            text = (o.get("text") or "").strip()
            cost = (o.get("aggregateUsage") or {}).get("totalCost", 0.0) or \
                   (o.get("usage") or {}).get("totalCost", 0.0)
    if text and text.lower().startswith(("unauthorized", "error:")):
        raise RuntimeError(f"cline backend refused the call: {text[:160]}")
    if text is None:
        raise RuntimeError(f"cline gave no run_result (rc={out.returncode}): "
                           f"{out.stderr[:200] or out.stdout[-200:]}")
    with _COST_LOCK:
        _COST[0] += cost
    return text


_COST = [0.0]
_COST_LOCK = threading.Lock()


BACKENDS = {"openai": ask_openai, "anthropic": ask_anthropic, "cline": ask_cline}


# ---------------------------------------------------------------- context

def build_context(vault: Path, bodies: dict, toks: dict, query: str,
                  condition: str, k: int, budget: int,
                  strategy: str = "hybrid") -> tuple[str, int]:
    """Assemble the context an arm hands the model.

    The strategy is per-arm on purpose. Holding it fixed at `hybrid` isolates
    the REPRESENTATION, which is the controlled comparison. Setting the chunk
    arm to `dense` instead reproduces a textbook RAG stack and compares whole
    SYSTEMS -- two variables at once, and worth reporting separately rather
    than instead, since dense-only is the weaker chunk baseline and a notes win
    against it would be partly a win against the retriever.
    """
    fn = getattr(R, strategy)
    ranked = [n for n, _ in fn(vault, query, max(k, 40))]
    picked, used = [], 0
    for nid in ranked:
        t = toks.get(nid, 0)
        if condition == "slots":
            if len(picked) >= k:
                break
        else:
            if used + t > budget:
                continue          # skip an overrunning unit, keep filling
            if used >= budget:
                break
        picked.append(nid); used += t
    return "\n\n---\n\n".join(strip_scaffolding(bodies[n]) for n in picked), len(picked)


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--arms", nargs="+", required=True,
                    help="name=path[:strategy]  (strategy defaults to hybrid; "
                         "use :dense on the chunk arm for a textbook RAG stack)")
    ap.add_argument("--backend", choices=sorted(BACKENDS), default="openai")
    ap.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-5-nano"))
    ap.add_argument("--condition", choices=["slots", "tokens"], default="tokens")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--budget", type=int, default=2048)
    ap.add_argument("--sample", type=int, default=200)
    ap.add_argument("--nulls", type=int, default=50,
                    help="null questions to include, to measure abstention")
    ap.add_argument("--workers", type=int, default=8)
    # Bound the work per invocation so a run always finishes before anything can
    # kill it. With checkpointing, repeated short invocations converge on a full
    # run and a kill costs at most one batch.
    ap.add_argument("--max-new", type=int, default=0,
                    help="answer at most N not-yet-checkpointed questions, then stop")
    ap.add_argument("--json")
    a = ap.parse_args()

    import sqlite3
    from concurrent.futures import ThreadPoolExecutor
    from score_retrieval import unit_tokens

    raw = json.loads((ROOT / "data/raw" / a.slug / "MultiHopRAG.json").read_text())
    random.seed(20260902)
    answerable = [q for q in raw if q.get("evidence_list") and q.get("answer")]
    nulls = [q for q in raw if not q.get("evidence_list")]
    random.shuffle(answerable); random.shuffle(nulls)
    qs = answerable[: a.sample] + nulls[: a.nulls]
    print(f"{len(qs)} questions ({min(a.sample, len(answerable))} answerable, "
          f"{min(a.nulls, len(nulls))} null)   backend={a.backend} model={a.model}   "
          f"condition={a.condition} " + (f"budget={a.budget}" if a.condition == "tokens"
                                         else f"k={a.k}"))

    ask = BACKENDS[a.backend]
    out = {}
    for spec in a.arms:
        name, _, rest = spec.partition("=")
        vp, _, strat = rest.partition(":")
        strat = strat or "hybrid"
        vault = Path(vp)
        con = sqlite3.connect(vault / "notes.db")
        bodies = {n: b for n, b in con.execute("SELECT note_id, body FROM notes")}
        con.close()
        toks = unit_tokens(vault / "notes.db", evidence_only=True)

        def one(q):
            ctx, nunits = build_context(vault, bodies, toks, q["query"],
                                        a.condition, a.k, a.budget, strat)
            u = USER.format(context=ctx, question=q["query"])
            try:
                ans = ask(SYSTEM, u, a.model)
            except Exception as e:
                return {"err": str(e)[:200]}
            gold = q.get("answer") or ""
            refused = REFUSAL.lower() in ans.lower()
            return {
                "qid": q["query"],
                "answer": ans,
                "gold": gold,
                "null": not q.get("evidence_list"),
                "units": nunits,
                "refused": refused,
                "em": float(normalise(ans) == normalise(gold)) if gold else 0.0,
                "f1": f1(ans, gold) if gold else 0.0,
                "contains": float(bool(gold) and normalise(gold) in normalise(ans)),
            }

        # warm the embedding model and per-vault caches on ONE thread first;
        # eight threads racing the lazy loader is what crashed the slots run
        build_context(vault, bodies, toks, qs[0]["query"], a.condition, a.k,
                      a.budget, strat)
        # Checkpoint every completed question as it lands. A long cline run has
        # been killed by token expiry, resource pressure and manual stops, and
        # each time an all-or-nothing run lost every answer it had paid for.
        # With a JSONL sidecar a restart skips what is already done.
        ck = Path(a.json).with_suffix(f".{name}.jsonl") if a.json else None
        done = {}
        if ck and ck.exists():
            for line in ck.read_text().splitlines():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue          # a kill mid-write truncates the last line
                if "qid" in r:
                    done[r["qid"]] = r
            if done:
                print(f"  {name}: resuming, {len(done)} already answered")

        todo = [q for q in qs if q["query"] not in done]
        if a.max_new and len(todo) > a.max_new:
            print(f"  {name}: {len(todo)} remaining, doing {a.max_new} this batch")
            todo = todo[: a.max_new]
        lock = threading.Lock()

        def one_ck(q):
            r = one(q)
            r.setdefault("qid", q["query"])
            if ck:
                with lock:
                    with ck.open("a") as fh:
                        fh.write(json.dumps(r) + "\n")
            return r

        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            fresh = list(ex.map(one_ck, todo))
        res = list(done.values()) + fresh
        errs = [r for r in res if "err" in r]
        if errs:
            frac = len(errs) / len(res)
            print(f"  {name}: {len(errs)}/{len(res)} call(s) FAILED ({frac:.1%}), "
                  f"e.g. {errs[0]['err']}")
            if frac > 0.05:
                print(f"  !! {name}: more than 5% of calls failed. The metrics below "
                      f"are computed on survivors only and are NOT comparable to a "
                      f"clean run. Re-run before using them.")
        res = [r for r in res if "err" not in r]
        ans_r = [r for r in res if not r["null"]]
        null_r = [r for r in res if r["null"]]
        mean = lambda v, f: sum(x[f] for x in v) / len(v) if v else 0.0
        out[name] = {
            "n_answerable": len(ans_r), "n_null": len(null_r), "n_failed": len(errs),
            "em": mean(ans_r, "em"), "f1": mean(ans_r, "f1"),
            "contains": mean(ans_r, "contains"),
            "over_refusal": mean(ans_r, "refused"),
            "abstained_on_null": mean(null_r, "refused"),
            "strategy": strat,
            "mean_units": mean(res, "units"),
            "per_question": res,
        }

    w = max(len(n) for n in out)
    print(f"\n{'arm':<{w}}   units      EM       F1  contains   over-refuse   abstain@null")
    for n, r in out.items():
        print(f"{n:<{w}}   {r['mean_units']:5.1f}   {r['em']:.3f}   {r['f1']:.3f}"
              f"     {r['contains']:.3f}        {r['over_refusal']:.3f}          "
              f"{r['abstained_on_null']:.3f}")
    if len(out) == 2:
        (x, rx), (y, ry) = out.items()
        print(f"\n{y} - {x}:  F1 {ry['f1']-rx['f1']:+.3f}   EM {ry['em']-rx['em']:+.3f}   "
              f"abstain@null {ry['abstained_on_null']-rx['abstained_on_null']:+.3f}")
    if _COST[0]:
        print(f"\ncline spend this run: ${_COST[0]:.2f}")
    incomplete = [n for n, r in out.items()
                  if r["n_answerable"] + r["n_null"] < len(qs)]
    if incomplete:
        print(f"\nPARTIAL: {', '.join(incomplete)} not finished. Re-run the same "
              f"command to resume; the aggregate file is not written yet.")
    if a.json and not incomplete:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
