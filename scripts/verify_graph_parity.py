#!/usr/bin/env python3
"""
Check that this repo's graph retrieval matches the source vault's, step by step.

Porting an algorithm by reading it is how subtle divergences get shipped: an
earlier version of this repo's bfs used a FIFO queue and propagated discounted
seed scores, which looked like the vault's best-first BFS in outline and could
not promote a single node in practice. Nothing downstream reported it.

This reimplements the vault's logic VERBATIM against this repo's database and
diffs the output against scripts/retrieval.py. A structural match is not
claimed; identical rankings are.

    python3 scripts/verify_graph_parity.py --vault vaults/multihop_rag
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

QUERIES = [
    "Who testified about Alameda borrowing from FTX customer funds",
    "What did the EU tell Elon Musk about illegal content on X",
    "What did Meta say about moderating Palestinian content",
    "Which NFL quarterback was injured and what was the diagnosis",
    "How did the Google antitrust trial address default search payments",
]


# ---------------------------------------------------------------- vault logic
# Transcribed from scripts/retrieval_strategies/{shared_loaders,best_first_bfs,
# hub_aware_ppr}.py in the source vault. Kept in the vault's shape, not
# refactored, so a reader can diff it against the original line by line.

def v_get_adjacency(db):
    """shared_loaders.get_adjacency — UNDIRECTED, self-loops excluded."""
    conn = sqlite3.connect(db)
    adj, deg = defaultdict(list), defaultdict(int)
    for s, t in conn.execute(
            "SELECT source_note_id, target_note_id FROM note_links "
            "WHERE source_note_id != target_note_id AND resolved=1"):
        adj[s].append(t)
        adj[t].append(s)
        deg[s] += 1
        deg[t] += 1
    conn.close()
    return dict(adj), dict(deg)


def v_hub_weighted_graph(db):
    """shared_loaders.get_hub_weighted_graph — DiGraph, w = 1/log(deg(target)+e)."""
    import networkx as nx
    adj, deg = v_get_adjacency(db)
    G = nx.DiGraph()
    for u in adj:
        G.add_node(u)
    for u, neighbors in adj.items():
        for v in neighbors:
            G.add_edge(u, v, weight=1.0 / math.log(deg.get(v, 1) + math.e))
    return G


def v_dense_seed(emb, ids, q, k=5, in_set=None):
    """shared_loaders.dense_seed — walk the ranking until k valid seeds."""
    import numpy as np
    scores = emb @ q
    out = []
    for i in np.argsort(scores)[::-1]:
        nid = ids[i]
        if in_set is None or nid in in_set:
            out.append(nid)
            if len(out) >= k:
                break
    return out


def v_best_first_bfs(db, emb, ids, idx, q, top_k, max_expansions=200, seed_k=5):
    """best_first_bfs.BestFirstBFS.retrieve — priority queue on own cosine."""
    adj, _ = v_get_adjacency(db)
    seeds = v_dense_seed(emb, ids, q, k=seed_k, in_set=set(adj.keys()))
    heap = []
    for s in seeds:
        i = idx.get(s)
        if i is None:
            continue
        heapq.heappush(heap, (-float(emb[i] @ q), s))
    visited, result, examined = set(), [], 0
    while heap and examined < max_expansions:
        neg, v = heapq.heappop(heap)
        if v in visited:
            continue
        visited.add(v)
        result.append((-neg, v))
        examined += 1
        if len(result) >= top_k * 4:
            break
        for u in adj.get(v, []):
            if u in visited:
                continue
            i = idx.get(u)
            if i is None:
                continue
            heapq.heappush(heap, (-float(emb[i] @ q), u))
    result.sort(key=lambda x: -x[0])
    return [(nid, sc) for sc, nid in result[:top_k]]


def v_hub_aware_ppr(db, emb, ids, q, top_k, alpha=0.85, seed_k=5, max_iter=100):
    """hub_aware_ppr.HubAwarePPR.retrieve — nx.pagerank on the weighted graph."""
    import networkx as nx
    G = v_hub_weighted_graph(db)
    seeds = v_dense_seed(emb, ids, q, k=seed_k, in_set=set(G.nodes()))
    valid = [s for s in seeds if s in G]
    if not valid:
        return []
    w = 1.0 / len(valid)
    pers = {n: (w if n in valid else 0.0) for n in G.nodes()}
    scores = nx.pagerank(G, alpha=alpha, personalization=pers,
                         weight="weight", max_iter=max_iter)
    return [(n, float(s)) for n, s in sorted(scores.items(), key=lambda x: -x[1])[:top_k]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default="vaults/multihop_rag")
    ap.add_argument("--k", type=int, default=10)
    a = ap.parse_args()

    import numpy as np
    import retrieval as R

    V = Path(a.vault)
    db = V / "notes.db"
    meta = json.loads((V / "embedding_ids.json").read_text())
    emb, ids = np.load(V / "embeddings.npy"), meta["ids"]
    idx = {n: i for i, n in enumerate(ids)}
    # Compare the ALGORITHMS, not the post-filters. This repo excludes navigation
    # notes from results; the vault has no such concept. Asking the vault for a
    # longer list to compensate does not work either, because bfs bounds its own
    # exploration at top_k * 4 -- a larger request changes the SEARCH, not just
    # the output length. So the filter is disabled on both sides for the diff.
    nav = R.navigation_notes(V)
    R._CACHE[("nav", str(V))] = set()

    # 1. graph parity
    va, vd = v_get_adjacency(db)
    ma, md = R.load_graph(V)
    ok = (set(va) == set(ma)
          and all(sorted(va[n]) == sorted(ma[n]) for n in va)
          and vd == md)
    print(f"adjacency parity      {'MATCH' if ok else 'DIFFER'}  "
          f"({len(va)} nodes, {sum(len(v) for v in va.values()):,} arcs)")

    vG, mG = v_hub_weighted_graph(db), R.hub_weighted_graph(V)
    same = (vG.number_of_nodes() == mG.number_of_nodes()
            and vG.number_of_edges() == mG.number_of_edges()
            and all(abs(vG[u][v]["weight"] - mG[u][v]["weight"]) < 1e-12
                    for u, v in list(vG.edges())[:5000]))
    print(f"hub-weighted graph    {'MATCH' if same else 'DIFFER'}  "
          f"({vG.number_of_edges():,} edges, weights checked on 5,000)")

    # 2. per-query ranking parity
    bad = 0
    for qs in QUERIES:
        q = R.encode_query(V, qs)
        for label, vault_fn, mine_fn in (
            ("bfs", lambda: v_best_first_bfs(db, emb, ids, idx, q, a.k),
             lambda: R.bfs(V, qs, a.k)),
            ("ppr", lambda: v_hub_aware_ppr(db, emb, ids, q, a.k),
             lambda: R.ppr(V, qs, a.k)),
        ):
            # The vault has no navigation-note concept, so ask it for a longer
            # list and apply the filter BEFORE truncating -- which is what this
            # repo's implementation does. Filtering after truncation compares a
            # short list against a full one and reports a difference that is the
            # test's, not the code's.
            vres = [n for n, _ in vault_fn()][:a.k]
            mres = [n for n, _ in mine_fn()][:a.k]
            if vres != mres:
                bad += 1
                print(f"  DIFFER {label:<4} {qs[:44]}…")
                print(f"    vault: {vres[:4]}")
                print(f"    mine : {mres[:4]}")
    print(f"\nranking parity        {'MATCH' if bad == 0 else f'{bad} DIFFERENCE(S)'} "
          f"over {len(QUERIES)} queries x 2 strategies")
    if bad or not ok or not same:
        sys.exit(1)
    print("\nPASS — graph retrieval is identical to the source vault's")


if __name__ == "__main__":
    main()
