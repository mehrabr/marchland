"""MARCHLAND CLI: 1415 vertical slice runner.

Usage:
    python -m clients.cli 1415 [--seeds N] [--out-dir DIR]

Runs the full Harfleur siege → Agincourt march → Agincourt battle chain,
prints an outcome table, saves traces to JSON, and prints a chronicle.
"""
import argparse
import json
import sys
from pathlib import Path

from core.chain import run_chain_1415
from tools.chronicle import generate_chronicle


def _win_label(win: int) -> str:
    if win == 0:
        return "English"
    if win == 1:
        return "French"
    return "draw"


def run_1415(seeds: int = 12, out_dir: Path = None):
    results = []
    print(f"\nRunning 1415 chain ({seeds} seeds)...")
    for seed in range(seeds):
        r = run_chain_1415(seed)
        results.append(r)
        print(f"  seed {seed:2d}: siege={r['siege']['outcome']:12s} "
              f"day={r['siege']['day']:2d}  "
              f"march={'OK' if r['march']['arrived'] else 'FAIL'}  "
              f"battle={_win_label(r['battle']['win'])}")

    _print_outcome_table(results, seeds)

    # save traces
    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        trace_path = out_dir / "chain_1415_traces.json"
        serialisable = []
        for r in results:
            tr = dict(r['trace'])
            # locations are tuples; convert for JSON
            for d in tr.get('deaths', []):
                if d.get('location'):
                    d['location'] = list(d['location'])
            serialisable.append(tr)
        trace_path.write_text(json.dumps(serialisable, indent=2))
        print(f"\nTraces saved to {trace_path}")

    # chronicle from seed-0 trace
    print("\n--- Chronicle (seed 0) ---")
    print(generate_chronicle(results[0]['trace']))
    print()


def _print_outcome_table(results, seeds):
    eng_wins = sum(r['battle']['win'] == 0 for r in results)
    arrived = sum(r['march']['arrived'] for r in results)
    negotiated = sum(r['siege']['outcome'] == 'NEGOTIATED' for r in results)

    print(f"\n{'='*60}")
    print(f"  1415 Campaign Chain — {seeds} seeds")
    print(f"{'='*60}")
    print(f"  Harfleur siege:    NEGOTIATED {negotiated}/{seeds}")
    print(f"  Agincourt march:   arrived    {arrived}/{seeds}")
    print(f"  Agincourt battle:  English    {eng_wins}/{seeds}")
    print(f"{'='*60}")

    # median stats
    import numpy as np
    med_unfit = float(np.median([r['siege']['unfit_frac'] for r in results]))
    med_fat = float(np.median([r['march']['fatigue'] for r in results]))
    med_eng_dead = float(np.median([r['battle']['s'][0]['dead'] for r in results]))
    med_fr_dead = float(np.median([r['battle']['s'][1]['dead'] for r in results]))

    print(f"  Siege unfit frac:  {med_unfit:.2f} (median)")
    print(f"  March fatigue:     {med_fat:.2f} (median)")
    print(f"  English dead:      {med_eng_dead:.0f} (median)")
    print(f"  French dead:       {med_fr_dead:.0f} (median)")
    print()


def main():
    ap = argparse.ArgumentParser(description="MARCHLAND CLI")
    ap.add_argument("command", nargs="?", default="1415",
                    help="'tutorial' to start; '1415' for the chain demo; 'season' for a full season")
    ap.add_argument("--seeds", type=int, default=12,
                    help="Seed count for the 1415 chain demo")
    ap.add_argument("--out-dir", default=None,
                    help="Directory to save trace JSON files (1415 command)")
    ap.add_argument("--culture", default="harfleur_1415",
                    help="Culture module name for the season command")
    ap.add_argument("--seed", type=int, default=0,
                    help="RNG seed for the season or tutorial command")
    args = ap.parse_args()

    if args.command == "1415":
        run_1415(seeds=args.seeds, out_dir=args.out_dir)
    elif args.command == "season":
        from clients.cli.season import run_season
        run_season(culture_name=args.culture, seed=args.seed)
    elif args.command == "tutorial":
        from clients.cli.tutorial import run_tutorial
        run_tutorial(seed=args.seed)
    else:
        print(f"Unknown command '{args.command}'. Use 'tutorial', '1415', or 'season'.",
              file=sys.stderr)
        sys.exit(1)
