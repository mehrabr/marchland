"""Tests for UX-03: audit table uses explanatory label for unverifiable claims."""
import importlib

import numpy as np

from clients.cli.season import SeasonState, _audit_phase
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
