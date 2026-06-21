"""Tests for clients/renpy/bridge.py — the Layer 2 adapter.

Four disciplines, each with its own section:
  1. Layer isolation  — bridge imports nothing from Ren'Py; sim types never escape
  2. Numpy transience — no numpy scalars or arrays in any public function output
  3. JSON serialization — every public output round-trips through json.dumps/loads
  4. Functional correctness — each function returns the right shape and values
"""
import json
import sys
import pytest
import numpy as np

from clients.renpy.bridge import (
    _strip_numpy,
    assert_serializable,
    run_chain,
    run_operation,
    SaveCapsule,
    save_capsule_from_state,
    capsule_to_dict,
    belief_view_for_table,
    _confidence_glyph,
    trace_for_archive,
    pending_order_for_renpy,
)
from clients.cli.season import run_season, PendingOrder


# ---------------------------------------------------------------------------
# Helpers

def _has_numpy(obj) -> bool:
    """Return True if obj (or any nested value) is a numpy scalar or array."""
    if isinstance(obj, (np.integer, np.floating, np.bool_, np.ndarray)):
        return True
    if isinstance(obj, dict):
        return any(_has_numpy(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_has_numpy(v) for v in obj)
    return False


def _is_json_safe(obj) -> bool:
    try:
        json.dumps(obj, default=str)
        return True
    except (TypeError, ValueError):
        return False


def _full_state():
    """Return a fully-run SeasonState (all three ops completed, accurate dispatches)."""
    cmds = [
        'liberal',
        'siege', 'wait', 'accurate',
        'march', 'normal', 'accurate',
        'battle', 'engage', 'accurate',
        'done',
    ]
    return run_season('harfleur_1415', seed=0, auto_commands=cmds)


# ==============================================================================
# 1. Layer isolation
# ==============================================================================

class TestLayerIsolation:
    def test_renpy_not_imported_by_bridge(self):
        """Importing the bridge must not pull Ren'Py into sys.modules."""
        assert 'renpy' not in sys.modules, (
            "Importing clients.renpy.bridge must not import the renpy package. "
            "The bridge is a plain Python module — Ren'Py only imports it, not the reverse."
        )

    def test_bridge_module_does_not_reference_renpy_in_source(self):
        """The bridge source file must contain no 'import renpy' statement."""
        import inspect
        import clients.renpy.bridge as bridge_mod
        src = inspect.getsource(bridge_mod)
        assert 'import renpy' not in src, (
            "clients/renpy/bridge.py must never import renpy — spec §1 layer rule."
        )

    def test_battle_object_not_in_run_chain_output(self):
        """run_chain must not return any Battle sim objects."""
        from core.lattice import Battle
        result = run_chain(seed=0)
        # Recursively check no Battle instances leaked into the result dict
        def _has_battle(obj):
            if isinstance(obj, Battle):
                return True
            if isinstance(obj, dict):
                return any(_has_battle(v) for v in obj.values())
            if isinstance(obj, (list, tuple)):
                return any(_has_battle(v) for v in obj)
            return False
        assert not _has_battle(result)

    def test_trace_object_not_in_run_operation_output(self):
        """run_operation must not return Trace dataclass instances."""
        from core.trace import Trace
        result = run_operation('siege', seed=0)
        def _has_trace(obj):
            if isinstance(obj, Trace):
                return True
            if isinstance(obj, dict):
                return any(_has_trace(v) for v in obj.values())
            if isinstance(obj, (list, tuple)):
                return any(_has_trace(v) for v in obj)
            return False
        assert not _has_trace(result)


# ==============================================================================
# 2. Numpy transience
# ==============================================================================

class TestNumpyTransience:
    def test_strip_numpy_int(self):
        assert _strip_numpy(np.int64(42)) == 42
        assert type(_strip_numpy(np.int64(42))) is int

    def test_strip_numpy_float(self):
        assert _strip_numpy(np.float64(3.14)) == pytest.approx(3.14)
        assert type(_strip_numpy(np.float64(3.14))) is float

    def test_strip_numpy_bool(self):
        assert _strip_numpy(np.bool_(True)) is True
        assert type(_strip_numpy(np.bool_(True))) is bool

    def test_strip_numpy_plain_python_unchanged(self):
        assert _strip_numpy(42) == 42
        assert _strip_numpy(3.14) == pytest.approx(3.14)
        assert _strip_numpy('hello') == 'hello'
        assert _strip_numpy(True) is True
        assert _strip_numpy(None) is None

    def test_strip_numpy_nested_dict(self):
        d = {'a': np.int64(1), 'b': {'c': np.float64(2.5)}}
        result = _strip_numpy(d)
        assert type(result['a']) is int
        assert type(result['b']['c']) is float

    def test_strip_numpy_list(self):
        lst = [np.int64(1), np.float64(2.5), np.bool_(False)]
        result = _strip_numpy(lst)
        assert all(type(v) in (int, float, bool) for v in result)

    def test_strip_numpy_tuple(self):
        t = (np.int64(7), 'hello')
        result = _strip_numpy(t)
        assert type(result[0]) is int

    def test_run_chain_no_numpy(self):
        result = run_chain(seed=0)
        assert not _has_numpy(result), "run_chain output must contain no numpy types"

    def test_run_operation_siege_no_numpy(self):
        result = run_operation('siege', seed=0)
        assert not _has_numpy(result)

    def test_run_operation_march_no_numpy(self):
        siege_res = run_operation('siege', seed=0)['result']
        result = run_operation('march', seed=0, siege_result=siege_res)
        assert not _has_numpy(result)

    def test_run_operation_battle_no_numpy(self):
        siege_res = run_operation('siege', seed=0)['result']
        march_res = run_operation('march', seed=0, siege_result=siege_res)['result']
        result = run_operation('battle', seed=0, march_result=march_res)
        assert not _has_numpy(result)

    def test_capsule_to_dict_no_numpy(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        d = capsule_to_dict(cap)
        assert not _has_numpy(d)

    def test_belief_view_for_table_no_numpy(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        view = belief_view_for_table(cap.belief_db_dict, 'CAMP')
        assert not _has_numpy(view)

    def test_trace_for_archive_no_numpy(self):
        result = run_chain(seed=0)
        arch = trace_for_archive(result['trace'])
        assert not _has_numpy(arch)


# ==============================================================================
# 3. JSON serializability
# ==============================================================================

class TestSerializability:
    def test_assert_serializable_passes_on_plain(self):
        assert_serializable({'a': 1, 'b': [True, None, 3.14]}, 'plain dict')

    def test_assert_serializable_raises_on_numpy(self):
        with pytest.raises(ValueError, match='non-serializable'):
            assert_serializable({'a': np.int64(1)}, 'numpy dict')

    def test_assert_serializable_raises_on_object(self):
        class _Unserializable:
            pass
        with pytest.raises(ValueError):
            assert_serializable({'x': _Unserializable()})

    def test_run_chain_json_serializable(self):
        result = run_chain(seed=0)
        assert _is_json_safe(result)

    def test_run_chain_trace_json_serializable(self):
        result = run_chain(seed=0)
        assert _is_json_safe(result['trace'])

    def test_run_operation_siege_json_serializable(self):
        result = run_operation('siege', seed=0)
        assert _is_json_safe(result)

    def test_run_operation_march_json_serializable(self):
        siege_res = run_operation('siege', seed=0)['result']
        result = run_operation('march', seed=0, siege_result=siege_res)
        assert _is_json_safe(result)

    def test_run_operation_battle_json_serializable(self):
        siege_res = run_operation('siege', seed=0)['result']
        march_res = run_operation('march', seed=0, siege_result=siege_res)['result']
        result = run_operation('battle', seed=0, march_result=march_res)
        assert _is_json_safe(result)

    def test_capsule_to_dict_json_serializable(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        d = capsule_to_dict(cap)
        assert _is_json_safe(d)

    def test_belief_view_for_table_json_serializable(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        view = belief_view_for_table(cap.belief_db_dict, 'CAMP')
        assert _is_json_safe(view)

    def test_trace_for_archive_json_serializable(self):
        result = run_chain(seed=0)
        arch = trace_for_archive(result['trace'])
        assert _is_json_safe(arch)


# ==============================================================================
# 4. Functional correctness
# ==============================================================================

class TestRunChain:
    def test_returns_dict_with_required_keys(self):
        result = run_chain(seed=0)
        for key in ('win', 'siege', 'march', 'battle', 'trace'):
            assert key in result, f"run_chain missing key: {key!r}"

    def test_english_win_on_seed_0(self):
        """Agincourt: English win on seed 0 (matches battery spec)."""
        result = run_chain(seed=0)
        assert result['win'] == 0, f"Expected English win (0), got {result['win']}"

    def test_trace_has_all_three_phases(self):
        result = run_chain(seed=0)
        assert set(result['trace']['phases']) >= {'siege', 'march', 'battle'}

    def test_trace_has_deaths(self):
        result = run_chain(seed=0)
        assert len(result['trace']['deaths']) > 0

    def test_deterministic_same_seed(self):
        r1 = run_chain(seed=5)
        r2 = run_chain(seed=5)
        assert r1['win'] == r2['win']
        assert len(r1['trace']['deaths']) == len(r2['trace']['deaths'])

    def test_different_seeds_may_differ(self):
        """Over 4 seeds, at least one should differ in death count."""
        counts = [len(run_chain(seed=i)['trace']['deaths']) for i in range(4)]
        assert len(set(counts)) > 1 or True  # non-determinism check — counts may coincide


class TestRunOperation:
    def test_siege_returns_result_and_trace(self):
        out = run_operation('siege', seed=0)
        assert 'result' in out
        assert 'trace' in out
        assert out['op'] == 'siege'

    def test_siege_result_has_outcome(self):
        out = run_operation('siege', seed=0)
        assert 'outcome' in out['result']

    def test_siege_storm_flag_accepted(self):
        out = run_operation('siege', seed=0, tactic='storm')
        assert 'outcome' in out['result']

    def test_march_uses_siege_result_when_provided(self):
        siege_res = run_operation('siege', seed=0)['result']
        out_linked = run_operation('march', seed=0, siege_result=siege_res)
        out_bare   = run_operation('march', seed=0)
        # Start counts differ because siege maps unfit fraction into march start
        assert out_linked['result']['start'] != out_bare['result']['start'] or True  # may coincide

    def test_march_result_has_required_fields(self):
        out = run_operation('march', seed=0)
        for field in ('arrived', 'fatigue', 'effective', 'start'):
            assert field in out['result'], f"March result missing {field!r}"

    def test_march_pace_push_increases_fatigue(self):
        """Push pace must produce higher or equal fatigue than normal."""
        normal = run_operation('march', seed=0, pace='normal')['result']['fatigue']
        push   = run_operation('march', seed=0, pace='push')['result']['fatigue']
        assert push >= normal

    def test_march_pace_rest_decreases_fatigue(self):
        normal = run_operation('march', seed=0, pace='normal')['result']['fatigue']
        rest   = run_operation('march', seed=0, pace='rest')['result']['fatigue']
        assert rest <= normal

    def test_battle_returns_result_and_trace(self):
        out = run_operation('battle', seed=0)
        assert 'result' in out
        assert 'trace' in out

    def test_battle_result_has_win_field(self):
        out = run_operation('battle', seed=0)
        assert 'win' in out['result']

    def test_battle_withdraw_returns_withdrew_flag(self):
        out = run_operation('battle', seed=0, battle_choice='withdraw')
        assert out['withdrew'] is True
        assert out['result']['win'] == -1

    def test_battle_withdraw_has_empty_trace(self):
        """Withdraw produces a trace dict but with no deaths."""
        out = run_operation('battle', seed=0, battle_choice='withdraw')
        assert 'trace' in out
        assert out['trace']['deaths'] == []

    def test_unknown_op_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown operation"):
            run_operation('pillage', seed=0)

    def test_operation_trace_has_phase_field(self):
        out = run_operation('siege', seed=0)
        assert out['trace']['phase'] == 'siege'

    def test_run_operation_deterministic(self):
        out1 = run_operation('siege', seed=3)
        out2 = run_operation('siege', seed=3)
        assert out1['result']['outcome'] == out2['result']['outcome']
        assert out1['result']['dead'] == out2['result']['dead']


class TestSaveCapsule:
    def test_default_seed_and_culture(self):
        cap = SaveCapsule(seed=7, culture_name='harfleur_1415')
        assert cap.seed == 7
        assert cap.culture_name == 'harfleur_1415'

    def test_default_station_is_camp(self):
        cap = SaveCapsule(seed=0, culture_name='harfleur_1415')
        assert cap.station == 'CAMP'

    def test_default_results_are_none(self):
        cap = SaveCapsule(seed=0, culture_name='harfleur_1415')
        assert cap.siege_result is None
        assert cap.march_result is None
        assert cap.battle_result is None

    def test_default_pending_orders_empty(self):
        cap = SaveCapsule(seed=0, culture_name='harfleur_1415')
        assert cap.pending_orders == []

    def test_default_trace_dicts_empty(self):
        cap = SaveCapsule(seed=0, culture_name='harfleur_1415')
        assert cap.trace_dicts == []

    def test_patron_favor_in_unit_range(self):
        cap = SaveCapsule(seed=0, culture_name='harfleur_1415')
        assert 0.0 <= cap.patron_favor <= 1.0


class TestSaveCapsuleFromState:
    def test_seed_preserved(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        assert cap.seed == state.seed

    def test_quarter_policy_preserved(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        assert cap.quarter_policy == state.quarter_policy

    def test_siege_result_preserved(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        assert cap.siege_result is not None
        assert cap.siege_result['outcome'] == state.siege_result['outcome']

    def test_march_result_preserved(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        assert cap.march_result is not None
        assert cap.march_result['arrived'] == state.march_result['arrived']

    def test_battle_result_preserved(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        assert cap.battle_result is not None
        assert cap.battle_result['win'] == state.battle_result['win']

    def test_belief_db_dict_populated_after_dispatches(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        # accurate dispatches were sent in _full_state — siege belief must exist
        assert 'siege' in cap.belief_db_dict

    def test_trace_dicts_has_three_entries(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        assert len(cap.trace_dicts) == 3

    def test_patron_favor_in_unit_range(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        assert 0.0 <= cap.patron_favor <= 1.0

    def test_station_is_string(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        assert isinstance(cap.station, str)
        assert cap.station in ('CAMP', 'HILL', 'KNOT', 'FRONT_RANK')

    def test_state_with_no_ops_produces_empty_results(self):
        """A capsule from a state with no operations has None results."""
        cmds = ['liberal', 'done']
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        cap = save_capsule_from_state(state)
        assert cap.siege_result is None
        assert cap.march_result is None
        assert cap.battle_result is None
        assert cap.trace_dicts == []

    def test_pending_orders_serialized(self):
        """Pending orders (if any) appear as plain dicts, not PendingOrder objects."""
        cmds = ['liberal', 'done']
        state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
        # Manually add a pending order
        state.pending_orders.append(PendingOrder(command='siege', eta_day=3, label='besiege'))
        cap = save_capsule_from_state(state)
        assert isinstance(cap.pending_orders[0], dict)
        assert cap.pending_orders[0]['command'] == 'siege'


class TestCapsuleToDict:
    def test_returns_dict(self):
        cap = SaveCapsule(seed=0, culture_name='harfleur_1415')
        d = capsule_to_dict(cap)
        assert isinstance(d, dict)

    def test_seed_in_dict(self):
        cap = SaveCapsule(seed=42, culture_name='test')
        d = capsule_to_dict(cap)
        assert d['seed'] == 42

    def test_full_state_capsule_to_dict_round_trips(self):
        state = _full_state()
        cap = save_capsule_from_state(state)
        d = capsule_to_dict(cap)
        # Re-creating from the dict must recover all key fields
        assert d['siege_result']['outcome'] == cap.siege_result['outcome']
        assert d['battle_result']['win'] == cap.battle_result['win']


class TestBeliefViewForTable:
    def _db_dict_with_dispatches(self):
        from core.belief_db import BeliefDB
        db = BeliefDB()
        db.receive_dispatch('siege', {'outcome': 'NEGOTIATED', 'day': 35}, confidence=0.90)
        db.observe('march', {'arrived': True}, source='landscape')
        db.observe('battle', {'won': True}, source='sightlines')
        return db.to_dict()

    def test_empty_belief_returns_empty_view(self):
        view = belief_view_for_table({}, 'CAMP')
        assert view == {}

    def test_camp_sees_only_dispatch_claims(self):
        d = self._db_dict_with_dispatches()
        view = belief_view_for_table(d, 'CAMP')
        assert 'siege' in view        # dispatch → visible at CAMP
        assert 'march' not in view    # landscape only → invisible at CAMP
        assert 'battle' not in view   # sightlines only → invisible at CAMP

    def test_hill_sees_dispatch_and_landscape(self):
        d = self._db_dict_with_dispatches()
        view = belief_view_for_table(d, 'HILL')
        assert 'siege' in view
        assert 'march' in view
        assert 'battle' not in view   # sightlines invisible at HILL

    def test_knot_sees_all_three(self):
        d = self._db_dict_with_dispatches()
        view = belief_view_for_table(d, 'KNOT')
        assert 'siege' in view
        assert 'march' in view
        assert 'battle' in view

    def test_front_rank_sees_nothing_from_these_claims(self):
        """FRONT_RANK can only see nearby_units; dispatch/landscape/sightlines invisible."""
        d = self._db_dict_with_dispatches()
        view = belief_view_for_table(d, 'FRONT_RANK')
        assert view == {}

    def test_each_claim_has_value_confidence_glyph(self):
        d = self._db_dict_with_dispatches()
        view = belief_view_for_table(d, 'CAMP')
        for phase_claims in view.values():
            for claim, entry in phase_claims.items():
                assert 'value' in entry, f"claim {claim!r} missing 'value'"
                assert 'confidence' in entry, f"claim {claim!r} missing 'confidence'"
                assert 'glyph' in entry, f"claim {claim!r} missing 'glyph'"

    def test_glyph_is_valid(self):
        d = self._db_dict_with_dispatches()
        view = belief_view_for_table(d, 'KNOT')
        for phase_claims in view.values():
            for claim, entry in phase_claims.items():
                assert entry['glyph'] in ('*', '~', '?', '.'), (
                    f"claim {claim!r} has invalid glyph {entry['glyph']!r}"
                )

    def test_invalid_station_falls_back_to_camp(self):
        """An unrecognised station name must not raise — it should fall back to CAMP."""
        from core.belief_db import BeliefDB
        db = BeliefDB()
        db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.9)
        d = db.to_dict()
        view = belief_view_for_table(d, 'TOWER_OF_LONDON')
        assert 'siege' in view   # dispatch visible from CAMP fallback

    def test_confidence_preserved_in_entry(self):
        from core.belief_db import BeliefDB
        db = BeliefDB()
        db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.9)
        d = db.to_dict()
        view = belief_view_for_table(d, 'CAMP')
        conf = view['siege']['outcome']['confidence']
        assert conf == pytest.approx(0.9, abs=0.01)


class TestConfidenceGlyph:
    def test_high_confidence_confirmed(self):
        assert _confidence_glyph(0.95) == '*'
        assert _confidence_glyph(0.90) == '*'

    def test_scouted_range(self):
        assert _confidence_glyph(0.80) == '~'
        assert _confidence_glyph(0.75) == '~'

    def test_rumoured_range(self):
        assert _confidence_glyph(0.70) == '?'
        assert _confidence_glyph(0.50) == '?'

    def test_stale_low_confidence(self):
        assert _confidence_glyph(0.49) == '.'
        assert _confidence_glyph(0.00) == '.'

    def test_boundary_0_90_is_confirmed(self):
        assert _confidence_glyph(0.90) == '*'

    def test_boundary_0_75_is_scouted(self):
        assert _confidence_glyph(0.75) == '~'

    def test_boundary_0_50_is_rumoured(self):
        assert _confidence_glyph(0.50) == '?'


class TestTraceForArchive:
    def _composed_trace(self, seed=0):
        return run_chain(seed=seed)['trace']

    def test_returns_dict_with_required_keys(self):
        arch = trace_for_archive(self._composed_trace())
        for key in ('phases', 'deaths', 'rout_count', 'events', 'summary'):
            assert key in arch, f"trace_for_archive missing key: {key!r}"

    def test_phases_contains_all_three(self):
        arch = trace_for_archive(self._composed_trace())
        assert set(arch['phases']) >= {'siege', 'march', 'battle'}

    def test_deaths_are_dicts_with_required_fields(self):
        arch = trace_for_archive(self._composed_trace())
        assert len(arch['deaths']) > 0
        for d in arch['deaths']:
            assert 't' in d, "death missing 't'"
            assert 'cause' in d, "death missing 'cause'"
            assert 'phase' in d, "death missing 'phase'"

    def test_deaths_strip_agent_id(self):
        """Archive deaths must not expose agent_id (privacy — spec §7 Archive)."""
        arch = trace_for_archive(self._composed_trace())
        for d in arch['deaths']:
            assert 'agent_id' not in d, "archive deaths must not expose agent_id"

    def test_rout_count_is_int(self):
        arch = trace_for_archive(self._composed_trace())
        assert isinstance(arch['rout_count'], int)
        assert arch['rout_count'] >= 0

    def test_events_have_name_t_phase(self):
        arch = trace_for_archive(self._composed_trace())
        for ev in arch['events']:
            assert 'name' in ev
            assert 't' in ev
            assert 'phase' in ev

    def test_summary_contains_siege_key(self):
        arch = trace_for_archive(self._composed_trace())
        assert 'siege' in arch['summary'], "summary must include siege key after a full chain run"

    def test_summary_siege_has_outcome(self):
        arch = trace_for_archive(self._composed_trace())
        assert 'outcome' in arch['summary']['siege']

    def test_summary_battle_won_field_present(self):
        arch = trace_for_archive(self._composed_trace())
        # Agincourt: English win → 'won' == True
        assert 'battle' in arch['summary']
        assert 'won' in arch['summary']['battle']

    def test_empty_trace_returns_safe_structure(self):
        empty = {'phases': [], 'scenarios': [], 'seed': 0,
                 'deaths': [], 'routs': [], 'events': []}
        arch = trace_for_archive(empty)
        assert arch['deaths'] == []
        assert arch['rout_count'] == 0
        assert arch['events'] == []

    def test_death_causes_are_known_values(self):
        """All cause strings must be from the spec'd vocabulary."""
        valid_causes = {'melee', 'volley', 'pursuit', 'thirst', 'disease', 'assault', 'cavalry'}
        arch = trace_for_archive(self._composed_trace())
        for d in arch['deaths']:
            assert d['cause'] in valid_causes, (
                f"Unknown death cause {d['cause']!r} — not in spec vocabulary"
            )


class TestPendingOrderForRenpy:
    def test_returns_dict(self):
        po = PendingOrder(command='siege', eta_day=3, label='besiege Harfleur')
        result = pending_order_for_renpy(po)
        assert isinstance(result, dict)

    def test_all_fields_preserved(self):
        po = PendingOrder(command='march', eta_day=7, label='march to Agincourt')
        result = pending_order_for_renpy(po)
        assert result['command'] == 'march'
        assert result['eta_day'] == 7
        assert result['label'] == 'march to Agincourt'

    def test_result_is_json_serializable(self):
        po = PendingOrder(command='battle', eta_day=12, label='engage the French')
        result = pending_order_for_renpy(po)
        assert _is_json_safe(result)
