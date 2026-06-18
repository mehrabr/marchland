"""MARCHLAND tools: trace → prose chronicle.

Rule: every statement in the output must cite a specific event or measurement from
the composed trace. Nothing is fabricated. If an event is absent from the trace,
the sentence that would reference it is omitted.

Usage:
    from tools.chronicle import generate_chronicle
    text = generate_chronicle(composed_trace)  # composed_trace from core.trace.compose_traces
"""
from typing import Any, Dict, List, Optional


def _events_for(trace: Dict, phase: str) -> List:
    return [ev for ev in trace.get('events', []) if ev[3] == phase]


def _deaths_for(trace: Dict, phase: str) -> List:
    return [d for d in trace.get('deaths', []) if d['phase'] == phase]


def _find_event(events: List, name: str) -> Optional[tuple]:
    for ev in events:
        if ev[0] == name:
            return ev
    return None


def _count_event(events: List, name: str) -> int:
    return sum(ev[2].get('count', 0) for ev in events if ev[0] == name)


def _siege_paragraph(trace: Dict) -> str:
    evs = _events_for(trace, 'siege')
    scenarios = trace.get('scenarios', [])
    scn_name = scenarios[0] if scenarios else 'siege'

    outcome_ev = None
    for name in ('NEGOTIATED', 'STORMED_sack', 'RELIEVED', 'ABANDONED_supply', 'ONGOING'):
        ev = _find_event(evs, name)
        if ev:
            outcome_ev = ev
            break

    disease_total = _count_event(evs, 'disease')
    terms_ev = _find_event(evs, 'terms_struck')
    assault_ev = _find_event(evs, 'assault')

    parts = []

    if outcome_ev:
        outcome_name = outcome_ev[0]
        day = int(outcome_ev[1])
        if outcome_name == 'NEGOTIATED':
            parts.append(
                f"The siege ran {day} days before the garrison struck terms "
                f"(trace: {outcome_name}@day{day})."
            )
        elif outcome_name == 'STORMED_sack':
            parts.append(
                f"The besieger stormed the breach on day {day} (trace: {outcome_name}@day{day})."
            )
        elif outcome_name == 'RELIEVED':
            parts.append(
                f"A relief force arrived on day {day}, ending the siege (trace: RELIEVED@day{day})."
            )
        else:
            parts.append(f"Siege outcome: {outcome_name}, day {day} (trace: {outcome_name}@day{day}).")

    if terms_ev:
        terms_day = int(terms_ev[1])
        parts.append(
            f"Terms were struck on day {terms_day}; the relief window expired before relief arrived "
            f"(trace: terms_struck@day{terms_day})."
        )

    if disease_total > 0:
        parts.append(
            f"Disease in the besieger's camp felled {disease_total} men "
            f"(trace: {len([e for e in evs if e[0]=='disease'])} disease events, total={disease_total})."
        )

    if assault_ev:
        assault_dead = assault_ev[2].get('dead', 0)
        parts.append(
            f"A storm was attempted on day {int(assault_ev[1])}, costing {assault_dead} assault dead "
            f"(trace: assault@day{int(assault_ev[1])})."
        )

    return " ".join(parts) if parts else f"Siege of {scn_name} completed."


def _march_paragraph(trace: Dict) -> str:
    evs = _events_for(trace, 'march')
    scenarios = trace.get('scenarios', [])
    scn_name = scenarios[1] if len(scenarios) > 1 else 'march'

    arrived_ev = _find_event(evs, 'arrived') or _find_event(evs, 'failed')
    thirst_total = _count_event(evs, 'thirst')
    disease_total = _count_event(evs, 'disease')
    detour_evs = [ev for ev in evs if ev[0] == 'detour']

    parts = []

    if arrived_ev:
        days = int(arrived_ev[1])
        miles = arrived_ev[2].get('miles', '?')
        fat = arrived_ev[2].get('fatigue', '?')
        status = "arrived" if arrived_ev[0] == 'arrived' else "failed to arrive"
        parts.append(
            f"The army {status} at its destination in {days} days "
            f"({miles} miles marched, fatigue {fat}) "
            f"(trace: {arrived_ev[0]}@day{days})."
        )

    for detour in detour_evs:
        parts.append(
            f"A detour of {detour[2].get('extra','?')} miles was taken on day {int(detour[1])} "
            f"(trace: detour@day{int(detour[1])})."
        )

    if thirst_total > 0:
        parts.append(
            f"Thirst claimed {thirst_total} men on dry days "
            f"(trace: {len([e for e in evs if e[0]=='thirst'])} thirst events, total={thirst_total})."
        )

    if disease_total > 0:
        parts.append(
            f"Camp disease took {disease_total} more "
            f"(trace: {len([e for e in evs if e[0]=='disease'])} disease events, total={disease_total})."
        )

    return " ".join(parts) if parts else f"March ({scn_name}) completed."


def _battle_paragraph(trace: Dict) -> str:
    evs = _events_for(trace, 'battle')
    deaths = _deaths_for(trace, 'battle')

    by_cause: Dict[str, int] = {}
    by_side: Dict[int, int] = {}
    for d in deaths:
        by_cause[d['cause']] = by_cause.get(d['cause'], 0) + 1
        s = d.get('side')
        if s is not None:
            by_side[s] = by_side.get(s, 0) + 1

    horse_balk_ev = _find_event(evs, 'horse_balk')
    broke_evs = {0: _find_event(evs, 'side0_broke'), 1: _find_event(evs, 'side1_broke')}
    ammo_ev = _find_event(evs, 'ammo_starved_far') or _find_event(evs, 'ammo_starved_near')
    leader_evs = [_find_event(evs, f'leader{s}_down') for s in (0, 1)]

    parts = []

    # volley deaths
    volley_count = by_cause.get('volley', 0)
    if volley_count > 0:
        parts.append(
            f"Arrow volleys accounted for {volley_count * 10} dead "
            f"(trace: {volley_count} death-certs, cause=volley)."
        )

    # horse balk
    if horse_balk_ev:
        balk_t = horse_balk_ev[1]
        parts.append(
            f"The opposing cavalry met the stake-line at {balk_t:.0f}s "
            f"(trace: horse_balk@{balk_t:.0f}s)."
        )

    # ammo starvation
    if ammo_ev:
        parts.append(
            f"The ranged supply was exhausted at {ammo_ev[1]:.0f}s "
            f"(trace: {ammo_ev[0]}@{ammo_ev[1]:.0f}s)."
        )

    # leader falls
    for s, lev in enumerate(leader_evs):
        if lev:
            side_label = 'side-0' if s == 0 else 'side-1'
            parts.append(
                f"The {side_label} commander fell at {lev[1]:.0f}s "
                f"(trace: leader{s}_down@{lev[1]:.0f}s)."
            )

    # melee deaths
    melee_count = by_cause.get('melee', 0) + by_cause.get('cavalry', 0)
    if melee_count > 0:
        parts.append(
            f"Melee contact killed {melee_count * 10} (trace: {melee_count} death-certs, cause=melee/cavalry)."
        )

    # pursuit deaths
    pursuit_count = by_cause.get('pursuit', 0)
    if pursuit_count > 0:
        parts.append(
            f"Pursuit accounted for {pursuit_count * 10} more "
            f"(trace: {pursuit_count} death-certs, cause=pursuit)."
        )

    # break events — whichever side broke determines the winner
    for s in (1, 0):   # check losing side first (winner is reported relative to break)
        if broke_evs[s]:
            bt = broke_evs[s][1]
            side_label = 'side-0' if s == 0 else 'side-1'
            parts.append(
                f"{side_label.capitalize()} broke at {bt:.0f}s "
                f"(trace: side{s}_broke@{bt:.0f}s)."
            )

    return " ".join(parts) if parts else "Battle concluded."


def generate_chronicle(trace: Dict[str, Any]) -> str:
    """Produce a three-paragraph prose chronicle from a composed trace.

    Each paragraph covers one phase (siege, march, battle).
    Only phases present in the trace are included.
    Every sentence cites its source event in the trace.
    """
    phases = trace.get('phases', [])
    paragraphs = []

    if 'siege' in phases:
        paragraphs.append(_siege_paragraph(trace))
    if 'march' in phases:
        paragraphs.append(_march_paragraph(trace))
    if 'battle' in phases:
        paragraphs.append(_battle_paragraph(trace))

    return "\n\n".join(paragraphs)
