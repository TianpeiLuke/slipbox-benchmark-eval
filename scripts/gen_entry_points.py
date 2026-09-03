#!/usr/bin/env python3
"""Generate the MultiHop-RAG entry-point hierarchy (navigation notes).

Navigation notes are GENERATED, not extracted (plan_corpus_master.md): they index
rather than assert, so they carry `building_block: navigation` and no source_docs
(FM-004 exempts them). Three levels, written so every target already exists:

  root      entry_multihop_rag.md          -> 6 category entries + references
  category  entry_<category>.md   (x6)     -> its cluster entries + root
  cluster   entry_<cid>.md        (x34)    -> one row per member note + parent category

Because build_local_db.py symmetrises every markdown link (the graph is
undirected), a cluster entry linking DOWN to its member notes gives each member
note an inbound edge -- which is what removes the graph-island (orphan) notes the
graph arm cannot otherwise reach. No content note is edited.
"""
from __future__ import annotations
import glob, json, os, re, sys
from collections import Counter, defaultdict

VAULT = "vaults/multihop_rag"
PLANS = "experiments/plans/multihop_rag"
IDX = json.load(open("data/corpus/multihop_rag/index.json"))

CATEGORY = {  # from plan_corpus_master.md
    "business":      ["c01","c02","c03","c04","c05"],
    "entertainment": ["c06","c07","c08","c09","c10","c11"],
    "health":        ["c12"],
    "science":       ["c13","c14"],
    "sports":        ["c15","c16","c17","c18","c19","c20","c21","c22","c23","c24","c25"],
    "technology":    ["c26","c27","c28","c29","c30","c31","c32","c33","pilot"],
}
CLUSTER_CAT = {c: cat for cat, cs in CATEGORY.items() for c in cs}

FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^# (.+)$", re.M)

def safe(text):
    """Markdown link text must not contain [ or ] (nested brackets break the
    link parser; the film '[REC]' is the corpus case). Strip them from anchors."""
    return text.replace("[", "").replace("]", "").strip()

def note_cluster():
    nc = {}
    for f in sorted(glob.glob(f"{PLANS}/clusters/c*.json")):
        cid = os.path.basename(f)[:-5]
        d = json.load(open(f))
        for sp in d.get("subplans", []):
            for n in sp.get("notes", []):
                nc[n["note"]] = cid
    for f in sorted(glob.glob(f"{PLANS}/subplan_*_assignments.json")):
        d = json.load(open(f))
        keys = d.keys() if isinstance(d, dict) else [ (it.get('note') if isinstance(it,dict) else it) for it in d ]
        for n in keys:
            if isinstance(n, str) and n.endswith(".md"):
                nc.setdefault(n, "pilot")
    return nc

def note_meta(fn):
    """(title, building_block, opening_claim) from a vault note."""
    p = os.path.join(VAULT, fn)
    txt = open(p, encoding="utf-8", errors="replace").read()
    m = FM.search(txt); fm = m.group(1) if m else ""
    bbm = re.search(r"building_block:\s*(\S+)", fm)
    bb = bbm.group(1) if bbm else "?"
    h1m = H1.search(txt); title = h1m.group(1).strip() if h1m else fn[:-3]
    body = txt[h1m.end():] if h1m else txt
    # first non-empty, non-heading line = the claim-first opening
    claim = ""
    for line in body.splitlines():
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith("---"):
            claim = s; break
    claim = re.sub(r"\s+", " ", claim)
    sent = re.split(r"(?<=[.!?])\s", claim)[0] if claim else ""
    if len(sent) > 160: sent = sent[:157].rstrip() + "…"
    return title, bb, sent

def write(path, text):
    with open(os.path.join(VAULT, path), "w", encoding="utf-8") as fh:
        fh.write(text)

def main():
    nc = note_cluster()
    by_cluster = defaultdict(list)
    for note, cid in nc.items():
        by_cluster[cid].append(note)
    all_clusters = sorted(by_cluster, key=lambda c: (0, int(c[1:])) if c.startswith("c") else (1, 0))

    # ---- cluster entries ----
    for cid in all_clusters:
        cat = CLUSTER_CAT[cid]
        notes = sorted(by_cluster[cid])
        rows, bbc = [], Counter()
        for fn in notes:
            title, bb, claim = note_meta(fn)
            bbc[bb] += 1
            rows.append(f"- [{safe(title)}]({fn}) — *{bb}*: {claim}")
        bbline = ", ".join(f"{v} {k}" for k, v in bbc.most_common())
        body = [
            "---", "building_block: navigation", "---", "",
            f"# Entry Point — {cat.title()} Cluster `{cid}`", "",
            f"Index of the {len(notes)} notes derived from the `{cid}` document cluster "
            f"({cat}). Building blocks: {bbline}.", "",
            f"Parent: [{cat.title()} Entry Point](entry_{cat}.md) · Root: "
            f"[MultiHop-RAG Corpus](entry_multihop_rag.md).", "",
            "## Notes", "",
            *rows, "",
            "## Related Notes", "",
            f"- [{cat.title()} Entry Point](entry_{cat}.md): parent category index this cluster belongs to.",
            "- [MultiHop-RAG Corpus](entry_multihop_rag.md): the corpus root index.",
            "",
            "## References", "",
            "- Source: index of notes derived from the MultiHop-RAG corpus "
            "(Tang & Yang, 2024, arXiv:2401.15391), ODC-BY-1.0.",
            "",
        ]
        write(f"entry_{cid}.md", "\n".join(body))

    # ---- category entries ----
    cat_counts = {}
    for cat, cs in CATEGORY.items():
        present = [c for c in cs if c in by_cluster]
        total = sum(len(by_cluster[c]) for c in present)
        cat_counts[cat] = total
        rows = []
        for c in present:
            n = len(by_cluster[c])
            rows.append(f"- [Cluster {c}](entry_{c}.md): {n} notes.")
        body = [
            "---", "building_block: navigation", "---", "",
            f"# {cat.title()} — Category Entry Point", "",
            f"Index of the {len(present)} `{cat}` clusters ({total} notes) in the "
            f"MultiHop-RAG corpus. Root: [MultiHop-RAG Corpus](entry_multihop_rag.md).", "",
            "## Clusters", "",
            *rows, "",
            "## Related Notes", "",
            "- [MultiHop-RAG Corpus](entry_multihop_rag.md): the corpus root index.",
            "",
            "## References", "",
            "- Source: index of notes derived from the MultiHop-RAG corpus "
            "(Tang & Yang, 2024, arXiv:2401.15391), ODC-BY-1.0.",
            "",
        ]
        write(f"entry_{cat}.md", "\n".join(body))

    # ---- root ----
    content = [f for f in glob.glob(f"{VAULT}/*.md")]
    def is_content(fn):
        b = os.path.basename(fn)
        return not b.startswith(("entry_", "term_")) and b != "glossary.md"
    allbb = Counter()
    for f in content:
        if not is_content(f): continue
        _, bb, _ = note_meta(os.path.basename(f))
        allbb[bb] += 1
    catrows = [f"- [{cat.title()}](entry_{cat}.md): {cat_counts[cat]} notes across "
               f"{len([c for c in CATEGORY[cat] if c in by_cluster])} clusters."
               for cat in CATEGORY]
    bbline = "\n".join(f"- {k}: {v}" for k, v in allbb.most_common())
    body = [
        "---", "building_block: navigation", "---", "",
        "# MultiHop-RAG Corpus — Root Entry Point", "",
        "Root index for the typed-atomic-note vault derived from the MultiHop-RAG "
        "benchmark corpus (609 news documents, 49 publishers). Navigation only — "
        "every note is reachable from here through its category and cluster entry points.", "",
        "## Quick Stats", "",
        f"- Source documents: 609 ({sum(d['words'] for d in IDX.values()):,} words, 49 publishers)",
        f"- Content notes: {sum(allbb.values())}",
        "- Building blocks:",
        *[f"  {l}" for l in bbline.splitlines()],
        "- Resolved link count: reported by `scripts/build_local_db.py --stats`.",
        "", "## Category Entry Points", "",
        *catrows, "",
        "## Related Notes", "",
        "- [Corpus Glossary](glossary.md): alphabetical index of the corpus term notes.",
        "", "## References", "",
        "- Corpus: MultiHop-RAG (Tang & Yang, 2024, arXiv:2401.15391), ODC-BY-1.0.",
        "- Plan: `experiments/plans/multihop_rag/plan_corpus_master.md`.",
        "",
    ]
    write("entry_multihop_rag.md", "\n".join(body))
    print(f"wrote {len(all_clusters)} cluster + {len(CATEGORY)} category + 1 root = "
          f"{len(all_clusters)+len(CATEGORY)+1} entry notes")

if __name__ == "__main__":
    main()
