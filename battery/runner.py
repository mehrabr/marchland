"""Battery runner: executes all scenarios and grades against calibration targets.

Usage:
    python -m battery.runner               # all scenarios, 12 seeds each
    python -m battery.runner agincourt     # one scenario
    python -m battery.runner agincourt --seeds 50
    python -m battery.runner --entry cannae_216bc --seeds 24
    python -m battery.runner --entry cannae_216bc --counterfactual kill_mago --seeds 24
    python -m battery.runner --filter officer_   # all officer probes
"""
import argparse, sys, json
from pathlib import Path
import numpy as np

from core.lattice import Battle
from core.siege import run_siege
from core.march import run_march
from core.scenarios import SCN_BATTLE, SCN_MARCH, SCN_SIEGE, SCN_DISSOLUTION
from core.sentiment import run_dissolution
from core.chain import run_chain_1415
from battery.targets import TARGETS
from battery.officer_probes import OFFICER_PROBES

ENTRIES_DIR = Path(__file__).parent / "entries"


def load_entries() -> dict:
    """Load all battery entry JSON files from battery/entries/.

    Returns a flat dict mapping target_key -> [range, grade, source_note, actual, pass].
    """
    entries = {}
    if not ENTRIES_DIR.exists():
        return entries
    for path in sorted(ENTRIES_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        entries.update(data)
    return entries

# Chain runners live here (not in core/scenarios) to avoid circular imports.
SCN_CHAIN = {'chain_1415': run_chain_1415}

# Officer probe runner: each function takes a seed and returns a decision dict.
SCN_OFFICER = OFFICER_PROBES


def run_scenario(name, seeds=12, counterfactual=None):
    """Run a named scenario for `seeds` seeds and return results list."""
    # Officer probes
    if name in SCN_OFFICER:
        return [SCN_OFFICER[name](s) for s in range(seeds)]

    # Battle scenarios (with optional counterfactual variant)
    if name in SCN_BATTLE:
        scn_fn = SCN_BATTLE[name]
        if counterfactual and hasattr(scn_fn, '__module__'):
            # Try to find a counterfactual variant: e.g. cannae_kill_mago
            variant_name = f"{name}_{counterfactual}"
            if variant_name in SCN_BATTLE:
                scn_fn = SCN_BATTLE[variant_name]
        return [Battle(scn_fn(), s).run() for s in range(seeds)]

    if name in SCN_MARCH:
        return [run_march(SCN_MARCH[name](), s) for s in range(seeds)]
    if name in SCN_SIEGE:
        return [run_siege(SCN_SIEGE[name](), s) for s in range(seeds)]
    if name in SCN_CHAIN:
        return [SCN_CHAIN[name](s) for s in range(seeds)]
    if name in SCN_DISSOLUTION:
        return [run_dissolution(SCN_DISSOLUTION[name](), s) for s in range(seeds)]
    raise ValueError(f"Unknown scenario: {name!r}")


def _grade_color(grade, passed):
    if grade == "A":
        return "PASS" if passed else "FAIL"
    if grade == "B":
        return "pass" if passed else "warn"
    return "info"


def grade_all(seeds=12, filter_prefix=None):
    """Run all scenarios and grade against TARGETS.

    filter_prefix: if given (e.g. 'officer_'), only run/grade matching targets.
    """
    cache = {}

    # Determine which scenario names to run
    all_scenarios = (
        list(SCN_BATTLE) + list(SCN_MARCH) + list(SCN_SIEGE)
        + list(SCN_CHAIN) + list(SCN_DISSOLUTION) + list(SCN_OFFICER)
    )
    for name in all_scenarios:
        if filter_prefix and not any(
            k.startswith(filter_prefix) for k in TARGETS
            if _resolve_scenario(k) == name
        ):
            continue
        try:
            cache[name] = run_scenario(name, seeds)
        except Exception as e:
            cache[name] = None

    rows = []
    a_failures = 0
    for key, spec in TARGETS.items():
        if filter_prefix and not key.startswith(filter_prefix):
            continue
        scn_name = _resolve_scenario(key)
        results = cache.get(scn_name)
        if results is None:
            rows.append((key, spec["grade"], "SKIP", "no results", spec["description"]))
            continue
        try:
            passed = spec["check"](results)
        except Exception as e:
            passed = False
            rows.append((key, spec["grade"], "ERROR", str(e)[:60], spec["description"]))
            if spec["grade"] == "A":
                a_failures += 1
            continue
        status = _grade_color(spec["grade"], passed)
        rows.append((key, spec["grade"], status, "", spec["description"]))
        if spec["grade"] == "A" and not passed:
            a_failures += 1

    return rows, a_failures


def grade_entry(entry_name, seeds=12, counterfactual=None):
    """Run and grade one specific battery entry (by scenario name prefix)."""
    results = run_scenario(entry_name, seeds, counterfactual=counterfactual)

    rows = []
    a_failures = 0
    for key, spec in TARGETS.items():
        if not key.startswith(entry_name):
            continue
        try:
            passed = spec["check"](results)
        except Exception as e:
            passed = False
            rows.append((key, spec["grade"], "ERROR", str(e)[:60], spec["description"]))
            if spec["grade"] == "A":
                a_failures += 1
            continue
        status = _grade_color(spec["grade"], passed)
        rows.append((key, spec["grade"], status, "", spec["description"]))
        if spec["grade"] == "A" and not passed:
            a_failures += 1

    return rows, a_failures, results


def _resolve_scenario(key):
    """Map a target key to a scenario name."""
    prefix_map = {
        "isandlwana_line": "isandlwana_line",
        "isandlwana_square": "isandlwana_square",
        "agincourt.": "agincourt",
        "hastings.": "hastings",
        "harfleur_siege": "harfleur",
        "assault.escalade": "escalade_fresh",
        "assault.breach_vs_fresh": "breach_fresh",
        "assault.breach_vs_starved": "breach_starved",
        "chain_1415.": "chain_1415",
        # M7.0 steppe scenarios
        "carrhae.": "carrhae",
        "sphacteria.": "sphacteria",
        # M7.5 dissolution
        "winter_quarters.": "winter_quarters",
        # M7.7 Cannae (base scenario for all cannae targets except kill_mago)
        "cannae_216bc.win": "cannae_216bc",
        "cannae_216bc.meaning_survives": "cannae_216bc",
        "cannae_216bc.kill_concentration": "cannae_216bc",
        # kill_mago counterfactual runs the kill_mago variant
        "cannae_216bc.kill_mago_roman_win": "cannae_kill_mago",
        # M7.7 officer probes
        "officer_open_flank.": "officer_open_flank",
        "officer_suicidal_order.": "officer_suicidal_order",
        "officer_stale_order.": "officer_stale_order",
        "officer_ambiguous_order.": "officer_ambiguous_order",
        "officer_cavalry_judgment.": "officer_cavalry_judgment",
        "officer_dead_repertoire.": "officer_dead_repertoire",
        "officer_honest_report.": "officer_honest_report",
        "officer_initiative_vs_trust.": "officer_initiative_vs_trust",
    }
    for prefix, scn in prefix_map.items():
        if key == prefix or key.startswith(prefix):
            return scn
    return key.split(".")[0]


def print_table(rows):
    w = max(len(r[0]) for r in rows) + 2
    print(f"\n{'TARGET':<{w}} {'GR':<4} {'STATUS':<6}  DESCRIPTION")
    print("-" * (w + 50))
    for key, grade, status, err, desc in rows:
        line = f"{key:<{w}} [{grade}]  {status:<6}"
        if err:
            line += f"  ({err})"
        else:
            line += f"  {desc[:60]}"
        print(line)
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario", nargs="?", help="run one scenario only")
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--entry", help="run and grade one battery entry by name")
    ap.add_argument("--counterfactual", help="select a counterfactual variant (e.g. kill_mago)")
    ap.add_argument("--filter", dest="filter_prefix", help="only run targets starting with prefix")
    args = ap.parse_args()

    if args.entry:
        rows, a_failures, _ = grade_entry(args.entry, args.seeds,
                                           counterfactual=args.counterfactual)
        print_table(rows)
        a_total = sum(1 for _, g, *_ in rows if g == "A")
        a_pass = sum(1 for _, g, s, *_ in rows if g == "A" and s == "PASS")
        print(f"Grade-A: {a_pass}/{a_total} pass")
        if a_failures:
            print(f"\nFAILED: {a_failures} grade-A target(s) did not pass.")
            sys.exit(1)
        print("All grade-A targets GREEN.")
        return

    if args.scenario:
        results = run_scenario(args.scenario, args.seeds)
        print(json.dumps(results[0], indent=2, default=str))
        print(f"\n{args.scenario}: {args.seeds} seeds run.")
        return

    rows, a_failures = grade_all(args.seeds, filter_prefix=args.filter_prefix)
    print_table(rows)

    a_total = sum(1 for _, g, *_ in rows if g == "A")
    a_pass = sum(1 for _, g, s, *_ in rows if g == "A" and s == "PASS")
    b_warn = sum(1 for _, g, s, *_ in rows if g == "B" and s == "warn")

    print(f"Grade-A: {a_pass}/{a_total} pass  |  Grade-B warnings: {b_warn}")
    if a_failures:
        print(f"\nFAILED: {a_failures} grade-A target(s) did not pass.")
        sys.exit(1)
    else:
        print("All grade-A targets GREEN.")


if __name__ == "__main__":
    main()
