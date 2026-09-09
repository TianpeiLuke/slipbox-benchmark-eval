#!/usr/bin/env bash
# Resume every quota-bound experiment in priority order. Idempotent: every stage
# is cached (note builds, answer files) and every writer aborts on a dead
# backend, so this can be re-run after each daily cap reset until it prints
# ALL_DONE. Order is by what each result licenses:
#   1. build-noise floor   -- decides whether ANY single-build arm difference means anything
#   2. 2Wiki answer arms   -- converts HippoRAG's retrieval margin into an answer-quality one
#   3. v3c length control  -- separates attribution from note length
set -u
cd "$(dirname "$0")/.."
M="${MODEL:-deepseek/deepseek-v4-flash}"
W="${WORKERS:-8}"
probe() { python3 -c "
import sys; sys.path.insert(0,'scripts')
from answer_eval import BACKENDS
o=BACKENDS['cline']('Reply only JSON.','Return {\"ok\":true}','$M')
sys.exit(0 if 'ok' in o.lower() else 1)" 2>/dev/null; }
probe || { echo "backend $M not available (cap or balance); nothing run"; exit 2; }

echo "##### 1. noise floor"
for R in A B; do
  python3 scripts/execute_v3.py --plan experiments/plans/v2/plan.jsonl --out vaults/v3_ds$R --backend cline --model "$M" --workers "$W" 2>&1 | tail -2
  [ "$(find vaults/v3_ds$R -name '*.md' | wc -l | tr -d ' ')" -ge 730 ] || { echo "build $R incomplete; stop here, re-run later"; exit 3; }
done
mkdir -p experiments/runs15/ctx experiments/runs15/ans
for R in A B; do
  [ -s experiments/runs15/ctx/ds$R.jsonl ] || {
    rm -f vaults/v3_ds$R/notes.db
    python3 scripts/build_local_db.py vaults/v3_ds$R --with-embeddings 2>&1 | grep -vi "warn\|hugging\|batches" | tail -1
    python3 scripts/dump_contexts.py multihop_rag --vault vaults/v3_ds$R --strategy hybrid --condition tokens --budget 2048 \
      --questions experiments/runs9/fair_questions.json --sample 450 --nulls 50 --out experiments/runs15/ctx/ds$R.jsonl 2>&1 | grep -vi "warn\|hugging\|batches" | tail -1; }
  python3 scripts/answer_from_contexts.py experiments/runs15/ctx/ds$R.jsonl --backend cline --model "$M" --workers "$W" --out experiments/runs15/ans/ds$R.jsonl 2>&1 | tail -1
done
python3 scripts/score_answers.py --arms dsA=experiments/runs15/ans/dsA.jsonl dsB=experiments/runs15/ans/dsB.jsonl --pairs dsA:dsB --json experiments/runs15/noise_floor.json

echo "##### 2. 2Wiki answer arms"
mkdir -p experiments/runs16/ans
for S in hybrid hipporag; do
  python3 scripts/answer_from_contexts.py experiments/runs16/ctx/2wiki_$S.jsonl --backend cline --model "$M" --workers "$W" --out experiments/runs16/ans/2wiki_$S.jsonl 2>&1 | tail -1
done
python3 scripts/score_answers.py --arms hybrid=experiments/runs16/ans/2wiki_hybrid.jsonl hipporag=experiments/runs16/ans/2wiki_hipporag.jsonl --pairs hybrid:hipporag --json experiments/runs16/2wiki_answers.json

echo "##### 3. v3c length control"
python3 scripts/execute_v3c.py --plan experiments/plans/v2/plan.jsonl --out vaults/v3c_short --backend cline --model "$M" --workers "$W" 2>&1 | tail -2
[ "$(find vaults/v3c_short -name '*.md' | wc -l | tr -d ' ')" -ge 730 ] || { echo "v3c incomplete; re-run later"; exit 3; }
[ -s experiments/runs15/ctx/v3c.jsonl ] || {
  rm -f vaults/v3c_short/notes.db
  python3 scripts/build_local_db.py vaults/v3c_short --with-embeddings 2>&1 | grep -vi "warn\|hugging\|batches" | tail -1
  python3 scripts/dump_contexts.py multihop_rag --vault vaults/v3c_short --strategy hybrid --condition tokens --budget 2048 \
    --questions experiments/runs9/fair_questions.json --sample 450 --nulls 50 --out experiments/runs15/ctx/v3c.jsonl 2>&1 | grep -vi "warn\|hugging\|batches" | tail -1; }
python3 scripts/answer_from_contexts.py experiments/runs15/ctx/v3c.jsonl --backend cline --model "$M" --workers "$W" --out experiments/runs15/ans/v3c.jsonl 2>&1 | tail -1
echo ALL_DONE
