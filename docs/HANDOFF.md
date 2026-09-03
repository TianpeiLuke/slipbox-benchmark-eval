# Handoff: continuing this work on another machine

Written for an agent picking this up cold. It covers what the project is, what
is already done, how to rebuild the data, how notes are made, and what to do
next. Read [BACKGROUND.md](BACKGROUND.md) for the research argument and
[BUILDING_BLOCKS.md](BUILDING_BLOCKS.md) for the note ontology.

---

## 1. What this is

**The question.** Does converting a document corpus into typed atomic notes with
a link graph retrieve better than chunking the raw documents — and if so, why?

**Why it needs a public benchmark.** A vault evaluated against questions
generated *from its own notes* is measuring itself: the questions inherit the
notes' vocabulary, so the notes win by construction. Every claim here is made
against **MultiHop-RAG**, whose 2,556 questions were written by other people
from a corpus we ingest but never author.

**The one rule everything depends on.** The ingesting side must never see the
questions. A note written with sight of them answers them by construction, and
every downstream number would then look valid while being meaningless.

```
data/corpus/multihop_rag/    the corpus half   — ingestion may read this
data/raw/multihop_rag/       BOTH halves       — MultiHopRAG.json is OFF LIMITS
```

Only three scripts may open the questions file, none of which builds the vault:
`fetch_benchmarks.py`, `select_slice.py`, `score_retrieval.py`.

```bash
python3 scripts/check_quarantine.py multihop_rag \
    --transcripts <agent transcript dir> --runs <run ids that shaped the vault>
```

This audits scripts, planning artifacts and agent transcripts. It also
distinguishes a *reference* from an *attestation* — an agent stating it did
**not** read the file is compliance, and flagging that would punish exactly the
behaviour the rule wants.

> The subtle breach is not an agent reading the gold. It is an **orchestrator**
> reading an aggregate — "gold evidence spans 2.6 documents on average" — and
> using it to decide how to build the graph. No note is contaminated and the
> treatment is still tuned on the test set. That happened once in this project's
> history and is why the guard exists.

---

## 2. Current state

| | |
|---|---|
| Corpus | MultiHop-RAG, 609 documents, 1,063,319 words, 49 publishers |
| Vault | `vaults/multihop_rag/` — **5,093 notes**, 40,712 resolved links, **0 orphans** |
| Mean note | 375 words; 299 notes cite more than one document |
| Of those | 4,925 content · 126 glossary terms · 41 entry points · 1 glossary |
| Plan | 33 cluster plans + 13 pilot sub-plans, 595 sub-plans total |
| Gates | validator 0 errors · 0 broken links · 0 ghosts · provenance PASS · quarantine PASS |
| Baseline | chunk-RAG measured: BM25 **Recall@10 0.699**, **All-Recall@10 0.419** |
| Notes arm | **not yet scored** — this is the next step |

There is also `vaults/multihop_rag_handwritten/` — 42 notes written by hand as a
**control arm**. It holds the note format fixed and varies only the method, which
separates "the format helps" from "the pipeline produces the format well".

---

## 3. Setup

```bash
git clone https://github.com/TianpeiLuke/slipbox-benchmark-eval
cd slipbox-benchmark-eval
pip install numpy sentence-transformers    # only needed for the dense arm
```

**Nothing under `data/` is committed** — it is the publishers' content, not ours.
One command rebuilds it:

```bash
bash scripts/rebuild_data.sh multihop_rag
```

That fetches the benchmark (~69MB), prepares the corpus half into one plain
document per file, and **verifies every download against `data/manifest.json`**,
which records each file's URL, license and sha256. A rebuild that cannot be
verified is a rebuild you should not trust.

Confirm the toolchain before doing anything else:

```bash
bash scripts/selftest.sh        # DB build, retrieval, publication gate, all gates
bash scripts/test_gates.sh      # 18 assertions on a deliberately broken vault
```

To confirm the vault is complete rather than merely present:

```bash
python3 scripts/check_execution.py   multihop_rag --vault vaults/multihop_rag
python3 scripts/check_provenance.py  multihop_rag --vault vaults/multihop_rag
python3 scripts/mark_plan_status.py  multihop_rag --vault vaults/multihop_rag --check
```

All three derive their answer from the vault. `mark_plan_status.py --check`
exists because a `status:` field is a claim that decays: it is written when a
plan is authored and nothing forces it to change when the plan is executed.
Thirteen sub-plans here read `ready` after being fully written, and 33 cluster
plans carried no status at all. Run it without `--check` to correct them.

`check_execution.py` asks the question a `status:` field cannot answer, in both
directions: every planned note exists, and every note on disk is accounted for
by some plan. It also verifies that every corpus document is cited and that
every note is **reachable from the root entry point** — a note with no path from
the root is invisible to the graph arm, whatever else is true of it.

---

## 4. How notes get made

Six stages. **Programs do what is structural and reproducible; agents do only
what requires reading.** Keeping that boundary is what makes the fan-out
affordable and the output checkable.

```
partition_corpus.py     → clusters of ~20 documents        (no reading)
  ↓  agent per cluster: read every document, assign paragraph blocks to notes
verify_cluster_plan.py  → re-derives every constraint from the corpus
merge_cluster_plans.py  → finds what no single cluster can see
build_term_links.py     → term links, derived from each note's own source
build_note_links.py     → note links, with the REASON each one exists
  ↓
emit_write_brief.py     → per-cluster brief with the source text inlined
  ↓  agent per cluster: write the notes from the brief
validate_notes.py · check_provenance.py · build_local_db.py
```

### The note contract

```markdown
---
building_block: <one of eight — see BUILDING_BLOCKS.md>
source_docs: [doc_0123, doc_0456]
---

# Title Case Heading

Claim-first body. The first paragraph answers the note's question outright.
Each paragraph is ONE continuous line — never hard-wrap mid-paragraph.

## Related Notes

- [Other Note](other_note.md): how it relates, not merely that it does

## Source

- doc_0123: publisher, date
```

`source_docs` is **the scoring key**. Gold evidence is document-level, so a note
is credited only through the documents it names. A wrong value is not rejected
anywhere — it validates, indexes and retrieves, and simply scores against the
wrong evidence. `check_provenance.py` is the only thing that catches it.

`navigation` notes (glossaries, entry points) are exempt from `source_docs`:
they index rather than assert, so their links are their provenance.

### Two rules that decide note boundaries, in this order

1. **Topical coherence governs.** One note, one subject.
2. **Density constrains size.** Past 1,800 source words a coherent unit splits
   again — at a sub-topic boundary, never at a word count.

Applying size first merges a 1,200-word newsletter roundup's fifteen unrelated
items into one note, which is then retrieved for everything and answers nothing.
**Size is a budget, not a boundary.**

### Rebuilding a plan or vault from scratch

```bash
python3 scripts/partition_corpus.py multihop_rag --target 20 --out clusters.json
# ... run the planning agents (see experiments/wf_plan_corpus.js for the prompt)
python3 scripts/verify_cluster_plan.py multihop_rag --plan <cluster>.json --own-docs <docs>
python3 scripts/merge_cluster_plans.py multihop_rag --clusters experiments/plans/multihop_rag/clusters
python3 scripts/build_term_links.py  multihop_rag --plans experiments/plans/multihop_rag --floor 3 --out .../term_links.json
python3 scripts/build_note_links.py  multihop_rag --plans experiments/plans/multihop_rag --out .../note_links.json
python3 scripts/emit_write_brief.py  multihop_rag --cluster c01 --out .../briefs/c01.md
# ... run the writing agents
python3 scripts/build_local_db.py    vaults/multihop_rag --stats
python3 scripts/check_provenance.py  multihop_rag --vault vaults/multihop_rag
```

---

## 5. What to do next

**The experiment has not been run.** Everything above exists to make it
possible; none of it is the result.

### Step 1 — build the index

```bash
python3 scripts/build_local_db.py vaults/multihop_rag --with-embeddings --stats
```

The index has three parts that must come from the **same** notes: FTS5 and the
link graph inside `notes.db`, and the dense vectors beside it. One pass builds
all three and then checks their ids agree, because a dense index left over from
an earlier vault answers with notes the database no longer has, and nothing
downstream reports it.

Vectors stay in a `.npy` rather than a BLOB column deliberately: dense search
reads every vector for every query, which a memory-mapped array does in one
operation and a per-row SQLite scan does not.

`dense` and `hybrid` **raise** rather than degrade when this index is missing.
That is deliberate: returning an empty list would make `hybrid` silently equal
`bm25`, and a missing index would read as a real result.

### Step 2 — score the notes arm against the chunk baseline

```bash
python3 scripts/build_chunk_baseline.py multihop_rag --words 200 --overlap 50
python3 scripts/score_retrieval.py multihop_rag --arm chunks --strategies bm25,hybrid --k 2,5,10
python3 scripts/score_retrieval.py multihop_rag --arm notes  --vault vaults/multihop_rag \
        --strategies bm25,hybrid,bfs,ppr --k 2,5,10
```

Two things to hold onto while reading the output:

- **Chunk size is a free parameter that moves the baseline** (`--sweep` spans
  14,177 to 1,772 chunks). Run more than one before claiming either arm wins.
- **Never match on `k`.** Matching *k* hands the win to whichever representation
  has larger units. Match on token budget.

### Step 3 — the comparisons worth making

| Comparison | What it isolates |
|---|---|
| notes vs chunks | the headline question |
| notes vs `multihop_rag_handwritten` | the format, versus the pipeline that produces it |
| `bfs`/`ppr` vs `bm25` on notes | whether the **graph** adds anything beyond the notes |
| budget sweep 512 → 8192 tokens | H1: is any advantage largest when the budget is tight? |

The budget range matters and was chosen, not assumed: **100%** of documents
exceed 512 and 1,024 tokens, **36.9%** still exceed 2,048, and the pressure is
gone by 8,192. A comparison run only at a large budget cannot show a slope.

### Step 4 — still open

- **H3 needs an order-sensitive metric.** Its first pass returned a null, and
  the null was uninformative: bag-of-words recall is order-invariant by
  construction, so it cannot detect position effects at all.
- ~~Term and entry-point notes~~ **done** — 126 term notes, a 41-note
  entry-point hierarchy and the glossary landed from another machine. Four terms
  deliberately reused an existing note instead of duplicating it, recorded in
  `term_reuse.json`; one was dropped for linking to nothing, recorded in
  `terms_dropped.md`. Both files exist so an absence is auditable rather than
  merely absent.
- ~~725 orphans~~ **0** — the entry-point hierarchy connected every note.

---

## 6. Hard-won lessons

Each of these cost real time here. They are listed because the failure mode is
the same in every case: **something that looked correct and was not.**

**A verifier that reuses the builder's code proves nothing.** The term-link
`--verify` guard passed a matcher that had no word boundaries, so `bot` matched
inside "both", `NFL` inside "influenza", `WHO` matched the pronoun. Verifier and
builder shared the bug, so verification only confirmed self-consistency.

**Agent self-reports are not evidence.** Every constraint is re-derived from the
corpus. Agents returned well-formed plans that broke block ranges, assigned one
source block to two notes, and oversized sub-plans — none visible without
recomputing.

**A weak edge is not a free edge.** `bfs` and `ppr` traverse every edge given, so
a spurious link degrades the arm as surely as a missing one. Single-shared-term
links were 22.9% of the graph and linked an FTX trial note to a football recap
through the football sense of "defense". Link density has an **optimum**, not a
maximum.

**Do not lower a threshold to make a failure disappear.** Three clusters failed a
coverage floor. The fix was not a lower floor but a verifier that must *prove*
the dropped material is chrome — short headings, promotional boilerplate,
self-referential framing. All three then passed with the evidence shown.

**Cross-document edges are the ones that matter here.** Ranking the tightest
relation first — same article — is the obvious choice and it is wrong for
multi-hop: it fills the graph with edges connecting notes a retriever already
reaches together.

**A checker only knows the plan shape it was taught.** `check_provenance.py`
reported 91 term notes as UNPLANNED when they arrived, because it read block
assignments and had never heard of `terms.json`. The notes were correct; the
checker was incomplete. When a gate fires on incoming work, establish which side
is wrong before acting on it.

**Trust the agents' problem reports.** Two independently flagged the noisy links;
all thirteen pilot agents flagged an empty `building_block` in my brief
generator and recovered the value from the plan rather than inventing one. Both
bugs were mine, and both were found by reading what the agents said rather than
what they returned.

---

## 7. Repository map

```
docs/          BACKGROUND (the argument) · BUILDING_BLOCKS (the ontology) · this file
skills/        11 digestion skills, ported from a private vault; port_skills.py regenerates
scripts/       everything above; each has a docstring explaining WHY, not just how
vaults/        multihop_rag (4,925 notes) · multihop_rag_handwritten (control arm)
experiments/   plans/ (cluster plans, term and note links, provenance map) · wf_*.js prompts
data/          gitignored except manifest.json; rebuild with scripts/rebuild_data.sh
```

Scripts are documented for *why* a rule exists, because a rule whose reason is
lost gets removed the first time it is inconvenient.
