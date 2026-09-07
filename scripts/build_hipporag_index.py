#!/usr/bin/env python3
"""Build a HippoRAG hippocampal index over a passage corpus.

Reproduces Gutierrez et al., "HippoRAG: Neurobiologically Inspired Long-Term
Memory for Large Language Models", NeurIPS 2024 (arXiv:2405.14831), offline
stage. Hyperparameters are taken from the authors' released config
(src/hipporag/utils/config_utils.py): synonymy_edge_sim_threshold 0.8,
damping 0.5 (used at query time), linking_top_k 5.

Offline pipeline, following the paper:
  1. per passage, a 1-shot LLM call extracts NAMED ENTITIES
  2. a second 1-shot call, seeded with those entities, extracts OpenIE TRIPLES
  3. noun phrases become nodes, triples become edges (schemaless open KG)
  4. SYNONYMY EDGES join node pairs whose encoder cosine exceeds tau = 0.8
  5. a node-by-passage membership matrix converts node mass to passage scores

Deviations from the paper, recorded because a baseline is only useful if its
gaps are known:
  - encoder is all-MiniLM-L6-v2, what the rest of this repo indexes with, not
    Contriever/ColBERTv2 (paper) or NV-Embed-v2 (current release). This lowers
    synonym-edge quality and is the largest single deviation.
  - extraction LLM is claude-haiku-4-5 at temperature 0, not GPT-3.5-turbo-1106.
  - synonymy candidates come from a full pairwise cosine over the node set
    rather than the released code's top-2047 KNN; on a node set this size the
    two are equivalent, and it removes a truncation the paper does not describe.
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import llm_call                                        # noqa: E402
from answer_eval import BACKENDS                       # noqa: E402

NER_SYSTEM = (
    "You extract named entities from a passage. Reply with ONLY a JSON object "
    'of the form {"named_entities": ["...", "..."]} and nothing else.'
)
NER_USER = """Example passage: Radio City is India's first private FM radio station, started on 3 July 2001. It plays Hindi, English and regional songs.
Example output: {"named_entities": ["Radio City", "India", "3 July 2001", "Hindi", "English"]}

Passage: {passage}
Output:"""

OIE_SYSTEM = (
    "You perform open information extraction. Given a passage and its named "
    "entities, produce subject-predicate-object triples covering the passage's "
    'claims. Reply with ONLY {"triples": [["s","p","o"], ...]} and nothing else. '
    "Keep every subject and object to a short noun phrase."
)
OIE_USER = """Example passage: Radio City is India's first private FM radio station, started on 3 July 2001.
Example entities: ["Radio City", "India", "3 July 2001"]
Example output: {"triples": [["Radio City", "is", "India's first private FM radio station"], ["Radio City", "started on", "3 July 2001"], ["Radio City", "located in", "India"]]}

Passage: {passage}
Named entities: {entities}
Output:"""


def _parse(key):
    """Parse the model's JSON, raising Format for anything malformed.

    json.loads raises JSONDecodeError, which is a ValueError but NOT
    llm_call.Format, so an unparseable reply escaped the retry handler and
    killed the whole run rather than costing one passage.
    """
    def p(raw: str):
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            raise llm_call.Format("no JSON object in output")
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError as e:
            raise llm_call.Format(f"malformed JSON: {e}") from None
        if not isinstance(obj, dict) or key not in obj:
            raise llm_call.Format(f"missing key {key}")
        val = obj[key]
        if not isinstance(val, list):
            raise llm_call.Format(f"{key} is not a list")
        return val
    return p


def norm_phrase(s: str) -> str:
    """Nodes are compared after light normalisation; the paper leaves phrases as
    extracted, and synonymy edges are what absorb surface variation."""
    return " ".join(str(s).lower().strip().split())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True,
                    help="path to a vault/chunk dir containing notes.db")
    ap.add_argument("--out", required=True, help="output index directory")
    ap.add_argument("--restrict-docs",
                    help="JSON list of source_doc ids to limit the corpus to")
    ap.add_argument("--backend", default="anthropic")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--tau", type=float, default=0.8,
                    help="synonymy edge cosine threshold (paper/code default 0.8)")
    ap.add_argument("--max-tokens", dest="max_tokens", type=int, default=2000,
                    help="extraction output budget; 128 truncates triple lists")
    ap.add_argument("--limit", type=int, default=0, help="debug: cap passages")
    a = ap.parse_args()

    con = sqlite3.connect(Path(a.corpus) / "notes.db")
    rows = list(con.execute("SELECT note_id, title, body, source_doc FROM notes"))
    con.close()
    if a.restrict_docs:
        keep = set(json.loads(Path(a.restrict_docs).read_text()))
        rows = [r for r in rows if r[3] and r[3].strip() in keep]
    if a.limit:
        rows = rows[: a.limit]
    print(f"{len(rows)} passages")

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    cache = out / "openie.jsonl"
    done = {}
    if cache.exists():
        for line in cache.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                # Error records must NOT count as done: keeping them meant a
                # re-run skipped exactly the passages that had failed, so a
                # mid-run service outage was permanent.
                if not r.get("err"):
                    done[r["pid"]] = r
    todo = [r for r in rows if r[0] not in done]
    print(f"{len(done)} cached, {len(todo)} to extract")

    # Extraction needs room: the answering default of 128 truncates triple
    # lists mid-JSON, which surfaces as a parse failure rather than a length one.
    _base = BACKENDS[a.backend]
    ask = (lambda s, u, m: _base(s, u, m, max_tokens=a.max_tokens)) \
        if a.backend == 'anthropic' else _base
    lock = threading.Lock()

    def extract(row):
        pid, title, body, _ = row
        passage = f"{title}\n{body}" if title else body
        passage = passage[:4000]
        ents, st = llm_call.call(ask, NER_SYSTEM, NER_USER.replace("{passage}", passage),
                                 a.model, _parse("named_entities"))
        if ents is None:
            rec = {"pid": pid, "err": f"ner:{st}"}
        else:
            trip, st2 = llm_call.call(
                ask, OIE_SYSTEM,
                OIE_USER.replace("{passage}", passage).replace("{entities}", json.dumps(ents)),
                a.model, _parse("triples"))
            rec = ({"pid": pid, "entities": ents, "triples": trip} if trip is not None
                   else {"pid": pid, "entities": ents, "triples": [], "err": f"oie:{st2}"})
        with lock:
            with cache.open("a") as fh:
                fh.write(json.dumps(rec) + "\n")
        return rec

    if todo:
        recent: list[bool] = []
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for i, rec in enumerate(ex.map(extract, todo), 1):
                recent.append(bool(rec.get("err")))
                recent = recent[-50:]
                if i % 100 == 0:
                    print(f"  {i}/{len(todo)}", flush=True)
                # A backend that starts failing usually keeps failing. One run
                # here went 0% failures for 60% of the corpus then 100% for the
                # rest -- a mid-run outage misreported as a format error. Stop
                # and say so rather than burning the remaining calls.
                if len(recent) == 50 and sum(recent) >= 45:
                    raise SystemExit(
                        f"\naborting at {i}/{len(todo)}: 45+ of the last 50 calls "
                        f"failed, which is a backend outage rather than bad input. "
                        f"Progress is cached; re-run to resume.")
        for line in cache.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if not r.get("err"):
                    done[r["pid"]] = r

    errs = [r for r in done.values() if r.get("err")]
    if errs:
        print(f"  !! {len(errs)}/{len(done)} passages failed extraction "
              f"({len(errs)/len(done):.1%}), e.g. {errs[0]['err']}")

    # ---- assemble the open KG -------------------------------------------
    src = {r[0]: (r[3] or "").strip() for r in rows}
    nodes: dict[str, int] = {}
    edges: set[tuple[int, int]] = set()
    membership: dict[tuple[int, str], int] = defaultdict(int)

    def nid(phrase: str) -> int:
        p = norm_phrase(phrase)
        if not p:
            return -1
        if p not in nodes:
            nodes[p] = len(nodes)
        return nodes[p]

    for pid, rec in done.items():
        if pid not in src:
            continue
        seen_here = set()
        for e in rec.get("entities") or []:
            i = nid(e)
            if i >= 0:
                seen_here.add(i)
        for t in rec.get("triples") or []:
            if not isinstance(t, (list, tuple)) or len(t) < 3:
                continue
            s, o = nid(t[0]), nid(t[2])
            if s >= 0 and o >= 0 and s != o:
                edges.add((s, o))
                seen_here.add(s); seen_here.add(o)
        for i in seen_here:
            membership[(i, pid)] += 1

    print(f"KG: {len(nodes)} nodes, {len(edges)} relation edges, "
          f"{len(membership)} node-passage links")

    # ---- synonymy edges --------------------------------------------------
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    phrases = [p for p, _ in sorted(nodes.items(), key=lambda kv: kv[1])]
    emb = model.encode(phrases, normalize_embeddings=True, show_progress_bar=False,
                       batch_size=256).astype(np.float32)
    syn = set()
    B = 512
    for s in range(0, len(phrases), B):
        sims = emb[s:s + B] @ emb.T
        for r in range(sims.shape[0]):
            i = s + r
            js = np.where(sims[r] >= a.tau)[0]
            for j in js:
                if int(j) != i:
                    syn.add((min(i, int(j)), max(i, int(j))))
    print(f"synonymy edges at tau={a.tau}: {len(syn)}")

    np.save(out / "node_emb.npy", emb)
    (out / "index.json").write_text(json.dumps({
        "phrases": phrases,
        "edges": sorted(map(list, edges)),
        "synonymy": sorted(map(list, syn)),
        "membership": [[i, p, c] for (i, p), c in membership.items()],
        "passages": {r[0]: src[r[0]] for r in rows},
        "tau": a.tau, "model": "sentence-transformers/all-MiniLM-L6-v2",
        "extraction_model": a.model, "n_passages": len(rows),
        "n_failed": len(errs),
    }))
    print(f"wrote {out}/index.json")


if __name__ == "__main__":
    main()
