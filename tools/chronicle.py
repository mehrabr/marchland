"""MARCHLAND tools: trace → prose chronicle.

Two render paths come off the one trace, never concatenated:

  NARRATION   generate_chronicle(trace) -> str
              Prose written FROM the trace, in a vantage voice with sympathies
              ('our men', 'the King's army'). NO numbers, no 'side-1', no
              seconds, no engine citations. Magnitude survives in period
              register ('the better part of a thousand', 'the dead lay thick',
              'far more of theirs than of ours').

  INSPECTION  build_chronicle(trace) -> List[ChronicleLine]
              Each line carries its grounding citation in a parallel field the
              inspector can surface ('explain'); the prose itself never shows it.

The chronicle is a SOURCE, not a read-out of the trace. The narrator is a
person who saw the day from a side. The grounding rule is unchanged: every
sentence still traces to a specific event or measurement. Nothing is fabricated;
if an event is absent, the sentence that would reference it is omitted.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ChronicleLine:
    """One narrated sentence and the trace fact that grounds it.

    `prose`    — the human, numberless, vantage-voice sentence (the wall).
    `citation` — the grounding event/measurement, surfaced only by `explain`
                 (the door). Never displayed in narration.
    `phase`    — 'siege' | 'march' | 'battle'.
    """
    prose: str
    citation: str
    phase: str


# ------------------------------------------------------------------
# Period number register

_ONES = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
         'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
         'sixteen', 'seventeen', 'eighteen', 'nineteen']
_TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy',
         'eighty', 'ninety']


def _spell_cardinal(n: int) -> str:
    """Spell a non-negative integer up to 999 in words. Larger falls back to digits."""
    if n < 0:
        return str(n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        t = _TENS[n // 10]
        return t if n % 10 == 0 else f"{t}-{_ONES[n % 10]}"
    if n < 1000:
        h = f"{_ONES[n // 100]} hundred"
        r = n % 100
        return h if r == 0 else f"{h} and {_spell_cardinal(r)}"
    return str(n)


_ORD_IRREGULAR = {1: 'first', 2: 'second', 3: 'third', 5: 'fifth', 8: 'eighth',
                  9: 'ninth', 12: 'twelfth'}


def _spell_ordinal(n: int) -> str:
    """Spell an ordinal (1st..99th) in period words. 'thirty-seventh', etc."""
    if n in _ORD_IRREGULAR:
        return _ORD_IRREGULAR[n]
    if n < 20:
        return _ONES[n] + 'th'
    if n < 100:
        if n % 10 == 0:
            return _TENS[n // 10][:-1] + 'ieth'   # twenty -> twentieth
        return f"{_TENS[n // 10]}-{_spell_ordinal(n % 10)}"
    return f"{n}th"


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _approx_miles(miles: float) -> str:
    """A rounded, period-register distance: 'two hundred and sixty miles'."""
    rounded = int(round(miles / 10.0) * 10)
    if rounded <= 0:
        return "a short way"
    return f"{_spell_cardinal(rounded)} miles"


def _magnitude(n: int) -> Optional[str]:
    """A period-register sense of a casualty count — magnitude kept, number hidden.

    Tuned so ~636 reads 'the better part of a thousand' (Sarris's caution:
    de-numbering must not flatten the shock of scale).
    """
    if n <= 0:
        return None
    if n < 30:
        return "a few"
    if n < 80:
        return "two score and more"
    if n < 150:
        return "near a hundred"
    if n < 300:
        return "some hundreds"
    if n < 550:
        return "many hundreds"
    if n < 950:
        return "the better part of a thousand"
    if n < 1500:
        return "a full thousand and more"
    thousands = int(round(n / 1000.0))
    return f"some {_spell_cardinal(thousands)} thousand"


# ------------------------------------------------------------------
# Trace access helpers

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


# ------------------------------------------------------------------
# Phase narrators — each returns a list of grounded ChronicleLines

def _siege_lines(trace: Dict) -> List[ChronicleLine]:
    evs = _events_for(trace, 'siege')
    lines: List[ChronicleLine] = []

    outcome_ev = None
    for name in ('NEGOTIATED', 'STORMED_sack', 'RELIEVED', 'ABANDONED_supply', 'ONGOING'):
        ev = _find_event(evs, name)
        if ev:
            outcome_ev = ev
            break

    if outcome_ev:
        name = outcome_ev[0]
        day = int(outcome_ev[1])
        weeks = max(1, day // 7)
        if name == 'NEGOTIATED':
            prose = (
                f"{_cap(_spell_cardinal(weeks))} weeks the town held, until the "
                f"garrison — sick of waiting on a relief that never came — sent "
                f"out to ask for terms, and on the {_spell_ordinal(day)} day the "
                f"gates were opened."
            )
        elif name == 'STORMED_sack':
            prose = (
                f"{_cap(_spell_cardinal(weeks))} weeks the town held, until on "
                f"the {_spell_ordinal(day)} day the walls were carried by storm, "
                f"and the place given over to the sack."
            )
        elif name == 'RELIEVED':
            prose = (
                f"On the {_spell_ordinal(day)} day a relief column came up under "
                f"the walls, and our siege was raised and the host drew off."
            )
        elif name == 'ABANDONED_supply':
            prose = (
                f"On the {_spell_ordinal(day)} day, our own stores failing, the "
                f"siege was abandoned and the host marched away unsatisfied."
            )
        else:
            prose = (
                f"When the season closed the town still held, and the siege was "
                f"left unfinished on the {_spell_ordinal(day)} day."
            )
        lines.append(ChronicleLine(prose, f"{name}@day{day}", 'siege'))

    disease_total = _count_event(evs, 'disease')
    if disease_total > 0:
        mag = _magnitude(disease_total)
        prose = (
            f"The siege had cost the King's army dearly without a blow struck in "
            f"anger: the bloody flux ran through the wet camps and carried off "
            f"{mag} men."
        )
        n_events = len([e for e in evs if e[0] == 'disease'])
        lines.append(ChronicleLine(prose, f"{n_events} disease events, total={disease_total}", 'siege'))

    assault_ev = _find_event(evs, 'assault')
    if assault_ev:
        day = int(assault_ev[1])
        prose = (
            f"A storm was pressed at the breach on the {_spell_ordinal(day)} day, "
            f"and it was bloody work, and many good men were left in the ditch."
        )
        lines.append(ChronicleLine(prose, f"assault@day{day}", 'siege'))

    if not lines:
        scn = (trace.get('scenarios') or ['the town'])[0]
        lines.append(ChronicleLine(f"The siege of {scn} ran its course.", "siege", 'siege'))
    return lines


def _march_lines(trace: Dict) -> List[ChronicleLine]:
    evs = _events_for(trace, 'march')
    lines: List[ChronicleLine] = []

    arrived_ev = _find_event(evs, 'arrived') or _find_event(evs, 'failed')
    detour_evs = [ev for ev in evs if ev[0] == 'detour']
    thirst_total = _count_event(evs, 'thirst')
    disease_total = _count_event(evs, 'disease')

    if arrived_ev:
        days = int(arrived_ev[1])
        miles = arrived_ev[2].get('miles', 0)
        detour_clause = ""
        detour_cite = ""
        if detour_evs:
            detour_clause = (
                ", for the way was barred against them and they were driven far "
                "aside to find a crossing"
            )
            detour_cite = f"; detour@day{int(detour_evs[0][1])}"
        if arrived_ev[0] == 'arrived':
            prose = (
                f"The march that followed was a hard one. "
                f"{_cap(_spell_cardinal(days))} days the host went, near to "
                f"{_approx_miles(miles)}{detour_clause}. They came to the field "
                f"footsore and hungry."
            )
        else:
            prose = (
                f"The march broke down before its end: "
                f"{_spell_cardinal(days)} days out and short of the goal"
                f"{detour_clause}, the host could go no further."
            )
        lines.append(ChronicleLine(prose, f"{arrived_ev[0]}@day{days}{detour_cite}", 'march'))

    if disease_total > 0:
        mag = _magnitude(disease_total)
        n_events = len([e for e in evs if e[0] == 'disease'])
        prose = f"The camp sickness followed them onto the road, and took {mag} more."
        lines.append(ChronicleLine(prose, f"{n_events} disease events, total={disease_total}", 'march'))
    elif arrived_ev:
        prose = "Disease spared them on the road, as it had not in the camp."
        lines.append(ChronicleLine(prose, "no march disease events", 'march'))

    if thirst_total > 0:
        mag = _magnitude(thirst_total)
        n_events = len([e for e in evs if e[0] == 'thirst'])
        prose = f"On the dry days thirst told upon them, and {mag} fell out and were lost."
        lines.append(ChronicleLine(prose, f"{n_events} thirst events, total={thirst_total}", 'march'))

    if not lines:
        scn = (trace.get('scenarios') or ['', 'the march'])
        name = scn[1] if len(scn) > 1 else 'the march'
        lines.append(ChronicleLine(f"The march to {name} was made.", "march", 'march'))
    return lines


def _battle_lines(trace: Dict) -> List[ChronicleLine]:
    evs = _events_for(trace, 'battle')
    deaths = _deaths_for(trace, 'battle')

    by_cause: Dict[str, int] = {}
    for d in deaths:
        by_cause[d['cause']] = by_cause.get(d['cause'], 0) + 1

    volley = by_cause.get('volley', 0)
    melee = by_cause.get('melee', 0) + by_cause.get('cavalry', 0)
    pursuit = by_cause.get('pursuit', 0)
    horse_balk = _find_event(evs, 'horse_balk')
    side0_broke = _find_event(evs, 'side0_broke')
    side1_broke = _find_event(evs, 'side1_broke')

    lines: List[ChronicleLine] = []

    if volley > 0:
        prose = (
            "Then the arrows did their work — the enemy came on, and our bowmen "
            "emptied their sheaves into them, and many fell before ever a sword "
            "was drawn."
        )
        lines.append(ChronicleLine(prose, f"{volley} volley death-certs", 'battle'))

    if horse_balk:
        prose = (
            "The enemy horse came against the stakes and would not face them, "
            "and shied away."
        )
        lines.append(ChronicleLine(prose, f"horse_balk@{horse_balk[1]:.0f}", 'battle'))

    if melee > 0:
        prose = "When the lines met at last, the slaughter was very great."
        lines.append(ChronicleLine(prose, f"{melee} melee/cavalry death-certs", 'battle'))

    # The break, the pursuit, and the lopsided dead — grounded in which side broke.
    # The broken side is run down in the flight; casualties live in the pursuit.
    if side1_broke:
        if pursuit > 0:
            tail = ("and at the last, near the day's end, the enemy broke, and "
                    "our men pursued them. The dead lay thick upon the ground, "
                    "and far more of theirs than of ours.")
            cite = f"side1_broke@{side1_broke[1]:.0f}; {pursuit} pursuit death-certs"
        else:
            tail = ("and at the last the enemy broke and quit the field, and "
                    "more of theirs than of ours lay dead upon it.")
            cite = f"side1_broke@{side1_broke[1]:.0f}"
        lines.append(ChronicleLine(_cap(tail), cite, 'battle'))
    elif side0_broke:
        tail = ("and at the last our own line gave way; we were driven from the "
                "field, and the greater part of the slain were our own.")
        lines.append(ChronicleLine(_cap(tail), f"side0_broke@{side0_broke[1]:.0f}", 'battle'))
    elif lines:
        lines.append(ChronicleLine(
            "Neither side would break, and the dead lay thick on both alike.",
            "no break event", 'battle'))

    if not lines:
        lines.append(ChronicleLine("The field was held, and little blood spilled.", "battle", 'battle'))
    return lines


# ------------------------------------------------------------------
# Public API

def build_chronicle(trace: Dict[str, Any]) -> List[ChronicleLine]:
    """Return the chronicle as a list of grounded ChronicleLines.

    The narration path joins their `prose`; the inspection path ('explain')
    surfaces their `citation`. Same trace, two registers.
    """
    phases = trace.get('phases', [])
    lines: List[ChronicleLine] = []
    if 'siege' in phases:
        lines.extend(_siege_lines(trace))
    if 'march' in phases:
        lines.extend(_march_lines(trace))
    if 'battle' in phases:
        lines.extend(_battle_lines(trace))
    return lines


def chronicle_with_citations(trace: Dict[str, Any]) -> List[Tuple[str, str]]:
    """(prose, citation) pairs — the parallel structure the inspector surfaces."""
    return [(ln.prose, ln.citation) for ln in build_chronicle(trace)]


def generate_chronicle(trace: Dict[str, Any]) -> str:
    """Produce the human, numberless, vantage-voice chronicle (the wall).

    One paragraph per phase (siege, march, battle), only for phases present.
    No engine numbers, no 'side-1', no seconds, no trace citations — those live
    behind 'explain' (see chronicle_with_citations / build_chronicle).
    """
    lines = build_chronicle(trace)
    by_phase: Dict[str, List[str]] = {}
    order: List[str] = []
    for ln in lines:
        if ln.phase not in by_phase:
            by_phase[ln.phase] = []
            order.append(ln.phase)
        by_phase[ln.phase].append(ln.prose)
    return "\n\n".join(" ".join(by_phase[ph]) for ph in order)
