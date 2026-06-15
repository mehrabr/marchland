"""Battery target registry.

Each entry: (target_description, grade, source_note, actual_from_ref, passing)

Grades:
  A — hard assertion in pytest; must pass for CI green
  B — warning if missed; documented finding
  C — informational; printed in summary

Known misses carried forward from the reference implementation:
  - isandlwana defender_dead_frac: 40% vs target 50-90% (grade B miss)
  - hastings casualty_shape_prebreak: 20% vs target <=10% (grade B miss — fixed in M1)
  - hastings near_run_contested: 0% vs 20-50% (grade C miss — fixed in M1)
  - harfleur storm_launched: 13% vs "rare" — tension, not a failure
"""

TARGETS = {
    # ---- Isandlwana Line ----
    "isandlwana_line.win": {
        "description": "Zulu win all seeds",
        "grade": "A",
        "check": lambda results: all(r["win"] == 1 for r in results),
        "note": "British thin line collapses under converging attack",
    },
    "isandlwana_line.sequence_ammo_before_break": {
        "description": "Ammo starvation event precedes break in majority of seeds",
        "grade": "A",
        "check": lambda results: sum(
            any(e[0].startswith("ammo_starved") for e in r["ev"]) for r in results
        ) > len(results) / 2,
        "note": "Supply point at camp; distant flank runs dry first",
    },
    "isandlwana_line.defender_dead_frac": {
        "description": "British dead fraction in [0.50, 0.90]",
        "grade": "B",
        "check": lambda results: 0.50 <= _median_dead_frac(results, 0) <= 0.90,
        "note": "KNOWN MISS: reference achieves ~0.40; pursuit model underdrives (fix post-M6)",
    },
    "isandlwana_line.zulu_loss_frac": {
        "description": "Zulu dead fraction in [0.05, 0.20]",
        "grade": "C",
        "check": lambda results: 0.05 <= _median_dead_frac(results, 1) <= 0.20,
        "note": "Light Zulu losses consistent with pursuit-phase kill dynamics",
    },

    # ---- Agincourt ----
    "agincourt.win": {
        "description": "English win all seeds (side 0 wins -> win==0)",
        "grade": "A",
        "check": lambda results: all(r["win"] == 0 for r in results),
        "note": "Stakes + mud + arrow storm; no plausible French path to victory",
    },
    "agincourt.asymmetry_min": {
        "description": "Dead-ratio French/English >= 5:1",
        "grade": "B",
        "check": lambda results: _median_asymmetry(results) >= 5,
        "note": "Historical ~25:1 dead; model achieves ~11 at median",
    },
    "agincourt.french_losses_incl_prisoners": {
        "description": "French losses (dead+cap) in [4000, 11000]",
        "grade": "C",
        "check": lambda results: 4000 <= _median_french_losses(results) <= 11000,
        "note": "Including ransomed prisoners",
    },
    "agincourt.english_dead": {
        "description": "English dead in [112, 600]",
        "grade": "C",
        "check": lambda results: 112 <= _median_side_dead(results, 0) <= 600,
        "note": "Historical ~112 known dead; model at ~450",
    },

    # ---- Hastings ----
    "hastings.win": {
        "description": "Norman win all seeds (side 1 wins -> win==1)",
        "grade": "A",
        "check": lambda results: all(r["win"] == 1 for r in results),
        "note": "Fyrd fatigue + feint + cavalry; English cannot hold indefinitely",
    },
    "hastings.harold_falls": {
        "description": "Leader0 (Harold) falls in majority of seeds",
        "grade": "A",
        "check": lambda results: sum(
            any(e[0] == "leader0_down" for e in r["ev"]) for r in results
        ) > len(results) / 2,
        "note": "Leader lottery fires when huscarl density drops",
    },
    "hastings.casualty_shape_prebreak": {
        "description": "Pre-break dead fraction <= 0.10",
        "grade": "B",
        "check": lambda results: _median_prebreak_frac(results) <= 0.10,
        "note": "KNOWN MISS: reference at ~0.20; phase pacing fix in M1",
    },
    "hastings.near_run_contested": {
        "description": "Norman win in 20-50% of seeds (contested)",
        "grade": "C",
        "check": lambda results: 0.20 <= sum(r["win"] == 1 for r in results) / len(results) <= 0.50,
        "note": "KNOWN MISS: currently Norman wins all seeds; M1 phase pacing will introduce variance",
    },

    # ---- Harfleur siege ----
    "harfleur_siege.negotiated_absent_relief": {
        "description": "NEGOTIATED outcome in majority of seeds",
        "grade": "A",
        "check": lambda results: sum(r["outcome"] == "NEGOTIATED" for r in results) > len(results) / 2,
        "note": "Historical outcome: terms on day 22 Sept 1415",
    },
    "harfleur_siege.duration_days": {
        "description": "NEGOTIATED day median in [30, 40]",
        "grade": "A",
        "check": lambda results: _in_range(
            _median_negotiated_day(results), 30, 40
        ),
        "note": "Historical: 36 days from investment to surrender",
    },
    "harfleur_siege.besieger_unfit_frac": {
        "description": "Besieger unfit fraction median in [0.15, 0.35]",
        "grade": "C",
        "check": lambda results: 0.15 <= _median_val(results, "unfit_frac") <= 0.35,
        "note": "Disease toll from marshy camp; historical ~dysentery epidemic",
    },

    # ---- Assault battery ----
    "assault.escalade_vs_fresh_repulsed": {
        "description": "Escalade vs fresh garrison: majority repulsed (garrison wins)",
        "grade": "B",
        "check": lambda results: sum(r["win"] == 0 for r in results) > len(results) / 2,
        "note": "Fresh garrison with cover holds wall against unsupported escalade",
    },
    "assault.breach_vs_fresh_contested": {
        "description": "Breach vs fresh: mixed outcomes (not all one side)",
        "grade": "B",
        "check": lambda results: 0 < sum(r["win"] == 1 for r in results) < len(results),
        "note": "Fresh garrison can hold a breach; contested is historically correct",
    },
    "assault.breach_vs_starved_carried": {
        "description": "Breach vs starved: majority carried (attackers win)",
        "grade": "B",
        "check": lambda results: sum(r["win"] == 1 for r in results) > len(results) / 2,
        "note": "KNOWN MISS: reference achieves 5/12; starved garrison not weak enough",
    },
}


# ---- helpers ----

import numpy as np


def _median_dead_frac(results, side):
    fracs = [r["s"][side]["dead"] / r["s"][side]["total"] for r in results if r["s"][side]["total"] > 0]
    return float(np.median(fracs)) if fracs else 0.0


def _median_asymmetry(results):
    ratios = []
    for r in results:
        e = r["s"][0]["dead"]; f = r["s"][1]["dead"]
        if e > 0: ratios.append(f / e)
    return float(np.median(ratios)) if ratios else 0.0


def _median_french_losses(results):
    vals = [r["s"][1]["dead"] + r["s"][1]["cap"] for r in results]
    return float(np.median(vals))


def _median_side_dead(results, side):
    return float(np.median([r["s"][side]["dead"] for r in results]))


def _median_prebreak_frac(results):
    fracs = []
    for r in results:
        total = sum(r["s"][s]["pre"] + r["s"][s]["post"] for s in (0, 1))
        pre = sum(r["s"][s]["pre"] for s in (0, 1))
        if total > 0: fracs.append(pre / total)
    return float(np.median(fracs)) if fracs else 0.0


def _median_negotiated_day(results):
    days = [r["day"] for r in results if r["outcome"] == "NEGOTIATED"]
    return float(np.median(days)) if days else 0.0


def _median_val(results, key):
    vals = [r[key] for r in results if key in r]
    return float(np.median(vals)) if vals else 0.0


def _in_range(val, lo, hi):
    return lo <= val <= hi
