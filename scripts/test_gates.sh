#!/usr/bin/env bash
# Gate regression test: format, broken links, ghost references.
#
# These gates are easy to break INVISIBLY. The skills that drive them are
# largely SQL against tables that a schema change can remove, and a query
# against a missing table fails per-invocation rather than failing the build --
# so a dead gate reports nothing and reads exactly like a clean vault.
# This test builds a deliberately broken vault and asserts each gate fires.
set -uo pipefail
cd "$(dirname "$0")/.."
V=$(mktemp -d)/vault; mkdir -p "$V"; fails=0

ck() { # ck <description> <expected-substring> <actual>
  if grep -qF "$2" <<<"$3"; then printf '  ok    %s\n' "$1"
  else printf '  FAIL  %s (expected %s)\n' "$1" "$2"; fails=$((fails+1)); fi
}

cat > "$V/good.md" <<'EOF'
---
building_block: concept
source_docs: [d1]
---

# Good Note

- [Target](target_note.md)
- [Moved](sub/target_note.md)
- [Ghost](no_such_thing_anywhere.md)
EOF
cat > "$V/target_note.md" <<'EOF'
---
building_block: model
source_docs: [d1]
---

# Target Note
EOF
printf -- '---\nbuilding_block: nonsense\n---\n\nprose first\n\n# Late H1\n' > "$V/bad_fm.md"
printf -- 'no frontmatter at all\n' > "$V/no_fm.md"
# frontmatter present but no building_block -- distinct from both cases above
printf -- '---\nsource_docs: [d1]\n---\n\n# No Block\n' > "$V/no_bb.md"
printf -- '---\nbuilding_block: concept\nsource_docs: [d1]\n---\n\n# Escapes\n\n[Out](../../etc/passwd.md)\n' > "$V/escapes.md"

echo "=== format + link + ghost gate (validate_notes.py) ==="
out=$(python3 scripts/validate_notes.py "$V" 2>&1)
ck "FM-001 missing frontmatter"       "FM-001" "$out"
ck "FM-002 missing building_block"    "FM-002" "$out"
ck "FM-003 building_block off-enum"   "FM-003" "$out"
ck "FM-004 missing source_docs"       "FM-004" "$out"
ck "ST-001 missing H1"                "ST-001" "$out"
ck "ST-002 content before H1"         "ST-002" "$out"
ck "LN-002 link escapes the vault"    "LN-002" "$out"
ck "GH-001 ghost target"              "GH-001" "$out"
python3 scripts/validate_notes.py "$V" --gate >/dev/null 2>&1
[ $? -ne 0 ] && echo "  ok    --gate exits non-zero on errors" \
             || { echo "  FAIL  --gate should exit non-zero"; fails=$((fails+1)); }

echo
echo "=== link-repair diagnostics (tables the gate skills query) ==="
python3 scripts/build_local_db.py "$V" >/dev/null 2>&1
DB="$V/notes.db"
for t in broken_links ghost_notes ghost_note_references; do
  if sqlite3 "$DB" "SELECT COUNT(*) FROM $t;" >/dev/null 2>&1
  then echo "  ok    table $t exists"
  else echo "  FAIL  table $t missing — the gate skills' SQL is dead"; fails=$((fails+1)); fi
done
ck "broken link has a repair candidate" "target_note.md" \
   "$(sqlite3 "$DB" "SELECT correct_note_id FROM broken_links;")"
ck "ghost recorded with no candidate"   "no_such_thing_anywhere.md" \
   "$(sqlite3 "$DB" "SELECT ghost_note_id FROM ghost_notes;")"
ck "ghost reference is attributed"      "good.md" \
   "$(sqlite3 "$DB" "SELECT source_note_id FROM ghost_note_references;")"

echo
echo "=== --fix repairs the repairable link ==="
python3 scripts/validate_notes.py "$V" --fix >/dev/null 2>&1
ck "moved link rewritten to the real path" "[Moved](target_note.md)" "$(cat "$V/good.md")"
ck "ghost left alone (needs a decision)"   "no_such_thing_anywhere.md" "$(cat "$V/good.md")"

echo
echo "=== term matcher boundaries ==="
if out=$(python3 tests/test_term_boundaries.py 2>&1); then
  echo "  ok    $(tail -1 <<<"$out")"
else
  echo "  FAIL  term matcher regressed"; echo "$out" | sed 's/^/        /'; fails=$((fails+1))
fi

echo
echo "=== fabricated-edge guard (term links must be backed by source) ==="
if [ -f experiments/plans/multihop_rag/term_links.json ]; then
  out=$(python3 scripts/build_term_links.py multihop_rag \
          --plans experiments/plans/multihop_rag \
          --verify experiments/plans/multihop_rag/term_links.json 2>&1)
  if grep -q "every link is backed" <<<"$out"
  then echo "  ok    $(grep 'backed by source' <<<"$out" | tr -s ' ')"
  else echo "  FAIL  unbacked term links present"; echo "$out" | sed 's/^/        /'; fails=$((fails+1)); fi
else
  echo "  skip  no term_links.json yet"
fi

echo
rm -rf "$(dirname "$V")"
if [ "$fails" -eq 0 ]; then echo "GATES PASS — format, broken links and ghosts all fire"; exit 0
else echo "GATES FAIL — $fails check(s) failed"; exit 1; fi
