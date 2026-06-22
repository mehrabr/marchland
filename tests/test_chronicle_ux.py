"""Tests for the presentation redesign: the chronicle is re-narrated FROM the
trace in a vantage voice with sympathies — no engine numbers on the wall, magnitude
preserved, and the grounding rule unchanged (every line still cites an event,
surfaced on demand via the inspection path).

Spec: docs/marchland-presentation-redesign-spec.md §3 and §5 checklist.
"""
import re

from tools.chronicle import (
    generate_chronicle,
    build_chronicle,
    chronicle_with_citations,
)
from core.trace import Trace, compose_traces
from core.march import run_march
from core.scenarios.marches import agincourt_march
from core.chain import run_chain_1415


def _chain_trace(seed: int = 0):
    return run_chain_1415(seed)['trace']


def _march_chronicle(seed: int = 0) -> str:
    tr = Trace(phase='march', scenario='agincourt_march', seed=seed)
    run_march(agincourt_march(), seed, trace=tr)
    return generate_chronicle(compose_traces([tr]))


# ------------------------------------------------------------------
# The narration carries NO engine register

def test_narration_has_no_trace_citations():
    """No '(trace: ...)' smeared into the prose — citations live behind 'explain'."""
    text = generate_chronicle(_chain_trace())
    assert 'trace:' not in text.lower(), f"Narration must not contain 'trace:':\n{text}"


def test_narration_has_no_sideN_labels():
    """The narrator is a person on a side — never the omniscient 'side-1'/'side1'."""
    text = generate_chronicle(_chain_trace()).lower()
    assert 'side-1' not in text and 'side-0' not in text, "No 'side-N' labels in narration"
    assert 'side1' not in text and 'side0' not in text, "No 'sideN' labels in narration"


def test_narration_has_no_bare_second_timestamps():
    """No '2164s' / '78s' seconds-timestamps — the narrator does not hold a stopwatch."""
    text = generate_chronicle(_chain_trace())
    assert not re.search(r'\b\d+\s*s\b', text), f"Narration must not contain bare seconds:\n{text}"


def test_narration_has_no_arrows_or_class_tags():
    """No '→' arrows and no '[B]/[C]/[D]/[E]' class tags in the prose."""
    text = generate_chronicle(_chain_trace())
    assert '→' not in text, "No '→' in narration"
    for tag in ('[A', '[B', '[C', '[D', '[E'):
        assert tag not in text, f"No class tag {tag!r} in narration"


def test_narration_has_no_bare_digits_in_prose():
    """Numbers are spelled or kept behind the door — no raw figures on the wall."""
    text = generate_chronicle(_chain_trace())
    # Allow none: the whole chronicle is period prose. A stray digit would be a leak.
    assert not re.search(r'\d', text), f"Narration must carry no bare digits:\n{text}"


# ------------------------------------------------------------------
# The vantage voice with sympathies

def test_narration_speaks_from_a_side():
    """The chronicle is written from a vantage — 'our'/'ours'/'the King's army'."""
    text = generate_chronicle(_chain_trace()).lower()
    assert ('our men' in text or 'of ours' in text or "king's army" in text), (
        f"Chronicle must be written from a vantage with sympathies:\n{text}"
    )


# ------------------------------------------------------------------
# Magnitude must survive (Sarris's caution)

def test_magnitude_survives_in_period_register():
    """De-numbering must not flatten scale — a heavy toll still reads as heavy."""
    text = generate_chronicle(_chain_trace()).lower()
    assert 'the better part of a thousand' in text, (
        f"The siege's disease toll must read as magnitude, not vanish:\n{text}"
    )


def test_lopsided_result_reads_as_lopsided():
    """A one-sided field (the enemy broke and was pursued) reads one-sided."""
    text = generate_chronicle(_chain_trace()).lower()
    assert 'far more of theirs than of ours' in text, (
        f"A lopsided outcome must read lopsided in the prose:\n{text}"
    )
    assert 'the dead lay thick' in text, "The shock of the dead must survive de-numbering"


# ------------------------------------------------------------------
# The grounding rule is UNCHANGED — 'explain' still surfaces the event

def test_every_line_carries_a_grounding_citation():
    """Each narrated line holds its citing event in the parallel structure."""
    lines = build_chronicle(_chain_trace())
    assert lines, "Chronicle must produce lines"
    for ln in lines:
        assert ln.prose.strip(), "Every line has prose"
        assert ln.citation.strip(), f"Every line must carry a grounding citation: {ln.prose!r}"


def test_explain_surfaces_the_siege_outcome_event():
    """The siege line's citation surfaces the actual outcome event from the trace."""
    pairs = chronicle_with_citations(_chain_trace())
    # The opening (siege) line cites the negotiated surrender at its real day.
    siege_prose, siege_cite = pairs[0]
    assert 'NEGOTIATED@day' in siege_cite, (
        f"Explain must surface the grounding event; got citation {siege_cite!r}"
    )
    # And that event genuinely exists in the trace.
    events = _chain_trace()['events']
    assert any(e[0] == 'NEGOTIATED' for e in events), "Cited event must exist in the trace"


def test_explain_citation_never_appears_in_narration():
    """The grounding citation is the door, not the wall — it must not leak into prose."""
    trace = _chain_trace()
    text = generate_chronicle(trace)
    for _prose, citation in chronicle_with_citations(trace):
        assert citation not in text, (
            f"Citation {citation!r} must not appear in the narration itself"
        )


# ------------------------------------------------------------------
# Detour still narrated worldly (no raw event token)

def test_detour_narrated_in_the_world_not_as_an_event():
    """A forced detour reads as a barred road, not a 'detour@day8' citation."""
    text = _march_chronicle(seed=0).lower()
    assert 'detour@' not in text, "Detour must not surface its event token in prose"
    assert ('barred' in text or 'driven far aside' in text), (
        f"The detour must be narrated worldly:\n{text}"
    )
