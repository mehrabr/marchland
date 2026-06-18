"""MARCHLAND core: mission taxonomy.

Seven mission types from the spec. Each mission has:
  description       — what the patron is asking for
  objective_label   — what the patron calls success
  patron_belief_claim — the claim checked in the belief_db at audit
  objective_predicate — callable(trace_summary) -> bool; ground-truth evaluation
  deadline_days     — default season clock

The objective_predicate is checked against the trace summary (ground truth).
The patron evaluates against their belief_db — which may differ.
"""
from typing import Callable, Dict, Any


def _siege_success(ts: Dict) -> bool:
    return ts.get('siege', {}).get('outcome') in ('NEGOTIATED', 'STORMED_sack')


def _siege_within_deadline(ts: Dict, deadline: int) -> bool:
    if not _siege_success(ts):
        return False
    return ts.get('siege', {}).get('day', 9999) <= deadline


def _march_arrived(ts: Dict) -> bool:
    return ts.get('march', {}).get('arrived', False)


def _battle_won(ts: Dict) -> bool:
    return ts.get('battle', {}).get('won', False)


def _escort_arrived(ts: Dict) -> bool:
    # Escort succeeds if march arrived AND battle (if any) was won or no battle occurred
    if not _march_arrived(ts):
        return False
    if 'battle' in ts:
        return _battle_won(ts)
    return True


def _hold_field(ts: Dict) -> bool:
    # Hold: player side did not break
    return ts.get('battle', {}).get('won', False)


def _chevauchee_success(ts: Dict) -> bool:
    # Chevauchée: march covered enough ground (arrived implies country was traversed)
    return _march_arrived(ts)


def _suppress_success(ts: Dict) -> bool:
    # Suppress: like siege but garrison militia; accept NEGOTIATED only
    return ts.get('siege', {}).get('outcome') == 'NEGOTIATED'


# ------------------------------------------------------------------
# Mission registry

MISSIONS: Dict[str, Dict[str, Any]] = {
    'siege': {
        'description': 'Reduce a fortified place; accept its surrender or storm the breach.',
        'objective_label': 'place_taken',
        'patron_belief_claim': 'outcome',
        'patron_success_values': ('NEGOTIATED', 'STORMED_sack'),
        'objective_predicate': _siege_success,
        'deadline_days': 60,
    },
    'intercept': {
        'description': 'Block the enemy column and hold the field.',
        'objective_label': 'field_held',
        'patron_belief_claim': 'won',
        'patron_success_values': (True,),
        'objective_predicate': _hold_field,
        'deadline_days': 14,
    },
    'chevauche': {
        'description': 'March through enemy country, devastating supplies.',
        'objective_label': 'country_harried',
        'patron_belief_claim': 'arrived',
        'patron_success_values': (True,),
        'objective_predicate': _chevauchee_success,
        'deadline_days': 21,
    },
    'relief': {
        'description': 'Relieve a besieged garrison before it falls.',
        'objective_label': 'garrison_relieved',
        'patron_belief_claim': 'arrived',
        'patron_success_values': (True,),
        'objective_predicate': _march_arrived,
        'deadline_days': 18,
    },
    'escort': {
        'description': 'Escort a convoy or dignitary to its destination intact.',
        'objective_label': 'convoy_delivered',
        'patron_belief_claim': 'arrived',
        'patron_success_values': (True,),
        'objective_predicate': _escort_arrived,
        'deadline_days': 28,
    },
    'hold': {
        'description': 'Defend a position until relieved or the enemy withdraws.',
        'objective_label': 'position_held',
        'patron_belief_claim': 'won',
        'patron_success_values': (True,),
        'objective_predicate': _hold_field,
        'deadline_days': 30,
    },
    'march': {
        'description': 'Reach the muster point before the season closes.',
        'objective_label': 'army_arrived',
        'patron_belief_claim': 'arrived',
        'patron_success_values': (True,),
        'objective_predicate': _march_arrived,
        'deadline_days': 22,
    },
    'suppress': {
        'description': 'Bring a rebellious town to terms without sacking it.',
        'objective_label': 'town_pacified',
        'patron_belief_claim': 'outcome',
        'patron_success_values': ('NEGOTIATED',),
        'objective_predicate': _suppress_success,
        'deadline_days': 45,
    },
}


def evaluate_mission(mission_key: str, trace_summary: Dict) -> bool:
    """Check whether the mission objective was met (ground truth from trace)."""
    spec = MISSIONS.get(mission_key)
    if spec is None:
        raise ValueError(f"Unknown mission {mission_key!r}")
    return spec['objective_predicate'](trace_summary)


def patron_believes_success(mission_key: str, belief_db) -> bool:
    """Check whether the patron (via belief_db) believes the mission succeeded."""
    spec = MISSIONS.get(mission_key)
    if spec is None:
        raise ValueError(f"Unknown mission {mission_key!r}")
    claim = spec['patron_belief_claim']
    success_values = spec['patron_success_values']

    # Patron checks the phase most relevant to the mission
    phase = _primary_phase(mission_key)
    believed = belief_db.believed(phase, claim)
    if believed is None:
        return False   # no dispatch = patron has no grounds to credit success
    return believed in success_values


def _primary_phase(mission_key: str) -> str:
    return {
        'siege':     'siege',
        'suppress':  'siege',
        'intercept': 'battle',
        'hold':      'battle',
        'chevauche': 'march',
        'relief':    'march',
        'escort':    'march',
        'march':     'march',
    }.get(mission_key, 'battle')
