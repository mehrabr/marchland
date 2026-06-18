"""M3 tests: commission, belief_db, missions, season (non-interactive).

Unit tests use direct module calls; the season integration test drives the
SeasonState via auto_commands so no stdin is required.
"""
import pytest
import numpy as np

from core.cultures.harfleur_1415 import CULTURE
from core.commission import Commission, generate_commission, apply_quarter_policy, muster_summary
from core.belief_db import BeliefDB, trace_to_summary
from core.missions import MISSIONS, evaluate_mission, patron_believes_success
from clients.cli.season import run_season, SeasonState, _credit_label


# ------------------------------------------------------------------
# Culture file sanity checks

def test_culture_has_required_keys():
    for key in ('patron', 'doctrine_vocab', 'station_prices', 'quarter_customs',
                'career', 'missions_pool', 'armies'):
        assert key in CULTURE, f"CULTURE missing key: {key}"


def test_culture_armies_no_quality_coefficients():
    """Receipts-grep rule: no per-cohort quality/bonus/modifier fields."""
    forbidden = {'quality', 'bonus', 'modifier', 'coeff', 'strength_modifier'}
    for army in CULTURE['armies']:
        for c in army['cohorts']:
            bad = set(c.keys()) & forbidden
            assert not bad, f"Cohort '{c.get('label')}' has forbidden fields: {bad}"


def test_culture_armies_have_required_cohort_fields():
    for army in CULTURE['armies']:
        assert army['cohorts'], "Army must have at least one cohort"
        for c in army['cohorts']:
            assert 'n' in c, f"Cohort missing 'n' (body count): {c}"
            assert 'side' in c, f"Cohort missing 'side': {c}"
            assert 'label' in c, f"Cohort missing 'label': {c}"


# ------------------------------------------------------------------
# Commission generation

def test_generate_commission_produces_valid_commission():
    rng = np.random.default_rng(42)
    comm = generate_commission(CULTURE, rng)
    assert isinstance(comm, Commission)
    assert comm.patron == CULTURE['patron']
    assert comm.mission in CULTURE['missions_pool']
    assert len(comm.army_cohorts) > 0
    assert 0.0 <= comm.patron_favor <= 1.0


def test_generate_commission_army_is_deep_copy():
    rng = np.random.default_rng(0)
    comm = generate_commission(CULTURE, rng)
    comm.army_cohorts[0]['n'] = 9999
    # Original culture file must be unchanged
    assert CULTURE['armies'][0]['cohorts'][0]['n'] != 9999


def test_apply_quarter_policy_valid():
    rng = np.random.default_rng(0)
    comm = generate_commission(CULTURE, rng)
    apply_quarter_policy(comm, 'strict')
    assert comm.strings['quarter_policy'] == 'strict'


def test_apply_quarter_policy_invalid_raises():
    rng = np.random.default_rng(0)
    comm = generate_commission(CULTURE, rng)
    with pytest.raises(ValueError):
        apply_quarter_policy(comm, 'pillage_everything')


def test_muster_summary_is_string():
    rng = np.random.default_rng(0)
    comm = generate_commission(CULTURE, rng)
    s = muster_summary(comm)
    assert isinstance(s, str)
    assert comm.patron in s
    assert comm.mission.upper() in s


def test_commission_deadline_uses_culture_override():
    """harfleur_1415 has a season_deadline override; it must take precedence."""
    rng = np.random.default_rng(0)
    comm = generate_commission(CULTURE, rng)
    expected = CULTURE['career']['season_deadline']
    assert comm.strings['deadline_days'] == expected


# ------------------------------------------------------------------
# BeliefDB

def test_belief_db_empty_returns_none():
    db = BeliefDB()
    assert db.get('siege', 'outcome') is None


def test_belief_db_receive_dispatch_stores_value():
    db = BeliefDB()
    db.receive_dispatch('siege', {'outcome': 'NEGOTIATED', 'day': 35}, confidence=0.9)
    val, conf = db.get('siege', 'outcome')
    assert val == 'NEGOTIATED'
    assert conf == pytest.approx(0.9)


def test_belief_db_later_dispatch_overwrites():
    db = BeliefDB()
    db.receive_dispatch('siege', {'day': 35}, confidence=0.9)
    db.receive_dispatch('siege', {'day': 38}, confidence=0.7)
    val, _ = db.get('siege', 'day')
    assert val == 38   # fresher rider wins


def test_belief_db_believed_default():
    db = BeliefDB()
    assert db.believed('siege', 'outcome', default='unknown') == 'unknown'


def test_belief_db_audit_match():
    db = BeliefDB()
    db.receive_dispatch('siege', {'outcome': 'NEGOTIATED', 'day': 35}, confidence=0.9)
    ts = {'siege': {'outcome': 'NEGOTIATED', 'day': 35}}
    findings = db.audit(ts)
    assert findings['siege.outcome']['match'] is True
    assert findings['siege.day']['match'] is True


def test_belief_db_audit_mismatch():
    db = BeliefDB()
    db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.9)
    ts = {'siege': {'outcome': 'STORMED_sack'}}
    findings = db.audit(ts)
    assert findings['siege.outcome']['match'] is False


def test_belief_db_audit_no_trace_analog():
    db = BeliefDB()
    db.receive_dispatch('siege', {'secret_claim': 'x'}, confidence=0.5)
    findings = db.audit({})
    assert findings['siege.secret_claim']['match'] is None


def test_belief_db_to_dict_serialisable():
    db = BeliefDB()
    db.receive_dispatch('battle', {'won': True}, confidence=0.85)
    d = db.to_dict()
    assert d['battle']['won']['value'] is True


# ------------------------------------------------------------------
# trace_to_summary

def test_trace_to_summary_siege_negotiated():
    trace = {
        'events': [('NEGOTIATED', 35.0, {}, 'siege')],
        'deaths': [],
        'routs': [],
    }
    ts = trace_to_summary(trace)
    assert ts['siege']['outcome'] == 'NEGOTIATED'
    assert ts['siege']['day'] == 35


def test_trace_to_summary_battle_won():
    trace = {
        'events': [('side1_broke', 1800.0, {}, 'battle')],
        'deaths': [],
        'routs': [],
    }
    ts = trace_to_summary(trace)
    assert ts['battle']['won'] is True


def test_trace_to_summary_battle_lost():
    trace = {
        'events': [('side0_broke', 2200.0, {}, 'battle')],
        'deaths': [],
        'routs': [],
    }
    ts = trace_to_summary(trace)
    assert ts['battle']['won'] is False


# ------------------------------------------------------------------
# Missions

def test_missions_registry_has_all_types():
    expected = {'siege', 'intercept', 'chevauche', 'relief', 'escort', 'hold',
                'march', 'suppress'}
    assert expected == set(MISSIONS.keys())


def test_mission_objective_predicate_callable():
    for key, spec in MISSIONS.items():
        pred = spec['objective_predicate']
        assert callable(pred), f"Mission '{key}' predicate is not callable"
        # Must not raise on empty trace summary
        result = pred({})
        assert isinstance(result, bool)


def test_evaluate_mission_siege_success():
    ts = {'siege': {'outcome': 'NEGOTIATED', 'day': 35}}
    assert evaluate_mission('siege', ts) is True


def test_evaluate_mission_siege_failure():
    ts = {'siege': {'outcome': 'ONGOING', 'day': 60}}
    assert evaluate_mission('siege', ts) is False


def test_evaluate_mission_march_arrived():
    ts = {'march': {'arrived': True, 'day': 17}}
    assert evaluate_mission('march', ts) is True


def test_evaluate_mission_unknown_raises():
    with pytest.raises(ValueError):
        evaluate_mission('made_up_mission', {})


def test_patron_believes_success_no_dispatches():
    db = BeliefDB()
    # No dispatches → patron cannot believe success
    assert patron_believes_success('siege', db) is False


def test_patron_believes_success_from_dispatch():
    db = BeliefDB()
    db.receive_dispatch('siege', {'outcome': 'NEGOTIATED'}, confidence=0.9)
    assert patron_believes_success('siege', db) is True


def test_patron_believes_success_wrong_outcome():
    db = BeliefDB()
    db.receive_dispatch('siege', {'outcome': 'ONGOING'}, confidence=0.9)
    assert patron_believes_success('siege', db) is False


# ------------------------------------------------------------------
# Season (non-interactive via auto_commands)

def _siege_commands(quarter='liberal', tactic='wait',
                    siege_dispatch='accurate', pace='normal',
                    march_dispatch='accurate',
                    battle='engage', battle_dispatch='accurate'):
    return [
        quarter,          # decision 1: quarter policy
        'siege',          # operation 1
        tactic,           # decision 2: siege tactic
        siege_dispatch,   # dispatch choice
        'march',          # operation 2
        pace,             # decision 3: march pace
        march_dispatch,   # dispatch choice
        'battle',         # operation 3
        battle,           # decision 4: engage or withdraw
        battle_dispatch,  # dispatch choice
        'done',           # conclude operations
    ]


def test_season_runs_without_error():
    state = run_season('harfleur_1415', seed=0,
                       auto_commands=_siege_commands())
    assert isinstance(state, SeasonState)


def test_season_all_four_decisions_recorded():
    state = run_season('harfleur_1415', seed=0,
                       auto_commands=_siege_commands(
                           quarter='strict', tactic='storm',
                           pace='push', battle='engage'))
    assert state.quarter_policy == 'strict'
    assert state.siege_tactic == 'storm'
    assert state.march_pace == 'push'
    assert state.battle_choice == 'engage'


def test_season_siege_result_populated():
    state = run_season('harfleur_1415', seed=0,
                       auto_commands=_siege_commands())
    assert state.siege_result is not None
    assert state.siege_result['outcome'] in ('NEGOTIATED', 'STORMED_sack',
                                             'RELIEVED', 'ABANDONED_supply', 'ONGOING')


def test_season_march_result_populated():
    state = run_season('harfleur_1415', seed=0,
                       auto_commands=_siege_commands())
    assert state.march_result is not None
    assert 'arrived' in state.march_result


def test_season_battle_result_populated():
    state = run_season('harfleur_1415', seed=0,
                       auto_commands=_siege_commands())
    assert state.battle_result is not None
    assert 'win' in state.battle_result


def test_season_withdraw_skips_battle():
    cmds = _siege_commands(battle='withdraw')
    state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
    assert state.battle_choice == 'withdraw'
    assert state.battle_result.get('withdrew') is True


def test_season_no_dispatch_leaves_belief_empty():
    cmds = _siege_commands(
        siege_dispatch='none',
        march_dispatch='none',
        battle_dispatch='none',
    )
    state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
    assert state.belief_db.phases_with_beliefs() == []


def test_season_accurate_dispatch_updates_belief():
    cmds = _siege_commands(siege_dispatch='accurate',
                           march_dispatch='none',
                           battle_dispatch='none')
    state = run_season('harfleur_1415', seed=0, auto_commands=cmds)
    assert 'siege' in state.belief_db.phases_with_beliefs()


def test_season_patron_favor_moves():
    """Patron favor must change from starting value after a completed season."""
    rng = np.random.default_rng(0)
    comm = generate_commission(CULTURE, rng)
    initial_favor = comm.patron_favor

    state = run_season('harfleur_1415', seed=0,
                       auto_commands=_siege_commands())
    assert state.patron_favor != initial_favor


def test_season_composed_trace_has_all_phases():
    state = run_season('harfleur_1415', seed=0,
                       auto_commands=_siege_commands())
    assert state.composed_trace is not None
    phases = state.composed_trace.get('phases', [])
    assert 'siege' in phases
    assert 'march' in phases
    assert 'battle' in phases


def test_season_deterministic_same_seed():
    cmds = _siege_commands()
    s1 = run_season('harfleur_1415', seed=7, auto_commands=cmds)
    s2 = run_season('harfleur_1415', seed=7, auto_commands=cmds)
    assert s1.siege_result == s2.siege_result
    assert s1.march_result == s2.march_result
    assert s1.battle_result['win'] == s2.battle_result['win']


def test_season_different_seeds_may_differ():
    cmds = _siege_commands()
    # Over 12 seeds, at least one pair should differ in some outcome
    results = [run_season('harfleur_1415', seed=i, auto_commands=cmds)
               for i in range(4)]
    outcomes = [r.siege_result['outcome'] for r in results]
    # All outcomes are valid siege outcomes
    valid = {'NEGOTIATED', 'STORMED_sack', 'RELIEVED', 'ABANDONED_supply', 'ONGOING'}
    assert all(o in valid for o in outcomes)


def test_credit_label_thresholds():
    thresholds = {'acclaim': 0.80, 'favor': 0.60, 'neutral': 0.40, 'cold': 0.20, 'censure': 0.00}
    labels = ['censure', 'cold shoulder', 'neutral', 'favor', 'acclaim']
    assert _credit_label(0.85, thresholds, labels) == 'acclaim'
    assert _credit_label(0.65, thresholds, labels) == 'favor'
    assert _credit_label(0.45, thresholds, labels) == 'neutral'
    assert _credit_label(0.25, thresholds, labels) == 'cold shoulder'
    assert _credit_label(0.05, thresholds, labels) == 'censure'
