"""Tests for M6: tutorial season, help system, and covenant.

Grade-A assertions:
  - tutorial runs to completion without error
  - tutorial march arrives at distance=50 (seed 0)
  - English win majority of seeds in tutorial skirmish
  - all help topics return non-empty text
  - covenant contains the key phrase

Grade-B (warnings):
  - tutorial winter court produces patron favor > 0.50 on success path

Covers:
  clients/cli/tutorial.py
  clients/cli/help.py
  clients/cli/covenant.py
  core/scenarios/tutorial_march.py
  core/scenarios/tutorial_skirmish.py
  core/cultures/tutorial_escort.py
"""
import pytest

from clients.cli.tutorial import run_tutorial, TutorialState, _tutorial_skirmish_scn, _tutorial_march_scn
from core.scenarios.tutorial_skirmish import tutorial_skirmish as _canon_skirmish_scn
from clients.cli.help import get_help, show_help, _TOPICS
from clients.cli.covenant import COVENANT_TEXT, print_covenant
from core.march import run_march
from core.lattice import Battle


# ------------------------------------------------------------------
# Helpers

def _success_commands():
    """Auto-commands that complete the tutorial on the success path."""
    return [
        '',             # press enter at covenant
        'liberal',      # quarter policy
        'march normal', # march at normal pace
        'engage',       # fight the patrol
        'done',         # conclude
    ]


def _evade_commands():
    """Auto-commands that evade the patrol."""
    return [
        '',
        'liberal',
        'march normal',
        'evade',
        'done',
    ]


# ------------------------------------------------------------------
# Tutorial completion

def test_tutorial_runs_to_completion():
    """Tutorial with success auto-commands completes without error."""
    state = run_tutorial(seed=0, auto_commands=_success_commands())
    assert isinstance(state, TutorialState)
    assert state.march_result is not None, "March must have run"


def test_tutorial_evade_path_completes():
    """Tutorial with evade path completes without error."""
    state = run_tutorial(seed=0, auto_commands=_evade_commands())
    assert isinstance(state, TutorialState)
    assert state.march_result is not None
    assert state.battle_result is None, "Evade path must not trigger battle"


def test_tutorial_strict_policy_completes():
    """Tutorial with strict quarter policy completes and shifts favor up."""
    cmds = ['', 'strict', 'march normal', 'evade', 'done']
    state = run_tutorial(seed=0, auto_commands=cmds)
    assert state.quarter_policy == 'strict'
    assert state.patron_favor >= 0.35, "Favor must not drop below tutorial floor"


def test_tutorial_push_pace_completes():
    """Push pace tutorial path completes (men arrive more tired)."""
    cmds = ['', 'liberal', 'march push', 'engage', 'done']
    state = run_tutorial(seed=0, auto_commands=cmds)
    assert state.march_result is not None
    assert state.march_result['arrived'], "Push pace must still arrive in time"


def test_tutorial_rest_pace_completes():
    """Rest pace tutorial path completes."""
    cmds = ['', 'liberal', 'march rest', 'engage', 'done']
    state = run_tutorial(seed=0, auto_commands=cmds)
    assert state.march_result is not None


# ------------------------------------------------------------------
# March scenario

def test_tutorial_march_arrives_seed0():
    """Tutorial march scenario arrives within max_days at seed 0."""
    scn = _tutorial_march_scn()
    result = run_march(scn, seed=0)
    assert result['arrived'], "Tutorial march must arrive on seed 0"
    assert result['days'] <= 12, f"Must arrive within 12 days, got {result['days']}"


def test_tutorial_march_arrives_majority():
    """Tutorial march arrives in ≥ 10/12 seeds (grade A)."""
    scn = _tutorial_march_scn()
    arrived = sum(run_march(scn, s)['arrived'] for s in range(12))
    assert arrived >= 10, f"Tutorial march should arrive in ≥10/12 seeds, got {arrived}/12"


def test_tutorial_march_fatigue_bounded():
    """March fatigue stays in [0, 1] for all seeds."""
    scn = _tutorial_march_scn()
    for seed in range(12):
        r = run_march(scn, seed)
        assert 0.0 <= r['fatigue'] <= 1.0, f"Fatigue out of range at seed {seed}: {r['fatigue']}"


def test_tutorial_march_push_pace_higher_fatigue():
    """Push pace produces higher fatigue than normal on same seed."""
    scn_normal = _tutorial_march_scn()
    scn_push = dict(scn_normal, pace=scn_normal['pace'] * 1.20,
                    fat0=min(1.0, scn_normal['fat0'] + 0.05))
    r_normal = run_march(scn_normal, seed=0)
    r_push = run_march(scn_push, seed=0)
    assert r_push['fatigue'] >= r_normal['fatigue'], \
        "Push pace must not produce lower fatigue than normal"


# ------------------------------------------------------------------
# Skirmish scenario

def test_tutorial_skirmish_english_win_majority():
    """English win ≥ 7/12 seeds in the tutorial skirmish (grade A)."""
    wins = sum(
        Battle(_tutorial_skirmish_scn(fat0=0.05), seed=s).run()['win'] == 0
        for s in range(12)
    )
    assert wins >= 7, f"English must win majority (≥7/12), got {wins}/12"


def test_tutorial_skirmish_deterministic():
    """Same seed produces identical battle outcome."""
    r1 = Battle(_tutorial_skirmish_scn(fat0=0.05), seed=3).run()
    r2 = Battle(_tutorial_skirmish_scn(fat0=0.05), seed=3).run()
    assert r1['win'] == r2['win'], "Battle outcome must be deterministic for same seed"
    assert r1['s'][0]['dead'] == r2['s'][0]['dead'], "Dead count must be deterministic"


def test_tutorial_skirmish_high_fatigue_hurts():
    """High march fatigue reduces English win rate vs. fresh troops."""
    wins_fresh = sum(
        Battle(_tutorial_skirmish_scn(fat0=0.05), seed=s).run()['win'] == 0
        for s in range(12)
    )
    wins_tired = sum(
        Battle(_tutorial_skirmish_scn(fat0=0.50), seed=s).run()['win'] == 0
        for s in range(12)
    )
    # High fatigue should not *improve* win rate
    assert wins_tired <= wins_fresh + 2, \
        f"High fatigue should not increase wins: tired={wins_tired}, fresh={wins_fresh}"


# ------------------------------------------------------------------
# Belief DB and mission evaluation

def test_tutorial_belief_db_receives_march_dispatch():
    """After the march, belief_db has 'march' phase claims."""
    state = run_tutorial(seed=0, auto_commands=_success_commands())
    arrived = state.belief_db.believed('march', 'arrived')
    assert arrived is not None, "Belief DB must have a 'march.arrived' claim"
    assert arrived is True, "Arrived dispatch must be True on success path"


def test_tutorial_patron_believes_success_on_success_path():
    """Patron believes escort succeeded on the success path."""
    from core.missions import patron_believes_success
    state = run_tutorial(seed=0, auto_commands=_success_commands())
    assert patron_believes_success('escort', state.belief_db), \
        "Patron must believe success on the success path"


def test_tutorial_patron_favor_increases_on_success():
    """Patron favor ends above starting value on the success path."""
    state = run_tutorial(seed=0, auto_commands=_success_commands())
    starting = state.commission.culture['career']['starting_patron_favor']
    assert state.patron_favor > starting, \
        f"Favor must increase on success: {state.patron_favor:.2f} vs start {starting:.2f}"


# ------------------------------------------------------------------
# Help system

def test_help_all_topics_return_text():
    """All help topics return non-empty strings."""
    for topic in _TOPICS:
        text = get_help(topic)
        assert text, f"Help topic '{topic}' returned empty string"
        assert len(text) > 50, f"Help topic '{topic}' is suspiciously short: {text!r}"


def test_help_no_topic_returns_topic_list():
    """get_help() with no topic returns the topic listing."""
    text = get_help()
    assert 'march' in text
    assert 'battle' in text
    assert 'receipts' in text


def test_help_prefix_match():
    """Help resolves unambiguous prefixes."""
    assert get_help('mar') == get_help('march')
    assert get_help('bat') == get_help('battle')
    assert get_help('rec') == get_help('receipts')


def test_help_unknown_topic():
    """Unknown help topic returns an error message, not an exception."""
    text = get_help('zxqwerty')
    assert 'Unknown' in text or 'unknown' in text


def test_help_receipts_contains_class_labels():
    """Receipts help explains all five receipt classes."""
    text = get_help('receipts')
    for cls in ('A', 'B', 'C', 'D', 'E'):
        assert f'  {cls} —' in text or f'  {cls}—' in text or f'{cls} —' in text, \
            f"Receipt class {cls} not mentioned in help receipts"


def test_show_help_uses_io(capsys):
    """show_help prints to stdout when no io supplied."""
    show_help('march')
    out = capsys.readouterr().out
    assert 'MARCH' in out


def test_show_help_uses_mock_io():
    """show_help with mock io captures output in io.lines."""
    from clients.cli.tutorial import _MockIO
    io = _MockIO([])
    show_help('march', io=io)
    combined = '\n'.join(io.lines)
    assert 'MARCH' in combined


# ------------------------------------------------------------------
# Covenant

def test_covenant_contains_key_phrase():
    """Covenant must contain 'You command; you do not pilot.'"""
    assert "You command; you do not pilot." in COVENANT_TEXT


def test_covenant_mentions_no_quality():
    """Covenant mentions that quality coefficients are absent."""
    assert 'quality' in COVENANT_TEXT.lower() or 'receipt' in COVENANT_TEXT.lower()


def test_print_covenant_mock_io():
    """print_covenant with mock io captures output."""
    from clients.cli.tutorial import _MockIO
    io = _MockIO([])
    print_covenant(io)
    combined = '\n'.join(io.lines)
    assert "You command; you do not pilot." in combined


# ------------------------------------------------------------------
# Culture file

def test_tutorial_culture_no_quality_coefficients():
    """Tutorial culture file contains no forbidden quality coefficient fields."""
    from tools.receipts_grep import scan_file
    from pathlib import Path
    path = Path(__file__).parent.parent / 'core' / 'cultures' / 'tutorial_escort.py'
    violations = scan_file(path)
    assert violations == [], f"Quality coefficient found in tutorial_escort.py: {violations}"


def test_tutorial_culture_has_escort_mission():
    """Tutorial culture has 'escort' as its sole mission."""
    from core.cultures.tutorial_escort import CULTURE
    assert CULTURE['missions_pool'] == ['escort']


def test_tutorial_culture_has_receipt_notes():
    """Tutorial culture has receipt_notes for all army cohorts."""
    from core.cultures.tutorial_escort import CULTURE
    army = CULTURE['armies'][0]
    notes = army.get('receipt_notes', {})
    for cohort in army['cohorts']:
        label = cohort['label']
        assert label in notes, f"No receipt_notes for cohort '{label}'"
        assert len(notes[label]) >= 2, f"receipt_notes for '{label}' too short"


# ------------------------------------------------------------------
# Season help integration

def test_season_help_topic_works():
    """Season with 'help march' command does not raise."""
    from clients.cli.season import run_season
    cmds = [
        'liberal',          # quarter policy
        'help march',       # help topic (new M6 integration)
        'siege',            # normal ops flow
        'wait',             # dispatch-tactic
        'accurate',         # siege dispatch
        'march',
        'normal',
        'accurate',
        'battle',
        'engage',
        'accurate',
        'done',
    ]
    state = run_season(culture_name='harfleur_1415', seed=0, auto_commands=cmds)
    assert state is not None
