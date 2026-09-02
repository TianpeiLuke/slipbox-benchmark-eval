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

Two upstream skills are deliberately **not** ported:

- **capture-term-note** — its research steps fetch internal wikis and documents.
  That is both unavailable here and forbidden by the blind-ingestion rule:
  corpus notes must derive from the corpus alone.
- **search-notes** — superseded by `scripts/retrieval.py`, which is
  self-contained and runs on this repo's own hybrid index.
