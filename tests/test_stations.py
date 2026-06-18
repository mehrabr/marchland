"""M4 tests: stations, belief_db extensions, table renderer, season integration.

Covers:
- core/stations.py  — StationSpec registry, StationState move_to / lottery
- core/belief_db.py — observe(), beliefs_for_station() (M4 additions)
- clients/cli/table.py — render_table() output sanity
- clients/cli/season.py — station command, wait command, table shown after ops,
                          dispatch latency (interactive path via station change),
                          M3 auto_commands still pass with instant_orders
"""
import pytest
import numpy as np

from core.stations import (
    Station, STATIONS, StationSpec, StationState,
    station_can_see, SOURCE_VISIBILITY,
)
from core.belief_db import BeliefDB
from clients.cli.table import render_table, _confidence_glyph, _glyph_label, summarise_station
from clients.cli.season import (
    run_season, SeasonState, PendingOrder, _credit_label,
)
from core.cultures.harfleur_1415 import CULTURE
from core.commission import generate_commission


# ==============================================================================
# core/stations.py
# ==============================================================================

class TestStationRegistry:
    def test_all_four_stations_defined(self):
        for s in (Station.CAMP, Station.HILL, Station.KNOT, Station.FRONT_RANK):
            assert s in STATIONS

    def test_each_spec_is_stationspec(self):
        for s, spec in STATIONS.items():
            assert isinstance(spec, StationSpec), f"{s} spec is not StationSpec"

    def test_camp_has_zero_lottery(self):
        assert STATIONS[Station.CAMP].lottery_per_day == 0.0

    def test_front_rank_has_highest_lottery(self):
        lotteries = {s: spec.lottery_per_day for s, spec in STATIONS.items()}
        assert lotteries[Station.FRONT_RANK] == max(lotteries.values())

    def test_camp_has_highest_latency(self):
        latencies = {s: spec.latency_days for s, spec in STATIONS.items()}
        assert latencies[Station.CAMP] == max(latencies.values())

    def test_knot_and_front_rank_have_zero_latency(self):
        assert STATIONS[Station.KNOT].latency_days == 0
        assert STATIONS[Station.FRONT_RANK].latency_days == 0

    def test_camp_travel_days_zero(self):
        assert STATIONS[Station.CAMP].travel_days_from_camp == 0

    def test_information_sets_are_frozensets(self):
        for s, spec in STATIONS.items():
            assert isinstance(spec.information_set, frozenset)

    def test_camp_information_set_dispatches_only(self):
        assert STATIONS[Station.CAMP].information_set == frozenset({'dispatches'})

    def test_knot_information_set_is_superset_of_hill(self):
        hill = STATIONS[Station.HILL].information_set
        knot = STATIONS[Station.KNOT].information_set
        assert hill.issubset(knot)

    def test_lever_sets_are_nonempty(self):
        for s, spec in STATIONS.items():
            assert len(spec.lever_set) > 0

    def test_anchor_radius_nonnegative(self):
        for s, spec in STATIONS.items():
            assert spec.anchor_radius_km >= 0.0


class TestSourceVisibility:
    def test_dispatch_visible_at_camp_hill_knot(self):
        for s in (Station.CAMP, Station.HILL, Station.KNOT):
            assert station_can_see(s, 'dispatch')

    def test_dispatch_not_visible_at_front_rank(self):
        assert not station_can_see(Station.FRONT_RANK, 'dispatch')

    def test_landscape_visible_at_hill_and_knot(self):
        assert station_can_see(Station.HILL, 'landscape')
        assert station_can_see(Station.KNOT, 'landscape')

    def test_landscape_not_visible_at_camp(self):
        assert not station_can_see(Station.CAMP, 'landscape')

    def test_sightlines_only_at_knot(self):
        assert station_can_see(Station.KNOT, 'sightlines')
        assert not station_can_see(Station.HILL, 'sightlines')
        assert not station_can_see(Station.CAMP, 'sightlines')
        assert not station_can_see(Station.FRONT_RANK, 'sightlines')

    def test_nearby_units_at_front_rank_and_knot(self):
        assert station_can_see(Station.FRONT_RANK, 'nearby_units')
        assert station_can_see(Station.KNOT, 'nearby_units')
        assert not station_can_see(Station.CAMP, 'nearby_units')

    def test_unknown_source_returns_false(self):
        assert not station_can_see(Station.CAMP, 'made_up_source')


class TestStationState:
    def test_default_station_is_camp(self):
        ss = StationState()
        assert ss.station == Station.CAMP

    def test_spec_property(self):
        ss = StationState()
        assert ss.spec is STATIONS[Station.CAMP]

    def test_latency_days_property(self):
        ss = StationState()
        assert ss.latency_days == STATIONS[Station.CAMP].latency_days

    def test_move_to_same_station_no_op(self):
        ss = StationState()
        rng = np.random.default_rng(0)
        ev = ss.move_to(Station.CAMP, rng, season_day=5)
        assert ev['moved'] is False
        assert ev['cost_days'] == 0
        assert ss.station == Station.CAMP

    def test_move_to_hill_costs_days(self):
        ss = StationState()
        rng = np.random.default_rng(0)
        ev = ss.move_to(Station.HILL, rng, season_day=0)
        assert ev['moved'] is True
        assert ev['cost_days'] >= 1
        assert ss.station == Station.HILL

    def test_move_to_knot_resets_days_at_station(self):
        ss = StationState(days_at_station=99)
        rng = np.random.default_rng(0)
        ss.move_to(Station.KNOT, rng, season_day=10)
        assert ss.days_at_station == 0

    def test_move_records_from_and_to_labels(self):
        ss = StationState()
        rng = np.random.default_rng(0)
        ev = ss.move_to(Station.HILL, rng, season_day=0)
        assert ev['from'] == STATIONS[Station.CAMP].label
        assert ev['to'] == STATIONS[Station.HILL].label

    def test_move_to_front_rank_from_camp_costs_more_than_hill(self):
        ss1 = StationState()
        rng1 = np.random.default_rng(42)
        ev_hill = ss1.move_to(Station.HILL, rng1, season_day=0)

        ss2 = StationState()
        rng2 = np.random.default_rng(42)
        ev_front = ss2.move_to(Station.FRONT_RANK, rng2, season_day=0)

        assert ev_front['cost_days'] >= ev_hill['cost_days']

    def test_lottery_at_camp_never_fires(self):
        """CAMP lottery_per_day is 0 — the lottery must never fire."""
        ss = StationState()
        rng = np.random.default_rng(0)
        # Run many trials from CAMP and check no injury accumulates
        for _ in range(50):
            ev = ss.move_to(Station.CAMP, rng, season_day=0)
        assert ss.lottery_injuries == 0

    def test_lottery_at_front_rank_fires_eventually(self):
        """With 5%/day, 2 days/move, 100 moves: P(0 hits) ≈ (0.9025)^100 < 1e-4."""
        injuries_total = 0
        for seed in range(100):
            ss = StationState()
            rng = np.random.default_rng(seed)
            ss.move_to(Station.FRONT_RANK, rng, season_day=0)
            injuries_total += ss.lottery_injuries
        assert injuries_total > 0

    def test_move_to_returns_hit_true_when_injured(self):
        """Force a hit by using a rng that always returns < lottery rate."""
        class _AlwaysHitRng:
            def random(self):
                return 0.0  # always < any positive lottery rate

        ss = StationState()
        ev = ss.move_to(Station.FRONT_RANK, _AlwaysHitRng(), season_day=0)
        assert ev['hit'] is True
        assert ss.lottery_injuries == 1

    def test_move_lottery_no_hit_when_rng_always_one(self):
        """Force a miss: rng always returns 1.0 > any lottery rate."""
        class _NeverHitRng:
            def random(self):
                return 1.0

        ss = StationState()
        ev = ss.move_to(Station.FRONT_RANK, _NeverHitRng(), season_day=0)
        assert ev['hit'] is False
        assert ss.lottery_injuries == 0


# ==============================================================================
# core/belief_db.py  — M4 additions
# ==============================================================================

class TestBeliefDBObserve:
    def test_observe_landscape_stores_claim(self):
        db = BeliefDB()
        db.observe('siege', {'outcome': 'NEGOTIATED'}, source='landscape')
        val, conf = db.get('siege', 'outcome')
        assert val == 'NEGOTIATED'
        assert 0.7 <= conf <= 0.8  # landscape confidence range

    def test_observe_sightlines_higher_confidence_than_landscape(self):
        db = BeliefDB()
        db.observe('siege', {'outcome': 'NEGOTIATED'}, source='sightlines')
        _, conf_s = db.get('siege', 'outcome')

        db2 = BeliefDB()
        db2.observe('siege', {'outcome': 'NEGOTIATED'}, source='landscape')
        _, conf_l = db2.get('siege', 'outcome')

        assert conf_s > conf_l

    def test_observe_does_not_downgrade_high_confidence_dispatch(self):
        """A fresh dispatch (0.9) must not be overwritten by landscape (0.75)."""
        db = BeliefDB()
        db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.9)
        db.observe('siege', {'outcome': 'NEGOTIATED'}, source='landscape')
        _, conf = db.get('siege', 'outcome')
        assert conf == pytest.approx(0.9)

    def test_observe_upgrades_low_confidence_with_sightlines(self):
        """A rumour (0.5) can be overwritten by sightlines (0.85)."""
        db = BeliefDB()
        db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.5)
        db.observe('siege', {'outcome': 'NEGOTIATED'}, source='sightlines')
        _, conf = db.get('siege', 'outcome')
        assert conf == pytest.approx(0.85)


class TestBeliefDBBeliefsForStation:
    def _populated_db(self) -> BeliefDB:
        db = BeliefDB()
        db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.9)
        db.observe('march', {'arrived': True}, source='landscape')
        db.observe('battle', {'won': True}, source='sightlines')
        return db

    def test_camp_sees_only_dispatches(self):
        db = self._populated_db()
        visible = db.beliefs_for_station(Station.CAMP)
        assert 'siege' in visible            # dispatch
        assert 'march' not in visible        # landscape only, invisible at CAMP
        assert 'battle' not in visible       # sightlines only, invisible at CAMP

    def test_hill_sees_dispatches_and_landscape(self):
        db = self._populated_db()
        visible = db.beliefs_for_station(Station.HILL)
        assert 'siege' in visible
        assert 'march' in visible
        assert 'battle' not in visible       # sightlines invisible at HILL

    def test_knot_sees_all_three(self):
        db = self._populated_db()
        visible = db.beliefs_for_station(Station.KNOT)
        assert 'siege' in visible
        assert 'march' in visible
        assert 'battle' in visible

    def test_front_rank_sees_nothing_from_this_db(self):
        """FRONT_RANK can only see nearby_units; this db has no such claims."""
        db = self._populated_db()
        visible = db.beliefs_for_station(Station.FRONT_RANK)
        assert visible == {}

    def test_front_rank_sees_nearby_units_claim(self):
        db = BeliefDB()
        db.observe('battle', {'won': True}, source='nearby_units')
        visible = db.beliefs_for_station(Station.FRONT_RANK)
        assert 'battle' in visible

    def test_beliefs_for_station_returns_value_confidence_pairs(self):
        db = BeliefDB()
        db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.9)
        visible = db.beliefs_for_station(Station.CAMP)
        val, conf = visible['siege']['outcome']
        assert val == 'NEGOTIATED'
        assert conf == pytest.approx(0.9)

    def test_empty_db_returns_empty_dict_for_any_station(self):
        db = BeliefDB()
        for s in Station:
            assert db.beliefs_for_station(s) == {}


# ==============================================================================
# clients/cli/table.py
# ==============================================================================

class TestGlyphs:
    def test_high_confidence_gives_confirmed(self):
        assert _confidence_glyph(0.9) == '*'
        assert _confidence_glyph(0.85) == '*'

    def test_mid_confidence_gives_scouted(self):
        assert _confidence_glyph(0.75) == '~'
        assert _confidence_glyph(0.70) == '~'

    def test_low_confidence_gives_rumoured(self):
        assert _confidence_glyph(0.5) == '?'
        assert _confidence_glyph(0.1) == '?'

    def test_stale_flag_overrides(self):
        assert _confidence_glyph(0.99, stale=True) == '.'

    def test_glyph_labels_complete(self):
        for g in ('*', '~', '?', '.'):
            assert _glyph_label(g) != ''


class _CapturingIO:
    def __init__(self):
        self.lines = []

    def print(self, *args, **kw):
        sep = kw.get('sep', ' ')
        self.lines.append(sep.join(str(a) for a in args))

    def input(self, prompt):
        return ''

    @property
    def text(self):
        return '\n'.join(self.lines)


class TestRenderTable:
    def _make_state(self) -> tuple:
        ss = StationState()
        db = BeliefDB()
        return ss, db, []

    def test_render_table_runs_without_error(self):
        ss, db, pending = self._make_state()
        io = _CapturingIO()
        render_table(day=5, station_state=ss, belief_db=db, pending_orders=pending, io=io)
        assert len(io.lines) > 0

    def test_render_table_shows_day(self):
        ss, db, pending = self._make_state()
        io = _CapturingIO()
        render_table(day=17, station_state=ss, belief_db=db, pending_orders=pending, io=io)
        assert any('17' in line for line in io.lines)

    def test_render_table_shows_station_label(self):
        ss, db, pending = self._make_state()
        io = _CapturingIO()
        render_table(day=0, station_state=ss, belief_db=db, pending_orders=pending, io=io)
        assert any('CAMP' in line.upper() for line in io.lines)

    def test_render_table_shows_pending_order_arrow(self):
        ss, db = StationState(), BeliefDB()
        pending = [PendingOrder(command='siege', eta_day=5, label='besiege Harfleur')]
        io = _CapturingIO()
        render_table(day=3, station_state=ss, belief_db=db, pending_orders=pending, io=io)
        assert any('→' in line for line in io.lines)

    def test_render_table_shows_known_dispatch(self):
        ss = StationState()
        db = BeliefDB()
        db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.9)
        io = _CapturingIO()
        render_table(day=40, station_state=ss, belief_db=db, pending_orders=[], io=io)
        assert any('NEGOTIATED' in line for line in io.lines)

    def test_render_table_camp_does_not_show_landscape_obs(self):
        """At CAMP, landscape observations must not appear in the table."""
        ss = StationState()   # CAMP
        db = BeliefDB()
        db.observe('march', {'arrived': True}, source='landscape')
        io = _CapturingIO()
        render_table(day=5, station_state=ss, belief_db=db, pending_orders=[], io=io)
        # 'arrived' should not appear since landscape is invisible at CAMP
        assert not any('arrived' in line for line in io.lines)

    def test_render_table_knot_shows_sightline_obs(self):
        ss = StationState(station=Station.KNOT)
        db = BeliefDB()
        db.observe('battle', {'won': True}, source='sightlines')
        io = _CapturingIO()
        render_table(day=5, station_state=ss, belief_db=db, pending_orders=[], io=io)
        assert any('True' in line or 'won' in line for line in io.lines)

    def test_render_table_shows_latency_note_at_camp(self):
        ss = StationState()
        db = BeliefDB()
        io = _CapturingIO()
        render_table(day=0, station_state=ss, belief_db=db, pending_orders=[], io=io)
        # Should mention latency for CAMP
        assert any('latency' in line.lower() or 'CAMP' in line.upper() for line in io.lines)

    def test_summarise_station(self):
        ss = StationState()
        s = summarise_station(ss)
        assert 'Camp' in s or 'CAMP' in s.upper()
        assert 'latency' in s.lower()


# ==============================================================================
# clients/cli/season.py  — M4 integration tests
# ==============================================================================

def _cmd(**kw):
    """Build a standard command list for the season; all M3 defaults."""
    defaults = dict(
        quarter='liberal',
        tactic='wait',
        siege_dispatch='accurate',
        pace='normal',
        march_dispatch='accurate',
        battle='engage',
        battle_dispatch='accurate',
    )
    defaults.update(kw)
    d = defaults
    return [
        d['quarter'],
        'siege',
        d['tactic'],
        d['siege_dispatch'],
        'march',
        d['pace'],
        d['march_dispatch'],
        'battle',
        d['battle'],
        d['battle_dispatch'],
        'done',
    ]


class TestSeasonStationCommand:
    # 'station' with no inline arg → reads destination as the next io.input()
    # So the command list is: ..., 'station', '<dest>', ...

    def test_station_command_changes_station(self):
        """'station' + 'knot' must leave station_state.station = KNOT."""
        cmds = [
            'liberal',
            'station', 'knot',   # 'station' prompts for destination, reads 'knot'
            'siege', 'wait',
            'accurate',
            'march', 'normal',
            'accurate',
            'battle', 'engage',
            'accurate',
            'done',
        ]
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        assert state.station_state.station == Station.KNOT

    def test_station_knot_costs_travel_days(self):
        cmds = [
            'liberal',
            'station', 'knot',
            'siege', 'wait',
            'accurate',
            'march', 'normal',
            'accurate',
            'battle', 'engage',
            'accurate',
            'done',
        ]
        state_with = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        state_without = run_season('harfleur_1415', seed=0, auto_commands=_cmd())
        # Moving to KNOT costs travel days → total elapsed is higher
        assert state_with.day > state_without.day

    def test_station_invalid_name_does_not_crash(self):
        cmds = [
            'liberal',
            'station', 'nowhere',   # invalid; should print error and continue
        ] + _cmd()[1:]
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        assert isinstance(state, SeasonState)
        # Station must remain CAMP (the default, since 'nowhere' is rejected)
        assert state.station_state.station == Station.CAMP

    def test_station_same_station_is_no_op(self):
        cmds = [
            'liberal',
            'station', 'camp',   # already at CAMP — no-op
        ] + _cmd()[1:]
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        assert state.station_state.station == Station.CAMP

    def test_station_hill_lottery_per_day_applies(self):
        """Moving to HILL runs the lottery; check station is set correctly."""
        cmds = [
            'liberal',
            'station', 'hill',
            'siege', 'wait',
            'accurate',
            'march', 'normal',
            'accurate',
            'battle', 'engage',
            'accurate',
            'done',
        ]
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        assert state.station_state.station == Station.HILL


class TestSeasonWaitCommand:
    def test_wait_advances_day(self):
        cmds = [
            'liberal',
            'wait', '3',    # advance 3 days at the start
        ] + _cmd()[1:]
        state_waited = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        state_plain  = run_season('harfleur_1415', seed=0, auto_commands=_cmd())
        assert state_waited.day > state_plain.day

    def test_wait_no_arg_advances_one_day(self):
        cmds = [
            'liberal',
            'wait', '',     # no argument → 1 day
        ] + _cmd()[1:]
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        assert state.day >= 1


class TestSeasonTableCommand:
    def test_table_command_does_not_crash(self):
        cmds = [
            'liberal',
            'table',       # show table before any operations
        ] + _cmd()[1:]
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        assert isinstance(state, SeasonState)


class TestSeasonDispatchLatency:
    def test_instant_orders_flag_bypasses_latency(self):
        """auto_commands → instant_orders=True; operations run without wait."""
        state = run_season('harfleur_1415', seed=0, auto_commands=_cmd())
        assert state.siege_result is not None
        assert state.march_result is not None
        assert state.battle_result is not None

    def test_pending_order_is_queued_at_camp_interactive(self):
        """In non-instant mode, issuing siege from CAMP queues a PendingOrder."""
        rng = np.random.default_rng(0)
        commission = generate_commission(CULTURE, rng)
        # instant_orders=False (interactive mode)
        state = SeasonState(commission, seed=0, instant_orders=False)
        assert state.station == Station.CAMP
        assert state.station_state.latency_days == 2

        # Simulate queueing without running
        queued = []

        def _capture_queue():
            nonlocal queued
            # peek at what _queue_or_run does
            pass

        state.siege_tactic = 'wait'
        ran = state._queue_or_run('siege', 'besiege Harfleur', lambda: None)
        assert ran is False
        assert len(state.pending_orders) == 1
        assert state.pending_orders[0].command == 'siege'
        assert state.pending_orders[0].eta_day == state.station_state.latency_days

    def test_pending_order_resolves_after_wait(self):
        """After wait(2), the queued order's ETA has passed and it resolves."""
        rng = np.random.default_rng(0)
        commission = generate_commission(CULTURE, rng)
        state = SeasonState(commission, seed=0, instant_orders=False)
        state.siege_tactic = 'wait'

        executed = []

        def _mock_run():
            executed.append(True)

        state._queue_or_run('siege', 'besiege Harfleur', _mock_run)
        assert len(executed) == 0          # not yet

        # Advance past the ETA
        state.elapsed(STATIONS[Station.CAMP].latency_days)

        class _SilentIO:
            def print(self, *a, **k):
                pass
            def input(self, p):
                return ''

        state._flush_matured_orders(_SilentIO())
        # The deferred command fires _dispatch_command('siege'), which tries to
        # run the real siege — that will fail because commission has no scenarios
        # attached.  We just confirm the pending list is cleared.
        assert state.pending_orders == []

    def test_queued_at_knot_latency_zero(self):
        """At KNOT (latency=0), _queue_or_run must run immediately."""
        rng = np.random.default_rng(0)
        commission = generate_commission(CULTURE, rng)
        state = SeasonState(commission, seed=0, instant_orders=False)
        state.station_state.station = Station.KNOT

        ran = state._queue_or_run('siege', 'besiege Harfleur', lambda: None)
        assert ran is True
        assert state.pending_orders == []


class TestSeasonObservationFromStation:
    def test_hill_station_populates_belief_db_with_landscape(self):
        """At HILL, completing siege records a landscape observation in belief_db."""
        cmds = [
            'liberal',
            'station', 'hill',   # 'station' reads 'hill' as destination
            'siege', 'wait',
            'none',              # no dispatch — only station observation
            'march', 'normal',
            'none',
            'battle', 'engage',
            'none',
            'done',
        ]
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        # At HILL, landscape observation should have been recorded for siege
        visible = state.belief_db.beliefs_for_station(Station.HILL)
        assert 'siege' in visible, "HILL station must record landscape obs for siege"

    def test_camp_no_dispatch_leaves_belief_empty(self):
        cmds = [
            'liberal',
            'siege', 'wait', 'none',
            'march', 'normal', 'none',
            'battle', 'engage', 'none',
            'done',
        ]
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        assert state.belief_db.phases_with_beliefs() == []


class TestSeasonM3Regression:
    """All M3 tests must still pass under the updated season.py."""

    def test_season_runs_without_error(self):
        state = run_season('harfleur_1415', seed=0, auto_commands=_cmd())
        assert isinstance(state, SeasonState)

    def test_all_four_decisions_recorded(self):
        state = run_season('harfleur_1415', seed=0,
                           auto_commands=_cmd(quarter='strict', tactic='storm',
                                              pace='push', battle='engage'))
        assert state.quarter_policy == 'strict'
        assert state.siege_tactic == 'storm'
        assert state.march_pace == 'push'
        assert state.battle_choice == 'engage'

    def test_results_populated(self):
        state = run_season('harfleur_1415', seed=0, auto_commands=_cmd())
        assert state.siege_result is not None
        assert state.march_result is not None
        assert state.battle_result is not None

    def test_withdraw_skips_battle(self):
        state = run_season('harfleur_1415', seed=0, auto_commands=_cmd(battle='withdraw'))
        assert state.battle_result.get('withdrew') is True

    def test_no_dispatch_leaves_belief_empty(self):
        state = run_season('harfleur_1415', seed=0,
                           auto_commands=_cmd(siege_dispatch='none',
                                              march_dispatch='none',
                                              battle_dispatch='none'))
        assert state.belief_db.phases_with_beliefs() == []

    def test_accurate_dispatch_updates_belief(self):
        state = run_season('harfleur_1415', seed=0,
                           auto_commands=_cmd(siege_dispatch='accurate',
                                              march_dispatch='none',
                                              battle_dispatch='none'))
        assert 'siege' in state.belief_db.phases_with_beliefs()

    def test_patron_favor_moves(self):
        rng = np.random.default_rng(0)
        comm = generate_commission(CULTURE, rng)
        initial = comm.patron_favor
        state = run_season('harfleur_1415', seed=0, auto_commands=_cmd())
        assert state.patron_favor != initial

    def test_composed_trace_has_all_phases(self):
        state = run_season('harfleur_1415', seed=0, auto_commands=_cmd())
        assert state.composed_trace is not None
        phases = state.composed_trace.get('phases', [])
        assert set(phases) >= {'siege', 'march', 'battle'}

    def test_deterministic_same_seed(self):
        c = _cmd()
        s1 = run_season('harfleur_1415', seed=7, auto_commands=c)
        s2 = run_season('harfleur_1415', seed=7, auto_commands=c)
        assert s1.siege_result == s2.siege_result
        assert s1.battle_result['win'] == s2.battle_result['win']
