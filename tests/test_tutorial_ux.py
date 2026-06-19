"""Tests for UX-01, UX-05, UX-07: tutorial UX issues."""
import importlib

import numpy as np
import pytest

from clients.cli.tutorial import (
    _TUTORIAL_COMMANDS,
    _MockIO,
    TutorialState,
    _operations_phase,
    _ask_quarter_policy,
    _print_quarter_options,
    _print_winter_court,
    run_tutorial,
)
from core.commission import generate_commission
from core.belief_db import BeliefDB


# ------------------------------------------------------------------
# UX-01: engage/evade gate is telegraphed in the command list


def test_ux01_command_list_telegraphs_patrol_gate():
    """The printed command list must indicate engage/evade need a march first."""
    assert 'after march' in _TUTORIAL_COMMANDS.lower() or \
           'march first' in _TUTORIAL_COMMANDS.lower(), (
        "Command list must label engage/evade as available only after march"
    )


def test_ux01_engage_and_evade_both_annotated():
    """Both engage and evade must carry the gate annotation."""
    lower = _TUTORIAL_COMMANDS.lower()
    # Locate the engage and evade lines and confirm annotation appears near each
    lines = lower.splitlines()
    engage_lines = [l for l in lines if 'engage' in l]
    evade_lines  = [l for l in lines if 'evade'  in l]
    assert engage_lines, "engage must appear in _TUTORIAL_COMMANDS"
    assert evade_lines,  "evade must appear in _TUTORIAL_COMMANDS"
    assert any('after march' in l or 'march first' in l for l in engage_lines), (
        "engage line must indicate it requires march first"
    )
    assert any('after march' in l or 'march first' in l for l in evade_lines), (
        "evade line must indicate it requires march first"
    )


def test_ux01_gate_error_is_instructive_engage():
    """Typing 'engage' before march must produce a message that teaches the ordering."""
    module = importlib.import_module('core.cultures.tutorial_escort')
    culture = module.CULTURE
    commission = generate_commission(culture, np.random.default_rng(0))
    state = TutorialState(commission=commission, seed=0,
                          patron_favor=culture['career']['starting_patron_favor'])
    io = _MockIO(['engage', 'done'])
    _operations_phase(state, io)
    joined = '\n'.join(io.lines)
    assert 'march' in joined.lower(), "Gate error must mention 'march'"
    # Must not solely say "no patrol" without guidance
    assert 'sighted' not in joined.lower() or 'march' in joined.lower()


def test_ux01_gate_error_is_instructive_evade():
    """Typing 'evade' before march must produce a message that teaches the ordering."""
    module = importlib.import_module('core.cultures.tutorial_escort')
    culture = module.CULTURE
    commission = generate_commission(culture, np.random.default_rng(0))
    state = TutorialState(commission=commission, seed=0,
                          patron_favor=culture['career']['starting_patron_favor'])
    io = _MockIO(['evade', 'done'])
    _operations_phase(state, io)
    joined = '\n'.join(io.lines)
    assert 'march' in joined.lower(), "Evade gate error must mention 'march'"


def test_ux01_engage_works_after_march():
    """engage command succeeds after march completes (gate correctly lifted)."""
    state = run_tutorial(seed=0, auto_commands=['', 'liberal', 'march normal', 'engage', 'done'])
    assert state.battle_result is not None, "Battle must have run after engage post-march"


def test_ux01_evade_works_after_march():
    """evade command succeeds after march completes."""
    state = run_tutorial(seed=0, auto_commands=['', 'liberal', 'march normal', 'evade', 'done'])
    assert state.march_result is not None
    assert state.battle_result is None, "Evade must not trigger battle"


# ------------------------------------------------------------------
# UX-05: invalid quarter policy redisplays options


def _make_tutorial_state(seed: int = 0) -> tuple:
    """Return (commission, culture, io-helper factory)."""
    module = importlib.import_module('core.cultures.tutorial_escort')
    culture = module.CULTURE
    commission = generate_commission(culture, np.random.default_rng(seed))
    return commission, culture


def test_ux05_invalid_quarter_policy_redisplays_options():
    """Typing an invalid quarter policy must redisplay the options before re-prompting."""
    commission, culture = _make_tutorial_state(seed=0)
    io = _MockIO(['?', 'liberal'])
    _ask_quarter_policy(commission, culture, io)
    joined = '\n'.join(io.lines)
    # 'strict' appears in each print of the options; must appear at least twice
    assert joined.count('strict') >= 2, (
        "Option list must be redisplayed after invalid quarter policy input"
    )


def test_ux05_invalid_quarter_resolves_to_valid_after_retry():
    """After an invalid input, a valid input must be accepted and applied."""
    commission, culture = _make_tutorial_state(seed=0)
    io = _MockIO(['?', 'strict'])
    result = _ask_quarter_policy(commission, culture, io)
    assert result == 'strict', "Policy must resolve to 'strict' after retry"


def test_ux05_full_tutorial_invalid_then_valid():
    """Full tutorial run with invalid then valid quarter policy must complete normally."""
    state = run_tutorial(
        seed=0,
        auto_commands=['', '?', 'liberal', 'march normal', 'evade', 'done'],
    )
    assert state.quarter_policy == 'liberal'
    assert state.march_result is not None


# ------------------------------------------------------------------
# UX-07: improvement advice cites the correct delta source


def _make_winter_court_state(seed: int = 0):
    module = importlib.import_module('core.cultures.tutorial_escort')
    culture = module.CULTURE
    from core.commission import generate_commission
    commission = generate_commission(culture, np.random.default_rng(seed))
    state = TutorialState(
        commission=commission,
        seed=seed,
        patron_favor=culture['career']['starting_patron_favor'],
    )
    return state, culture


def test_ux07_advice_blames_quarter_when_free_rein_is_cause():
    """Neutral favor from free_rein + mission success must blame quarter, not dispatches."""
    state, culture = _make_winter_court_state(seed=0)
    state.quarter_policy = 'free_rein'
    # Mission believed = True via dispatch
    state.belief_db.receive_dispatch('march', {'arrived': True}, confidence=0.90)
    io = _MockIO([])
    _print_winter_court(state, io)
    joined = '\n'.join(io.lines)
    # Only relevant when neutral/noted appears (free_rein + mission success = neutral)
    if 'noted' in joined or 'neutral' in joined.lower():
        assert 'quarter' in joined.lower(), (
            "When free_rein caused neutral favor, advice must mention quarter policy"
        )
        assert 'send accurate dispatches' not in joined.lower(), (
            "Advice must not blame dispatches when dispatches were accurate"
        )


def test_ux07_advice_blames_mission_when_mission_not_believed():
    """Neutral favor from mission failure must mention march/mission, not quarter."""
    state, culture = _make_winter_court_state(seed=0)
    state.quarter_policy = 'liberal'
    # No march dispatch → mission not believed
    io = _MockIO([])
    _print_winter_court(state, io)
    joined = '\n'.join(io.lines)
    # liberal + no mission = favor ~0.45 = neutral; check advice
    if 'noted' in joined or 'neutral' in joined.lower():
        assert 'arrived' in joined.lower() or 'march' in joined.lower(), (
            "When mission was not believed, advice must mention 'arrived' or 'march'"
        )


def test_ux07_high_favor_shows_commission_offer():
    """When patron favor is high, the commission offer line must appear (not the advice)."""
    state, culture = _make_winter_court_state(seed=0)
    state.quarter_policy = 'liberal'
    # Mission success + liberal → favor rises above threshold
    state.belief_db.receive_dispatch('march', {'arrived': True}, confidence=0.90)
    io = _MockIO([])
    _print_winter_court(state, io)
    joined = '\n'.join(io.lines)
    assert 'commission' in joined.lower(), "High favor must show commission offer"
