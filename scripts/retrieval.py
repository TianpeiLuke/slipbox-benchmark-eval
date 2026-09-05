#!/usr/bin/env python3
"""
Retrieval strategies over a corpus vault -- lexical, dense, hybrid, and graph.

Self-contained: reads only the vault's own notes.db, embeddings.npy and link
graph. Nothing outside this repository is touched, which is the isolation
condition the evaluation depends on.

Strategies
----------
  bm25    FTS5 over title+body (the lexical baseline)
  dense   cosine over sentence embeddings
  hybrid  reciprocal-rank fusion of bm25 and dense
  bfs     hybrid seeds, then best-first expansion over resolved links
  ppr     hybrid seeds, then personalised PageRank over the link graph

The last two are the "graph-based retrieval" arm. They exist to test whether a
typed link graph reaches gold evidence that similarity alone misses -- which is
the whole claim of graph RAG, and the reason multi-hop benchmarks are the
right test.

    python3 scripts/retrieval.py vaults/musique --query "who founded X" --strategy ppr
    python3 scripts/retrieval.py vaults/musique --query "..." --strategy all --k 5
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
import threading
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

RRF_K = 60          # standard reciprocal-rank-fusion constant
PPR_ALPHA = 0.85    # damping: 85% follow links, 15% teleport to seeds
PPR_ITERS = 30


# ---------------------------------------------------------------- lexical

def bm25(vault: Path, query: str, k: int) -> list[tuple[str, float]]:
    con = sqlite3.connect(vault / "notes.db")
    # FTS5 MATCH needs a sanitised query; OR the content terms
    terms = [t for t in re.findall(r"[A-Za-z0-9]+", query) if len(t) > 2]
    if not terms:
        return []
    expr = " OR ".join(terms)
    try:
        rows = con.execute(
            "SELECT note_id, bm25(notes_fts) FROM notes_fts "
            "WHERE notes_fts MATCH ? ORDER BY bm25(notes_fts) LIMIT ?",
            (expr, k)).fetchall()
    except sqlite3.OperationalError:
        rows = []
    con.close()
    # bm25() returns lower-is-better; invert for a uniform convention
    return [(nid, -score) for nid, score in rows]


# ------------------------------------------------------------------ dense

_MODEL = None
# lazy init is not thread-safe: concurrent first calls raced inside torch and
# died with "Cannot copy out of meta tensor". One loader, everyone else waits.
_MODEL_LOCK = threading.Lock()


def dense(vault: Path, query: str, k: int) -> list[tuple[str, float]]:
    import numpy as np
    epath, ipath = vault / "embeddings.npy", vault / "embedding_ids.json"
    if not epath.exists():
        # Returning [] here would make hybrid silently equal bm25 and dense
        # silently equal nothing -- a missing index would read as a real result.
        raise FileNotFoundError(
            f"no dense index at {epath}. Run: python3 scripts/build_embeddings.py {vault}\n"
            f"(bm25 works without it. bfs and ppr SEED from hybrid, so they need it too "
            f"unless you pass seed='bm25'.)")
    global _MODEL
    meta = json.loads(ipath.read_text())
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        with _MODEL_LOCK:
            if _MODEL is None:
                _MODEL = SentenceTransformer(meta["model"])
    emb = np.load(epath)
    q = _MODEL.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    sims = emb @ q
    idx = sims.argsort()[::-1][:k]
    return [(meta["ids"][i], float(sims[i])) for i in idx]


# ----------------------------------------------------------------- hybrid

def hybrid(vault: Path, query: str, k: int) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for rank, (nid, _) in enumerate(bm25(vault, query, k * 3)):
        scores[nid] += 1.0 / (RRF_K + rank)
    for rank, (nid, _) in enumerate(dense(vault, query, k * 3)):
        scores[nid] += 1.0 / (RRF_K + rank)
    return sorted(scores.items(), key=lambda x: -x[1])[:k]


# ------------------------------------------------------------------ graph

def navigation_notes(vault: Path) -> set[str]:
    """Notes that index rather than assert.

    They must stay IN the graph -- an entry point is often the only path between
    two clusters, so removing it would disconnect the very traversal the graph
    arm tests. But they must not be RETURNED: an entry point carries no
    source_docs, so it can never satisfy passage-level gold, and every slot one
    occupies in the top k is a slot that could have held an answer. Leaving them
    in results does not merely add noise, it understates the arm.
    """
    def build():
        con = sqlite3.connect(vault / "notes.db")
        out = {n for n, in con.execute(
            "SELECT note_id FROM notes WHERE building_block = 'navigation'")}
        con.close()
        return out
    return _cached(("nav", str(vault)), build)


# Per-vault caches. Rebuilding the graph, the networkx view or the embedding
# matrix per query turns a 2,255-question run from minutes into hours, and the
# inputs do not change within a run.
_CACHE: dict[tuple, object] = {}


def _cached(key, build):
    if key not in _CACHE:
        _CACHE[key] = build()
    return _CACHE[key]


def load_graph(vault: Path, undirected: bool = True
               ) -> tuple[dict[str, list[str]], dict[str, int]]:
    """Adjacency over RESOLVED in-vault links, UNDIRECTED, with degrees.

    Direction is a fact about how a note was written, not about what it is
    about: if A cites B the two are related whichever way a reader arrives.
    Treating the graph as directed makes every note that is cited but does not
    cite back a sink -- walk mass flows in and dies -- which silences most of
    this vault, where entity notes are cited far more than they cite.
    """
    return _cached(("graph", str(vault), undirected),
                   lambda: _build_graph(vault, undirected))


def _build_graph(vault: Path, undirected: bool):
    con = sqlite3.connect(vault / "notes.db")
    adj: dict[str, list[str]] = defaultdict(list)
    deg: dict[str, int] = defaultdict(int)
    for a_, b_ in con.execute(
            "SELECT source_note_id, target_note_id FROM note_links "
            "WHERE resolved=1 AND source_note_id != target_note_id"):
        adj[a_].append(b_)
        deg[a_] += 1
        deg[b_] += 1
        if undirected:
            adj[b_].append(a_)
    con.close()
    return dict(adj), dict(deg)


def hub_weighted_graph(vault: Path):
    """Directed graph whose edge weight is 1/log(deg(target)+e).

    Standard PageRank spreads a node's mass uniformly over its out-edges, which
    concentrates on hubs: a note everything links to accumulates rank regardless
    of the query. Weighting the transition INTO a node by its degree damps that
    without penalising flow OUT of a hub, so a well-connected note still passes
    mass along.
    """
    def build():
        import networkx as nx
        adj, deg = load_graph(vault)
        G = nx.DiGraph()
        for u, nbrs in adj.items():
            for v in nbrs:
                G.add_edge(u, v, weight=1.0 / math.log(deg.get(v, 1) + math.e))
        return G
    return _cached(("hubG", str(vault)), build)


def _embeddings(vault: Path):
    """(matrix, id list, id->row) for the vault's dense index."""
    import numpy as np
    epath, ipath = vault / "embeddings.npy", vault / "embedding_ids.json"
    if not epath.exists():
        raise FileNotFoundError(
            f"no dense index at {epath}. Run: python3 scripts/build_embeddings.py {vault}")
    def build():
        meta = json.loads(ipath.read_text())
        return np.load(epath), meta["ids"], {n: i for i, n in enumerate(meta["ids"])}
    return _cached(("emb", str(vault)), build)


def encode_query(vault: Path, query: str):
    global _MODEL
    meta = json.loads((vault / "embedding_ids.json").read_text())
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        with _MODEL_LOCK:
            if _MODEL is None:
                _MODEL = SentenceTransformer(meta["model"])
    return _MODEL.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]


def dense_seed(vault: Path, q_emb, k: int = 5, in_set: set | None = None) -> list[str]:
    """Top-k dense notes as seeds for the graph arms.

    Seeds come from the EMBEDDING, not from lexical or fused retrieval. A graph
    arm exists to test what traversal adds on top of semantic seeding, so
    seeding it with a fusion that already includes lexical evidence confounds
    the two: any gain could be the lexical half rather than the graph.

    `in_set` filters to ids present in the graph, walking further down the
    ranking to find k valid seeds. Without it a seed can be a node the graph
    does not contain, and the traversal starts from nothing.
    """
    import numpy as np
    emb, ids, _ = _embeddings(vault)
    scores = emb @ q_emb
    order = np.argsort(scores)[::-1]
    out: list[str] = []
    for i in order:
        nid = ids[i]
        if in_set is None or nid in in_set:
            out.append(nid)
            if len(out) >= k:
                break
    return out


def keyword_seed(vault: Path, query: str, k: int = 5,
                 in_set: set | None = None) -> list[tuple[str, float]]:
    """Seed from CURATED metadata: note name, keywords, topics, tags.

    Ported from the source vault, where it is one of three seeding strategies
    for graph traversal. It matches a query against what a curator said the note
    is about rather than against its prose, which is a different and often
    sharper signal: a short question tends to use the vocabulary a keyword list
    was written in, while a body buries it among incidental words.

    It also costs nothing to run -- no encoder -- so it is the fallback when no
    dense index exists.
    """
    terms = [w for w in re.findall(r"[A-Za-z0-9]{3,}", query.lower())]
    if not terms:
        return []
    con = sqlite3.connect(vault / "notes.db")
    clause = " OR ".join(
        ["note_name LIKE ? OR keywords LIKE ? OR topics LIKE ? OR tags LIKE ?"] * len(terms))
    args = [f"%{t}%" for t in terms for _ in range(4)]
    rows = con.execute(
        f"SELECT note_id, note_name, keywords, topics, tags FROM notes WHERE {clause}",
        args).fetchall()
    con.close()
    scored = []
    for nid, name, kw, tp, tg in rows:
        hay = f"{name} {kw} {tp} {tg}".lower()
        hits = sum(1 for t in terms if t in hay)
        if hits and (in_set is None or nid in in_set):
            scored.append((nid, hits / len(terms)))
    return sorted(scored, key=lambda x: -x[1])[:k]


def bfs(vault: Path, query: str, k: int, seeds: int = 5,
        max_expansions: int = 200, seed: str = "dense") -> list[tuple[str, float]]:
    """Best-first BFS: priority queue ordered by each node's OWN cosine to the query.

    The graph decides which notes are considered; the embedding decides how they
    rank. Keeping those separate is what makes the arm testable. An earlier
    version propagated a discounted copy of the seed's score outward, so a
    node's rank was capped by whoever reached it, no expanded note could ever
    outrank its seed, and bfs's top-k was identical to its seeding for every
    query.

    Bounded by max_expansions because two-hop reach on a small-world graph runs
    to thousands of nodes; an unbounded frontier is a full scan wearing a
    traversal's clothes.
    """
    import heapq
    adj, _ = load_graph(vault)
    emb, ids, idx = _embeddings(vault)
    q = encode_query(vault, query)
    # Seeds are drawn from nodes that HAVE edges, since a seed that cannot
    # expand contributes nothing a dense query would not already return. On a
    # graph with no edges at all that set is empty, which silently zeroes the
    # arm rather than degenerating it to dense seeding -- so an empty adjacency
    # lifts the restriction instead of emptying the candidate pool.
    linked = set(adj) or None
    if seed == "dense":
        start = dense_seed(vault, q, seeds, linked)
    elif seed == "keyword":
        start = [n for n, _ in keyword_seed(vault, query, seeds, linked)] \
            or dense_seed(vault, q, seeds, linked)
    else:
        start = [n for n, _ in bm25(vault, query, seeds)]

    heap: list[tuple[float, str]] = []
    for nid in start:
        i = idx.get(nid)
        if i is not None:
            heapq.heappush(heap, (-float(emb[i] @ q), nid))

    visited: set[str] = set()
    out: list[tuple[float, str]] = []
    while heap and len(visited) < max_expansions:
        neg, v = heapq.heappop(heap)
        if v in visited:
            continue
        visited.add(v)
        out.append((-neg, v))
        if len(out) >= k * 4:
            break
        for u in adj.get(v, ()):
            if u not in visited and u in idx:
                heapq.heappush(heap, (-float(emb[idx[u]] @ q), u))

    nav = navigation_notes(vault)
    out.sort(key=lambda x: -x[0])
    return [(nid, sc) for sc, nid in out if nid not in nav][:k]


def ppr(vault: Path, query: str, k: int, seeds: int = 5, alpha: float = PPR_ALPHA,
        seed: str = "dense") -> list[tuple[str, float]]:
    """Hub-aware personalised PageRank, restarting on dense seeds.

    Personalisation is uniform over the seeds; the transition weights damp
    entry into hubs. This is the HippoRAG-shaped arm: unlike best-first BFS,
    which ranks a node by its own similarity, PPR ranks by stationary mass, so
    a note that is not itself similar to the query can still rank highly when
    several query-relevant notes point at it -- which is what a second hop is.
    """
    import networkx as nx
    G = hub_weighted_graph(vault)
    if G.number_of_nodes() == 0:
        return dense(vault, query, k)
    q = encode_query(vault, query)
    if seed == "dense":
        start = dense_seed(vault, q, seeds, set(G.nodes()))
    elif seed == "keyword":
        start = [n for n, _ in keyword_seed(vault, query, seeds, set(G.nodes()))] \
            or dense_seed(vault, q, seeds, set(G.nodes()))
    else:
        start = [n for n, _ in bm25(vault, query, seeds) if n in G]
    if not start:
        return dense(vault, query, k)
    w = 1.0 / len(start)
    pers = {n: (w if n in start else 0.0) for n in G.nodes()}
    scores = nx.pagerank(G, alpha=alpha, personalization=pers, weight="weight")
    nav = navigation_notes(vault)
    ranked = [(n, float(sc)) for n, sc in sorted(scores.items(), key=lambda x: -x[1])
              if n not in nav]
    return ranked[:k]


def graph_hybrid(vault: Path, query: str, k: int, seeds: int = 5,
                 seed: str = "dense") -> list[tuple[str, float]]:
    """Lexical + embedding + graph, fused as three ranked lists via RRF.

    `hybrid` fuses two signals and the graph arms use one as a SEED, which makes
    the graph a second stage rather than a third vote: it can only reorder what
    seeding already found. This fuses all three at once, so a note the query
    never lexically matches and no embedding ranks highly can still surface on
    graph evidence alone -- the case a multi-hop question needs, since the
    second hop is by construction not what the question names.

    RRF rather than score addition: BM25 scores, cosines and PageRank masses are
    on incomparable scales, and normalising them would introduce a weighting
    nobody chose. RRF needs only the ordering.
    """
    scores: dict[str, float] = defaultdict(float)
    for rank, (nid, _) in enumerate(bm25(vault, query, k * 3)):
        scores[nid] += 1.0 / (RRF_K + rank)
    for rank, (nid, _) in enumerate(dense(vault, query, k * 3)):
        scores[nid] += 1.0 / (RRF_K + rank)
    for rank, (nid, _) in enumerate(ppr(vault, query, k * 3, seeds=seeds, seed=seed)):
        scores[nid] += 1.0 / (RRF_K + rank)
    nav = navigation_notes(vault)
    return [x for x in sorted(scores.items(), key=lambda y: -y[1]) if x[0] not in nav][:k]


def mmr(vault: Path, query: str, k: int, pool: int = 60, lam: float = 0.7,
        base: str = "hybrid") -> list[tuple[str, float]]:
    """Maximal marginal relevance: pick the next unit by what it ADDS.

    Atomic notes scatter one document across many units, so a plain top-k fills
    with near-duplicates from whichever document matched best -- measured, an
    atom vault returns 19.7 units per document against a coarse vault's 10.8, and
    the slot metric punishes that hard.

    MMR selects greedily on `lam * sim(query, u) - (1-lam) * max sim(u, chosen)`,
    so a unit that repeats what is already selected is passed over for one that
    adds something. The diversity signal is EMBEDDING similarity, deliberately,
    not shared provenance: penalising units for sharing a source document would
    be optimising directly against a metric defined over source documents, which
    is teaching to the test rather than improving retrieval.
    """
    import numpy as np
    fn = bm25 if base == "bm25" else hybrid
    cands = [n for n, _ in fn(vault, query, pool)]
    if len(cands) <= k:
        return [(n, 1.0) for n in cands]
    emb, ids, idx = _embeddings(vault)
    q = encode_query(vault, query)
    keep = [n for n in cands if n in idx]
    M = np.stack([emb[idx[n]] for n in keep])
    rel = M @ q
    chosen, chosen_i = [], []
    while len(chosen) < k and len(chosen) < len(keep):
        if not chosen_i:
            i = int(np.argmax(rel))
        else:
            red = (M @ M[chosen_i].T).max(axis=1)
            score = lam * rel - (1 - lam) * red
            score[chosen_i] = -1e9
            i = int(np.argmax(score))
        chosen_i.append(i); chosen.append((keep[i], float(rel[i])))
    return chosen


def perdoc(vault: Path, query: str, k: int, cap: int = 2, pool: int = 80,
           base: str = "hybrid", spill: bool = False) -> list[tuple[str, float]]:
    """Take the best units in rank order, but at most `cap` from any one source.

    A multi-hop question needs evidence from several documents by construction --
    every answerable question in this benchmark draws on 2 to 4, and 64.8% cross
    publishers. Splitting a document into atoms does not change that requirement,
    it only makes it easier for one document to consume the whole result list.

    IMPORTANT -- this strategy is a diagnostic, not a recommended default. It
    raises document-level recall and LOWERS fact-level recall on both vaults
    (paired bootstrap, 400 questions, all four intervals excluding zero). See
    docs/PIPELINE.md. Document credit pays in full for any one unit from a gold
    document whether or not that unit carries the fact, so capping optimises the
    proxy and moves away from the target.

    Two corrections to the first implementation:

    `key` charges EVERY declared source document, not `min(docs)`. Keying on the
    alphabetically smallest id let a note declaring {A,B} and a note declaring
    {A,C} both pass a cap of 1 whenever their smallest ids differed, so the cap
    under-counted exactly on the multi-source notes it exists to control -- 26.8%
    of v1_slice's notes declare more than one source.

    `spill` defaults to False. Back-filling from the rejected units whenever the
    pool holds fewer than k distinct sources silently disabled the cap in any
    caller asking for a large k: build_context requests 40 units, far more than
    the distinct documents available, so the "capped" context arms were nearly
    identical to the uncapped ones. Returning short is what a cap means.
    """
    fn_ = bm25 if base == "bm25" else hybrid
    con = sqlite3.connect(vault / "notes.db")
    src = {n: {x.strip() for x in (s or "").split(",") if x.strip()}
           for n, s in con.execute("SELECT note_id, source_doc FROM notes")}
    con.close()
    out, used, held = [], Counter(), []
    for nid, sc in fn_(vault, query, pool):
        docs = src.get(nid, set()) or {nid}
        if all(used[d] < cap for d in docs):
            for d in docs:
                used[d] += 1
            out.append((nid, sc))
        else:
            held.append((nid, sc))
        if len(out) >= k:
            return out
    return (out + held)[:k] if spill else out


def perdoc1(vault: Path, query: str, k: int, **kw) -> list[tuple[str, float]]:
    """perdoc with cap=1. A module-level def, not a dict-only lambda: callers
    resolve strategies by getattr as well as through STRATEGIES, and a lambda
    that exists in only one of the two registries fails at run time."""
    return perdoc(vault, query, k, cap=1, **kw)



# --------------------------------------------------------------- chain retrieval
#
# Motivated by the refusal diagnosis: the model abstains on CHAIN COMPLETENESS,
# not on answer presence. Capping left the count of answer-bearing contexts
# unchanged (484 vs 484) while cutting refusals a quarter, and refusal falls
# monotonically with the fraction of the question's supporting facts present --
# 0.65 none, 0.25 some, 0.08 all. So the objective for retrieval on a multi-hop
# task is to cover the question's distinct sub-claims across distinct documents,
# which is not what ranking by whole-query similarity optimises.
#
# Everything below derives its probes from the QUESTION TEXT ONLY. Using the gold
# evidence facts to steer retrieval would be label leakage; scoring against them
# afterwards is ordinary evaluation.

_STOP = set("""a an the is are was were be been being of in on at to for from by with
about into over after before between during under above below than then this that these
those it its it's as and or but if while which who whom whose what when where why how
do does did done have has had having will would shall should can could may might must
more most other some such no nor not only own same so too very s t just don now also
according based both each few many much any all one two three both either neither""".split())


def query_anchors(query: str, max_anchors: int = 4) -> list[str]:
    """Split a question into the distinct things it asks about.

    A multi-hop question names several entities and the hop is between them, so
    the capitalised spans are a good free proxy for the sub-claims -- no LLM call
    and no gold labels. Falls back to content words when a question is lowercase.
    """
    spans = re.findall(r"\b[A-Z][\w&.'-]*(?:\s+[A-Z][\w&.'-]*)*", query)
    seen, anchors = set(), []
    for sp in spans:
        toks = [t for t in sp.split() if t.lower() not in _STOP]
        if not toks:
            continue
        cand = " ".join(toks)
        if len(cand) > 2 and cand.lower() not in seen:
            seen.add(cand.lower()); anchors.append(cand)
    if len(anchors) < 2:
        words = [w for w in re.findall(r"[A-Za-z][\w-]{3,}", query)
                 if w.lower() not in _STOP]
        for w in words:
            if w.lower() not in seen:
                seen.add(w.lower()); anchors.append(w)
    return anchors[:max_anchors]


def chain(vault: Path, query: str, k: int, cap: int = 2, per_probe: int = 12,
          base: str = "hybrid") -> list[tuple[str, float]]:
    """Retrieve per sub-claim and interleave, so every probe gets represented.

    Plain top-k lets the strongest sub-claim monopolise the slots: whichever
    entity the ranker likes best returns units about that entity, and the hop
    the question actually asks about goes unsupported. Round-robin over the
    anchors spends the budget on breadth of sub-claim instead, and the per-source
    cap keeps one document from answering every probe.
    """
    fn_ = bm25 if base == "bm25" else hybrid
    anchors = query_anchors(query)
    con = sqlite3.connect(vault / "notes.db")
    src = {n: {x.strip() for x in (s or "").split(",") if x.strip()}
           for n, s in con.execute("SELECT note_id, source_doc FROM notes")}
    con.close()

    # the whole query first, then each anchor -- so a question whose anchors are
    # useless is never worse than the base ranker
    lists = [fn_(vault, query, per_probe)]
    lists += [fn_(vault, a, per_probe) for a in anchors]

    out, seen, used = [], set(), Counter()
    for rank in range(per_probe):
        for lst in lists:
            if rank >= len(lst):
                continue
            nid, sc = lst[rank]
            if nid in seen:
                continue
            docs = src.get(nid, set()) or {nid}
            if any(used[d] >= cap for d in docs):
                continue
            for d in docs:
                used[d] += 1
            seen.add(nid); out.append((nid, sc))
            if len(out) >= k:
                return out
    if len(out) < k:                       # top up in rank order, cap ignored
        for nid, sc in lists[0]:
            if nid not in seen:
                seen.add(nid); out.append((nid, sc))
                if len(out) >= k:
                    break
    return out[:k]


def gapfill(vault: Path, query: str, k: int, rounds: int = 3, cap: int = 2,
            base: str = "hybrid") -> list[tuple[str, float]]:
    """Iteratively re-query using the parts of the question still uncovered.

    After each round, take the question's content words that do NOT yet appear in
    the retrieved text and use them as the next probe. This closes chain gaps
    directly rather than hoping breadth produces them, and it needs no labels --
    the uncovered set is computed from the question against the retrieved text.
    """
    fn_ = bm25 if base == "bm25" else hybrid
    con = sqlite3.connect(vault / "notes.db")
    src = {n: {x.strip() for x in (s or "").split(",") if x.strip()}
           for n, s in con.execute("SELECT note_id, source_doc FROM notes")}
    body = dict(con.execute("SELECT note_id, body FROM notes"))
    con.close()

    want = {w.lower() for w in re.findall(r"[A-Za-z][\w-]{3,}", query)
            if w.lower() not in _STOP}
    out, seen, used, covered = [], set(), Counter(), set()
    probe = query
    for _ in range(max(1, rounds)):
        for nid, sc in fn_(vault, probe, k * 2):
            if nid in seen or len(out) >= k:
                continue
            docs = src.get(nid, set()) or {nid}
            if any(used[d] >= cap for d in docs):
                continue
            for d in docs:
                used[d] += 1
            seen.add(nid); out.append((nid, sc))
            covered |= {w.lower() for w in re.findall(r"[A-Za-z][\w-]{3,}",
                                                      body.get(nid, ""))}
        if len(out) >= k:
            break
        missing = want - covered
        if not missing:
            break
        probe = " ".join(sorted(missing))
    return out[:k]


def chain1(vault: Path, query: str, k: int, **kw) -> list[tuple[str, float]]:
    """chain with a strict one-unit-per-document cap."""
    return chain(vault, query, k, cap=1, **kw)



_PUBCACHE: dict = {}


def _publishers(vault: Path):
    """(note_id -> publishers, list of publisher names) for this corpus.

    Uses corpus METADATA (which publisher each document came from), not gold
    labels. A deployed system has the same information about its own sources.
    """
    key = str(vault)
    if key in _PUBCACHE:
        return _PUBCACHE[key]
    root = Path(__file__).resolve().parent.parent
    idx = json.loads((root / "data/corpus/multihop_rag/index.json").read_text())
    doc_pub = {d: v.get("publisher", "") for d, v in idx.items()}
    con = sqlite3.connect(vault / "notes.db")
    note_pub = {}
    for n, sd in con.execute("SELECT note_id, source_doc FROM notes"):
        pubs = {doc_pub.get(x.strip(), "") for x in (sd or "").split(",") if x.strip()}
        note_pub[n] = {p for p in pubs if p}
    con.close()
    names = sorted({p for p in doc_pub.values() if p}, key=len, reverse=True)
    _PUBCACHE[key] = (note_pub, names)
    return _PUBCACHE[key]


def named_sources(query: str, names: list[str]) -> list[str]:
    """Publishers the question names explicitly. Longest-first so a short name
    nested in a longer one does not shadow it."""
    q = query.lower()
    found, taken = [], []
    for n in names:
        nl = n.lower()
        if nl in q and not any(nl in t for t in taken):
            taken.append(nl); found.append(n)
    return found


def logical(vault: Path, query: str, k: int, per_source: int = 4, pool: int = 200,
            base: str = "hybrid") -> list[tuple[str, float]]:
    """Retrieve the question's PREDICATE separately from each source it NAMES.

    These questions have a consistent logical form -- one topic, asserted by two
    or more explicitly named publishers -- and 98.9% of them name at least one of
    their own gold publishers. Nothing in plain ranking uses that: it scores every
    unit against the whole question, so the strongest source can supply every slot
    and the cross-source comparison the question asks for never assembles.

    So: strip the source names to leave the predicate, rank the pool by the
    predicate, then fill a quota from each named source. Per-source capping
    approximates this blindly by forcing diversity in every direction; this aims
    at the sources the question actually asks about.

    An earlier attempt decomposed the query into ENTITY anchors and did markedly
    worse than plain ranking (chain completeness 0.073 against 0.190), because
    probing "Apple" and "Google" separately retrieves units about each entity and
    discards the relation between them that the question is asking about. The
    predicate has to stay intact; only the SOURCE is a legitimate axis to split on.
    """
    fn_ = bm25 if base == "bm25" else hybrid
    note_pub, names = _publishers(vault)
    asked = named_sources(query, names)
    if not asked:
        return fn_(vault, query, k)

    predicate = query
    for n in asked:
        predicate = re.sub(re.escape(n), " ", predicate, flags=re.I)
    predicate = " ".join(predicate.split()) or query

    ranked = fn_(vault, predicate, pool)
    buckets = {a: [] for a in asked}
    for nid, sc in ranked:
        for a in asked:
            if a in note_pub.get(nid, set()) and len(buckets[a]) < per_source:
                buckets[a].append((nid, sc))
                break

    out, seen = [], set()
    for rank in range(per_source):              # round-robin across named sources
        for a in asked:
            if rank < len(buckets[a]):
                nid, sc = buckets[a][rank]
                if nid not in seen:
                    seen.add(nid); out.append((nid, sc))
                    if len(out) >= k:
                        return out
    for nid, sc in ranked:                      # top up on the predicate
        if nid not in seen:
            seen.add(nid); out.append((nid, sc))
            if len(out) >= k:
                break
    return out[:k]


def logical_cap(vault: Path, query: str, k: int, **kw) -> list[tuple[str, float]]:
    """logical, then per-document capping over whatever slots remain."""
    got = logical(vault, query, k, **kw)
    if len(got) >= k:
        return got
    have = {n for n, _ in got}
    for nid, sc in perdoc(vault, query, k, cap=1):
        if nid not in have:
            got.append((nid, sc))
            if len(got) >= k:
                break
    return got[:k]


# The registry key is "keyword" while the function is keyword_seed. Alias it so
# name-based resolution and STRATEGIES cannot disagree; renaming the key instead
# would invalidate the strategy names recorded in earlier run files.
keyword = keyword_seed

STRATEGIES = {"bm25": bm25, "dense": dense, "hybrid": hybrid,
              "bfs": bfs, "ppr": ppr, "graph_hybrid": graph_hybrid,
              "keyword": keyword_seed,
              "mmr": mmr,
              "perdoc": perdoc,
              "perdoc1": perdoc1,
              "chain": chain,
              "chain1": chain1,
              "gapfill": gapfill,
              "logical": logical,
              "logical_cap": logical_cap}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--query", required=True)
    ap.add_argument("--strategy", default="hybrid",
                    choices=list(STRATEGIES) + ["all"])
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--seed", default="dense", choices=["dense", "bm25", "keyword"],
                    help="seed set for bfs and ppr. Default hybrid, matching the "
                         "HippoRAG protocol; bm25 lets the graph arms run with no "
                         "embedding index. Chosen, never substituted silently.")
    a = ap.parse_args()

    vault = Path(a.vault)
    if not (vault / "notes.db").exists():
        print(f"no database at {vault}/notes.db; run build_local_db.py first")
        sys.exit(2)

    names = list(STRATEGIES) if a.strategy == "all" else [a.strategy]
    for name in names:
        res = (STRATEGIES[name](vault, a.query, a.k, seed=a.seed)
               if name in ("bfs", "ppr", "graph_hybrid")
               else STRATEGIES[name](vault, a.query, a.k))
        print(f"\n=== {name} ===")
        if not res:
            print("  (no results -- embeddings missing, or no lexical match)")
        for i, (nid, sc) in enumerate(res, 1):
            print(f"  {i}. {sc:8.4f}  {nid}")


if __name__ == "__main__":
    main()
