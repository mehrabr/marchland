"""Tests for UX-01: tutorial command list telegraphs patrol gate."""
import importlib

import numpy as np
import pytest

from clients.cli.tutorial import (
    _TUTORIAL_COMMANDS,
    _MockIO,
    TutorialState,
    _operations_phase,
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
