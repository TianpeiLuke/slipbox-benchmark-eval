#!/usr/bin/env python3
"""
GATE 4b (weight) and GATE 5 (self-sufficiency) over a built vault.

The self-sufficiency check distinguishes a DANGLING reference from a
SELF-REFERENTIAL one. "This was announced Tuesday" points outside the note and
is a defect; "This index covers the November trial coverage" points at the note
itself and is exactly how a navigation note should open. An earlier version of
this check flagged all seven navigation notes in the pilot and would have had
them rewritten for being correct.

    python3 scripts/check_v2_gates.py --vault vaults/v2_pilot
"""
from __future__ import annotations
import argparse, re, glob, statistics as st
from collections import Counter
from pathlib import Path

CEIL = {"empirical_observation": 130, "concept": 160, "navigation": 170,
        "model": 190, "hypothesis": 190, "counter_argument": 190,
        "argument": 220, "procedure": 350}

FM = re.compile(r"^---\n(.*?)\n---\n", re.S)
H1 = re.compile(r"^# (.+)$", re.M)
# a bare pronoun or connective opener, pointing outside the note
DANGLING = re.compile(
    r"^\W*(he|she|they|him|her|them|it|its|his|their"
    r"|but|and|so|however|meanwhile|also|then|therefore)\b", re.I)
# self-reference: the demonstrative is immediately anchored to the note itself
SELF_REF = re.compile(
    r"^\W*(this|these|the)\s+"
    r"(note|notes|index|document|collection|review|page|entry|record|guide|scope)\b", re.I)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    a = ap.parse_args()

    over, dang, w, bbs = [], [], [], Counter()
    files = sorted(glob.glob(f"{a.vault}/*.md"))
    for f in files:
        t = Path(f).read_text()
        m = FM.match(t)
        if not m:
            continue
        bbm = re.search(r"building_block:\s*(\S+)", m.group(1))
        bb = bbm.group(1) if bbm else "?"
        bbs[bb] += 1
        prose = H1.sub("", FM.sub("", t)).strip()
        n = len(prose.split()); w.append(n)
        if n > CEIL.get(bb, 200):
            over.append((Path(f).name, bb, n, CEIL.get(bb, 200)))
        if DANGLING.match(prose) and not SELF_REF.match(prose):
            dang.append((Path(f).name, prose[:70]))

    print(f"vault {a.vault} — {len(files)} notes\n")
    print(f"GATE 4b weight: {len(over)} over ceiling ({len(over)/len(files):.1%})")
    for f, bb, n, c in over:
        print(f"  WT-001 {f}: {n} body words, ceiling {c} for {bb}")
    print(f"\nGATE 5 self-sufficiency: {len(dang)} dangling openers")
    for f, p in dang:
        print(f"  SS-001 {f}: {p!r}")
    print(f"\nbody words: median {st.median(w):.0f}  mean {st.mean(w):.0f}  max {max(w)}")
    print("median by block:")
    for b in sorted(bbs):
        bw = [len(H1.sub("", FM.sub("", Path(f).read_text())).strip().split())
              for f in files if re.search(rf"building_block:\s*{b}\b", Path(f).read_text())]
        if bw:
            print(f"  {b:<24}{st.median(bw):>5.0f}w   n={len(bw):<4} ceiling {CEIL.get(b,200)}")


if __name__ == "__main__":
    main()
