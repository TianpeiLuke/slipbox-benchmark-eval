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


def dense(vault: Path, query: str, k: int) -> list[tuple[str, float]]:
    import numpy as np
    epath, ipath = vault / "embeddings.npy", vault / "embedding_ids.json"
    if not epath.exists():
        return []
    global _MODEL
    meta = json.loads(ipath.read_text())
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
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

def load_graph(vault: Path) -> dict[str, list[str]]:
    """Adjacency over RESOLVED in-vault links only. An unresolved link points
    outside this vault and must never be traversed."""
    con = sqlite3.connect(vault / "notes.db")
    adj: dict[str, list[str]] = defaultdict(list)
    for s, t in con.execute(
            "SELECT source_note_id, target_note_id FROM note_links WHERE resolved=1"):
        adj[s].append(t)
        adj[t].append(s)          # treat links as undirected for reachability
    con.close()
    return adj


def bfs(vault: Path, query: str, k: int, seeds: int = 5, depth: int = 2
        ) -> list[tuple[str, float]]:
    """Best-first expansion: seed with hybrid, walk resolved links outward,
    discounting by hop distance."""
    adj = load_graph(vault)
    seeded = hybrid(vault, query, seeds)
    scores: dict[str, float] = {nid: s for nid, s in seeded}
    frontier = [(nid, 0) for nid, _ in seeded]
    seen = {nid for nid, _ in seeded}
    while frontier:
        nid, d = frontier.pop(0)
        if d >= depth:
            continue
        base = scores.get(nid, 0.0)
        for nb in adj.get(nid, []):
            gain = base * (0.5 ** (d + 1))
            scores[nb] = max(scores.get(nb, 0.0), gain)
            if nb not in seen:
                seen.add(nb)
                frontier.append((nb, d + 1))
    return sorted(scores.items(), key=lambda x: -x[1])[:k]


def ppr(vault: Path, query: str, k: int, seeds: int = 5) -> list[tuple[str, float]]:
    """Personalised PageRank with the teleport distribution set to the hybrid
    seeds. This is the HippoRAG-style graph arm."""
    adj = load_graph(vault)
    if not adj:
        return hybrid(vault, query, k)
    seeded = hybrid(vault, query, seeds)
    if not seeded:
        return []
    total = sum(s for _, s in seeded) or 1.0
    teleport = {nid: s / total for nid, s in seeded}
    nodes = set(adj) | set(teleport)
    rank = {n: teleport.get(n, 0.0) for n in nodes}
    for _ in range(PPR_ITERS):
        nxt = {n: (1 - PPR_ALPHA) * teleport.get(n, 0.0) for n in nodes}
        for n, r in rank.items():
            nbrs = adj.get(n)
            if not nbrs:
                # dangling mass returns to the teleport set
                for t, w in teleport.items():
                    nxt[t] += PPR_ALPHA * r * w
                continue
            share = PPR_ALPHA * r / len(nbrs)
            for nb in nbrs:
                nxt[nb] = nxt.get(nb, 0.0) + share
        delta = sum(abs(nxt[n] - rank[n]) for n in nodes)
        rank = nxt
        if delta < 1e-8:
            break
    return sorted(rank.items(), key=lambda x: -x[1])[:k]


STRATEGIES = {"bm25": bm25, "dense": dense, "hybrid": hybrid, "bfs": bfs, "ppr": ppr}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("vault")
    ap.add_argument("--query", required=True)
    ap.add_argument("--strategy", default="hybrid",
                    choices=list(STRATEGIES) + ["all"])
    ap.add_argument("--k", type=int, default=5)
    a = ap.parse_args()

    vault = Path(a.vault)
    if not (vault / "notes.db").exists():
        print(f"no database at {vault}/notes.db; run build_local_db.py first")
        sys.exit(2)

    names = list(STRATEGIES) if a.strategy == "all" else [a.strategy]
    for name in names:
        res = STRATEGIES[name](vault, a.query, a.k)
        print(f"\n=== {name} ===")
        if not res:
            print("  (no results -- embeddings missing, or no lexical match)")
        for i, (nid, sc) in enumerate(res, 1):
            print(f"  {i}. {sc:8.4f}  {nid}")


if __name__ == "__main__":
    main()
