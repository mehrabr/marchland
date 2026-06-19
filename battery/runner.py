"""Battery runner: executes all scenarios and grades against calibration targets.

Usage:
    python -m battery.runner               # all scenarios, 12 seeds each
    python -m battery.runner agincourt     # one scenario
    python -m battery.runner agincourt --seeds 50
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


def run_scenario(name, seeds=12):
    if name in SCN_BATTLE:
        return [Battle(SCN_BATTLE[name](), s).run() for s in range(seeds)]
    if name in SCN_MARCH:
        return [run_march(SCN_MARCH[name](), s) for s in range(seeds)]
    if name in SCN_SIEGE:
        return [run_siege(SCN_SIEGE[name](), s) for s in range(seeds)]
    if name in SCN_CHAIN:
        return [SCN_CHAIN[name](s) for s in range(seeds)]
    if name in SCN_DISSOLUTION:
        return [run_dissolution(SCN_DISSOLUTION[name](), s) for s in range(seeds)]
    raise ValueError(f"Unknown scenario: {name}")


def _grade_color(grade, passed):
    if grade == "A":
        return "PASS" if passed else "FAIL"
    if grade == "B":
        return "pass" if passed else "warn"
    return "info"


def grade_all(seeds=12):
    # collect scenario results
    cache = {}
    for name in list(SCN_BATTLE) + list(SCN_MARCH) + list(SCN_SIEGE) + list(SCN_CHAIN) + list(SCN_DISSOLUTION):
        cache[name] = run_scenario(name, seeds)

    rows = []
    a_failures = 0
    for key, spec in TARGETS.items():
        # map target key to scenario name
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


def _resolve_scenario(key):
    # target key prefix -> scenario name
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
    }
    for prefix, scn in prefix_map.items():
        if key.startswith(prefix):
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
    args = ap.parse_args()

    if args.scenario:
        results = run_scenario(args.scenario, args.seeds)
        print(json.dumps(results[0], indent=2, default=str))
        print(f"\n{args.scenario}: {args.seeds} seeds run.")
        return

    rows, a_failures = grade_all(args.seeds)
    print_table(rows)

    a_total = sum(1 for _, g, _, _, _ in rows if g == "A")
    a_pass = sum(1 for _, g, s, _, _ in rows if g == "A" and s == "PASS")
    b_warn = sum(1 for _, g, s, _, _ in rows if g == "B" and s == "warn")

    print(f"Grade-A: {a_pass}/{a_total} pass  |  Grade-B warnings: {b_warn}")
    if a_failures:
        print(f"\nFAILED: {a_failures} grade-A target(s) did not pass.")
        sys.exit(1)
    else:
        print("All grade-A targets GREEN.")


if __name__ == "__main__":
    main()
