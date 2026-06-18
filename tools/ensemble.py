"""tools/ensemble.py: K-seed runner with chronicle language gating.

Runs a scenario across K seeds, computes the outcome distribution, and
returns a language gate so the chronicle caller knows whether "decisive"
language is warranted.

Language gate (based on majority-outcome fraction):
  'decisive'  : >75% same outcome — majority agrees; strong directional claim allowed
  'likely'    : 60–75% same outcome — directional lean, but hedge
  'near-run'  : 45–60% same outcome — contested; avoid "decisively" in prose
  'contested' : <45% for any single outcome — no majority; chronicle must reflect uncertainty

Usage:
    from tools.ensemble import run_ensemble
    result = run_ensemble('agincourt', seeds=50)
    print(result['language'])   # 'decisive'

    # Or from CLI:
    python -m tools.ensemble agincourt --seeds 50
"""
from __future__ import annotations
import argparse, json, sys
from typing import Any


def _language_gate(majority_fraction: float) -> str:
    if majority_fraction > 0.75:
        return "decisive"
    elif majority_fraction >= 0.60:
        return "likely"
    elif majority_fraction >= 0.45:
        return "near-run"
    else:
        return "contested"


def _extract_primary_outcome(result: dict, scn_type: str) -> Any:
    """Return the primary scalar outcome for a single seed result."""
    if scn_type == "battle":
        return result.get("win")
    if scn_type == "march":
        return bool(result.get("arrived", False))
    if scn_type == "siege":
        return result.get("outcome", "UNKNOWN")
    if scn_type == "chain":
        # Chain primary outcome is the battle result.
        battle = result.get("battle", {})
        return battle.get("win") if battle else result.get("win")
    return None


def _majority(outcomes: list) -> tuple[Any, float]:
    """Return (most_common_outcome, fraction)."""
    if not outcomes:
        return None, 0.0
    counts: dict = {}
    for o in outcomes:
        counts[o] = counts.get(o, 0) + 1
    majority_outcome = max(counts, key=counts.__getitem__)
    return majority_outcome, counts[majority_outcome] / len(outcomes)


def run_ensemble(scenario_name: str, seeds: int = 50) -> dict:
    """Run *scenario_name* for *seeds* seeds and return ensemble statistics.

    Returns
    -------
    dict with keys:
      scenario        : str
      seeds           : int
      results         : list of raw per-seed results
      scn_type        : 'battle'|'march'|'siege'|'chain'
      outcome_counts  : {outcome: count}
      majority_outcome: most common outcome value
      majority_fraction: fraction of seeds with majority outcome
      language        : 'decisive'|'likely'|'near-run'|'contested'
      near_run        : bool (True when language is near-run or contested)
    """
    from battery.runner import run_scenario, SCN_CHAIN
    from core.scenarios import SCN_BATTLE, SCN_MARCH, SCN_SIEGE

    if scenario_name in SCN_BATTLE:
        scn_type = "battle"
    elif scenario_name in SCN_MARCH:
        scn_type = "march"
    elif scenario_name in SCN_SIEGE:
        scn_type = "siege"
    elif scenario_name in SCN_CHAIN:
        scn_type = "chain"
    else:
        raise ValueError(f"Unknown scenario: {scenario_name!r}")

    results = run_scenario(scenario_name, seeds)
    outcomes = [_extract_primary_outcome(r, scn_type) for r in results]

    counts: dict = {}
    for o in outcomes:
        counts[o] = counts.get(o, 0) + 1

    majority_outcome, majority_frac = _majority(outcomes)
    language = _language_gate(majority_frac)

    return {
        "scenario": scenario_name,
        "seeds": seeds,
        "results": results,
        "scn_type": scn_type,
        "outcome_counts": counts,
        "majority_outcome": majority_outcome,
        "majority_fraction": majority_frac,
        "language": language,
        "near_run": language in ("near-run", "contested"),
    }


def print_ensemble_summary(ensemble: dict) -> None:
    scn = ensemble["scenario"]
    seeds = ensemble["seeds"]
    language = ensemble["language"]
    maj = ensemble["majority_outcome"]
    frac = ensemble["majority_fraction"]
    counts = ensemble["outcome_counts"]

    print(f"\nEnsemble: {scn}  ({seeds} seeds)")
    print(f"  majority outcome : {maj!r}  ({frac:.0%} of seeds)")
    print(f"  language gate    : {language!r}")
    print(f"  outcome counts   : { {str(k): v for k, v in counts.items()} }")
    if ensemble["near_run"]:
        print("  NOTE: outcome is contested — avoid 'decisive' in chronicle prose")
    else:
        print("  'decisive' language is warranted for this scenario")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description="MARCHLAND ensemble runner")
    ap.add_argument("scenario", help="Scenario name (e.g. agincourt, hastings)")
    ap.add_argument("--seeds", type=int, default=50)
    ap.add_argument("--json", action="store_true", help="Output raw JSON instead of summary")
    args = ap.parse_args()

    ensemble = run_ensemble(args.scenario, seeds=args.seeds)

    if args.json:
        # Omit raw results (large) from JSON output by default.
        out = {k: v for k, v in ensemble.items() if k != "results"}
        print(json.dumps(out, indent=2, default=str))
    else:
        print_ensemble_summary(ensemble)


if __name__ == "__main__":
    main()
