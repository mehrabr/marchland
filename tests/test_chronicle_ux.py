"""Tests for UX-12: chronicle citation variety and detour reason field."""
from tools.chronicle import generate_chronicle
from core.trace import Trace, compose_traces
from core.march import run_march
from core.scenarios.marches import agincourt_march


def _get_march_chronicle(seed: int = 0) -> str:
    tr = Trace(phase='march', scenario='agincourt_march', seed=seed)
    run_march(agincourt_march(), seed, trace=tr)
    composed = compose_traces([tr])
    return generate_chronicle(composed)


def test_ux12_not_all_sentences_end_with_trace_citation():
    """Chronicle must not end every sentence with '(trace: ...)'."""
    text = _get_march_chronicle(seed=0)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    trace_suffix_count = sum(1 for s in sentences if s.endswith(')') and 'trace:' in s)
    assert trace_suffix_count < len(sentences) * 0.6, (
        f"Too many sentences end with trace citation: {trace_suffix_count}/{len(sentences)}\n{text}"
    )


def test_ux12_detour_event_has_reason_field():
    """Detour events in the march trace must carry a reason string."""
    tr = Trace(phase='march', scenario='agincourt_march', seed=0)
    run_march(agincourt_march(), seed=0, trace=tr)
    detours = [e for e in tr.events if e[0] == 'detour']
    assert detours, "agincourt_march must produce at least one detour event"
    for d in detours:
        assert 'reason' in d[2], f"Detour event must have a 'reason' field: {d}"
        assert d[2]['reason'], "Detour reason must be a non-empty string"


def test_ux12_detour_chronicle_uses_reason_prose():
    """Chronicle prose for detour must use the reason string, not just cite the event."""
    text = _get_march_chronicle(seed=0)
    # The reason 'road_blocked' → 'road blocked' must appear in the prose
    assert 'road blocked' in text.lower() or 'blocked road' in text.lower(), (
        f"Chronicle must include 'road blocked' from the detour reason. Got:\n{text}"
    )
    # The generic '(trace: detour@...)' pattern must NOT appear for the agincourt detour
    assert '(trace: detour@' not in text, (
        f"Detour with a reason must not fall back to trace citation pattern. Got:\n{text}"
    )


def test_ux12_arrival_sentence_has_inline_citation():
    """Arrival sentence must include citation, but not end the sentence with it."""
    text = _get_march_chronicle(seed=0)
    # Find the arrival sentence (contains 'arrived' or 'failed to arrive')
    sentences = [s.strip() for s in text.split('.') if 'arrived' in s.lower() or 'failed to arrive' in s.lower()]
    assert sentences, "Chronicle must contain an arrival sentence"
    arrival_sentence = sentences[0]
    # It must NOT end with a trace citation bracket
    assert not (arrival_sentence.endswith(')') and 'trace:' in arrival_sentence), (
        f"Arrival sentence must not end with trace citation; got: {arrival_sentence!r}"
    )
    # It must still reference 'trace:' somewhere (inline)
    assert 'trace:' in arrival_sentence, (
        f"Arrival sentence must include an inline trace citation; got: {arrival_sentence!r}"
    )
