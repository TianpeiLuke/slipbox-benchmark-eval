#!/usr/bin/env python3
"""HippoRAG online retrieval: query NER -> node linking -> PPR -> passage scores.

Reproduces the query-time half of Gutierrez et al., NeurIPS 2024
(arXiv:2405.14831). damping 0.5 and synonymy threshold 0.8 are the authors'
released defaults and both were confirmed best here by ablation.

linking_top_k defaults to 1, which follows the PAPER ("take the most
cosine-similar node") rather than the released config's 5. Measured on this
corpus, 1 beats 3, 5 and 10 (R@5 0.310 / 0.310 / 0.292 / 0.269), so the paper's
description is the better setting when the encoder is weak.

The steps, following the paper:
  1. a 1-shot LLM call extracts the query's named entities
  2. each is encoded and linked to its most similar KG node
  3. the personalization vector puts equal mass on those nodes, then multiplies
     by NODE SPECIFICITY s_i = 1/|P_i|, the inverse passage frequency the paper
     offers as a locally computable analog of IDF
  4. Personalized PageRank diffuses that mass over relation + synonymy edges
  5. passage score = sum of the PPR mass of the nodes the passage contains

Query NER is cached to disk, so a scoring sweep costs LLM calls only once.
"""
from __future__ import annotations
import json, re, sys, threading
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import llm_call                                        # noqa: E402

QNER_SYSTEM = (
    "You extract named entities from a question. Reply with ONLY a JSON object "
    'of the form {"named_entities": ["...", "..."]} and nothing else.'
)
QNER_USER = """Example question: Which magazine was started first, Arthur's Magazine or First for Women?
Example output: {"named_entities": ["Arthur's Magazine", "First for Women"]}

Question: {q}
Output:"""

_LOCK = threading.Lock()
_STATE: dict = {}


def _parse_ents(raw: str):
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        raise llm_call.Format("no JSON object in output")
    obj = json.loads(m.group(0))
    if "named_entities" not in obj:
        raise llm_call.Format("missing named_entities")
    return obj["named_entities"]


def load(index_dir: Path) -> dict:
    key = str(index_dir)
    with _LOCK:
        if key in _STATE:
            return _STATE[key]
    idx = json.loads((index_dir / "index.json").read_text())
    emb = np.load(index_dir / "node_emb.npy")
    n = len(idx["phrases"])

    import networkx as nx
    G = nx.Graph()
    G.add_nodes_from(range(n))
    G.add_edges_from((int(u), int(v)) for u, v in idx["edges"])
    G.add_edges_from((int(u), int(v)) for u, v in idx["synonymy"])

    passages = idx["passages"]
    pids = sorted(passages)
    pcol = {p: i for i, p in enumerate(pids)}
    # node -> passage counts, and |P_i| for node specificity
    mem: dict[int, list[tuple[int, int]]] = {}
    freq = np.zeros(n, dtype=np.float32)
    for i, p, c in idx["membership"]:
        if p in pcol:
            mem.setdefault(int(i), []).append((pcol[p], int(c)))
            freq[int(i)] += 1
    spec = np.where(freq > 0, 1.0 / np.maximum(freq, 1.0), 0.0)

    st = {"idx": idx, "emb": emb, "G": G, "pids": pids, "mem": mem,
          "spec": spec, "cache_path": index_dir / "query_ner.json"}
    st["qcache"] = (json.loads(st["cache_path"].read_text())
                    if st["cache_path"].exists() else {})
    with _LOCK:
        _STATE[key] = st
    return st


_STOP_NER = set("""the a an of in on at to for from by with and or but is are was were
between before after during which who what when where why how did does do has have had
there their its it this that these those than then both either neither also according""".split())


def heuristic_entities(query: str) -> list[str]:
    """Deterministic stand-in for the paper's LLM query-NER call.

    HippoRAG extracts query entities with a 1-shot LLM call. This fallback takes
    capitalised spans, quoted strings and dates instead. It is a DEVIATION and
    is expected to be weaker -- it cannot recognise a lowercase entity or
    normalise a paraphrase -- but it makes the baseline runnable without an API
    key, and it is deterministic, which the LLM path is not.
    """
    ents: list[str] = []
    seen = set()
    for m in re.findall(r"'([^']{2,60})'|\"([^\"]{2,60})\"", query):
        cand = (m[0] or m[1]).strip()
        if cand and cand.lower() not in seen:
            seen.add(cand.lower()); ents.append(cand)
    for sp in re.findall(r"\b[A-Z][\w&.'-]*(?:\s+[A-Z][\w&.'-]*)*", query):
        toks = [t for t in sp.split() if t.lower() not in _STOP_NER]
        cand = " ".join(toks).strip()
        if len(cand) > 2 and cand.lower() not in seen:
            seen.add(cand.lower()); ents.append(cand)
    for d in re.findall(r"\b(?:January|February|March|April|May|June|July|August|"
                        r"September|October|November|December)\s+\d{1,2},?\s*\d{4}\b", query):
        if d.lower() not in seen:
            seen.add(d.lower()); ents.append(d)
    return ents


def query_entities(st: dict, query: str, ask, model: str, mode: str = "llm") -> list[str]:
    if query in st["qcache"]:
        return st["qcache"][query]
    ents = None
    if mode == "llm":
        ents, _ = llm_call.call(ask, QNER_SYSTEM, QNER_USER.replace("{q}", query),
                                model, _parse_ents)
        if ents is None:
            # Fall back rather than cache an empty list. Caching the failure made
            # an exhausted API key look like a corpus with no entities in it, and
            # the empty result then persisted across every later run.
            ents = heuristic_entities(query)
            st["fellback"] = st.get("fellback", 0) + 1
    else:
        ents = heuristic_entities(query)
    with _LOCK:
        st["qcache"][query] = ents
        st["cache_path"].write_text(json.dumps(st["qcache"]))
    return ents


def retrieve(index_dir: Path, query: str, k: int, ask=None,
             model: str = "claude-haiku-4-5-20251001",
             damping: float = 0.5, linking_top_k: int = 1,
             ner: str = "llm") -> list[tuple[str, float]]:
    st = load(Path(index_dir))
    if ask is None and ner == "llm":
        from answer_eval import BACKENDS
        base = BACKENDS["anthropic"]
        ask = lambda s, u, m: base(s, u, m, max_tokens=256)   # noqa: E731

    ents = query_entities(st, query, ask, model, mode=ner)
    if not ents:
        return []

    from sentence_transformers import SentenceTransformer
    global _ENC
    try:
        _ENC
    except NameError:
        _ENC = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    qe = _ENC.encode(ents, normalize_embeddings=True, show_progress_bar=False)
    sims = qe @ st["emb"].T                      # (n_ents, n_nodes)

    seeds: dict[int, float] = {}
    for r in range(sims.shape[0]):
        for j in np.argsort(sims[r])[::-1][:linking_top_k]:
            seeds[int(j)] = seeds.get(int(j), 0.0) + float(sims[r][j])
    if not seeds:
        return []

    # node specificity: 1/|P_i|, the paper's IDF analog
    pers = {i: w * float(st["spec"][i]) for i, w in seeds.items()}
    tot = sum(pers.values())
    if tot <= 0:
        return []
    pers = {i: w / tot for i, w in pers.items()}

    import networkx as nx
    pr = nx.pagerank(st["G"], alpha=damping, personalization=pers, max_iter=200,
                     tol=1e-8)

    scores = np.zeros(len(st["pids"]), dtype=np.float32)
    for i, mass in pr.items():
        if mass <= 0:
            continue
        for col, cnt in st["mem"].get(int(i), ()):
            scores[col] += mass * cnt
    order = np.argsort(scores)[::-1][:k]
    return [(st["pids"][j], float(scores[j])) for j in order if scores[j] > 0]
