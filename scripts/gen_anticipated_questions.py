#!/usr/bin/env python3
"""
Generate the questions each unit answers, for index-time expansion.

This is document expansion by query prediction, and it is the machine form of
the elaborative half of note-taking: the writer anticipates what will be asked
and stores it with the artifact, where a retriever can reach it. Keywords
derived from a unit's own body cannot close a gap that exists between that body
and a question; generated questions can, because they are written in the
questioner's vocabulary rather than the author's.

CONTAMINATION GUARD. The generator sees the unit text and nothing else. The
benchmark question file is never opened here, and must never be shown to it --
questions that mirror the test set would produce a spectacular and meaningless
result.

    python3 scripts/gen_anticipated_questions.py --vault vaults/multihop_rag \
        --out expansions/notes.jsonl --batch 12 --limit 60
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from answer_eval import BACKENDS   # noqa: E402

NON = re.compile(r"^## (Related Notes|Source|References)\s*$.*?(?=^## |\Z)", re.M | re.S)

SYSTEM = (
    "You write the search queries a document would answer.\n"
    "- Output the questions a real person would type to find this text, not a "
    "summary of it.\n"
    "- Prefer the vocabulary a searcher uses over the vocabulary the text uses: "
    "the acronym when the text spells the name out, the common name when the "
    "text uses the formal one, the popular phrase for the event.\n"
    "- Never restate the title.\n"
    "- Output STRICT JSON only: {\"<id>\": [\"q1\", \"q2\", ...], ...}. No prose."
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--backend", default="cline")
    ap.add_argument("--model", default="qwen/qwen3.8-flash")
    ap.add_argument("--batch", type=int, default=12)
    ap.add_argument("--per-unit", type=int, default=4)
    ap.add_argument("--chars", type=int, default=700)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0, help="pilot on the first N units")
    a = ap.parse_args()

    con = sqlite3.connect(Path(a.vault) / "notes.db")
    rows = con.execute("SELECT note_id, title, body FROM notes ORDER BY note_id").fetchall()
    con.close()
    if a.limit:
        rows = rows[: a.limit]

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            try:
                done.add(json.loads(line)["id"])
            except Exception:
                continue
    todo = [r for r in rows if r[0] not in done]
    print(f"{len(rows):,} units, {len(done):,} already expanded, {len(todo):,} to do")

    batches = [todo[i:i + a.batch] for i in range(0, len(todo), a.batch)]
    ask = BACKENDS[a.backend]
    lock = threading.Lock()

    def run(batch):
        parts = []
        for nid, title, body in batch:
            txt = NON.sub("", body).strip().replace("\n", " ")[: a.chars]
            parts.append(f"### {nid}\nTITLE: {title}\n{txt}")
        user = (f"Write {a.per_unit} search questions for EACH document below. "
                f"Return JSON keyed by the id shown after ###.\n\n" + "\n\n".join(parts))
        try:
            raw = ask(SYSTEM, user, a.model)
        except Exception as e:
            return 0, str(e)[:120]
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            return 0, "no json"
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            return 0, "bad json"
        n = 0
        with lock, out.open("a") as fh:
            for nid, _, _ in batch:
                qs = obj.get(nid)
                if isinstance(qs, list) and qs:
                    fh.write(json.dumps({"id": nid, "questions": [str(q) for q in qs]}) + "\n")
                    n += 1
        return n, None

    ok = 0; errs = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for n, err in ex.map(run, batches):
            ok += n
            if err:
                errs.append(err)
    print(f"expanded {ok:,} units" + (f"; {len(errs)} batch error(s), e.g. {errs[0]}" if errs else ""))


if __name__ == "__main__":
    main()
