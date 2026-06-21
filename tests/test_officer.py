"""Tests for core/officer.py — officer model with belief-DB-driven decisions (M7.7).

Battery acceptance criteria (isolated, belief-bounded):
  - officer_open_flank:          exploits gap; trust modulates threshold; no trace-cheat
  - officer_suicidal_order:      refuses charge into suicidal density; belief cited
  - officer_stale_order:         acts on stale standing order (latency model validated)
  - officer_ambiguous_order:     interpretation biases toward belief state
  - officer_cavalry_judgment:    mounted officer refuses formed infantry density
  - officer_dead_repertoire:     dead officer cannot execute any action
  - officer_honest_report:       report from belief; low trust shades bad news
  - officer_initiative_vs_trust: high trust exploits monotonically more than low trust
"""
import pytest
from core.officer import (
    Officer, OfficerDecision, make_officer,
    SUICIDAL_FOE_DENSITY, EXPLOITABLE_GAP_THRESHOLD, DISPATCH_AMBIGUITY_THRESHOLD,
    CAVALRY_FORMED_DENSITY, ORDER_TYPES,
)


# ---------------------------------------------------------------------------
# Helpers

def _officer_with_density(density: float, role='flank_commander', authority=0.85,
                           trust=0.70) -> Officer:
    return make_officer(
        cohort_id=0,
        role=role,
        authority=authority,
        trust=trust,
        beliefs={'foe_density_ahead': density, 'own_strength_frac': 0.9},
        belief_confidence=0.90,
    )


def _officer_with_gap(coverage: float, gap_side='left', authority=0.85,
                      trust=0.70) -> Officer:
    return make_officer(
        cohort_id=1,
        role='flank_commander',
        authority=authority,
        trust=trust,
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

    def test_cowed_officer_complies_literally(self):
        # trust < 0.30: cowed subordinate obeys literally into pikes — captain-wrong, not pathfinding-wrong
        officer = _officer_with_density(SUICIDAL_FOE_DENSITY + 2.0, trust=0.20)
        decision = officer.process_order({'type': 'charge'})
        assert decision.order_executed == 'charge'
        assert decision.complied


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
        # Default trust=0.70, adjusted threshold = 0.2*(0.5+0.7)=0.24
        # Coverage 0.30 > 0.24 → no action
        officer = _officer_with_gap(0.30)
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
        assert 'gap' in action['rationale'].lower() or '%' in action['rationale']

    def test_dead_officer_cannot_exploit(self):
        officer = make_officer(
            cohort_id=0, role='flank_commander', is_dead=True,
            beliefs={'foe_coverage_fraction': 0.05, 'foe_gap_side': 'left'},
            belief_confidence=0.90,
        )
        action = officer.seek_opportunity()
        assert action is None

    def test_flank_not_in_repertoire_no_initiative(self):
        officer = make_officer(
            cohort_id=0, role='flank_commander',
            repertoire=frozenset({'hold', 'advance', 'charge'}),  # no 'flank'
            beliefs={'foe_coverage_fraction': 0.05, 'foe_gap_side': 'right'},
            belief_confidence=0.90,
        )
        action = officer.seek_opportunity()
        assert action is None


# ---------------------------------------------------------------------------
# officer_misreads_dispatch / officer_ambiguous_order (M7.7 battery target)

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
# officer_stale_order (M7.7 battery target — latency model)

class TestOfficerStaleOrder:
    def test_executes_standing_order(self):
        officer = make_officer(cohort_id=0, role='vanguard',
                               beliefs={'foe_density_ahead': 0.8}, belief_confidence=0.85)
        advance_order = {'type': 'advance', 'dispatch_confidence': 0.90}
        officer.receive_order(advance_order)
        # Countermand sent but not yet received — officer acts on current_order
        decision = officer.act_on_standing_order()
        assert decision.order_executed == 'advance'

    def test_no_standing_order_defaults_to_hold(self):
        officer = Officer(cohort_id=0, role='vanguard')
        decision = officer.act_on_standing_order()
        assert decision.order_executed == 'hold'
        assert not decision.complied

    def test_receive_order_updates_standing_order(self):
        officer = Officer(cohort_id=0, role='vanguard')
        officer.receive_order({'type': 'charge'})
        assert officer.current_order is not None
        assert officer.current_order['type'] == 'charge'

    def test_second_order_overwrites_first(self):
        officer = make_officer(cohort_id=0, role='vanguard',
                               beliefs={'foe_density_ahead': 0.5}, belief_confidence=0.85)
        officer.receive_order({'type': 'advance'})
        officer.receive_order({'type': 'hold'})  # countermand received (rider arrived)
        decision = officer.act_on_standing_order()
        assert decision.order_executed == 'hold'


# ---------------------------------------------------------------------------
# officer_cavalry_judgment (M7.7 battery target)

class TestOfficerCavalryJudgment:
    def test_cavalry_refuses_formed_charge(self):
        officer = make_officer(
            cohort_id=0, role='cavalry_wing', mounted=True,
            beliefs={'foe_density_ahead': CAVALRY_FORMED_DENSITY + 1.0},
            belief_confidence=0.88,
        )
        decision = officer.process_order({'type': 'charge'})
        assert decision.order_executed == 'hold'
        assert not decision.complied
        assert 'cavalry' in decision.rationale.lower()

    def test_cavalry_refuses_advance_into_formed(self):
        officer = make_officer(
            cohort_id=0, role='cavalry_wing', mounted=True,
            beliefs={'foe_density_ahead': CAVALRY_FORMED_DENSITY + 0.5},
            belief_confidence=0.88,
        )
        decision = officer.process_order({'type': 'advance'})
        assert decision.order_executed == 'hold'

    def test_cavalry_charges_when_below_threshold(self):
        officer = make_officer(
            cohort_id=0, role='cavalry_wing', mounted=True,
            beliefs={'foe_density_ahead': CAVALRY_FORMED_DENSITY - 1.0},
            belief_confidence=0.88,
        )
        decision = officer.process_order({'type': 'charge'})
        assert decision.order_executed == 'charge'
        assert decision.complied

    def test_infantry_ignores_cavalry_judgment(self):
        # Non-mounted officer: cavalry judgment doesn't apply
        officer = make_officer(
            cohort_id=0, role='infantry_commander', mounted=False,
            beliefs={'foe_density_ahead': CAVALRY_FORMED_DENSITY + 2.0},
            belief_confidence=0.88,
        )
        decision = officer.process_order({'type': 'charge'})
        # Infantry should refuse via SUICIDAL_FOE_DENSITY, not cavalry judgment
        # CAVALRY_FORMED_DENSITY=3.0, SUICIDAL_FOE_DENSITY=4.0 → still above suicidal
        assert decision.order_executed == 'hold'  # but for suicidal reasons


# ---------------------------------------------------------------------------
# officer_dead_repertoire (M7.7 battery target — Addendum K)

class TestOfficerDeadRepertoire:
    def test_alive_officer_executes_fighting_withdrawal(self):
        officer = make_officer(
            cohort_id=0, role='center_commander',
            repertoire=frozenset({'fighting_withdrawal', 'hold', 'advance'}),
            beliefs={'foe_density_ahead': 2.0},
            belief_confidence=0.85,
        )
        decision = officer.process_order({'type': 'fighting_withdrawal'})
        assert decision.order_executed == 'fighting_withdrawal'
        assert decision.complied

    def test_dead_officer_cannot_execute_fighting_withdrawal(self):
        officer = make_officer(
            cohort_id=0, role='center_commander',
            repertoire=frozenset({'fighting_withdrawal', 'hold', 'advance'}),
            is_dead=True,
            beliefs={'foe_density_ahead': 2.0},
            belief_confidence=0.85,
        )
        decision = officer.process_order({'type': 'fighting_withdrawal'})
        assert decision.order_executed == 'hold'
        assert not decision.complied
        assert 'down' in decision.rationale.lower()

    def test_mark_dead_empties_effective_repertoire(self):
        officer = make_officer(
            cohort_id=0, role='vanguard',
            repertoire=frozenset(ORDER_TYPES),
        )
        assert not officer.is_dead
        officer.mark_dead()
        assert officer.is_dead
        for order_type in ('charge', 'advance', 'hold', 'fighting_withdrawal'):
            decision = officer.process_order({'type': order_type})
            assert decision.order_executed == 'hold'

    def test_order_not_in_repertoire_falls_back_to_hold(self):
        # Officer alive but fighting_withdrawal not in their repertoire
        officer = make_officer(
            cohort_id=0, role='vanguard',
            repertoire=frozenset({'charge', 'hold', 'advance'}),  # no fighting_withdrawal
            beliefs={'foe_density_ahead': 1.0},
            belief_confidence=0.85,
        )
        decision = officer.process_order({'type': 'fighting_withdrawal'})
        assert decision.order_executed == 'hold'
        assert not decision.complied
        assert 'repertoire' in decision.rationale.lower()


# ---------------------------------------------------------------------------
# officer_honest_report (M7.7 battery target — grade B)

class TestOfficerHonestReport:
    def test_report_from_belief_not_trace(self):
        officer = make_officer(
            cohort_id=0, role='wing_commander', trust=0.80,
            beliefs={'dead_fraction': 0.35, 'own_strength_frac': 0.65},
            belief_confidence=0.80,
        )
        report = officer.honest_report()
        assert 'officer_id' in report
        assert 'report' in report
        # Report structure: {phase: {claim: {reported, believed, confidence, shaded}}}
        battle_report = report['report'].get('battle', {})
        assert 'dead_fraction' in battle_report
        assert 'believed' in battle_report['dead_fraction']
        assert abs(battle_report['dead_fraction']['believed'] - 0.35) < 0.01

    def test_low_trust_shades_bad_news(self):
        officer = make_officer(
            cohort_id=0, role='wing_commander', trust=0.20,
            beliefs={'dead_fraction': 0.40},
            belief_confidence=0.80,
        )
        report = officer.honest_report()
        assert report['shading_applied'] is True
        battle_report = report['report'].get('battle', {})
        dead_entry = battle_report.get('dead_fraction', {})
        # Low trust: reported dead_fraction < believed dead_fraction (under-reporting losses)
        if dead_entry and 'reported' in dead_entry and 'believed' in dead_entry:
            assert dead_entry['reported'] <= dead_entry['believed']

    def test_high_trust_reports_accurately(self):
        officer = make_officer(
            cohort_id=0, role='wing_commander', trust=0.95,
            beliefs={'dead_fraction': 0.40},
            belief_confidence=0.80,
        )
        report = officer.honest_report()
        assert report['shading_applied'] is False
        battle_report = report['report'].get('battle', {})
        dead_entry = battle_report.get('dead_fraction', {})
        if dead_entry and 'reported' in dead_entry:
            assert dead_entry['shaded'] is False

    def test_empty_belief_db_produces_empty_report(self):
        officer = Officer(cohort_id=0, role='reserves')
        report = officer.honest_report()
        assert report['report'] == {}


# ---------------------------------------------------------------------------
# officer_initiative_vs_trust (M7.7 battery target)

class TestOfficerInitiativeVsTrust:
    def _officer_gap_scenario(self, trust: float, coverage: float = 0.18) -> Officer:
        return make_officer(
            cohort_id=0, role='flank_commander', trust=trust,
            beliefs={'foe_coverage_fraction': coverage, 'foe_gap_side': 'right'},
            belief_confidence=0.88,
        )

    def test_high_trust_exploits_where_low_trust_holds(self):
        # Coverage 0.18: high-trust threshold=0.2*(0.5+0.9)=0.28 → exploits
        #                low-trust threshold=0.2*(0.5+0.2)=0.14 → 0.18>0.14 → holds
        high = self._officer_gap_scenario(trust=0.90, coverage=0.18)
        low  = self._officer_gap_scenario(trust=0.20, coverage=0.18)
        assert high.seek_opportunity() is not None
        assert low.seek_opportunity() is None

    def test_both_exploit_obvious_gap(self):
        # Coverage 0.05: both thresholds > 0.05 → both exploit
        high = self._officer_gap_scenario(trust=0.90, coverage=0.05)
        low  = self._officer_gap_scenario(trust=0.20, coverage=0.05)
        assert high.seek_opportunity() is not None
        # low threshold = 0.2*(0.5+0.2)=0.14 > 0.05 → also exploits
        assert low.seek_opportunity() is not None

    def test_neither_exploits_covered_front(self):
        # Coverage 0.50: above all thresholds → neither exploits
        high = self._officer_gap_scenario(trust=0.90, coverage=0.50)
        low  = self._officer_gap_scenario(trust=0.20, coverage=0.50)
        assert high.seek_opportunity() is None
        assert low.seek_opportunity() is None

    def test_monotone_across_trust_range(self):
        # Across trust [0.0, 0.2, 0.5, 0.7, 0.9, 1.0] at coverage=0.18:
        # threshold = 0.2*(0.5+trust): exploits if coverage < threshold
        # 0.18 < 0.2*(0.5+trust) → trust > 0.4 → exploits for trust=0.5, 0.7, 0.9, 1.0
        coverage = 0.18
        trust_levels = [0.0, 0.2, 0.5, 0.7, 0.9, 1.0]
        exploits = []
        for t in trust_levels:
            o = self._officer_gap_scenario(trust=t, coverage=coverage)
            exploits.append(o.seek_opportunity() is not None)
        # Exploits must be monotone: once True, stays True as trust increases
        found_true = False
        for did_exploit in exploits:
            if did_exploit:
                found_true = True
            if found_true:
                assert did_exploit, f"Trust monotone violated: {list(zip(trust_levels, exploits))}"

    def test_low_trust_produces_no_mutiny(self):
        # Low trust: seek_opportunity returns None (hold) or 'flank' (the valid action)
        # NEVER produces charge, withdraw, advance, etc. — no erratic action
        officer = self._officer_gap_scenario(trust=0.0, coverage=0.05)
        action = officer.seek_opportunity()
        # Action must be None (hold) or a flank action — not something else
        assert action is None or action.get('type') == 'flank'


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
        officer = make_officer(cohort_id=5, role='reserves', authority=0.70,
                               trust=0.60, mounted=True)
        assert officer.cohort_id == 5
        assert officer.role == 'reserves'
        assert officer.authority == pytest.approx(0.70)
        assert officer.trust == pytest.approx(0.60)
        assert officer.mounted is True
        assert not officer.is_dead

    def test_fighting_withdrawal_available_in_default_repertoire(self):
        officer = Officer(cohort_id=0, role='center_commander')
        assert 'fighting_withdrawal' in officer.repertoire

    def test_order_not_in_custom_repertoire_rejected(self):
        officer = make_officer(
            cohort_id=0, role='simple_soldier',
            repertoire=frozenset({'hold', 'advance'}),
        )
        decision = officer.process_order({'type': 'fighting_withdrawal'})
        assert decision.order_executed == 'hold'
        assert 'repertoire' in decision.rationale.lower()
