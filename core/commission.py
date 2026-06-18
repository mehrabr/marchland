"""MARCHLAND core: commission — the patron's dealt hand.

A Commission is the patron's offer: an army (muster receipts), a mission
from the taxonomy, and strings (deadline, quarter policy, co-commander).
The player reads the receipts at muster and accepts or negotiates terms.

Army receipts are read from culture data files; no armies are hardcoded here.
"""
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Commission:
    patron: str
    patron_favor: float          # 0.0–1.0; how much the patron trusts the commander
    army_name: str
    army_cohorts: List[Dict]     # cohort receipt dicts (read from culture file)
    mission: str                 # mission type key from core.missions.MISSIONS
    strings: Dict[str, Any]     # deadline_days, quarter_policy, co_commander
    culture: Dict                # full culture dict for reference during the season
    season_day: int = 0          # current season clock


def generate_commission(culture: Dict, rng) -> Commission:
    """Deal a commission hand from a culture file.

    Picks one army from culture['armies'], one mission from
    culture['missions_pool'], and generates the attached strings.
    Army receipts are copied — the caller may not mutate the culture file.
    """
    armies = culture['armies']
    army = armies[rng.integers(0, len(armies))]

    missions_pool = culture['missions_pool']
    mission = missions_pool[rng.integers(0, len(missions_pool))]

    # Strings: the patron's conditions attached to the commission
    strings: Dict[str, Any] = {
        'deadline_days': _deadline_for(mission, culture),
        'quarter_policy': 'liberal',    # player may negotiate at muster
        'co_commander':  None,
    }

    return Commission(
        patron=culture['patron'],
        patron_favor=culture['career']['starting_patron_favor'],
        army_name=army['name'],
        army_cohorts=copy.deepcopy(army['cohorts']),
        mission=mission,
        strings=strings,
        culture=culture,
    )


def apply_quarter_policy(commission: Commission, policy: str) -> None:
    """Player negotiates quarter policy at muster.

    Updates commission.strings['quarter_policy'].
    Caller must supply a valid policy key from culture['quarter_customs'].
    """
    valid = set(commission.culture['quarter_customs'].keys())
    if policy not in valid:
        raise ValueError(f"Unknown quarter policy {policy!r}; valid: {valid}")
    commission.strings['quarter_policy'] = policy


def muster_summary(commission: Commission) -> str:
    """Return a readable muster report string (no side-effects)."""
    vocab = commission.culture['doctrine_vocab']
    lines = [
        f"Commission from {commission.patron}",
        f"Mission: {commission.mission.upper()}",
        f"Deadline: {commission.strings['deadline_days']} days",
        f"Army: {commission.army_name}",
        "",
        "  Cohort                    Men  Equipment",
        "  " + "-" * 50,
    ]
    for c in commission.army_cohorts:
        equip_parts = []
        if c.get('armor', 0) >= 0.8:
            equip_parts.append('full harness')
        elif c.get('armor', 0) >= 0.4:
            equip_parts.append('partial armor')
        if c.get('ranged'):
            equip_parts.append(f"longbow ×{c.get('ammo', 0)} sheaves")
        if c.get('mounted'):
            equip_parts.append('mounted')
        equip = ', '.join(equip_parts) if equip_parts else '—'
        lines.append(f"  {c['label']:<25} {c['n']:>4}  {equip}")
    lines += [
        "",
        f"Quarter policy: {commission.strings['quarter_policy']}",
    ]
    if commission.strings.get('co_commander'):
        lines.append(f"Co-commander: {commission.strings['co_commander']}")
    return "\n".join(lines)


def _deadline_for(mission: str, culture: Dict) -> int:
    """Season deadline: culture may override per-mission default for a vertical slice."""
    # A culture's career block may set 'season_deadline' to accommodate multi-phase chains
    if 'season_deadline' in culture.get('career', {}):
        return culture['career']['season_deadline']
    from .missions import MISSIONS
    return MISSIONS.get(mission, {}).get('deadline_days', 60)
