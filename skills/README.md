# Skills

Procedures for turning a benchmark corpus into a typed-note knowledge graph.
**All paths are local to this repository.** Notes live under `vaults/$CORPUS`,
each corpus has its own `notes.db`, and plans go to `experiments/plans/`.
No skill here reads or writes any vault outside this repo.

| Skill | Role |
|---|---|
| `slipbox-ingest-benchmark-corpus` | the adapter: corpus in, isolated vault out, questions quarantined |
| `plan-digestion` | decompose a source into building-block-atomic notes |
| `augment-digestion-plan` | add coverage map, split decisions, validation gates |
| `review-digestion-plan` | sign-off checkpoints before execution |
| `execute-digestion-plan` | write the notes, run the gates |
| `capture-term-note` | create a term note from corpus evidence and register it in the glossary |
| `validate-note-gates` | the shared gate every authoring skill ends with |
| `check-note-format` / `check-broken-links` / `fix-broken-links` / `fix-ghost-references` | validation and repair |

## Provenance

The nine pipeline skills are **ported** from an upstream vault's canonicals by
`scripts/port_skills.py`, which rewrites config-resolved paths to the local
`$VAULT`/`$DB`, maps every upstream validator and indexer onto this repo's
`validate_notes.py` / `build_local_db.py` / `retrieval.py`, strips vault-only
frontmatter, and converts internal wiki links to plain text. The port **fails
rather than ships** if any residual absolute path, config import, internal
token, or reference to a non-existent script survives.

Re-run it against an updated source with:

```bash
python3 scripts/port_skills.py /path/to/source/vault
```

**`capture-term-note` is rewritten by hand rather than ported.** The digestion
plan calls it for every undigested term, so it cannot simply be dropped — but
upstream researches each term against internal wikis and routes it into one of
several established domain glossaries. Neither is available here: external
research is forbidden by the blind-ingestion rule, and a fresh corpus has no
glossary at all. The local version researches **the corpus and vault only**, and
`scripts/glossary.py` **creates the glossary on first capture**, keeping it a
single alphabetical file until the corpus is large enough for domains to be
visible in the data rather than guessed up front.

**`search-notes` is not ported** — superseded by `scripts/retrieval.py`, which is
self-contained and runs on this repo's own hybrid index.
