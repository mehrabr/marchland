"""MARCHLAND core: chain protocol — field mappings between simulation phases.

Models compose by field mapping, never by assertion (Bible §III-D).
Each mapping is a pure function: input dict → modified scenario dict.

Chain for 1415:
  Harfleur siege → Agincourt march → Agincourt battle
"""
import copy
import numpy as np

from .siege import run_siege
from .march import run_march
from .lattice import Battle
from .trace import Trace, compose_traces
from .scenarios.harfleur import harfleur
from .scenarios.marches import agincourt_march
from .scenarios.agincourt import agincourt


def siege_to_march(siege_result: dict, siege_scn: dict, base_march_scn: dict) -> dict:
    """Map SiegeResult → MarchStart. Bible §III-D.

    fit = N * (1 - unfit_frac)  →  march start
    fat0 = unfit_frac * 0.4     — siege disease pressure bleeds into march fatigue
    """
    march = copy.deepcopy(base_march_scn)
    fit = int(siege_scn['besieger'] * (1.0 - siege_result['unfit_frac']))
    march['start'] = max(1, fit)
    march['fat0'] = float(np.clip(siege_result['unfit_frac'] * 0.4, 0.0, 0.5))
    return march


def march_to_battle(march_result: dict, base_battle_scn: dict, rest_nights: int = 1) -> dict:
    """Map MarchResult → BattleStart. Bible §III-D.

    fat0   = arrival_fatigue - 0.3 * rest_nights (floor 0)
    belief += +0.10 if cornered (cohesion < 0.4) — "backs to wall" receipt
    belief -= 0.05 if starving (stock_days < 1.0)
    n      scaled by march attrition ratio (effective / start)
    """
    battle = copy.deepcopy(base_battle_scn)
    arrival_fat = march_result['fatigue']
    battle_fat0 = max(0.0, arrival_fat - 0.3 * rest_nights)

    scale = (march_result['effective'] / march_result['start']
             if march_result['start'] > 0 else 1.0)

    belief_mod = 0.0
    if march_result['stock_days'] < 1.0:
        belief_mod -= 0.05
    if march_result['cohesion'] < 0.4:
        belief_mod += 0.10   # cornered receipt: desperation raises resolve

    marching_side = base_battle_scn.get('marching_side', 0)
    for c in battle['cohorts']:
        if c.get('side') == marching_side:
            c['fat0'] = battle_fat0
            c['n'] = max(1, int(round(c['n'] * scale)))
            if 'belief' in c:
                c['belief'] = float(np.clip(c['belief'] + belief_mod, 0.0, 1.0))
    return battle


def run_chain_1415(seed: int) -> dict:
    """Full Harfleur siege → Agincourt march → Agincourt battle chain for one seed.

    Returns a dict with siege, march, and battle sub-results, plus composed trace.
    The battle win field is promoted to the top level for battery grading.
    """
    siege_scn = harfleur()
    march_base = agincourt_march()
    battle_base = agincourt()

    # Phase 1: Harfleur siege
    siege_tr = Trace(phase='siege', scenario='harfleur', seed=seed)
    siege_result = run_siege(siege_scn, seed, trace=siege_tr)

    # Phase 2: March — map from siege result
    march_scn = siege_to_march(siege_result, siege_scn, march_base)
    march_tr = Trace(phase='march', scenario='agincourt_march', seed=seed)
    march_result = run_march(march_scn, seed, trace=march_tr)

    # Phase 3: Battle — map from march result, 1 rest night before Agincourt
    battle_scn = march_to_battle(march_result, battle_base, rest_nights=1)
    battle_tr = Trace(phase='battle', scenario='agincourt', seed=seed)
    battle_result = Battle(battle_scn, seed, trace=battle_tr).run()

    composed = compose_traces([siege_tr, march_tr, battle_tr])

    return dict(
        win=battle_result['win'],
        siege=siege_result,
        march=march_result,
        battle=battle_result,
        trace=composed,
    )
