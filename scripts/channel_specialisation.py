"""Do typed notes behave like channels -- does retrieval select different types
for different question types? If the distribution is flat across query types,
the taxonomy carries no query-relevant signal and 'directional' is a label
rather than a mechanism.
"""
import json, random, sqlite3, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, "scripts")
from retrieval import hybrid

random.seed(9)
raw = json.loads(Path("data/raw/multihop_rag/MultiHopRAG.json").read_text())
con = sqlite3.connect("vaults/multihop_rag/notes.db")
bb = {n: b for n, b in con.execute("SELECT note_id, building_block FROM notes")}
con.close()

by_type = defaultdict(list)
for q in raw:
    if q.get("evidence_list"):
        by_type[q.get("question_type", "?")].append(q["query"])
for t in by_type:
    random.shuffle(by_type[t]); by_type[t] = by_type[t][:40]

base = Counter(bb.values()); tot = sum(base.values())
rows = {}
for t, qs in sorted(by_type.items()):
    c = Counter()
    for query in qs:
        for nid, _ in hybrid(Path("vaults/multihop_rag"), query, 10):
            c[bb.get(nid, "?")] += 1
    rows[t] = c

kinds = [k for k, _ in base.most_common() if k]
print(f"{'building block':<24}{'vault':>8}" + "".join(f"{t.replace('_query',''):>13}" for t in rows))
for k in kinds:
    line = f"{k:<24}{base[k]/tot:>7.1%}"
    for t, c in rows.items():
        s = sum(c.values())
        line += f"{c[k]/s:>13.1%}" if s else f"{'-':>13}"
    print(line)
print("\nlift over the vault's own composition (retrieved share / vault share):")
for k in kinds:
    line = f"{k:<24}{'':>8}"
    for t, c in rows.items():
        s = sum(c.values())
        line += f"{(c[k]/s)/(base[k]/tot):>13.2f}" if s and base[k] else f"{'-':>13}"
    print(line)
