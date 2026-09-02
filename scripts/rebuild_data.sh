#!/usr/bin/env bash
# Reconstruct every local data artefact from scratch. Nothing under data/ is
# committed except the manifest, so this script is the only way the corpus
# comes back -- and the only thing that has to stay correct for it to.
set -euo pipefail
cd "$(dirname "$0")/.."
SLUG="${1:-multihop_rag}"

echo "=== 1. fetch raw benchmark files (skipped if already present) ==="
python3 scripts/fetch_benchmarks.py "$SLUG"

echo
echo "=== 2. prepare the corpus half into plain documents ==="
# Reads ONLY the corpus file. The questions are never written here, which is
# what lets an ingesting agent be given data/corpus/ with a straight face.
python3 scripts/prepare_corpus.py "$SLUG" --stats

echo
echo "=== 3. verify the download against the manifest ==="
python3 - "$SLUG" <<'PY'
import hashlib, json, sys
from pathlib import Path
slug = sys.argv[1]
man = json.loads(Path("data/manifest.json").read_text()).get(slug, {})
ok = True
for fname, meta in man.get("files", {}).items():
    p = Path("data/raw") / slug / fname
    if not p.exists():
        print(f"  MISSING  {fname}"); ok = False; continue
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    good = h.hexdigest() == meta["sha256"]
    print(f"  {'ok  ' if good else 'BAD '}     {fname}  {meta['bytes']:,} bytes")
    ok &= good
print("manifest verified" if ok else "MANIFEST MISMATCH — re-fetch")
sys.exit(0 if ok else 1)
PY

echo
echo "Data rebuilt. Nothing under data/ is committed except the manifest."
