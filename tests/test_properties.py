"""F3 property tests (CLAUDE.md spec): n=0 no-crash, fatigue bounds, siege_to_march invariants.

These three tests are exactly those CLAUDE.md §Testing Strategy / Property Tests promises.
"""
from hypothesis import given, settings
from hypothesis import strategies as st

from core.scenarios.agincourt import agincourt
from core.lattice import Battle
from core.chain import siege_to_march
from core.scenarios.harfleur import harfleur


# ---------------------------------------------------------------------------
# 1. Any cohort with n=0 does not crash

def _minimal_scn_with_n(n_val):
    """One cohort per side, configurable n for side 0."""
    return dict(
        field=(200, 100),
        cohorts=[
            dict(side=0, n=n_val, x=(10, 40), y=(10, 90), err=1.0, armor=0.0,
                 belief=0.6, disc=0.5, fat0=0.1),
            dict(side=1, n=5,     x=(140, 180), y=(10, 90), err=1.0, armor=0.0,
                 belief=0.6, disc=0.5, fat0=0.1),
        ],
    )


@given(n=st.integers(min_value=0, max_value=5))
@settings(max_examples=20)
def test_zero_agent_cohort_does_not_crash(n):
    """A cohort with n in [0, 5] must not raise; the sim completes or times out cleanly."""
    scn = _minimal_scn_with_n(n)
    b = Battle(scn, seed=42, det=False)
    ticks = 0
    while b.bt[0] is None and b.bt[1] is None and b.t < 600:
        b.tick()
        ticks += 1
        if ticks > 10_000:
            break


# ---------------------------------------------------------------------------
# 2. Fatigue stays in [0, 1] after any number of ticks

@given(seed=st.integers(min_value=0, max_value=9999),
       fat0=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@settings(max_examples=20, deadline=None)
def test_fatigue_stays_bounded(seed, fat0):
    """fat must remain in [0, 1] throughout any battle run."""
    scn = agincourt()
    for c in scn['cohorts']:
        c['fat0'] = fat0
    b = Battle(scn, seed=seed, det=False)
    ticks = 0
    while b.bt[0] is None and b.bt[1] is None and b.t < 1200:
        b.tick()
        ticks += 1
        if ticks > 5_000:
            break
        if b.alive.any():
            assert float(b.fat[b.alive].min()) >= 0.0, f"fat went negative at tick {ticks}"
            assert float(b.fat[b.alive].max()) <= 1.0, f"fat exceeded 1.0 at tick {ticks}"


# ---------------------------------------------------------------------------
# 3. siege_to_march never produces negative start

@given(
    besieger=st.integers(min_value=0, max_value=10_000),
    unfit_frac=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
)
@settings(max_examples=50)
def test_siege_to_march_start_non_negative(besieger, unfit_frac):
    """siege_to_march must never produce a negative start count."""
    siege_result = {'unfit_frac': unfit_frac, 'outcome': 'negotiated', 'day': 30}
    siege_scn = harfleur()
    siege_scn['besieger'] = besieger
    from core.scenarios.marches import agincourt_march
    march = siege_to_march(siege_result, siege_scn, agincourt_march())
    assert march['start'] >= 1, (
        f"start={march['start']} is < 1 for besieger={besieger}, unfit_frac={unfit_frac}"
    )
    assert march['fat0'] >= 0.0, f"fat0={march['fat0']} is negative"
    assert march['fat0'] <= 0.5, f"fat0={march['fat0']} exceeds clip ceiling"
