"""Tests for core/sentiment.py — sentiment drift field and dissolution runner (M7.4/M7.5)."""
import pytest
from core.sentiment import (
    TRACKED_RECEIPTS, SentimentSpec, SentimentField, run_dissolution,
    _default_winter_sentiments,
)


# ---------------------------------------------------------------------------
# SentimentSpec — Olleus's law enforcement

class TestSentimentSpec:
    def test_valid_spec_constructs(self):
        sp = SentimentSpec(
            id='cursed_campaign',
            valence='-',
            transmission={'idle': 0.8, 'arrears': 1.2},
        )
        assert sp.id == 'cursed_campaign'

    def test_untracked_transmission_raises(self):
        with pytest.raises(ValueError, match="TRACKED_RECEIPTS"):
            SentimentSpec(
                id='bad_sentiment',
                valence='-',
                transmission={'morale': 0.5, 'quality': 0.3},  # not in registry
            )

    def test_all_tracked_receipts_allowed(self):
        for key in TRACKED_RECEIPTS:
            sp = SentimentSpec(
                id=f'test_{key}',
                valence='-',
                transmission={key: 0.5},
            )
            assert key in sp.transmission

    def test_empty_transmission_allowed(self):
        sp = SentimentSpec(id='passive', valence='+', transmission={})
        assert sp.transmission == {}


# ---------------------------------------------------------------------------
# SentimentField

def _make_cursed_field(n=3):
    spec = SentimentSpec(
        id='cursed_campaign',
        valence='-',
        affects=['honor_in_death'],
        transmission={'idle': 0.8, 'arrears': 1.2, 'bond': 0.5},
        seed_events=['pointless_loss', 'broken_promise'],
        counter='dispatch_trusted_officer',
    )
    sf = SentimentField(list(range(n)), [spec])
    # chain edges: 0-1, 1-2
    sf.set_edges([(i, i+1, 0.8) for i in range(n-1)])
    return sf


class TestSentimentField:
    def test_seed_plants_penetration(self):
        sf = _make_cursed_field()
        sf.seed('pointless_loss', cause_cohort=0, initial_penetration=0.40)
        assert sf.penetration('cursed_campaign', 0) == pytest.approx(0.40)

    def test_seed_unknown_event_is_noop(self):
        sf = _make_cursed_field()
        sf.seed('miracle', cause_cohort=0, initial_penetration=0.50)
        assert sf.penetration('cursed_campaign', 0) == 0.0

    def test_tick_spreads_to_neighbour(self):
        sf = _make_cursed_field()
        # Set low officer authority so spread is not fully blocked
        for i in range(3):
            sf.set_authority(i, 0.0)
        sf.seed('pointless_loss', cause_cohort=0, initial_penetration=0.50)
        receipts = {'idle': 20, 'arrears': 0.8, 'bond': 0.6, 'officers': 0.0}
        sf.tick(receipts)
        # Cohort 1 should have picked up some penetration
        assert sf.penetration('cursed_campaign', 1) > 0.0

    def test_tick_decays_without_spread(self):
        sf = _make_cursed_field(n=1)
        sf.seed('pointless_loss', cause_cohort=0, initial_penetration=0.50)
        receipts = {'idle': 0, 'arrears': 0.0, 'bond': 0.0}
        sf.tick(receipts)
        # Passive decay should reduce
        assert sf.penetration('cursed_campaign', 0) < 0.50

    def test_tick_emits_threshold_crossing_event(self):
        # Use n=2: cohort 0 at 0.95 spreads to cohort 1 which starts at 0.69
        # Both authorities at 0.0 so resistance is zero
        sf = _make_cursed_field(n=2)
        sf.set_authority(0, 0.0)
        sf.set_authority(1, 0.0)
        sf._penetration['cursed_campaign'][0] = 0.999   # maximum pressure
        sf._penetration['cursed_campaign'][1] = 0.69
        receipts = {'idle': 30, 'arrears': 1.0, 'bond': 1.0, 'officers': 0.0}
        events = sf.tick(receipts)
        # Cohort 1 should have crossed 0.70 from the spread
        crossings = [(cid, sid) for (cid, sid, old_p, new_p) in events
                     if sid == 'cursed_campaign' and cid == 1]
        assert len(crossings) == 1

    def test_threshold_event_not_emitted_twice(self):
        # Use n=2 same as crossing test: cohort 0 high, cohort 1 at 0.69
        sf = _make_cursed_field(n=2)
        sf.set_authority(0, 0.0)
        sf.set_authority(1, 0.0)
        sf._penetration['cursed_campaign'][0] = 0.999
        sf._penetration['cursed_campaign'][1] = 0.69
        receipts = {'idle': 30, 'arrears': 1.0, 'bond': 1.0, 'officers': 0.0}
        events1 = sf.tick(receipts)  # cohort 1 crosses 0.70
        events2 = sf.tick(receipts)  # already flipped — should not re-emit
        assert len([e for e in events1 if e[1] == 'cursed_campaign']) == 1
        assert len([e for e in events2 if e[1] == 'cursed_campaign']) == 0

    def test_apply_counter_reduces_penetration(self):
        sf = _make_cursed_field()
        sf.seed('pointless_loss', cause_cohort=0, initial_penetration=0.60)
        sf.apply_counter('cursed_campaign', 0, reduction=0.30)
        assert sf.penetration('cursed_campaign', 0) == pytest.approx(0.30)

    def test_counter_all_reduces_all_cohorts(self):
        sf = _make_cursed_field()
        for i in range(3):
            sf.seed('pointless_loss', cause_cohort=i, initial_penetration=0.50)
        sf.counter_all('cursed_campaign', reduction=0.20)
        for i in range(3):
            assert sf.penetration('cursed_campaign', i) <= 0.31  # 0.50 - 0.20 = 0.30 + decay

    def test_max_penetration(self):
        sf = _make_cursed_field()
        sf.seed('pointless_loss', cause_cohort=0, initial_penetration=0.60)
        sf.seed('pointless_loss', cause_cohort=1, initial_penetration=0.40)
        assert sf.max_penetration('cursed_campaign') == pytest.approx(0.60)

    def test_cohort_summary_has_all_cohorts(self):
        sf = _make_cursed_field(n=3)
        summary = sf.cohort_summary()
        assert len(summary) == 3
        for row in summary:
            assert 'cohort_id' in row
            assert 'cursed_campaign' in row
            assert 'authority' in row

    def test_authority_set_clamped(self):
        sf = _make_cursed_field()
        sf.set_authority(0, 1.5)
        assert sf._authority[0] == 1.0
        sf.set_authority(0, -0.3)
        assert sf._authority[0] == 0.0

    def test_penetration_clamped_to_one(self):
        sf = _make_cursed_field(n=1)
        sf.seed('pointless_loss', cause_cohort=0, initial_penetration=0.90)
        sf.seed('pointless_loss', cause_cohort=0, initial_penetration=0.90)
        assert sf.penetration('cursed_campaign', 0) <= 1.0


# ---------------------------------------------------------------------------
# Default winter sentiments

class TestDefaultWinterSentiments:
    def test_specs_construct_without_error(self):
        specs = _default_winter_sentiments()
        assert len(specs) >= 2
        assert all(isinstance(s, SentimentSpec) for s in specs)

    def test_all_transmission_terms_tracked(self):
        for spec in _default_winter_sentiments():
            bad = set(spec.transmission) - TRACKED_RECEIPTS
            assert not bad, f"{spec.id}: untracked terms {bad}"


# ---------------------------------------------------------------------------
# run_dissolution — M7.5

class TestRunDissolution:
    def _get_scn(self):
        from core.scenarios.winter_quarters import winter_quarters
        return winter_quarters()

    def test_effective_frac_below_threshold(self):
        scn = self._get_scn()
        result = run_dissolution(scn, seed=0)
        assert result['effective_frac'] < 0.50, (
            f"expected effective_frac < 0.50, got {result['effective_frac']}"
        )

    def test_no_combat_events(self):
        scn = self._get_scn()
        result = run_dissolution(scn, seed=0)
        assert result['combat_events'] == [], (
            f"combat_events should be empty, got {result['combat_events']}"
        )

    def test_sentiment_max_reached(self):
        scn = self._get_scn()
        result = run_dissolution(scn, seed=0)
        assert result['sentiment_max'] > 0.0

    def test_sentiment_summary_present(self):
        scn = self._get_scn()
        result = run_dissolution(scn, seed=0)
        assert isinstance(result['sentiment_summary'], list)
        assert len(result['sentiment_summary']) > 0

    def test_result_has_trace(self):
        scn = self._get_scn()
        result = run_dissolution(scn, seed=0)
        assert 'trace' in result

    def test_deterministic(self):
        scn = self._get_scn()
        r1 = run_dissolution(scn, seed=7)
        r2 = run_dissolution(scn, seed=7)
        assert r1['effective_frac'] == r2['effective_frac']
        assert r1['sentiment_max'] == r2['sentiment_max']
