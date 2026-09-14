"""Centralized reporting — a self-contained HTML dashboard over the metric store.

Reads only `data/metrics.db` (a derived index, rebuildable from the committed
manifests) and writes one standalone file with no network dependencies.

Three design decisions that are about honesty rather than looks:

**Every panel is one comparable cell, and the cell key is in its heading.** A cell
is (benchmark, subset, gold_form). The dashboard offers no way to put two cells on
one axis, because that is the credit error the whole stack is built to prevent —
document-level credit inflated a note arm about ten times more than a chunk arm,
and a slice of 854 questions is not the full 2,255.

**Matched-k and matched-budget are shown as two panels, never one axis.** Same
arms, same colors, opposite verdicts: notes lead by +0.306 All-Recall at k=10 and
trail by −0.155 Recall at a 2048-token budget. Putting those on one scale would be
a dual-axis chart, and would also bury the point. Side by side, the inversion *is*
the visual.

**Unmeasured benchmarks are rendered, not omitted.** Five of six registered
benchmarks have never been run. A dashboard that shows only what was measured
makes the gap invisible.

    python3 -m metrics.store --rebuild
    python3 -m report.dashboard --out report/dashboard.html
"""

from __future__ import annotations

import argparse
import html
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from metrics.store import (  # noqa: E402
    cells,
    connect,
    coverage_gaps,
    leaderboard,
)

# Validated with dataviz/scripts/validate_palette.js --mode light and --mode dark.
# All checks PASS; the contrast WARN is discharged by direct value labels on every
# bar plus the table view, both of which ship below.
SERIES_LIGHT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
                "#008300", "#4a3aa7", "#7f7c73"]
SERIES_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181",
               "#008300", "#9085e9", "#96938a"]

# Colour carries the REPRESENTATION FAMILY, not the individual arm.
#
# The `full` cell holds 45 distinct arms. Cycling eight hues across them would put
# ~6 unrelated arms on each colour, which breaks the fixed-order rule and implies
# relationships that do not exist. Identity is already carried by the direct label
# on every row, so hue is free to encode the thing the comparison is actually
# about: which representation the arm is. Four categories, never cycled.
FAMILIES = [
    ("notes", 0, "typed atomic notes"),
    ("chunks", 1, "chunked raw documents"),
    ("wholedoc", 2, "whole documents"),
    ("other", 7, "variants, unions, sweeps"),
]


def family_of(system: str) -> tuple[str, int]:
    """(family, colour slot). Longest-prefix match, else `other`."""
    t = system.lower()
    if t.startswith("deg"):
        return ("other", 7)
    if t.startswith(("notes", "v1_", "v2_", "v_")):
        return ("notes", 0)
    if "chunks" in t:
        return ("chunks", 1)
    if "wholedoc" in t:
        return ("wholedoc", 2)
    return ("other", 7)


# The two panels whose disagreement is the project's central methodological point.
PANELS = [
    ("Matched token budget (2048) — the fair cut", "recall@b2048",
     "Assemble units in rank order until the budget is spent. This is the only "
     "fair comparison between representations of different unit size."),
    ("Matched k (10) — the misleading cut", "all_recall@k10",
     "Fixed number of units. Hands the win to whichever arm has smaller units, "
     "so it must never be reported as the result."),
]


def _rows(con: sqlite3.Connection, bench: str, subset: str, metric: str) -> list[dict]:
    """Rows for one metric in one cell, tolerant of the two naming eras.

    Backfilled runs store `<strategy>/<metric>`; harness runs store the bare
    name. Resolving that PER CELL matters: a global resolution silently dropped
    45 backfilled runs the first time, because one smoke-test run supplied the
    bare name and every other cell was then looked up under it.
    """
    out: list[dict] = []
    seen: set[str] = set()
    for name in (metric, f"bm25/{metric}"):
        for r in leaderboard(con, bench, name, subset=subset):
            if r["run_id"] in seen:
                continue
            seen.add(r["run_id"])
            prov = con.execute(
                "SELECT provenance FROM runs WHERE run_id=?", (r["run_id"],)
            ).fetchone()
            out.append({
                "system": r["system"],
                "value": r["value"],
                "run_id": r["run_id"],
                "reconstructed": bool(prov and prov["provenance"] == "reconstructed"),
            })
    out.sort(key=lambda r: -r["value"])
    return out


def _bars(rows: list[dict], vmax: float) -> str:
    """Horizontal bars: magnitude by length, identity by hue, value direct-labelled.

    Direct labels on every bar are not decoration here — they discharge the
    palette validator's contrast WARN, which is not dismissable.
    """
    if not rows:
        return '<p class="empty">No runs in this cell.</p>'
    out = []
    for r in rows:
        pct = 0.0 if vmax <= 0 else max(r["value"], 0) / vmax * 100
        fam, slot = family_of(r["system"])
        dagger = ' <span class="dag" title="reconstructed from experiments/ — arm and benchmark inferred; exact config not recoverable">†</span>' if r["reconstructed"] else ""
        out.append(
            f'<div class="row" tabindex="0" '
            f'aria-label="{html.escape(r["system"])}: {r["value"]:.3f}">'
            f'<div class="name"><span class="swatch s{slot}"></span>'
            f'<code>{html.escape(r["system"])}</code>{dagger}</div>'
            f'<div class="track"><div class="bar s{slot}" style="width:{pct:.2f}%"></div>'
            f'<span class="val">{r["value"]:.3f}</span></div>'
            f'<div class="tip">run <code>{r["run_id"]}</code></div>'
            f"</div>"
        )
    return "\n".join(out)


def _table(panels: list[tuple[str, list[dict]]]) -> str:
    """The table view. Required relief for the contrast WARN, and the a11y path."""
    systems: dict[str, dict[str, float]] = {}
    for label, rows in panels:
        for r in rows:
            systems.setdefault(r["system"], {})[label] = r["value"]
    heads = [label for label, _ in panels]
    th = "".join(f"<th>{html.escape(h)}</th>" for h in heads)
    body = []
    for sysname in sorted(systems, key=lambda s: -(systems[s].get(heads[0]) or -1)):
        tds = "".join(
            f"<td>{systems[sysname][h]:.4f}</td>" if h in systems[sysname]
            else "<td class=na>—</td>" for h in heads
        )
        body.append(f"<tr><th scope=row><code>{html.escape(sysname)}</code></th>{tds}</tr>")
    return (f'<table><caption>All values, both cuts</caption><thead><tr>'
            f'<th scope=col>system</th>{th}</tr></thead><tbody>'
            + "".join(body) + "</tbody></table>")


LEGEND = "".join(
    f'<span class="key"><span class="swatch s{slot}"></span>{label}</span>'
    for _, slot, label in FAMILIES
)

CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f4f3f0;
 --text-primary:#0b0b0b;--text-secondary:#52514e;--text-muted:#77746c;
 --line:#e2e0da;
 --s0:#2a78d6;--s1:#eb6834;--s2:#1baf7a;--s3:#eda100;
 --s4:#e87ba4;--s5:#008300;--s6:#4a3aa7;--s7:#7f7c73;}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme=light])) .viz-root{
 color-scheme:dark;--surface-1:#1a1a19;--surface-2:#232322;
 --text-primary:#fff;--text-secondary:#c3c2b7;--text-muted:#96938a;--line:#38372f;
 --s0:#3987e5;--s1:#d95926;--s2:#199e70;--s3:#c98500;
 --s4:#d55181;--s5:#008300;--s6:#9085e9;--s7:#96938a;}}
:root[data-theme=dark] .viz-root{color-scheme:dark;--surface-1:#1a1a19;
 --surface-2:#232322;--text-primary:#fff;--text-secondary:#c3c2b7;
 --text-muted:#96938a;--line:#38372f;
 --s0:#3987e5;--s1:#d95926;--s2:#199e70;--s3:#c98500;
 --s4:#d55181;--s5:#008300;--s6:#9085e9;--s7:#96938a;}
*{box-sizing:border-box}
body{margin:0;background:var(--surface-1);color:var(--text-primary);
 font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:32px 24px 64px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:36px 0 2px}
h3{font-size:13px;margin:20px 0 8px;color:var(--text-secondary);font-weight:600}
.sub{color:var(--text-secondary);margin:0 0 4px}
.note{color:var(--text-muted);font-size:12px;margin:0 0 14px;max-width:62ch}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:10px 0 4px;
 font-size:12px;color:var(--text-secondary)}
.key{display:flex;align-items:center;gap:6px}
.tiles{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0 8px}
.tile{background:var(--surface-2);border:1px solid var(--line);border-radius:8px;
 padding:12px 16px;min-width:132px}
.tile .n{font-size:26px;font-weight:650;letter-spacing:-.02em}
.tile .l{font-size:11px;color:var(--text-secondary);text-transform:uppercase;
 letter-spacing:.06em}
.panels{display:grid;grid-template-columns:1fr 1fr;gap:28px}
@media(max-width:820px){.panels{grid-template-columns:1fr}}
.row{display:grid;grid-template-columns:230px 1fr;gap:10px;align-items:center;
 padding:3px 0;position:relative;outline:none}
.row:hover,.row:focus{background:var(--surface-2);border-radius:4px}
.name{display:flex;align-items:center;gap:6px;font-size:12px;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.swatch{width:9px;height:9px;border-radius:2px;flex:0 0 auto;
 box-shadow:0 0 0 2px var(--surface-1)}
.track{position:relative;height:16px;display:flex;align-items:center}
.bar{height:10px;border-radius:0 4px 4px 0;min-width:1px}
.val{font-size:11px;color:var(--text-secondary);margin-left:6px;
 font-variant-numeric:tabular-nums}
.tip{display:none;position:absolute;right:0;top:-2px;font-size:11px;
 color:var(--text-muted);background:var(--surface-1);padding:0 4px}
.row:hover .tip,.row:focus .tip{display:block}
.s0 .bar,.bar.s0,.swatch.s0{background:var(--s0)}.s1 .bar,.bar.s1,.swatch.s1{background:var(--s1)}
.bar.s2,.swatch.s2{background:var(--s2)}.bar.s3,.swatch.s3{background:var(--s3)}
.bar.s4,.swatch.s4{background:var(--s4)}.bar.s5,.swatch.s5{background:var(--s5)}
.bar.s6,.swatch.s6{background:var(--s6)}.bar.s7,.swatch.s7{background:var(--s7)}
table{border-collapse:collapse;width:100%;font-size:12px;margin-top:8px}
caption{text-align:left;color:var(--text-secondary);font-size:12px;padding:6px 0}
th,td{text-align:right;padding:5px 8px;border-bottom:1px solid var(--line)}
th[scope=row]{text-align:left;font-weight:500}
thead th{color:var(--text-secondary);font-weight:600;font-size:11px}
td.na{color:var(--text-muted)}
code{font:12px/1 ui-monospace,SFMono-Regular,Menlo,monospace}
.dag{color:var(--text-muted);cursor:help}
.gap{background:var(--surface-2);border:1px dashed var(--line);border-radius:8px;
 padding:14px 16px;margin-top:12px}
.gap ul{margin:6px 0 0;padding-left:20px;color:var(--text-secondary)}
.warn{border-left:3px solid var(--s1);padding-left:12px;margin:18px 0}
.empty{color:var(--text-muted);font-size:12px}
details{margin-top:24px}summary{cursor:pointer;color:var(--text-secondary);
 font-size:12px}
"""


def build(con: sqlite3.Connection) -> str:
    all_cells = cells(con)
    gaps = coverage_gaps(con)
    n_runs = con.execute("SELECT COUNT(*) c FROM runs").fetchone()["c"]
    n_metrics = con.execute("SELECT COUNT(*) c FROM metrics").fetchone()["c"]
    n_recon = con.execute(
        "SELECT COUNT(*) c FROM runs WHERE provenance='reconstructed'"
    ).fetchone()["c"]
    measured = len({c["benchmark"] for c in all_cells})

    parts: list[str] = []
    parts.append(f"""<h1>Benchmark results</h1>
<p class="sub">Generated from <code>data/metrics.db</code>, a derived index over the
committed run manifests. Nothing here is hand-maintained.</p>
<div class="tiles">
  <div class="tile"><div class="n">{measured}/{measured + len(gaps)}</div>
    <div class="l">benchmarks measured</div></div>
  <div class="tile"><div class="n">{n_runs}</div><div class="l">runs indexed</div></div>
  <div class="tile"><div class="n">{n_metrics}</div><div class="l">metric values</div></div>
  <div class="tile"><div class="n">{n_recon}</div><div class="l">reconstructed †</div></div>
</div>""")

    if gaps:
        items = "".join(f"<li><code>{html.escape(g['benchmark'])}</code></li>" for g in gaps)
        parts.append(f"""<div class="gap"><strong>Registered but never measured
({len(gaps)})</strong><ul>{items}</ul>
<p class="note" style="margin-top:8px">Shown rather than omitted: a dashboard that
renders only what was measured makes the gap invisible.</p></div>""")

    for cell in all_cells:
        bench, subset, gf = cell["benchmark"], cell["subset"], cell["gold_form"]
        panel_rows: list[tuple[str, list[dict]]] = []
        blocks: list[str] = []

        for label, metric, why in PANELS:
            rows = _rows(con, bench, subset, metric)
            panel_rows.append((label, rows))
            vmax = max([r["value"] for r in rows], default=0) or 1.0
            blocks.append(
                f'<div><h3>{html.escape(label)}</h3>'
                f'<p class="note">{html.escape(why)}</p>'
                f'{_bars(rows, vmax)}</div>'
            )

        if not any(rows for _, rows in panel_rows):
            continue

        parts.append(f"""<h2>{html.escape(bench)} · {html.escape(subset)}</h2>
<p class="note">Gold granularity <code>{html.escape(gf)}</code>,
{cell['runs']} run(s). This heading is the comparable cell: nothing in this
dashboard puts two cells on one axis, because differing gold granularity or
corpus subset makes the numbers incommensurable.</p>
<div class="legend">{LEGEND}</div>
<div class="panels">{"".join(blocks)}</div>
<details><summary>Table view — all values, both cuts</summary>
{_table(panel_rows)}</details>""")

    parts.append("""<div class="warn"><p class="note" style="margin:0">
<strong>Reading these numbers.</strong> A single build cannot license an effect
here: build-to-build variance from the stochastic writer alone was measured at
±0.047 pooled, so a gap smaller than that is not a result. Bars are point
estimates; use <code>report.tables compare</code> for a paired interval.
</p></div>
<p class="note">† reconstructed from <code>experiments/</code> by
<code>runs.backfill</code> — arm and benchmark inferred, exact config not
recoverable.</p>""")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Benchmark results</title><style>{CSS}</style></head>
<body class="viz-root"><div class="wrap">{"".join(parts)}</div></body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description="generate the dashboard")
    ap.add_argument("--out", default=str(ROOT / "report" / "dashboard.html"))
    a = ap.parse_args()
    con = connect()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(con))
    print(f"dashboard -> {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}")


if __name__ == "__main__":
    main()
