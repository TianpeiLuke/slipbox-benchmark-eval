#!/usr/bin/env python3
"""
Check that nothing which shapes the vault has read the benchmark questions.

The quarantine is easy to state and easy to breach in a way that leaves no
trace. An ingesting agent that reads the questions would write notes answering
them by construction. But the subtler breach is an ORCHESTRATOR reading an
aggregate -- "gold evidence spans 2.6 documents on average" -- and using it to
choose how to build the graph. No note is contaminated, and yet the treatment
was tuned on the test set.

    python3 scripts/check_quarantine.py multihop_rag --transcripts <dir>

Only three scripts may read the questions file, and each for a reason that is
not part of building the vault: fetching it, selecting an experimental slice,
and scoring. Anything else naming it is a finding.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED = {"fetch_benchmarks.py", "select_slice.py", "score_retrieval.py",
           "check_quarantine.py"}
QUESTION_FILES = ("MultiHopRAG.json", "questions/", "data/gold/")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--transcripts", help="agent transcript directory to audit")
    ap.add_argument("--runs", help="comma-separated workflow run ids that shape the vault. "
                                   "Other runs in the same directory (research, review) are "
                                   "not vault-shaping and are not audited.")
    a = ap.parse_args()

    bad = []

    for f in sorted((ROOT / "scripts").glob("*.py")):
        if f.name in ALLOWED:
            continue
        text = f.read_text()
        for q in QUESTION_FILES:
            if q in text:
                bad.append(f"SCRIPT    {f.name} names {q} and is not on the allow-list")

    # An agent attesting that it did NOT read the file is compliance, not breach.
    # Flagging the attestation punishes exactly the behaviour the rule wants.
    #
    # Proximity, not sentence splitting: the filename itself contains a period,
    # so any "up to the sentence end" pattern stops inside ".json" and never sees
    # the denial that follows it.
    DENIAL = re.compile(r"never (opened|read|listed|grepped|touched)|was not (opened|read)|"
                        r"quarantine (held|intact)|off limits|do not open|must never|"
                        r"forbidden|not opened", re.I)
    WINDOW = 220

    for f in sorted((ROOT / "experiments" / "plans").rglob("*.json")):
        text = f.read_text()[:400000]
        for q in QUESTION_FILES:
            for m in re.finditer(re.escape(q), text):
                near = text[max(0, m.start() - WINDOW): m.end() + WINDOW]
                if not DENIAL.search(near):
                    bad.append(f"ARTIFACT  {f.relative_to(ROOT)} references {q} "
                               f"with no denial nearby")
                    break

    if a.transcripts:
        d = Path(a.transcripts)
        runs = set(a.runs.split(",")) if a.runs else None
        calls = 0
        audited = [t for t in d.rglob("*.jsonl")
                   if runs is None or any(r in str(t) for r in runs)]
        for t in audited:
            for line in t.read_text(errors="replace").splitlines():
                if not re.search(r'"name"\s*:\s*"(Read|Bash|Grep|Glob)"', line):
                    continue
                if any(q in line for q in QUESTION_FILES) and "off limits" not in line \
                        and "NEVER" not in line:
                    calls += 1
                    bad.append(f"AGENT     a tool call in {t.parent.name} names the questions file")
        print(f"transcripts audited: {len(audited)}"
              + (f" (runs: {a.runs})" if runs else " (all runs)")
              + f", offending tool calls: {calls}")

    print(f"scripts on the allow-list: {', '.join(sorted(ALLOWED))}")
    if bad:
        print(f"\nFAIL — {len(bad)} quarantine finding(s):")
        for b in bad[:25]:
            print("  " + b)
        sys.exit(1)
    print("\nPASS — nothing that shapes the vault reads the benchmark questions")


if __name__ == "__main__":
    main()
