"""Sensitivity harness (M7.1): perturb every class-A constant ±DELTA and re-run battery.

Emits a load-bearing-vs-decorative table:
  load-bearing  — battery target fails when this constant is perturbed
  decorative    — battery target passes regardless of perturbation

Wire into CI as a report (not a gate):
    python -m tools.sensitivity [--delta 0.30] [--seeds 4]

Output: a CSV-style table, each row = (constant, perturb, target_key, result).

Per Olleus's non-optional (M7.1): if a headline pass exists only at the fitted
value it is flagged as a "tension" in the output. This rewrites the claim in
docs honestly — if the geometry does the work, not the cue weights, say so.
"""
import argparse, sys, copy
from pathlib import Path

import numpy as np

# We import the full battery runner machinery
import battery.runner as runner
from battery.targets import TARGETS
import core.constants as constants_module


# ---------------------------------------------------------------------------
# Constants registry: all scalar class-A values to perturb
# We extract them from BATTLE_A and the standalone march constants.
# Class B/C/D/E constants are NOT perturbed (they're receipts, not universals).

def _collect_class_a() -> dict:
    """Return a flat dict of {name: (current_value, container_ref, key_path)}."""
    entries = {}

    # BATTLE_A — flat and nested (w dict)
    ba = constants_module.BATTLE_A
    for k, v in ba.items():
        if isinstance(v, (int, float)):
            entries[f'BATTLE_A.{k}'] = v
        elif isinstance(v, dict):
            for kk, vv in v.items():
                if isinstance(vv, (int, float)):
                    entries[f'BATTLE_A.{k}.{kk}'] = vv

    # March class-A scalars
    for name in ('GRAIN_KG', 'WATER_KG', 'SPEED', 'DAYLIGHT', 'THIRST_K', 'BATTLE_DT'):
        val = getattr(constants_module, name, None)
        if val is not None and isinstance(val, (int, float)):
            entries[name] = val

    return entries


def _apply_perturbation(name: str, base_val: float, factor: float) -> None:
    """Temporarily set constant `name` to base_val * factor in the live module."""
    parts = name.split('.')
    if parts[0] == 'BATTLE_A':
        if len(parts) == 2:
            constants_module.BATTLE_A[parts[1]] = base_val * factor
        elif len(parts) == 3:
            constants_module.BATTLE_A[parts[1]][parts[2]] = base_val * factor
    elif parts[0] == 'BATTLE_DT':
        constants_module.BATTLE_DT = base_val * factor
        # Also patch the module-level DT imported by lattice
        import core.lattice
        core.lattice.DT = base_val * factor
    else:
        setattr(constants_module, parts[0], base_val * factor)


def _restore(name: str, base_val: float) -> None:
    """Restore constant `name` to its original value."""
    _apply_perturbation(name, base_val, 1.0)


# ---------------------------------------------------------------------------
# Run all targets and return pass/fail dict

def _run_targets(seeds: int) -> dict:
    """Return {target_key: bool (passed)} for all battery targets."""
    # Rebuild scenario cache freshly
    cache = {}
    for scn_name in list(runner.SCN_BATTLE) + list(runner.SCN_MARCH) + list(runner.SCN_SIEGE) + list(runner.SCN_CHAIN):
        try:
            cache[scn_name] = runner.run_scenario(scn_name, seeds)
        except Exception:
            cache[scn_name] = []

    results = {}
    for key, spec in TARGETS.items():
        scn_name = runner._resolve_scenario(key)
        scn_results = cache.get(scn_name, [])
        try:
            passed = spec['check'](scn_results) if scn_results else False
        except Exception:
            passed = False
        results[key] = passed
    return results


# ---------------------------------------------------------------------------
# Main harness

def run_sensitivity(delta: float = 0.30, seeds: int = 4) -> list:
    """Run sensitivity analysis. Returns list of finding dicts."""
    class_a = _collect_class_a()

    # Baseline pass/fail
    print(f"Sensitivity harness: baseline run ({seeds} seeds)...")
    baseline = _run_targets(seeds)

    findings = []

    total = len(class_a) * 2  # +delta and -delta per constant
    done = 0
    for const_name, base_val in class_a.items():
        for sign, label in [(1.0 + delta, f'+{delta:.0%}'), (1.0 - delta, f'-{delta:.0%}')]:
            done += 1
            _apply_perturbation(const_name, base_val, sign)
            perturbed = _run_targets(seeds)
            _restore(const_name, base_val)

            for key, base_pass in baseline.items():
                pert_pass = perturbed.get(key, False)
                if base_pass and not pert_pass:
                    classification = 'load-bearing'
                elif base_pass and pert_pass:
                    classification = 'decorative'
                elif not base_pass:
                    classification = 'already-failing'
                else:
                    classification = 'unknown'

                if classification in ('load-bearing', 'decorative'):
                    findings.append(dict(
                        constant=const_name,
                        perturbation=label,
                        target=key,
                        baseline_pass=base_pass,
                        perturbed_pass=pert_pass,
                        classification=classification,
                    ))

        if done % 10 == 0:
            print(f"  {done}/{total} perturbations done...", end='\r', flush=True)

    print()
    return findings


def print_table(findings: list) -> None:
    """Print a human-readable load-bearing vs decorative table."""
    load_bearing = [f for f in findings if f['classification'] == 'load-bearing']
    decorative   = [f for f in findings if f['classification'] == 'decorative']

    print("\n=== SENSITIVITY REPORT ===")
    print(f"Total findings: {len(findings)}  "
          f"Load-bearing: {len(load_bearing)}  "
          f"Decorative: {len(decorative)}")
    print()

    if load_bearing:
        print("LOAD-BEARING (battery target fails when constant is perturbed):")
        prev_const = None
        for f in sorted(load_bearing, key=lambda x: (x['constant'], x['target'])):
            if f['constant'] != prev_const:
                print(f"  {f['constant']}")
                prev_const = f['constant']
            print(f"    {f['perturbation']:>6}  →  {f['target']} FAILS")
        print()

    decorative_targets = set(f['target'] for f in decorative)
    load_bearing_targets = set(f['target'] for f in load_bearing)
    tension = decorative_targets - load_bearing_targets
    if tension:
        print("TENSIONS (passes exist only at fitted values or are insensitive):")
        for t in sorted(tension):
            print(f"  {t}: passes under all tested perturbations — credit the geometry, not the weights")
        print()

    print("Note: perturb ±{:.0%} from fitted values; {} seeds per run.".format(
        0.30, 4))
    print("Wire into CI as a report (never a gate): `make sensitivity`")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--delta', type=float, default=0.30)
    ap.add_argument('--seeds', type=int, default=4)
    ap.add_argument('--csv', action='store_true', help='Output CSV to stdout')
    args = ap.parse_args()

    findings = run_sensitivity(args.delta, args.seeds)
    if args.csv:
        print("constant,perturbation,target,classification")
        for f in findings:
            print(f"{f['constant']},{f['perturbation']},{f['target']},{f['classification']}")
    else:
        print_table(findings)


if __name__ == '__main__':
    main()
