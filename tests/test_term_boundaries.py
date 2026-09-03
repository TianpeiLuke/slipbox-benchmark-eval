#!/usr/bin/env python3
"""
Boundary cases for the term matcher, pinned because it has been wrong three times.

Each fix here traded one error class for another, and only a table of cases
made that visible:

  v1  plain substring   -- "bot" matched inside "both", "NFL" inside "influenza"
  v2  \b boundaries     -- "fine" matched inside "fine-tuning"
  v3  hyphen is a wall  -- lost "COVID-19" for the form "COVID" (19 real edges
                          removed to delete 8 wrong ones: a net loss)
  v4  hyphens permeable, sense-changing compounds excluded by name, and
      case-sensitivity narrowed to acronyms that lowercase into real words

A false edge is not neutral: bfs and ppr traverse every edge they are given, so
a fabricated link degrades the arm under test.

    python3 tests/test_term_boundaries.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_term_links import compile_forms   # noqa: E402

CASES = [
    # form, text, should_match, why
    ("bot",      "they were both there",                False, "substring inside a word"),
    ("NFL",      "the influenza outbreak",              False, "substring, different case"),
    ("trial",    "a clinical trial began",              True,  "genuine occurrence"),
    ("fine",     "a fine of 6% of annual turnover",     True,  "monetary fine"),
    ("fine",     "model fine-tuning and prompts",       False, "fine-tuning is not a fine"),
    ("fine",     "OpenAI brings fine-tuning to GPT",    False, "fine-tuning is not a fine"),
    ("charging", "fast-charging support",               True,  "still about charging"),
    ("charging", "a hard-charging executive",           False, "sense changes"),
    ("COVID",    "during the COVID-19 pandemic",        True,  "the corpus writes COVID-19"),
    ("COVID",    "covid-related restrictions",          True,  "lowercased, still the term"),
    ("battery",  "its battery-swapping network",        True,  "head noun is the term"),
    ("battery",  "a swappable-battery scooter",         True,  "term on the right of the hyphen"),
    ("WHO",      "the WHO said",                        True,  "organisation"),
    ("WHO",      "who said that",                       False, "pronoun"),
    ("US",       "the US government",                   True,  "country"),
    ("US",       "give us a call",                      False, "pronoun"),
    ("CFTC",     "the cftc fine",                       True,  "unambiguous acronym, any case"),
    ("CSAM",     "csam-scanning tools",                 True,  "unambiguous acronym, hyphen"),
    ("annual turnover", "6% of annual turnover",        True,  "multi-word form"),
]


def main() -> int:
    bad = []
    for form, text, want, why in CASES:
        got = bool(compile_forms([form]).search(text))
        if got != want:
            bad.append((form, text, want, got, why))
    for form, text, want, got, why in bad:
        print(f"  FAIL  {form!r} in {text!r}: expected "
              f"{'a match' if want else 'no match'} ({why})")
    print(f"{len(CASES) - len(bad)}/{len(CASES)} term-boundary cases correct")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
