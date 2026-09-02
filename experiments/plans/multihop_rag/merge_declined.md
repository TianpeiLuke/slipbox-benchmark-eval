# Near-matches deliberately NOT merged

`merge_cluster_plans.py` flagged 20 near-identical filenames across clusters.
Fifteen were merged; five were declined, because the names differ by a **model
identifier**, not a suffix.

| Left | Right | Why kept separate |
|---|---|---|
| `bose_quietcomfort_45_headphones_deal` | `bose_quietcomfort_ultra_headphones_deal` | QC45 and QC Ultra are different products |
| `samsung_smart_monitor_m8` | `samsung_smart_monitor_m80c_deal` | M8 and M80C are different models |
| `dyson_v15_detect_absolute_vacuum_deal` | `dyson_v15_detect_vacuum_deal` | "Absolute" is a distinct variant |
| `how_to_open_a_sportsbook_account_and_place_a_bet` | `how_to_open_a_sportsbook_account_and_place_bowl_bets` | Two procedures with different preconditions; a procedure note's value is its preconditions |
| `google_pixel_buds_pro_deal` | `google_pixel_buds_pro_holiday_deal` | Merged into `google_pixel_buds_pro` instead, so the pair is resolved rather than declined |

The asymmetry is deliberate. A missed merge splits evidence across two notes and
costs recall on questions needing both. A wrong merge **destroys** evidence:
two genuinely different products collapse into one note that is right about
neither, and no downstream check can recover the distinction. Where the names
disagree about which thing they name, keeping them separate is the recoverable
error.
