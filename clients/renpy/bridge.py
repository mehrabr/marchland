"""MARCHLAND Ren'Py bridge — Layer 2 adapter.

The three-layer contract (integration spec §1–3):
  Layer 1  core/        sim, RNG, battery — imports nothing from Ren'Py
  Layer 2  THIS FILE    plain serializable dicts; the only thing that crosses
  Layer 3  game/*.rpy   Ren'Py scenes, screens, menus — imports nothing numpy

Save discipline (spec §5):
  Persist: seed (int), player choices (strs), belief_db.to_dict(), trace dicts.
  NEVER persist: numpy arrays, Battle objects, or RNG state.
  To resume a battle — re-run from (scenario, seed). Determinism reconstructs it.

All public functions return plain Python objects (dicts, lists, ints, strs, floats,
bools). No numpy types. No sim objects. Ren'Py can pickle any of these safely.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Layer 1 imports — sim only; nothing from Ren'Py
from core.chain import run_chain_1415
from core.trace import compose_traces, Trace
from core.siege import run_siege
from core.march import run_march
from core.lattice import Battle
from core.belief_db import BeliefDB, trace_to_summary
from core.stations import Station, STATIONS
from core.scenarios.harfleur import harfleur
from core.scenarios.marches import agincourt_march
from core.scenarios.agincourt import agincourt
from core.chain import siege_to_march, march_to_battle


# ---------------------------------------------------------------------------
# Serialization helpers

def _strip_numpy(obj: Any) -> Any:
    """Recursively convert any numpy scalars in a dict/list to plain Python types.

    Defensive pass — compose_traces already returns plain Python, but this
    catches any scalar that slips through (e.g. from scenario field reads).
    """
    import numpy as np
    if isinstance(obj, dict):
        return {k: _strip_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_numpy(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_strip_numpy(v) for v in obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)
    return obj


def assert_serializable(obj: Any, label: str = '') -> None:
    """Raise ValueError if obj is not JSON-serializable — use in dev/test.

    The golden-hash test already verifies this for the trace; this is the
    bridge-layer analogue for save capsules.
    """
    try:
        json.dumps(obj)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Bridge layer produced non-serializable object{' (' + label + ')' if label else ''}: {exc}") from exc


# ---------------------------------------------------------------------------
# One-shot sim calls (numpy stays inside, never escapes)

def run_chain(seed: int) -> Dict[str, Any]:
    """Run the full 1415 chain for one seed and return a serializable result.

    Returns the same shape as core.chain.run_chain_1415 — sub-results for siege,
    march, battle, and the composed trace — with all numpy types stripped.
    """
    result = run_chain_1415(seed)
    return _strip_numpy(result)


def run_operation(op: str, seed: int,
                  siege_result: Optional[Dict] = None,
                  march_result: Optional[Dict] = None,
                  tactic: str = 'wait',
                  pace: str = 'normal',
                  battle_choice: str = 'engage',
                  rest_nights: int = 1) -> Dict[str, Any]:
    """Run one campaign operation and return a serializable {result, trace} dict.

    op: 'siege' | 'march' | 'battle'

    Callers (Ren'Py menus) pass in tactic/pace/battle_choice; this function
    runs the sim, strips numpy, and returns plain dicts. The sim objects die
    when this call returns — only the result dict crosses the boundary.
    """
    tr = Trace(phase=op, scenario=f"harfleur_1415_{op}", seed=seed)

    if op == 'siege':
        scn = harfleur()
        if tactic == 'storm':
            scn = dict(scn, storm_threshold=0.15)
        result = run_siege(scn, seed, trace=tr)

    elif op == 'march':
        base = agincourt_march()
        if siege_result is not None:
            scn = siege_to_march(siege_result, harfleur(), base)
        else:
            scn = base
        if pace == 'push':
            scn = dict(scn, pace=scn.get('pace', 15.5) * 1.20,
                       fat0=min(1.0, scn.get('fat0', 0.20) + 0.05))
        elif pace == 'rest':
            scn = dict(scn,
                       rest_every=max(1, scn.get('rest_every', 0) or 4),
                       fat0=max(0.0, scn.get('fat0', 0.20) - 0.05))
        result = run_march(scn, seed, trace=tr)

    elif op == 'battle':
        if battle_choice == 'withdraw':
            return _strip_numpy({
                'op': 'battle',
                'withdrew': True,
                'result': {'win': -1, 'withdrew': True, 's': [{}, {}]},
                'trace': Trace(phase='battle', scenario='agincourt', seed=seed).to_dict(),
            })
        if march_result is not None:
            scn = march_to_battle(march_result, agincourt(), rest_nights=rest_nights)
        else:
            scn = agincourt()
        scn['marching_side'] = 0
        result = Battle(scn, seed, trace=tr).run()

    else:
        raise ValueError(f"Unknown operation: {op!r}. Expected 'siege', 'march', or 'battle'.")

    return _strip_numpy({
        'op': op,
        'result': result,
        'trace': tr.to_dict(),
    })


# ---------------------------------------------------------------------------
# Save capsule — everything Ren'Py needs to persist a season

@dataclass
class SaveCapsule:
    """Serializable snapshot of season state for Ren'Py save/load.

    Ren'Py pickles this as a RevertableObject.  Every field is a plain Python
    type — no numpy, no sim objects.  Battles reconstruct from seed (spec §5).
    """
    seed: int
    culture_name: str

    # Player choices
    quarter_policy: str = 'liberal'
    siege_tactic: Optional[str] = None
    march_pace: Optional[str] = None
    battle_choice: Optional[str] = None

    # Operation results (plain dicts)
    siege_result: Optional[Dict] = None
    march_result: Optional[Dict] = None
    battle_result: Optional[Dict] = None

    # Belief DB snapshot (from BeliefDB.to_dict())
    belief_db_dict: Dict = field(default_factory=dict)

    # Composed trace (from compose_traces, already plain Python)
    trace_dicts: List[Dict] = field(default_factory=list)

    # Season clock
    day: int = 0
    patron_favor: float = 0.5

    # Station
    station: str = 'CAMP'
    station_lottery_injuries: int = 0

    # Pending orders: list of {command, eta_day, label}
    pending_orders: List[Dict] = field(default_factory=list)


def save_capsule_from_state(state: Any) -> SaveCapsule:
    """Extract a SaveCapsule from a SeasonState (clients.cli.season.SeasonState).

    Used by Ren'Py to snapshot state before any save point.
    """
    traces_raw = [tr.to_dict() for tr in getattr(state, 'trace_phases', [])]

    pending = [
        {'command': po.command, 'eta_day': po.eta_day, 'label': po.label}
        for po in getattr(state, 'pending_orders', [])
    ]

    capsule = SaveCapsule(
        seed=state.seed,
        culture_name=getattr(state.commission, 'culture', {}).get('name', 'harfleur_1415'),
        quarter_policy=getattr(state, 'quarter_policy', 'liberal'),
        siege_tactic=getattr(state, 'siege_tactic', None),
        march_pace=getattr(state, 'march_pace', None),
        battle_choice=getattr(state, 'battle_choice', None),
        siege_result=_strip_numpy(state.siege_result) if state.siege_result else None,
        march_result=_strip_numpy(state.march_result) if state.march_result else None,
        battle_result=_strip_numpy(state.battle_result) if state.battle_result else None,
        belief_db_dict=state.belief_db.to_dict(),
        trace_dicts=_strip_numpy(traces_raw),
        day=state.day,
        patron_favor=float(state.patron_favor),
        station=state.station.value,
        station_lottery_injuries=state.station_state.lottery_injuries,
        pending_orders=pending,
    )
    return capsule


def capsule_to_dict(capsule: SaveCapsule) -> Dict:
    """Convert a SaveCapsule to a plain dict (for JSON save files or Ren'Py extras)."""
    import dataclasses
    return _strip_numpy(dataclasses.asdict(capsule))


# ---------------------------------------------------------------------------
# Belief view for the Table screen (Layer 2 → Layer 3)

def belief_view_for_table(belief_db_dict: Dict, station_name: str) -> Dict[str, Any]:
    """Return a station-filtered belief view from a serialized BeliefDB snapshot.

    Used by the Ren'Py Table screen: takes the belief_db_dict from a SaveCapsule
    and returns only the claims visible from the given station.

    Output shape: {phase: {claim: {value, confidence, glyph}}}
    Glyph: '?' rumored, '~' scouted, '*' confirmed, '.' stale.
    """
    try:
        station = Station(station_name.upper())
    except ValueError:
        station = Station.CAMP

    db = BeliefDB()
    # Reconstruct BeliefDB from the saved dict
    for phase, claims in belief_db_dict.items():
        for claim, entry in claims.items():
            v = entry.get('value')
            c = entry.get('confidence', 0.5)
            # Infer source from confidence band (approximation for legacy dicts)
            if c >= 0.90:
                src = 'dispatch'
            elif c >= 0.80:
                src = 'sightlines'
            elif c >= 0.70:
                src = 'landscape'
            else:
                src = 'dispatch'
            db._beliefs.setdefault(phase, {})[claim] = (v, c, src)

    station_beliefs = db.beliefs_for_station(station)

    result: Dict[str, Any] = {}
    for phase, claims in station_beliefs.items():
        result[phase] = {}
        for claim, (value, conf) in claims.items():
            result[phase][claim] = {
                'value': value,
                'confidence': conf,
                'glyph': _confidence_glyph(conf),
            }
    return result


def _confidence_glyph(conf: float) -> str:
    """Map confidence to a Table glyph (spec §7, M4 Table screen)."""
    if conf >= 0.90:
        return '*'   # confirmed (painted miniature)
    if conf >= 0.75:
        return '~'   # scouted (unpainted lead)
    if conf >= 0.50:
        return '?'   # rumored (charcoal sketch)
    return '.'       # stale (dust)


# ---------------------------------------------------------------------------
# Archive / chronicle scrub (Layer 2 → Layer 3, post-battle)

def trace_for_archive(trace_dict: Dict) -> Dict[str, Any]:
    """Prepare a composed trace dict for the Ren'Py Archive scrub screen.

    Returns a dict with:
      phases      — ordered list of phase names
      deaths      — list of {t, cause, phase, location} (no agent_ids for privacy)
      rout_count  — int
      events      — list of {name, t, phase, kw} for chronicle citations
      summary     — {phase: {claim: value}} from trace_to_summary()

    The Archive renders two views of this: the chronicle (prose, with citations)
    and the trace (raw events). Rollback is re-enabled in the Archive layer only.
    """
    deaths = [
        {
            't': d['t'],
            'cause': d['cause'],
            'phase': d.get('phase', ''),
            'location': d.get('location'),
        }
        for d in trace_dict.get('deaths', [])
    ]

    events = [
        {
            'name': ev[0],
            't': ev[1],
            'kw': ev[2],
            'phase': ev[3] if len(ev) > 3 else '',
        }
        for ev in trace_dict.get('events', [])
    ]

    return {
        'phases': trace_dict.get('phases', []),
        'deaths': deaths,
        'rout_count': len(trace_dict.get('routs', [])),
        'events': events,
        'summary': trace_to_summary(trace_dict),
    }


# ---------------------------------------------------------------------------
# Vertical slice: single-battle run with cavalry parameter

def run_slice_battle(seed: int, order: str) -> Dict[str, Any]:
    """Run the Agincourt battle for the vertical slice.

    order: 'hold' | 'open'
      'hold'  → standard scenario: stakes at x=170, cavalry balks (horse_balk event)
      'open'  → stakes key removed: cavalry rides through, threatens archers

    The cavalry IS real in both cases; 'hold' accounts for it, 'open' ignores it.
    Returns {result, trace (composed 4-tuple events), chronicle (str), archive (dict)}.
    """
    from tools.chronicle import generate_chronicle

    scn = agincourt()

    if order == 'open':
        # Remove stake line so cavalry is not blocked; English advance onto flat
        scn = {k: v for k, v in scn.items() if k != 'stakes_x'}

    # 'hold' uses agincourt() as-is: stakes active, cavalry will balk

    tr = Trace(phase='battle', scenario=f'agincourt_slice_{order}', seed=seed)
    result = Battle(scn, seed, trace=tr).run()

    # Build composed trace (4-tuple events) for generate_chronicle and trace_for_archive
    composed: Dict[str, Any] = {
        'phases': ['battle'],
        'scenarios': [tr.scenario],
        'seed': seed,
        'deaths': [
            dict(t=d.t, agent_id=d.agent_id, cause=d.cause,
                 killer_cohort=d.killer_cohort, location=d.location, phase='battle')
            for d in tr.deaths
        ],
        'routs': [
            dict(t=r.t, agent_id=r.agent_id, appraisal=r.appraisal, phase='battle')
            for r in tr.routs
        ],
        'events': [(ev[0], ev[1], ev[2], 'battle') for ev in tr.events],
    }
    chronicle = generate_chronicle(composed)
    archive = trace_for_archive(composed)

    return _strip_numpy({
        'result': result,
        'trace': composed,
        'chronicle': chronicle,
        'archive': archive,
    })


# ---------------------------------------------------------------------------
# Pending order serialization

def pending_order_for_renpy(po: Any) -> Dict:
    """Serialize a PendingOrder (clients.cli.season.PendingOrder) to a plain dict."""
    return {
        'command': po.command,
        'eta_day': po.eta_day,
        'label': po.label,
    }
