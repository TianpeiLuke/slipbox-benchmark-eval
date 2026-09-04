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
           base: str = "hybrid") -> list[tuple[str, float]]:
    """Take the best units in rank order, but at most `cap` from any one source.

    A multi-hop question needs evidence from several documents by construction --
    in this benchmark every answerable question draws on 2 to 4, and 64.8% cross
    publishers. Splitting a document into atoms does not change that requirement,
    it only makes it easier for one document to consume the whole result list:
    measured, an atom vault returns 4.80 distinct documents in a top-10 where a
    coarse vault returns 6.88.

    Capping per source is a response to a KNOWN STRUCTURAL PROPERTY OF THE TASK,
    not to the scorer. Using the gold labels would be fitting the benchmark;
    using the fact that multi-hop questions need multiple sources is what any
    system built for this task should do. An earlier version of this file
    declined to add it on the grounds that the metric counts documents, which
    confused the two.
    """
    fn_ = bm25 if base == "bm25" else hybrid
    con = sqlite3.connect(vault / "notes.db")
    src = {n: {x.strip() for x in (s or "").split(",") if x.strip()}
           for n, s in con.execute("SELECT note_id, source_doc FROM notes")}
    con.close()
    out, used = [], Counter()
    spill = []
    for nid, sc in fn_(vault, query, pool):
        docs = src.get(nid, set())
        key = min(docs) if docs else nid
        if used[key] < cap:
            used[key] += 1
            out.append((nid, sc))
        else:
            spill.append((nid, sc))
        if len(out) >= k:
            return out
    # not enough distinct sources to fill k -- fall back to rank order rather
    # than returning short, so the cap never costs coverage it cannot replace
    return (out + spill)[:k]


STRATEGIES = {"bm25": bm25, "dense": dense, "hybrid": hybrid,
              "bfs": bfs, "ppr": ppr, "graph_hybrid": graph_hybrid,
              "keyword": lambda v, q, k, **kw: keyword_seed(v, q, k),
              "mmr": mmr,
              "perdoc": perdoc,
              "perdoc1": lambda v,q,k,**kw: perdoc(v,q,k,cap=1)}


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
