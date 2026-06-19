"""Tests for core/officer.py — officer model with belief-DB-driven decisions (M7.7).

Battery acceptance criteria:
  - officer_refuses_suicidal: foe_density >= 4.0 → holds regardless of order
  - officer_exploits_flank: foe_coverage < 0.2 and gap known → returns flank action
  - officer_misreads_dispatch: low-confidence advance order + favorable belief → advances now
"""
import pytest
from core.officer import (
    Officer, OfficerDecision, make_officer,
    SUICIDAL_FOE_DENSITY, EXPLOITABLE_GAP_THRESHOLD, DISPATCH_AMBIGUITY_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Helpers

def _officer_with_density(density: float, role='flank_commander', authority=0.85) -> Officer:
    return make_officer(
        cohort_id=0,
        role=role,
        authority=authority,
        beliefs={'foe_density_ahead': density, 'own_strength_frac': 0.9},
        belief_confidence=0.90,
    )


def _officer_with_gap(coverage: float, gap_side='left', authority=0.85) -> Officer:
    return make_officer(
        cohort_id=1,
        role='flank_commander',
        authority=authority,
        beliefs={
            'foe_coverage_fraction': coverage,
            'foe_gap_side': gap_side,
        },
        belief_confidence=0.90,
    )


# ---------------------------------------------------------------------------
# officer_refuses_suicidal (M7.7 battery target)

class TestOfficerRefusesSuicidal:
    def test_holds_when_density_at_threshold(self):
        officer = _officer_with_density(SUICIDAL_FOE_DENSITY)
        decision = officer.process_order({'type': 'charge'})
        assert decision.order_executed == 'hold'
        assert not decision.complied

    def test_holds_when_density_above_threshold(self):
        officer = _officer_with_density(SUICIDAL_FOE_DENSITY + 1.0)
        decision = officer.process_order({'type': 'charge'})
        assert decision.order_executed == 'hold'
        assert 'suicidal' in decision.rationale.lower()

    def test_charges_when_density_below_threshold(self):
        officer = _officer_with_density(SUICIDAL_FOE_DENSITY - 1.0)
        decision = officer.process_order({'type': 'charge'})
        assert decision.order_executed == 'charge'
        assert decision.complied

    def test_holds_when_own_strength_critical(self):
        officer = make_officer(
            cohort_id=0, role='rearguard', authority=0.85,
            beliefs={'foe_density_ahead': 1.0, 'own_strength_frac': 0.20},
            belief_confidence=0.90,
        )
        decision = officer.process_order({'type': 'charge'})
        assert decision.order_executed == 'hold'

    def test_belief_state_logged_in_decision(self):
        officer = _officer_with_density(SUICIDAL_FOE_DENSITY + 0.5)
        decision = officer.process_order({'type': 'charge'})
        assert 'foe_density_ahead' in decision.belief_state
        assert decision.belief_state['foe_density_ahead'] >= SUICIDAL_FOE_DENSITY


# ---------------------------------------------------------------------------
# officer_exploits_flank (M7.7 battery target)

class TestOfficerExploitsFlank:
    def test_returns_flank_action_when_gap_visible(self):
        officer = _officer_with_gap(EXPLOITABLE_GAP_THRESHOLD - 0.05, gap_side='right')
        action = officer.seek_opportunity()
        assert action is not None
        assert action['type'] == 'flank'
        assert action['target_side'] == 'right'
        assert action['self_initiated'] is True

    def test_no_action_when_coverage_above_threshold(self):
        officer = _officer_with_gap(EXPLOITABLE_GAP_THRESHOLD + 0.05)
        action = officer.seek_opportunity()
        assert action is None

    def test_no_action_when_gap_side_unknown(self):
        officer = make_officer(
            cohort_id=2, role='vanguard',
            beliefs={'foe_coverage_fraction': 0.1},  # gap present but side unknown
            belief_confidence=0.85,
        )
        action = officer.seek_opportunity()
        assert action is None

    def test_no_action_when_no_battle_beliefs(self):
        officer = Officer(cohort_id=0, role='reserves')
        action = officer.seek_opportunity()
        assert action is None

    def test_rationale_cites_gap_percentage(self):
        officer = _officer_with_gap(0.10, gap_side='left')
        action = officer.seek_opportunity()
        assert action is not None
        assert '10%' in action['rationale'] or '0.10' in action['rationale'] or 'gap' in action['rationale'].lower()


# ---------------------------------------------------------------------------
# officer_misreads_dispatch (M7.7 battery target)

class TestOfficerMisreadsDispatch:
    def _ambiguous_advance_order(self, dispatch_confidence: float):
        return {
            'type': 'advance',
            'when': 'when_favorable',
            'dispatch_confidence': dispatch_confidence,
        }

    def test_misreads_as_advance_now_with_low_confidence_and_low_threat(self):
        officer = make_officer(
            cohort_id=0, role='vanguard',
            beliefs={'foe_density_ahead': 0.8},  # believed low density = favorable
            belief_confidence=0.90,
        )
        order = self._ambiguous_advance_order(DISPATCH_AMBIGUITY_THRESHOLD - 0.10)
        decision = officer.process_order(order)
        assert decision.order_executed == 'advance'
        assert 'advance now' in decision.rationale.lower() or 'favorable' in decision.rationale.lower()
        assert 'interpretation' in decision.belief_state

    def test_holds_when_ambiguous_but_threat_high(self):
        officer = make_officer(
            cohort_id=0, role='vanguard',
            beliefs={'foe_density_ahead': 2.5},  # believed high density = unfavorable
            belief_confidence=0.90,
        )
        order = self._ambiguous_advance_order(DISPATCH_AMBIGUITY_THRESHOLD - 0.10)
        decision = officer.process_order(order)
        assert decision.order_executed == 'hold'
        assert not decision.complied

    def test_obeys_clear_unambiguous_order(self):
        officer = make_officer(cohort_id=0, role='vanguard')
        order = {
            'type': 'advance',
            'dispatch_confidence': 0.95,  # high confidence = no ambiguity
        }
        decision = officer.process_order(order)
        assert decision.order_executed == 'advance'
        assert decision.complied

    def test_belief_state_records_interpretation(self):
        officer = make_officer(
            cohort_id=0, role='vanguard',
            beliefs={'foe_density_ahead': 0.5},
            belief_confidence=0.90,
        )
        order = self._ambiguous_advance_order(0.40)
        decision = officer.process_order(order)
        assert 'dispatch_confidence' in decision.belief_state


# ---------------------------------------------------------------------------
# General officer behaviour

class TestOfficerGeneral:
    def test_unrecognised_order_defaults_to_hold(self):
        officer = Officer(cohort_id=0, role='vanguard')
        decision = officer.process_order({'type': 'teleport'})
        assert decision.order_executed == 'hold'
        assert not decision.complied

    def test_low_authority_prevents_enforcement(self):
        officer = Officer(cohort_id=0, role='rearguard', authority=0.10)
        decision = officer.process_order({'type': 'withdraw'})
        assert decision.order_executed == 'hold'

    def test_sufficient_authority_obeys_withdraw(self):
        officer = Officer(cohort_id=0, role='rearguard', authority=0.80)
        decision = officer.process_order({'type': 'withdraw'})
        assert decision.order_executed == 'withdraw'
        assert decision.complied

    def test_flank_order_converted_to_advance_without_gap(self):
        officer = make_officer(cohort_id=0, role='flank_commander',
                               beliefs={}, belief_confidence=0.5)
        decision = officer.process_order({'type': 'flank'})
        assert decision.order_executed == 'advance'
        assert not decision.complied

    def test_flank_order_complied_with_known_gap(self):
        officer = make_officer(
            cohort_id=0, role='flank_commander',
            beliefs={'foe_gap_side': 'right'},
            belief_confidence=0.85,
        )
        decision = officer.process_order({'type': 'flank'})
        assert decision.order_executed == 'flank'
        assert decision.complied

    def test_degrade_authority_clamped(self):
        officer = Officer(cohort_id=0, role='vanguard', authority=0.30)
        officer.degrade_authority(0.50)
        assert officer.authority == 0.0

    def test_receive_dispatch_updates_beliefs(self):
        officer = Officer(cohort_id=0, role='vanguard')
        officer.receive_dispatch({'foe_density_ahead': 3.0}, 0.80)
        val = officer.belief_db.believed('battle', 'foe_density_ahead')
        assert val is not None
        assert val == pytest.approx(3.0)

    def test_observe_directly_updates_beliefs(self):
        officer = Officer(cohort_id=0, role='vanguard')
        officer.observe_directly({'foe_density_ahead': 2.5}, source='sightlines')
        val = officer.belief_db.believed('battle', 'foe_density_ahead')
        assert val is not None

    def test_make_officer_factory(self):
        officer = make_officer(cohort_id=5, role='reserves', authority=0.70)
        assert officer.cohort_id == 5
        assert officer.role == 'reserves'
        assert officer.authority == pytest.approx(0.70)
