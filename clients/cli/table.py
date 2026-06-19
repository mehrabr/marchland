"""MARCHLAND CLI: campaign Table renderer (M4/M7.6).

Renders the player's information state as a formatted text view. Each entity
is shown at its believed position with an uncertainty glyph:

  *  confirmed   (painted miniature — rider confirmed, high confidence)
  ~  scouted     (unpainted lead — landscape/sightline observation)
  ?  rumoured    (charcoal sketch — second-hand, low confidence)
  .  stale       (dust — last update was more than one operation ago)

Dispatches in transit are shown with → and an ETA.

M7.6: Sentiment renders as a visible field spreading across the player's own
cohorts, in the same uncertainty grammar. True mood may require a present,
trusted officer's report. Intervention levers (issued as in-flight orders
through the M7.A queue) are shown alongside each cohort's sentiment state.

This module depends only on core.* and the stdlib; it has no Rich dependency
so it can emit plain text even when Rich is unavailable.
"""
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

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
    sentiment_summary: Optional[List[Any]] = None,  # M7.6: SentimentField.cohort_summary()
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

    # -- M7.6: Sentiment field (if any) --
    if sentiment_summary:
        render_sentiment(sentiment_summary, spec.lottery_per_day,
                         io=io)

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
# M7.6: Sentiment field rendering

# Penetration glyphs (mirrors the confidence uncertainty grammar)
_SENTIMENT_GLYPHS = [
    (0.70, '!', 'flipped  — meaning may be broken'),
    (0.45, '▲', 'high     — spreading fast'),
    (0.20, '~', 'present  — seed established'),
    (0.05, '?', 'rumoured — early trace'),
    (0.00, '·', 'clear    — no penetration'),
]


def _sentiment_glyph(penetration: float) -> tuple:
    for threshold, glyph, label in _SENTIMENT_GLYPHS:
        if penetration >= threshold:
            return glyph, label
    return '·', 'clear'


def render_sentiment(sentiment_summary: list, station_authority: float,
                     *, io: Any) -> None:
    """M7.6: Render the sentiment field for the current cohort graph.

    sentiment_summary: list of dicts from SentimentField.cohort_summary()
    station_authority: player's current command authority (0–1); affects visibility

    The player sees true sentiment only if a trusted officer (authority ≥ 0.7)
    is with the cohort. Otherwise they see the uncertainty glyph '?'.

    Intervention levers are shown alongside each cohort:
      dispatch_officer  — send a trusted officer to counter the rumour
      pay_arrears       — clear arrears to counter 'we_are_abandoned'
      rest_idle         — order rest to reduce idle-time rumour pressure
      break_up          — disband the cohort before it infects neighbours
      small_victory     — seed 'follow_a_winner' with an easy win
    """
    if not sentiment_summary:
        return

    io.print()
    io.print("  SENTIMENT FIELD:")
    can_see_true = station_authority >= 0.70

    for row in sentiment_summary:
        cid = row['cohort_id']
        auth = row.get('authority', 0.5)
        flipped = row.get('flipped', [])

        # Build sentiment line per known sentiment id
        sent_parts = []
        for sid, penetration in [(k, v) for k, v in row.items()
                                 if k not in ('cohort_id', 'authority', 'flipped')
                                 and isinstance(v, float)]:
            if can_see_true or auth >= 0.70:
                glyph, glabel = _sentiment_glyph(penetration)
                sent_parts.append(f"{sid}: {glyph}({penetration:.0%})")
            else:
                sent_parts.append(f"{sid}: ?  [officer absent — mood unknown]")

        sent_str = '  '.join(sent_parts) if sent_parts else 'no active sentiments'

        flip_str = f"  [MEANING FLIPPED: {', '.join(flipped)}]" if flipped else ''
        io.print(f"    Cohort {cid}  auth={auth:.0%}  {sent_str}{flip_str}")

    # Intervention levers
    io.print()
    io.print("  SENTIMENT LEVERS (issue as in-flight orders via the M7.A queue):")
    io.print("    dispatch_officer  — send a trusted officer to counter a rumour")
    io.print("    pay_arrears       — clear pay arrears (counters 'we_are_abandoned')")
    io.print("    rest_idle         — order rest to reduce rumour-mill pressure")
    io.print("    small_victory     — seed 'follow_a_winner' with an easy engagement")
    io.print("    break_up          — disband a cohort before it infects neighbours")
    io.print()


# ------------------------------------------------------------------
# Standalone summary for use in audit / court scenes

def summarise_station(station_state: StationState) -> str:
    """One-line summary of current station for display in court / audit text."""
    spec = STATIONS[station_state.station]
    return (
        f"{spec.label} "
        f"(latency {spec.latency_days}d, lottery {spec.lottery_per_day:.1%}/day)"
    )
