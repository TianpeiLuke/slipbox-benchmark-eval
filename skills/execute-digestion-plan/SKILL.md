---
tags:
  - resource
  - skill
  - procedure
  - capture
  - planning
  - execution
  - multi_agent
  - dynamic_workflow
keywords:
  - execute digestion plan
  - slipbox-execute-digestion-plan
  - in-vault skill canonical
  - dynamic workflow
  - subagent dispatch
  - master agent contract extraction
  - plan amendment
  - pilot calibration
  - bounded fix loop
  - independent verification
topics:
  - Skill Procedures
  - Vault Tools
  - Multi-Agent Execution
language: markdown
date of note: 2026-06-12
status: active
building_block: procedure
---

# Procedure: slipbox-execute-digestion-plan (Canonical Body)

> **Ported skill.** Adapted from an upstream vault canonical for use in this
> repository. All paths are local: notes live under `vaults/$CORPUS`, the database
> is that corpus's own `notes.db`, and plans go to `experiments/plans/`. This skill
> never reads or writes any vault outside this repo.

This is the **single canonical body** for the `slipbox-execute-digestion-plan` skill (FZ 12a). The thin headers under `.claude/skills/slipbox-execute-digestion-plan/SKILL.md` and `.kiro/skills/slipbox-execute-digestion-plan/SKILL.md` point an invoking agent here for the procedural content.

## Skill description <!-- :: section_id = skill_description :: -->

Execute a digestion plan that has passed review (`status: ready`) using the multi-agent runbook strategy + Claude Code dynamic workflows. The skill plays the role of **master orchestrator**: it pilots one note, derives per-batch sub-agent contracts from the plan, dispatches a fleet of sub-agents (one per note) via dynamic workflow, validates each batch with a master validator + bounded fix loop, and runs independent post-hoc verification before commit + push. The master agent has explicit authority to **modify the plan as it sees fit** (with amendments recorded in the plan file) and **extract parts of the plan** to form the contracts each sub-agent receives. Use AFTER `/slipbox-review-digestion-plan` returns READY.

## Setup <!-- :: section_id = setup :: -->

```bash
# Paths are LOCAL to this repository. Nothing here reads or writes any other vault.
CORPUS="${CORPUS:?set CORPUS, e.g. musique}"
VAULT="vaults/$CORPUS"          # notes for this corpus
DB="$VAULT/notes.db"            # this corpus's own database
PLANS="experiments/plans/$CORPUS"
```

## Resources <!-- :: section_id = resources :: -->

- **Plan to execute**: `$PLANS/plan_digest_<topic>.md` (must have `status: ready`)
- **Methodology**: [Runbook: Large-Scale Note Processing with Multi-Agent Pipelines (FZ 28f1)](../policy_sops/runbook_large_scale_note_processing_multiagent.md) — the playbook this skill implements
- **Empirical reference**: Deep Dive: VCL Variable Note Enrichment Multi-Agent Pipeline (FZ 28f2) — case study (130 notes, 18 batches, 221 agents, all gates passed); Deep Dive: Causal Handbook Digest Campaign (FZ 28f3) — generative case study (139 notes) + the rate-limit/fan-out-cap learnings
- **Gate**: `python3 scripts/validate_notes.py "$VAULT" --gate` — one validator for frontmatter, structure, broken links and ghosts; see `skills/validate-note-gates/SKILL.md`. (The upstream per-campaign workflow templates are not ported: this repo drives execution from the plan file directly.)
- **Dynamic workflow announcement**: Claude Code Dynamic Workflows (2026-06-12) — feature: unlimited subagents, `/workflows` panel, requires Opus 4.7/4.8 + `/effort ultracode`
- **Validation skills (closing gates)**: `/slipbox-check-note-format`, `/slipbox-check-broken-links`, `/slipbox-run-full-database-rebuild`

---

## Step 0: Pre-Flight — Verify Plan Is Ready <!-- :: section_id = step_0_preflight :: -->

```bash
# Confirm plan exists and has status: ready
test -f "$PLANS/$PLAN_FILE" || { echo "Plan not found"; exit 1; }
grep -E '^status:\s*ready' "$PLANS/$PLAN_FILE" || {
  echo "Plan status is not 'ready' — run /slipbox-review-digestion-plan first"; exit 1; }
```

Refuse to start if:
- Plan status is `pending` or `in-progress` (not yet sign-off)
- Plan is missing a Planned Notes table (or a Sub-Plans Index Table for master plans)
- Source URLs are unreachable (do a HEAD-check on 1-2)

For master + sub-plans (per Step 1e of `/slipbox-plan-digestion`), this skill operates on ONE plan at a time. Master plans are not executed directly — execute each sub-plan independently in priority order.

> **Entry-point creation timing (G-G, added 2026-06-13).** For master+sub-plans, create the dedicated
> `entry_<slug>.md` as a **standalone pre-step BEFORE the first sub-plan executes** (and add its back-link
> row to the named parent hub from the master's "Entry Points to Update"). Each sub-plan then appends its
> rows to that hub, and every new note can receive its entry-point back-link (feeds G8). Do NOT defer
> entry-point creation to "after all sub-plans" — that leaves early notes without a hub link.

---

## Step 1: Boot — Master Agent Reads Plan + Spot-Checks Source <!-- :: section_id = step_1_boot :: -->

The master orchestrator reads the plan from start to finish AND spot-checks 1-2 of the densest source pages with the same tool the plan used. This pass identifies plan amendments that should land BEFORE any sub-agent runs.

Output of Step 1: a `## Plan Boot Report` line written into the plan file recording:
- Source pages spot-checked + measured word count vs plan estimate
- Any defects observed (placeholder strings, mismatched section counts, missing required fields)
- Initial defect inventory (which notes will need which kind of work)

---

## Step 2: Plan Amendment (Master Agent Authority) <!-- :: section_id = step_2_amend :: -->

> **Master agent has explicit authority to modify the plan** — this is the design of the skill. A plan written hours or days earlier may have under-counted words, mis-classified a building block, or assumed a section was small that turns out to be 4000 words. The master agent corrects these mismatches BEFORE fan-out, where fixes are cheap (a table edit) rather than expensive (re-doing 100 sub-agent runs).

### 2a. Classify the amendment scope

| Amendment | Authority | Action |
|---|---|---|
| Density correction (split a note, merge two notes) | **Auto-apply** — record in `## Plan Amendments` section | Master agent updates the Planned Notes table + Section Coverage Map |
| BB re-classification (procedure → concept, etc.) | **Auto-apply** — record | Master agent updates Planned Notes table + adds rationale |
| Reference-mapping correction (add/drop a related note) | **Auto-apply** — record | Master agent updates Per-Note Related Notes Mapping |
| Re-route to a different directory | **Pause for user approval** | Master agent reports proposed change + waits |
| Drop a planned note entirely | **Pause for user approval** | Master agent reports + waits |
| Change the source URL | **Pause for user approval** | Master agent reports + waits |
| Add a NEW note not in the plan | **Pause for user approval** | Master agent reports + waits |

### 2b. Append `## Plan Amendments` section

```markdown
## Plan Amendments (by master agent during execution)

| Date | Section | Original | Amended | Rationale |
|---|---|---|---|---|
| YYYY-MM-DD HH:MM | Planned Notes | note_X (1 note, 1500w est.) | note_Xa + note_Xb (split, measured 3200w) | Source page actually 3200w, exceeds 2500w threshold |
| ... | ... | ... | ... | ... |
```

This section is the durable record. Every amendment must trace back to a concrete observation (measured word count, source structure, etc.) — never a master agent's "I think it would be cleaner if..."

### 2c. Rule: don't redesign the plan, correct it

Plan amendments correct mistakes the plan-author couldn't have seen. They do NOT re-invent the routing, the BB taxonomy, or the gate definitions. If the plan structure is fundamentally wrong (e.g., wrong source-of-truth identified), STOP and route back to `/slipbox-augment-digestion-plan` or `/slipbox-plan-digestion`.

---

## Step 3: Pilot — Hand-Execute One Note + Calibrate Gates <!-- :: section_id = step_3_pilot :: -->

Per Phase 2 of the runbook. Pick one representative note from the Planned Notes table (preferably the one with the most cross-references — it stresses the link-resolution path).

> **The pilot is a COST control, not only a quality control (FZ 28f7 economics).** Under fan-out, a wrong
> method costs N× — every sub-agent repeats the mistake. A single hand-built pilot + a check of the method
> against the canonical caps that risk at 1×; its ROI is the entire batch you would otherwise revert. (In
> the CC-docs run, skipping this discipline cost ~4M reverted tokens, ~36% of the spend — see FZ 28f4.)
> **Never fan out an un-piloted method.**

### 3a. Master agent writes the pilot manually

Read the assigned source page. Write the note following the plan's Note Format Definition + Section Coverage Map + Per-Note Related Notes Mapping. Run the plan's validation scripts (Script 1 Format+Density, Script 2 Cross-Link, Script 3 Prerequisite Duplication).

### 3b. Calibrate gates on the pilot

| Calibration | Result |
|---|---|
| Run gates on the pilot (known-good) → ALL should pass | Any FAIL is a false positive — fix the gate or the contract |
| Construct a known-bad version (insert a placeholder string, drop a section) → gate MUST fail | If it passes, the gate is too weak — strengthen it |
| Gate that rejects a placeholder must NOT be satisfiable by paraphrasing | Test: paraphrase the placeholder and re-run the gate |

Record calibration outcomes in a `## Pilot + Gate Calibration` section appended to the plan.

### 3c. Embed the pilot as the worked example

The completed pilot note path goes into the per-batch contract (Step 4) as `WORKED_EXAMPLE_PATH`. Sub-agents read it as the quality anchor — "match this exact shape."

---

## Step 4: Extract Contracts (Master Agent Derives Per-Batch Contracts) <!-- :: section_id = step_4_extract_contract :: -->

> The plan is the durable specification. The contract is the per-batch projection of the plan that each sub-agent actually receives. The master agent EXTRACTS the contract from the plan — selecting and reorganizing plan sections into a self-contained sub-agent brief.

### 4a. The shared contract (one per execution run)

Extract these sections from the plan and concatenate into `$PLANS/contract_<plan_slug>_shared.md`:

| From the plan | Extracted into the shared contract |
|---|---|
| Note Format Definition (YAML template + forbidden fields) | **YAML contract** |
| Pacing Rules | **Pacing rules** |
| Per-Phase GATE Tables | **Gate spec** |
| Validation Scripts (bash) | **Script appendix** (sub-agent does NOT run these — the validator does) |
| Important Constraints | **Absolute rules** (BB *and thought* atomicity, self-sufficiency, data preservation, density, no fabrication) |
| Source URL + measured word counts | **Source provenance** |
| Pilot path | **Worked example** (must be read first) |

Add three sections the plan does NOT provide:

```markdown
## Absolute Rules (Non-Negotiable)

1. **Read source FIRST** — before writing anything, fetch the assigned source page(s) fully.
2. **No fabrication** — every claim must trace to source. Sanctioned honest outputs:
   - `"Not specified in source"` when a fact is absent
   - `*(source metadata description absent — inferred from logic)*` when reasoning beyond source
3. **No forbidden placeholders** — never write the literal strings `"Description missing"`, `"TBD"`, `"TODO"`, or any equivalent paraphrase.
4. **BB atomicity** — one building_block per note. If your assigned section mixes BBs, return STATUS=split-needed and DO NOT write the note.
5. **Thought atomicity** — one *thought* of that block's kind, which is a separate constraint from rule 4 and the one most often missed. What counts as one thought depends on the block:

   | your building block | write exactly one | return split-needed when the source gives you |
   |---|---|---|
   | concept | definition — term, genus and differentia, boundary | a second term to define |
   | model | relation — entities, the relation, the conditions it holds under | a second relation |
   | procedure | **outcome** — precondition, ordered steps, verifiable postcondition | a second independent postcondition |
   | empirical_observation | measurement — subject, metric, value, conditions, provenance | a second independent metric |
   | argument | claim — with its warrant, evidence and scope | a second claim to defend |
   | counter_argument | objection — naming and **linking** its target | a second target |
   | hypothesis | testable proposition — with its prediction and falsifier | a second falsifier |
   | navigation | index scope — with its ordering principle | a second unrelated scope |

   **A procedure's atom is one OUTCOME, not one step.** Nine steps reaching one verifiable end state is one note; three outcomes is three notes.

   **Target weight for the body** (excluding frontmatter and Related Notes). A note competes with a 100-word chunk on information per token, and at 190 words for one thought it loses that comparison two to one:

   | your block | write | stop and reconsider past |
   |---|---|---|
   | empirical_observation | 40–90 words | 130 |
   | concept | 50–110 | 160 |
   | navigation | 40–120 plus the list | 170 |
   | model / hypothesis / counter_argument | 60–130 | 190 |
   | argument | 70–150 | 220 |
   | procedure | 80–250 | 350 |

   Past the ceiling you are either holding a second thought — return STATUS=split-needed — or padding one, which is more likely and is a defect no other rule catches.

   **Do not spend words on:** a preamble restating the title (it is already indexed and read first); a closing summary (a note this short does not need to recapitulate itself); transitions to other notes (that is the relation, and it belongs in the link); hedging that carries no scope condition ("it is worth noting that"). A real scope condition — *in the EU*, *after 2023*, *for enterprise accounts* — is content and stays.

   Before writing, apply the **split test**: could this be two notes answering *different questions*? If yes, return STATUS=split-needed with the two proposed thoughts named. A short note is not automatically atomic — three claims in two hundred words fails this rule and passes rule 6.

6. **Self-sufficiency** — the note must be readable alone. Never open with an unresolved reference (`he`, `this`, `the company`, `however`); name the subject; carry the date where the source has one. Atomicity without resolution produces fragments, which is the opposite failure and equally disqualifying. **Do not satisfy rule 5 by deleting the context rule 6 requires.**
7. **Preserve the data** — paraphrase the prose, never the data. Every date, quantity with a unit, proper name and figure in your assigned source must appear in the note, verbatim where it is a number or a name.
8. **Density** — if your draft exceeds 400 lines / 2500 words / 6 code blocks, return STATUS=split-needed. This is a backstop for notes that are too LARGE; it cannot detect one that is merely diffuse, which is what rule 5 is for.
9. **Verbatim code** — code blocks must be character-for-character from source. No reformatting.

## Return Schema (Structured Output)

Every sub-agent returns:

| Field | Type | Required |
|---|---|---|
| `note_path` | str | yes |
| `status` | enum[`ok`, `split-needed`, `source-mismatch`, `error`] | yes |
| `word_count` | int | yes |
| `line_count` | int | yes |
| `code_block_count` | int | yes |
| `inferred_fields` | list[str] (per-field justification) | yes |
| `not_in_source_fields` | list[str] | yes |
| `cross_references_used` | list[path] | yes |
| `notes` | str (free-form report) | optional |
```

### 4b. Per-batch assignments

For each batch defined in the plan's batch table, extract the per-note rows into `$PLANS/contract_<plan_slug>_batch_<N>.md`:

```markdown
# Batch <N> Assignments

Reads: contract_<plan_slug>_shared.md

| Note | Target Path | Source Path / URL | Per-Note Related Notes (from plan) | Per-Note Inlinks (from plan) |
|---|---|---|---|---|
| note_1 | topic_overview.md | https://... | [term:A], [tool:B], [entry:C] | from repo_X.md, snippet_Y.md |
| ... | ... | ... | ... | ... |
```

The per-batch file is what each sub-agent receives alongside the shared contract.

### 4c. Constraint on extraction: faithful projection only

The extraction may NOT introduce content that isn't in the plan. If the plan is missing required information (e.g., a sub-agent contract needs cross-references but the plan doesn't list them), return to Step 2 and amend the plan first.

---

## Step 5: Dispatch — Dynamic Workflow Pipeline <!-- :: section_id = step_5_dispatch :: -->

Per Phase 5 of the runbook. Use the dynamic workflow with `pipeline()` so each batch flows enrich → validate → fix INDEPENDENTLY (no global barrier — a slow batch never blocks fast ones).

### 5a0. Cost & wave budgeting (FZ 28f7 economics)

Before dispatching, budget the run — make scale a choice, not a surprise:

- **Token cost ≈ items × per-item.** Calibrate per-item from the pilot or a sibling campaign (enrichment ≈ ~106K tokens/note [VCL FZ 28f2/28f5]; planning author+verify ≈ ~170K/sub-plan [FZ 28f7]). Project the total before launching.
- **Wall-clock ≈ ceil(items / ~16) × per-agent-time** — throughput is concurrency-bound (`~min(16, cores−2)`), NOT token-bound; a 1.9M-token wave and a 1.3M-token wave finish in roughly the same time. Parallelism trades tokens for time.
- **The ~30-agent/run fan-out cap governs BURST (rate-limit avoidance), not total cost** (FZ 28f3). Split large runs into ≤30-note waves; total tokens are unchanged by wave size — only the transient-rate-limit risk is.
- **Verification is the cheapest control, not overhead to cut.** The adversarial validator + the deterministic post-check (~30–50% overhead) intercept defects pre-commit; a defect that reaches a committed batch costs far more (reindex, broken-link sweep, re-dispatch). Step 6 stays non-negotiable.
- **Commit per sub-plan / per batch** so the blast radius of any single bad wave is bounded (cheap to revert one wave, expensive to unwind many).

### 5a. Pre-flight for dynamic workflow

```
/model      → Opus 4.7 or 4.8 (required for dynamic workflows)
/effort ultracode    → enable the subagent fleet
/workflows           → opens the panel for live monitoring (arrow keys to view each subagent)
```

### 5b. The three-stage pipeline (per batch)

```
pipeline(batches,
  // STAGE 1 — ENRICH/CAPTURE: one agent per note, concurrent
  batch => parallel( notes.map(note => () =>
    agent({
      prompt: SHARED_CONTRACT + BATCH_ASSIGNMENT(batch, note) + WORKED_EXAMPLE,
      schema: NOTE_SCHEMA,
      label: `capture:${note.target_path}`,
      phase: 'Capture'
    })
  )),

  // STAGE 2 — VALIDATE: one master validator per batch
  (captured, batch) => agent({
    prompt: VALIDATOR_PROMPT(batch) + GATE_SCRIPT + FAITHFULNESS_PROTOCOL,
    schema: VALIDATION_SCHEMA,
    label: `validate:batch-${batch.id}`,
    phase: 'Validate'
  }),

  // STAGE 3 — FIX: bounded loop (≤2 rounds)
  (validation, batch) => fixLoop(validation, batch, { maxRounds: 2 })
)
```

### 5c. Sub-agent dispatch principles (load-bearing)

1. **One agent per atomic unit** (one note). Isolates hallucination blast radius — a fabrication in one note can't contaminate siblings — and keeps each agent's context focused on a single source.
2. **Structured output** (`schema:`) per agent — platform retries on schema mismatch, and you get auditable per-note reports for free.
3. **Concurrency is auto-capped** (~min(16, cores−2)); pass all items, the platform queues them.
4. **Label agents** for the `/workflows` panel — `capture:<note>`, `validate:batch-N`, `fix:<note>` makes live progress readable.
5. **Filter nulls** before consuming results — an agent that dies on a terminal error returns `null`.
6. **Auth fail-closed + a pre-flight probe** (added 2026-06-24 after the Pipelines B2 incident — see 5f). Every agent that reads source via an authenticated tool (`local file read`, auth-gated fetches) MUST treat an auth failure as a *failure*, not a silent pass; and a wave SHOULD open with one cheap auth-probe agent that fails the whole wave fast if the authenticated fetch path is down — far cheaper than fanning out a wave that silently produces unverified notes.

### 5d. The master validator (Stage 2) does FOUR things — automation alone is not enough

1. **Run the gate script** (Script 1 + Script 2 from the plan) on the batch glob. *(The gate is deterministic/local — it works even when source-auth is down; report its result regardless so the orchestrator can see the local checks passed.)*
2. **Faithfulness spot-check** — pick 2-3 notes; re-read BOTH the source and the note; verify NO fabrication (values match source, logic steps correspond to real code, no invented facts, inferred markers used honestly). **Fabrication is a *blocking* failure, categorically distinct from a format failure.** This step REQUIRES a live source re-read — if you cannot fetch source, you have NOT done it (see 5f).
3. **Cross-reference integrity** — confirm every emitted link target exists (the anti-ghost check).
4. **Completeness** — confirm the domain invariant from the plan (e.g. "every variable identifier appears in keywords", "every source H2/H3 covered").

Verdict: `pass` only if gates pass AND a **real source re-read** confirmed no faithfulness issues. Must emit a **specific, actionable problem list per failing note** (e.g., `note_path: ..., problems: ["G3-Density: 4200 words, must split", "G2-Grounding: claim X has no source citation"]`). **Never report `pass` on internal-consistency/plausibility alone** — an unverifiable result is `auth_blocked` (see 5f), not `pass`.

### 5f. Auth fail-closed — the silent-degradation guard (added 2026-06-24, Pipelines B2 incident)

> **What happened (FZ — Pipelines B2).** Mid-wave, the authenticated fetch path auth expired. `local file read` started returning login pages instead of doc content. The note-writers and the validator kept going — the validator returned `verdict: pass` on **internal-consistency signals** (self-consistent ARNs, preserved source typos) rather than a real source diff, and the entry-rows/inlinks (Phase-3) agents died on the 403 returning `null`, which the success path ignored. The whole wave **looked complete and green** while being unverified-against-source and graph-islanded. It was caught only by the *independent post-hoc on-disk sweep* (Step 6), then remediated after auth was restored. An LLM agent's "pass" is not proof the source was actually read.

Make auth degradation **fail closed** at three points:

1. **Pre-flight probe (cheapest fix, highest ROV).** Before fan-out, dispatch ONE low-effort agent that fetches a single known source page and returns `{auth_ok, evidence}`. If `auth_ok=false`, **abort the wave before fan-out** with a clear "restore auth / re-run" message — turning a wasted multi-agent wave into an instant, obvious stop. (One probe ≪ one wave.)
2. **Per-agent fail-closed status.** Give source-reading agents a `source_fetch_ok: boolean` field and an `auth_blocked` value in their status/verdict enum. Instruct them: *if any source fetch returns a login page / 403 / "Please run /login" / "security token expired" / empty body, set `source_fetch_ok=false` and status/verdict=`auth_blocked`; do NOT fall back to memory/plausibility to claim success.* Treat `auth_blocked` exactly like `fail` in the bounded fix loop.
3. **Honest run rollup.** The orchestration's final `return` MUST compute an explicit `overall_ok` that is false if ANY sub-stage is `auth_blocked`, any `source_fetch_ok=false`, OR any Phase-3 (entry-rows / inlinks) agent did not return `ok=true`. Schema Phase-3 agents too (don't leave them schema-less returning free text that the success path can ignore). Never let a `null`/failed downstream agent be swallowed into a green report — `log()` the incompleteness and emit `needs_remediation`.

Even with all three, **Step 6 (independent post-hoc sweep) is still mandatory** — it is the backstop that actually caught B2. The in-loop guards make the failure loud *during* the run; the post-hoc sweep proves completeness *after* it, on disk, independent of any agent's self-report.

### 5e. The bounded fix loop (Stage 3)

```
while (verdict == "fail" && round < 2):
    for each failing note:
        dispatch a fix agent with: SHARED_CONTRACT + VALIDATOR_PROBLEMS_FOR_THIS_NOTE
        (fix agent re-reads source if any faithfulness issue is listed)
    re-validate the batch
```

**Bound the loop at 2 rounds.** Per-note fix dispatch with the validator's exact problem list converges fast. An unbounded loop is an operational hazard. If round 2 fails, STOP and surface to user — there's a contract or gate bug that needs human judgment.

---

## Step 6: Independent Post-Hoc Verification (Never Skip) <!-- :: section_id = step_6_verify :: -->

> The workflow's "all batches passed" is a claim, not proof. The in-loop validators only check what they were told to. The independent sweep catches what no in-loop validator was watching for (VCL: 3 notes had a real-but-noise source constant sitting in keywords).

### 6a. Full gate suite across ALL notes (not per-batch)

```bash
# Re-run plan's gate script across the full output set
bash <(echo "$GATE_SCRIPT_FROM_PLAN") "$TARGET_DIR"/${PREFIX}*.md
```

### 6b. Skill-based closing gates

> **Shortcut:** G1 format + G6 broken links + G5 ghost references can be run as one pass via **`/slipbox-validate-note-gates`** (it runs format → incremental DB update → `/slipbox-fix-broken-links` → `/slipbox-fix-ghost-references` and returns a single `VALIDATION GATES: PASS/FAIL` verdict). The explicit steps below are the equivalent manual sequence; use either, but every gate must pass.

```bash
# Format check (must pass with 0 errors)
/slipbox-check-note-format --path "$TARGET_DIR"

# Broken-link check (dry run first; must report 0)
/slipbox-check-broken-links

# DB rebuild + ghost query
/slipbox-run-full-database-rebuild
sqlite3 "$DB" "
  SELECT COUNT(*) FROM note_links nl
  LEFT JOIN notes n ON n.note_id = nl.target_note_id
  WHERE nl.source_note_id LIKE '${TARGET_DIR_REL}%'
    AND n.note_id IS NULL;
"  # must be 0 — no ghost references from new notes
# Any ghost found → resolve via /slipbox-fix-ghost-references (redirect / drop / defer→capture), then re-rebuild and re-check

# G8-Discoverability (added 2026-06-13): every new note must have >=1 inbound link from OUTSIDE its folder
sqlite3 "$DB" "
  SELECT n.note_id
  FROM notes n
  WHERE n.note_id LIKE '${TARGET_DIR_REL}%'
    AND NOT EXISTS (
      SELECT 1 FROM note_links l
      WHERE l.target_note_id = n.note_id
        AND l.source_note_id NOT LIKE '${TARGET_DIR_REL}%'
    );
"  # must return NO rows — any row is a graph-island note (G8 FAIL); execute the Inlink Mapping (add reciprocal inlinks) then re-check
```

### 6c. Failure protocol

Any independent-sweep failure → patch in place + re-rebuild. Do NOT consider the run complete with residual broken/ghost/format issues.

---

## Step 7: Commit + Confirm Sync <!-- :: section_id = step_7_commit :: -->

Per Phase 7 of the runbook.

### 7a. Per-logical-unit commits

- Group commits by batch (or by a coherent unit if batches are small): `docs(digest:<topic>): batch N — <count> notes`
- Include the plan amendments commit as a separate commit before the batch commits

### 7b. Push + verify

```bash
git pull --rebase --autostash origin main
git push origin main
git status                                   # must show clean
git log @{u}..HEAD --oneline                 # must show "no commits" (0 ahead)
```

### 7c. Concurrent-sync caveat (load-bearing on long runs)

> On long-running multi-agent jobs, expect concurrent external commits (a sync workspace may commit+push mid-run). Verify completion by inspecting **committed content** (`git show HEAD:<path>`), NOT by counting working-tree modifications. A sync can sweep your changes into its own commit, leaving a misleading `git status`.

---

## Step 8: Report + Update Plan Status <!-- :: section_id = step_8_report :: -->

Append a `## Execution Report` section to the plan and update plan status `ready → completed`.

```markdown
## Execution Report

| Metric | Value |
|---|---|
| Notes created | N / M planned |
| Batches passed (rounds) | 14 in round 1, 4 in round 2, 0 looped |
| Agents (capture + validate + fix) | A1 + A2 + A3 |
| Tokens | ~X.YM |
| Tool uses | ~Z,000 |
| Duration | ~MM min |
| Format check | 0 errors / 0 warnings |
| Broken links (vault-wide) | 0 |
| Ghost references from new notes | 0 |
| Graph-island notes (0 outside-inbound, G8) | 0 |
| Plan amendments applied | K (see § Plan Amendments) |
| Notes returned `split-needed` from sub-agents | J (amended + re-dispatched) |

## Status

Execution complete. Plan moves from `ready` → `completed`.
```

If the run touched ≥30 notes or used ≥3 fix-loop rounds, consider writing a deep-dive note at `experiments/plans/$CORPUS/YYYY-MM-DD_<topic>_execution.md` (the empirical record + transferable lessons), following the FZ 28f2 case-study template.

---

## Anti-Patterns to Avoid <!-- :: section_id = anti_patterns :: -->

| Anti-pattern | Why it fails | Do instead |
|---|---|---|
| Skip pilot, fan out directly | Template/gate bugs hit every sub-agent | Step 3 mandatory — calibrate against pilot first |
| Hand the plan verbatim to each sub-agent | Plan has master-orchestrator context the sub-agent doesn't need; the irrelevant content distracts | Step 4 mandatory — extract the per-batch contract |
| Trust the workflow's self-report | In-loop validators are blind to unstated issues | Step 6 independent sweep, no exceptions |
| Master agent rewrites the plan structure | Drifts away from reviewed/approved scope | Step 2 amendments correct mistakes, do NOT redesign |
| Unbounded fix loop | Operational hazard, can spin | Cap at 2 rounds; round 3 means contract bug |
| Wrap programmatic gates in a sub-agent verifier | Adds cost without information | Run scripts directly; reserve sub-agent for semantic checks |
| Run multiple plans concurrently | Concurrency caps cross between runs; logs interleave | One plan at a time |
| Judge completion by `git status` after a long run | Concurrent sync can hide your changes | Verify via `git show HEAD:<path>` |
| Accept a validator `pass` when source-auth was down | An LLM "passes" on internal-consistency/plausibility, not a real source diff — unverified notes look green (B2) | Fail closed: source-reading agents return `auth_blocked` + `source_fetch_ok=false`; run a pre-flight auth probe; `pass` requires a real source re-read (5f) |
| Let a `null`/failed downstream agent be swallowed into a green report | Phase-3 (entry-rows/inlinks) or a validator that dies on 403 returns `null`; the success path ignores it → graph-islands ship "complete" | Schema every stage; compute an explicit `overall_ok`/`needs_remediation`; `log()` incompleteness; Step 6 sweep is the backstop (5c.6, 5f) |

## Where Notes Go, and What They Must Carry

**Every note this skill creates is written to `$VAULT/<slug>.md` — flat, one
directory, no subtree.** `scripts/build_local_db.py` indexes `$VAULT/**/*.md`
and uses the vault-relative path as the note id, so a flat layout makes the id
equal to the filename and lets links be bare filenames that always resolve.

The source vault's `resources/` / `areas/` / `projects/` tree is deliberately
**not** reproduced. That tree encodes a personal-vault organising scheme; here
it would only make a note's id depend on a routing decision, adding a free
parameter to the retrieval comparison for no benefit.

### Required frontmatter

```yaml
---
tags:                                # FM-010 — 2+, first is a P.A.R.A. type
  - resource                         #   archive | area | entry_point | project | resource
  - <domain tag>
keywords:                            # FM-020 — 3+, and see below
  - <term the note is about>
  - <term a question would use>
  - <acronym or variant spelling>
topics:                              # FM-030
  - <broad subject area>
language: markdown                   # FM-040
date of note: <YYYY-MM-DD>           # FM-040
status: active                       # FM-040
building_block: <one of the eight>   # FM-002 / FM-003 — closed enum
source_docs: [<corpus_doc_id>, ...]  # FM-004 — the corpus evidence, the scoring key
---
```

**`keywords` and `topics` are retrieval surface, not decoration.** Graph
traversal can be seeded by matching a query against
`note_name`, `keywords`, `topics` and `tags` — so a note with none of them is
invisible to that seeding, and a vault with none of them cannot run the strategy
at all. They are also a denser statement of what the note is about than its body:
a short question tends to use the vocabulary a keyword list is written in, while
a body buries that vocabulary among incidental words. Write keywords a
*questioner* would use, not a summary of the note.

`building_block` and `source_docs` are ERRORS if absent. The rest are WARNINGS:
their absence degrades retrieval without making a note unscorable, and gating on
them would block a vault that is merely incomplete rather than wrong.

`navigation` notes — glossaries, entry points, indexes — are **exempt from
`source_docs`**. They index rather than assert, so there is no document to trace
them to; their links are their provenance. Every other building block requires
it.

Both are **enforced**, not conventional. `building_block` is what the retrieval
arms stratify on. `source_docs` is what makes the note scorable at all: gold
labels in these benchmarks are passage-level, so a note that cannot name the
documents it came from cannot be credited when it is retrieved. A note without
it is invisible to the evaluation even when it is correct.

`tags`, `keywords`, `topics`, `status`, `language` and `date of note` may be
included and are preserved, but the database does not read them — do not spend
effort on them at the expense of the two fields above.

### One note, one topic — then one building block, then a size budget

**Thought-atomicity decides where a note ends.** One note carries one thought of
its building block's kind — one fact, definition, mechanism, outcome, claim,
objection, hypothesis or index scope — so that retrieving it returns one whole
thing rather than several partial ones.

**Topical coherence is not the boundary.** Several thoughts about one subject are
exactly what a coherence rule merges, and the merged note then holds many
thoughts while passing every size check. Split on the thought; stop when the
relation between the halves can no longer be stated in one line.

**Density then constrains size, it does not set boundaries.** Past 1,800 source
words a coherent unit splits again — at a sub-topic boundary, never at a word
count. Applying size first merges unrelated subjects that happen to be short,
producing a note that is retrieved for everything and answers nothing.

### Related Notes — derived from evidence, minimum three

Every note carries a `## Related Notes` section with **at least three** outbound
links, each naming **how** the notes relate, not merely that they do.

Two ways to find them, and both beat recall:

```bash
# already-written notes: search on this note's own content
python3 scripts/retrieval.py "$VAULT" --query "<the note's opening claim>"     --strategy hybrid --k 8

# planned term notes: derive from the source blocks this note carries
python3 scripts/build_term_links.py <slug> --plans experiments/plans/<slug> --floor 3
```

The second is what makes a per-note term table possible before the vault exists.
A term links to a note when the term's surface forms appear in **that note's own
source text**, so relevance is corpus evidence rather than recollection. That is
the whole difference between a relevancy-ranked mapping and a padded one.

**The floor is a floor, never a quota.** A spurious edge is not harmless: `bfs`
and `ppr` traverse every edge they are given, so a false link degrades the arm
under test as surely as a missing one. Link density has an **optimum, not a
maximum**. If a floor cannot be met from evidence, the answer is to widen the
term list or accept the note as peripheral — never to invent an edge. On this
corpus a floor of 8 would have fabricated 40% of the graph, which is why the
measured floor is 3.

A note with no inbound link is a graph island: retrievable by name, unreachable
by traversal. Since the graph IS the treatment being measured, an under-linked
vault removes the thing the experiment exists to test.

### Required structure

- **H1 first** — the first content line after the frontmatter (`ST-001`/`ST-002`).
  It becomes the note title in the database and in every retrieval result.
- **Links are bare filenames** — `[Other Note](other_note.md)`, resolved inside
  `$VAULT` only. A link that escapes the vault is reported as `LN-002`
  contamination, because it means the note was written against a different vault.

### Verify before considering the note written

```bash
python3 scripts/validate_notes.py "$VAULT" --gate
python3 scripts/build_local_db.py "$VAULT" --stats
```

The second must report **zero unresolved links**.

## Knowledge Building Blocks (reference)

Every note carries exactly **one** `building_block:`. Closed enum — any other
value is rejected by `scripts/validate_notes.py` (rule `FM-003`):

| Type | Answers | Must retain |
|---|---|---|
| `concept` | *What is X?* | definition, discriminating features, boundary cases |
| `model` | *How does X relate to Y?* | structure, relations, the range over which they hold |
| `procedure` | *How do I do X?* | ordered steps, preconditions, where it does not apply |
| `empirical_observation` | *What happened?* | the event, its source, time anchor, conditions |
| `argument` | *Why believe P?* | claim, grounds, and the warrant joining them |
| `counter_argument` | *Why might that be wrong?* | which premise or inference it attacks |
| `hypothesis` | *Might P be true?* | the proposition and what would falsify it |
| `navigation` | *Where do I find things?* | index or routing only, no substantive claims |

The type is chosen **before** writing, because it is a retention contract: the
"must retain" column names the fields that have to survive. Scope conditions —
preconditions, authority, time anchors, applicability bounds — are the class an
unconditioned summariser reliably deletes, since they qualify claims rather than
being claims. Never mix two building blocks in one note.

Full definitions and the benchmark-corpus caveats: `docs/BUILDING_BLOCKS.md`.

## Planning Accounting (this repo)

A plan asserts three things about every note. Here they are **checked by
script**, because two of them cannot be seen by reading the plan.

```bash
# per-note source ceiling + per-document coverage
python3 scripts/plan_coverage.py <slug> --check <assignments>.json --own-docs doc_a,doc_b

# no source block assigned to two notes, across ALL sub-plans at once
python3 scripts/plan_coverage.py <slug> --crossplan experiments/plans/<slug>/

# per-note term links, derived from each note's own source blocks
python3 scripts/build_term_links.py <slug> --plans experiments/plans/<slug> --floor 3

# audit an existing mapping: every link must be backed by source
python3 scripts/build_term_links.py <slug> --plans experiments/plans/<slug> \
    --verify experiments/plans/<slug>/term_links.json
```

**A link the source does not support is a fabricated edge, and it is not inert.**
`bfs` and `ppr` traverse every edge given, so it moves probability mass onto a
note the evidence never connected — degrading the arm the experiment exists to
measure, and showing up later only as a retrieval number that looks
disappointing for no visible reason. `--verify` blocks it at plan time instead.

**Assignments are block-level.** `--segment` splits a source into paragraph
blocks; the plan records which blocks each note carries, as JSON beside the
plan. That file is what makes the numbers reproducible instead of narrated.

**Coverage is measured over documents the plan OWNS.** A note extended by
another sub-plan brings that sub-plan's documents along; counting them here
would penalise a plan for correctly reusing a note instead of duplicating one.

**Duplicate source assignment is invisible to coverage.** A block counted twice
still looks covered, so summing can never find it — only the cross-plan check
can. It matters because two notes then carry the same claim, retrieval splits
between them, and the dedup rule that lets one note satisfy several pieces of
gold evidence is defeated.

**Dropped source must be listed, not just subtracted.** Publisher chrome —
titles already in the H1, section labels, newsletter promotion, contentless
reaction, bylines — carries no claim and should go. But the same subtraction
hides genuine omission, so enumerate what was dropped and inspect it. On this
corpus that review recovered a block that read as a routine correction notice
and in fact stated the opposite of its article's headline: a scope condition on
the central claim, which is precisely the class an unconditioned summariser
deletes.

## Error Handling <!-- :: section_id = error_handling :: -->

| Error | Cause | Recovery |
|---|---|---|
| Plan status not `ready` | Skipped review | Run `/slipbox-review-digestion-plan`; refuse to start until READY |
| Pilot's gates fail | Template / gate bug | Fix gate or contract; re-run pilot; do NOT proceed to fan-out |
| Sub-agent returns `status=source-mismatch` | Source page changed since plan was written | Master agent re-fetches source; either amend plan + re-dispatch, or escalate |
| Sub-agent returns `status=split-needed` | Density/BB issue not caught at plan time | Master agent splits the note in plan amendments + re-dispatches as two units |
| Validator round 2 still failing | Gate bug or contract bug | STOP. Surface to user with the validator's problem list; do not loop further |
| Independent sweep flags residual issue | In-loop validators missed a class of issue | Patch in place + re-rebuild; update the runbook with the residual class as a future check |
| Concurrent sync committed mid-run | Expected on long runs | Verify via `git show HEAD:<note_path>`; check log for sync commits sweeping the changes |
| Agent returns `status=auth_blocked` / `source_fetch_ok=false` | the authenticated fetch path/auth expired mid-wave; `local file read` returns login pages (5f) | Restore auth (`mwinit` / `/login`), then re-dispatch the affected agents; never accept the wave as complete while any `auth_blocked` remains. The wave's `overall_ok` must be false |
| Wave reports done but Step 6 finds graph-islands / unverified notes | A downstream agent (validator / Phase-3 entry-rows-inlinks) silently failed or died `null` and was swallowed (the B2 incident) | This is exactly why Step 6 is non-negotiable. Re-run the failed phase once auth/cause is fixed; harden the workflow to schema + fail-close the swallowing point (5c.6, 5f) |

## Related Entry Point <!-- :: section_id = related_entry_point :: -->

- Skill Catalog — full vault skill index
- [Runbook: Large-Scale Note Processing with Multi-Agent Pipelines (FZ 28f1)](../policy_sops/runbook_large_scale_note_processing_multiagent.md) — the methodology this skill operationalizes
- Deep Dive: VCL Variable Note Enrichment (FZ 28f2) — empirical reference (130 notes, 18 batches, all gates passed)
- Pipeline siblings: skill_slipbox_plan_digestion → skill_slipbox_augment_digestion_plan → skill_slipbox_review_digestion_plan → **this skill**
