"""MARCHLAND CLI: campaign Table renderer (M4).

Renders the player's information state as a formatted text view. Each entity
is shown at its believed position with an uncertainty glyph:

  *  confirmed   (painted miniature — rider confirmed, high confidence)
  ~  scouted     (unpainted lead — landscape/sightline observation)
  ?  rumoured    (charcoal sketch — second-hand, low confidence)
  .  stale       (dust — last update was more than one operation ago)

Dispatches in transit are shown with → and an ETA.

This module depends only on core.* and the stdlib; it has no Rich dependency
so it can emit plain text even when Rich is unavailable.
"""
from typing import Any, Dict, List, Optional, Tuple

from core.stations import Station, STATIONS, StationState


# ------------------------------------------------------------------
# Glyph logic

def _confidence_glyph(confidence: float, stale: bool = False) -> str:
    """Return the uncertainty glyph for a given confidence level."""
    if stale:
        return '.'
    if confidence >= 0.85:
        return '*'
    if confidence >= 0.70:
        return '~'
    return '?'


def _glyph_label(glyph: str) -> str:
    return {
        '*': 'confirmed',
        '~': 'scouted',
        '?': 'rumoured',
        '.': 'stale',
    }.get(glyph, '')


# ------------------------------------------------------------------
# Campaign line

# The 1415 campaign unfolds along a simple east-west axis.
# Positions are 0-based offsets in the campaign line string.
_CAMPAIGN_LINE = [
    ('HARFLEUR',   0,  'H'),
    ('ROAD',       1,  '—'),
    ('AGINCOURT',  2,  'A'),
]


def _build_campaign_line(phase_known: Dict[str, str]) -> str:
    """Draw the campaign line with known operation markers."""
    # phase_known: {'siege': glyph, 'march': glyph, 'battle': glyph}
    h = phase_known.get('siege', ' ')
    m = phase_known.get('march', ' ')
    a = phase_known.get('battle', ' ')
    return f"  [{h}]HARFLEUR  ——{[m][0]}——>  [{a}]AGINCOURT"


# ------------------------------------------------------------------
# Main render function

def render_table(
    day: int,
    station_state: StationState,
    belief_db: Any,           # BeliefDB
    pending_orders: List[Any],  # List[PendingOrder] from season.py
    *,
    io: Any,                  # _IO compatible
) -> None:
    """Print the campaign Table to the given io object."""
    spec = STATIONS[station_state.station]

    io.print()
    io.print("╔══════════════════════════════════════════════════════╗")
    io.print(f"  TABLE — Day {day}   Station: {spec.label.upper()}")
    io.print(f"  ({spec.description})")
    io.print("══════════════════════════════════════════════════════")

    # -- Campaign line --
    visible = belief_db.beliefs_for_station(station_state.station)
    phase_glyphs: Dict[str, str] = {}
    for phase_key, map_key in [('siege', 'siege'), ('march', 'march'), ('battle', 'battle')]:
        claims = visible.get(phase_key, {})
        if claims:
            confs = [c for _v, c in claims.values()]
            glyph = _confidence_glyph(min(confs))
            phase_glyphs[map_key] = glyph
    io.print(_build_campaign_line(phase_glyphs))
    io.print()

    # -- Known entities --
    io.print("  KNOWN:")
    _print_known(visible, io)

    # -- Pending orders (dispatches in transit) --
    if pending_orders:
        io.print()
        io.print("  ORDERS IN TRANSIT:")
        for po in pending_orders:
            eta = po.eta_day
            io.print(f"    → {po.label}  (ETA: day {eta})")
    else:
        if station_state.station == Station.CAMP and station_state.spec.latency_days > 0:
            io.print(f"  (At CAMP — orders take {station_state.spec.latency_days} days to reach the field.)")

    # -- Station properties --
    io.print()
    io.print(f"  Station lottery: {spec.lottery_per_day:.1%}/day   "
             f"Order latency: {spec.latency_days}d   "
             f"Injuries this season: {station_state.lottery_injuries}")
    io.print("╚══════════════════════════════════════════════════════╝")
    io.print()


def _print_known(visible: Dict[str, Dict], io: Any) -> None:
    """Print each known phase's claims with glyphs."""
    PHASE_LABELS = {
        'siege':  'Harfleur siege',
        'march':  'March to Agincourt',
        'battle': 'Battle of Agincourt',
    }
    if not visible:
        io.print("    (nothing known — no dispatches received)")
        return

    for phase in ('siege', 'march', 'battle'):
        claims = visible.get(phase)
        if not claims:
            continue
        label = PHASE_LABELS.get(phase, phase)
        # Render each claim on its own line with the glyph
        for claim, (value, conf) in claims.items():
            glyph = _confidence_glyph(conf)
            glabel = _glyph_label(glyph)
            io.print(f"    {glyph} {label} — {claim}: {value}  [{glabel}, {conf:.0%}]")


# ------------------------------------------------------------------
# Standalone summary for use in audit / court scenes

def summarise_station(station_state: StationState) -> str:
    """One-line summary of current station for display in court / audit text."""
    spec = STATIONS[station_state.station]
    return (
        f"{spec.label} "
        f"(latency {spec.latency_days}d, lottery {spec.lottery_per_day:.1%}/day)"
    )
