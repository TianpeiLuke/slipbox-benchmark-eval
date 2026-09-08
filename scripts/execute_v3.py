#!/usr/bin/env python3
"""
Stage 3 of the v3 pipeline: write each planned note with SOURCE ATTRIBUTION.

v3 reuses the v2 PLAN unchanged -- same documents, same note boundaries, same
building blocks, same thoughts -- and changes only the writing brief. That makes
this a single-variable ablation rather than a rebuild.

The variable is ATTRIBUTION, and it was chosen by measurement rather than by
preference. Two pre-build checks redirected the experiment:

  - The obvious hypothesis, that summarisation loses the literal answer string,
    is FALSE here. v2 notes preserve the gold answer at 98.2%, exactly the rate
    of the raw source. Verbatim anchors cannot explain the deficit.
  - Decomposing the note-vs-chunk entity gap shows notes get the answer INTO
    context more often (+0.037) and are MORE accurate once they answer (+0.016).
    They lose entirely on refusal (+0.087). The reader declines to commit.
  - Refusal tracks attribution: with every publisher the question names present
    in context, refusal is 0.481; with only some present, 0.615.

These questions ask who reported what, so a note that never says which outlet
reported it cannot be matched against the question's attribution and the reader
sees an unsourced assertion. 19.2% of v2 notes name no publisher at all.

    python3 scripts/execute_v3.py --plan experiments/plans/v2/plan.jsonl \
        --out vaults/v3_attributed
"""
from __future__ import annotations
import argparse, json, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from answer_eval import BACKENDS   # noqa: E402
from llm_call import call, Format   # noqa: E402

CEIL = {"empirical_observation": 130, "concept": 160, "navigation": 170,
        "model": 190, "hypothesis": 190, "counter_argument": 190,
        "argument": 220, "procedure": 350}

SYSTEM = """You write ONE thought-atomic note for a knowledge vault, from source text.

ABSOLUTE RULES
1. ONE THOUGHT of the assigned building block's kind. Not two. If the source gives you a
   second, write only the assigned one.
2. TARGET WEIGHT: write to the word budget given. Past it you are padding.
3. SELF-SUFFICIENT: name the subject, give the date, resolve every reference. Never open
   with "he", "this", "the company", "however". A reader sees this note ALONE.
3b. ATTRIBUTE THE CLAIM. State WHICH PUBLICATION reported it and WHEN, in the first
   sentence, using the publisher name and date you are given -- e.g. "TechCrunch reported
   on 2023-12-15 that ...". A reader asked whether a named outlet said something must be
   able to answer from this note alone. An unattributed assertion is unverifiable and gets
   declined, however accurate it is.
3c. QUOTE THE LOAD-BEARING CLAIM. The one assertion this note exists to convey appears
   ALSO as a short direct quotation from the source, in quotation marks, where the source
   states it in its own words. Quote a clause, not a paragraph. This gives the reader the
   source's own wording to check the paraphrase against.
4. PRESERVE THE DATA: paraphrase prose, never data. Every date, quantity with a unit,
   proper name and figure from the source appears verbatim.
5. NO FABRICATION: every claim traces to the source given.
6. DO NOT SPEND WORDS ON: a preamble restating the title; a closing summary; transitions
   to other notes; hedging with no scope condition ("it is worth noting"). A real scope
   condition (in the EU, after 2023) is content and stays.

Return EXACTLY this format and nothing else. Do not use JSON -- the body is multi-line
markdown and JSON escaping corrupts it:

TITLE: <short descriptive title on one line>
BODY:
<the note body: markdown prose, no H1, no headings>
END"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--slug", default="multihop_rag")
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", default="cline")
    ap.add_argument("--model", default="qwen/qwen3.8-flash")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--chars", type=int, default=5000)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    corpus = ROOT / "data/corpus" / a.slug
    plans = [json.loads(l) for l in Path(a.plan).read_text().splitlines() if l.strip()]
    tasks = []
    for p in plans:
        for n in p["notes"]:
            tasks.append((p, n))
    if a.limit:
        tasks = tasks[: a.limit]

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    todo = [(p, n) for p, n in tasks if not (out / f"{n['slug']}.md").exists()]
    print(f"{len(tasks)} planned notes, {len(tasks)-len(todo)} written, {len(todo)} to do")

    ask = BACKENDS[a.backend]; lock = threading.Lock()

    def one(item):
        p, n = item
        bb = n["bb"]
        tgt = int(n.get("target_words") or 90)
        src = (corpus / f"{p['doc']}.txt").read_text()[: a.chars]
        user = (f"BUILDING BLOCK: {bb}\nTHE ONE THOUGHT: {n['thought']}\n"
                f"TARGET: {tgt} words (ceiling {CEIL.get(bb,200)})\n"
                f"COVERS: {n.get('covers','')}\n"
                f"SOURCE TITLE: {p['title']}\nPUBLISHER: {p['publisher']}  DATE: {p['date']}\n\n"
                f"SOURCE:\n{src}\n\nWrite the note.")
        def parse(raw):
            mt = re.search(r"^TITLE:\s*(.+)$", raw, re.M)
            mb = re.search(r"^BODY:\s*\n(.*?)(?:\nEND\s*$|\Z)", raw, re.S | re.M)
            if not mb:
                raise Format("no BODY block")
            body = re.sub(r"^#\s+.*\n+", "", mb.group(1).strip())
            if len(body.split()) < 15:
                raise Format(f"body too short ({len(body.split())}w)")
            return (mt.group(1).strip() if mt else None), body

        got, status = call(ask, SYSTEM, user, a.model, parse)
        if got is None:
            return 0, status
        mtitle, body = got
        title = (mtitle or n["slug"].replace("_", " ")).strip()
        # NOT the title: it is already indexed as its own field, and plan-digestion
        # forbids title restatement outright. Keywords are anticipated questions and
        # are generated separately by gen_anticipated_questions.py, so leave the
        # field minimal here rather than filling it with a restatement.
        kw = n.get("covers") or n["slug"].replace("_", " ")
        fm = (f"---\ntags:\n  - resource\n  - {bb}\nkeywords:\n  - {kw[:80]}\n"
              f"topics:\n  - {p['publisher'] or 'news'}\nlanguage: markdown\n"
              f"date of note: {p['date'] or '2023-12-01'}\nstatus: active\n"
              f"building_block: {bb}\nsource_docs: [{p['doc']}]\n"
              f"access_control_group: [\"general\"]\n---\n\n")
        with lock:
            (out / f"{n['slug']}.md").write_text(f"{fm}# {title}\n\n{body}\n")
        return len(body.split()), None

    from collections import Counter
    ok = words = 0; kinds = Counter(); sample = {}
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for w, err in ex.map(one, todo):
            if err:
                k = err.split(":", 1)[0]
                kinds[k] += 1; sample.setdefault(k, err)
            else:
                ok += 1; words += w
    print(f"wrote {ok} notes, mean {words/ok if ok else 0:.0f} body words")
    if kinds:
        print("failures by KIND (transport means the model never ran):")
        for k, c in kinds.most_common():
            print(f"  {k:<10} {c:>4}   e.g. {sample[k][:96]}")


if __name__ == "__main__":
    main()
