"""Tests for UX-03, UX-05, UX-06, UX-08: season UX issues."""
import importlib

import numpy as np

from clients.cli.season import (
    SeasonState,
    _audit_phase,
    _ask_quarter_policy,
    _print_quarter_options,
    _ask_dispatch,
    _print_court_scene,
    _MockIO,
    _DISPATCH_EXPLANATION,
)
from core.commission import generate_commission
from core.belief_db import BeliefDB


# ------------------------------------------------------------------
# Shared helpers

class _CaptureIO:
    """Minimal IO that captures printed lines (no input needed for audit)."""
    def __init__(self):
        self.lines = []

    def print(self, *args, **kw):
        sep = kw.get('sep', ' ')
        self.lines.append(sep.join(str(a) for a in args))

    def input(self, prompt: str) -> str:
        return ''


def _make_state(seed: int = 42) -> SeasonState:
    module = importlib.import_module('core.cultures.harfleur_1415')
    culture = module.CULTURE
    commission = generate_commission(culture, np.random.default_rng(seed))
    return SeasonState(commission, seed, instant_orders=True)


# ------------------------------------------------------------------
# UX-03: '(unknown)' label replaced with explanatory text


def test_ux03_audit_does_not_use_unknown_label():
    """Audit table must not use the raw '(unknown)' label for unverifiable claims."""
    state = _make_state()
    # Siege casualties have no trace analog — this is the canonical unverifiable claim
    state.belief_db.receive_dispatch(
        'siege', {'outcome': 'NEGOTIATED', 'day': 29, 'casualties': 553},
        confidence=0.90,
    )

    io = _CaptureIO()
    _audit_phase(state, io)

    audit_rows = [l for l in io.lines if 'siege.' in l]
    assert audit_rows, "Audit must produce siege rows when siege dispatch was sent"
    for row in audit_rows:
        assert '(unknown)' not in row, (
            f"Audit must not use '(unknown)'; found in row: {row!r}"
        )


def test_ux03_unverifiable_claim_is_explained():
    """Unverifiable claims must show a descriptive label, not an error-looking one."""
    state = _make_state()
    state.belief_db.receive_dispatch(
        'siege', {'outcome': 'NEGOTIATED', 'day': 29, 'casualties': 553},
        confidence=0.90,
    )

    io = _CaptureIO()
    _audit_phase(state, io)

    # The label must convey design intent, not missing data
    audit_text = '\n'.join(io.lines)
    assert 'not in trace' in audit_text.lower() or 'unverifiable' in audit_text.lower(), (
        "Audit must use an explanatory label for claims with no trace analog"
    )


def test_ux03_audit_footer_present_when_unverifiable():
    """A footer explaining unverifiable claims must appear when any claim has no trace analog."""
    state = _make_state()
    state.belief_db.receive_dispatch(
        'siege', {'outcome': 'NEGOTIATED', 'day': 29, 'casualties': 553},
        confidence=0.90,
    )

    io = _CaptureIO()
    _audit_phase(state, io)

    full_text = '\n'.join(io.lines)
    assert 'patron accepts as reported' in full_text.lower() or \
           'no trace analog' in full_text.lower(), (
        "Audit must include a footer explaining why some claims have no actual value"
    )


def test_ux03_verifiable_claim_still_shows_actual():
    """Claims that do have a trace analog must still show their actual value."""
    state = _make_state()
    from core.trace import Trace
    from core.siege import run_siege
    from core.scenarios.harfleur import harfleur

    # Run a siege so the trace is populated
    tr = Trace(phase='siege', scenario='harfleur', seed=42)
    result = run_siege(harfleur(), 42, trace=tr)
    state.trace_phases.append(tr)

    from core.trace import compose_traces
    from core.belief_db import trace_to_summary
    state.composed_trace = compose_traces(state.trace_phases)

    # Send dispatch with 'outcome' which IS verifiable from trace
    state.belief_db.receive_dispatch(
        'siege', {'outcome': result['outcome'], 'day': result['day']},
        confidence=0.90,
    )

    io = _CaptureIO()
    _audit_phase(state, io)

    outcome_row = next(
        (l for l in io.lines if 'siege.outcome' in l), None
    )
    assert outcome_row is not None, "siege.outcome must appear in audit"
    assert '(not in trace' not in outcome_row.lower(), (
        "A verifiable claim (outcome) must show its actual value, not '(not in trace summary)'"
    )


def test_ux03_no_footer_when_all_claims_verifiable():
    """Footer must be absent when all dispatched claims have trace analogs."""
    state = _make_state()
    from core.trace import Trace
    from core.siege import run_siege
    from core.scenarios.harfleur import harfleur
    from core.trace import compose_traces

    tr = Trace(phase='siege', scenario='harfleur', seed=42)
    result = run_siege(harfleur(), 42, trace=tr)
    state.trace_phases.append(tr)
    state.composed_trace = compose_traces(state.trace_phases)

    # Only send verifiable claims — no casualties
    state.belief_db.receive_dispatch(
        'siege', {'outcome': result['outcome'], 'day': result['day']},
        confidence=0.90,
    )

    io = _CaptureIO()
    _audit_phase(state, io)

    full_text = '\n'.join(io.lines)
    # If all claims are verifiable, the † footer should not appear
    assert '† claim has no trace analog' not in full_text, (
        "Footer must not appear when all dispatched claims have trace analogs"
    )


# ------------------------------------------------------------------
# UX-05: invalid quarter policy redisplays options (season)


def _make_season_state(seed: int = 0) -> tuple:
    module = importlib.import_module('core.cultures.harfleur_1415')
    culture = module.CULTURE
    commission = generate_commission(culture, np.random.default_rng(seed))
    return commission, culture


def test_ux05_season_invalid_quarter_policy_redisplays_options():
    """Typing an invalid quarter policy in the season must redisplay the options."""
    commission, culture = _make_season_state(seed=0)
    io = _MockIO(['?', 'liberal'])
    _ask_quarter_policy(commission, culture, io)
    joined = '\n'.join(io.lines)
    assert joined.count('strict') >= 2, (
        "Season quarter prompt must redisplay options after invalid input"
    )


def test_ux05_season_invalid_then_valid_sets_correct_policy():
    """After invalid input, a valid policy input must be accepted and applied."""
    commission, culture = _make_season_state(seed=0)
    io = _MockIO(['bad', 'strict'])
    result = _ask_quarter_policy(commission, culture, io)
    assert result == 'strict'


def test_ux05_season_options_printed_before_prompt():
    """Season quarter policy must print options before the first prompt."""
    commission, culture = _make_season_state(seed=0)
    io = _MockIO(['liberal'])
    _ask_quarter_policy(commission, culture, io)
    # The options line must appear before the prompt in captured output
    all_output = '\n'.join(io.lines)
    assert 'strict' in all_output, "Options must be printed before prompting"
    assert 'liberal' in all_output
    assert 'free_rein' in all_output


# ------------------------------------------------------------------
# UX-06: dispatch prompt explains what partial withholds


def test_ux06_dispatch_explanation_constant_mentions_casualties():
    """The dispatch explanation constant must mention 'casualt' for partial."""
    assert 'casualt' in _DISPATCH_EXPLANATION.lower() or \
           ('partial' in _DISPATCH_EXPLANATION.lower() and 'omit' in _DISPATCH_EXPLANATION.lower()), (
        "Dispatch explanation must convey what partial withholds (casualties)"
    )


def test_ux06_ask_dispatch_prints_explanation_before_prompt():
    """_ask_dispatch must print an explanation of what partial withholds."""
    commission, culture = _make_season_state(seed=0)
    state = SeasonState(commission, seed=0, instant_orders=True)
    io = _MockIO(['partial'])
    _ask_dispatch(state, 'siege', io,
                  full_claims={'outcome': 'NEGOTIATED', 'day': 29, 'casualties': 553},
                  partial_claims={'outcome': 'NEGOTIATED', 'day': 29})
    # Find the dispatch prompt line
    prompt_idx = next(
        (i for i, l in enumerate(io.lines) if 'dispatch' in l.lower()), None
    )
    assert prompt_idx is not None, "Dispatch prompt must appear in output"
    # The explanation must appear before or at the prompt (within 3 lines above)
    context = '\n'.join(io.lines[max(0, prompt_idx - 4):prompt_idx + 1])
    assert 'casualt' in context.lower() or 'omit' in context.lower(), (
        f"Explanation of what partial withholds must appear near the dispatch prompt.\n"
        f"Got context:\n{context}"
    )


# ------------------------------------------------------------------
# UX-08: storm vs wait siege differentiation in winter court prose


def _make_court_state(seed: int = 0) -> SeasonState:
    module = importlib.import_module('core.cultures.harfleur_1415')
    culture = module.CULTURE
    commission = generate_commission(culture, np.random.default_rng(seed))
    state = SeasonState(commission, seed, instant_orders=True)
    return state


def test_ux08_storm_negotiated_adds_specific_prose():
    """Storm tactic with NEGOTIATED outcome must add storm-specific court prose."""
    state = _make_court_state()
    state.siege_tactic = 'storm'
    state.siege_result = {'outcome': 'NEGOTIATED', 'day': 29, 'dead': 700, 'sick': 200,
                          'unfit_frac': 0.45}
    state.patron_favor = 0.65  # 'favor' credit label
    io = _CaptureIO()
    credit_label = 'favor'
    _print_court_scene(state, io, credit_label, state.patron_favor)
    joined = '\n'.join(io.lines).lower()
    assert 'storm' in joined, (
        "Winter court must mention 'storm' when siege tactic was storm"
    )


def test_ux08_wait_negotiated_does_not_add_storm_prose():
    """Wait tactic with NEGOTIATED outcome must NOT include storm-specific prose."""
    state = _make_court_state()
    state.siege_tactic = 'wait'
    state.siege_result = {'outcome': 'NEGOTIATED', 'day': 29, 'dead': 350, 'sick': 150,
                          'unfit_frac': 0.30}
    state.patron_favor = 0.65
    io = _CaptureIO()
    _print_court_scene(state, io, 'favor', state.patron_favor)
    joined = '\n'.join(io.lines).lower()
    # Wait tactic must not produce storm-specific language
    assert 'storm was pressed' not in joined, (
        "Wait tactic must not produce 'storm was pressed' prose"
    )


def test_ux08_storm_produces_different_prose_than_wait():
    """Winter court prose must differ between storm and wait siege tactics."""
    state_wait = _make_court_state()
    state_wait.siege_tactic = 'wait'
    state_wait.siege_result = {'outcome': 'NEGOTIATED', 'day': 29, 'dead': 350, 'sick': 150,
                                'unfit_frac': 0.30}
    state_wait.patron_favor = 0.65

    state_storm = _make_court_state()
    state_storm.siege_tactic = 'storm'
    state_storm.siege_result = {'outcome': 'NEGOTIATED', 'day': 29, 'dead': 700, 'sick': 200,
                                 'unfit_frac': 0.45}
    state_storm.patron_favor = 0.65

    io_wait = _CaptureIO()
    io_storm = _CaptureIO()
    _print_court_scene(state_wait, io_wait, 'favor', state_wait.patron_favor)
    _print_court_scene(state_storm, io_storm, 'favor', state_storm.patron_favor)

    wait_text = '\n'.join(io_wait.lines)
    storm_text = '\n'.join(io_storm.lines)
    assert wait_text != storm_text, (
        "Winter court prose must differ between storm and wait siege tactics"
    )
    assert 'storm' in storm_text.lower(), (
        "Storm tactic must be mentioned in the winter court prose"
    )
