#!/usr/bin/env bash
# End-to-end check on a tiny committed fixture -- no downloads, no API keys.
# Verifies: DB build, link resolution, escape detection, hybrid index, and all
# five retrieval strategies.
set -euo pipefail
cd "$(dirname "$0")/.."
V=tests/fixture_vault

echo "=== 1. build local DB (links must resolve in-vault) ==="
python3 scripts/build_local_db.py "$V" --stats

echo
echo "=== 2. build dense half of the hybrid index ==="
python3 scripts/build_embeddings.py "$V" 2>&1 | grep -v Batches

echo
echo "=== 3. multi-hop query: answer lives in gamma.md, which shares no terms"
echo "       with the query; beta.md is the bridge node ==="
python3 scripts/retrieval.py "$V" --query "where is Alpha Protocol deployed" \
    --strategy all --k 3 2>&1 | grep -v Batches

echo
echo "=== 4. publication gate ==="
python3 scripts/scrub_check.py "$V"
