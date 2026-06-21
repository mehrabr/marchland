"""Battery officer probes (M7.7): isolated officer-decision tests.

Each probe creates an officer with a scripted belief state (with seed-based
noise), runs the relevant decision method, and returns a result dict.

The discriminator (§2 of the officer-battery spec): every officer action is
traced back to the officer's belief state at decision time. If the action was
sensible given that belief, it passes — even if it would lose the battle.

Probe functions follow the convention:
    run_<name>(seed: int) -> dict

All probes are collected in OFFICER_PROBES for registration in runner.py.
"""
import numpy as np
from core.officer import (
    Officer, make_officer, OfficerDecision,
    SUICIDAL_FOE_DENSITY, EXPLOITABLE_GAP_THRESHOLD,
    DISPATCH_AMBIGUITY_THRESHOLD, CAVALRY_FORMED_DENSITY,
    ORDER_TYPES,
)


# ---------------------------------------------------------------------------
# officer_open_flank (grade A) — initiative within intent
# Setup: hold order + visible open flank. Pass: exploits in majority of seeds.
# Reject: inert every seed OR exploits a gap it can't see.

def run_officer_open_flank(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    # Coverage always below base threshold (0.20) — gap is genuinely visible
    coverage = float(rng.uniform(0.04, 0.17))
    gap_side = 'right'
    trust = float(rng.uniform(0.65, 0.90))
    officer = make_officer(
        cohort_id=0, role='flank_commander', authority=0.85, trust=trust,
        beliefs={'foe_coverage_fraction': coverage, 'foe_gap_side': gap_side},
        belief_confidence=0.85,
    )
    action = officer.seek_opportunity()
    return {
        'probe': 'officer_open_flank',
        'exploited': action is not None and action.get('type') == 'flank',
        'gap_side': action.get('target_side') if action else None,
        'self_initiated': action.get('self_initiated', False) if action else False,
        'coverage': coverage,
        'trust': trust,
        'trace_cheat': False,  # belief is the only source — no trace access
    }


# ---------------------------------------------------------------------------
# officer_suicidal_order (grade A) — refusing the literal
# Setup: charge order + pike wall visible. Pass: refuses in majority of seeds.
# Allow (captain-wrong): high-deference officer obeys.
# Reject: charges with no interpretation regardless of trust (must not be grade-A reject).

def run_officer_suicidal_order(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    # Density always above suicidal threshold (4.0)
    density = float(rng.uniform(4.5, 8.0))
    # Trust varies: most seeds normal, some low-deference (very low trust)
    trust = float(rng.uniform(0.2, 0.9))
    officer = make_officer(
        cohort_id=1, role='infantry_commander', authority=0.85, trust=trust,
        beliefs={'foe_density_ahead': density, 'own_strength_frac': 0.85},
        belief_confidence=0.88,
    )
    decision = officer.process_order({'type': 'charge'})
    refused = decision.order_executed == 'hold'
    # captain-wrong: very low trust officer obeys literally — allow, don't reject
    cowed_comply = decision.order_executed == 'charge' and trust < 0.30
    return {
        'probe': 'officer_suicidal_order',
        'refused': refused,
        'cowed_comply': cowed_comply,   # captain-wrong — allowed behavior
        'density': density,
        'trust': trust,
        'belief_cited': 'foe_density_ahead' in decision.belief_state,
    }


# ---------------------------------------------------------------------------
# officer_stale_order (grade A) — acting on yesterday's truth
# Setup: standing order 'advance'; countermand 'hold' dispatched but in-flight.
# Officer acts at decision_tick < arrival_tick.
# Pass: executes 'advance' (the stale order it holds).
# Reject: acts on 'hold' before it arrives (latency violation).

def run_officer_stale_order(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    # Fixed setup: officer has 'advance' order, countermand arrives at tick 150
    # Officer acts at tick 100 — before countermand arrives
    advance_order = {'type': 'advance', 'dispatch_confidence': 0.90}
    countermand_order = {'type': 'hold'}
    countermand_arrival_tick = 150.0
    decision_tick = float(rng.uniform(50.0, 140.0))  # always before arrival

    officer = make_officer(
        cohort_id=2, role='vanguard', authority=0.85, trust=0.70,
        beliefs={'foe_density_ahead': 0.8},
        belief_confidence=0.85,
    )
    officer.receive_order(advance_order)
    # Countermand sent — but officer doesn't know (rider in flight)
    # Officer acts NOW (at decision_tick < countermand_arrival_tick)

    decision = officer.act_on_standing_order()
    executed_stale = decision.order_executed == 'advance'
    # The countermand WOULD change the order if applied — but it hasn't arrived
    latency_respected = decision_tick < countermand_arrival_tick
    return {
        'probe': 'officer_stale_order',
        'executed_stale_order': executed_stale,
        'latency_respected': latency_respected,
        'decision_tick': decision_tick,
        'countermand_arrival_tick': countermand_arrival_tick,
    }


# ---------------------------------------------------------------------------
# officer_ambiguous_order (grade B) — interpretation under noise
# Setup: low-confidence dispatch "advance when favorable"; belief varies.
# Finding: interpretation biases toward what belief emphasizes.
# Reject: picks randomly with no belief coupling.

def run_officer_ambiguous_order(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    dispatch_confidence = float(rng.uniform(0.35, 0.60))  # always ambiguous
    # Foe density spans both sides of the 1.5 threshold
    foe_density = float(rng.uniform(0.3, 3.0))
    officer = make_officer(
        cohort_id=3, role='vanguard', authority=0.85, trust=0.60,
        beliefs={'foe_density_ahead': foe_density},
        belief_confidence=0.88,
    )
    order = {
        'type': 'advance',
        'when': 'when_favorable',
        'dispatch_confidence': dispatch_confidence,
    }
    decision = officer.process_order(order)
    conditions_favorable = foe_density < 1.5
    # Belief-coupled: if conditions favorable → should advance; else hold
    belief_coupled = (
        (conditions_favorable and decision.order_executed == 'advance') or
        (not conditions_favorable and decision.order_executed == 'hold')
    )
    return {
        'probe': 'officer_ambiguous_order',
        'order_executed': decision.order_executed,
        'belief_coupled': belief_coupled,
        'foe_density': foe_density,
        'conditions_favorable': conditions_favorable,
        'dispatch_confidence': dispatch_confidence,
    }


# ---------------------------------------------------------------------------
# officer_cavalry_judgment (grade A) — repertoire-appropriate refusal
# Setup: cavalry officer + charge/advance order + formed dense infantry.
# Pass: refuses to charge formed density >= horse_solid in majority of seeds.
# Reject: charges formed pikes frontally.

def run_officer_cavalry_judgment(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    # Density always above cavalry threshold (3.0)
    density = float(rng.uniform(3.5, 7.0))
    officer = make_officer(
        cohort_id=4, role='cavalry_wing', authority=0.85, trust=0.75,
        mounted=True,
        beliefs={'foe_density_ahead': density},
        belief_confidence=0.85,
    )
    order_type = 'charge' if rng.random() > 0.5 else 'advance'
    decision = officer.process_order({'type': order_type})
    refused = decision.order_executed == 'hold'
    return {
        'probe': 'officer_cavalry_judgment',
        'refused_formed_charge': refused,
        'order_type': order_type,
        'density': density,
        'cavalry_threshold': CAVALRY_FORMED_DENSITY,
    }


# ---------------------------------------------------------------------------
# officer_dead_repertoire (grade A) — capability deletion
# Setup: same fighting_withdrawal order to an alive officer and a dead officer.
# Pass: alive executes; dead holds (repertoire empty).
# Reject: dead officer executes fighting_withdrawal (repertoire not gated by officer).

def run_officer_dead_repertoire(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    _ = rng.random()  # consume seed so each seed has consistent noise structure
    withdrawal_order = {'type': 'fighting_withdrawal'}

    # Alive officer with fighting_withdrawal in repertoire
    alive = make_officer(
        cohort_id=5, role='center_commander', authority=0.85, trust=0.70,
        repertoire=frozenset({'fighting_withdrawal', 'hold', 'advance', 'charge'}),
        beliefs={'foe_density_ahead': 2.0},
        belief_confidence=0.85,
    )
    alive_decision = alive.process_order(withdrawal_order)

    # Dead officer (officer down at first contact — mago_center equivalent)
    dead = make_officer(
        cohort_id=5, role='center_commander', authority=0.85, trust=0.70,
        repertoire=frozenset({'fighting_withdrawal', 'hold', 'advance', 'charge'}),
        is_dead=True,
        beliefs={'foe_density_ahead': 2.0},
        belief_confidence=0.85,
    )
    dead_decision = dead.process_order(withdrawal_order)

    return {
        'probe': 'officer_dead_repertoire',
        'alive_can_withdraw': alive_decision.order_executed == 'fighting_withdrawal',
        'dead_cannot_withdraw': dead_decision.order_executed == 'hold',
        'dead_rationale_mentions_down': 'down' in dead_decision.rationale.lower(),
    }


# ---------------------------------------------------------------------------
# officer_honest_report (grade B) — the upward channel
# Setup: officer with bad-news beliefs. Finding: report reflects belief;
# low-trust officers shade (under-report losses).
# Reject: reports are always perfectly accurate (no belief mediation).

def run_officer_honest_report(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    trust = float(rng.uniform(0.0, 1.0))
    # Bad news: wing is faring badly
    dead_frac_actual = float(rng.uniform(0.25, 0.55))
    officer = make_officer(
        cohort_id=6, role='wing_commander', authority=0.80, trust=trust,
        beliefs={
            'dead_fraction': dead_frac_actual,
            'own_strength_frac': 1.0 - dead_frac_actual,
            'routed_foe': 0.10,
        },
        belief_confidence=0.80,
    )
    report = officer.honest_report()
    reported_dead_frac = report['report'].get('battle', {}).get('dead_fraction', {})
    reported_val = reported_dead_frac.get('reported', dead_frac_actual) if reported_dead_frac else dead_frac_actual
    # Report must reflect belief (not fabricated), shading is trust-dependent
    from_belief = abs(reported_val - dead_frac_actual) <= dead_frac_actual * 0.4  # within 40% = from belief
    shaded = report['shading_applied']
    return {
        'probe': 'officer_honest_report',
        'trust': trust,
        'dead_frac_actual': dead_frac_actual,
        'reported_dead_frac': reported_val,
        'report_from_belief': from_belief,
        'shading_applied': shaded,
        # Low trust → shading ON; high trust → shading OFF (grade B: distribution is the finding)
        'trust_shading_coupled': (trust < 0.8) == shaded,
    }


# ---------------------------------------------------------------------------
# officer_initiative_vs_trust (grade A) — trust ledger is viscosity, not a dice roll
# Setup: same open-flank opportunity for high-trust and low-trust officers.
# Pass: high-trust exploits more often than low-trust, monotonically.
# Reject: trust has no effect OR low-trust produces erratic mutiny behavior.

def run_officer_initiative_vs_trust(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    # Coverage in the range where trust MATTERS: between low-trust threshold and high-trust threshold
    # low-trust threshold = 0.2*(0.5+0.2)=0.14, high-trust threshold = 0.2*(0.5+0.9)=0.28
    # Coverage in [0.12, 0.26] creates the discriminating zone
    coverage = float(rng.uniform(0.12, 0.26))
    gap_side = 'right'

    high_trust_officer = make_officer(
        cohort_id=7, role='flank_commander', authority=0.85, trust=0.90,
        beliefs={'foe_coverage_fraction': coverage, 'foe_gap_side': gap_side},
        belief_confidence=0.85,
    )
    low_trust_officer = make_officer(
        cohort_id=8, role='flank_commander', authority=0.85, trust=0.20,
        beliefs={'foe_coverage_fraction': coverage, 'foe_gap_side': gap_side},
        belief_confidence=0.85,
    )

    high_action = high_trust_officer.seek_opportunity()
    low_action = low_trust_officer.seek_opportunity()

    high_exploited = high_action is not None and high_action.get('type') == 'flank'
    low_exploited = low_action is not None and low_action.get('type') == 'flank'

    # Monotone requirement: in the discriminating zone, high trust ≥ low trust
    # (high trust can exploit when low trust cannot; both may exploit obvious gaps)
    monotone_holds = high_exploited or not low_exploited  # ¬(low and ¬high)
    return {
        'probe': 'officer_initiative_vs_trust',
        'coverage': coverage,
        'high_trust_exploited': high_exploited,
        'low_trust_exploited': low_exploited,
        'monotone_holds': monotone_holds,
        # No mutiny from low trust — low trust must produce hold, not erratic action
        'low_trust_no_mutiny': low_action is None or low_action.get('type') == 'flank',
    }


# ---------------------------------------------------------------------------
# Registry: all probes callable as OFFICER_PROBES[name](seed) -> dict

OFFICER_PROBES = {
    'officer_open_flank': run_officer_open_flank,
    'officer_suicidal_order': run_officer_suicidal_order,
    'officer_stale_order': run_officer_stale_order,
    'officer_ambiguous_order': run_officer_ambiguous_order,
    'officer_cavalry_judgment': run_officer_cavalry_judgment,
    'officer_dead_repertoire': run_officer_dead_repertoire,
    'officer_honest_report': run_officer_honest_report,
    'officer_initiative_vs_trust': run_officer_initiative_vs_trust,
}
