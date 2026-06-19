"""Tests for UX-02: phase-bar glyph updates after battle dispatch."""
from core.belief_db import BeliefDB
from core.stations import Station, STATIONS, StationState
from clients.cli.table import render_table, _build_campaign_line, _confidence_glyph
from clients.cli.tutorial import _MockIO


# ------------------------------------------------------------------
# UX-02: phase bar reflects dispatched battle


def test_ux02_phase_bar_updates_after_battle_dispatch():
    """Phase bar must show a non-space glyph for AGINCOURT after a confirmed battle dispatch."""
    db = BeliefDB()
    db.receive_dispatch('battle', {'won': True, 'casualties': 400}, confidence=0.90)

    station_state = StationState(station=Station.CAMP)
    io = _MockIO([])
    render_table(day=53, station_state=station_state,
                 belief_db=db, pending_orders=[], io=io)

    campaign_line = next(
        (l for l in io.lines if 'HARFLEUR' in l and 'AGINCOURT' in l), None
    )
    assert campaign_line is not None, "Campaign line must be rendered"
    assert '[*]AGINCOURT' in campaign_line or \
           '[~]AGINCOURT' in campaign_line or \
           '[?]AGINCOURT' in campaign_line, (
        f"AGINCOURT bracket must show a glyph after dispatch, got: {campaign_line!r}"
    )


def test_ux02_phase_bar_empty_without_dispatch():
    """Phase bar must show [ ]AGINCOURT when no battle dispatch has been sent."""
    db = BeliefDB()
    station_state = StationState(station=Station.CAMP)
    io = _MockIO([])
    render_table(day=1, station_state=station_state,
                 belief_db=db, pending_orders=[], io=io)

    campaign_line = next(
        (l for l in io.lines if 'HARFLEUR' in l and 'AGINCOURT' in l), None
    )
    assert campaign_line is not None, "Campaign line must be rendered even without dispatches"
    assert '[ ]AGINCOURT' in campaign_line, (
        f"AGINCOURT bracket must be empty without dispatch, got: {campaign_line!r}"
    )


def test_ux02_all_three_phases_reflect_dispatches():
    """All three phase brackets update when siege, march, and battle dispatches arrive."""
    db = BeliefDB()
    db.receive_dispatch('siege',  {'outcome': 'NEGOTIATED', 'day': 29},  confidence=0.90)
    db.receive_dispatch('march',  {'arrived': True, 'day': 16},           confidence=0.90)
    db.receive_dispatch('battle', {'won': True, 'casualties': 112},       confidence=0.90)

    station_state = StationState(station=Station.CAMP)
    io = _MockIO([])
    render_table(day=53, station_state=station_state,
                 belief_db=db, pending_orders=[], io=io)

    campaign_line = next(
        (l for l in io.lines if 'HARFLEUR' in l and 'AGINCOURT' in l), None
    )
    assert campaign_line is not None
    assert '[*]HARFLEUR' in campaign_line, "Siege glyph must be * at 90% confidence"
    assert '[*]AGINCOURT' in campaign_line, "Battle glyph must be * at 90% confidence"


def test_ux02_partial_dispatch_shows_lower_confidence_glyph():
    """A 70% confidence dispatch must yield ~ not * in the phase bar."""
    db = BeliefDB()
    db.receive_dispatch('battle', {'won': True}, confidence=0.70)

    station_state = StationState(station=Station.CAMP)
    io = _MockIO([])
    render_table(day=53, station_state=station_state,
                 belief_db=db, pending_orders=[], io=io)

    campaign_line = next(
        (l for l in io.lines if 'HARFLEUR' in l and 'AGINCOURT' in l), None
    )
    assert campaign_line is not None
    assert '[~]AGINCOURT' in campaign_line, (
        f"70% confidence dispatch must yield ~ glyph, got: {campaign_line!r}"
    )


def test_ux02_camp_cannot_see_sightlines_source():
    """CAMP station must not see claims from sightlines source (no eye without body)."""
    db = BeliefDB()
    db.observe('battle', {'won': True}, source='sightlines')

    station_state = StationState(station=Station.CAMP)
    io = _MockIO([])
    render_table(day=53, station_state=station_state,
                 belief_db=db, pending_orders=[], io=io)

    campaign_line = next(
        (l for l in io.lines if 'HARFLEUR' in l and 'AGINCOURT' in l), None
    )
    assert campaign_line is not None
    # CAMP cannot see sightlines — battle bracket must remain empty
    assert '[ ]AGINCOURT' in campaign_line, (
        f"CAMP must not see sightlines-source claims, got: {campaign_line!r}"
    )
